# ====================================================================
# FootballDecoded - Understat Optimized Advanced Metrics Extractor
# ====================================================================
"""
Understat Wrapper especializado en métricas avanzadas únicas:

MÉTRICAS EXCLUSIVAS DE UNDERSTAT (no disponibles en FBref):
- xG Chain: xG generado en jugadas donde participó el jugador
- xG Buildup: xG en jugadas que el jugador ayudó a construir  
- npxG + xA: Métricas combinadas sin penales
- Key Passes: Pases clave que llevan a ocasiones
- PPDA: Presión defensiva (Passes Allowed Per Defensive Action)
- Deep Completions: Pases completados en último tercio rival

CARACTERÍSTICAS AVANZADAS:
- Sistema de caché inteligente para métricas complejas
- Procesamiento paralelo optimizado con rate limiting
- Merge robusto con datos de FBref automático
- Búsqueda automática de match IDs y jugadores
- Validación específica para datos Understat

FUNCIONES CLAVE:
- extract_data(): Métricas avanzadas Understat
- merge_with_fbref(): Fusión automática FBref + Understat
- extract_shot_events(): Eventos de disparos con xG
- get_match_ids(): Búsqueda automática de IDs de partidos

USO TÍPICO:
    from wrappers import understat_data
    
    # Métricas avanzadas individuales
    player = understat_data.get_player("Messi", "ESP-La Liga", "23-24")
    
    # Fusión automática con FBref
    fbref_players = fbref_data.get_players(["Messi", "Benzema"], ...)
    merged = understat_data.merge_with_fbref(fbref_players, "ESP-La Liga", "23-24")
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
import pickle
import hashlib
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import Understat
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# INPUT VALIDATION SYSTEM
# ====================================================================

def _validate_inputs(entity_name: str, entity_type: str, league: str, season: str) -> bool:
    """Validar entradas de manera robusta."""
    if not entity_name or not isinstance(entity_name, str) or entity_name.strip() == "":
        raise ValueError("entity_name must be a non-empty string")
    
    valid_types = ['player', 'team']
    if entity_type not in valid_types:
        raise ValueError(f"entity_type must be one of {valid_types}, got '{entity_type}'")
    
    if not league or not isinstance(league, str):
        raise ValueError("league must be a non-empty string")
    
    if not season or not isinstance(season, str):
        raise ValueError("season must be a string")
    
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

def validate_inputs_with_suggestions(entity_name: str, entity_type: str, league: str, season: str) -> Dict[str, Any]:
    """Validar entradas con sugerencias de corrección."""
    result = {'valid': True, 'errors': [], 'suggestions': []}
    
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        result['valid'] = False
        result['errors'].append(str(e))
        
        if 'entity_type' in str(e):
            result['suggestions'].append("Use 'player' or 'team' for entity_type")
        if 'season' in str(e) and 'format' in str(e):
            result['suggestions'].append("Use season format like '23-24', '22-23', etc.")
        if 'league' in str(e):
            valid_leagues = [league for league in LEAGUE_DICT.keys() if 'Understat' in LEAGUE_DICT[league]]
            result['suggestions'].append(f"Valid leagues for Understat: {', '.join(valid_leagues[:3])}{'...' if len(valid_leagues) > 3 else ''}")
    
    return result

# ====================================================================
# INTELLIGENT CACHE SYSTEM
# ====================================================================

CACHE_DIR = Path.home() / ".footballdecoded_cache" / "understat"
CACHE_EXPIRY_HOURS = 24

def _ensure_cache_dir():
    """Crear directorio de caché si no existe."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(entity_name: str, entity_type: str, league: str, season: str, **kwargs) -> str:
    """Generar clave única para cache."""
    cache_data = f"{entity_name}:{entity_type}:{league}:{season}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def _get_cache_path(cache_key: str) -> Path:
    """Obtener ruta completa del archivo de cache."""
    return CACHE_DIR / f"{cache_key}.pkl"

def _is_cache_valid(cache_path: Path) -> bool:
    """Verificar si el cache es válido."""
    if not cache_path.exists():
        return False
    
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
    return file_time > expiry_time

def _save_to_cache(data: Union[Dict, pd.DataFrame], cache_key: str):
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

def _load_from_cache(cache_key: str) -> Optional[Union[Dict, pd.DataFrame]]:
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
    """Limpiar todo el cache de Understat."""
    try:
        if CACHE_DIR.exists():
            for cache_file in CACHE_DIR.glob("*.pkl"):
                cache_file.unlink()
            print("Understat cache cleared successfully")
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
    use_cache: bool = True
) -> Optional[Dict]:
    """
    Motor de extracción unificado para métricas avanzadas de Understat con cache.
    
    Args:
        entity_name: Nombre del jugador o equipo
        entity_type: 'player' o 'team'
        league: ID de liga
        season: ID de temporada
        use_cache: Usar sistema de cache (default: True)
        
    Returns:
        Dict con métricas únicas de Understat (NO en FBref)
    """
    # Validar entradas
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        print(f"Understat input validation failed: {e}")
        validation_result = validate_inputs_with_suggestions(entity_name, entity_type, league, season)
        if validation_result['suggestions']:
            print("Suggestions:")
            for suggestion in validation_result['suggestions']:
                print(f"  - {suggestion}")
        return None
    
    # Generar clave de cache
    cache_key = _generate_cache_key(entity_name, entity_type, league, season)
    
    # Intentar cargar desde cache
    if use_cache:
        cached_data = _load_from_cache(cache_key)
        if cached_data:
            print(f"Loading {entity_name} from Understat cache")
            return cached_data
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        if entity_type == 'player':
            stats = understat.read_player_season_stats()
            entity_row = _find_entity(stats, entity_name, 'player')
            
            if entity_row is None:
                return None
            
            basic_info = {
                'player_name': entity_name,
                'league': league,
                'season': season,
                'team': entity_row.index.get_level_values('team')[0],
                'official_player_name': entity_row.index.get_level_values('player')[0]
            }
            
            understat_metrics = _extract_player_metrics(entity_row)
            
        else:
            team_stats = understat.read_team_match_stats()
            team_matches = _find_team_matches(team_stats, entity_name)
            
            if team_matches is None or team_matches.empty:
                return None
            
            basic_info = {
                'team_name': entity_name,
                'league': league,
                'season': season,
                'official_team_name': team_matches.iloc[0]['home_team'] if 'home_team' in team_matches.columns else entity_name
            }
            
            understat_metrics = _calculate_team_metrics(team_matches)
        
        final_data = {**basic_info, **understat_metrics}
        
        # Guardar en cache si está habilitado
        if use_cache and final_data:
            _save_to_cache(final_data, cache_key)
        
        return final_data
        
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
    max_workers: int = 3,
    show_progress: bool = True,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Extraer múltiples entidades con procesamiento paralelo optimizado.
    
    Args:
        entities: Lista de nombres de entidades
        entity_type: 'player' o 'team'
        league: Identificador de liga
        season: Identificador de temporada
        max_workers: Número máximo de hilos paralelos (default: 3)
        show_progress: Mostrar barra de progreso (default: True)
        use_cache: Usar sistema de cache (default: True)
        
    Returns:
        DataFrame con métricas de Understat de todas las entidades
    """
    if not entities:
        return pd.DataFrame()
    
    def extract_single_entity(entity_name: str) -> Optional[Dict]:
        """Extract single entity with rate limiting."""
        try:
            # Add delay to respect rate limits (Understat is more sensitive)
            time.sleep(1.0)
            return extract_data(entity_name, entity_type, league, season, use_cache=use_cache)
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
                          desc=f"Extracting Understat {entity_type}s")
        else:
            futures = as_completed(future_to_entity)
            if show_progress:
                print(f"Processing {len(entities)} Understat {entity_type}s...")
        
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
        print(f"Successfully extracted {success_count}/{total_count} Understat {entity_type}s")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


# ====================================================================
# SHOT EVENTS EXTRACTION
# ====================================================================

def extract_shot_events(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False  # ← AGREGAR ESTE PARÁMETRO
) -> pd.DataFrame:
    """
    Extraer eventos de disparos con información espacial y táctica completa.
    
    Args:
        match_id: ID de partido de Understat (entero)
        league: Identificador de liga
        season: Identificador de temporada
        player_filter: Filtro opcional de nombre de jugador
        team_filter: Filtro opcional de nombre de equipo
        verbose: Mostrar información de progreso
        
    Returns:
        DataFrame con eventos de disparos completos y análisis táctico
    """
    try:
        if verbose:
            print(f"   Extracting shot data for match {match_id}...")
            
        understat = Understat(leagues=[league], seasons=[season])
        shot_events = understat.read_shot_events(match_id=match_id)
        
        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   No shot events found for match {match_id}")
            return pd.DataFrame()
        
        enhanced_events = _process_shot_events(shot_events)
        filtered_events = _apply_shot_filters(enhanced_events, player_filter, team_filter)
        
        if not filtered_events.empty:
            filtered_events['match_id'] = match_id
            filtered_events['data_source'] = 'understat'
            
        if verbose:
            print(f"   Found {len(filtered_events)} shot events")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   Error extracting shot events: {e}")
        return pd.DataFrame()


# ====================================================================
# INTEGRATION WITH FBREF
# ====================================================================

def merge_with_fbref(
    fbref_data: Union[pd.DataFrame, Dict],
    league: str,
    season: str,
    data_type: str = 'player',
    show_progress: bool = True,
    fallback_matching: bool = True
) -> pd.DataFrame:
    """
    Fusionar datos de FBref con métricas de Understat con robustez mejorada al 100%.
    
    Args:
        fbref_data: DataFrame o Dict de FBref
        league: Identificador de liga  
        season: Identificador de temporada
        data_type: 'player' o 'team'
        show_progress: Mostrar progreso de la fusión (default: True)
        fallback_matching: Usar matching alternativo si falla el estándar (default: True)
        
    Returns:
        DataFrame con métricas combinadas FBref + Understat
    """
    # Validación de entrada
    if fbref_data is None:
        if show_progress:
            print("Warning: No FBref data provided")
        return pd.DataFrame()
    
    if isinstance(fbref_data, dict):
        fbref_df = pd.DataFrame([fbref_data])
    else:
        fbref_df = fbref_data.copy()
    
    if fbref_df.empty:
        if show_progress:
            print("Warning: Empty FBref DataFrame provided")
        return fbref_df
    
    # Determinar clave de merge y entidades
    if data_type == 'player':
        if 'player_name' not in fbref_df.columns:
            if show_progress:
                print("Error: 'player_name' column not found in FBref data")
            return fbref_df
        entities = fbref_df['player_name'].unique().tolist()
        merge_key = 'player_name'
    else:
        if 'team_name' not in fbref_df.columns:
            if show_progress:
                print("Error: 'team_name' column not found in FBref data")
            return fbref_df
        entities = fbref_df['team_name'].unique().tolist()
        merge_key = 'team_name'
    
    if show_progress:
        print(f"Merging {len(entities)} {data_type}s with Understat data...")
    
    # Extraer datos de Understat
    understat_df = extract_multiple(
        entities, data_type, league, season, 
        show_progress=show_progress
    )
    
    if understat_df.empty:
        if show_progress:
            print("Warning: No Understat data found for any entities")
        return fbref_df
    
    # Intentar merge estándar
    try:
        # Verificar columnas necesarias para merge
        required_cols = [merge_key, 'league', 'season']
        
        # Usar solo columnas que existen en ambos DataFrames
        merge_cols = []
        for col in required_cols:
            if col in fbref_df.columns and col in understat_df.columns:
                merge_cols.append(col)
        
        # Añadir 'team' si está disponible en ambos
        if 'team' in fbref_df.columns and 'team' in understat_df.columns:
            merge_cols.append('team')
        
        if show_progress:
            print(f"Merging on columns: {merge_cols}")
        
        merged_df = pd.merge(
            fbref_df, understat_df,
            on=merge_cols,
            how='left', suffixes=('', '_understat_dup')
        )
        
        # Limpiar columnas duplicadas
        dup_cols = [col for col in merged_df.columns if col.endswith('_understat_dup')]
        if dup_cols:
            merged_df = merged_df.drop(columns=dup_cols)
        
        # Verificar el éxito del merge
        understat_cols = [col for col in merged_df.columns if col.startswith('understat_')]
        successful_merges = merged_df[understat_cols[0]].notna().sum() if understat_cols else 0
        
        if show_progress:
            print(f"Successfully merged {successful_merges}/{len(fbref_df)} entities with Understat data")
        
        # Si el merge falló y está habilitado el fallback, intentar matching alternativo
        if successful_merges < len(entities) * 0.5 and fallback_matching:
            if show_progress:
                print("Standard merge had low success rate. Attempting fallback matching...")
            
            # Merge solo por nombre de entidad (menos restrictivo)
            fallback_df = pd.merge(
                fbref_df, understat_df,
                on=merge_key,
                how='left', suffixes=('', '_understat_fallback')
            )
            
            # Limpiar duplicados del fallback
            fallback_dup_cols = [col for col in fallback_df.columns if col.endswith('_understat_fallback')]
            if fallback_dup_cols:
                fallback_df = fallback_df.drop(columns=fallback_dup_cols)
            
            fallback_understat_cols = [col for col in fallback_df.columns if col.startswith('understat_')]
            fallback_successful_merges = fallback_df[fallback_understat_cols[0]].notna().sum() if fallback_understat_cols else 0
            
            # Usar el mejor resultado
            if fallback_successful_merges > successful_merges:
                merged_df = fallback_df
                if show_progress:
                    print(f"Fallback matching improved success to {fallback_successful_merges}/{len(fbref_df)} entities")
        
        return merged_df
        
    except Exception as e:
        if show_progress:
            print(f"Error during merge: {e}")
            print("Returning original FBref data without Understat metrics")
        return fbref_df


# ====================================================================
# CORE PROCESSING FUNCTIONS
# ====================================================================

def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str) -> Optional[pd.DataFrame]:
    """Encontrar entidad con coincidencia flexible de nombres."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(entity_name)
    index_level = entity_type
    
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.lower() == variation.lower()]
        if not matches.empty:
            return matches
    
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.contains(
            variation, case=False, na=False, regex=False)]
        if not matches.empty:
            return matches
    
    return None


def _find_team_matches(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Encontrar partidos de equipo en formato Understat."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(team_name)
    
    for variation in variations:
        home_matches = stats[stats['home_team'].str.contains(variation, case=False, na=False, regex=False)]
        away_matches = stats[stats['away_team'].str.contains(variation, case=False, na=False, regex=False)]
        
        if not home_matches.empty or not away_matches.empty:
            return pd.concat([home_matches, away_matches]).drop_duplicates()
    
    return None


def _generate_name_variations(name: str) -> List[str]:
    """Generar variaciones de nombres para convenciones de nomenclatura de Understat."""
    variations = [name]
    
    clean_name = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != name:
        variations.append(clean_name)
    
    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) >= 2:
            variations.append(f"{parts[0]} {parts[-1]}")
    
    mappings = {
        "Kylian Mbappé": ["Kylian Mbappe", "K. Mbappe", "Mbappe"],
        "Erling Haaland": ["E. Haaland", "Haaland"],
        "Vinicius Jr": ["Vinicius Junior", "Vinicius"],
        'Manchester United': ['Manchester Utd', 'Man United'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur'],
        'Real Madrid': ['Madrid'],
        'Barcelona': ['Barça', 'FC Barcelona']
    }
    
    if name in mappings:
        variations.extend(mappings[name])
    
    return list(dict.fromkeys(variations))


def _extract_player_metrics(player_row: pd.DataFrame) -> Dict:
    """Extraer métricas de jugador específicas de Understat (NO en FBref)."""
    understat_data = {}
    
    core_metrics = {
        'xg_chain': 'understat_xg_chain',
        'xg_buildup': 'understat_xg_buildup',
        'key_passes': 'understat_key_passes',
        'np_xg': 'understat_np_xg',
        'xa': 'understat_xa',
        'np_goals': 'understat_np_goals',
        'player_id': 'understat_player_id',
        'team_id': 'understat_team_id'
    }
    
    for col in player_row.columns:
        if col in core_metrics:
            value = player_row.iloc[0][col]
            understat_data[core_metrics[col]] = value if pd.notna(value) else None
    
    _add_derived_player_metrics(understat_data)
    
    return understat_data


def _add_derived_player_metrics(data: Dict) -> None:
    """Añadir métricas calculadas únicas para análisis de Understat."""
    if data.get('understat_np_xg') and data.get('understat_xa'):
        np_xg = data['understat_np_xg'] or 0
        xa = data['understat_xa'] or 0
        data['understat_npxg_plus_xa'] = np_xg + xa
    
    if data.get('understat_xg_chain') and data.get('understat_np_xg'):
        xg_chain = data['understat_xg_chain'] or 0
        np_xg = data['understat_np_xg'] or 0
        if np_xg > 0:
            data['understat_buildup_involvement_pct'] = (xg_chain / np_xg) * 100


def _calculate_team_metrics(team_matches: pd.DataFrame) -> Dict:
    """Calcular métricas de equipo específicas de Understat."""
    team_metrics = {}
    
    total_matches = len(team_matches)
    team_metrics['understat_matches_analyzed'] = total_matches
    
    if total_matches == 0:
        return team_metrics
    
    ppda_values = _extract_column_values(team_matches, ['home_ppda', 'away_ppda'])
    if ppda_values:
        team_metrics['understat_ppda_avg'] = np.mean(ppda_values)
        team_metrics['understat_ppda_std'] = np.std(ppda_values)
    
    deep_values = _extract_column_values(team_matches, ['home_deep_completions', 'away_deep_completions'])
    if deep_values:
        team_metrics['understat_deep_completions_total'] = np.sum(deep_values)
        team_metrics['understat_deep_completions_avg'] = np.mean(deep_values)
    
    xpts_values = _extract_column_values(team_matches, ['home_expected_points', 'away_expected_points'])
    if xpts_values:
        team_metrics['understat_expected_points_total'] = np.sum(xpts_values)
        team_metrics['understat_expected_points_avg'] = np.mean(xpts_values)
    
    np_xg_values = _extract_column_values(team_matches, ['home_np_xg', 'away_np_xg'])
    if np_xg_values:
        team_metrics['understat_np_xg_total'] = np.sum(np_xg_values)
        team_metrics['understat_np_xg_avg'] = np.mean(np_xg_values)
    
    _add_derived_team_metrics(team_metrics)
    
    return team_metrics


def _extract_column_values(df: pd.DataFrame, columns: List[str]) -> List[float]:
    """Extraer y combinar valores de múltiples columnas."""
    values = []
    for col in columns:
        if col in df.columns:
            col_values = df[col].dropna()
            values.extend(col_values.tolist())
    return values


def _add_derived_team_metrics(metrics: Dict) -> None:
    """Añadir métricas de equipo calculadas únicas para análisis."""
    if 'understat_expected_points_total' in metrics:
        xpts = metrics['understat_expected_points_total']
        if xpts > 0:
            metrics['understat_points_efficiency'] = xpts / metrics.get('understat_matches_analyzed', 1)


def _process_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Procesar y mejorar datos de eventos de disparos."""
    if shot_events.empty:
        return shot_events
    
    df = shot_events.copy()
    
    column_mapping = {
        'xg': 'shot_xg',
        'location_x': 'shot_location_x',
        'location_y': 'shot_location_y',
        'body_part': 'shot_body_part',
        'situation': 'shot_situation',
        'result': 'shot_result',
        'minute': 'shot_minute',
        'player': 'shot_player',
        'team': 'shot_team',
        'assist_player': 'assist_player_name'
    }
    
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
    _add_shot_analytics(df)
    
    return df


def _add_shot_analytics(df: pd.DataFrame) -> None:
    """Añadir campos de análisis de disparos calculados."""
    if 'shot_result' in df.columns:
        df['is_goal'] = (df['shot_result'] == 'Goal').astype(int)
        df['is_on_target'] = df['shot_result'].isin(['Goal', 'Saved Shot']).astype(int)
        df['is_blocked'] = (df['shot_result'] == 'Blocked Shot').astype(int)
    
    if 'shot_location_x' in df.columns and 'shot_location_y' in df.columns:
        df['shot_distance_to_goal'] = _calculate_shot_distance(df['shot_location_x'], df['shot_location_y'])
        df['shot_zone'] = _classify_shot_zones(df['shot_location_x'], df['shot_location_y'])
    
    if 'assist_player_name' in df.columns:
        df['is_assisted'] = (~df['assist_player_name'].isna()).astype(int)


def _calculate_shot_distance(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calcular distancia desde ubicación del disparo al centro de la portería."""
    distances = []
    goal_x, goal_y = 1.0, 0.5
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        distance = np.sqrt((float(x) - goal_x)**2 + (float(y) - goal_y)**2) * 100
        distances.append(distance)
    
    return pd.Series(distances, index=x_coords.index)


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Clasificar disparos en zonas tácticas."""
    zones = []
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x) * 100
        y_pct = float(y) * 100
        
        if x_pct >= 88:
            zones.append('Six_Yard_Box')
        elif x_pct >= 83:
            zones.append('Penalty_Box')
        elif x_pct >= 67:
            zones.append('Penalty_Area_Edge')
        else:
            zones.append('Long_Range')
    
    return pd.Series(zones, index=x_coords.index)


def _apply_shot_filters(df: pd.DataFrame, player_filter: Optional[str], team_filter: Optional[str]) -> pd.DataFrame:
    """Aplicar filtros a eventos de disparos."""
    filtered_df = df.copy()
    
    if player_filter and 'shot_player' in filtered_df.columns:
        player_variations = _generate_name_variations(player_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in player_variations:
            mask |= filtered_df['shot_player'].str.contains(variation, case=False, na=False, regex=False)
        
        filtered_df = filtered_df[mask]
    
    if team_filter and 'shot_team' in filtered_df.columns:
        team_variations = _generate_name_variations(team_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in team_variations:
            mask |= filtered_df['shot_team'].str.contains(variation, case=False, na=False, regex=False)
        
        filtered_df = filtered_df[mask]
    
    return filtered_df


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Asegurar orden adecuado de columnas."""
    if df.empty:
        return df
    
    if entity_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'official_player_name',
            'understat_xg_chain', 'understat_xg_buildup', 'understat_npxg_plus_xa',
            'understat_key_passes', 'understat_np_xg', 'understat_xa'
        ]
    else:
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'understat_ppda_avg', 'understat_deep_completions_total',
            'understat_expected_points_total', 'understat_np_xg_total'
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
# AUTOMATIC ID RETRIEVAL FUNCTIONS
# ====================================================================

def get_match_ids(league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Extraer automáticamente IDs de partidos de Understat para una liga y temporada.
    
    Args:
        league: Código de liga (e.g., 'ESP-La Liga', 'ENG-Premier League')
        season: Temporada en formato YY-YY (e.g., '23-24')
        team_filter: Filtro opcional por nombre de equipo
        
    Returns:
        DataFrame con columnas: match_id, home_team, away_team, date
        
    Raises:
        ValueError: Si la liga o temporada no son válidas
        ConnectionError: Si falla la conexión con Understat
    """
    try:
        from ..scrappers.understat import UnderstatReader
        
        scraper = UnderstatReader(league=league, season=season)
        schedule_data = scraper.read_schedule()
        
        if schedule_data.empty:
            print(f"No matches found for {league} {season}")
            return pd.DataFrame()
        
        # Extraer match_ids y información básica
        match_info = []
        for _, match in schedule_data.iterrows():
            if 'id' in match and pd.notna(match['id']):
                match_info.append({
                    'match_id': int(match['id']),
                    'home_team': match.get('home_team', 'Unknown'),
                    'away_team': match.get('away_team', 'Unknown'), 
                    'date': match.get('datetime', 'Unknown'),
                    'league': league,
                    'season': season
                })
        
        result_df = pd.DataFrame(match_info)
        
        # Aplicar filtro de equipo si se especifica
        if team_filter and not result_df.empty:
            team_variations = _generate_name_variations(team_filter)
            mask = pd.Series([False] * len(result_df))
            
            for variation in team_variations:
                mask |= result_df['home_team'].str.contains(variation, case=False, na=False, regex=False)
                mask |= result_df['away_team'].str.contains(variation, case=False, na=False, regex=False)
            
            result_df = result_df[mask]
        
        print(f"Found {len(result_df)} matches for {league} {season}")
        if team_filter:
            print(f"Filtered by team: {team_filter}")
            
        return result_df.sort_values('date').reset_index(drop=True)
        
    except ImportError as e:
        raise ConnectionError(f"Cannot import Understat scraper: {e}")
    except Exception as e:
        raise ConnectionError(f"Error retrieving match IDs from Understat: {e}")


def search_player_id(player_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
    """
    Buscar automáticamente información de jugador en Understat.
    
    Args:
        player_name: Nombre del jugador a buscar
        league: Código de liga
        season: Temporada en formato YY-YY
        
    Returns:
        Dict con player_id y datos básicos del jugador, o None si no se encuentra
    """
    try:
        # Usar extract_data existente para verificar si el jugador existe
        player_data = extract_data(player_name, 'player', league, season)
        
        if player_data:
            return {
                'player_name': player_data.get('official_player_name', player_name),
                'team': player_data.get('team'),
                'league': league,
                'season': season,
                'found': True,
                'understat_data_available': True
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching for player {player_name}: {e}")
        return None


def search_team_id(team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
    """
    Buscar automáticamente información de equipo en Understat.
    
    Args:
        team_name: Nombre del equipo a buscar
        league: Código de liga
        season: Temporada en formato YY-YY
        
    Returns:
        Dict con team_id y datos básicos del equipo, o None si no se encuentra
    """
    try:
        # Usar extract_data existente para verificar si el equipo existe
        team_data = extract_data(team_name, 'team', league, season)
        
        if team_data:
            return {
                'team_name': team_data.get('official_team_name', team_name),
                'league': league,
                'season': season,
                'found': True,
                'understat_data_available': True
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching for team {team_name}: {e}")
        return None


# ====================================================================
# QUICK ACCESS FUNCTIONS - SIMPLIFIED API
# ====================================================================

def get_player(player_name: str, league: str, season: str, use_cache: bool = True) -> Optional[Dict]:
    """Extracción rápida de métricas avanzadas de jugador."""
    return extract_data(player_name, 'player', league, season, use_cache=use_cache)

def get_team(team_name: str, league: str, season: str, use_cache: bool = True) -> Optional[Dict]:
    """Extracción rápida de métricas avanzadas de equipo."""
    return extract_data(team_name, 'team', league, season, use_cache=use_cache)

def get_players(players: List[str], league: str, season: str, max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Extracción rápida de múltiples jugadores con procesamiento paralelo."""
    return extract_multiple(players, 'player', league, season, max_workers=max_workers, show_progress=show_progress)

def get_teams(teams: List[str], league: str, season: str, max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Extracción rápida de múltiples equipos con procesamiento paralelo."""
    return extract_multiple(teams, 'team', league, season, max_workers=max_workers, show_progress=show_progress)

def get_shots(match_id: int, league: str, season: str, player_filter: Optional[str] = None) -> pd.DataFrame:
    """Extracción rápida de eventos de disparos."""
    return extract_shot_events(match_id, league, season, player_filter=player_filter)