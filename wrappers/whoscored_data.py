# ====================================================================
# FootballDecoded - WhoScored Optimized Spatial Data Extractor
# ====================================================================
# Compacto y eficiente para extraer SOLO datos espaciales únicos de WhoScored
# Focus: Coordenadas completas + análisis táctico + visualización ready
# ====================================================================

import sys
import os
import pandas as pd
import numpy as np
import warnings
import ast
from typing import Dict, List, Optional, Union
from datetime import datetime

# Add extractors to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import WhoScored

warnings.filterwarnings('ignore', category=FutureWarning)

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
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract ALL match events with complete spatial coordinates.
    
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
        
    Returns:
        DataFrame with ALL spatial events and tactical context
    """
    if verbose:
        print(f"🎯 Extracting spatial data from match {match_id}")
    
    try:
        whoscored = WhoScored(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   📊 Reading event stream...")
        
        events_df = whoscored.read_events(match_id=match_id, output_fmt='events')
        
        if events_df is None or events_df.empty:
            if verbose:
                print(f"   ❌ No events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(events_df)} events extracted")
        
        # Process spatial events with tactical analysis
        enhanced_events = _process_spatial_events(events_df, match_id, for_viz)
        
        # Apply filters if specified
        filtered_events = _apply_filters(enhanced_events, event_filter, player_filter, team_filter, verbose)
        
        if verbose and not filtered_events.empty:
            total_events = len(filtered_events)
            unique_players = filtered_events['player'].nunique()
            event_types = filtered_events['event_type'].nunique()
            
            print(f"   ✅ SUCCESS: {total_events} spatial events with coordinates")
            print(f"   📊 Players: {unique_players} | Event types: {event_types}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Event extraction failed: {str(e)}")
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
        print(f"🔗 Creating pass network for {team_name}")
    
    # Get all pass events with coordinates
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
    
    if verbose and network_data['passes'] is not None and not network_data['passes'].empty:
        total_passes = len(network_data['passes'])
        successful_passes = len(network_data['passes'][network_data['passes']['is_successful'] == True])
        success_rate = (successful_passes / total_passes * 100) if total_passes > 0 else 0
        
        print(f"   ✅ Pass network: {total_passes} passes analyzed")
        print(f"   🎯 Success rate: {success_rate:.1f}%")
        print(f"   👥 Players: {len(network_data['positions'])} | Connections: {len(network_data['connections'])}")
    
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
        print(f"🔥 Creating spatial heatmap for {player_name}")
    
    # Get all events for the player with coordinates
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
    
    # Create heatmap analysis
    heatmap_data = _calculate_player_heatmap(events_df, player_name)
    
    if verbose and not heatmap_data.empty:
        total_actions = heatmap_data['action_count'].sum()
        active_zones = len(heatmap_data[heatmap_data['action_count'] > 0])
        max_zone_actions = heatmap_data['action_count'].max()
        
        print(f"   ✅ Heatmap: {total_actions} actions across {active_zones} zones")
        print(f"   🔥 Hottest zone: {max_zone_actions} actions")
    
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
        print(f"⚽ Creating shot map with spatial analysis")
    
    # Get all shot events with coordinates
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
    
    # Enhance shots with spatial analysis
    enhanced_shots = _analyze_shot_events(shot_events)
    
    if verbose and not enhanced_shots.empty:
        total_shots = len(enhanced_shots)
        goals = len(enhanced_shots[enhanced_shots.get('is_goal', False) == True])
        shots_on_target = len(enhanced_shots[enhanced_shots.get('is_on_target', False) == True])
        
        print(f"   ✅ Shot map: {total_shots} shots analyzed")
        print(f"   ⚽ Goals: {goals} | On target: {shots_on_target}")
    
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
        print(f"🏟️ Analyzing field occupation for {team_name}")
    
    # Get all events for the team with coordinates
    team_events = extract_match_events(
        match_id, league, season, 
        team_filter=team_name,
        verbose=False
    )
    
    if team_events.empty:
        if verbose:
            print(f"   ❌ No events found for {team_name}")
        return pd.DataFrame()
    
    # Filter by time period if specified
    if time_period:
        team_events = _filter_by_time_period(team_events, time_period)
    
    # Calculate field occupation by zones
    occupation_data = _calculate_field_occupation(team_events, team_name)
    
    if verbose and not occupation_data.empty:
        total_events = occupation_data['event_count'].sum()
        dominant_zone = occupation_data.loc[occupation_data['event_count'].idxmax(), 'field_zone']
        
        print(f"   ✅ Occupation: {total_events} events analyzed")
        print(f"   🏟️ Dominant zone: {dominant_zone}")
    
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


def extract_missing_players(
    match_id: int,
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract injured and suspended players for tactical context."""
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
# CORE PROCESSING FUNCTIONS
# ====================================================================

def _process_spatial_events(events_df: pd.DataFrame, match_id: int, for_viz: bool = False) -> pd.DataFrame:
    """Process raw events into spatial analysis format."""
    
    if events_df.empty:
        return events_df
    
    enhanced_df = events_df.copy()
    
    # Add match context
    enhanced_df['match_id'] = match_id
    enhanced_df['data_source'] = 'whoscored'
    
    # Clean and unify coordinates
    enhanced_df = _unify_coordinates(enhanced_df)
    
    # Parse qualifiers into usable columns
    enhanced_df = _parse_qualifiers(enhanced_df)
    
    # Add spatial zones classification
    enhanced_df['field_zone'] = _classify_field_zones(enhanced_df['x'], enhanced_df['y'])
    
    # Add event outcome classification
    enhanced_df['is_successful'] = _classify_event_success(enhanced_df)
    
    # Standardize event types
    enhanced_df['event_type'] = enhanced_df['type'].fillna('Unknown')
    
    # Add sequence tracking for pass networks
    enhanced_df = _add_sequence_tracking(enhanced_df)
    
    # Add spatial calculations
    enhanced_df = _add_spatial_calculations(enhanced_df)
    
    # Optimize for visualization if requested
    if for_viz:
        enhanced_df = _optimize_for_visualization(enhanced_df)
    
    return enhanced_df


def _unify_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Unify coordinate system for consistent spatial analysis."""
    # Ensure x,y are primary coordinates
    if 'x' in df.columns and 'y' in df.columns:
        df['x'] = pd.to_numeric(df['x'], errors='coerce')
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
    
    # Ensure end coordinates are available
    if 'end_x' in df.columns and 'end_y' in df.columns:
        df['end_x'] = pd.to_numeric(df['end_x'], errors='coerce')
        df['end_y'] = pd.to_numeric(df['end_y'], errors='coerce')
    
    return df


def _parse_qualifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Parse key qualifiers into separate usable columns."""
    
    # Initialize qualifier columns
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
    
    # Parse qualifiers row by row (simplified)
    for idx in range(len(df)):
        try:
            qualifiers_str = str(df.iloc[idx]['qualifiers'])
            
            if qualifiers_str and qualifiers_str != '[]' and qualifiers_str != 'nan':
                qualifiers = ast.literal_eval(qualifiers_str)
                
                for q in qualifiers:
                    if isinstance(q, dict) and 'type' in q:
                        qualifier_name = q['type'].get('displayName', '')
                        
                        # Parse key qualifiers only
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
        
        # WhoScored coordinate system (0-100)
        x_pct = float(x)
        y_pct = float(y)
        
        # 9-zone tactical classification
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
    
    # Initialize tracking columns
    df['possession_sequence'] = 0
    df['next_player'] = None
    
    current_sequence = 0
    current_team = None
    
    for idx in range(len(df)):
        # Check possession changes
        if current_team != df.iloc[idx]['team']:
            current_sequence += 1
            current_team = df.iloc[idx]['team']
        
        df.iloc[idx, df.columns.get_loc('possession_sequence')] = current_sequence
        
        # Track next event for pass network
        if idx < len(df) - 1:
            next_event = df.iloc[idx + 1]
            
            # Only track if same team and reasonable time gap
            time_current = df.iloc[idx]['minute'] * 60 + df.iloc[idx]['second']
            time_next = next_event['minute'] * 60 + next_event['second']
            time_diff = time_next - time_current
            
            if (next_event['team'] == df.iloc[idx]['team'] and 0 <= time_diff <= 10):
                df.iloc[idx, df.columns.get_loc('next_player')] = next_event['player']
    
    return df


def _add_spatial_calculations(df: pd.DataFrame) -> pd.DataFrame:
    """Add spatial calculation columns."""
    
    # Distance to goal
    df['distance_to_goal'] = _calculate_distance_to_goal(df['x'], df['y'])
    
    # Pass distance
    df['pass_distance'] = _calculate_pass_distance(df['x'], df['y'], df['end_x'], df['end_y'])
    
    return df


def _calculate_distance_to_goal(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calculate distance to goal center."""
    
    distances = []
    goal_x, goal_y = 100, 50  # Goal center in WhoScored coordinates
    
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
    
    # Convert boolean columns properly
    bool_cols = ['is_successful', 'is_longball', 'is_header', 'is_cross', 'is_through_ball', 'is_assist']
    
    for col in bool_cols:
        if col in viz_df.columns:
            viz_df[col] = viz_df[col].astype(bool)
    
    # Ensure numeric columns are clean
    numeric_cols = ['x', 'y', 'end_x', 'end_y', 'minute', 'second', 'distance_to_goal', 'pass_distance']
    
    for col in numeric_cols:
        if col in viz_df.columns:
            viz_df[col] = pd.to_numeric(viz_df[col], errors='coerce')
    
    # Remove processing columns
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
    
    # All passes
    results['passes'] = successful_passes.copy()
    
    # Average positions per player
    if not successful_passes.empty:
        positions = successful_passes.groupby('player').agg({
            'x': 'mean',
            'y': 'mean',
            'match_id': 'count',  # Total passes
            'is_cross': 'sum',
            'is_longball': 'sum'
        }).round(2)
        
        positions.columns = ['avg_x', 'avg_y', 'total_passes', 'crosses', 'longballs']
        positions['team'] = team_name
        results['positions'] = positions.reset_index()
    
    # Pass connections between players (BIDIRECCIONAL)
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
        
        # Agrupar por DIRECCIÓN (A→B separado de B→A)
        directional_counts = connections_df.groupby(['team', 'source', 'target']).agg({
            'source_x': 'mean',
            'source_y': 'mean', 
            'target_x': 'mean',
            'target_y': 'mean',
            'team': 'count'  # Contar conexiones
        }).round(2)
        
        directional_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
        directional_counts = directional_counts.reset_index()
        
        # CREAR CONEXIONES BIDIRECCIONALES
        bidirectional_connections = []
        processed_pairs = set()
        
        for _, conn in directional_counts.iterrows():
            source = conn['source']
            target = conn['target']
            pass_count_a_to_b = conn['pass_count']
            
            # Buscar la conexión inversa (B→A)
            reverse_conn = directional_counts[
                (directional_counts['source'] == target) & 
                (directional_counts['target'] == source)
            ]
            
            pass_count_b_to_a = reverse_conn['pass_count'].iloc[0] if not reverse_conn.empty else 0
            
            # Crear identificador único para el par
            pair_id = tuple(sorted([source, target]))
            
            if pair_id not in processed_pairs:
                processed_pairs.add(pair_id)
                
                # Solo incluir si alguna dirección tiene suficientes pases
                if pass_count_a_to_b >= min_passes or pass_count_b_to_a >= min_passes:
                    
                    # Conexión A→B (si tiene suficientes pases)
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
                    
                    # Conexión B→A (si existe y tiene suficientes pases)
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
    
    # Group by field zones
    zone_analysis = events_df.groupby('field_zone').agg({
        'match_id': 'count',  # Action count
        'is_successful': ['sum', 'mean'],
        'x': 'mean',
        'y': 'mean'
    }).round(2)
    
    # Flatten column names
    zone_analysis.columns = ['action_count', 'successful_actions', 'success_rate', 'avg_x', 'avg_y']
    
    zone_analysis['player'] = player_name
    zone_analysis['total_actions'] = len(events_df)
    zone_analysis['zone_percentage'] = (zone_analysis['action_count'] / zone_analysis['total_actions'] * 100).round(2)
    zone_analysis['success_rate'] = (zone_analysis['success_rate'] * 100).round(2)
    
    return zone_analysis.reset_index()


def _analyze_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Enhance shot events with spatial analysis."""
    
    enhanced_df = shot_events.copy()
    
    # Add shot outcome classification
    if 'outcome_type' in enhanced_df.columns:
        enhanced_df['is_goal'] = enhanced_df['outcome_type'].str.contains('Goal', case=False, na=False)
        enhanced_df['is_on_target'] = enhanced_df['outcome_type'].isin(['Goal', 'Saved', 'SavedShot'])
        enhanced_df['is_blocked'] = enhanced_df['outcome_type'].str.contains('Block', case=False, na=False)
    
    # Add shot zone classification
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
        
        # Shot zone classification
        if x_pct >= 88:  # 6-yard box
            zones.append('Six_Yard_Box')
        elif x_pct >= 83:  # Penalty box
            if 35 <= y_pct <= 65:
                zones.append('Central_Penalty_Box')
            else:
                zones.append('Wide_Penalty_Box')
        elif x_pct >= 67:  # Penalty area edge
            zones.append('Penalty_Area_Edge')
        else:  # Long range
            zones.append('Long_Range')
    
    return pd.Series(zones, index=x_coords.index)


def _calculate_field_occupation(team_events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Calculate field occupation by zones."""
    
    occupation_data = team_events.groupby('field_zone').agg({
        'match_id': 'count',  # Event count
        'is_successful': ['sum', 'mean'],
        'x': 'mean',
        'y': 'mean'
    }).round(2)
    
    # Flatten columns
    occupation_data.columns = ['event_count', 'successful_events', 'success_rate', 'avg_x', 'avg_y']
    
    # Add percentages
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
        # Handle multiple DataFrames (e.g., pass network)
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
        
        print(f"📊 Exported {len(files_created)} spatial data files")
        return ", ".join(files_created)
    else:
        # Handle single DataFrame
        df = data.copy()
        
        # Optimize for visualization if requested
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
        
        print(f"📊 Exported spatial data: {full_filename}")
        print(f"   Rows: {len(df)} | Columns: {len(df.columns)}")
        
        return full_filename


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