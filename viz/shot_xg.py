"""
FootballDecoded Expected Goals (xG) Visualization Module
========================================================

Specialized single-team or comparative xG analysis visualization system.
Creates focused half-pitch xG maps with comprehensive statistical analysis.

Key Features:
- Flexible filtering: all teams, single team, or individual player analysis
- Half-pitch visualization focused on attacking scenarios
- Shot type differentiation (foot vs header markers)
- Outcome-based transparency (goals opaque, attempts transparent)
- Extreme scenario highlighting (lowest xG goals, highest xG misses)
- Comprehensive statistical panel with performance metrics
- Unified colormap integration with FootballDecoded design system

Shot Visualization System:
- Foot Shots: Hexagonal markers with xG color coding
- Headers: Circular markers with xG color coding  
- Goals: Full opacity with white outlines for emphasis
- Attempts: 20% transparency to show underlying shot density
- Extreme Cases: Special highlighting with contrasting colors

Statistical Analysis:
- Shot count and goal conversion rates
- Expected Goals (xG) totals and averages
- xG Performance: actual goals vs expected (over/under performance)
- Efficiency metrics: goals per shot, xG per shot
- Extreme value identification: lowest xG goal, highest xG miss

Technical Implementation:
- Half-pitch Opta coordinate system (attacking direction)
- Y-axis coordinate flipping for proper visualization orientation
- Dynamic filtering system for team/player focus
- Automatic title generation based on filter selection
- Logo integration and metadata display

Author: Jaime Oriol  
Created: 2025 - FootballDecoded Project
Coordinate System: Half-pitch Opta (0-100, attacking toward 100)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from mplsoccer.pitch import VerticalPitch
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'  # Professional dark theme
PITCH_COLOR = '#313332'       # Seamless pitch integration

def plot_shot_xg(csv_path, filter_by='all', logo_path=None, 
                 title_text=None, subtitle_text=None, subsubtitle_text=None):
    """
    Create focused xG visualization with flexible filtering options.
    
    Generates half-pitch xG analysis with comprehensive statistical panel.
    Supports filtering by team or individual player for detailed analysis.
    
    Features:
    - Dynamic filtering system (all teams, single team, individual player)
    - Shot type differentiation with appropriate markers
    - Outcome-based visual encoding (opacity, outlines)
    - Extreme scenario highlighting (best/worst xG cases)
    - Comprehensive statistical analysis panel
    - Automatic title generation based on filter selection
    
    Args:
        csv_path: Path to shots CSV file from match data processing
        filter_by: Filter criteria ('all', team name, or player name)
        logo_path: Optional path to team/player logo image
        title_text: Custom title (auto-generated if None)
        subtitle_text: Custom subtitle (auto-generated if None) 
        subsubtitle_text: Custom sub-subtitle (auto-generated if None)
        
    Returns:
        matplotlib Figure object with xG analysis
        
    Note:
        Half-pitch visualization focuses on attacking scenarios
        Coordinate system uses Opta standard with Y-axis flipping
        Statistical panel includes performance vs expectation analysis
    """
    # Load shots data from processed match CSV
    shots_df = pd.read_csv(csv_path)
    
    # Unified typography system
    font = 'DejaVu Sans'
    
    # Unified colormap system matching FootballDecoded modules
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Extract competition context for automatic title generation
    teams = shots_df['team'].unique()
    comp_name = f"{teams[0]} vs {teams[1]}" if len(teams) == 2 else teams[0]
    
    # DYNAMIC FILTERING SYSTEM: Support all/team/player analysis
    comp_selected = 0  # Flag for title generation logic
    if filter_by.lower() == 'all':
        selected_shots = shots_df
        comp_selected = 1  # Competition-level analysis
    elif filter_by in shots_df['team'].values:
        selected_shots = shots_df[shots_df['team'] == filter_by]
        comp_selected = 0  # Team-level analysis
    elif filter_by in shots_df['player'].values:
        selected_shots = shots_df[shots_df['player'] == filter_by]
        comp_selected = 0  # Player-level analysis
    else:
        return print(f"No data found for: {filter_by}")
    
    # PREPARE DATA: Add computed fields for visualization logic
    selected_shots = selected_shots.copy()
    selected_shots['header_tag'] = (selected_shots['body_part'] == 'Head').astype(int)  # Header identification
    selected_shots['goal'] = selected_shots['is_goal'].astype(int)                      # Goal flag for filtering
    
    # DATA SEGMENTATION: Separate by shot type and outcome for layered visualization
    selected_ground_shots = selected_shots[selected_shots['header_tag']==0]           # Foot shots
    selected_ground_goals = selected_ground_shots[selected_ground_shots['goal']==1]   # Foot goals
    selected_headers = selected_shots[selected_shots['header_tag']==1]               # Header attempts
    selected_headed_goals = selected_headers[selected_headers['goal']==1]             # Header goals
    
    # EXTREME SCENARIO IDENTIFICATION: Find best/worst xG cases for highlighting
    lowest_xg_goal = selected_shots[selected_shots['goal']==1].sort_values('xg').head(1)           # "Lucky" goal
    highest_xg_miss = selected_shots[selected_shots['goal']==0].sort_values('xg', ascending=False).head(1)  # "Unlucky" miss
    
    # MATPLOTLIB CONFIGURATION: Dark theme consistency
    mpl.rcParams['xtick.color'] = "white"
    mpl.rcParams['ytick.color'] = "white"
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    
    # PITCH SETUP: Half-pitch configuration for attacking focus
    pitch = VerticalPitch(pitch_type='opta', half=True, pitch_color=PITCH_COLOR, 
                         line_color='white', linewidth=1, stripe=False)
    fig, ax = pitch.grid(nrows=1, ncols=1, title_height=0.03, grid_height=0.7, 
                        endnote_height=0.05, axis=False)
    fig.set_size_inches(9, 7)
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # FOOT SHOT ATTEMPTS: Transparent to show density without overwhelming goals
    if not selected_ground_shots.empty:
        ax['pitch'].scatter(selected_ground_shots['y'], selected_ground_shots['x'], 
                           marker='h', s=200, alpha=0.2, c=selected_ground_shots['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # FOOT GOALS: Full opacity with white outline for emphasis
    if not selected_ground_goals.empty:
        p1 = ax['pitch'].scatter(selected_ground_goals['y'], selected_ground_goals['x'], 
                                marker='h', s=200, c=selected_ground_goals['xg'], 
                                edgecolors='w', lw=2, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # HEADER ATTEMPTS: Transparent circular markers
    if not selected_headers.empty:
        ax['pitch'].scatter(selected_headers['y'], selected_headers['x'], 
                           marker='o', s=200, alpha=0.2, c=selected_headers['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # HEADER GOALS: Full opacity circular markers with outline
    if not selected_headed_goals.empty:
        ax['pitch'].scatter(selected_headed_goals['y'], selected_headed_goals['x'], 
                           marker='o', s=200, c=selected_headed_goals['xg'], 
                           edgecolors='w', lw=2, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # EXTREME HIGHLIGHT: Highest xG miss with maximum color intensity
    if not highest_xg_miss.empty:
        highxg_marker = 'o' if highest_xg_miss['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(highest_xg_miss['y'].iloc[0], highest_xg_miss['x'].iloc[0], 
                           marker=highxg_marker, s=200, c=node_cmap(1.0), edgecolors='grey', 
                           lw=2.5, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=3)
    
    # EXTREME HIGHLIGHT: Lowest xG goal with minimum color intensity  
    if not lowest_xg_goal.empty:
        lowxg_marker = 'o' if lowest_xg_goal['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(lowest_xg_goal['y'].iloc[0], lowest_xg_goal['x'].iloc[0], 
                           marker=lowxg_marker, s=200, c=node_cmap(0.0), edgecolors='w', 
                           lw=2.5, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=3)
    
    # xG COLOR SCALE: Horizontal colorbar for value reference
    if 'p1' in locals():
        cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
        cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)
    
    # Leyenda de símbolos y colores
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])
    
    # Tipo de disparo
    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.2, marker='o', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Foot", color="w", fontfamily=font)
    legend_ax.text(0.35, 0.11, "Header", color="w", fontfamily=font)
    
    # Estado del disparo
    mid_color = node_cmap(0.5)
    legend_ax.scatter(1.3, 0.7, marker='h', s=200, c='grey', edgecolors='w', lw=2)
    legend_ax.scatter(1.3, 0.2, marker='h', alpha=0.2, s=200, c=mid_color, edgecolors='w')
    legend_ax.text(1.45, 0.61, "Goal", color="w", fontfamily=font)
    legend_ax.text(1.465, 0.11, "No Goal", color="w", fontfamily=font)
    
    # Extremos destacados
    legend_ax.scatter(2.4, 0.7, marker='h', s=200, c=node_cmap(0.0), edgecolors='w', lw=2.5)
    legend_ax.scatter(2.4, 0.2, marker='h', s=200, c=node_cmap(1.0), edgecolors='grey', lw=2.5)
    legend_ax.text(2.55, 0.61, "Lowest xG Goal", color="w", fontfamily=font)
    legend_ax.text(2.565, 0.11, "Highest xG Miss", color="w", fontfamily=font)
    
    # Títulos con defaults automáticos
    if not title_text:
        title_text = "Expected Goals" if comp_selected == 1 else f"{filter_by} Expected Goals"
    if not subtitle_text:
        subtitle_text = comp_name
    if not subsubtitle_text:
        subsubtitle_text = "2024-25"
    
    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=13, color='w', fontfamily=font)
    fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Estadísticas calculadas
    sign = '+' if selected_shots['goal'].sum() - selected_shots['xg'].sum() > 0 else ''
    
    # Labels izquierda
    fig.text(0.65, 0.925, "Shots:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.9, "xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "Goals:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    # Valores izquierda
    fig.text(0.73, 0.925, f"{int(selected_shots.count()[0])}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.9, f"{round(selected_shots['xg'].sum(), 1)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.875, f"{int(selected_shots['goal'].sum())}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    xg_sum = selected_shots['xg'].sum()
    perf_pct = int(round(100*(selected_shots['goal'].sum()-xg_sum)/xg_sum, 0)) if xg_sum > 0 else 0
    fig.text(0.73, 0.85, f"{sign}{perf_pct}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Labels derecha
    fig.text(0.79, 0.927, "xG/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.9, "Goal/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.875, "L xG Goal:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.85, "H xG Miss:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    # Valores derecha
    shot_count = selected_shots.count()[0]
    fig.text(0.89, 0.925, f"{round(selected_shots['xg'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.9, f"{round(selected_shots['goal'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.875, f"{round(lowest_xg_goal['xg'].iloc[0], 2)}" if not lowest_xg_goal.empty else "N/A", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.85, f"{round(highest_xg_miss['xg'].iloc[0], 2)}" if not highest_xg_miss.empty else "N/A", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # UNIFIED FOOTER: Consistent FootballDecoded branding
    fig.text(0.085 , 0.02, "Created by Jaime Oriol", fontweight='bold', fontsize=10, color="white", fontfamily=font)
    
    # Logo Football Decoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path_fd = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path_fd)
        logo_ax = fig.add_axes([0.67, -0.018, 0.28, 0.12])  # [x, y, width, height]
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        fig.text(0.7, 0.02, "Football Decoded", fontweight='bold', fontsize=14, color="white", fontfamily=font)
    
    # Logo opcional
    if logo_path and os.path.exists(logo_path):
        ax_logo = fig.add_axes([0.05, 0.82, 0.15, 0.15])
        ax_logo.axis("off")
        try:
            img = Image.open(logo_path)
            ax_logo.imshow(img)
        except Exception as e:
            print(f"Error cargando logo: {e}")
    
    plt.tight_layout()
    return fig