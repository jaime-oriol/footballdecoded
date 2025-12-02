"""
PCA + Cosine Similarity para Similitud de Jugadores

Algoritmo no supervisado que encuentra jugadores similares usando reducción de
dimensionalidad (PCA) y similitud coseno.

Uso:
    from tfm.algorithms import find_similar_players_cosine

    result = find_similar_players_cosine(
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
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity


def find_similar_players_cosine(
    df: pd.DataFrame,
    target_player_id: str,
    n_similar: int = 10,
    pca_variance: float = 0.85,
    return_all_scores: bool = False
) -> Dict:
    """
    Encuentra jugadores similares usando PCA + Cosine Similarity.

    Args:
        df: DataFrame YA PROCESADO con métricas per90 (del notebook).
            Debe tener columnas: unique_player_id, player_name, team, league, season, position
            y métricas normalizadas: *_per90, %, _pct, /Sh, etc.
        target_player_id: unique_player_id del jugador objetivo (YA está en df).
        n_similar: Número de jugadores similares a devolver.
        pca_variance: Varianza retenida en PCA (0.0-1.0). Default 0.85 (85%).
        return_all_scores: Si True, devuelve scores de TODOS los jugadores.

    Returns:
        Dict con:
            - similar_players: DataFrame con top-N jugadores similares
            - all_scores: DataFrame con TODOS los scores (si return_all_scores=True)
            - score_distribution: Estadísticas de similitud
            - pca_info: Información de reducción de dimensionalidad
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

    # Todas las _per90
    per90_cols = [col for col in df.columns if col.endswith('_per90')]

    # Porcentajes y ratios
    pct_cols = [col for col in df.columns
                if any(x in col for x in ['%', '_pct', '/Sh', 'AvgLen', 'AvgDist'])]

    # Understat ratios especiales
    understat_ratios = [col for col in df.columns
                        if 'understat_buildup_involvement_pct' in col]

    # Combinar y limpiar
    feature_cols = list(set(per90_cols + pct_cols + understat_ratios))
    feature_cols = [c for c in feature_cols if c not in basic_cols]

    print(f"Features seleccionados automáticamente: {len(feature_cols)}")

    if len(feature_cols) == 0:
        raise ValueError("No se encontraron features válidos (per90, porcentajes, ratios)")

    # ========== 3. MANEJAR NaNs ==========
    df_work = df.copy()

    # Understat faltante → imputar 0
    understat_cols = [c for c in feature_cols if 'understat' in c.lower()]
    for col in understat_cols:
        if col in df_work.columns:
            df_work[col] = df_work[col].fillna(0)

    # FBref NaNs → eliminar filas (son errores)
    fbref_cols = [c for c in feature_cols if c not in understat_cols]
    df_clean = df_work.dropna(subset=fbref_cols)

    print(f"Jugadores tras limpieza: {len(df_clean)} (eliminados {len(df_work) - len(df_clean)} con NaNs)")

    # Verificar que target sigue en df_clean
    if target_player_id not in df_clean['unique_player_id'].values:
        raise ValueError(f"Target {target_player_id} fue eliminado por NaNs. Revisa datos.")

    # ========== 4. EXTRAER MATRIZ ==========
    X = df_clean[feature_cols].values
    target_idx_clean = df_clean[df_clean['unique_player_id'] == target_player_id].index[0]

    # ========== 5. ESCALAR ==========
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ========== 6. PCA ==========
    pca = PCA(n_components=pca_variance, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    n_components = X_pca.shape[1]
    explained_variance = pca.explained_variance_ratio_.sum()

    print(f"PCA: {n_components} componentes (varianza explicada: {explained_variance:.1%})")
    print(f"Reducción: {len(feature_cols)} → {n_components} dimensiones")

    # ========== 7. SIMILITUD COSENO ==========
    target_vector = X_pca[target_idx_clean].reshape(1, -1)

    # Calcular similitud de target con TODOS los demás
    cosine_scores = cosine_similarity(target_vector, X_pca)[0]

    # Crear DataFrame con scores
    scores_df = df_clean.copy()
    scores_df['cosine_similarity'] = cosine_scores
    scores_df['similarity_percentile'] = (1 - scores_df['cosine_similarity'].rank(pct=True)) * 100

    # Excluir target
    scores_df = scores_df[scores_df['unique_player_id'] != target_player_id].copy()

    # Ordenar por similitud (mayor = más similar)
    scores_df = scores_df.sort_values('cosine_similarity', ascending=False)

    # Top-N similares
    similar_df = scores_df.head(n_similar)

    print(f"Top {n_similar} similares encontrados")
    print(f"Rango similitud: [{similar_df['cosine_similarity'].min():.4f}, {similar_df['cosine_similarity'].max():.4f}]")

    # ========== 8. ESTADÍSTICAS ==========
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

    # Return
    result = {
        'similar_players': similar_df[[
            'unique_player_id', 'player_name', 'team', 'league', 'season',
            'cosine_similarity', 'similarity_percentile'
        ]],
        'score_distribution': score_distribution,
        'pca_info': pca_info,
        'metadata': {
            'n_features': len(feature_cols),
            'features_used': feature_cols,
            'pca_variance_threshold': pca_variance,
            'n_players_analyzed': len(scores_df),
            'timestamp': datetime.now().isoformat()
        }
    }

    if return_all_scores:
        result['all_scores'] = scores_df[[
            'unique_player_id', 'player_name', 'team', 'league', 'season',
            'cosine_similarity', 'similarity_percentile'
        ]]

    return result
