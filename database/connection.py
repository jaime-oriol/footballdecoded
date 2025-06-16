# ====================================================================
# FootballDecoded Database Connection Manager - Sistema de IDs Únicos
# ====================================================================

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

load_dotenv()

# ====================================================================
# DATABASE CONFIGURATION
# ====================================================================

class DatabaseConfig:
    """Database configuration from environment variables."""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'footballdecoded_dev')
        self.username = os.getenv('DB_USER', 'footballdecoded')
        self.password = os.getenv('DB_PASSWORD', '')
        self.echo = os.getenv('DB_ECHO', 'False').lower() == 'true'
        
    @property
    def connection_string(self) -> str:
        """SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

# ====================================================================
# DATABASE CONNECTION MANAGER
# ====================================================================

class DatabaseManager:
    """Manages database connections and operations with unique ID system."""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.engine = create_engine(
                self.config.connection_string,
                echo=self.config.echo,
                pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
                max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '10'))
            )
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("Database connection established")
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def execute_sql_file(self, filepath: str) -> bool:
        """Execute SQL file with proper handling of multi-line statements."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # Execute the entire file as one statement block
            with self.engine.begin() as conn:
                conn.execute(text(sql_content))
            
            print(f"SQL file executed successfully: {filepath}")
            return True
            
        except Exception as e:
            print(f"Failed to execute SQL file: {e}")
            return False
    
    def _serialize_for_json(self, obj):
        """Convert numpy/pandas types to JSON-serializable types."""
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, pd.Int64Dtype)):
            return int(obj)
        elif isinstance(obj, (np.floating, pd.Float64Dtype)):
            return float(obj)
        elif isinstance(obj, (np.bool_, pd.BooleanDtype)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def insert_player_data(self, player_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insert player data using unique ID system."""
        try:
            table_name = f"footballdecoded.players_{table_type}"
            
            # Basic fields with unique ID
            if table_type == 'domestic':
                basic_fields = ['unique_player_id', 'player_name', 'league', 'season', 'team', 'nationality', 
                            'position', 'age', 'birth_year', 'fbref_official_name', 
                            'understat_official_name', 'normalized_name', 'teams_played', 
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            else:  # european
                basic_fields = ['unique_player_id', 'player_name', 'competition', 'season', 'team', 'nationality', 
                            'position', 'age', 'birth_year', 'fbref_official_name', 
                            'normalized_name', 'teams_played', 
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            
            # Map league -> competition for European tables
            processed_data = player_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Validate unique_player_id exists
            if 'unique_player_id' not in processed_data:
                print(f"Error: unique_player_id missing for player {processed_data.get('player_name', 'Unknown')}")
                return False
            
            # Separate data
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                        if k not in basic_fields and not k.startswith('understat_')}
            
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in processed_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            # Insert data
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                    if_exists='append', index=False, method='multi')
            
            return True
            
        except Exception as e:
            print(f"Failed to insert player data: {e}")
            return False
    
    def insert_team_data(self, team_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insert team data using unique ID system."""
        try:
            table_name = f"footballdecoded.teams_{table_type}"
            
            # Basic fields with unique ID
            if table_type == 'domestic':
                basic_fields = ['unique_team_id', 'team_name', 'league', 'season', 'normalized_name', 
                               'fbref_official_name', 'understat_official_name']
            else:  # european
                basic_fields = ['unique_team_id', 'team_name', 'competition', 'season', 'normalized_name', 
                               'fbref_official_name']
            
            # Map league -> competition for European tables
            processed_data = team_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Validate unique_team_id exists
            if 'unique_team_id' not in processed_data:
                print(f"Error: unique_team_id missing for team {processed_data.get('team_name', 'Unknown')}")
                return False
            
            # Separate data
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                           if k not in basic_fields and not k.startswith('understat_')}
            
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in team_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            # Insert data
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                     if_exists='append', index=False, method='multi')
            
            return True
            
        except Exception as e:
            print(f"Failed to insert team data: {e}")
            return False
        
    def clear_season_data(self, competition: str, season: str, table_type: str, entity_type: str) -> bool:
        """Clear existing data for a specific competition and season before reloading."""
        try:
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            league_field = 'competition' if table_type == 'european' else 'league'
            
            with self.engine.begin() as conn:
                query = f"DELETE FROM {table_name} WHERE {league_field} = :league AND season = :season"
                result = conn.execute(
                    text(query), 
                    {'league': competition, 'season': season}
                )
                
            print(f"Cleared {result.rowcount} existing records from {table_name}")
            return True
            
        except Exception as e:
            print(f"Failed to clear existing data: {e}")
            return False
    
    def get_transfers_by_unique_id(self, table_type: str = 'domestic') -> pd.DataFrame:
        """Get players with multiple teams using unique ID system."""
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
            
        except Exception as e:
            print(f"Failed to get transfers: {e}")
            return pd.DataFrame()
    
    def get_entity_by_unique_id(self, unique_id: str, entity_type: str, table_type: str = 'domestic') -> pd.DataFrame:
        """Get all records for a specific unique ID."""
        try:
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            id_field = f"unique_{entity_type}_id"
            
            query = f"SELECT * FROM {table_name} WHERE {id_field} = :unique_id ORDER BY season DESC, team"
            
            return pd.read_sql(query, self.engine, params={'unique_id': unique_id})
            
        except Exception as e:
            print(f"Failed to get entity by unique ID: {e}")
            return pd.DataFrame()
    
    def query_players(self, league: str = None, season: str = None, team: str = None) -> pd.DataFrame:
        """Query players with optional filters."""
        try:
            query = "SELECT * FROM footballdecoded.players_domestic WHERE 1=1"
            params = {}
            
            if league:
                query += " AND league = %(league)s"
                params['league'] = league
            if season:
                query += " AND season = %(season)s"  
                params['season'] = season
            if team:
                query += " AND team = %(team)s"
                params['team'] = team
                
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            print(f"Query failed: {e}")
            return pd.DataFrame()
    
    def get_data_quality_summary(self) -> pd.DataFrame:
        """Get comprehensive data quality summary."""
        try:
            query = "SELECT * FROM footballdecoded.data_quality_summary ORDER BY table_name"
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"Failed to get data quality summary: {e}")
            return pd.DataFrame()
    
    def get_unique_entities_count(self) -> Dict[str, int]:
        """Get count of unique entities using ID system."""
        try:
            counts = {}
            
            # Domestic players
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_domestic", 
                self.engine
            )
            counts['unique_domestic_players'] = result.iloc[0]['count']
            
            # European players
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_european", 
                self.engine
            )
            counts['unique_european_players'] = result.iloc[0]['count']
            
            # Domestic teams
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_domestic", 
                self.engine
            )
            counts['unique_domestic_teams'] = result.iloc[0]['count']
            
            # European teams
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_european", 
                self.engine
            )
            counts['unique_european_teams'] = result.iloc[0]['count']
            
            return counts
            
        except Exception as e:
            print(f"Failed to get unique entities count: {e}")
            return {}
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            print("Database connection closed")

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def get_db_manager() -> DatabaseManager:
    """Get configured database manager instance."""
    db = DatabaseManager()
    if db.connect():
        return db
    else:
        raise ConnectionError("Failed to connect to database")

def setup_database() -> bool:
    """Run initial database setup."""
    db = DatabaseManager()
    if db.connect():
        return db.execute_sql_file('database/setup.sql')
    return False

def test_connection():
    """Test database connection."""
    try:
        db = get_db_manager()
        print("Database connection test successful")
        
        result = db.query_players()
        print(f"Found {len(result)} players in database")
        
        # Test unique ID system
        unique_counts = db.get_unique_entities_count()
        print("Unique entities:", unique_counts)
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()