# ====================================================================
# FootballDecoded - Shot Map con Líneas Cohesivas al Pass Network
# ====================================================================

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects

from visualization.core import (
    draw_pitch, get_primary_color, FONT_CONFIG
)

# ====================================================================
# SCALING CONFIGURATION
# ====================================================================

XG_SCALE_CONFIG = {
    'min_size': 500,
    'max_size': 3200,
    'low_threshold': 0.05,
    'mid_threshold': 0.30,
    'high_threshold': 0.80,
    'slope_low': 800,
    'slope_high': 800
}

GOAL_LINE_CONFIG = {
    'width_base': 2.8,
    'width_multiplier': 0.3,
    'gradient_points': 60,
    'arrow_size': 0.8,
    'arrow_extension': 0.2
}

RESULT_STYLES = {
    'Goal': {'marker': '*', 'alpha': 1.0, 'face': '#FFD700', 'edge': 'team_color', 'width': 2},
    'Saved Shot': {'marker': 's', 'alpha': 1.0, 'face': 'team_color', 'edge': 'black', 'width': 2},
    'Blocked Shot': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': 'gray', 'width': 2},
    'Missed Shot': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': 'lightgray', 'width': 2},
    'Shot On Post': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': '#FF6B35', 'width': 2}
}

# ====================================================================
# SCALING SYSTEM (Mantenido del original)
# ====================================================================

def calculate_xg_node_size(xg_value: float) -> float:
    """Sistema suave de escalado adaptado del pass_network."""
    config = XG_SCALE_CONFIG
    
    if xg_value <= config['low_threshold']:
        return config['min_size']
    if xg_value >= config['high_threshold']:
        return config['max_size']
    
    if xg_value <= config['mid_threshold']:
        range_xg = config['mid_threshold'] - config['low_threshold']
        progress = (xg_value - config['low_threshold']) / range_xg
        return config['min_size'] + progress * config['slope_low']
    else:
        base_size = config['min_size'] + config['slope_low']
        range_xg = config['high_threshold'] - config['mid_threshold']
        progress = (xg_value - config['mid_threshold']) / range_xg
        remaining_size = config['max_size'] - base_size
        return base_size + progress * remaining_size

def calculate_shot_sizes(shots_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula tamaños para todos los disparos usando SOLO el xG real."""
    if shots_df.empty:
        return shots_df
    
    df_with_sizes = shots_df.copy()
    df_with_sizes['final_node_size'] = df_with_sizes['shot_xg'].apply(calculate_xg_node_size)
    
    return df_with_sizes

# ====================================================================
# MAIN FUNCTION
# ====================================================================

def create_shot_map(match_id: int, league: str, season: str,
                   team_colors: Dict[str, str] = None,
                   figsize: Tuple[int, int] = (16, 10),
                   save_path: Optional[str] = None) -> plt.Figure:
    """Create shot map con sistema de escalado unificado y líneas cohesivas."""
    
    from wrappers import understat_extract_shot_events
    shots_df = understat_extract_shot_events(match_id, league, season)
    
    if shots_df.empty:
        raise ValueError(f"No shots found for match {match_id}")
    
    shots_clean = shots_df.reset_index()
    teams = shots_clean['team'].unique()
    
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    
    shots_with_sizes = calculate_shot_sizes(shots_clean)
    
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    draw_pitch(ax)
    
    colors = {
        team_a: get_primary_color(team_a) if not team_colors else team_colors.get(team_a, get_primary_color(team_a)),
        team_b: get_primary_color(team_b) if not team_colors else team_colors.get(team_b, get_primary_color(team_b))
    }
    
    _draw_team_shots_unified(ax, shots_with_sizes, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots_unified(ax, shots_with_sizes, team_b, colors[team_b], 'right_to_left')
    
    _add_interior_layout(ax, shots_with_sizes, team_a, team_b, colors)
    
    ax.set_xlim(-2, 107)
    ax.set_ylim(-2, 70)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig

# ====================================================================
# DRAWING FUNCTIONS
# ====================================================================

def _draw_team_shots_unified(ax, shots_df: pd.DataFrame, team_name: str, team_color: str, direction: str):
    """Dibujar disparos usando tamaños del sistema unificado."""
    team_shots = shots_df[shots_df['team'] == team_name]
    
    for _, shot in team_shots.iterrows():
        x = float(shot['shot_location_x']) * 105
        y = float(shot['shot_location_y']) * 68
        
        if direction == 'right_to_left':
            x = 105 - x
            y = 68 - y
        
        final_size = shot['final_node_size']
        
        result = shot['shot_result']
        style = RESULT_STYLES.get(result, RESULT_STYLES['Missed Shot'])
        
        if result == 'Goal':
            face_color = '#FFD700'
            edge_color = team_color
        elif result == 'Saved Shot':
            face_color = team_color
            alpha = 0.5
        else:
            face_color = 'white'
            edge_color = team_color
        
        if result == 'Saved Shot':
            ax.scatter(x, y, s=final_size, c=face_color, marker=style['marker'],
                      alpha=alpha, edgecolors=edge_color, 
                      linewidth=style['width'], zorder=10)
        else:
            ax.scatter(x, y, s=final_size, c=face_color, marker=style['marker'],
                      alpha=style['alpha'], edgecolors=edge_color, 
                      linewidth=style['width'], zorder=10)
        
        if result == 'Goal':
            _draw_goal_line_cohesive(ax, x, y, direction, team_color, shot['shot_xg'])

def _draw_goal_line_cohesive(ax, shot_x: float, shot_y: float, direction: str, team_color: str, xg_value: float):
    """
    Dibujar línea de gol con gradiente y flecha final al estilo pass_network.
    Adapta el grosor según el xG del disparo.
    """
    # Determinar la portería objetivo
    goal_x = 105 if direction == 'left_to_right' else 0
    goal_y = 34
    
    # Calcular grosor basado en xG (similar a pass_count en connections)
    base_width = GOAL_LINE_CONFIG['width_base']
    width_factor = GOAL_LINE_CONFIG['width_multiplier']
    line_width = base_width + (xg_value * width_factor * 8)  # Escalar según xG
    line_width = max(line_width, 1.5)  # Mínimo
    line_width = min(line_width, 6.0)  # Máximo
    
    # Calcular dirección y distancia
    dx, dy = goal_x - shot_x, goal_y - shot_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vector unitario
    ux, uy = dx / length, dy / length
    
    # Calcular punto final (sin llegar exactamente a la portería)
    margin = 2.0  # Espacio antes de la portería
    end_x = goal_x - margin * ux
    end_y = goal_y - margin * uy
    
    # Crear gradiente suave con más puntos
    num_points = GOAL_LINE_CONFIG['gradient_points']
    x_points = np.linspace(shot_x, end_x, num_points)
    y_points = np.linspace(shot_y, end_y, num_points)
    
    # Crear segmentos para LineCollection
    points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Gradiente de transparencia (como en pass_network)
    alphas = np.linspace(0.15, 1.0, len(segments))
    rgb = mcolors.to_rgb(team_color)
    colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
    
    # Dibujar línea con gradiente
    lc = LineCollection(segments, colors=colors_with_alpha, linewidths=line_width,
                       capstyle='round', zorder=8)
    ax.add_collection(lc)
    
    # Dibujar flecha al final (adaptada de pass_network)
    _draw_goal_arrow_cohesive(ax, shot_x, shot_y, end_x, end_y, team_color, line_width)

def _draw_goal_arrow_cohesive(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                             color: str, line_width: float):
    """
    Dibujar flecha al final de la línea de gol usando la misma lógica que pass_network.
    """
    # Calcular dirección
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vector unitario y perpendicular
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    
    # Tamaño de flecha adaptado del line_width
    size = max(GOAL_LINE_CONFIG['arrow_size'], line_width * 0.25)
    extension = size * GOAL_LINE_CONFIG['arrow_extension']
    
    # Punto de la punta (ligeramente extendido)
    tip_x = end_x + extension * ux
    tip_y = end_y + extension * uy
    
    # Punto base de la flecha
    origin_x = tip_x - size * 1.0 * ux + size * 0.7 * px
    origin_y = tip_y - size * 1.0 * uy + size * 0.7 * py
    
    # Dibujar la flecha
    ax.plot([tip_x, origin_x], [tip_y, origin_y], 
           color=color, linewidth=max(2.0, line_width * 0.8), 
           alpha=1.0, solid_capstyle='round', zorder=100)

def _add_interior_layout(ax, shots_df: pd.DataFrame, team_a: str, team_b: str, colors: Dict):
    """Layout interior con leyendas centrales y xG en círculo central."""
    
    team_a_shots = shots_df[shots_df['team'] == team_a]
    team_b_shots = shots_df[shots_df['team'] == team_b]
    
    a_xg = team_a_shots['shot_xg'].sum()
    b_xg = team_b_shots['shot_xg'].sum()
    
    a_has_higher_xg = a_xg >= b_xg
    
    center_x, center_y = 52.5, 34
    lateral_offset = 18
    
    _draw_central_xg(ax, center_x - lateral_offset, center_y, b_xg, colors[team_b], not a_has_higher_xg)
    _draw_central_xg(ax, center_x + lateral_offset, center_y, a_xg, colors[team_a], a_has_higher_xg)
    
    legend_y = 2
    
    _draw_xg_scale_legend(ax, center_x-15, legend_y, colors[team_a], shots_df)
    _draw_symbols_legend(ax, center_x+3.5, legend_y)

def _draw_central_xg(ax, x: float, y: float, xg_value: float, team_color: str, is_higher: bool):
    """Dibujar xG en lateral del círculo central con styling diferenciado."""
    
    if is_higher:
        bbox_props = dict(boxstyle="round,pad=0.6", facecolor=team_color, 
                         edgecolor=team_color, linewidth=3, alpha=0.9)
        text_color = 'white'
    else:
        bbox_props = dict(boxstyle="round,pad=0.6", facecolor='white', 
                         edgecolor=team_color, linewidth=3, alpha=0.9)
        text_color = team_color
    
    ax.text(x, y, f"{xg_value:.1f} xG", ha='center', va='center',
           fontsize=18, fontweight='bold', color=text_color,
           family=FONT_CONFIG['family'], bbox=bbox_props, zorder=20)

def _draw_xg_scale_legend(ax, x: float, y: float, color: str, shots_df: pd.DataFrame):
    """Leyenda con escalado dinámico basado en xG máximo del partido."""
    
    max_xg_match = shots_df['shot_xg'].max()
    
    if max_xg_match <= 0.8:
        high_xg = max_xg_match
        low_xg = min(0.05, max_xg_match * 0.1)
    else:
        high_xg = XG_SCALE_CONFIG['high_threshold']
        low_xg = XG_SCALE_CONFIG['low_threshold']
    
    low_size = calculate_xg_node_size(low_xg)
    high_size = calculate_xg_node_size(high_xg)
    
    arrow_length = 14
    number_offset = 3
    positions = [x - arrow_length/2 - number_offset, x + arrow_length/2 + number_offset]
    circle_y = y + 3
    text_y = y - 1.2
    
    ax.scatter(positions[0]+1, circle_y, s=low_size, c='white',
              edgecolors='black', linewidth=2)
    ax.text(positions[0]+1, text_y, f"{low_xg:.2f}", ha='center', fontsize=12, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.scatter(positions[1]-1, circle_y, s=high_size, c='white', 
              edgecolors='black', linewidth=2)
    ax.text(positions[1]-1, text_y, f"{high_xg:.2f}", ha='center', fontsize=12, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    arrow_start_x = x - arrow_length/2
    arrow_end_x = x + arrow_length/2
    ax.annotate('', xy=(arrow_end_x, text_y + 0.5), xytext=(arrow_start_x, text_y + 0.5),
               arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))
    
    ax.text(x, circle_y-2.5, "xG", ha='center', va='center', fontsize=14, 
           fontweight='bold', family=FONT_CONFIG['family'])

def _draw_symbols_legend(ax, x: float, y: float):
    """Leyenda de símbolos."""
    
    ax.scatter(x, y, s=300, marker='*', c='#FFD700', edgecolors='black', linewidth=2)
    ax.text(x + 1.5, y, "Gol", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.text(x + 5, y, "|", ha='center', va='center', fontsize=11, 
           family=FONT_CONFIG['family'])
    
    ax.scatter(x + 7, y, s=200, marker='s', c='gray', alpha=0.5, edgecolors='black', linewidth=2)
    ax.text(x + 8.5, y, "Parada", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.text(x + 14.5, y, "|", ha='center', va='center', fontsize=11, 
           family=FONT_CONFIG['family'])
    
    ax.scatter(x + 16, y, s=150, marker='o', c='white', edgecolors='black', linewidth=2)
    ax.text(x + 17.25, y, "Otros", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])

# ====================================================================
# CONVENIENCE FUNCTION
# ====================================================================

def create_shot_map_with_match_data(match_data: Dict[str, pd.DataFrame],
                                   team_colors: Dict[str, str] = None,
                                   save_path: Optional[str] = None) -> plt.Figure:
    """Crear shot map desde datos pre-cargados con escalado unificado y líneas cohesivas."""
    if 'shots' not in match_data or match_data['shots'].empty:
        raise ValueError("No shot data found in match_data")
    
    shots_df = match_data['shots']
    shots_clean = shots_df.reset_index() if hasattr(shots_df.index, 'levels') else shots_df
    
    teams = shots_clean['team'].unique()
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    
    shots_with_sizes = calculate_shot_sizes(shots_clean)
    
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    draw_pitch(ax)
    
    colors = {
        team_a: get_primary_color(team_a) if not team_colors else team_colors.get(team_a, get_primary_color(team_a)),
        team_b: get_primary_color(team_b) if not team_colors else team_colors.get(team_b, get_primary_color(team_b))
    }
    
    _draw_team_shots_unified(ax, shots_with_sizes, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots_unified(ax, shots_with_sizes, team_b, colors[team_b], 'right_to_left')
    
    _add_interior_layout(ax, shots_with_sizes, team_a, team_b, colors)
    
    ax.set_xlim(-2, 107)
    ax.set_ylim(-2, 70)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig