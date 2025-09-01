"""
FootballDecoded Statistical Comparison Table Module
===================================================

Comprehensive statistical comparison system for player performance analysis.
Creates professional statistical tables with percentile-based performance indicators.

Key Features:
- Single or dual-player statistical comparison
- Percentile-based performance evaluation (0-100 scale)
- Unified colormap integration for performance visualization
- Team logo integration and contextual information display
- Comprehensive metrics coverage (minutes, matches, performance indicators)
- Color-coded percentile legend with performance gradients

Statistical Framework:
- Context Integration: Minutes played, matches played for proper evaluation
- Performance Metrics: Raw values with percentile rankings
- Color Coding: Percentile-based performance indication (0-100 scale)
- Comparison Mode: Side-by-side player evaluation with visual distinction
- Team Context: Logo integration and team color coordination

Technical Implementation:
- Fixed dimensions for swarm radar integration compatibility
- Alternating row backgrounds for readability
- Percentile normalization with unified colormap
- Logo positioning and scaling for professional appearance
- Arrow-based performance scale indication

Visual Design:
- Consistent with FootballDecoded design language
- Professional sports analytics aesthetics
- Clear statistical hierarchy and performance indication
- Team-based color coordination for player distinction

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
Integration: Designed for combination with swarm_radar visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, FancyArrowPatch, ArrowStyle
import matplotlib.patheffects as path_effects
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'

# Fixed dimensions for radar integration compatibility
# These ensure perfect alignment when combining with radar visualizations

# Swarm radar dimensions (original)
SWARM_TOTAL_SIZE = (4945, 2755)   # Total combined visualization size
SWARM_RADAR_SIZE = (2625, 2755)   # Radar chart portion dimensions
SWARM_TABLE_SIZE = (2320, 2755)   # Statistical table portion dimensions

# Traditional radar dimensions (adjusted for 9x10 aspect ratio)
TRADITIONAL_TOTAL_SIZE = (4820, 2755)   # Total combined size for traditional radar
TRADITIONAL_RADAR_SIZE = (2500, 2755)   # Traditional radar portion (maintains aspect ratio)
TRADITIONAL_TABLE_SIZE = (2320, 2755)   # Table portion (same as swarm)

def create_stats_table(df_data, player_1_id, metrics, metric_titles, 
                      player_2_id=None, team_colors=None, 
                      save_path='stats_table.png', show_plot=True,
                      team_logos=None, footer_text='Percentiles vs dataset'):
    """
    Create comprehensive statistical comparison table for player analysis.
    
    Generates professional statistical table with percentile-based performance
    evaluation, team context, and visual performance indicators.
    
    Features:
    - Single or dual-player comparison mode
    - Percentile-based performance ranking (0-100 scale)
    - Team logo integration and color coordination
    - Contextual information (minutes, matches played)
    - Color-coded performance legend with gradient scale
    - Professional formatting with alternating row backgrounds
    
    Args:
        df_data: DataFrame with player statistics and percentile columns
        player_1_id: Primary player identifier
        metrics: List of statistical metric column names
        metric_titles: List of display names for metrics
        player_2_id: Optional secondary player for comparison
        team_colors: Optional team colors [primary, secondary] for each player
        save_path: Output file path for saved visualization
        show_plot: Whether to display the plot
        team_logos: Dictionary mapping team names to logo file paths
        footer_text: Explanatory text for percentile context
        
    Returns:
        Path to saved visualization file
        
    Note:
        Expects percentile columns named as '{metric}_pct' for each metric
        Fixed dimensions ensure compatibility with swarm radar integration
        Color coding uses unified FootballDecoded colormap system
    """
    
    # Default team colors if not provided
    if team_colors is None:
        team_colors = ['#FF6B6B', '#4ECDC4']  # Friendly default color scheme
    
    # Unified colormap system for percentile visualization
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    percentile_norm = Normalize(vmin=0, vmax=100)  # 0-100 percentile scale
    
    # Extract player data from dataset
    p1 = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]  # Primary player
    p2 = None
    if player_2_id is not None:
        p2 = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]  # Comparison player
    
    # Figure setup with consistent FootballDecoded styling
    fig = plt.figure(figsize=(7.5, 8.5), facecolor=BACKGROUND_COLOR)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 8.5)  # Fixed width for consistent layout
    ax.set_ylim(0, 15)   # Fixed height for metric accommodation
    ax.axis('off')       # Clean appearance without axes
    
    # Main title - removed
    # fig.text(0.5, 0.95, "Player Comparison", fontweight='bold', fontsize=20, 
    #          color='white', ha='center', va='top', family='DejaVu Sans')
    
    # Layout positioning coordinates (optimized for readability)
    y_start = 14.5      # Top position for player headers
    # Player 1 positions
    logo1_x = 3.35      # Logo X coordinate
    text1_x = 3.6       # Name text X coordinate
    p1_value_x = 4.1    # Statistical value X coordinate
    p1_pct_x = 4.5      # Percentile value X coordinate
    
    # Player 2 positions (when comparing two players)
    logo2_x = 6.15      # Second player logo X
    text2_x = 6.2       # Second player name X
    p2_value_x = 6.7    # Second player value X
    p2_pct_x = 7.1      # Second player percentile X
    
    # PLAYER 1 HEADER: Logo and identification
    if team_logos and p1['team'] in team_logos:
        try:
            logo = Image.open(team_logos[p1['team']])
            # Positioning: convert layout coords to figure fractions
            logo_ax = fig.add_axes([logo1_x/10, (y_start-0.8)/15, 0.08, 0.08])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except Exception as e:
            print(f"Error cargando logo para {p1['team']}: {e}")
            print(f"Ruta: {team_logos[p1['team']]}")  # Graceful failure if logo unavailable
    
    # Player 1 name and context
    ax.text(text1_x, y_start, p1['player_name'], 
            fontweight='bold', fontsize=14, color=team_colors[0], ha='left', va='center', family='DejaVu Sans')
    ax.text(text1_x, y_start - 0.425, f"{p1['league']} {p1['season']}", 
            fontsize=10, color='white', alpha=0.9, ha='left', fontweight='regular', family='DejaVu Sans')
    
    # PLAYER 2 HEADER: Logo and identification (only show if P2 exists)
    if p2 is not None:
        if team_logos and p2['team'] in team_logos:
            try:
                logo = Image.open(team_logos[p2['team']])
                logo_ax = fig.add_axes([logo2_x/10, (y_start-0.8)/15, 0.08, 0.08])
                logo_ax.imshow(logo)
                logo_ax.axis('off')
            except Exception as e:
                print(f"Error cargando logo para {p2['team']}: {e}")
                print(f"Ruta: {team_logos[p2['team']]}")  # Graceful failure if logo unavailable
        
        # Player 2 name and context
        ax.text(text2_x, y_start, p2['player_name'],
                fontweight='bold', fontsize=14, color=team_colors[1], ha='left', va='center', family='DejaVu Sans')
        ax.text(text2_x, y_start - 0.425, f"{p2['league']} {p2['season']}", 
                fontsize=10, color='white', alpha=0.9, ha='left', fontweight='regular', family='DejaVu Sans')
    # NOTE: Layout space for P2 is always reserved, content only shows when P2 exists
    # Add invisible placeholder elements to maintain consistent layout even with 1 player
    if p2 is None:
        # Invisible text elements to preserve layout dimensions
        ax.text(text2_x, y_start, "", 
                fontweight='bold', fontsize=14, color='white', alpha=0, ha='left', va='center', family='DejaVu Sans')
        ax.text(text2_x, y_start - 0.425, "", 
                fontsize=10, color='white', alpha=0, ha='left', fontweight='regular', family='DejaVu Sans')
    
    # Header separator line
    y_line = y_start - 0.7
    ax.plot([0.5, 8.5], [y_line, y_line], color='grey', linewidth=0.5, alpha=0.6)
    
    # CONTEXTUAL INFORMATION: Minutes and matches for proper evaluation context
    y_context = y_start - 1.2
    
    # Minutes played context
    ax.text(0.7, y_context, "Minutes Played", fontsize=10, color='white', fontweight='bold', family='DejaVu Sans')
    min1 = int(p1.get('minutes_played', 0))
    ax.text(p1_value_x, y_context, f"{min1}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    if p2 is not None:
        min2 = int(p2.get('minutes_played', 0))
        ax.text(p2_value_x, y_context, f"{min2}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    else:
        # Invisible placeholder for consistent layout
        ax.text(p2_value_x, y_context, "", fontsize=11, color='white', alpha=0, ha='right', fontweight='regular', family='DejaVu Sans')
    # NOTE: P2 column space reserved, value only shown when P2 exists
    
    # Matches played context
    y_context -= 0.4
    ax.text(0.7, y_context, "Matches Played", fontsize=10, color='white', fontweight='bold', family='DejaVu Sans')
    mat1 = int(p1.get('matches_played', 0))
    ax.text(p1_value_x, y_context, f"{mat1}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    if p2 is not None:
        mat2 = int(p2.get('matches_played', 0))
        ax.text(p2_value_x, y_context, f"{mat2}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    else:
        # Invisible placeholder for consistent layout
        ax.text(p2_value_x, y_context, "", fontsize=11, color='white', alpha=0, ha='right', fontweight='regular', family='DejaVu Sans')
    # NOTE: P2 column space reserved, value only shown when P2 exists
    
    # Context separator line
    y_line = y_context - 0.3
    ax.plot([0.5, 8.5], [y_line, y_line], color='grey', linewidth=0.5, alpha=0.6)
    
    # STATISTICAL METRICS: Core performance data with percentile indicators
    y_metrics = y_context - 0.7
    row_height = 1.0  # Spacing between metric rows
    
    for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
        y_pos = y_metrics - (idx * row_height)
        
        if idx % 2 == 0:
            rect = Rectangle((0.5, y_pos - 0.4), 8.0, 0.8, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        clean_title = title.replace('\n', ' ')
        ax.text(0.7, y_pos, clean_title, fontsize=10, color='white', fontweight='bold', va='center', family='DejaVu Sans')
        
        # Jugador 1
        val_1 = p1.get(metric, 0)
        pct_col = f"{metric}_pct"
        pct_1 = p1.get(pct_col, 0)
        
        if pd.isna(pct_1):
            pct_1 = 0
        
        if pd.isna(val_1):
            val_str_1 = "0.0"
        elif 0 < val_1 < 1:
            val_str_1 = f"{val_1:.2f}"
        elif val_1 < 10:
            val_str_1 = f"{val_1:.1f}"
        else:
            val_str_1 = f"{int(val_1)}"
        
        pct_color_1 = node_cmap(percentile_norm(pct_1))
        
        ax.text(p1_value_x, y_pos, val_str_1, fontsize=11, color='white', ha='right', 
                fontweight='regular', va='center', family='DejaVu Sans')
        ax.text(p1_pct_x, y_pos, f"{int(pct_1)}", 
                fontsize=10, color=pct_color_1, ha='left', fontweight='regular', va='center', family='DejaVu Sans')
        
        # Jugador 2 (only show values when P2 exists)
        if p2 is not None:
            val_2 = p2.get(metric, 0)
            pct_2 = p2.get(pct_col, 0)
            
            if pd.isna(pct_2):
                pct_2 = 0
            
            if pd.isna(val_2):
                val_str_2 = "0.0"
            elif 0 < val_2 < 1:
                val_str_2 = f"{val_2:.2f}"
            elif val_2 < 10:
                val_str_2 = f"{val_2:.1f}"
            else:
                val_str_2 = f"{int(val_2)}"
            
            pct_color_2 = node_cmap(percentile_norm(pct_2))
            
            ax.text(p2_value_x, y_pos, val_str_2, fontsize=11, color='white', ha='right', 
                    fontweight='regular', va='center', family='DejaVu Sans')
            ax.text(p2_pct_x, y_pos, f"{int(pct_2)}", 
                    fontsize=10, color=pct_color_2, ha='left', fontweight='regular', va='center', family='DejaVu Sans')
        else:
            # Invisible placeholders for consistent layout
            ax.text(p2_value_x, y_pos, "", fontsize=11, color='white', alpha=0, ha='right', 
                    fontweight='regular', va='center', family='DejaVu Sans')
            ax.text(p2_pct_x, y_pos, "", 
                    fontsize=10, color='white', alpha=0, ha='left', fontweight='regular', va='center', family='DejaVu Sans')
        # NOTE: P2 statistics columns reserved, values only shown when P2 exists
    
    # Footer
    footer_y = y_metrics - (len(metrics) * row_height)
    
    if len(metrics) % 2 == 1:
        rect = Rectangle((0.5, footer_y - 0.4), 8.0, 0.8, facecolor='white', alpha=0.05)
        ax.add_patch(rect)
    
    ax.text(0.7, footer_y, f"*{footer_text}", 
            fontsize=10, color='white', ha='left', style='italic', fontweight='bold', va='center', family='DejaVu Sans')
    
    # Leyenda de percentiles (movida a la derecha)
    legend_y = footer_y - 0.8
    
    intervals = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
    interval_colors = [node_cmap(percentile_norm(i*25)) for i in range(5)]
    
    spacing = 0.8
    
    for i, ((low, high), color) in enumerate(zip(intervals, interval_colors)):
        x_pos = 1.0 + i * spacing
        
        ax.plot([x_pos - 0.25, x_pos + 0.25], [legend_y, legend_y], 
                color=color, linewidth=3, solid_capstyle='round')
        
        ax.text(x_pos, legend_y - 0.3, f"{low}-{high}", 
                fontsize=9, color='white', ha='center', va='center', family='DejaVu Sans')
    
    # LOW → HIGH con flecha
    arrow_y = legend_y - 0.8
    arrow_start_x = 1.2
    arrow_end_x = 4.0
    
    ax.annotate('', xy=(arrow_end_x, arrow_y), xytext=(arrow_start_x, arrow_y),
                arrowprops=dict(arrowstyle='->', color='white', lw=1))
    
    ax.text(arrow_start_x - 0.1, arrow_y, 'LOW', fontsize=9, color='white', 
            ha='right', va='center', family='DejaVu Sans')
    ax.text(arrow_end_x + 0.1, arrow_y, 'HIGH', fontsize=9, color='white', 
            ha='left', va='center', family='DejaVu Sans')
    
    # Logo Football Decoded in lower right corner
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.5, 0.025, 0.4, 0.16])  # [x, y, width, height] - back to original size
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        ax.text(5.75, 0.5, "Football Decoded", fontsize=10, color='white', 
                fontweight='bold', ha='center', va='center', family='DejaVu Sans')
    
    # "Created by Jaime Oriol" below the logo
    ax.text(5.95, 0.65, "Created by Jaime Oriol", fontsize=11, color='white', 
            fontweight='bold', ha='center', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def combine_radar_and_table(radar_path, table_path, output_path='combined_visualization.png', radar_type='auto'):
    """
    Combine radar chart and statistical table with appropriate dimensions.
    
    Creates unified visualization by combining radar chart and statistical
    table with dimensions optimized for the specific radar type.
    
    Features:
    - Automatic radar type detection or manual specification
    - Dimension system adapted to swarm vs traditional radar
    - High-quality resampling for professional appearance
    - Seamless integration with unified background
    - Optimal layout for comparative analysis
    
    Args:
        radar_path: Path to radar chart image file
        table_path: Path to statistical table image file
        output_path: Path for combined output image
        radar_type: 'auto', 'swarm', or 'traditional' - type of radar to combine
        
    Returns:
        Path to saved combined visualization
        
    Note:
        Uses LANCZOS resampling for high-quality scaling
        Auto-detection based on image dimensions
        Background color maintained for visual consistency
    """
    
    # Load individual components
    radar_img = Image.open(radar_path)
    table_img = Image.open(table_path)
    
    # Detect radar type if auto
    if radar_type == 'auto':
        radar_width, radar_height = radar_img.size
        aspect_ratio = radar_width / radar_height
        
        # Traditional radar has more square aspect (9x10 = 0.9)
        # Swarm radar is more rectangular (different proportions)
        if 0.8 <= aspect_ratio <= 1.0:
            radar_type = 'traditional'
        else:
            radar_type = 'swarm'
    
    # Select appropriate dimensions based on radar type
    if radar_type == 'traditional':
        total_size = TRADITIONAL_TOTAL_SIZE
        radar_size = TRADITIONAL_RADAR_SIZE
        table_size = TRADITIONAL_TABLE_SIZE
        table_x_offset = TRADITIONAL_RADAR_SIZE[0]  # Position table after radar
    else:  # swarm or fallback
        total_size = SWARM_TOTAL_SIZE
        radar_size = SWARM_RADAR_SIZE
        table_size = SWARM_TABLE_SIZE
        table_x_offset = SWARM_RADAR_SIZE[0]  # Position table after radar
    
    # Resize to exact dimensions with high-quality resampling
    radar_resized = radar_img.resize(radar_size, Image.Resampling.LANCZOS)
    table_resized = table_img.resize(table_size, Image.Resampling.LANCZOS)
    
    # Create combined canvas with appropriate dimensions and consistent background
    combined = Image.new('RGB', total_size, color=BACKGROUND_COLOR)
    combined.paste(radar_resized, (0, 0))              # Radar on left side
    combined.paste(table_resized, (table_x_offset, 0))  # Table on right side
    
    # Save with high DPI for professional quality
    combined.save(output_path, dpi=(300, 300))
    
    return output_path