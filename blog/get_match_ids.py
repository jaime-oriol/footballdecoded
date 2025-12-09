#!/usr/bin/env python3
"""
Match ID Extractor for WhoScored and Understat
==============================================

Extrae automáticamente los IDs de partidos de un equipo específico
desde WhoScored y Understat para una liga y temporada determinadas.

Uso:
    from get_match_ids import get_match_ids

    ids = get_match_ids("Atlético Madrid", "ESP-La Liga", "24-25")
    print(ids)

    # Exportar a CSV
    ids.to_csv("atm_matches_24-25.csv", index=False)
"""

import sys
import os
from pathlib import Path
from typing import Optional
import pandas as pd
import warnings

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrappers import WhoScored, Understat
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore')


def _normalize_team_name(team_name: str) -> list[str]:
    """Generar variaciones del nombre de equipo para matching flexible."""
    variations = [team_name]

    clean_name = (team_name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u'))
    if clean_name != team_name:
        variations.append(clean_name)

    common_mappings = {
        'Atlético Madrid': ['Atletico Madrid', 'Atlético', 'Atletico', 'ATM'],
        'Athletic Club': ['Athletic Bilbao', 'Athletic'],
        'Real Madrid': ['Madrid', 'Real'],
        'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
        'Manchester United': ['Man United', 'Manchester Utd'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur', 'Spurs'],
        'Inter Miami': ['Inter Miami CF', 'Miami', 'Inter Miami C.F.'],
    }

    for key, values in common_mappings.items():
        if team_name in [key] + values:
            variations.extend([key] + values)

    return list(dict.fromkeys(variations))


def _filter_team_matches(schedule: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Filtrar partidos donde juega el equipo especificado."""
    if schedule.empty:
        return schedule

    variations = _normalize_team_name(team_name)
    mask = pd.Series([False] * len(schedule))

    for variation in variations:
        if 'home_team' in schedule.columns:
            mask |= schedule['home_team'].str.contains(variation, case=False, na=False, regex=False)
        if 'away_team' in schedule.columns:
            mask |= schedule['away_team'].str.contains(variation, case=False, na=False, regex=False)

    return schedule[mask].copy()


def get_match_ids(
    team_name: str,
    league: str,
    season: str,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Extraer IDs de partidos de WhoScored y Understat para un equipo.

    Args:
        team_name: Nombre del equipo (e.g., "Atlético Madrid", "Barcelona")
        league: Código de liga (e.g., "ESP-La Liga", "ENG-Premier League")
        season: Temporada en formato YY-YY (e.g., "24-25", "23-24")
        verbose: Mostrar información de progreso

    Returns:
        DataFrame con columnas:
            - date: Fecha del partido
            - home_team: Equipo local
            - away_team: Equipo visitante
            - whoscored_id: ID de WhoScored (int)
            - understat_id: ID de Understat (int)
            - league: Liga
            - season: Temporada

    Raises:
        ValueError: Si la liga no es válida o no está en LEAGUE_DICT

    Examples:
        >>> # Atlético Madrid temporada 24-25
        >>> ids = get_match_ids("Atlético Madrid", "ESP-La Liga", "24-25")
        >>> print(f"Encontrados {len(ids)} partidos")
        >>>
        >>> # Exportar a CSV
        >>> ids.to_csv("atm_matches.csv", index=False)
    """

    if league not in LEAGUE_DICT:
        raise ValueError(f"Liga '{league}' no encontrada en LEAGUE_DICT")

    if verbose:
        print(f"\n{'='*60}")
        print(f"Extrayendo IDs de partidos para:")
        print(f"  Equipo: {team_name}")
        print(f"  Liga: {league}")
        print(f"  Temporada: {season}")
        print(f"{'='*60}\n")

    whoscored_matches = pd.DataFrame()
    understat_matches = pd.DataFrame()

    # Extraer de WhoScored
    if 'WhoScored' in LEAGUE_DICT[league]:
        try:
            if verbose:
                print("Extrayendo de WhoScored...")

            ws = WhoScored(leagues=[league], seasons=[season])
            ws_schedule = ws.read_schedule()

            if not ws_schedule.empty:
                ws_schedule_reset = ws_schedule.reset_index()
                whoscored_matches = _filter_team_matches(ws_schedule_reset, team_name)

                if not whoscored_matches.empty:
                    whoscored_matches = whoscored_matches[['date', 'home_team', 'away_team', 'game_id']].copy()
                    whoscored_matches = whoscored_matches.rename(columns={'game_id': 'whoscored_id'})
                    whoscored_matches['date'] = pd.to_datetime(whoscored_matches['date']).dt.tz_localize(None)

                    if verbose:
                        print(f"   ✓ Encontrados {len(whoscored_matches)} partidos en WhoScored")
                else:
                    if verbose:
                        print(f"   ⚠ No se encontraron partidos de '{team_name}' en WhoScored")
        except Exception as e:
            if verbose:
                print(f"   ✗ Error extrayendo de WhoScored: {e}")
    else:
        if verbose:
            print(f"   ℹ Liga '{league}' no disponible en WhoScored")

    # Extraer de Understat
    if 'Understat' in LEAGUE_DICT[league]:
        try:
            if verbose:
                print("\nExtrayendo de Understat...")

            us = Understat(leagues=[league], seasons=[season])
            us_schedule = us.read_schedule()

            if not us_schedule.empty:
                us_schedule_reset = us_schedule.reset_index()
                understat_matches = _filter_team_matches(us_schedule_reset, team_name)

                if not understat_matches.empty:
                    understat_matches = understat_matches[['date', 'home_team', 'away_team', 'game_id']].copy()
                    understat_matches = understat_matches.rename(columns={'game_id': 'understat_id'})
                    understat_matches['date'] = pd.to_datetime(understat_matches['date']).dt.tz_localize(None)

                    if verbose:
                        print(f"   ✓ Encontrados {len(understat_matches)} partidos en Understat")
                else:
                    if verbose:
                        print(f"   ⚠ No se encontraron partidos de '{team_name}' en Understat")
        except Exception as e:
            if verbose:
                print(f"   ✗ Error extrayendo de Understat: {e}")
    else:
        if verbose:
            print(f"   ℹ Liga '{league}' no disponible en Understat")

    # Merge de ambas fuentes
    if not whoscored_matches.empty and not understat_matches.empty:
        merged = pd.merge(
            whoscored_matches,
            understat_matches[['date', 'understat_id']],
            on='date',
            how='outer'
        )
    elif not whoscored_matches.empty:
        merged = whoscored_matches.copy()
        merged['understat_id'] = None
    elif not understat_matches.empty:
        merged = understat_matches.copy()
        merged['whoscored_id'] = None
    else:
        if verbose:
            print("\nNo se encontraron partidos en ninguna fuente")
        return pd.DataFrame(columns=['date', 'home_team', 'away_team', 'whoscored_id', 'understat_id', 'league', 'season'])

    merged['league'] = league
    merged['season'] = season

    merged = merged.sort_values('date').reset_index(drop=True)

    if verbose:
        print(f"\n{'='*60}")
        print(f"RESUMEN:")
        print(f"   Total partidos encontrados: {len(merged)}")

        ws_count = merged['whoscored_id'].notna().sum()
        us_count = merged['understat_id'].notna().sum()
        both_count = (merged['whoscored_id'].notna() & merged['understat_id'].notna()).sum()

        print(f"   - Con ID WhoScored: {ws_count}")
        print(f"   - Con ID Understat: {us_count}")
        print(f"   - Con ambos IDs: {both_count}")
        print(f"{'='*60}\n")

    return merged


def main():
    """Ejemplo de uso del script."""

    print("\n🔍 MATCH ID EXTRACTOR - WhoScored & Understat\n")

    # Ejemplo 1: Atlético Madrid temporada 24-25
    print("Ejemplo 1: Atlético Madrid 24-25")
    atm_ids = get_match_ids("Atlético Madrid", "ESP-La Liga", "24-25")

    if not atm_ids.empty:
        print("\nPrimeros 5 partidos:")
        print(atm_ids.head())

        # Guardar a CSV
        output_file = "atm_match_ids_24-25.csv"
        atm_ids.to_csv(output_file, index=False)
        print(f"\nGuardado en: {output_file}")

    # Ejemplo 2: Barcelona temporada 23-24
    print("\n" + "="*60 + "\n")
    print("Ejemplo 2: Barcelona 23-24")
    barca_ids = get_match_ids("Barcelona", "ESP-La Liga", "23-24")

    if not barca_ids.empty:
        print("\nPrimeros 5 partidos:")
        print(barca_ids.head())


if __name__ == "__main__":
    main()