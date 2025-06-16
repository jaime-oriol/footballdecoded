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
        """Execute SQL file."""
        try:
            with open(filepath, 'r') as file:
                sql_content = file.read()
            
            with self.engine.connect() as conn:
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        conn.execute(text(statement))
                        
                conn.commit()
            
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
        """Insert player data with unique ID system."""
        try:
            table_name = f"footballdecoded.players_{table_type}"
            
            # Define basic fields with unique ID
            if table_type == 'domestic':
                basic_fields = ['unique_player_id', 'player_name', 'league', 'season', 'team', 
                              'nationality', 'position', 'age', 'birth_year', 'fbref_official_name', 
                              'understat_official_name', 'normalized_name', 'teams_played', 
                              'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            else:  # european
                basic_fields = ['unique_player_id', 'player_name', 'competition', 'season', 'team', 
                              'nationality', 'position', 'age', 'birth_year', 'fbref_official_name', 
                              'normalized_name', 'teams_played', 'data_quality_score', 
                              'processing_warnings', 'is_transfer', 'transfer_count']
            
            # Map league -> competition for European tables
            processed_data = player_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Validate unique ID exists
            if 'unique_player_id' not in processed_data:
                print(f"Error: Missing unique_player_id for player {processed_data.get('player_name', 'Unknown')}")
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
        """Insert team data with unique ID system."""
        try:
            table_name = f"footballdecoded.teams_{table_type}"
            
            # Define basic fields with unique ID
            if table_type == 'domestic':
                basic_fields = ['unique_team_id', 'team_name', 'league', 'season', 'normalized_name', 
                              'fbref_official_name', 'understat_official_name', 'data_quality_score', 
                              'processing_warnings']
            else:  # european
                basic_fields = ['unique_team_id', 'team_name', 'competition', 'season', 'normalized_name', 
                              'fbref_official_name', 'data_quality_score', 'processing_warnings']
            
            # Map league -> competition for European tables
            processed_data = team_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Validate unique ID exists
            if 'unique_team_id' not in processed_data:
                print(f"Error: Missing unique_team_id for team {processed_data.get('team_name', 'Unknown')}")
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
    
    def get_player_transfers(self, unique_player_id: str, league: str = None, season: str = None) -> pd.DataFrame:
        """Get all records for a player across teams (transfers)."""
        try:
            base_query = """
            SELECT * FROM footballdecoded.players_domestic 
            WHERE unique_player_id = :player_id
            """
            params = {'player_id': unique_player_id}
            
            if league:
                base_query += " AND league = :league"
                params['league'] = league
            if season:
                base_query += " AND season = :season"
                params['season'] = season
                
            base_query += " ORDER BY team"
            
            domestic_df = pd.read_sql(base_query, self.engine, params=params)
            
            # Check European table too
            european_query = base_query.replace('footballdecoded.players_domestic', 
                                              'footballdecoded.players_european')
            european_query = european_query.replace('league', 'competition')
            
            european_df = pd.read_sql(european_query, self.engine, params=params)
            
            # Combine results
            all_records = pd.concat([domestic_df, european_df], ignore_index=True)
            return all_records
            
        except Exception as e:
            print(f"Failed to get player transfers: {e}")
            return pd.DataFrame()
    
    def get_transfer_summary(self, league: str = None, season: str = None) -> pd.DataFrame:
        """Get summary of all transfers detected."""
        try:
            query = """
            SELECT 
                unique_player_id,
                player_name,
                league,
                season,
                COUNT(*) as teams_count,
                STRING_AGG(team, ' -> ' ORDER BY team) as transfer_path,
                AVG(data_quality_score) as avg_quality
            FROM footballdecoded.players_domestic
            WHERE 1=1
            """
            params = {}
            
            if league:
                query += " AND league = :league"
                params['league'] = league
            if season:
                query += " AND season = :season"
                params['season'] = season
                
            query += """
            GROUP BY unique_player_id, player_name, league, season
            HAVING COUNT(*) > 1
            ORDER BY teams_count DESC, player_name
            """
            
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            print(f"Failed to get transfer summary: {e}")
            return pd.DataFrame()
    
    def get_unique_entities_stats(self) -> Dict[str, int]:
        """Get statistics about unique entities in database."""
        try:
            stats = {}
            
            # Unique players in domestic leagues
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_domestic", 
                self.engine
            )
            stats['unique_domestic_players'] = result.iloc[0]['count']
            
            # Unique players in European competitions  
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_player_id) as count FROM footballdecoded.players_european", 
                self.engine
            )
            stats['unique_european_players'] = result.iloc[0]['count']
            
            # Unique teams in domestic leagues
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_domestic", 
                self.engine
            )
            stats['unique_domestic_teams'] = result.iloc[0]['count']
            
            # Unique teams in European competitions
            result = pd.read_sql(
                "SELECT COUNT(DISTINCT unique_team_id) as count FROM footballdecoded.teams_european", 
                self.engine
            )
            stats['unique_european_teams'] = result.iloc[0]['count']
            
            # Players with transfers (multiple teams)
            result = pd.read_sql("""
                SELECT COUNT(*) as count FROM (
                    SELECT unique_player_id 
                    FROM footballdecoded.players_domestic 
                    GROUP BY unique_player_id, league, season 
                    HAVING COUNT(DISTINCT team) > 1
                ) transfers
            """, self.engine)
            stats['players_with_transfers'] = result.iloc[0]['count']
            
            return stats
            
        except Exception as e:
            print(f"Failed to get unique entities stats: {e}")
            return {}
    
    def query_players(self, league: str = None, season: str = None, team: str = None, 
                     unique_id: str = None) -> pd.DataFrame:
        """Query players with optional filters including unique ID."""
        try:
            query = "SELECT * FROM footballdecoded.players_domestic WHERE 1=1"
            params = {}
            
            if unique_id:
                query += " AND unique_player_id = :unique_id"
                params['unique_id'] = unique_id
            if league:
                query += " AND league = :league"
                params['league'] = league
            if season:
                query += " AND season = :season"  
                params['season'] = season
            if team:
                query += " AND team = :team"
                params['team'] = team
                
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            print(f"Query failed: {e}")
            return pd.DataFrame()
    
    def query_teams(self, league: str = None, season: str = None, 
                   unique_id: str = None) -> pd.DataFrame:
        """Query teams with optional filters including unique ID."""
        try:
            query = "SELECT * FROM footballdecoded.teams_domestic WHERE 1=1"
            params = {}
            
            if unique_id:
                query += " AND unique_team_id = :unique_id"
                params['unique_id'] = unique_id
            if league:
                query += " AND league = :league"
                params['league'] = league
            if season:
                query += " AND season = :season"  
                params['season'] = season
                
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            print(f"Query failed: {e}")
            return pd.DataFrame()
    
    def verify_unique_ids_integrity(self) -> Dict[str, Any]:
        """Verify integrity of unique ID system."""
        try:
            integrity_check = {}
            
            # Check for duplicate unique_player_ids within same league/season/team
            result = pd.read_sql("""
                SELECT unique_player_id, league, season, team, COUNT(*) as duplicates
                FROM footballdecoded.players_domestic 
                GROUP BY unique_player_id, league, season, team
                HAVING COUNT(*) > 1
            """, self.engine)
            integrity_check['duplicate_player_records'] = len(result)
            
            # Check for missing unique IDs
            result = pd.read_sql("""
                SELECT COUNT(*) as count 
                FROM footballdecoded.players_domestic 
                WHERE unique_player_id IS NULL OR unique_player_id = ''
            """, self.engine)
            integrity_check['players_missing_id'] = result.iloc[0]['count']
            
            result = pd.read_sql("""
                SELECT COUNT(*) as count 
                FROM footballdecoded.teams_domestic 
                WHERE unique_team_id IS NULL OR unique_team_id = ''
            """, self.engine)
            integrity_check['teams_missing_id'] = result.iloc[0]['count']
            
            # Check ID length consistency (should be 16 chars)
            result = pd.read_sql("""
                SELECT COUNT(*) as count 
                FROM footballdecoded.players_domestic 
                WHERE LENGTH(unique_player_id) != 16
            """, self.engine)
            integrity_check['players_invalid_id_length'] = result.iloc[0]['count']
            
            return integrity_check
            
        except Exception as e:
            print(f"Failed to verify ID integrity: {e}")
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
    """Test database connection with unique ID system."""
    try:
        db = get_db_manager()
        print("Database connection test successful")
        
        # Test basic queries
        result = db.query_players()
        print(f"Found {len(result)} player records in database")
        
        # Test unique ID stats
        stats = db.get_unique_entities_stats()
        print(f"Unique players (domestic): {stats.get('unique_domestic_players', 0)}")
        print(f"Players with transfers: {stats.get('players_with_transfers', 0)}")
        
        # Test integrity
        integrity = db.verify_unique_ids_integrity()
        print(f"ID integrity check: {integrity}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()