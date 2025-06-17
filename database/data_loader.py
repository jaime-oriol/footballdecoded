# ====================================================================
# FootballDecoded Data Loader - Sistema de IDs Únicos Optimizado
# ====================================================================

import sys
import os
import pandas as pd
import json
import re
import unicodedata
import hashlib
import time
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
    'goals': (0, 120),
    'assists': (0, 60),
    'shots': (0, 600),
    'expected_goals': (0, 80),
    'passes_completed': (0, 4000),
    'pass_completion_pct': (30, 100),
    'tackles': (0, 300),
    'yellow_cards': (0, 25),
    'red_cards': (0, 6),
}

# MASSIVE LOAD ONLY - Conservative rate limiting para 100% seguridad
MASSIVE_LOAD_CONFIG = {
    'league_delay_minutes': 45,  # 45 minutos entre ligas
    'progress_save_interval': 50,  # Guardar progreso cada 50 entidades
    'connection_timeout_hours': 12  # Timeout total de 12 horas
}

# ====================================================================
# LOGGING SYSTEM ESTANDARIZADO
# ====================================================================

class LogManager:
    def __init__(self):
        self.start_time = None
        self.phase_start_time = None
        self.line_width = 80
    
    def header(self, competition: str, season: str, data_sources: str):
        print("FootballDecoded Data Loader")
        print("═" * self.line_width)
        print(f"Competition: {competition} {season} ({data_sources})")
        
        # Database status
        try:
            db = get_db_manager()
            db_status = "Connected"
            schema = "footballdecoded"
            db.close()
        except:
            db_status = "Failed"
            schema = "unknown"
        
        print(f"Database: {db_status} | Schema: {schema}")
        print("Clearing existing data: 0 records removed (fresh load)")
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def massive_header(self, season: str):
        print("FootballDecoded Massive Annual Loader")
        print("═" * self.line_width)
        print(f"Season: {season} | All Competitions (6 leagues)")
        print(f"Rate limiting: {MASSIVE_LOAD_CONFIG['league_delay_minutes']} minutes between leagues")
        
        # Database status
        try:
            db = get_db_manager()
            db_status = "Connected"
            schema = "footballdecoded"
            db.close()
        except:
            db_status = "Failed"
            schema = "unknown"
        
        print(f"Database: {db_status} | Schema: {schema}")
        print("Clearing existing data: 0 records removed (fresh load)")
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def competition_start(self, comp_number: int, total_comps: int, competition: str, data_source: str):
        print(f"[{comp_number}/{total_comps}] {competition.upper()}")
        print(f"Data source: {data_source}")
        print("─" * 50)
    
    def phase_start(self, phase_name: str, total_entities: int):
        self.phase_start_time = datetime.now()
        print(f"{phase_name.upper()} EXTRACTION")
        print(f"{phase_name} found: {total_entities:,} -> Processing extraction")
    
    def progress_update(self, current: int, total: int, current_entity: str, 
                       metrics_count: int, fbref_success: int, understat_success: int, 
                       understat_total: int, failed_count: int):
        percentage = (current / total) * 100
        filled = int(40 * current // total)
        bar = '\033[42m' + ' ' * filled + '\033[0m' + ' ' * (40 - filled)
        
        print(f"\rProgress: [{bar}] {current}/{total} ({percentage:.1f}%)")
        
        if current > 0:
            print(f"├─ Current: {current_entity}")
            
            if understat_total == 0:
                understat_text = " (Understat: N/A)"
            else:
                understat_text = ""
            print(f"├─ Metrics: {metrics_count} fields extracted{understat_text}")
            
            print(f"├─ FBref: {fbref_success}/{current} successful")
            
            if understat_total > 0:
                understat_pct = (understat_success / understat_total * 100) if understat_total > 0 else 0
                print(f"├─ Understat: {understat_success}/{understat_total} merged ({understat_pct:.1f}%)")
            else:
                print("├─ Understat: N/A (European competition)")
            
            print(f"└─ Failed: {failed_count}")
        
        if current < total:
            print("\033[6A", end="", flush=True)
    
    def progress_complete(self, total: int):
        # Clear previous lines
        for _ in range(6):
            print(" " * self.line_width)
        print("\033[6A", end="")
        
        bar = '\033[42m' + ' ' * 40 + '\033[0m'
        print(f"Progress: [{bar}] {total}/{total} (100%)")
        
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            elapsed_formatted = self._format_time(int(elapsed))
            print(f"└─ Completed in: {elapsed_formatted}")
        
        print()
    
    def competition_summary(self, stats: dict, competition: str):
        total = stats['players']['total'] + stats['teams']['total']
        successful = stats['players']['successful'] + stats['teams']['successful']
        failed = stats['players']['failed'] + stats['teams']['failed']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"COMPETITION SUMMARY: {competition}")
        print(f"Total: {total} | Success: {successful} | Failed: {failed} | Rate: {success_rate:.1f}%")
        print(f"Players: {stats['players']['successful']} | Teams: {stats['teams']['successful']}")
        print()
    
    def massive_league_pause(self, current_league: int, total_leagues: int, next_league: str, delay_minutes: int):
        remaining_leagues = total_leagues - current_league
        estimated_time = remaining_leagues * delay_minutes
        
        print("─" * self.line_width)
        print(f"MASSIVE LOAD RATE LIMITING")
        print(f"Next: {next_league}")
        print(f"Pausing: {delay_minutes} minutes (ensuring IP safety)")
        print(f"Remaining: {remaining_leagues} leagues | Est. time: {estimated_time} minutes")
        print("─" * self.line_width)
        
        # Countdown timer
        for minute in range(delay_minutes, 0, -1):
            print(f"\rResuming in: {minute} minutes...", end="", flush=True)
            time.sleep(60)
        print(f"\rResuming now...                  ")
        print()
    
    def massive_summary(self, all_stats: Dict, total_time: int):
        print("─" * self.line_width)
        print("MASSIVE LOAD SUMMARY")
        print("─" * self.line_width)
        
        total_entities = sum(stats['players']['total'] + stats['teams']['total'] for stats in all_stats.values())
        total_successful = sum(stats['players']['successful'] + stats['teams']['successful'] for stats in all_stats.values())
        total_failed = sum(stats['players']['failed'] + stats['teams']['failed'] for stats in all_stats.values())
        
        print(f"Total entities processed: {total_entities:,}")
        print(f"Successfully loaded: {total_successful:,}")
        print(f"Failed: {total_failed:,}")
        print(f"Success rate: {(total_successful/total_entities*100):.1f}%")
        print(f"Total processing time: {self._format_time(total_time)}")
        
        total_players = sum(stats['players']['successful'] for stats in all_stats.values())
        total_teams = sum(stats['teams']['successful'] for stats in all_stats.values())
        print(f"Unique players loaded: {total_players:,}")
        print(f"Unique teams loaded: {total_teams:,}")
        
        print("\nPer competition breakdown:")
        for comp, stats in all_stats.items():
            success = stats['players']['successful'] + stats['teams']['successful']
            total = stats['players']['total'] + stats['teams']['total']
            rate = (success/total*100) if total > 0 else 0
            print(f"  {comp}: {success:,}/{total:,} ({rate:.1f}%)")
        
        print("═" * self.line_width)
    
    def final_summary(self, stats: dict):
        print("─" * self.line_width)
        print("EXTRACTION SUMMARY")
        print("─" * self.line_width)
        
        total = stats['players']['total'] + stats['teams']['total']
        successful = stats['players']['successful'] + stats['teams']['successful']
        failed = stats['players']['failed'] + stats['teams']['failed']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"Total entities: {total:,} | Successful: {successful:,} | Failed: {failed:,} | Success rate: {success_rate:.1f}%")
        print(f"Unique player IDs: {stats['players']['successful']:,} | Unique team IDs: {stats['teams']['successful']:,}")
        
        if stats.get('transfers', 0) > 0:
            print(f"Transfer detection: {stats['transfers']:,} players with multiple teams")
        
        if stats.get('understat_coverage'):
            player_cov = stats['understat_coverage'].get('players', 0)
            team_cov = stats['understat_coverage'].get('teams', 0)
            if player_cov > 0 or team_cov > 0:
                print(f"Understat coverage: Players {player_cov:.1f}% | Teams {team_cov:.1f}%")
            else:
                print("Understat coverage: N/A (European competition)")
        
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            total_seconds = elapsed.total_seconds()
            records_per_second = successful / total_seconds if total_seconds > 0 else 0
            elapsed_formatted = self._format_time(int(total_seconds))
            print(f"Processing time: {elapsed_formatted} | Records per second: {records_per_second:.1f}")
        
        storage_mb = successful * 0.004
        print(f"Database records: {successful:,} inserted | Storage: +{storage_mb:.1f}MB")
        
        if failed > 0:
            print()
            if success_rate >= 95:
                print("EXTRACTION COMPLETED WITH MINOR ISSUES")
                print(f"└─ {failed:,} extraction failures (recommend retry)")
            else:
                print("ISSUES DETECTED")
                print(f"├─ {failed:,} extraction failures (connection or data issues)")
                print("└─ Recommendation: Check network connection and retry")
        
        print("═" * self.line_width)
    
    def _format_time(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

# ====================================================================
# ID GENERATION SYSTEM
# ====================================================================

class IDGenerator:
    @staticmethod
    def normalize_for_id(text: str) -> str:
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
        normalized_name = IDGenerator.normalize_for_id(name)
        birth_str = str(birth_year) if birth_year else "unknown"
        nation_str = IDGenerator.normalize_for_id(nationality) if nationality else "unknown"
        
        combined = f"{normalized_name}_{birth_str}_{nation_str}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    @staticmethod
    def generate_team_hash_id(team_name: str, league: str) -> str:
        normalized_team = IDGenerator.normalize_for_id(team_name)
        normalized_league = IDGenerator.normalize_for_id(league)
        
        combined = f"{normalized_team}_{normalized_league}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

# ====================================================================
# DATA PROCESSING
# ====================================================================

class DataNormalizer:
    def normalize_name(self, name: str) -> str:
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
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.id_generator = IDGenerator()
    
    def validate_record(self, record: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], float, List[str]]:
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
# CORE LOADING FUNCTIONS - SIN RATE LIMITING PARA LOAD NORMAL
# ====================================================================

def load_players(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Load players - NO rate limiting for normal load."""
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total': 0, 'successful': 0, 'failed': 0, 'avg_metrics': 0}
    
    try:
        db.clear_season_data(competition, season, table_type, 'players')
        
        players_list_df = fbref_get_league_players(competition, season)
        
        if hasattr(players_list_df.columns, 'levels'):
            players_list_df.columns = [col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in players_list_df.columns]
        
        if players_list_df.empty:
            return stats
        
        unique_players = players_list_df['player'].dropna().unique().tolist()
        stats['total'] = len(unique_players)
        
        logger.phase_start("Players", len(unique_players))
        
        total_metrics = 0
        fbref_success = 0
        understat_success = 0
        understat_total = 0 if table_type == 'european' else len(unique_players)
        
        for i, player_name in enumerate(unique_players, 1):
            current_entity = f"{player_name} (Processing...)"
            
            try:
                # FBref extraction - direct, no retries
                fbref_data = fbref_get_player(player_name, competition, season)
                if not fbref_data:
                    stats['failed'] += 1
                    continue
                
                fbref_success += 1
                team = fbref_data.get('team', 'Unknown')
                current_entity = f"{player_name} ({team})"
                
                # Understat extraction for domestic leagues
                if table_type == 'domestic':
                    understat_data = understat_get_player(player_name, competition, season)
                    if understat_data:
                        understat_success += 1
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                # Data validation and storage
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'player')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                success = db.insert_player_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    total_metrics += len(cleaned_data)
                else:
                    stats['failed'] += 1
                
                avg_metrics = total_metrics // max(stats['successful'], 1)
                
                logger.progress_update(
                    i, len(unique_players), current_entity, avg_metrics,
                    fbref_success, understat_success, understat_total, stats['failed']
                )
                
            except Exception:
                stats['failed'] += 1
                continue
        
        logger.progress_complete(stats['total'])
        stats['avg_metrics'] = total_metrics // max(stats['successful'], 1)
        
        return stats
        
    except Exception:
        return stats

def load_teams(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Load teams - NO rate limiting for normal load."""
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total': 0, 'successful': 0, 'failed': 0, 'avg_metrics': 0}
    
    try:
        db.clear_season_data(competition, season, table_type, 'teams')
        
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            return stats
        
        unique_teams = players_list_df['team'].dropna().unique().tolist()
        stats['total'] = len(unique_teams)
        
        logger.phase_start("Teams", len(unique_teams))
        
        total_metrics = 0
        fbref_success = 0
        understat_success = 0
        understat_total = 0 if table_type == 'european' else len(unique_teams)
        
        for i, team_name in enumerate(unique_teams, 1):
            current_entity = f"{team_name}"
            
            try:
                # FBref extraction - direct, no retries
                fbref_data = fbref_get_team(team_name, competition, season)
                if not fbref_data:
                    stats['failed'] += 1
                    continue
                
                fbref_success += 1
                
                # Understat extraction for domestic leagues
                if table_type == 'domestic':
                    understat_data = understat_get_team(team_name, competition, season)
                    if understat_data:
                        understat_success += 1
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                # Data validation and storage
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'team')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                success = db.insert_team_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    total_metrics += len(cleaned_data)
                else:
                    stats['failed'] += 1
                
                avg_metrics = total_metrics // max(stats['successful'], 1)
                
                logger.progress_update(
                    i, len(unique_teams), current_entity, avg_metrics,
                    fbref_success, understat_success, understat_total, stats['failed']
                )
                
            except Exception:
                stats['failed'] += 1
                continue
        
        logger.progress_complete(stats['total'])
        stats['avg_metrics'] = total_metrics // max(stats['successful'], 1)
        
        return stats
        
    except Exception:
        return stats

def load_complete_competition(competition: str, season: str) -> Dict[str, Dict[str, int]]:
    """Load complete competition - NO rate limiting."""
    table_type = 'domestic' if competition != 'INT-Champions League' else 'european'
    data_source = "FBref + Understat" if table_type == 'domestic' else "FBref only"
    
    logger = LogManager()
    logger.header(competition, season, data_source)
    
    player_stats = load_players(competition, season, table_type, logger)
    team_stats = load_teams(competition, season, table_type, logger)
    
    understat_coverage = None
    if table_type == 'domestic':
        player_coverage = (understat_success / max(player_stats['successful'], 1) * 100) if player_stats['successful'] > 0 else 0
        team_coverage = (understat_success / max(team_stats['successful'], 1) * 100) if team_stats['successful'] > 0 else 0
        understat_coverage = {'players': player_coverage, 'teams': team_coverage}
    
    summary_stats = {
        'players': player_stats,
        'teams': team_stats,
        'understat_coverage': understat_coverage
    }
    
    logger.final_summary(summary_stats)
    
    return {'players': player_stats, 'teams': team_stats}

# ====================================================================
# MASSIVE ANNUAL LOADER - CON RATE LIMITING CONSERVATIVO
# ====================================================================

def load_massive_annual(season: str) -> Dict[str, Dict[str, Dict[str, int]]]:
    """Load all competitions with conservative rate limiting - 100% IP safety."""
    logger = LogManager()
    logger.massive_header(season)
    
    all_stats = {}
    start_time = datetime.now()
    
    for i, (competition, table_type) in enumerate(AVAILABLE_COMPETITIONS, 1):
        data_source = "FBref + Understat" if table_type == 'domestic' else "FBref only"
        
        logger.competition_start(i, len(AVAILABLE_COMPETITIONS), competition, data_source)
        
        try:
            # Load players and teams for this competition
            player_stats = load_players(competition, season, table_type, logger)
            team_stats = load_teams(competition, season, table_type, logger)
            
            # Store stats
            competition_stats = {'players': player_stats, 'teams': team_stats}
            all_stats[competition] = competition_stats
            
            # Competition summary
            logger.competition_summary(competition_stats, competition)
            
            # MASSIVE LOAD RATE LIMITING - Only between complete leagues
            if i < len(AVAILABLE_COMPETITIONS):
                next_competition = AVAILABLE_COMPETITIONS[i][0]
                logger.massive_league_pause(
                    i, len(AVAILABLE_COMPETITIONS), 
                    next_competition, 
                    MASSIVE_LOAD_CONFIG['league_delay_minutes']
                )
            
        except Exception as e:
            print(f"ERROR: Failed to process {competition}: {e}")
            all_stats[competition] = {
                'players': {'total': 0, 'successful': 0, 'failed': 0}, 
                'teams': {'total': 0, 'successful': 0, 'failed': 0}
            }
            continue
    
    # Final massive summary
    total_time = int((datetime.now() - start_time).total_seconds())
    logger.massive_summary(all_stats, total_time)
    
    return all_stats

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    print("FootballDecoded Data Loader")
    print("═" * 50)
    print("\n1. Load competition data (players + teams)")
    print("2. Load ALL competitions for season (massive)")
    print("3. Test database connection")
    print("4. Setup database schema")
    print("5. Clear all existing data")
    print("6. Check database status")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        print("\nAvailable competitions:")
        for i, (comp_name, comp_type) in enumerate(AVAILABLE_COMPETITIONS, 1):
            data_source = "FBref + Understat" if comp_type == 'domestic' else "FBref only"
            print(f"   {i}. {comp_name} ({data_source})")
        
        try:
            comp_choice = int(input(f"\nSelect competition (1-{len(AVAILABLE_COMPETITIONS)}): ").strip())
            if 1 <= comp_choice <= len(AVAILABLE_COMPETITIONS):
                selected_competition, _ = AVAILABLE_COMPETITIONS[comp_choice - 1]
                season = input("Enter season (e.g., 2023-24): ").strip()
                
                if season:
                    load_complete_competition(selected_competition, season)
                else:
                    print("Invalid season format")
            else:
                print("Invalid competition selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "2":
        season = input("Enter season for massive load (e.g., 2023-24): ").strip()
        if season:
            print(f"\nMASSIVE ANNUAL LOAD CONFIGURATION")
            print("═" * 50)
            print(f"Season: {season}")
            print(f"Competitions: {len(AVAILABLE_COMPETITIONS)} leagues")
            print(f"Rate limiting: {MASSIVE_LOAD_CONFIG['league_delay_minutes']} minutes between leagues")
            
            # Calculate estimated time
            estimated_hours = (MASSIVE_LOAD_CONFIG['league_delay_minutes'] * (len(AVAILABLE_COMPETITIONS) - 1)) / 60
            estimated_hours += 2  # Add processing time
            print(f"Estimated duration: {estimated_hours:.1f} hours")
            print(f"IP safety: 100% conservative approach")
            print()
            
            confirm = input(f"Proceed with massive load? (y/N): ").strip().lower()
            if confirm == 'y':
                print(f"\nStarting massive annual load for {season}...")
                print("IMPORTANT: Conservative rate limiting active")
                print("You can safely leave this running overnight")
                print()
                
                load_massive_annual(season)
            else:
                print("Massive load cancelled")
        else:
            print("Invalid season format")
    
    elif choice == "3":
        print("\nTesting database connection...")
        try:
            from database.connection import test_connection
            success = test_connection()
            status = "successful" if success else "failed"
            print(f"Database connection {status}")
        except Exception as e:
            print(f"Connection test error: {e}")
    
    elif choice == "4":
        confirm = input("Setup database schema? This will create/recreate tables (y/N): ").strip().lower()
        if confirm == 'y':
            print("\nSetting up database schema...")
            try:
                from database.connection import setup_database
                success = setup_database()
                status = "complete" if success else "failed"
                print(f"Database schema setup {status}")
            except Exception as e:
                print(f"Schema setup error: {e}")
        else:
            print("Schema setup cancelled")
    
    elif choice == "5":
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
    
    elif choice == "6":
        print("\nChecking database status...")
        try:
            from database.database_checker import check_database_status
            check_database_status(verbose=True)
        except ImportError:
            print("database_checker.py not found")
        except Exception as e:
            print(f"Error checking database: {e}")
    
    else:
        print("Invalid option. Please select 1-6.")


if __name__ == "__main__":
    main()