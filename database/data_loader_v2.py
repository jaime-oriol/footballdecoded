"""FootballDecoded v2 Data Loader.

Pipeline: FotMob bulk -> Understat merge (Big 5) -> Transfermarkt enrich.
Schema: footballdecoded_v2 (players, teams, understat_team_matches, understat_shots).

Usage:
    python data_loader_v2.py       # Interactive menu
    Option 1: Single league        # ~15 min for Big 5, ~5 min for others
    Option 2-4: Block load         # Multiple leagues with pauses
    Option 5: Test DB connection
    Option 6: Setup v2 schema
    Option 7: Clear all v2 data
    Option 8: Check v2 DB status
"""

import sys
import os
import re
import json
import time
import random
import hashlib
import pickle
import unicodedata
import logging
import warnings
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=UserWarning, module='lxml')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('tls_requests').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.WARNING)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrappers import FotMob, Understat
from scrappers._config import LEAGUE_DICT
from wrappers import (
    understat_get_player, understat_get_team,
    understat_get_team_advanced,
    transfermarkt_get_player,
    fotmob_get_league_players, fotmob_get_league_teams,
)
from database.connection import DatabaseManager, get_db_manager

UNDERSTAT_LEAGUES = {
    'ENG-Premier League', 'ESP-La Liga', 'ITA-Serie A',
    'GER-Bundesliga', 'FRA-Ligue 1',
}

AVAILABLE_COMPETITIONS = [
    'ENG-Premier League',
    'ESP-La Liga',
    'ITA-Serie A',
    'GER-Bundesliga',
    'FRA-Ligue 1',
    'INT-Champions League',
    'POR-Primeira Liga',
    'NED-Eredivisie',
    'BEL-Pro League',
    'TUR-Süper Lig',
    'SCO-Premiership',
    'SUI-Super League',
    'USA-MLS',
]

BLOCK_1 = ['ENG-Premier League', 'ESP-La Liga', 'ITA-Serie A']
BLOCK_2 = ['GER-Bundesliga', 'FRA-Ligue 1', 'INT-Champions League']
BLOCK_3 = ['POR-Primeira Liga', 'NED-Eredivisie', 'BEL-Pro League',
           'TUR-Süper Lig', 'SCO-Premiership', 'SUI-Super League', 'USA-MLS']

LOAD_CONFIG = {
    'block_pause_min': 10,
    'block_pause_max': 20,
    'progress_bar_width': 40,
    'line_width': 80,
    'parallel_workers': 3,
    'checkpoint_interval': 25,
    'checkpoint_dir': '.checkpoints_v2',
    'min_delay': 0.5,
    'max_delay': 3.0,
    'initial_delay': 1.0,
}

class CheckpointManager:
    """Save/restore progress for crash recovery. Expires after 24h."""

    def __init__(self, competition: str, season: str, entity_type: str):
        """Initialize checkpoint for a specific competition/season/entity combination."""
        self.checkpoint_dir = Path(LOAD_CONFIG['checkpoint_dir'])
        self.checkpoint_dir.mkdir(exist_ok=True)
        safe_name = competition.replace(' ', '_').replace('-', '_')
        self.checkpoint_file = self.checkpoint_dir / f"{safe_name}_{season}_{entity_type}_v2.pkl"

    def save_progress(self, processed: List[str], stats: Dict, current_index: int):
        """Persist current progress to disk for crash recovery."""
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump({
                    'processed': processed,
                    'stats': stats,
                    'current_index': current_index,
                    'timestamp': datetime.now(),
                }, f)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_progress(self) -> Optional[Dict]:
        """Load previous progress if checkpoint exists and is <24h old."""
        try:
            if not self.checkpoint_file.exists():
                return None
            with open(self.checkpoint_file, 'rb') as f:
                data = pickle.load(f)
            if datetime.now() - data['timestamp'] > timedelta(days=1):
                return None
            return data
        except Exception:
            return None

    def clear(self):
        """Delete checkpoint file after successful completion."""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
        except Exception:
            pass


class AdaptiveRateLimit:
    """Adjusts delay between API calls based on response times."""

    def __init__(self):
        """Initialize with default delay from config."""
        self.current_delay = LOAD_CONFIG['initial_delay']
        self.min_delay = LOAD_CONFIG['min_delay']
        self.max_delay = LOAD_CONFIG['max_delay']
        self.response_times = []
        self.lock = Lock()
        self.consecutive_failures = 0

    def record(self, response_time: float, success: bool):
        """Adjust delay based on response time (rolling window of 10)."""
        with self.lock:
            if success:
                self.response_times.append(response_time)
                self.consecutive_failures = 0
                if len(self.response_times) > 10:
                    self.response_times.pop(0)
                avg = sum(self.response_times) / len(self.response_times)
                if avg < 1.0:
                    self.current_delay = max(self.min_delay, self.current_delay * 0.9)
                elif avg > 3.0:
                    self.current_delay = min(self.max_delay, self.current_delay * 1.2)
            else:
                self.consecutive_failures += 1
                mult = 1.5 ** min(self.consecutive_failures, 3)
                self.current_delay = min(self.max_delay, self.current_delay * mult)

    def wait(self):
        """Sleep for the current adaptive delay."""
        time.sleep(self.current_delay)


class IDGenerator:
    """Generate deterministic 16-char hex IDs via SHA256 hash."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text: lowercase, strip accents, remove special chars."""
        if not text or pd.isna(text):
            return ""
        text = str(text).lower().strip()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text).strip('_')
        return re.sub(r'_+', '_', text)

    @staticmethod
    def player_id(name: str, birth_year: Optional[int], nationality: Optional[str]) -> str:
        """SHA256(name + birth_year + nationality) -> 16-char hex."""
        n = IDGenerator.normalize(name)
        b = str(birth_year) if birth_year else "unknown"
        nat = IDGenerator.normalize(nationality) if nationality else "unknown"
        return hashlib.sha256(f"{n}_{b}_{nat}".encode()).hexdigest()[:16]

    @staticmethod
    def team_id(team_name: str, league: str) -> str:
        """SHA256(team_name + league) -> 16-char hex."""
        t = IDGenerator.normalize(team_name)
        l = IDGenerator.normalize(league)
        return hashlib.sha256(f"{t}_{l}".encode()).hexdigest()[:16]


class DataNormalizer:
    """Name normalization for consistent storage."""

    def normalize_name(self, name: str) -> str:
        """Lowercase, strip accents, title case."""
        if not name or pd.isna(name):
            return ""
        name = str(name)
        # Extract value if a pandas Series was accidentally stringified
        if '\n' in name and 'dtype: object' in name:
            for line in name.split('\n'):
                if 'Name:' not in line and 'dtype:' not in line and line.strip():
                    name = line.strip()
                    break
        name = name.lower().strip()
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        name = re.sub(r'[^\w\s\-\.]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name.title()


class LogManager:
    """Terminal output with progress bar and ETA display."""

    def __init__(self):
        """Initialize timing state and terminal width."""
        self.start_time = None
        self.phase_start_time = None
        self.line_width = LOAD_CONFIG['line_width']
        self.current_lines = 0

    def header(self, competition: str, season: str, data_sources: str):
        """Print pipeline header."""
        print("FootballDecoded v2 Data Loader")
        print("=" * self.line_width)
        print(f"Competition: {competition} {season} ({data_sources})")
        print(f"Schema: footballdecoded_v2")
        print("-" * self.line_width)
        print()
        self.start_time = datetime.now()

    def block_header(self, block_name: str, season: str, num: int):
        """Print block load header (multiple leagues)."""
        print(f"FootballDecoded v2 {block_name} Loader")
        print("=" * self.line_width)
        print(f"Season: {season} | {block_name} ({num} leagues)")
        print(f"Pauses: {LOAD_CONFIG['block_pause_min']}-{LOAD_CONFIG['block_pause_max']} min between leagues")
        print("-" * self.line_width)
        print()
        self.start_time = datetime.now()

    def competition_start(self, num: int, total: int, competition: str, sources: str):
        """Print start of individual competition within a block."""
        print(f"[{num}/{total}] {competition.upper()}")
        print(f"Sources: {sources}")
        print("-" * 50)

    def phase_start(self, phase: str, total: int):
        """Print start of a loading phase (players, teams, etc)."""
        self.phase_start_time = datetime.now()
        self.current_lines = 0
        print(f"{phase.upper()}")
        print(f"Found: {total:,} -> Processing")
        print()

    def progress(self, current: int, total: int, name: str, failed: int,
                 entity_type: str, state: str, eta_seconds: Optional[int] = None):
        """Update in-place progress bar with ETA."""
        if self.current_lines > 0:
            for _ in range(self.current_lines):
                print("\033[1A\033[K", end="")

        pct = (current / total) * 100
        filled = int(LOAD_CONFIG['progress_bar_width'] * current // total)
        bar = '\033[42m' + ' ' * filled + '\033[0m' + '░' * (LOAD_CONFIG['progress_bar_width'] - filled)

        eta = ""
        if eta_seconds and eta_seconds > 0:
            if eta_seconds < 60:
                eta = f" | ETA: {eta_seconds}s"
            elif eta_seconds < 3600:
                eta = f" | ETA: {eta_seconds // 60}m {eta_seconds % 60}s"
            else:
                eta = f" | ETA: {eta_seconds // 3600}h {(eta_seconds % 3600) // 60}m"

        lines = [
            f"Progress: [{bar}] {current}/{total} ({pct:.1f}%){eta}",
            f"  {entity_type}: {name}",
            f"  State: {state} | Failed: {failed}",
        ]
        for line in lines:
            print(line)
        self.current_lines = len(lines)
        if current < total:
            print(end="", flush=True)

    def progress_complete(self, total: int):
        """Print final 100% progress bar with elapsed time for the phase."""
        if self.current_lines > 0:
            for _ in range(self.current_lines):
                print("\033[1A\033[K", end="")
        bar = '\033[42m' + ' ' * LOAD_CONFIG['progress_bar_width'] + '\033[0m'
        print(f"Progress: [{bar}] {total}/{total} (100%)")
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            print(f"  Completed in: {self._fmt_time(int(elapsed))}")
        print()
        self.current_lines = 0

    def summary(self, stats: Dict):
        """Print final summary with counts and success rate."""
        print("-" * self.line_width)
        print("SUMMARY")
        print("-" * self.line_width)
        p = stats.get('players', {})
        t = stats.get('teams', {})
        m = stats.get('matches', {})
        s = stats.get('shots', {})
        total = p.get('successful', 0) + t.get('successful', 0)
        failed = p.get('failed', 0) + t.get('failed', 0)
        rate = (total / (total + failed) * 100) if (total + failed) > 0 else 0
        print(f"Players: {p.get('successful', 0)}/{p.get('total', 0)} | Teams: {t.get('successful', 0)}/{t.get('total', 0)}")
        print(f"Matches: {m.get('successful', 0)} | Shots: {s.get('successful', 0)}")
        print(f"Success rate: {rate:.1f}%")
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"Time: {self._fmt_time(int(elapsed))}")
        print("=" * self.line_width)

    def block_pause(self, current: int, total: int, next_league: str, minutes: int):
        """Countdown timer between leagues in block load."""
        print("-" * self.line_width)
        print(f"PAUSE: {minutes} min before {next_league} ({total - current} remaining)")
        print("-" * self.line_width)
        for m in range(minutes, 0, -1):
            print(f"\rResuming in: {m} min...", end="", flush=True)
            time.sleep(60)
        print(f"\rResuming now...                  ")
        print()

    def block_summary(self, all_stats: Dict, total_time: int, block_name: str):
        """Print summary for entire block of leagues."""
        print("-" * self.line_width)
        print(f"{block_name.upper()} SUMMARY")
        print("-" * self.line_width)
        total_p = sum(s.get('players', {}).get('successful', 0) for s in all_stats.values())
        total_t = sum(s.get('teams', {}).get('successful', 0) for s in all_stats.values())
        total_m = sum(s.get('matches', {}).get('successful', 0) for s in all_stats.values())
        total_s = sum(s.get('shots', {}).get('successful', 0) for s in all_stats.values())
        print(f"Players: {total_p} | Teams: {total_t} | Matches: {total_m} | Shots: {total_s}")
        print(f"Time: {self._fmt_time(total_time)}")
        for comp, stats in all_stats.items():
            p_ok = stats.get('players', {}).get('successful', 0)
            t_ok = stats.get('teams', {}).get('successful', 0)
            print(f"  {comp}: {p_ok} players, {t_ok} teams")
        print("=" * self.line_width)

    def _fmt_time(self, seconds: int) -> str:
        """Format seconds as human-readable duration string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _has_understat(league: str) -> bool:
    """Check if league has Understat coverage (Big 5 only)."""
    return league in UNDERSTAT_LEAGUES


def _parse_season(season: str, league: str) -> str:
    """Convert user season input (e.g. '25-26') to DB format (e.g. '2526')."""
    from scrappers._common import SeasonCode
    sc = SeasonCode.from_leagues([league])
    return sc.parse(season)


def load_players(competition: str, season: str, log: LogManager, db: DatabaseManager) -> Dict[str, int]:
    """Load players: FotMob bulk -> Understat merge (Big 5) -> Transfermarkt enrich -> DB."""
    normalizer = DataNormalizer()
    rate_limiter = AdaptiveRateLimit()
    parsed_season = _parse_season(season, competition)
    stats = {'total': 0, 'successful': 0, 'failed': 0}

    try:
        db.clear_season_data_v2(competition, parsed_season, 'players')
    except Exception as e:
        logger.warning(f"Could not clear existing player data: {e}")

    try:
        players_df = fotmob_get_league_players(competition, season)
        teams_df = fotmob_get_league_teams(competition, season)
    except Exception as e:
        logger.error(f"Failed to get FotMob data for {competition} {season}: {e}")
        return stats

    if players_df is None or players_df.empty:
        logger.warning(f"No FotMob players found for {competition} {season}")
        return stats

    # FotMob players only have numeric team_id, need name lookup
    team_id_to_name = {}
    if teams_df is not None and not teams_df.empty:
        for _, trow in teams_df.iterrows():
            tid = trow.get('fotmob_id') or trow.get('fotmob_team_id')
            tname = trow.get('name', '')
            if tid is not None and pd.notna(tid) and tname:
                team_id_to_name[int(tid)] = str(tname)

    stats['total'] = len(players_df)
    log.phase_start(f"Players ({competition})", len(players_df))

    checkpoint = CheckpointManager(competition, season, 'players')
    prev = checkpoint.load_progress()
    processed = prev['processed'] if prev else []
    start_idx = prev['current_index'] if prev else 0
    if prev:
        stats.update(prev['stats'])

    start_time = time.time()

    for i, (_, row) in enumerate(players_df.iterrows()):
        if i < start_idx:
            continue

        player_name = row.get('name', '')
        if not player_name or player_name in processed:
            continue

        t0 = time.time()

        try:
            fotmob_team_id = row.get('fotmob_team_id')
            team_name = 'Unknown'
            if fotmob_team_id is not None and pd.notna(fotmob_team_id):
                team_name = team_id_to_name.get(int(fotmob_team_id), 'Unknown')

            record = {
                'player_name': player_name,
                'league': competition,
                'season': parsed_season,
                'team': team_name,
                'fotmob_name': player_name,
                'fotmob_id': int(row['fotmob_id']) if pd.notna(row.get('fotmob_id')) else None,
            }

            skip_cols = {'name', 'league', 'season', 'fotmob_id', 'fotmob_team_id'}
            for col in row.index:
                if col in skip_cols:
                    continue
                val = row[col]
                if pd.notna(val):
                    record[col] = val if not hasattr(val, 'item') else val.item()

            if _has_understat(competition):
                try:
                    us_data = understat_get_player(player_name, competition, season,
                                                    team_name=team_name if team_name != 'Unknown' else None)
                    if us_data:
                        record['understat_name'] = us_data.get('official_player_name', player_name)
                        record['understat_id'] = us_data.get('understat_player_id')
                        if team_name == 'Unknown' and us_data.get('team'):
                            record['team'] = us_data['team']
                        for k, v in us_data.items():
                            if k.startswith('understat_'):
                                record[k] = v
                except Exception as e:
                    logger.debug(f"Understat merge failed for {player_name}: {e}")

            birth_year = record.get('birth_year')
            try:
                tm_data = transfermarkt_get_player(player_name, competition, season, birth_year=birth_year)
                if tm_data:
                    record['transfermarkt_id'] = str(tm_data.get('transfermarkt_player_id', ''))
                    # Transfermarkt positions are more granular than FotMob
                    tm_position = tm_data.get('transfermarkt_position_specific')
                    if tm_position:
                        record['position'] = tm_position
                    for k, v in tm_data.items():
                        record[k] = v
            except Exception as e:
                logger.debug(f"Transfermarkt enrich failed for {player_name}: {e}")

            record['normalized_name'] = normalizer.normalize_name(player_name)
            record['unique_player_id'] = IDGenerator.player_id(
                player_name, record.get('birth_year'), record.get('nationality')
            )
            record['data_quality_score'] = 1.0
            record['processing_warnings'] = []

            db.insert_player_v2(record)
            stats['successful'] += 1
            processed.append(player_name)
            rate_limiter.record(time.time() - t0, True)
            state = f"OK ({time.time() - t0:.1f}s)"

        except Exception as e:
            stats['failed'] += 1
            rate_limiter.record(time.time() - t0, False)
            state = f"FAIL: {str(e)[:30]}"
            logger.debug(f"Failed to process player {player_name}: {e}")

        elapsed = time.time() - start_time
        done = i - start_idx + 1
        eta = int((stats['total'] - i - 1) * (elapsed / max(done, 1)))
        log.progress(i + 1, stats['total'], player_name, stats['failed'], 'Player', state, eta)

        if len(processed) % LOAD_CONFIG['checkpoint_interval'] == 0:
            checkpoint.save_progress(processed, stats, i + 1)

        rate_limiter.wait()

    log.progress_complete(stats['total'])
    checkpoint.clear()
    return stats


def load_teams(competition: str, season: str, log: LogManager, db: DatabaseManager) -> Dict[str, int]:
    """Load teams: FotMob bulk -> Understat basic + advanced merge (Big 5) -> DB."""
    normalizer = DataNormalizer()
    rate_limiter = AdaptiveRateLimit()
    parsed_season = _parse_season(season, competition)
    stats = {'total': 0, 'successful': 0, 'failed': 0}

    try:
        db.clear_season_data_v2(competition, parsed_season, 'teams')
    except Exception as e:
        logger.warning(f"Could not clear existing team data: {e}")

    try:
        teams_df = fotmob_get_league_teams(competition, season)
    except Exception as e:
        logger.error(f"Failed to get FotMob teams for {competition} {season}: {e}")
        return stats

    if teams_df is None or teams_df.empty:
        logger.warning(f"No FotMob teams found for {competition} {season}")
        return stats

    stats['total'] = len(teams_df)
    log.phase_start(f"Teams ({competition})", len(teams_df))

    start_time = time.time()

    for i, (_, row) in enumerate(teams_df.iterrows()):
        team_name = row.get('name', '')
        if not team_name:
            stats['failed'] += 1
            continue

        t0 = time.time()

        try:
            record = {
                'team_name': team_name,
                'league': competition,
                'season': parsed_season,
            }

            for col in row.index:
                val = row[col]
                if col in ('name', 'league', 'season'):
                    continue
                if pd.notna(val):
                    record[col] = val if not hasattr(val, 'item') else val.item()

            record['fotmob_name'] = team_name
            record['fotmob_id'] = row.get('fotmob_id')

            if _has_understat(competition):
                try:
                    us_data = understat_get_team(team_name, competition, season)
                    if us_data:
                        record['understat_name'] = us_data.get('official_team_name', team_name)
                        for k, v in us_data.items():
                            if k.startswith('understat_'):
                                record[k] = v
                except Exception as e:
                    logger.debug(f"Understat merge failed for team {team_name}: {e}")

                try:
                    adv_data = understat_get_team_advanced(team_name, competition, season)
                    if adv_data:
                        for k, v in adv_data.items():
                            record[k] = v
                except Exception as e:
                    logger.debug(f"Understat advanced merge failed for team {team_name}: {e}")

            record['normalized_name'] = normalizer.normalize_name(team_name)
            record['unique_team_id'] = IDGenerator.team_id(team_name, competition)
            record['data_quality_score'] = 1.0
            record['processing_warnings'] = []

            db.insert_team_v2(record)
            stats['successful'] += 1
            rate_limiter.record(time.time() - t0, True)
            state = f"OK ({time.time() - t0:.1f}s)"

        except Exception as e:
            stats['failed'] += 1
            rate_limiter.record(time.time() - t0, False)
            state = f"FAIL: {str(e)[:30]}"
            logger.debug(f"Failed to process team {team_name}: {e}")

        elapsed = time.time() - start_time
        done = i + 1
        eta = int((stats['total'] - done) * (elapsed / max(done, 1)))
        log.progress(done, stats['total'], team_name, stats['failed'], 'Team', state, eta)
        rate_limiter.wait()

    log.progress_complete(stats['total'])
    return stats


def load_understat_matches(competition: str, season: str, log: LogManager, db: DatabaseManager) -> Dict[str, int]:
    """Load Understat match-level team stats (xG, PPDA, deep completions). Big 5 only.
    Each match produces 2 records (home + away).
    """
    if not _has_understat(competition):
        return {'successful': 0, 'failed': 0}

    parsed_season = _parse_season(season, competition)
    stats = {'successful': 0, 'failed': 0}

    try:
        db.clear_season_data_v2(competition, parsed_season, 'understat_team_matches')
    except Exception:
        pass

    try:
        us = Understat(leagues=[competition], seasons=[season])
        match_stats = us.read_team_match_stats()
    except Exception as e:
        logger.error(f"Failed to get Understat match stats: {e}")
        return stats

    if match_stats is None or match_stats.empty:
        return stats

    match_stats = match_stats.reset_index()
    print(f"Loading {len(match_stats)} match records...")

    for _, row in match_stats.iterrows():
        try:
            home_team = row.get('home_team', '')
            away_team = row.get('away_team', '')
            game_id = row.get('game_id')
            match_date = row.get('date')

            home_record = {
                'unique_team_id': IDGenerator.team_id(home_team, competition),
                'team_name': home_team,
                'league': competition,
                'season': parsed_season,
                'match_id': int(game_id),
                'match_date': match_date,
                'opponent': away_team,
                'is_home': True,
                'goals': row.get('home_goals'),
                'goals_against': row.get('away_goals'),
                'xg': row.get('home_xg'),
                'xg_against': row.get('away_xg'),
                'np_xg': row.get('home_np_xg'),
                'np_xg_against': row.get('away_np_xg'),
                'ppda': row.get('home_ppda'),
                'ppda_against': row.get('away_ppda'),
                'deep_completions': row.get('home_deep_completions'),
                'deep_completions_against': row.get('away_deep_completions'),
                'points': row.get('home_points'),
                'expected_points': row.get('home_expected_points'),
                'np_xg_difference': row.get('home_np_xg_difference'),
            }
            hg = home_record.get('goals') or 0
            ag = home_record.get('goals_against') or 0
            home_record['result'] = 'W' if hg > ag else ('D' if hg == ag else 'L')

            db.insert_team_match_v2(home_record)
            stats['successful'] += 1

            away_record = {
                'unique_team_id': IDGenerator.team_id(away_team, competition),
                'team_name': away_team,
                'league': competition,
                'season': parsed_season,
                'match_id': int(game_id),
                'match_date': match_date,
                'opponent': home_team,
                'is_home': False,
                'goals': row.get('away_goals'),
                'goals_against': row.get('home_goals'),
                'xg': row.get('away_xg'),
                'xg_against': row.get('home_xg'),
                'np_xg': row.get('away_np_xg'),
                'np_xg_against': row.get('home_np_xg'),
                'ppda': row.get('away_ppda'),
                'ppda_against': row.get('home_ppda'),
                'deep_completions': row.get('away_deep_completions'),
                'deep_completions_against': row.get('home_deep_completions'),
                'points': row.get('away_points'),
                'expected_points': row.get('away_expected_points'),
                'np_xg_difference': row.get('away_np_xg_difference'),
            }
            ag2 = away_record.get('goals') or 0
            hg2 = away_record.get('goals_against') or 0
            away_record['result'] = 'W' if ag2 > hg2 else ('D' if ag2 == hg2 else 'L')

            db.insert_team_match_v2(away_record)
            stats['successful'] += 1

        except Exception as e:
            stats['failed'] += 1
            logger.debug(f"Failed to insert match record: {e}")

    print(f"  Loaded {stats['successful']} match records ({stats['failed']} failed)")
    return stats


def load_understat_shots(competition: str, season: str, log: LogManager, db: DatabaseManager) -> Dict[str, int]:
    """Bulk load Understat shot events (xG, coords, body part, situation). Big 5 only."""
    if not _has_understat(competition):
        return {'successful': 0, 'failed': 0}

    parsed_season = _parse_season(season, competition)
    stats = {'successful': 0, 'failed': 0}

    try:
        db.clear_season_data_v2(competition, parsed_season, 'understat_shots')
    except Exception:
        pass

    try:
        us = Understat(leagues=[competition], seasons=[season])
        shots_df = us.read_shot_events()
    except Exception as e:
        logger.error(f"Failed to get Understat shots: {e}")
        return stats

    if shots_df is None or shots_df.empty:
        return stats

    shots_df = shots_df.reset_index()
    print(f"Loading {len(shots_df)} shot events...")

    insert_records = []
    for _, row in shots_df.iterrows():
        try:
            insert_records.append({
                'league': competition,
                'season': parsed_season,
                'match_id': int(row.get('game_id', 0)),
                'shot_id': row.get('shot_id'),
                'team': row.get('team'),
                'player': row.get('player'),
                'player_id': row.get('player_id'),
                'assist_player': row.get('assist_player'),
                'minute': row.get('minute'),
                'xg': row.get('xg'),
                'location_x': row.get('location_x'),
                'location_y': row.get('location_y'),
                'body_part': row.get('body_part'),
                'situation': row.get('situation'),
                'result': row.get('result'),
            })
        except Exception:
            stats['failed'] += 1

    if insert_records:
        try:
            insert_df = pd.DataFrame(insert_records)
            db.insert_shots_v2(insert_df)
            stats['successful'] = len(insert_records)
        except Exception as e:
            logger.error(f"Failed to bulk insert shots: {e}")
            stats['failed'] = len(insert_records)

    print(f"  Loaded {stats['successful']} shots ({stats['failed']} failed)")
    return stats


def load_complete_competition(competition: str, season: str) -> Dict:
    """Load all data for a single competition: players, teams, matches, shots."""
    has_us = _has_understat(competition)
    sources = "FotMob + Understat + Transfermarkt" if has_us else "FotMob + Transfermarkt"

    log = LogManager()
    log.header(competition, season, sources)

    db = get_db_manager()

    player_stats = load_players(competition, season, log, db)
    team_stats = load_teams(competition, season, log, db)
    match_stats = load_understat_matches(competition, season, log, db)
    shot_stats = load_understat_shots(competition, season, log, db)

    all_stats = {
        'players': player_stats,
        'teams': team_stats,
        'matches': match_stats,
        'shots': shot_stats,
    }

    log.summary(all_stats)
    db.close()
    return all_stats


def load_competition_block(competitions: List[str], block_name: str, season: str) -> Dict:
    """Load multiple competitions sequentially with random pauses between them."""
    log = LogManager()
    log.block_header(block_name, season, len(competitions))

    all_stats = {}
    start_time = datetime.now()

    for i, competition in enumerate(competitions, 1):
        has_us = _has_understat(competition)
        sources = "FotMob + Understat + TM" if has_us else "FotMob + TM"
        log.competition_start(i, len(competitions), competition, sources)

        try:
            result = load_complete_competition(competition, season)
            all_stats[competition] = result
        except Exception as e:
            print(f"ERROR: Failed {competition}: {e}")
            all_stats[competition] = {
                'players': {'total': 0, 'successful': 0, 'failed': 0},
                'teams': {'total': 0, 'successful': 0, 'failed': 0},
                'matches': {'successful': 0, 'failed': 0},
                'shots': {'successful': 0, 'failed': 0},
            }

        if i < len(competitions):
            pause = random.randint(LOAD_CONFIG['block_pause_min'], LOAD_CONFIG['block_pause_max'])
            log.block_pause(i, len(competitions), competitions[i], pause)

    total_time = int((datetime.now() - start_time).total_seconds())
    log.block_summary(all_stats, total_time, block_name)
    return all_stats


def main():
    """Interactive CLI menu for data loading operations."""
    print("FootballDecoded v2 Data Loader")
    print("=" * 50)
    print("\n1. Load single competition")
    print("2. Load Block 1: ENG + ESP + ITA")
    print("3. Load Block 2: GER + FRA + Champions")
    print("4. Load Extras: POR, NED, BEL, TUR, SCO, SUI, USA")
    print("5. Test database connection")
    print("6. Setup v2 schema")
    print("7. Clear all v2 data")
    print("8. Check v2 database status")

    choice = input("\nSelect option (1-8): ").strip()

    if choice == "1":
        print("\nAvailable competitions:")
        for i, comp in enumerate(AVAILABLE_COMPETITIONS, 1):
            us = " + Understat" if _has_understat(comp) else ""
            print(f"  {i}. {comp} (FotMob{us} + TM)")

        try:
            idx = int(input(f"\nSelect (1-{len(AVAILABLE_COMPETITIONS)}): ").strip())
            if 1 <= idx <= len(AVAILABLE_COMPETITIONS):
                comp = AVAILABLE_COMPETITIONS[idx - 1]
                season = input("Enter season (e.g., 25-26): ").strip()
                if season:
                    load_complete_competition(comp, season)
                else:
                    print("Invalid season")
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")

    elif choice == "2":
        season = input("Enter season (e.g., 25-26): ").strip()
        if season:
            confirm = input("Proceed with Block 1 load? (y/N): ").strip().lower()
            if confirm == 'y':
                load_competition_block(BLOCK_1, "Block 1", season)
        else:
            print("Invalid season")

    elif choice == "3":
        season = input("Enter season (e.g., 25-26): ").strip()
        if season:
            confirm = input("Proceed with Block 2 load? (y/N): ").strip().lower()
            if confirm == 'y':
                load_competition_block(BLOCK_2, "Block 2", season)
        else:
            print("Invalid season")

    elif choice == "4":
        season = input("Enter season (e.g., 25-26): ").strip()
        if season:
            confirm = input("Proceed with Extras load? (y/N): ").strip().lower()
            if confirm == 'y':
                load_competition_block(BLOCK_3, "Extras", season)
        else:
            print("Invalid season")

    elif choice == "5":
        print("\nTesting database connection...")
        try:
            db = get_db_manager()
            print("Connection successful")
            db.close()
        except Exception as e:
            print(f"Connection failed: {e}")

    elif choice == "6":
        confirm = input("Setup v2 schema? (y/N): ").strip().lower()
        if confirm == 'y':
            try:
                db = get_db_manager()
                db.execute_sql_file('database/setup_v2.sql')
                print("v2 schema created successfully")
                db.close()
            except Exception as e:
                print(f"Schema setup failed: {e}")

    elif choice == "7":
        confirm = input("Clear ALL v2 data? (type 'YES'): ").strip()
        if confirm == "YES":
            try:
                from sqlalchemy import text
                db = get_db_manager()
                with db.engine.begin() as conn:
                    conn.execute(text("DELETE FROM footballdecoded_v2.understat_shots"))
                    conn.execute(text("DELETE FROM footballdecoded_v2.understat_team_matches"))
                    conn.execute(text("DELETE FROM footballdecoded_v2.players"))
                    conn.execute(text("DELETE FROM footballdecoded_v2.teams"))
                print("All v2 data cleared")
                db.close()
            except Exception as e:
                print(f"Failed: {e}")

    elif choice == "8":
        try:
            from database.database_checker_v2 import check_database_status
            check_database_status()
        except ImportError:
            print("database_checker_v2.py not found")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
