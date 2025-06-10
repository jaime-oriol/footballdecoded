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
import os
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
    'min_passes': 5,  # Ahora empieza en 5 pases
    'alpha': 0.8,
    'offset': 1.0,  # Aumentado para mejor separación
    'arrow_length': 1.2,  # Tamaño de flecha ajustado
    'arrow_width': 0.8
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
    _draw_connections(ax, team_data['connections'], team_data['players'], colors['secondary'])
    _draw_players(ax, team_data['players'], colors['primary'])
    
    if show_labels:
        _draw_labels(ax, team_data['players'])
    
    # Añadir leyenda en la parte inferior
    _draw_legend(ax, team_data, team_name)
    
    # Configurar ejes
    ax.set_xlim(-5, 110)
    ax.set_ylim(-18, 73)  # AÚN MÁS espacio para leyenda completa
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
    """Dibuja áreas de penalti con semicírculos CORRECTOS."""
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
    # Área izquierda
    ax.plot([penalty_length, penalty_length], [penalty_y, penalty_y + penalty_width], 
           color=color, linewidth=lw)
    ax.plot([0, penalty_length], [penalty_y, penalty_y], 
           color=color, linewidth=lw)
    ax.plot([0, penalty_length], [penalty_y + penalty_width, penalty_y + penalty_width], 
           color=color, linewidth=lw)
    
    # Área derecha  
    ax.plot([length - penalty_length, length - penalty_length], [penalty_y, penalty_y + penalty_width], 
           color=color, linewidth=lw)
    ax.plot([length - penalty_length, length], [penalty_y, penalty_y], 
           color=color, linewidth=lw)
    ax.plot([length - penalty_length, length], [penalty_y + penalty_width, penalty_y + penalty_width], 
           color=color, linewidth=lw)
    
    # Áreas pequeñas (6 yards)
    # Área pequeña izquierda
    ax.plot([small_length, small_length], [small_y, small_y + small_width], 
           color=color, linewidth=lw)
    ax.plot([0, small_length], [small_y, small_y], 
           color=color, linewidth=lw)
    ax.plot([0, small_length], [small_y + small_width, small_y + small_width], 
           color=color, linewidth=lw)
    
    # Área pequeña derecha
    ax.plot([length - small_length, length - small_length], [small_y, small_y + small_width], 
           color=color, linewidth=lw)
    ax.plot([length - small_length, length], [small_y, small_y], 
           color=color, linewidth=lw)
    ax.plot([length - small_length, length], [small_y + small_width, small_y + small_width], 
           color=color, linewidth=lw)
    
    # Semicírculos y puntos de penalti
    penalty_spot_distance = 11.0
    semicircle_radius = 9.15
    
    # Calcular ángulos para que SOLO se vea la parte EXTERIOR del área
    # Distancia desde centro del semicírculo al borde del área
    distance_to_area_edge = penalty_length - penalty_spot_distance  # 16.5 - 11 = 5.5
    
    # Ángulo donde el semicírculo intersecta con el borde del área
    if distance_to_area_edge < semicircle_radius:
        angle_rad = np.arccos(distance_to_area_edge / semicircle_radius)
        angle_deg = np.degrees(angle_rad)
        
        # Semicírculo izquierdo - solo la parte que sale del área
        theta1 = -angle_deg
        theta2 = angle_deg
        
        semicircle_l = patches.Arc((penalty_spot_distance, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=theta1, theta2=theta2, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_l)
        
        # Semicírculo derecho - solo la parte que sale del área
        theta1_r = 180 - angle_deg
        theta2_r = 180 + angle_deg
        
        semicircle_r = patches.Arc((length - penalty_spot_distance, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=theta1_r, theta2=theta2_r, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_r)
    
    # Puntos de penalti
    ax.plot(penalty_spot_distance, width/2, 'o', color=color, markersize=4)
    ax.plot(length - penalty_spot_distance, width/2, 'o', color=color, markersize=4)

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
    """Dibuja conexiones entre jugadores con flechas desde bordes de nodos."""
    if connections_df.empty:
        return
    
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
        
        # Calcular radios de los nodos
        source_radius = _get_node_radius(source_pos.iloc[0]['total_passes'])
        target_radius = _get_node_radius(target_pos.iloc[0]['total_passes'])
        
        # Calcular puntos de conexión desde bordes
        start_x, start_y, end_x, end_y = _calculate_edge_points(
            x1, y1, x2, y2, source_radius, target_radius, conn['pass_count']
        )
        
        # Determinar grosor y opacidad
        line_width = _calculate_line_width(conn['pass_count'])
        alpha = min(0.4 + (conn['pass_count'] / 30) * 0.5, 0.9)
        
        # Dibujar línea principal
        ax.plot([start_x, end_x], [start_y, end_y], 
               color=color, linewidth=line_width, alpha=alpha,
               solid_capstyle='round', zorder=1)
        
        # Dibujar flecha
        _draw_arrow_head(ax, start_x, start_y, end_x, end_y, color, line_width, alpha)

def _calculate_edge_points(x1: float, y1: float, x2: float, y2: float, 
                          r1: float, r2: float, pass_count: int) -> Tuple[float, float, float, float]:
    """Calcula puntos: flecha sale JUSTO del borde, llega con MUCHO margen."""
    # Vector dirección
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    # Vector unitario
    ux = dx / length
    uy = dy / length
    
    # Vector perpendicular para offset
    perp_x = -uy
    perp_y = ux
    
    # Offset basado en número de pases
    offset = CONNECTION_CONFIG['offset'] * (1 + pass_count / 50)
    
    # INICIO: Sale EXACTAMENTE del borde del nodo (sin margen adicional)
    start_x = x1 + r1 * ux + perp_x * offset
    start_y = y1 + r1 * uy + perp_y * offset
    
    # FINAL: Llega con MUCHO margen para no tapar nombres
    large_margin = 4.0  # Margen muy grande para evitar tapar nombres
    end_x = x2 - (r2 + large_margin) * ux + perp_x * offset
    end_y = y2 - (r2 + large_margin) * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def _draw_arrow_head(ax, start_x: float, start_y: float, end_x: float, end_y: float, 
                    color: str, line_width: float, alpha: float):
    """Dibuja punta de flecha que se SUPERPONE a la línea."""
    # Vector dirección
    dx = end_x - start_x
    dy = end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vector unitario
    ux = dx / length
    uy = dy / length
    
    # Tamaño de la flecha proporcional al grosor de línea
    arrow_length = CONNECTION_CONFIG['arrow_length'] * (1 + line_width / 8)
    arrow_width = CONNECTION_CONFIG['arrow_width'] * (1 + line_width / 12)
    
    # EXTENDER la flecha más allá del final de la línea para superponerse
    extension = arrow_length * 0.3  # 30% de extensión
    arrow_tip_x = end_x + extension * ux
    arrow_tip_y = end_y + extension * uy
    
    # Puntos de la flecha (ahora más larga para cubrír línea)
    back_x = arrow_tip_x - (arrow_length + extension) * ux
    back_y = arrow_tip_y - (arrow_length + extension) * uy
    
    left_x = back_x - arrow_width * (-uy)
    left_y = back_y - arrow_width * ux
    
    right_x = back_x + arrow_width * (-uy)
    right_y = back_y + arrow_width * ux
    
    # Dibujar triángulo de flecha con Z-ORDER ALTO para que esté encima
    triangle = patches.Polygon([(arrow_tip_x, arrow_tip_y), (left_x, left_y), (right_x, right_y)],
                              closed=True, facecolor=color, edgecolor=color,
                              alpha=alpha, linewidth=0, zorder=5)  # Z-order más alto
    ax.add_patch(triangle)

def _calculate_line_width(pass_count: int) -> float:
    """Calcula grosor de línea: 5, 10, 15, 25+ pases."""
    if pass_count < 5: return 0.5
    elif pass_count < 10: return 2.5
    elif pass_count < 15: return 5.0
    elif pass_count < 25: return 7.5
    else: return 10.0

def _get_node_radius(total_passes: int) -> float:
    """Calcula radio del nodo basado en total de pases."""
    node_size = _calculate_node_size(total_passes)
    # Radio visual aproximado (ajustado para coincidir con scatter)
    return np.sqrt(node_size / np.pi) / 18

# ====================================================================
# DIBUJO DE JUGADORES
# ====================================================================

def _draw_players(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores con 4 tamaños MUY diferenciados."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        
        # Tamaño del nodo
        node_size = _calculate_node_size(player['total_passes'])
        
        # Círculo con relleno y borde del mismo color
        ax.scatter(x, y, s=node_size, 
                  c=color, alpha=0.6,
                  edgecolors=color, linewidth=4,
                  zorder=10)

def _calculate_node_size(total_passes: int) -> float:
    """Calcula tamaño de nodo con 4 categorías MUY diferenciadas."""
    if total_passes <= 10:
        return 800    # Categoría 1: Pocos pases
    elif total_passes <= 25:
        return 1800   # Categoría 2: Pases moderados
    elif total_passes <= 50:
        return 3200   # Categoría 3: Muchos pases
    else:
        return 5000   # Categoría 4: Muchísimos pases

def _draw_labels(ax, players_df: pd.DataFrame):
    """Dibuja nombres de jugadores dentro de los nodos con letra más grande."""
    for _, player in players_df.iterrows():
        name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        # Acortar nombre si es muy largo
        display_name = name
        if len(name) > 16:
            parts = name.split()
            if len(parts) >= 2:
                display_name = f"{parts[0]} {parts[-1]}"
        
        # Texto más grande
        ax.text(x, y, display_name,
               ha='center', va='center',
               color='white', fontsize=16, fontweight='bold',  # Más grande
               family='Arial',
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=11)

# ====================================================================
# LEYENDA
# ====================================================================

def _draw_legend(ax, team_data: Dict[str, pd.DataFrame], team_name: str):
    """Dibuja leyenda con el mismo color que los nodos."""
    # Obtener color del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    legend_color = colors['primary']  # Mismo color que los nodos
    
    # Posición de la leyenda MÁS BAJA para que se vea completa
    legend_y = -10
    
    # Solo mostrar total de pases (sin conexiones)
    total_passes = len(team_data['passes'])
    
    # Texto principal solo con pases
    stats_text = f"Pases: {total_passes}"
    ax.text(52.5, legend_y, stats_text, ha='center', va='center',
           fontsize=18, fontweight='bold', color=legend_color, family='Arial')
    
    # Escala de nodos (lado izquierdo)
    _draw_node_scale_legend(ax, 20, legend_y - 4, legend_color)
    
    # Escala de conexiones (lado derecho)  
    _draw_connection_scale_legend(ax, 85, legend_y - 4, legend_color)

def _draw_node_scale_legend(ax, x: float, y: float, color: str):
    """Dibuja escala de tamaños de nodos con el color del equipo."""
    # 4 tamaños diferenciados
    sizes = [10, 25, 50, 75]  # Ejemplos de pases
    circle_sizes = [_calculate_node_size(s) for s in sizes]
    positions = [x - 15, x - 5, x + 5, x + 15]
    
    for i, (size, circle_size, pos) in enumerate(zip(sizes, circle_sizes, positions)):
        ax.scatter(pos, y, s=circle_size, c=color, alpha=0.6, 
                  edgecolors=color, linewidth=3, zorder=10)
        
        # Etiquetas MÁS ABAJO para que se vean completamente
        label = f"≤{size}" if i < 3 else f"{size}+"
        ax.text(pos, y - 3.5, label, ha='center', va='top', 
               fontsize=12, fontweight='bold', color=color, family='Arial')
    
    # Etiqueta de la escala MÁS ARRIBA
    ax.text(x, y + 2.5, "pases", ha='center', va='bottom',
           fontsize=14, fontweight='bold', color=color, family='Arial')

def _draw_connection_scale_legend(ax, x: float, y: float, color: str):
    """Dibuja escala de grosores de conexiones con el color del equipo."""
    # Líneas de ejemplo según nueva escala
    pass_counts = [5, 10, 15, 25]
    line_widths = [_calculate_line_width(p) for p in pass_counts]
    positions = [x - 15, x - 5, x + 5, x + 15]
    
    for i, (passes, width, pos) in enumerate(zip(pass_counts, line_widths, positions)):
        # Línea con el color del equipo - MÁS LARGA para ver mejor
        ax.plot([pos - 3, pos + 3], [y, y], color=color, 
               linewidth=width, alpha=0.8, solid_capstyle='round')
        
        # Etiquetas MÁS ABAJO para que se vean completamente
        label = f"{passes}" if passes < 25 else f"{passes}+"
        ax.text(pos, y - 3.5, label, ha='center', va='top',
               fontsize=12, fontweight='bold', color=color, family='Arial')
    
    # Etiqueta de la escala MÁS ARRIBA
    ax.text(x, y + 2.5, "pases", ha='center', va='bottom',
           fontsize=14, fontweight='bold', color=color, family='Arial')

# ====================================================================
# FUNCIONES DE CONVENIENCIA
# ====================================================================

def load_from_csv_files(passes_path: str, players_path: str, connections_path: str) -> Dict[str, pd.DataFrame]:
    """Carga datos desde archivos CSV específicos."""
    match_data = {
        'passes': pd.read_csv(passes_path),
        'players': pd.read_csv(players_path),
        'connections': pd.read_csv(connections_path)
    }
    
    print(f"✅ Datos cargados desde CSV:")
    print(f"   - Pases: {len(match_data['passes'])} filas")
    print(f"   - Jugadores: {len(match_data['players'])} filas")
    print(f"   - Conexiones: {len(match_data['connections'])} filas")
    
    return match_data

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