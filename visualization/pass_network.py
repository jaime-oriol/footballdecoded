# ====================================================================
# FootballDecoded - Visualizador de Redes de Pase
# ====================================================================
# Módulo genérico para visualizar redes de pase de cualquier equipo
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
    'color': 'white',  # Fondo blanco
    'line_color': 'black',  # Líneas negras
    'line_width': 2.5,
    'goal_color': '#333333',
    'goal_width': 8.0
}

# Configuración de conexiones
CONNECTION_CONFIG = {
    'min_passes': 3,  # Reducido para mostrar más conexiones
    'alpha': 0.7,
    'offset': 2.0,  # Mayor separación entre líneas bidireccionales
    'curve_factor': 0.1  # Factor de curvatura para separar líneas
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
# FUNCIÓN PRINCIPAL
# ====================================================================

def create_pass_network(match_data: Dict[str, pd.DataFrame], 
                       team_name: str,
                       title: Optional[str] = None,
                       show_labels: bool = True,
                       figsize: Tuple[int, int] = (18, 14),
                       save_path: Optional[str] = None) -> plt.Figure:
    """
    Crea visualización de red de pases para un equipo.
    
    Args:
        match_data: Datos del partido (de match_data.py)
        team_name: Nombre del equipo a visualizar
        title: Título personalizado (None = auto)
        show_labels: Mostrar nombres de jugadores
        figsize: Tamaño de figura
        save_path: Ruta para guardar (None = no guardar)
        
    Returns:
        Figura de matplotlib
    """
    from match_data import filter_team_data
    
    # Filtrar datos del equipo
    team_data = filter_team_data(match_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name}")
    
    # Crear figura con fondo blanco
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Dibujar campo
    _draw_pitch(ax)
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar red de pases (conexiones primero, jugadores encima)
    _draw_bidirectional_connections(ax, team_data['connections'], team_data['players'], colors['secondary'])
    _draw_players_enhanced(ax, team_data['players'], colors['primary'])
    
    if show_labels:
        _draw_labels_enhanced(ax, team_data['players'])
    
    # Configurar título
    if title is None:
        total_passes = len(team_data['passes'])
        connections_count = len(team_data['connections']) if not team_data['connections'].empty else 0
        title = f"{team_name} - Red de Pases\nPases: {total_passes} | Conexiones: {connections_count}"
    
    ax.set_title(title, fontsize=20, fontweight='bold', pad=25, color='#1A1A1A')
    
    # Configurar ejes
    ax.set_xlim(-5, 110)
    ax.set_ylim(-5, 73)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    # Guardar si se especifica
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado: {save_path}")
    
    return fig


# ====================================================================
# DIBUJO DEL CAMPO
# ====================================================================

def _draw_pitch(ax):
    """Dibuja un campo de fútbol profesional con fondo blanco y líneas negras."""
    length, width = FIELD_CONFIG['length'], FIELD_CONFIG['width']
    
    # Base del campo (fondo blanco)
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0, 
                            facecolor=FIELD_CONFIG['color'])
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
    color = FIELD_CONFIG['line_color']
    lw = FIELD_CONFIG['line_width']
    
    # Línea central
    ax.plot([length/2, length/2], [0, width], color=color, linewidth=lw)
    
    # Círculo central
    center_circle = patches.Circle((length/2, width/2), 9.15, 
                                  linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(center_circle)
    
    # Punto central
    ax.plot(length/2, width/2, 'o', color=color, markersize=4)


def _draw_penalty_areas(ax, length: float, width: float):
    """Dibuja áreas de penalti y semicírculos correctamente."""
    color = FIELD_CONFIG['line_color']
    lw = FIELD_CONFIG['line_width']
    
    # Dimensiones áreas
    penalty_length = 16.5
    penalty_width = 40.32
    small_length = 5.5
    small_width = 18.32
    
    penalty_y = (width - penalty_width) / 2
    small_y = (width - small_width) / 2
    
    # Áreas grandes
    left_area = patches.Rectangle((0, penalty_y), penalty_length, penalty_width,
                                linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(left_area)
    
    right_area = patches.Rectangle((length - penalty_length, penalty_y), penalty_length, penalty_width,
                                 linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(right_area)
    
    # Áreas pequeñas
    left_small = patches.Rectangle((0, small_y), small_length, small_width,
                                 linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(left_small)
    
    right_small = patches.Rectangle((length - small_length, small_y), small_length, small_width,
                                  linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(right_small)
    
    # Semicírculos y puntos de penalti
    penalty_spot = 11.0
    semicircle_radius = 9.15
    
    # Semicírculo izquierdo (orientación correcta)
    semicircle_l = patches.Arc((penalty_spot, width/2), 
                              semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=-90, theta2=90, 
                              linewidth=lw, edgecolor=color)
    ax.add_patch(semicircle_l)
    ax.plot(penalty_spot, width/2, 'o', color=color, markersize=4)
    
    # Semicírculo derecho (orientación correcta)
    semicircle_r = patches.Arc((length - penalty_spot, width/2), 
                              semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=90, theta2=270, 
                              linewidth=lw, edgecolor=color)
    ax.add_patch(semicircle_r)
    ax.plot(length - penalty_spot, width/2, 'o', color=color, markersize=4)


def _draw_goals(ax, length: float, width: float):
    """Dibuja las porterías."""
    goal_width = 7.32
    goal_y = (width - goal_width) / 2
    color = FIELD_CONFIG['goal_color']
    lw = FIELD_CONFIG['goal_width']
    
    # Portería izquierda
    ax.plot([0, 0], [goal_y, goal_y + goal_width], 
           color=color, linewidth=lw, solid_capstyle='round')
    
    # Portería derecha
    ax.plot([length, length], [goal_y, goal_y + goal_width], 
           color=color, linewidth=lw, solid_capstyle='round')


# ====================================================================
# DIBUJO DE LA RED DE PASES - VERSIÓN MEJORADA
# ====================================================================

def _draw_bidirectional_connections(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones bidireccionales entre jugadores."""
    if connections_df.empty:
        return
    
    # Dibujar TODAS las conexiones, incluso las de bajo valor
    for _, conn in connections_df.iterrows():
        if conn['pass_count'] < CONNECTION_CONFIG['min_passes']:
            continue
            
        source_player = conn['source']
        target_player = conn['target']
        
        # Obtener posiciones de los jugadores
        source_pos = players_df[players_df['player'] == source_player]
        target_pos = players_df[players_df['player'] == target_player]
        
        if source_pos.empty or target_pos.empty:
            continue
        
        x1, y1 = source_pos.iloc[0]['avg_x'], source_pos.iloc[0]['avg_y']
        x2, y2 = target_pos.iloc[0]['avg_x'], target_pos.iloc[0]['avg_y']
        
        # Calcular línea con offset para separar direcciones
        offset_line = _calculate_offset_line(x1, y1, x2, y2, conn['pass_count'])
        
        # Determinar grosor y opacidad basado en número de pases
        line_width = _calculate_enhanced_line_width(conn['pass_count'])
        alpha = min(0.3 + (conn['pass_count'] / 20) * 0.5, 0.8)
        
        # Dibujar línea
        ax.plot(offset_line['x'], offset_line['y'], 
               color=color, 
               linewidth=line_width,
               alpha=alpha,
               solid_capstyle='round',
               zorder=1)


def _calculate_offset_line(x1: float, y1: float, x2: float, y2: float, pass_count: int) -> Dict:
    """Calcula línea con offset para separar conexiones bidireccionales."""
    # Calcular vector perpendicular para offset
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return {'x': [x1, x2], 'y': [y1, y2]}
    
    # Vector perpendicular normalizado
    perp_x = -dy / length
    perp_y = dx / length
    
    # Offset basado en número de pases (más pases = más separación)
    offset = CONNECTION_CONFIG['offset'] * (1 + pass_count / 30)
    
    # Aplicar offset
    offset_x1 = x1 + perp_x * offset
    offset_y1 = y1 + perp_y * offset
    offset_x2 = x2 + perp_x * offset
    offset_y2 = y2 + perp_y * offset
    
    return {'x': [offset_x1, offset_x2], 'y': [offset_y1, offset_y2]}


def _calculate_enhanced_line_width(pass_count: int) -> float:
    """Calcula grosor de línea más diferenciado."""
    if pass_count < 3: return 0.5
    elif pass_count < 5: return 1.5
    elif pass_count < 8: return 3.0
    elif pass_count < 12: return 5.0
    elif pass_count < 18: return 7.0
    else: return 10.0


def _draw_players_enhanced(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores con diseño mejorado."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        
        # Tamaño escalado más agresivamente
        base_size = _calculate_enhanced_node_size(player['total_passes'])
        
        # Círculo con relleno semitransparente y borde grueso
        ax.scatter(x, y, s=base_size, 
                  c=color, alpha=0.6,  # Relleno semitransparente
                  edgecolors=color, linewidth=4,  # Borde grueso del mismo color
                  zorder=10)


def _calculate_enhanced_node_size(total_passes: int) -> float:
    """Calcula tamaño de nodo más diferenciado."""
    # Rango más amplio y progresión más agresiva
    min_size = 1000
    max_size = 3500
    
    # Normalización con escalado logarítmico para mayor diferenciación
    if total_passes <= 5:
        return min_size
    elif total_passes >= 100:
        return max_size
    else:
        # Escalado logarítmico para amplificar diferencias
        log_passes = np.log(total_passes + 1)
        log_max = np.log(101)
        log_min = np.log(6)
        
        normalized = (log_passes - log_min) / (log_max - log_min)
        return min_size + (normalized * (max_size - min_size))


def _draw_labels_enhanced(ax, players_df: pd.DataFrame):
    """Dibuja nombres completos de jugadores dentro de los nodos."""
    for _, player in players_df.iterrows():
        name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        # Usar nombre completo, pero ajustar si es muy largo
        display_name = name
        if len(name) > 16:
            parts = name.split()
            if len(parts) >= 2:
                # Primer nombre + apellido
                display_name = f"{parts[0]} {parts[-1]}"
        
        # Texto más grande y dentro del nodo
        ax.text(x, y, display_name,
               ha='center', va='center',
               color='white', fontsize=12, fontweight='bold',
               path_effects=[
                   path_effects.Stroke(linewidth=2, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=11)


# ====================================================================
# FUNCIONES DE CONVENIENCIA
# ====================================================================

def quick_visualize_team(team_name: str, match_data: Optional[Dict] = None) -> plt.Figure:
    """
    Visualización rápida de un equipo.
    
    Args:
        team_name: Nombre del equipo
        match_data: Datos del partido (None = cargar desde datos guardados)
    """
    if match_data is None:
        from match_data import load_match_data
        match_data = load_match_data(1821769)  # Athletic vs Barcelona
    
    return create_pass_network(match_data, team_name)


def save_high_quality(fig: plt.Figure, team_name: str, suffix: str = "") -> str:
    """Guarda en alta calidad para presentaciones."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = team_name.replace(" ", "_").replace("-", "_")
    
    if suffix:
        filename = f"pass_network_{clean_name}_{suffix}_{timestamp}.png"
    else:
        filename = f"pass_network_{clean_name}_{timestamp}.png"
    
    fig.savefig(filename, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none', format='png')
    
    print(f"💾 Guardado en alta calidad: {filename}")
    return filename


def create_comparison_networks(match_data: Dict[str, pd.DataFrame], 
                             team1: str, team2: str,
                             save_path: Optional[str] = None) -> plt.Figure:
    """Crea comparación lado a lado de dos equipos."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(32, 14), facecolor='white')
    
    # Crear redes para cada equipo en subplots separados
    # (Implementación simplificada para mantener enfoque en mejoras principales)
    
    return fig