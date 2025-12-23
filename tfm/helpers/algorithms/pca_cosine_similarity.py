"""
PCA + Cosine Similarity para Similitud de Jugadores

Algoritmo no supervisado que encuentra jugadores similares usando reducción de
dimensionalidad (PCA) y similitud coseno.

Uso:
    from tfm.algorithms import find_similar_players_cosine

    result = find_similar_players_cosine(
        df=df_procesado,
        target_player_id='abc123',
        n_similar=30,
        replacement_id='def456'
    )
"""

import numpy as np
import pandas as pd
import warnings
from typing import Dict, List, Optional
from datetime import datetime
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity


# Keywords GK exportables como constante
GK_KEYWORDS = ['Save', 'PSxG', 'CS_per90', 'CS%', 'GA90', 'SoTA', 'Goal Kicks',
               'Launched', 'Passes_Att (GK)', 'Sweeper', 'Penalty Kicks_PK']


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
        ValueError: Si faltan métricas críticas en target
    """
    if target_player_id not in df['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} not found in DataFrame")

    target_row = df[df['unique_player_id'] == target_player_id].iloc[0]

    critical_features = [col for col in feature_cols if 'understat' not in col.lower()]

    missing = []
    for col in critical_features:
        if pd.isna(target_row[col]):
            missing.append(col)

    if missing:
        raise ValueError(
            f"\n{'='*60}\n"
            f"ERROR: Target missing {len(missing)} critical FBref metrics\n"
            f"{'='*60}\n"
            f"Missing metrics (first 10): {missing[:10]}\n"
            f"Total missing: {len(missing)}/{len(critical_features)}\n\n"
            f"Possible causes:\n"
            f"  1. Incompatible league/season (missing FBref coverage)\n"
            f"  2. Insufficient playing time\n"
            f"  3. Database extraction error\n\n"
            f"Solutions:\n"
            f"  - Use validate_required_metrics() before calling algorithm\n"
            f"  - Check target has min_minutes >= 300\n"
            f"{'='*60}"
        )


def find_similar_players_cosine(
    df: pd.DataFrame,
    target_player_id: str,
    n_similar: int = 30,
    pca_variance: float = 0.85,
    return_all_scores: bool = False,
    replacement_id: Optional[str] = None,
    robust_scaling: bool = False
) -> Dict:
    """
    Encuentra jugadores similares usando PCA + Cosine Similarity.

    Args:
        df: DataFrame procesado con métricas per90.
            Columnas requeridas: unique_player_id, player_name, team, league, season
        target_player_id: ID del jugador objetivo
        n_similar: Número de jugadores similares a devolver (default: 30)
        pca_variance: Varianza retenida en PCA (default: 0.85)
        return_all_scores: Si True, devuelve scores de todos los jugadores
        replacement_id: ID del reemplazo para calcular validación (opcional)
        robust_scaling: Si True, usa RobustScaler en lugar de StandardScaler

    Returns:
        Dict con:
            - target_info: Información del jugador objetivo
            - replacement_info: Información del reemplazo (si replacement_id)
            - similar_players: DataFrame con top-N similares
            - score_distribution: Estadísticas de similitud
            - pca_info: Información de reducción dimensional
            - metadata: Metadata del proceso
            - all_scores: Scores completos (si return_all_scores=True)

    Raises:
        ValueError: Si target_player_id no existe en df
    """

    # ========== VALIDAR TARGET ==========
    if target_player_id not in df['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} not found in df")

    target_idx = df[df['unique_player_id'] == target_player_id].index[0]
    target_row = df.iloc[target_idx]

    print(f"Target: {target_row['player_name']} ({target_row['team']}, {target_row['league']})")

    # ========== SELECCIONAR FEATURES ==========
    basic_cols = ['unique_player_id', 'player_name', 'team', 'league', 'season', 'position']

    # Usar SOLO normalización per 100 touches
    normalized_cols = [col for col in df.columns if col.endswith('_per100touches')]
    normalized_cols = [col for col in normalized_cols
                       if not any(kw in col for kw in GK_KEYWORDS)]

    feature_cols = [c for c in normalized_cols if c not in basic_cols]

    print(f"Features: {len(feature_cols)} (per 100 touches, excl. GK)")

    if len(feature_cols) == 0:
        raise ValueError("No features válidos con sufijo _per100touches")

    # ========== MANEJAR NANs ==========
    df_work = df.copy()

    understat_cols = [c for c in feature_cols if 'understat' in c.lower()]
    for col in understat_cols:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    fbref_cols = [c for c in feature_cols if c not in understat_cols]

    # Core keywords base (sin sufijo) - per 100 touches
    core_base_keywords = ['goals', 'assists', 'shots',
                          'passes_attempted', 'passes_completed',
                          'Touches_Touches', 'Tackles_Tkl', 'interceptions',
                          'Carries_Carries', 'non_penalty_expected_goals',
                          'expected_assists', 'SCA_SCA', 'GCA_GCA']

    # Excluir métricas defensivas que no son relevantes para atacantes
    defensive_exclude = ['goals_against', 'Goals_GA', 'Goals_GK']

    core_metrics = [c for c in fbref_cols
                    if any(c.startswith(kw + '_') or c == kw + '_per100touches' for kw in core_base_keywords)
                    and not any(excl in c for excl in defensive_exclude)]

    secondary_keywords = ['wins', 'draws', 'losses', 'Goals_CK', 'Goals_GA', 'Goals_PKA',
                         'Crosses_Stp', 'Crosses_Opp', 'Launch', 'errors', 'OG', 'PKcon', 'PKwon',
                         'goals_against']
    secondary_metrics = [c for c in fbref_cols if any(kw in c for kw in secondary_keywords)]

    for col in secondary_metrics:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    other_metrics = [c for c in fbref_cols if c not in core_metrics and c not in secondary_metrics]
    for col in other_metrics:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    df_clean = df_work.dropna(subset=core_metrics).reset_index(drop=True)

    print(f"Jugadores: {len(df_clean)} (eliminados {len(df_work) - len(df_clean)} con NaNs CORE)")

    if target_player_id not in df_clean['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} eliminado por NaNs. Revisar datos.")

    _validate_target_metrics(df_clean, target_player_id, feature_cols)

    # ========== EXTRAER MATRIZ ==========
    X = df_clean[feature_cols].values
    target_idx_clean = df_clean[df_clean['unique_player_id'] == target_player_id].index[0]

    # ========== ESCALAR ==========
    scaler = RobustScaler() if robust_scaling else StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ========== PCA ==========
    pca = PCA(n_components=pca_variance, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    n_components = X_pca.shape[1]
    explained_variance = pca.explained_variance_ratio_.sum()

    print(f"PCA: {n_components} componentes (varianza: {explained_variance:.1%})")
    print(f"Reducción: {len(feature_cols)} → {n_components} dimensiones")

    # ========== SIMILITUD COSENO ==========
    target_vector = X_pca[target_idx_clean].reshape(1, -1)
    cosine_scores = cosine_similarity(target_vector, X_pca)[0]

    scores_df = df_clean.copy()
    scores_df['cosine_similarity'] = cosine_scores

    scores_df = scores_df[scores_df['unique_player_id'] != target_player_id].copy()
    scores_df = scores_df.sort_values('cosine_similarity', ascending=False).reset_index(drop=True)

    scores_df['rank'] = range(1, len(scores_df) + 1)

    def get_validation_status(rank):
        if rank <= 10:
            return 'VALIDADO'
        elif rank <= 30:
            return 'PARCIAL'
        else:
            return 'NO_VALIDADO'

    scores_df['validation_status'] = scores_df['rank'].apply(get_validation_status)
    scores_df['similarity_percentile'] = (1 - scores_df['rank'] / len(scores_df)) * 100

    similar_df = scores_df.head(n_similar)

    print(f"Top-{n_similar} encontrados")
    print(f"Rango similitud: [{similar_df['cosine_similarity'].min():.4f}, {similar_df['cosine_similarity'].max():.4f}]")

    # ========== ESTADÍSTICAS ==========
    score_distribution = {
        'min': float(scores_df['cosine_similarity'].min()),
        'q5': float(scores_df['cosine_similarity'].quantile(0.05)),
        'q25': float(scores_df['cosine_similarity'].quantile(0.25)),
        'median': float(scores_df['cosine_similarity'].median()),
        'q75': float(scores_df['cosine_similarity'].quantile(0.75)),
        'q95': float(scores_df['cosine_similarity'].quantile(0.95)),
        'max': float(scores_df['cosine_similarity'].max()),
        'mean': float(scores_df['cosine_similarity'].mean()),
        'std': float(scores_df['cosine_similarity'].std())
    }

    pca_info = {
        'n_components': int(n_components),
        'explained_variance_ratio': float(explained_variance),
        'original_dimensions': len(feature_cols),
        'reduced_dimensions': int(n_components),
        'compression_ratio': float(n_components / len(feature_cols)),
        'top_5_components_variance': pca.explained_variance_ratio_[:5].tolist()
    }

    target_info = {
        'player_name': target_row['player_name'],
        'unique_player_id': target_player_id,
        'team': target_row['team'],
        'league': target_row['league'],
        'season': target_row['season']
    }

    result = {
        'target_info': target_info,
        'similar_players': similar_df[[
            'unique_player_id', 'player_name', 'team', 'league', 'season',
            'rank', 'cosine_similarity', 'validation_status', 'similarity_percentile'
        ]],
        'score_distribution': score_distribution,
        'pca_info': pca_info,
        'metadata': {
            'n_features': len(feature_cols),
            'features_used': feature_cols,
            'pca_variance_threshold': pca_variance,
            'n_players_analyzed': len(scores_df),
            'robust_scaling': robust_scaling,
            'timestamp': datetime.now().isoformat()
        }
    }

    # ========== REPLACEMENT INFO (OPCIONAL) ==========
    if replacement_id:
        if replacement_id in scores_df['unique_player_id'].values:
            repl_row = scores_df[scores_df['unique_player_id'] == replacement_id].iloc[0]
            result['replacement_info'] = {
                'player_name': repl_row['player_name'],
                'unique_player_id': replacement_id,
                'team': repl_row['team'],
                'league': repl_row['league'],
                'season': repl_row['season'],
                'rank': int(repl_row['rank']),
                'cosine_similarity': float(repl_row['cosine_similarity']),
                'validation_status': repl_row['validation_status'],
                'similarity_percentile': float(repl_row['similarity_percentile'])
            }
        else:
            result['replacement_info'] = {
                'player_name': 'NOT_FOUND',
                'unique_player_id': replacement_id,
                'rank': None,
                'cosine_similarity': None,
                'validation_status': 'NOT_IN_POOL'
            }

    if return_all_scores:
        result['all_scores'] = scores_df[[
            'unique_player_id', 'player_name', 'team', 'league', 'season',
            'rank', 'cosine_similarity', 'validation_status', 'similarity_percentile'
        ]]

    return result
