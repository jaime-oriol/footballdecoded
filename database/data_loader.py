# ====================================================================
# FootballDecoded Data Loader - FIXED Understat prefixes
# ====================================================================

import sys
import os
import pandas as pd
import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_league_players,
                     understat_get_player, understat_get_team)
from database.connection import DatabaseManager, get_db_manager
from sqlalchemy import text

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

# Validation ranges
METRIC_RANGES = {
    # Basic info - ultra safe ranges
    'age': (15, 50),                    # Covers youngest debuts to oldest goalkeepers
    'birth_year': (1950, 2020),         # 50 years old to 15 years old players
    
    # Playing time - realistic maximums
    'minutes_played': (0, 6000),        # ~66 full games (covers all competitions)
    'matches_played': (0, 80),          # Domestic + cups + international competitions
    'matches_started': (0, 80),
    
    # Scoring - based on historical records
    'goals': (0, 120),                  # Covers Messi's 91-goal record + margin
    'assists': (0, 60),                 # Covers highest assist records + margin
    'goals_plus_assists': (0, 150),
    
    # Shooting - realistic volumes
    'shots': (0, 600),                  # Covers highest shooters like Ronaldo/Messi
    'shots_on_target': (0, 300),
    'shots_on_target_pct': (0, 100),
    
    # Expected metrics - reasonable bounds
    'expected_goals': (0, 80),
    'expected_assists': (0, 40),
    'non_penalty_expected_goals': (0, 70),
    
    # Passing - realistic ranges
    'passes_completed': (0, 4000),      # High-volume passers like Busquets
    'passes_attempted': (0, 4500),
    'pass_completion_pct': (30, 100),   # Minimum 30% to avoid invalid data
    'key_passes': (0, 200),
    
    # Defensive actions - active defenders
    'tackles': (0, 300),                # Very active defensive midfielders
    'interceptions': (0, 250),
    'clearances': (0, 400),             # Center-backs in defensive teams
    
    # Possession - typical ranges
    'touches': (0, 5000),               # High-involvement players
    'carries': (0, 3000),
    
    # Disciplinary - realistic but safe
    'yellow_cards': (0, 25),            # Very aggressive players maximum
    'red_cards': (0, 6),                # Extreme cases but possible
    
    # Percentages - must be valid percentages
    'take_on_success_pct': (0, 100),
    'aerial_duels_won_pct': (0, 100),
}

# ====================================================================
# DATA PROCESSING CLASSES
# ====================================================================

class DataNormalizer:
    """Clean and normalize football data."""
    
    def normalize_name(self, name: str) -> str:
        """Normalize player/team names for consistent matching."""
        if not name or pd.isna(name):
            return ""
        
        name_str = str(name)
        if '\n' in name_str and 'dtype: object' in name_str:
            lines = name_str.split('\n')
            for line in lines:
                if 'Name:' not in line and 'dtype:' not in line and line.strip():
                    name_str = line.strip()
                    break
        
        name_str = name_str.lower().strip()
        name_str = unicodedata.normalize('NFD', name_str)
        name_str = ''.join(c for c in name_str if unicodedata.category(c) != 'Mn')
        name_str = re.sub(r'[^\w\s\-\.]', '', name_str)
        name_str = re.sub(r'\s+', ' ', name_str).strip()
        name_str = re.sub(r'\bjr\.?\b', 'jr', name_str)
        name_str = re.sub(r'\bsr\.?\b', 'sr', name_str)
        
        return name_str.title()
    
    def clean_value(self, value: Any, field_name: str) -> Any:
        """Clean individual field values."""
        if pd.isna(value) or value is None:
            return None
        
        str_value = str(value)
        if '\n' in str_value and 'dtype: object' in str_value:
            lines = str_value.split('\n')
            for line in lines:
                if 'Name:' not in line and 'dtype:' not in line and line.strip():
                    str_value = line.strip()
                    break
        
        if isinstance(value, list):
            if field_name in ['teams_played', 'player_name', 'team_name']:
                return ', '.join(str(item) for item in value)
        
        if str_value.lower() in ['nan', 'none', 'null', '']:
            return None
        
        return str_value.strip()


class DataValidator:
    """Validate football data integrity."""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
    
    def validate_record(self, record: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], float, List[str]]:
        """Validate and clean a data record."""
        cleaned_record = {}
        quality_score = 1.0
        warnings = []
        
        for field, value in record.items():
            cleaned_value = self.normalizer.clean_value(value, field)
            
            if field in METRIC_RANGES and cleaned_value is not None:
                try:
                    numeric_value = float(cleaned_value)
                    min_val, max_val = METRIC_RANGES[field]
                    
                    if numeric_value < min_val or numeric_value > max_val:
                        warnings.append(f"{field} out of range: {numeric_value}")
                        quality_score -= 0.1
                    else:
                        if field in ['age', 'birth_year', 'matches_played', 'goals', 'assists']:
                            cleaned_record[field] = int(numeric_value)
                        else:
                            cleaned_record[field] = numeric_value
                except ValueError:
                    warnings.append(f"Invalid numeric value for {field}: {cleaned_value}")
                    quality_score -= 0.1
            else:
                cleaned_record[field] = cleaned_value
        
        required_fields = ['player_name', 'league', 'season', 'team'] if entity_type == 'player' else ['team_name', 'league', 'season']
        for field in required_fields:
            if field not in cleaned_record or not cleaned_record[field]:
                warnings.append(f"Missing required field: {field}")
                quality_score -= 0.3
        
        if entity_type == 'player' and 'player_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['player_name'])
        elif entity_type == 'team' and 'team_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['team_name'])
        
        return cleaned_record, max(0.0, quality_score), warnings


class DuplicateHandler:
    """Handle duplicates and transfers intelligently."""
    
    def create_entity_key(self, record: Dict[str, Any], entity_type: str) -> str:
        """Create unique key for entity identification."""
        if entity_type == 'player':
            name = record.get('normalized_name', '')
            age = record.get('age', '')
            nationality = record.get('nationality', '')
            position = record.get('position', '')
            return f"{name}_{age}_{nationality}_{position}".lower()
        else:
            name = record.get('normalized_name', '')
            league = record.get('league', '')
            return f"{name}_{league}".lower()
    
    def detect_duplicates(self, records: List[Dict[str, Any]], entity_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group records by entity key to detect duplicates and transfers."""
        groups = defaultdict(list)
        
        for record in records:
            key = self.create_entity_key(record, entity_type)
            groups[key].append(record)
        
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def merge_transfer_records(self, records: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """Merge records from same entity (transfers)."""
        if not records:
            return {}
        
        merged = records[0].copy()
        
        numeric_fields = ['minutes_played', 'matches_played', 'goals', 'assists', 'shots', 'tackles', 'interceptions']
        
        for field in numeric_fields:
            total = 0
            for record in records:
                if field in record and record[field] is not None:
                    try:
                        total += float(record[field])
                    except (ValueError, TypeError):
                        continue
            merged[field] = total
        
        if entity_type == 'player':
            teams = [r.get('team') for r in records if r.get('team')]
            if len(set(teams)) > 1:
                merged['teams_played'] = ' -> '.join(teams)
                merged['is_transfer'] = True
                merged['transfer_count'] = len(set(teams))
                merged['team'] = teams[-1]
        
        return merged

# ====================================================================
# MAIN LOADING FUNCTIONS
# ====================================================================

def load_players(competition: str, season: str, table_type: str, verbose: bool = True) -> Dict[str, int]:
    """Load all players from specific competition and season."""
    if verbose:
        print(f"Loading players from {competition} - {season}")
        print("=" * 70)
    
    db = get_db_manager()
    
    # ADDED: Clear existing data for this competition/season before loading
    if verbose:
        print("Clearing existing player data for this season...")
    
    success = db.clear_season_data(competition, season, table_type, 'players')
    if not success and verbose:
        print("Warning: Could not clear existing data, may cause duplicates")
    
    validator = DataValidator()
    duplicate_handler = DuplicateHandler()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0, 'transfers': 0}
    
    try:
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"No players found for {competition} {season}")
            return stats
        
        # Rest of the function remains exactly the same...
        unique_players = players_list_df['player'].dropna().unique().tolist()
        stats['total_players'] = len(unique_players)
        
        if verbose:
            print(f"Found {len(unique_players)} players to process")
            print("Extracting data...\n")
        
        all_player_data = []
        for i, player_name in enumerate(unique_players, 1):
            team = 'Unknown'
            try:
                fbref_data = fbref_get_player(player_name, competition, season)
                if not fbref_data:
                    if verbose:
                        print(f"[{i:3d}/{len(unique_players)}] {player_name}")
                        print(f"          {competition} - FAILED (No FBref data)")
                    stats['failed'] += 1
                    continue
                
                team = fbref_data.get('team', 'Unknown')
                
                # FIXED: Avoid double Understat prefix
                if table_type == 'domestic':
                    understat_data = understat_get_player(player_name, competition, season)
                    if understat_data:
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'player')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                all_player_data.append(cleaned_data)
                
                if verbose:
                    metrics_count = len(cleaned_data)
                    print(f"[{i:3d}/{len(unique_players)}] {player_name}")
                    print(f"          {team}, {competition} - SUCCESS ({metrics_count} metrics)")
                
            except Exception as e:
                if verbose:
                    print(f"[{i:3d}/{len(unique_players)}] {player_name}")
                    print(f"          {team}, {competition} - FAILED ({str(e)[:30]}...)")
                stats['failed'] += 1
                continue
        
        duplicates = duplicate_handler.detect_duplicates(all_player_data, 'player')
        final_player_data = []
        processed_keys = set()
        
        for player_data in all_player_data:
            key = duplicate_handler.create_entity_key(player_data, 'player')
            
            if key in duplicates and key not in processed_keys:
                merged_data = duplicate_handler.merge_transfer_records(duplicates[key], 'player')
                if merged_data.get('is_transfer'):
                    stats['transfers'] += 1
                final_player_data.append(merged_data)
                processed_keys.add(key)
            elif key not in duplicates:
                final_player_data.append(player_data)
        
        for player_data in final_player_data:
            try:
                success = db.insert_player_data(player_data, table_type)
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
            except Exception:
                stats['failed'] += 1
        
        if verbose:
            print(f"\nPlayers loading complete:")
            print(f"   Total: {stats['total_players']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Transfers detected: {stats['transfers']}")
            print(f"   Failed: {stats['failed']}")
        
        return stats
        
    except Exception as e:
        if verbose:
            print(f"Failed to load {competition}: {e}")
        return stats


def load_teams(competition: str, season: str, table_type: str, verbose: bool = True) -> Dict[str, int]:
    """Load all teams from specific competition and season."""
    if verbose:
        print(f"Loading teams from {competition} - {season}")
        print("=" * 70)
    
    db = get_db_manager()
    
    # ADDED: Clear existing data for this competition/season before loading
    if verbose:
        print("Clearing existing team data for this season...")
    
    success = db.clear_season_data(competition, season, table_type, 'teams')
    if not success and verbose:
        print("Warning: Could not clear existing data, may cause duplicates")
    
    validator = DataValidator()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0}
    
    try:
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"No data found for {competition} {season}")
            return stats
        
        # Rest of the function remains exactly the same...
        unique_teams = players_list_df['team'].dropna().unique().tolist()
        stats['total_teams'] = len(unique_teams)
        
        if verbose:
            print(f"Found {len(unique_teams)} teams to process")
            print("Extracting data...\n")
        
        for i, team_name in enumerate(unique_teams, 1):
            try:
                fbref_data = fbref_get_team(team_name, competition, season)
                if not fbref_data:
                    if verbose:
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name}")
                        print(f"          League, {competition} - FAILED (No FBref data)")
                    stats['failed'] += 1
                    continue
                
                # FIXED: Avoid double Understat prefix
                if table_type == 'domestic':
                    understat_data = understat_get_team(team_name, competition, season)
                    if understat_data:
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'team')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                success = db.insert_team_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    if verbose:
                        metrics_count = len(cleaned_data)
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name}")
                        print(f"          League, {competition} - SUCCESS ({metrics_count} metrics)")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name}")
                        print(f"          League, {competition} - FAILED (DB insert error)")
                    
            except Exception as e:
                if verbose:
                    print(f"[{i:3d}/{len(unique_teams)}] {team_name}")
                    print(f"          League, {competition} - FAILED ({str(e)[:30]}...)")
                stats['failed'] += 1
                continue
        
        if verbose:
            print(f"\nTeams loading complete:")
            print(f"   Total: {stats['total_teams']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Failed: {stats['failed']}")
        
        return stats
        
    except Exception as e:
        if verbose:
            print(f"Failed to load {competition}: {e}")
        return stats


def load_complete_competition(competition: str, season: str, verbose: bool = True) -> Dict[str, Dict[str, int]]:
    """Load both players and teams from a competition."""
    table_type = 'domestic' if competition != 'INT-Champions League' else 'european'
    
    if verbose:
        data_source = "FBref + Understat" if table_type == 'domestic' else "FBref only"
        print(f"Loading complete data from {competition} - {season} ({data_source})")
        print("=" * 80)
    
    results = {}
    
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
        print(f"Players - Total: {player_stats['total_players']} | Successful: {player_stats['successful']} | Transfers: {player_stats['transfers']} | Failed: {player_stats['failed']}")
        print(f"Teams   - Total: {team_stats['total_teams']} | Successful: {team_stats['successful']} | Failed: {team_stats['failed']}")
        
        total_entities = player_stats['total_players'] + team_stats['total_teams']
        total_successful = player_stats['successful'] + team_stats['successful']
        success_rate = (total_successful / total_entities * 100) if total_entities > 0 else 0
        print(f"Overall success rate: {success_rate:.1f}%")
    
    return results

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    """Main execution function."""
    print("FootballDecoded Data Loader - Enhanced Version")
    print("=" * 50)
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
                
                with db.engine.begin() as conn:  # ✅ .begin() auto-commits
                    conn.execute(text("DELETE FROM footballdecoded.players_domestic"))
                    conn.execute(text("DELETE FROM footballdecoded.teams_domestic"))
                    conn.execute(text("DELETE FROM footballdecoded.players_european"))
                    conn.execute(text("DELETE FROM footballdecoded.teams_european"))
                
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