# ====================================================================
# FootballDecoded - WhoScored Spatial Events Extractor
# ====================================================================
# Specialized wrapper for extracting ALL spatial/coordinate data from WhoScored
# Focus: x/y coordinates, heat maps, defensive events, dribbles, momentum analysis
# ====================================================================

import sys
import os
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Union
from datetime import datetime

# Add extractors to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import WhoScored

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)


# ====================================================================
# MATCH EVENTS - Complete Spatial Analysis
# ====================================================================

def extract_match_events(
    match_id: int,
    league: str,
    season: str,
    event_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract ALL match events with complete spatial information.
    
    This is the core function for tactical analysis - gets every event
    with x/y coordinates, timings, and detailed context.
    
    Args:
        match_id: WhoScored match ID (integer)
        league: League identifier
        season: Season identifier
        event_filter: Optional event type filter (e.g., 'Pass', 'Shot', 'Tackle')
        player_filter: Optional player name filter
        team_filter: Optional team name filter
        verbose: Show extraction progress
        
    Returns:
        DataFrame with ALL events including coordinates and tactical context
    """
    if verbose:
        print(f"🎯 Extracting complete event data from match {match_id}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   📊 Reading event stream...")
        
        # Extract raw events with all spatial data
        events_df = whoscored.read_events(match_id=match_id, output_fmt='events')
        
        if events_df is None or events_df.empty:
            if verbose:
                print(f"   ❌ No events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(events_df)} events extracted")
        
        # Process and enhance events with tactical analysis
        enhanced_events = _process_spatial_events(events_df)
        
        # Apply filters if specified
        filtered_events = _apply_event_filters(
            enhanced_events, event_filter, player_filter, team_filter, verbose
        )
        
        # Add match context
        if not filtered_events.empty:
            filtered_events['match_id'] = match_id
            filtered_events['data_source'] = 'whoscored'
        
        if verbose and not filtered_events.empty:
            total_events = len(filtered_events)
            unique_players = filtered_events['player'].nunique()
            event_types = filtered_events['event_type'].nunique()
            
            print(f"   ✅ SUCCESS: {total_events} events with spatial data")
            print(f"   📊 Players: {unique_players} | Event types: {event_types}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Event extraction failed: {str(e)}")
        return pd.DataFrame()


def extract_player_heatmap(
    match_id: int,
    player_name: str,
    league: str,
    season: str,
    event_types: Optional[List[str]] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract player heatmap data from match events.
    
    Creates detailed spatial distribution of player actions for tactical analysis.
    
    Args:
        match_id: WhoScored match identifier
        player_name: Player name for heatmap analysis
        league: League identifier
        season: Season identifier
        event_types: Optional list of event types to include (e.g., ['Pass', 'Carry'])
        verbose: Show extraction progress
        
    Returns:
        DataFrame with player position data and action frequencies by zone
    """
    if verbose:
        print(f"🔥 Creating heatmap for {player_name} in match {match_id}")
    
    # Get all events for the player
    events_df = extract_match_events(
        match_id, league, season, 
        player_filter=player_name, 
        verbose=False
    )
    
    if events_df.empty:
        if verbose:
            print(f"   ❌ No events found for {player_name}")
        return pd.DataFrame()
    
    # Filter by event types if specified
    if event_types:
        events_df = events_df[events_df['event_type'].isin(event_types)]
    
    if events_df.empty:
        if verbose:
            print(f"   ❌ No events of specified types for {player_name}")
        return pd.DataFrame()
    
    # Create heatmap zones and calculate frequencies
    heatmap_data = _calculate_player_heatmap(events_df, player_name)
    
    if verbose and not heatmap_data.empty:
        total_actions = heatmap_data['action_count'].sum()
        active_zones = len(heatmap_data[heatmap_data['action_count'] > 0])
        max_zone_actions = heatmap_data['action_count'].max()
        
        print(f"   ✅ Heatmap: {total_actions} actions across {active_zones} zones")
        print(f"   🔥 Hottest zone: {max_zone_actions} actions")
    
    return heatmap_data


def extract_defensive_events(
    match_id: int,
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract ALL defensive events with precise spatial coordinates.
    
    Perfect for analyzing defensive intensity, pressing zones, and tackle success rates.
    
    Args:
        match_id: WhoScored match identifier
        league: League identifier
        season: Season identifier
        team_filter: Optional team name filter
        player_filter: Optional player name filter
        verbose: Show extraction progress
        
    Returns:
        DataFrame with defensive actions and spatial analysis
    """
    if verbose:
        print(f"🛡️ Extracting defensive events from match {match_id}")
    
    # Define defensive event types
    defensive_events = [
        'Tackle', 'Interception', 'Clearance', 'Block', 'Foul',
        'Aerial', 'Challenge', 'Dispossessed'
    ]
    
    all_events = extract_match_events(
        match_id, league, season, 
        team_filter=team_filter, 
        player_filter=player_filter,
        verbose=False
    )
    
    if all_events.empty:
        if verbose:
            print(f"   ❌ No events found")
        return pd.DataFrame()
    
    # Filter to defensive events only
    defensive_df = all_events[all_events['event_type'].isin(defensive_events)].copy()
    
    if defensive_df.empty:
        if verbose:
            print(f"   ❌ No defensive events found")
        return pd.DataFrame()
    
    # Enhance with defensive analysis
    enhanced_defensive = _analyze_defensive_events(defensive_df)
    
    if verbose and not enhanced_defensive.empty:
        total_actions = len(enhanced_defensive)
        successful_actions = len(enhanced_defensive[enhanced_defensive.get('is_successful', False)])
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        print(f"   ✅ Defensive analysis: {total_actions} actions")
        print(f"   🎯 Success rate: {success_rate:.1f}%")
    
    return enhanced_defensive


def extract_pass_network(
    match_id: int,
    team_name: str,
    league: str,
    season: str,
    min_passes: int = 5,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Extract complete pass network data with coordinates.
    
    Creates pass maps, average positions, and connection strength for tactical analysis.
    
    Args:
        match_id: WhoScored match identifier
        team_name: Team name for pass network analysis
        league: League identifier
        season: Season identifier
        min_passes: Minimum passes between players to include connection
        verbose: Show extraction progress
        
    Returns:
        Dict with 'passes', 'positions', and 'connections' DataFrames
    """
    if verbose:
        print(f"🔗 Creating pass network for {team_name} in match {match_id}")
    
    # Get all pass events for the team
    pass_events = extract_match_events(
        match_id, league, season, 
        event_filter='Pass',
        team_filter=team_name,
        verbose=False
    )
    
    if pass_events.empty:
        if verbose:
            print(f"   ❌ No pass events found for {team_name}")
        return {'passes': pd.DataFrame(), 'positions': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    # Calculate pass network components
    network_data = _calculate_pass_network(pass_events, team_name, min_passes)
    
    if verbose:
        passes_df = network_data['passes']
        positions_df = network_data['positions']
        connections_df = network_data['connections']
        
        if not passes_df.empty:
            total_passes = len(passes_df)
            successful_passes = len(passes_df[passes_df.get('is_successful', False)])
            success_rate = (successful_passes / total_passes * 100) if total_passes > 0 else 0
            
            print(f"   ✅ Pass network: {total_passes} passes analyzed")
            print(f"   🎯 Success rate: {success_rate:.1f}%")
            print(f"   👥 Players: {len(positions_df)} | Connections: {len(connections_df)}")
    
    return network_data


def extract_shot_map(
    match_id: int,
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract detailed shot map with xG, coordinates, and outcome analysis.
    
    Args:
        match_id: WhoScored match identifier
        league: League identifier
        season: Season identifier
        team_filter: Optional team name filter
        player_filter: Optional player name filter
        verbose: Show extraction progress
        
    Returns:
        DataFrame with shot locations, xG values, and tactical context
    """
    if verbose:
        print(f"⚽ Creating shot map for match {match_id}")
    
    # Get all shot events
    shot_events = extract_match_events(
        match_id, league, season,
        event_filter='Shot',
        team_filter=team_filter,
        player_filter=player_filter,
        verbose=False
    )
    
    if shot_events.empty:
        if verbose:
            print(f"   ❌ No shot events found")
        return pd.DataFrame()
    
    # Enhance shots with xG and spatial analysis
    enhanced_shots = _analyze_shot_events(shot_events)
    
    if verbose and not enhanced_shots.empty:
        total_shots = len(enhanced_shots)
        goals = len(enhanced_shots[enhanced_shots.get('is_goal', False)])
        shots_on_target = len(enhanced_shots[enhanced_shots.get('is_on_target', False)])
        
        print(f"   ✅ Shot map: {total_shots} shots analyzed")
        print(f"   ⚽ Goals: {goals} | On target: {shots_on_target}")
    
    return enhanced_shots


# ====================================================================
# TEAM ANALYSIS - Match-specific Performance
# ====================================================================

def extract_team_match_analysis(
    match_id: int,
    team_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """
    Complete team analysis for a specific match.
    
    Includes pass network, defensive actions, shot map, and spatial statistics.
    
    Args:
        match_id: WhoScored match identifier
        team_name: Team name for analysis
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        Dict with comprehensive team analysis data
    """
    if verbose:
        print(f"🏟️ Complete team analysis: {team_name} in match {match_id}")
    
    results = {}
    
    # Pass network analysis
    if verbose:
        print("   🔗 Analyzing pass network...")
    pass_network = extract_pass_network(match_id, team_name, league, season, verbose=False)
    results['pass_network'] = pass_network
    
    # Defensive analysis
    if verbose:
        print("   🛡️ Analyzing defensive actions...")
    defensive_events = extract_defensive_events(match_id, league, season, team_filter=team_name, verbose=False)
    results['defensive_actions'] = defensive_events
    
    # Shot analysis
    if verbose:
        print("   ⚽ Analyzing shot map...")
    shot_map = extract_shot_map(match_id, league, season, team_filter=team_name, verbose=False)
    results['shot_map'] = shot_map
    
    # Overall team statistics
    if verbose:
        print("   📊 Calculating team statistics...")
    team_stats = _calculate_team_match_stats(match_id, team_name, league, season)
    results['team_stats'] = team_stats
    
    if verbose:
        print(f"✅ Team analysis complete for {team_name}")
    
    return results


def extract_match_missing_players(
    match_id: int,
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract injured and suspended players for match analysis.
    
    Important for understanding team selection and tactical adjustments.
    
    Args:
        match_id: WhoScored match identifier
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        DataFrame with missing players and reasons
    """
    if verbose:
        print(f"🏥 Extracting missing players for match {match_id}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        missing_players = whoscored.read_missing_players(match_id=match_id)
        
        if verbose and not missing_players.empty:
            total_missing = len(missing_players)
            teams_affected = missing_players.index.get_level_values('team').nunique()
            
            print(f"   ✅ Missing players: {total_missing} across {teams_affected} teams")
        
        return missing_players
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Missing players extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# LEAGUE SCHEDULE - Match Discovery
# ====================================================================

def extract_league_schedule(
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract complete league schedule for match ID discovery.
    
    Essential for finding match IDs for detailed analysis.
    
    Args:
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        DataFrame with league schedule and match IDs
    """
    if verbose:
        print(f"📅 Extracting schedule for {league} {season}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        schedule = whoscored.read_schedule()
        
        if verbose and not schedule.empty:
            total_matches = len(schedule)
            completed_matches = len(schedule[schedule['score'].notna()])
            
            print(f"   ✅ Schedule: {total_matches} matches ({completed_matches} completed)")
        
        return schedule
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Schedule extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# CORE PROCESSING ENGINE - Internal Functions
# ====================================================================

def _process_spatial_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Process and enhance raw events with spatial analysis."""
    if events_df.empty:
        return events_df
    
    enhanced_df = events_df.copy()
    
    # Standardize coordinate columns
    if 'x' in enhanced_df.columns and 'y' in enhanced_df.columns:
        enhanced_df['start_x'] = pd.to_numeric(enhanced_df['x'], errors='coerce')
        enhanced_df['start_y'] = pd.to_numeric(enhanced_df['y'], errors='coerce')
    
    if 'end_x' in enhanced_df.columns and 'end_y' in enhanced_df.columns:
        enhanced_df['end_x'] = pd.to_numeric(enhanced_df['end_x'], errors='coerce')
        enhanced_df['end_y'] = pd.to_numeric(enhanced_df['end_y'], errors='coerce')
    
    # Add spatial zones
    enhanced_df['field_zone'] = _classify_field_zones(enhanced_df.get('start_x'), enhanced_df.get('start_y'))
    
    # Add event outcome classification
    enhanced_df['is_successful'] = _classify_event_success(enhanced_df)
    
    # Clean and standardize event types
    enhanced_df['event_type'] = enhanced_df['type'].fillna('Unknown')
    
    # Add timing analysis
    enhanced_df['match_period'] = _classify_match_periods(enhanced_df.get('minute', 0))
    
    return enhanced_df


def _classify_field_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify field positions into tactical zones."""
    if x_coords is None or y_coords is None:
        return pd.Series(['Unknown'] * len(x_coords) if x_coords is not None else [])
    
    zones = []
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        # Convert to percentage (WhoScored uses 0-100 scale)
        x_pct = float(x)
        y_pct = float(y)
        
        # Tactical zone classification
        if x_pct <= 33:
            if y_pct <= 33:
                zones.append('Defensive Left')
            elif y_pct <= 66:
                zones.append('Defensive Center')
            else:
                zones.append('Defensive Right')
        elif x_pct <= 66:
            if y_pct <= 33:
                zones.append('Middle Left')
            elif y_pct <= 66:
                zones.append('Middle Center')
            else:
                zones.append('Middle Right')
        else:
            if y_pct <= 33:
                zones.append('Attacking Left')
            elif y_pct <= 66:
                zones.append('Attacking Center')
            else:
                zones.append('Attacking Right')
    
    return pd.Series(zones, index=x_coords.index if hasattr(x_coords, 'index') else None)


def _classify_event_success(events_df: pd.DataFrame) -> pd.Series:
    """Classify event success based on outcome type."""
    if 'outcome_type' not in events_df.columns:
        return pd.Series([False] * len(events_df))
    
    successful_outcomes = ['Successful', 'Goal', 'Assist', 'Won']
    return events_df['outcome_type'].isin(successful_outcomes)


def _classify_match_periods(minutes: pd.Series) -> pd.Series:
    """Classify match timing into tactical periods."""
    periods = []
    for minute in minutes:
        if pd.isna(minute):
            periods.append('Unknown')
        elif minute <= 15:
            periods.append('Opening')
        elif minute <= 30:
            periods.append('First Third')
        elif minute <= 45:
            periods.append('End First Half')
        elif minute <= 60:
            periods.append('Early Second Half')
        elif minute <= 75:
            periods.append('Second Third')
        elif minute <= 90:
            periods.append('Final Third')
        else:
            periods.append('Extra Time')
    
    return pd.Series(periods, index=minutes.index if hasattr(minutes, 'index') else None)


def _apply_event_filters(
    events_df: pd.DataFrame,
    event_filter: Optional[str],
    player_filter: Optional[str],
    team_filter: Optional[str],
    verbose: bool
) -> pd.DataFrame:
    """Apply various filters to event data."""
    filtered_df = events_df.copy()
    
    # Event type filter
    if event_filter:
        if verbose:
            print(f"   🎯 Applying event filter: {event_filter}")
        mask = filtered_df['event_type'].str.contains(event_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    # Player filter
    if player_filter:
        if verbose:
            print(f"   👤 Applying player filter: {player_filter}")
        mask = filtered_df['player'].str.contains(player_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    # Team filter
    if team_filter:
        if verbose:
            print(f"   🏟️ Applying team filter: {team_filter}")
        mask = filtered_df['team'].str.contains(team_filter, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    return filtered_df


def _calculate_player_heatmap(events_df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    """Calculate player heatmap data from events."""
    # Group events by field zones
    zone_counts = events_df.groupby('field_zone').size().reset_index(name='action_count')
    
    # Add player info
    zone_counts['player'] = player_name
    zone_counts['total_actions'] = len(events_df)
    zone_counts['zone_percentage'] = (zone_counts['action_count'] / zone_counts['total_actions'] * 100).round(2)
    
    # Add average coordinates per zone
    avg_coords = events_df.groupby('field_zone')[['start_x', 'start_y']].mean().round(2)
    zone_counts = zone_counts.merge(avg_coords, left_on='field_zone', right_index=True, how='left')
    
    return zone_counts.sort_values('action_count', ascending=False)


def _analyze_defensive_events(defensive_df: pd.DataFrame) -> pd.DataFrame:
    """Enhance defensive events with tactical analysis."""
    enhanced_df = defensive_df.copy()
    
    # Add defensive intensity by zone
    zone_intensity = enhanced_df.groupby('field_zone').size()
    enhanced_df['zone_defensive_intensity'] = enhanced_df['field_zone'].map(zone_intensity)
    
    # Calculate success rates by event type
    success_by_type = enhanced_df.groupby('event_type')['is_successful'].mean()
    enhanced_df['event_type_success_rate'] = enhanced_df['event_type'].map(success_by_type)
    
    return enhanced_df


def _calculate_pass_network(pass_events: pd.DataFrame, team_name: str, min_passes: int) -> Dict[str, pd.DataFrame]:
    """Calculate pass network components."""
    results = {
        'passes': pd.DataFrame(),
        'positions': pd.DataFrame(),
        'connections': pd.DataFrame()
    }
    
    if pass_events.empty:
        return results
    
    # All passes
    results['passes'] = pass_events.copy()
    
    # Average positions per player
    positions = pass_events.groupby('player')[['start_x', 'start_y']].mean().round(2)
    positions['team'] = team_name
    positions['total_passes'] = pass_events.groupby('player').size()
    results['positions'] = positions.reset_index()
    
    # Pass connections (simplified - would need pass recipient data for full network)
    # For now, show pass frequency by player and zone
    connections = pass_events.groupby(['player', 'field_zone']).size().reset_index(name='pass_count')
    connections = connections[connections['pass_count'] >= min_passes]
    results['connections'] = connections
    
    return results


def _analyze_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Enhance shot events with detailed analysis."""
    enhanced_df = shot_events.copy()
    
    # Add shot outcome classification
    if 'outcome_type' in enhanced_df.columns:
        enhanced_df['is_goal'] = enhanced_df['outcome_type'].str.contains('Goal', case=False, na=False)
        enhanced_df['is_on_target'] = enhanced_df['outcome_type'].isin(['Goal', 'Saved'])
        enhanced_df['is_blocked'] = enhanced_df['outcome_type'].str.contains('Block', case=False, na=False)
    
    # Add shot zone classification
    enhanced_df['shot_zone'] = _classify_shot_zones(enhanced_df.get('start_x'), enhanced_df.get('start_y'))
    
    return enhanced_df


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify shots into detailed zones."""
    if x_coords is None or y_coords is None:
        return pd.Series(['Unknown'] * len(x_coords) if x_coords is not None else [])
    
    zones = []
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x)
        y_pct = float(y)
        
        # Shot zone classification (attacking perspective)
        if x_pct >= 83:  # Inside penalty box
            if 35 <= y_pct <= 65:
                zones.append('Central Box')
            else:
                zones.append('Wide Box')
        elif x_pct >= 66:  # Edge of box
            if 40 <= y_pct <= 60:
                zones.append('Central Edge')
            else:
                zones.append('Wide Edge')
        else:  # Long range
            zones.append('Long Range')
    
    return pd.Series(zones, index=x_coords.index if hasattr(x_coords, 'index') else None)


def _calculate_team_match_stats(match_id: int, team_name: str, league: str, season: str) -> Dict:
    """Calculate overall team statistics for the match."""
    # Get all events for the team
    team_events = extract_match_events(match_id, league, season, team_filter=team_name, verbose=False)
    
    if team_events.empty:
        return {}
    
    stats = {
        'team_name': team_name,
        'match_id': match_id,
        'total_events': len(team_events),
        'successful_events': len(team_events[team_events.get('is_successful', False)]),
        'event_success_rate': (len(team_events[team_events.get('is_successful', False)]) / len(team_events) * 100) if len(team_events) > 0 else 0
    }
    
    # Add event type breakdowns
    event_counts = team_events['event_type'].value_counts().to_dict()
    for event_type, count in event_counts.items():
        stats[f'{event_type.lower()}_count'] = count
    
    return stats


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(
    data: Union[Dict, pd.DataFrame],
    filename: str,
    include_timestamp: bool = True
) -> str:
    """Export data to CSV with proper formatting."""
    if isinstance(data, dict):
        # Handle dict of DataFrames
        if all(isinstance(v, pd.DataFrame) for v in data.values()):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            files_created = []
            
            for key, df in data.items():
                if not df.empty:
                    file_suffix = f"_{timestamp}" if timestamp else ""
                    full_filename = f"{filename}_{key}{file_suffix}.csv"
                    df.to_csv(full_filename, index=False, encoding='utf-8')
                    files_created.append(full_filename)
            
            print(f"📊 Data exported to {len(files_created)} files")
            return ", ".join(files_created)
        else:
            # Handle dict of stats
            df = pd.DataFrame([data])
    else:
        df = data
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    df.to_csv(full_filename, index=False, encoding='utf-8')
    
    print(f"📊 Data exported to: {full_filename}")
    print(f"   Rows: {len(df)} | Columns: {len(df.columns)}")
    
    return full_filename


# ====================================================================
# QUICK ACCESS FUNCTIONS
# ====================================================================

def get_match_events(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Quick match events extraction."""
    return extract_match_events(match_id, league, season, verbose=False)


def get_player_heatmap(match_id: int, player_name: str, league: str, season: str) -> pd.DataFrame:
    """Quick player heatmap extraction."""
    return extract_player_heatmap(match_id, player_name, league, season, verbose=False)


def get_defensive_events(match_id: int, league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Quick defensive events extraction."""
    return extract_defensive_events(match_id, league, season, team_filter=team, verbose=False)


def get_pass_network(match_id: int, team_name: str, league: str, season: str) -> Dict[str, pd.DataFrame]:
    """Quick pass network extraction."""
    return extract_pass_network(match_id, team_name, league, season, verbose=False)


def get_shot_map(match_id: int, league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Quick shot map extraction."""
    return extract_shot_map(match_id, league, season, team_filter=team, verbose=False)


def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Quick schedule extraction."""
    return extract_league_schedule(league, season, verbose=False)


def get_missing_players(match_id: int, league: str, season: str) -> pd.DataFrame:
    """Quick missing players extraction."""
    return extract_match_missing_players(match_id, league, season, verbose=False)


# ====================================================================
# ADVANCED ANALYSIS - Multi-Match and Comparative
# ====================================================================

def analyze_player_across_matches(
    player_name: str,
    match_ids: List[int],
    league: str,
    season: str,
    analysis_type: str = 'heatmap',
    export: bool = True,
    verbose: bool = False
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Analyze player performance across multiple matches.
    
    Args:
        player_name: Player name for analysis
        match_ids: List of WhoScored match IDs
        league: League identifier
        season: Season identifier
        analysis_type: 'heatmap', 'events', or 'all'
        export: Whether to export results
        verbose: Show progress
        
    Returns:
        DataFrame or Dict with multi-match analysis
    """
    if verbose:
        print(f"🔍 Multi-match analysis for {player_name}: {len(match_ids)} matches")
    
    all_data = []
    results = {}
    
    for i, match_id in enumerate(match_ids, 1):
        if verbose:
            print(f"   [{i}/{len(match_ids)}] Processing match {match_id}")
        
        if analysis_type in ['heatmap', 'all']:
            heatmap_data = extract_player_heatmap(match_id, player_name, league, season, verbose=False)
            if not heatmap_data.empty:
                heatmap_data['match_id'] = match_id
                all_data.append(heatmap_data)
        
        if analysis_type in ['events', 'all']:
            event_data = extract_match_events(match_id, league, season, player_filter=player_name, verbose=False)
            if not event_data.empty:
                event_data['analysis_match_id'] = match_id
                if 'events' not in results:
                    results['events'] = []
                results['events'].append(event_data)
    
    # Combine and analyze data
    if all_data:
        combined_heatmap = pd.concat(all_data, ignore_index=True)
        
        # Calculate aggregate heatmap
        aggregate_heatmap = combined_heatmap.groupby('field_zone').agg({
            'action_count': 'sum',
            'start_x': 'mean',
            'start_y': 'mean'
        }).reset_index()
        
        aggregate_heatmap['player'] = player_name
        aggregate_heatmap['matches_analyzed'] = len(match_ids)
        aggregate_heatmap['zone_percentage'] = (
            aggregate_heatmap['action_count'] / aggregate_heatmap['action_count'].sum() * 100
        ).round(2)
        
        results['aggregate_heatmap'] = aggregate_heatmap
        results['individual_matches'] = combined_heatmap
    
    if 'events' in results:
        results['all_events'] = pd.concat(results['events'], ignore_index=True)
        del results['events']
    
    # Export if requested
    if export and results:
        filename = f"{player_name.replace(' ', '_')}_multi_match_analysis"
        export_to_csv(results, filename)
    
    if verbose:
        total_actions = results.get('aggregate_heatmap', pd.DataFrame()).get('action_count', pd.Series()).sum()
        if total_actions > 0:
            print(f"   ✅ Analysis complete: {total_actions} total actions across matches")
    
    return results if analysis_type == 'all' else results.get('aggregate_heatmap', pd.DataFrame())


def compare_teams_tactical_analysis(
    match_id: int,
    league: str,
    season: str,
    export: bool = True,
    verbose: bool = False
) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """
    Complete tactical comparison between both teams in a match.
    
    Args:
        match_id: WhoScored match identifier
        league: League identifier
        season: Season identifier
        export: Whether to export results
        verbose: Show progress
        
    Returns:
        Dict with comprehensive tactical comparison
    """
    if verbose:
        print(f"⚔️ Complete tactical analysis for match {match_id}")
    
    # Get all events to identify teams
    all_events = extract_match_events(match_id, league, season, verbose=False)
    
    if all_events.empty:
        if verbose:
            print(f"   ❌ No events found for match {match_id}")
        return {}
    
    teams = all_events['team'].unique()
    if len(teams) != 2:
        if verbose:
            print(f"   ❌ Expected 2 teams, found {len(teams)}")
        return {}
    
    team_a, team_b = teams[0], teams[1]
    
    if verbose:
        print(f"   🆚 Analyzing: {team_a} vs {team_b}")
    
    results = {
        'match_info': {
            'match_id': match_id,
            'team_a': team_a,
            'team_b': team_b,
            'league': league,
            'season': season
        }
    }
    
    # Analyze both teams
    for team_name in [team_a, team_b]:
        team_key = f"team_{'a' if team_name == team_a else 'b'}_analysis"
        
        if verbose:
            print(f"   📊 Analyzing {team_name}...")
        
        team_analysis = extract_team_match_analysis(match_id, team_name, league, season, verbose=False)
        results[team_key] = team_analysis
    
    # Comparative analysis
    if verbose:
        print("   ⚖️ Creating comparative analysis...")
    
    comparative_stats = _create_comparative_analysis(results, team_a, team_b)
    results['comparative_analysis'] = comparative_stats
    
    # Export if requested
    if export:
        filename = f"tactical_comparison_match_{match_id}"
        export_to_csv(results, filename)
    
    if verbose:
        print(f"✅ Tactical comparison complete for {team_a} vs {team_b}")
    
    return results


def analyze_league_tactical_trends(
    league: str,
    season: str,
    max_matches: int = 50,
    analysis_focus: str = 'all',
    export: bool = True,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Analyze tactical trends across multiple matches in a league.
    
    Args:
        league: League identifier
        season: Season identifier
        max_matches: Maximum number of matches to analyze
        analysis_focus: 'defensive', 'attacking', 'passing', or 'all'
        export: Whether to export results
        verbose: Show progress
        
    Returns:
        Dict with league-wide tactical analysis
    """
    if verbose:
        print(f"📈 League tactical trends analysis: {league} {season}")
    
    # Get league schedule
    schedule = extract_league_schedule(league, season, verbose=False)
    
    if schedule.empty:
        if verbose:
            print(f"   ❌ No schedule found for {league} {season}")
        return {}
    
    # Filter to completed matches with match IDs
    completed_matches = schedule[
        schedule['game_id'].notna() & 
        schedule['score'].notna()
    ].head(max_matches)
    
    if completed_matches.empty:
        if verbose:
            print(f"   ❌ No completed matches found")
        return {}
    
    if verbose:
        print(f"   📊 Analyzing {len(completed_matches)} matches...")
    
    results = {
        'league_info': {
            'league': league,
            'season': season,
            'matches_analyzed': len(completed_matches),
            'analysis_focus': analysis_focus
        }
    }
    
    all_events = []
    all_defensive = []
    all_shots = []
    
    # Process each match
    for i, (_, match) in enumerate(completed_matches.iterrows(), 1):
        match_id = match['game_id']
        
        if verbose and i % 10 == 0:
            print(f"   Progress: {i}/{len(completed_matches)} matches processed")
        
        try:
            # Get events based on analysis focus
            if analysis_focus in ['all', 'passing']:
                events = extract_match_events(match_id, league, season, verbose=False)
                if not events.empty:
                    events['match_id'] = match_id
                    all_events.append(events)
            
            if analysis_focus in ['all', 'defensive']:
                defensive = extract_defensive_events(match_id, league, season, verbose=False)
                if not defensive.empty:
                    defensive['match_id'] = match_id
                    all_defensive.append(defensive)
            
            if analysis_focus in ['all', 'attacking']:
                shots = extract_shot_map(match_id, league, season, verbose=False)
                if not shots.empty:
                    shots['match_id'] = match_id
                    all_shots.append(shots)
        
        except Exception:
            continue  # Skip problematic matches
    
    # Combine and analyze data
    if all_events:
        combined_events = pd.concat(all_events, ignore_index=True)
        results['passing_trends'] = _analyze_passing_trends(combined_events)
    
    if all_defensive:
        combined_defensive = pd.concat(all_defensive, ignore_index=True)
        results['defensive_trends'] = _analyze_defensive_trends(combined_defensive)
    
    if all_shots:
        combined_shots = pd.concat(all_shots, ignore_index=True)
        results['attacking_trends'] = _analyze_attacking_trends(combined_shots)
    
    # Export if requested
    if export and len(results) > 1:  # More than just league_info
        filename = f"{league}_{season}_tactical_trends"
        export_to_csv(results, filename)
    
    if verbose:
        trends_found = len(results) - 1
        print(f"✅ League analysis complete: {trends_found} trend categories analyzed")
    
    return results


# ====================================================================
# ADVANCED ANALYSIS HELPERS
# ====================================================================

def _create_comparative_analysis(results: Dict, team_a: str, team_b: str) -> Dict:
    """Create comparative statistics between two teams."""
    comparison = {
        'team_a': team_a,
        'team_b': team_b
    }
    
    # Compare team stats if available
    team_a_stats = results.get('team_a_analysis', {}).get('team_stats', {})
    team_b_stats = results.get('team_b_analysis', {}).get('team_stats', {})
    
    if team_a_stats and team_b_stats:
        for stat in ['total_events', 'successful_events', 'event_success_rate']:
            if stat in team_a_stats and stat in team_b_stats:
                comparison[f'{stat}_a'] = team_a_stats[stat]
                comparison[f'{stat}_b'] = team_b_stats[stat]
                
                if stat != 'event_success_rate':
                    comparison[f'{stat}_difference'] = team_a_stats[stat] - team_b_stats[stat]
    
    return comparison


def _analyze_passing_trends(events_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze passing trends across matches."""
    pass_events = events_df[events_df['event_type'].str.contains('Pass', case=False, na=False)]
    
    if pass_events.empty:
        return pd.DataFrame()
    
    # Trends by field zone
    zone_trends = pass_events.groupby(['field_zone', 'match_id']).agg({
        'is_successful': ['count', 'sum', 'mean']
    }).round(3)
    
    zone_trends.columns = ['total_passes', 'successful_passes', 'success_rate']
    return zone_trends.reset_index()


def _analyze_defensive_trends(defensive_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze defensive trends across matches."""
    if defensive_df.empty:
        return pd.DataFrame()
    
    # Trends by event type and zone
    defensive_trends = defensive_df.groupby(['event_type', 'field_zone', 'match_id']).agg({
        'is_successful': ['count', 'sum', 'mean']
    }).round(3)
    
    defensive_trends.columns = ['total_actions', 'successful_actions', 'success_rate']
    return defensive_trends.reset_index()


def _analyze_attacking_trends(shots_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze attacking/shooting trends across matches."""
    if shots_df.empty:
        return pd.DataFrame()
    
    # Trends by shot zone
    shot_trends = shots_df.groupby(['shot_zone', 'match_id']).agg({
        'is_goal': ['count', 'sum'],
        'is_on_target': 'sum'
    }).round(3)
    
    shot_trends.columns = ['total_shots', 'goals', 'shots_on_target']
    shot_trends['conversion_rate'] = (shot_trends['goals'] / shot_trends['total_shots']).fillna(0).round(3)
    
    return shot_trends.reset_index()


# ====================================================================
# MOMENTUM ANALYSIS - Time-based Insights
# ====================================================================

def extract_match_momentum(
    match_id: int,
    league: str,
    season: str,
    time_intervals: int = 15,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract match momentum analysis based on event frequency and success.
    
    Args:
        match_id: WhoScored match identifier
        league: League identifier
        season: Season identifier
        time_intervals: Time interval in minutes for momentum analysis
        verbose: Show progress
        
    Returns:
        DataFrame with momentum analysis by time periods
    """
    if verbose:
        print(f"📊 Extracting momentum analysis for match {match_id}")
    
    # Get all events
    events = extract_match_events(match_id, league, season, verbose=False)
    
    if events.empty:
        if verbose:
            print(f"   ❌ No events found")
        return pd.DataFrame()
    
    # Create time intervals
    events['time_interval'] = (events['minute'] // time_intervals) * time_intervals
    
    # Calculate momentum by team and time interval
    momentum_data = []
    
    for team in events['team'].unique():
        team_events = events[events['team'] == team]
        
        for interval in range(0, 90, time_intervals):
            interval_events = team_events[
                (team_events['time_interval'] == interval)
            ]
            
            if not interval_events.empty:
                momentum_data.append({
                    'team': team,
                    'time_interval': f"{interval}-{interval + time_intervals}",
                    'total_events': len(interval_events),
                    'successful_events': len(interval_events[interval_events.get('is_successful', False)]),
                    'success_rate': len(interval_events[interval_events.get('is_successful', False)]) / len(interval_events) * 100,
                    'attacking_events': len(interval_events[interval_events['field_zone'].str.contains('Attacking', na=False)]),
                    'defensive_events': len(interval_events[interval_events['field_zone'].str.contains('Defensive', na=False)]),
                    'middle_events': len(interval_events[interval_events['field_zone'].str.contains('Middle', na=False)])
                })
    
    momentum_df = pd.DataFrame(momentum_data)
    
    if verbose and not momentum_df.empty:
        print(f"   ✅ Momentum analysis: {len(momentum_df)} time intervals analyzed")
    
    return momentum_df