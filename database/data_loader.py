"""Data loader pipeline: FBref -> Understat merge -> Transfermarkt enrich -> PostgreSQL.

Parallel extraction (3 workers), checkpoint recovery (24h expiry),
adaptive rate limiting, and terminal progress bar with ETA.

Usage: python data_loader.py  (interactive menu, options 1-8)
"""

import sys
import os
import pandas as pd
import json
import re
import unicodedata
import hashlib
import time
import random
import pickle
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pathlib import Path
import logging
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='lxml')
warnings.filterwarnings('ignore', category=UserWarning, module='html5lib')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger('tls_requests').setLevel(logging.CRITICAL)
logging.getLogger('wrapper_tls_requests').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.WARNING)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_league_players,
                     understat_get_player, understat_get_team, transfermarkt_get_player)
from database.connection import DatabaseManager, get_db_manager

AVAILABLE_COMPETITIONS = [
    ('ENG-Premier League', 'domestic'),
    ('ESP-La Liga', 'domestic'),
    ('ITA-Serie A', 'domestic'),
    ('GER-Bundesliga', 'domestic'),
    ('FRA-Ligue 1', 'domestic'),
    ('INT-Champions League', 'european'),
    ('POR-Primeira Liga', 'extras'),
    ('NED-Eredivisie', 'extras'),
    ('BEL-Pro League', 'extras'),
    ('TUR-Süper Lig', 'extras'),
    ('SCO-Premiership', 'extras'),
    ('SUI-Super League', 'extras'),
    ('USA-MLS', 'extras')
]

# Outlier detection ranges; values outside trigger a quality score penalty
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

LOAD_CONFIG = {
    'massive_league_delay_minutes': 45,
    'massive_progress_save_interval': 50,
    'massive_connection_timeout_hours': 12,
    'block_pause_min': 10,             # Min minutes pause between leagues (anti-ban)
    'block_pause_max': 20,             # Max minutes pause between leagues
    'progress_bar_width': 40,
    'line_width': 80,
    'parallel_workers': 3,             # Conservative parallelism to avoid rate limits
    'checkpoint_interval': 25,         # Save progress every N records
    'checkpoint_dir': '.checkpoints',
    'adaptive_rate_limiting': True,
    'min_delay': 0.5,                  # Seconds between API calls (floor)
    'max_delay': 3.0,                  # Seconds between API calls (ceiling)
    'initial_delay': 1.0,
}

BLOCK_1_COMPETITIONS = [
    ('ENG-Premier League', 'domestic'),
    ('ESP-La Liga', 'domestic'),
    ('ITA-Serie A', 'domestic')
]

BLOCK_2_COMPETITIONS = [
    ('GER-Bundesliga', 'domestic'),
    ('FRA-Ligue 1', 'domestic'),
    ('INT-Champions League', 'european')
]

BLOCK_3_EXTRAS = [
    ('POR-Primeira Liga', 'extras'),
    ('NED-Eredivisie', 'extras'),
    ('BEL-Pro League', 'extras'),
    ('TUR-Süper Lig', 'extras'),
    ('SCO-Premiership', 'extras'),
    ('SUI-Super League', 'extras'),
    ('USA-MLS', 'extras')
]

class CheckpointManager:
    """Pickle-based crash recovery for interrupted loads (24h expiry)."""
    
    def __init__(self, competition: str, season: str, entity_type: str):
        self.competition = competition
        self.season = season
        self.entity_type = entity_type
        self.checkpoint_dir = Path(LOAD_CONFIG['checkpoint_dir'])
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        safe_competition = competition.replace(' ', '_').replace('-', '_')
        self.checkpoint_file = self.checkpoint_dir / f"{safe_competition}_{season}_{entity_type}_checkpoint.pkl"
        
    def save_progress(self, processed_entities: List[str], stats: Dict[str, Any], current_index: int):
        """Persist current progress to pickle file."""
        try:
            checkpoint_data = {
                'competition': self.competition,
                'season': self.season,
                'entity_type': self.entity_type,
                'processed_entities': processed_entities,
                'current_index': current_index,
                'stats': stats,
                'timestamp': datetime.now(),
                'total_processed': len(processed_entities)
            }
            
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
                
            logger.debug(f"Checkpoint saved: {len(processed_entities)} {self.entity_type}s processed")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def load_progress(self) -> Optional[Dict[str, Any]]:
        """Load previous checkpoint if it exists and is less than 24h old."""
        try:
            if not self.checkpoint_file.exists():
                return None
                
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
                
            if datetime.now() - checkpoint_data['timestamp'] > timedelta(days=1):
                logger.warning("Checkpoint is older than 24 hours, ignoring")
                return None
                
            logger.info(f"Loaded checkpoint: {checkpoint_data['total_processed']} {self.entity_type}s already processed")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def clear_checkpoint(self):
        """Delete checkpoint file after successful completion."""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                logger.info("Checkpoint cleared")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")

class AdaptiveRateLimit:
    """Adjusts request delay based on response times and failure streaks."""
    
    def __init__(self):
        self.current_delay = LOAD_CONFIG['initial_delay']
        self.min_delay = LOAD_CONFIG['min_delay'] 
        self.max_delay = LOAD_CONFIG['max_delay']
        self.response_times = []
        self.lock = Lock()
        self.consecutive_failures = 0
        
    def record_request(self, response_time: float, success: bool):
        """Record response time and adjust delay accordingly."""
        with self.lock:
            if success:
                self.response_times.append(response_time)
                self.consecutive_failures = 0

                if len(self.response_times) > 10:
                    self.response_times.pop(0)

                avg_response_time = sum(self.response_times) / len(self.response_times)

                if avg_response_time < 1.0:
                    self.current_delay = max(self.min_delay, self.current_delay * 0.9)
                elif avg_response_time > 3.0:
                    self.current_delay = min(self.max_delay, self.current_delay * 1.2)

            else:
                self.consecutive_failures += 1
                # Exponential backoff capped at 3 consecutive failures
                failure_multiplier = 1.5 ** min(self.consecutive_failures, 3)
                self.current_delay = min(self.max_delay, self.current_delay * failure_multiplier)
    
    def get_delay(self) -> float:
        """Return current delay in seconds."""
        return self.current_delay

    def wait(self):
        """Sleep for the current adaptive delay."""
        time.sleep(self.current_delay)

class LogManager:
    """Terminal output manager with progress bar, ETA, and summary formatting."""

    def __init__(self):
        self.start_time = None
        self.phase_start_time = None
        self.line_width = LOAD_CONFIG['line_width']
        self.current_lines_printed = 0
    
    def header(self, competition: str, season: str, data_sources: str):
        """Print single-competition load header with DB status."""
        print("FootballDecoded Data Loader")
        print("═" * self.line_width)
        print(f"Competition: {competition} {season} ({data_sources})")
        
        try:
            db = get_db_manager()
            db_status = "Connected"
            schema = "footballdecoded"

            table_type = 'domestic'
            for comp, ttype in AVAILABLE_COMPETITIONS:
                if comp == competition:
                    table_type = ttype
                    break
            existing_records = self._count_existing_records(db, competition, season, table_type)
            
            db.close()
        except:
            db_status = "Failed"
            schema = "unknown"
            existing_records = 0
        
        print(f"Database: {db_status} | Schema: {schema}")
        
        if existing_records > 0:
            print(f"Clearing existing data: {existing_records} records removed")
        else:
            print("Clearing existing data: 0 records removed (fresh load)")
            
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def massive_header_block(self, block_name: str, season: str, num_competitions: int):
        """Print block-load header with pause configuration."""
        print(f"FootballDecoded {block_name} Loader")
        print("═" * self.line_width)
        print(f"Season: {season} | {block_name} ({num_competitions} leagues)")
        print(f"Random pauses: {LOAD_CONFIG['block_pause_min']}-{LOAD_CONFIG['block_pause_max']} minutes between leagues")
        
        try:
            db = get_db_manager()
            db_status = "Connected"
            schema = "footballdecoded"
            db.close()
        except:
            db_status = "Failed"
            schema = "unknown"
        
        print(f"Database: {db_status} | Schema: {schema}")
        print("Note: Individual competition clearing will be done per league")
            
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def competition_start(self, comp_number: int, total_comps: int, competition: str, data_source: str):
        """Print competition start banner within a block load."""
        print(f"[{comp_number}/{total_comps}] {competition.upper()}")
        print(f"Data source: {data_source}")
        print("─" * 50)
    
    def phase_start(self, phase_name: str, total_entities: int):
        """Print phase header (e.g. 'PLAYERS EXTRACTION') and reset timer."""
        self.phase_start_time = datetime.now()
        self.current_lines_printed = 0
        print(f"{phase_name.upper()} EXTRACTION")
        print(f"{phase_name} found: {total_entities:,} -> Processing extraction")
        print()
    
    def progress_update(self, current: int, total: int, current_entity: str,
                       metrics_count: int, failed_count: int, entity_type: str,
                       entity_context: str, state: str, eta_seconds: Optional[int] = None):
        """Overwrite previous progress lines with updated bar and stats."""
        if self.current_lines_printed > 0:
            for _ in range(self.current_lines_printed):
                print("\033[1A\033[K", end="")
        
        percentage = (current / total) * 100
        filled = int(LOAD_CONFIG['progress_bar_width'] * current // total)
        
        progress_bar = (
            '\033[42m' + ' ' * filled +
            '\033[0m' + '░' * (LOAD_CONFIG['progress_bar_width'] - filled)
        )
        
        eta_text = ""
        if eta_seconds and eta_seconds > 0:
            if eta_seconds < 60:
                eta_text = f" | ETA: {eta_seconds}s"
            elif eta_seconds < 3600:
                eta_text = f" | ETA: {eta_seconds//60}m {eta_seconds%60}s"
            else:
                hours = eta_seconds // 3600
                minutes = (eta_seconds % 3600) // 60
                eta_text = f" | ETA: {hours}h {minutes}m"
        
        lines = [
            f"Progress: [{progress_bar}] {current}/{total} ({percentage:.1f}%){eta_text}",
            f"├─ {entity_type}: {current_entity}",
            f"├─ {'Team' if entity_type == 'Player' else 'League'}: {entity_context}",
            f"├─ Metrics: {metrics_count} fields extracted",
            f"├─ State: {state}",
            f"└─ Failed: {failed_count}"
        ]
        
        for line in lines:
            print(line)
        
        self.current_lines_printed = len(lines)
        
        if current < total:
            print(end="", flush=True)
    
    def progress_complete(self, total: int):
        """Replace progress bar with 100% completed line and elapsed time."""
        if self.current_lines_printed > 0:
            for _ in range(self.current_lines_printed):
                print("\033[1A\033[K", end="")
        
        progress_bar = '\033[42m' + ' ' * LOAD_CONFIG['progress_bar_width'] + '\033[0m'
        print(f"Progress: [{progress_bar}] {total}/{total} (100%)")
        
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            elapsed_formatted = self._format_time(int(elapsed))
            print(f"└─ Completed in: {elapsed_formatted}")
        
        print()
        self.current_lines_printed = 0
    
    def competition_summary(self, stats: dict, competition: str):
        """Print success/failure breakdown for a single competition."""
        total = stats['players']['total'] + stats['teams']['total']
        successful = stats['players']['successful'] + stats['teams']['successful']
        failed = stats['players']['failed'] + stats['teams']['failed']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"COMPETITION SUMMARY: {competition}")
        print(f"Total: {total} | Success: {successful} | Failed: {failed} | Rate: {success_rate:.1f}%")
        print(f"Players: {stats['players']['successful']} | Teams: {stats['teams']['successful']}")
        print()
    
    def block_league_pause(self, current_league: int, total_leagues: int, next_league: str, pause_minutes: int):
        """Display countdown timer between leagues (anti-ban pause)."""
        remaining_leagues = total_leagues - current_league
        
        print("─" * self.line_width)
        print(f"BLOCK LOAD RANDOM PAUSE")
        print(f"Next: {next_league}")
        print(f"Random pause: {pause_minutes} minutes (IP safety)")
        print(f"Remaining: {remaining_leagues} leagues in this block")
        print("─" * self.line_width)
        
        for minute in range(pause_minutes, 0, -1):
            print(f"\rResuming in: {minute} minutes...", end="", flush=True)
            time.sleep(60)
        print(f"\rResuming now...                  ")
        print()
    
    def block_summary(self, all_stats: Dict, total_time: int, block_name: str):
        """Print aggregate stats for all competitions in a block."""
        print("─" * self.line_width)
        print(f"{block_name.upper()} SUMMARY")
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
        
        print(f"\n{block_name} breakdown:")
        for comp, stats in all_stats.items():
            success = stats['players']['successful'] + stats['teams']['successful']
            total = stats['players']['total'] + stats['teams']['total']
            rate = (success/total*100) if total > 0 else 0
            print(f"  {comp}: {success:,}/{total:,} ({rate:.1f}%)")
        
        print("═" * self.line_width)
    
    def final_summary(self, stats: dict):
        """Print final extraction summary with timing, coverage, and recommendations."""
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
    
    def _count_existing_records(self, db, competition: str, season: str, table_type: str) -> int:
        """Count player + team records for a competition/season (for header display)."""
        try:
            from scrappers._common import SeasonCode
            
            season_code = SeasonCode.from_leagues([competition])
            parsed_season = season_code.parse(season)
            
            league_field = 'competition' if table_type == 'european' else 'league'
            
            player_query = f"""
                SELECT COUNT(*) as count 
                FROM footballdecoded.players_{table_type} 
                WHERE {league_field} = %(league)s AND season = %(season)s
            """
            player_result = pd.read_sql(player_query, db.engine, params={
                'league': competition, 
                'season': parsed_season
            })
            
            team_query = f"""
                SELECT COUNT(*) as count 
                FROM footballdecoded.teams_{table_type} 
                WHERE {league_field} = %(league)s AND season = %(season)s
            """
            team_result = pd.read_sql(team_query, db.engine, params={
                'league': competition, 
                'season': parsed_season
            })
            
            total_records = player_result.iloc[0]['count'] + team_result.iloc[0]['count']
            return total_records
            
        except Exception:
            return 0
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds as human-readable string (e.g. '2m 30s')."""
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

class IDGenerator:
    """Generate deterministic SHA256-based unique IDs for players and teams."""

    @staticmethod
    def normalize_for_id(text: str) -> str:
        """Strip accents, lowercase, and normalize whitespace for hashing."""
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
        """Return 16-char hex ID from SHA256(name + birth_year + nationality)."""
        normalized_name = IDGenerator.normalize_for_id(name)
        birth_str = str(birth_year) if birth_year else "unknown"
        nation_str = IDGenerator.normalize_for_id(nationality) if nationality else "unknown"
        
        combined = f"{normalized_name}_{birth_str}_{nation_str}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    @staticmethod
    def generate_team_hash_id(team_name: str, league: str) -> str:
        """Return 16-char hex ID from SHA256(team_name + league)."""
        normalized_team = IDGenerator.normalize_for_id(team_name)
        normalized_league = IDGenerator.normalize_for_id(league)
        
        combined = f"{normalized_team}_{normalized_league}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

class DataNormalizer:
    """Clean and normalize player/team names and field values."""

    def normalize_name(self, name: str) -> str:
        """Strip accents, fix suffixes (Jr/Sr), and title-case a name."""
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
        """Sanitize a field value: handle NaN, Series repr leaks, and list fields."""
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
    """Validate and clean entity records, computing quality scores and unique IDs."""

    def __init__(self):
        self.normalizer = DataNormalizer()
        self.id_generator = IDGenerator()
    
    def validate_record(self, record: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], float, List[str]]:
        """Clean all fields, check ranges, generate unique ID. Returns (record, quality_score, warnings)."""
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

def process_single_entity(args: Tuple[str, str, str, str, DataValidator, str]) -> Tuple[bool, Dict[str, Any], str, str]:
    """Extract, merge, and validate a single player/team. Designed for ThreadPoolExecutor."""
    entity_name, entity_type, competition, season, validator, table_type = args
    
    start_time = time.time()
    entity_context = "Processing..."
    state = "Processing"
    
    try:
        if entity_type == 'player':
            fbref_data = fbref_get_player(entity_name, competition, season)
            if fbref_data:
                entity_context = fbref_data.get('team', 'Unknown')
        else:
            fbref_data = fbref_get_team(entity_name, competition, season)
            if fbref_data:
                entity_context = competition

        if not fbref_data:
            return False, {}, entity_context, "Failed - No FBref data"

        # Merge Understat data for domestic/extras leagues
        if table_type in ['domestic', 'extras']:
            if entity_type == 'player':
                # Pass team_name to disambiguate players with similar names
                team_name_for_matching = fbref_data.get('team')
                understat_data = understat_get_player(entity_name, competition, season,
                                                      team_name=team_name_for_matching)
            else:
                understat_data = understat_get_team(entity_name, competition, season)

            if understat_data:
                for key, value in understat_data.items():
                    if key.startswith('understat_'):
                        fbref_data[key] = value
                    else:
                        fbref_data[f"understat_{key}"] = value

        # Enrich players with Transfermarkt profile data
        if entity_type == 'player':
            birth_year = fbref_data.get('birth_year')
            transfermarkt_data = transfermarkt_get_player(entity_name, competition, season, birth_year=birth_year)

            if transfermarkt_data:
                for key, value in transfermarkt_data.items():
                    fbref_data[key] = value

        cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, entity_type)
        cleaned_data['data_quality_score'] = quality_score
        cleaned_data['processing_warnings'] = warnings
        
        response_time = time.time() - start_time
        
        return True, cleaned_data, entity_context, f"Success ({response_time:.1f}s)"
        
    except Exception as e:
        response_time = time.time() - start_time
        return False, {}, "Error", f"Failed: {str(e)[:30]}..."

def load_entities(entity_type: str, competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Load entities with parallel processing and checkpoint support."""
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total': 0, 'successful': 0, 'failed': 0, 'avg_metrics': 0}
    
    checkpoint_mgr = CheckpointManager(competition, season, f"{entity_type}s")
    rate_limiter = AdaptiveRateLimit()

    try:
        db.clear_season_data(competition, season, table_type, f'{entity_type}s')

        players_list_df = fbref_get_league_players(competition, season)

        # Flatten MultiIndex columns if present
        if hasattr(players_list_df.columns, 'levels'):
            players_list_df.columns = [col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in players_list_df.columns]

        if players_list_df.empty:
            return stats

        if entity_type == 'player':
            unique_entities = players_list_df['player'].dropna().unique().tolist()
        else:
            unique_entities = players_list_df['team'].dropna().unique().tolist()

        stats['total'] = len(unique_entities)

        checkpoint = checkpoint_mgr.load_progress()
        processed_entities = []
        start_index = 0

        if checkpoint:
            processed_entities = checkpoint['processed_entities']
            start_index = checkpoint['current_index']
            stats.update(checkpoint['stats'])
            logger.phase_start(f"RESUMING {entity_type.title()}s", len(unique_entities))
            print(f"Resuming from entity {start_index + 1}/{len(unique_entities)}")
        else:
            logger.phase_start(entity_type.title() + 's', len(unique_entities))

        remaining_entities = unique_entities[start_index:]
        total_metrics = 0
        max_workers = LOAD_CONFIG['parallel_workers']
        checkpoint_interval = LOAD_CONFIG['checkpoint_interval']
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_size = max_workers * 2

            for batch_start in range(0, len(remaining_entities), batch_size):
                batch_end = min(batch_start + batch_size, len(remaining_entities))
                batch_entities = remaining_entities[batch_start:batch_end]

                batch_args = [(entity, entity_type, competition, season, validator, table_type)
                            for entity in batch_entities]

                future_to_entity = {
                    executor.submit(process_single_entity, args): args[0]
                    for args in batch_args
                }

                for future in as_completed(future_to_entity):
                    entity_name = future_to_entity[future]
                    current_index = start_index + len(processed_entities) + 1

                    try:
                        success, cleaned_data, entity_context, state = future.result()

                        if success and cleaned_data:
                            if entity_type == 'player':
                                insert_success = db.insert_player_data(cleaned_data, table_type)
                            else:
                                insert_success = db.insert_team_data(cleaned_data, table_type)

                            if insert_success:
                                stats['successful'] += 1
                                total_metrics += len(cleaned_data)
                                processed_entities.append(entity_name)
                                rate_limiter.record_request(1.0, True)
                            else:
                                stats['failed'] += 1
                                rate_limiter.record_request(1.0, False)
                        else:
                            stats['failed'] += 1
                            rate_limiter.record_request(1.0, False)

                        elapsed_time = time.time() - start_time
                        if current_index > start_index:
                            avg_time_per_entity = elapsed_time / (current_index - start_index)
                            remaining_entities_count = len(unique_entities) - current_index
                            eta_seconds = int(remaining_entities_count * avg_time_per_entity)
                        else:
                            eta_seconds = None
                        
                        avg_metrics = total_metrics // max(stats['successful'], 1) if stats['successful'] > 0 else 0
                        logger.progress_update(
                            current_index, len(unique_entities), entity_name, avg_metrics,
                            stats['failed'], entity_type.title(), entity_context, state, eta_seconds
                        )
                        
                        if len(processed_entities) % checkpoint_interval == 0:
                            checkpoint_mgr.save_progress(processed_entities, stats, current_index)
                        
                        if LOAD_CONFIG['adaptive_rate_limiting']:
                            rate_limiter.wait()
                    
                    except Exception as e:
                        stats['failed'] += 1
                        logger.error(f"Error processing {entity_name}: {e}")
                        continue
        
        logger.progress_complete(stats['total'])
        stats['avg_metrics'] = total_metrics // max(stats['successful'], 1) if stats['successful'] > 0 else 0
        
        checkpoint_mgr.clear_checkpoint()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in load_entities: {e}")
        # Save progress so the load can be resumed
        checkpoint_mgr.save_progress(processed_entities if 'processed_entities' in locals() else [], stats, start_index)
        return stats

def load_players(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Load players using unified entity loading logic."""
    return load_entities('player', competition, season, table_type, logger)

def load_teams(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Load teams using unified entity loading logic."""
    return load_entities('team', competition, season, table_type, logger)

def load_complete_competition(competition: str, season: str) -> Dict[str, Dict[str, int]]:
    """Load all players and teams for a single competition into PostgreSQL."""
    table_type = 'domestic'
    for comp, ttype in AVAILABLE_COMPETITIONS:
        if comp == competition:
            table_type = ttype
            break
    
    if table_type == 'european':
        data_source = "FBref only"
    else:
        data_source = "FBref + Understat"
    
    logger = LogManager()
    logger.header(competition, season, data_source)
    
    player_stats = load_players(competition, season, table_type, logger)
    team_stats = load_teams(competition, season, table_type, logger)
    
    understat_coverage = None
    if table_type in ['domestic', 'extras']:
        understat_coverage = {'players': 0, 'teams': 0}
    
    summary_stats = {
        'players': player_stats,
        'teams': team_stats,
        'understat_coverage': understat_coverage
    }
    
    logger.final_summary(summary_stats)
    
    return {'players': player_stats, 'teams': team_stats}

def load_competition_block(block_competitions: List[Tuple[str, str]], block_name: str, season: str) -> Dict[str, Dict[str, Dict[str, int]]]:
    """Load multiple competitions sequentially with random anti-ban pauses between them."""
    logger = LogManager()
    logger.massive_header_block(block_name, season, len(block_competitions))
    
    all_stats = {}
    start_time = datetime.now()
    
    for i, (competition, table_type) in enumerate(block_competitions, 1):
        data_source = "FBref only" if table_type == 'european' else "FBref + Understat"
        
        logger.competition_start(i, len(block_competitions), competition, data_source)
        
        try:
            player_stats = load_players(competition, season, table_type, logger)
            team_stats = load_teams(competition, season, table_type, logger)
            
            competition_stats = {'players': player_stats, 'teams': team_stats}
            all_stats[competition] = competition_stats
            
            logger.competition_summary(competition_stats, competition)
            
            if i < len(block_competitions):
                next_competition = block_competitions[i][0]
                pause_minutes = random.randint(LOAD_CONFIG['block_pause_min'], LOAD_CONFIG['block_pause_max'])
                logger.block_league_pause(
                    i, len(block_competitions), 
                    next_competition, 
                    pause_minutes
                )
            
        except Exception as e:
            print(f"ERROR: Failed to process {competition}: {e}")
            all_stats[competition] = {
                'players': {'total': 0, 'successful': 0, 'failed': 0}, 
                'teams': {'total': 0, 'successful': 0, 'failed': 0}
            }
            continue
    
    total_time = int((datetime.now() - start_time).total_seconds())
    logger.block_summary(all_stats, total_time, block_name)
    
    return all_stats

def main():
    """Interactive CLI menu for data loading, schema setup, and DB management."""
    print("FootballDecoded Data Loader")
    print("═" * 50)
    print("\n1. Load competition data (players + teams)")
    print("2. Load Block 1: ENG + ESP + ITA")
    print("3. Load Block 2: GER + FRA + Champions")
    print("4. Load Extras (POR, NED, BEL, TUR, SCO, SUI, USA)")
    print("5. Test database connection")
    print("6. Setup database schema")
    print("7. Clear all existing data")
    print("8. Check database status")

    choice = input("\nSelect option (1-8): ").strip()
    
    if choice == "1":
        print("\nAvailable competitions:")
        all_competitions = BLOCK_1_COMPETITIONS + BLOCK_2_COMPETITIONS + BLOCK_3_EXTRAS
        for i, (comp_name, comp_type) in enumerate(all_competitions, 1):
            data_source = "FBref + Understat" if comp_type in ['domestic', 'extras'] else "FBref only"
            print(f"   {i}. {comp_name} ({data_source})")
        
        try:
            comp_choice = int(input(f"\nSelect competition (1-{len(all_competitions)}): ").strip())
            if 1 <= comp_choice <= len(all_competitions):
                selected_competition, _ = all_competitions[comp_choice - 1]
                season = input("Enter season (e.g., 24-25): ").strip()
                
                if season:
                    load_complete_competition(selected_competition, season)
                else:
                    print("Invalid season format")
            else:
                print("Invalid competition selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "2":
        season = input("Enter season for Block 1 load (e.g., 24-25): ").strip()
        if season:
            print(f"\nBLOCK 1 LOAD CONFIGURATION")
            print("═" * 50)
            print(f"Season: {season}")
            print("Competitions: ENG-Premier League, ESP-La Liga, ITA-Serie A")
            print(f"Random pauses: {LOAD_CONFIG['block_pause_min']}-{LOAD_CONFIG['block_pause_max']} minutes between leagues")
            
            avg_pause = (LOAD_CONFIG['block_pause_min'] + LOAD_CONFIG['block_pause_max']) / 2
            estimated_hours = (avg_pause * (len(BLOCK_1_COMPETITIONS) - 1)) / 60
            estimated_hours += 1.5
            print(f"Estimated duration: {estimated_hours:.1f} hours")
            print(f"IP safety: Random timing approach")
            print()
            
            confirm = input(f"Proceed with Block 1 load? (y/N): ").strip().lower()
            if confirm == 'y':
                print(f"\nStarting Block 1 load for {season}...")
                print("IMPORTANT: Random pauses between leagues (10-20 min)")
                print()
                
                load_competition_block(BLOCK_1_COMPETITIONS, "Block 1", season)
            else:
                print("Block 1 load cancelled")
        else:
            print("Invalid season format")
    
    elif choice == "3":
        season = input("Enter season for Block 2 load (e.g., 24-25): ").strip()
        if season:
            print(f"\nBLOCK 2 LOAD CONFIGURATION")
            print("═" * 50)
            print(f"Season: {season}")
            print("Competitions: GER-Bundesliga, FRA-Ligue 1, INT-Champions League")
            print(f"Random pauses: {LOAD_CONFIG['block_pause_min']}-{LOAD_CONFIG['block_pause_max']} minutes between leagues")
            
            avg_pause = (LOAD_CONFIG['block_pause_min'] + LOAD_CONFIG['block_pause_max']) / 2
            estimated_hours = (avg_pause * (len(BLOCK_2_COMPETITIONS) - 1)) / 60
            estimated_hours += 1.5
            print(f"Estimated duration: {estimated_hours:.1f} hours")
            print(f"IP safety: Random timing approach")
            print()
            
            confirm = input(f"Proceed with Block 2 load? (y/N): ").strip().lower()
            if confirm == 'y':
                print(f"\nStarting Block 2 load for {season}...")
                print("IMPORTANT: Random pauses between leagues (10-20 min)")
                print()
                
                load_competition_block(BLOCK_2_COMPETITIONS, "Block 2", season)
            else:
                print("Block 2 load cancelled")
        else:
            print("Invalid season format")
    
    elif choice == "4":
        season = input("Enter season for Extras load (e.g., 24-25): ").strip()
        if season:
            print(f"\nEXTRAS LOAD CONFIGURATION")
            print("═" * 50)
            print(f"Season: {season}")
            print("Competitions: POR-Primeira Liga, NED-Eredivisie, BEL-Pro League")
            print("             TUR-Süper Lig, SCO-Premiership, SUI-Super League, USA-MLS")
            print(f"Data sources: FBref + Understat")
            print(f"Random pauses: {LOAD_CONFIG['block_pause_min']}-{LOAD_CONFIG['block_pause_max']} minutes between leagues")

            avg_pause = (LOAD_CONFIG['block_pause_min'] + LOAD_CONFIG['block_pause_max']) / 2
            estimated_hours = (avg_pause * (len(BLOCK_3_EXTRAS) - 1)) / 60
            estimated_hours += 2.0
            print(f"Estimated duration: {estimated_hours:.1f} hours")
            print(f"IP safety: Random timing approach")
            print()

            confirm = input(f"Proceed with Extras load? (y/N): ").strip().lower()
            if confirm == 'y':
                print(f"\nStarting Extras load for {season}...")
                print("IMPORTANT: Random pauses between leagues (10-20 min)")
                print()

                load_competition_block(BLOCK_3_EXTRAS, "Extras", season)
            else:
                print("Extras load cancelled")
        else:
            print("Invalid season format")

    elif choice == "5":
        print("\nTesting database connection...")
        try:
            from database.connection import test_connection
            success = test_connection()
            status = "successful" if success else "failed"
            print(f"Database connection {status}")
        except Exception as e:
            print(f"Connection test error: {e}")

    elif choice == "6":
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

    elif choice == "7":
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
                    conn.execute(text("DELETE FROM footballdecoded.players_extras"))
                    conn.execute(text("DELETE FROM footballdecoded.teams_extras"))
                
                print("All data cleared successfully")
                db.close()
            except Exception as e:
                print(f"Failed to clear data: {e}")
        else:
            print("Clear operation cancelled")
    
    elif choice == "8":
        print("\nChecking database status...")
        try:
            from database.database_checker import check_database_status
            check_database_status(verbose=True)
        except ImportError:
            print("database_checker.py not found")
        except Exception as e:
            print(f"Error checking database: {e}")

    else:
        print("Invalid option. Please select 1-8.")


if __name__ == "__main__":
    main()