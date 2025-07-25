import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull
from matplotlib.patches import Polygon
from PIL import Image
import os

def create_pass_hulls(passes_csv, positions_csv, home_team, away_team, league, season, 
                     match_date, central_pct=75, min_passes=5):
    
    passes_df = pd.read_csv(passes_csv)
    successful_passes = passes_df[passes_df['is_successful'] == True].copy()
    teams = [home_team, away_team]
    
    fig, axes = plt.subplots(1, 2, figsize=(17, 10))
    fig.patch.set_facecolor('#313332')
    
    all_hulls = []
    
    for idx, team in enumerate(teams):
        ax = axes[idx]
        setup_pitch(ax)
        
        team_passes = successful_passes[successful_passes['team'] == team]
        team_hulls = calculate_team_hulls(team_passes, central_pct, min_passes, idx)
        all_hulls.extend(team_hulls)
        
        plot_hulls(ax, team_hulls, team_passes)
        ax.set_title(team, color='white', fontsize=16, fontweight='bold', pad=20)
    
    add_titles(fig, teams, league, season, match_date, central_pct)
    add_statistics(fig, all_hulls, teams)
    add_direction_arrow(fig)
    
    return fig

def setup_pitch(ax):
    ax.set_facecolor('#313332')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    
    # Líneas principales
    ax.plot([0, 100], [50, 50], 'white', linewidth=1, alpha=0.5)
    ax.plot([50, 50], [0, 100], 'white', linewidth=1, alpha=0.5)
    
    # Áreas del campo
    areas = [
        plt.Rectangle((0, 21.1), 16.5, 57.8, fill=False, edgecolor='white', linewidth=1),
        plt.Rectangle((83.5, 21.1), 16.5, 57.8, fill=False, edgecolor='white', linewidth=1),
        plt.Rectangle((0, 36.8), 5.5, 26.4, fill=False, edgecolor='white', linewidth=1),
        plt.Rectangle((94.5, 36.8), 5.5, 26.4, fill=False, edgecolor='white', linewidth=1)
    ]
    
    for area in areas:
        ax.add_patch(area)
    
    # Círculo central
    circle = plt.Circle((50, 50), 9.15, fill=False, edgecolor='white', linewidth=1)
    ax.add_patch(circle)
    
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

def calculate_team_hulls(team_passes, central_pct, min_passes, team_idx):
    hulls_data = []
    players = team_passes['player'].unique()
    
    for i, player in enumerate(players):
        player_passes = team_passes[team_passes['player'] == player]
        
        if len(player_passes) >= min_passes:
            hull_data = create_player_hull(player_passes, player, central_pct, team_idx, i)
            if hull_data:
                hulls_data.append(hull_data)
    
    return sorted(hulls_data, key=lambda x: x['area'], reverse=True)

def create_player_hull(player_passes, player, central_pct, team_idx, player_idx):
    try:
        coords = player_passes[['x', 'y']].values
        
        # Calcular hull reducido
        centroid = np.mean(coords, axis=0)
        distances = np.sqrt(np.sum((coords - centroid)**2, axis=1))
        percentile = np.percentile(distances, central_pct)
        central_coords = coords[distances <= percentile]
        
        if len(central_coords) < 3:
            return None
        
        hull = ConvexHull(central_coords)
        hull_coords = central_coords[hull.vertices]
        
        # Calcular métricas
        hull_center = np.mean(hull_coords, axis=0)
        hull_area = hull.volume
        hull_area_pct = (hull_area / 10000) * 100
        
        return {
            'player': player,
            'team_idx': team_idx,
            'coords': hull_coords,
            'center': hull_center,
            'area': hull_area,
            'area_pct': hull_area_pct,
            'color': get_position_color(player_idx, team_idx),
            'passes': len(player_passes)
        }
    except:
        return None

def get_position_color(player_idx, team_idx):
    # Sistema de colores basado en el original
    position_colors = [
        'lawngreen', 'deepskyblue', 'tomato', 'lightpink', 'snow', 
        'violet', 'cyan', 'yellow', 'gold', 'orange', 'lightcoral'
    ]
    return position_colors[player_idx % len(position_colors)]

def plot_hulls(ax, hulls_data, team_passes):
    for hull_data in hulls_data:
        color = hull_data['color']
        
        # Puntos de pases dispersos
        player_passes = team_passes[team_passes['player'] == hull_data['player']]
        ax.scatter(player_passes['x'], player_passes['y'], 
                  c=color, s=20, alpha=0.3, zorder=2)
        
        # Polígono del hull
        hull_polygon = Polygon(hull_data['coords'], 
                              facecolor=color, alpha=0.2, 
                              edgecolor=color, linewidth=1, zorder=1)
        ax.add_patch(hull_polygon)
        
        # Centro con hexágono y borde
        center = hull_data['center']
        ax.scatter(center[0], center[1], marker='H', s=400, 
                  c=color, alpha=0.6, zorder=3)
        ax.scatter(center[0], center[1], marker='H', s=400,
                  facecolor='none', edgecolors=color, linewidth=2, alpha=1, zorder=3)
        
        # Iniciales del jugador
        initials = get_initials(hull_data['player'])
        text_color = 'black' if is_light_color(color) else 'white'
        ax.text(center[0], center[1], initials, ha='center', va='center',
               fontweight='bold', fontsize=8, color=text_color, zorder=4)

def get_initials(name):
    parts = name.split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    else:
        return (parts[0][0] + parts[-1][0]).upper()

def is_light_color(color):
    light_colors = ['snow', 'white', 'yellow', 'cyan', 'lightpink', 'lawngreen', 'gold']
    return color in light_colors

def add_titles(fig, teams, league, season, match_date, central_pct):
    fig.suptitle(f'{league} - {season}\n{teams[0]} vs {teams[1]} - {match_date}', 
                color='white', fontsize=18, fontweight='bold', y=0.95)
    
    subtitle = f'Variation in start position of player passes. Central {central_pct}%\nof passes shown per player, represented by a shaded region'
    fig.text(0.5, 0.88, subtitle, ha='center', color='white', fontsize=11)

def add_statistics(fig, all_hulls, teams):
    # Panel de estadísticas como el original
    stats_ax = fig.add_axes([0.053, 0.055, 0.895, 0.11])
    stats_ax.set_xlim(0, 1)
    stats_ax.set_ylim(0, 1)
    stats_ax.axis('off')
    
    # Top 3 por equipo
    for team_idx in range(2):
        team_hulls = [h for h in all_hulls if h['team_idx'] == team_idx]
        team_hulls = sorted(team_hulls, key=lambda x: x['area'], reverse=True)[:3]
        
        x_base = 0.04 + team_idx * 0.67
        
        for i, hull in enumerate(team_hulls):
            y_pos = 0.71 - i * 0.22
            
            # Nombre corto
            name = hull['player']
            if len(name.split()) > 1:
                short_name = f"{name.split()[0][0]}. {name.split()[-1]}"
            else:
                short_name = name
            
            if len(short_name) >= 15:
                short_name = short_name[:16] + '...'
            
            stats_ax.text(x_base, y_pos, f"{i+1}.     {short_name}", color='w')
            stats_ax.text(x_base + 0.24, y_pos, f"{hull['area_pct']:.1f}%", color='w')
    
    # Labels y flechas como el original
    stats_ax.plot([0.38, 0.38], [0.22, 0.87], lw=0.5, color='w')
    stats_ax.plot([0.62, 0.62], [0.22, 0.87], lw=0.5, color='w')
    stats_ax.text(0.5, 0.55, "Top players by area of\nregion containing central\n75% passes (as % of\ntotal pitch area)", 
                 ha='center', va='center', color='w', fontsize=9)
    stats_ax.arrow(0.375, 0.55, -0.05, 0, color="w", width=0.001, head_width=0.05, head_length=0.01, lw=0.5)
    stats_ax.arrow(0.625, 0.55, 0.05, 0, color="w", width=0.001, head_width=0.05, head_length=0.01, lw=0.5)

def add_direction_arrow(fig):
    # Flecha de dirección como el original
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", 
                 fontsize=10, color="w", fontweight="regular", rotation=90)

def plot_pass_hulls(csv_path, home_logo_path=None, away_logo_path=None, season='2024-2025', 
                   central_pct=75, min_passes=5):
    """
    Función wrapper para notebook - detecta automáticamente liga, equipos y fecha
    """
    
    # Detectar archivos
    if csv_path.endswith('.csv'):
        passes_csv = csv_path
        folder_path = os.path.dirname(csv_path)
        positions_csv = os.path.join(folder_path, '3_player_positions.csv')
    else:
        passes_csv = os.path.join(csv_path, '2_passes_complete.csv')
        positions_csv = os.path.join(csv_path, '3_player_positions.csv')
    
    # Detectar equipos del CSV
    passes_df = pd.read_csv(passes_csv)
    successful_passes = passes_df[passes_df['is_successful'] == True]
    teams = successful_passes['team'].unique()
    
    home_team = teams[0]
    away_team = teams[1]
    
    # Detectar liga, temporada y fecha del path
    path_parts = csv_path.replace('\\', '/').split('/')
    
    league = next((part for part in path_parts if '-' in part and any(x in part for x in ['ESP', 'ENG', 'GER', 'ITA', 'FRA', 'INT'])), "Liga")
    season_from_path = next((part for part in path_parts if len(part) == 7 and '-' in part), season)
    folder_name = next((part for part in path_parts if '_' in part and len(part.split('_')[-1]) == 8), "")
    match_date = folder_name.split('_')[-1] if folder_name else "2024-01-01"
    
    if len(match_date) == 8 and match_date.isdigit():
        match_date = f"{match_date[:4]}-{match_date[4:6]}-{match_date[6:8]}"
    
    # Crear visualización
    fig = create_pass_hulls(passes_csv, positions_csv, home_team, away_team, 
                           league, season_from_path, match_date, central_pct, min_passes)
    
    # Agregar logos
    if home_logo_path and os.path.exists(home_logo_path):
        ax_logo = fig.add_axes([0.07, 0.825, 0.14, 0.14])
        ax_logo.axis("off")
        logo = Image.open(home_logo_path)
        ax_logo.imshow(logo)
    
    if away_logo_path and os.path.exists(away_logo_path):
        ax_logo = fig.add_axes([0.79, 0.825, 0.14, 0.14])
        ax_logo.axis("off")
        logo = Image.open(away_logo_path)
        ax_logo.imshow(logo)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)
    return fig