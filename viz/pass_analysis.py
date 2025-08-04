import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import VerticalPitch
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
from PIL import Image
from collections import Counter
from scipy.spatial import ConvexHull
import os
import warnings
warnings.filterwarnings('ignore')

# Configuración visual global
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

# ====================================================================
# UTILIDADES COMUNES
# ====================================================================

def get_zone_jdp_custom(x, y):
    """Sistema de zonas jdp_custom (19 zonas)."""
    if pd.isna(x) or pd.isna(y):
        return np.nan
    
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    if x <= box_x_ratio * 100:
        if y < box_y_ratio * 100:
            return 2
        elif y <= (1-box_y_ratio) * 100:
            return 1
        else:
            return 0
    elif x <= 50:
        if y < box_y_ratio * 100:
            return 7
        elif y < 36.75:
            return 6
        elif y <= 63.25:
            return 5
        elif y <= (1-box_y_ratio) * 100:
            return 4
        else:
            return 3
    elif x < 66.67:
        if y < box_y_ratio * 100:
            return 10
        elif y < 36.75:
            return 12
        elif y <= 63.25:
            return 9
        elif y <= (1-box_y_ratio) * 100:
            return 11
        else:
            return 8
    elif x < (1-box_x_ratio) * 100:
        if y < box_y_ratio * 100:
            return 15
        elif y < 36.75:
            return 12
        elif y <= 63.25:
            return 14
        elif y <= (1-box_y_ratio) * 100:
            return 11
        else:
            return 13
    else:
        if y < box_y_ratio * 100:
            return 18
        elif y <= (1-box_y_ratio) * 100:
            return 17
        else:
            return 16

def get_zone_center(zone_id):
    """Centro de zona para visualización."""
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    centers = {
        0: (box_x_ratio * 50, (1 + (1-box_y_ratio)) * 50),
        1: (box_x_ratio * 50, ((1-box_y_ratio) + box_y_ratio) * 50),
        2: (box_x_ratio * 50, box_y_ratio * 50),
        3: ((box_x_ratio + 0.5) * 50, ((1-box_y_ratio) + 1) * 50),
        4: ((box_x_ratio + 0.5) * 50, ((1-box_y_ratio) + 0.6325) * 50),
        5: ((box_x_ratio + 0.5) * 50, (0.3675 + 0.6325) * 50),
        6: ((box_x_ratio + 0.5) * 50, (0.3675 + box_y_ratio) * 50),
        7: ((box_x_ratio + 0.5) * 50, box_y_ratio * 50),
        8: (((2/3) + 0.5) * 50, (1 + (1-box_y_ratio)) * 50),
        9: (((2/3) + 0.5) * 50, (0.6325 + 0.3675) * 50),
        10: (((2/3) + 0.5) * 50, box_y_ratio * 50),
        11: (((1-box_x_ratio) + 0.5) * 50, (0.6325 + (1-box_y_ratio)) * 50),
        12: (((1-box_x_ratio) + 0.5) * 50, (0.3675 + box_y_ratio) * 50),
        13: (((2/3) + (1-box_x_ratio)) * 50, (1 + (1-box_y_ratio)) * 50),
        14: (((2/3) + (1-box_x_ratio)) * 50, (0.6325 + 0.3675) * 50),
        15: (((2/3) + (1-box_x_ratio)) * 50, box_y_ratio * 50),
        16: ((1 + (1-box_x_ratio)) * 50, (1 + (1-box_y_ratio)) * 50),
        17: ((1 + (1-box_x_ratio)) * 50, (box_y_ratio + (1-box_y_ratio)) * 50),
        18: ((1 + (1-box_x_ratio)) * 50, box_y_ratio * 50)
    }
    return centers.get(zone_id, (50, 50))

def add_pitch_zones(ax):
    """Dibuja líneas de zona jdp_custom."""
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    lines = [
        ([box_y_ratio * 100] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([box_y_ratio * 100] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([(1 - box_y_ratio) * 100] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([(1 - box_y_ratio) * 100] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([36.75] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([36.75] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([63.25] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([63.25] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([0.1, (box_y_ratio - 0.001) * 100], [box_x_ratio * 100] * 2),
        ([(1 - box_y_ratio + 0.001) * 100, 99.9], [box_x_ratio * 100] * 2),
        ([0.1, (box_y_ratio - 0.001) * 100], [(1 - box_x_ratio) * 100] * 2),
        ([(1 - box_y_ratio + 0.001) * 100, 99.9], [(1 - box_x_ratio) * 100] * 2),
        ([0.1, (box_y_ratio - 0.001) * 100], [66.67] * 2),
        ([36.75, 63.25], [66.67] * 2),
        ([99.9, (1 - box_y_ratio + 0.001) * 100], [66.67] * 2)
    ]
    
    for line in lines:
        ax.plot(line[0], line[1], color='grey', alpha=0.3, lw=1, linestyle='--')

def format_player_initials(full_name):
    """Formatea a iniciales para hexágonos."""
    if pd.isna(full_name) or not full_name.strip():
        return "UK"
    
    name_parts = full_name.strip().split()
    
    if len(name_parts) == 1:
        return name_parts[0][:2].upper()
    else:
        return (name_parts[0][0] + name_parts[-1][0]).upper()

# ====================================================================
# PASS FLOW VISUALIZATION
# ====================================================================

def plot_pass_flow(events_csv_path, info_csv_path, home_logo_path=None, away_logo_path=None, save_path=None):
    """Visualización de flujo de pases con estética unificada."""
    # Cargar datos
    events_df = pd.read_csv(events_csv_path)
    info_df = pd.read_csv(info_csv_path)
    
    # Filtrar pases exitosos
    passes_df = events_df[
        (events_df['event_type'] == 'Pass') & 
        (events_df['outcome_type'] == 'Successful')
    ].dropna(subset=['x', 'y', 'end_x', 'end_y']).copy()
    
    if passes_df.empty:
        print("No hay pases válidos en los datos")
        return None
    
    teams = passes_df['team'].unique()
    if len(teams) != 2:
        print("Error: Se necesitan exactamente 2 equipos")
        return None
    
    # Extraer metadata
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Calcular resultado
    timeline_goals = info_df[
        (info_df['info_category'] == 'timeline') & 
        (info_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(timeline_goals[timeline_goals['team'] == home_team])
    away_goals = len(timeline_goals[timeline_goals['team'] == away_team])
    
    # Calcular zonas
    passes_df['start_zone'] = passes_df.apply(lambda r: get_zone_jdp_custom(r['x'], r['y']), axis=1)
    passes_df['end_zone'] = passes_df.apply(lambda r: get_zone_jdp_custom(r['end_x'], r['end_y']), axis=1)
    passes_df = passes_df.dropna(subset=['start_zone', 'end_zone'])
    
    # Calcular popularidad de zonas
    zone_popularity = {}
    for team in teams:
        team_passes = passes_df[passes_df['team'] == team]
        team_popularity = {}
        
        for start_zone in team_passes['start_zone'].unique():
            zone_passes = team_passes[team_passes['start_zone'] == start_zone]
            end_zones = Counter(zone_passes['end_zone'].values)
            
            if start_zone in end_zones and len(end_zones) > 1:
                del end_zones[start_zone]
            elif start_zone in end_zones and len(end_zones) == 1:
                continue
                
            if end_zones:
                team_popularity[start_zone] = end_zones
        
        zone_popularity[team] = team_popularity
    
    # Configurar figura
    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=(8.5, 8.5), dpi=400, facecolor=BACKGROUND_COLOR)
    
    for i in range(2):
        ax[i].set_facecolor(BACKGROUND_COLOR)
    
    # Configurar campos
    pitch1 = VerticalPitch(pitch_color=PITCH_COLOR, pitch_type='opta', line_color='white', linewidth=1)
    pitch2 = VerticalPitch(pitch_color=PITCH_COLOR, pitch_type='opta', line_color='white', linewidth=1)
    
    pitch1.draw(ax=ax[0])
    pitch2.draw(ax=ax[1])
    
    add_pitch_zones(ax[0])
    add_pitch_zones(ax[1])
    
    # Colormaps
    home_cmap, away_cmap = plt.cm.Oranges, plt.cm.Blues
    cmaps = [home_cmap, away_cmap]
    
    # Dibujar flujos
    team_list = [home_team, away_team]
    for idx, team in enumerate(team_list):
        team_connections = zone_popularity[team]
        
        for start_zone, end_zones in team_connections.items():
            most_common = end_zones.most_common(1)[0]
            end_zone, count = most_common
            
            start_x, start_y = get_zone_center(start_zone)
            end_x, end_y = get_zone_center(end_zone)
            
            color_intensity = min(1.0, max(0.1, count / 15.0))
            color = cmaps[idx](color_intensity)
            
            # Dibujar línea
            if idx == 0:
                pitch1.lines(start_x, start_y, end_x, end_y, lw=10, comet=True,
                           ax=ax[idx], color=color, transparent=True, alpha=0.3, zorder=count)
            else:
                pitch2.lines(start_x, start_y, end_x, end_y, lw=10, comet=True,
                           ax=ax[idx], color=color, transparent=True, alpha=0.3, zorder=count)
            
            ax[idx].scatter(end_x, end_y, s=100, c=[color], zorder=count)
    
    font = 'serif'
    
    # TÍTULOS CORREGIDOS - Usar mismas coordenadas que Pass Hull
    fig.text(x=0.5, y=.93, s="Pass Flow",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.91  # CAMBIO: era 0.9
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='bold', va="bottom", ha="center", fontsize=11, font=font, color='white')
    
    fig.text(x=0.5, y=0.89, s=f"{league} | Season {season} | {match_date}",  # CAMBIO: era 0.875
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    fig.text(x=0.5, y=0.87, s="Most Frequent Inter-zone Passes", ha='center',  # CAMBIO: era 0.84
            fontweight="regular", fontsize=12, color='w', family=font)
    
    # Logos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.27, result_y-0.035, 0.09, 0.09])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.65, result_y-0.035, 0.09, 0.09])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Flecha de dirección
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", fontsize=10, color="w", fontweight="regular", rotation=90, family=font)
    
    # Leyendas
    legend_ax_1 = fig.add_axes([0.055, 0.07, 0.4, 0.09])
    legend_ax_1.set_xlim([0, 8])
    legend_ax_1.set_ylim([-0.5, 1])
    legend_ax_1.axis("off")
    
    legend_ax_2 = fig.add_axes([0.545, 0.07, 0.4, 0.09])
    legend_ax_2.set_xlim([0, 8])
    legend_ax_2.set_ylim([-0.5, 1])
    legend_ax_2.axis("off")
    
    legend_values = [1, 3, 5, 7, 9, 11, 13, 15]
    for idx, pass_count in enumerate(legend_values):
        ypos = 0.32 if idx % 2 == 0 else 0.56
        xpos = idx / 1.4 + 1.5
        
        color_intensity = min(1.0, max(0.1, pass_count / 15.0))
        text_color = '#313332' if pass_count <= 3 else 'w'
        
        color_1 = home_cmap(color_intensity)
        legend_ax_1.scatter(xpos, ypos, marker='H', s=550, color=color_1, edgecolors='w', lw=0.5)
        legend_ax_1.text(xpos, ypos, pass_count, color=text_color, ha="center", va="center", fontsize=9, family=font)
        
        color_2 = away_cmap(color_intensity)
        legend_ax_2.scatter(xpos, ypos, marker='H', s=550, color=color_2, edgecolors='w', lw=0.5)
        legend_ax_2.text(xpos, ypos, pass_count, color=text_color, ha="center", va="center", fontsize=9, family=font)
    
    legend_ax_1.text(4, -0.25, "Pass Count", color='w', ha="center", va="center", fontsize=9, family=font)
    legend_ax_2.text(4, -0.25, "Pass Count", color='w', ha="center", va="center", fontsize=9, family=font)
    
    # Stats footer
    home_total = len(passes_df[passes_df['team'] == home_team])
    away_total = len(passes_df[passes_df['team'] == away_team])
    
    fig.text(0.5, 0.055, f"Total passes: {home_team} {home_total} | {away_team} {away_total}", 
             ha='center', va='center', color='white', fontsize=9, family=font)
    
    # Créditos
    fig.text(0.87, 0.03, "Football Decoded", va="bottom", ha="center", weight='bold', fontsize=14, family=font, color='white')
    fig.text(0.1, 0.03, "Created by Jaime Oriol", va="bottom", ha="center", weight='bold', fontsize=10, family=font, color='white')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Pass Flow guardado en: {save_path}")
    
    return fig

# ====================================================================
# PASS HULL VISUALIZATION  
# ====================================================================

def calculate_player_hull(player_events, min_events=5):
    """Calcula convex hull para un jugador."""
    if len(player_events) < min_events:
        return None
    
    coordinates = player_events[['x', 'y']].dropna().values
    
    if len(coordinates) < 3:
        return None
    
    try:
        # Filtrar outliers (1 std dev)
        center_x, center_y = coordinates[:, 0].mean(), coordinates[:, 1].mean()
        distances = np.sqrt((coordinates[:, 0] - center_x)**2 + (coordinates[:, 1] - center_y)**2)
        std_dist = distances.std()
        
        mask = distances <= std_dist
        filtered_coords = coordinates[mask]
        
        if len(filtered_coords) < 3:
            filtered_coords = coordinates
        
        hull = ConvexHull(filtered_coords)
        hull_points = filtered_coords[hull.vertices]
        
        hull_centroid_x = hull_points[:, 0].mean()
        hull_centroid_y = hull_points[:, 1].mean()
        
        return {
            'hull_points': hull_points,
            'area': hull.volume,
            'centroid_x': hull_centroid_x,
            'centroid_y': hull_centroid_y
        }
    except:
        return None

def plot_pass_hull(events_csv_path, info_csv_path, home_logo_path=None, away_logo_path=None, save_path=None):
    """Visualización de hulls de jugadores con estética unificada."""
    # Cargar datos
    events_df = pd.read_csv(events_csv_path)
    info_df = pd.read_csv(info_csv_path)
    
    # Filtrar eventos con coordenadas
    valid_events = events_df.dropna(subset=['x', 'y', 'player']).copy()
    
    if valid_events.empty:
        print("No hay eventos válidos con coordenadas")
        return None
    
    teams = valid_events['team'].unique()
    if len(teams) != 2:
        print("Error: Se necesitan exactamente 2 equipos")  
        return None
    
    # Extraer metadata
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Calcular resultado
    timeline_goals = info_df[
        (info_df['info_category'] == 'timeline') & 
        (info_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(timeline_goals[timeline_goals['team'] == home_team])
    away_goals = len(timeline_goals[timeline_goals['team'] == away_team])
    
    # Configurar figura
    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=(8.5, 8.5), dpi=400, facecolor=BACKGROUND_COLOR)
    
    for i in range(2):
        ax[i].set_facecolor(BACKGROUND_COLOR)
    
    # Configurar campos
    pitch1 = VerticalPitch(pitch_color=PITCH_COLOR, pitch_type='opta', line_color='white', linewidth=1)
    pitch2 = VerticalPitch(pitch_color=PITCH_COLOR, pitch_type='opta', line_color='white', linewidth=1)
    
    pitch1.draw(ax=ax[0])
    pitch2.draw(ax=ax[1])
    
    # Colores para jugadores
    colors = ['tomato', 'gold', 'lawngreen', 'deepskyblue', 'violet', 'cyan', 'yellow', 'lightpink', 'orange', 'lime', 'magenta']
    
    team_list = [home_team, away_team]
    
    # Calcular TODOS los hulls primero para ranking global
    all_player_hulls = []
    
    for team in team_list:
        team_events = valid_events[valid_events['team'] == team]
        players = team_events['player'].unique()
        
        for player in players:
            player_events = team_events[team_events['player'] == player]
            hull_data = calculate_player_hull(player_events)
            
            if hull_data:
                hull_data['player'] = player
                hull_data['team'] = team
                all_player_hulls.append(hull_data)
    
    # Ranking global (no por equipo)
    all_player_hulls.sort(key=lambda x: x['area'], reverse=True)
    top_3_global = all_player_hulls[:3]
    
    for idx, team in enumerate(team_list):
        team_hulls = [h for h in all_player_hulls if h['team'] == team]
        
        # Dibujar hulls
        for i, hull_data in enumerate(team_hulls):
            player = hull_data['player']
            hull_points = hull_data['hull_points']
            centroid_x, centroid_y = hull_data['centroid_x'], hull_data['centroid_y']
            
            color = colors[i % len(colors)]
            
            # Dibujar hull
            ax[idx].scatter(hull_points[:, 1], hull_points[:, 0], color=color, s=20, alpha=0.3, zorder=2)
            
            # Polygon
            from matplotlib.patches import Polygon
            poly = Polygon([(p[1], p[0]) for p in hull_points], facecolor=color, alpha=0.2, zorder=1)
            ax[idx].add_patch(poly)
            
            poly_edge = Polygon([(p[1], p[0]) for p in hull_points], facecolor='none', edgecolor=color, alpha=0.3, zorder=1)
            ax[idx].add_patch(poly_edge)
            
            # Centro del jugador usando centroide del hull
            ax[idx].scatter(centroid_y, centroid_x, marker='H', color=color, alpha=0.6, s=400, zorder=3)
            ax[idx].scatter(centroid_y, centroid_x, marker='H', edgecolor=color, facecolor='none', alpha=1, lw=2, s=400, zorder=3)
            
            # Iniciales
            initials = format_player_initials(player)
            text_color = 'w' if color not in ['snow', 'white', 'yellow', 'cyan', 'lime'] else 'k'
            ax[idx].text(centroid_y, centroid_x, initials, fontsize=8, fontweight='bold', va='center', ha='center', color=text_color, zorder=4, family='serif')
    
    font = 'serif'
    
    # Títulos
    fig.text(x=0.5, y=.93, s="Pass Hull",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.91
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='bold', va="bottom", ha="center", fontsize=11, font=font, color='white')
    
    fig.text(x=0.5, y=0.89, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    fig.text(x=0.5, y=0.85, s="Variation in start position of player passes. Central 75%\nof passes shown per player, represented by a shaded region", ha='center', 
            fontweight="regular", fontsize=10, color='w', family=font)
    
    # Logos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.27, result_y-0.035, 0.09, 0.09])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.65, result_y-0.035, 0.09, 0.09])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Flecha de dirección
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", fontsize=10, color="w", fontweight="regular", rotation=90, family=font)
    
    # Rankings por equipos (layout doble como original)
    home_hulls = [h for h in all_player_hulls if h['team'] == home_team][:3]
    away_hulls = [h for h in all_player_hulls if h['team'] == away_team][:3]
    
    # Crear axes para la leyenda con líneas
    legend_ax = fig.add_axes([0.05, 0.05, 0.9, 0.12])
    legend_ax.set_xlim(0, 10)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis('off')
    
    # Texto central
    ranking_text = "Top players by area of\nregion containing central\n75% passes shown (as % of total\npitch area)"
    legend_ax.text(5, 0.55, ranking_text, ha='center', va='center', fontsize=9, color='w', family=font)
    
    # Líneas de conexión (como el original)
    legend_ax.arrow(3.6, 0.5, -0.75, 0, color='w', width=0.005, head_width=0.03, head_length=0.1)
    legend_ax.arrow(6.4, 0.5, 0.75, 0, color='w', width=0.005, head_width=0.03, head_length=0.1)
    
    # Rankings por equipo (alineación exacta)
    for i, hull_data in enumerate(home_hulls):
        player_surname = hull_data['player'].split()[-1]
        area_pct = (hull_data['area'] / 10000) * 100
        y_pos = 0.6 - (i * 0.12)
        legend_ax.text(0.5, y_pos, f"{i+1}.", ha='left', va='center', fontsize=10, color='w', family=font)
        legend_ax.text(0.8, y_pos, f"{player_surname}", ha='left', va='center', fontsize=10, color='w', family=font)
        legend_ax.text(2.65, y_pos, f"{area_pct:.1f}%", ha='right', va='center', fontsize=10, color='w', family=font)
    
    for i, hull_data in enumerate(away_hulls):
        player_surname = hull_data['player'].split()[-1]
        area_pct = (hull_data['area'] / 10000) * 100
        y_pos = 0.6 - (i * 0.12)
        legend_ax.text(7.5, y_pos, f"{i+1}.", ha='left', va='center', fontsize=10, color='w', family=font)
        legend_ax.text(7.8, y_pos, f"{player_surname}", ha='left', va='center', fontsize=10, color='w', family=font)
        legend_ax.text(9.65, y_pos, f"{area_pct:.1f}%", ha='right', va='center', fontsize=10, color='w', family=font)
    
    # FOOTER AÑADIDO - idéntico a Pass Flow
    fig.text(0.87, 0.05, "Football Decoded", va="bottom", ha="center", weight='bold', fontsize=14, family=font, color='white')
    fig.text(0.1, 0.05, "Created by Jaime Oriol", va="bottom", ha="center", weight='bold', fontsize=10, family=font, color='white')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Pass Hull guardado en: {save_path}")
    
    return fig