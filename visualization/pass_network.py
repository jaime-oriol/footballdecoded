# ====================================================================
# FootballDecoded - Pass Network Visualization Engine
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import seaborn as sns
from datetime import datetime

# ====================================================================
# CONFIGURATION
# ====================================================================

FIELD_CONFIG = {
    'length': 105,
    'width': 68,
    'color': 'white',
    'line_color': '#000000',
    'line_width': 2.0,
    'goal_color': '#666666',
    'goal_width': 10.0
}

CONNECTION_CONFIG = {
    'min_passes': 5,
    'thickness_tiers': [5, 8, 12, 18, 25],
    'line_widths': [2.0, 4.0, 6.5, 9.0, 12.0],
    'max_width': 12.0,
    'direction_offset': 1.5,
    'alpha': 0.8
}

TEAM_COLORS = {
    'default': {'primary': '#2E4A87', 'secondary': '#1A365D'},
    'Barcelona': {'primary': '#A50044', 'secondary': '#004D98'},
    'Real Madrid': {'primary': '#FEBE10', 'secondary': '#002147'},
    'Athletic': {'primary': '#E30613', 'secondary': '#1B1B1B'},
    'Athletic Club': {'primary': '#E30613', 'secondary': '#1B1B1B'},
    'Manchester City': {'primary': '#6CABDD', 'secondary': '#1C2C5B'},
    'Liverpool': {'primary': '#C8102E', 'secondary': '#00B2A9'}
}

# ====================================================================
# DATA PROCESSING
# ====================================================================

def process_pass_network_data(network_data: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process raw network data and calculate metrics for visualization."""
    players_key = 'players' if 'players' in network_data else 'positions'
    
    if not network_data or players_key not in network_data or network_data[players_key].empty:
        return pd.DataFrame(), pd.DataFrame()
    
    positions_df = network_data[players_key].copy()
    connections_df = network_data['connections'].copy() if 'connections' in network_data and not network_data['connections'].empty else pd.DataFrame()
    
    positions_df['field_x'] = positions_df['avg_x']
    positions_df['field_y'] = positions_df['avg_y']
    positions_df['node_size'] = calculate_node_sizes(positions_df['total_passes'])
    
    if not connections_df.empty:
        connections_df['line_width'] = calculate_line_widths(connections_df['pass_count'])
        connections_processed = create_directional_connections(connections_df, network_data['passes'])
    else:
        connections_processed = pd.DataFrame()
    
    return positions_df, connections_processed


def calculate_node_sizes(pass_counts: pd.Series, min_size: int = 1500, max_size: int = 4000) -> pd.Series:
    """Calculate node sizes with logarithmic scaling for better visual differentiation."""
    if pass_counts.empty:
        return pd.Series()
    
    min_passes = pass_counts.min()
    max_passes = pass_counts.max()
    
    if max_passes == min_passes:
        return pd.Series([min_size] * len(pass_counts), index=pass_counts.index)
    
    log_passes = np.log1p(pass_counts - min_passes)
    log_max = np.log1p(max_passes - min_passes)
    normalized = log_passes / log_max
    
    sizes = min_size + (normalized * (max_size - min_size))
    return sizes


def calculate_line_widths(pass_counts: pd.Series) -> pd.Series:
    """Calculate line widths based on pass frequency."""
    if pass_counts.empty:
        return pd.Series()
    
    def get_width(count):
        if count < CONNECTION_CONFIG['min_passes']:
            return 0
        elif count < 8:
            return 2.0
        elif count < 12:
            return 4.0
        elif count < 18:
            return 6.5
        elif count < 25:
            return 9.0
        else:
            return 12.0
    
    return pass_counts.apply(get_width)


def create_directional_connections(connections_df: pd.DataFrame, passes_df: pd.DataFrame) -> pd.DataFrame:
    """Create simplified connections from existing data."""
    if connections_df.empty:
        return pd.DataFrame()
    
    directional_connections = []
    processed_pairs = set()
    
    for _, conn in connections_df.iterrows():
        source = conn['source']
        target = conn['target']
        pass_count = conn['pass_count']
        
        pair_id = tuple(sorted([source, target]))
        
        if pair_id not in processed_pairs and pass_count >= CONNECTION_CONFIG['min_passes']:
            processed_pairs.add(pair_id)
            
            directional_connections.append({
                'source': source,
                'target': target,
                'pass_count': pass_count,
                'line_width': calculate_line_widths(pd.Series([pass_count])).iloc[0],
                'direction': 'main'
            })
    
    return pd.DataFrame(directional_connections)


def filter_team_data(processed_data: Dict[str, pd.DataFrame], team_name: str) -> Dict[str, pd.DataFrame]:
    """Filter data for a specific team."""
    players_key = 'players' if 'players' in processed_data else 'positions'
    
    team_players = processed_data[players_key][processed_data[players_key]['team'] == team_name]
    team_connections = processed_data['connections'][processed_data['connections']['team'] == team_name] if 'connections' in processed_data else pd.DataFrame()
    team_passes = processed_data['passes'][processed_data['passes']['team'] == team_name]
    
    return {
        'passes': team_passes,
        'players': team_players,
        'connections': team_connections
    }

# ====================================================================
# FIELD VISUALIZATION
# ====================================================================

def draw_football_pitch(ax, half_pitch: bool = False):
    """Draw a professional football pitch with enhanced elements."""
    length = FIELD_CONFIG['length']
    width = FIELD_CONFIG['width']
    
    if half_pitch:
        length = length / 2
    
    # Base pitch
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0,
                            edgecolor='none',
                            facecolor=FIELD_CONFIG['color'])
    ax.add_patch(pitch)
    
    # Center line and circle
    if not half_pitch:
        ax.plot([length/2, length/2], [0, width], 
               color=FIELD_CONFIG['line_color'], 
               linewidth=FIELD_CONFIG['line_width'])
        
        circle = patches.Circle((length/2, width/2), 9.15, 
                              linewidth=FIELD_CONFIG['line_width'],
                              edgecolor=FIELD_CONFIG['line_color'],
                              facecolor='none')
        ax.add_patch(circle)
    
    draw_penalty_areas(ax, length, width)
    draw_goals(ax, length, width)
    
    # Field borders
    border = patches.Rectangle((0, 0), length, width,
                             linewidth=FIELD_CONFIG['line_width'],
                             edgecolor=FIELD_CONFIG['line_color'],
                             facecolor='none')
    ax.add_patch(border)
    
    ax.set_xlim(-5, length + 5)
    ax.set_ylim(-5, width + 5)
    ax.set_aspect('equal')
    ax.axis('off')


def draw_penalty_areas(ax, length: float, width: float):
    """Draw penalty areas with semicircle and penalty spots."""
    penalty_length = 16.5
    penalty_width = 40.32
    penalty_y_start = (width - penalty_width) / 2
    
    # Large penalty areas
    penalty_left = patches.Rectangle((0, penalty_y_start), penalty_length, penalty_width,
                                   linewidth=FIELD_CONFIG['line_width'],
                                   edgecolor=FIELD_CONFIG['line_color'],
                                   facecolor='none')
    ax.add_patch(penalty_left)
    
    penalty_right = patches.Rectangle((length - penalty_length, penalty_y_start), 
                                    penalty_length, penalty_width,
                                    linewidth=FIELD_CONFIG['line_width'],
                                    edgecolor=FIELD_CONFIG['line_color'],
                                    facecolor='none')
    ax.add_patch(penalty_right)
    
    # Small penalty areas
    small_area_length = 5.5
    small_area_width = 18.32
    small_y_start = (width - small_area_width) / 2
    
    small_left = patches.Rectangle((0, small_y_start), small_area_length, small_area_width,
                                 linewidth=FIELD_CONFIG['line_width'],
                                 edgecolor=FIELD_CONFIG['line_color'],
                                 facecolor='none')
    ax.add_patch(small_left)
    
    small_right = patches.Rectangle((length - small_area_length, small_y_start), 
                                  small_area_length, small_area_width,
                                  linewidth=FIELD_CONFIG['line_width'],
                                  edgecolor=FIELD_CONFIG['line_color'],
                                  facecolor='none')
    ax.add_patch(small_right)
    
    # Penalty area semicircles
    penalty_spot_distance = 11.0
    semicircle_radius = 9.15
    
    semicircle_left = patches.Arc((penalty_spot_distance, width/2), 
                                 semicircle_radius * 2, semicircle_radius * 2,
                                 angle=0, theta1=-90, theta2=90,
                                 linewidth=FIELD_CONFIG['line_width'],
                                 edgecolor=FIELD_CONFIG['line_color'],
                                 facecolor='none')
    ax.add_patch(semicircle_left)
    
    semicircle_right = patches.Arc((length - penalty_spot_distance, width/2), 
                                  semicircle_radius * 2, semicircle_radius * 2,
                                  angle=0, theta1=90, theta2=270,
                                  linewidth=FIELD_CONFIG['line_width'],
                                  edgecolor=FIELD_CONFIG['line_color'],
                                  facecolor='none')
    ax.add_patch(semicircle_right)
    
    # Penalty spots
    penalty_spot_radius = 0.3
    
    penalty_spot_left = patches.Circle((penalty_spot_distance, width/2), 
                                      penalty_spot_radius,
                                      linewidth=0,
                                      edgecolor='none',
                                      facecolor=FIELD_CONFIG['line_color'])
    ax.add_patch(penalty_spot_left)
    
    penalty_spot_right = patches.Circle((length - penalty_spot_distance, width/2), 
                                       penalty_spot_radius,
                                       linewidth=0,
                                       edgecolor='none',
                                       facecolor=FIELD_CONFIG['line_color'])
    ax.add_patch(penalty_spot_right)


def draw_goals(ax, length: float, width: float):
    """Draw goals with thick visible lines."""
    goal_width = 7.32
    goal_y_start = (width - goal_width) / 2
    
    ax.plot([0, 0], [goal_y_start, goal_y_start + goal_width],
           color=FIELD_CONFIG['goal_color'],
           linewidth=FIELD_CONFIG['goal_width'],
           solid_capstyle='round',
           zorder=5)
    
    ax.plot([length, length], [goal_y_start, goal_y_start + goal_width],
           color=FIELD_CONFIG['goal_color'],
           linewidth=FIELD_CONFIG['goal_width'],
           solid_capstyle='round',
           zorder=5)

# ====================================================================
# NETWORK VISUALIZATION
# ====================================================================

def draw_connections(ax, connections_df: pd.DataFrame, positions_df: pd.DataFrame, color: str):
    """Draw bidirectional connections with visual separation."""
    if connections_df.empty:
        return
        
    offset_distance = 1.5
    
    for _, connection in connections_df.iterrows():
        source_player = connection['source']
        target_player = connection['target']
        
        source_pos = positions_df[positions_df['player'] == source_player]
        target_pos = positions_df[positions_df['player'] == target_player]
        
        if source_pos.empty or target_pos.empty:
            continue
        
        x1, y1 = source_pos.iloc[0]['field_x'], source_pos.iloc[0]['field_y']
        x2, y2 = target_pos.iloc[0]['field_x'], target_pos.iloc[0]['field_y']
        
        line_width = connection['line_width']
        
        if line_width > 0:
            # Calculate perpendicular offset for line separation
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                perp_x = -dy / length * offset_distance
                perp_y = dx / length * offset_distance
                
                direction = connection.get('direction', 'A_to_B')
                if direction == 'B_to_A':
                    perp_x = -perp_x
                    perp_y = -perp_y
                
                x1_offset = x1 + perp_x
                y1_offset = y1 + perp_y
                x2_offset = x2 + perp_x
                y2_offset = y2 + perp_y
                
                ax.plot([x1_offset, x2_offset], [y1_offset, y2_offset], 
                       color=color, 
                       linewidth=line_width,
                       alpha=CONNECTION_CONFIG['alpha'],
                       solid_capstyle='round',
                       zorder=1)


def draw_player_nodes(ax, positions_df: pd.DataFrame, color: str):
    """Draw player nodes with double-circle effect."""
    for _, player in positions_df.iterrows():
        node_size = player['node_size']
        x, y = player['field_x'], player['field_y']
        
        # Outer circle (solid border)
        ax.scatter(x, y,
                  s=node_size,
                  c='none',
                  edgecolors=color,
                  linewidth=8,
                  alpha=1.0,
                  zorder=10)
        
        # Inner circle (semi-transparent center)
        inner_size = node_size * 0.7
        ax.scatter(x, y,
                  s=inner_size,
                  c=color,
                  edgecolors='none',
                  linewidth=0,
                  alpha=0.4,
                  zorder=9)


def add_player_labels(ax, positions_df: pd.DataFrame):
    """Add player names inside nodes with high contrast."""
    for _, player in positions_df.iterrows():
        player_name = player['player']
        
        # Use only surname for long names
        if len(player_name) > 14:
            parts = player_name.split()
            if len(parts) >= 2:
                player_name = parts[-1]
        
        ax.text(player['field_x'], player['field_y'],
               player_name,
               ha='center', va='center',
               color='#1A1A1A',
               fontsize=16,
               fontweight='bold',
               path_effects=[
                   path_effects.Stroke(linewidth=4, foreground='white'),
                   path_effects.Normal()
               ],
               zorder=11)

# ====================================================================
# MAIN VISUALIZATION FUNCTION
# ====================================================================

def plot_pass_network(network_data: Dict, team_name: str, 
                     show_player_names: bool = True,
                     title: Optional[str] = None,
                     figsize: Tuple[int, int] = (20, 14)) -> plt.Figure:
    """Generate complete pass network visualization."""
    positions_df, connections_df = process_pass_network_data(network_data)
    
    if positions_df.empty:
        raise ValueError(f"No data found for {team_name}")
    
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    
    draw_football_pitch(ax)
    
    team_colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    draw_player_nodes(ax, positions_df, team_colors['primary'])
    
    if not connections_df.empty:
        draw_connections(ax, connections_df, positions_df, team_colors['secondary'])
        connections_count = len(connections_df)
    else:
        connections_count = 0
    
    if show_player_names:
        add_player_labels(ax, positions_df)
    
    # Configure title
    if title is None:
        total_passes = len(network_data['passes']) if 'passes' in network_data else 0
        if connections_count > 0:
            title = f"{team_name} - Red de Pases\nPases completados: {total_passes} | Conexiones: {connections_count}"
        else:
            title = f"{team_name} - Posiciones Medias\nPases completados: {total_passes} | Sin conexiones suficientes"
    
    ax.set_title(title, 
                color='#2C3E50',
                fontsize=22,
                fontweight='bold', 
                pad=30,
                family='DejaVu Sans')
    
    plt.tight_layout()
    return fig

# ====================================================================
# EXPORT AND UTILITY FUNCTIONS
# ====================================================================

def save_pass_network_hd(fig: plt.Figure, team_name: str, match_info: str = "") -> str:
    """Save visualization in high quality for presentations."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_team_name = team_name.replace(" ", "_").replace("-", "_")
    
    if match_info:
        filename = f"pass_network_{clean_team_name}_{match_info}_{timestamp}.png"
    else:
        filename = f"pass_network_{clean_team_name}_{timestamp}.png"
    
    fig.savefig(filename, 
                dpi=300,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none',
                format='png',
                pad_inches=0.2)
    
    print(f"Visualization saved: {filename}")
    print(f"Resolution: 300 DPI (professional quality)")
    
    return filename


def create_pass_network_from_data(processed_data: Dict[str, pd.DataFrame], 
                                team_name: str,
                                save_path: Optional[str] = None,
                                save_hd: bool = True) -> plt.Figure:
    """Create visualization from processed data with automatic HD export."""
    print(f"Creating premium visualization for {team_name}...")
    
    team_data = filter_team_data(processed_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No data found for {team_name}")
    
    fig = plot_pass_network(team_data, team_name)
    
    if save_hd:
        save_pass_network_hd(fig, team_name)
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Also saved to: {save_path}")
    
    return fig

# ====================================================================
# EXAMPLE USAGE
# ====================================================================

if __name__ == "__main__":
    try:
        print("Loading previously processed data...")
        from match_data import load_processed_data
        
        processed_data = load_processed_data("visualization/data", 1821769)
        
        # Create visualization for Barcelona
        fig_barca = create_pass_network_from_data(
            processed_data=processed_data,
            team_name="Barcelona"
        )
        
        # Create visualization for Athletic
        fig_athletic = create_pass_network_from_data(
            processed_data=processed_data,
            team_name="Athletic"
        )
        
        plt.show()
        
    except Exception as e:
        print(f"Error: {e}")
        print("First run: visualization/match_data.py to extract the data")