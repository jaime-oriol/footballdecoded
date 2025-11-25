#!/usr/bin/env python3
"""
Análisis profundo de casos TFM fallidos.

Investiga por qué los fichados no salen en top 50:
- Compara métricas per90 entre vendido y fichado
- Analiza distancias UMAP
- Verifica clusters GMM
- Identifica patrones de fallo
"""

import sys
sys.path.append('/home/jaime/FD/data')

import pandas as pd
import numpy as np
from database.connection import get_db_manager
from sqlalchemy import text
from similarity import DataPreparator, FeatureEngineer, UMAPReducer, GMMClusterer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Casos FALLIDOS a analizar
FAILED_CASES = [
    {"vendido_id": "859f713390732d2a", "vendido": "Ben Brereton",
     "fichado_id": "1dc1d9419b82ed73", "fichado": "Ayoze Pérez",
     "season": "2324", "position": "FW"},
    {"vendido_id": "7038310ad2ae51db", "vendido": "Pau Torres",
     "fichado_id": "3b445a031f685465", "fichado": "Logan Costa",
     "season": "2324", "position": "DF"},
    {"vendido_id": "c230785304a6bacb", "vendido": "Johan Mojica",
     "fichado_id": "dc5dd1f512cb8bf2", "fichado": "Sergi Cardona",
     "season": "2324", "position": "DF"},
    {"vendido_id": "eb4c447d1a00eb39", "vendido": "Álex Baena",
     "fichado_id": "e3039aff904c9c54", "fichado": "Alberto Moleiro",
     "season": "2425", "position": "MF"},
    {"vendido_id": "8cfbfca3e5dc4ba0", "vendido": "Randal Kolo Muani",
     "fichado_id": "b5fd95dbeba1f61f", "fichado": "Omar Marmoush",
     "season": "2223", "position": "FW"},
    {"vendido_id": "8cfbfca3e5dc4ba0", "vendido": "Randal Kolo Muani",
     "fichado_id": "2af83c0acb2812de", "fichado": "Hugo Ekitike",
     "season": "2223", "position": "FW"},
    {"vendido_id": "b5fd95dbeba1f61f", "vendido": "Omar Marmoush",
     "fichado_id": "588046b2ff0315c7", "fichado": "Elye Wahi",
     "season": "2324", "position": "FW"},
    {"vendido_id": "3b6c6d66fee0938d", "vendido": "Willian Pacho",
     "fichado_id": "4736a05f4cc311c0", "fichado": "Arthur Theate",
     "season": "2324", "position": "DF"},
]

def get_player_raw_data(db, player_id, season):
    """Obtiene datos crudos del jugador."""
    query = text("""
        SELECT
            unique_player_id, player_name, team, league, position, age,
            fbref_metrics, understat_metrics
        FROM footballdecoded.players_domestic
        WHERE unique_player_id = :player_id AND season = :season
    """)

    df = pd.read_sql(query, db.engine, params={'player_id': player_id, 'season': season})
    return df

def safe_float(val):
    """Convierte a float de forma segura."""
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

def extract_key_per90(fbref_dict, understat_dict, position):
    """Extrae métricas clave per90 según posición."""
    minutes = safe_float(fbref_dict.get('minutes_played', 0)) if fbref_dict else 0
    if minutes == 0:
        return {}

    metrics = {'minutes': minutes}

    if position == 'FW':
        metrics['goals_p90'] = (safe_float(fbref_dict.get('goals', 0)) / minutes) * 90
        metrics['xG_p90'] = (safe_float(fbref_dict.get('expected_goals', 0)) / minutes) * 90
        metrics['shots_p90'] = (safe_float(fbref_dict.get('shots', 0)) / minutes) * 90
        metrics['npxG_p90'] = (safe_float(understat_dict.get('understat_npxg', 0)) / minutes) * 90 if understat_dict else 0
        metrics['touches_box_p90'] = (safe_float(fbref_dict.get('Touches_Att Pen', 0)) / minutes) * 90
        metrics['key_passes_p90'] = (safe_float(fbref_dict.get('key_passes', 0)) / minutes) * 90
        metrics['progressive_carries_p90'] = (safe_float(fbref_dict.get('Carries_PrgC', 0)) / minutes) * 90
    elif position == 'DF':
        metrics['tackles_p90'] = (safe_float(fbref_dict.get('Tackles_TklW', 0)) / minutes) * 90
        metrics['interceptions_p90'] = (safe_float(fbref_dict.get('interceptions', 0)) / minutes) * 90
        metrics['clearances_p90'] = (safe_float(fbref_dict.get('clearances', 0)) / minutes) * 90
        metrics['progressive_passes_p90'] = (safe_float(fbref_dict.get('progressive_passes', 0)) / minutes) * 90
        metrics['aerial_won_p90'] = (safe_float(fbref_dict.get('Aerial Duels_Won', 0)) / minutes) * 90
        metrics['passes_final_third_p90'] = (safe_float(fbref_dict.get('passes_final_third', 0)) / minutes) * 90
        metrics['xA_p90'] = (safe_float(fbref_dict.get('expected_assists', 0)) / minutes) * 90
    elif position == 'MF':
        metrics['progressive_passes_p90'] = (safe_float(fbref_dict.get('progressive_passes', 0)) / minutes) * 90
        metrics['progressive_carries_p90'] = (safe_float(fbref_dict.get('Carries_PrgC', 0)) / minutes) * 90
        metrics['key_passes_p90'] = (safe_float(fbref_dict.get('key_passes', 0)) / minutes) * 90
        metrics['xA_p90'] = (safe_float(fbref_dict.get('expected_assists', 0)) / minutes) * 90
        metrics['tackles_p90'] = (safe_float(fbref_dict.get('Tackles_TklW', 0)) / minutes) * 90
        metrics['interceptions_p90'] = (safe_float(fbref_dict.get('interceptions', 0)) / minutes) * 90
        metrics['shots_p90'] = (safe_float(fbref_dict.get('shots', 0)) / minutes) * 90
        metrics['xG_p90'] = (safe_float(fbref_dict.get('expected_goals', 0)) / minutes) * 90

    return metrics

def analyze_case(db, case):
    """Analiza un caso fallido en detalle."""
    print(f"\n{'='*100}")
    print(f"CASO: {case['vendido']} → {case['fichado']}")
    print(f"Temporada: {case['season']}, Posición: {case['position']}")
    print(f"{'='*100}\n")

    # Obtener datos crudos
    vendido_df = get_player_raw_data(db, case['vendido_id'], case['season'])
    fichado_df = get_player_raw_data(db, case['fichado_id'], case['season'])

    if vendido_df.empty:
        print(f"✗ VENDIDO no encontrado en BD")
        return
    if fichado_df.empty:
        print(f"✗ FICHADO no encontrado en BD")
        return

    vendido_row = vendido_df.iloc[0]
    fichado_row = fichado_df.iloc[0]

    print(f"VENDIDO: {vendido_row['player_name']} ({vendido_row['team']}, {vendido_row['league']})")
    print(f"         Edad: {vendido_row['age']}")
    print(f"FICHADO: {fichado_row['player_name']} ({fichado_row['team']}, {fichado_row['league']})")
    print(f"         Edad: {fichado_row['age']}")
    print()

    # Extraer métricas per90
    vendido_metrics = extract_key_per90(
        vendido_row['fbref_metrics'],
        vendido_row['understat_metrics'],
        case['position']
    )
    fichado_metrics = extract_key_per90(
        fichado_row['fbref_metrics'],
        fichado_row['understat_metrics'],
        case['position']
    )

    print(f"{'Métrica':<30} {'Vendido':<15} {'Fichado':<15} {'Diff %':<15} {'Problema?'}")
    print("-" * 100)

    metrics_keys = sorted(set(vendido_metrics.keys()) | set(fichado_metrics.keys()))
    problemas = []

    for key in metrics_keys:
        v_val = vendido_metrics.get(key, 0)
        f_val = fichado_metrics.get(key, 0)

        if key == 'minutes':
            diff_pct = 0
            problema = "✓" if abs(v_val - f_val) < 500 else "⚠ Mucha diferencia minutos"
        else:
            if v_val > 0:
                diff_pct = ((f_val - v_val) / v_val) * 100
            else:
                diff_pct = 0

            # Detectar problemas
            if abs(diff_pct) > 50:
                problema = "✗ MUY diferente"
                problemas.append(key)
            elif abs(diff_pct) > 30:
                problema = "⚠ Bastante diferente"
            else:
                problema = "✓"

        print(f"{key:<30} {v_val:<15.2f} {f_val:<15.2f} {diff_pct:>14.1f}% {problema}")

    print()

    # Ahora hacer UMAP para ver distancia real
    print("Ejecutando pipeline UMAP+GMM para calcular distancia real...")

    try:
        leagues = ['ESP-La Liga', 'ENG-Premier League', 'GER-Bundesliga', 'FRA-Ligue 1', 'ITA-Serie A']
        df_list = []
        for league in leagues:
            try:
                data_prep_temp = DataPreparator(db, table_type='domestic')
                df_temp = data_prep_temp.load_players(
                    leagues=[league],
                    season=case['season'],
                    position_filter=case['position'],
                    min_minutes=150
                )
                if not df_temp.empty:
                    df_list.append(df_temp)
            except:
                continue

        if not df_list:
            print("✗ No se pudo cargar pool")
            return

        df_raw = pd.concat(df_list, ignore_index=True)

        # Pipeline completo
        data_prep = DataPreparator(db, table_type='domestic')
        data_prep.set_raw_data(df_raw)
        df_metrics_all = data_prep.extract_all_metrics()

        # Filtrar per90
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league', 'season', 'position', 'age']
        per90_cols = [col for col in df_metrics_all.columns if col.endswith('_per90')]
        ratio_cols = [col for col in df_metrics_all.columns
                     if any(x in col for x in ['%', '_pct', '/90', 'SCA90', 'GCA90', '/Sh', 'xG+xAG'])]
        feature_cols = list(set(per90_cols + ratio_cols))
        df_per90 = df_metrics_all[metadata_cols + feature_cols].copy()
        data_prep.df_clean = df_per90

        df_clean = data_prep.handle_missing_values(strategy='median_by_position', max_missing_pct=0.6)
        df_outliers = data_prep.detect_outliers(method='isolation_forest', contamination=0.01)

        feature_eng = FeatureEngineer(position_type=case['position'])
        df_selected = feature_eng.select_relevant_features(df_outliers, exclude_gk_metrics=True, min_variance=0.001)
        df_uncorrelated = feature_eng.remove_correlated_features(df_selected, threshold=0.99)
        df_normalized = feature_eng.normalize_by_position(df_uncorrelated, method='standard', fit_per_position=True)

        X, metadata_df = feature_eng.prepare_for_umap(df_normalized, return_dataframe=True)

        umap_reducer = UMAPReducer(n_components=5, n_neighbors=10, min_dist=0.2, metric='euclidean', random_state=42)
        X_umap = umap_reducer.fit_transform(X, verbose=False)

        embedding_df = umap_reducer.get_embedding_dataframe(metadata_df)

        # Verificar si ambos están
        vendido_in = case['vendido_id'] in embedding_df['unique_player_id'].values
        fichado_in = case['fichado_id'] in embedding_df['unique_player_id'].values

        print(f"Vendido en embedding: {vendido_in}")
        print(f"Fichado en embedding: {fichado_in}")

        if vendido_in and fichado_in:
            v_row = embedding_df[embedding_df['unique_player_id'] == case['vendido_id']].iloc[0]
            f_row = embedding_df[embedding_df['unique_player_id'] == case['fichado_id']].iloc[0]

            umap_cols = [col for col in embedding_df.columns if col.startswith('umap_')]
            v_umap = v_row[umap_cols].values
            f_umap = f_row[umap_cols].values

            from scipy.spatial.distance import euclidean
            dist = euclidean(v_umap, f_umap)

            print(f"\nDistancia UMAP entre vendido y fichado: {dist:.3f}")

            # Calcular distancias a todos
            all_dists = []
            for idx, row in embedding_df.iterrows():
                if row['unique_player_id'] == case['vendido_id']:
                    continue
                other_umap = row[umap_cols].values
                d = euclidean(v_umap, other_umap)
                all_dists.append(d)

            all_dists_sorted = sorted(all_dists)
            percentile = (all_dists_sorted.index(dist) / len(all_dists_sorted)) * 100 if dist in all_dists_sorted else 100

            print(f"Percentil de distancia: {percentile:.1f}% (menor = más cercano)")
            print(f"Distancia mínima en pool: {min(all_dists):.3f}")
            print(f"Distancia máxima en pool: {max(all_dists):.3f}")
            print(f"Distancia mediana en pool: {np.median(all_dists):.3f}")

            if percentile > 50:
                print(f"\n⚠ PROBLEMA: Fichado está en mitad LEJANA del pool (percentil {percentile:.1f}%)")
            else:
                print(f"\n✓ Fichado está en mitad CERCANA del pool (percentil {percentile:.1f}%)")

        elif not fichado_in:
            print(f"\n✗ PROBLEMA CRÍTICO: FICHADO NO ESTÁ EN EMBEDDING")
            print("   Posibles razones:")
            print("   - Eliminado por outlier detection")
            print("   - Eliminado por missing values")
            print("   - No cumple min_minutes=150")
        elif not vendido_in:
            print(f"\n✗ PROBLEMA CRÍTICO: VENDIDO NO ESTÁ EN EMBEDDING")

    except Exception as e:
        print(f"✗ Error en pipeline: {e}")

    print()

    # Resumen
    print("RESUMEN DEL CASO:")
    print("-" * 100)
    if problemas:
        print(f"✗ Métricas muy diferentes ({len(problemas)}): {', '.join(problemas[:5])}")
        print("  → Jugadores tienen PERFILES DIFERENTES estadísticamente")
    else:
        print("✓ Métricas similares en general")

    print()

def main():
    """Analizar todos los casos fallidos."""
    logger.info("="*100)
    logger.info("ANÁLISIS PROFUNDO DE CASOS FALLIDOS TFM")
    logger.info("="*100)

    db = get_db_manager()

    for case in FAILED_CASES:
        analyze_case(db, case)

    db.close()
    logger.info("\n✓ Análisis completado\n")

if __name__ == "__main__":
    main()
