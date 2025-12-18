"""
FootballDecoded Pass Network Visualization Module
=================================================

Advanced pass network visualization system for tactical analysis. Creates sophisticated
network diagrams showing player connections, positioning, and passing relationships.

Key Features:
- Dual-team pass network visualization with side-by-side comparison
- Node sizing based on pass completion volume
- Connection strength visualization with gradient transparency
- xThreat-based color coding for pass value assessment  
- Geometric arrow positioning to avoid node overlap
- Player name formatting with particle handling
- Comprehensive legend system with visual scaling guides

Technical Implementation:
- Advanced coordinate geometry for connection positioning
- LineCollection with alpha gradients for visual depth
- Regular grid interpolator for smooth xThreat calculation
- Dynamic node radius calculation for overlap prevention
- Multi-level legend system (thickness, color, size, value)

Visual Design:
- Unified colormap system across FootballDecoded modules
- Professional sports visualization aesthetics
- Team logo integration and match metadata display
- Comprehensive scaling legends for data interpretation

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project  
Coordinate System: Opta (0-100) with vertical pitch orientation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch, Circle, ArrowStyle
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
from PIL import Image
import os
import warnings
warnings.filterwarnings('ignore')

# Configuración visual global
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def calculate_node_size(total_passes: int, max_passes: int, threshold: int = 20) -> float:
    """
    Calculate node size based on completed passes with logarithmic scaling.
    
    Uses adaptive scaling to ensure visual distinction between players
    while maintaining readability. Prevents oversized nodes while
    emphasizing high-volume passers.
    
    Scaling Logic:
    - Minimum size: 5 points (low activity players)
    - Maximum size: 30 points (high activity players)  
    - Linear scaling between 5-100 completed passes
    - Threshold cutoff prevents extreme node sizes
    
    Args:
        total_passes: Player's completed pass count
        max_passes: Maximum passes by any player (unused, kept for compatibility)
        threshold: Minimum passes for size calculation (unused)
        
    Returns:
        Node size in points (5.0 to 30.0)
        
    Note:
        Size calculation is independent of team maximum for consistent scaling
        Linear interpolation provides intuitive size-to-activity relationship
    """
    min_size = 5
    max_size = 30
    
    if total_passes <= 5:
        return min_size
    if total_passes >= 100:
        return max_size
    
    # Escalado lineal entre 5 y 100 pases
    size_range = max_size - min_size  
    pass_range = 100 - 5             
    increment_per_pass = size_range / pass_range  
    
    return min_size + (total_passes - 5) * increment_per_pass

def calculate_node_size_period(total_passes: int, max_passes: int = 50, threshold: int = 20) -> float:
    """
    Calculate node size for period visualizations (first/second half).
    
    Adjusted scaling for 45-minute periods where typical maximum is ~50 passes
    instead of 100+ passes in full matches.
    
    Scaling Logic:
    - Minimum size: 5 points (low activity players)
    - Maximum size: 30 points (high activity players)  
    - Linear scaling between 3-50 completed passes
    - Better visual distribution for period data
    
    Args:
        total_passes: Player's completed pass count in period
        max_passes: Expected maximum for period (default 50)
        threshold: Minimum passes for size calculation (unused)
        
    Returns:
        Node size in points (5.0 to 30.0)
    """
    min_size = 5
    max_size = 30
    
    if total_passes <= 3:
        return min_size
    if total_passes >= 50:
        return max_size
    
    # Escalado lineal entre 3 y 50 pases (ajustado para períodos)
    size_range = max_size - min_size  
    pass_range = 50 - 3             
    increment_per_pass = size_range / pass_range  
    
    return min_size + (total_passes - 3) * increment_per_pass

def calculate_line_width(pass_count: int, min_connections: int, max_connections: int, min_required: int = 5) -> float:
    """Grosor de línea según número de pases: 3-5 (fino), 5-9 (medio), 9+ (grueso)."""
    if pass_count < min_required:
        return 0.0
    
    if pass_count <= 5:
        return 0.5
    elif pass_count <= 9:
        return 1.5
    else:
        return 2.5

def get_node_radius(marker_size: float) -> float:
    """Convierte tamaño de marcador a radio real para cálculos geométricos."""
    visual_area = marker_size**2
    return np.sqrt(visual_area / np.pi) * 0.32

def calculate_connection_points(x1: float, y1: float, x2: float, y2: float, 
                              r1: float, r2: float, pass_count: int) -> tuple:
    """
    Calcula puntos de inicio/fin de conexiones evitando solapamiento con nodos.
    Las flechas salen del borde del nodo origen y terminan antes del nodo destino.
    """
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    # Vector unitario y perpendicular
    ux, uy = dx / length, dy / length
    perp_x, perp_y = -uy, ux
    
    # Umbral para considerar nodos muy cercanos
    combined_radius = r1 + r2
    min_safe_distance = combined_radius * 1.2
    
    if length < min_safe_distance:
        # Nodos superpuestos: mayor offset
        offset = 1.0 * (1 + pass_count / 50)
        
        start_x = x1 + r1 * 1.2 * ux + perp_x * offset
        start_y = y1 + r1 * 1.2 * uy + perp_y * offset
        
        end_margin = r2 + 2.5
        end_x = x2 - end_margin * ux + perp_x * offset
        end_y = y2 - end_margin * uy + perp_y * offset
        
    else:
        # Comportamiento normal: offset mínimo para separar flechas paralelas
        min_offset = 0.75
        offset = min_offset + 0.2 * (pass_count / 100)
        
        start_x = x1 + r1 * 1.2 * ux + perp_x * offset
        start_y = y1 + r1 * 1.2 * uy + perp_y * offset
        
        end_margin = r2 + 2.4
        end_x = x2 - end_margin * ux + perp_x * offset
        end_y = y2 - end_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def draw_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
               color: str, line_width: float):
    """Dibuja punta de flecha al final de cada conexión."""
    dx, dy = end_x - start_x, end_y - start_y
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return
    
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    
    size = max(0.6, line_width * 0.25)
    extension = size * 0.05
    tip_x = end_x + extension * ux
    tip_y = end_y + extension * uy
    
    origin_x = tip_x - size * 1.0 * ux + size * 0.7 * px
    origin_y = tip_y - size * 1.0 * uy + size * 0.7 * py
    
    ax.plot([tip_x, origin_x], [tip_y, origin_y], 
           color=color, linewidth=max(1.8, line_width * 0.7), 
           alpha=1.0, solid_capstyle='round', zorder=100)

def format_player_name(full_name: str) -> str:
    """Formatea nombres: Inicial + Apellido (maneja partículas como 'de', 'van')."""
    if pd.isna(full_name) or not full_name.strip():
        return "Unknown"
    
    full_name = full_name.strip()
    name_parts = full_name.split()
    
    if len(name_parts) == 1:
        return name_parts[0]
    
    first_initial = name_parts[0][0].upper()
    particles = ['de', 'del', 'da', 'dos', 'van', 'von', 'le', 'la', 'du', 'di', 'el']
    
    # Construir apellido incluyendo partículas
    surname_parts = [name_parts[-1]]
    
    for i in range(len(name_parts) - 2, 0, -1):
        if name_parts[i].lower() in particles:
            surname_parts.insert(0, name_parts[i])
        else:
            break
    
    surname = ' '.join(surname_parts)
    
    return f"{first_initial}. {surname}"

def _filter_players_by_period(events_df, aggregates_df, period_type='full', min_minutes=15):
    """
    Helper function to filter players based on activity in specific periods.
    
    Args:
        events_df: Match events dataframe  
        aggregates_df: Player aggregates dataframe
        period_type: 'full', 'first_half', 'second_half'
        min_minutes: Minimum minutes threshold
    """
    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
        period_text = "Passes from First Half"
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
        period_text = "Passes from Second Half"
    else:
        period_events = events_df
        period_text = "Passes from Full Match"
    
    # Calculate period-specific minutes for each player
    period_player_minutes = {}
    for player in aggregates_df['entity_name'].unique():
        player_events = period_events[period_events['player'] == player]
        if len(player_events) > 0:
            period_player_minutes[player] = player_events['minute'].max() - player_events['minute'].min()
        else:
            period_player_minutes[player] = 0
    
    # Filter players based on period activity
    filtered_aggregates = aggregates_df.copy()
    if period_type != 'full':
        valid_players = [p for p, mins in period_player_minutes.items() if mins >= min_minutes]
        filtered_aggregates = filtered_aggregates[filtered_aggregates['entity_name'].isin(valid_players)]
    else:
        filtered_aggregates = filtered_aggregates[filtered_aggregates['minutes_active'] > min_minutes]
    
    return filtered_aggregates, period_events, f"{period_text}. Only players with {min_minutes}+ minutes shown for visual clarity."

def _calculate_period_stats(events_df, player_name, period_type='full'):
    """
    Calculate player statistics for specific period.
    """
    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
    else:
        period_events = events_df
    
    player_passes = period_events[
        (period_events['player'] == player_name) & 
        (period_events['event_type'] == 'Pass') &
        (period_events['outcome_type'] == 'Successful')
    ]
    
    if len(player_passes) == 0:
        return 0, 0.0
        
    passes_completed = len(player_passes)
    xthreat_per_pass = player_passes['xthreat_gen'].sum() / max(1, len(player_passes))
    
    return passes_completed, xthreat_per_pass

def _calculate_period_positions(events_df, positions_df, period_type='full'):
    """
    Calculate positions exactly like match_data.py but for specific period.
    
    Replicates _build_player_network_optimized() position logic with period filtering.
    
    Args:
        events_df: Match events dataframe 
        positions_df: Original positions dataframe (structure template)
        period_type: 'first_half', 'second_half', or 'full'
        
    Returns:
        Updated positions_df with period-specific data using exact match_data.py logic
    """
    if period_type == 'full':
        return positions_df  # No changes for full match
        
    # Filter events for the period - using period column
    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
    
    # Create copy to avoid modifying original
    updated_positions = positions_df.copy()
    
    # EXACT same grouping and calculation as match_data.py line 826-848
    for (player, team), player_events in period_events.groupby(['player', 'team']):
        if pd.notna(player):
            # Find the corresponding position in updated_positions
            mask = (
                (updated_positions['source_player'] == player) &
                (updated_positions['team'] == team)
            )
            
            if mask.any():
                # Update with EXACT same calculations as match_data.py
                updated_positions.loc[mask, 'avg_x_start'] = round(player_events['x'].mean(), 2)
                updated_positions.loc[mask, 'avg_y_start'] = round(player_events['y'].mean(), 2)
                updated_positions.loc[mask, 'avg_xthreat'] = round(player_events['xthreat_gen'].mean(), 4)
                updated_positions.loc[mask, 'total_actions'] = len(player_events)
                updated_positions.loc[mask, 'minutes_active'] = round(player_events['minute'].max() - player_events['minute'].min(), 1)
                updated_positions.loc[mask, 'position_variance_x'] = round(player_events['x'].std(), 2)
                updated_positions.loc[mask, 'position_variance_y'] = round(player_events['y'].std(), 2)
                updated_positions.loc[mask, 'xthreat_total'] = round(player_events['xthreat_gen'].sum(), 4)
    
    return updated_positions

def _calculate_period_connections(events_df, connections_df, period_type='full'):
    """
    Recalculate connections exactly like match_data.py but for specific period.
    
    Replicates _build_player_network_optimized() logic with period filtering.
    
    Args:
        events_df: Match events dataframe 
        connections_df: Original connections dataframe (structure template)
        period_type: 'first_half', 'second_half', or 'full'
        
    Returns:
        Updated connections_df with period-specific data using exact match_data.py logic
    """
    if period_type == 'full':
        return connections_df  # No changes for full match
    
    # Filter events for the period - using period column
    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
    
    # EXACT same pass filtering as match_data.py line 800-804
    passes = period_events[
        (period_events['event_type'] == 'Pass') & 
        (period_events['outcome_type'] == 'Successful') &
        period_events['next_player'].notna()
    ]
    
    # Create copy to avoid modifying original
    updated_connections = connections_df.copy()
    updated_connections['connection_strength'] = 0
    updated_connections['avg_xthreat'] = 0.0
    updated_connections['progressive_passes'] = 0
    updated_connections['box_entries'] = 0
    updated_connections['pass_distance_avg'] = 0.0
    
    # EXACT same grouping and calculation as match_data.py line 806-823
    for (team, passer, receiver), group in passes.groupby(['team', 'player', 'next_player']):
        if passer != receiver:
            # Find the corresponding connection in updated_connections
            mask = (
                (updated_connections['team'] == team) &
                (updated_connections['source_player'] == passer) &
                (updated_connections['target_player'] == receiver)
            )
            
            if mask.any():
                # Update with EXACT same calculations as match_data.py
                updated_connections.loc[mask, 'connection_strength'] = len(group)
                updated_connections.loc[mask, 'avg_xthreat'] = round(group['xthreat'].mean(), 4)
                updated_connections.loc[mask, 'progressive_passes'] = int(group['is_progressive'].sum())
                updated_connections.loc[mask, 'box_entries'] = int(group['is_box_entry'].sum())
                updated_connections.loc[mask, 'pass_distance_avg'] = round(group['pass_distance'].mean(), 2)
    
    return updated_connections

def plot_pass_network(network_csv_path, info_csv_path, aggregates_csv_path,
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(6, 6), save_path=None):
    """
    Genera visualización de red de pases con ambos equipos lado a lado.
    
    Estructura:
    1. Campo vertical para cada equipo
    2. Conexiones coloreadas por xThreat
    3. Nodos dimensionados por pases completados
    4. Gradiente de transparencia en conexiones
    """
    
    # Cargar datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    # CORRECTED: Load events data for accurate xThreat per pass calculation
    # This fixes the xThreat calculation that was using aggregated data
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    # Extraer metadata del partido
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
    
    # Separar datos
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # Transformar coordenadas Opta a campo vertical
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Rangos para normalización de colores
    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08  # Ajustado para xT per pass
    min_passes = 6

    # Configurar figura
    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    # Configurar mapas de color
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Procesar cada equipo
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        # Dibujar campo
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        # Filtrar datos del equipo
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = player_aggregates[player_aggregates['team'] == team].copy()
        
        # FILTRAR JUGADORES CON MENOS DE 15 MINUTOS
        team_player_data = team_player_data[team_player_data['minutes_active'] > 15].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max()
        
        # Procesar estadísticas de jugadores
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            player_data = team_player_data[team_player_data['entity_name'] == player_name]
            
            if player_data.empty:
                continue
                
            num_passes = int(player_data.iloc[0]['passes_completed'])
            
            # CORRECTED: Accurate xThreat per pass using raw match events
            # Previous calculation used aggregated data which was less precise
            player_passes = events_df[
                (events_df['player'] == player_name) & 
                (events_df['event_type'] == 'Pass') &
                (events_df['outcome_type'] == 'Successful')
            ]
            
            # Calculate true xThreat per pass from individual pass events
            xthreat_per_pass = player_passes['xthreat_gen'].sum() / max(1, len(player_passes))
            
            marker_size = calculate_node_size(num_passes, max_passes_team)
            node_radius = get_node_radius(marker_size)
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': num_passes,
                'xthreat_per_pass': xthreat_per_pass
            }
        
        # Dibujar conexiones
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        if not valid_connections.empty:
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
                
                # Calcular puntos evitando solapamiento
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                # Crear línea con gradiente de transparencia
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Gradiente: transparente al inicio, opaco al final
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        # Dibujar nodos de jugadores
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            # Círculo interior transparente
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            # Borde nítido
            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            # Nombre del jugador
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Flecha de dirección de juego
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    # Textos y títulos
    fig.text(x=0.5, y=0.19, s='Passes from minutes 1 to 90 (+ extra time). Only players with 15+ minutes shown for visual clarity.',
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.9
    
    # Logos de equipos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.20, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.69, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Resultado
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    # Metadata
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    # Logo Football Decoded
    try:
        # Obtener la ruta del directorio del proyecto
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])  # [x, y, width, height]
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        print(f"Error cargando logo: {e}")  # Para debug
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Títulos de leyenda
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Valores de leyenda
    fig.text(x=0.13, y=0.07, s="6 to 12+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="5 to 100+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    # Indicadores de escala
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Elementos visuales de leyenda
    x0 = 195
    y0 = 370
    dx = 60
    dy = 120
    shift_x = 70
    
    x1 = 710
    x2 = 1370
    y2 = 430
    shift_x2 = 70
    radius = 20
    
    x3 = 1810
    shift_x3 = 100
    
    x4 = 930
    y4 = 220
    
    style = ArrowStyle('->', head_length=5, head_width=3)
    
    # Leyenda de grosor de líneas
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Leyenda de colores de conexiones
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Leyenda de tamaños de nodos
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Leyenda de colores de nodos
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        # Interior transparente
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        # Borde nítido
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    # Flecha de escala
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Visualización guardada en: {save_path}")
    
    return fig

def plot_pass_network_first_half(network_csv_path, info_csv_path, aggregates_csv_path,
                                 home_logo_path=None, away_logo_path=None, 
                                 figsize=(6, 6), save_path=None):
    """
    Genera visualización de red de pases para el primer tiempo (minutos 1-44).
    Usa la misma implementación visual que plot_pass_network() pero filtra por período.
    """
    # Cargar datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    # Extraer metadata del partido
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Calcular resultado del primer tiempo
    first_half_goals = events_df[
        (events_df['period'] == 'FirstHalf') & 
        (events_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(first_half_goals[first_half_goals['team'] == home_team])
    away_goals = len(first_half_goals[first_half_goals['team'] == away_team])
    
    # Separar datos
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # Aplicar filtro de período
    filtered_aggregates, period_events, period_text = _filter_players_by_period(
        events_df, player_aggregates, 'first_half', 5
    )
    
    # Recalcular posiciones para el primer tiempo
    positions_df = _calculate_period_positions(events_df, positions_df, 'first_half')
    
    # Recalcular conexiones para el primer tiempo
    connections_df = _calculate_period_connections(events_df, connections_df, 'first_half')
    
    # Transformar coordenadas Opta a campo vertical
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Rangos para normalización de colores (IDÉNTICOS AL ORIGINAL)
    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08
    min_passes = 4  # Reducido para primer tiempo

    # Configurar figura
    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    # Configurar mapas de color
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Procesar cada equipo
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        # Dibujar campo
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        # Filtrar datos del equipo
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = filtered_aggregates[filtered_aggregates['team'] == team].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max() if not team_player_data.empty else 50
        
        # Procesar estadísticas de jugadores (LÓGICA EXACTA DEL ORIGINAL)
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            if player_name not in team_player_data['entity_name'].values:
                continue
            
            # Calcular stats específicas del primer tiempo
            passes_completed, xthreat_per_pass = _calculate_period_stats(
                events_df, player_name, 'first_half'
            )
            
            # No filtrar por pases aquí - solo mostrar jugadores con minutos suficientes
            
            marker_size = calculate_node_size_period(passes_completed, max_passes_team)
            node_radius = get_node_radius(marker_size)
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': passes_completed,
                'xthreat_per_pass': xthreat_per_pass
            }
        
        # Dibujar conexiones (LÓGICA EXACTA DEL ORIGINAL)
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        if not valid_connections.empty:
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
                
                # Calcular puntos evitando solapamiento
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                # Crear línea con gradiente de transparencia
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Gradiente: transparente al inicio, opaco al final
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        # Dibujar nodos de jugadores (LÓGICA EXACTA DEL ORIGINAL)
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            # Círculo interior transparente
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            # Borde nítido
            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            # Nombre del jugador
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Flecha de dirección de juego
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    # Textos y títulos
    fig.text(x=0.5, y=0.19, s=period_text,
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="1st Half Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=13, font=font, color='white')
    
    result_y = 0.9
    
    # Logos de equipos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.20, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.69, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Resultado
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    # Metadata
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    # Logo Football Decoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        print(f"Error cargando logo: {e}")
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Títulos de leyenda
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Valores de leyenda
    fig.text(x=0.13, y=0.07, s="4 to 10+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="3 to 50+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    # Indicadores de escala
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Elementos visuales de leyenda
    x0 = 195
    y0 = 370
    dx = 60
    dy = 120
    shift_x = 70
    
    x1 = 710
    x2 = 1370
    y2 = 430
    shift_x2 = 70
    radius = 20
    
    x3 = 1810
    shift_x3 = 100
    
    x4 = 930
    y4 = 220
    
    style = ArrowStyle('->', head_length=5, head_width=3)
    
    # Leyenda de grosor de líneas
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Leyenda de colores de conexiones
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Leyenda de tamaños de nodos
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Leyenda de colores de nodos
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        # Interior transparente
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        # Borde nítido
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    # Flecha de escala
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Visualización primer tiempo guardada en: {save_path}")
    
    return fig

def plot_pass_network_second_half(network_csv_path, info_csv_path, aggregates_csv_path,
                                  home_logo_path=None, away_logo_path=None, 
                                  figsize=(6, 6), save_path=None):
    """
    Genera visualización de red de pases para el segundo tiempo (minutos 46-90).
    Usa la misma implementación visual que plot_pass_network() pero filtra por período.
    """
    # Cargar datos
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    # Extraer metadata del partido
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    # Calcular resultado del segundo tiempo
    second_half_goals = events_df[
        (events_df['period'] == 'SecondHalf') & 
        (events_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(second_half_goals[second_half_goals['team'] == home_team])
    away_goals = len(second_half_goals[second_half_goals['team'] == away_team])
    
    # Separar datos
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # Aplicar filtro de período
    filtered_aggregates, period_events, period_text = _filter_players_by_period(
        events_df, player_aggregates, 'second_half', 5
    )
    
    # Recalcular posiciones para el segundo tiempo
    positions_df = _calculate_period_positions(events_df, positions_df, 'second_half')
    
    # Recalcular conexiones para el segundo tiempo
    connections_df = _calculate_period_connections(events_df, connections_df, 'second_half')
    
    # Transformar coordenadas Opta a campo vertical
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Rangos para normalización de colores (IDÉNTICOS AL ORIGINAL)
    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08
    min_passes = 4  # Reducido para segundo tiempo

    # Configurar figura
    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    # Configurar mapas de color
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Procesar cada equipo
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        # Dibujar campo
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        # Filtrar datos del equipo
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = filtered_aggregates[filtered_aggregates['team'] == team].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max() if not team_player_data.empty else 50
        
        # Procesar estadísticas de jugadores (LÓGICA EXACTA DEL ORIGINAL)
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            if player_name not in team_player_data['entity_name'].values:
                continue
            
            # Calcular stats específicas del segundo tiempo
            passes_completed, xthreat_per_pass = _calculate_period_stats(
                events_df, player_name, 'second_half'
            )
            
            # No filtrar por pases aquí - solo mostrar jugadores con minutos suficientes
            
            marker_size = calculate_node_size_period(passes_completed, max_passes_team)
            node_radius = get_node_radius(marker_size)
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': passes_completed,
                'xthreat_per_pass': xthreat_per_pass
            }
        
        # Dibujar conexiones (LÓGICA EXACTA DEL ORIGINAL)
        valid_connections = team_connections[team_connections['connection_strength'] >= min_passes].copy()
        
        if not valid_connections.empty:
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
                
                # Calcular puntos evitando solapamiento
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                # Crear línea con gradiente de transparencia
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Gradiente: transparente al inicio, opaco al final
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        # Dibujar nodos de jugadores (LÓGICA EXACTA DEL ORIGINAL)
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            # Círculo interior transparente
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            # Borde nítido
            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            # Nombre del jugador
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Flecha de dirección de juego
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    # Textos y títulos
    fig.text(x=0.5, y=0.19, s=period_text,
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="2nd Half Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=13, font=font, color='white')
    
    result_y = 0.9
    
    # Logos de equipos
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            logo = Image.open(home_logo_path)
            logo_ax = fig.add_axes([0.20, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            logo = Image.open(away_logo_path)
            logo_ax = fig.add_axes([0.69, result_y-0.025, 0.104, 0.104])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Resultado
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    # Metadata
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    # Logo Football Decoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        print(f"Error cargando logo: {e}")
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Títulos de leyenda
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Valores de leyenda
    fig.text(x=0.13, y=0.07, s="4 to 10+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="3 to 50+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    # Indicadores de escala
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Elementos visuales de leyenda
    x0 = 195
    y0 = 370
    dx = 60
    dy = 120
    shift_x = 70
    
    x1 = 710
    x2 = 1370
    y2 = 430
    shift_x2 = 70
    radius = 20
    
    x3 = 1810
    shift_x3 = 100
    
    x4 = 930
    y4 = 220
    
    style = ArrowStyle('->', head_length=5, head_width=3)
    
    # Leyenda de grosor de líneas
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Leyenda de colores de conexiones
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Leyenda de tamaños de nodos
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Leyenda de colores de nodos
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        # Interior transparente
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        # Borde nítido
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    # Flecha de escala
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Visualización segundo tiempo guardada en: {save_path}")
    
    return fig