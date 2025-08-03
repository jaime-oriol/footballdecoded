import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import VerticalPitch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch, Circle, ArrowStyle
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

def calculate_node_size(total_passes: int, max_passes: int, threshold: int = 20) -> float:
    """Calculate individual node size with very gradual scaling."""
    min_size = 5   
    max_size = 30  
    
    if total_passes <= 5:
        return min_size
    if total_passes >= 100:
        return max_size
    
    size_range = max_size - min_size  
    pass_range = 100 - 5             
    increment_per_pass = size_range / pass_range  
    
    return min_size + (total_passes - 5) * increment_per_pass

def calculate_line_width(pass_count: int, min_connections: int, max_connections: int, min_required: int = 5) -> float:
    """Calculate line width with smooth scaling."""
    if pass_count < min_required:
        return 0.0
    
    if max_connections == min_connections:
        return 2.0
    
    normalized = (pass_count - min_connections) / (max_connections - min_connections)
    curved = normalized ** 0.6
    return 0.5 + curved * (4.5 - 0.5)

def get_node_radius(marker_size: float) -> float:
    """Convert marker size to radius using map.py formula adapted to pass_network scale."""
    # En pass_network: scatter usa s=marker_size**2, asi que el area visual es marker_size^2
    # Aplicamos la formula de map.py pero adaptada a nuestra escala
    visual_area = marker_size**2  # Area real en scatter
    return np.sqrt(visual_area / np.pi) * 0.105  # Formula exacta de map.py

def calculate_connection_points(x1: float, y1: float, x2: float, y2: float, 
                              r1: float, r2: float, pass_count: int) -> tuple:
    """Calculate connection points using EXACT map.py logic."""
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    ux, uy = dx / length, dy / length
    combined_radius = r1 + r2
    min_safe_distance = combined_radius * 1.1
    
    # Usar el mismo base_offset que map.py (inferido de los resultados visuales)
    base_offset = 0.8  # Valor típico usado en map.py
    
    if length < min_safe_distance:
        perp_x, perp_y = -uy, ux
        offset = base_offset * (1 + pass_count / 50)
        
        start_x = x1 + r1 * ux * 1.1 + perp_x * offset
        start_y = y1 + r1 * uy * 1.1 + perp_y * offset
        
        reduced_margin = r2 + 0.5
        end_x = x2 - reduced_margin * ux + perp_x * offset
        end_y = y2 - reduced_margin * uy + perp_y * offset
        
        if np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2) < 1.0:
            start_x = x1 + r1 * ux + perp_x * offset
            start_y = y1 + r1 * uy + perp_y * offset
            end_x = x2 - 1.5 * ux + perp_x * offset 
            end_y = y2 - 1.5 * uy + perp_y * offset  
            
    else:
        perp_x, perp_y = -uy, ux
        offset = base_offset * (1 + pass_count / 50)
        
        start_x = x1 + r1 * ux + perp_x * offset
        start_y = y1 + r1 * uy + perp_y * offset
        
        name_margin = r2 + 1
        end_x = x2 - name_margin * ux + perp_x * offset
        end_y = y2 - name_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def draw_connection_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                         color: str, line_width: float):
    """Draw directional arrow using EXACT map.py logic."""
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    
    size = max(0.6, line_width * 0.25)
    extension = size * 0.125
    tip_x = end_x + extension * ux
    tip_y = end_y + extension * uy
    
    origin_x = tip_x - size * 1.0 * ux + size * 0.7 * px
    origin_y = tip_y - size * 1.0 * uy + size * 0.7 * py
    
    ax.plot([tip_x, origin_x], [tip_y, origin_y], 
           color=color, linewidth=max(1.8, line_width * 0.7), 
           alpha=1.0, solid_capstyle='round', zorder=100)

def optimize_name(full_name: str) -> str:
    """Use first initial + surname, including particles like 'de', 'van', etc."""
    if pd.isna(full_name) or not full_name.strip():
        return "Unknown"
    
    full_name = full_name.strip()
    name_parts = full_name.split()
    
    if len(name_parts) == 1:
        return name_parts[0]
    
    first_initial = name_parts[0][0].upper()
    particles = ['de', 'del', 'da', 'dos', 'van', 'von', 'le', 'la', 'du', 'di', 'el']
    
    surname_parts = [name_parts[-1]]
    
    for i in range(len(name_parts) - 2, 0, -1):
        if name_parts[i].lower() in particles:
            surname_parts.insert(0, name_parts[i])
        else:
            break
    
    surname = ' '.join(surname_parts)
    
    return f"{first_initial}. {surname}"

def plot_pass_network(network_csv_path, info_csv_path, aggregates_csv_path,
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(6, 6), save_path=None):
    
    # Leer datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    # Extraer metadata
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Filtrar solo jugadores del aggregates
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # TRANSFORMACIÓN CORRECTA: Para vertical, Y del CSV -> X del pitch, X del CSV -> Y del pitch
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Límites para normalización
    min_player_value = 0.01
    max_player_value = 0.36
    min_passes = 5

    def change_range(value, old_range, new_range):
        new_value = ((value-old_range[0]) / (old_range[1]-old_range[0])) * (new_range[1]-new_range[0]) + new_range[0]
        if new_value >= new_range[1]:
            return new_range[1]
        elif new_value <= new_range[0]:
            return new_range[0]
        else:
            return new_value
    
    # Setup figura
    plt.style.use('fivethirtyeight')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400)
    
    teams = [home_team, away_team]
    
    # Normalización global de xThreat
    xthreat_norm = Normalize(vmin=min_player_value, vmax=max_player_value)
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        '#E15A82', '#EEA934', '#F1CA56', '#DCED69', '#7FF7A8', '#5AE1AC', '#11C0A1'
    ])
    
    for i, team in enumerate(teams):
        # Dibujar pitch
        pitch = VerticalPitch(pitch_type='opta', line_color='#7c7c7c', goal_type='box',
                             linewidth=0.5, pad_bottom=3)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        # Líneas punteadas
        ax[i].plot([21, 21], [ax[i].get_ylim()[0]+19, ax[i].get_ylim()[1]-19], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([78.8, 78.8], [ax[i].get_ylim()[0]+19, ax[i].get_ylim()[1]-19], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([36.8, 36.8], [ax[i].get_ylim()[0]+8.5, ax[i].get_ylim()[1]-8.5], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([63.2, 63.2], [ax[i].get_ylim()[0]+8.5, ax[i].get_ylim()[1]-8.5], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        
        ax[i].plot([ax[i].get_xlim()[0]-4, ax[i].get_xlim()[1]+4], [83, 83], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([ax[i].get_xlim()[0]-4, ax[i].get_xlim()[1]+4], [67, 67], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([ax[i].get_xlim()[0]-4, ax[i].get_xlim()[1]+4], [17, 17], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        ax[i].plot([ax[i].get_xlim()[0]-4, ax[i].get_xlim()[1]+4], [33, 33], 
                   ls=':', dashes=(1, 3), color='gray', lw=0.4)
        
        # Flecha Attack
        head_length = 0.3
        head_width = 0.05
        ax[i].annotate(xy=(102, 58), xytext=(102, 43), zorder=2, text='',
                      ha='center', arrowprops=dict(arrowstyle=f'->, head_length={head_length}, head_width={head_width}',
                      color='#7c7c7c', lw=0.5))
        ax[i].annotate(xy=(104, 48), zorder=2, text='Attack', ha='center',
                      color='#7c7c7c', rotation=90, size=5)
        
        # Texto minutos
        ax[i].annotate(xy=(50, -5), zorder=2, text='Passes from minutes 1 to 90',
                      ha='center', color='#7c7c7c', size=6)
        
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = player_aggregates[player_aggregates['team'] == team].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        # USAR DIRECTAMENTE passes_completed del CSV aggregates
        max_passes_team = team_player_data['passes_completed'].max()
        
        # Preparar datos de jugadores usando aggregates CSV
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            # Buscar en aggregates CSV
            player_data = team_player_data[team_player_data['entity_name'] == player_name]
            
            if player_data.empty:
                continue
                
            # USAR passes_completed directamente del CSV
            num_passes = int(player_data.iloc[0]['passes_completed'])
            
            # Calcular tamaño y radio usando lógica exacta de map.py
            marker_size = calculate_node_size(num_passes, max_passes_team)
            node_radius = get_node_radius(marker_size)  # Formula exacta de map.py
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': num_passes,
                'xthreat': player['avg_xthreat']
            }
        
        # SISTEMA AVANZADO: Dibujar conexiones con gradiente usando lógica map.py
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        if not valid_connections.empty:
            # Calcular anchos de línea dinámicos
            min_conn = valid_connections['connection_strength'].min()
            max_conn = valid_connections['connection_strength'].max()
            
            for _, conn in valid_connections.iterrows():
                source_name = conn['source_player']
                target_name = conn['target_player']
                
                if source_name not in player_stats or target_name not in player_stats:
                    continue
                
                source = player_stats[source_name]
                target = player_stats[target_name]
                
                num_passes = conn['connection_strength']
                pass_value = conn.get('avg_xthreat', 0)
                
                # USAR LÓGICA EXACTA DE MAP.PY para calcular puntos
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(xthreat_norm(pass_value))
                
                # Crear gradiente con LineCollection EXACTO como map.py
                num_points = 75  # Mismo valor que map.py
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Usar mismo rango de alphas que map.py
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)  # Mismo zorder que map.py
                ax[i].add_collection(lc)
                
                # Dibujar flecha con lógica EXACTA de map.py
                draw_connection_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        # SISTEMA AVANZADO: Dibujar nodos con transparencia y tamaño dinámico
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat']
            
            node_color = node_cmap(xthreat_norm(pass_value))
            
            # Nodo principal con transparencia
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.8,
                         edgecolors=node_color, linewidth=2, zorder=5)
            
            # Borde blanco sutil
            ax[i].scatter(x, y, s=(marker_size+1)**2, color='white', 
                         alpha=0.3, zorder=4)
            
            # Nombre centrado optimizado
            display_name = optimize_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Títulos
    font = 'serif'
    fig.text(x=0.5, y=.90, s=f"Passing network for {home_team} vs {away_team}",
            weight='bold', va="bottom", ha="center", fontsize=10, font=font)
    
    fig.text(x=0.25, y=.855, s=home_team, weight='bold', va="bottom", ha="center",
            fontsize=8, font=font)
    fig.text(x=0.73, y=.855, s=away_team, weight='bold', va="bottom", ha="center",
            fontsize=8, font=font)
    
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=6, font=font)
    
    # Créditos
    fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
            weight='bold', fontsize=12, font=font, color='black')
    fig.text(x=0.1, y=-0.0, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='black')
    
    # Textos de leyenda
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font)
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font)
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font)
    fig.text(x=0.84, y=.14, s="Player pass value (xT)", va="bottom", ha="center",
            fontsize=6, font=font)
    
    fig.text(x=0.13, y=0.07, s="5 to 16+", va="bottom", ha="center",
            fontsize=5, font=font, color='black')
    fig.text(x=0.37, y=0.07, s="0 to 0.09+", va="bottom", ha="center",
            fontsize=5, font=font, color='black')
    fig.text(x=0.61, y=0.07, s="1 to 88+", va="bottom", ha="center",
            fontsize=5, font=font, color='black')
    fig.text(x=0.84, y=0.07, s="0.01 to 0.36+", va="bottom", ha="center",
            fontsize=5, font=font, color='black')
    
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font)
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font)
    
    # LEYENDA VISUAL
    x0 = 225
    y0 = 250
    dx = 60
    dy = 120
    shift_x = 70
    
    x1 = 740
    x2 = 1400
    y2 = 310
    shift_x2 = 70
    radius = 20
    
    x3 = 1840
    shift_x3 = 100
    
    x4 = 960
    y4 = 100
    
    style = ArrowStyle('->', head_length=5, head_width=3)
    
    # Flechas de grosor
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='black')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='black')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='black')
    
    # Flechas de colores
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Círculos de tamaño
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='black', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='black', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='black', fill=False)
    
    # Círculos de colores
    circle4 = Circle(xy=(x3, y2), radius=radius*2, color=colors_legend[0])
    circle5 = Circle(xy=(x3+shift_x3, y2), radius=radius*2, color=colors_legend[1])
    circle6 = Circle(xy=(x3+2*shift_x3, y2), radius=radius*2, color=colors_legend[2])
    circle7 = Circle(xy=(x3+3*shift_x3, y2), radius=radius*2, color=colors_legend[3])
    circle8 = Circle(xy=(x3+4*shift_x3, y2), radius=radius*2, color=colors_legend[4])
    
    # Flecha horizontal
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='black')
    
    # Agregar elementos
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, circle4, circle5, circle6, circle7, circle8, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400)
        print(f"Visualización guardada en: {save_path}")
    
    return fig