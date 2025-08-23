# ====================================================================
# FootballDecoded - WhoScored Optimized Spatial Data Extractor
# ====================================================================
"""
WhoScored Wrapper especializado en datos espaciales y eventos de partido:

DATOS ÚNICOS DE WHOSCORED (imposibles de obtener en FBref/Understat):
- Coordenadas x,y EXACTAS de todos los eventos del partido
- Qualifiers detallados: longball, cross, through ball, etc.
- Redes de pases con posiciones promedio de jugadores
- Mapas de calor de jugadores por zonas tácticas
- Análisis de ocupación del campo por equipos
- Secuencias de posesión con conexiones jugador-jugador

ANÁLISIS ESPACIALES AVANZADOS:
- extract_match_events(): TODOS los eventos con coordenadas
- extract_pass_network(): Red completa de pases con posiciones
- extract_player_heatmap(): Mapa de calor individual por zonas
- extract_shot_map(): Mapa de disparos con ubicaciones exactas
- extract_field_occupation(): Análisis de ocupación por zonas

CARACTERÍSTICAS TÉCNICAS:
- Sistema de caché optimizado para datos espaciales complejos
- Procesamiento de eventos JavaScript en tiempo real
- Clasificación automática de zonas tácticas del campo
- Validación específica para match IDs de WhoScored
- Exportación optimizada para herramientas de visualización

USO TÍPICO:
    from wrappers import whoscored_data
    
    # Todos los eventos espaciales de un partido
    events = whoscored_data.get_match_events(1234567, "ESP-La Liga", "23-24")
    
    # Red de pases de un equipo
    network = whoscored_data.get_pass_network(1234567, "Barcelona", "ESP-La Liga", "23-24")
    
    # Mapa de calor de jugador específico
    heatmap = whoscored_data.get_player_heatmap(1234567, "Messi", "ESP-La Liga", "23-24")
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
import ast
import pickle
import hashlib
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import WhoScored

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# INPUT VALIDATION SYSTEM
# ====================================================================

def _validate_match_inputs(match_id: int, league: str, season: str) -> bool:
    """Validar entradas específicas de WhoScored."""
    # Validar match_id
    if not isinstance(match_id, int) or match_id <= 0:
        raise ValueError("match_id must be a positive integer")
    
    # Validar league
    if not league or not isinstance(league, str):
        raise ValueError("league must be a non-empty string")
    
    # Validar season format (YY-YY)
    if not season or not isinstance(season, str):
        raise ValueError("season must be a string")
    
    season_parts = season.split('-')
    if len(season_parts) != 2:
        raise ValueError(f"season must be in YY-YY format, got '{season}'")
    
    try:
        year1, year2 = int(season_parts[0]), int(season_parts[1])
        if not (0 <= year1 <= 99 and 0 <= year2 <= 99):
            raise ValueError(f"season years must be 00-99, got '{season}'")
        if year2 != (year1 + 1) % 100:
            raise ValueError(f"season must be consecutive years, got '{season}'")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"season must contain valid numbers, got '{season}'")
        raise
    
    return True

def validate_match_inputs_with_suggestions(match_id: int, league: str, season: str) -> Dict[str, Any]:
    """Validar entradas de match con sugerencias."""
    result = {'valid': True, 'errors': [], 'suggestions': []}
    
    try:
        _validate_match_inputs(match_id, league, season)
    except ValueError as e:
        result['valid'] = False
        result['errors'].append(str(e))
        
        if 'match_id' in str(e):
            result['suggestions'].append("Use a positive integer for match_id (e.g., 1234567)")
        if 'season' in str(e) and 'format' in str(e):
            result['suggestions'].append("Use season format like '23-24', '22-23', etc.")
        if 'league' in str(e):
            result['suggestions'].append("Valid leagues: ESP-La Liga, ENG-Premier League, etc.")
    
    return result

# ====================================================================
# INTELLIGENT CACHE SYSTEM
# ====================================================================

CACHE_DIR = Path.home() / ".footballdecoded_cache" / "whoscored"
CACHE_EXPIRY_HOURS = 24

def _ensure_cache_dir():
    """Crear directorio de caché si no existe."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(match_id: int, league: str, season: str, **kwargs) -> str:
    """Generar clave única para cache."""
    cache_data = f"{match_id}:{league}:{season}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def _get_cache_path(cache_key: str) -> Path:
    """Obtener ruta completa del archivo de cache."""
    return CACHE_DIR / f"{cache_key}.pkl"

def _is_cache_valid(cache_path: Path) -> bool:
    """Verificar si el cache es válido."""
    if not cache_path.exists():
        return False
    
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
    return file_time > expiry_time

def _save_to_cache(data: Union[Dict, pd.DataFrame], cache_key: str):
    """Guardar datos en cache."""
    try:
        _ensure_cache_dir()
        cache_path = _get_cache_path(cache_key)
        
        cache_data = {
            'data': data,
            'timestamp': datetime.now(),
            'cache_key': cache_key
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
            
    except Exception as e:
        print(f"Warning: Could not save to cache: {e}")

def _load_from_cache(cache_key: str) -> Optional[Union[Dict, pd.DataFrame]]:
    """Cargar datos del cache si existen y son válidos."""
    try:
        cache_path = _get_cache_path(cache_key)
        
        if not _is_cache_valid(cache_path):
            return None
            
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
            
        return cache_data.get('data')
        
    except Exception as e:
        print(f"Warning: Could not load from cache: {e}")
        return None

def clear_cache():
    """Limpiar todo el cache de WhoScored."""
    try:
        if CACHE_DIR.exists():
            for cache_file in CACHE_DIR.glob("*.pkl"):
                cache_file.unlink()
            print("WhoScored cache cleared successfully")
    except Exception as e:
        print(f"Error clearing cache: {e}")

# ====================================================================
# CORE ENGINE - SPATIAL EVENTS EXTRACTION
# ====================================================================

def extract_match_events(
    match_id: int,
    league: str,
    season: str,
    event_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    for_viz: bool = False,
    verbose: bool = False,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Extract ALL match events with complete spatial coordinates with cache.
    
    Core function - gets EVERYTHING FBref doesn't provide:
    - All events with x/y coordinates (start + end positions)
    - Parsed qualifiers (pass types, body parts, etc.)
    - Tactical zones and spatial analysis
    
    Args:
        match_id: WhoScored match ID
        league: League identifier
        season: Season identifier
        event_filter: Optional event type filter
        player_filter: Optional player name filter
        team_filter: Optional team name filter
        for_viz: If True, optimize for visualization tools
        verbose: Show extraction progress
        use_cache: Usar sistema de cache (default: True)
        
    Returns:
        DataFrame with ALL spatial events and tactical context
    """
    # Validar entradas
    try:
        _validate_match_inputs(match_id, league, season)
    except ValueError as e:
        print(f"WhoScored input validation failed: {e}")
        validation_result = validate_match_inputs_with_suggestions(match_id, league, season)
        if validation_result['suggestions']:
            print("Suggestions:")
            for suggestion in validation_result['suggestions']:
                print(f"  - {suggestion}")
        return pd.DataFrame()
    
    # Generar clave de cache
    cache_key = _generate_cache_key(
        match_id, league, season,
        event_filter=event_filter, player_filter=player_filter,
        team_filter=team_filter, for_viz=for_viz
    )
    
    # Intentar cargar desde cache
    if use_cache:
        cached_data = _load_from_cache(cache_key)
        if cached_data is not None:
            if verbose:
                print(f"Loading match {match_id} events from cache")
            return cached_data
    
    if verbose:
        print(f"Extracting spatial data from match {match_id}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        
        if verbose:
            print("Reading event stream...")
        
        events_df = whoscored.read_events(match_id=match_id, output_fmt='events')
        
        if events_df is None or events_df.empty:
            if verbose:
                print(f"No events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"Raw data: {len(events_df)} events extracted")
        
        enhanced_events = _process_spatial_events(events_df, match_id, for_viz)
        filtered_events = _apply_filters(enhanced_events, event_filter, player_filter, team_filter, verbose)
        
        if verbose and not filtered_events.empty:
            total_events = len(filtered_events)
            unique_players = filtered_events['player'].nunique()
            event_types = filtered_events['event_type'].nunique()
            
            print(f"SUCCESS: {total_events} spatial events with coordinates")
            print(f"Players: {unique_players} | Event types: {event_types}")
        
        # Guardar en cache si está habilitado
        if use_cache and not filtered_events.empty:
            _save_to_cache(filtered_events, cache_key)
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"Event extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# SPECIALIZED SPATIAL ANALYSIS
# ====================================================================

def extract_pass_network(
    match_id: int,
    team_name: str,
    league: str,
    season: str,
    min_passes: int = 3,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Extract complete pass network with coordinates and connections.
    
    Creates what FBref cannot: actual pass networks with:
    - Average positions per player with coordinates
    - Pass connections between players (frequency + success rates)
    - Spatial distribution of passes
    
    Returns:
        Dict with 'passes', 'positions', and 'connections' DataFrames
    """
    if verbose:
        print(f"Creating pass network for {team_name}")
    
    pass_events = extract_match_events(
        match_id, league, season, 
        event_filter='Pass',
        team_filter=team_name,
        verbose=False
    )
    
    if pass_events.empty:
        if verbose:
            print(f"No pass events found for {team_name}")
        return {'passes': pd.DataFrame(), 'positions': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    network_data = _calculate_pass_network(pass_events, team_name, min_passes)
    
    if verbose and network_data['passes'] is not None and not network_data['passes'].empty:
        total_passes = len(network_data['passes'])
        successful_passes = len(network_data['passes'][network_data['passes']['is_successful'] == True])
        success_rate = (successful_passes / total_passes * 100) if total_passes > 0 else 0
        
        print(f"Pass network: {total_passes} passes analyzed")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Players: {len(network_data['positions'])} | Connections: {len(network_data['connections'])}")
    
    return network_data


def extract_player_heatmap(
    match_id: int,
    player_name: str,
    league: str,
    season: str,
    event_types: Optional[List[str]] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract player heatmap with precise spatial distribution.
    
    Creates detailed spatial analysis FBref cannot provide:
    - Action frequency by field zones
    - Average positions per zone
    - Success rates by spatial location
    """
    if verbose:
        print(f"Creating spatial heatmap for {player_name}")
    
    events_df = extract_match_events(
        match_id, league, season, 
        player_filter=player_name, 
        verbose=False
    )
    
    if events_df.empty:
        if verbose:
            print(f"No events found for {player_name}")
        return pd.DataFrame()
    
    if event_types:
        events_df = events_df[events_df['event_type'].isin(event_types)]
    
    if events_df.empty:
        if verbose:
            print(f"No events of specified types for {player_name}")
        return pd.DataFrame()
    
    heatmap_data = _calculate_player_heatmap(events_df, player_name)
    
    if verbose and not heatmap_data.empty:
        total_actions = heatmap_data['action_count'].sum()
        active_zones = len(heatmap_data[heatmap_data['action_count'] > 0])
        max_zone_actions = heatmap_data['action_count'].max()
        
        print(f"Heatmap: {total_actions} actions across {active_zones} zones")
        print(f"Hottest zone: {max_zone_actions} actions")
    
    return heatmap_data


def extract_shot_map(
    match_id: int,
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract detailed shot map with coordinates and spatial analysis.
    
    Provides shot location data FBref doesn't have:
    - Exact shot coordinates (x, y)
    - Distance and angle to goal
    - Shot zones classification
    """
    if verbose:
        print("Creating shot map with spatial analysis")
    
    shot_events = extract_match_events(
        match_id, league, season,
        event_filter='Shot',
        team_filter=team_filter,
        player_filter=player_filter,
        verbose=False
    )
    
    if shot_events.empty:
        if verbose:
            print("No shot events found")
        return pd.DataFrame()
    
    enhanced_shots = _analyze_shot_events(shot_events)
    
    if verbose and not enhanced_shots.empty:
        total_shots = len(enhanced_shots)
        goals = len(enhanced_shots[enhanced_shots.get('is_goal', False) == True])
        shots_on_target = len(enhanced_shots[enhanced_shots.get('is_on_target', False) == True])
        
        print(f"Shot map: {total_shots} shots analyzed")
        print(f"Goals: {goals} | On target: {shots_on_target}")
    
    return enhanced_shots


def extract_field_occupation(
    match_id: int,
    team_name: str,
    league: str,
    season: str,
    time_period: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract field occupation patterns by zones.
    
    Analyzes spatial dominance FBref cannot provide:
    - Event density by field zones
    - Territorial control percentages
    - Zone-specific activity patterns
    """
    if verbose:
        print(f"Analyzing field occupation for {team_name}")
    
    team_events = extract_match_events(
        match_id, league, season, 
        team_filter=team_name,
        verbose=False
    )
    
    if team_events.empty:
        if verbose:
            print(f"No events found for {team_name}")
        return pd.DataFrame()
    
    if time_period:
        team_events = _filter_by_time_period(team_events, time_period)
    
    occupation_data = _calculate_field_occupation(team_events, team_name)
    
    if verbose and not occupation_data.empty:
        total_events = occupation_data['event_count'].sum()
        dominant_zone = occupation_data.loc[occupation_data['event_count'].idxmax(), 'field_zone']
        
        print(f"Occupation: {total_events} events analyzed")
        print(f"Dominant zone: {dominant_zone}")
    
    return occupation_data


# ====================================================================
# SCHEDULE AND CONTEXT
# ====================================================================

def extract_league_schedule(
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract complete league schedule for match ID discovery."""
    if verbose:
        print(f"Extracting schedule for {league} {season}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        schedule = whoscored.read_schedule()
        
        if verbose and not schedule.empty:
            total_matches = len(schedule)
            completed_matches = len(schedule[schedule['score'].notna()])
            
            print(f"Schedule: {total_matches} matches ({completed_matches} completed)")
        
        return schedule
        
    except Exception as e:
        if verbose:
            print(f"Schedule extraction failed: {str(e)}")
        return pd.DataFrame()


def extract_missing_players(
    match_id: int,
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract injured and suspended players for tactical context."""
    if verbose:
        print(f"Extracting missing players for match {match_id}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        missing_players = whoscored.read_missing_players(match_id=match_id)
        
        if verbose and not missing_players.empty:
            total_missing = len(missing_players)
            teams_affected = missing_players.index.get_level_values('team').nunique()
            
            print(f"Missing players: {total_missing} across {teams_affected} teams")
        
        return missing_players
        
    except Exception as e:
        if verbose:
            print(f"Missing players extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# CORE PROCESSING FUNCTIONS
# ====================================================================

def _process_spatial_events(events_df: pd.DataFrame, match_id: int, for_viz: bool = False) -> pd.DataFrame:
    """Process raw events into spatial analysis format."""
    
    if events_df.empty:
        return events_df
    
    enhanced_df = events_df.copy()
    
    enhanced_df['match_id'] = match_id
    enhanced_df['data_source'] = 'whoscored'
    
    enhanced_df = _unify_coordinates(enhanced_df)
    enhanced_df = _parse_qualifiers(enhanced_df)
    
    enhanced_df['field_zone'] = _classify_field_zones(enhanced_df['x'], enhanced_df['y'])
    enhanced_df['is_successful'] = _classify_event_success(enhanced_df)
    enhanced_df['event_type'] = enhanced_df['type'].fillna('Unknown')
    
    enhanced_df = _add_sequence_tracking(enhanced_df)
    enhanced_df = _add_spatial_calculations(enhanced_df)
    
    if for_viz:
        enhanced_df = _optimize_for_visualization(enhanced_df)
    
    return enhanced_df


def _unify_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Unify coordinate system for consistent spatial analysis."""
    if 'x' in df.columns and 'y' in df.columns:
        df['x'] = pd.to_numeric(df['x'], errors='coerce')
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
    
    if 'end_x' in df.columns and 'end_y' in df.columns:
        df['end_x'] = pd.to_numeric(df['end_x'], errors='coerce')
        df['end_y'] = pd.to_numeric(df['end_y'], errors='coerce')
    
    return df


def _parse_qualifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Parse key qualifiers into separate usable columns."""
    
    qualifier_columns = {
        'pass_length': None,
        'is_longball': False,
        'is_header': False,
        'is_cross': False,
        'is_through_ball': False,
        'shot_body_part': None,
        'card_type': None,
        'is_assist': False
    }
    
    for col, default_value in qualifier_columns.items():
        df[col] = default_value
    
    for idx in range(len(df)):
        try:
            qualifiers_str = str(df.iloc[idx]['qualifiers'])
            
            if qualifiers_str and qualifiers_str != '[]' and qualifiers_str != 'nan':
                qualifiers = ast.literal_eval(qualifiers_str)
                
                for q in qualifiers:
                    if isinstance(q, dict) and 'type' in q:
                        qualifier_name = q['type'].get('displayName', '')
                        
                        if qualifier_name == 'Longball':
                            df.iloc[idx, df.columns.get_loc('is_longball')] = True
                        elif qualifier_name == 'Cross':
                            df.iloc[idx, df.columns.get_loc('is_cross')] = True
                        elif qualifier_name == 'ThroughBall':
                            df.iloc[idx, df.columns.get_loc('is_through_ball')] = True
                        elif qualifier_name == 'Head':
                            df.iloc[idx, df.columns.get_loc('shot_body_part')] = 'Head'
                        elif qualifier_name == 'KeyPass':
                            df.iloc[idx, df.columns.get_loc('is_assist')] = True
                        
        except Exception:
            continue
    
    return df


def _classify_field_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify field positions into 9 tactical zones."""
    
    zones = []
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x)
        y_pct = float(y)
        
        if x_pct <= 33.33:
            if y_pct <= 33.33:
                zone = 'Defensive_Left'
            elif y_pct <= 66.66:
                zone = 'Defensive_Center'
            else:
                zone = 'Defensive_Right'
        elif x_pct <= 66.66:
            if y_pct <= 33.33:
                zone = 'Middle_Left'
            elif y_pct <= 66.66:
                zone = 'Middle_Center'
            else:
                zone = 'Middle_Right'
        else:
            if y_pct <= 33.33:
                zone = 'Attacking_Left'
            elif y_pct <= 66.66:
                zone = 'Attacking_Center'
            else:
                zone = 'Attacking_Right'
        
        zones.append(zone)
    
    return pd.Series(zones, index=x_coords.index)


def _classify_event_success(events_df: pd.DataFrame) -> pd.Series:
    """Classify event success based on outcome type."""
    if 'outcome_type' not in events_df.columns:
        return pd.Series([False] * len(events_df))
    
    successful_outcomes = ['Successful', 'Goal', 'Assist', 'Won']
    return events_df['outcome_type'].isin(successful_outcomes)


def _add_sequence_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Add possession sequence tracking for pass network analysis."""
    
    df = df.sort_values(['minute', 'second']).reset_index(drop=True)
    
    df['possession_sequence'] = 0
    df['next_player'] = None
    
    current_sequence = 0
    current_team = None
    
    for idx in range(len(df)):
        if current_team != df.iloc[idx]['team']:
            current_sequence += 1
            current_team = df.iloc[idx]['team']
        
        df.iloc[idx, df.columns.get_loc('possession_sequence')] = current_sequence
        
        if idx < len(df) - 1:
            next_event = df.iloc[idx + 1]
            
            time_current = df.iloc[idx]['minute'] * 60 + df.iloc[idx]['second']
            time_next = next_event['minute'] * 60 + next_event['second']
            time_diff = time_next - time_current
            
            if (next_event['team'] == df.iloc[idx]['team'] and 0 <= time_diff <= 10):
                df.iloc[idx, df.columns.get_loc('next_player')] = next_event['player']
    
    return df


def _add_spatial_calculations(df: pd.DataFrame) -> pd.DataFrame:
    """Add spatial calculation columns."""
    
    df['distance_to_goal'] = _calculate_distance_to_goal(df['x'], df['y'])
    df['pass_distance'] = _calculate_pass_distance(df['x'], df['y'], df['end_x'], df['end_y'])
    
    return df


def _calculate_distance_to_goal(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calculate distance to goal center."""
    
    distances = []
    goal_x, goal_y = 100, 50
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        distance = np.sqrt((x - goal_x)**2 + (y - goal_y)**2)
        distances.append(round(distance, 2))
    
    return pd.Series(distances, index=x_coords.index)


def _calculate_pass_distance(x1: pd.Series, y1: pd.Series, x2: pd.Series, y2: pd.Series) -> pd.Series:
    """Calculate pass distance from coordinates."""
    
    distances = []
    
    for start_x, start_y, end_x, end_y in zip(x1, y1, x2, y2):
        if pd.isna(start_x) or pd.isna(end_x):
            distances.append(None)
            continue
        
        distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        distances.append(round(distance, 2))
    
    return pd.Series(distances, index=x1.index)


def _optimize_for_visualization(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame for visualization tools."""
    
    viz_df = df.copy()
    
    bool_cols = ['is_successful', 'is_longball', 'is_header', 'is_cross', 'is_through_ball', 'is_assist']
    
    for col in bool_cols:
        if col in viz_df.columns:
            viz_df[col] = viz_df[col].astype(bool)
    
    numeric_cols = ['x', 'y', 'end_x', 'end_y', 'minute', 'second', 'distance_to_goal', 'pass_distance']
    
    for col in numeric_cols:
        if col in viz_df.columns:
            viz_df[col] = pd.to_numeric(viz_df[col], errors='coerce')
    
    processing_cols = ['qualifiers', 'goal_mouth_y', 'goal_mouth_z', 'blocked_x', 'blocked_y']
    viz_df = viz_df.drop([col for col in processing_cols if col in viz_df.columns], axis=1)
    
    return viz_df

def _calculate_pass_network(pass_events: pd.DataFrame, team_name: str, min_passes: int) -> Dict[str, pd.DataFrame]:
    """Calculate pass network components."""
    
    results = {
        'passes': pd.DataFrame(),
        'positions': pd.DataFrame(),
        'connections': pd.DataFrame()
    }
    
    if pass_events.empty:
        return results
    
    successful_passes = pass_events[pass_events['is_successful'] == True]
    
    results['passes'] = successful_passes.copy()
    
    if not successful_passes.empty:
        positions = successful_passes.groupby('player').agg({
            'x': 'mean',
            'y': 'mean',
            'match_id': 'count',
            'is_cross': 'sum',
            'is_longball': 'sum'
        }).round(2)
        
        positions.columns = ['avg_x', 'avg_y', 'total_passes', 'crosses', 'longballs']
        positions['team'] = team_name
        results['positions'] = positions.reset_index()
    
    connections = []
    
    for _, event in successful_passes.iterrows():
        if pd.notna(event['next_player']) and event['next_player'] != event['player']:
            connections.append({
                'team': event['team'],
                'source': event['player'],
                'target': event['next_player'],
                'source_x': event['x'],
                'source_y': event['y'],
                'target_x': event['end_x'] if pd.notna(event['end_x']) else None,
                'target_y': event['end_y'] if pd.notna(event['end_y']) else None
            })
    
    if connections:
        connections_df = pd.DataFrame(connections)
        
        directional_counts = connections_df.groupby(['team', 'source', 'target']).agg({
            'source_x': 'mean',
            'source_y': 'mean', 
            'target_x': 'mean',
            'target_y': 'mean',
            'team': 'count'
        }).round(2)
        
        directional_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
        directional_counts = directional_counts.reset_index()
        
        bidirectional_connections = []
        processed_pairs = set()
        
        for _, conn in directional_counts.iterrows():
            source = conn['source']
            target = conn['target']
            pass_count_a_to_b = conn['pass_count']
            
            reverse_conn = directional_counts[
                (directional_counts['source'] == target) & 
                (directional_counts['target'] == source)
            ]
            
            pass_count_b_to_a = reverse_conn['pass_count'].iloc[0] if not reverse_conn.empty else 0
            
            pair_id = tuple(sorted([source, target]))
            
            if pair_id not in processed_pairs:
                processed_pairs.add(pair_id)
                
                if pass_count_a_to_b >= min_passes or pass_count_b_to_a >= min_passes:
                    
                    if pass_count_a_to_b >= min_passes:
                        bidirectional_connections.append({
                            'team': conn['team'],
                            'source': source,
                            'target': target,
                            'pass_count': pass_count_a_to_b,
                            'direction': 'A_to_B',
                            'avg_source_x': conn['avg_source_x'],
                            'avg_source_y': conn['avg_source_y'],
                            'avg_target_x': conn['avg_target_x'],
                            'avg_target_y': conn['avg_target_y']
                        })
                    
                    if pass_count_b_to_a >= min_passes and not reverse_conn.empty:
                        bidirectional_connections.append({
                            'team': conn['team'],
                            'source': target,
                            'target': source,
                            'pass_count': pass_count_b_to_a,
                            'direction': 'B_to_A',
                            'avg_source_x': reverse_conn.iloc[0]['avg_source_x'],
                            'avg_source_y': reverse_conn.iloc[0]['avg_source_y'],
                            'avg_target_x': reverse_conn.iloc[0]['avg_target_x'],
                            'avg_target_y': reverse_conn.iloc[0]['avg_target_y']
                        })
        
        results['connections'] = pd.DataFrame(bidirectional_connections)
    
    return results

def _calculate_player_heatmap(events_df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    """Calculate spatial heatmap for player."""
    
    zone_analysis = events_df.groupby('field_zone').agg({
        'match_id': 'count',
        'is_successful': ['sum', 'mean'],
        'x': 'mean',
        'y': 'mean'
    }).round(2)
    
    zone_analysis.columns = ['action_count', 'successful_actions', 'success_rate', 'avg_x', 'avg_y']
    
    zone_analysis['player'] = player_name
    zone_analysis['total_actions'] = len(events_df)
    zone_analysis['zone_percentage'] = (zone_analysis['action_count'] / zone_analysis['total_actions'] * 100).round(2)
    zone_analysis['success_rate'] = (zone_analysis['success_rate'] * 100).round(2)
    
    return zone_analysis.reset_index()


def _analyze_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Enhance shot events with spatial analysis."""
    
    enhanced_df = shot_events.copy()
    
    if 'outcome_type' in enhanced_df.columns:
        enhanced_df['is_goal'] = enhanced_df['outcome_type'].str.contains('Goal', case=False, na=False)
        enhanced_df['is_on_target'] = enhanced_df['outcome_type'].isin(['Goal', 'Saved', 'SavedShot'])
        enhanced_df['is_blocked'] = enhanced_df['outcome_type'].str.contains('Block', case=False, na=False)
    
    enhanced_df['shot_zone'] = _classify_shot_zones(enhanced_df['x'], enhanced_df['y'])
    
    return enhanced_df


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify shots into tactical zones."""
    
    zones = []
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x)
        y_pct = float(y)
        
        if x_pct >= 88:
            zones.append('Six_Yard_Box')
        elif x_pct >= 83:
            if 35 <= y_pct <= 65:
                zones.append('Central_Penalty_Box')
            else:
                zones.append('Wide_Penalty_Box')
        elif x_pct >= 67:
            zones.append('Penalty_Area_Edge')
        else:
            zones.append('Long_Range')
    
    return pd.Series(zones, index=x_coords.index)


def _calculate_field_occupation(team_events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Calculate field occupation by zones."""
    
    occupation_data = team_events.groupby('field_zone').agg({
        'match_id': 'count',
        'is_successful': ['sum', 'mean'],
        'x': 'mean',
        'y': 'mean'
    }).round(2)
    
    occupation_data.columns = ['event_count', 'successful_events', 'success_rate', 'avg_x', 'avg_y']
    
    total_events = occupation_data['event_count'].sum()
    occupation_data['occupation_percentage'] = (occupation_data['event_count'] / total_events * 100).round(2)
    occupation_data['success_rate'] = (occupation_data['success_rate'] * 100).round(2)
    occupation_data['team'] = team_name
    
    return occupation_data.reset_index()


def _filter_by_time_period(events: pd.DataFrame, time_period: str) -> pd.DataFrame:
    """Filter events by specific time periods."""
    
    if time_period == 'first_half':
        return events[events['minute'] <= 45]
    elif time_period == 'second_half':
        return events[events['minute'] > 45]
    elif time_period == 'first_30':
        return events[events['minute'] <= 30]
    elif time_period == 'last_30':
        return events[events['minute'] >= 60]
    else:
        return events


def _apply_filters(
    events_df: pd.DataFrame,
    event_filter: Optional[str],
    player_filter: Optional[str],
    team_filter: Optional[str],
    verbose: bool
) -> pd.DataFrame:
    """Apply various filters to event data."""
    
    filtered_df = events_df.copy()
    
    if event_filter:
        if verbose:
            print(f"Applying event filter: {event_filter}")
        mask = filtered_df['event_type'].str.contains(event_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    if player_filter:
        if verbose:
            print(f"Applying player filter: {player_filter}")
        mask = filtered_df['player'].str.contains(player_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    if team_filter:
        if verbose:
            print(f"Applying team filter: {team_filter}")
        mask = filtered_df['team'].str.contains(team_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    return filtered_df


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(
    data: Union[Dict, pd.DataFrame],
    filename: str,
    include_timestamp: bool = True,
    for_viz: bool = False
) -> str:
    """Export spatial data to CSV optimized for analysis and visualization."""
    if isinstance(data, dict):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
        files_created = []
        
        for key, df in data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                if for_viz:
                    df = _optimize_for_visualization(df)
                
                file_suffix = f"_{timestamp}" if timestamp else ""
                full_filename = f"{filename}_{key}{file_suffix}.csv"
                df.to_csv(full_filename, index=False, encoding='utf-8')
                files_created.append(full_filename)
        
        print(f"Exported {len(files_created)} spatial data files")
        return ", ".join(files_created)
    else:
        df = data.copy()
        
        if for_viz:
            df = _optimize_for_visualization(df)
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_viz" if for_viz else ""
            full_filename = f"{filename}{suffix}_{timestamp}.csv"
        else:
            suffix = "_viz" if for_viz else ""
            full_filename = f"{filename}{suffix}.csv"
        
        df.to_csv(full_filename, index=False, encoding='utf-8')
        
        print(f"Exported spatial data: {full_filename}")
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        
        return full_filename


# ====================================================================
# AUTOMATIC ID RETRIEVAL FUNCTIONS
# ====================================================================

def get_match_ids(league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Extraer automáticamente IDs de partidos de WhoScored para una liga y temporada.
    
    Args:
        league: Código de liga (e.g., 'ESP-La Liga', 'ENG-Premier League')
        season: Temporada en formato YY-YY (e.g., '23-24')
        team_filter: Filtro opcional por nombre de equipo
        
    Returns:
        DataFrame con columnas: match_id, home_team, away_team, date
        
    Raises:
        ValueError: Si la liga o temporada no son válidas
        ConnectionError: Si falla la conexión con WhoScored
    """
    try:
        from ..scrappers.whoscored import WhoScoredReader
        
        scraper = WhoScoredReader(league=league, season=season)
        schedule_data = scraper.read_schedule()
        
        if schedule_data.empty:
            print(f"No matches found for {league} {season}")
            return pd.DataFrame()
        
        # Extraer match_ids y información básica
        match_info = []
        for _, match in schedule_data.iterrows():
            if 'match_id' in match and pd.notna(match['match_id']):
                match_info.append({
                    'match_id': int(match['match_id']),
                    'home_team': match.get('home_team', 'Unknown'),
                    'away_team': match.get('away_team', 'Unknown'),
                    'date': match.get('date', 'Unknown'),
                    'league': league,
                    'season': season
                })
        
        result_df = pd.DataFrame(match_info)
        
        # Aplicar filtro de equipo si se especifica
        if team_filter and not result_df.empty:
            mask = (
                result_df['home_team'].str.contains(team_filter, case=False, na=False, regex=False) |
                result_df['away_team'].str.contains(team_filter, case=False, na=False, regex=False)
            )
            result_df = result_df[mask]
        
        print(f"Found {len(result_df)} matches for {league} {season}")
        if team_filter:
            print(f"Filtered by team: {team_filter}")
            
        return result_df.sort_values('date').reset_index(drop=True)
        
    except ImportError as e:
        raise ConnectionError(f"Cannot import WhoScored scraper: {e}")
    except Exception as e:
        raise ConnectionError(f"Error retrieving match IDs from WhoScored: {e}")


def search_player_id(player_name: str, match_id: int, league: str, season: str) -> Optional[Dict[str, Any]]:
    """
    Buscar automáticamente información de jugador en eventos de partido de WhoScored.
    
    Args:
        player_name: Nombre del jugador a buscar
        match_id: ID del partido donde buscar
        league: Código de liga
        season: Temporada en formato YY-YY
        
    Returns:
        Dict con información del jugador encontrado, o None si no se encuentra
    """
    try:
        # Extraer eventos del partido
        match_events = extract_match_events(match_id, league, season, verbose=False)
        
        if match_events.empty:
            return None
        
        # Buscar jugador en los eventos
        player_events = match_events[
            match_events['player'].str.contains(player_name, case=False, na=False, regex=False)
        ]
        
        if not player_events.empty:
            first_event = player_events.iloc[0]
            return {
                'player_name': first_event['player'],
                'team': first_event['team'],
                'match_id': match_id,
                'league': league,
                'season': season,
                'found': True,
                'total_events': len(player_events),
                'whoscored_data_available': True
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching for player {player_name}: {e}")
        return None


def search_team_id(team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
    """
    Buscar automáticamente información de equipo en WhoScored schedule.
    
    Args:
        team_name: Nombre del equipo a buscar
        league: Código de liga
        season: Temporada en formato YY-YY
        
    Returns:
        Dict con información del equipo encontrado, o None si no se encuentra
    """
    try:
        # Usar get_match_ids para obtener el schedule
        schedule_data = get_match_ids(league, season, team_filter=team_name)
        
        if not schedule_data.empty:
            # Obtener información del primer partido encontrado
            first_match = schedule_data.iloc[0]
            
            # Determinar si es equipo local o visitante
            is_home = team_name.lower() in first_match['home_team'].lower()
            actual_team_name = first_match['home_team'] if is_home else first_match['away_team']
            
            return {
                'team_name': actual_team_name,
                'league': league,
                'season': season,
                'found': True,
                'total_matches': len(schedule_data),
                'whoscored_data_available': True
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching for team {team_name}: {e}")
        return None


# ====================================================================
# QUICK ACCESS FUNCTIONS - SIMPLIFIED API
# ====================================================================

def get_match_events(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Quick access to complete match events with spatial data."""
    return extract_match_events(match_id, league, season, verbose=False)

def get_match_events_viz(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Quick access to visualization-optimized match events."""
    return extract_match_events(match_id, league, season, for_viz=True, verbose=False)

def get_pass_network(match_id: int, team: str, league: str, season: str) -> Dict[str, pd.DataFrame]:
    """Quick access to complete pass network analysis."""
    return extract_pass_network(match_id, team, league, season, verbose=False)

def get_player_heatmap(match_id: int, player: str, league: str, season: str) -> pd.DataFrame:
    """Quick access to player spatial heatmap."""
    return extract_player_heatmap(match_id, player, league, season, verbose=False)

def get_shot_map(match_id: int, league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Quick access to shot map with coordinates."""
    return extract_shot_map(match_id, league, season, team_filter=team, verbose=False)

def get_field_occupation(match_id: int, team: str, league: str, season: str) -> pd.DataFrame:
    """Quick access to field occupation analysis."""
    return extract_field_occupation(match_id, team, league, season, verbose=False)

def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Quick access to league schedule."""
    return extract_league_schedule(league, season, verbose=False)

def get_missing_players(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Quick access to missing players data."""
    return extract_missing_players(match_id, league, season, verbose=False)