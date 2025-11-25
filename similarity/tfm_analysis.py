#!/usr/bin/env python3
"""
Análisis de casos TFM para ajustar algoritmo.

Analiza por qué los fichados no están saliendo en top 50 y propone ajustes.
"""

import sys
sys.path.append('/home/jaime/FD/data')

import pandas as pd
import numpy as np
from database.connection import get_db_manager
from sqlalchemy import text

# TODOS los casos TFM a analizar
ALL_CASES = [
    # DELANTEROS
    {
        "vendido_id": "df3c607f8f46ffc1",
        "vendido_name": "Nicolas Jackson",
        "fichado_id": "cad28b020b20f985",
        "fichado_name": "Alexander Sørloth",
        "season": "2223",
        "position": "FW",
        "status": "FAILED"
    },
    {
        "vendido_id": "859f713390732d2a",
        "vendido_name": "Ben Brereton",
        "fichado_id": "1dc1d9419b82ed73",
        "fichado_name": "Ayoze Pérez",
        "season": "2324",
        "position": "FW",
        "status": "FAILED"
    },
    {
        "vendido_id": "8cfbfca3e5dc4ba0",
        "vendido_name": "Randal Kolo Muani",
        "fichado_id": "b5fd95dbeba1f61f",
        "fichado_name": "Omar Marmoush",
        "season": "2223",
        "position": "FW",
        "status": "SUCCESS"  # Rank 14
    },
    {
        "vendido_id": "8cfbfca3e5dc4ba0",
        "vendido_name": "Randal Kolo Muani",
        "fichado_id": "2af83c0acb2812de",
        "fichado_name": "Hugo Ekitike",
        "season": "2223",
        "position": "FW",
        "status": "FAILED"
    },
    {
        "vendido_id": "b5fd95dbeba1f61f",
        "vendido_name": "Omar Marmoush",
        "fichado_id": "588046b2ff0315c7",
        "fichado_name": "Elye Wahi",
        "season": "2324",
        "position": "FW",
        "status": "FAILED"
    },
    {
        "vendido_id": "2af83c0acb2812de",
        "vendido_name": "Hugo Ekitike",
        "fichado_id": "b6fcc5ac2ef92f29",
        "fichado_name": "Jonathan Burkardt",
        "season": "2425",
        "position": "FW",
        "status": "FAILED"
    },
    # DEFENSAS
    {
        "vendido_id": "cbb3780ec36be9be",
        "vendido_name": "Pervis Estupiñán",
        "fichado_id": "c230785304a6bacb",
        "fichado_name": "Johan Mojica",
        "season": "2122",
        "position": "DF",
        "status": "FAILED"
    },
    {
        "vendido_id": "7038310ad2ae51db",
        "vendido_name": "Pau Torres",
        "fichado_id": "3b445a031f685465",
        "fichado_name": "Logan Costa",
        "season": "2324",
        "position": "DF",
        "status": "SUCCESS"  # Rank 36
    },
    {
        "vendido_id": "c230785304a6bacb",
        "vendido_name": "Johan Mojica",
        "fichado_id": "dc5dd1f512cb8bf2",
        "fichado_name": "Sergi Cardona",
        "season": "2324",
        "position": "DF",
        "status": "FAILED"
    },
    {
        "vendido_id": "3b6c6d66fee0938d",
        "vendido_name": "Willian Pacho",
        "fichado_id": "4736a05f4cc311c0",
        "fichado_name": "Arthur Theate",
        "season": "2324",
        "position": "DF",
        "status": "FAILED"
    },
    # MEDIOCAMPISTAS
    {
        "vendido_id": "eb4c447d1a00eb39",
        "vendido_name": "Álex Baena",
        "fichado_id": "e3039aff904c9c54",
        "fichado_name": "Alberto Moleiro",
        "season": "2425",
        "position": "MF",
        "status": "FAILED"
    },
    {
        "vendido_id": "f78eb44040a1bfde",
        "vendido_name": "Carlos Baleba",
        "fichado_id": "ee0c963766e4e66c",
        "fichado_name": "Nabil Bentaleb",
        "season": "2223",
        "position": "MF",
        "status": "FAILED"  # Caso fallido esperado
    },
]

def get_player_stats(db, player_id, season):
    """Obtiene stats de un jugador en una temporada."""
    query = text("""
        SELECT
            player_name, team, league, position, age,
            fbref_metrics, understat_metrics
        FROM footballdecoded.players_domestic
        WHERE unique_player_id = :player_id
        AND season = :season
    """)

    df = pd.read_sql(query, db.engine, params={'player_id': player_id, 'season': season})
    return df

def extract_key_metrics(fbref_dict, understat_dict):
    """Extrae métricas clave de los dicts."""
    def safe_float(val):
        """Convierte a float de forma segura."""
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    metrics = {}

    # FBref
    if fbref_dict:
        metrics['minutes'] = safe_float(fbref_dict.get('minutes_played', 0))
        metrics['goals'] = safe_float(fbref_dict.get('goals', 0))
        metrics['assists'] = safe_float(fbref_dict.get('assists', 0))
        metrics['xG'] = safe_float(fbref_dict.get('expected_goals', 0))
        metrics['xA'] = safe_float(fbref_dict.get('expected_assists', 0))
        metrics['shots'] = safe_float(fbref_dict.get('shots', 0))
        metrics['key_passes'] = safe_float(fbref_dict.get('key_passes', 0))
        metrics['progressive_passes'] = safe_float(fbref_dict.get('progressive_passes', 0))
        metrics['progressive_carries'] = safe_float(fbref_dict.get('Carries_PrgC', 0))
        metrics['tackles_won'] = safe_float(fbref_dict.get('Tackles_TklW', 0))
        metrics['interceptions'] = safe_float(fbref_dict.get('interceptions', 0))

    # Understat
    if understat_dict:
        metrics['npxG'] = safe_float(understat_dict.get('understat_npxg', 0))
        metrics['xA_understat'] = safe_float(understat_dict.get('understat_xa', 0))

    # Per 90
    if metrics.get('minutes', 0) > 0:
        minutes = metrics['minutes']
        metrics['goals_p90'] = (metrics.get('goals', 0) / minutes) * 90
        metrics['xG_p90'] = (metrics.get('xG', 0) / minutes) * 90
        metrics['shots_p90'] = (metrics.get('shots', 0) / minutes) * 90
        metrics['progressive_passes_p90'] = (metrics.get('progressive_passes', 0) / minutes) * 90

    return metrics

def compare_players(vendido_stats, fichado_stats):
    """Compara stats de dos jugadores."""
    print(f"\n{'='*80}")
    print(f"COMPARACIÓN: {vendido_stats['player_name'].iloc[0]} vs {fichado_stats['player_name'].iloc[0]}")
    print(f"{'='*80}\n")

    vendido_fbref = vendido_stats['fbref_metrics'].iloc[0]
    vendido_understat = vendido_stats['understat_metrics'].iloc[0] if 'understat_metrics' in vendido_stats.columns else None

    fichado_fbref = fichado_stats['fbref_metrics'].iloc[0]
    fichado_understat = fichado_stats['understat_metrics'].iloc[0] if 'understat_metrics' in fichado_stats.columns else None

    vendido_m = extract_key_metrics(vendido_fbref, vendido_understat)
    fichado_m = extract_key_metrics(fichado_fbref, fichado_understat)

    print(f"{'Métrica':<30} {'Vendido':<15} {'Fichado':<15} {'Diff %':<15}")
    print("-" * 80)

    for key in ['minutes', 'goals', 'assists', 'xG', 'xA', 'shots',
                'goals_p90', 'xG_p90', 'shots_p90', 'progressive_passes_p90']:
        vendido_val = vendido_m.get(key, 0)
        fichado_val = fichado_m.get(key, 0)

        if vendido_val > 0:
            diff_pct = ((fichado_val - vendido_val) / vendido_val) * 100
        else:
            diff_pct = 0

        print(f"{key:<30} {vendido_val:<15.2f} {fichado_val:<15.2f} {diff_pct:<15.1f}")

    print("\n")

    # Info contextual
    print(f"Vendido: {vendido_stats['team'].iloc[0]} ({vendido_stats['league'].iloc[0]})")
    print(f"Fichado: {fichado_stats['team'].iloc[0]} ({fichado_stats['league'].iloc[0]})")
    print(f"Edad vendido: {vendido_stats['age'].iloc[0]}")
    print(f"Edad fichado: {fichado_stats['age'].iloc[0]}")

def main():
    """Analizar casos fallidos."""
    db = get_db_manager()

    for case in FAILED_CASES:
        vendido_stats = get_player_stats(db, case['vendido_id'], case['season'])
        fichado_stats = get_player_stats(db, case['fichado_id'], case['season'])

        if vendido_stats.empty:
            print(f"✗ No data for vendido: {case['vendido_name']} (ID: {case['vendido_id']}) season {case['season']}")
            continue

        if fichado_stats.empty:
            print(f"✗ No data for fichado: {case['fichado_name']} (ID: {case['fichado_id']}) season {case['season']}")
            continue

        compare_players(vendido_stats, fichado_stats)

    db.close()

if __name__ == "__main__":
    main()
