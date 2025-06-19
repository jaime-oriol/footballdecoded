# ====================================================================
# FootballDecoded - Shot Map Visualization
# ====================================================================
# Professional shot map with coherent design system
# ====================================================================

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

from visualization.core import (
    draw_pitch, get_team_colors, get_primary_color, get_secondary_color,
    FONT_CONFIG, save_high_quality
)

# ====================================================================
# SHOT MAP CONFIGURATION
# ====================================================================

SHOT_CONFIG = {
    'size_min': 100,
    'size_max': 1000,
    'alpha_base': 0.8,
    'edge_width_default': 2,
    'edge_width_goal': 4
}

RESULT_STYLES = {
    'Goal': {'alpha': 1.0, 'edge_color': '#FFD700', 'edge_width': 4},
    'Saved Shot': {'alpha': 0.8, 'edge_color': 'black', 'edge_width': 2},
    'Blocked Shot': {'alpha': 0.6, 'edge_color': 'gray', 'edge_width': 2},
    'Missed Shot': {'alpha': 0.5, 'edge_color': 'lightgray', 'edge_width': 1},
    'Shot On Post': {'alpha': 0.9, 'edge_color': '#FF6B35', 'edge_width': 3}
}

# ====================================================================
# MAIN VISUALIZATION FUNCTION
# ====================================================================

def create_shot_map(match_id: int, league: str, season: str,
                   team_colors: Dict[str, str] = None,
                   title: Optional[str] = None,
                   figsize: Tuple[int, int] = (16, 10),
                   save_path: Optional[str] = None) -> plt.Figure:
    """
    Create professional shot map with coherent design system.
    
    Args:
        match_id: Match ID for Understat
        league: League identifier
        season: Season identifier
        team_colors: Optional dict with team color overrides
        title: Optional custom title
        figsize: Figure size tuple
        save_path: Optional path to save figure
        
    Returns:
        Matplotlib figure
    """
    print(f"Creating shot map for match {match_id}")
    
    # Extract shot data
    from wrappers import understat_extract_shot_events
    shots_df = understat_extract_shot_events(match_id, league, season)
    
    if shots_df.empty:
        raise ValueError(f"No shots found for match {match_id}")
    
    # Process data
    shots_clean = shots_df.reset_index()
    teams = shots_clean['team'].unique()
    
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    print(f"Teams: {team_a} vs {team_b}")
    
    # Create figure with consistent styling
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    draw_pitch(ax)
    
    # Get team colors (coherent with pass_network)
    colors = _get_shot_colors(team_a, team_b, team_colors)
    
    # Draw shots for each team
    _draw_team_shots(ax, shots_clean, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots(ax, shots_clean, team_b, colors[team_b], 'right_to_left')
    
    # Add statistics and legend
    _add_team_statistics(ax, shots_clean, team_a, team_b, colors)
    _add_shot_legend(ax, colors, team_a, team_b)
    
    # Title with consistent styling
    match_title = title or f"{team_a} vs {team_b} - Mapa de Disparos"
    ax.text(52.5, 80, match_title, ha='center', va='center',
           fontsize=20, fontweight='bold', family=FONT_CONFIG['family'])
    
    # Consistent formatting
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 85)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save with consistent settings
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig

# ====================================================================
# SHOT DRAWING FUNCTIONS
# ====================================================================

def _draw_team_shots(ax, shots_df: pd.DataFrame, team_name: str, 
                    team_color: str, direction: str):
    """Draw shots for a specific team."""
    team_shots = shots_df[shots_df['team'] == team_name]
    
    for _, shot in team_shots.iterrows():
        # Get coordinates (convert from 0-1 to field meters)
        x = float(shot['shot_location_x']) * 105
        y = float(shot['shot_location_y']) * 68
        
        # Flip coordinates for team attacking right-to-left
        if direction == 'right_to_left':
            x = 105 - x
            y = 68 - y
        
        # Calculate size based on xG
        xg = float(shot['shot_xg'])
        size = SHOT_CONFIG['size_min'] + (xg * (SHOT_CONFIG['size_max'] - SHOT_CONFIG['size_min']))
        
        # Get style based on result
        result = shot['shot_result']
        style = RESULT_STYLES.get(result, RESULT_STYLES['Missed Shot'])
        
        # Draw shot
        ax.scatter(x, y,
                  s=size,
                  c=team_color,
                  alpha=style['alpha'],
                  edgecolors=style['edge_color'],
                  linewidth=style['edge_width'],
                  zorder=10)

def _add_team_statistics(ax, shots_df: pd.DataFrame, team_a: str, team_b: str, colors: Dict):
    """Add team statistics with consistent styling."""
    
    # Team A statistics (left side)
    team_a_shots = shots_df[shots_df['team'] == team_a]
    a_total = len(team_a_shots)
    a_xg = team_a_shots['shot_xg'].sum()
    a_goals = team_a_shots['is_goal'].sum()
    
    ax.text(26, 75, f"{team_a}", fontsize=18, fontweight='bold',
           color=colors[team_a], ha='center', family=FONT_CONFIG['family'])
    ax.text(26, 71, f"Disparos: {a_total} | xG: {a_xg:.2f} | Goles: {a_goals}",
           fontsize=14, ha='center', color='black', family=FONT_CONFIG['family'])
    
    # Team B statistics (right side)
    team_b_shots = shots_df[shots_df['team'] == team_b]
    b_total = len(team_b_shots)
    b_xg = team_b_shots['shot_xg'].sum()
    b_goals = team_b_shots['is_goal'].sum()
    
    ax.text(79, 75, f"{team_b}", fontsize=18, fontweight='bold',
           color=colors[team_b], ha='center', family=FONT_CONFIG['family'])
    ax.text(79, 71, f"Disparos: {b_total} | xG: {b_xg:.2f} | Goles: {b_goals}",
           fontsize=14, ha='center', color='black', family=FONT_CONFIG['family'])

def _add_shot_legend(ax, colors: Dict, team_a: str, team_b: str):
    """Add legend with consistent styling."""
    
    # Direction indicators (consistent with pass_network style)
    ax.annotate('', xy=(35, -3), xytext=(15, -3),
                arrowprops=dict(arrowstyle='->', color=colors[team_a], lw=4))
    ax.text(10, -3, f"{team_a}", fontsize=14, fontweight='bold',
           color=colors[team_a], va='center', family=FONT_CONFIG['family'])
    
    ax.annotate('', xy=(70, -3), xytext=(90, -3),
                arrowprops=dict(arrowstyle='->', color=colors[team_b], lw=4))
    ax.text(95, -3, f"{team_b}", fontsize=14, fontweight='bold',
           color=colors[team_b], va='center', family=FONT_CONFIG['family'])
    
    # Size legend (consistent with pass_network)
    ax.text(52.5, -8, "Tamaño = xG", fontsize=16, fontweight='bold',
           ha='center', color='black', family=FONT_CONFIG['family'])
    
    # xG scale examples
    legend_y = -12
    xg_examples = [(0.1, "0.1"), (0.3, "0.3"), (0.8, "0.8")]
    
    for i, (xg, label) in enumerate(xg_examples):
        x_pos = 52.5 - 12 + (i * 12)
        size = SHOT_CONFIG['size_min'] + (xg * (SHOT_CONFIG['size_max'] - SHOT_CONFIG['size_min']))
        
        ax.scatter(x_pos, legend_y, s=size, c='gray', alpha=0.6,
                  edgecolors='black', linewidth=1)
        ax.text(x_pos, legend_y - 4, label, fontsize=12, ha='center',
               fontweight='bold', family=FONT_CONFIG['family'])
    
    # Result legend
    ax.text(52.5, -20, "Dorado = Gol | Negro = Parada | Naranja = Poste",
           fontsize=12, ha='center', style='italic', family=FONT_CONFIG['family'])

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _get_shot_colors(team_a: str, team_b: str, custom_colors: Optional[Dict] = None) -> Dict[str, str]:
    """Get team colors with consistent system."""
    if custom_colors:
        return custom_colors
    
    colors = {}
    colors[team_a] = get_primary_color(team_a)
    colors[team_b] = get_primary_color(team_b)
    
    return colors

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def create_shot_map_with_match_data(match_data: Dict[str, pd.DataFrame],
                                   team_colors: Dict[str, str] = None,
                                   title: Optional[str] = None,
                                   save_path: Optional[str] = None) -> plt.Figure:
    """Create shot map from pre-loaded match data."""
    if 'shots' not in match_data or match_data['shots'].empty:
        raise ValueError("No shot data found in match_data")
    
    shots_df = match_data['shots']
    shots_clean = shots_df.reset_index() if hasattr(shots_df.index, 'levels') else shots_df
    
    teams = shots_clean['team'].unique()
    if len(teams) != 2:
        raise ValueError(f"Expected 2 teams, found {len(teams)}")
    
    team_a, team_b = teams[0], teams[1]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    draw_pitch(ax)
    
    # Get colors
    colors = _get_shot_colors(team_a, team_b, team_colors)
    
    # Draw shots
    _draw_team_shots(ax, shots_clean, team_a, colors[team_a], 'left_to_right')
    _draw_team_shots(ax, shots_clean, team_b, colors[team_b], 'right_to_left')
    
    # Add elements
    _add_team_statistics(ax, shots_clean, team_a, team_b, colors)
    _add_shot_legend(ax, colors, team_a, team_b)
    
    # Title
    match_title = title or f"{team_a} vs {team_b} - Mapa de Disparos"
    ax.text(52.5, 80, match_title, ha='center', va='center',
           fontsize=20, fontweight='bold', family=FONT_CONFIG['family'])
    
    # Formatting
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 85)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Saved: {save_path}")
    
    return fig