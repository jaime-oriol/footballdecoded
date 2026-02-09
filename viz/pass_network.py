"""
Pass network visualization with dual-team side-by-side comparison.
Nodes sized by completed passes, colored by xThreat per pass.
Connections use gradient transparency and xThreat coloring.
Opta coordinates (0-100) rendered on vertical pitch.
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

BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def calculate_node_size(total_passes: int, max_passes: int, threshold: int = 20) -> float:
    """Linear scale from 5 to 30 based on completed passes (5-100 range)."""
    min_size = 5
    max_size = 30
    
    if total_passes <= 5:
        return min_size
    if total_passes >= 100:
        return max_size
    
    size_range = max_size - min_size
    pass_range = 100 - 5
    return min_size + (total_passes - 5) * (size_range / pass_range)

def calculate_node_size_period(total_passes: int, max_passes: int = 50, threshold: int = 20) -> float:
    """Linear scale from 5 to 30 for half-match data (3-50 pass range)."""
    min_size = 5
    max_size = 30
    
    if total_passes <= 3:
        return min_size
    if total_passes >= 50:
        return max_size
    
    size_range = max_size - min_size
    pass_range = 50 - 3
    return min_size + (total_passes - 3) * (size_range / pass_range)

def calculate_line_width(pass_count: int, min_connections: int, max_connections: int, min_required: int = 5) -> float:
    """Line width by pass count: <=5 thin, 6-9 medium, 10+ thick."""
    if pass_count < min_required:
        return 0.0
    
    if pass_count <= 5:
        return 0.5
    elif pass_count <= 9:
        return 1.5
    else:
        return 2.5

def get_node_radius(marker_size: float) -> float:
    """Convert marker size to geometric radius for overlap calculations."""
    visual_area = marker_size**2
    return np.sqrt(visual_area / np.pi) * 0.32

def calculate_connection_points(x1: float, y1: float, x2: float, y2: float, 
                              r1: float, r2: float, pass_count: int) -> tuple:
    """Offset connection start/end to avoid overlapping with nodes."""
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    ux, uy = dx / length, dy / length
    perp_x, perp_y = -uy, ux

    combined_radius = r1 + r2
    min_safe_distance = combined_radius * 1.2

    if length < min_safe_distance:
        # Overlapping nodes: larger perpendicular offset
        offset = 1.0 * (1 + pass_count / 50)

        start_x = x1 + r1 * 1.2 * ux + perp_x * offset
        start_y = y1 + r1 * 1.2 * uy + perp_y * offset

        end_margin = r2 + 2.5
        end_x = x2 - end_margin * ux + perp_x * offset
        end_y = y2 - end_margin * uy + perp_y * offset

    else:
        # Minimal offset to separate parallel arrows
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
    """Draw arrowhead at the end of a connection line."""
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
    """Format as 'F. Surname', handling particles like 'de', 'van', 'di'."""
    if pd.isna(full_name) or not full_name.strip():
        return "Unknown"
    
    full_name = full_name.strip()
    name_parts = full_name.split()
    
    if len(name_parts) == 1:
        return name_parts[0]
    
    first_initial = name_parts[0][0].upper()
    particles = ['de', 'del', 'da', 'dos', 'van', 'von', 'le', 'la', 'du', 'di', 'el']
    
    # Build surname including particles
    surname_parts = [name_parts[-1]]
    
    for i in range(len(name_parts) - 2, 0, -1):
        if name_parts[i].lower() in particles:
            surname_parts.insert(0, name_parts[i])
        else:
            break
    
    surname = ' '.join(surname_parts)
    
    return f"{first_initial}. {surname}"

def _filter_players_by_period(events_df, aggregates_df, period_type='full', min_minutes=15):
    """Filter players by minimum minutes in a given match period."""
    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
        period_text = "Passes from First Half"
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
        period_text = "Passes from Second Half"
    else:
        period_events = events_df
        period_text = "Passes from Full Match"
    
    period_player_minutes = {}
    for player in aggregates_df['entity_name'].unique():
        player_events = period_events[period_events['player'] == player]
        if len(player_events) > 0:
            period_player_minutes[player] = player_events['minute'].max() - player_events['minute'].min()
        else:
            period_player_minutes[player] = 0
    
    filtered_aggregates = aggregates_df.copy()
    if period_type != 'full':
        valid_players = [p for p, mins in period_player_minutes.items() if mins >= min_minutes]
        filtered_aggregates = filtered_aggregates[filtered_aggregates['entity_name'].isin(valid_players)]
    else:
        filtered_aggregates = filtered_aggregates[filtered_aggregates['minutes_active'] > min_minutes]
    
    return filtered_aggregates, period_events, f"{period_text}. Only players with {min_minutes}+ minutes shown for visual clarity."

def _calculate_period_stats(events_df, player_name, period_type='full'):
    """Return (passes_completed, xthreat_per_pass) for a player in given period."""
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
    """Recalculate player average positions for a specific match period."""
    if period_type == 'full':
        return positions_df

    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
    
    updated_positions = positions_df.copy()

    for (player, team), player_events in period_events.groupby(['player', 'team']):
        if pd.notna(player):
            mask = (
                (updated_positions['source_player'] == player) &
                (updated_positions['team'] == team)
            )
            
            if mask.any():
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
    """Recalculate pass connections for a specific match period."""
    if period_type == 'full':
        return connections_df

    if period_type == 'first_half':
        period_events = events_df[events_df['period'] == 'FirstHalf']
    elif period_type == 'second_half':
        period_events = events_df[events_df['period'] == 'SecondHalf']
    
    passes = period_events[
        (period_events['event_type'] == 'Pass') & 
        (period_events['outcome_type'] == 'Successful') &
        period_events['next_player'].notna()
    ]
    
    updated_connections = connections_df.copy()
    updated_connections['connection_strength'] = 0
    updated_connections['avg_xthreat'] = 0.0
    updated_connections['progressive_passes'] = 0
    updated_connections['box_entries'] = 0
    updated_connections['pass_distance_avg'] = 0.0
    
    for (team, passer, receiver), group in passes.groupby(['team', 'player', 'next_player']):
        if passer != receiver:
            mask = (
                (updated_connections['team'] == team) &
                (updated_connections['source_player'] == passer) &
                (updated_connections['target_player'] == receiver)
            )
            
            if mask.any():
                updated_connections.loc[mask, 'connection_strength'] = len(group)
                updated_connections.loc[mask, 'avg_xthreat'] = round(group['xthreat'].mean(), 4)
                updated_connections.loc[mask, 'progressive_passes'] = int(group['is_progressive'].sum())
                updated_connections.loc[mask, 'box_entries'] = int(group['is_box_entry'].sum())
                updated_connections.loc[mask, 'pass_distance_avg'] = round(group['pass_distance'].mean(), 2)
    
    return updated_connections

def plot_pass_network(network_csv_path, info_csv_path, aggregates_csv_path,
                     home_logo_path=None, away_logo_path=None, 
                     figsize=(6, 6), save_path=None):
    """Generate dual-team pass network with xThreat-colored connections and nodes."""
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    timeline_goals = info_df[
        (info_df['info_category'] == 'timeline') & 
        (info_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(timeline_goals[timeline_goals['team'] == home_team])
    away_goals = len(timeline_goals[timeline_goals['team'] == away_team])
    
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    # Map Opta coords to vertical pitch
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Color normalization ranges
    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08
    min_passes = 6

    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = player_aggregates[player_aggregates['team'] == team].copy()
        
        # Exclude players with <15 minutes
        team_player_data = team_player_data[team_player_data['minutes_active'] > 15].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max()
        
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            player_data = team_player_data[team_player_data['entity_name'] == player_name]
            
            if player_data.empty:
                continue
                
            num_passes = int(player_data.iloc[0]['passes_completed'])
            
            player_passes = events_df[
                (events_df['player'] == player_name) & 
                (events_df['event_type'] == 'Pass') &
                (events_df['outcome_type'] == 'Successful')
            ]
            
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
                
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Alpha gradient: transparent at start, opaque at end
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Direction of play arrow
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    fig.text(x=0.5, y=0.19, s='Passes from minutes 1 to 90 (+ extra time). Only players with 15+ minutes shown for visual clarity.',
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=14, font=font, color='white')
    
    result_y = 0.9
    
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
    
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])  # [x, y, width, height]
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        print(f"Logo load error: {e}")
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Legend
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    fig.text(x=0.13, y=0.07, s="6 to 12+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="5 to 100+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Legend visual elements (pixel coordinates)
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
    
    # Line width legend
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Connection color legend
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Node size legend
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Node color legend
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Saved: {save_path}")
    
    return fig

def plot_pass_network_first_half(network_csv_path, info_csv_path, aggregates_csv_path,
                                 home_logo_path=None, away_logo_path=None, 
                                 figsize=(6, 6), save_path=None):
    """First half pass network (same layout as full match, filtered by period)."""
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    first_half_goals = events_df[
        (events_df['period'] == 'FirstHalf') & 
        (events_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(first_half_goals[first_half_goals['team'] == home_team])
    away_goals = len(first_half_goals[first_half_goals['team'] == away_team])
    
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    filtered_aggregates, period_events, period_text = _filter_players_by_period(
        events_df, player_aggregates, 'first_half', 5
    )
    
    positions_df = _calculate_period_positions(events_df, positions_df, 'first_half')
    
    connections_df = _calculate_period_connections(events_df, connections_df, 'first_half')
    
    # Map Opta coords to vertical pitch
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Color normalization ranges    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08
    min_passes = 4

    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = filtered_aggregates[filtered_aggregates['team'] == team].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max() if not team_player_data.empty else 50
        
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            if player_name not in team_player_data['entity_name'].values:
                continue
            
            passes_completed, xthreat_per_pass = _calculate_period_stats(
                events_df, player_name, 'first_half'
            )
            
            
            marker_size = calculate_node_size_period(passes_completed, max_passes_team)
            node_radius = get_node_radius(marker_size)
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': passes_completed,
                'xthreat_per_pass': xthreat_per_pass
            }
        
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
                
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Alpha gradient: transparent at start, opaque at end
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Direction of play arrow
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    fig.text(x=0.5, y=0.19, s=period_text,
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="1st Half Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=13, font=font, color='white')
    
    result_y = 0.9
    
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
    
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        print(f"Logo load error: {e}")
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Legend
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    fig.text(x=0.13, y=0.07, s="4 to 10+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="3 to 50+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Legend visual elements (pixel coordinates)
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
    
    # Line width legend
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Connection color legend
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Node size legend
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Node color legend
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Saved: {save_path}")
    
    return fig

def plot_pass_network_second_half(network_csv_path, info_csv_path, aggregates_csv_path,
                                  home_logo_path=None, away_logo_path=None, 
                                  figsize=(6, 6), save_path=None):
    """Second half pass network (same layout as full match, filtered by period)."""
    network_df = pd.read_csv(network_csv_path)
    info_df = pd.read_csv(info_csv_path)
    aggregates_df = pd.read_csv(aggregates_csv_path)
    
    events_csv_path = os.path.join(os.path.dirname(network_csv_path), 'match_events.csv')
    events_df = pd.read_csv(events_csv_path)
    
    home_team = info_df[info_df['info_key'] == 'home_team']['info_value'].iloc[0]
    away_team = info_df[info_df['info_key'] == 'away_team']['info_value'].iloc[0]
    match_date = info_df[info_df['info_key'] == 'match_date']['info_value'].iloc[0]
    league = info_df[info_df['info_key'] == 'league']['info_value'].iloc[0]
    season = info_df[info_df['info_key'] == 'season']['info_value'].iloc[0]
    
    second_half_goals = events_df[
        (events_df['period'] == 'SecondHalf') & 
        (events_df['event_type'] == 'Goal')
    ]
    
    home_goals = len(second_half_goals[second_half_goals['team'] == home_team])
    away_goals = len(second_half_goals[second_half_goals['team'] == away_team])
    
    player_aggregates = aggregates_df[aggregates_df['entity_type'] == 'player'].copy()
    positions_df = network_df[network_df['record_type'] == 'position'].copy()
    connections_df = network_df[network_df['record_type'] == 'connection'].copy()
    
    filtered_aggregates, period_events, period_text = _filter_players_by_period(
        events_df, player_aggregates, 'second_half', 5
    )
    
    positions_df = _calculate_period_positions(events_df, positions_df, 'second_half')
    
    connections_df = _calculate_period_connections(events_df, connections_df, 'second_half')
    
    # Map Opta coords to vertical pitch
    positions_df['x_pitch'] = positions_df['avg_y_start']
    positions_df['y_pitch'] = positions_df['avg_x_start']
    
    # Color normalization ranges    min_connection_xt = -0.1
    max_connection_xt = 0.2
    min_player_xt = 0.0
    max_player_xt = 0.08
    min_passes = 4

    plt.style.use('default')
    fig, ax = plt.subplots(1, 2, figsize=figsize, dpi=400, facecolor=BACKGROUND_COLOR)
    
    teams = [home_team, away_team]
    
    connection_norm = Normalize(vmin=min_connection_xt, vmax=max_connection_xt)
    player_norm = Normalize(vmin=min_player_xt, vmax=max_player_xt)
    
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    for i, team in enumerate(teams):
        ax[i].set_facecolor(BACKGROUND_COLOR)
        
        pitch = VerticalPitch(pitch_type='opta', 
                             pitch_color=PITCH_COLOR,
                             line_color='white',
                             linewidth=1, 
                             pad_bottom=4)
        pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
        
        team_positions = positions_df[positions_df['team'] == team].copy()
        team_connections = connections_df[connections_df['team'] == team].copy()
        team_player_data = filtered_aggregates[filtered_aggregates['team'] == team].copy()
        
        if team_positions.empty or team_player_data.empty:
            continue
        
        max_passes_team = team_player_data['passes_completed'].max() if not team_player_data.empty else 50
        
        player_stats = {}
        
        for _, player in team_positions.iterrows():
            x = player['x_pitch']
            y = player['y_pitch']
            player_name = player['source_player']
            
            if player_name not in team_player_data['entity_name'].values:
                continue
            
            passes_completed, xthreat_per_pass = _calculate_period_stats(
                events_df, player_name, 'second_half'
            )
            
            
            marker_size = calculate_node_size_period(passes_completed, max_passes_team)
            node_radius = get_node_radius(marker_size)
            
            player_stats[player_name] = {
                'x': x, 'y': y, 
                'radius': node_radius, 
                'marker_size': marker_size,
                'passes': passes_completed,
                'xthreat_per_pass': xthreat_per_pass
            }
        
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
                
                start_x, start_y, end_x, end_y = calculate_connection_points(
                    source['x'], source['y'], target['x'], target['y'],
                    source['radius'], target['radius'], num_passes
                )
                
                line_width = calculate_line_width(num_passes, min_conn, max_conn, min_passes)
                edge_color = node_cmap(connection_norm(pass_value))
                
                num_points = 75
                x_points = np.linspace(start_x, end_x, num_points)
                y_points = np.linspace(start_y, end_y, num_points)
                
                points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # Alpha gradient: transparent at start, opaque at end
                alphas = np.linspace(0.1, 1.0, len(segments))
                rgb = mcolors.to_rgb(edge_color)
                colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
                
                lc = LineCollection(segments, colors=colors_with_alpha, 
                                   linewidths=line_width, capstyle='round', zorder=1)
                ax[i].add_collection(lc)
                
                draw_arrow(ax[i], start_x, start_y, end_x, end_y, edge_color, line_width)
        
        for player_name, stats in player_stats.items():
            x, y = stats['x'], stats['y']
            marker_size = stats['marker_size']
            pass_value = stats['xthreat_per_pass']
            
            node_color = node_cmap(player_norm(pass_value))
                        
            ax[i].scatter(x, y, s=marker_size**2, c=node_color, alpha=0.3, 
                        edgecolors='none', zorder=5)

            ax[i].scatter(x, y, s=marker_size**2, facecolors='none', 
                        edgecolors=node_color, linewidth=1, zorder=6)
            
            display_name = format_player_name(player_name)
            ax[i].text(x, y, display_name, ha='center', va='center',
                      color='white', fontsize=5, fontweight='bold',
                      family='serif',
                      path_effects=[
                          path_effects.Stroke(linewidth=1.5, foreground='black'),
                          path_effects.Normal()
                      ], zorder=7)
    
    # Direction of play arrow
    arrow_ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    arrow_ax.set_xlim(0, 1)
    arrow_ax.set_ylim(0, 1)
    arrow_ax.axis("off")
    arrow_ax.arrow(0.55, 0.45, 0, 0.3, color="w", width=0.001, head_width=0.1, head_length=0.02)
    arrow_ax.text(0.35, 0.6, "Direction of play", ha="center", va="center", fontsize=7, font = 'serif', color="w", fontweight="regular", rotation=90)
    
    fig.text(x=0.5, y=0.19, s=period_text,
             ha='center', va='center', color='white', fontsize=7, fontfamily='DejaVu Sans')
    
    font = 'DejaVu Sans'
    
    fig.text(x=0.5, y=.93, s="2nd Half Pass Network",
            weight='bold', va="bottom", ha="center", fontsize=13, font=font, color='white')
    
    result_y = 0.9
    
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
    
    fig.text(x=0.5, y=result_y, s=f"{home_team} {home_goals} - {away_goals} {away_team}",
            weight='regular', va="bottom", ha="center", fontsize=10, font=font, color='white')
    
    fig.text(x=0.5, y=0.875, s=f"{league} | Season {season} | {match_date}",
            va="bottom", ha="center", fontsize=8, font=font, color='white')
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.675, -0.05, 0.32, 0.12])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        print(f"Logo load error: {e}")
        fig.text(x=0.87, y=-0.0, s="Football Decoded", va="bottom", ha="center", 
                weight='bold', fontsize=12, font=font, color='white')
    fig.text(x=0.14, y=-0.015, s="Created by Jaime Oriol", va="bottom", ha="center", 
            weight='bold', fontsize=6, font=font, color='white')
    
    # Legend
    fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.84, y=.14, s="Player value per pass (xT)", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    fig.text(x=0.13, y=0.07, s="4 to 10+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.37, y=0.07, s="-0.1 to 0.2+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.61, y=0.07, s="3 to 50+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    fig.text(x=0.84, y=0.07, s="0 to 0.08+", va="bottom", ha="center",
            fontsize=5, font=font, color='white')
    
    fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center",
            fontsize=6, font=font, color='white')
    
    # Legend visual elements (pixel coordinates)
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
    
    # Line width legend
    arrow1 = FancyArrowPatch((x0, y0), (x0+dx, y0+dy), lw=0.5, arrowstyle=style, color='white')
    arrow2 = FancyArrowPatch((x0+shift_x, y0), (x0+dx+shift_x, y0+dy), lw=1.5, arrowstyle=style, color='white')
    arrow3 = FancyArrowPatch((x0+2*shift_x, y0), (x0+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color='white')
    
    # Connection color legend
    colors_legend = [node_cmap(i/4) for i in range(5)]
    
    arrow4 = FancyArrowPatch((x1, y0), (x1+dx, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[0])
    arrow5 = FancyArrowPatch((x1+shift_x, y0), (x1+dx+shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[1])
    arrow6 = FancyArrowPatch((x1+2*shift_x, y0), (x1+dx+2*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[2])
    arrow7 = FancyArrowPatch((x1+3*shift_x, y0), (x1+dx+3*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[3])
    arrow8 = FancyArrowPatch((x1+4*shift_x, y0), (x1+dx+4*shift_x, y0+dy), lw=2.5, arrowstyle=style, color=colors_legend[4])
    
    # Node size legend
    circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='white', fill=False)
    circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='white', fill=False)
    circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='white', fill=False)
    
    # Node color legend
    for idx, (x_pos, color) in enumerate([
        (x3, colors_legend[0]),
        (x3+shift_x3, colors_legend[1]),
        (x3+2*shift_x3, colors_legend[2]),
        (x3+3*shift_x3, colors_legend[3]),
        (x3+4*shift_x3, colors_legend[4])
    ]):
        inner_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                            color=color, alpha=0.3, zorder=10)
        fig.patches.append(inner_circle)
        
        border_circle = Circle(xy=(x_pos, y2), radius=radius*2, 
                             color=color, fill=False, linewidth=1, zorder=11)
        fig.patches.append(border_circle)
    
    arrow9 = FancyArrowPatch((x4, y4), (x4+550, y4), lw=1, arrowstyle=style, color='white')
    
    fig.patches.extend([arrow1, arrow2, arrow3, arrow4, arrow5, arrow6, arrow7, arrow8,
                       circle1, circle2, circle3, arrow9])
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)
    
    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=400, facecolor=BACKGROUND_COLOR)
        print(f"Saved: {save_path}")
    
    return fig