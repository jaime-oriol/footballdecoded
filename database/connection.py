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
    """Configuración de base de datos desde variables de entorno."""
    
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
    """Gestiona conexiones y operaciones de base de datos con sistema de IDs únicos."""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        
    def connect(self) -> bool:
        """Establecer conexión a la base de datos."""
        try:
            self.engine = create_engine(
                self.config.connection_string,
                echo=self.config.echo,
                pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
                max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '10'))
            )
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True
            
        except Exception:
            return False
    
    def execute_sql_file(self, filepath: str) -> bool:
        """Ejecutar archivo SQL con manejo de statements multi-línea."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            with self.engine.begin() as conn:
                conn.execute(text(sql_content))
            
            return True
            
        except Exception:
            return False
    
    def _serialize_for_json(self, obj):
        """Convertir tipos numpy/pandas a tipos serializables JSON."""
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
        """Insertar datos de jugador usando sistema de IDs únicos."""
        try:
            table_name = f"footballdecoded.players_{table_type}"
            
            if table_type == 'domestic':
                basic_fields = ['unique_player_id', 'player_name', 'league', 'season', 'team', 'nationality', 
                            'position', 'age', 'birth_year', 'fbref_official_name', 
                            'understat_official_name', 'normalized_name', 'teams_played', 
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            else:
                basic_fields = ['unique_player_id', 'player_name', 'competition', 'season', 'team', 'nationality', 
                            'position', 'age', 'birth_year', 'fbref_official_name', 
                            'normalized_name', 'teams_played', 
                            'data_quality_score', 'processing_warnings', 'is_transfer', 'transfer_count']
            
            processed_data = player_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            if 'unique_player_id' not in processed_data:
                return False
            
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                        if k not in basic_fields and not k.startswith('understat_')}
            
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in processed_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                    if_exists='append', index=False, method='multi')
            
            return True
            
        except Exception:
            return False
    
    def insert_team_data(self, team_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insertar datos de equipo usando sistema de IDs únicos."""
        try:
            table_name = f"footballdecoded.teams_{table_type}"
            
            if table_type == 'domestic':
                basic_fields = ['unique_team_id', 'team_name', 'league', 'season', 'normalized_name', 
                               'fbref_official_name', 'understat_official_name']
            else:
                basic_fields = ['unique_team_id', 'team_name', 'competition', 'season', 'normalized_name', 
                               'fbref_official_name']
            
            processed_data = team_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            if 'unique_team_id' not in processed_data:
                return False
            
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                           if k not in basic_fields and not k.startswith('understat_')}
            
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in team_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                     if_exists='append', index=False, method='multi')
            
            return True
            
        except Exception:
            return False
        
    def clear_season_data(self, competition: str, season: str, table_type: str, entity_type: str) -> int:
        """Limpiar datos existentes para una competición y temporada específica."""
        try:
            # IMPORTAR SeasonCode para parsing consistente
            from scrappers._common import SeasonCode
            
            # PARSEAR temporada para consistencia con datos almacenados
            season_code = SeasonCode.from_leagues([competition])
            parsed_season = season_code.parse(season)  # "2023-24" → "2324"
            
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            league_field = 'competition' if table_type == 'european' else 'league'
            
            with self.engine.begin() as conn:
                query = f"DELETE FROM {table_name} WHERE {league_field} = :league AND season = :season"
                result = conn.execute(
                    text(query), 
                    {'league': competition, 'season': parsed_season}  # Usar parsed_season
                )
                
            return result.rowcount
            
        except Exception:
            return 0
    
    def get_transfers_by_unique_id(self, table_type: str = 'domestic') -> pd.DataFrame:
        """Obtener jugadores con múltiples equipos usando sistema de IDs únicos."""
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
        """Obtener todos los registros para un ID único específico."""
        try:
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            id_field = f"unique_{entity_type}_id"
            
            query = f"SELECT * FROM {table_name} WHERE {id_field} = :unique_id ORDER BY season DESC, team"
            
            return pd.read_sql(query, self.engine, params={'unique_id': unique_id})
            
        except Exception:
            return pd.DataFrame()
    
    def query_players(self, league: str = None, season: str = None, team: str = None) -> pd.DataFrame:
        """Consultar jugadores con filtros opcionales."""
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
            
        except Exception:
            return pd.DataFrame()
    
    def get_data_quality_summary(self) -> pd.DataFrame:
        """Obtener resumen completo de calidad de datos."""
        try:
            query = "SELECT * FROM footballdecoded.data_quality_summary ORDER BY table_name"
            return pd.read_sql(query, self.engine)
        except Exception:
            return pd.DataFrame()
    
    def get_unique_entities_count(self) -> Dict[str, int]:
        """Obtener conteo de entidades únicas usando sistema de IDs."""
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
            
            return counts
            
        except Exception:
            return {}
    
    def close(self):
        """Cerrar conexiones de base de datos."""
        if self.engine:
            self.engine.dispose()

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def get_db_manager() -> DatabaseManager:
    """Obtener instancia configurada del gestor de base de datos."""
    db = DatabaseManager()
    if db.connect():
        return db
    else:
        raise ConnectionError("Failed to connect to database")

def setup_database() -> bool:
    """Ejecutar configuración inicial de base de datos."""
    db = DatabaseManager()
    if db.connect():
        return db.execute_sql_file('database/setup.sql')
    return False

def test_connection() -> bool:
    """Probar conexión a base de datos."""
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