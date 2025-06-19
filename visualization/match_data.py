# ====================================================================
# FootballDecoded - Enhanced Match Data Extractor
# ====================================================================
# Multi-source module for extracting complete match data
# ====================================================================

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, List
from datetime import datetime

# ====================================================================
# CONFIGURATION
# ====================================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ====================================================================
# MAIN EXTRACTION FUNCTIONS
# ====================================================================

def extract_match_data(match_id: int, league: str, season: str, 
                      source: str = 'whoscored',
                      data_types: List[str] = None,
                      force_reload: bool = False, 
                      verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Extract complete match data from multiple sources.
    
    Args:
        match_id: Match ID (specific to the source)
        league: League identifier
        season: Season identifier
        source: 'whoscored' or 'understat' - determines ID ecosystem
        data_types: List of data types to extract ['passes', 'shots', 'all']
        force_reload: Re-extract even if data exists
        verbose: Show progress
        
    Returns:
        Dict with available data: 'passes', 'players', 'connections', 'shots'
    """
    if verbose:
        print(f"Processing match {match_id} ({league} {season}) - Source: {source}")
    
    cache_key = f"{source}_{match_id}"
    
    if not force_reload and _data_exists(cache_key):
        if verbose:
            print("   Data found, loading from cache...")
        return load_match_data(cache_key)
    
    result = {}
    
    # Determine what to extract
    if data_types is None:
        data_types = ['all']
    
    extract_passes = 'passes' in data_types or 'all' in data_types
    extract_shots = 'shots' in data_types or 'all' in data_types
    
    # Extract from WhoScored (passes, events, spatial data)
    if source == 'whoscored' and extract_passes:
        if verbose:
            print("   Extracting spatial data from WhoScored...")
        
        try:
            from wrappers import whoscored_extract_match_events
            events_df = whoscored_extract_match_events(match_id, league, season, verbose=False)
            
            if not events_df.empty:
                passes_data = _process_whoscored_data(events_df, verbose)
                result.update(passes_data)
            else:
                if verbose:
                    print("   No WhoScored events found")
        except Exception as e:
            if verbose:
                print(f"   Error extracting WhoScored data: {e}")
    
    # Extract from Understat (shots with xG)
    if source == 'understat' and extract_shots:
        if verbose:
            print("   Extracting shot data from Understat...")
        
        try:
            from wrappers import understat_extract_shot_events
            shots_df = understat_extract_shot_events(match_id, league, season, verbose=False)
            
            if not shots_df.empty:
                result['shots'] = _process_understat_shots(shots_df, verbose)
            else:
                if verbose:
                    print("   No Understat shots found")
        except Exception as e:
            if verbose:
                print(f"   Error extracting Understat data: {e}")
    
    # Cross-source extraction (when we have both IDs)
    if source == 'both':
        # This would require both match IDs - implement later if needed
        pass
    
    if result:
        save_match_data(result, cache_key, verbose)
    
    return result


def extract_complete_match(whoscored_id: int, understat_id: int, 
                          league: str, season: str,
                          force_reload: bool = False,
                          verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Extract complete match data from both sources using different IDs.
    
    Args:
        whoscored_id: WhoScored match ID
        understat_id: Understat match ID  
        league: League identifier
        season: Season identifier
        
    Returns:
        Dict with all available data from both sources
    """
    if verbose:
        print(f"Extracting complete match data ({league} {season})")
        print(f"   WhoScored ID: {whoscored_id}")
        print(f"   Understat ID: {understat_id}")
    
    # Extract from both sources
    whoscored_data = extract_match_data(whoscored_id, league, season, 
                                       source='whoscored', verbose=verbose)
    understat_data = extract_match_data(understat_id, league, season, 
                                       source='understat', verbose=verbose)
    
    # Combine results
    combined_data = {**whoscored_data, **understat_data}
    
    if verbose and combined_data:
        available_types = list(combined_data.keys())
        print(f"   Combined data types: {', '.join(available_types)}")
    
    return combined_data


def load_match_data(cache_key: str) -> Dict[str, pd.DataFrame]:
    """Load previously processed data."""
    result = {}
    
    possible_types = ['passes', 'players', 'connections', 'shots']
    
    for data_type in possible_types:
        filepath = _get_filepath(cache_key, data_type)
        
        if os.path.exists(filepath):
            result[data_type] = pd.read_csv(filepath)
    
    return result


def save_match_data(data_dict: Dict[str, pd.DataFrame], cache_key: str, verbose: bool = True):
    """Save processed data to CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for data_type, df in data_dict.items():
        if not df.empty:
            filepath = _get_filepath(cache_key, data_type)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            if verbose:
                print(f"   Saved: {data_type} ({len(df)} rows)")


def filter_team_data(match_data: Dict[str, pd.DataFrame], team_name: str) -> Dict[str, pd.DataFrame]:
    """Filter data for specific team."""
    result = {}
    
    # Filter passes data
    if 'passes' in match_data:
        result['passes'] = match_data['passes'][match_data['passes']['team'] == team_name]
    
    if 'players' in match_data:
        result['players'] = match_data['players'][match_data['players']['team'] == team_name]
    
    if 'connections' in match_data:
        connections = match_data['connections']
        if not connections.empty:
            result['connections'] = connections[connections['team'] == team_name]
        else:
            result['connections'] = pd.DataFrame()
    
    # Filter shots data
    if 'shots' in match_data:
        shots = match_data['shots']
        if 'shot_team' in shots.columns:
            result['shots'] = shots[shots['shot_team'] == team_name]
        elif 'team' in shots.columns:
            result['shots'] = shots[shots['team'] == team_name]
    
    return result

# ====================================================================
# WHOSCORED DATA PROCESSING
# ====================================================================

def _process_whoscored_data(events_df: pd.DataFrame, verbose: bool) -> Dict[str, pd.DataFrame]:
    """Process WhoScored events into passes, players, and connections."""
    result = {}
    
    try:
        passes_df = _process_passes(events_df, verbose)
        result['passes'] = passes_df
        
        players_df = _calculate_players(passes_df, verbose)
        result['players'] = players_df
        
        connections_df = _calculate_connections(passes_df, verbose)
        result['connections'] = connections_df
        
    except Exception as e:
        if verbose:
            print(f"   Error processing WhoScored data: {e}")
    
    return result


def _process_passes(events_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Extract and clean successful passes."""
    passes = events_df[
        events_df['event_type'].str.contains('Pass', case=False, na=False) & 
        (events_df['is_successful'] == True)
    ].copy()
    
    if passes.empty:
        if verbose:
            print("   No successful passes found")
        return pd.DataFrame()
    
    # Convert coordinates to field meters
    passes['field_x'] = (passes['x'] / 100) * 105
    passes['field_y'] = (passes['y'] / 100) * 68
    
    # Calculate pass distance if end coordinates available
    if 'end_x' in passes.columns and 'end_y' in passes.columns:
        passes['field_end_x'] = (passes['end_x'] / 100) * 105
        passes['field_end_y'] = (passes['end_y'] / 100) * 68
        passes['pass_distance'] = np.sqrt(
            (passes['field_end_x'] - passes['field_x'])**2 + 
            (passes['field_end_y'] - passes['field_y'])**2
        )
    
    essential_cols = ['player', 'team', 'field_x', 'field_y', 'minute', 'second']
    if 'pass_distance' in passes.columns:
        essential_cols.append('pass_distance')
    
    passes_clean = passes[essential_cols].copy()
    
    if verbose:
        teams = passes_clean['team'].unique()
        print(f"   {len(passes_clean)} passes | Teams: {', '.join(teams)}")
    
    return passes_clean


def _calculate_players(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calculate average positions and player statistics."""
    if passes_df.empty:
        return pd.DataFrame()
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',
        'field_y': 'mean',
        'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    
    min_passes = player_stats['total_passes'].min()
    max_passes = player_stats['total_passes'].max()
    
    if max_passes > min_passes:
        log_passes = np.log(player_stats['total_passes'] + 1)
        log_min = np.log(min_passes + 1)
        log_max = np.log(max_passes + 1)
        
        normalized = (log_passes - log_min) / (log_max - log_min)
        player_stats['node_size'] = 800 + (normalized * 2400)
    else:
        player_stats['node_size'] = 1600
    
    result = player_stats.reset_index()
    
    if verbose:
        print(f"   {len(result)} players processed")
    
    return result


def _calculate_connections(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calculate pass connections between players."""
    if passes_df.empty:
        return pd.DataFrame()
    
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    connections = []
    
    for i in range(len(passes_sorted) - 1):
        current = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
        if current['team'] != next_pass['team']:
            continue
        
        time_diff = (next_pass['minute'] * 60 + next_pass['second']) - \
                   (current['minute'] * 60 + current['second'])
        
        if 0 < time_diff <= 10:
            connections.append({
                'team': current['team'],
                'source': current['player'],
                'target': next_pass['player'],
                'source_x': current['field_x'],
                'source_y': current['field_y'],
                'target_x': next_pass['field_x'],
                'target_y': next_pass['field_y']
            })
    
    if not connections:
        if verbose:
            print("   No connections found")
        return pd.DataFrame()
    
    connections_df = pd.DataFrame(connections)
    connection_counts = connections_df.groupby(['team', 'source', 'target']).agg({
        'source_x': 'mean',
        'source_y': 'mean',
        'target_x': 'mean',
        'target_y': 'mean',
        'team': 'count'
    }).round(1)
    
    connection_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
    result = connection_counts.reset_index()
    
    result['line_width'] = result['pass_count'].apply(_get_line_width)
    
    significant_count = len(result[result['pass_count'] >= 3])
    
    if verbose:
        print(f"   {len(result)} total connections ({significant_count} significant >=3 passes)")
    
    return result

# ====================================================================
# UNDERSTAT DATA PROCESSING
# ====================================================================

def _process_understat_shots(shots_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Process Understat shots data."""
    if shots_df.empty:
        return pd.DataFrame()
    
    processed_shots = shots_df.copy()
    
    # Ensure we have the required columns for shot maps
    required_cols = ['shot_team', 'shot_player', 'shot_xg', 'shot_location_x', 'shot_location_y', 'shot_result']
    missing_cols = [col for col in required_cols if col not in processed_shots.columns]
    
    if missing_cols:
        if verbose:
            print(f"   Warning: Missing columns in shots data: {missing_cols}")
    
    # Convert coordinates to field meters if needed
    if 'shot_location_x' in processed_shots.columns and 'shot_location_y' in processed_shots.columns:
        # Understat coordinates are typically 0-1, convert to field dimensions
        processed_shots['field_x'] = processed_shots['shot_location_x'] * 105
        processed_shots['field_y'] = processed_shots['shot_location_y'] * 68
    
    if verbose:
        teams = processed_shots['shot_team'].unique() if 'shot_team' in processed_shots.columns else ['Unknown']
        total_shots = len(processed_shots)
        print(f"   {total_shots} shots | Teams: {', '.join(teams)}")
    
    return processed_shots

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _get_line_width(count: int) -> float:
    """Calculate line width based on pass count."""
    if count < 3: return 0.0
    elif count < 5: return 1.5
    elif count < 8: return 3.0
    elif count < 12: return 5.0
    elif count < 18: return 7.0
    else: return 10.0


def _data_exists(cache_key: str) -> bool:
    """Check if any data files exist for the cache key."""
    possible_types = ['passes', 'players', 'connections', 'shots']
    
    for data_type in possible_types:
        if os.path.exists(_get_filepath(cache_key, data_type)):
            return True
    return False


def _get_filepath(cache_key: str, data_type: str) -> str:
    """Generate file path for data type."""
    filename = f"match_{cache_key}_{data_type}.csv"
    return os.path.join(DATA_DIR, filename)

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def get_available_data_types(match_data: Dict[str, pd.DataFrame]) -> List[str]:
    """Get list of available data types in match data."""
    return [key for key, df in match_data.items() if not df.empty]


def print_match_summary(match_data: Dict[str, pd.DataFrame]):
    """Print summary of available match data."""
    print("Match Data Summary:")
    print("=" * 40)
    
    for data_type, df in match_data.items():
        if not df.empty:
            print(f"   {data_type.title()}: {len(df)} records")
            
            if data_type == 'passes' and 'team' in df.columns:
                teams = df['team'].unique()
                print(f"      Teams: {', '.join(teams)}")
            
            elif data_type == 'shots' and 'shot_team' in df.columns:
                teams = df['shot_team'].unique()
                total_xg = df['shot_xg'].sum() if 'shot_xg' in df.columns else 0
                print(f"      Teams: {', '.join(teams)}")
                print(f"      Total xG: {total_xg:.2f}")
        else:
            print(f"   {data_type.title()}: No data")
    
    print("=" * 40)