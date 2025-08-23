# ====================================================================
# FootballDecoded Database Connection Manager
# ====================================================================
# 
# Gestiona conexiones robustas a PostgreSQL con sistema de IDs únicos.
# Incluye retry logic, timeouts configurables, y validación de datos.
#
# Características principales:
# - Conexiones con pool y timeout configurables
# - Retry automático con exponential backoff  
# - Validación de estructura de datos antes de inserción
# - Logging detallado de operaciones y errores
# - Soporte para inserción masiva de datos
#
# ====================================================================

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json
import time
import logging
from functools import wraps

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ====================================================================
# RETRY AND TIMEOUT UTILITIES
# ====================================================================

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator para reintentar operaciones fallidas con backoff exponencial."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # No delay en el último intento
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def validate_data_structure(data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """Validación básica de estructura de datos antes de inserción."""
    if not isinstance(data, dict):
        raise ValueError(f"Data must be a dictionary, got {type(data)}")
    
    # Campos requeridos según tipo de entidad
    if entity_type == 'player':
        required_fields = ['player_name', 'league', 'season', 'team']
    elif entity_type == 'team':
        required_fields = ['team_name', 'league', 'season']
    else:
        raise ValueError(f"Invalid entity_type: {entity_type}")
    
    # Verificar campos requeridos
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields for {entity_type}: {missing_fields}")
    
    # Validar que los IDs únicos existan
    unique_id_field = f'unique_{entity_type}_id'
    if not data.get(unique_id_field):
        raise ValueError(f"Missing {unique_id_field}")
    
    # Validar formato de ID único (debe ser hexadecimal de 16 caracteres)
    unique_id = data[unique_id_field]
    if not isinstance(unique_id, str) or len(unique_id) != 16:
        raise ValueError(f"Invalid {unique_id_field} format: must be 16-character string")
    
    try:
        int(unique_id, 16)  # Verificar que es hexadecimal válido
    except ValueError:
        raise ValueError(f"Invalid {unique_id_field}: must be hexadecimal")
    
    return data

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
        
        # Configuración de timeouts y performance
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # segundos
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hora
        self.connect_timeout = int(os.getenv('DB_CONNECT_TIMEOUT', '10'))  # segundos
        
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
        
    @retry_on_failure(max_retries=3, delay=2.0)
    def connect(self) -> bool:
        """Establecer conexión a la base de datos con retry automático."""
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
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                if test_value != 1:
                    raise ConnectionError("Database connection test failed")
            
            logger.info("Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise  # Re-raise to let retry decorator handle it
    
    def execute_sql_file(self, filepath: str) -> bool:
        """
        Ejecutar archivo SQL con manejo de statements multi-línea.
        
        Args:
            filepath: Ruta al archivo SQL a ejecutar
            
        Returns:
            bool: True si la ejecución fue exitosa
            
        Raises:
            FileNotFoundError: Si el archivo SQL no existe
            SQLAlchemyError: Si hay errores en la ejecución SQL
        """
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
        """
        Convertir tipos numpy/pandas a tipos serializables JSON.
        
        Maneja la conversión recursiva de estructuras complejas con tipos
        numpy/pandas que no son directamente serializables a JSON.
        
        Args:
            obj: Objeto a serializar (puede ser dict, list, numpy array, etc.)
            
        Returns:
            Objeto serializable a JSON (int, float, bool, str, list, dict, None)
        """
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
        """Insertar datos de jugador con validación y retry automático."""
        try:
            # Validar datos antes de insertar
            validated_data = validate_data_structure(player_data, 'player')
            logger.debug(f"Inserting player: {validated_data.get('player_name')} in {table_type}")
            
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
            
            # Procesar datos para estructura de BD
            processed_data = validated_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Separar datos básicos de métricas
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                        if k not in basic_fields and not k.startswith('understat_')}
            
            # Serializar métricas a JSON
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            # Añadir métricas de Understat si es liga doméstica
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in processed_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            # Insertar en base de datos
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                    if_exists='append', index=False, method='multi')
            
            logger.debug(f"Successfully inserted player: {validated_data.get('player_name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert player data: {e}")
            raise  # Re-raise to let retry decorator handle it
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def insert_team_data(self, team_data: Dict[str, Any], table_type: str = 'domestic') -> bool:
        """Insertar datos de equipo con validación y retry automático."""
        try:
            # Validar datos antes de insertar
            validated_data = validate_data_structure(team_data, 'team')
            logger.debug(f"Inserting team: {validated_data.get('team_name')} in {table_type}")
            
            table_name = f"footballdecoded.teams_{table_type}"
            
            if table_type == 'domestic':
                basic_fields = ['unique_team_id', 'team_name', 'league', 'season', 'normalized_name', 
                               'fbref_official_name', 'understat_official_name']
            else:
                basic_fields = ['unique_team_id', 'team_name', 'competition', 'season', 'normalized_name', 
                               'fbref_official_name']
            
            # Procesar datos para estructura de BD
            processed_data = validated_data.copy()
            if table_type == 'european' and 'league' in processed_data:
                processed_data['competition'] = processed_data['league']
            
            # Separar datos básicos de métricas
            basic_data = {k: v for k, v in processed_data.items() if k in basic_fields}
            fbref_metrics = {k: v for k, v in processed_data.items() 
                           if k not in basic_fields and not k.startswith('understat_')}
            
            # Serializar métricas a JSON
            basic_data['fbref_metrics'] = json.dumps(self._serialize_for_json(fbref_metrics))
            
            # Añadir métricas de Understat si es liga doméstica
            if table_type == 'domestic':
                understat_metrics = {k: v for k, v in validated_data.items() if k.startswith('understat_')}
                basic_data['understat_metrics'] = json.dumps(self._serialize_for_json(understat_metrics))
            
            # Insertar en base de datos
            df = pd.DataFrame([basic_data])
            df.to_sql(table_name.split('.')[1], self.engine, schema='footballdecoded', 
                     if_exists='append', index=False, method='multi')
            
            logger.debug(f"Successfully inserted team: {validated_data.get('team_name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert team data: {e}")
            raise  # Re-raise to let retry decorator handle it
        
    @retry_on_failure(max_retries=2, delay=1.0)
    def clear_season_data(self, competition: str, season: str, table_type: str, entity_type: str) -> int:
        """Limpiar datos existentes para una competición y temporada específica."""
        try:
            from scrappers._common import SeasonCode
            
            logger.info(f"Clearing {entity_type} data for {competition} {season} ({table_type})")
            
            # Parsear temporada
            season_code = SeasonCode.from_leagues([competition])
            parsed_season = season_code.parse(season)
            
            # Construir nombre de tabla y campo de liga
            table_name = f"footballdecoded.{entity_type}_{table_type}"
            league_field = 'competition' if table_type == 'european' else 'league'
            
            # Ejecutar eliminación en transacción
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