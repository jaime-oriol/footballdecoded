"""
FootballDecoded - Player Similarity System using UMAP + GMM

Sistema de similitud de jugadores basado en clustering probabilístico no supervisado.
Implementa UMAP (Uniform Manifold Approximation and Projection) para reducción
dimensional y GMM (Gaussian Mixture Models) para identificación de arquetipos.

Workflow completo:
    1. DataPreparator: Extrae datos BD PostgreSQL, limpia y maneja outliers
    2. FeatureEngineer: Selecciona features relevantes, normaliza por posición
    3. UMAPReducer: Reduce 220+ features a espacio 5-10D preservando estructura
    4. GMMClusterer: Identifica arquetipos jugadores mediante clustering probabilístico
    5. PlayerSimilarity: Motor búsqueda similitud multi-criterio (distancia + GMM + features)
    6. PipelineValidator: Valida resultados con ground truth y métricas
    7. SimilarityVisualizer: Genera plots científicos para análisis

Uso rápido:
    >>> from similarity import DataPreparator, FeatureEngineer, UMAPReducer, GMMClusterer, PlayerSimilarity
    >>> from database.connection import get_db_manager
    >>>
    >>> # Preparar datos
    >>> db = get_db_manager()
    >>> prep = DataPreparator(db, table_type='domestic')
    >>> df = prep.load_players(['ESP-La Liga'], '2526', 'FW', min_minutes=200)
    >>> df = prep.extract_all_metrics()
    >>> df = prep.filter_per90_only()  # CRÍTICO: Usar solo métricas per90
    >>> df = prep.handle_missing_values()
    >>> df = prep.detect_outliers()
    >>>
    >>> # Feature engineering
    >>> eng = FeatureEngineer('FW')
    >>> df = eng.select_relevant_features(df)
    >>> df = eng.remove_correlated_features(df)
    >>> df = eng.normalize_by_position(df)
    >>> X, metadata = eng.prepare_for_umap(df, return_dataframe=True)
    >>>
    >>> # UMAP + GMM
    >>> umap = UMAPReducer(n_components=5, n_neighbors=20, min_dist=0.0)
    >>> X_umap = umap.fit_transform(X)
    >>> gmm = GMMClusterer()
    >>> optimal = gmm.find_optimal_clusters(X_umap, min_clusters=3, max_clusters=12)
    >>> gmm.fit(X_umap)
    >>>
    >>> # Similitud
    >>> embedding_df = umap.get_embedding_dataframe(metadata)
    >>> sim = PlayerSimilarity(embedding_df, gmm.labels_proba, df)
    >>> similar = sim.find_similar_players('player_id', top_n=10)

Referencias literatura:
    - McInnes et al. (2018): UMAP: Uniform Manifold Approximation and Projection
    - Schwarz (1978): Estimating the dimension of a model (BIC)
    - Pappalardo et al. (2019): PlayeRank: data-driven performance evaluation
    - Decroos et al. (2019): Actions speak louder than goals (VAEP)
    - Fraley & Raftery (2002): Model-Based Clustering, Discriminant Analysis
    - Little & Rubin (2002): Statistical Analysis with Missing Data

Autor: FootballDecoded
Versión: 1.0.0
"""

__version__ = '1.0.0'

from similarity.data_preparation import DataPreparator
from similarity.feature_engineering import FeatureEngineer
from similarity.umap_reducer import UMAPReducer
from similarity.gmm_clustering import GMMClusterer
from similarity.player_similarity import PlayerSimilarity
from similarity.validation import PipelineValidator
from similarity.visualization import SimilarityVisualizer

__all__ = [
    'DataPreparator',
    'FeatureEngineer',
    'UMAPReducer',
    'GMMClusterer',
    'PlayerSimilarity',
    'PipelineValidator',
    'SimilarityVisualizer',
]
