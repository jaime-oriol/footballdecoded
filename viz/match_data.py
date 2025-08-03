#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from scipy.interpolate import interp2d, RegularGridInterpolator
from scipy.spatial import ConvexHull, Delaunay
from shapely.geometry.polygon import Polygon

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (whoscored_extract_match_events, whoscored_extract_pass_network,
                     understat_extract_shot_events)
from scrappers import Understat

# xThreat grid
XT_GRID = np.array([
    [0.00483, 0.00637, 0.00844, 0.01174, 0.01988, 0.02474, 0.03257, 0.03438, 0.02313, 0.01847, 0.01399, 0.00857],
    [0.00701, 0.00979, 0.01311, 0.01858, 0.02993, 0.04155, 0.05201, 0.05514, 0.04194, 0.02928, 0.02156, 0.01371],
    [0.01048, 0.0145, 0.02012, 0.0289, 0.04332, 0.06203, 0.08037, 0.08593, 0.06459, 0.04482, 0.0329, 0.02071],
    [0.01655, 0.02257, 0.03147, 0.04593, 0.06853, 0.09604, 0.12674, 0.14082, 0.10225, 0.07231, 0.05322, 0.03238],
    [0.02498, 0.03464, 0.04932, 0.07309, 0.10568, 0.14973, 0.19926, 0.22421, 0.16121, 0.11366, 0.08228, 0.05092],
    [0.03853, 0.05325, 0.07773, 0.11445, 0.16439, 0.22821, 0.31086, 0.35597, 0.24897, 0.17836, 0.12983, 0.08099],
    [0.05641, 0.07852, 0.11556, 0.17078, 0.24459, 0.3353, 0.46341, 0.54065, 0.36872, 0.2677, 0.1917, 0.12165],
    [0.08795, 0.11808, 0.17804, 0.26294, 0.37277, 0.5022, 0.68894, 0.81764, 0.5481, 0.39934, 0.29327, 0.18853]
])

def extract_match_complete(ws_id: int, us_id: int, league: str, season: str,
                          home_team: str, away_team: str, match_date: str) -> Dict[str, pd.DataFrame]:
    print(f"\nExtracting: {home_team} vs {away_team} ({match_date})")
    print("-" * 50)
    
    ws_data = _get_whoscored_data(ws_id, league, season)
    us_data = _get_understat_data(us_id, league, season)
    
    events = ws_data.get('events', pd.DataFrame())
    if events.empty:
        return {}
    
    # PIPELINE COMPLETO DE ENRIQUECIMIENTO
    events = _add_carries(events)
    events = _add_xthreat(events)
    events = _add_pre_assists(events)
    events = _add_possession_chains(events)
    events = _add_progressive_actions(events)
    events = _add_box_entries(events)
    events = _add_pass_outcomes(events)
    events = _add_action_classifications(events)
    events = _add_zone_classification(events)
    events = _merge_shot_xg(events, us_data.get('shots', pd.DataFrame()))
    
    # Generate convex hulls for spatial analysis
    hull_data = _generate_team_hulls(events, home_team, away_team)
    
    # Generate 5 validation CSVs as per plan
    _generate_validation_csvs(events, hull_data, home_team, away_team, match_date, league, season)
    
    # Summary
    shots = events[events['event_type'].str.contains('Shot|Goal', case=False, na=False)]
    if not shots.empty:
        goals = shots[shots['type'].str.contains('Goal', case=False, na=False)]
        xg_total = shots['xg'].sum() if 'xg' in shots.columns else 0
        print(f"\nShots: {len(shots)} | Goals: {len(goals)} | xG: {xg_total:.2f}")
    
    return {'status': 'complete', 'events_count': len(events)}

def _get_whoscored_data(match_id: int, league: str, season: str) -> Dict:
    try:
        events = whoscored_extract_match_events(match_id, league, season, verbose=False)
        if events.empty:
            return {}
        return {'events': events}
    except Exception as e:
        print(f"WhoScored error: {e}")
        return {}

def _get_understat_data(match_id: int, league: str, season: str) -> Dict:
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        shots = understat.read_shot_events(match_id=match_id)
        if shots.empty:
            return {}
        
        players = understat.read_player_match_stats(match_id=match_id)
        if not players.empty:
            players_reset = players.reset_index()
            player_lookup = players_reset.set_index('player_id')['player'].to_dict()
            team_lookup = players_reset.set_index('team_id')['team'].to_dict()
            
            shots = shots.reset_index()
            shots['player'] = shots['player_id'].map(player_lookup)
            shots['team'] = shots['team_id'].map(team_lookup)
        else:
            shots = shots.reset_index()
        
        return {'shots': shots}
    except Exception:
        return {}

def _add_carries(events: pd.DataFrame) -> pd.DataFrame:
    """Enhanced carry detection with take-on tracking"""
    events = events.sort_values(['minute', 'second']).reset_index(drop=True)
    carries = []
    
    for idx in range(len(events) - 1):
        curr = events.iloc[idx]
        next_idx = idx + 1
        take_ons = 0
        
        while next_idx < len(events):
            next_evt = events.iloc[next_idx]
            
            # Count successful take-ons in sequence
            if (next_evt['team'] == curr['team'] and 
                next_evt['event_type'] == 'TakeOn' and 
                next_evt['outcome_type'] == 'Successful'):
                take_ons += 1
                next_idx += 1
                continue
            
            # Skip failed take-ons and fouls
            if next_evt['event_type'] in ['TakeOn', 'Challenge', 'Foul']:
                next_idx += 1
                continue
                
            if next_evt['team'] != curr['team']:
                break
                
            dt = (next_evt['minute'] - curr['minute']) * 60 + (next_evt.get('second', 0) - curr.get('second', 0))
            if dt < 1 or dt > 10:
                break
                
            dx = abs(next_evt['x'] - curr.get('end_x', curr['x']))
            dy = abs(next_evt['y'] - curr.get('end_y', curr['y']))
            distance = np.sqrt(dx**2 + dy**2)
            
            if 3 <= distance <= 60:
                carry = curr.copy()
                carry['event_id'] = curr.get('event_id', idx) + 0.5
                carry['type'] = 'Carry'
                carry['event_type'] = 'Carry'
                carry['outcome_type'] = 'Successful'
                carry['x'] = curr.get('end_x', curr['x'])
                carry['y'] = curr.get('end_y', curr['y'])
                carry['end_x'] = next_evt['x']
                carry['end_y'] = next_evt['y']
                carry['minute'] = (curr['minute'] + next_evt['minute']) / 2
                carry['second'] = (curr.get('second', 0) + next_evt.get('second', 0)) / 2
                carry['take_ons_in_carry'] = take_ons
                carries.append(carry)
            break
    
    if carries:
        carries_df = pd.DataFrame(carries)
        events = pd.concat([events, carries_df], ignore_index=True)
        events = events.sort_values(['minute', 'second']).reset_index(drop=True)
    
    return events

def _add_xthreat(events: pd.DataFrame) -> pd.DataFrame:
    """Enhanced xThreat with interpolation"""
    move_events = events[events['event_type'].isin(['Pass', 'Carry']) & 
                        (events['outcome_type'] == 'Successful')]
    
    if move_events.empty:
        events['xthreat'] = 0.0
        events['xthreat_gen'] = 0.0
        return events
    
    # Create interpolator
    x = np.linspace(0, 100, 12)
    y = np.linspace(0, 100, 8)
    f = RegularGridInterpolator((y, x), XT_GRID, method='linear', 
                               bounds_error=False, fill_value=0)
    
    events['xthreat'] = 0.0
    events['xthreat_gen'] = 0.0
    
    for idx in move_events.index:
        x1, y1 = events.loc[idx, 'x'], events.loc[idx, 'y']
        x2, y2 = events.loc[idx, 'end_x'], events.loc[idx, 'end_y']
        
        if pd.notna(x1) and pd.notna(y1) and pd.notna(x2) and pd.notna(y2):
            xt_start = float(f([y1, x1]))
            xt_end = float(f([y2, x2]))
            xt_diff = xt_end - xt_start
            
            events.loc[idx, 'xthreat'] = xt_diff
            events.loc[idx, 'xthreat_gen'] = max(0, xt_diff)
    
    return events

def _add_pre_assists(events: pd.DataFrame) -> pd.DataFrame:
    """Enhanced pre-assist detection"""
    events['is_pre_assist'] = False
    
    # Find assists first
    assist_events = events[events.get('is_assist', False) == True]
    
    for idx, assist_event in assist_events.iterrows():
        assister = assist_event['player']
        team = assist_event['team']
        period = assist_event.get('period', 'FirstHalf')
        
        # Look backwards for the pass to the assister
        scan_idx = idx - 1
        while scan_idx >= 0:
            prev_event = events.iloc[scan_idx]
            
            # Same period and team
            if (prev_event.get('period', 'FirstHalf') != period or 
                prev_event['team'] != team):
                break
                
            # Check if this event led to the assister
            if (prev_event['event_type'] == 'Pass' and 
                prev_event['outcome_type'] == 'Successful' and
                prev_event.get('next_player') == assister):
                events.loc[scan_idx, 'is_pre_assist'] = True
                break
                
            scan_idx -= 1
    
    return events

def _add_possession_chains(events: pd.DataFrame) -> pd.DataFrame:
    """Enhanced possession chain detection"""
    events['possession_id'] = 0
    events['possession_team'] = None
    
    possession_id = 1
    current_team = None
    
    for idx in range(len(events)):
        event = events.iloc[idx]
        
        # New possession on team change or period change
        if (event['team'] != current_team or 
            (idx > 0 and events.iloc[idx-1].get('period') != event.get('period'))):
            possession_id += 1
            current_team = event['team']
            
        events.loc[idx, 'possession_id'] = possession_id
        events.loc[idx, 'possession_team'] = current_team
    
    return events

def _add_progressive_actions(events: pd.DataFrame) -> pd.DataFrame:
    """Advanced progressive action detection"""
    events['is_progressive'] = False
    
    move_events = events[(events['event_type'].isin(['Pass', 'Carry'])) & 
                        (events['outcome_type'] == 'Successful')]
    
    for idx in move_events.index:
        event = events.loc[idx]
        x1, y1 = event['x'], event['y']
        x2, y2 = event['end_x'], event['end_y']
        
        if pd.isna(x2) or pd.isna(y2):
            continue
            
        # Convert to yards (120x80 pitch)
        x1_yards = x1 * 1.2
        y1_yards = y1 * 0.8
        x2_yards = x2 * 1.2
        y2_yards = y2 * 0.8
        
        # Distance to goal calculation
        delta_goal = (np.sqrt((120-x1_yards)**2 + (40-y1_yards)**2) - 
                     np.sqrt((120-x2_yards)**2 + (40-y2_yards)**2))
        
        # Progressive criteria
        if ((x1 < 50 and x2 < 50 and delta_goal >= 30) or  # Own half: 30m
            (x1 < 50 <= x2 and delta_goal >= 15) or         # Cross halfway: 15m
            (x1 >= 50 and x2 >= 50 and delta_goal >= 10)):  # Opp half: 10m
            events.loc[idx, 'is_progressive'] = True
    
    return events

def _add_box_entries(events: pd.DataFrame) -> pd.DataFrame:
    """Detect passes and carries into the penalty box"""
    events['is_box_entry'] = False
    
    move_events = events[(events['event_type'].isin(['Pass', 'Carry'])) & 
                        (events['outcome_type'] == 'Successful')]
    
    for idx in move_events.index:
        event = events.loc[idx]
        x1, y1 = event['x'], event['y']
        x2, y2 = event['end_x'], event['end_y']
        
        if pd.isna(x2) or pd.isna(y2):
            continue
            
        # Box boundaries (83-100 x, 21.1-78.9 y)
        in_box_start = (x1 >= 83 and 21.1 <= y1 <= 78.9)
        in_box_end = (x2 >= 83 and 21.1 <= y2 <= 78.9)
        
        # Entry into box
        if not in_box_start and in_box_end:
            events.loc[idx, 'is_box_entry'] = True
    
    return events

def _add_pass_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    """Classify pass outcomes based on subsequent events"""
    events['pass_outcome'] = None
    
    pass_events = events[events['event_type'] == 'Pass']
    
    for idx, pass_event in pass_events.iterrows():
        team = pass_event['team']
        period = pass_event.get('period', 'FirstHalf')
        
        # Look at next 5 seconds of events
        next_events = events[
            (events.index > idx) & 
            (events.index <= idx + 10) &  # Rough 5-second window
            (events.get('period', 'FirstHalf') == period)
        ]
        
        team_next_events = next_events[next_events['team'] == team]
        
        # Classify outcome
        if pass_event['outcome_type'] != 'Successful':
            outcome = 'Unsuccessful'
        elif 'Goal' in team_next_events['event_type'].values:
            outcome = 'Goal'
        elif any(team_next_events['event_type'].str.contains('Shot', na=False)):
            outcome = 'Shot'
        elif pass_event.get('is_assist', False):
            outcome = 'Assist'
        elif any(team_next_events.get('is_assist', False)):
            outcome = 'Key Pass'
        else:
            outcome = 'Retention'
            
        events.loc[idx, 'pass_outcome'] = outcome
    
    return events

def _add_zone_classification(events: pd.DataFrame) -> pd.DataFrame:
    """Add zone_id classification to events"""
    def get_zone(x, y):
        # 18 zones: 6x3 grid
        if x < 16.67:
            zone_x = 0
        elif x < 33.33:
            zone_x = 1
        elif x < 50:
            zone_x = 2
        elif x < 66.67:
            zone_x = 3
        elif x < 83.33:
            zone_x = 4
        else:
            zone_x = 5
        
        if y < 33.33:
            zone_y = 0
        elif y < 66.67:
            zone_y = 1
        else:
            zone_y = 2
        
        return zone_x * 3 + zone_y + 1
    
    events['zone_id'] = events.apply(lambda r: get_zone(r['x'], r['y']), axis=1)
    return events

def _add_action_classifications(events: pd.DataFrame) -> pd.DataFrame:
    """Classify events as offensive or defensive actions"""
    events['action_type'] = 'Neutral'
    
    # Offensive actions
    offensive_types = ['Pass', 'Carry', 'Shot', 'Goal', 'TakeOn', 'Touch']
    events.loc[events['event_type'].isin(offensive_types), 'action_type'] = 'Offensive'
    
    # Defensive actions  
    defensive_types = ['Tackle', 'Interception', 'Clearance', 'BallRecovery', 'Block']
    events.loc[events['event_type'].isin(defensive_types), 'action_type'] = 'Defensive'
    
    # Aerial duels classification
    if 'qualifiers' in events.columns:
        events.loc[
            (events['event_type'] == 'Aerial') & 
            events['qualifiers'].str.contains('Offensive', na=False), 
            'action_type'
        ] = 'Offensive'
        
        events.loc[
            (events['event_type'] == 'Aerial') & 
            events['qualifiers'].str.contains('Defensive', na=False), 
            'action_type'
        ] = 'Defensive'
    
    return events

def _merge_shot_xg(events: pd.DataFrame, us_shots: pd.DataFrame) -> pd.DataFrame:
    """Enhanced xG merging with better matching"""
    if us_shots.empty:
        events['xg'] = 0.0
        return events
    
    events['xg'] = 0.0
    shot_events = events[events['event_type'].str.contains('Shot|Goal', case=False, na=False)]
    
    for idx, shot in shot_events.iterrows():
        minute = shot['minute']
        team = shot['team']
        player = shot['player']
        
        # Try exact match first
        exact_match = us_shots[
            (us_shots['minute'] == minute) & 
            (us_shots['team'] == team)
        ]
        
        if not exact_match.empty:
            events.loc[idx, 'xg'] = exact_match.iloc[0]['xg']
            continue
            
        # Fuzzy match within 2-minute window
        fuzzy_match = us_shots[
            (us_shots['minute'].between(minute-2, minute+2)) & 
            (us_shots['team'] == team)
        ]
        
        if not fuzzy_match.empty:
            # Get closest match
            time_diffs = abs(fuzzy_match['minute'] - minute)
            best_match = fuzzy_match.loc[time_diffs.idxmin()]
            events.loc[idx, 'xg'] = best_match['xg']
    
    return events

def _generate_team_hulls(events: pd.DataFrame, home_team: str, away_team: str) -> pd.DataFrame:
    """Generate convex hulls for both teams"""
    hull_data = []
    
    for team in [home_team, away_team]:
        team_events = events[
            (events['team'] == team) & 
            events['x'].notna() & 
            events['y'].notna()
        ]
        
        if len(team_events) >= 3:
            hull_info = _create_convex_hull(team_events, team)
            if hull_info is not None:
                hull_data.append(hull_info)
    
    return pd.DataFrame(hull_data) if hull_data else pd.DataFrame()

def _create_convex_hull(events_df: pd.DataFrame, team_name: str) -> Dict:
    """Create convex hull from team events"""
    if len(events_df) < 3:
        return None
        
    # Get event positions
    positions = events_df[['x', 'y']].values
    
    # Remove outliers (beyond 1 std dev)
    center_x, center_y = positions[:, 0].mean(), positions[:, 1].mean()
    distances = np.sqrt((positions[:, 0] - center_x)**2 + (positions[:, 1] - center_y)**2)
    std_dist = distances.std()
    
    # Keep points within 1 standard deviation
    mask = distances <= std_dist
    filtered_positions = positions[mask]
    
    if len(filtered_positions) < 3:
        filtered_positions = positions
    
    try:
        hull = ConvexHull(filtered_positions)
        hull_points = filtered_positions[hull.vertices]
        
        return {
            'team': team_name,
            'hull_points_x': hull_points[:, 0].tolist(),
            'hull_points_y': hull_points[:, 1].tolist(),
            'hull_area': hull.volume,
            'hull_perimeter': hull.area,
            'center_x': center_x,
            'center_y': center_y,
            'events_count': len(events_df)
        }
    except:
        return None

def _generate_validation_csvs(events: pd.DataFrame, hull_data: pd.DataFrame, 
                            home_team: str, away_team: str, match_date: str, 
                            league: str, season: str):
    """Generate 5 optimized validation CSVs for perfect visualizations"""
    
    # Create simple data directory
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. match_events.csv - TODOS los eventos enriquecidos
    events.to_csv(os.path.join(base_dir, 'match_events.csv'), index=False)
    print(f"1. match_events.csv: {len(events)} events")
    
    # 2. player_network.csv - Conexiones y posiciones optimizadas para viz
    network_df = _build_player_network_optimized(events)
    network_df.to_csv(os.path.join(base_dir, 'player_network.csv'), index=False)
    print(f"2. player_network.csv: {len(network_df)} records")
    
    # 3. match_aggregates.csv - Stats separados perfectamente por tipo
    aggregates = _build_match_aggregates_optimized(events)
    aggregates.to_csv(os.path.join(base_dir, 'match_aggregates.csv'), index=False)
    print(f"3. match_aggregates.csv: {len(aggregates)} records")
    
    # 4. spatial_analysis.csv - Datos espaciales optimizados para viz
    spatial_df = _build_spatial_analysis_optimized(events, hull_data)
    spatial_df.to_csv(os.path.join(base_dir, 'spatial_analysis.csv'), index=False)
    print(f"4. spatial_analysis.csv: {len(spatial_df)} spatial records")
    
    # 5. match_info.csv - Metadata optimizada para contexto
    info_df = _build_match_info_optimized(events, home_team, away_team, match_date, league, season)
    info_df.to_csv(os.path.join(base_dir, 'match_info.csv'), index=False)
    print(f"5. match_info.csv: {len(info_df)} info records")
    
def _build_player_network_optimized(events: pd.DataFrame) -> pd.DataFrame:
    """Optimized player network for perfect visualizations"""
    network_data = []
    
    # 1. PASS CONNECTIONS - para network graphs
    passes = events[
        (events['event_type'] == 'Pass') & 
        (events['outcome_type'] == 'Successful') &
        events['next_player'].notna()
    ]
    
    for (team, passer, receiver), group in passes.groupby(['team', 'player', 'next_player']):
        if passer != receiver:
            network_data.append({
                'record_type': 'connection',
                'team': team,
                'source_player': passer,
                'target_player': receiver,
                'connection_strength': len(group),
                'avg_x_start': round(group['x'].mean(), 2),
                'avg_y_start': round(group['y'].mean(), 2),
                'avg_x_end': round(group['end_x'].mean(), 2),
                'avg_y_end': round(group['end_y'].mean(), 2),
                'avg_xthreat': round(group['xthreat'].mean(), 4),
                'progressive_passes': int(group['is_progressive'].sum()),
                'box_entries': int(group['is_box_entry'].sum()),
                'pass_distance_avg': round(group['pass_distance'].mean(), 2),
                'connection_id': f"{team}_{passer}_{receiver}"
            })
    
    # 2. PLAYER POSITIONS - para heat maps y positioning
    for (player, team), player_events in events.groupby(['player', 'team']):
        if pd.notna(player):
            network_data.append({
                'record_type': 'position',
                'team': team,
                'source_player': player,
                'target_player': None,
                'connection_strength': 0,
                'avg_x_start': round(player_events['x'].mean(), 2),
                'avg_y_start': round(player_events['y'].mean(), 2),
                'avg_x_end': None,
                'avg_y_end': None,
                'avg_xthreat': round(player_events['xthreat_gen'].mean(), 4),
                'progressive_passes': 0,
                'box_entries': 0,
                'pass_distance_avg': 0,
                'connection_id': f"{team}_{player}_position",
                'total_actions': len(player_events),
                'minutes_active': round(player_events['minute'].max() - player_events['minute'].min(), 1),
                'position_variance_x': round(player_events['x'].std(), 2),
                'position_variance_y': round(player_events['y'].std(), 2),
                'xthreat_total': round(player_events['xthreat_gen'].sum(), 4)  # ← AÑADIDO
            })
    
    return pd.DataFrame(network_data)

def _build_match_aggregates_optimized(events: pd.DataFrame) -> pd.DataFrame:
    """Optimized aggregates with clean separation by type"""
    all_data = []
    
    # PLAYERS DATA - only player-relevant fields
    for (player, team), player_events in events.groupby(['player', 'team']):
        if pd.isna(player):
            continue
            
        passes = player_events[player_events['event_type'] == 'Pass']
        carries = player_events[player_events['event_type'] == 'Carry']
        
        player_data = {
            'entity_type': 'player',
            'entity_id': player,
            'entity_name': player,
            'team': team,
            
            # TIME & ACTIVITY (only for players)
            'minutes_active': round(player_events['minute'].max() - player_events['minute'].min(), 1),
            'total_actions': len(player_events),
            'actions_per_minute': round(len(player_events) / max(1, (player_events['minute'].max() - player_events['minute'].min())), 2),
            
            # POSITIONING FOR HEATMAPS (only for players)
            'avg_x': round(player_events['x'].mean(), 2),
            'avg_y': round(player_events['y'].mean(), 2),
            'position_variance_x': round(player_events['x'].std(), 2),
            'position_variance_y': round(player_events['y'].std(), 2),
            
            # ACTION CLASSIFICATION
            'offensive_actions': len(player_events[player_events['action_type'] == 'Offensive']),
            'defensive_actions': len(player_events[player_events['action_type'] == 'Defensive']),
            'neutral_actions': len(player_events[player_events['action_type'] == 'Neutral']),
            
            # PASSING METRICS (only for players)
            'passes_attempted': len(passes),
            'passes_completed': len(passes[passes['outcome_type'] == 'Successful']),
            'pass_completion_pct': round(len(passes[passes['outcome_type'] == 'Successful']) / max(1, len(passes)) * 100, 1),
            'progressive_passes': int(player_events['is_progressive'].sum()),
            'box_entries': int(player_events['is_box_entry'].sum()),
            
            # ADVANCED METRICS
            'xthreat_total': round(player_events['xthreat_gen'].sum(), 4),
            'xthreat_per_action': round(player_events['xthreat_gen'].sum() / max(1, len(player_events)), 4),
            'pre_assists': int(player_events['is_pre_assist'].sum()),
            
            # CARRY METRICS (only for players)
            'carries': len(carries),
            'progressive_carries': len(carries[carries['is_progressive'] == True]),
            'carry_distance_total': round(carries['pass_distance'].sum(), 2),
            
            # PASS OUTCOMES FOR FLOW VIZ (only for players)
            'passes_to_goal': int(passes[passes['pass_outcome'] == 'Goal'].count().iloc[0] if 'pass_outcome' in passes.columns and not passes.empty else 0),
            'passes_to_shot': int(passes[passes['pass_outcome'] == 'Shot'].count().iloc[0] if 'pass_outcome' in passes.columns and not passes.empty else 0),
            'key_passes': int(passes[passes['pass_outcome'] == 'Key Pass'].count().iloc[0] if 'pass_outcome' in passes.columns and not passes.empty else 0),
            
            # ZONE FIELDS - NULL for players
            'zone_id': None,
            'zone_x_center': None,
            'zone_y_center': None,
            'possession_pct': None,
            'action_density': None
        }
        all_data.append(player_data)
    
    # ZONES DATA - only zone-relevant fields  
    for (team, zone_id), zone_events in events.groupby(['team', 'zone_id']):
        zone_names = {
            1: 'Def_Left', 2: 'Def_Center', 3: 'Def_Right',
            4: 'DefMid_Left', 5: 'DefMid_Center', 6: 'DefMid_Right', 
            7: 'Mid_Left', 8: 'Mid_Center', 9: 'Mid_Right',
            10: 'AttMid_Left', 11: 'AttMid_Center', 12: 'AttMid_Right',
            13: 'Att_Left', 14: 'Att_Center', 15: 'Att_Right',
            16: 'FinalThird_Left', 17: 'FinalThird_Center', 18: 'FinalThird_Right'
        }
        
        team_total_actions = len(events[events['team'] == team])
        
        zone_data = {
            'entity_type': 'zone',
            'entity_id': f'{team}_zone_{zone_id}',
            'entity_name': zone_names.get(zone_id, f'Zone_{zone_id}'),
            'team': team,
            
            # ZONE IDENTIFICATION
            'zone_id': int(zone_id),
            'zone_x_center': round(zone_events['x'].mean(), 2),
            'zone_y_center': round(zone_events['y'].mean(), 2),
            
            # ACTIVITY INTENSITY FOR PRESSURE MAPS
            'total_actions': len(zone_events),
            'possession_pct': round(len(zone_events) / team_total_actions * 100, 1),
            'action_density': round(len(zone_events) / max(1, zone_events['minute'].nunique()), 2),
            
            # ACTION TYPES FOR TACTICAL VIZ
            'offensive_actions': len(zone_events[zone_events['action_type'] == 'Offensive']),
            'defensive_actions': len(zone_events[zone_events['action_type'] == 'Defensive']),
            'neutral_actions': len(zone_events[zone_events['action_type'] == 'Neutral']),
            
            # THREAT GENERATION
            'xthreat_total': round(zone_events['xthreat_gen'].sum(), 4),
            'xthreat_per_action': round(zone_events['xthreat_gen'].sum() / max(1, len(zone_events)), 4),
            'progressive_actions': int(zone_events['is_progressive'].sum()),
            'box_entries': int(zone_events['is_box_entry'].sum()),
            
            # FLOW METRICS
            'passes_through_zone': len(zone_events[zone_events['event_type'] == 'Pass']),
            'successful_passes': len(zone_events[
                (zone_events['event_type'] == 'Pass') & 
                (zone_events['outcome_type'] == 'Successful')
            ]),
            
            # Set player-specific fields to None for clean separation
            'minutes_active': None,
            'actions_per_minute': None,
            'position_variance_x': None, 
            'position_variance_y': None,
            'passes_attempted': None,
            'passes_completed': None,
            'pass_completion_pct': None,
            'pre_assists': None,
            'carries': None,
            'progressive_carries': None,
            'carry_distance_total': None,
            'passes_to_goal': None,
            'passes_to_shot': None,
            'key_passes': None
        }
        all_data.append(zone_data)
    
    return pd.DataFrame(all_data)

def _build_spatial_analysis_optimized(events: pd.DataFrame, hull_data: pd.DataFrame) -> pd.DataFrame:
    """Optimized spatial analysis with processable coordinates"""
    spatial_data = []
    
    # 1. CONVEX HULLS - with JSON coordinates for easy visualization
    for _, hull in hull_data.iterrows():
        hull_coords = list(zip(hull['hull_points_x'], hull['hull_points_y']))
        
        spatial_data.append({
            'analysis_type': 'convex_hull',
            'team': hull['team'],
            'metric_name': f"{hull['team']}_team_hull",
            'coordinates_json': str(hull_coords),  # Processable format
            'hull_area': round(hull['hull_area'], 2),
            'hull_perimeter': round(hull['hull_perimeter'], 2),
            'center_x': round(hull['center_x'], 2),
            'center_y': round(hull['center_y'], 2),
            'events_count': int(hull['events_count']),
            'area_percentage': round(hull['hull_area'] / 10000 * 100, 2)  # % of total field
        })
    
    # 2. PRESSURE MAPS - optimized for heatmap visualizations
    for team in events['team'].unique():
        team_events = events[events['team'] == team]
        total_team_events = len(team_events)
        
        # Create 6x3 pressure grid (18 zones)
        for zone_id in range(1, 19):
            zone_events = team_events[team_events['zone_id'] == zone_id]
            
            if len(zone_events) > 0:
                # Zone boundaries for visualization
                zone_x = ((zone_id - 1) // 3) * 16.67 + 8.33  # Center X of zone
                zone_y = ((zone_id - 1) % 3) * 33.33 + 16.67  # Center Y of zone
                
                spatial_data.append({
                    'analysis_type': 'pressure_map',
                    'team': team,
                    'metric_name': f'zone_{zone_id}_pressure',
                    'zone_id': int(zone_id),
                    'zone_center_x': round(zone_x, 1),
                    'zone_center_y': round(zone_y, 1),
                    'pressure_intensity': round(len(zone_events) / total_team_events, 4),
                    'events_count': len(zone_events),
                    'avg_xthreat': round(zone_events['xthreat_gen'].mean(), 4),
                    'xthreat_total': round(zone_events['xthreat_gen'].sum(), 4),
                    'progressive_actions': int(zone_events['is_progressive'].sum()),
                    'action_efficiency': round(zone_events['is_progressive'].sum() / max(1, len(zone_events)), 3)
                })
    
    # 3. TERRITORIAL CONTROL - for control flow visualizations
    for team in events['team'].unique():
        team_events = events[events['team'] == team]
        total_team_events = len(team_events)
        
        # Analyze by field thirds
        thirds = [
            ('defensive', 0, 33.33),
            ('middle', 33.33, 66.67),
            ('attacking', 66.67, 100)
        ]
        
        for third_name, x_min, x_max in thirds:
            third_events = team_events[
                (team_events['x'] >= x_min) & (team_events['x'] < x_max)
            ]
            
            spatial_data.append({
                'analysis_type': 'territorial_control',
                'team': team,
                'metric_name': f'{third_name}_third_control',
                'third_name': third_name,
                'x_range_min': x_min,
                'x_range_max': x_max,
                'control_percentage': round(len(third_events) / total_team_events * 100, 1),
                'events_count': len(third_events),
                'xthreat_total': round(third_events['xthreat_gen'].sum(), 4),
                'avg_xthreat_per_action': round(third_events['xthreat_gen'].mean(), 4),
                'progressive_actions': int(third_events['is_progressive'].sum()),
                'box_entries': int(third_events['is_box_entry'].sum())
            })
    
    # 4. FLOW PATTERNS - for pass flow visualizations
    for team in events['team'].unique():
        passes = events[
            (events['team'] == team) & 
            (events['event_type'] == 'Pass') & 
            (events['outcome_type'] == 'Successful')
        ]
        
        # Analyze flow directions
        flow_patterns = []
        
        # Forward passes (progressing)
        forward_passes = passes[passes['end_x'] > passes['x']]
        if len(forward_passes) > 0:
            flow_patterns.append({
                'flow_type': 'forward',
                'pass_count': len(forward_passes),
                'avg_distance': round(forward_passes['pass_distance'].mean(), 2),
                'avg_xthreat': round(forward_passes['xthreat'].mean(), 4),
                'progressive_count': int(forward_passes['is_progressive'].sum())
            })
        
        # Backward passes (retention)
        backward_passes = passes[passes['end_x'] < passes['x']]
        if len(backward_passes) > 0:
            flow_patterns.append({
                'flow_type': 'backward',
                'pass_count': len(backward_passes),
                'avg_distance': round(backward_passes['pass_distance'].mean(), 2),
                'avg_xthreat': round(backward_passes['xthreat'].mean(), 4),
                'progressive_count': int(backward_passes['is_progressive'].sum())
            })
        
        # Lateral passes
        lateral_passes = passes[abs(passes['end_x'] - passes['x']) < 5]
        if len(lateral_passes) > 0:
            flow_patterns.append({
                'flow_type': 'lateral',
                'pass_count': len(lateral_passes),
                'avg_distance': round(lateral_passes['pass_distance'].mean(), 2),
                'avg_xthreat': round(lateral_passes['xthreat'].mean(), 4),
                'progressive_count': int(lateral_passes['is_progressive'].sum())
            })
        
        for pattern in flow_patterns:
            spatial_data.append({
                'analysis_type': 'flow_pattern',
                'team': team,
                'metric_name': f"{pattern['flow_type']}_flow",
                'flow_direction': pattern['flow_type'],
                'pass_count': pattern['pass_count'],
                'avg_distance': pattern['avg_distance'],
                'avg_xthreat': pattern['avg_xthreat'],
                'progressive_count': pattern['progressive_count'],
                'flow_efficiency': round(pattern['progressive_count'] / max(1, pattern['pass_count']), 3)
            })
    
    return pd.DataFrame(spatial_data)

def _build_match_info_optimized(events: pd.DataFrame, home_team: str, away_team: str, 
                               match_date: str, league: str, season: str) -> pd.DataFrame:
    """Optimized match info for perfect context and metadata viz"""
    info_data = []
    
    # 1. BASIC MATCH METADATA
    basic_info = [
        ('match_id', f"{home_team}_vs_{away_team}_{match_date}"),
        ('home_team', home_team),
        ('away_team', away_team),
        ('match_date', match_date),
        ('league', league),
        ('season', season),
        ('total_events', str(len(events))),
        ('match_duration_minutes', str(int(events['minute'].max())))
    ]
    
    for key, value in basic_info:
        info_data.append({
            'info_category': 'match_metadata',
            'info_key': key,
            'info_value': value,
            'team': None,
            'numeric_value': None
        })
    
    # 2. TEAM STATISTICS - for scoreboard and comparison viz
    for team in [home_team, away_team]:
        team_events = events[events['team'] == team]
        
        team_stats = {
            'total_events': len(team_events),
            'possession_pct': round(len(team_events) / len(events) * 100, 1),
            'passes_attempted': len(team_events[team_events['event_type'] == 'Pass']),
            'passes_completed': len(team_events[
                (team_events['event_type'] == 'Pass') & 
                (team_events['outcome_type'] == 'Successful')
            ]),
            'pass_accuracy': round(
                len(team_events[(team_events['event_type'] == 'Pass') & (team_events['outcome_type'] == 'Successful')]) /
                max(1, len(team_events[team_events['event_type'] == 'Pass'])) * 100, 1
            ),
            'xthreat_total': round(team_events['xthreat_gen'].sum(), 3),
            'progressive_actions': int(team_events['is_progressive'].sum()),
            'box_entries': int(team_events['is_box_entry'].sum()),
            'shots': len(team_events[team_events['event_type'].str.contains('Shot|Goal', case=False, na=False)]),
            'xg_total': round(team_events['xg'].sum(), 2)
        }
        
        for stat_key, stat_value in team_stats.items():
            info_data.append({
                'info_category': 'team_stats',
                'info_key': stat_key,
                'info_value': str(stat_value),
                'team': team,
                'numeric_value': float(stat_value) if isinstance(stat_value, (int, float)) else None
            })
    
    # 3. PLAYER PARTICIPATION - for lineup and substitution viz
    for team in [home_team, away_team]:
        team_players = events[events['team'] == team]['player'].dropna().unique()
        
        for player in team_players:
            player_events = events[(events['team'] == team) & (events['player'] == player)]
            first_minute = player_events['minute'].min()
            last_minute = player_events['minute'].max()
            
            info_data.append({
                'info_category': 'player_participation',
                'info_key': 'player_activity',
                'info_value': player,
                'team': team,
                'numeric_value': len(player_events),
                'first_minute': first_minute,
                'last_minute': last_minute,
                'minutes_active': round(last_minute - first_minute, 1)
            })
    
    # 4. MATCH TIMELINE - for timeline visualizations
    timeline_events = events[events['event_type'].str.contains('Goal|Card|Substitution', case=False, na=False)]
    
    for idx, event in timeline_events.iterrows():
        info_data.append({
            'info_category': 'timeline',
            'info_key': 'key_event',
            'info_value': f"{event['event_type']} - {event['player']}",
            'team': event['team'],
            'numeric_value': event['minute'],
            'event_type': event['event_type'],
            'minute': event['minute'],
            'period': event.get('period', 'Unknown')
        })
    
    # 5. DATA QUALITY METRICS - for validation viz
    quality_metrics = {
        'events_with_coordinates': len(events[(events['x'].notna()) & (events['y'].notna())]),
        'events_with_xthreat': len(events[events['xthreat_gen'] > 0]),
        'events_with_outcome': len(events[events['outcome_type'].notna()]),
        'successful_events': len(events[events['outcome_type'] == 'Successful']),
        'unique_players': events['player'].nunique(),
        'periods_played': len(events.get('period', pd.Series()).dropna().unique())
    }
    
    for metric_key, metric_value in quality_metrics.items():
        info_data.append({
            'info_category': 'data_quality',
            'info_key': metric_key,
            'info_value': str(metric_value),
            'team': None,
            'numeric_value': float(metric_value)
        })
    
    return pd.DataFrame(info_data)