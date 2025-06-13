# ====================================================================
# FootballDecoded Data Loading Pipeline
# ====================================================================

import sys
import os
import pandas as pd
import json
from typing import Dict, Optional, Tuple
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

AVAILABLE_COMPETITIONS = [
    ('ENG-Premier League', 'domestic'),
    ('ESP-La Liga', 'domestic'),
    ('ITA-Serie A', 'domestic'), 
    ('GER-Bundesliga', 'domestic'),
    ('FRA-Ligue 1', 'domestic'),
    ('INT-Champions League', 'european')
]

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def normalize_season_format(season: str) -> str:
    """Normalize season to YYYY-YY format consistently."""
    if not season:
        return season
    
    if len(season) == 4 and season.isdigit():
        year = int(season[:2]) + 2000
        return f"{year}-{season[2:]}"
    elif len(season) == 7 and '-' in season:
        return season
    elif len(season) == 4 and season.startswith('20'):
        year = int(season)
        next_year = str(year + 1)[-2:]
        return f"{year}-{next_year}"
    
    return season

def format_status_log(index: int, total: int, name: str, team: str, competition: str, 
                     status: str, metrics_count: int = 0) -> str:
    """Format consistent status log for processing."""
    status_symbols = {
        'new': 'NEW',
        'update': 'UPDATE', 
        'skip': 'SKIP',
        'failed': 'FAILED'
    }
    
    # First line: index and name
    first_line = f"[{index:3d}/{total}] {name}"
    
    # Second line: different format for teams vs players
    if team == "League":  # This is a team entry
        if status in ['new', 'update']:
            second_line = f"          {competition} - {status_symbols[status]} ({metrics_count} metrics)"
        elif status.startswith('skip'):
            second_line = f"          {competition} - {status_symbols['skip']} ({status.replace('skip', '').strip()})"
        else:
            second_line = f"          {competition} - {status_symbols.get('failed', 'FAILED')} ({status})"
    else:  # This is a player entry
        if status in ['new', 'update']:
            second_line = f"          {team}, {competition} - {status_symbols[status]} ({metrics_count} metrics)"
        elif status.startswith('skip'):
            second_line = f"          {team}, {competition} - {status_symbols['skip']} ({status.replace('skip', '').strip()})"
        else:
            second_line = f"          {team}, {competition} - {status_symbols.get('failed', 'FAILED')} ({status})"
    
    return f"{first_line}\n{second_line}"

def should_update_player(player_name: str, competition: str, season: str, team: str, 
                        new_matches: int, db: DatabaseManager, table_type: str) -> Tuple[bool, str]:
    """Check if player should be updated based on matches played."""
    try:
        if table_type == 'domestic':
            query = """
            SELECT fbref_metrics->>'matches_played' as current_matches 
            FROM footballdecoded.players_domestic 
            WHERE player_name = %(player_name)s AND league = %(competition)s 
            AND season = %(season)s AND team = %(team)s
            """
        else:
            query = """
            SELECT fbref_metrics->>'matches_played' as current_matches 
            FROM footballdecoded.players_european 
            WHERE player_name = %(player_name)s AND competition = %(competition)s 
            AND season = %(season)s AND team = %(team)s
            """
        
        result = pd.read_sql(query, db.engine, params={
            'player_name': player_name,
            'competition': competition,
            'season': season,
            'team': team
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip - No changes ({current_matches} matches)"
            
    except Exception as e:
        return True, f"error - {str(e)[:30]}"

def should_update_team(team_name: str, competition: str, season: str, 
                      new_matches: int, db: DatabaseManager, table_type: str) -> Tuple[bool, str]:
    """Check if team should be updated based on matches played."""
    try:
        if table_type == 'domestic':
            query = """
            SELECT fbref_metrics->>'matches_played' as current_matches 
            FROM footballdecoded.teams_domestic 
            WHERE team_name = %(team_name)s AND league = %(competition)s AND season = %(season)s
            """
        else:
            query = """
            SELECT fbref_metrics->>'matches_played' as current_matches 
            FROM footballdecoded.teams_european 
            WHERE team_name = %(team_name)s AND competition = %(competition)s AND season = %(season)s
            """
        
        result = pd.read_sql(query, db.engine, params={
            'team_name': team_name,
            'competition': competition,
            'season': season
        })
        
        if result.empty:
            return True, "new"
        
        current_matches = result.iloc[0]['current_matches']
        current_matches = int(current_matches) if current_matches and current_matches != 'None' else 0
        new_matches = new_matches or 0
        
        if new_matches > current_matches:
            return True, f"update ({current_matches}→{new_matches} matches)"
        else:
            return False, f"skip - No changes ({current_matches} matches)"
            
    except Exception as e:
        return True, f"error - {str(e)[:30]}"

# ====================================================================
# CORE LOADING FUNCTIONS
# ====================================================================

def load_players(competition: str, season: str, table_type: str, verbose: bool = True) -> Dict[str, int]:
    """Load all players from specific competition and season."""
    if verbose:
        print(f"Loading players from {competition} - {season}")
        print("=" * 70)
    
    db = get_db_manager()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"No players found for {competition} {season}")
            return stats
        
        players_data = players_list_df[['player', 'team']].drop_duplicates()
        stats['total_players'] = len(players_data)
        
        if verbose:
            print(f"Found {len(players_data)} players to process")
            print("Extracting data...\n")
        
        for i, (idx, row) in enumerate(players_data.iterrows(), 1):
            # Initialize variables before try block
            player_name = 'Unknown'
            team = 'Unknown'
            
            try:
                # Safe extraction of player and team names - handle pandas Series properly
                player_value = row['player']
                team_value = row['team']
                
                # Convert to scalar if Series, then to string
                if isinstance(player_value, pd.Series):
                    player_value = player_value.iloc[0] if len(player_value) > 0 else None
                if isinstance(team_value, pd.Series):
                    team_value = team_value.iloc[0] if len(team_value) > 0 else None
                
                player_name = str(player_value) if pd.notna(player_value) else 'Unknown'
                team = str(team_value) if pd.notna(team_value) else 'Unknown'
                
                if player_name in ['Unknown', 'nan', ''] or team in ['Unknown', 'nan', '']:
                    if verbose:
                        print(format_status_log(i, len(players_data), player_name, team, competition, "failed - Invalid data"))
                    stats['failed'] += 1
                    continue
                
                # Get FBref data
                fbref_data = fbref_get_player(player_name, competition, season)
                
                if not fbref_data:
                    if verbose:
                        print(format_status_log(i, len(players_data), player_name, team, competition, "failed - No FBref data"))
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = should_update_player(
                    player_name, competition, season, team, new_matches, db, table_type
                )
                
                if not should_update:
                    if verbose:
                        print(format_status_log(i, len(players_data), player_name, team, competition, reason))
                    stats['skipped'] += 1
                    continue
                
                # Get Understat data for domestic competitions only
                combined_data = fbref_data.copy()
                if table_type == 'domestic':
                    understat_data = understat_get_player(player_name, competition, season)
                    if understat_data:
                        combined_data.update(understat_data)
                
                # Adjust data format for table type
                if table_type == 'european':
                    combined_data['competition'] = combined_data.pop('league', competition)
                
                combined_data['season'] = normalize_season_format(combined_data.get('season', ''))
                
                # Count metrics
                fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                total_metrics = fbref_count + understat_count
                
                success = db.insert_player_data(combined_data, table_type)
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(format_status_log(i, len(players_data), player_name, team, competition, 'update', total_metrics))
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(format_status_log(i, len(players_data), player_name, team, competition, 'new', total_metrics))
                else:
                    stats['failed'] += 1
                    if verbose:
                        print(format_status_log(i, len(players_data), player_name, team, competition, "failed - DB insert error"))
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(format_status_log(i, len(players_data), player_name, team, competition, f"failed - {str(e)[:30]}..."))
                continue
                
    except Exception as e:
        if verbose:
            print(f"Failed to load {competition}: {e}")
    
    if verbose:
        print(f"\nPlayers loading complete:")
        print(f"   Total: {stats['total_players']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

def load_teams(competition: str, season: str, table_type: str, verbose: bool = True) -> Dict[str, int]:
    """Load all teams from specific competition and season."""
    if verbose:
        print(f"Loading teams from {competition} - {season}")
        print("=" * 70)
    
    db = get_db_manager()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'updated': 0}
    
    try:
        teams_list_df = fbref_get_league_players(competition, season)
        
        if teams_list_df.empty:
            if verbose:
                print(f"No data found for {competition} {season}")
            return stats
        
        # Get unique teams safely
        unique_teams = []
        for team in teams_list_df['team'].unique():
            if pd.notna(team) and str(team) not in ['nan', 'NaN', '', 'None']:
                unique_teams.append(str(team))
        
        stats['total_teams'] = len(unique_teams)
        
        if verbose:
            print(f"Found {len(unique_teams)} teams to process")
            print("Extracting data...\n")
        
        for i, team_name in enumerate(unique_teams, 1):
            try:
                # Get FBref data
                fbref_data = fbref_get_team(team_name, competition, season)
                
                if not fbref_data:
                    if verbose:
                        print(format_status_log(i, len(unique_teams), team_name, "League", competition, "failed - No FBref data"))
                    stats['failed'] += 1
                    continue
                
                new_matches = fbref_data.get('matches_played', 0)
                should_update, reason = should_update_team(
                    team_name, competition, season, new_matches, db, table_type
                )
                
                if not should_update:
                    if verbose:
                        print(format_status_log(i, len(unique_teams), team_name, "League", competition, reason))
                    stats['skipped'] += 1
                    continue
                
                # Get Understat data for domestic competitions only
                combined_data = fbref_data.copy()
                if table_type == 'domestic':
                    understat_data = understat_get_team(team_name, competition, season)
                    if understat_data:
                        combined_data.update(understat_data)
                
                # Adjust data format for table type
                if table_type == 'european':
                    combined_data['competition'] = combined_data.pop('league', competition)
                
                combined_data['season'] = normalize_season_format(combined_data.get('season', ''))
                
                # Count metrics
                fbref_count = len([k for k in combined_data.keys() if not k.startswith('understat_')])
                understat_count = len([k for k in combined_data.keys() if k.startswith('understat_')])
                total_metrics = fbref_count + understat_count
                
                success = db.insert_team_data(combined_data, table_type)
                
                if success:
                    if reason.startswith('update'):
                        stats['updated'] += 1
                        if verbose:
                            print(format_status_log(i, len(unique_teams), team_name, "League", competition, 'update', total_metrics))
                    else:
                        stats['successful'] += 1
                        if verbose:
                            print(format_status_log(i, len(unique_teams), team_name, "League", competition, 'new', total_metrics))
                else:
                    stats['failed'] += 1
                    if verbose:
                        print(format_status_log(i, len(unique_teams), team_name, "League", competition, "failed - DB insert error"))
                        
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(format_status_log(i, len(unique_teams), team_name, "League", competition, f"failed - {str(e)[:30]}..."))
                continue
                
    except Exception as e:
        if verbose:
            print(f"Failed to load {competition}: {e}")
    
    if verbose:
        print(f"\nTeams loading complete:")
        print(f"   Total: {stats['total_teams']}")
        print(f"   New: {stats['successful']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")
        
    return stats

def load_complete_competition(competition: str, season: str, verbose: bool = True) -> Dict[str, Dict[str, int]]:
    """Load both players and teams from a competition in one go."""
    table_type = 'domestic' if competition != 'INT-Champions League' else 'european'
    
    if verbose:
        data_source = "FBref + Understat" if table_type == 'domestic' else "FBref only"
        print(f"Loading complete data from {competition} - {season} ({data_source})")
        print("=" * 80)
    
    results = {}
    
    # Load players first
    if verbose:
        print("PHASE 1: Loading Players")
        print("-" * 40)
    
    player_stats = load_players(competition, season, table_type, verbose)
    results['players'] = player_stats
    
    if verbose:
        print("\nPHASE 2: Loading Teams")
        print("-" * 40)
    
    team_stats = load_teams(competition, season, table_type, verbose)
    results['teams'] = team_stats
    
    if verbose:
        print(f"\nCOMPLETE LOADING SUMMARY for {competition} {season}")
        print("=" * 60)
        print(f"Players - Total: {player_stats['total_players']} | New: {player_stats['successful']} | Updated: {player_stats['updated']} | Failed: {player_stats['failed']}")
        print(f"Teams   - Total: {team_stats['total_teams']} | New: {team_stats['successful']} | Updated: {team_stats['updated']} | Failed: {team_stats['failed']}")
        
        total_entities = player_stats['total_players'] + team_stats['total_teams']
        total_successful = player_stats['successful'] + team_stats['successful'] + player_stats['updated'] + team_stats['updated']
        success_rate = (total_successful / total_entities * 100) if total_entities > 0 else 0
        print(f"Overall success rate: {success_rate:.1f}%")
    
    return results

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    """Main execution function with unified menu."""
    print("FootballDecoded Data Loader")
    print("=" * 40)
    print("\n1. Load competition data (players + teams)")
    print("2. Test database connection")
    print("3. Setup database schema")
    print("4. Clear all existing data")
    print("5. Check database status")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        print("\nAvailable competitions:")
        for i, (comp_name, comp_type) in enumerate(AVAILABLE_COMPETITIONS, 1):
            data_source = "FBref + Understat" if comp_type == 'domestic' else "FBref only"
            print(f"   {i}. {comp_name} ({data_source})")
        
        try:
            comp_choice = int(input(f"\nSelect competition (1-{len(AVAILABLE_COMPETITIONS)}): ").strip())
            if 1 <= comp_choice <= len(AVAILABLE_COMPETITIONS):
                selected_competition, _ = AVAILABLE_COMPETITIONS[comp_choice - 1]
                season = input("Enter season (e.g., 2024-25): ").strip()
                
                if season:
                    results = load_complete_competition(selected_competition, season, verbose=True)
                else:
                    print("Invalid season format")
            else:
                print("Invalid competition selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "2":
        print("\nTesting database connection...")
        try:
            from database.connection import test_connection
            success = test_connection()
            if success:
                print("Database connection successful!")
            else:
                print("Database connection failed!")
        except Exception as e:
            print(f"Connection test error: {e}")
    
    elif choice == "3":
        confirm = input("Setup database schema? This will create/recreate tables (y/N): ").strip().lower()
        if confirm == 'y':
            print("\nSetting up database schema...")
            try:
                from database.connection import setup_database
                success = setup_database()
                if success:
                    print("Database schema setup complete!")
                else:
                    print("Database schema setup failed!")
            except Exception as e:
                print(f"Schema setup error: {e}")
        else:
            print("Schema setup cancelled")
    
    elif choice == "4":
        confirm = input("Clear ALL data? (type 'YES' to confirm): ").strip()
        if confirm == "YES":
            try:
                db = get_db_manager()
                
                with db.engine.connect() as conn:
                    conn.execute("DELETE FROM footballdecoded.players_domestic")
                    conn.execute("DELETE FROM footballdecoded.teams_domestic")
                    conn.execute("DELETE FROM footballdecoded.players_european")
                    conn.execute("DELETE FROM footballdecoded.teams_european")
                    conn.commit()
                
                print("All data cleared successfully")
                db.close()
            except Exception as e:
                print(f"Failed to clear data: {e}")
        else:
            print("Clear operation cancelled")
    
    elif choice == "5":
        print("\nChecking database status...")
        try:
            from database.database_checker import check_database_status
            check_database_status(verbose=True)
        except ImportError:
            print("database_checker.py not found")
        except Exception as e:
            print(f"Error checking database: {e}")
    
    else:
        print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main()