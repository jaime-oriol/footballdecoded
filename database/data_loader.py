# ====================================================================
# FootballDecoded Data Loading Pipeline
# ====================================================================
# Simplified and specific data loading with smart update logic
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
# SMART UPDATE CHECKING FUNCTIONS
# ====================================================================

def _should_update_domestic_player(player_name: str, league: str, season: str, team: str, 
                                 new_matches_played: int, db: DatabaseManager) -> tuple[bool, str]:
    """
    Check if domestic player should be updated based on matches played.
    
    Returns:
        (should_update: bool, reason: str)
    """
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
    Updates only if player has more matches played than stored data.
    
    Args:
        league: League identifier (e.g., 'FRA-Ligue 1')
        season: Season identifier (e.g., '2024-25')
        verbose: Show progress
        
    Returns:
        Dict with load statistics
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
        
        # Process each player
        for i, (_, row) in enumerate(players_data.iterrows(), 1):
            player_name = row['player']
            team = row['team']
            
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
                
                # Merge data
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                    combined_data['understat_official_name'] = understat_data.get('official_player_name')
                else:
                    combined_data = fbref_data
                    combined_data['understat_official_name'] = None
                
                combined_data['fbref_official_name'] = combined_data.get('player_name')
                
                # Insert/Update in database
                success = db.insert_player_data(combined_data, 'domestic')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(f"🔄 {reason}")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(f"✅ {reason}")
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
    Updates only if team has more matches played than stored data.
    """
    if verbose:
        print(f"🏟️ Loading teams from {league} - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get teams from schedule
        schedule_df = fbref_get_schedule(league, season)
        
        if schedule_df.empty:
            if verbose:
                print(f"❌ No schedule found for {league} {season}")
            return stats
        
        # Extract unique teams
        teams_list = []
        schedule_reset = schedule_df.reset_index()
        if 'home_team' in schedule_reset.columns:
            teams_list.extend(schedule_reset['home_team'].unique().tolist())
        if 'away_team' in schedule_reset.columns:
            teams_list.extend(schedule_reset['away_team'].unique().tolist())
        
        teams_list = list(set([t for t in teams_list if pd.notna(t)]))
        stats['total_teams'] = len(teams_list)
        
        if verbose:
            print(f"📊 Found {len(teams_list)} teams to process")
            print("🎯 Extracting FBref + Understat data...\n")
        
        # Process each team
        for i, team_name in enumerate(teams_list, 1):
            if verbose:
                print(f"[{i:2d}/{len(teams_list)}] {team_name}", end=" ")
            
            try:
                # Get FBref data first to check matches played
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
                
                # Merge data
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                    combined_data['understat_official_name'] = understat_data.get('official_team_name')
                else:
                    combined_data = fbref_data
                    combined_data['understat_official_name'] = None
                
                combined_data['fbref_official_name'] = combined_data.get('official_team_name')
                
                # Insert/Update in database
                success = db.insert_team_data(combined_data, 'domestic')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(f"🔄 {reason}")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(f"✅ {reason}")
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

# ====================================================================
# CHAMPIONS LEAGUE DATA LOADING FUNCTIONS
# ====================================================================

def load_champions_players(season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load all players from Champions League for specific season.
    Updates only if player has more matches played than stored data.
    """
    if verbose:
        print(f"🏆 Loading Champions League players - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get all players from Champions League
        players_list_df = fbref_get_league_players(CHAMPIONS_LEAGUE, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"❌ No players found for Champions League {season}")
            return stats
        
        # Get unique players with their teams
        players_data = players_list_df[['player', 'team']].drop_duplicates()
        stats['total_players'] = len(players_data)
        
        if verbose:
            print(f"📊 Found {len(players_data)} players to process")
            print("🎯 Extracting FBref data...\n")
        
        # Process each player
        for i, (_, row) in enumerate(players_data.iterrows(), 1):
            player_name = row['player']
            team = row['team']
            
            if verbose:
                print(f"[{i:3d}/{len(players_data)}] {player_name} ({team})", end=" ")
            
            try:
                # Get FBref data
                fbref_data = fbref_get_player(player_name, CHAMPIONS_LEAGUE, season)
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
                
                # Adjust for European table structure
                fbref_data['competition'] = fbref_data.pop('league')
                fbref_data['fbref_official_name'] = fbref_data.get('player_name')
                
                # Insert/Update in database
                success = db.insert_player_data(fbref_data, 'european')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(f"🔄 {reason}")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(f"✅ {reason}")
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
            print(f"❌ Failed to load Champions League: {e}")
    
    if verbose:
        print(f"\n✅ Champions League players loading complete:")
        print(f"   Total: {stats['total_players']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

def load_champions_teams(season: str, verbose: bool = True) -> Dict[str, int]:
    """
    Load all teams from Champions League for specific season.
    Updates only if team has more matches played than stored data.
    """
    if verbose:
        print(f"🏆 Loading Champions League teams - {season}")
        print("=" * 60)
    
    db = get_db_manager()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        # Get teams from schedule
        schedule_df = fbref_get_schedule(CHAMPIONS_LEAGUE, season)
        
        if schedule_df.empty:
            if verbose:
                print(f"❌ No schedule found for Champions League {season}")
            return stats
        
        # Extract unique teams
        teams_list = []
        schedule_reset = schedule_df.reset_index()
        if 'home_team' in schedule_reset.columns:
            teams_list.extend(schedule_reset['home_team'].unique().tolist())
        if 'away_team' in schedule_reset.columns:
            teams_list.extend(schedule_reset['away_team'].unique().tolist())
        
        teams_list = list(set([t for t in teams_list if pd.notna(t)]))
        stats['total_teams'] = len(teams_list)
        
        if verbose:
            print(f"📊 Found {len(teams_list)} teams to process")
            print("🎯 Extracting FBref data...\n")
        
        # Process each team
        for i, team_name in enumerate(teams_list, 1):
            if verbose:
                print(f"[{i:2d}/{len(teams_list)}] {team_name}", end=" ")
            
            try:
                # Get FBref data
                fbref_data = fbref_get_team(team_name, CHAMPIONS_LEAGUE, season)
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
                
                # Adjust for European table structure
                fbref_data['competition'] = fbref_data.pop('league')
                fbref_data['fbref_official_name'] = fbref_data.get('official_team_name')
                
                # Insert/Update in database
                success = db.insert_team_data(fbref_data, 'european')
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(f"🔄 {reason}")
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(f"✅ {reason}")
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
            print(f"❌ Failed to load Champions League: {e}")
    
    if verbose:
        print(f"\n✅ Champions League teams loading complete:")
        print(f"   Total: {stats['total_teams']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

# ====================================================================
# TESTING AND UTILITY FUNCTIONS
# ====================================================================

def load_sample_data(verbose: bool = True):
    """Load sample data for testing."""
    if verbose:
        print("🧪 Loading sample data for testing...")
        print("=" * 60)
    
    # Load a few players from Real Madrid
    sample_players = ["Kylian Mbappé", "Vinicius Jr", "Jude Bellingham"]
    
    for player in sample_players:
        try:
            fbref_data = fbref_get_player(player, "ESP-La Liga", "2024-25")
            understat_data = understat_get_player(player, "ESP-La Liga", "2024-25")
            
            if fbref_data:
                if understat_data:
                    combined_data = {**fbref_data, **understat_data}
                    combined_data['understat_official_name'] = understat_data.get('official_player_name')
                else:
                    combined_data = fbref_data
                    combined_data['understat_official_name'] = None
                
                combined_data['fbref_official_name'] = combined_data.get('player_name')
                
                db = get_db_manager()
                success = db.insert_player_data(combined_data, 'domestic')
                
                if verbose:
                    status = "✅" if success else "❌"
                    print(f"   {status} {player}")
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
            if understat_data:
                combined_data = {**fbref_data, **understat_data}
                combined_data['understat_official_name'] = understat_data.get('official_team_name')
            else:
                combined_data = fbref_data
                combined_data['understat_official_name'] = None
            
            combined_data['fbref_official_name'] = combined_data.get('official_team_name')
            
            db = get_db_manager()
            success = db.insert_team_data(combined_data, 'domestic')
            
            if verbose:
                status = "✅" if success else "❌"
                print(f"   {status} Real Madrid")
        else:
            if verbose:
                print("   ❌ Real Madrid (no data)")
    except Exception as e:
        if verbose:
            print(f"   ❌ Real Madrid (error: {e})")

def test_connection():
    """Test database connection."""
    try:
        from database.connection import test_connection as db_test
        return db_test()
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def setup_database():
    """Setup database schema."""
    try:
        from database.connection import setup_database as db_setup
        return db_setup()
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

# ====================================================================
# MAIN EXECUTION WITH INTERACTIVE MENU
# ====================================================================

def main():
    """Main execution function with simplified menu."""
    print("FootballDecoded Data Loader")
    print("=" * 30)
    print("\n1. Load domestic players (specify league + season)")
    print("2. Load domestic teams (specify league + season)")
    print("3. Load Champions League players (specify season)")
    print("4. Load Champions League teams (specify season)")
    print("5. Load sample data (testing)")
    print("6. Test database connection")
    print("7. Setup database schema")
    
    choice = input("\nSelect option (1-7): ").strip()
    
    if choice == "1":
        print("\nAvailable leagues:")
        for i, league in enumerate(AVAILABLE_LEAGUES, 1):
            print(f"  {i}. {league}")
        
        league_choice = input("Select league number: ").strip()
        season = input("Enter season (e.g., 2024-25): ").strip()
        
        try:
            league_idx = int(league_choice) - 1
            if 0 <= league_idx < len(AVAILABLE_LEAGUES):
                league = AVAILABLE_LEAGUES[league_idx]
                load_domestic_players(league, season, verbose=True)
            else:
                print("❌ Invalid league number")
        except ValueError:
            print("❌ Please enter a valid number")
            
    elif choice == "2":
        print("\nAvailable leagues:")
        for i, league in enumerate(AVAILABLE_LEAGUES, 1):
            print(f"  {i}. {league}")
        
        league_choice = input("Select league number: ").strip()
        season = input("Enter season (e.g., 2024-25): ").strip()
        
        try:
            league_idx = int(league_choice) - 1
            if 0 <= league_idx < len(AVAILABLE_LEAGUES):
                league = AVAILABLE_LEAGUES[league_idx]
                load_domestic_teams(league, season, verbose=True)
            else:
                print("❌ Invalid league number")
        except ValueError:
            print("❌ Please enter a valid number")
            
    elif choice == "3":
        season = input("Enter season (e.g., 2024-25): ").strip()
        load_champions_players(season, verbose=True)
        
    elif choice == "4":
        season = input("Enter season (e.g., 2024-25): ").strip()
        load_champions_teams(season, verbose=True)
        
    elif choice == "5":
        load_sample_data(verbose=True)
        
    elif choice == "6":
        test_connection()
        
    elif choice == "7":
        if setup_database():
            print("✅ Database schema setup complete")
        else:
            print("❌ Database schema setup failed")
            
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()