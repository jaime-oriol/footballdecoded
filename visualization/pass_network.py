# ====================================================================
# FootballDecoded - Visualizador de Redes de Pase CORREGIDO
# ====================================================================
# Módulo corregido para conexiones precisas desde borde de nodos
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

# Configuración de conexiones CORREGIDA
CONNECTION_CONFIG = {
    'min_passes': 5,
    'alpha': 0.8,
    'base_offset': 0.4,
    'arrow_length': 1.0,      # MÁS PEQUEÑA
    'arrow_width': 0.6,       # MÁS PEQUEÑA
    'name_margin': 2.0       # Margen para nombres
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
    """Crea visualización de red de pases CORREGIDA."""
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
    
    # Dibujar red de pases CORREGIDA
    _draw_connections_corrected(ax, team_data['connections'], team_data['players'], colors['secondary'])
    _draw_players(ax, team_data['players'], colors['primary'])
    
    if show_labels:
        _draw_labels(ax, team_data['players'])
    
    # Añadir leyenda CORREGIDA
    _draw_legend_corrected(ax, team_data, team_name)
    
    # Configurar ejes con leyenda PEGADA al campo
    ax.set_xlim(-5, 110)
    ax.set_ylim(-8, 68)  # Leyenda PEGADA al borde del campo
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Guardado: {save_path}")
    
    return fig

# ====================================================================
# DIBUJO DEL CAMPO (SIN CAMBIOS)
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
# DIBUJO DE CONEXIONES CORREGIDO
# ====================================================================

def _draw_connections_corrected(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones CORREGIDAS: desde borde exacto, flecha lejos del nombre."""
    if connections_df.empty:
        return
    
    for _, conn in connections_df.iterrows():
        if conn['pass_count'] < CONNECTION_CONFIG['min_passes']:
            continue
            
        # Obtener datos de jugadores
        source_data = players_df[players_df['player'] == conn['source']]
        target_data = players_df[players_df['player'] == conn['target']]
        
        if source_data.empty or target_data.empty:
            continue
        
        source_player = source_data.iloc[0]
        target_player = target_data.iloc[0]
        
        # Calcular radios REALES basados en tamaño específico del nodo
        source_radius = _get_actual_node_radius(source_player['total_passes'])
        target_radius = _get_actual_node_radius(target_player['total_passes'])
        
        # Calcular puntos CORREGIDOS
        start_x, start_y, end_x, end_y = _calculate_corrected_points(
            source_player['avg_x'], source_player['avg_y'],
            target_player['avg_x'], target_player['avg_y'],
            source_radius, target_radius, conn['pass_count']
        )
        
        # Propiedades de línea
        line_width = _calculate_line_width(conn['pass_count'])
        alpha = min(0.4 + (conn['pass_count'] / 30) * 0.5, 0.9)
        
        # Dibujar línea (SIN flecha al final para evitar atravesar)
        ax.plot([start_x, end_x], [start_y, end_y], 
               color=color, linewidth=line_width, alpha=alpha,
               solid_capstyle='round', zorder=1)
        
        # Dibujar flecha PEQUEÑA que se SUPERPONE
        _draw_small_superposed_arrow(ax, start_x, start_y, end_x, end_y, 
                                   color, line_width, alpha)

def _get_actual_node_radius(total_passes: int) -> float:
    """
    Calcula el radio REAL del nodo basado en el scatter size.
    DEBE coincidir EXACTAMENTE con lo que se ve visualmente.
    """
    node_size = _calculate_node_size(total_passes)
    # Conversión EXACTA - aumentado para que la línea salga del BORDE EXTREMO
    return np.sqrt(node_size / np.pi) * 0.105  # Factor aumentado más para el extremo exacto

def _calculate_corrected_points(x1: float, y1: float, x2: float, y2: float,
                              r1: float, r2: float, pass_count: int) -> Tuple[float, float, float, float]:
    """
    Calcula puntos CORREGIDOS:
    - INICIO: EXACTAMENTE en el borde del nodo fuente
    - FINAL: LEJOS del nodo destino para no tapar el nombre
    """
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
    
    # PUNTO DE INICIO: EXACTAMENTE en el borde del nodo fuente
    start_x = x1 + r1 * ux + perp_x * offset
    start_y = y1 + r1 * uy + perp_y * offset
    
    # PUNTO FINAL: LEJOS del nodo para no tapar nombre
    # Margen = radio del nodo + espacio extra para nombre
    name_margin = r2 + CONNECTION_CONFIG['name_margin']
    end_x = x2 - name_margin * ux + perp_x * offset
    end_y = y2 - name_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def _draw_small_superposed_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                               color: str, line_width: float, alpha: float):
    """
    Dibuja flecha que TERMINA EXACTAMENTE donde termina la línea.
    NO sobresale línea al final.
    """
    # Vector dirección
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    # Vector unitario
    ux, uy = dx / length, dy / length
    
    # Flecha 1 puntito más grande
    arrow_length = CONNECTION_CONFIG['arrow_length'] * 1.3 * max(1.0, line_width / 5)
    arrow_width = CONNECTION_CONFIG['arrow_width'] * 1.3 * max(1.0, line_width / 6)
    

    push_forward = 1.5  # Ajusta este valor
    arrow_tip_x = end_x + push_forward * ux
    arrow_tip_y = end_y + push_forward * uy
    
    # Base de la flecha - retrocede EXACTAMENTE la longitud de la flecha
    back_x = arrow_tip_x - arrow_length * ux
    back_y = arrow_tip_y - arrow_length * uy
    
    # Puntos laterales
    left_x = back_x - arrow_width * (-uy)
    left_y = back_y - arrow_width * ux
    right_x = back_x + arrow_width * (-uy)
    right_y = back_y + arrow_width * ux
    
    # Dibujar triángulo que TAPA EXACTAMENTE el final de la línea
    triangle = patches.Polygon([(arrow_tip_x, arrow_tip_y), (left_x, left_y), (right_x, right_y)],
                              closed=True, facecolor=color, edgecolor=color,
                              alpha=1.0, linewidth=0, zorder=25)
    ax.add_patch(triangle)

def _calculate_line_width(pass_count: int) -> float:
    """Calcula grosor de línea."""
    if pass_count < 5: return 0.5
    elif pass_count < 10: return 2.5
    elif pass_count < 15: return 5.0
    elif pass_count < 25: return 7.5
    else: return 10.0

# ====================================================================
# DIBUJO DE JUGADORES (SIN CAMBIOS)
# ====================================================================

def _draw_players(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        node_size = _calculate_node_size(player['total_passes'])
        
        ax.scatter(x, y, s=node_size, 
                  c=color, alpha=0.6,
                  edgecolors=color, linewidth=4,
                  zorder=10)

def _calculate_node_size(total_passes: int) -> float:
    """Calcula tamaño de nodo con categorías bien diferenciadas."""
    if total_passes <= 10:
        return 1000    # Pequeño
    elif total_passes <= 25:
        return 2200    # Mediano
    elif total_passes <= 50:
        return 3800    # Grande
    else:
        return 5600    # Muy grande

def _draw_labels(ax, players_df: pd.DataFrame):
    """Dibuja nombres de jugadores."""
    for _, player in players_df.iterrows():
        name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        # Acortar nombre si es necesario
        display_name = name
        if len(name) > 16:
            parts = name.split()
            if len(parts) >= 2:
                display_name = f"{parts[0]} {parts[-1]}"
        
        # Texto con outline
        ax.text(x, y, display_name,
               ha='center', va='center',
               color='white', fontsize=16, fontweight='bold',
               family='Arial',
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=15)

# ====================================================================
# LEYENDA CORREGIDA
# ====================================================================

def _draw_legend_corrected(ax, team_data: Dict[str, pd.DataFrame], team_name: str):
    """Leyenda FINAL: título centrado y círculos completos."""
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    legend_color = colors['primary']
    
    # POSICIÓN con espacio suficiente
    legend_y = -10
    
    # Estadísticas centrales
    total_passes = len(team_data['passes'])
    ax.text(52.5, legend_y + 6, f"Pases: {total_passes}", 
           ha='center', va='center', fontsize=18, fontweight='bold', 
           color=legend_color, family='Arial')
    
    # TÍTULO ÚNICO CENTRADO debajo de "Pases"
    ax.text(52.5, legend_y + 1, "Nº Pases", 
           ha='center', va='center', fontsize=14, fontweight='bold', 
           color=legend_color, family='Arial')
    
    # Escalas SIN títulos individuales
    _draw_nodes_no_title(ax, 20, legend_y, legend_color)
    _draw_lines_no_title(ax, 85, legend_y, legend_color)

def _draw_nodes_no_title(ax, x: float, y: float, color: str):
    """Nodos SIN título individual y que NO se corten."""
    pass_examples = [8, 20, 40, 70]
    node_sizes = [_calculate_node_size(p) for p in pass_examples]
    positions = [x - 15, x - 5, x + 5, x + 15]
    
    # CÍRCULOS BIEN ARRIBA para que NO se corten
    circle_y = y + 5.3
    
    for passes, size, pos in zip(pass_examples, node_sizes, positions):
        display_size = size * 0.6  # Tamaño apropiado
        ax.scatter(pos, circle_y, s=display_size, c=color, alpha=0.8, 
                  edgecolors=color, linewidth=2, zorder=10)
        
        # NÚMEROS BIEN ABAJO separados de los círculos
        if passes <= 10:
            label = "≤10"
        elif passes <= 25:
            label = "≤25" 
        elif passes <= 50:
            label = "≤50"
        else:
            label = "50+"
            
        ax.text(pos, y + 0.5, label, ha='center', va='center',
               fontsize=11, fontweight='bold', color=color, family='Arial')

def _draw_lines_no_title(ax, x: float, y: float, color: str):
    """Líneas SIN título individual."""
    pass_counts = [5, 10, 15, 25]
    line_widths = [_calculate_line_width(p) for p in pass_counts]
    positions = [x - 15, x - 5, x + 5, x + 15]
    
    # LÍNEAS BIEN ARRIBA
    line_y = y + 2.5
    
    for passes, width, pos in zip(pass_counts, line_widths, positions):
        ax.plot([pos - 2.5, pos + 2.5], [line_y, line_y], color=color, 
               linewidth=width, alpha=0.8, solid_capstyle='round')
        
        # NÚMEROS BIEN ABAJO separados
        label = f"{passes}" if passes < 25 else f"{passes}+"
        ax.text(pos, y + 0.5, label, ha='center', va='center',
               fontsize=10, fontweight='bold', color=color, family='Arial')

# Y CAMBIAR EN create_pass_network():
# ax.set_ylim(-18, 68)  POR:
# ax.set_ylim(-16, 68)

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