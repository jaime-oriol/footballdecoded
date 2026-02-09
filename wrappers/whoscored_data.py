"""WhoScored spatial data extractor.

Provides match events with x/y coordinates, pass networks, player heatmaps,
shot maps, and field occupation analysis. All data includes tactical zone
classification and spatial calculations.

Main functions:
    extract_match_events()     - All events with coordinates and qualifiers
    extract_pass_network()     - Pass network with positions and connections
    extract_player_heatmap()   - Player action frequency by field zone
    extract_shot_map()         - Shot locations with distance/angle analysis
    extract_field_occupation() - Territorial control by zones

Quick access (no verbose):
    get_match_events(), get_pass_network(), get_player_heatmap(),
    get_shot_map(), get_field_occupation(), get_schedule()
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
import ast
import pickle
import hashlib
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import WhoScored
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# INPUT VALIDATION
# ====================================================================

def _validate_match_inputs(match_id: int, league: str, season: str) -> bool:
    """Validate match_id, league, and season format. Raises ValueError on failure."""
    if not isinstance(match_id, int) or match_id <= 0:
        raise ValueError("match_id must be a positive integer")

    if not league or not isinstance(league, str):
        raise ValueError("league must be a non-empty string")

    if not season or not isinstance(season, str):
        raise ValueError("season must be a string")

    season_parts = season.split('-')
    if len(season_parts) != 2:
        raise ValueError(f"season must be in YY-YY format, got '{season}'")

    try:
        year1, year2 = int(season_parts[0]), int(season_parts[1])
        if not (0 <= year1 <= 99 and 0 <= year2 <= 99):
            raise ValueError(f"season years must be 00-99, got '{season}'")
        # Ensure years are consecutive (handles 99->00 wrap with modulo)
        if year2 != (year1 + 1) % 100:
            raise ValueError(f"season must be consecutive years, got '{season}'")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"season must contain valid numbers, got '{season}'")
        raise
    
    return True

def validate_match_inputs_with_suggestions(match_id: int, league: str, season: str) -> Dict[str, Any]:
    """Validate inputs and return dict with errors and user-friendly suggestions."""
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
            valid_leagues = [league for league in LEAGUE_DICT.keys() if 'WhoScored' in LEAGUE_DICT[league]]
            result['suggestions'].append(f"Valid leagues: {', '.join(valid_leagues[:3])}{'...' if len(valid_leagues) > 3 else ''}")
    
    return result

# ====================================================================
# CACHE SYSTEM
# ====================================================================

CACHE_DIR = Path.home() / ".footballdecoded_cache" / "whoscored"
CACHE_EXPIRY_HOURS = 24

def _ensure_cache_dir():
    """Create cache directory if it does not exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(match_id: int, league: str, season: str, **kwargs) -> str:
    """Generate deterministic MD5 cache key from all parameters."""
    cache_data = f"{match_id}:{league}:{season}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def _get_cache_path(cache_key: str) -> Path:
    """Return full path for a cache key."""
    return CACHE_DIR / f"{cache_key}.pkl"

def _is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is within the 24h expiry window."""
    if not cache_path.exists():
        return False

    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
    return file_time > expiry_time

def _save_to_cache(data: Union[Dict, pd.DataFrame], cache_key: str):
    """Serialize data to pickle cache file."""
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
    """Load data from cache if valid, otherwise return None."""
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
    """Delete all WhoScored pickle cache files."""
    try:
        if CACHE_DIR.exists():
            for cache_file in CACHE_DIR.glob("*.pkl"):
                cache_file.unlink()
            print("WhoScored cache cleared successfully")
    except Exception as e:
        print(f"Error clearing cache: {e}")

# ====================================================================
# CORE - SPATIAL EVENTS EXTRACTION
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
    """Extract all match events with x/y coordinates, qualifiers, and tactical zones.

    Args:
        match_id: WhoScored match ID.
        league: League code (e.g. 'ESP-La Liga').
        season: Season in YY-YY format.
        event_filter: Filter by event type (case-insensitive substring).
        player_filter: Filter by player name (case-insensitive substring).
        team_filter: Filter by team name (case-insensitive substring).
        for_viz: If True, clean types and drop internal columns.
        verbose: Print extraction progress.
        use_cache: Use 24h pickle cache.

    Returns:
        DataFrame with spatial events, or empty DataFrame on failure.
    """
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
    
    cache_key = _generate_cache_key(
        match_id, league, season,
        event_filter=event_filter, player_filter=player_filter,
        team_filter=team_filter, for_viz=for_viz
    )

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
    """Extract pass network with average positions and player-to-player connections.

    Returns:
        Dict with 'passes' (successful passes), 'positions' (avg x/y per player),
        and 'connections' (passer->receiver links filtered by min_passes).
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
    """Extract player action frequency, success rate, and avg position per field zone."""
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
    """Extract shot events with coordinates, distance to goal, and zone classification."""
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
    """Extract event density and territorial control percentage per field zone."""
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
    """Extract league schedule with match IDs, teams, dates, and scores."""
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
    """Extract injured and suspended players for a match."""
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
    """Enrich raw events with zones, qualifiers, sequences, and spatial calculations."""
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
    """Coerce x/y and end_x/end_y columns to numeric."""
    if 'x' in df.columns and 'y' in df.columns:
        df['x'] = pd.to_numeric(df['x'], errors='coerce')
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
    
    if 'end_x' in df.columns and 'end_y' in df.columns:
        df['end_x'] = pd.to_numeric(df['end_x'], errors='coerce')
        df['end_y'] = pd.to_numeric(df['end_y'], errors='coerce')
    
    return df


def _parse_qualifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Parse qualifier dicts into boolean/value columns (longball, cross, header, etc.)."""
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
    """Classify positions into 3x3 tactical grid (defensive/middle/attacking x left/center/right)."""
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
    """Return boolean series: True if outcome_type indicates success."""
    if 'outcome_type' not in events_df.columns:
        return pd.Series([False] * len(events_df))

    successful_outcomes = ['Successful', 'Goal', 'Assist', 'Won']
    return events_df['outcome_type'].isin(successful_outcomes)


def _add_sequence_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Add possession_sequence IDs and next_player links for pass chains."""
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

            # Same team + within 10s = same possession chain
            if (next_event['team'] == df.iloc[idx]['team'] and 0 <= time_diff <= 10):
                df.iloc[idx, df.columns.get_loc('next_player')] = next_event['player']

    return df


def _add_spatial_calculations(df: pd.DataFrame) -> pd.DataFrame:
    """Add distance_to_goal and pass_distance columns."""
    
    df['distance_to_goal'] = _calculate_distance_to_goal(df['x'], df['y'])
    df['pass_distance'] = _calculate_pass_distance(df['x'], df['y'], df['end_x'], df['end_y'])
    
    return df


def _calculate_distance_to_goal(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Euclidean distance to goal center (x=100, y=50) in percentage-unit space."""
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
    """Euclidean distance between pass origin and destination."""
    distances = []

    for start_x, start_y, end_x, end_y in zip(x1, y1, x2, y2):
        if pd.isna(start_x) or pd.isna(end_x):
            distances.append(None)
            continue

        distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        distances.append(round(distance, 2))

    return pd.Series(distances, index=x1.index)


def _optimize_for_visualization(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce strict types and drop internal columns for clean viz output."""
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
    """Build pass network: avg positions, directional connections filtered by min_passes."""
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

        # Merge A->B and B->A into bidirectional pairs, keeping directions above min_passes
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
    """Aggregate actions per zone: count, success rate, avg position, zone percentage."""
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
    """Add is_goal, is_on_target, is_blocked flags and shot_zone classification."""
    enhanced_df = shot_events.copy()

    if 'outcome_type' in enhanced_df.columns:
        enhanced_df['is_goal'] = enhanced_df['outcome_type'].str.contains('Goal', case=False, na=False)
        enhanced_df['is_on_target'] = enhanced_df['outcome_type'].isin(['Goal', 'Saved', 'SavedShot'])
        enhanced_df['is_blocked'] = enhanced_df['outcome_type'].str.contains('Block', case=False, na=False)

    enhanced_df['shot_zone'] = _classify_shot_zones(enhanced_df['x'], enhanced_df['y'])

    return enhanced_df


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify shots by zone: Six_Yard_Box, Central/Wide_Penalty_Box, Penalty_Area_Edge, Long_Range."""
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
    """Aggregate event density and success rate per field zone for a team."""
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
    """Filter events by time period: first_half, second_half, first_30, last_30."""
    
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
    """Apply case-insensitive substring filters for event type, player, and team."""
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
    """Export DataFrame or dict of DataFrames to CSV. Returns filename(s)."""
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
# ID RETRIEVAL
# ====================================================================

def get_match_ids(league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame:
    """Extract match IDs from WhoScored schedule. Returns DataFrame with match_id, teams, date."""
    try:
        from ..scrappers.whoscored import WhoScoredReader
        
        scraper = WhoScoredReader(league=league, season=season)
        schedule_data = scraper.read_schedule()
        
        if schedule_data.empty:
            print(f"No matches found for {league} {season}")
            return pd.DataFrame()
        
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
    """Search for a player in match events. Returns player info dict or None."""
    try:
        match_events = extract_match_events(match_id, league, season, verbose=False)

        if match_events.empty:
            return None

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
    """Search for a team in league schedule. Returns team info dict or None."""
    try:
        schedule_data = get_match_ids(league, season, team_filter=team_name)

        if not schedule_data.empty:
            first_match = schedule_data.iloc[0]
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
# QUICK ACCESS (no verbose)
# ====================================================================

def get_match_events(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Get all match events with spatial data."""
    return extract_match_events(match_id, league, season, verbose=False)

def get_match_events_viz(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Get match events optimized for visualization."""
    return extract_match_events(match_id, league, season, for_viz=True, verbose=False)

def get_pass_network(match_id: int, team: str, league: str, season: str) -> Dict[str, pd.DataFrame]:
    """Get pass network with positions and connections."""
    return extract_pass_network(match_id, team, league, season, verbose=False)

def get_player_heatmap(match_id: int, player: str, league: str, season: str) -> pd.DataFrame:
    """Get player action heatmap by field zone."""
    return extract_player_heatmap(match_id, player, league, season, verbose=False)

def get_shot_map(match_id: int, league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Get shot map with coordinates and zone classification."""
    return extract_shot_map(match_id, league, season, team_filter=team, verbose=False)

def get_field_occupation(match_id: int, team: str, league: str, season: str) -> pd.DataFrame:
    """Get field occupation analysis by zones."""
    return extract_field_occupation(match_id, team, league, season, verbose=False)

def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Get league schedule with match IDs."""
    return extract_league_schedule(league, season, verbose=False)

def get_missing_players(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Get injured and suspended players for a match."""
    return extract_missing_players(match_id, league, season, verbose=False)