# ====================================================================
# FootballDecoded - Match Data Extractor
# ====================================================================
# Generic module for extracting and processing match data
# ====================================================================

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional
from datetime import datetime

# ====================================================================
# CONFIGURATION
# ====================================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ====================================================================
# MAIN EXTRACTION FUNCTIONS
# ====================================================================

def extract_match_data(match_id: int, league: str, season: str, 
                      force_reload: bool = False, verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Extract and process complete match data.
    
    Args:
        match_id: Match ID
        league: League identifier
        season: Season identifier
        force_reload: Re-extract even if data exists
        verbose: Show progress
        
    Returns:
        Dict with 'passes', 'players', 'connections'
    """
    if verbose:
        print(f"Processing match {match_id} ({league} {season})")
    
    if not force_reload and _data_exists(match_id):
        if verbose:
            print("   Data found, loading from files...")
        return load_match_data(match_id)
    
    if verbose:
        print("   Extracting data from WhoScored...")
    
    try:
        from wrappers import whoscored_extract_match_events
        events_df = whoscored_extract_match_events(match_id, league, season, verbose=False)
        
        if events_df.empty:
            raise ValueError(f"No events found for match {match_id}")
        
        passes_df = _process_passes(events_df, verbose)
        players_df = _calculate_players(passes_df, verbose)
        connections_df = _calculate_connections(passes_df, verbose)
        
        result = {
            'passes': passes_df,
            'players': players_df, 
            'connections': connections_df
        }
        
        save_match_data(result, match_id, verbose)
        return result
        
    except Exception as e:
        if verbose:
            print(f"   Error in extraction: {e}")
        raise


def load_match_data(match_id: int) -> Dict[str, pd.DataFrame]:
    """Load previously processed data."""
    result = {}
    
    for data_type in ['passes', 'players', 'connections']:
        filepath = _get_filepath(match_id, data_type)
        
        if os.path.exists(filepath):
            result[data_type] = pd.read_csv(filepath)
        else:
            result[data_type] = pd.DataFrame()
    
    return result


def save_match_data(data_dict: Dict[str, pd.DataFrame], match_id: int, verbose: bool = True):
    """Save processed data to CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for data_type, df in data_dict.items():
        if not df.empty:
            filepath = _get_filepath(match_id, data_type)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            if verbose:
                print(f"   Saved: {data_type} ({len(df)} rows)")


def filter_team_data(match_data: Dict[str, pd.DataFrame], team_name: str) -> Dict[str, pd.DataFrame]:
    """Filter data for specific team."""
    team_players = match_data['players'][match_data['players']['team'] == team_name]
    team_connections = match_data['connections'][match_data['connections']['team'] == team_name] if not match_data['connections'].empty else pd.DataFrame()
    team_passes = match_data['passes'][match_data['passes']['team'] == team_name]
    
    return {
        'passes': team_passes,
        'players': team_players,
        'connections': team_connections
    }

# ====================================================================
# DATA PROCESSING
# ====================================================================

def _process_passes(events_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Extract and clean successful passes."""
    passes = events_df[
        events_df['event_type'].str.contains('Pass', case=False, na=False) & 
        (events_df['is_successful'] == True)
    ].copy()
    
    if passes.empty:
        raise ValueError("No successful passes found")
    
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


def _get_line_width(count: int) -> float:
    """Calculate line width based on pass count."""
    if count < 3: return 0.0
    elif count < 5: return 1.5
    elif count < 8: return 3.0
    elif count < 12: return 5.0
    elif count < 18: return 7.0
    else: return 10.0

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _data_exists(match_id: int) -> bool:
    """Check if all data files exist."""
    for data_type in ['passes', 'players', 'connections']:
        if not os.path.exists(_get_filepath(match_id, data_type)):
            return False
    return True


def _get_filepath(match_id: int, data_type: str) -> str:
    """Generate file path for data type."""
    filename = f"match_{match_id}_{data_type}.csv"
    return os.path.join(DATA_DIR, filename)