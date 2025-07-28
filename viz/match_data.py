#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from scipy.interpolate import interp2d

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
    
    # Enrich events
    events = _add_carries(events)
    events = _add_xthreat(events)
    events = _add_pre_assists(events)
    events = _add_possession_chains(events)
    events = _add_progressive_real(events)
    events = _merge_shot_xg(events, us_data.get('shots', pd.DataFrame()))
    
    # Generate aggregates
    players = _aggregate_players(events)
    zones = _aggregate_zones(events)
    
    result = {
        'events': events,
        'players': players,
        'zones': zones
    }
    

    _save_match_data(result, league, season, home_team, away_team, match_date)
    
    # Summary
    shots = events[events['event_type'].str.contains('Shot|Goal', case=False, na=False)]
    if not shots.empty:
        goals = shots[shots['type'].str.contains('Goal', case=False, na=False)]
        xg_total = shots['xg'].sum() if 'xg' in shots.columns else 0
        print(f"\nShots: {len(shots)} | Goals: {len(goals)} | xG: {xg_total:.2f}")
    
    return result

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
    events = events.sort_values(['minute', 'second']).reset_index(drop=True)
    carries = []
    
    for idx in range(len(events) - 1):
        curr = events.iloc[idx]
        next_idx = idx + 1
        
        while next_idx < len(events):
            next_evt = events.iloc[next_idx]
            
            if next_evt['team'] != curr['team']:
                break
            
            if next_evt['event_type'] in ['TakeOn', 'Challenge', 'Foul']:
                next_idx += 1
                continue
                
            dt = (next_evt['minute'] - curr['minute']) * 60 + (next_evt.get('second', 0) - curr.get('second', 0))
            if dt < 1 or dt > 10:
                break
                
            dx = abs(next_evt['x'] - curr.get('end_x', curr['x']))
            dy = abs(next_evt['y'] - curr.get('end_y', curr['y']))
            distance = np.sqrt(dx**2 + dy**2)
            
            if 3 <= distance <= 60:
                carry = curr.copy()
                carry['event_id'] = curr['event_id'] if 'event_id' in curr else idx + 0.5
                carry['type'] = 'Carry'
                carry['event_type'] = 'Carry'
                carry['x'] = curr.get('end_x', curr['x'])
                carry['y'] = curr.get('end_y', curr['y'])
                carry['end_x'] = next_evt['x']
                carry['end_y'] = next_evt['y']
                carry['minute'] = (curr['minute'] + next_evt['minute']) / 2
                carry['second'] = ((curr.get('second', 0) + next_evt.get('second', 0)) / 2)
                carries.append(carry)
            break
    
    if carries:
        carries_df = pd.DataFrame(carries)
        events = pd.concat([events, carries_df], ignore_index=True)
        events = events.sort_values(['minute', 'second']).reset_index(drop=True)
    
    return events

def _add_xthreat(events: pd.DataFrame) -> pd.DataFrame:
    move_events = events[events['event_type'].isin(['Pass', 'Carry']) & 
                        (events['outcome_type'] == 'Successful')]
    
    if move_events.empty:
        events['xthreat'] = np.nan
        events['xthreat_gen'] = 0
        return events
    
    # Create interpolator with RegularGridInterpolator
    from scipy.interpolate import RegularGridInterpolator
    
    x = np.linspace(0, 100, 12)
    y = np.linspace(0, 100, 8)
    
    # RegularGridInterpolator expects (y,x) order
    f = RegularGridInterpolator((y, x), XT_GRID, method='linear', 
                               bounds_error=False, fill_value=0)
    
    # Calculate xT
    for idx in move_events.index:
        x1, y1 = events.loc[idx, 'x'], events.loc[idx, 'y']
        x2, y2 = events.loc[idx, 'end_x'], events.loc[idx, 'end_y']
        
        # Get xT values
        xt_start = f([y1, x1])
        xt_end = f([y2, x2])
        
        events.loc[idx, 'xthreat'] = float(xt_end - xt_start)
        events.loc[idx, 'xthreat_gen'] = max(0, float(xt_end - xt_start))
    
    events['xthreat'] = events['xthreat'].fillna(0)
    events['xthreat_gen'] = events['xthreat_gen'].fillna(0)
    
    return events

def _add_pre_assists(events: pd.DataFrame) -> pd.DataFrame:
    events['is_pre_assist'] = False
    
    for idx, event in events.iterrows():
        if event.get('is_assist', False):
            scan_idx = idx - 1
            assister = event['player']
            team = event['team']
            
            while scan_idx >= 0 and events.iloc[scan_idx]['team'] == team:
                if events.iloc[scan_idx].get('next_player') == assister:
                    events.loc[scan_idx, 'is_pre_assist'] = True
                    break
                scan_idx -= 1
    
    return events

def _add_possession_chains(events: pd.DataFrame) -> pd.DataFrame:
    events['possession_id'] = 0
    possession_id = 1
    current_team = None
    
    for idx in range(len(events)):
        if events.iloc[idx]['team'] != current_team:
            possession_id += 1
            current_team = events.iloc[idx]['team']
        events.loc[idx, 'possession_id'] = possession_id
    
    return events

def _add_progressive_real(events: pd.DataFrame) -> pd.DataFrame:
    events['is_progressive_real'] = False
    
    move_events = events[(events['event_type'].isin(['Pass', 'Carry'])) & 
                        (events['outcome_type'] == 'Successful')]
    
    for idx in move_events.index:
        x1, y1 = events.loc[idx, 'x'], events.loc[idx, 'y']
        x2, y2 = events.loc[idx, 'end_x'], events.loc[idx, 'end_y']
        
        # Convert to yards
        x1_yards = x1 * 1.2
        y1_yards = y1 * 0.8
        x2_yards = x2 * 1.2
        y2_yards = y2 * 0.8
        
        delta_goal = np.sqrt((120-x1_yards)**2 + (40-y1_yards)**2) - np.sqrt((120-x2_yards)**2 + (40-y2_yards)**2)
        
        if (x1 < 50 and x2 < 50 and delta_goal >= 32.8) or \
           (x1 < 50 <= x2 and delta_goal >= 16.4) or \
           (x1 >= 50 and x2 >= 50 and delta_goal >= 10.94):
            events.loc[idx, 'is_progressive_real'] = True
    
    return events

def _merge_shot_xg(events: pd.DataFrame, us_shots: pd.DataFrame) -> pd.DataFrame:
    if us_shots.empty:
        return events
    
    shot_events = events[events['event_type'].str.contains('Shot|Goal', case=False, na=False)]
    
    for idx, shot in shot_events.iterrows():
        minute = shot['minute']
        candidates = us_shots[us_shots['minute'].between(minute-2, minute+2)]
        
        if not candidates.empty:
            best_match = candidates.iloc[0]
            events.loc[idx, 'xg'] = best_match['xg']
    
    return events

def _aggregate_players(events: pd.DataFrame) -> pd.DataFrame:
    players = []
    
    for (player, team), player_events in events.groupby(['player', 'team']):
        if pd.isna(player):
            continue
            
        minutes = player_events['minute'].max() - player_events['minute'].min()
        
        players.append({
            'player': player,
            'team': team,
            'minutes': minutes,
            'xthreat_total': player_events['xthreat_gen'].sum(),
            'progressive_passes': len(player_events[(player_events['event_type'] == 'Pass') & 
                                                   (player_events['is_progressive_real'] == True)]),
            'progressive_carries': len(player_events[(player_events['event_type'] == 'Carry') & 
                                                    (player_events['is_progressive_real'] == True)]),
            'pre_assists': player_events['is_pre_assist'].sum(),
            'avg_x': player_events['x'].mean(),
            'avg_y': player_events['y'].mean()
        })
    
    return pd.DataFrame(players)

def _aggregate_zones(events: pd.DataFrame) -> pd.DataFrame:
    def get_zone(x, y):
        # 18 zones: 6x3 grid (6 horizontal, 3 vertical)
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
    
    zones = []
    for (team, zone_id), zone_events in events.groupby(['team', 'zone_id']):
        zones.append({
            'team': team,
            'zone_id': zone_id,
            'events_count': len(zone_events),
            'xthreat_total': zone_events['xthreat_gen'].sum(),
            'possession_pct': len(zone_events) / len(events[events['team'] == team]) * 100
        })
    
    return pd.DataFrame(zones)

def _save_match_data(data: Dict[str, pd.DataFrame], league: str, season: str,
                    home: str, away: str, date: str):
    # Simple save to /data/ folder
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(base_dir, exist_ok=True)
    
    filenames = {
        'events': 'events.csv',
        'players': 'players.csv',
        'zones': 'zones.csv'
    }
    
    saved = 0
    for key, filename in filenames.items():
        if key in data and not data[key].empty:
            filepath = os.path.join(base_dir, filename)
            data[key].to_csv(filepath, index=False)
            saved += 1
    
    print(f"Saved {saved} files to: {base_dir}")