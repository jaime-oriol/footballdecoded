# ====================================================================
# FootballDecoded - FBref Optimized Data Extractor
# ====================================================================
"""
FBref Wrapper con funcionalidades avanzadas optimizadas:

CARACTERÍSTICAS PRINCIPALES:
- Sistema de caché inteligente con expiración automática
- Procesamiento paralelo para extracciones múltiples 
- Validación robusta de entradas con sugerencias
- Barras de progreso para operaciones largas
- Búsqueda automática de IDs de jugadores/equipos
- Integración optimizada con Understat

FUNCIONES PRINCIPALES:
- extract_data(): Extracción unificada de stats FBref
- extract_multiple(): Procesamiento paralelo de múltiples entidades
- get_player()/get_team(): Acceso rápido con caché
- get_players()/get_teams(): Procesamiento paralelo múltiple
- clear_cache(): Limpieza de caché local

USO TÍPICO:
    from wrappers import fbref_data
    
    # Extracción individual con caché
    player = fbref_data.get_player("Lionel Messi", "ESP-La Liga", "23-24")
    
    # Extracción múltiple con progreso
    players = fbref_data.get_players(
        ["Messi", "Benzema", "Lewandowski"], 
        "ESP-La Liga", "23-24", show_progress=True
    )
"""

import sys
import os
import pandas as pd
import warnings
import pickle
import hashlib
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import tqdm for progress bars, fallback to dummy if not available
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import FBref
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# INPUT VALIDATION SYSTEM
# ====================================================================

def _validate_inputs(entity_name: str, entity_type: str, league: str, season: str) -> bool:
    """
    Validar entradas de manera robusta.
    
    Args:
        entity_name: Nombre de entidad (jugador/equipo)
        entity_type: Tipo de entidad ('player' o 'team')
        league: Código de liga
        season: Temporada en formato YY-YY
        
    Returns:
        True si las entradas son válidas
        
    Raises:
        ValueError: Si alguna entrada no es válida
    """
    # Validar entity_name
    if not entity_name or not isinstance(entity_name, str) or entity_name.strip() == "":
        raise ValueError("entity_name must be a non-empty string")
    
    # Validar entity_type
    valid_types = ['player', 'team']
    if entity_type not in valid_types:
        raise ValueError(f"entity_type must be one of {valid_types}, got '{entity_type}'")
    
    # Validar league format
    if not league or not isinstance(league, str):
        raise ValueError("league must be a non-empty string")
    
    # Validar season format (YY-YY)
    if not season or not isinstance(season, str):
        raise ValueError("season must be a string")
    
    # Verificar formato de temporada
    season_parts = season.split('-')
    if len(season_parts) != 2:
        raise ValueError(f"season must be in YY-YY format, got '{season}'")
    
    try:
        year1, year2 = int(season_parts[0]), int(season_parts[1])
        if not (0 <= year1 <= 99 and 0 <= year2 <= 99):
            raise ValueError(f"season years must be 00-99, got '{season}'")
        if year2 != (year1 + 1) % 100:
            raise ValueError(f"season must be consecutive years, got '{season}'")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"season must contain valid numbers, got '{season}'")
        raise
    
    return True

def _validate_league_codes() -> Dict[str, str]:
    """Obtener códigos de liga válidos para validación."""
    # Use dynamic league configuration from LEAGUE_DICT
    valid_leagues = {}
    for league_code, league_config in LEAGUE_DICT.items():
        if 'FBref' in league_config:
            fbref_name = league_config['FBref']
            valid_leagues[league_code] = fbref_name
    return valid_leagues

def validate_inputs_with_suggestions(entity_name: str, entity_type: str, league: str, season: str) -> Dict[str, Any]:
    """
    Validar entradas con sugerencias de corrección.
    
    Returns:
        Dict con 'valid', 'errors', 'suggestions'
    """
    result = {
        'valid': True,
        'errors': [],
        'suggestions': []
    }
    
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        result['valid'] = False
        result['errors'].append(str(e))
        
        # Sugerencias específicas
        if 'entity_type' in str(e):
            result['suggestions'].append("Use 'player' or 'team' for entity_type")
        
        if 'season' in str(e) and 'format' in str(e):
            result['suggestions'].append("Use season format like '23-24', '22-23', etc.")
            
        if 'league' in str(e):
            valid_leagues = _validate_league_codes()
            result['suggestions'].append(f"Valid leagues: {list(valid_leagues.keys())}")
    
    return result

# ====================================================================
# INTELLIGENT CACHE SYSTEM
# ====================================================================

CACHE_DIR = Path.home() / ".footballdecoded_cache" / "fbref"
CACHE_EXPIRY_HOURS = 24  # Cache válido por 24 horas

def _ensure_cache_dir():
    """Crear directorio de caché si no existe."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(entity_name: str, entity_type: str, league: str, season: str, **kwargs) -> str:
    """Generar clave única para cache basada en parámetros."""
    cache_data = f"{entity_name}:{entity_type}:{league}:{season}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def _get_cache_path(cache_key: str) -> Path:
    """Obtener ruta completa del archivo de cache."""
    return CACHE_DIR / f"{cache_key}.pkl"

def _is_cache_valid(cache_path: Path) -> bool:
    """Verificar si el cache es válido (no expirado)."""
    if not cache_path.exists():
        return False
    
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
    return file_time > expiry_time

def _save_to_cache(data: Dict, cache_key: str):
    """Guardar datos en cache."""
    try:
        _ensure_cache_dir()
        cache_path = _get_cache_path(cache_key)
        
        cache_data = {
            'data': data,
            'timestamp': datetime.now(),
            'cache_key': cache_key
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
            
    except Exception as e:
        print(f"Warning: Could not save to cache: {e}")

def _load_from_cache(cache_key: str) -> Optional[Dict]:
    """Cargar datos del cache si existen y son válidos."""
    try:
        cache_path = _get_cache_path(cache_key)
        
        if not _is_cache_valid(cache_path):
            return None
            
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
            
        return cache_data.get('data')
        
    except Exception as e:
        print(f"Warning: Could not load from cache: {e}")
        return None

def clear_cache():
    """Limpiar todo el cache de FBref."""
    try:
        if CACHE_DIR.exists():
            for cache_file in CACHE_DIR.glob("*.pkl"):
                cache_file.unlink()
            print("FBref cache cleared successfully")
    except Exception as e:
        print(f"Error clearing cache: {e}")

# ====================================================================
# CORE ENGINE - UNIFIED EXTRACTION
# ====================================================================

def extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    use_cache: bool = True
) -> Optional[Dict]:
    """
    Motor de extracción unificado para jugadores y equipos con cache inteligente.
    
    Args:
        entity_name: Nombre del jugador o equipo
        entity_type: 'player' o 'team'
        league: ID de liga
        season: ID de temporada
        match_id: ID de partido opcional para datos específicos del partido
        include_opponent_stats: Incluir estadísticas del oponente (solo equipos)
        use_cache: Usar sistema de cache (default: True)
        
    Returns:
        Dict con todas las estadísticas FBref disponibles
    """
    # Validar entradas
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        print(f"Input validation failed: {e}")
        validation_result = validate_inputs_with_suggestions(entity_name, entity_type, league, season)
        if validation_result['suggestions']:
            print("Suggestions:")
            for suggestion in validation_result['suggestions']:
                print(f"  - {suggestion}")
        return None
    
    # Generar clave de cache
    cache_key = _generate_cache_key(
        entity_name, entity_type, league, season,
        match_id=match_id, include_opponent_stats=include_opponent_stats
    )
    
    # Intentar cargar desde cache si está habilitado
    if use_cache:
        cached_data = _load_from_cache(cache_key)
        if cached_data:
            print(f"Loading {entity_name} from cache")
            return cached_data
    
    try:
        fbref = FBref(leagues=[league], seasons=[season], no_cache=True)
        
        if entity_type == 'player':
            if match_id:
                stat_types = ['summary', 'passing', 'passing_types', 'defense', 'possession', 'misc', 'keepers']
            else:
                stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation', 
                             'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        else:
            stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation',
                         'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        
        extracted_data = {}
        basic_info = {}
        
        for stat_type in stat_types:
            try:
                if entity_type == 'player':
                    if match_id:
                        stats = fbref.read_player_match_stats(stat_type=stat_type, match_id=match_id)
                    else:
                        stats = fbref.read_player_season_stats(stat_type=stat_type)
                    entity_row = _find_entity(stats, entity_name, 'player')
                else:
                    stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=False)
                    entity_row = _find_entity(stats, entity_name, 'team')
                
                if entity_row is not None:
                    if not basic_info:
                        basic_info = _extract_basic_info(entity_row, entity_name, entity_type, match_id)
                    
                    _process_columns(entity_row, extracted_data)
                    
                    if entity_type == 'team' and include_opponent_stats and not match_id:
                        try:
                            opp_stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=True)
                            opp_row = _find_entity(opp_stats, entity_name, 'team')
                            if opp_row is not None:
                                _process_columns(opp_row, extracted_data, prefix='opponent_')
                        except Exception:
                            pass
                            
            except Exception:
                continue
        
        if not basic_info:
            return None
        
        final_data = {**basic_info, **extracted_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        # Guardar en cache si está habilitado
        if use_cache and standardized_data:
            _save_to_cache(standardized_data, cache_key)
        
        return standardized_data
        
    except Exception:
        return None


# ====================================================================
# BATCH EXTRACTION
# ====================================================================

def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    max_workers: int = 3,
    show_progress: bool = True,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Extraer múltiples entidades con procesamiento optimizado en paralelo.
    
    Args:
        entities: Lista de nombres de entidades
        entity_type: 'player' o 'team'
        league: Identificador de liga
        season: Identificador de temporada
        match_id: ID de partido opcional
        include_opponent_stats: Incluir estadísticas del oponente (solo equipos)
        max_workers: Número máximo de hilos paralelos (default: 3)
        show_progress: Mostrar barra de progreso (default: True)
        use_cache: Usar sistema de cache (default: True)
        
    Returns:
        DataFrame con estadísticas de todas las entidades
    """
    if not entities:
        return pd.DataFrame()
    
    def extract_single_entity(entity_name: str) -> Optional[Dict]:
        """Extract single entity with rate limiting."""
        try:
            # Add small delay between requests to respect rate limits
            time.sleep(0.5)
            return extract_data(
                entity_name, entity_type, league, season, 
                match_id, include_opponent_stats, use_cache=use_cache
            )
        except Exception as e:
            if show_progress:
                print(f"Error extracting {entity_name}: {e}")
            return None
    
    all_data = []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_entity = {
            executor.submit(extract_single_entity, entity): entity 
            for entity in entities
        }
        
        # Process completed tasks with progress bar
        if show_progress and TQDM_AVAILABLE:
            futures = tqdm(as_completed(future_to_entity), total=len(entities), 
                          desc=f"Extracting {entity_type}s")
        else:
            futures = as_completed(future_to_entity)
            if show_progress:
                print(f"Processing {len(entities)} {entity_type}s...")
        
        for future in futures:
            entity_name = future_to_entity[future]
            try:
                entity_data = future.result()
                if entity_data:
                    all_data.append(entity_data)
            except Exception as e:
                if show_progress:
                    print(f"Failed to extract {entity_name}: {e}")
    
    if show_progress:
        success_count = len(all_data)
        total_count = len(entities)
        print(f"Successfully extracted {success_count}/{total_count} {entity_type}s")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


# ====================================================================
# SPECIALIZED EXTRACTION FUNCTIONS
# ====================================================================

def extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None
) -> pd.DataFrame:
    """Extraer todos los jugadores de una liga con filtrado opcional."""
    try:
        fbref = FBref(leagues=[league], seasons=[season], no_cache=True)
        player_stats = fbref.read_player_season_stats(stat_type='standard')
        
        if player_stats is None or player_stats.empty:
            return pd.DataFrame()
        
        players_df = player_stats.reset_index()
        
        if team_filter:
            players_df = players_df[players_df['team'].str.contains(team_filter, case=False, na=False)]
        if position_filter:
            players_df = players_df[players_df['pos'].str.contains(position_filter, case=False, na=False)]
        
        columns = ['player', 'team', 'league', 'season']
        optional_cols = ['pos', 'age', 'nation']
        for col in optional_cols:
            if col in players_df.columns:
                columns.append(col)
        
        result_df = players_df[columns].sort_values(['team', 'player'])
        
        return result_df
        
    except Exception:
        return pd.DataFrame()


def extract_match_events(
    match_id: str,
    league: str,
    season: str,
    event_type: str = 'all'
) -> Union[pd.DataFrame, Dict]:
    """Extraer eventos de partido (goles, tarjetas, sustituciones, disparos)."""
    try:
        fbref = FBref(leagues=[league], seasons=[season], no_cache=True)
        result = {}
        
        if event_type in ['all', 'events']:
            events = fbref.read_events(match_id=match_id)
            if event_type == 'events':
                return events
            result['events'] = events
        
        if event_type in ['all', 'shots']:
            shots = fbref.read_shot_events(match_id=match_id)
            if event_type == 'shots':
                return shots
            result['shots'] = shots
        
        if event_type in ['all', 'lineups']:
            lineups = fbref.read_lineup(match_id=match_id)
            if event_type == 'lineups':
                return lineups
            result['lineups'] = lineups
        
        return result if event_type == 'all' else pd.DataFrame()
        
    except Exception:
        return pd.DataFrame() if event_type != 'all' else {}


def extract_league_schedule(
    league: str,
    season: str
) -> pd.DataFrame:
    """Extraer calendario completo de liga con resultados."""
    try:
        fbref = FBref(leagues=[league], seasons=[season], no_cache=True)
        schedule = fbref.read_schedule()
        
        return schedule
        
    except Exception:
        return pd.DataFrame()


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str) -> Optional[pd.DataFrame]:
    """Encontrar entidad con coincidencia flexible de nombres."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(entity_name, entity_type)
    index_level = entity_type
    
    # Intentar coincidencias exactas primero
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.lower() == variation.lower()]
        if not matches.empty:
            return matches
    
    # Intentar coincidencias parciales
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.contains(
            variation, case=False, na=False, regex=False)]
        if not matches.empty:
            return matches
    
    return None


def _generate_name_variations(name: str, entity_type: str) -> List[str]:
    """Generar variaciones de nombres para coincidencia robusta."""
    variations = [name]
    
    # Eliminar acentos
    clean_name = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != name:
        variations.append(clean_name)
    
    # Añadir componentes del nombre
    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) > 1:
            variations.append(' '.join(parts[:2]))
            variations.append(' '.join(parts[-2:]))
    
    # Variaciones específicas de equipos
    if entity_type == 'team':
        for suffix in [' FC', ' CF', ' United', ' City', ' Real', ' Club']:
            if name.endswith(suffix):
                variations.append(name[:-len(suffix)])
        
        team_mappings = {
            'Real Madrid': ['Madrid', 'Real Madrid CF'],
            'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
            'Manchester United': ['Man United', 'Man Utd', 'United'],
            'Manchester City': ['Man City', 'City'],
            'Tottenham': ['Spurs', 'Tottenham Hotspur']
        }
        if name in team_mappings:
            variations.extend(team_mappings[name])
    
    return list(dict.fromkeys(variations))


def _extract_basic_info(row: pd.DataFrame, name: str, entity_type: str, match_id: Optional[str] = None) -> Dict:
    """Extraer información básica de identificación."""
    if entity_type == 'player':
        basic_info = {
            'player_name': name,
            'league': row.index.get_level_values('league')[0],
            'season': row.index.get_level_values('season')[0],
            'team': row.index.get_level_values('team')[0]
        }
        if match_id:
            basic_info['match_id'] = match_id
            if 'game' in row.index.names:
                basic_info['game'] = row.index.get_level_values('game')[0]
    else:
        basic_info = {
            'team_name': name,
            'league': row.index.get_level_values('league')[0],
            'season': row.index.get_level_values('season')[0],
            'official_team_name': row.index.get_level_values('team')[0]
        }
    
    return basic_info


def _process_columns(row: pd.DataFrame, data_dict: Dict, prefix: str = '') -> None:
    """Procesar todas las columnas de una fila, evitando duplicados."""
    for col in row.columns:
        clean_name = _clean_column_name(col)
        if prefix:
            clean_name = f"{prefix}{clean_name}"
        
        if clean_name not in data_dict:
            data_dict[clean_name] = row.iloc[0][col]


def _clean_column_name(col: Union[str, tuple]) -> str:
    """Limpiar y estandarizar nombres de columnas."""
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        if level1 == '' or pd.isna(level1) or level1 is None:
            return level0
        
        common_categories = ['Standard', 'Performance', 'Expected', 'Total', 'Short', 
                           'Medium', 'Long', 'Playing Time', 'Per 90 Minutes']
        
        if level0 in common_categories:
            return level1
        else:
            return f"{level0}_{level1}"
    
    return str(col)


def _apply_stat_mapping(data: Dict) -> Dict:
    """Aplicar convención de nomenclatura estandarizada."""
    stat_mapping = {
        'nation': 'nationality', 'pos': 'position', 'age': 'age', 'born': 'birth_year',
        'MP': 'matches_played', 'Starts': 'matches_started', 'Min': 'minutes_played',
        '90s': 'full_matches_equivalent', 'Mn/MP': 'minutes_per_match',
        'Gls': 'goals', 'Ast': 'assists', 'G+A': 'goals_plus_assists',
        'G-PK': 'non_penalty_goals', 'PK': 'penalty_goals', 'PKatt': 'penalty_attempts',
        'CrdY': 'yellow_cards', 'CrdR': 'red_cards',
        'Sh': 'shots', 'SoT': 'shots_on_target', 'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90', 'G/Sh': 'goals_per_shot', 'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        'xG': 'expected_goals', 'npxG': 'non_penalty_expected_goals',
        'xAG': 'expected_assists', 'xA': 'expected_assists_alt',
        'npxG+xAG': 'non_penalty_xG_plus_xAG',
        'Cmp': 'passes_completed', 'Att': 'passes_attempted', 'Cmp%': 'pass_completion_pct',
        'TotDist': 'total_pass_distance', 'PrgDist': 'progressive_pass_distance',
        'KP': 'key_passes', '1/3': 'passes_final_third', 'PPA': 'passes_penalty_area',
        'PrgP': 'progressive_passes',
        'Tkl': 'tackles', 'TklW': 'tackles_won', 'Int': 'interceptions',
        'Clr': 'clearances', 'Err': 'errors',
        'Touches': 'touches', 'Succ': 'successful_take_ons', 'Succ%': 'take_on_success_pct',
        'Carries': 'carries', 'PrgC': 'progressive_carries', 'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        'W': 'wins', 'D': 'draws', 'L': 'losses', 'Pts': 'points',
        'GF': 'goals_for', 'GA': 'goals_against', 'GD': 'goal_difference',
        'xGF': 'expected_goals_for', 'xGA': 'expected_goals_against'
    }
    
    standardized_data = {}
    for original_name, value in data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Asegurar orden consistente de columnas."""
    if df.empty:
        return df
    
    if entity_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'match_id', 'game',
            'position', 'age', 'nationality', 'birth_year',
            'minutes_played', 'matches_played', 'matches_started',
            'goals', 'assists', 'goals_plus_assists',
            'expected_goals', 'shots', 'shots_on_target',
            'passes_completed', 'pass_completion_pct', 'key_passes',
            'touches', 'tackles', 'interceptions'
        ]
    else:
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'wins', 'draws', 'losses', 'points', 'goals_for', 'goals_against',
            'expected_goals_for', 'expected_goals_against', 'shots', 'passes_completed'
        ]
    
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_order = available_priority + remaining_columns
    return df[final_order]


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, include_timestamp: bool = True) -> str:
    """Exportar datos a CSV con formato adecuado."""
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    df.to_csv(full_filename, index=False, encoding='utf-8')
    
    return full_filename


# ====================================================================
# QUICK ACCESS FUNCTIONS - SIMPLIFIED API
# ====================================================================

def get_player(player_name: str, league: str, season: str, use_cache: bool = True) -> Optional[Dict]:
    """Extracción rápida de estadísticas de temporada de jugador."""
    return extract_data(player_name, 'player', league, season, use_cache=use_cache)

def get_team(team_name: str, league: str, season: str, use_cache: bool = True) -> Optional[Dict]:
    """Extracción rápida de estadísticas de temporada de equipo."""
    return extract_data(team_name, 'team', league, season, use_cache=use_cache)

def get_players(players: List[str], league: str, season: str, max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Extracción rápida de múltiples jugadores con procesamiento paralelo."""
    return extract_multiple(players, 'player', league, season, max_workers=max_workers, show_progress=show_progress)

def get_teams(teams: List[str], league: str, season: str, max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Extracción rápida de múltiples equipos con procesamiento paralelo."""
    return extract_multiple(teams, 'team', league, season, max_workers=max_workers, show_progress=show_progress)

def get_league_players(league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Lista rápida de jugadores de liga."""
    return extract_league_players(league, season, team_filter=team)

def get_match_data(match_id: str, league: str, season: str, data_type: str = 'all') -> Union[pd.DataFrame, Dict]:
    """Extracción rápida de datos de partido."""
    return extract_match_events(match_id, league, season, event_type=data_type)

def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Extracción rápida de calendario de liga."""
    return extract_league_schedule(league, season)