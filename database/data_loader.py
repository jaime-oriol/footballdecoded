# ====================================================================
# FootballDecoded Data Loader - Sistema de IDs Únicos
# ====================================================================

import sys
import os
import pandas as pd
import json
import re
import unicodedata
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_league_players,
                     understat_get_player, understat_get_team)
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

METRIC_RANGES = {
    'age': (15, 50),
    'birth_year': (1950, 2020),
    'minutes_played': (0, 6000),
    'matches_played': (0, 80),
    'matches_started': (0, 80),
    'goals': (0, 120),
    'assists': (0, 60),
    'goals_plus_assists': (0, 150),
    'shots': (0, 600),
    'shots_on_target': (0, 300),
    'shots_on_target_pct': (0, 100),
    'expected_goals': (0, 80),
    'expected_assists': (0, 40),
    'non_penalty_expected_goals': (0, 70),
    'passes_completed': (0, 4000),
    'passes_attempted': (0, 4500),
    'pass_completion_pct': (30, 100),
    'key_passes': (0, 200),
    'tackles': (0, 300),
    'interceptions': (0, 250),
    'clearances': (0, 400),
    'touches': (0, 5000),
    'carries': (0, 3000),
    'yellow_cards': (0, 25),
    'red_cards': (0, 6),
    'take_on_success_pct': (0, 100),
    'aerial_duels_won_pct': (0, 100),
}

# ====================================================================
# SISTEMA DE IDS ÚNICOS
# ====================================================================

class IDGenerator:
    """Generador de IDs únicos usando SHA256."""
    
    @staticmethod
    def normalize_for_id(text: str) -> str:
        """Normalización robusta para generación de IDs."""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).lower().strip()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text).strip('_')
        text = re.sub(r'_+', '_', text)
        
        return text
    
    @staticmethod
    def generate_player_hash_id(name: str, birth_year: Optional[int], nationality: Optional[str]) -> str:
        """Generar ID único para jugador usando SHA256."""
        normalized_name = IDGenerator.normalize_for_id(name)
        birth_str = str(birth_year) if birth_year else "unknown"
        nation_str = IDGenerator.normalize_for_id(nationality) if nationality else "unknown"
        
        combined = f"{normalized_name}_{birth_str}_{nation_str}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    @staticmethod
    def generate_team_hash_id(team_name: str, league: str) -> str:
        """Generar ID único para equipo usando SHA256."""
        normalized_team = IDGenerator.normalize_for_id(team_name)
        normalized_league = IDGenerator.normalize_for_id(league)
        
        combined = f"{normalized_team}_{normalized_league}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

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
    """Validate football data integrity with ID generation."""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.id_generator = IDGenerator()
    
    def validate_record(self, record: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], float, List[str]]:
        """Validate and clean a data record with unique ID generation."""
        cleaned_record = {}
        quality_score = 1.0
        warnings = []
        
        # Clean all fields
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
        
        # Validate required fields
        required_fields = ['player_name', 'league', 'season', 'team'] if entity_type == 'player' else ['team_name', 'league', 'season']
        for field in required_fields:
            if field not in cleaned_record or not cleaned_record[field]:
                warnings.append(f"Missing required field: {field}")
                quality_score -= 0.3
        
        # Generate normalized name and unique ID
        if entity_type == 'player' and 'player_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['player_name'])
            cleaned_record['unique_player_id'] = self.id_generator.generate_player_hash_id(
                cleaned_record['player_name'],
                cleaned_record.get('birth_year'),
                cleaned_record.get('nationality')
            )
        elif entity_type == 'team' and 'team_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['team_name'])
            cleaned_record['unique_team_id'] = self.id_generator.generate_team_hash_id(
                cleaned_record['team_name'],
                cleaned_record['league']
            )
        
        return cleaned_record, max(0.0, quality_score), warnings

# ====================================================================
# MAIN LOADING FUNCTIONS - SIMPLIFICADAS
# ====================================================================

def load_players(competition: str, season: str, table_type: str, verbose: bool = True) -> Dict[str, int]:
    """Load all players from specific competition and season."""
    if verbose:
        print(f"Loading players from {competition} - {season}")
        print("=" * 70)
    
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total_players': 0, 'successful': 0, 'failed': 0}
    
    try:
        # Clear existing data before loading
        if verbose:
            print(f"Clearing existing data for {competition} {season}")
        db.clear_season_data(competition, season, table_type, 'players')
        
        players_list_df = fbref_get_league_players(competition, season)
        
        if hasattr(players_list_df.columns, 'levels'):
            players_list_df.columns = [col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in players_list_df.columns]
        
        if players_list_df.empty:
            if verbose:
                print(f"No players found for {competition} {season}")
            return stats
        
        unique_players = players_list_df['player'].dropna().unique().tolist()
        stats['total_players'] = len(unique_players)
        
        if verbose:
            print(f"Found {len(unique_players)} players to process")
            print("Extracting data...\n")
        
        for i, player_name in enumerate(unique_players, 1):
            team = 'Unknown'
            try:
                fbref_data = fbref_get_player(player_name, competition, season)
                if not fbref_data:
                    if verbose:
                        print(f"[{i:3d}/{len(unique_players)}] {player_name} - FAILED (No FBref data)")
                    stats['failed'] += 1
                    continue
                
                team = fbref_data.get('team', 'Unknown')
                
                # Add Understat data for domestic leagues
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
                
                success = db.insert_player_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    if verbose:
                        print(f"[{i:3d}/{len(unique_players)}] {player_name} - SUCCESS")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print(f"[{i:3d}/{len(unique_players)}] {player_name} - FAILED (DB insert)")
                
            except Exception as e:
                if verbose:
                    print(f"[{i:3d}/{len(unique_players)}] {player_name} - FAILED ({str(e)[:30]}...)")
                stats['failed'] += 1
                continue
        
        if verbose:
            print(f"\nPlayers loading complete:")
            print(f"   Total: {stats['total_players']}")
            print(f"   Successful: {stats['successful']}")
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
    validator = DataValidator()
    stats = {'total_teams': 0, 'successful': 0, 'failed': 0}
    
    try:
        # Clear existing data before loading
        if verbose:
            print(f"Clearing existing data for {competition} {season}")
        db.clear_season_data(competition, season, table_type, 'teams')
        
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            if verbose:
                print(f"No data found for {competition} {season}")
            return stats
        
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
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name} - FAILED (No FBref data)")
                    stats['failed'] += 1
                    continue
                
                # Add Understat data for domestic leagues
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
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name} - SUCCESS")
                else:
                    stats['failed'] += 1
                    if verbose:
                        print(f"[{i:3d}/{len(unique_teams)}] {team_name} - FAILED (DB insert)")
                    
            except Exception as e:
                if verbose:
                    print(f"[{i:3d}/{len(unique_teams)}] {team_name} - FAILED ({str(e)[:30]}...)")
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
        print(f"Players - Total: {player_stats['total_players']} | Successful: {player_stats['successful']} | Failed: {player_stats['failed']}")
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
    print("FootballDecoded Data Loader - ID System")
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
                from database.connection import get_db_manager
                from sqlalchemy import text
                
                db = get_db_manager()
                
                with db.engine.begin() as conn:
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