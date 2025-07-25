#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (whoscored_extract_match_events, whoscored_extract_pass_network,
                     understat_extract_shot_events)
from scrappers import Understat

def extract_match_complete(ws_id: int, us_id: int, league: str, season: str,
                          home_team: str, away_team: str, match_date: str) -> Dict[str, pd.DataFrame]:
    """Extract complete match data from WhoScored and Understat."""
    print(f"\nExtracting: {home_team} vs {away_team} ({match_date})")
    print("-" * 50)
    
    ws_data = _get_whoscored_data(ws_id, league, season)
    us_data = _get_understat_data(us_id, league, season)
    
    result = {
        'shots': _merge_shots(ws_data.get('events', pd.DataFrame()), 
                             us_data.get('shots', pd.DataFrame())),
        'passes': _extract_passes(ws_data.get('events', pd.DataFrame())),
        'positions': _extract_positions(ws_data.get('pass_network', {})),
        'defensive': _extract_defensive(ws_data.get('events', pd.DataFrame())),
        'events': ws_data.get('events', pd.DataFrame()),
        'progressive': _extract_progressive(ws_data.get('events', pd.DataFrame())),
        'connections': _extract_connections(ws_data.get('pass_network', {}))
    }
    
    _save_match_data(result, league, season, home_team, away_team, match_date)
    
    # Summary
    if 'shots' in result and not result['shots'].empty:
        shots = result['shots']
        print(f"\nShots: {len(shots)} | Goals: {shots['is_goal'].sum()} | xG: {shots['xg'].sum():.2f}")
    
    return result

def _get_whoscored_data(match_id: int, league: str, season: str) -> Dict:
    """Extract WhoScored events and pass networks."""
    try:
        events = whoscored_extract_match_events(match_id, league, season, verbose=False)
        
        if events.empty:
            return {}
        
        data = {'events': events}
        teams = events['team'].unique()
        
        # Extract pass networks
        pass_networks = {}
        for team in teams:
            network = whoscored_extract_pass_network(match_id, team, league, season, 
                                                   min_passes=3, verbose=False)
            if network:
                for key in ['passes', 'positions', 'connections']:
                    if key not in pass_networks:
                        pass_networks[key] = []
                    if key in network and not network[key].empty:
                        pass_networks[key].append(network[key])
        
        # Combine networks
        for key, dfs in pass_networks.items():
            if dfs:
                data[f'pass_network_{key}'] = pd.concat(dfs, ignore_index=True)
        
        data['pass_network'] = {
            'passes': data.get('pass_network_passes', pd.DataFrame()),
            'positions': data.get('pass_network_positions', pd.DataFrame()),
            'connections': data.get('pass_network_connections', pd.DataFrame())
        }
        
        return data
        
    except Exception as e:
        print(f"WhoScored error: {e}")
        return {}

def _get_understat_data(match_id: int, league: str, season: str) -> Dict:
    """Extract Understat shots with player names."""
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        shots = understat.read_shot_events(match_id=match_id)
        if shots.empty:
            return {}
        
        # Map player IDs to names
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

def _merge_shots(ws_events: pd.DataFrame, us_shots: pd.DataFrame) -> pd.DataFrame:
    """Merge WhoScored and Understat shot data."""
    if ws_events.empty and us_shots.empty:
        return pd.DataFrame()
    
    # Extract WhoScored shots
    ws_shots = pd.DataFrame()
    if not ws_events.empty:
        shot_mask = (ws_events['event_type'].str.contains('Shot', case=False, na=False) | 
                    ws_events['type'].str.contains('Goal', case=False, na=False))
        ws_shots = ws_events[shot_mask].copy()
    
    if us_shots.empty:
        return _format_ws_shots(ws_shots)
    
    if ws_shots.empty:
        return _format_us_shots(us_shots)
    
    # Merge by minute and player name
    merged = []
    ws_used = set()
    
    for _, us_shot in us_shots.iterrows():
        us_minute = us_shot['minute']
        
        # Find candidates within 2 minutes
        candidates = ws_shots[
            (ws_shots['minute'].between(us_minute-2, us_minute+2)) &
            (~ws_shots.index.isin(ws_used))
        ]
        
        best_match = None
        for idx, ws_shot in candidates.iterrows():
            name_score = _name_match(us_shot.get('player'), ws_shot.get('player'))
            
            # Coordinates are identical in both sources
            if name_score >= 1 or len(candidates) == 1:
                best_match = (ws_shot, idx)
                break
        
        if best_match:
            ws_shot, ws_idx = best_match
            ws_used.add(ws_idx)
            merged.append(_create_merged_shot(us_shot, ws_shot))
        else:
            merged.append(_create_us_shot(us_shot))
    
    # Add unmatched WhoScored shots
    for idx, ws_shot in ws_shots.iterrows():
        if idx not in ws_used:
            merged.append(_create_ws_shot(ws_shot))
    
    return pd.DataFrame(merged)

def _name_match(name1, name2) -> int:
    """Simple name matching: 2=exact, 1=partial, 0=none."""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    
    n1, n2 = str(name1).lower(), str(name2).lower()
    
    if n1 == n2:
        return 2
    
    parts1 = n1.split()
    parts2 = n2.split()
    
    if any(p in parts2 for p in parts1 if len(p) > 2):
        return 1
    
    return 0

def _create_merged_shot(us: pd.Series, ws: pd.Series) -> dict:
    """Create merged shot record prioritizing Understat xG and WhoScored spatial."""
    return {
        'minute': us['minute'],
        'second': ws.get('second'),
        'player': ws['player'] if pd.notna(ws.get('player')) else us.get('player'),
        'team': ws['team'] if pd.notna(ws.get('team')) else us.get('team'),
        'x': ws['x'],
        'y': ws['y'],
        'xg': us['xg'],
        'outcome': us.get('result', 'Unknown'),
        'body_part': us.get('body_part') if pd.notna(us.get('body_part')) else None,
        'situation': us.get('situation'),
        'goal_mouth_y': ws.get('goal_mouth_y'),
        'goal_mouth_z': ws.get('goal_mouth_z'),
        'is_goal': us.get('result') == 'Goal',
        'is_blocked': us.get('result') == 'Blocked Shot',
        'zone': ws.get('field_zone'),
        'assist': us.get('assist_player'),
        'source': 'merged'
    }

def _create_us_shot(us: pd.Series) -> dict:
    """Create shot record from Understat only."""
    return {
        'minute': us['minute'],
        'player': us.get('player', f"Player_{us.get('player_id', 'Unknown')}"),
        'team': us.get('team', f"Team_{us.get('team_id', 'Unknown')}"),
        'x': us['location_x'] * 100,
        'y': us['location_y'] * 100,
        'xg': us['xg'],
        'outcome': us.get('result', 'Unknown'),
        'body_part': us.get('body_part') if pd.notna(us.get('body_part')) else None,
        'situation': us.get('situation'),
        'is_goal': us.get('result') == 'Goal',
        'is_blocked': us.get('result') == 'Blocked Shot',
        'assist': us.get('assist_player'),
        'source': 'understat_only'
    }

def _create_ws_shot(ws: pd.Series) -> dict:
    """Create shot record from WhoScored only."""
    return {
        'minute': ws['minute'],
        'second': ws.get('second'),
        'player': ws['player'],
        'team': ws['team'],
        'x': ws.get('x'),
        'y': ws.get('y'),
        'xg': 0.1,  # Default xG when not available
        'outcome': ws.get('outcome_type', 'Unknown'),
        'goal_mouth_y': ws.get('goal_mouth_y'),
        'goal_mouth_z': ws.get('goal_mouth_z'),
        'is_goal': 'Goal' in str(ws.get('type', '')),
        'zone': ws.get('field_zone'),
        'source': 'whoscored_only'
    }

def _format_ws_shots(shots: pd.DataFrame) -> pd.DataFrame:
    """Format WhoScored-only shots."""
    if shots.empty:
        return pd.DataFrame()
    return pd.DataFrame([_create_ws_shot(row) for _, row in shots.iterrows()])

def _format_us_shots(shots: pd.DataFrame) -> pd.DataFrame:
    """Format Understat-only shots."""
    if shots.empty:
        return pd.DataFrame()
    return pd.DataFrame([_create_us_shot(row) for _, row in shots.iterrows()])

def _extract_passes(events: pd.DataFrame) -> pd.DataFrame:
    """Extract all passes with spatial data."""
    if events.empty:
        return pd.DataFrame()
    
    passes = events[events['event_type'].str.contains('Pass', case=False, na=False)].copy()
    
    if passes.empty:
        return pd.DataFrame()
    
    # Calculate pass distance and progression
    passes['pass_distance'] = np.sqrt(
        (passes['end_x'] - passes['x'])**2 + 
        (passes['end_y'] - passes['y'])**2
    ).round(1)
    
    passes['is_progressive'] = (passes['end_x'] - passes['x']) >= 10
    
    return passes[['minute', 'second', 'player', 'team', 'x', 'y', 'end_x', 'end_y',
                  'pass_distance', 'is_progressive', 'is_successful', 'is_cross', 
                  'is_through_ball', 'field_zone', 'pass_length']].copy()

def _extract_positions(pass_network: Dict) -> pd.DataFrame:
    """Extract player average positions."""
    positions = pass_network.get('positions', pd.DataFrame())
    return positions if not positions.empty else pd.DataFrame()

def _extract_defensive(events: pd.DataFrame) -> pd.DataFrame:
    """Extract defensive actions with zones."""
    if events.empty:
        return pd.DataFrame()
    
    defensive_types = ['Tackle', 'Interception', 'Clearance', 'Block', 'Aerial']
    pattern = '|'.join(defensive_types)
    
    defensive = events[events['event_type'].str.contains(pattern, case=False, na=False)].copy()
    
    if not defensive.empty:
        # Classify defensive zones
        defensive['defensive_third'] = defensive['x'] < 33.33
        defensive['middle_third'] = (defensive['x'] >= 33.33) & (defensive['x'] < 66.66)
        defensive['attacking_third'] = defensive['x'] >= 66.66
    
    return defensive[['minute', 'second', 'player', 'team', 'event_type', 'x', 'y',
                     'is_successful', 'field_zone', 'defensive_third', 
                     'middle_third', 'attacking_third']].copy()

def _extract_progressive(events: pd.DataFrame) -> pd.DataFrame:
    """Extract progressive passes and carries (10+ meters towards goal)."""
    if events.empty:
        return pd.DataFrame()
    
    progressive = []
    
    # Progressive passes
    passes = events[events['event_type'].str.contains('Pass', case=False, na=False)]
    for _, p in passes.iterrows():
        if pd.notna(p.get('x')) and pd.notna(p.get('end_x')):
            prog = p['end_x'] - p['x']
            if prog >= 10:
                progressive.append({
                    'minute': p['minute'],
                    'player': p['player'],
                    'team': p['team'],
                    'action': 'pass',
                    'start_x': p['x'],
                    'start_y': p['y'],
                    'end_x': p['end_x'],
                    'end_y': p['end_y'],
                    'progression': round(prog, 1),
                    'is_successful': p.get('is_successful', True)
                })
    
    # Progressive carries
    carries = events[events['event_type'].str.contains('Carry|Dribble', case=False, na=False)]
    for _, c in carries.iterrows():
        if pd.notna(c.get('x')) and pd.notna(c.get('end_x')):
            prog = c['end_x'] - c['x']
            if prog >= 10:
                progressive.append({
                    'minute': c['minute'],
                    'player': c['player'],
                    'team': c['team'],
                    'action': 'carry',
                    'start_x': c['x'],
                    'start_y': c['y'],
                    'end_x': c['end_x'],
                    'end_y': c['end_y'],
                    'progression': round(prog, 1),
                    'is_successful': True
                })
    
    return pd.DataFrame(progressive)

def _extract_connections(pass_network: Dict) -> pd.DataFrame:
    """Extract pass connections between players."""
    connections = pass_network.get('connections', pd.DataFrame())
    return connections if not connections.empty else pd.DataFrame()

def _save_match_data(data: Dict[str, pd.DataFrame], league: str, season: str,
                    home: str, away: str, date: str):
    """Save all data to structured folders."""
    # Create folder name
    home_clean = ''.join(c for c in home[:3].upper() if c.isalnum())
    away_clean = ''.join(c for c in away[:3].upper() if c.isalnum())
    date_clean = date.replace('-', '')
    
    base_dir = os.path.join(os.path.dirname(__file__), 'data', league, season,
                           f"{home_clean}{away_clean}_{date_clean}")
    os.makedirs(base_dir, exist_ok=True)
    
    # Save CSVs
    filenames = {
        'shots': '1_shots_enhanced.csv',
        'passes': '2_passes_complete.csv',
        'positions': '3_player_positions.csv',
        'defensive': '4_defensive_actions.csv',
        'events': '5_all_events.csv',
        'progressive': '6_progressive_actions.csv',
        'connections': '7_pass_connections.csv'
    }
    
    saved = 0
    for key, filename in filenames.items():
        if key in data and not data[key].empty:
            filepath = os.path.join(base_dir, filename)
            data[key].to_csv(filepath, index=False)
            saved += 1
    
    print(f"Saved {saved} files to: {base_dir}")