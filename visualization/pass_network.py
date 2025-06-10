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
    'min_passes': 4,  # Aumentado para mostrar solo conexiones significativas
    'alpha': 0.8,
    'offset': 1.5,  # Separación entre líneas bidireccionales
    'arrow_length': 1.5,  # Longitud de la punta de flecha (MUCHO MÁS PEQUEÑA)
    'arrow_width': 1.0   # Ancho de la punta de flecha (MUCHO MÁS PEQUEÑA)
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
    
    # Añadir leyenda en la parte inferior
    _draw_legend(ax, team_data, team_name)
    
    # Sin título principal
    
    # Configurar ejes
    ax.set_xlim(-5, 110)
    ax.set_ylim(-12, 73)  # MÁS espacio abajo para la leyenda VISIBLE
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
    """Dibuja áreas de penalti y semicírculos CORRECTAMENTE."""
    color = FIELD_CONFIG['line_color']
    lw = FIELD_CONFIG['line_width']
    
    # Dimensiones áreas
    penalty_length = 16.5
    penalty_width = 40.32
    small_length = 5.5
    small_width = 18.32
    
    penalty_y = (width - penalty_width) / 2
    small_y = (width - small_width) / 2
    
    # Áreas grandes - solo las líneas que NO están en el borde del campo
    # Área izquierda
    ax.plot([penalty_length, penalty_length], [penalty_y, penalty_y + penalty_width], 
           color=color, linewidth=lw)  # Línea vertical derecha del área izquierda
    ax.plot([0, penalty_length], [penalty_y, penalty_y], 
           color=color, linewidth=lw)  # Línea horizontal inferior
    ax.plot([0, penalty_length], [penalty_y + penalty_width, penalty_y + penalty_width], 
           color=color, linewidth=lw)  # Línea horizontal superior
    
    # Área derecha  
    ax.plot([length - penalty_length, length - penalty_length], [penalty_y, penalty_y + penalty_width], 
           color=color, linewidth=lw)  # Línea vertical izquierda del área derecha
    ax.plot([length - penalty_length, length], [penalty_y, penalty_y], 
           color=color, linewidth=lw)  # Línea horizontal inferior
    ax.plot([length - penalty_length, length], [penalty_y + penalty_width, penalty_y + penalty_width], 
           color=color, linewidth=lw)  # Línea horizontal superior
    
    # Áreas pequeñas (6 yards) - solo las líneas que NO están en el borde
    # Área pequeña izquierda
    ax.plot([small_length, small_length], [small_y, small_y + small_width], 
           color=color, linewidth=lw)  # Línea vertical derecha
    ax.plot([0, small_length], [small_y, small_y], 
           color=color, linewidth=lw)  # Línea horizontal inferior
    ax.plot([0, small_length], [small_y + small_width, small_y + small_width], 
           color=color, linewidth=lw)  # Línea horizontal superior
    
    # Área pequeña derecha
    ax.plot([length - small_length, length - small_length], [small_y, small_y + small_width], 
           color=color, linewidth=lw)  # Línea vertical izquierda
    ax.plot([length - small_length, length], [small_y, small_y], 
           color=color, linewidth=lw)  # Línea horizontal inferior
    ax.plot([length - small_length, length], [small_y + small_width, small_y + small_width], 
           color=color, linewidth=lw)  # Línea horizontal superior
    
    # Semicírculos y puntos de penalti
    penalty_spot_distance = 11.0
    semicircle_radius = 9.15
    
    # Semicírculo izquierdo (SOLO la parte que sobresale del área)
    semicircle_l = patches.Arc((penalty_spot_distance, width/2), 
                              semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=-90, theta2=90, 
                              linewidth=lw, edgecolor=color, fill=False)
    ax.add_patch(semicircle_l)
    ax.plot(penalty_spot_distance, width/2, 'o', color=color, markersize=4)
    
    # Semicírculo derecho (SOLO la parte que sobresale del área)
    semicircle_r = patches.Arc((length - penalty_spot_distance, width/2), 
                              semicircle_radius*2, semicircle_radius*2,
                              angle=0, theta1=90, theta2=270, 
                              linewidth=lw, edgecolor=color, fill=False)
    ax.add_patch(semicircle_r)
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
# DIBUJO DE LA RED DE PASES - VERSIÓN MEJORADA
# ====================================================================

def _draw_bidirectional_connections(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Dibuja conexiones bidireccionales con flechas desde y hacia los bordes EXACTOS de los nodos."""
    if connections_df.empty:
        return
    
    # Dibujar solo conexiones significativas
    for _, conn in connections_df.iterrows():
        if conn['pass_count'] < CONNECTION_CONFIG['min_passes']:
            continue
            
        source_player = conn['source']
        target_player = conn['target']
        
        # Obtener posiciones y tamaños de los jugadores
        source_pos = players_df[players_df['player'] == source_player]
        target_pos = players_df[players_df['player'] == target_player]
        
        if source_pos.empty or target_pos.empty:
            continue
        
        x1, y1 = source_pos.iloc[0]['avg_x'], source_pos.iloc[0]['avg_y']
        x2, y2 = target_pos.iloc[0]['avg_x'], target_pos.iloc[0]['avg_y']
        
        # Calcular radios EXACTOS de los nodos (del tamaño visual real)
        source_radius = np.sqrt(source_pos.iloc[0]['node_size'] / np.pi) / 20  # Ajuste más preciso
        target_radius = np.sqrt(target_pos.iloc[0]['node_size'] / np.pi) / 20
        
        # Calcular línea desde borde EXACTO a borde EXACTO con offset
        arrow_data = _calculate_arrow_from_exact_edge_to_exact_edge(x1, y1, x2, y2, source_radius, target_radius, conn['pass_count'])
        
        # Determinar grosor y opacidad basado en número de pases
        line_width = _calculate_enhanced_line_width(conn['pass_count'])
        alpha = min(0.4 + (conn['pass_count'] / 25) * 0.5, 0.9)
        
        # Dibujar línea principal
        ax.plot([arrow_data['start_x'], arrow_data['end_x']], 
               [arrow_data['start_y'], arrow_data['end_y']], 
               color=color, 
               linewidth=line_width,
               alpha=alpha,
               solid_capstyle='round',
               zorder=1)
        
        # Dibujar punta de flecha MINÚSCULA
        _draw_arrow_head(ax, arrow_data, color, line_width, alpha)


def _calculate_arrow_from_exact_edge_to_exact_edge(x1: float, y1: float, x2: float, y2: float, 
                                                 r1: float, r2: float, pass_count: int) -> Dict:
    """Calcula coordenadas de flecha desde borde EXACTO de un nodo hasta borde EXACTO del otro."""
    # Vector dirección
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return {'start_x': x1, 'start_y': y1, 'end_x': x2, 'end_y': y2, 'dx': 0, 'dy': 0}
    
    # Vector unitario
    ux = dx / length
    uy = dy / length
    
    # Vector perpendicular para offset
    perp_x = -uy
    perp_y = ux
    
    # Offset basado en número de pases
    offset = CONNECTION_CONFIG['offset'] * (1 + pass_count / 40)
    
    # Punto de inicio: EXACTAMENTE en el borde del nodo origen + offset
    start_x = x1 + r1 * ux + perp_x * offset
    start_y = y1 + r1 * uy + perp_y * offset
    
    # Punto final: EXACTAMENTE en el borde del nodo destino + offset  
    end_x = x2 - r2 * ux + perp_x * offset
    end_y = y2 - r2 * uy + perp_y * offset
    
    return {
        'start_x': start_x, 'start_y': start_y,
        'end_x': end_x, 'end_y': end_y,
        'dx': ux, 'dy': uy
    }


def _draw_arrow_head(ax, arrow_data: Dict, color: str, line_width: float, alpha: float):
    """Dibuja la punta de flecha MINÚSCULA al final de la línea."""
    # Coordenadas de la punta
    tip_x = arrow_data['end_x']
    tip_y = arrow_data['end_y']
    
    # Vector dirección
    dx = arrow_data['dx']
    dy = arrow_data['dy']
    
    # Tamaño de la flecha MÍNIMO
    arrow_length = CONNECTION_CONFIG['arrow_length']  # Sin multiplicar por line_width
    arrow_width = CONNECTION_CONFIG['arrow_width']    # Sin multiplicar por line_width
    
    # Puntos de la flecha
    back_x = tip_x - arrow_length * dx
    back_y = tip_y - arrow_length * dy
    
    left_x = back_x - arrow_width * (-dy)
    left_y = back_y - arrow_width * dx
    
    right_x = back_x + arrow_width * (-dy)
    right_y = back_y + arrow_width * dx
    
    # Dibujar triángulo de flecha MINÚSCULO
    triangle = patches.Polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)],
                              closed=True, facecolor=color, edgecolor=color,
                              alpha=alpha, linewidth=0, zorder=2)


    ax.add_patch(triangle)


def _calculate_enhanced_line_width(pass_count: int) -> float:
    """Calcula grosor de línea con mayor diferenciación."""
    if pass_count < 4: return 0.5
    elif pass_count < 8: return 2.0
    elif pass_count < 15: return 4.5
    elif pass_count < 25: return 7.0
    else: return 10.0


def _draw_players_enhanced(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores con mayor diferenciación de tamaños."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        
        # Tamaño escalado más agresivamente
        base_size = _calculate_enhanced_node_size(player['total_passes'])
        
        # Círculo con relleno semitransparente y borde grueso
        ax.scatter(x, y, s=base_size, 
                  c=color, alpha=0.6,  # Relleno semitransparente
                  edgecolors=color, linewidth=5,  # Borde más grueso
                  zorder=10)


def _calculate_enhanced_node_size(total_passes: int) -> float:
    """Calcula tamaño de nodo con 4 TAMAÑOS MUY DIFERENCIADOS."""
    # 4 categorías muy diferenciadas
    if total_passes <= 5:
        return 800    # Categoría 1: Muy pocos pases
    elif total_passes <= 15:
        return 1800   # Categoría 2: Pocos pases  
    elif total_passes <= 35:
        return 3200   # Categoría 3: Bastantes pases
    else:
        return 5500   # Categoría 4: Muchos pases


def _draw_labels_enhanced(ax, players_df: pd.DataFrame):
    """Dibuja nombres completos de jugadores dentro de los nodos con letra más grande."""
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
               color='white', fontsize=14, fontweight='bold',  # Fuente más grande
               family='Arial',  # Fuente similar a Gotham
               path_effects=[
                   path_effects.Stroke(linewidth=2.5, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=11)


def _draw_legend(ax, team_data: Dict[str, pd.DataFrame], team_name: str):
    """Dibuja leyenda VISIBLE con el mismo color que los nodos."""
    # Obtener colores del equipo
    colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    legend_color = colors['primary']  # Mismo color que los nodos
    
    # Posición de la leyenda MÁS BAJA para ser VISIBLE
    legend_y = -9
    
    # Estadísticas básicas
    total_passes = len(team_data['passes'])
    connections_count = len(team_data['connections']) if not team_data['connections'].empty else 0
    
    # Texto principal con estadísticas VISIBLE y del color de los nodos
    stats_text = f"Pases: {total_passes} | Conexiones: {connections_count}"
    ax.text(52.5, legend_y, stats_text, ha='center', va='center',
           fontsize=20, fontweight='bold', color=legend_color, family='Arial')
    
    # Escala de nodos (lado izquierdo) 
    node_legend_x = 15
    _draw_node_scale_legend(ax, node_legend_x, legend_y - 4, legend_color)
    
    # Escala de conexiones (lado derecho)  
    connection_legend_x = 85
    _draw_connection_scale_legend(ax, connection_legend_x, legend_y - 4, legend_color)


def _draw_node_scale_legend(ax, x: float, y: float, color: str):
    """Dibuja escala de tamaños de nodos con 4 tamaños diferenciados."""
    # 4 tamaños MUY DIFERENCIADOS
    sizes = [5, 15, 35, 50]  # Ejemplos de pases
    # Tamaños de leyenda proporcionales a los del campo
    circle_sizes = [400, 900, 1600, 2500]  # 4 tamaños muy diferenciados
    positions = [x - 18, x - 6, x + 6, x + 18]
    
    for i, (size, circle_size, pos) in enumerate(zip(sizes, circle_sizes, positions)):
        ax.scatter(pos, y, s=circle_size, c=color, alpha=0.6, 
                  edgecolors=color, linewidth=3, zorder=10)
        
        # Etiquetas con el mismo color
        label = f"≤{size}" if i < 3 else f"{size}+"
        ax.text(pos, y - 2.5, label, ha='center', va='top', 
               fontsize=12, fontweight='bold', color=color, family='Arial')
    
    # Etiqueta de la escala con el mismo color
    ax.text(x, y + 2.5, "pases", ha='center', va='bottom',
           fontsize=14, fontweight='bold', color=color, family='Arial')


def _draw_connection_scale_legend(ax, x: float, y: float, color: str):
    """Dibuja escala de grosores de conexiones con el color de los nodos."""
    # Líneas de ejemplo
    pass_counts = [4, 8, 15, 25]
    line_widths = [_calculate_enhanced_line_width(p) for p in pass_counts]
    positions = [x - 18, x - 6, x + 6, x + 18]
    
    for i, (passes, width, pos) in enumerate(zip(pass_counts, line_widths, positions)):
        # Línea con el color de los nodos
        ax.plot([pos - 2, pos + 2], [y, y], color=color, 
               linewidth=width, alpha=0.8, solid_capstyle='round')
        
        # Etiquetas con el mismo color
        label = f"{passes}" if passes < 25 else f"{passes}+"
        ax.text(pos, y - 2.5, label, ha='center', va='top',
               fontsize=12, fontweight='bold', color=color, family='Arial')
    
    # Etiqueta de la escala con el mismo color
    ax.text(x, y + 2.5, "pases", ha='center', va='bottom',
           fontsize=14, fontweight='bold', color=color, family='Arial')


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


# ====================================================================
# FUNCIONES PARA USAR CON CSV EXISTENTES
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


def quick_barcelona_from_csv(csv_dir: str = "visualization/data") -> plt.Figure:
    """Visualización rápida de Barcelona desde CSV."""
    
    passes_path = os.path.join(csv_dir, "match_1821769_passes.csv")
    players_path = os.path.join(csv_dir, "match_1821769_players.csv") 
    connections_path = os.path.join(csv_dir, "match_1821769_connections.csv")
    
    try:
        match_data = load_from_csv_files(passes_path, players_path, connections_path)
        fig = create_pass_network(match_data, "Barcelona")
        plt.show()
        return fig
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return None


def quick_athletic_from_csv(csv_dir: str = "visualization/data") -> plt.Figure:
    """Visualización rápida de Athletic desde CSV."""
    
    passes_path = os.path.join(csv_dir, "match_1821769_passes.csv")
    players_path = os.path.join(csv_dir, "match_1821769_players.csv") 
    connections_path = os.path.join(csv_dir, "match_1821769_connections.csv")
    
    try:
        match_data = load_from_csv_files(passes_path, players_path, connections_path)
        fig = create_pass_network(match_data, "Athletic Club")
        plt.show()
        return fig
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return None
    else: return 10.0


def _draw_players_enhanced(ax, players_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores con mayor diferenciación de tamaños."""
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        
        # Tamaño escalado más agresivamente
        base_size = _calculate_enhanced_node_size(player['total_passes'])
        
        # Círculo con relleno semitransparente y borde grueso
        ax.scatter(x, y, s=base_size, 
                  c=color, alpha=0.6,  # Relleno semitransparente
                  edgecolors=color, linewidth=5,  # Borde más grueso
                  zorder=10)


def _calculate_enhanced_node_size(total_passes: int) -> float:
    """Calcula tamaño de nodo con mayor diferenciación según escala de referencia."""
    # Escala de referencia: 1 pass = mínimo, 50+ passes = máximo
    min_size = 800   # Tamaño para 1 pase
    max_size = 4000  # Tamaño para 50+ pases
    
    if total_passes <= 1:
        return min_size
    elif total_passes >= 50:
        return max_size
    else:
        # Escalado progresivo
        ratio = (total_passes - 1) / (50 - 1)
        return min_size + (ratio * (max_size - min_size))


def _draw_labels_enhanced(ax, players_df: pd.DataFrame):
    """Dibuja nombres completos de jugadores dentro de los nodos con letra más grande."""
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
               color='white', fontsize=14, fontweight='bold',  # Fuente más grande
               family='Arial',  # Fuente similar a Gotham
               path_effects=[
                   path_effects.Stroke(linewidth=2.5, foreground='black'),
                   path_effects.Normal()
               ],
               zorder=11)


def _draw_legend(ax, team_data: Dict[str, pd.DataFrame], team_name: str):
    """Dibuja leyenda en la parte inferior con estadísticas y escalas."""
    # Posición de la leyenda
    legend_y = -8
    
    # Estadísticas básicas
    total_passes = len(team_data['passes'])
    connections_count = len(team_data['connections']) if not team_data['connections'].empty else 0
    
    # Texto principal con estadísticas
    stats_text = f"Pases: {total_passes} | Conexiones: {connections_count}"
    ax.text(52.5, legend_y, stats_text, ha='center', va='center',
           fontsize=16, fontweight='bold', color='#1A1A1A', family='Arial')
    
    # Escala de nodos (lado izquierdo)
    node_legend_x = 15
    _draw_node_scale_legend(ax, node_legend_x, legend_y - 2)
    
    # Escala de conexiones (lado derecho)  
    connection_legend_x = 85
    _draw_connection_scale_legend(ax, connection_legend_x, legend_y - 2)


def _draw_node_scale_legend(ax, x: float, y: float):
    """Dibuja escala de tamaños de nodos."""
    # Círculos de ejemplo
    sizes = [1, 15, 30, 50]  # Ejemplos de pases
    circle_sizes = [_calculate_enhanced_node_size(s) for s in sizes]
    positions = [x - 12, x - 4, x + 4, x + 12]
    
    for i, (size, circle_size, pos) in enumerate(zip(sizes, circle_sizes, positions)):
        ax.scatter(pos, y, s=circle_size, c='#666666', alpha=0.6, 
                  edgecolors='#666666', linewidth=3, zorder=10)
        
        # Etiquetas
        label = f"{size}" if size < 50 else "50+"
        ax.text(pos, y - 1.5, label, ha='center', va='top', 
               fontsize=10, color='#333333', family='Arial')
    
    # Etiqueta de la escala
    ax.text(x, y + 1.5, "pases", ha='center', va='bottom',
           fontsize=12, fontweight='bold', color='#333333', family='Arial')


def _draw_connection_scale_legend(ax, x: float, y: float):
    """Dibuja escala de grosores de conexiones."""
    # Líneas de ejemplo
    pass_counts = [4, 8, 15, 25]
    line_widths = [_calculate_enhanced_line_width(p) for p in pass_counts]
    positions = [x - 12, x - 4, x + 4, x + 12]
    
    for i, (passes, width, pos) in enumerate(zip(pass_counts, line_widths, positions)):
        # Línea
        ax.plot([pos - 1, pos + 1], [y, y], color='#666666', 
               linewidth=width, alpha=0.8, solid_capstyle='round')
        
        # Etiquetas
        label = f"{passes}" if passes < 25 else "25+"
        ax.text(pos, y - 1.5, label, ha='center', va='top',
               fontsize=10, color='#333333', family='Arial')
    
    # Etiqueta de la escala
    ax.text(x, y + 1.5, "pases", ha='center', va='bottom',
           fontsize=12, fontweight='bold', color='#333333', family='Arial')
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