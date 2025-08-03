import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import VerticalPitch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch, Circle, ArrowStyle
import matplotlib.colors as mcolors
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

def plot_pass_network(network_csv_path, info_csv_path, 
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(6, 6), save_path=None):
    
    # Leer datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    
    # Extraer metadata
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # TRANSFORMACIÓN CORRECTA: Para vertical, Y del CSV -> X del pitch, X del CSV -> Y del pitch
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
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
    
    # Setup figura
    plt.style.use('fivethirtyeight')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400)
    
    teams = [home_team, away_team]
    
    # Normalización global de xThreat
    all_xthreat_values = []
    for team in teams:
        team_positions = positions_df[positions_df['team'] == team]
        if not team_positions.empty:
            all_xthreat_values.extend(team_positions['avg_xthreat'].values)
    
    xthreat_norm = Normalize(vmin=min_player_value, vmax=max_player_value)
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        '#E15A82', '#EEA934', '#F1CA56', '#DCED69', '#7FF7A8', '#5AE1AC', '#11C0A1'
    ])
    
    for i, team in enumerate(teams):
        # Dibujar pitch
        pitch = VerticalPitch(pitch_type='opta', line_color='#7c7c7c', goal_type='box',
                             linewidth=0.5, pad_bottom=10)
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
        
        if team_positions.empty:
            continue
        
        # Preparar datos de jugadores
        player_stats = {}
        
        # Dibujar conexiones
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        for _, conn in valid_connections.iterrows():
            # Buscar posiciones usando source_player
            source_pos = team_positions[team_positions['source_player'] == conn['source_player']]
            target_pos = team_positions[team_positions['source_player'] == conn['target_player']]
            
            if source_pos.empty or target_pos.empty:
                continue
            
            # Usar coordenadas transformadas
            x1 = source_pos.iloc[0]['x_pitch']
            y1 = source_pos.iloc[0]['y_pitch'] 
            x2 = target_pos.iloc[0]['x_pitch']
            y2 = target_pos.iloc[0]['y_pitch']
            
            num_passes = conn['connection_strength']
            pass_value = conn.get('avg_xthreat', 0)
            
            line_width = change_range(num_passes, (min_pair_count, max_pair_count), (min_edge_width, max_edge_width))
            alpha = change_range(pass_value, (min_pair_value, max_pair_value), (0.4, 1))
            
            edge_color = node_cmap(xthreat_norm(pass_value))
            
            # Calcular shifts
            dx = x2 - x1
            dy = y2 - y1
            rel = 68/105
            shift_x = 2
            shift_y = shift_x * rel
            
            slope = abs(dy * 105/100 / (dx * 68/100)) if dx != 0 else float('inf')
            
            # Dibujar flecha con offset correcto
            if slope > 0.5:
                if dy > 0:
                    ax[i].annotate("", xy=(x2+shift_x, y2), xytext=(x1+shift_x, y1), zorder=2,
                            arrowprops=dict(arrowstyle=f'->, head_length={head_length}, head_width={head_width}',
                                          color=tuple([alpha if n == 3 else c for n, c in enumerate(edge_color)]),
                                          lw=line_width,
                                          shrinkB=5))
                else:
                    ax[i].annotate("", xy=(x2-shift_x, y2), xytext=(x1-shift_x, y1), zorder=2,
                            arrowprops=dict(arrowstyle=f'->, head_length={head_length}, head_width={head_width}',
                                          color=tuple([alpha if n == 3 else c for n, c in enumerate(edge_color)]),
                                          lw=line_width,
                                          shrinkB=5))
            else:
                if dx > 0:
                    ax[i].annotate("", xy=(x2, y2-shift_y), xytext=(x1, y1-shift_y), zorder=2,
                            arrowprops=dict(arrowstyle=f'->, head_length={head_length}, head_width={head_width}',
                                          color=tuple([alpha if n == 3 else c for n, c in enumerate(edge_color)]),
                                          lw=line_width,
                                          shrinkB=5))
                else:
                    ax[i].annotate("", xy=(x2, y2+shift_y), xytext=(x1, y1+shift_y), zorder=2,
                            arrowprops=dict(arrowstyle=f'->, head_length={head_length}, head_width={head_width}',
                                          color=tuple([alpha if n == 3 else c for n, c in enumerate(edge_color)]),
                                          lw=line_width,
                                          shrinkB=5))
        
        # Dibujar nodos
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            
            num_passes = player['total_actions']
            pass_value = player['avg_xthreat']
            
            marker_size = change_range(num_passes, (min_player_count, max_player_count), (min_node_size, max_node_size))
            node_color = node_cmap(xthreat_norm(pass_value))
            
            ax[i].plot(x, y, '.', color=node_color, markersize=marker_size, zorder=5)
            ax[i].plot(x, y, '.', markersize=marker_size+2, zorder=4, color='white')
            
            # Guardar marker_size para las conexiones
            player_stats[player['source_player']] = {'marker_size': marker_size}
            
            # Nombre
            name = player['source_player']
            var_ = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else name
            ax[i].annotate(var_, xy=(x, y+5 if y > 48 else y-5), ha="center", va="center",
                          zorder=7, fontsize=5, color='black', font='serif', weight='heavy')
    
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
    # Coordenadas absolutas del notebook
    x0 = 190
    y0 = 280
    dx = 60
    dy = 120
    shift_x = 70
    
    x1 = 700
    x2 = 1350
    y2 = 340
    shift_x2 = 70
    radius = 20
    
    x3 = 1800
    shift_x3 = 100
    
    x4 = 1020
    y4 = 180
    
    style = ArrowStyle('->', head_length=5, head_width=3)
    
    # Flechas de grosor para pass count
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='black')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='black')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='black')
    
    # Flechas de colores para xT
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
    
    # Flecha horizontal Low -> High
    arrow9 = FancyArrowPatch((x4, y4), (x4+350, y4), lw=1, arrowstyle=style, color='black')
    
    # Agregar todos los elementos
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, circle4, circle5, circle6, circle7, circle8, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400)
        print(f"Visualización guardada en: {save_path}")
    
    return fig