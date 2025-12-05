"""
K-Means Clustering para Similitud de Jugadores

Algoritmo no supervisado que encuentra jugadores similares basándose en métricas
de rendimiento normalizadas per 90 minutos.

Uso:
    from tfm.algorithms import find_similar_players_kmeans

    result = find_similar_players_kmeans(
        df=df_procesado,  # DF con métricas per90 del notebook
        target_player_id='abc123',
        n_similar=10
    )
"""

import numpy as np
import pandas as pd
import warnings
from typing import Dict, List
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


def _validate_target_metrics(
    df: pd.DataFrame,
    target_player_id: str,
    feature_cols: List[str]
) -> None:
    """
    Valida que el target tenga valores válidos (no NaN) en features críticos.

    Args:
        df: DataFrame con todas las columnas (antes de dropna)
        target_player_id: ID del target
        feature_cols: Lista de features que se usarán

    Raises:
        ValueError: Si faltan métricas críticas en target (con mensaje claro)
    """
    if target_player_id not in df['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} not found in DataFrame")

    target_row = df[df['unique_player_id'] == target_player_id].iloc[0]

    # Identificar features críticos (FBref, excluyendo Understat que puede ser 0)
    critical_features = [col for col in feature_cols if 'understat' not in col.lower()]

    missing = []
    for col in critical_features:
        if pd.isna(target_row[col]):
            missing.append(col)

    if missing:
        raise ValueError(
            f"\n{'='*60}\n"
            f"ERROR: Target player missing {len(missing)} critical FBref metrics\n"
            f"{'='*60}\n"
            f"Missing metrics (first 10): {missing[:10]}\n"
            f"Total missing: {len(missing)}/{len(critical_features)}\n\n"
            f"Possible causes:\n"
            f"  1. Target from incompatible league/season (missing FBref coverage)\n"
            f"  2. Target has insufficient playing time\n"
            f"  3. Database extraction error\n\n"
            f"Solutions:\n"
            f"  - Use validate_required_metrics() before calling algorithm\n"
            f"  - Check target has min_minutes >= 300\n"
            f"  - Verify target league in FBref coverage\n"
            f"{'='*60}"
        )


def find_similar_players_kmeans(
    df: pd.DataFrame,
    target_player_id: str,
    n_similar: int = 10,
    k_clusters: int = None,
    use_pca: bool = False
) -> Dict:
    """
    Encuentra jugadores similares usando K-Means clustering.

    Args:
        df: DataFrame YA PROCESADO con métricas per90 (del notebook).
            Debe tener columnas: unique_player_id, player_name, team, league, season, position
            y métricas normalizadas: *_per90, %, _pct, /Sh, etc.
        target_player_id: unique_player_id del jugador objetivo (YA está en df).
        n_similar: Número de jugadores similares a devolver.
        k_clusters: Número de clusters. Si None, se calcula con método del codo.
        use_pca: Si True, aplica PCA antes de clustering.

    Returns:
        Dict con:
            - target_cluster: Cluster asignado al target
            - similar_players: DataFrame con top-N jugadores similares
            - cluster_info: Métricas de validación del cluster
            - distances_distribution: Estadísticas de distancias
            - metadata: Información del proceso

    Raises:
        ValueError: Si target_player_id no existe en df
    """

    # ========== 1. VALIDAR TARGET ==========
    if target_player_id not in df['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} not found in df")

    target_idx = df[df['unique_player_id'] == target_player_id].index[0]
    target_row = df.iloc[target_idx]

    print(f"Target: {target_row['player_name']} ({target_row['team']}, {target_row['league']})")

    # ========== 2. SELECCIONAR FEATURES AUTOMÁTICAMENTE ==========
    basic_cols = ['unique_player_id', 'player_name', 'team', 'league', 'season', 'position']

    # SOLO columnas _per90 (métricas normalizadas)
    per90_cols = [col for col in df.columns if col.endswith('_per90')]

    # FILTRAR métricas de GK (irrelevantes para jugadores de campo)
    gk_keywords = ['Save', 'PSxG', 'CS_per90', 'CS%', 'GA90', 'SoTA', 'Goal Kicks',
                   'Launched', 'Passes_Att (GK)', 'Sweeper', 'Penalty Kicks_PK']
    per90_cols = [col for col in per90_cols
                  if not any(kw in col for kw in gk_keywords)]

    feature_cols = [c for c in per90_cols if c not in basic_cols]

    print(f"Features seleccionados automáticamente: {len(feature_cols)} (solo _per90, excl. GK)")

    if len(feature_cols) == 0:
        raise ValueError("No se encontraron features válidos (columnas _per90)")

    # ========== 3. MANEJAR NaNs INTELIGENTEMENTE ==========
    df_work = df.copy()

    # Understat faltante → imputar 0 (siempre opcional)
    understat_cols = [c for c in feature_cols if 'understat' in c.lower()]
    for col in understat_cols:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    # Clasificar métricas FBref por importancia
    fbref_cols = [c for c in feature_cols if c not in understat_cols]

    # Métricas CORE (si faltan → eliminar jugador) - usar nombres EXACTOS de BD
    core_keywords = ['goals_per90', 'assists_per90', 'shots_per90',
                     'passes_attempted_per90', 'passes_completed_per90',
                     'Touches_Touches_per90', 'Tackles_Tkl_per90', 'interceptions_per90',
                     'Carries_Carries_per90', 'non_penalty_expected_goals_per90',
                     'expected_assists_per90', 'SCA_SCA_per90', 'GCA_GCA_per90']
    core_metrics = [c for c in fbref_cols if c in core_keywords]

    # Métricas SECUNDARIAS (si faltan → fillna(0), son métricas de equipo o eventos raros)
    secondary_keywords = ['wins', 'draws', 'losses', 'Goals_CK', 'Goals_GA', 'Goals_PKA',
                         'Crosses_Stp', 'Crosses_Opp', 'Launch', 'errors', 'OG', 'PKcon', 'PKwon']
    secondary_metrics = [c for c in fbref_cols if any(kw in c for kw in secondary_keywords)]

    # Imputar 0 en métricas secundarias (eventos raros o team records)
    for col in secondary_metrics:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    # Imputar 0 en TODAS las métricas NO-CORE de FBref (pueden faltar en algunas ligas)
    other_metrics = [c for c in fbref_cols if c not in core_metrics and c not in secondary_metrics]
    for col in other_metrics:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    # Solo eliminar jugadores con NaNs en métricas CORE
    df_clean = df_work.dropna(subset=core_metrics).reset_index(drop=True)

    print(f"Jugadores tras limpieza: {len(df_clean)} (eliminados {len(df_work) - len(df_clean)} con NaNs en métricas CORE)")

    # Verificar que target sigue en df_clean
    if target_player_id not in df_clean['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} fue eliminado por NaNs. Revisa datos.")

    # Validar métricas del target
    _validate_target_metrics(df_clean, target_player_id, feature_cols)

    # ========== 4. EXTRAER MATRIZ ==========
    X = df_clean[feature_cols].values
    target_idx_clean = df_clean[df_clean['unique_player_id'] == target_player_id].index[0]

    # ========== 5. ESCALAR ==========
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ========== 6. PCA OPCIONAL ==========
    features_used = feature_cols
    if use_pca or len(X_scaled) < 50:
        pca = PCA(n_components=0.85, random_state=42)
        X_scaled = pca.fit_transform(X_scaled)
        features_used = f"PCA_{X_scaled.shape[1]}_components"
        print(f"PCA aplicado: {X_scaled.shape[1]} componentes (85% varianza)")

    # ========== 7. MÉTODO DEL CODO (si k=None) ==========
    if k_clusters is None:
        k_clusters = _find_optimal_k(X_scaled)
        print(f"Clusters óptimos (método del codo): {k_clusters}")

    # ========== 8. K-MEANS Y CÁLCULO DE SIMILITUD ==========
    kmeans = KMeans(n_clusters=k_clusters, n_init=10, max_iter=300, random_state=42)
    cluster_labels = kmeans.fit_predict(X_scaled)

    target_cluster = cluster_labels[target_idx_clean]
    target_vector = X_scaled[target_idx_clean]

    print(f"Target asignado a cluster: {target_cluster}")

    # Filtrar mismo cluster
    cluster_mask = cluster_labels == target_cluster
    cluster_indices = np.where(cluster_mask)[0]

    # Distancias euclidianas
    distances = np.linalg.norm(X_scaled[cluster_indices] - target_vector, axis=1)

    # Crear DF con distancias
    cluster_df = df_clean.iloc[cluster_indices].copy()
    cluster_df['euclidean_distance'] = distances
    cluster_df['distance_percentile'] = cluster_df['euclidean_distance'].rank(pct=True) * 100
    cluster_df['cluster_id'] = target_cluster

    # Top-N similares (excluir target)
    similar_df = cluster_df[cluster_df['unique_player_id'] != target_player_id].copy()
    similar_df = similar_df.sort_values('euclidean_distance').head(n_similar)

    print(f"Jugadores en cluster {target_cluster}: {len(cluster_df)}")
    print(f"Top {n_similar} similares encontrados")

    # Métricas de validación
    silhouette_avg = silhouette_score(X_scaled, cluster_labels)

    cluster_info = {
        'cluster_id': int(target_cluster),
        'n_players': len(cluster_df),
        'avg_distance': float(np.mean(distances)),
        'std_distance': float(np.std(distances)),
        'silhouette_score': float(silhouette_avg)
    }

    distances_distribution = {
        'min': float(np.min(distances)),
        'q25': float(np.percentile(distances, 25)),
        'median': float(np.median(distances)),
        'q75': float(np.percentile(distances, 75)),
        'max': float(np.max(distances))
    }

    # Return
    return {
        'target_cluster': int(target_cluster),
        'similar_players': similar_df[[
            'unique_player_id', 'player_name', 'team', 'league', 'season',
            'euclidean_distance', 'distance_percentile', 'cluster_id'
        ]],
        'cluster_info': cluster_info,
        'distances_distribution': distances_distribution,
        'metadata': {
            'n_clusters': int(k_clusters),
            'n_features': len(feature_cols) if isinstance(features_used, list) else X_scaled.shape[1],
            'features_used': features_used,
            'pca_applied': use_pca or len(X) < 50,
            'timestamp': datetime.now().isoformat()
        }
    }


def _find_optimal_k(X: np.ndarray, k_range: List[int] = None) -> int:
    """
    Encuentra el número óptimo de clusters usando el método del codo.

    Args:
        X: Matriz de features escalada
        k_range: Rango de k a evaluar

    Returns:
        Número óptimo de clusters
    """
    if k_range is None:
        k_range = [3, 4, 5, 6, 7, 8]

    sse = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        kmeans.fit(X)
        sse.append(kmeans.inertia_)

    # Mejora marginal
    improvements = []
    for i in range(1, len(sse)):
        improvement = (sse[i-1] - sse[i]) / (k_range[i] - k_range[i-1])
        improvements.append(improvement)

    # Codo: mejora < 20% de la primera mejora
    threshold = 0.20 * improvements[0]
    for i, imp in enumerate(improvements):
        if imp < threshold:
            return k_range[i]

    # Si no encuentra codo, devolver el último
    return k_range[-1]
