import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch, Circle, ArrowStyle
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

def plot_pass_network(network_csv_path, info_csv_path, 
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(16, 20), save_path=None):
    
    # Leer datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    
    # Extraer metadata
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Extraer resultado
    home_goals = int(info_df[(info_df['info_key'] == 'goals') & (info_df['team'] == home_team)]['numeric_value'].iloc[0])
    away_goals = int(info_df[(info_df['info_key'] == 'goals') & (info_df['team'] == away_team)]['numeric_value'].iloc[0])
    
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # Colormap del notebook
    nodes_cmap = LinearSegmentedColormap.from_list("", [
        '#E15A82', '#EEA934', '#F1CA56', '#DCED69', '#7FF7A8', '#5AE1AC', '#11C0A1'
    ])
    
    # Límites del notebook
    min_node_size = 5
    max_node_size = 35
    min_player_count = 1
    max_player_count = 88
    min_player_value = 0.01
    max_player_value = 0.36
    
    min_edge_width = 0.5
    max_edge_width = 5
    min_pair_count = 1
    max_pair_count = 16
    min_pair_value = 0.01
    max_pair_value = 0.09
    min_passes = 5
    
    def change_range(value, old_range, new_range):
        new_value = ((value-old_range[0]) / (old_range[1]-old_range[0])) * (new_range[1]-new_range[0]) + new_range[0]
        if new_value >= new_range[1]:
            return new_range[1]
        elif new_value <= new_range[0]:
            return new_range[0]
        else:
            return new_value
    
    def get_node_radius(node_size):
        return np.sqrt(node_size / np.pi) * 0.105
    
    def calculate_connection_points(x1, y1, x2, y2, r1, r2, pass_count):
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return x1, y1, x2, y2
        
        ux, uy = dx / length, dy / length
        combined_radius = r1 + r2
        min_safe_distance = combined_radius * 1.1
        
        base_offset = 0.3
        perp_x, perp_y = -uy, ux
        offset = base_offset * (1 + pass_count / 50)
        
        if length < min_safe_distance:
            start_x = x1 + r1 * ux * 1.1 + perp_x * offset
            start_y = y1 + r1 * uy * 1.1 + perp_y * offset
            reduced_margin = r2 + 0.5
            end_x = x2 - reduced_margin * ux + perp_x * offset
            end_y = y2 - reduced_margin * uy + perp_y * offset
        else:
            start_x = x1 + r1 * ux + perp_x * offset
            start_y = y1 + r1 * uy + perp_y * offset
            name_margin = r2 + 1
            end_x = x2 - name_margin * ux + perp_x * offset
            end_y = y2 - name_margin * uy + perp_y * offset
        
        return start_x, start_y, end_x, end_y
    
    def draw_connection_arrow(ax, start_x, start_y, end_x, end_y, color, line_width, alpha):
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
    
    # Setup figura con fondo gris
    fig, axes = plt.subplots(2, 1, figsize=figsize, facecolor='#313332')
    fig.patch.set_facecolor('#313332')
    
    teams = [home_team, away_team]
    
    # Normalización global de xThreat
    all_xthreat_values = []
    for team in teams:
        team_positions = positions_df[positions_df['team'] == team]
        if not team_positions.empty:
            all_xthreat_values.extend(team_positions['avg_xthreat'].values)
    
    xthreat_norm = Normalize(vmin=min_player_value, vmax=max_player_value)
    
    # Dibujar cada equipo
    for i, (ax, team) in enumerate(zip(axes, teams)):
        # Crear pitch horizontal
        pitch = Pitch(pitch_type='opta', pitch_color='#313332', line_color='white', linewidth=2)
        pitch.draw(ax=ax)
        
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        
        if team_positions.empty:
            continue
        
        # Preparar datos de jugadores
        player_stats = {}
        for _, player in team_positions.iterrows():
            num_passes = player['total_actions']
            marker_size = change_range(num_passes, (min_player_count, max_player_count), (min_node_size, max_node_size))
            player_stats[player['source_player']] = {'marker_size': marker_size}
        
        # Dibujar conexiones con gradiente
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        for _, conn in valid_connections.iterrows():
            source_pos = team_positions[team_positions['source_player'] == conn['source_player']]
            target_pos = team_positions[team_positions['source_player'] == conn['target_player']]
            
            if source_pos.empty or target_pos.empty:
                continue
            
            x1 = source_pos.iloc[0]['avg_x_start']
            y1 = source_pos.iloc[0]['avg_y_start']
            x2 = target_pos.iloc[0]['avg_x_start']
            y2 = target_pos.iloc[0]['avg_y_start']
            
            source_radius = get_node_radius(player_stats[conn['source_player']]['marker_size'])
            target_radius = get_node_radius(player_stats[conn['target_player']]['marker_size'])
            
            start_x, start_y, end_x, end_y = calculate_connection_points(
                x1, y1, x2, y2, source_radius, target_radius, conn['connection_strength']
            )
            
            num_passes = conn['connection_strength']
            pass_value = conn.get('avg_xthreat', 0)
            
            line_width = change_range(num_passes, (min_pair_count, max_pair_count), (min_edge_width, max_edge_width))
            edge_color = nodes_cmap(xthreat_norm(pass_value))
            
            # Gradiente
            num_points = 75
            x_points = np.linspace(start_x, end_x, num_points)
            y_points = np.linspace(start_y, end_y, num_points)
            
            points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            
            alphas = np.linspace(0.1, 1.0, len(segments))
            rgb = mcolors.to_rgb(edge_color)
            colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
            
            lc = LineCollection(segments, colors=colors_with_alpha, linewidths=line_width,
                               capstyle='round', zorder=1)
            ax.add_collection(lc)
            
            draw_connection_arrow(ax, start_x, start_y, end_x, end_y, edge_color, line_width, 1.0)
        
        # Dibujar nodos semitransparentes
        for _, player in team_positions.iterrows():
            x = player['avg_x_start']
            y = player['avg_y_start']
            num_passes = player['total_actions']
            pass_value = player['avg_xthreat']
            
            marker_size = change_range(num_passes, (min_player_count, max_player_count), (min_node_size, max_node_size))
            node_color = nodes_cmap(xthreat_norm(pass_value))
            
            # Nodo con alpha=0.5
            ax.scatter(x, y, s=marker_size*15, c=[node_color], alpha=0.5,
                      edgecolors=node_color, linewidth=4, zorder=10)
            
            # Nombre centrado en el nodo
            name = player['source_player']
            display_name = ' '.join(name.split()[-2:]) if len(name) > 15 else name
            
            ax.text(x, y, display_name, ha='center', va='center',
                   color='white', fontsize=10, fontweight='bold',
                   path_effects=[
                       path_effects.Stroke(linewidth=3, foreground='black'),
                       path_effects.Normal()
                   ], zorder=15)
        
        # Nombre del equipo y logo en esquina superior izquierda
        ax.text(2, 96, team, fontsize=16, fontweight='bold', color='white', va='top')
        
        if (i == 0 and home_logo_path) or (i == 1 and away_logo_path):
            logo_path = home_logo_path if i == 0 else away_logo_path
            try:
                logo = Image.open(logo_path)
                logo_ax = fig.add_axes([0.05 if i == 0 else 0.05, 
                                       0.745 - i*0.375, 0.08, 0.08])
                logo_ax.imshow(logo)
                logo_ax.axis('off')
            except:
                pass
    
    # Título con resultado
    fig.suptitle(f"{home_team} {home_goals} - {away_goals} {away_team}", 
                fontsize=20, fontweight='bold', color='white', y=0.98)
    fig.text(0.5, 0.95, f"{league} | {season} | {match_date}",
            ha='center', fontsize=14, color='white')
    
    # Leyenda
    legend_y = 0.08
    font = 'Arial'
    
    # Textos de leyenda
    fig.text(0.14, legend_y + 0.05, "Pass count between", ha="center", fontsize=10, font=font, color='white')
    fig.text(0.38, legend_y + 0.05, "Pass value between (xT)", ha="center", fontsize=10, font=font, color='white')
    fig.text(0.61, legend_y + 0.05, "Player pass count", ha="center", fontsize=10, font=font, color='white')
    fig.text(0.84, legend_y + 0.05, "Player pass value (xT)", ha="center", fontsize=10, font=font, color='white')
    
    fig.text(0.13, legend_y, "5 to 16+", ha="center", fontsize=8, font=font, color='white')
    fig.text(0.37, legend_y, "0 to 0.09+", ha="center", fontsize=8, font=font, color='white')
    fig.text(0.61, legend_y, "1 to 88+", ha="center", fontsize=8, font=font, color='white')
    fig.text(0.84, legend_y, "0.01 to 0.36+", ha="center", fontsize=8, font=font, color='white')
    
    fig.text(0.41, legend_y - 0.02, "Low", ha="center", fontsize=9, font=font, color='white')
    fig.text(0.6, legend_y - 0.02, "High", ha="center", fontsize=9, font=font, color='white')
    
    # ELEMENTOS VISUALES DE LA LEYENDA
    # Coordenadas normalizadas para la leyenda
    ax_legend = fig.add_axes([0.05, 0.01, 0.9, 0.12], frameon=False)
    ax_legend.set_xlim(0, 1)
    ax_legend.set_ylim(0, 1)
    ax_legend.axis('off')
    
    # Flechas de grosor
    x0, y0 = 0.09, 0.2
    dx, dy = 0.03, 0.4
    shift = 0.02
    
    for i, lw in enumerate([0.5, 1.5, 2.5]):
        ax_legend.arrow(x0 + i*shift, y0, dx, dy, head_width=0.01, head_length=0.05,
                       fc='white', ec='white', linewidth=lw, alpha=0.8)
    
    # Flechas de colores
    x1 = 0.28
    colors_legend = [nodes_cmap(i/4) for i in range(5)]
    
    for i, color in enumerate(colors_legend):
        ax_legend.arrow(x1 + i*shift*1.5, y0, dx, dy, head_width=0.01, head_length=0.05,
                       fc=color, ec=color, linewidth=2.5, alpha=0.8)
    
    # Círculos de tamaño
    x2 = 0.57
    y2 = 0.5
    sizes = [0.01, 0.015, 0.02]
    
    for i, size in enumerate(sizes):
        circle = plt.Circle((x2 + i*0.04, y2), size, color='white', fill=False, linewidth=2)
        ax_legend.add_patch(circle)
    
    # Círculos de colores
    x3 = 0.78
    for i, color in enumerate(colors_legend[:5]):
        circle = plt.Circle((x3 + i*0.04, y2), 0.02, color=color, alpha=0.8)
        ax_legend.add_patch(circle)
    
    # Flecha Low -> High
    ax_legend.arrow(0.45, 0.15, 0.1, 0, head_width=0.05, head_length=0.02,
                   fc='white', ec='white', linewidth=1.5)
    
    # Créditos
    fig.text(0.95, 0.005, "Football Decoded", ha="right", fontsize=12, 
            font=font, color='white', weight='bold')
    fig.text(0.05, 0.005, "Created by Jaime Oriol", ha="left", fontsize=9, 
            font=font, color='white', style='italic')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15, top=0.93, hspace=0.05)
    
    if save_path:
        fig.savefig(save_path, dpi=400, bbox_inches='tight', facecolor='#313332')
        print(f"Visualización guardada en: {save_path}")
    
    return fig