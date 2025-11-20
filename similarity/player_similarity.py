"""
Player Similarity Engine

Motor de búsqueda similitud multi-criterio combinando distancia euclidiana UMAP,
probabilidades GMM y feature similarity. Identifica reemplazos potenciales.

Basado en:
    - Decroos et al. (2019): Actions speak louder than goals - VAEP similarity
    - Brooks et al. (2016): Using machine learning to quantify talent
    - Scoring multi-criterio ponderado

Clase principal:
    PlayerSimilarity: API unificada para búsqueda y validación similitud
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Union
from scipy.spatial.distance import euclidean, cosine
from scipy.stats import percentileofscore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerSimilarity:
    """
    Motor búsqueda jugadores similares usando UMAP + GMM + features.

    Combina múltiples criterios similitud:
        1. Distancia euclidiana en espacio UMAP (estructura manifiesto)
        2. Probabilidad GMM mismo cluster (pertenencia arquetipo)
        3. Similaridad features críticas (métricas específicas)

    Workflow:
        1. Recibe player_id query
        2. Encuentra vecinos cercanos en UMAP
        3. Calcula probabilidades GMM
        4. Pondera y rankea candidatos
        5. Aplica filtros contextuales (edad, liga, etc.)
        6. Retorna top_n similares con scores

    Attributes:
        embedding_df: DataFrame con UMAP + metadata
        gmm_proba: Matriz probabilidades GMM
        feature_df: DataFrame features originales (para similarity detallada)
        weights: Dict pesos para cada componente score
    """

    def __init__(self,
                 embedding_df: pd.DataFrame,
                 gmm_proba: np.ndarray,
                 feature_df: pd.DataFrame,
                 weights: Optional[Dict[str, float]] = None):
        """
        Inicializa motor similitud.

        Parameters:
            embedding_df: DataFrame con [metadata + umap_1, umap_2, ..., umap_n]
            gmm_proba: Matriz probabilidades GMM (n_players, n_clusters)
            feature_df: DataFrame con [metadata + features originales normalizadas]
            weights: Dict pesos componentes score. Default:
                    {'umap_distance': 0.50,
                     'gmm_probability': 0.30,
                     'feature_similarity': 0.20}

        Notes:
            Pesos ajustables según prioridad: si solo interesa estructura UMAP,
            aumentar peso 'umap_distance'. Para priorizar arquetipos GMM,
            aumentar 'gmm_probability'.
        """
        if weights is None:
            self.weights = {
                'umap_distance': 0.50,
                'gmm_probability': 0.30,
                'feature_similarity': 0.20
            }
        else:
            # Validar suma = 1.0
            weight_sum = sum(weights.values())
            if not np.isclose(weight_sum, 1.0):
                raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
            self.weights = weights

        self.embedding_df = embedding_df.reset_index(drop=True)
        self.gmm_proba = gmm_proba
        self.feature_df = feature_df.reset_index(drop=True)

        # Extraer columnas UMAP
        self.umap_cols = [col for col in embedding_df.columns if col.startswith('umap_')]
        self.n_umap_dims = len(self.umap_cols)

        # Crear lookup dict para player_id -> index
        self._player_id_to_idx = {
            pid: idx for idx, pid in enumerate(self.embedding_df['unique_player_id'])
        }

        logger.info(f"PlayerSimilarity initialized: {len(self.embedding_df)} players, "
                   f"{self.n_umap_dims} UMAP dimensions")
        logger.info(f"Score weights: {self.weights}")

    def find_similar_players(self,
                            player_identifier: Union[str, int],
                            top_n: int = 10,
                            filters: Optional[Dict] = None,
                            return_scores: bool = True) -> pd.DataFrame:
        """
        Encuentra jugadores más similares a query player.

        Parameters:
            player_identifier: unique_player_id (str) o índice (int)
            top_n: Número resultados a retornar
            filters: Dict filtros opcionales:
                    - 'exclude_same_team': bool
                    - 'exclude_same_league': bool
                    - 'max_age': int
                    - 'min_age': int
                    - 'position': str (debe empezar con este)
                    - 'leagues': List[str] (solo estas ligas)
            return_scores: Si True, incluye scores detallados en output

        Returns:
            DataFrame con jugadores similares ordenados por score descendente:
                - Columnas metadata (player_name, team, league, position, age)
                - similarity_score: Score combinado (0-1, mayor es más similar)
                - umap_distance: Distancia euclidiana UMAP
                - gmm_similarity: Probabilidad cluster compartido
                - feature_similarity: Similaridad features (opcional)

        Raises:
            ValueError: Si player_identifier no encontrado

        Examples:
            >>> similar = engine.find_similar_players(
            ...     'player_abc123',
            ...     top_n=5,
            ...     filters={'max_age': 26, 'exclude_same_team': True}
            ... )
        """
        # Obtener índice query player
        query_idx = self._get_player_index(player_identifier)

        # Obtener datos query player
        query_embedding = self.embedding_df.loc[query_idx, self.umap_cols].values
        query_gmm_proba = self.gmm_proba[query_idx]

        logger.info(f"Finding similar players to: "
                   f"{self.embedding_df.loc[query_idx, 'player_name']} "
                   f"({self.embedding_df.loc[query_idx, 'team']})")

        # Calcular scores para todos los jugadores
        all_scores = []

        for idx in range(len(self.embedding_df)):
            if idx == query_idx:
                continue  # Skip self

            # 1. UMAP distance score
            candidate_embedding = self.embedding_df.loc[idx, self.umap_cols].values
            umap_dist = euclidean(query_embedding, candidate_embedding)
            # Normalizar a [0,1] y invertir (menor distancia = mayor score)
            # Usa percentil para normalización robusta
            umap_score = 1.0 - (umap_dist / (umap_dist + 1.0))  # Normalización suave

            # 2. GMM probability score
            candidate_gmm_proba = self.gmm_proba[idx]
            # Similaridad = overlap distribuciones (dot product probabilidades)
            gmm_similarity = np.dot(query_gmm_proba, candidate_gmm_proba)

            # 3. Feature similarity score (opcional, si peso > 0)
            if self.weights['feature_similarity'] > 0:
                feature_sim = self._calculate_feature_similarity(query_idx, idx)
            else:
                feature_sim = 0.0

            # 4. Score combinado
            combined_score = (
                self.weights['umap_distance'] * umap_score +
                self.weights['gmm_probability'] * gmm_similarity +
                self.weights['feature_similarity'] * feature_sim
            )

            all_scores.append({
                'idx': idx,
                'similarity_score': combined_score,
                'umap_distance': umap_dist,
                'umap_score': umap_score,
                'gmm_similarity': gmm_similarity,
                'feature_similarity': feature_sim
            })

        # Convertir a DataFrame
        df_scores = pd.DataFrame(all_scores)

        # Merge con metadata
        df_results = pd.merge(
            df_scores,
            self.embedding_df[['unique_player_id', 'player_name', 'team',
                              'league', 'position']],
            left_on='idx',
            right_index=True
        )

        # Aplicar filtros
        if filters:
            df_results = self._apply_filters(df_results, query_idx, filters)

        # Ordenar por score y tomar top_n
        df_results = df_results.sort_values('similarity_score', ascending=False).head(top_n)

        # Limpiar columnas output
        if not return_scores:
            df_results = df_results.drop(columns=['idx', 'umap_score'])

        # Reset index
        df_results = df_results.reset_index(drop=True)

        logger.info(f"Found {len(df_results)} similar players")

        return df_results

    def _get_player_index(self, identifier: Union[str, int]) -> int:
        """Convierte player_identifier a índice."""
        if isinstance(identifier, int):
            if 0 <= identifier < len(self.embedding_df):
                return identifier
            else:
                raise ValueError(f"Index {identifier} out of range")

        elif isinstance(identifier, str):
            if identifier in self._player_id_to_idx:
                return self._player_id_to_idx[identifier]
            else:
                raise ValueError(f"Player ID '{identifier}' not found")

        else:
            raise ValueError(f"Invalid identifier type: {type(identifier)}")

    def _calculate_feature_similarity(self, idx1: int, idx2: int,
                                     top_k_features: int = 20) -> float:
        """
        Calcula similaridad basada en features originales.

        Usa distancia coseno entre top_k features más importantes (mayor varianza).
        """
        # Obtener features (excluir metadata)
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'age', 'is_outlier']
        feature_cols = [col for col in self.feature_df.columns
                       if col not in metadata_cols]

        # Seleccionar top_k features por varianza (más discriminativas)
        if not hasattr(self, '_top_features'):
            # Filtrar solo columnas numéricas
            numeric_feature_cols = self.feature_df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_feature_cols) == 0:
                return 0.0
            variances = self.feature_df[numeric_feature_cols].var()
            self._top_features = variances.nlargest(min(top_k_features, len(numeric_feature_cols))).index.tolist()

        # Vectores features
        vec1 = self.feature_df.loc[idx1, self._top_features].values
        vec2 = self.feature_df.loc[idx2, self._top_features].values

        # Convertir a float y manejar NaN
        vec1 = pd.to_numeric(vec1, errors='coerce')
        vec2 = pd.to_numeric(vec2, errors='coerce')
        mask = ~(np.isnan(vec1) | np.isnan(vec2))
        if mask.sum() < 5:  # Muy pocos features válidos
            return 0.0

        vec1_clean = vec1[mask]
        vec2_clean = vec2[mask]

        # Similaridad coseno (1 - distancia)
        cos_dist = cosine(vec1_clean, vec2_clean)
        cos_sim = 1.0 - cos_dist

        return cos_sim

    def _apply_filters(self,
                      df: pd.DataFrame,
                      query_idx: int,
                      filters: Dict) -> pd.DataFrame:
        """Aplica filtros contextuales a resultados."""
        query_team = self.embedding_df.loc[query_idx, 'team']
        query_league = self.embedding_df.loc[query_idx, 'league']

        if filters.get('exclude_same_team', False):
            df = df[df['team'] != query_team]
            logger.debug(f"Filtered same team: {len(df)} remaining")

        if filters.get('exclude_same_league', False):
            df = df[df['league'] != query_league]
            logger.debug(f"Filtered same league: {len(df)} remaining")

        if 'max_age' in filters:
            # Nota: age puede no estar en embedding_df, verificar
            if 'age' in df.columns:
                df = df[pd.to_numeric(df['age'], errors='coerce') <= filters['max_age']]

        if 'min_age' in filters:
            if 'age' in df.columns:
                df = df[pd.to_numeric(df['age'], errors='coerce') >= filters['min_age']]

        if 'position' in filters:
            df = df[df['position'].str.startswith(filters['position'])]
            logger.debug(f"Filtered position {filters['position']}: {len(df)} remaining")

        if 'leagues' in filters:
            df = df[df['league'].isin(filters['leagues'])]
            logger.debug(f"Filtered leagues: {len(df)} remaining")

        return df

    def validate_replacement_chain(self,
                                  player_identifiers: List[Union[str, int]],
                                  min_similarity: float = 0.6) -> pd.DataFrame:
        """
        Valida cadena de reemplazos (ej: Sørloth -> Jackson -> Next).

        Parameters:
            player_identifiers: Lista IDs jugadores en orden cadena
            min_similarity: Threshold similaridad mínima aceptable

        Returns:
            DataFrame con validación:
                - player_1, player_2: Par jugadores
                - similarity_score: Score similitud
                - is_valid: bool (score >= min_similarity)
                - notes: Observaciones

        Examples:
            >>> chain = engine.validate_replacement_chain(
            ...     ['sorloth_id', 'jackson_id', 'candidate_id'],
            ...     min_similarity=0.65
            ... )
        """
        logger.info(f"Validating replacement chain of {len(player_identifiers)} players...")

        if len(player_identifiers) < 2:
            raise ValueError("Need at least 2 players for chain validation")

        results = []

        for i in range(len(player_identifiers) - 1):
            player1_id = player_identifiers[i]
            player2_id = player_identifiers[i + 1]

            # Obtener índices
            idx1 = self._get_player_index(player1_id)
            idx2 = self._get_player_index(player2_id)

            # Calcular similaridad
            player1_name = self.embedding_df.loc[idx1, 'player_name']
            player2_name = self.embedding_df.loc[idx2, 'player_name']

            # Buscar player2 en similares de player1
            similar_df = self.find_similar_players(player1_id, top_n=50, return_scores=True)

            # Encontrar player2 en resultados
            match = similar_df[similar_df['unique_player_id'] ==
                             self.embedding_df.loc[idx2, 'unique_player_id']]

            if len(match) > 0:
                score = match.iloc[0]['similarity_score']
                rank = match.index[0] + 1
            else:
                # Player2 no está en top 50
                score = 0.0
                rank = np.nan

            is_valid = score >= min_similarity

            notes = []
            if is_valid:
                notes.append(f"Valid replacement (rank {rank})")
            else:
                notes.append(f"Low similarity (below threshold {min_similarity})")

            results.append({
                'player_1': player1_name,
                'player_2': player2_name,
                'player_1_id': self.embedding_df.loc[idx1, 'unique_player_id'],
                'player_2_id': self.embedding_df.loc[idx2, 'unique_player_id'],
                'similarity_score': score,
                'rank_in_top50': rank,
                'is_valid': is_valid,
                'notes': '; '.join(notes)
            })

        df_validation = pd.DataFrame(results)

        n_valid = df_validation['is_valid'].sum()
        logger.info(f"Chain validation complete: {n_valid}/{len(df_validation)} links valid")

        return df_validation

    def get_similarity_matrix(self,
                             player_identifiers: List[Union[str, int]],
                             normalize: bool = True) -> Tuple[np.ndarray, List[str]]:
        """
        Calcula matriz similaridad NxN entre lista jugadores.

        Parameters:
            player_identifiers: Lista IDs jugadores
            normalize: Si True, normaliza scores a [0,1]

        Returns:
            Tuple (similarity_matrix, player_names)
            - similarity_matrix: Array (N, N) con scores
            - player_names: Lista nombres jugadores (orden matriz)

        Notes:
            Útil para análisis clusters múltiples jugadores o visualización heatmap.
        """
        logger.info(f"Computing similarity matrix for {len(player_identifiers)} players...")

        n = len(player_identifiers)
        indices = [self._get_player_index(pid) for pid in player_identifiers]
        player_names = [self.embedding_df.loc[idx, 'player_name'] for idx in indices]

        # Inicializar matriz
        sim_matrix = np.zeros((n, n))

        # Calcular similaridades pairwise
        for i in range(n):
            for j in range(n):
                if i == j:
                    sim_matrix[i, j] = 1.0  # Self-similarity
                elif i < j:  # Solo calcular triángulo superior
                    idx1, idx2 = indices[i], indices[j]

                    # UMAP distance
                    emb1 = self.embedding_df.loc[idx1, self.umap_cols].values
                    emb2 = self.embedding_df.loc[idx2, self.umap_cols].values
                    umap_dist = euclidean(emb1, emb2)
                    umap_score = 1.0 - (umap_dist / (umap_dist + 1.0))

                    # GMM similarity
                    gmm1 = self.gmm_proba[idx1]
                    gmm2 = self.gmm_proba[idx2]
                    gmm_sim = np.dot(gmm1, gmm2)

                    # Feature similarity
                    if self.weights['feature_similarity'] > 0:
                        feat_sim = self._calculate_feature_similarity(idx1, idx2)
                    else:
                        feat_sim = 0.0

                    # Combinar
                    score = (
                        self.weights['umap_distance'] * umap_score +
                        self.weights['gmm_probability'] * gmm_sim +
                        self.weights['feature_similarity'] * feat_sim
                    )

                    sim_matrix[i, j] = score
                    sim_matrix[j, i] = score  # Simetría

        if normalize:
            # Normalizar a [0,1] (diagonal ya es 1.0)
            sim_matrix = (sim_matrix - sim_matrix.min()) / (sim_matrix.max() - sim_matrix.min() + 1e-10)

        logger.info(f"Similarity matrix computed: shape {sim_matrix.shape}")

        return sim_matrix, player_names

    def find_cluster_representatives(self,
                                    cluster_id: int,
                                    n_representatives: int = 5) -> pd.DataFrame:
        """
        Encuentra jugadores más representativos de un cluster (arquetipo).

        Parameters:
            cluster_id: ID cluster GMM
            n_representatives: Número representantes a retornar

        Returns:
            DataFrame con jugadores más centrados en cluster:
                - Metadata jugadores
                - cluster_probability: Probabilidad pertenecer a cluster
                - distance_to_center: Distancia a centro cluster en UMAP

        Notes:
            Útil para interpretar arquetipos identificando ejemplos prototípicos.
        """
        logger.info(f"Finding representatives for cluster {cluster_id}...")

        # Jugadores en este cluster
        mask = np.argmax(self.gmm_proba, axis=1) == cluster_id
        indices = np.where(mask)[0]

        if len(indices) == 0:
            logger.warning(f"Cluster {cluster_id} is empty")
            return pd.DataFrame()

        # Probabilidades cluster
        cluster_probas = self.gmm_proba[indices, cluster_id]

        # Centro cluster en UMAP (promedio)
        embeddings_cluster = self.embedding_df.loc[indices, self.umap_cols].values
        cluster_center = embeddings_cluster.mean(axis=0)

        # Distancias a centro
        distances = [euclidean(emb, cluster_center) for emb in embeddings_cluster]

        # Score combinado: alta probabilidad + cerca del centro
        scores = cluster_probas * (1.0 / (1.0 + np.array(distances)))

        # Top n_representatives
        top_indices = indices[np.argsort(scores)[-n_representatives:][::-1]]

        # Crear DataFrame resultado
        df_result = self.embedding_df.loc[top_indices].copy()
        df_result['cluster_probability'] = self.gmm_proba[top_indices, cluster_id]
        df_result['distance_to_center'] = [euclidean(
            self.embedding_df.loc[idx, self.umap_cols].values, cluster_center
        ) for idx in top_indices]

        df_result = df_result.reset_index(drop=True)

        logger.info(f"Found {len(df_result)} representatives for cluster {cluster_id}")

        return df_result

    def explain_similarity(self,
                          player1_identifier: Union[str, int],
                          player2_identifier: Union[str, int],
                          top_features: int = 10) -> Dict:
        """
        Explica por qué dos jugadores son similares (interpretabilidad).

        Parameters:
            player1_identifier, player2_identifier: IDs jugadores
            top_features: Top features a mostrar

        Returns:
            Dict con explicación:
                - overall_score: Score similaridad total
                - component_scores: Dict scores por componente
                - common_cluster: Cluster compartido (si existe)
                - top_similar_features: Features con valores similares
                - top_different_features: Features con valores diferentes

        Notes:
            Crítico para interpretabilidad y validación manual resultados.
        """
        idx1 = self._get_player_index(player1_identifier)
        idx2 = self._get_player_index(player2_identifier)

        name1 = self.embedding_df.loc[idx1, 'player_name']
        name2 = self.embedding_df.loc[idx2, 'player_name']

        logger.info(f"Explaining similarity: {name1} vs {name2}")

        # Scores componentes
        emb1 = self.embedding_df.loc[idx1, self.umap_cols].values
        emb2 = self.embedding_df.loc[idx2, self.umap_cols].values
        umap_dist = euclidean(emb1, emb2)
        umap_score = 1.0 - (umap_dist / (umap_dist + 1.0))

        gmm1 = self.gmm_proba[idx1]
        gmm2 = self.gmm_proba[idx2]
        gmm_sim = np.dot(gmm1, gmm2)

        feat_sim = self._calculate_feature_similarity(idx1, idx2)

        overall_score = (
            self.weights['umap_distance'] * umap_score +
            self.weights['gmm_probability'] * gmm_sim +
            self.weights['feature_similarity'] * feat_sim
        )

        # Cluster compartido
        cluster1 = np.argmax(gmm1)
        cluster2 = np.argmax(gmm2)
        common_cluster = cluster1 if cluster1 == cluster2 else None

        # Análisis features
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'age', 'is_outlier']
        feature_cols = [col for col in self.feature_df.columns
                       if col not in metadata_cols]

        vec1 = self.feature_df.loc[idx1, feature_cols].values
        vec2 = self.feature_df.loc[idx2, feature_cols].values

        # Diferencias absolutas
        diffs = np.abs(vec1 - vec2)
        valid_mask = ~(np.isnan(diffs))

        # Top similares (menor diferencia)
        similar_indices = np.argsort(diffs[valid_mask])[:top_features]
        similar_features = [feature_cols[i] for i in np.where(valid_mask)[0][similar_indices]]

        # Top diferentes (mayor diferencia)
        different_indices = np.argsort(diffs[valid_mask])[-top_features:][::-1]
        different_features = [feature_cols[i] for i in np.where(valid_mask)[0][different_indices]]

        explanation = {
            'player_1': name1,
            'player_2': name2,
            'overall_score': overall_score,
            'component_scores': {
                'umap_distance_score': umap_score,
                'gmm_similarity_score': gmm_sim,
                'feature_similarity_score': feat_sim
            },
            'common_cluster': common_cluster,
            'cluster_1': cluster1,
            'cluster_2': cluster2,
            'top_similar_features': similar_features,
            'top_different_features': different_features
        }

        return explanation
