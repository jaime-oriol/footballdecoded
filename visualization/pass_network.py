# ====================================================================
# FootballDecoded - Extractor de Datos de Partidos
# ====================================================================
# Módulo genérico para extraer y procesar datos de cualquier partido
# ====================================================================

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, Tuple
from datetime import datetime

# ====================================================================
# CONFIGURACIÓN
# ====================================================================

# Directorio de datos relativo al archivo actual
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ====================================================================
# EXTRACCIÓN DE DATOS
# ====================================================================

def extract_match_data(match_id: int, league: str, season: str, 
                      force_reload: bool = False, verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Extrae y procesa datos completos de un partido.
    
    Args:
        match_id: ID del partido
        league: Liga (ej: "ESP-La Liga")
        season: Temporada (ej: "2024-25")
        force_reload: Si True, re-extrae aunque existan los datos
        verbose: Mostrar progreso
        
    Returns:
        Dict con 'passes', 'players', 'connections'
    """
    if verbose:
        print(f"🎯 Procesando partido {match_id} ({league} {season})")
    
    # Verificar si los datos ya existen
    if not force_reload and _data_exists(match_id):
        if verbose:
            print("   📂 Datos encontrados, cargando desde archivos...")
        return load_match_data(match_id)
    
    # Extraer datos nuevos
    if verbose:
        print("   🔍 Extrayendo datos desde WhoScored...")
    
    try:
        from wrappers import whoscored_extract_match_events
        events_df = whoscored_extract_match_events(match_id, league, season, verbose=False)
        
        if events_df.empty:
            raise ValueError(f"No se encontraron eventos para el partido {match_id}")
        
        # Procesar datos
        passes_df = _process_passes(events_df, verbose)
        players_df = _calculate_players(passes_df, verbose)
        connections_df = _calculate_connections(passes_df, verbose)
        
        result = {
            'passes': passes_df,
            'players': players_df, 
            'connections': connections_df
        }
        
        # Guardar automáticamente
        save_match_data(result, match_id, verbose)
        
        return result
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Error en extracción: {e}")
        raise


def load_match_data(match_id: int) -> Dict[str, pd.DataFrame]:
    """Carga datos previamente procesados."""
    result = {}
    
    for data_type in ['passes', 'players', 'connections']:
        filepath = _get_filepath(match_id, data_type)
        
        if os.path.exists(filepath):
            result[data_type] = pd.read_csv(filepath)
        else:
            result[data_type] = pd.DataFrame()
    
    return result


def save_match_data(data_dict: Dict[str, pd.DataFrame], match_id: int, verbose: bool = True):
    """Guarda datos procesados en CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for data_type, df in data_dict.items():
        if not df.empty:
            filepath = _get_filepath(match_id, data_type)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            if verbose:
                print(f"   💾 Guardado: {data_type} ({len(df)} filas)")


# ====================================================================
# PROCESAMIENTO DE DATOS
# ====================================================================

def _process_passes(events_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Extrae y limpia pases exitosos."""
    
    # Filtrar solo pases exitosos
    passes = events_df[
        events_df['event_type'].str.contains('Pass', case=False, na=False) & 
        (events_df['is_successful'] == True)
    ].copy()
    
    if passes.empty:
        raise ValueError("No se encontraron pases exitosos")
    
    # Convertir coordenadas a metros de campo
    passes['field_x'] = (passes['x'] / 100) * 105
    passes['field_y'] = (passes['y'] / 100) * 68
    
    # Calcular distancia del pase si hay coordenadas de destino
    if 'end_x' in passes.columns and 'end_y' in passes.columns:
        passes['field_end_x'] = (passes['end_x'] / 100) * 105
        passes['field_end_y'] = (passes['end_y'] / 100) * 68
        passes['pass_distance'] = np.sqrt(
            (passes['field_end_x'] - passes['field_x'])**2 + 
            (passes['field_end_y'] - passes['field_y'])**2
        )
    
    # Seleccionar columnas esenciales
    essential_cols = ['player', 'team', 'field_x', 'field_y', 'minute', 'second']
    if 'pass_distance' in passes.columns:
        essential_cols.append('pass_distance')
    
    passes_clean = passes[essential_cols].copy()
    
    if verbose:
        teams = passes_clean['team'].unique()
        print(f"   ✅ {len(passes_clean)} pases | Equipos: {', '.join(teams)}")
    
    return passes_clean


def _calculate_players(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calcula posiciones medias y estadísticas de jugadores."""
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',
        'field_y': 'mean',
        'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    
    # Calcular tamaños de nodo según escala de referencia (1 pase = min, 50+ = max)
    min_size = 800   # Para 1 pase
    max_size = 4000  # Para 50+ pases
    
    def calculate_node_size(passes):
        if passes <= 1:
            return min_size
        elif passes >= 50:
            return max_size
        else:
            ratio = (passes - 1) / (50 - 1)
            return min_size + (ratio * (max_size - min_size))
    
    player_stats['node_size'] = player_stats['total_passes'].apply(calculate_node_size)
    
    result = player_stats.reset_index()
    
    if verbose:
        print(f"   👥 {len(result)} jugadores procesados")
    
    return result


def _calculate_connections(passes_df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    """Calcula conexiones de pases entre jugadores."""
    
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    connections = []
    
    # Ventana de 10 segundos para pases conectados
    for i in range(len(passes_sorted) - 1):
        current = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
        # Solo pases del mismo equipo
        if current['team'] != next_pass['team']:
            continue
        
        time_diff = (next_pass['minute'] * 60 + next_pass['second']) - \
                   (current['minute'] * 60 + current['second'])
        
        if 0 < time_diff <= 10:
            connections.append({
                'team': current['team'],
                'source': current['player'],
                'target': next_pass['player'],
                'source_x': current['field_x'],
                'source_y': current['field_y'],
                'target_x': next_pass['field_x'],
                'target_y': next_pass['field_y']
            })
    
    if not connections:
        if verbose:
            print("   ⚠️ No se encontraron conexiones")
        return pd.DataFrame()
    
    # Agrupar y contar conexiones
    connections_df = pd.DataFrame(connections)
    connection_counts = connections_df.groupby(['team', 'source', 'target']).agg({
        'source_x': 'mean',
        'source_y': 'mean',
        'target_x': 'mean',
        'target_y': 'mean',
        'team': 'count'
    }).round(1)
    
    connection_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
    result = connection_counts.reset_index()
    
    # Añadir ancho de línea mejorado
    result['line_width'] = result['pass_count'].apply(_get_line_width_enhanced)
    
    # Contar conexiones significativas (ahora desde 4 pases)
    significant_count = len(result[result['pass_count'] >= 4])
    
    if verbose:
        print(f"   🔗 {len(result)} conexiones totales ({significant_count} significativas ≥4 pases)")
    
    return result


def _get_line_width_enhanced(count: int) -> float:
    """Calcula ancho de línea con mayor diferenciación basado en número de pases."""
    if count < 4: return 0.0
    elif count < 8: return 2.0
    elif count < 15: return 4.5
    elif count < 25: return 7.0
    else: return 10.0


# ====================================================================
# UTILIDADES
# ====================================================================

def _data_exists(match_id: int) -> bool:
    """Verifica si existen todos los archivos de datos."""
    for data_type in ['passes', 'players', 'connections']:
        if not os.path.exists(_get_filepath(match_id, data_type)):
            return False
    return True


def _get_filepath(match_id: int, data_type: str) -> str:
    """Genera ruta de archivo para un tipo de datos."""
    filename = f"match_{match_id}_{data_type}.csv"
    return os.path.join(DATA_DIR, filename)


def get_team_summary(match_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """Obtiene resumen rápido por equipo."""
    summary = {}
    players_df = match_data['players']
    connections_df = match_data['connections']
    
    for team in players_df['team'].unique():
        team_players = players_df[players_df['team'] == team]
        team_connections = connections_df[connections_df['team'] == team] if not connections_df.empty else pd.DataFrame()
        
        summary[team] = {
            'players': len(team_players),
            'total_passes': team_players['total_passes'].sum(),
            'connections': len(team_connections)
        }
    
    return summary


def filter_team_data(match_data: Dict[str, pd.DataFrame], team_name: str) -> Dict[str, pd.DataFrame]:
    """Filtra datos para un equipo específico."""
    team_players = match_data['players'][match_data['players']['team'] == team_name]
    team_connections = match_data['connections'][match_data['connections']['team'] == team_name] if not match_data['connections'].empty else pd.DataFrame()
    team_passes = match_data['passes'][match_data['passes']['team'] == team_name]
    
    return {
        'passes': team_passes,
        'players': team_players,
        'connections': team_connections
    }


# ====================================================================
# FUNCIONES DE CONVENIENCIA PARA TESTING
# ====================================================================

def quick_extract_athletic_barcelona(match_id: int = 1821769, 
                                   league: str = "ESP-La Liga", 
                                   season: str = "2024-25") -> Dict[str, pd.DataFrame]:
    """Función de conveniencia para extraer el partido Athletic vs Barcelona."""
    return extract_match_data(match_id, league, season, verbose=True)


def quick_visualize_barcelona(match_id: int = 1821769) -> None:
    """Visualización rápida de Barcelona."""
    from pass_network import create_pass_network
    
    # Cargar datos
    match_data = load_match_data(match_id)
    if not match_data or match_data['players'].empty:
        print("❌ No hay datos guardados. Ejecuta extract_match_data() primero.")
        return
    
    # Crear visualización
    fig = create_pass_network(match_data, "Barcelona")
    return fig


def quick_visualize_athletic(match_id: int = 1821769) -> None:
    """Visualización rápida de Athletic Club."""
    from pass_network import create_pass_network
    
    # Cargar datos
    match_data = load_match_data(match_id)
    if not match_data or match_data['players'].empty:
        print("❌ No hay datos guardados. Ejecuta extract_match_data() primero.")
        return
    
    # Crear visualización
    fig = create_pass_network(match_data, "Athletic Club")
    return fig