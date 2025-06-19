# ====================================================================
# FootballDecoded - Shot Map con Sistema de Escalado Unificado
# ====================================================================

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

from visualization.core import (
    draw_pitch, get_primary_color, FONT_CONFIG
)

# ====================================================================
# CONFIGURACIÓN UNIFICADA DE ESCALADO
# ====================================================================

# Sistema suave como pass_network pero adaptado a xG
XG_SCALE_CONFIG = {
    'min_size': 200,        # Coherente con pass_network
    'max_size': 2500,       # Rango razonable para shot map
    'low_threshold': 0.05,  # xG bajo
    'mid_threshold': 0.30,  # xG medio (punto de inflexión)
    'high_threshold': 0.80, # xG alto
    'slope_low': 800,       # Crecimiento suave inicial
    'slope_high': 800       # Crecimiento suave final
}

RESULT_STYLES = {
    'Goal': {'marker': '*', 'alpha': 1.0, 'face': '#FFD700', 'edge': 'team_color', 'width': 2},
    'Saved Shot': {'marker': 's', 'alpha': 1.0, 'face': 'team_color', 'edge': 'black', 'width': 2},
    'Blocked Shot': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': 'gray', 'width': 2},
    'Missed Shot': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': 'lightgray', 'width': 2},
    'Shot On Post': {'marker': 'o', 'alpha': 1.0, 'face': 'team_color', 'edge': '#FF6B35', 'width': 2}
}

# ====================================================================
# SISTEMA DE ESCALADO UNIFICADO (Adaptado de Pass Network)
# ====================================================================

def calculate_xg_node_size(xg_value: float) -> float:
    """
    Sistema suave de escalado adaptado del pass_network.
    
    Escalado por tramos como pass_network:
    - xG ≤ 0.05 → Tamaño mínimo (400)
    - xG 0.05-0.30 → Crecimiento suave
    - xG 0.30-0.80 → Crecimiento suave continuado  
    - xG ≥ 0.80 → Tamaño máximo (2000)
    """
    config = XG_SCALE_CONFIG
    
    # Casos extremos (igual que pass_network)
    if xg_value <= config['low_threshold']:
        return config['min_size']
    if xg_value >= config['high_threshold']:
        return config['max_size']
    
    # Crecimiento por tramos (lógica pass_network adaptada)
    if xg_value <= config['mid_threshold']:
        # Fase 1: Crecimiento suave (0.05 → 0.30)
        range_xg = config['mid_threshold'] - config['low_threshold']  # 0.25
        progress = (xg_value - config['low_threshold']) / range_xg
        return config['min_size'] + progress * config['slope_low']
    else:
        # Fase 2: Crecimiento suave continuado (0.30 → 0.80)
        base_size = config['min_size'] + config['slope_low']  # 1200
        range_xg = config['high_threshold'] - config['mid_threshold']  # 0.50
        progress = (xg_value - config['mid_threshold']) / range_xg
        remaining_size = config['max_size'] - base_size  # 800
        return base_size + progress * remaining_size

def calculate_shot_sizes(shots_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula tamaños para todos los disparos usando SOLO el xG real."""
    if shots_df.empty:
        return shots_df
    
    df_with_sizes = shots_df.copy()
    
    # SOLO el xG determina el tamaño - sin multiplicadores artificiales
    df_with_sizes['final_node_size'] = df_with_sizes['shot_xg'].apply(calculate_xg_node_size)
    
    return df_with_sizes

# ====================================================================
# FUNCIÓN PRINCIPAL DE SHOT MAP
# ====================================================================

def create_shot_map(match_id: int, league: str, season: str,
                   team_colors: Dict[str, str] = None,
                   figsize: Tuple[int, int] = (16, 10),
                   save_path: Optional[str] = None) -> plt.Figure:
    """Create shot map con sistema de escalado unificado."""
    
    # Extraer datos
    from wrappers import understat_extract_shot_events
    shots_df = understat_extract_shot_events(match_id, league, season)
    
    if shots_df.empty:
        raise ValueError(f"No shots found for match {match_id}")
    
    shots_clean = shots_df.reset_index()
    teams = shots_clean['team'].unique()
    
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    
    # APLICAR SISTEMA DE ESCALADO UNIFICADO
    shots_with_sizes = calculate_shot_sizes(shots_clean)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    draw_pitch(ax)
    
    # Obtener colores
    colors = {
        team_a: get_primary_color(team_a) if not team_colors else team_colors.get(team_a, get_primary_color(team_a)),
        team_b: get_primary_color(team_b) if not team_colors else team_colors.get(team_b, get_primary_color(team_b))
    }
    
    # Dibujar disparos con tamaños calculados
    _draw_team_shots_unified(ax, shots_with_sizes, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots_unified(ax, shots_with_sizes, team_b, colors[team_b], 'right_to_left')
    
    # Layout inferior con leyenda unificada
    _add_unified_layout(ax, shots_with_sizes, team_a, team_b, colors)
    
    # Formato final
    ax.set_xlim(-5, 110)
    ax.set_ylim(-10, 77)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig

# ====================================================================
# FUNCIONES DE DIBUJO UNIFICADAS
# ====================================================================

def _draw_team_shots_unified(ax, shots_df: pd.DataFrame, team_name: str, team_color: str, direction: str):
    """Dibujar disparos usando tamaños del sistema unificado."""
    team_shots = shots_df[shots_df['team'] == team_name]
    
    for _, shot in team_shots.iterrows():
        # Coordenadas
        x = float(shot['shot_location_x']) * 105
        y = float(shot['shot_location_y']) * 68
        
        if direction == 'right_to_left':
            x = 105 - x
            y = 68 - y
        
        # Usar tamaño calculado DIRECTAMENTE del xG
        final_size = shot['final_node_size']  # Solo xG, sin multiplicadores
        
        # Estilo según resultado
        result = shot['shot_result']
        style = RESULT_STYLES.get(result, RESULT_STYLES['Missed Shot'])
        
        # Colores específicos según tipo
        if result == 'Goal':
            # Goles: dorado por dentro, borde del equipo
            face_color = '#FFD700'
            edge_color = team_color
        elif result == 'Saved Shot':

            face_color = team_color
            alpha = 0.5
        else:
            # Resto: blanco por dentro, borde del equipo
            face_color = 'white'
            edge_color = team_color
        
        # Aplicar alpha específico para paradas
        if result == 'Saved Shot':
            ax.scatter(x, y, s=final_size, c=face_color, marker=style['marker'],
                      alpha=alpha, edgecolors=edge_color, 
                      linewidth=style['width'], zorder=10)
        else:
            ax.scatter(x, y, s=final_size, c=face_color, marker=style['marker'],
                      alpha=style['alpha'], edgecolors=edge_color, 
                      linewidth=style['width'], zorder=10)
        
        # Línea de dirección para goles
        if result == 'Goal':
            _draw_goal_line(ax, x, y, direction, team_color)

def _draw_goal_line(ax, shot_x: float, shot_y: float, direction: str, team_color: str):
    """Dibujar línea de dirección del gol con gradiente."""
    from matplotlib.collections import LineCollection
    import matplotlib.colors as mcolors
    
    goal_x = 105 if direction == 'left_to_right' else 0
    goal_y = 34
    
    # Crear línea con gradiente
    num_points = 50
    x_points = np.linspace(shot_x, goal_x, num_points)
    y_points = np.linspace(shot_y, goal_y, num_points)
    
    points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    alphas = np.linspace(0.3, 1.0, len(segments))
    rgb = mcolors.to_rgb(team_color)
    colors_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
    
    lc = LineCollection(segments, colors=colors_alpha, linewidths=3.5, capstyle='round', zorder=7)
    ax.add_collection(lc)

def _add_unified_layout(ax, shots_df: pd.DataFrame, team_a: str, team_b: str, colors: Dict):
    """Layout con leyenda de escalado unificado."""
    
    # Estadísticas de equipos
    team_a_shots = shots_df[shots_df['team'] == team_a]
    a_total, a_xg, a_goals = len(team_a_shots), team_a_shots['shot_xg'].sum(), team_a_shots['is_goal'].sum()
    
    team_b_shots = shots_df[shots_df['team'] == team_b]
    b_total, b_xg, b_goals = len(team_b_shots), team_b_shots['shot_xg'].sum(), team_b_shots['is_goal'].sum()
    
    # Estadísticas de equipos
    ax.text(0, -3, f"Disparos: {b_total} | xG: {b_xg:.2f} | Goles: {b_goals}",
           fontsize=14, ha='left', color=colors[team_b], fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.text(105, -3, f"Disparos: {a_total} | xG: {a_xg:.2f} | Goles: {a_goals}",
           fontsize=14, ha='right', color=colors[team_a], fontweight='bold', family=FONT_CONFIG['family'])
    
    # LEYENDA XG UNIFICADA (misma lógica que pass_network)
    center_x = 52.5
    legend_y = 2
    
    # Leyenda de escalado xG (coherente con pass_network)
    _draw_xg_scale_legend(ax, center_x-15, legend_y, colors[team_a], shots_df)
    
    # Leyenda de símbolos (lado derecho)
    _draw_symbols_legend(ax, center_x+3.5, legend_y)

def _draw_xg_scale_legend(ax, x: float, y: float, color: str, shots_df: pd.DataFrame):
    """Leyenda con escalado dinámico basado en xG máximo del partido."""
    
    # Calcular xG máximo real del partido
    max_xg_match = shots_df['shot_xg'].max()
    
    # Ajustar umbrales dinámicamente
    if max_xg_match <= 0.8:
        # Si el xG máximo es bajo, usar el máximo real como umbral superior
        high_xg = max_xg_match
        low_xg = min(0.05, max_xg_match * 0.1)  # Proporcionalmente menor
    else:
        # Si hay disparos de muy alto xG, mantener rango amplio
        high_xg = XG_SCALE_CONFIG['high_threshold']  # 0.80
        low_xg = XG_SCALE_CONFIG['low_threshold']    # 0.05
    
    # Tamaños basados en umbrales dinámicos
    low_size = calculate_xg_node_size(low_xg)
    high_size = calculate_xg_node_size(high_xg)
    
    # Layout exacto como pass_network
    arrow_length = 14
    number_offset = 3
    positions = [x - arrow_length/2 - number_offset, x + arrow_length/2 + number_offset]
    circle_y = y + 3
    text_y = y - 1.2
    
    # Círculo pequeño (xG bajo) - tamaño real
    ax.scatter(positions[0]+1, circle_y, s=low_size, c='white',
              edgecolors='black', linewidth=2)
    ax.text(positions[0]+1, text_y, f"{low_xg:.2f}", ha='center', fontsize=12, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    # Círculo grande (xG alto) - tamaño real
    ax.scatter(positions[1]-1, circle_y, s=high_size, c='white', 
              edgecolors='black', linewidth=2)
    ax.text(positions[1]-1, text_y, f"{high_xg:.2f}", ha='center', fontsize=12, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    # Flecha ENTRE los números (como pass_network) - coordenadas exactas
    arrow_start_x = x - arrow_length/2
    arrow_end_x = x + arrow_length/2
    ax.annotate('', xy=(arrow_end_x, text_y + 0.5), xytext=(arrow_start_x, text_y + 0.5),
               arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))
    
    # Texto xG centrado sobre la flecha
    ax.text(x, circle_y-2.5, "xG", ha='center', va='center', fontsize=14, 
           fontweight='bold', family=FONT_CONFIG['family'])

def _draw_symbols_legend(ax, x: float, y: float):
    """Leyenda de símbolos (mantenida del diseño original)."""
    
    # Gol (estrella): dorado por dentro, borde negro
    ax.scatter(x, y, s=300, marker='*', c='#FFD700', edgecolors='black', linewidth=2)
    ax.text(x + 1.5, y, "Gol", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    # Separador
    ax.text(x + 5, y, "|", ha='center', va='center', fontsize=11, 
           family=FONT_CONFIG['family'])
    
    # Parada (cuadrado): gris más claro, borde negro
    ax.scatter(x + 7, y, s=200, marker='s', c='gray', alpha=0.5, edgecolors='black', linewidth=2)
    ax.text(x + 8.5, y, "Parada", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])
    
    # Separador
    ax.text(x + 14.5, y, "|", ha='center', va='center', fontsize=11, 
           family=FONT_CONFIG['family'])
    
    # Otros (círculo): blanco por dentro, borde negro
    ax.scatter(x + 16, y, s=150, marker='o', c='white', edgecolors='black', linewidth=2)
    ax.text(x + 17.25, y, "Otros", ha='left', va='center', fontsize=11, 
           fontweight='bold', family=FONT_CONFIG['family'])

# ====================================================================
# FUNCIÓN PARA DATOS PRE-CARGADOS
# ====================================================================

def create_shot_map_with_match_data(match_data: Dict[str, pd.DataFrame],
                                   team_colors: Dict[str, str] = None,
                                   save_path: Optional[str] = None) -> plt.Figure:
    """Crear shot map desde datos pre-cargados con escalado unificado."""
    if 'shots' not in match_data or match_data['shots'].empty:
        raise ValueError("No shot data found in match_data")
    
    shots_df = match_data['shots']
    shots_clean = shots_df.reset_index() if hasattr(shots_df.index, 'levels') else shots_df
    
    teams = shots_clean['team'].unique()
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    
    # APLICAR SISTEMA DE ESCALADO UNIFICADO
    shots_with_sizes = calculate_shot_sizes(shots_clean)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    draw_pitch(ax)
    
    # Colores
    colors = {
        team_a: get_primary_color(team_a) if not team_colors else team_colors.get(team_a, get_primary_color(team_a)),
        team_b: get_primary_color(team_b) if not team_colors else team_colors.get(team_b, get_primary_color(team_b))
    }
    
    # Dibujar
    _draw_team_shots_unified(ax, shots_with_sizes, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots_unified(ax, shots_with_sizes, team_b, colors[team_b], 'right_to_left')
    
    ax.text(52.5, 72, "Shot Map", ha='center', va='center',
           fontsize=20, fontweight='bold', family=FONT_CONFIG['family'])
    
    _add_unified_layout(ax, shots_with_sizes, team_a, team_b, colors)
    
    ax.set_xlim(-5, 110)
    ax.set_ylim(-10, 77)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig