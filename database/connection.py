"""PostgreSQL connection manager with pooling, retry logic, and data validation.

Provides DatabaseManager for all DB operations: inserts (v1 + v2 schemas),
queries, season clearing, and transfer detection. Records are validated
before insertion, and metrics are split by prefix into JSONB columns.
"""

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from typing import Dict, Any
import json
import time
import logging
from functools import wraps

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator: retries failed DB operations with exponential backoff.

    Example: delay=1, backoff=2 -> waits 1s, 2s, 4s between retries.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff: delay * backoff^attempt
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")

            raise last_exception
        return wrapper
    return decorator

def validate_data_structure(data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """Validate a record before DB insertion. Checks required fields and unique ID format."""
    if not isinstance(data, dict):
        raise ValueError(f"Data must be a dictionary, got {type(data)}")

    if entity_type == 'player':
        required_fields = ['player_name', 'league', 'season', 'team']
    elif entity_type == 'team':
        required_fields = ['team_name', 'league', 'season']
    else:
        raise ValueError(f"Invalid entity_type: {entity_type}")

    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields for {entity_type}: {missing_fields}")

    unique_id_field = f'unique_{entity_type}_id'
    if not data.get(unique_id_field):
        raise ValueError(f"Missing {unique_id_field}")

    unique_id = data[unique_id_field]
    if not isinstance(unique_id, str) or len(unique_id) != 16:
        raise ValueError(f"Invalid {unique_id_field} format: must be 16-character string")

    try:
        int(unique_id, 16)
    except ValueError:
        raise ValueError(f"Invalid {unique_id_field}: must be hexadecimal")

    return data

class DatabaseConfig:
    """Database configuration loaded from .env environment variables."""

    def __init__(self):
        """Load connection credentials and pool settings from environment variables."""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'footballdecoded_dev')
        self.username = os.getenv('DB_USER', 'footballdecoded')
        self.password = os.getenv('DB_PASSWORD', '')
        self.echo = os.getenv('DB_ECHO', 'False').lower() == 'true'

        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        self.connect_timeout = int(os.getenv('DB_CONNECT_TIMEOUT', '10'))

    @property
    def connection_string(self) -> str:
        """Build SQLAlchemy PostgreSQL connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseManager:
    """Manages PostgreSQL connections, inserts, and queries for both v1 and v2 schemas."""

    def __init__(self):
        """Initialize with config; call connect() to create the engine."""
        self.config = DatabaseConfig()
        self.engine = None

    @retry_on_failure(max_retries=3, delay=2.0)
    def connect(self) -> bool:
        """Create connection pool and verify DB is reachable."""
        try:
            logger.info(f"Connecting to database: {self.config.host}:{self.config.port}/{self.config.database}")

            self.engine = create_engine(
                self.config.connection_string,
                echo=self.config.echo,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                connect_args={
                    'connect_timeout': self.config.connect_timeout
                }
            )

            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                if test_value != 1:
                    raise ConnectionError("Database connection test failed")

            logger.info("Database connection successful")
            return True

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def execute_sql_file(self, filepath: str) -> bool:
        """Execute a SQL file within a single transaction. Returns True on success."""
        try:
            logger.info(f"Executing SQL file: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            with self.engine.begin() as conn:
                conn.execute(text(sql_content))
            
            logger.info(f"SQL file executed successfully: {filepath}")
            return True
            
        except FileNotFoundError:
            logger.error(f"SQL file not found: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Failed to execute SQL file {filepath}: {e}")
            return False
    
    def _serialize_for_json(self, obj):
        """Recursively convert numpy/pandas types to JSON-serializable Python natives."""
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_player_data(self, player_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insert player into v1 schema (footballdecoded.players_{table_type}).

        Splits flat dict into: basic columns + fbref_metrics JSONB + understat_metrics JSONB + transfermarkt_metrics JSONB.
        """
        try:
            validated_data = validate_data_structure(player_data, 'player')
            logger.debug(f"Inserting player: {validated_data.get('player_name')} in {table_type}")

            table_name = f"footballdecoded.players_{table_type}"

            if table_type in ['domestic', 'extras']:
                basic_fields = ['unique_player_id', 'player_name', 'league', 'season', 'team', 'nationality',
                            'position', 'age', 'birth_year', 'fbref_official_name',
                            'understat_official_name', 'transfermarkt_official_name', 'normalized_name', 'teams_played',
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            else:  # european schema uses 'competition' column
                basic_fields = ['unique_player_id', 'player_name', 'competition', 'season', 'team', 'nationality',
                            'position', 'age', 'birth_year', 'fbref_official_name',
                            'transfermarkt_official_name', 'normalized_name', 'teams_played',
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']

            processed_data = validated_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']

            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}

            # Non-basic, non-prefixed keys are FBref metrics by elimination
            fbref_metrics = {k: v for k, v in processed_data.items()
                        if k not in basic_fields and not k.startswith('understat_') and not k.startswith('transfermarkt_')}
            understat_metrics = {k: v for k, v in processed_data.items() if k.startswith('understat_')}
            transfermarkt_metrics = {k: v for k, v in processed_data.items() if k.startswith('transfermarkt_')}

            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))

            if table_type in ['domestic', 'extras']:
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))

            if transfermarkt_metrics:
                basic_data['transfermarkt_metrics'] = json.dumps(self._serialize_for_json(transfermarkt_metrics))

            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded',
                    if_exists='append', index=False, method='multi')

            logger.debug(f"Successfully inserted player: {validated_data.get('player_name')}")
            return True

        except Exception as e:
            logger.error(f"Failed to insert player data: {e}")
            raise

    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_team_data(self, team_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insert team into v1 schema (footballdecoded.teams_{table_type}).

        Splits flat dict into: basic columns + fbref_metrics JSONB + understat_metrics JSONB.
        """
        try:
            validated_data = validate_data_structure(team_data, 'team')
            logger.debug(f"Inserting team: {validated_data.get('team_name')} in {table_type}")

            table_name = f"footballdecoded.teams_{table_type}"

            if table_type in ['domestic', 'extras']:
                basic_fields = ['unique_team_id', 'team_name', 'league', 'season', 'normalized_name',
                               'fbref_official_name', 'understat_official_name']
            else:  # european schema uses 'competition' column
                basic_fields = ['unique_team_id', 'team_name', 'competition', 'season', 'normalized_name',
                               'fbref_official_name']

            processed_data = validated_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']

            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items()
                           if k not in basic_fields and not k.startswith('understat_')}

            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))

            # Only domestic tables have understat_metrics column (Big 5 coverage)
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in validated_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))

            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded',
                     if_exists='append', index=False, method='multi')

            logger.debug(f"Successfully inserted team: {validated_data.get('team_name')}")
            return True

        except Exception as e:
            logger.error(f"Failed to insert team data: {e}")
            raise
        
    @retry_on_failure(max_retries=2, delay=1.0)
    def clear_season_data(self, competition: str, season: str, table_type: str, entity_type: str) -> int:
        """Delete all v1 records for a competition+season. Returns number of deleted rows."""
        try:
            from scrappers._common import SeasonCode

            logger.info(f"Clearing {entity_type} data for {competition} {season} ({table_type})")

            season_code = SeasonCode.from_leagues([competition])
            parsed_season = season_code.parse(season)

            table_name = f"footballdecoded.{entity_type}_{table_type}"
            league_field = 'competition' if table_type == 'european' else 'league'

            with self.engine.begin() as conn:
                query = f"DELETE FROM {table_name} WHERE {league_field} = :league AND season = :season"
                result = conn.execute(
                    text(query), 
                    {'league': competition, 'season': parsed_season}
                )
                deleted_count = result.rowcount
                
            logger.info(f"Cleared {deleted_count} {entity_type} records for {competition} {season}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear season data: {e}")
            raise
    
    def get_transfers_by_unique_id(self, table_type: str = 'domestic') -> pd.DataFrame:
        """Find players who played for multiple teams in the same season (transfers)."""
        try:
            if table_type == 'domestic':
                query = """
                SELECT 
                    unique_player_id,
                    player_name,
                    league,
                    season,
                    COUNT(DISTINCT team) as teams_count,
                    STRING_AGG(DISTINCT team, ' -> ' ORDER BY team) as teams_path,
                    AVG(data_quality_score) as avg_quality
                FROM footballdecoded.players_domestic
                GROUP BY unique_player_id, player_name, league, season
                HAVING COUNT(DISTINCT team) > 1
                ORDER BY teams_count DESC
                """
            else:
                query = """
                SELECT 
                    unique_player_id,
                    player_name,
                    competition as league,
                    season,
                    COUNT(DISTINCT team) as teams_count,
                    STRING_AGG(DISTINCT team, ' -> ' ORDER BY team) as teams_path,
                    AVG(data_quality_score) as avg_quality
                FROM footballdecoded.players_european
                GROUP BY unique_player_id, player_name, competition, season
                HAVING COUNT(DISTINCT team) > 1
                ORDER BY teams_count DESC
                """
            
            return pd.read_sql(query, self.engine)
            
        except Exception:
            return pd.DataFrame()
    
    def get_entity_by_unique_id(self, unique_id: str, entity_type: str, table_type: str = 'domestic') -> pd.DataFrame:
        """Get all records for a specific unique ID (tracks player/team across seasons)."""
        try:
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            id_field = f"unique_{entity_type}_id"
            
            query = f"SELECT * FROM {table_name} WHERE {id_field} = :unique_id ORDER BY season DESC, team"
            
            return pd.read_sql(query, self.engine, params={'unique_id': unique_id})
            
        except Exception:
            return pd.DataFrame()
    
    def query_players(self, league: str = None, season: str = None, team: str = None, table_type: str = 'domestic') -> pd.DataFrame:
        """Query v1 players with optional league/season/team filters."""
        try:
            table_name = f"footballdecoded.players_{table_type}"
            league_field = 'competition' if table_type == 'european' else 'league'
            
            query = f"SELECT * FROM {table_name} WHERE 1=1"
            params = {}
            
            if league:
                query += f" AND {league_field} = %(league)s"
                params['league'] = league
            if season:
                query += " AND season = %(season)s"  
                params['season'] = season
            if team:
                query += " AND team = %(team)s"
                params['team'] = team
                
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception:
            return pd.DataFrame()
    
    def get_data_quality_summary(self) -> pd.DataFrame:
        """Get data quality summary view (v1 schema)."""
        try:
            query = "SELECT * FROM footballdecoded.data_quality_summary ORDER BY table_name"
            return pd.read_sql(query, self.engine)
        except Exception:
            return pd.DataFrame()
    
    def get_unique_entities_count(self) -> Dict[str, int]:
        """Count distinct unique IDs across all v1 tables."""
        try:
            counts = {}
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_domestic", 
                self.engine
            )
            counts['unique_domestic_players'] = result.iloc[0]['count']
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_european", 
                self.engine
            )
            counts['unique_european_players'] = result.iloc[0]['count']
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_domestic", 
                self.engine
            )
            counts['unique_domestic_teams'] = result.iloc[0]['count']
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_european", 
                self.engine
            )
            counts['unique_european_teams'] = result.iloc[0]['count']
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_extras", 
                self.engine
            )
            counts['unique_extras_players'] = result.iloc[0]['count']
            
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_extras", 
                self.engine
            )
            counts['unique_extras_teams'] = result.iloc[0]['count']
            
            return counts
            
        except Exception:
            return {}
    
    # --- V2 methods (footballdecoded_v2 schema) ---
    # Flat dicts are split by prefix (fotmob_*, understat_*, transfermarkt_*) into JSONB columns.

    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_player_v2(self, player_data: Dict[str, Any]) -> bool:
        """Insert player into footballdecoded_v2.players.

        Splits flat dict into scalar columns + fotmob/understat/transfermarkt JSONB.
        """
        try:
            validated_data = validate_data_structure(player_data, 'player')

            basic_fields = [
                'unique_player_id', 'player_name', 'normalized_name',
                'league', 'season', 'team', 'nationality', 'position',
                'age', 'birth_year', 'fotmob_id', 'fotmob_name',
                'understat_id', 'understat_name', 'transfermarkt_id',
                'data_quality_score', 'processing_warnings',
            ]

            basic_data = {k: v for k, v in validated_data.items() if k in basic_fields}

            fotmob_metrics = {k: v for k, v in validated_data.items() if k.startswith('fotmob_') and k not in basic_fields}
            understat_metrics = {k: v for k, v in validated_data.items() if k.startswith('understat_') and k not in basic_fields}
            transfermarkt_metrics = {k: v for k, v in validated_data.items() if k.startswith('transfermarkt_') and k not in basic_fields}

            basic_data['fotmob_metrics'] = json.dumps(self._serialize_for_json(fotmob_metrics)) if fotmob_metrics else None
            basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics)) if understat_metrics else None
            basic_data['transfermarkt_metrics'] = json.dumps(self._serialize_for_json(transfermarkt_metrics)) if transfermarkt_metrics else None

            df = pd.DataFrame([basic_data])
            df.to_sql('players', self.engine, schema='footballdecoded_v2',
                      if_exists='append', index=False, method='multi')
            return True

        except Exception as e:
            logger.error(f"Failed to insert v2 player: {e}")
            raise

    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_team_v2(self, team_data: Dict[str, Any]) -> bool:
        """Insert team into footballdecoded_v2.teams.

        Splits flat dict into scalar columns + fotmob/understat/understat_advanced JSONB.
        understat_adv_* keys go into a separate understat_advanced column (~200 keys).
        """
        try:
            validated_data = validate_data_structure(team_data, 'team')

            basic_fields = [
                'unique_team_id', 'team_name', 'normalized_name',
                'league', 'season', 'fotmob_id', 'fotmob_name',
                'understat_name', 'data_quality_score', 'processing_warnings',
            ]

            basic_data = {k: v for k, v in validated_data.items() if k in basic_fields}

            fotmob_metrics = {k: v for k, v in validated_data.items() if k.startswith('fotmob_') and k not in basic_fields}
            understat_metrics = {k: v for k, v in validated_data.items()
                                 if k.startswith('understat_') and not k.startswith('understat_adv_') and k not in basic_fields}
            understat_advanced = {k: v for k, v in validated_data.items() if k.startswith('understat_adv_')}

            basic_data['fotmob_metrics'] = json.dumps(self._serialize_for_json(fotmob_metrics)) if fotmob_metrics else None
            basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics)) if understat_metrics else None
            basic_data['understat_advanced'] = json.dumps(self._serialize_for_json(understat_advanced)) if understat_advanced else None

            df = pd.DataFrame([basic_data])
            df.to_sql('teams', self.engine, schema='footballdecoded_v2',
                      if_exists='append', index=False, method='multi')
            return True

        except Exception as e:
            logger.error(f"Failed to insert v2 team: {e}")
            raise

    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_team_match_v2(self, match_data: Dict[str, Any]) -> bool:
        """Insert single team-match record into footballdecoded_v2.understat_team_matches."""
        try:
            df = pd.DataFrame([match_data])
            df.to_sql('understat_team_matches', self.engine, schema='footballdecoded_v2',
                      if_exists='append', index=False, method='multi')
            return True
        except Exception as e:
            logger.error(f"Failed to insert v2 team match: {e}")
            raise

    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_shots_v2(self, shots_df: pd.DataFrame) -> bool:
        """Bulk insert shot events into footballdecoded_v2.understat_shots."""
        try:
            if shots_df.empty:
                return True
            shots_df.to_sql('understat_shots', self.engine, schema='footballdecoded_v2',
                            if_exists='append', index=False, method='multi')
            return True
        except Exception as e:
            logger.error(f"Failed to insert v2 shots: {e}")
            raise

    @retry_on_failure(max_retries=2, delay=1.0)
    def clear_season_data_v2(self, league: str, season: str, entity_type: str) -> int:
        """Delete all v2 records for a specific league+season.

        Args:
            league: League code (e.g. 'ESP-La Liga')
            season: Parsed season (e.g. '2526')
            entity_type: Table name: 'players', 'teams', 'understat_team_matches', 'understat_shots'
        """
        try:
            table_name = f"footballdecoded_v2.{entity_type}"
            with self.engine.begin() as conn:
                result = conn.execute(
                    text(f"DELETE FROM {table_name} WHERE league = :league AND season = :season"),
                    {'league': league, 'season': season}
                )
                deleted = result.rowcount
            logger.info(f"Cleared {deleted} {entity_type} records for {league} {season}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear v2 season data: {e}")
            raise

    def close(self):
        """Dispose the engine and close all pooled connections."""
        if self.engine:
            self.engine.dispose()


def get_db_manager() -> DatabaseManager:
    """Create a connected DatabaseManager instance (convenience function)."""
    db = DatabaseManager()
    if db.connect():
        return db
    else:
        raise ConnectionError("Failed to connect to database")

def setup_database() -> bool:
    """Connect and execute the v1 schema setup SQL file."""
    db = DatabaseManager()
    if db.connect():
        return db.execute_sql_file('database/setup.sql')
    return False

def test_connection() -> bool:
    """Verify DB connectivity by querying players and counting entities."""
    try:
        db = get_db_manager()
        
        result = db.query_players()
        
        unique_counts = db.get_unique_entities_count()
        
        db.close()
        return True
        
    except Exception:
        return False

if __name__ == "__main__":
    test_connection()