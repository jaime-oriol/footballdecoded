# ====================================================================
# FootballDecoded - FBref Optimized Data Extractor
# ====================================================================

import sys
import os
import pandas as pd
import warnings
from typing import Dict, List, Optional, Union
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import FBref

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# CORE ENGINE - UNIFIED EXTRACTION
# ====================================================================

def extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False
) -> Optional[Dict]:
    """
    Motor de extracción unificado para jugadores y equipos.
    
    Args:
        entity_name: Nombre del jugador o equipo
        entity_type: 'player' o 'team'
        league: ID de liga
        season: ID de temporada
        match_id: ID de partido opcional para datos específicos del partido
        include_opponent_stats: Incluir estadísticas del oponente (solo equipos)
        
    Returns:
        Dict con todas las estadísticas FBref disponibles
    """
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        
        if entity_type == 'player':
            if match_id:
                stat_types = ['summary', 'passing', 'passing_types', 'defense', 'possession', 'misc', 'keepers']
            else:
                stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation', 
                             'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        else:
            stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation',
                         'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        
        extracted_data = {}
        basic_info = {}
        
        for stat_type in stat_types:
            try:
                if entity_type == 'player':
                    if match_id:
                        stats = fbref.read_player_match_stats(stat_type=stat_type, match_id=match_id)
                    else:
                        stats = fbref.read_player_season_stats(stat_type=stat_type)
                    entity_row = _find_entity(stats, entity_name, 'player')
                else:
                    stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=False)
                    entity_row = _find_entity(stats, entity_name, 'team')
                
                if entity_row is not None:
                    if not basic_info:
                        basic_info = _extract_basic_info(entity_row, entity_name, entity_type, match_id)
                    
                    _process_columns(entity_row, extracted_data)
                    
                    if entity_type == 'team' and include_opponent_stats and not match_id:
                        try:
                            opp_stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=True)
                            opp_row = _find_entity(opp_stats, entity_name, 'team')
                            if opp_row is not None:
                                _process_columns(opp_row, extracted_data, prefix='opponent_')
                        except Exception:
                            pass
                            
            except Exception:
                continue
        
        if not basic_info:
            return None
        
        final_data = {**basic_info, **extracted_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        return standardized_data
        
    except Exception:
        return None


# ====================================================================
# BATCH EXTRACTION
# ====================================================================

def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False
) -> pd.DataFrame:
    """
    Extraer múltiples entidades de manera eficiente.
    
    Args:
        entities: Lista de nombres de entidades
        entity_type: 'player' o 'team'
        league: Identificador de liga
        season: Identificador de temporada
        match_id: ID de partido opcional
        include_opponent_stats: Incluir estadísticas del oponente (solo equipos)
        
    Returns:
        DataFrame con estadísticas de todas las entidades
    """
    all_data = []
    
    for entity_name in entities:
        entity_data = extract_data(
            entity_name, entity_type, league, season, match_id, include_opponent_stats
        )
        
        if entity_data:
            all_data.append(entity_data)
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


# ====================================================================
# SPECIALIZED EXTRACTION FUNCTIONS
# ====================================================================

def extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None
) -> pd.DataFrame:
    """Extraer todos los jugadores de una liga con filtrado opcional."""
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        player_stats = fbref.read_player_season_stats(stat_type='standard')
        
        if player_stats is None or player_stats.empty:
            return pd.DataFrame()
        
        players_df = player_stats.reset_index()
        
        if team_filter:
            players_df = players_df[players_df['team'].str.contains(team_filter, case=False, na=False)]
        if position_filter:
            players_df = players_df[players_df['pos'].str.contains(position_filter, case=False, na=False)]
        
        columns = ['player', 'team', 'league', 'season']
        optional_cols = ['pos', 'age', 'nation']
        for col in optional_cols:
            if col in players_df.columns:
                columns.append(col)
        
        result_df = players_df[columns].sort_values(['team', 'player'])
        
        return result_df
        
    except Exception:
        return pd.DataFrame()


def extract_match_events(
    match_id: str,
    league: str,
    season: str,
    event_type: str = 'all'
) -> Union[pd.DataFrame, Dict]:
    """Extraer eventos de partido (goles, tarjetas, sustituciones, disparos)."""
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        result = {}
        
        if event_type in ['all', 'events']:
            events = fbref.read_events(match_id=match_id)
            if event_type == 'events':
                return events
            result['events'] = events
        
        if event_type in ['all', 'shots']:
            shots = fbref.read_shot_events(match_id=match_id)
            if event_type == 'shots':
                return shots
            result['shots'] = shots
        
        if event_type in ['all', 'lineups']:
            lineups = fbref.read_lineup(match_id=match_id)
            if event_type == 'lineups':
                return lineups
            result['lineups'] = lineups
        
        return result if event_type == 'all' else pd.DataFrame()
        
    except Exception:
        return pd.DataFrame() if event_type != 'all' else {}


def extract_league_schedule(
    league: str,
    season: str
) -> pd.DataFrame:
    """Extraer calendario completo de liga con resultados."""
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        schedule = fbref.read_schedule()
        
        return schedule
        
    except Exception:
        return pd.DataFrame()


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str) -> Optional[pd.DataFrame]:
    """Encontrar entidad con coincidencia flexible de nombres."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(entity_name, entity_type)
    index_level = entity_type
    
    # Intentar coincidencias exactas primero
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.lower() == variation.lower()]
        if not matches.empty:
            return matches
    
    # Intentar coincidencias parciales
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.contains(
            variation, case=False, na=False, regex=False)]
        if not matches.empty:
            return matches
    
    return None


def _generate_name_variations(name: str, entity_type: str) -> List[str]:
    """Generar variaciones de nombres para coincidencia robusta."""
    variations = [name]
    
    # Eliminar acentos
    clean_name = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != name:
        variations.append(clean_name)
    
    # Añadir componentes del nombre
    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) > 1:
            variations.append(' '.join(parts[:2]))
            variations.append(' '.join(parts[-2:]))
    
    # Variaciones específicas de equipos
    if entity_type == 'team':
        for suffix in [' FC', ' CF', ' United', ' City', ' Real', ' Club']:
            if name.endswith(suffix):
                variations.append(name[:-len(suffix)])
        
        team_mappings = {
            'Real Madrid': ['Madrid', 'Real Madrid CF'],
            'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
            'Manchester United': ['Man United', 'Man Utd', 'United'],
            'Manchester City': ['Man City', 'City'],
            'Tottenham': ['Spurs', 'Tottenham Hotspur']
        }
        if name in team_mappings:
            variations.extend(team_mappings[name])
    
    return list(dict.fromkeys(variations))


def _extract_basic_info(row: pd.DataFrame, name: str, entity_type: str, match_id: Optional[str] = None) -> Dict:
    """Extraer información básica de identificación."""
    if entity_type == 'player':
        basic_info = {
            'player_name': name,
            'league': row.index.get_level_values('league')[0],
            'season': row.index.get_level_values('season')[0],
            'team': row.index.get_level_values('team')[0]
        }
        if match_id:
            basic_info['match_id'] = match_id
            if 'game' in row.index.names:
                basic_info['game'] = row.index.get_level_values('game')[0]
    else:
        basic_info = {
            'team_name': name,
            'league': row.index.get_level_values('league')[0],
            'season': row.index.get_level_values('season')[0],
            'official_team_name': row.index.get_level_values('team')[0]
        }
    
    return basic_info


def _process_columns(row: pd.DataFrame, data_dict: Dict, prefix: str = '') -> None:
    """Procesar todas las columnas de una fila, evitando duplicados."""
    for col in row.columns:
        clean_name = _clean_column_name(col)
        if prefix:
            clean_name = f"{prefix}{clean_name}"
        
        if clean_name not in data_dict:
            data_dict[clean_name] = row.iloc[0][col]


def _clean_column_name(col: Union[str, tuple]) -> str:
    """Limpiar y estandarizar nombres de columnas."""
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        if level1 == '' or pd.isna(level1) or level1 is None:
            return level0
        
        common_categories = ['Standard', 'Performance', 'Expected', 'Total', 'Short', 
                           'Medium', 'Long', 'Playing Time', 'Per 90 Minutes']
        
        if level0 in common_categories:
            return level1
        else:
            return f"{level0}_{level1}"
    
    return str(col)


def _apply_stat_mapping(data: Dict) -> Dict:
    """Aplicar convención de nomenclatura estandarizada."""
    stat_mapping = {
        'nation': 'nationality', 'pos': 'position', 'age': 'age', 'born': 'birth_year',
        'MP': 'matches_played', 'Starts': 'matches_started', 'Min': 'minutes_played',
        '90s': 'full_matches_equivalent', 'Mn/MP': 'minutes_per_match',
        'Gls': 'goals', 'Ast': 'assists', 'G+A': 'goals_plus_assists',
        'G-PK': 'non_penalty_goals', 'PK': 'penalty_goals', 'PKatt': 'penalty_attempts',
        'CrdY': 'yellow_cards', 'CrdR': 'red_cards',
        'Sh': 'shots', 'SoT': 'shots_on_target', 'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90', 'G/Sh': 'goals_per_shot', 'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        'xG': 'expected_goals', 'npxG': 'non_penalty_expected_goals',
        'xAG': 'expected_assists', 'xA': 'expected_assists_alt',
        'npxG+xAG': 'non_penalty_xG_plus_xAG',
        'Cmp': 'passes_completed', 'Att': 'passes_attempted', 'Cmp%': 'pass_completion_pct',
        'TotDist': 'total_pass_distance', 'PrgDist': 'progressive_pass_distance',
        'KP': 'key_passes', '1/3': 'passes_final_third', 'PPA': 'passes_penalty_area',
        'PrgP': 'progressive_passes',
        'Tkl': 'tackles', 'TklW': 'tackles_won', 'Int': 'interceptions',
        'Clr': 'clearances', 'Err': 'errors',
        'Touches': 'touches', 'Succ': 'successful_take_ons', 'Succ%': 'take_on_success_pct',
        'Carries': 'carries', 'PrgC': 'progressive_carries', 'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        'W': 'wins', 'D': 'draws', 'L': 'losses', 'Pts': 'points',
        'GF': 'goals_for', 'GA': 'goals_against', 'GD': 'goal_difference',
        'xGF': 'expected_goals_for', 'xGA': 'expected_goals_against'
    }
    
    standardized_data = {}
    for original_name, value in data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Asegurar orden consistente de columnas."""
    if df.empty:
        return df
    
    if entity_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'match_id', 'game',
            'position', 'age', 'nationality', 'birth_year',
            'minutes_played', 'matches_played', 'matches_started',
            'goals', 'assists', 'goals_plus_assists',
            'expected_goals', 'shots', 'shots_on_target',
            'passes_completed', 'pass_completion_pct', 'key_passes',
            'touches', 'tackles', 'interceptions'
        ]
    else:
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'wins', 'draws', 'losses', 'points', 'goals_for', 'goals_against',
            'expected_goals_for', 'expected_goals_against', 'shots', 'passes_completed'
        ]
    
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_order = available_priority + remaining_columns
    return df[final_order]


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, include_timestamp: bool = True) -> str:
    """Exportar datos a CSV con formato adecuado."""
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    df.to_csv(full_filename, index=False, encoding='utf-8')
    
    return full_filename


# ====================================================================
# QUICK ACCESS FUNCTIONS - SIMPLIFIED API
# ====================================================================

def get_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Extracción rápida de estadísticas de temporada de jugador."""
    return extract_data(player_name, 'player', league, season)

def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Extracción rápida de estadísticas de temporada de equipo."""
    return extract_data(team_name, 'team', league, season)

def get_players(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Extracción rápida de múltiples jugadores."""
    return extract_multiple(players, 'player', league, season)

def get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame:
    """Extracción rápida de múltiples equipos."""
    return extract_multiple(teams, 'team', league, season)

def get_league_players(league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Lista rápida de jugadores de liga."""
    return extract_league_players(league, season, team_filter=team)

def get_match_data(match_id: str, league: str, season: str, data_type: str = 'all') -> Union[pd.DataFrame, Dict]:
    """Extracción rápida de datos de partido."""
    return extract_match_events(match_id, league, season, event_type=data_type)

def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Extracción rápida de calendario de liga."""
    return extract_league_schedule(league, season)