import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import VerticalPitch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

def plot_pass_network(network_csv_path, aggregates_csv_path, info_csv_path, 
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(16, 10), save_path=None):
    """
    Crea visualización de pass network con colores StatsBomb para xThreat.
    """
    
    try:
        network_df = pd.read_csv(network_csv_path)
        info_df = pd.read_csv(info_csv_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"No se pudo encontrar el archivo: {e}")
    except Exception as e:
        raise Exception(f"Error al leer los CSVs: {e}")
    
    # Extraer metadata
    try:
        home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
        away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
        match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
        league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
        season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    except IndexError:
        raise ValueError("Los CSVs no contienen la información requerida de match_info")
    
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    if positions_df.empty:
        raise ValueError("No se encontraron datos de posiciones en el CSV")
    
    statsbomb_cmap = LinearSegmentedColormap.from_list("statsbomb_xthreat", [
        '#1f4e79', '#5b9bd5', '#a9d18e', '#f4b942', '#c5504b'
    ])
    
    def calculate_node_size(total_actions):
        if total_actions <= 10:
            return 400
        elif total_actions >= 110:
            return 12400
        elif total_actions <= 60:
            return 400 + (total_actions - 10) * 80
        else:
            base = 400 + (60 - 10) * 80
            return base + (total_actions - 60) * 160
    
    def calculate_line_width(connection_strength, min_conn, max_conn):
        min_passes_required = 5
        if connection_strength < min_passes_required:
            return 0.0
        
        if max_conn == min_conn:
            return 2.5
        
        normalized = (connection_strength - min_conn) / (max_conn - min_conn)
        curved = normalized ** 0.6
        return 0.5 + curved * 4.5
    
    def optimize_name(full_name):
        if len(full_name.split()) > 1:
            return ' '.join(full_name.split()[-2:]) if len(full_name) > 15 else full_name
        return full_name
    
    def process_team_data(team_name):
        team_positions = positions_df[positions_df['team'] == team_name].copy()
        team_connections = connections_df[connections_df['team'] == team_name].copy()
        
        if team_positions.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        team_data = team_positions.copy()
        team_data['xthreat_total'] = team_data['xthreat_total'].fillna(0)
        team_data['total_actions'] = team_data['total_actions'].fillna(1)
        team_data['node_size'] = team_data['total_actions'].apply(calculate_node_size)
        
        valid_connections = team_connections[team_connections['connection_strength'] >= 5].copy()
        
        if not valid_connections.empty:
            min_conn = valid_connections['connection_strength'].min()
            max_conn = valid_connections['connection_strength'].max()
            valid_connections['line_width'] = valid_connections['connection_strength'].apply(
                lambda x: calculate_line_width(x, min_conn, max_conn)
            )
        else:
            valid_connections = pd.DataFrame()
        
        return team_data, valid_connections
    
    fig, axes = plt.subplots(1, 2, figsize=figsize, facecolor='#313332')
    teams = [home_team, away_team]
    all_xthreat_values = []
    
    # Normalización global de xThreat desde positions
    for team in teams:
        team_positions_temp = positions_df[positions_df['team'] == team]
        if not team_positions_temp.empty:
            all_xthreat_values.extend(team_positions_temp['xthreat_total'].values)
    
    if all_xthreat_values:
        global_xthreat_min = min(all_xthreat_values)
        global_xthreat_max = max(all_xthreat_values)
        if global_xthreat_max == global_xthreat_min:
            global_xthreat_max = global_xthreat_min + 0.1
    else:
        global_xthreat_min, global_xthreat_max = 0, 0.1
    
    xthreat_norm = Normalize(vmin=global_xthreat_min, vmax=global_xthreat_max)
    
    for i, team in enumerate(teams):
        ax = axes[i]
        
        pitch = VerticalPitch(pitch_color='#313332', line_color='white', linewidth=1, pitch_type='opta')
        pitch.draw(ax=ax)
        
        team_players, team_connections = process_team_data(team)
        
        if team_players.empty:
            ax.text(52.5, 35, f"No data for {team}", ha='center', va='center', 
                   fontsize=16, color='white', fontweight='bold')
            continue
        
        # Dibujar conexiones
        if not team_connections.empty:
            for _, conn in team_connections.iterrows():
                source_pos = team_players[team_players['source_player'] == conn['source_player']]
                target_pos = team_players[team_players['source_player'] == conn['target_player']]
                
                if source_pos.empty or target_pos.empty:
                    continue
                
                x1, y1 = source_pos.iloc[0]['avg_x_start'], source_pos.iloc[0]['avg_y_start']
                x2, y2 = target_pos.iloc[0]['avg_x_start'], target_pos.iloc[0]['avg_y_start']
                
                conn_xthreat = conn.get('avg_xthreat', 0)
                color = statsbomb_cmap(xthreat_norm(conn_xthreat))
                
                # Gradiente en línea
                num_points = 50
                x_points = np.linspace(x1, x2, num_points)
                y_points = np.linspace(y1, y2, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                alphas = np.linspace(0.3, 0.9, len(segments))
                rgb = mcolors.to_rgb(color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=conn['line_width'], capstyle='round', zorder=2)
                ax.add_collection(lc)
                
                # Flecha direccional
                dx, dy = x2 - x1, y2 - y1
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    ux, uy = dx / length, dy / length
                    
                    arrow_size = max(0.8, conn['line_width'] * 0.3)
                    tip_x = x2 - 1.5 * ux
                    tip_y = y2 - 1.5 * uy
                    
                    base_x = tip_x - arrow_size * ux
                    base_y = tip_y - arrow_size * uy
                    
                    ax.plot([tip_x, base_x], [tip_y, base_y], 
                           color=color, linewidth=max(2.0, conn['line_width'] * 0.8), 
                           alpha=0.9, solid_capstyle='round', zorder=100)
        
        # Dibujar nodos
        for _, player in team_players.iterrows():
            x, y = player['avg_x_start'], player['avg_y_start']
            node_size = player['node_size']
            xthreat_value = player['xthreat_total']
            
            node_color = statsbomb_cmap(xthreat_norm(xthreat_value))
            
            ax.scatter(x, y, s=node_size, c=[node_color], alpha=0.8,
                      edgecolors='white', linewidth=3, zorder=10)
        
        # Nombres de jugadores
        for _, player in team_players.iterrows():
            x, y = player['avg_x_start'], player['avg_y_start']
            full_name = player['source_player']
            display_name = optimize_name(full_name)
            
            ax.text(x, y, display_name, ha='center', va='center',
                   color='white', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.1", facecolor='black', alpha=0.3),
                   zorder=15)
        
        ax.set_xlim(-5, 110)
        ax.set_ylim(-10, 70)
        ax.set_aspect('equal')
        ax.axis('off')
        
        ax.text(52.5, -6, team, ha='center', va='center', 
               fontsize=16, fontweight='bold', color='white')
    
    # Títulos
    fig.text(0.5, 0.95, f"Passing Network - {league}", 
             ha='center', va='center', fontsize=24, fontweight='bold', color='white')
    
    fig.text(0.5, 0.91, f"{home_team} vs {away_team}", 
             ha='center', va='center', fontsize=20, fontweight='bold', color='white')
    
    fig.text(0.5, 0.87, f"{season} | {match_date}", 
             ha='center', va='center', fontsize=14, color='white')
    
    # Logos
    if home_logo_path:
        try:
            img = Image.open(home_logo_path)
            ax_logo = fig.add_axes([0.05, 0.85, 0.08, 0.08])
            ax_logo.imshow(img)
            ax_logo.axis('off')
        except Exception as e:
            print(f"Warning: No se pudo cargar el logo home: {e}")
    
    if away_logo_path:
        try:
            img = Image.open(away_logo_path)
            ax_logo = fig.add_axes([0.87, 0.85, 0.08, 0.08])
            ax_logo.imshow(img)
            ax_logo.axis('off')
        except Exception as e:
            print(f"Warning: No se pudo cargar el logo away: {e}")
    
    # Leyenda de tamaños
    legend_ax1 = fig.add_axes([0.1, 0.05, 0.35, 0.08])
    legend_ax1.set_xlim([0, 10])
    legend_ax1.set_ylim([0, 1])
    legend_ax1.axis('off')
    
    sizes = [10, 30, 60, 100]
    positions = [1, 3, 5, 7]
    
    for i, (size, pos) in enumerate(zip(sizes, positions)):
        node_size = calculate_node_size(size) * 0.3
        legend_ax1.scatter(pos, 0.7, s=node_size, c='gray', alpha=0.6, 
                          edgecolors='white', linewidth=1)
        legend_ax1.text(pos, 0.2, f"{size}", ha='center', va='center',
                       fontsize=10, color='white', fontweight='bold')
    
    legend_ax1.text(4, 0.05, "Total Actions", ha='center', va='center',
                   fontsize=12, color='white', fontweight='bold')
    
    # Leyenda de colores
    legend_ax2 = fig.add_axes([0.55, 0.05, 0.35, 0.08])
    legend_ax2.set_xlim([0, 10])
    legend_ax2.set_ylim([0, 1])
    legend_ax2.axis('off')
    
    xthreat_step = (global_xthreat_max - global_xthreat_min) / 4
    xthreat_values = [global_xthreat_min + i * xthreat_step for i in range(5)]
    colors = [statsbomb_cmap(i/4) for i in range(5)]
    
    for i, (xt_val, color, pos) in enumerate(zip(xthreat_values, colors, positions)):
        legend_ax2.scatter(pos, 0.7, s=800, c=[color], alpha=0.8, 
                          edgecolors='white', linewidth=1)
        legend_ax2.text(pos, 0.2, f"{xt_val:.2f}", ha='center', va='center',
                       fontsize=10, color='white', fontweight='bold')
    
    legend_ax2.text(4, 0.05, "xThreat Value", ha='center', va='center',
                   fontsize=12, color='white', fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.83, bottom=0.18)
    
    if save_path:
        try:
            fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor='#313332', edgecolor='none')
            print(f"Visualización guardada en: {save_path}")
        except Exception as e:
            print(f"Error al guardar: {e}")
    
    return fig