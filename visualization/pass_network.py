# ====================================================================
# FootballDecoded - Visualizador de Redes de Pase Mejorado
# ====================================================================
# Módulo mejorado con escalas graduales, nombres optimizados y división por partes
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime

# ====================================================================
# CONFIGURACIÓN
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
    'min_passes': 5,
    'alpha': 0.8,
    'base_offset': 0.4,
    'arrow_length': 1.0,
    'arrow_width': 0.6,
    'name_margin': 2.0
}

# Configuración de escalas graduales
SCALE_CONFIG = {
    'node_size_min': 600,      # Tamaño mínimo de nodo (más pequeño)
    'node_size_max': 8000,     # Tamaño máximo de nodo (más grande)
    'line_width_min': 1.0,     # Grosor mínimo de línea
    'line_width_max': 8.0,     # Grosor máximo de línea (menos agresivo)
    'name_length_threshold': 12 # Longitud máxima antes de usar solo apellido
}

# Configuración de fuente
FONT_CONFIG = {
    'family': 'DejaVu Sans',  # Fuente disponible por defecto
    'fallback': 'sans-serif'
}

# Configuración de división por partes
HALVES_CONFIG = {
    'first_half_end': 45,     # Minuto final primera parte
    'second_half_start': 46,  # Minuto inicio segunda parte
    'match_end': 120          # Minuto final del partido (incluye prórroga)
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
# FUNCIÓN PRINCIPAL - PARTIDO COMPLETO
# ====================================================================

def create_pass_network(match_data: Dict[str, pd.DataFrame], 
                       team_name: str,
                       title: Optional[str] = None,
                       show_labels: bool = True,
                       figsize: Tuple[int, int] = (18, 14),
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización de red de pases con escalas graduales.
    
    Args:
        match_data: Diccionario con DataFrames de 'passes', 'players', 'connections'
        team_name: Nombre del equipo a visualizar
        title: Título personalizado (opcional)
        show_labels: Mostrar nombres de jugadores
        figsize: Tamaño de figura
        save_path: Ruta para guardar (opcional)
        
    Returns:
        Figura de matplotlib
    """
    from match_data import filter_team_data
    
    # Filtrar datos del equipo
    team_data = filter_team_data(match_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name}")
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Dibujar campo
    _draw_pitch(ax)
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar red de pases con escalas graduales
    _draw_connections_gradual(ax, team_data['connections'], team_data['players'], colors['secondary'])
    _draw_players_gradual(ax, team_data['players'], colors['primary'])
    
    if show_labels:
        _draw_optimized_labels(ax, team_data['players'])
    
    # Añadir leyenda mejorada
    _draw_enhanced_legend(ax, team_data, team_name)
    
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
# NUEVAS FUNCIONES - DIVISIÓN POR PARTES
# ====================================================================

def create_pass_network_by_halves(match_data: Dict[str, pd.DataFrame], 
                                 team_name: str,
                                 save_individual: bool = True,
                                 show_labels: bool = True,
                                 figsize: Tuple[int, int] = (36, 14),
                                 save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización dual con primera y segunda parte del partido.
    
    Args:
        match_data: Diccionario con DataFrames de 'passes', 'players', 'connections'
        team_name: Nombre del equipo a visualizar
        save_individual: Si True, guarda también gráficos individuales
        show_labels: Mostrar nombres de jugadores
        figsize: Tamaño de figura (doble ancho para dos campos)
        save_path: Ruta base para guardar (opcional)
        
    Returns:
        Figura de matplotlib con ambas partes
    """
    # Procesar datos por partes
    first_half_data = _process_half_data(match_data, team_name, "first")
    second_half_data = _process_half_data(match_data, team_name, "second")
    
    if first_half_data['players'].empty and second_half_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name} en ninguna parte")
    
    # Crear figura dual
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, facecolor='white')
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar primera parte
    _draw_half_visualization(ax1, first_half_data, colors, "Primera Parte", show_labels)
    
    # Dibujar segunda parte
    _draw_half_visualization(ax2, second_half_data, colors, "Segunda Parte", show_labels)
    
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
        _save_individual_halves(first_half_data, second_half_data, team_name, colors, 
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
    Crea visualización de una sola parte del partido.
    
    Args:
        match_data: Diccionario con DataFrames completos del partido
        team_name: Nombre del equipo a visualizar
        half: "first" o "second" para seleccionar la parte
        title: Título personalizado (opcional)
        show_labels: Mostrar nombres de jugadores
        figsize: Tamaño de figura
        save_path: Ruta para guardar (opcional)
        
    Returns:
        Figura de matplotlib
    """
    # Procesar datos de la parte específica
    half_data = _process_half_data(match_data, team_name, half)
    
    if half_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name} en la {half} parte")
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Título de la parte
    part_title = title or f"{team_name} - {'Primera' if half == 'first' else 'Segunda'} Parte"
    
    # Dibujar visualización
    _draw_half_visualization(ax, half_data, colors, part_title, show_labels)
    
    plt.tight_layout()
    
    if save_path:
        half_suffix = f"_{half}_half"
        half_path = save_path.replace('.png', f'{half_suffix}.png')
        fig.savefig(half_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado {half} parte: {half_path}")
    
    return fig

# ====================================================================
# FUNCIONES DE PROCESAMIENTO POR PARTES
# ====================================================================

def _process_half_data(match_data: Dict[str, pd.DataFrame], team_name: str, half: str) -> Dict[str, pd.DataFrame]:
    """
    Procesa datos de match_data para una parte específica del partido.
    SOLO incluye jugadores que participaron en esa parte específica.
    
    Args:
        match_data: Datos completos del partido
        team_name: Nombre del equipo
        half: "first" o "second"
        
    Returns:
        Diccionario con datos procesados SOLO de jugadores activos en esa parte
    """
    # Definir rango de minutos
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
    
    # CRÍTICO: Filtrar pases por tiempo específico de esta parte
    half_passes = team_passes[
        (team_passes['minute'] >= min_minute) & 
        (team_passes['minute'] <= max_minute)
    ].copy()
    
    if half_passes.empty:
        return {'passes': pd.DataFrame(), 'players': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    # Recalcular jugadores y conexiones basado SOLO en pases de esta parte
    half_players = _recalculate_players_from_passes(half_passes)
    half_connections = _recalculate_connections_from_passes(half_passes)
    
    return {
        'passes': half_passes,
        'players': half_players,
        'connections': half_connections
    }

def _recalculate_players_from_passes(passes_df: pd.DataFrame) -> pd.DataFrame:
    """Recalcula estadísticas de jugadores basado en pases filtrados de ESTA PARTE específica."""
    if passes_df.empty:
        return pd.DataFrame()
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean',
        'field_y': 'mean',
        'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    
    # CRÍTICO: No calcular node_size aquí - se calculará dinámicamente 
    # en _draw_players_gradual() basado en los rangos ESPECÍFICOS de esta parte
    
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
    
    # Añadir ancho de línea
    result['line_width'] = result['pass_count'].apply(_get_line_width_enhanced)
    
    return result

def _get_line_width_enhanced(count: int) -> float:
    """Calcula ancho de línea basado en número de pases."""
    if count < 3: return 0.0
    elif count < 5: return 1.5
    elif count < 8: return 3.0
    elif count < 12: return 5.0
    elif count < 18: return 7.0
    else: return 10.0

def _draw_half_visualization(ax, half_data: Dict[str, pd.DataFrame], colors: Dict, 
                           title: str, show_labels: bool):
    """Dibuja visualización completa para una parte del partido."""
    # Dibujar campo
    _draw_pitch(ax)
    
    # Dibujar red de pases si hay datos
    if not half_data['connections'].empty:
        _draw_connections_gradual(ax, half_data['connections'], half_data['players'], colors['secondary'])
    
    if not half_data['players'].empty:
        _draw_players_gradual(ax, half_data['players'], colors['primary'])
        
        if show_labels:
            _draw_optimized_labels(ax, half_data['players'])
    
    # Añadir leyenda
    _draw_enhanced_legend(ax, half_data, title.split(' - ')[0])
    
    # Título de la parte
    ax.text(52.5, 75, title, ha='center', va='center', 
           fontsize=16, fontweight='bold', family=FONT_CONFIG['family'])
    
    # Configurar ejes
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 78)
    ax.set_aspect('equal')
    ax.axis('off')

def _save_individual_halves(first_half_data: Dict[str, pd.DataFrame], 
                          second_half_data: Dict[str, pd.DataFrame],
                          team_name: str, colors: Dict, show_labels: bool, 
                          base_path: Optional[str]):
    """Guarda gráficos individuales de cada parte."""
    if not base_path:
        return
    
    # Primera parte
    if not first_half_data['players'].empty:
        fig1, ax1 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization(ax1, first_half_data, colors, f"{team_name} - Primera Parte", show_labels)
        plt.tight_layout()
        
        first_path = base_path.replace('.png', '_first_half.png')
        fig1.savefig(first_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"📊 Guardado primera parte: {first_path}")
        plt.close(fig1)
    
    # Segunda parte
    if not second_half_data['players'].empty:
        fig2, ax2 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization(ax2, second_half_data, colors, f"{team_name} - Segunda Parte", show_labels)
        plt.tight_layout()
        
        second_path = base_path.replace('.png', '_second_half.png')
        fig2.savefig(second_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"📊 Guardado segunda parte: {second_path}")
        plt.close(fig2)

# ====================================================================
# FUNCIONES DE ESCALADO GRADUAL
# ====================================================================

def calculate_gradual_node_size(total_passes: int, min_passes: int, max_passes: int) -> float:
    """
    Calcula tamaño de nodo con escala gradual más diferenciada.
    
    Args:
        total_passes: Número de pases del jugador
        min_passes: Mínimo de pases en el equipo
        max_passes: Máximo de pases en el equipo
        
    Returns:
        Tamaño de nodo escalado
    """
    if max_passes == min_passes:
        return (SCALE_CONFIG['node_size_min'] + SCALE_CONFIG['node_size_max']) / 2
    
    # Normalización lineal simple
    normalized = (total_passes - min_passes) / (max_passes - min_passes)
    
    # Aplicar curva exponencial MÁS agresiva para mejor diferenciación
    # Especialmente importante para valores bajos
    curved = normalized ** 0.3  # Curva muy agresiva
    
    return SCALE_CONFIG['node_size_min'] + curved * (SCALE_CONFIG['node_size_max'] - SCALE_CONFIG['node_size_min'])

def calculate_gradual_line_width(pass_count: int, min_connections: int, max_connections: int) -> float:
    """
    Calcula grosor de línea con escala gradual suave.
    
    Args:
        pass_count: Número de pases en la conexión
        min_connections: Mínimo de pases en conexiones
        max_connections: Máximo de pases en conexiones
        
    Returns:
        Grosor de línea escalado
    """
    if max_connections == min_connections:
        return (SCALE_CONFIG['line_width_min'] + SCALE_CONFIG['line_width_max']) / 2
    
    # Normalización con función suave para grosores menos agresivos
    normalized = (pass_count - min_connections) / (max_connections - min_connections)
    curved = normalized ** 0.8
    
    return SCALE_CONFIG['line_width_min'] + curved * (SCALE_CONFIG['line_width_max'] - SCALE_CONFIG['line_width_min'])

def optimize_player_name(full_name: str) -> str:
    """
    Optimiza nombres largos para mejor legibilidad.
    
    Args:
        full_name: Nombre completo del jugador
        
    Returns:
        Nombre optimizado
    """
    if len(full_name) <= SCALE_CONFIG['name_length_threshold']:
        return full_name
    
    # Si es muy largo, usar solo apellido
    name_parts = full_name.split()
    
    if len(name_parts) >= 2:
        # Usar apellido (última parte)
        return name_parts[-1]
    else:
        # Si solo tiene una parte, truncar
        return full_name[:SCALE_CONFIG['name_length_threshold']]

# ====================================================================
# DIBUJO DEL CAMPO
# ====================================================================

def _draw_pitch(ax):
    """Dibuja campo de fútbol profesional."""
    length, width = FIELD_CONFIG['length'], FIELD_CONFIG['width']
    
    # Base del campo
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0, facecolor=FIELD_CONFIG['color'])
    ax.add_patch(pitch)
    
    # Líneas del campo
    _draw_field_lines(ax, length, width)
    _draw_penalty_areas(ax, length, width)
    _draw_goals(ax, length, width)
    
    # Borde del campo
    border = patches.Rectangle((0, 0), length, width,
                             linewidth=FIELD_CONFIG['line_width'],
                             edgecolor=FIELD_CONFIG['line_color'],
                             facecolor='none')
    ax.add_patch(border)

def _draw_field_lines(ax, length: float, width: float):
    """Dibuja líneas centrales y círculo central."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    # Línea central
    ax.plot([length/2, length/2], [0, width], color=color, linewidth=lw)
    
    # Círculo central
    center_circle = patches.Circle((length/2, width/2), 9.15, 
                                  linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(center_circle)
    
    # Punto central
    ax.plot(length/2, width/2, 'o', color=color, markersize=4)

def _draw_penalty_areas(ax, length: float, width: float):
    """Dibuja áreas de penalti."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    # Dimensiones
    penalty_length, penalty_width = 16.5, 40.32
    small_length, small_width = 5.5, 18.32
    penalty_y = (width - penalty_width) / 2
    small_y = (width - small_width) / 2
    
    # Áreas grandes
    for side in [0, length]:
        x_offset = penalty_length if side == 0 else length - penalty_length
        ax.plot([x_offset, x_offset], [penalty_y, penalty_y + penalty_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y, penalty_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y + penalty_width, penalty_y + penalty_width], color=color, linewidth=lw)
    
    # Áreas pequeñas
    for side in [0, length]:
        x_offset = small_length if side == 0 else length - small_length
        ax.plot([x_offset, x_offset], [small_y, small_y + small_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y, small_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y + small_width, small_y + small_width], color=color, linewidth=lw)
    
    # Semicírculos y puntos de penalti
    penalty_spot = 11.0
    semicircle_radius = 9.15
    distance_to_edge = penalty_length - penalty_spot
    
    if distance_to_edge < semicircle_radius:
        angle_rad = np.arccos(distance_to_edge / semicircle_radius)
        angle_deg = np.degrees(angle_rad)
        
        # Semicírculo izquierdo
        semicircle_l = patches.Arc((penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=-angle_deg, theta2=angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_l)
        
        # Semicírculo derecho
        semicircle_r = patches.Arc((length - penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=180-angle_deg, theta2=180+angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_r)
    
    # Puntos de penalti
    ax.plot(penalty_spot, width/2, 'o', color=color, markersize=4)
    ax.plot(length - penalty_spot, width/2, 'o', color=color, markersize=4)

def _draw_goals(ax, length: float, width: float):
    """Dibuja las porterías."""
    goal_width = 7.32
    goal_y = (width - goal_width) / 2
    color, lw = FIELD_CONFIG['goal_color'], FIELD_CONFIG['goal_width']
    
    # Porterías
    ax.plot([0, 0], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')
    ax.plot([length, length], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')

# ====================================================================
# DIBUJO DE CONEXIONES CON ESCALA GRADUAL
# ====================================================================

def _draw_connections_gradual(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones con grosor gradual basado en escalas reales."""
    if connections_df.empty:
        return
    
    # Calcular rangos reales de conexiones
    valid_connections = connections_df[connections_df['pass_count'] >= CONNECTION_CONFIG['min_passes']]
    if valid_connections.empty:
        return
    
    min_connections = valid_connections['pass_count'].min()
    max_connections = valid_connections['pass_count'].max()
    
    for _, conn in valid_connections.iterrows():
        # Obtener datos de jugadores
        source_data = players_df[players_df['player'] == conn['source']]
        target_data = players_df[players_df['player'] == conn['target']]
        
        if source_data.empty or target_data.empty:
            continue
        
        source_player = source_data.iloc[0]
        target_player = target_data.iloc[0]
        
        # Calcular radios basados en escalas graduales
        source_radius = _get_gradual_node_radius(source_player['total_passes'], players_df)
        target_radius = _get_gradual_node_radius(target_player['total_passes'], players_df)
        
        # Calcular puntos de conexión
        start_x, start_y, end_x, end_y = _calculate_connection_points(
            source_player['avg_x'], source_player['avg_y'],
            target_player['avg_x'], target_player['avg_y'],
            source_radius, target_radius, conn['pass_count']
        )
        
        # Propiedades de línea graduales
        line_width = calculate_gradual_line_width(conn['pass_count'], min_connections, max_connections)
        alpha = min(0.4 + (conn['pass_count'] / max_connections) * 0.5, 0.9)
        
        # Dibujar línea
        ax.plot([start_x, end_x], [start_y, end_y], 
               color=color, linewidth=line_width, alpha=alpha,
               solid_capstyle='round', zorder=1)
        
        # Dibujar flecha
        _draw_connection_arrow(ax, start_x, start_y, end_x, end_y, 
                              color, line_width, alpha)

def _get_gradual_node_radius(total_passes: int, players_df: pd.DataFrame) -> float:
    """Calcula radio de nodo basado en escala gradual ESPECÍFICA de esta parte."""
    min_passes = players_df['total_passes'].min()
    max_passes = players_df['total_passes'].max()
    
    # NUEVO: Usar función específica para esta parte
    node_size = _calculate_half_specific_node_size(total_passes, min_passes, max_passes)
    return np.sqrt(node_size / np.pi) * 0.105

def _calculate_connection_points(x1: float, y1: float, x2: float, y2: float,
                               r1: float, r2: float, pass_count: int) -> Tuple[float, float, float, float]:
    """Calcula puntos de inicio y fin de conexiones."""
    # Vector dirección
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    # Vector unitario
    ux, uy = dx / length, dy / length
    
    # Vector perpendicular para offset
    perp_x, perp_y = -uy, ux
    
    # Offset pequeño
    offset = CONNECTION_CONFIG['base_offset'] * (1 + pass_count / 50)
    
    # Punto de inicio: en el borde del nodo fuente
    start_x = x1 + r1 * ux + perp_x * offset
    start_y = y1 + r1 * uy + perp_y * offset
    
    # Punto final: lejos del nodo para no tapar nombre
    name_margin = r2 + CONNECTION_CONFIG['name_margin']
    end_x = x2 - name_margin * ux + perp_x * offset
    end_y = y2 - name_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def _draw_connection_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                          color: str, line_width: float, alpha: float):
    """Dibuja flecha al final de la conexión."""
    # Vector dirección
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vector unitario
    ux, uy = dx / length, dy / length
    
    # Dimensiones de flecha
    arrow_length = CONNECTION_CONFIG['arrow_length'] * 1.3 * max(1.0, line_width / 5)
    arrow_width = CONNECTION_CONFIG['arrow_width'] * 1.3 * max(1.0, line_width / 6)
    
    # Posición de punta
    push_forward = 1.5
    arrow_tip_x = end_x + push_forward * ux
    arrow_tip_y = end_y + push_forward * uy
    
    # Base de la flecha
    back_x = arrow_tip_x - arrow_length * ux
    back_y = arrow_tip_y - arrow_length * uy
    
    # Puntos laterales
    left_x = back_x - arrow_width * (-uy)
    left_y = back_y - arrow_width * ux
    right_x = back_x + arrow_width * (-uy)
    right_y = back_y + arrow_width * ux
    
    # Dibujar triángulo
    triangle = patches.Polygon([(arrow_tip_x, arrow_tip_y), (left_x, left_y), (right_x, right_y)],
                              closed=True, facecolor=color, edgecolor=color,
                              alpha=1.0, linewidth=0, zorder=25)
    ax.add_patch(triangle)

# ====================================================================
# DIBUJO DE JUGADORES CON ESCALA GRADUAL
# ====================================================================

def _draw_players_gradual(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores con tamaños graduales basados SOLO en esta parte específica."""
    if players_df.empty:
        return
    
    # CRÍTICO: Calcular min/max basado SOLO en jugadores de ESTA parte
    min_passes = players_df['total_passes'].min()
    max_passes = players_df['total_passes'].max()
    
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        
        # NUEVO: Calcular tamaño específico para ESTA parte solamente
        node_size = _calculate_half_specific_node_size(player['total_passes'], min_passes, max_passes)
        
        ax.scatter(x, y, s=node_size, 
                  c=color, alpha=0.6,
                  edgecolors=color, linewidth=4,
                  zorder=10)

def _calculate_half_specific_node_size(total_passes: int, min_passes_this_half: int, max_passes_this_half: int) -> float:
    """
    Calcula tamaño de nodo basado ÚNICAMENTE en el rango de ESTA parte específica.
    """
    if max_passes_this_half == min_passes_this_half:
        return 4300  # Valor medio si todos tienen los mismos pases
    
    # Normalización basada SOLO en esta parte
    normalized = (total_passes - min_passes_this_half) / (max_passes_this_half - min_passes_this_half)
    
    # Curva agresiva para diferenciación
    curved = normalized ** 0.3
    
    return SCALE_CONFIG['node_size_min'] + curved * (SCALE_CONFIG['node_size_max'] - SCALE_CONFIG['node_size_min'])

def _draw_optimized_labels(ax, players_df: pd.DataFrame):
    """Dibuja nombres optimizados de jugadores."""
    for _, player in players_df.iterrows():
        full_name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        # Optimizar nombre
        display_name = optimize_player_name(full_name)
        
        # Texto con outline
        ax.text(x, y, display_name,
               ha='center', va='center',
               color='white', fontsize=16, fontweight='bold',
               family=FONT_CONFIG['family'],
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=15)

# ====================================================================
# LEYENDA MEJORADA
# ====================================================================

def _draw_enhanced_legend(ax, team_data: Dict[str, pd.DataFrame], team_name: str):
    """Leyenda con escalas graduales reales."""
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    legend_color = colors['primary']
    
    # Posición
    legend_y = -10
    
    # Estadísticas centrales
    total_passes = len(team_data['passes'])
    ax.text(52.5, legend_y + 6, f"Pases: {total_passes}", 
           ha='center', va='center', fontsize=18, fontweight='bold', 
           color=legend_color, family=FONT_CONFIG['family'])
    
    # Título
    ax.text(52.5, legend_y + 1, "Nº Pases", 
           ha='center', va='center', fontsize=14, fontweight='bold', 
           color=legend_color, family=FONT_CONFIG['family'])
    
    # Línea debajo del título
    ax.plot([42, 63], [legend_y - 0.5, legend_y - 0.5], color=legend_color, linewidth=2)
    
    # Escalas graduales
    _draw_gradual_nodes_legend(ax, 20, legend_y, legend_color, team_data['players'])
    _draw_gradual_lines_legend(ax, 85, legend_y, legend_color, team_data['connections'])

def _draw_gradual_nodes_legend(ax, x: float, y: float, color: str, players_df: pd.DataFrame):
    """Leyenda de nodos con flecha gradual basada SOLO en jugadores de esta parte."""
    if players_df.empty:
        return
    
    # CRÍTICO: Min/max basado SOLO en jugadores activos en esta parte específica
    min_passes = players_df['total_passes'].min()
    max_passes = players_df['total_passes'].max()
    
    # Solo mostrar extremos: mínimo y máximo de ESTA parte
    pass_values = [min_passes, max_passes]
    positions = [x - 8, x + 8]  # Más separados
    circle_y = y + 5.3
    
    for passes, pos in zip(pass_values, positions):
        # NUEVO: Usar función específica para esta parte
        node_size = _calculate_half_specific_node_size(int(passes), min_passes, max_passes) * 0.6
        ax.scatter(pos, circle_y, s=node_size, c=color, alpha=0.8, 
                  edgecolors=color, linewidth=2, zorder=10)
        
        # Etiquetas con línea debajo
        ax.text(pos, y + 0.5, f"{int(passes)}", ha='center', va='center',
               fontsize=11, fontweight='bold', color=color, 
               family=FONT_CONFIG['family'])
        ax.plot([pos - 2, pos + 2], [y - 0.5, y - 0.5], color=color, linewidth=1)
    
    # Flecha gradual entre extremos
    ax.annotate('', xy=(x + 6, circle_y), xytext=(x - 6, circle_y),
                arrowprops=dict(arrowstyle='->', color=color, lw=2, alpha=0.7))

def _draw_gradual_lines_legend(ax, x: float, y: float, color: str, connections_df: pd.DataFrame):
    """Leyenda de líneas con flecha gradual (mínimo → máximo)."""
    if connections_df.empty:
        return
    
    valid_connections = connections_df[connections_df['pass_count'] >= CONNECTION_CONFIG['min_passes']]
    if valid_connections.empty:
        return
    
    min_conn = valid_connections['pass_count'].min()
    max_conn = valid_connections['pass_count'].max()
    
    # Solo mostrar extremos: mínimo y máximo
    conn_values = [min_conn, max_conn]
    positions = [x - 8, x + 8]  # Más separados
    line_y = y + 2.5
    
    for connections, pos in zip(conn_values, positions):
        line_width = calculate_gradual_line_width(int(connections), min_conn, max_conn)
        ax.plot([pos - 2.5, pos + 2.5], [line_y, line_y], color=color, 
               linewidth=line_width, alpha=0.8, solid_capstyle='round')
        
        # Etiquetas con línea debajo
        ax.text(pos, y + 0.5, f"{int(connections)}", ha='center', va='center',
               fontsize=10, fontweight='bold', color=color,
               family=FONT_CONFIG['family'])
        ax.plot([pos - 2, pos + 2], [y - 0.5, y - 0.5], color=color, linewidth=1)
    
    # Flecha gradual entre extremos
    ax.annotate('', xy=(x + 6, line_y), xytext=(x - 6, line_y),
                arrowprops=dict(arrowstyle='->', color=color, lw=2, alpha=0.7))

# ====================================================================
# FUNCIONES DE CONVENIENCIA
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

# ====================================================================
# FUNCIONES DE ACCESO RÁPIDO PARA TESTING
# ====================================================================

def quick_visualize_barcelona_full_match(match_id: int = 1821769) -> plt.Figure:
    """Visualización rápida de Barcelona - partido completo."""
    from match_data import load_match_data
    match_data = load_match_data(match_id)
    return create_pass_network(match_data, "Barcelona")

def quick_visualize_barcelona_by_halves(match_id: int = 1821769) -> plt.Figure:
    """Visualización rápida de Barcelona - por partes."""
    from match_data import load_match_data
    match_data = load_match_data(match_id)
    return create_pass_network_by_halves(match_data, "Barcelona", save_individual=True)

def quick_visualize_barcelona_first_half(match_id: int = 1821769) -> plt.Figure:
    """Visualización rápida de Barcelona - solo primera parte."""
    from match_data import load_match_data
    match_data = load_match_data(match_id)
    return create_pass_network_single_half(match_data, "Barcelona", "first")

def quick_visualize_barcelona_second_half(match_id: int = 1821769) -> plt.Figure:
    """Visualización rápida de Barcelona - solo segunda parte."""
    from match_data import load_match_data
    match_data = load_match_data(match_id)
    return create_pass_network_single_half(match_data, "Barcelona", "second")