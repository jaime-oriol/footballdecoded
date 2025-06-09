# ====================================================================
# FootballDecoded - Quick Data Extractor for Pass Network Testing
# ====================================================================
# Script para extraer y guardar datos de WhoScored rápidamente
# ====================================================================

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import os
from datetime import datetime

# ====================================================================
# EXTRACTOR PRINCIPAL
# ====================================================================

def extract_match_data_for_visualization(
    match_id: int,
    league: str,
    season: str,
    save_path: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Extrae y procesa datos completos del partido para visualización.
    
    Args:
        match_id: ID del partido en WhoScored
        league: Liga (ej: "ESP-La Liga")
        season: Temporada (ej: "2024-25") 
        save_path: Directorio donde guardar CSVs (opcional)
        verbose: Mostrar progreso
        
    Returns:
        Dict con DataFrames procesados: 'passes', 'players', 'connections'
    """
    from wrappers import whoscored_extract_match_events
    
    if verbose:
        print(f"🔍 Extrayendo datos del partido {match_id}")
        print(f"   Liga: {league} | Temporada: {season}")
    
    # 1. EXTRAER EVENTOS COMPLETOS
    if verbose:
        print("📊 Obteniendo eventos del partido...")
    
    events_df = whoscored_extract_match_events(
        match_id=match_id,
        league=league,
        season=season,
        verbose=False
    )
    
    if events_df.empty:
        raise ValueError(f"No se pudieron extraer eventos del partido {match_id}")
    
    if verbose:
        print(f"   ✅ {len(events_df)} eventos extraídos")
    
    # 2. FILTRAR Y PROCESAR PASES
    passes_df = _extract_pass_data(events_df, verbose)
    
    # 3. CALCULAR POSICIONES PROMEDIO DE JUGADORES
    players_df = _calculate_player_positions(passes_df, verbose)
    
    # 4. CALCULAR CONEXIONES ENTRE JUGADORES
    connections_df = _calculate_pass_connections(passes_df, verbose)
    
    # 5. GUARDAR DATOS SI SE ESPECIFICA RUTA
    if save_path:
        _save_processed_data(
            {'passes': passes_df, 'players': players_df, 'connections': connections_df},
            save_path, match_id, verbose
        )
    
    if verbose:
        print("✅ Extracción completada")
    
    return {
        'passes': passes_df,
        'players': players_df, 
        'connections': connections_df
    }


# ====================================================================
# PROCESAMIENTO DE PASES
# ====================================================================

def _extract_pass_data(events_df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Filtra y limpia eventos de pase."""
    
    if verbose:
        print("🔄 Procesando eventos de pase...")
    
    # Filtrar solo pases
    passes_mask = events_df['event_type'].str.contains('Pass', case=False, na=False)
    passes_df = events_df[passes_mask].copy()
    
    if passes_df.empty:
        raise ValueError("No se encontraron eventos de pase")
    
    # Limpiar y estandarizar datos
    passes_clean = passes_df[[
        'player', 'team', 'x', 'y', 'end_x', 'end_y',
        'minute', 'second', 'is_successful', 'outcome_type'
    ]].copy()
    
    # Convertir coordenadas a numéricas
    coord_cols = ['x', 'y', 'end_x', 'end_y']
    for col in coord_cols:
        passes_clean[col] = pd.to_numeric(passes_clean[col], errors='coerce')
    
    # Filtrar pases válidos (con coordenadas)
    valid_coords = passes_clean[coord_cols].notna().all(axis=1)
    passes_clean = passes_clean[valid_coords]
    
    # Convertir coordenadas WhoScored (0-100) a campo real (metros)
    passes_clean['field_x'] = (passes_clean['x'] / 100) * 105  # 105m campo
    passes_clean['field_y'] = (passes_clean['y'] / 100) * 68   # 68m campo
    passes_clean['field_end_x'] = (passes_clean['end_x'] / 100) * 105
    passes_clean['field_end_y'] = (passes_clean['end_y'] / 100) * 68
    
    # Calcular distancia del pase
    passes_clean['pass_distance'] = np.sqrt(
        (passes_clean['field_end_x'] - passes_clean['field_x'])**2 + 
        (passes_clean['field_end_y'] - passes_clean['field_y'])**2
    )
    
    # Solo pases exitosos para red de pases
    successful_passes = passes_clean[passes_clean['is_successful'] == True]
    
    if verbose:
        total_passes = len(passes_clean)
        successful_count = len(successful_passes)
        success_rate = (successful_count / total_passes * 100) if total_passes > 0 else 0
        
        print(f"   📊 {total_passes} pases totales")
        print(f"   ✅ {successful_count} pases exitosos ({success_rate:.1f}%)")
    
    return successful_passes


# ====================================================================
# CÁLCULO DE POSICIONES
# ====================================================================

def _calculate_player_positions(passes_df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Calcula posiciones promedio y estadísticas por jugador."""
    
    if verbose:
        print("📍 Calculando posiciones promedio de jugadores...")
    
    # Agrupar por jugador y equipo
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',           # Posición X promedio
        'field_y': 'mean',           # Posición Y promedio  
        'player': 'count',           # Total de pases realizados
        'pass_distance': 'mean',     # Distancia promedio de pases
        'minute': ['min', 'max']     # Minutos de juego
    }).round(2)
    
    # Aplanar columnas MultiIndex
    player_stats.columns = [
        'avg_x', 'avg_y', 'total_passes', 'avg_pass_distance', 'min_minute', 'max_minute'
    ]
    
    # Calcular minutos jugados aproximados
    player_stats['minutes_played'] = player_stats['max_minute'] - player_stats['min_minute']
    
    # Calcular tamaño de nodo (proporcional a pases)
    min_passes = player_stats['total_passes'].min()
    max_passes = player_stats['total_passes'].max()
    
    if max_passes > min_passes:
        # Normalizar entre 300-1200 para tamaños de nodo
        normalized = (player_stats['total_passes'] - min_passes) / (max_passes - min_passes)
        player_stats['node_size'] = 300 + (normalized * 900)
    else:
        player_stats['node_size'] = 600  # Tamaño fijo si todos igual
    
    # Reset index para tener player y team como columnas
    player_stats = player_stats.reset_index()
    
    if verbose:
        total_players = len(player_stats)
        teams = player_stats['team'].unique()
        print(f"   👥 {total_players} jugadores procesados")
        print(f"   🏟️ Equipos: {', '.join(teams)}")
    
    return player_stats


# ====================================================================
# CÁLCULO DE CONEXIONES
# ====================================================================

def _calculate_pass_connections(passes_df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Calcula conexiones de pases entre jugadores."""
    
    if verbose:
        print("🔗 Calculando conexiones entre jugadores...")
    
    # Ordenar por tiempo para secuencia de pases
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    
    # Lista para almacenar conexiones
    connections = []
    
    # Ventana de tiempo para considerar pases conectados (10 segundos)
    time_window = 10
    
    for i in range(len(passes_sorted) - 1):
        current_pass = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
        # Solo si es del mismo equipo
        if current_pass['team'] != next_pass['team']:
            continue
        
        # Calcular diferencia de tiempo
        time_current = current_pass['minute'] * 60 + current_pass['second']
        time_next = next_pass['minute'] * 60 + next_pass['second']
        time_diff = time_next - time_current
        
        # Solo si está dentro de la ventana de tiempo
        if 0 < time_diff <= time_window:
            connections.append({
                'team': current_pass['team'],
                'source': current_pass['player'],
                'target': next_pass['player'],
                'source_x': current_pass['field_x'],
                'source_y': current_pass['field_y'],
                'target_x': next_pass['field_x'],
                'target_y': next_pass['field_y']
            })
    
    if not connections:
        return pd.DataFrame()
    
    # Convertir a DataFrame y agrupar
    connections_df = pd.DataFrame(connections)
    
    # Contar conexiones entre jugadores (direccional)
    connection_counts = connections_df.groupby(['team', 'source', 'target']).agg({
        'source_x': 'mean',
        'source_y': 'mean', 
        'target_x': 'mean',
        'target_y': 'mean',
        'team': 'count'  # Contar conexiones
    }).round(2)
    
    connection_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
    connection_counts = connection_counts.reset_index()
    
    # Calcular grosor de línea estilo StatsBomb (mínimo 5 pases)
    connection_counts['line_width'] = connection_counts['pass_count'].apply(_calculate_statsbomb_thickness)
    
    # Filtrar solo conexiones con al menos 5 pases
    significant_connections = connection_counts[connection_counts['pass_count'] >= 5]
    
    if verbose:
        total_connections = len(connection_counts)
        significant_count = len(significant_connections)
        print(f"   🔗 {total_connections} conexiones totales")
        print(f"   ⚡ {significant_count} conexiones significativas (≥5 pases)")
    
    return significant_connections


def _calculate_statsbomb_thickness(pass_count: int) -> float:
    """Calcula grosor de línea estilo StatsBomb."""
    if pass_count < 5:
        return 0  # No mostrar
    elif 5 <= pass_count < 10:
        return 2.0
    elif 10 <= pass_count < 15:
        return 3.5
    elif 15 <= pass_count < 20:
        return 5.0
    elif 20 <= pass_count < 25:
        return 6.5
    else:
        return 8.0  # Máximo grosor


# ====================================================================
# GUARDADO DE DATOS
# ====================================================================

def _save_processed_data(data_dict: Dict[str, pd.DataFrame], save_path: str, 
                        match_id: int, verbose: bool = True):
    """Guarda DataFrames procesados en CSVs."""
    
    # Crear directorio si no existe
    os.makedirs(save_path, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files_created = []
    for data_type, df in data_dict.items():
        if df.empty:
            continue
            
        filename = f"match_{match_id}_{data_type}_{timestamp}.csv"
        filepath = os.path.join(save_path, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        files_created.append(filepath)
    
    if verbose:
        print(f"💾 Datos guardados en: {save_path}")
        for file in files_created:
            print(f"   📄 {os.path.basename(file)}")


# ====================================================================
# FUNCIÓN DE CARGA RÁPIDA
# ====================================================================

def load_processed_data(data_dir: str, match_id: int) -> Dict[str, pd.DataFrame]:
    """Carga datos previamente procesados desde CSVs."""
    
    data_dict = {}
    data_types = ['passes', 'players', 'connections']
    
    for data_type in data_types:
        # Buscar archivo más reciente para este match_id y tipo
        pattern = f"match_{match_id}_{data_type}_"
        files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
        
        if files:
            # Tomar el más reciente
            latest_file = sorted(files)[-1]
            filepath = os.path.join(data_dir, latest_file)
            data_dict[data_type] = pd.read_csv(filepath)
            print(f"📂 Cargado: {latest_file}")
        else:
            data_dict[data_type] = pd.DataFrame()
            print(f"⚠️ No encontrado: {data_type} para match {match_id}")
    
    return data_dict


# ====================================================================
# SCRIPTS DE EJEMPLO
# ====================================================================

def extract_athletic_barcelona_data():
    """Script específico para el partido Athletic vs Barcelona."""
    
    print("🔍 EXTRACCIÓN RÁPIDA: Athletic Club vs Barcelona")
    print("=" * 50)
    
    match_data = extract_match_data_for_visualization(
        match_id=1821769,
        league="ESP-La Liga",
        season="2024-25",
        save_path="./match_data",
        verbose=True
    )
    
    print("\n📊 RESUMEN DE DATOS EXTRAÍDOS:")
    print(f"   Pases: {len(match_data['passes'])}")
    print(f"   Jugadores: {len(match_data['players'])}")
    print(f"   Conexiones: {len(match_data['connections'])}")
    
    return match_data


def quick_team_summary(match_data: Dict[str, pd.DataFrame]):
    """Resumen rápido por equipo."""
    
    players_df = match_data['players']
    connections_df = match_data['connections']
    
    print("\n👥 RESUMEN POR EQUIPO:")
    for team in players_df['team'].unique():
        team_players = players_df[players_df['team'] == team]
        team_connections = connections_df[connections_df['team'] == team]
        
        total_passes = team_players['total_passes'].sum()
        avg_connections = len(team_connections)
        
        print(f"   🏟️ {team}:")
        print(f"      - {len(team_players)} jugadores")
        print(f"      - {total_passes} pases exitosos")
        print(f"      - {avg_connections} conexiones significativas")


# ====================================================================
# MAIN EXECUTION
# ====================================================================

if __name__ == "__main__":
    # Extraer datos del partido Athletic vs Barcelona
    try:
        match_data = extract_athletic_barcelona_data()
        quick_team_summary(match_data)
        
        print("\n✅ Datos listos para visualización!")
        print("💡 Usar: visualizar_red_pases.py con estos datos")
        
    except Exception as e:
        print(f"❌ Error durante extracción: {e}")