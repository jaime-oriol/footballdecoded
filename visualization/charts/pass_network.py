# ====================================================================
# FootballDecoded - Pass Network Visualization
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors

from core import (
    draw_pitch, SCALE_CONFIG, CONNECTION_CONFIG, FONT_CONFIG, HALVES_CONFIG,
    optimize_name, save_high_quality
)

# ====================================================================
# SCALING SYSTEM
# ====================================================================

def calculate_node_sizes(players_df: pd.DataFrame, is_full_match: bool = False) -> pd.DataFrame:
    """Calculate dynamic node sizes based on pass count."""
    if players_df.empty:
        return players_df
    
    df_with_sizes = players_df.copy()
    threshold = SCALE_CONFIG['node_threshold_full_match'] if is_full_match else SCALE_CONFIG['node_threshold_halves']
    
    df_with_sizes['node_size'] = df_with_sizes['total_passes'].apply(
        lambda passes: _calculate_node_size(passes, df_with_sizes['total_passes'].max(), threshold)
    )
    return df_with_sizes

def calculate_line_widths(connections_df: pd.DataFrame, is_full_match: bool = False) -> pd.DataFrame:
    """Calculate dynamic line widths based on connection frequency."""
    if connections_df.empty:
        return connections_df
    
    df_with_widths = connections_df.copy()
    min_passes_required = CONNECTION_CONFIG['min_passes_full_match'] if is_full_match else CONNECTION_CONFIG['min_passes_halves']
    
    valid_connections = df_with_widths[df_with_widths['pass_count'] >= min_passes_required]
    
    if valid_connections.empty:
        df_with_widths['line_width'] = 0.0
        return df_with_widths
    
    min_connections = valid_connections['pass_count'].min()
    max_connections = valid_connections['pass_count'].max()
    
    df_with_widths['line_width'] = df_with_widths['pass_count'].apply(
        lambda count: _calculate_line_width(count, min_connections, max_connections, min_passes_required)
    )
    return df_with_widths

def get_node_radius(node_size: float) -> float:
    """Convert node size to radius for calculations."""
    return np.sqrt(node_size / np.pi) * 0.105

def _calculate_node_size(total_passes: int, max_passes: int, threshold: int) -> float:
    """Calculate individual node size with linear scaling."""
    if total_passes <= 10:
        return 400
    if total_passes >= 110:
        return 12400
    
    if total_passes <= 60:
        return 400 + (total_passes - 10) * 80
    else:
        base = 400 + (60 - 10) * 80
        return base + (total_passes - 60) * 160

def _calculate_line_width(pass_count: int, min_connections: int, max_connections: int, min_required: int) -> float:
    """Calculate individual line width with smooth scaling."""
    if pass_count < min_required:
        return 0.0
    
    if max_connections == min_connections:
        return (SCALE_CONFIG['line_width_min'] + SCALE_CONFIG['line_width_max']) / 2
    
    normalized = (pass_count - min_connections) / (max_connections - min_connections)
    curved = normalized ** 0.6
    return SCALE_CONFIG['line_width_min'] + curved * (SCALE_CONFIG['line_width_max'] - SCALE_CONFIG['line_width_min'])

# ====================================================================
# MAIN VISUALIZATION FUNCTIONS
# ====================================================================

def create_pass_network(match_data: Dict[str, pd.DataFrame], 
                       team_name: str,
                       primary_color: str = '#2E4A87',
                       secondary_color: str = '#1A365D',
                       title: Optional[str] = None,
                       show_labels: bool = True,
                       figsize: Tuple[int, int] = (14, 10),
                       save_path: Optional[str] = None) -> plt.Figure:
    """Create complete match pass network visualization."""
    from match_data import filter_team_data
    
    team_data = filter_team_data(match_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No data found for {team_name}")
    
    print(f"Creating pass network for {team_name} (Full match)")
    
    team_players_with_sizes = calculate_node_sizes(team_data['players'], is_full_match=True)
    team_connections_with_widths = calculate_line_widths(team_data['connections'], is_full_match=True)
    
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    draw_pitch(ax)
    
    colors = {'primary': primary_color, 'secondary': secondary_color}
    
    _draw_connections(ax, team_connections_with_widths, team_players_with_sizes, colors['secondary'])
    _draw_players(ax, team_players_with_sizes, colors['primary'])
    
    if show_labels:
        _draw_labels(ax, team_players_with_sizes)
    
    _draw_legend(ax, team_players_with_sizes, team_connections_with_widths, team_name, primary_color)
    
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 68)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig

def create_pass_network_by_halves(match_data: Dict[str, pd.DataFrame], 
                                 team_name: str,
                                 primary_color: str = '#2E4A87',
                                 secondary_color: str = '#1A365D',
                                 save_individual: bool = True,
                                 show_labels: bool = True,
                                 figsize: Tuple[int, int] = (36, 14),
                                 save_path: Optional[str] = None) -> plt.Figure:
    """Create dual visualization showing both halves."""
    print(f"Creating halves analysis for {team_name}")
    
    first_half_data = _process_half_data(match_data, team_name, "first")
    second_half_data = _process_half_data(match_data, team_name, "second")
    
    if first_half_data['players'].empty and second_half_data['players'].empty:
        raise ValueError(f"No data found for {team_name} in either half")
    
    if not first_half_data['players'].empty:
        first_half_data['players'] = calculate_node_sizes(first_half_data['players'], is_full_match=False)
        first_half_data['connections'] = calculate_line_widths(first_half_data['connections'], is_full_match=False)
    
    if not second_half_data['players'].empty:
        second_half_data['players'] = calculate_node_sizes(second_half_data['players'], is_full_match=False)
        second_half_data['connections'] = calculate_line_widths(second_half_data['connections'], is_full_match=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, facecolor='white')
    
    colors = {'primary': primary_color, 'secondary': secondary_color}
    
    _draw_half_visualization(ax1, first_half_data, colors, "Primera Parte", show_labels)
    _draw_half_visualization(ax2, second_half_data, colors, "Segunda Parte", show_labels)
    
    fig.suptitle(f"{team_name} - Evolución Táctica por Partes", 
                fontsize=20, fontweight='bold', y=0.95, family=FONT_CONFIG['family'])
    
    plt.tight_layout()
    
    if save_path:
        dual_path = save_path.replace('.png', '_dual_halves.png')
        fig.savefig(dual_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Saved dual: {dual_path}")
    
    if save_individual:
        _save_individual_halves(first_half_data, second_half_data, team_name, colors, 
                               show_labels, save_path)
    
    return fig

def create_pass_network_single_half(match_data: Dict[str, pd.DataFrame], 
                                   team_name: str,
                                   primary_color: str = '#2E4A87',
                                   secondary_color: str = '#1A365D',
                                   half: str = "first",
                                   title: Optional[str] = None,
                                   show_labels: bool = True,
                                   figsize: Tuple[int, int] = (18, 14),
                                   save_path: Optional[str] = None) -> plt.Figure:
    """Create single half visualization."""
    print(f"Creating pass network for {team_name} ({half} half)")
    
    half_data = _process_half_data(match_data, team_name, half)
    
    if half_data['players'].empty:
        raise ValueError(f"No data found for {team_name} in {half} half")
    
    half_data['players'] = calculate_node_sizes(half_data['players'], is_full_match=False)
    half_data['connections'] = calculate_line_widths(half_data['connections'], is_full_match=False)
    
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    colors = {'primary': primary_color, 'secondary': secondary_color}
    
    part_title = title or f"{team_name} - {'Primera' if half == 'first' else 'Segunda'} Parte"
    
    _draw_half_visualization(ax, half_data, colors, part_title, show_labels)
    
    plt.tight_layout()
    
    if save_path:
        half_suffix = f"_{half}_half"
        half_path = save_path.replace('.png', f'{half_suffix}.png')
        fig.savefig(half_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Saved {half} half: {half_path}")
    
    return fig

# ====================================================================
# DATA PROCESSING
# ====================================================================

def _process_half_data(match_data: Dict[str, pd.DataFrame], team_name: str, half: str) -> Dict[str, pd.DataFrame]:
    """Process data for specific match half."""
    if half == "first":
        min_minute, max_minute = 0, HALVES_CONFIG['first_half_end']
    else:
        min_minute, max_minute = HALVES_CONFIG['second_half_start'], HALVES_CONFIG['match_end']
    
    all_passes = match_data['passes']
    team_passes = all_passes[all_passes['team'] == team_name]
    
    if team_passes.empty:
        return {'passes': pd.DataFrame(), 'players': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    half_passes = team_passes[
        (team_passes['minute'] >= min_minute) & 
        (team_passes['minute'] <= max_minute)
    ].copy()
    
    if half_passes.empty:
        return {'passes': pd.DataFrame(), 'players': pd.DataFrame(), 'connections': pd.DataFrame()}
    
    half_players = _recalculate_players(half_passes)
    half_connections = _recalculate_connections(half_passes)
    
    return {'passes': half_passes, 'players': half_players, 'connections': half_connections}

def _recalculate_players(passes_df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate player statistics from filtered passes."""
    if passes_df.empty:
        return pd.DataFrame()
    
    player_stats = passes_df.groupby(['player', 'team']).agg({
        'field_x': 'mean', 'field_y': 'mean', 'player': 'count'
    }).round(1)
    
    player_stats.columns = ['avg_x', 'avg_y', 'total_passes']
    return player_stats.reset_index()

def _recalculate_connections(passes_df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate connections from filtered passes."""
    if passes_df.empty:
        return pd.DataFrame()
    
    passes_sorted = passes_df.sort_values(['minute', 'second']).reset_index(drop=True)
    connections = []
    
    for i in range(len(passes_sorted) - 1):
        current = passes_sorted.iloc[i]
        next_pass = passes_sorted.iloc[i + 1]
        
        if current['team'] != next_pass['team']:
            continue
        
        time_diff = (next_pass['minute'] * 60 + next_pass['second']) - (current['minute'] * 60 + current['second'])
        
        if 0 < time_diff <= 10:
            connections.append({
                'team': current['team'], 'source': current['player'], 'target': next_pass['player'],
                'source_x': current['field_x'], 'source_y': current['field_y'],
                'target_x': next_pass['field_x'], 'target_y': next_pass['field_y']
            })
    
    if not connections:
        return pd.DataFrame()
    
    connections_df = pd.DataFrame(connections)
    connection_counts = connections_df.groupby(['team', 'source', 'target']).agg({
        'source_x': 'mean', 'source_y': 'mean', 'target_x': 'mean', 'target_y': 'mean', 'team': 'count'
    }).round(1)
    
    connection_counts.columns = ['avg_source_x', 'avg_source_y', 'avg_target_x', 'avg_target_y', 'pass_count']
    return connection_counts.reset_index()

# ====================================================================
# DRAWING FUNCTIONS
# ====================================================================

def _draw_half_visualization(ax, half_data: Dict[str, pd.DataFrame], colors: Dict, title: str, show_labels: bool):
    """Draw complete visualization for match half."""
    draw_pitch(ax)
    
    if not half_data['connections'].empty:
        _draw_connections(ax, half_data['connections'], half_data['players'], colors['secondary'])
    
    if not half_data['players'].empty:
        _draw_players(ax, half_data['players'], colors['primary'])
        
        if show_labels:
            _draw_labels(ax, half_data['players'])
    
    _draw_legend(ax, half_data['players'], half_data['connections'], title.split(' - ')[0], colors['primary'])
    
    ax.text(52.5, 75, title, ha='center', va='center', 
           fontsize=16, fontweight='bold', family=FONT_CONFIG['family'])
    
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 78)
    ax.set_aspect('equal')
    ax.axis('off')

def _draw_players(ax, players_df: pd.DataFrame, color: str):
    """Draw player nodes."""
    if players_df.empty:
        return
    
    for _, player in players_df.iterrows():
        x, y = player['avg_x'], player['avg_y']
        node_size = player['node_size']
        
        ax.scatter(x, y, s=node_size, c=color, alpha=0.5,
                  edgecolors=color, linewidth=4, zorder=10)

def _draw_connections(ax, connections_df: pd.DataFrame, players_df: pd.DataFrame, color: str):
    """Draw pass connections with gradient effect."""
    if connections_df.empty:
        return
    
    valid_connections = connections_df[connections_df['line_width'] > 0]
    if valid_connections.empty:
        return
    
    for _, conn in valid_connections.iterrows():
        source_data = players_df[players_df['player'] == conn['source']]
        target_data = players_df[players_df['player'] == conn['target']]
        
        if source_data.empty or target_data.empty:
            continue
        
        source_player = source_data.iloc[0]
        target_player = target_data.iloc[0]
        
        source_radius = get_node_radius(source_player['node_size'])
        target_radius = get_node_radius(target_player['node_size'])
        
        start_x, start_y, end_x, end_y = _calculate_connection_points(
            source_player['avg_x'], source_player['avg_y'],
            target_player['avg_x'], target_player['avg_y'],
            source_radius, target_radius, conn['pass_count']
        )
        
        line_width = conn['line_width']
        
        num_points = 75
        x_points = np.linspace(start_x, end_x, num_points)
        y_points = np.linspace(start_y, end_y, num_points)
        
        points = np.array([x_points, y_points]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        alphas = np.linspace(0.1, 1.0, len(segments))
        rgb = mcolors.to_rgb(color)
        colors_with_alpha = [(rgb[0], rgb[1], rgb[2], alpha) for alpha in alphas]
        
        lc = LineCollection(segments, colors=colors_with_alpha, linewidths=line_width,
                           capstyle='round', zorder=1)
        ax.add_collection(lc)
        
        _draw_connection_arrow(ax, start_x, start_y, end_x, end_y, color, line_width, 1.0)

def _draw_labels(ax, players_df: pd.DataFrame):
    """Draw optimized player labels."""
    for _, player in players_df.iterrows():
        full_name = player['player']
        x, y = player['avg_x'], player['avg_y']
        
        display_name = optimize_name(full_name)
        
        ax.text(x, y, display_name, ha='center', va='center',
               color='white', fontsize=16, fontweight='bold',
               family=FONT_CONFIG['family'],
               path_effects=[
                   path_effects.Stroke(linewidth=3, foreground='black'),
                   path_effects.Normal()
               ], zorder=15)

def _draw_legend(ax, players_df: pd.DataFrame, connections_df: pd.DataFrame, team_name: str, primary_color: str):
   """Draw enhanced legend with consistent alignment and sizing."""
   legend_y = -9
   text_y = legend_y - 1.5
   
   total_passes = players_df['total_passes'].sum() if not players_df.empty else 0
   ax.text(52.5, text_y, f"Pases: {total_passes}", 
          ha='center', va='center', fontsize=18, fontweight='bold', 
          color=primary_color, family=FONT_CONFIG['family'])
   
   _draw_nodes_legend(ax, 20, legend_y, primary_color, players_df)
   _draw_lines_legend(ax, 80, legend_y, primary_color, connections_df)

def _draw_nodes_legend(ax, x: float, y: float, color: str, players_df: pd.DataFrame):
   """Draw nodes legend."""
   if players_df.empty:
       return
   
   min_passes = players_df['total_passes'].min()
   max_passes = players_df['total_passes'].max()
   threshold = 20 if max_passes > 50 else 10
   
   if min_passes == max_passes:
       node_size = players_df['node_size'].iloc[0] * 0.4
       ax.scatter(x, y + 2, s=node_size, c=color, alpha=0.5, 
                 edgecolors=color, linewidth=2, zorder=10)
       ax.text(x, y - 1.5, f"{int(min_passes)}", ha='center', va='center',
              fontsize=16, fontweight='bold', color='black', 
              family=FONT_CONFIG['family'])
       return
   
   arrow_length = 14
   number_offset = 3
   positions = [x - arrow_length/2 - number_offset, x + arrow_length/2 + number_offset]
   circle_y = y + 4
   text_y = y - 1.5
   display_values = [threshold, max_passes]
   
   for i, (pos, passes) in enumerate(zip(positions, display_values)):
       node_size = _calculate_node_size(int(passes), max_passes, threshold) * 0.4
       ax.scatter(pos, circle_y, s=node_size, c=color, alpha=0.5, 
                 edgecolors=color, linewidth=2, zorder=10)
   
   ax.text(positions[0], text_y, f"≤10", ha='center', va='center',
          fontsize=16, fontweight='bold', color='black', 
          family=FONT_CONFIG['family'])
   
   ax.text(positions[1], text_y, f"{int(max_passes)}", ha='center', va='center',
          fontsize=16, fontweight='bold', color='black', 
          family=FONT_CONFIG['family'])
   
   arrow_start_x = x - arrow_length/2
   arrow_end_x = x + arrow_length/2
   ax.annotate('', xy=(arrow_end_x, text_y), xytext=(arrow_start_x, text_y),
               arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))

def _draw_lines_legend(ax, x: float, y: float, color: str, connections_df: pd.DataFrame):
   """Draw lines legend."""
   if connections_df.empty:
       return
   
   valid_connections = connections_df[connections_df['line_width'] > 0]
   if valid_connections.empty:
       return
   
   min_conn = valid_connections['pass_count'].min()
   max_conn = valid_connections['pass_count'].max()
   min_required = 8 if max_conn > 15 else 4
   
   if min_conn == max_conn:
       line_width = valid_connections['line_width'].iloc[0]
       ax.plot([x - 2, x + 2], [y + 2, y + 2], color=color, 
              linewidth=line_width * 1.5, alpha=0.8, solid_capstyle='round')
       ax.text(x, y - 1.5, f"{int(min_conn)}", ha='center', va='center',
              fontsize=16, fontweight='bold', color='black',
              family=FONT_CONFIG['family'])
       return
   
   arrow_length = 14
   number_offset = 3
   positions = [x - arrow_length/2 - number_offset, x + arrow_length/2 + number_offset]
   line_y = y + 1
   text_y = y - 1.5
   
   ax.plot([positions[0] - 1.5, positions[0] + 1.5], [line_y, line_y], color=color, 
          linewidth=2.5, alpha=0.8, solid_capstyle='round')
   
   thick_width = _calculate_line_width(int(max_conn), min_conn, max_conn, min_required) * 1.5
   ax.plot([positions[1] - 1.5, positions[1] + 1.5], [line_y, line_y], color=color, 
          linewidth=max(thick_width, 5.0), alpha=0.8, solid_capstyle='round')
   
   ax.text(positions[0], text_y, f"≥{min_required}", ha='center', va='center',
          fontsize=16, fontweight='bold', color='black',
          family=FONT_CONFIG['family'])
   
   ax.text(positions[1], text_y, f"{int(max_conn)}", ha='center', va='center',
          fontsize=16, fontweight='bold', color='black',
          family=FONT_CONFIG['family'])
   
   arrow_start_x = x - arrow_length/2
   arrow_end_x = x + arrow_length/2
   ax.annotate('', xy=(arrow_end_x, text_y), xytext=(arrow_start_x, text_y),
               arrowprops=dict(arrowstyle='->', color='black', lw=3, alpha=1))

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _draw_connection_arrow(ax, start_x: float, start_y: float, end_x: float, end_y: float,
                          color: str, line_width: float, alpha: float):
    """Draw directional arrow at connection end."""
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

def _calculate_connection_points(x1: float, y1: float, x2: float, y2: float,
                               r1: float, r2: float, pass_count: int) -> Tuple[float, float, float, float]:
    """Calculate connection start and end points avoiding node overlap."""
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length == 0:
        return x1, y1, x2, y2
    
    ux, uy = dx / length, dy / length
    combined_radius = r1 + r2
    min_safe_distance = combined_radius * 1.1
    
    if length < min_safe_distance:
        perp_x, perp_y = -uy, ux
        offset = CONNECTION_CONFIG['base_offset'] * (1 + pass_count / 50)
        
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
        offset = CONNECTION_CONFIG['base_offset'] * (1 + pass_count / 50)
        
        start_x = x1 + r1 * ux + perp_x * offset
        start_y = y1 + r1 * uy + perp_y * offset
        
        name_margin = r2 + 1
        end_x = x2 - name_margin * ux + perp_x * offset
        end_y = y2 - name_margin * uy + perp_y * offset
    
    return start_x, start_y, end_x, end_y

def _save_individual_halves(first_half_data: Dict[str, pd.DataFrame], 
                           second_half_data: Dict[str, pd.DataFrame],
                           team_name: str, colors: Dict, show_labels: bool, 
                           base_path: Optional[str]):
    """Save individual half visualizations."""
    if not base_path:
        return
    
    if not first_half_data['players'].empty:
        fig1, ax1 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization(ax1, first_half_data, colors, f"{team_name} - Primera Parte", show_labels)
        plt.tight_layout()
        
        first_path = base_path.replace('.png', '_first_half.png')
        fig1.savefig(first_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"Saved first half: {first_path}")
        plt.close(fig1)
    
    if not second_half_data['players'].empty:
        fig2, ax2 = plt.subplots(figsize=(18, 14), facecolor='white')
        _draw_half_visualization(ax2, second_half_data, colors, f"{team_name} - Segunda Parte", show_labels)
        plt.tight_layout()
        
        second_path = base_path.replace('.png', '_second_half.png')
        fig2.savefig(second_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"Saved second half: {second_path}")
        plt.close(fig2)

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def load_from_csv_files(passes_path: str, players_path: str, connections_path: str) -> Dict[str, pd.DataFrame]:
    """Load data from specific CSV files."""
    match_data = {
        'passes': pd.read_csv(passes_path),
        'players': pd.read_csv(players_path),
        'connections': pd.read_csv(connections_path)
    }
    
    print("Data loaded from CSV:")
    for key, df in match_data.items():
        print(f"   - {key.title()}: {len(df)} rows")
    
    return match_data