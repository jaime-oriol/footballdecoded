# ====================================================================
# FootballDecoded Data Loading Pipeline - FIXED VERSION
# ====================================================================
# FIX: Ahora guarda TODAS las métricas extraídas por los wrappers
# ====================================================================

import sys
import os
import pandas as pd
import json
from typing import Dict, Optional
from datetime import datetime

# Add wrappers to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_players, fbref_get_teams,
                     understat_get_player, understat_get_team, fbref_get_league_players,
                     fbref_get_schedule)
from database.connection import DatabaseManager, get_db_manager

# ====================================================================
# CONFIGURATION
# ====================================================================

# Available domestic leagues
AVAILABLE_LEAGUES = [
    'ENG-Premier League',
    'ESP-La Liga',
    'ITA-Serie A', 
    'GER-Bundesliga',
    'FRA-Ligue 1'
]

# Champions League identifier
CHAMPIONS_LEAGUE = 'INT-Champions League'

# ====================================================================
# DATA NORMALIZATION FUNCTIONS
# ====================================================================

def _normalize_season_format(season: str) -> str:
    """Normalize season to YYYY-YY format consistently."""
    if not season:
        return season
    
    # Handle different formats
    if len(season) == 4 and season.isdigit():  # "2425" -> "2024-25"
        year = int(season[:2]) + 2000
        return f"{year}-{season[2:]}"
    elif len(season) == 7 and '-' in season:  # Already "2024-25"
        return season
    elif len(season) == 4 and season.startswith('20'):  # "2024" -> "2024-25"
        year = int(season)
        next_year = str(year + 1)[-2:]
        return f"{year}-{next_year}"
    
    return season

def _separate_metrics_from_basic_data(data: Dict, entity_type: str) -> tuple[Dict, Dict, Dict]:
    """
    Separate raw data into basic fields, FBref metrics, and Understat metrics.
    
    Args:
        data: Raw combined data from wrappers
        entity_type: 'player' or 'team'
        
    Returns:
        (basic_data, fbref_metrics, understat_metrics)
    """
    # Define basic identification fields
    if entity_type == 'player':
        basic_fields = {
            'player_name', 'team', 'league', 'season', 'nationality', 
            'position', 'age', 'birth_year'
        }
    else:  # team
        basic_fields = {
            'team_name', 'league', 'season'
        }
    
    # Add official names to basic fields
    basic_fields.update({
        'fbref_official_name', 'understat_official_name', 'official_player_name', 'official_team_name'
    })
    
    # Separate data
    basic_data = {}
    fbref_metrics = {}
    understat_metrics = {}
    
    for key, value in data.items():
        if key in basic_fields:
            basic_data[key] = value
        elif key.startswith('understat_'):
            understat_metrics[key] = value
        else:
            # Everything else goes to FBref metrics
            fbref_metrics[key] = value
    
    # Handle official names properly
    if entity_type == 'player':
        basic_data['fbref_official_name'] = basic_data.get('player_name') or basic_data.get('official_player_name')
        basic_data['understat_official_name'] = basic_data.get('official_player_name')
    else:  # team
        basic_data['fbref_official_name'] = basic_data.get('team_name') or basic_data.get('official_team_name')
        basic_data['understat_official_name'] = basic_data.get('official_team_name')
    
    # Clean up redundant fields
    for field in ['official_player_name', 'official_team_name']:
        basic_data.pop(field, None)
        fbref_metrics.pop(field, None)
        understat_metrics.pop(field, None)
    
    return basic_data, fbref_metrics, understat_metrics

# ====================================================================
# SMART UPDATE CHECKING FUNCTIONS
# ====================================================================

def _should_update_domestic_player(player_name: str, league: str, season: str, team: str, 
                                 new_matches_played: int, db: DatabaseManager) -> tuple[bool, str]:
    """Check if domestic player should be updated based on matches played."""
    try:
        query = """
        SELECT fbref_metrics->>'matches_played' as current_matches 
        FROM footballdecoded.players_domestic 
        WHERE player_name = %(player_name)s 
        AND league = %(league)s 
        AND season = %(season)s 
        AND team = %(team)s
        """
        result = pd.read_sql(query, db.engine, params={
            'player_name': player_name,
            'league': league,
            'season': season,
            'team': team
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches_played or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip ({current_matches} matches, no change)"
            
    except Exception as e:
        return True, f"error_check ({e})"

# Similar functions for other entity types...
def _should_update_european_player(player_name: str, season: str, team: str,
                                 new_matches_played: int, db: DatabaseManager) -> tuple[bool, str]:
    """Check if European player should be updated based on matches played."""
    try:
        query = """
        SELECT fbref_metrics->>'matches_played' as current_matches 
        FROM footballdecoded.players_european 
        WHERE player_name = %(player_name)s 
        AND competition = %(competition)s 
        AND season = %(season)s 
        AND team = %(team)s
        """
        result = pd.read_sql(query, db.engine, params={
            'player_name': player_name,
            'competition': CHAMPIONS_LEAGUE,
            'season': season,
            'team': team
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches_played or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip ({current_matches} matches, no change)"
            
    except Exception as e:
        return True, f"error_check ({e})"

def _should_update_domestic_team(team_name: str, league: str, season: str,
                               new_matches_played: int, db: DatabaseManager) -> tuple[bool, str]:
    """Check if domestic team should be updated based on matches played."""
    try:
        query = """
        SELECT fbref_metrics->>'matches_played' as current_matches 
        FROM footballdecoded.teams_domestic 
        WHERE team_name = %(team_name)s 
        AND league = %(league)s 
        AND season = %(season)s
        """
        result = pd.read_sql(query, db.engine, params={
            'team_name': team_name,
            'league': league,
            'season': season
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches_played or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip ({current_matches} matches, no change)"
            
    except Exception as e:
        return True, f"error_check ({e})"

def _should_update_european_team(team_name: str, season: str,
                               new_matches_played: int, db: DatabaseManager) -> tuple[bool, str]:
    """Check if European team should be updated based on matches played."""
    try:
        query = """
        SELECT fbref_metrics->>'matches_played' as current_matches 
        FROM footballdecoded.teams_european 
        WHERE team_name = %(team_name)s 
        AND competition = %(competition)s 
        AND season = %(season)s
        """
        result = pd.read_sql(query, db.engine, params={
            'team_name': team_name,
            'competition': CHAMPIONS_LEAGUE,
            'season': season
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches_played or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip ({current_matches} matches, no change)"
            
    except Exception as e:
        return True, f"error_check ({e})"

# ====================================================================
# DOMESTIC DATA LOADING FUNCTIONS
# ====================================================================

def load_domestic_players(league: str, season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load all players from specific domestic league and season.
    FIXED: Now correctly handles pandas Series extraction.
    """
    if verbose:
        print(f"🔍 Loading players from {league} - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get all players from league
        players_list_df = fbref_get_league_players(league, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"❌ No players found for {league} {season}")
            return stats
        
        # Get unique players with their teams
        players_data = players_list_df[['player', 'team']].drop_duplicates()
        stats['total_players'] = len(players_data)
        
        if verbose:
            print(f"📊 Found {len(players_data)} players to process")
            print("🎯 Extracting FBref + Understat data...\n")
        
        # Process each player - FIX: Extract scalar values correctly
        for i, (idx, row) in enumerate(players_data.iterrows(), 1):
            # ✅ FIX: Extract scalar values from pandas Series
            player_name = str(row['player']) if pd.notna(row['player']) else 'Unknown'
            team = str(row['team']) if pd.notna(row['team']) else 'Unknown'
            
            # Skip if invalid data
            if player_name == 'Unknown' or team == 'Unknown':
                if verbose:
                    print(f"[{i:3d}/{len(players_data)}] ❌ Invalid data: {player_name} ({team})")
                stats['failed'] += 1
                continue
            
            if verbose:
                print(f"[{i:3d}/{len(players_data)}] {player_name} ({team})", end=" ")
            
            try:
                # Get FBref data first to check matches played
                fbref_data = fbref_get_player(player_name, league, season)
                if not fbref_data:
                    if verbose:
                        print("❌ No FBref data")
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = _should_update_domestic_player(
                    player_name, league, season, team, new_matches, db
                )
                
                if not should_update:
                    if verbose:
                        print(f"⏭️  {reason}")
                    stats['skipped'] += 1
                    continue
                
                # Get Understat data
                understat_data = understat_get_player(player_name, league, season)
                
                # Merge ALL data
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                else:
                    combined_data = fbref_data
                
                # Normalize season format
                combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
                
                # Insert COMPLETE data in database
                success = db.insert_player_data(combined_data, 'domestic')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                            understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                            print(f"🔄 {reason} | {fbref_count}+{understat_count} metrics")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                            understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                            print(f"✅ {reason} | {fbref_count}+{understat_count} metrics")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print("❌ DB insert failed")
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"❌ Error: {str(e)[:30]}...")
                continue
                
    except Exception as e:
        if verbose:
            print(f"❌ Failed to load {league}: {e}")
    
    if verbose:
        print(f"\n✅ Domestic players loading complete:")
        print(f"   Total: {stats['total_players']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

def load_domestic_teams(league: str, season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load all teams from specific domestic league and season.
    FIXED: Correctly handles team names extraction.
    """
    if verbose:
        print(f"🔍 Loading teams from {league} - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get all teams from league
        teams_list_df = fbref_get_league_players(league, season)
        
        if teams_list_df.empty:
            if verbose:
                print(f"❌ No data found for {league} {season}")
            return stats
        
        # Get unique teams - FIX: Extract scalar values correctly
        unique_teams = teams_list_df['team'].unique()
        # Filter out NaN and convert to strings
        unique_teams = [str(team) for team in unique_teams if pd.notna(team)]
        stats['total_teams'] = len(unique_teams)
        
        if verbose:
            print(f"📊 Found {len(unique_teams)} teams to process")
            print("🎯 Extracting FBref + Understat data...\n")
        
        # Process each team
        for i, team_name in enumerate(unique_teams, 1):
            if verbose:
                print(f"[{i:3d}/{len(unique_teams)}] {team_name}", end=" ")
            
            try:
                # Get FBref data first
                fbref_data = fbref_get_team(team_name, league, season)
                if not fbref_data:
                    if verbose:
                        print("❌ No FBref data")
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = _should_update_domestic_team(
                    team_name, league, season, new_matches, db
                )
                
                if not should_update:
                    if verbose:
                        print(f"⏭️  {reason}")
                    stats['skipped'] += 1
                    continue
                
                # Get Understat data
                understat_data = understat_get_team(team_name, league, season)
                
                # Merge ALL data
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                else:
                    combined_data = fbref_data
                
                # Normalize season format
                combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
                
                # Insert COMPLETE data in database
                success = db.insert_team_data(combined_data, 'domestic')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                            understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                            print(f"🔄 {reason} | {fbref_count}+{understat_count} metrics")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                            understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                            print(f"✅ {reason} | {fbref_count}+{understat_count} metrics")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print("❌ DB insert failed")
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"❌ Error: {str(e)[:30]}...")
                continue
                
    except Exception as e:
        if verbose:
            print(f"❌ Failed to load {league}: {e}")
    
    if verbose:
        print(f"\n✅ Domestic teams loading complete:")
        print(f"   Total: {stats['total_teams']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats


def load_european_players(competition: str, season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load Champions League players (FBref only).
    FIXED: Correctly handles player/team names extraction.
    """
    if verbose:
        print(f"🔍 Loading European players from {competition} - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get all players from competition
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"❌ No players found for {competition} {season}")
            return stats
        
        # Get unique players with their teams
        players_data = players_list_df[['player', 'team']].drop_duplicates()
        stats['total_players'] = len(players_data)
        
        if verbose:
            print(f"📊 Found {len(players_data)} players to process")
            print("🎯 Extracting FBref data only (no Understat for European competitions)...\n")
        
        # Process each player - FIX: Extract scalar values correctly
        for i, (idx, row) in enumerate(players_data.iterrows(), 1):
            # ✅ FIX: Extract scalar values from pandas Series
            player_name = str(row['player']) if pd.notna(row['player']) else 'Unknown'
            team = str(row['team']) if pd.notna(row['team']) else 'Unknown'
            
            # Skip if invalid data
            if player_name == 'Unknown' or team == 'Unknown':
                if verbose:
                    print(f"[{i:3d}/{len(players_data)}] ❌ Invalid data: {player_name} ({team})")
                stats['failed'] += 1
                continue
            
            if verbose:
                print(f"[{i:3d}/{len(players_data)}] {player_name} ({team})", end=" ")
            
            try:
                # Get FBref data only (no Understat for European competitions)
                fbref_data = fbref_get_player(player_name, competition, season)
                if not fbref_data:
                    if verbose:
                        print("❌ No FBref data")
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = _should_update_european_player(
                    player_name, season, team, new_matches, db
                )
                
                if not should_update:
                    if verbose:
                        print(f"⏭️  {reason}")
                    stats['skipped'] += 1
                    continue
                
                # Use ONLY FBref data (change league to competition)
                combined_data = fbref_data.copy()
                combined_data['competition'] = combined_data.pop('league', competition)
                combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
                
                # Insert data in European table
                success = db.insert_player_data(combined_data, 'european')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            metrics_count = len(combined_data)
                            print(f"🔄 {reason} | {metrics_count} metrics")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            metrics_count = len(combined_data)
                            print(f"✅ {reason} | {metrics_count} metrics")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print("❌ DB insert failed")
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"❌ Error: {str(e)[:30]}...")
                continue
                
    except Exception as e:
        if verbose:
            print(f"❌ Failed to load {competition}: {e}")
    
    if verbose:
        print(f"\n✅ European players loading complete:")
        print(f"   Total: {stats['total_players']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats


def load_european_teams(competition: str, season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load Champions League teams (FBref only).
    FIXED: Correctly handles team names extraction.
    """
    if verbose:
        print(f"🔍 Loading European teams from {competition} - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get all teams from competition
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"❌ No data found for {competition} {season}")
            return stats
        
        # Get unique teams - FIX: Extract scalar values correctly
        unique_teams = players_list_df['team'].unique()
        # Filter out NaN and convert to strings
        unique_teams = [str(team) for team in unique_teams if pd.notna(team)]
        stats['total_teams'] = len(unique_teams)
        
        if verbose:
            print(f"📊 Found {len(unique_teams)} teams to process")
            print("🎯 Extracting FBref data only (no Understat for European competitions)...\n")
        
        # Process each team
        for i, team_name in enumerate(unique_teams, 1):
            if verbose:
                print(f"[{i:3d}/{len(unique_teams)}] {team_name}", end=" ")
            
            try:
                # Get FBref data only
                fbref_data = fbref_get_team(team_name, competition, season)
                if not fbref_data:
                    if verbose:
                        print("❌ No FBref data")
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = _should_update_european_team(
                    team_name, season, new_matches, db
                )
                
                if not should_update:
                    if verbose:
                        print(f"⏭️  {reason}")
                    stats['skipped'] += 1
                    continue
                
                # Use ONLY FBref data (change league to competition)
                combined_data = fbref_data.copy()
                combined_data['competition'] = combined_data.pop('league', competition)
                combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
                
                # Insert data in European table
                success = db.insert_team_data(combined_data, 'european')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            metrics_count = len(combined_data)
                            print(f"🔄 {reason} | {metrics_count} metrics")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            metrics_count = len(combined_data)
                            print(f"✅ {reason} | {metrics_count} metrics")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print("❌ DB insert failed")
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"❌ Error: {str(e)[:30]}...")
                continue
                
    except Exception as e:
        if verbose:
            print(f"❌ Failed to load {competition}: {e}")
    
    if verbose:
        print(f"\n✅ European teams loading complete:")
        print(f"   Total: {stats['total_teams']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

def load_sample_data(verbose: bool = True):
    """Load sample data for testing - FIXED VERSION."""
    if verbose:
        print("🧪 Loading sample data for testing...")
        print("=" * 60)
    
    # Load a few players from Real Madrid
    sample_players = ["Kylian Mbappé", "Vinicius Jr", "Jude Bellingham"]
    
    db = get_db_manager()
    
    for player in sample_players:
        try:
            fbref_data = fbref_get_player(player, "ESP-La Liga", "2024-25")
            understat_data = understat_get_player(player, "ESP-La Liga", "2024-25")
            
            if fbref_data:
                # Merge ALL data
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                else:
                    combined_data = fbref_data
                
                # Normalize season format
                combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
                
                # Count metrics
                fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                total_metrics = fbref_count + understat_count
                
                success = db.insert_player_data(combined_data, 'domestic')
                
                if verbose:
                    status = "✅" if success else "❌"
                    print(f"   {status} {player} | {total_metrics} metrics ({fbref_count}+{understat_count})")
            else:
                if verbose:
                    print(f"   ❌ {player} (no data)")
        except Exception as e:
            if verbose:
                print(f"   ❌ {player} (error: {e})")
    
    # Load Real Madrid team data
    try:
        fbref_data = fbref_get_team("Real Madrid", "ESP-La Liga", "2024-25")
        understat_data = understat_get_team("Real Madrid", "ESP-La Liga", "2024-25")
        
        if fbref_data:
            # Merge ALL data
            if understat_data:
                combined_data = {**fbref_data, **understat_data}
            else:
                combined_data = fbref_data
            
            # Normalize season format
            combined_data['season'] = _normalize_season_format(combined_data.get('season', ''))
            
            # Count metrics
            fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
            understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
            total_metrics = fbref_count + understat_count
            
            success = db.insert_team_data(combined_data, 'domestic')
            
            if verbose:
                status = "✅" if success else "❌"
                print(f"   {status} Real Madrid | {total_metrics} metrics ({fbref_count}+{understat_count})")
        else:
            if verbose:
                print("   ❌ Real Madrid (no data)")
    except Exception as e:
        if verbose:
            print(f"   ❌ Real Madrid (error: {e})")

# ====================================================================
# MAIN EXECUTION WITH INTERACTIVE MENU
# ====================================================================

def main():
    """Main execution function with complete menu implementation."""
    print("FootballDecoded Data Loader - FIXED VERSION")
    print("=" * 40)
    print("\n1. Load domestic players (specify league + season)")
    print("2. Load domestic teams (specify league + season)")
    print("3. Load Champions League players (specify season)")
    print("4. Load Champions League teams (specify season)")
    print("5. Load sample data (testing) - FIXED")
    print("6. Test database connection")
    print("7. Setup database schema")
    print("8. Clear all existing data")
    
    choice = input("\nSelect option (1-8): ").strip()
    
    # ================================================================
    # OPCIÓN 1: LOAD DOMESTIC PLAYERS
    # ================================================================
    if choice == "1":
        print("\n📋 Available domestic leagues:")
        for i, league in enumerate(AVAILABLE_LEAGUES, 1):
            print(f"   {i}. {league}")
        
        try:
            league_choice = int(input("\nSelect league (1-5): ").strip())
            if 1 <= league_choice <= len(AVAILABLE_LEAGUES):
                selected_league = AVAILABLE_LEAGUES[league_choice - 1]
                season = input("Enter season (e.g., 2024-25): ").strip()
                
                if season:
                    print(f"\n🔍 Loading players from {selected_league} - {season}")
                    stats = load_domestic_players(selected_league, season, verbose=True)
                else:
                    print("❌ Invalid season format")
            else:
                print("❌ Invalid league selection")
        except ValueError:
            print("❌ Invalid input")
    
    # ================================================================
    # OPCIÓN 2: LOAD DOMESTIC TEAMS
    # ================================================================
    elif choice == "2":
        print("\n📋 Available domestic leagues:")
        for i, league in enumerate(AVAILABLE_LEAGUES, 1):
            print(f"   {i}. {league}")
        
        try:
            league_choice = int(input("\nSelect league (1-5): ").strip())
            if 1 <= league_choice <= len(AVAILABLE_LEAGUES):
                selected_league = AVAILABLE_LEAGUES[league_choice - 1]
                season = input("Enter season (e.g., 2024-25): ").strip()
                
                if season:
                    print(f"\n🔍 Loading teams from {selected_league} - {season}")
                    stats = load_domestic_teams(selected_league, season, verbose=True)
                else:
                    print("❌ Invalid season format")
            else:
                print("❌ Invalid league selection")
        except ValueError:
            print("❌ Invalid input")
    
    # ================================================================
    # OPCIÓN 3: LOAD CHAMPIONS LEAGUE PLAYERS
    # ================================================================
    elif choice == "3":
        season = input("Enter Champions League season (e.g., 2024-25): ").strip()
        
        if season:
            print(f"\n🔍 Loading Champions League players - {season}")
            stats = load_european_players(CHAMPIONS_LEAGUE, season, verbose=True)
        else:
            print("❌ Invalid season format")
    
    # ================================================================
    # OPCIÓN 4: LOAD CHAMPIONS LEAGUE TEAMS
    # ================================================================
    elif choice == "4":
        season = input("Enter Champions League season (e.g., 2024-25): ").strip()
        
        if season:
            print(f"\n🔍 Loading Champions League teams - {season}")
            stats = load_european_teams(CHAMPIONS_LEAGUE, season, verbose=True)
        else:
            print("❌ Invalid season format")
    
    # ================================================================
    # OPCIÓN 5: LOAD SAMPLE DATA
    # ================================================================
    elif choice == "5":
        load_sample_data(verbose=True)
    
    # ================================================================
    # OPCIÓN 6: TEST DATABASE CONNECTION
    # ================================================================
    elif choice == "6":
        print("\n🔍 Testing database connection...")
        try:
            from database.connection import test_connection
            success = test_connection()
            if success:
                print("✅ Database connection successful!")
            else:
                print("❌ Database connection failed!")
        except Exception as e:
            print(f"❌ Connection test error: {e}")
    
    # ================================================================
    # OPCIÓN 7: SETUP DATABASE SCHEMA
    # ================================================================
    elif choice == "7":
        confirm = input("⚠️  Setup database schema? This will create/recreate tables (y/N): ").strip().lower()
        if confirm == 'y':
            print("\n🔧 Setting up database schema...")
            try:
                from database.connection import setup_database
                success = setup_database()
                if success:
                    print("✅ Database schema setup complete!")
                else:
                    print("❌ Database schema setup failed!")
            except Exception as e:
                print(f"❌ Schema setup error: {e}")
        else:
            print("❌ Schema setup cancelled")
    
    # ================================================================
    # OPCIÓN 8: CLEAR ALL DATA
    # ================================================================
    elif choice == "8":
        confirm = input("⚠️  Clear ALL data? (type 'YES' to confirm): ").strip()
        if confirm == "YES":
            try:
                db = get_db_manager()
                
                # Clear all tables
                with db.engine.connect() as conn:
                    conn.execute("DELETE FROM footballdecoded.players_domestic")
                    conn.execute("DELETE FROM footballdecoded.teams_domestic")
                    conn.execute("DELETE FROM footballdecoded.players_european")
                    conn.execute("DELETE FROM footballdecoded.teams_european")
                    conn.commit()
                
                print("✅ All data cleared successfully")
                db.close()
            except Exception as e:
                print(f"❌ Failed to clear data: {e}")
        else:
            print("❌ Clear operation cancelled")
    
    # ================================================================
    # INVALID OPTION
    # ================================================================
    else:
        print("❌ Invalid option. Please select 1-8.")
        
if __name__ == "__main__":
    main()