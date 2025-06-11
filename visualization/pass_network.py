# ====================================================================
# FootballDecoded - Visualizador de Redes de Pase MEJORADO
# ====================================================================
# Escalado gradual sin umbrales abruptos para máxima diferenciación visual
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime

# ====================================================================
# CONFIGURACIÓN MEJORADA
# ====================================================================

# Configuración del campo
FIELD_CONFIG = {
    'length': 105,
    'width': 68,
    'color': 'white',
    'line_color': 'black',
    'line_width': 2.5,
    'goal_color': '#333333',
    'goal_width': 8.0
}

# Configuración de conexiones
CONNECTION_CONFIG = {
    'alpha': 0.8,
    'base_offset': 0.4,
    'arrow_length': 1.0,
    'arrow_width': 0.6,
    'name_margin': 2.0
}

# Configuración de escalas graduales MEJORADAS
SCALE_CONFIG = {
    'node_size_min': 500,           # Tamaño mínimo de nodo
    'node_size_max': 10000,         # Tamaño máximo de nodo
    'node_threshold_halves': 10,    # Umbral para partes (≤10 = tamaño mínimo)
    'node_threshold_full_match': 20, # Umbral para partido completo (≤20 = tamaño mínimo)
    'line_width_min': 1.0,          # Grosor mínimo de línea
    'line_width_max': 8.0,          # Grosor máximo de línea
    'name_length_threshold': 10     # Longitud máxima antes de usar solo apellido
}

# Configuración de conexiones ORIGINAL
CONNECTION_CONFIG = {
    'min_passes_halves': 4,       # Mínimo para partes (primera/segunda)
    'min_passes_full_match': 8,   # Mínimo para partido completo
    'alpha': 0.8,
    'base_offset': 0.4,
    'arrow_length': 1.0,
    'arrow_width': 0.6,
    'name_margin': 2.0
}

# Configuración de fuente
FONT_CONFIG = {
    'family': 'DejaVu Sans',
    'fallback': 'sans-serif'
}

# Configuración de división por partes
HALVES_CONFIG = {
    'first_half_end': 44,
    'second_half_start': 45,
    'match_end': 120
}

# Colores por equipo
TEAM_COLORS = {
    'Barcelona': {'primary': '#A50044', 'secondary': '#004D98'},
    'Real Madrid': {'primary': '#FEBE10', 'secondary': '#002147'},
    'Athletic': {'primary': '#E30613', 'secondary': '#FFFFFF'},
    'Athletic Club': {'primary': '#E30613', 'secondary': '#FFFFFF'},
    'Manchester City': {'primary': '#6CABDD', 'secondary': '#1C2C5B'},
    'Liverpool': {'primary': '#C8102E', 'secondary': '#00B2A9'},
    'default': {'primary': '#2E4A87', 'secondary': '#1A365D'}
}

# ====================================================================
# SISTEMA GRADUAL MEJORADO - SIN UMBRALES ABRUPTOS
# ====================================================================

def calculate_dynamic_node_sizes(players_df: pd.DataFrame, is_full_match: bool = False) -> pd.DataFrame:
    """
    Calcula tamaños de nodos dinámicamente con umbral base y escalado más gradual.
    
    Args:
        players_df: DataFrame con jugadores y sus total_passes
        is_full_match: True para partido completo (+90 min), False para partes
        
    Returns:
        DataFrame con columna 'node_size' añadida/actualizada
    """
    if players_df.empty:
        return players_df
    
    # Crear copia para no modificar original
    df_with_sizes = players_df.copy()
    
    # Obtener rango de pases SOLO de estos jugadores
    max_passes = df_with_sizes['total_passes'].max()
    
    # Seleccionar umbral según el contexto (MANTENER ORIGINAL)
    threshold = SCALE_CONFIG['node_threshold_full_match'] if is_full_match else SCALE_CONFIG['node_threshold_halves']
    
    # Calcular tamaño para cada jugador con escalado MÁS GRADUAL
    df_with_sizes['node_size'] = df_with_sizes['total_passes'].apply(
        lambda passes: _calculate_single_node_size_with_threshold_gradual(passes, max_passes, threshold)
    )
    
    return df_with_sizes

def calculate_dynamic_line_widths(connections_df: pd.DataFrame, is_full_match: bool = False) -> pd.DataFrame:
    """
    Calcula grosores de línea dinámicamente con mínimo configurable.
    
    Args:
        connections_df: DataFrame con conexiones y sus pass_count
        is_full_match: True para partido completo (+90 min), False para partes
        
    Returns:
        DataFrame con columna 'line_width' añadida/actualizada
    """
    if connections_df.empty:
        return connections_df
    
    # Crear copia para no modificar original
    df_with_widths = connections_df.copy()
    
    # Seleccionar mínimo según el contexto (MANTENER ORIGINAL)
    min_passes_required = CONNECTION_CONFIG['min_passes_full_match'] if is_full_match else CONNECTION_CONFIG['min_passes_halves']
    
    # Filtrar conexiones válidas
    valid_connections = df_with_widths[df_with_widths['pass_count'] >= min_passes_required]
    
    if valid_connections.empty:
        df_with_widths['line_width'] = 0.0
        return df_with_widths
    
    # Obtener rango de conexiones SOLO de estas conexiones válidas
    min_connections = valid_connections['pass_count'].min()
    max_connections = valid_connections['pass_count'].max()
    
    # Calcular grosor para cada conexión con escalado MÁS GRADUAL
    df_with_widths['line_width'] = df_with_widths['pass_count'].apply(
        lambda count: _calculate_single_line_width_gradual(count, min_connections, max_connections, min_passes_required)
    )
    
    return df_with_widths

def _calculate_single_node_size_with_threshold_gradual(total_passes: int, max_passes: int, threshold: int) -> float:
    """
    Calcula tamaño de nodo con escalado lineal fijo.
    
    Lógica fija:
    - ≤5 pases → 500
    - ≥120 pases → 12,000  
    - Entre 6-119 → 500 + (pases - 5) × 100
    """
    # Mínimo: ≤5 pases
    if total_passes <= 5:
        return 500
    
    # Máximo: ≥120 pases
    if total_passes >= 120:
        return 12000
    
    # Escalado lineal entre 6-119 pases
    # Cada pase adicional suma exactamente 100 unidades
    return 500 + (total_passes - 5) * 100

def _calculate_single_line_width_gradual(pass_count: int, min_connections: int, max_connections: int, min_required: int) -> float:
    """
    Calcula grosor de línea individual con escalado MÁS GRADUAL.
    """
    # Si no cumple el mínimo, grosor 0
    if pass_count < min_required:
        return 0.0
    
    if max_connections == min_connections:
        # Si todas las conexiones válidas tienen el mismo valor
        return (SCALE_CONFIG['line_width_min'] + SCALE_CONFIG['line_width_max']) / 2
    
    # Normalización lineal (0 a 1)
    normalized = (pass_count - min_connections) / (max_connections - min_connections)
    
    # Aplicar curva MÁS SUAVE para grosores menos agresivos (0.6 en lugar de 0.8)
    curved = normalized ** 0.6
    
    # Escalar al rango de grosores configurado
    return SCALE_CONFIG['line_width_min'] + curved * (
        SCALE_CONFIG['line_width_max'] - SCALE_CONFIG['line_width_min']
    )

def get_node_radius_from_size(node_size: float) -> float:
    """Convierte tamaño de nodo a radio para cálculos."""
    return np.sqrt(node_size / np.pi) * 0.105

# ====================================================================
# FUNCIÓN PRINCIPAL - PARTIDO COMPLETO (ACTUALIZADA)
# ====================================================================

def create_pass_network(match_data: Dict[str, pd.DataFrame], 
                       team_name: str,
                       title: Optional[str] = None,
                       show_labels: bool = True,
                       figsize: Tuple[int, int] = (18, 14),
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización de red de pases con sistema gradual MEJORADO.
    """
    from match_data import filter_team_data
    
    # Filtrar datos del equipo
    team_data = filter_team_data(match_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name}")
    
    print(f"\n🎯 Creando red de pases para {team_name} (Partido completo)")
    
    # Calcular tamaños con sistema GRADUAL MEJORADO
    team_players_with_sizes = calculate_dynamic_node_sizes(team_data['players'], is_full_match=True)
    team_connections_with_widths = calculate_dynamic_line_widths(team_data['connections'], is_full_match=True)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Dibujar campo
    _draw_pitch(ax)
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar red de pases
    _draw_connections_unified(ax, team_connections_with_widths, team_players_with_sizes, colors['secondary'])
    _draw_players_unified(ax, team_players_with_sizes, colors['primary'])
    
    if show_labels:
        _draw_optimized_labels(ax, team_players_with_sizes)
    
    # Añadir leyenda mejorada
    _draw_enhanced_legend_unified(ax, team_players_with_sizes, team_connections_with_widths, team_name)
    
    # Configurar ejes
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 68)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado: {save_path}")
    
    return fig

# ====================================================================
# FUNCIONES DE DIVISIÓN POR PARTES (ACTUALIZADAS)
# ====================================================================

def create_pass_network_by_halves(match_data: Dict[str, pd.DataFrame], 
                                 team_name: str,
                                 save_individual: bool = True,
                                 show_labels: bool = True,
                                 figsize: Tuple[int, int] = (36, 14),
                                 save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización dual con sistema gradual MEJORADO.
    """
    print(f"\n🎯 Creando análisis por partes para {team_name}")
    
    # Procesar datos por partes
    first_half_data = _process_half_data(match_data, team_name, "first")
    second_half_data = _process_half_data(match_data, team_name, "second")
    
    if first_half_data['players'].empty and second_half_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name} en ninguna parte")
    
    # Calcular tamaños con sistema MEJORADO (mantiene umbral 10) para cada parte
    if not first_half_data['players'].empty:
        first_half_data['players'] = calculate_dynamic_node_sizes(first_half_data['players'], is_full_match=False)
        first_half_data['connections'] = calculate_dynamic_line_widths(first_half_data['connections'], is_full_match=False)
    
    if not second_half_data['players'].empty:
        second_half_data['players'] = calculate_dynamic_node_sizes(second_half_data['players'], is_full_match=False)
        second_half_data['connections'] = calculate_dynamic_line_widths(second_half_data['connections'], is_full_match=False)
    
    # Crear figura dual
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, facecolor='white')
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar primera parte
    _draw_half_visualization_unified(ax1, first_half_data, colors, "Primera Parte", show_labels)
    
    # Dibujar segunda parte
    _draw_half_visualization_unified(ax2, second_half_data, colors, "Segunda Parte", show_labels)
    
    # Título general
    fig.suptitle(f"{team_name} - Evolución Táctica por Partes", 
                fontsize=20, fontweight='bold', y=0.95, family=FONT_CONFIG['family'])
    
    plt.tight_layout()
    
    # Guardar gráfico dual
    if save_path:
        dual_path = save_path.replace('.png', '_dual_halves.png')
        fig.savefig(dual_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado dual: {dual_path}")
    
    # Guardar gráficos individuales si se solicita
    if save_individual:
        _save_individual_halves_unified(first_half_data, second_half_data, team_name, colors, 
                                      show_labels, save_path)
    
    return fig

def create_pass_network_single_half(match_data: Dict[str, pd.DataFrame], 
                                   team_name: str,
                                   half: str = "first",
                                   title: Optional[str] = None,
                                   show_labels: bool = True,
                                   figsize: Tuple[int, int] = (18, 14),
                                   save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización de una sola parte con sistema gradual MEJORADO.
    """
    print(f"\n🎯 Creando red de pases para {team_name} ({half} parte)")
    
    # Procesar datos de la parte específica
    half_data = _process_half_data(match_data, team_name, half)
    
    if half_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name} en la {half} parte")
    
    # Calcular tamaños con sistema MEJORADO (mantiene umbral 10)
    half_data['players'] = calculate_dynamic_node_sizes(half_data['players'], is_full_match=False)
    half_data['connections'] = calculate_dynamic_line_widths(half_data['connections'], is_full_match=False)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Título de la parte
    part_title = title or f"{team_name} - {'Primera' if half == 'first' else 'Segunda'} Parte"
    
    # Dibujar visualización
    _draw_half_visualization_unified(ax, half_data, colors, part_title, show_labels)
    
    plt.tight_layout()
    
    if save_path:
        half_suffix = f"_{half}_half"
        half_path = save_path.replace('.png', f'{half_suffix}.png')
        fig.savefig(half_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado {half} parte: {half_path}")
    
    return fig

# ====================================================================
# FUNCIONES DE PROCESAMIENTO POR PARTES (SIN CAMBIOS)
# ====================================================================

def _process_half_data(match_data: Dict[str, pd.DataFrame], team_name: str, half: str) -> Dict[str, pd.DataFrame]:
    """Procesa datos para una parte específica del partido."""
    if half == "first":
        min_minute = 0
        max_minute = HALVES_CONFIG['first_half_end']
    else:  # "second"
        min_minute = HALVES_CONFIG['second_half_start']
        max_minute = HALVES_CONFIG['match_end']
    
    # Filtrar pases por equipo Y tiempo
    all_passes = match_data['passes']
    team_passes = all_passes[all_passes['team'] == team_name]
    
    if team_passes.empty:
        return {'passes': pd.DataFrame(), 'players': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    # Filtrar por tiempo específico
    half_passes = team_passes[
        (team_passes['minute'] >= min_minute) & 
        (team_passes['minute'] <= max_minute)
    ].copy()
    
    if half_passes.empty:
        return {'passes': pd.DataFrame(), 'players': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    # Recalcular estadísticas basado en esta parte
    half_players = _recalculate_players_from_passes(half_passes)
    half_connections = _recalculate_connections_from_passes(half_passes)
    
    return {
        'passes': half_passes,
        'players': half_players,
        'connections': half_connections
    }

def _recalculate_players_from_passes(passes_df: pd.DataFrame) -> pd.DataFrame:
    """Recalcula estadísticas de jugadores basado en pases filtrados."""
    if passes_df.empty:
        return pd.DataFrame()
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',
        'field_y': 'mean',
        'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    
    return player_stats.reset_index()

def _recalculate_connections_from_passes(passes_df: pd.DataFrame) -> pd.DataFrame:
    """Recalcula conexiones basado en pases filtrados."""
    if passes_df.empty:
        return pd.DataFrame()
    
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    connections = []
    
    # Ventana de 10 segundos para pases conectados
    for i in range(len(passes_sorted) - 1):
        current = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
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
    
    return connection_counts.reset_index()

# ====================================================================
# FUNCIONES DE DIBUJO (SIN CAMBIOS MAYORES)
# ====================================================================

def _draw_half_visualization_unified(ax, half_data: Dict[str, pd.DataFrame], colors: Dict, 
                                   title: str, show_labels: bool):
    """Dibuja visualización completa para una parte del partido."""
    _draw_pitch(ax)
    
    if not half_data['connections'].empty:
        _draw_connections_unified(ax, half_data['connections'], half_data['players'], colors['secondary'])
    
    if not half_data['players'].empty:
        _draw_players_unified(ax, half_data['players'], colors['primary'])
        
        if show_labels:
            _draw_optimized_labels(ax, half_data['players'])
    
    _draw_enhanced_legend_unified(ax, half_data['players'], half_data['connections'], title.split(' - ')[0])
    
    ax.text(52.5, 75, title, ha='center', va='center', 
           fontsize=16, fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 78)
    ax.set_aspect('equal')
    ax.axis('off')

def _draw_players_unified(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores usando tamaños calculados."""
    if players_df.empty:
        return
    
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        node_size = player['node_size']
        
        ax.scatter(x, y, s=node_size, 
                  c=color, alpha=0.6,
                  edgecolors=color, linewidth=4,
                  zorder=10)


def _draw_connections_unified(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones usando grosores calculados y gradiente suave perfecto."""
    if connections_df.empty:
        return
    
    valid_connections = connections_df[connections_df['line_width'] > 0]
    if valid_connections.empty:
        return
    
    from matplotlib.collections import LineCollection
    import matplotlib.colors as mcolors
    
    for _, conn in valid_connections.iterrows():
        source_data = players_df[players_df['player'] == conn['source']]
        target_data = players_df[players_df['player'] == conn['target']]
        
        if source_data.empty or target_data.empty:
            continue
        
        source_player = source_data.iloc[0]
        target_player = target_data.iloc[0]
        
        source_radius = get_node_radius_from_size(source_player['node_size'])
        target_radius = get_node_radius_from_size(target_player['node_size'])
        
        start_x, start_y, end_x, end_y = _calculate_connection_points(
            source_player['avg_x'], source_player['avg_y'],
            target_player['avg_x'], target_player['avg_y'],
            source_radius, target_radius, conn['pass_count']
        )
        
        line_width = conn['line_width']
        
        # Crear línea con gradiente perfecto usando LineCollection
        num_points = 50
        x_points = np.linspace(start_x, end_x, num_points)
        y_points = np.linspace(start_y, end_y, num_points)
        
        # Crear segmentos para LineCollection
        points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        alphas = np.linspace(0.1, 1.0, len(segments))
        
        # Convertir color string a RGB y añadir alpha
        rgb = mcolors.to_rgb(color)
        colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
        
        # Crear y añadir LineCollection
        lc = LineCollection(segments, colors=colors_with_alpha, linewidths=line_width,
                           capstyle='round', zorder=1)
        ax.add_collection(lc)
        
        # Dibujar marca al final
        _draw_connection_arrow(ax, start_x, start_y, end_x, end_y, 
                              color, line_width, 1.0)


def _save_individual_halves_unified(first_half_data: Dict[str, pd.DataFrame], 
                                  second_half_data: Dict[str, pd.DataFrame],
                                  team_name: str, colors: Dict, show_labels: bool, 
                                  base_path: Optional[str]):
    """Guarda gráficos individuales de cada parte."""
    if not base_path:
        return
    
    if not first_half_data['players'].empty:
        fig1, ax1 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization_unified(ax1, first_half_data, colors, f"{team_name} - Primera Parte", show_labels)
        plt.tight_layout()
        
        first_path = base_path.replace('.png', '_first_half.png')
        fig1.savefig(first_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"📊 Guardado primera parte: {first_path}")
        plt.close(fig1)
    
    if not second_half_data['players'].empty:
        fig2, ax2 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization_unified(ax2, second_half_data, colors, f"{team_name} - Segunda Parte", show_labels)
        plt.tight_layout()
        
        second_path = base_path.replace('.png', '_second_half.png')
        fig2.savefig(second_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"📊 Guardado segunda parte: {second_path}")
        plt.close(fig2)

# ====================================================================
# LEYENDA MEJORADA (ACTUALIZADA PARA ESCALADO GRADUAL)
# ====================================================================

# ====================================================================
# CAMBIO 1: Función _draw_enhanced_legend_unified
# ====================================================================

def _draw_enhanced_legend_unified(ax, players_df: pd.DataFrame, connections_df: pd.DataFrame, team_name: str):
    """Leyenda con estilo de referencia adaptada a FootballDecoded."""
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    legend_color = colors['primary']
    
    # Posición base
    legend_y = -9
    
    # Estadísticas centrales "Pases: 694" (SIN cambios aquí)
    total_passes = players_df['total_passes'].sum() if not players_df.empty else 0
    ax.text(52.5, legend_y + 0.0, f"Pases: {total_passes}", 
           ha='center', va='center', fontsize=18, fontweight='bold', 
           color=legend_color, family=FONT_CONFIG['family'])
    
    # ELIMINAR COMPLETAMENTE EL TÍTULO "Nº Pases"
    # (Se borra esta línea completamente)
    
    # Dibujar escalas con estilo de referencia
    _draw_reference_style_nodes_legend(ax, 20, legend_y, legend_color, players_df)
    _draw_reference_style_lines_legend(ax, 80, legend_y, legend_color, connections_df)

# ====================================================================
# CAMBIO 2: Función _draw_reference_style_nodes_legend - TAMAÑOS AUMENTADOS
# ====================================================================

def _draw_reference_style_nodes_legend(ax, x: float, y: float, color: str, players_df: pd.DataFrame):
    """Leyenda de nodos con estilo exacto de la referencia - SOLO 2 CÍRCULOS."""
    if players_df.empty:
        return
    
    # Usar valores REALES de este conjunto específico
    min_passes = players_df['total_passes'].min()
    max_passes = players_df['total_passes'].max()
    
    # Determinar umbral (adaptado a FootballDecoded: ≤20 para partido completo)
    threshold = 20 if max_passes > 50 else 10
    
    if min_passes == max_passes:
        # Si todos tienen los mismos pases, mostrar solo un círculo
        node_size = players_df['node_size'].iloc[0] * 0.4
        ax.scatter(x, y + 2, s=node_size, c=color, alpha=0.6, 
                  edgecolors=color, linewidth=2, zorder=10)
        # TAMAÑO AUMENTADO de 10 a 14
        ax.text(x, y - 1.5, f"{int(min_passes)}", ha='center', va='center',
               fontsize=14, fontweight='normal', color='black', 
               family=FONT_CONFIG['family'])
        return
    
    # =============================================
    # SOLO 2 CÍRCULOS: PEQUEÑO Y GRANDE
    # =============================================
    
    # Posiciones horizontales - solo 2
    positions = [x - 8, x + 8]  # Más separados
    circle_y = y + 4  # Más arriba
    
    # Solo mostrar threshold y máximo
    display_values = [threshold, max_passes]
    
    # Crear solo 2 círculos
    for i, (pos, passes) in enumerate(zip(positions, display_values)):
        # Calcular tamaño usando tu sistema unificado
        node_size = _calculate_single_node_size_with_threshold_gradual(int(passes), max_passes, threshold) * 0.4
        
        # Círculo con borde
        ax.scatter(pos, circle_y, s=node_size, c=color, alpha=0.6, 
                  edgecolors=color, linewidth=2, zorder=10)
    
    # =============================================
    # ETIQUETAS SOLO EN EXTREMOS - TAMAÑOS AUMENTADOS
    # =============================================
    
    # Izquierda: ≤threshold - TAMAÑO AUMENTADO de 10 a 14
    ax.text(positions[0], y - 1.5, f"≤5", ha='center', va='center',
           fontsize=14, fontweight='normal', color='black', 
           family=FONT_CONFIG['family'])
    
    # Derecha: máximo valor - TAMAÑO AUMENTADO de 10 a 14
    ax.text(positions[1], y - 1.5, f"{int(max_passes)}", ha='center', va='center',
           fontsize=14, fontweight='normal', color='black', 
           family=FONT_CONFIG['family'])
    
    # =============================================
    # FLECHA PROGRESIVA EN NEGRO - GROSOR AUMENTADO
    # =============================================
    
    # Flecha debajo de los círculos EN NEGRO - GROSOR AUMENTADO de 2 a 3
    arrow_y = y - 0.5
    ax.annotate('', xy=(positions[1] - 2, arrow_y), xytext=(positions[0] + 2, arrow_y),
                arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))

# ====================================================================
# CAMBIO 3: Función _draw_reference_style_lines_legend - TAMAÑOS AUMENTADOS
# ====================================================================

def _draw_reference_style_lines_legend(ax, x: float, y: float, color: str, connections_df: pd.DataFrame):
    """Leyenda de líneas con estilo exacto de la referencia - MÁS CENTRADA."""
    if connections_df.empty:
        return
    
    # Filtrar conexiones válidas (line_width > 0)
    valid_connections = connections_df[connections_df['line_width'] > 0]
    if valid_connections.empty:
        return
    
    # Usar valores REALES de este conjunto específico
    min_conn = valid_connections['pass_count'].min()
    max_conn = valid_connections['pass_count'].max()
    
    # Determinar mínimo requerido (adaptado a FootballDecoded: mín 8 para partido completo)
    min_required = 8 if max_conn > 15 else 4
    
    if min_conn == max_conn:
        # Si todas las conexiones tienen el mismo valor, mostrar solo una línea
        line_width = valid_connections['line_width'].iloc[0]
        # GROSOR AUMENTADO - multiplicar por 1.5
        ax.plot([x - 2, x + 2], [y + 2, y + 2], color=color, 
               linewidth=line_width * 1.5, alpha=0.8, solid_capstyle='round')
        # TAMAÑO AUMENTADO de 10 a 14
        ax.text(x, y - 1.5, f"{int(min_conn)}", ha='center', va='center',
               fontsize=14, fontweight='normal', color='black',
               family=FONT_CONFIG['family'])
        return
    
    # =============================================
    # LÍNEAS MÁS CENTRADAS Y ORGANIZADAS - GROSORES AUMENTADOS
    # =============================================
    
    positions = [x - 9, x - 3, x + 3, x + 9]  # 4 líneas equidistantes y centradas
    line_y = y + 2  # Misma altura que círculos
    
    # Valores progresivos más equilibrados
    step = (max_conn - min_required) / 3 if max_conn > min_required else 1
    display_values = [
        min_required,
        min_required + step,
        min_required + 2*step,
        max_conn
    ]
    
    # Crear líneas graduales centradas
    for i, (pos, connections) in enumerate(zip(positions, display_values)):
        # Calcular grosor usando tu sistema unificado
        line_width = _calculate_single_line_width_gradual(int(connections), min_conn, max_conn, min_required)
        
        # Líneas centradas (sin desplazamiento adicional) - GROSOR AUMENTADO
        ax.plot([pos - 1.5 - 3, pos + 1.5 - 3], [line_y, line_y], color=color, 
           linewidth=max(line_width * 1.5, 1.5), alpha=0.8, solid_capstyle='round')
    
    # =============================================
    # ETIQUETAS SOLO EN EXTREMOS - TAMAÑOS AUMENTADOS
    # =============================================
    
    # Izquierda: ≥mínimo requerido - TAMAÑO AUMENTADO de 10 a 14
    ax.text(positions[0], y - 1.5, f"≥{min_required}", ha='center', va='center',
           fontsize=14, fontweight='normal', color='black',
           family=FONT_CONFIG['family'])
    
    # Derecha: máximo valor - TAMAÑO AUMENTADO de 10 a 14
    ax.text(positions[-1], y - 1.5, f"{int(max_conn)}", ha='center', va='center',
           fontsize=14, fontweight='normal', color='black',
           family=FONT_CONFIG['family'])
    
    # =============================================
    # FLECHA PROGRESIVA EN NEGRO - GROSOR AUMENTADO
    # =============================================
    
    # Flecha debajo de las líneas EN NEGRO - GROSOR AUMENTADO de 2 a 3
    arrow_y = y - 0.5
    ax.annotate('', xy=(positions[-1] - 1, arrow_y), xytext=(positions[0] + 1, arrow_y),
                arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))

# ====================================================================
# FUNCIONES DE UTILIDAD (SIN CAMBIOS)
# ====================================================================

def _draw_connection_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                          color: str, line_width: float, alpha: float):
    """Dibuja marca direccional pequeña y perfectamente posicionada que sobrepasa la línea."""
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vectores de dirección
    ux, uy = dx / length, dy / length
    px, py = -uy, ux  # Perpendicular (izquierda)
    
    # Tamaño muy pequeño y proporcional
    size = max(0.6, line_width * 0.25)
    
    # Punto final EXTENDIDO para que sobrepase ligeramente la línea
    extension = size * 0.125  # Extensión pequeña más allá del final
    tip_x = end_x + extension * ux
    tip_y = end_y + extension * uy
    
    # Punto de origen de la marca (hacia atrás y hacia la izquierda desde el punto extendido)
    origin_x = tip_x - size * 1.0 * ux + size * 0.7 * px
    origin_y = tip_y - size * 1.0 * uy + size * 0.7 * py
    
    # Dibujar línea direccional simple con grosor perfecto
    ax.plot([tip_x, origin_x], [tip_y, origin_y], 
           color=color, 
           linewidth=max(1.8, line_width * 0.7), 
           alpha=1.0, 
           solid_capstyle='round', 
           zorder=100)

def optimize_player_name(full_name: str) -> str:
    """Optimiza nombres largos para mejor legibilidad."""
    if len(full_name) <= SCALE_CONFIG['name_length_threshold']:
        return full_name
    
    name_parts = full_name.split()
    
    if len(name_parts) >= 2:
        return name_parts[-1]
    else:
        return full_name[:SCALE_CONFIG['name_length_threshold']]

def _draw_optimized_labels(ax, players_df: pd.DataFrame):
    """Dibuja nombres optimizados de jugadores."""
    for _, player in players_df.iterrows():
        full_name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        display_name = optimize_player_name(full_name)
        
        ax.text(x, y, display_name,
               ha='center', va='center',
               color='white', fontsize=16, fontweight='bold',
               family=FONT_CONFIG['family'],
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=15)

def _calculate_connection_points(x1: float, y1: float, x2: float, y2: float,
                               r1: float, r2: float, pass_count: int) -> Tuple[float, float, float, float]:
    """Calcula puntos de inicio y fin de conexiones."""
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    ux, uy = dx / length, dy / length
    perp_x, perp_y = -uy, ux
    
    offset = CONNECTION_CONFIG['base_offset'] * (1 + pass_count / 50)
    
    start_x = x1 + r1 * ux + perp_x * offset
    start_y = y1 + r1 * uy + perp_y * offset
    
    name_margin = r2 + CONNECTION_CONFIG['name_margin']
    end_x = x2 - name_margin * ux + perp_x * offset
    end_y = y2 - name_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

# ====================================================================
# DIBUJO DEL CAMPO (SIN CAMBIOS)
# ====================================================================

def _draw_pitch(ax):
    """Dibuja campo de fútbol profesional."""
    length, width = FIELD_CONFIG['length'], FIELD_CONFIG['width']
    
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0, facecolor=FIELD_CONFIG['color'])
    ax.add_patch(pitch)
    
    _draw_field_lines(ax, length, width)
    _draw_penalty_areas(ax, length, width)
    _draw_goals(ax, length, width)
    
    border = patches.Rectangle((0, 0), length, width,
                             linewidth=FIELD_CONFIG['line_width'],
                             edgecolor=FIELD_CONFIG['line_color'],
                             facecolor='none')
    ax.add_patch(border)

def _draw_field_lines(ax, length: float, width: float):
    """Dibuja líneas centrales y círculo central."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    ax.plot([length/2, length/2], [0, width], color=color, linewidth=lw)
    
    center_circle = patches.Circle((length/2, width/2), 9.15, 
                                  linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(center_circle)
    
    ax.plot(length/2, width/2, 'o', color=color, markersize=4)

def _draw_penalty_areas(ax, length: float, width: float):
    """Dibuja áreas de penalti."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    penalty_length, penalty_width = 16.5, 40.32
    small_length, small_width = 5.5, 18.32
    penalty_y = (width - penalty_width) / 2
    small_y = (width - small_width) / 2
    
    for side in [0, length]:
        x_offset = penalty_length if side == 0 else length - penalty_length
        ax.plot([x_offset, x_offset], [penalty_y, penalty_y + penalty_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y, penalty_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y + penalty_width, penalty_y + penalty_width], color=color, linewidth=lw)
    
    for side in [0, length]:
        x_offset = small_length if side == 0 else length - small_length
        ax.plot([x_offset, x_offset], [small_y, small_y + small_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y, small_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y + small_width, small_y + small_width], color=color, linewidth=lw)
    
    penalty_spot = 11.0
    semicircle_radius = 9.15
    distance_to_edge = penalty_length - penalty_spot
    
    if distance_to_edge < semicircle_radius:
        angle_rad = np.arccos(distance_to_edge / semicircle_radius)
        angle_deg = np.degrees(angle_rad)
        
        semicircle_l = patches.Arc((penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=-angle_deg, theta2=angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_l)
        
        semicircle_r = patches.Arc((length - penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=180-angle_deg, theta2=180+angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_r)
    
    ax.plot(penalty_spot, width/2, 'o', color=color, markersize=4)
    ax.plot(length - penalty_spot, width/2, 'o', color=color, markersize=4)

def _draw_goals(ax, length: float, width: float):
    """Dibuja las porterías."""
    goal_width = 7.32
    goal_y = (width - goal_width) / 2
    color, lw = FIELD_CONFIG['goal_color'], FIELD_CONFIG['goal_width']
    
    ax.plot([0, 0], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')
    ax.plot([length, length], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')

# ====================================================================
# FUNCIONES DE CONVENIENCIA (SIN CAMBIOS)
# ====================================================================

def save_high_quality(fig: plt.Figure, team_name: str, suffix: str = "") -> str:
    """Guarda visualización en alta calidad."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = team_name.replace(" ", "_").replace("-", "_")
    
    filename = f"pass_network_{clean_name}"
    if suffix:
        filename += f"_{suffix}"
    filename += f"_{timestamp}.png"
    
    fig.savefig(filename, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none', format='png')
    
    print(f"💾 Guardado en alta calidad: {filename}")
    return filename

def load_from_csv_files(passes_path: str, players_path: str, connections_path: str) -> Dict[str, pd.DataFrame]:
    """Carga datos desde archivos CSV específicos."""
    match_data = {
        'passes': pd.read_csv(passes_path),
        'players': pd.read_csv(players_path),
        'connections': pd.read_csv(connections_path)
    }
    
    print(f"✅ Datos cargados desde CSV:")
    for key, df in match_data.items():
        print(f"   - {key.title()}: {len(df)} filas")
    
    return match_data