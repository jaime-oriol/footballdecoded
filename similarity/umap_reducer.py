"""
UMAP Dimensionality Reduction Module

Reduce dimensionalidad 220+ features a espacio 2-10D preservando estructura
local y global. Base para clustering GMM posterior.

Basado en:
    - McInnes et al. (2018): UMAP: Uniform Manifold Approximation and Projection
    - Becht et al. (2019): Dimensionality reduction for visualizing single-cell data
    - Ventaja sobre t-SNE: preserva estructura global, más rápido, permite inverse_transform

Clase principal:
    UMAPReducer: Reducción dimensional optimizada para datos fútbol
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List
import logging
from sklearn.model_selection import ParameterGrid

try:
    from umap import UMAP
except ImportError:
    raise ImportError("UMAP not installed. Run: pip install umap-learn")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UMAPReducer:
    """
    Reducción dimensional usando UMAP para player similarity.

    UMAP (Uniform Manifold Approximation and Projection) es superior a PCA/t-SNE para:
        - Preserva estructura local Y global (PCA solo global, t-SNE solo local)
        - Más rápido que t-SNE en datasets grandes
        - Permite aproximar inverse_transform para interpretabilidad
        - Mejor separación clusters para GMM posterior

    Workflow:
        1. Fit UMAP en feature matrix normalizada
        2. Transform a espacio reducido (2-10D típicamente)
        3. Validar estabilidad embedding (multiple runs)
        4. Optimizar hiperparámetros vía grid search (opcional)

    Attributes:
        n_components: Dimensiones output (2-10 recomendado)
        n_neighbors: Balance local/global structure (15-30 típico)
        min_dist: Compactness clusters (0.0-0.1 típico)
        model: Instancia UMAP fitted
        embedding: Array embeding resultante
    """

    def __init__(self,
                 n_components: int = 5,
                 n_neighbors: int = 15,
                 min_dist: float = 0.1,
                 metric: str = 'euclidean',
                 random_state: int = 42):
        """
        Inicializa UMAP reducer.

        Parameters:
            n_components: Dimensiones output embedding
                         2-3 -> Visualización
                         5-10 -> Clustering (mejor balance información/ruido)
            n_neighbors: Tamaño vecindario local
                        Menor (5-10) -> Preserva estructura local fina
                        Mayor (30-50) -> Captura más estructura global
                        15-30 -> Balance óptimo para fútbol
            min_dist: Distancia mínima entre puntos en embedding
                     0.0 -> Clusters muy compactos (recomendado clustering)
                     0.1-0.3 -> Más dispersión (mejor visualización)
            metric: Métrica distancia
                   'euclidean' -> Default, funciona bien con features normalizadas
                   'manhattan', 'cosine' -> Alternativas
            random_state: Seed reproducibilidad

        Notes:
            Hiperparámetros basados en análisis empírico datasets similares
            (Becht et al., 2019 + testing interno)
        """
        if n_components < 2:
            raise ValueError("n_components must be >= 2")
        if n_neighbors < 2:
            raise ValueError("n_neighbors must be >= 2")
        if not 0.0 <= min_dist <= 1.0:
            raise ValueError("min_dist must be in [0.0, 1.0]")

        self.n_components = n_components
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.metric = metric
        self.random_state = random_state

        self.model = None
        self.embedding = None
        self._fitted = False

        logger.info(f"UMAPReducer initialized: n_components={n_components}, "
                   f"n_neighbors={n_neighbors}, min_dist={min_dist}")

    def fit_transform(self, X: np.ndarray, verbose: bool = True) -> np.ndarray:
        """
        Fit UMAP y transforma datos a espacio reducido.

        Parameters:
            X: Feature matrix (n_samples, n_features)
            verbose: Si True, imprime progreso

        Returns:
            Embedding array (n_samples, n_components)

        Notes:
            Complejidad O(n_samples^1.14) aprox, mucho más rápido que t-SNE O(n^2)
        """
        logger.info(f"Fitting UMAP on {X.shape[0]} samples, {X.shape[1]} features...")

        self.model = UMAP(
            n_components=self.n_components,
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            metric=self.metric,
            random_state=self.random_state,
            verbose=verbose
        )

        self.embedding = self.model.fit_transform(X)
        self._fitted = True

        logger.info(f"UMAP fitting complete. Output shape: {self.embedding.shape}")

        return self.embedding

    def transform(self, X_new: np.ndarray) -> np.ndarray:
        """
        Transforma nuevos datos usando UMAP ya fitted.

        Parameters:
            X_new: Nuevos datos (n_samples_new, n_features)

        Returns:
            Embedding para nuevos datos

        Notes:
            UMAP permite transform de nuevos puntos sin refit completo.
            Útil para añadir jugadores nuevos al espacio existente.
        """
        if not self._fitted:
            raise ValueError("Must call fit_transform() before transform()")

        logger.info(f"Transforming {X_new.shape[0]} new samples...")

        embedding_new = self.model.transform(X_new)

        logger.info(f"Transform complete. Output shape: {embedding_new.shape}")

        return embedding_new

    def inverse_transform(self, X_embedding: np.ndarray) -> np.ndarray:
        """
        Aproxima inverse transform desde espacio reducido a original.

        Parameters:
            X_embedding: Puntos en espacio reducido (n_samples, n_components)

        Returns:
            Aproximación en espacio original (n_samples, n_features)

        Notes:
            UMAP inverse_transform es aproximación (no exacto).
            Útil para interpretar qué features caracterizan zonas del embedding.
        """
        if not self._fitted:
            raise ValueError("Must call fit_transform() before inverse_transform()")

        logger.info(f"Inverse transforming {X_embedding.shape[0]} samples...")

        X_reconstructed = self.model.inverse_transform(X_embedding)

        logger.info(f"Inverse transform complete. Output shape: {X_reconstructed.shape}")

        return X_reconstructed

    def validate_embedding_stability(self,
                                    X: np.ndarray,
                                    n_runs: int = 10,
                                    metric: str = 'correlation') -> Dict[str, float]:
        """
        Valida estabilidad embedding mediante múltiples runs.

        Parameters:
            X: Feature matrix original
            n_runs: Número runs con diferentes random seeds
            metric: Métrica estabilidad
                   'correlation' -> Correlación Pearson entre embeddings
                   'procrustes' -> Procrustes distance (alineación óptima)

        Returns:
            Dict con estadísticas estabilidad:
                - mean_similarity: Media similaridad entre runs
                - std_similarity: Std similaridad
                - min_similarity: Mínima similaridad observada

        Notes:
            Embeddings inestables (mean < 0.7) sugieren hiperparámetros inadecuados
            o datos insuficientes. Basado en Becht et al. (2019).
        """
        logger.info(f"Validating embedding stability with {n_runs} runs...")

        embeddings = []

        for i in range(n_runs):
            model_temp = UMAP(
                n_components=self.n_components,
                n_neighbors=self.n_neighbors,
                min_dist=self.min_dist,
                metric=self.metric,
                random_state=self.random_state + i,
                verbose=False
            )
            embedding_temp = model_temp.fit_transform(X)
            embeddings.append(embedding_temp)

        # Calcular similaridad pairwise
        similarities = []

        if metric == 'correlation':
            # Correlación Pearson entre embeddings
            for i in range(n_runs):
                for j in range(i+1, n_runs):
                    # Flatten y correlacionar
                    emb_i = embeddings[i].flatten()
                    emb_j = embeddings[j].flatten()
                    corr = np.corrcoef(emb_i, emb_j)[0, 1]
                    similarities.append(corr)

        elif metric == 'procrustes':
            # Procrustes distance (requiere alineación óptima)
            from scipy.spatial import procrustes

            for i in range(n_runs):
                for j in range(i+1, n_runs):
                    _, _, disparity = procrustes(embeddings[i], embeddings[j])
                    # Convertir disparidad a similaridad (1 - disparity)
                    similarities.append(1.0 - disparity)

        else:
            raise ValueError(f"Unknown stability metric: {metric}")

        results = {
            'mean_similarity': np.mean(similarities),
            'std_similarity': np.std(similarities),
            'min_similarity': np.min(similarities),
            'max_similarity': np.max(similarities),
            'n_runs': n_runs
        }

        logger.info(f"Stability validation complete: mean={results['mean_similarity']:.3f}, "
                   f"std={results['std_similarity']:.3f}")

        if results['mean_similarity'] < 0.7:
            logger.warning("Low embedding stability detected. Consider adjusting hyperparameters.")

        return results

    def optimize_hyperparameters(self,
                                X: np.ndarray,
                                param_grid: Optional[Dict] = None,
                                n_runs_per_config: int = 3) -> Dict:
        """
        Optimiza hiperparámetros UMAP via grid search.

        Parameters:
            X: Feature matrix
            param_grid: Dict con ranges a explorar. Si None, usa default.
                       Ejemplo: {
                           'n_neighbors': [10, 15, 30],
                           'min_dist': [0.0, 0.1, 0.3],
                           'n_components': [5, 10]
                       }
            n_runs_per_config: Runs por config para estabilidad

        Returns:
            Dict con mejores parámetros y resultados:
                - best_params: Mejores hiperparámetros
                - best_stability: Estabilidad de mejores params
                - all_results: Lista resultados todas configs

        Notes:
            Grid search costoso computacionalmente. Para datasets grandes,
            usar subset aleatorio para optimización.
        """
        logger.info("Starting hyperparameter optimization...")

        if param_grid is None:
            param_grid = {
                'n_neighbors': [15, 20, 30],
                'min_dist': [0.0, 0.1],
                'n_components': [5, 7, 10]
            }

        grid = ParameterGrid(param_grid)
        results = []

        for i, params in enumerate(grid):
            logger.info(f"Testing config {i+1}/{len(grid)}: {params}")

            # Crear reducer temporal
            reducer_temp = UMAPReducer(
                n_components=params.get('n_components', self.n_components),
                n_neighbors=params.get('n_neighbors', self.n_neighbors),
                min_dist=params.get('min_dist', self.min_dist),
                metric=self.metric,
                random_state=self.random_state
            )

            # Validar estabilidad
            stability = reducer_temp.validate_embedding_stability(
                X, n_runs=n_runs_per_config
            )

            results.append({
                'params': params,
                'stability_mean': stability['mean_similarity'],
                'stability_std': stability['std_similarity']
            })

        # Encontrar mejor config (mayor estabilidad)
        best_idx = np.argmax([r['stability_mean'] for r in results])
        best_result = results[best_idx]

        logger.info(f"Best parameters: {best_result['params']}")
        logger.info(f"Best stability: {best_result['stability_mean']:.3f}")

        # Actualizar parámetros de esta instancia
        self.n_components = best_result['params'].get('n_components', self.n_components)
        self.n_neighbors = best_result['params'].get('n_neighbors', self.n_neighbors)
        self.min_dist = best_result['params'].get('min_dist', self.min_dist)

        return {
            'best_params': best_result['params'],
            'best_stability': best_result['stability_mean'],
            'all_results': results
        }

    def get_embedding_dataframe(self, metadata_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte embedding a DataFrame con metadata.

        Parameters:
            metadata_df: DataFrame con columnas metadata (player_name, team, etc.)

        Returns:
            DataFrame con columnas: [metadata cols] + [umap_1, umap_2, ..., umap_n]

        Notes:
            Útil para análisis y visualización posterior.
        """
        if not self._fitted:
            raise ValueError("Must call fit_transform() before get_embedding_dataframe()")

        # Crear columnas UMAP
        umap_cols = [f'umap_{i+1}' for i in range(self.n_components)]
        embedding_df = pd.DataFrame(self.embedding, columns=umap_cols)

        # Resetear index metadata para concatenar
        metadata_df = metadata_df.reset_index(drop=True)

        # Concatenar
        result_df = pd.concat([metadata_df, embedding_df], axis=1)

        logger.info(f"Created embedding DataFrame with shape {result_df.shape}")

        return result_df

    def get_feature_contribution(self,
                                X_original: np.ndarray,
                                feature_names: List[str],
                                component_idx: int = 0) -> pd.Series:
        """
        Estima contribución de features originales a componente UMAP.

        Parameters:
            X_original: Feature matrix original (n_samples, n_features)
            feature_names: Nombres features originales
            component_idx: Índice componente UMAP a analizar (0-indexed)

        Returns:
            Series con correlaciones feature -> componente (ordenado desc)

        Notes:
            UMAP no tiene loadings explícitos como PCA. Esta función calcula
            correlación Pearson entre cada feature original y componente UMAP
            como proxy de importancia.
        """
        if not self._fitted:
            raise ValueError("Must call fit_transform() first")

        if component_idx >= self.n_components:
            raise ValueError(f"component_idx must be < {self.n_components}")

        logger.info(f"Computing feature contributions to UMAP component {component_idx+1}...")

        # Obtener componente UMAP específica
        umap_component = self.embedding[:, component_idx]

        # Calcular correlación con cada feature original
        correlations = []
        for i in range(X_original.shape[1]):
            feature_vals = X_original[:, i]
            corr = np.corrcoef(feature_vals, umap_component)[0, 1]
            correlations.append(corr)

        # Crear Series
        contrib_series = pd.Series(correlations, index=feature_names)
        contrib_series = contrib_series.abs().sort_values(ascending=False)

        logger.info(f"Top 5 contributing features: {list(contrib_series.index[:5])}")

        return contrib_series

    def save_model(self, filepath: str):
        """
        Guarda modelo UMAP fitted.

        Parameters:
            filepath: Path archivo output (.pkl)
        """
        if not self._fitted:
            raise ValueError("Must fit model before saving")

        import pickle

        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'embedding': self.embedding,
                'params': {
                    'n_components': self.n_components,
                    'n_neighbors': self.n_neighbors,
                    'min_dist': self.min_dist,
                    'metric': self.metric
                }
            }, f)

        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load_model(cls, filepath: str) -> 'UMAPReducer':
        """
        Carga modelo UMAP desde archivo.

        Parameters:
            filepath: Path archivo input (.pkl)

        Returns:
            Instancia UMAPReducer con modelo loaded
        """
        import pickle

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        reducer = cls(
            n_components=data['params']['n_components'],
            n_neighbors=data['params']['n_neighbors'],
            min_dist=data['params']['min_dist'],
            metric=data['params']['metric']
        )

        reducer.model = data['model']
        reducer.embedding = data['embedding']
        reducer._fitted = True

        logger.info(f"Model loaded from {filepath}")

        return reducer
