# ====================================================================
# FootballDecoded Database Connection Manager - FIXED
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
    """Manages database connections and operations."""
    
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
            
            # Test connection
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
        """Insert player data into appropriate table."""
        try:
            table_name = f"footballdecoded.players_{table_type}"
            
            # FIXED: Define basic fields correctly for each table type
            if table_type == 'domestic':
                basic_fields = ['player_name', 'league', 'season', 'team', 'nationality', 
                               'position', 'age', 'birth_year', 'fbref_official_name', 
                               'understat_official_name', 'normalized_name', 'teams_played', 
                               'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            else:  # european
                basic_fields = ['player_name', 'competition', 'season', 'team', 'nationality', 
                               'position', 'age', 'birth_year', 'fbref_official_name', 
                               'normalized_name', 'teams_played', 
                               'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            
            # FIXED: Map league -> competition for European tables
            processed_data = player_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
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
        """Insert team data into appropriate table."""
        try:
            table_name = f"footballdecoded.teams_{table_type}"
            
            # FIXED: Define basic fields correctly for each table type
            if table_type == 'domestic':
                basic_fields = ['team_name', 'league', 'season', 'normalized_name', 'fbref_official_name', 'understat_official_name']
            else:  # european
                basic_fields = ['team_name', 'competition', 'season', 'normalized_name', 'fbref_official_name']
            
            # FIXED: Map league -> competition for European tables
            processed_data = team_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
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
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()