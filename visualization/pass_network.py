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
    'color': '#2D5B2D',  # Verde césped
    'line_color': 'white',
    'line_width': 2.0,
    'goal_color': '#666666',
    'goal_width': 8.0
}

# Configuración de conexiones
CONNECTION_CONFIG = {
    'min_passes': 5,
    'alpha': 0.8,
    'offset': 1.0  # Separación entre líneas bidireccionales
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
                       figsize: Tuple[int, int] = (16, 12),
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
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Dibujar campo
    _draw_pitch(ax)
    
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # Dibujar red de pases
    _draw_connections(ax, team_data['connections'], team_data['players'], colors['secondary'])
    _draw_players(ax, team_data['players'], colors['primary'])
    
    if show_labels:
        _draw_labels(ax, team_data['players'])
    
    # Configurar título
    if title is None:
        total_passes = len(team_data['passes'])
        connections_count = len(team_data['connections'][team_data['connections']['line_width'] > 0]) if not team_data['connections'].empty else 0
        title = f"{team_name} - Red de Pases\nPases: {total_passes} | Conexiones: {connections_count}"
    
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20, color='#2C3E50')
    
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
    """Dibuja un campo de fútbol profesional."""
    length, width = FIELD_CONFIG['length'], FIELD_CONFIG['width']
    
    # Base del campo
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
    ax.plot(length/2, width/2, 'o', color=color, markersize=3)


def _draw_penalty_areas(ax, length: float, width: float):
    """Dibuja áreas de penalti y semicírculos."""
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
    for x in [0, length - penalty_length]:
        area = patches.Rectangle((x, penalty_y), penalty_length, penalty_width,
                               linewidth=lw, edgecolor=color, facecolor='none')
        ax.add_patch(area)
    
    # Áreas pequeñas
    for x in [0, length - small_length]:
        small_area = patches.Rectangle((x, small_y), small_length, small_width,
                                     linewidth=lw, edgecolor=color, facecolor='none')
        ax.add_patch(small_area)
    
    # Semicírculos y puntos de penalti
    penalty_spot = 11.0
    semicircle_radius = 9.15
    
    # Izquierda
    semicircle_l = patches.Arc((penalty_spot, width/2), semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=-90, theta2=90, linewidth=lw, edgecolor=color)
    ax.add_patch(semicircle_l)
    ax.plot(penalty_spot, width/2, 'o', color=color, markersize=3)
    
    # Derecha
    semicircle_r = patches.Arc((length - penalty_spot, width/2), semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=90, theta2=270, linewidth=lw, edgecolor=color)
    ax.add_patch(semicircle_r)
    ax.plot(length - penalty_spot, width/2, 'o', color=color, markersize=3)


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
# DIBUJO DE LA RED DE PASES
# ====================================================================

def _draw_connections(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones entre jugadores."""
    if connections_df.empty:
        return
    
    # Solo conexiones significativas
    significant_connections = connections_df[connections_df['line_width'] > 0]
    
    for _, conn in significant_connections.iterrows():
        source_player = conn['source']
        target_player = conn['target']
        
        # Obtener posiciones
        source_pos = players_df[players_df['player'] == source_player]
        target_pos = players_df[players_df['player'] == target_player]
        
        if source_pos.empty or target_pos.empty:
            continue
        
        x1, y1 = source_pos.iloc[0]['avg_x'], source_pos.iloc[0]['avg_y']
        x2, y2 = target_pos.iloc[0]['avg_x'], target_pos.iloc[0]['avg_y']
        
        # Dibujar línea
        ax.plot([x1, x2], [y1, y2], 
               color=color, 
               linewidth=conn['line_width'],
               alpha=CONNECTION_CONFIG['alpha'],
               solid_capstyle='round',
               zorder=1)


def _draw_players(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        size = player['node_size']
        
        # Círculo exterior (borde)
        ax.scatter(x, y, s=size, c='white', edgecolors=color, 
                  linewidth=6, alpha=1.0, zorder=10)
        
        # Círculo interior
        inner_size = size * 0.6
        ax.scatter(x, y, s=inner_size, c=color, edgecolors='none', 
                  alpha=0.7, zorder=9)


def _draw_labels(ax, players_df: pd.DataFrame):
    """Dibuja nombres de jugadores."""
    for _, player in players_df.iterrows():
        name = player['player']
        
        # Acortar nombres largos
        if len(name) > 14:
            parts = name.split()
            if len(parts) >= 2:
                name = parts[-1]  # Solo apellido
        
        ax.text(player['avg_x'], player['avg_y'], name,
               ha='center', va='center',
               color='#1A1A1A', fontsize=10, fontweight='bold',
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='white'),
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
        match_data: Datos del partido (None = cargar Athletic vs Barcelona)
    """
    if match_data is None:
        from match_data import quick_extract_athletic_barcelona
        match_data = quick_extract_athletic_barcelona()
    
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