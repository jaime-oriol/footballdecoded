"""
GMM Clustering Module

Clustering probabilístico usando Gaussian Mixture Models sobre embedding UMAP.
Identifica arquetipos de jugadores y asigna probabilidades (no labels hard).

Basado en:
    - Schwarz (1978): Estimating the dimension of a model (BIC criterion)
    - Fraley & Raftery (2002): Model-Based Clustering
    - Pappalardo et al. (2019): PlayeRank player role classification

Ventajas GMM vs K-Means:
    - Probabilidades soft (no asignación binaria)
    - Maneja clusters elípticos (K-Means solo esféricos)
    - Selección automática n_clusters via BIC/AIC

Clase principal:
    GMMClusterer: Clustering probabilístico optimizado para player archetypes
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GMMClusterer:
    """
    Clustering probabilístico GMM para identificar arquetipos jugadores.

    GMM modela datos como mezcla de distribuciones Gaussianas. Para cada jugador,
    retorna probabilidad de pertenecer a cada cluster (arquetipo).

    Workflow:
        1. Encuentra número óptimo clusters via BIC/AIC
        2. Fit GMM con parámetros óptimos
        3. Asigna probabilidades a cada jugador
        4. Caracteriza arquetipos via medias clusters
        5. Valida estabilidad clustering (bootstrap)

    Attributes:
        n_components: Número clusters (arquetipos)
        covariance_type: Tipo matriz covarianza
        model: Instancia GaussianMixture fitted
        labels_hard: Cluster asignado (max probability)
        labels_proba: Matriz probabilidades (n_samples, n_clusters)
    """

    def __init__(self,
                 n_components: Optional[int] = None,
                 covariance_type: str = 'full',
                 max_iter: int = 200,
                 random_state: int = 42):
        """
        Inicializa GMM clusterer.

        Parameters:
            n_components: Número clusters. Si None, se optimiza automáticamente.
            covariance_type: Tipo covarianza
                            'full' -> Cada cluster tiene covarianza propia (más flexible)
                            'tied' -> Todos clusters comparten covarianza
                            'diag' -> Covarianzas diagonales (asume features independientes)
                            'spherical' -> Varianza igual todas dimensiones (más simple)
            max_iter: Máximo iteraciones EM algorithm
            random_state: Seed reproducibilidad

        Notes:
            'full' recomendado para datasets medianos/grandes (>500 samples).
            'tied'/'diag' si pocos datos o problemas convergencia.
        """
        valid_cov_types = ['full', 'tied', 'diag', 'spherical']
        if covariance_type not in valid_cov_types:
            raise ValueError(f"covariance_type must be one of {valid_cov_types}")

        self.n_components = n_components
        self.covariance_type = covariance_type
        self.max_iter = max_iter
        self.random_state = random_state

        self.model = None
        self.labels_hard = None
        self.labels_proba = None
        self._fitted = False

        logger.info(f"GMMClusterer initialized with covariance_type={covariance_type}")

    def find_optimal_clusters(self,
                             X: np.ndarray,
                             min_clusters: int = 2,
                             max_clusters: int = 20,
                             criterion: str = 'bic') -> Dict:
        """
        Encuentra número óptimo clusters usando BIC o AIC.

        Parameters:
            X: Embedding UMAP (n_samples, n_components)
            min_clusters: Mínimo clusters a probar
            max_clusters: Máximo clusters a probar
            criterion: Criterio selección
                      'bic' -> Bayesian Information Criterion (penaliza complejidad más)
                      'aic' -> Akaike Information Criterion (menos penalización)
                      'silhouette' -> Silhouette score (geométrico)

        Returns:
            Dict con resultados:
                - optimal_n: Número óptimo clusters
                - scores: Lista scores por cada n_clusters
                - all_models: Dict modelos fitted por n_clusters

        Notes:
            BIC preferido sobre AIC para evitar overfitting (Schwarz, 1978).
            BIC más conservador, típicamente selecciona menos clusters.
        """
        logger.info(f"Finding optimal clusters using {criterion} criterion...")
        logger.info(f"Testing range: {min_clusters} to {max_clusters} clusters")

        if X.shape[0] < min_clusters:
            raise ValueError(f"Need at least {min_clusters} samples")

        scores = []
        models = {}

        for n in range(min_clusters, max_clusters + 1):
            try:
                model = GaussianMixture(
                    n_components=n,
                    covariance_type=self.covariance_type,
                    max_iter=self.max_iter,
                    random_state=self.random_state,
                    verbose=0
                )

                model.fit(X)

                if criterion == 'bic':
                    score = model.bic(X)
                    # BIC: menor es mejor
                elif criterion == 'aic':
                    score = model.aic(X)
                    # AIC: menor es mejor
                elif criterion == 'silhouette':
                    labels = model.predict(X)
                    score = silhouette_score(X, labels)
                    # Silhouette: mayor es mejor
                    score = -score  # Invertir para mantener lógica "menor mejor"
                else:
                    raise ValueError(f"Unknown criterion: {criterion}")

                scores.append(score)
                models[n] = model

                logger.debug(f"n_clusters={n}: {criterion}={score:.2f}")

            except Exception as e:
                logger.warning(f"Failed to fit n_clusters={n}: {e}")
                scores.append(np.inf)

        # Encontrar óptimo (mínimo score)
        optimal_idx = np.argmin(scores)
        optimal_n = min_clusters + optimal_idx

        logger.info(f"Optimal number of clusters: {optimal_n}")
        logger.info(f"Optimal {criterion} score: {scores[optimal_idx]:.2f}")

        # Calcular elbow sharpness (para BIC/AIC)
        if criterion in ['bic', 'aic']:
            # Buscar "codo" en curva
            scores_norm = (scores - np.min(scores)) / (np.max(scores) - np.min(scores) + 1e-10)
            diffs = np.diff(scores_norm)
            elbow_sharpness = np.abs(diffs).max()
            logger.info(f"Elbow sharpness: {elbow_sharpness:.3f}")

        return {
            'optimal_n': optimal_n,
            'scores': scores,
            'all_models': models,
            'criterion': criterion
        }

    def fit(self, X: np.ndarray, n_components: Optional[int] = None) -> 'GMMClusterer':
        """
        Fit GMM en datos.

        Parameters:
            X: Embedding UMAP (n_samples, n_components_umap)
            n_components: Número clusters. Si None, usa self.n_components.

        Returns:
            self (fitted)

        Raises:
            ValueError: Si n_components no especificado
        """
        if n_components is None and self.n_components is None:
            raise ValueError("Must specify n_components or call find_optimal_clusters() first")

        n_comp = n_components if n_components else self.n_components

        logger.info(f"Fitting GMM with {n_comp} components on {X.shape[0]} samples...")

        self.model = GaussianMixture(
            n_components=n_comp,
            covariance_type=self.covariance_type,
            max_iter=self.max_iter,
            random_state=self.random_state,
            verbose=1
        )

        self.model.fit(X)

        # Asignaciones
        self.labels_proba = self.model.predict_proba(X)
        self.labels_hard = self.model.predict(X)

        self.n_components = n_comp
        self._fitted = True

        logger.info(f"GMM fitting complete. Converged: {self.model.converged_}")
        logger.info(f"Cluster sizes: {np.bincount(self.labels_hard)}")

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predice probabilidades cluster para nuevos datos.

        Parameters:
            X: Nuevos datos embedding UMAP

        Returns:
            Matriz probabilidades (n_samples, n_clusters)
        """
        if not self._fitted:
            raise ValueError("Must call fit() before predict_proba()")

        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predice cluster hard assignment (max probability) para nuevos datos.

        Parameters:
            X: Nuevos datos embedding UMAP

        Returns:
            Array labels cluster (n_samples,)
        """
        if not self._fitted:
            raise ValueError("Must call fit() before predict()")

        return self.model.predict(X)

    def get_cluster_profiles(self,
                            X_original: np.ndarray,
                            feature_names: List[str],
                            top_n_features: int = 10) -> pd.DataFrame:
        """
        Caracteriza cada cluster (arquetipo) via features originales.

        Parameters:
            X_original: Feature matrix original (pre-UMAP) normalizada
            feature_names: Nombres features originales
            top_n_features: Top features a mostrar por cluster

        Returns:
            DataFrame con perfiles clusters:
                - Columnas: cluster_id, feature, mean_value, std_value, percentile
                - Ordenado por importancia relativa

        Notes:
            Análisis crítico para interpretar arquetipos. Identifica qué features
            caracterizan cada tipo de jugador.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")

        logger.info(f"Computing cluster profiles for {self.n_components} clusters...")

        profiles = []

        for cluster_id in range(self.n_components):
            # Jugadores en este cluster
            mask = self.labels_hard == cluster_id
            X_cluster = X_original[mask]

            if len(X_cluster) == 0:
                logger.warning(f"Cluster {cluster_id} is empty")
                continue

            # Calcular estadísticas por feature
            means = X_cluster.mean(axis=0)
            stds = X_cluster.std(axis=0)

            # Z-scores relativos a población total (identifica features distintivas)
            global_means = X_original.mean(axis=0)
            global_stds = X_original.std(axis=0)
            z_scores = (means - global_means) / (global_stds + 1e-10)

            # Top features por |z_score|
            top_indices = np.argsort(np.abs(z_scores))[-top_n_features:][::-1]

            for idx in top_indices:
                profiles.append({
                    'cluster_id': cluster_id,
                    'cluster_size': mask.sum(),
                    'feature': feature_names[idx],
                    'mean_value': means[idx],
                    'std_value': stds[idx],
                    'z_score': z_scores[idx],
                    'rank': len(profiles) % top_n_features + 1
                })

        df_profiles = pd.DataFrame(profiles)

        logger.info(f"Cluster profiles computed. Total rows: {len(df_profiles)}")

        return df_profiles

    def cluster_stability(self,
                         X: np.ndarray,
                         n_runs: int = 50,
                         subsample_frac: float = 0.8) -> Dict[str, float]:
        """
        Valida estabilidad clustering via bootstrap.

        Parameters:
            X: Embedding UMAP
            n_runs: Número runs bootstrap
            subsample_frac: Fracción samples por run (0-1)

        Returns:
            Dict con métricas estabilidad:
                - mean_ari: Adjusted Rand Index medio entre runs
                - std_ari: Std ARI
                - mean_convergence: % runs que convergieron

        Notes:
            ARI (Adjusted Rand Index) mide similaridad entre clusterings.
            ARI > 0.7 indica clustering estable (Vinh et al., 2010).
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")

        logger.info(f"Validating cluster stability with {n_runs} bootstrap runs...")

        from sklearn.metrics import adjusted_rand_score
        from sklearn.utils import resample

        aris = []
        convergence_count = 0

        for i in range(n_runs):
            # Bootstrap sample
            n_samples = int(X.shape[0] * subsample_frac)
            X_boot, indices = resample(X, np.arange(X.shape[0]),
                                      n_samples=n_samples,
                                      random_state=self.random_state + i,
                                      replace=True)

            # Fit GMM en bootstrap
            model_boot = GaussianMixture(
                n_components=self.n_components,
                covariance_type=self.covariance_type,
                max_iter=self.max_iter,
                random_state=self.random_state + i,
                verbose=0
            )

            try:
                model_boot.fit(X_boot)

                if model_boot.converged_:
                    convergence_count += 1

                # Predecir en samples bootstrap
                labels_boot = model_boot.predict(X[indices])

                # Comparar con labels originales
                labels_original = self.labels_hard[indices]

                # Calcular ARI
                ari = adjusted_rand_score(labels_original, labels_boot)
                aris.append(ari)

            except Exception as e:
                logger.warning(f"Bootstrap run {i+1} failed: {e}")

        results = {
            'mean_ari': np.mean(aris),
            'std_ari': np.std(aris),
            'min_ari': np.min(aris),
            'max_ari': np.max(aris),
            'convergence_rate': convergence_count / n_runs,
            'n_runs': n_runs
        }

        logger.info(f"Stability validation complete: mean_ARI={results['mean_ari']:.3f}, "
                   f"convergence_rate={results['convergence_rate']:.2f}")

        if results['mean_ari'] < 0.7:
            logger.warning("Low clustering stability detected. Results may be unreliable.")

        return results

    def get_cluster_metrics(self, X: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas calidad clustering.

        Parameters:
            X: Embedding UMAP usado para clustering

        Returns:
            Dict con métricas:
                - silhouette: Silhouette score (mayor mejor)
                - davies_bouldin: Davies-Bouldin index (menor mejor)
                - bic: BIC score
                - aic: AIC score
                - log_likelihood: Log-likelihood

        Notes:
            Métricas complementarias para evaluar calidad clustering.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")

        logger.info("Computing clustering quality metrics...")

        metrics = {
            'bic': self.model.bic(X),
            'aic': self.model.aic(X),
            'log_likelihood': self.model.score(X) * X.shape[0],  # score() retorna per-sample
            'silhouette': silhouette_score(X, self.labels_hard),
            'davies_bouldin': davies_bouldin_score(X, self.labels_hard),
            'n_components': self.n_components,
            'converged': self.model.converged_,
            'n_iter': self.model.n_iter_
        }

        logger.info(f"Metrics: silhouette={metrics['silhouette']:.3f}, "
                   f"davies_bouldin={metrics['davies_bouldin']:.3f}")

        return metrics

    def get_cluster_assignments_df(self, metadata_df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera DataFrame con assignments clusters y probabilidades.

        Parameters:
            metadata_df: DataFrame metadata jugadores

        Returns:
            DataFrame con columnas:
                - Metadata original (player_name, team, etc.)
                - cluster_id: Cluster asignado (hard)
                - cluster_proba_0, cluster_proba_1, ...: Probabilidades
                - cluster_confidence: Max probability (confianza asignación)

        Notes:
            Útil para análisis post-clustering y validación manual.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")

        # Resetear index metadata
        metadata_df = metadata_df.reset_index(drop=True)

        # Cluster assignments
        df_result = metadata_df.copy()
        df_result['cluster_id'] = self.labels_hard

        # Probabilidades
        for i in range(self.n_components):
            df_result[f'cluster_proba_{i}'] = self.labels_proba[:, i]

        # Confianza (max probability)
        df_result['cluster_confidence'] = self.labels_proba.max(axis=1)

        logger.info(f"Generated cluster assignments DataFrame: {df_result.shape}")

        return df_result

    def save_model(self, filepath: str):
        """
        Guarda modelo GMM fitted.

        Parameters:
            filepath: Path archivo output (.pkl)
        """
        if not self._fitted:
            raise ValueError("Must fit model before saving")

        import pickle

        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'labels_hard': self.labels_hard,
                'labels_proba': self.labels_proba,
                'params': {
                    'n_components': self.n_components,
                    'covariance_type': self.covariance_type,
                    'max_iter': self.max_iter
                }
            }, f)

        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load_model(cls, filepath: str) -> 'GMMClusterer':
        """
        Carga modelo GMM desde archivo.

        Parameters:
            filepath: Path archivo input (.pkl)

        Returns:
            Instancia GMMClusterer con modelo loaded
        """
        import pickle

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        clusterer = cls(
            n_components=data['params']['n_components'],
            covariance_type=data['params']['covariance_type'],
            max_iter=data['params']['max_iter']
        )

        clusterer.model = data['model']
        clusterer.labels_hard = data['labels_hard']
        clusterer.labels_proba = data['labels_proba']
        clusterer._fitted = True

        logger.info(f"Model loaded from {filepath}")

        return clusterer
