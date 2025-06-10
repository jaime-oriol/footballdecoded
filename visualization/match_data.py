# ====================================================================
# FootballDecoded - Optimized Match Data Extractor
# ====================================================================

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional
from datetime import datetime

# ====================================================================
# CORE EXTRACTOR
# ====================================================================

def extract_match_data(match_id: int, league: str, season: str, 
                      save_to_data_folder: bool = True, verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Extract and process complete match data optimized for pass network visualization.
    
    Returns:
        Dict with 'passes', 'players', 'connections' DataFrames
    """
    from wrappers import whoscored_extract_match_events
    
    if verbose:
        print(f"🎯 Extracting match {match_id} ({league} {season})")
    
    events_df = whoscored_extract_match_events(match_id, league, season, verbose=False)
    
    if events_df.empty:
        raise ValueError(f"No events found for match {match_id}")
    
    # Process data
    passes_df = _process_passes(events_df, verbose)
    players_df = _calculate_players(passes_df, verbose)
    connections_df = _calculate_connections(passes_df, verbose)
    
    result = {'passes': passes_df, 'players': players_df, 'connections': connections_df}
    
    if save_to_data_folder:
        _save_data(result, match_id, verbose)
    
    return result


# ====================================================================
# DATA PROCESSING
# ====================================================================

def _process_passes(events_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Extract and clean successful passes."""
    
    # Filter passes only
    passes = events_df[
        events_df['event_type'].str.contains('Pass', case=False, na=False) & 
        (events_df['is_successful'] == True)
    ].copy()
    
    if passes.empty:
        raise ValueError("No successful passes found")
    
    # Convert coordinates to field meters
    passes['field_x'] = (passes['x'] / 100) * 105
    passes['field_y'] = (passes['y'] / 100) * 68
    
    # Calculate pass distance
    if 'end_x' in passes.columns and 'end_y' in passes.columns:
        passes['field_end_x'] = (passes['end_x'] / 100) * 105
        passes['field_end_y'] = (passes['end_y'] / 100) * 68
        passes['pass_distance'] = np.sqrt(
            (passes['field_end_x'] - passes['field_x'])**2 + 
            (passes['field_end_y'] - passes['field_y'])**2
        )
    
    # Select essential columns
    essential_cols = ['player', 'team', 'field_x', 'field_y', 'minute', 'second']
    if 'pass_distance' in passes.columns:
        essential_cols.append('pass_distance')
    
    passes_clean = passes[essential_cols].copy()
    
    if verbose:
        teams = passes_clean['team'].unique()
        print(f"   ✅ {len(passes_clean)} passes | Teams: {', '.join(teams)}")
    
    return passes_clean


def _calculate_players(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calculate player average positions and stats."""
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',
        'field_y': 'mean',
        'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    
    # Calculate node sizes (300-1200 range)
    min_passes = player_stats['total_passes'].min()
    max_passes = player_stats['total_passes'].max()
    
    if max_passes > min_passes:
        normalized = (player_stats['total_passes'] - min_passes) / (max_passes - min_passes)
        player_stats['node_size'] = 300 + (normalized * 900)
    else:
        player_stats['node_size'] = 600
    
    result = player_stats.reset_index()
    
    if verbose:
        print(f"   👥 {len(result)} players processed")
    
    return result


def _calculate_connections(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calculate pass connections between players."""
    
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    connections = []
    
    # 10-second window for connected passes
    for i in range(len(passes_sorted) - 1):
        current = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
        if current['team'] != next_pass['team']:
            continue
        
        time_diff = (next_pass['minute'] * 60 + next_pass['second']) - (current['minute'] * 60 + current['second'])
        
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
        return pd.DataFrame()
    
    # Group and count connections
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
    
    # Add line width
    result['line_width'] = result['pass_count'].apply(_get_line_width)
    
    # Count significant connections for verbose output
    significant_count = len(result[result['pass_count'] >= 5])
    
    if verbose:
        print(f"   🔗 {len(result)} total connections ({significant_count} significant ≥5 passes)")
    
    return result


def _get_line_width(count: int) -> float:
    """Calculate line width based on pass count."""
    if count < 5: return 0
    elif count < 10: return 2.0
    elif count < 15: return 4.0
    elif count < 20: return 6.0
    else: return 8.0


# ====================================================================
# DATA MANAGEMENT
# ====================================================================

def _save_data(data_dict: Dict[str, pd.DataFrame], match_id: int, verbose: bool):
    """Save processed data to visualization/data folder."""
    
    data_dir = os.path.join("data")
    os.makedirs(data_dir, exist_ok=True)
    
    for data_type, df in data_dict.items():
        if df.empty:
            continue
        
        filename = f"match_{match_id}_{data_type}.csv"
        filepath = os.path.join(data_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        if verbose:
            print(f"   💾 Saved: {filename} ({len(df)} rows)")


def load_match_data(match_id: int) -> Dict[str, pd.DataFrame]:
    """Load previously processed match data."""
    
    data_dir = "visualization/data"
    result = {}
    
    for data_type in ['passes', 'players', 'connections']:
        filename = f"match_{match_id}_{data_type}.csv"
        filepath = os.path.join(data_dir, filename)
        
        if os.path.exists(filepath):
            result[data_type] = pd.read_csv(filepath)
        else:
            result[data_type] = pd.DataFrame()
    
    return result


def get_team_summary(match_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """Get quick summary by team."""
    
    summary = {}
    players_df = match_data['players']
    connections_df = match_data['connections']
    
    for team in players_df['team'].unique():
        team_players = players_df[players_df['team'] == team]
        team_connections = connections_df[connections_df['team'] == team]
        
        summary[team] = {
            'players': len(team_players),
            'total_passes': team_players['total_passes'].sum(),
            'connections': len(team_connections)
        }
    
    return summary


# ====================================================================
# QUICK EXTRACTION SCRIPTS
# ====================================================================

def extract_athletic_barcelona():
    """Quick extraction for Athletic vs Barcelona match."""
    
    print("🔍 Athletic Club vs Barcelona - Data Extraction")
    print("=" * 50)
    
    match_data = extract_match_data(
        match_id=1821769,
        league="ESP-La Liga", 
        season="2024-25"
    )
    
    summary = get_team_summary(match_data)
    
    print("\n📊 MATCH SUMMARY:")
    for team, stats in summary.items():
        print(f"   🏟️ {team}: {stats['players']} players, {stats['total_passes']} passes, {stats['connections']} connections")
    
    print("\n✅ Data ready for visualization!")
    return match_data


# ====================================================================
# MAIN EXECUTION
# ====================================================================

if __name__ == "__main__":
    try:
        match_data = extract_athletic_barcelona()
    except Exception as e:
        print(f"❌ Error: {e}")