"""
FootballDecoded Pass Analysis Visualization Module
==================================================

Specialized visualization module for pass flow and spatial analysis. Creates two main visualizations:
1. Pass Flow Analysis - Inter-zone pass frequency and patterns
2. Pass Hull Analysis - Player positioning and spatial distribution

Key Features:
- Custom 19-zone system (jdp_custom) for tactical analysis
- Inter-zone pass flow visualization with dynamic coloring
- Convex hull generation for player positioning analysis
- Color alternation system for visual clarity
- Unified visual design with FootballDecoded branding

Coordinate Systems:
- Opta coordinates (0-100 x 0-100) for data processing
- Custom coordinate transformations for visualization
- Zone-based analysis using percentage-based boundaries

Visual Design:
- Consistent background color (#313332)
- Team-specific color schemes
- Logo integration and match metadata display
- Professional sports visualization standards

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
"""

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

# Global visual configuration - unified with other FootballDecoded modules
BACKGROUND_COLOR = '#313332'  # Dark background for professional appearance
PITCH_COLOR = '#313332'       # Matching pitch color for seamless integration

# ====================================================================
# UTILIDADES COMUNES
# ====================================================================

def get_zone_jdp_custom(x, y):
    """
    Custom 19-zone tactical classification system.
    
    Divides the field into 19 tactical zones based on penalty box boundaries
    and strategic field areas. More granular than standard 18-zone systems.
    
    Zone Layout:
    - Penalty boxes: Zones 0-2 (defensive), 16-18 (attacking)
    - Central areas: Zones 3-15 with varying tactical importance
    - Width divisions based on box_y_ratio (21.1%)
    - Length divisions based on box_x_ratio (17%)
    
    Args:
        x: Horizontal coordinate (0-100, Opta system)
        y: Vertical coordinate (0-100, Opta system)
        
    Returns:
        Zone ID (0-18) or np.nan for invalid coordinates
        
    Note:
        Uses penalty box ratios for realistic tactical boundaries
        Zone numbering follows strategic importance patterns
    """
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
    """Centro de zona en coordenadas Opta originales."""
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
# PASS FLOW VISUALIZATION - CORREGIDO SIGUIENDO PATRÓN ORIGINAL
# ====================================================================

def plot_pass_flow(events_csv_path, info_csv_path, home_colors=['#E23237', '#FFFFFF'], 
                  away_colors=['#004D98', '#A50044'], home_logo_path=None, away_logo_path=None, save_path=None):
    """
    Create pass flow visualization showing inter-zone pass patterns.
    
    Generates dual-pitch visualization showing the most frequent pass
    connections between tactical zones for both teams. Uses dynamic
    coloring based on pass frequency and team colors.
    
    Features:
    - 19-zone tactical system for granular analysis
    - Most frequent inter-zone connections only
    - Dynamic line thickness based on pass frequency
    - Team-specific color schemes with intensity scaling
    - Integrated team logos and match metadata
    
    Args:
        events_csv_path: Path to match_events.csv file
        info_csv_path: Path to match_info.csv file
        home_colors: [primary, secondary] colors for home team
        away_colors: [primary, secondary] colors for away team
        home_logo_path: Optional path to home team logo
        away_logo_path: Optional path to away team logo
        save_path: Optional path to save the visualization
        
    Returns:
        matplotlib Figure object or None if no valid data
        
    Note:
        Filters out self-passes (same zone connections)
        Uses comet-style arrows for directional flow indication
        Color intensity scales with pass frequency (max 15 passes)
    """
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
    
    # Home team siempre a la izquierda
    team_list = [home_team, away_team]
    team_colors = [home_colors, away_colors]
    
    # Crear colormaps dinámicos
    home_cmap = mcolors.LinearSegmentedColormap.from_list("home", [home_colors[0], home_colors[1]])
    away_cmap = mcolors.LinearSegmentedColormap.from_list("away", [away_colors[0], away_colors[1]])
    cmaps = [home_cmap, away_cmap]
    
    # Dibujar flujos - USANDO PATRÓN DEL CÓDIGO ORIGINAL
    for idx, team in enumerate(team_list):
        team_connections = zone_popularity[team]
        
        for start_zone, end_zones in team_connections.items():
            most_common = end_zones.most_common(1)[0]
            end_zone, count = most_common
            
            # Obtener centros de zona
            start_x, start_y = get_zone_center(start_zone)
            end_x, end_y = get_zone_center(end_zone)
            
            color_intensity = min(1.0, max(0.1, count / 15.0))
            color = cmaps[idx](color_intensity)
            
            # SIGUIENDO EL PATRÓN ORIGINAL: pitch.lines usa coordenadas Opta originales
            if idx == 0:  # Home team
                pitch1.lines(start_x, start_y, end_x, end_y, lw=10, comet=True,
                           ax=ax[idx], color=color, transparent=True, alpha=0.3, zorder=count)
            else:  # Away team
                pitch2.lines(start_x, start_y, end_x, end_y, lw=10, comet=True,
                           ax=ax[idx], color=color, transparent=True, alpha=0.3, zorder=count)
            
            # SCATTER USA COORDENADAS INVERTIDAS (y, x)
            ax[idx].scatter(end_y, end_x, s=100, c=[color], zorder=count)
    
    font = 'serif'
    
    # Títulos
    fig.text(x=0.5, y=.93, s="Pass Flow",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.91
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='bold', va="bottom", ha="center", fontsize=11, font=font, color='white')
    
    fig.text(x=0.5, y=0.89, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    fig.text(x=0.5, y=0.87, s="Most Frequent Inter-zone Passes", ha='center',
            fontweight="regular", fontsize=10, color='w', family=font)
    
    # Logos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.23, result_y-0.07, 0.13, 0.13])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.65, result_y-0.07, 0.13, 0.13])
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
    
    # Leyendas con colores dinámicos
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
        text_color =  '#000000'
        
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
# PASS HULL VISUALIZATION - SIGUIENDO PATRÓN ORIGINAL
# ====================================================================

def calculate_player_hull(player_events, min_events=5):
    """
    Calculate convex hull for player's central positioning area.
    
    Uses percentile filtering to focus on the central 50% of player
    positions, providing a more representative view of typical positioning
    rather than being distorted by extreme outlier positions.
    
    Process:
    1. Filter to valid coordinate pairs
    2. Calculate 25th and 75th percentiles for X and Y
    3. Keep only positions within central 50% range
    4. Generate convex hull from filtered positions
    5. Calculate geometric properties
    
    Args:
        player_events: DataFrame with player's events
        min_events: Minimum events required for hull calculation
        
    Returns:
        Dictionary with hull data or None if insufficient data
        
    Fields returned:
        - hull_points: Array of hull vertex coordinates
        - area: Hull area coverage
        - centroid_x/y: Hull geometric center
        
    Note:
        Falls back to all positions if filtering leaves <3 points
        Area calculation uses scipy.spatial.ConvexHull volume property
    """
    if len(player_events) < min_events:
        return None
    
    coordinates = player_events[['x', 'y']].dropna().values
    
    if len(coordinates) < 3:
        return None
    
    try:
        x_coords = coordinates[:, 0]
        y_coords = coordinates[:, 1]
        
        # Calcular percentiles 25% y 75% para mantener 50% central
        x_low, x_high = np.percentile(x_coords, [25, 75])
        y_low, y_high = np.percentile(y_coords, [25, 75])
        
        # Filtrar puntos dentro del 50% central
        mask = (
            (x_coords >= x_low) & (x_coords <= x_high) &
            (y_coords >= y_low) & (y_coords <= y_high)
        )
        filtered_coords = coordinates[mask]
        
        # Si quedan muy pocos puntos, usar todos
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

def assign_colors_by_proximity(all_player_hulls, team_colors):
    """
    Assign colors to player hulls using proximity-based alternation.
    
    Implements intelligent color assignment to maximize visual distinction
    between nearby players. Uses breadth-first search from central players
    to ensure optimal color distribution.
    
    Algorithm:
    1. Calculate distance matrix between all player centroids
    2. Find most central player (closest to field center)
    3. Use BFS to assign alternating colors to nearby players
    4. Prioritize color balance within proximity threshold (30 units)
    5. Fall back to global balance for isolated players
    
    Args:
        all_player_hulls: List of hull dictionaries with team_idx
        team_colors: List of [primary, secondary] colors per team
        
    Modifies:
        Adds 'color' field to each hull dictionary in-place
        
    Note:
        Processes each team separately to maintain team color schemes
        Distance threshold of 30 units defines "nearby" players
        Uses Euclidean distance in Opta coordinate system
    """
    # Process each team separately for color assignment
    for team_idx, team in enumerate(['home', 'away']):
        # Filter to current team's hulls
        team_hulls = [h for h in all_player_hulls if h['team_idx'] == team_idx]
        
        if not team_hulls:
            continue  # Skip if no hulls for this team
            
        # Calculate distance matrix between player centroids
        n_players = len(team_hulls)
        distances = np.zeros((n_players, n_players))  # Symmetric distance matrix
        
        # Populate distance matrix with Euclidean distances
        for i in range(n_players):
            for j in range(i+1, n_players):
                # Calculate Euclidean distance between centroids
                dist = np.sqrt((team_hulls[i]['centroid_x'] - team_hulls[j]['centroid_x'])**2 + 
                             (team_hulls[i]['centroid_y'] - team_hulls[j]['centroid_y'])**2)
                distances[i, j] = distances[j, i] = dist  # Symmetric assignment
        
        # Asignar colores empezando por el jugador más central
        colors_assigned = [-1] * n_players
        color_count = [0, 0]  # Contador para cada color
        
        # Encontrar jugador más central (más cerca del centro del campo)
        center_dists = [np.sqrt((h['centroid_x'] - 50)**2 + (h['centroid_y'] - 50)**2) for h in team_hulls]
        start_idx = np.argmin(center_dists)
        
        # Asignar color inicial al más central
        colors_assigned[start_idx] = 0
        color_count[0] = 1
        
        # BFS para asignar colores
        queue = [start_idx]
        while queue:
            current = queue.pop(0)
            current_color = colors_assigned[current]
            
            # Encontrar vecinos no asignados ordenados por distancia
            neighbors = []
            for i in range(n_players):
                if colors_assigned[i] == -1:
                    neighbors.append((distances[current, i], i))
            
            neighbors.sort()  # Ordenar por distancia
            
            for dist, neighbor_idx in neighbors:
                if colors_assigned[neighbor_idx] == -1:
                    # Verificar colores de vecinos cercanos
                    neighbor_colors = []
                    threshold = 30  # Distancia para considerar "cercano"
                    
                    for j in range(n_players):
                        if j != neighbor_idx and colors_assigned[j] != -1 and distances[neighbor_idx, j] < threshold:
                            neighbor_colors.append(colors_assigned[j])
                    
                    # Elegir color menos usado entre vecinos cercanos
                    if neighbor_colors:
                        color_0_count = neighbor_colors.count(0)
                        color_1_count = neighbor_colors.count(1)
                        
                        if color_0_count < color_1_count:
                            chosen_color = 0
                        elif color_1_count < color_0_count:
                            chosen_color = 1
                        else:
                            # Si hay empate, usar el menos usado globalmente
                            chosen_color = 0 if color_count[0] <= color_count[1] else 1
                    else:
                        # Sin vecinos cercanos, balancear globalmente
                        chosen_color = 0 if color_count[0] <= color_count[1] else 1
                    
                    colors_assigned[neighbor_idx] = chosen_color
                    color_count[chosen_color] += 1
                    queue.append(neighbor_idx)
        
        # Aplicar colores asignados
        for i, hull in enumerate(team_hulls):
            color_idx = colors_assigned[i] if colors_assigned[i] != -1 else 0
            hull['color'] = team_colors[team_idx][color_idx]

def plot_pass_hull(events_csv_path, info_csv_path, aggregates_csv_path, 
                  home_colors=['#E23237', '#FFFFFF'], away_colors=['#004D98', '#A50044'],
                  home_logo_path=None, away_logo_path=None, save_path=None):
    """
    Create player positioning visualization using convex hulls.
    
    Generates dual-pitch visualization showing the central 50% of each
    player's pass positions as convex hulls. Uses intelligent color
    assignment to avoid visual confusion between nearby players.
    
    Features:
    - Convex hulls for central 50% of pass positions
    - Intelligent color alternation for visual clarity
    - Player ranking by hull area coverage
    - Proximity-based color assignment algorithm
    - Team logos and comprehensive metadata display
    
    Args:
        events_csv_path: Path to match_events.csv file
        info_csv_path: Path to match_info.csv file  
        aggregates_csv_path: Path to match_aggregates.csv file
        home_colors: [primary, secondary] colors for home team
        away_colors: [primary, secondary] colors for away team
        home_logo_path: Optional path to home team logo
        away_logo_path: Optional path to away team logo
        save_path: Optional path to save the visualization
        
    Returns:
        matplotlib Figure object or None if no valid data
        
    Note:
        Requires minimum 5 events per player for hull calculation
        Uses percentile filtering (25%-75%) for representative positioning
        Rankings show top 3 players by area coverage per team
    """
    # Cargar datos
    events_df = pd.read_csv(events_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
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
    
    # Home team siempre a la izquierda
    team_list = [home_team, away_team]
    team_colors = [home_colors, away_colors]
    
    # Calcular TODOS los hulls primero
    all_player_hulls = []
    
    for idx, team in enumerate(team_list):
        team_events = valid_events[valid_events['team'] == team]
        players = team_events['player'].unique()
        
        for player in players:
            player_events = team_events[team_events['player'] == player]
            hull_data = calculate_player_hull(player_events)
            
            if hull_data:
                hull_data['player'] = player
                hull_data['team'] = team
                hull_data['team_idx'] = idx
                all_player_hulls.append(hull_data)
    
    # Asignar colores por proximidad
    assign_colors_by_proximity(all_player_hulls, team_colors)
    
    # Ordenar por área para el ranking
    all_player_hulls.sort(key=lambda x: x['area'], reverse=True)
    
    # SIGUIENDO EL PATRÓN ORIGINAL EXACTO
    for idx, team in enumerate(team_list):
        team_hulls = [h for h in all_player_hulls if h['team'] == team]
        
        # Dibujar hulls
        for hull_data in team_hulls:
            player = hull_data['player']
            hull_points = hull_data['hull_points']
            centroid_x, centroid_y = hull_data['centroid_x'], hull_data['centroid_y']
            color = hull_data['color']
            
            # SCATTER: usa (y, x)
            ax[idx].scatter(hull_points[:, 1], hull_points[:, 0], 
                          color=color, s=20, alpha=0.3, zorder=2)
            
            # PITCH.CONVEXHULL: usa (x, y)
            plot_hull = pitch1.convexhull(hull_points[:, 0], hull_points[:, 1]) if idx == 0 else pitch2.convexhull(hull_points[:, 0], hull_points[:, 1])
            
            # PITCH.POLYGON: usa el objeto hull retornado
            if idx == 0:
                pitch1.polygon(plot_hull, ax=ax[idx], facecolor=color, alpha=0.2, capstyle='round', zorder=1)
                pitch1.polygon(plot_hull, ax=ax[idx], edgecolor=color, alpha=0.3, facecolor='none', capstyle='round', zorder=1)
            else:
                pitch2.polygon(plot_hull, ax=ax[idx], facecolor=color, alpha=0.2, capstyle='round', zorder=1)
                pitch2.polygon(plot_hull, ax=ax[idx], edgecolor=color, alpha=0.3, facecolor='none', capstyle='round', zorder=1)
            
            # CENTRO: usa (centro[1], centro[0])
            ax[idx].scatter(centroid_y, centroid_x, marker='H', 
                          color=color, alpha=0.6, s=400, zorder=3)
            ax[idx].scatter(centroid_y, centroid_x, marker='H', 
                          edgecolor=color, facecolor='none', alpha=1, lw=2, s=400, zorder=3)
            
            # Iniciales
            initials = format_player_initials(player)
            text_color = 'k' if color in ['#FFFFFF', '#FFFF00', '#00FFFF', '#90EE90'] else 'w'
            ax[idx].text(centroid_y, centroid_x, initials, 
                        fontsize=8, fontweight='bold', va='center', ha='center', 
                        color=text_color, zorder=4, family='serif')
    
    font = 'serif'
    
    # Títulos
    fig.text(x=0.5, y=.93, s="Pass Hull",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.91
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='bold', va="bottom", ha="center", fontsize=11, font=font, color='white')
    
    fig.text(x=0.5, y=0.895, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    fig.text(x=0.5, y=0.85, s="Variation in start position of player passes.\nCentral 50% of passes shown per player,\nrepresented by a shaded region", ha='center', 
            fontweight="regular", fontsize=8, color='w', family=font)
    
    # Logos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.23, result_y-0.07, 0.13, 0.13])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.65, result_y-0.07, 0.13, 0.13])
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
    
    # Rankings por equipos
    home_hulls = [h for h in all_player_hulls if h['team'] == home_team][:3]
    away_hulls = [h for h in all_player_hulls if h['team'] == away_team][:3]
    
    # Crear axes para la leyenda con líneas
    legend_ax = fig.add_axes([0.05, 0.05, 0.9, 0.12])
    legend_ax.set_xlim(0, 10)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis('off')
    
    ranking_text = "Top players by area of\nregion containing central\n50% passes shown \n(as % of total pitch area)"
    legend_ax.text(5, 0.55, ranking_text, ha='center', va='center', fontsize=9, color='w', family=font)
    
    # Líneas de conexión
    legend_ax.arrow(3.6, 0.5, -0.75, 0, color='w', width=0.005, head_width=0.03, head_length=0.1)
    legend_ax.arrow(6.4, 0.5, 0.75, 0, color='w', width=0.005, head_width=0.03, head_length=0.1)
    
    # Rankings por equipo
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
    
    # Footer
    fig.text(0.87, 0.05, "Football Decoded", va="bottom", ha="center", weight='bold', fontsize=14, family=font, color='white')
    fig.text(0.1, 0.05, "Created by Jaime Oriol", va="bottom", ha="center", weight='bold', fontsize=10, family=font, color='white')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Pass Hull guardado en: {save_path}")
    
    return fig