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
from mplsoccer.pitch import VerticalPitch
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
        except:
            pass  # Graceful failure if logo unavailable
    
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
            except:
                pass  # Graceful failure if logo unavailable
        
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
        logo_ax = fig.add_axes([0.575, 0.025, 0.4, 0.16])  # [x, y, width, height] - back to original size
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        ax.text(6.5, 0.5, "Football Decoded", fontsize=10, color='white', 
                fontweight='bold', ha='center', va='center', family='DejaVu Sans')
    
    # "Created by Jaime Oriol" below the logo
    ax.text(6.7, 0.65, "Created by Jaime Oriol", fontsize=10, color='white', 
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

def create_minimal_stats_table(player_name, team_name, metrics_data, metrics_titles, 
                               save_path='minimal_stats.png', show_plot=True, player_image_path=None):
    """
    Create minimal statistical table for notebook analysis.
    
    Simple, clean statistical table showing player name, team, and 8-12 metrics
    without percentiles, logos, or decorative elements.
    
    Args:
        player_name: Player name string
        team_name: Team name string  
        metrics_data: List of 8-12 numerical values
        metrics_titles: List of 8-12 metric display names
        save_path: Output file path
        show_plot: Whether to display the plot
        player_image_path: Optional path to player image file
        
    Returns:
        Path to saved visualization file
    """
    # Validate inputs
    if len(metrics_data) != len(metrics_titles):
        raise ValueError("metrics_data and metrics_titles must have same length")
    if not (8 <= len(metrics_data) <= 12):
        raise ValueError("Must provide between 8 and 12 metrics")
    
    # Setup figure - increased size for better balance
    fig, ax = plt.subplots(figsize=(6, 7))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, len(metrics_data) + 3)
    ax.axis('off')
    
    # Header with player and team - moved to right to make space for image
    ax.text(1.4, len(metrics_data) + 1.4, player_name, fontsize=14, color='white', 
            fontweight='bold', ha='left', va='center', family='DejaVu Sans')
    ax.text(1.4, len(metrics_data) + 0.9, team_name, fontsize=10, color='white', 
            ha='left', va='center', family='DejaVu Sans')
    
    # Player image in top left if provided
    if player_image_path and os.path.exists(player_image_path):
        try:
            player_img = Image.open(player_image_path)
            player_ax = fig.add_axes([0.075, 0.825, 0.20, 0.15])  # [x, y, width, height] - top left
            player_ax.imshow(player_img)
            player_ax.axis('off')
        except Exception as e:
            pass  # Skip image if loading fails
    
    # Logo in top right corner
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.575, 0.75, 0.3, 0.25])  # [x, y, width, height] - top right, double size
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        pass  # Skip logo if not found
    
    # Stats table - more compact
    for i, (title, value) in enumerate(zip(metrics_titles, metrics_data)):
        y_pos = len(metrics_data) - i
        
        # Alternating row background - narrower
        if i % 2 == 0:
            rect = Rectangle((0.3, y_pos - 0.4), 4.4, 0.8, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        # Metric name (left) - closer to center
        ax.text(0.5, y_pos, title, fontsize=11, color='white', 
                ha='left', va='center', family='DejaVu Sans', fontweight='bold')
        
        # Value (right) - much closer to names
        if isinstance(value, float):
            display_value = f"{value:.2f}"
        else:
            display_value = str(value)
            
        ax.text(4.2, y_pos, display_value, fontsize=11, color='white', 
                ha='right', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def create_enriched_stats_table(player_name, team_name, enriched_metrics, 
                                save_path='enriched_stats.png', show_plot=True, player_image_path=None):
    """
    Create enriched statistical table with success/attempt format.
    
    Enhanced version showing metrics as "completed/attempted percentage%" format
    (e.g., "26/30 87%") for better context and professional appearance.
    
    Args:
        player_name: Player name string
        team_name: Team name string  
        enriched_metrics: List of tuples (metric_name, formatted_value)
        save_path: Output file path
        show_plot: Whether to display the plot
        player_image_path: Optional path to player image file
        
    Returns:
        Path to saved visualization file
    """
    # Validate inputs
    if not (8 <= len(enriched_metrics) <= 12):
        raise ValueError("Must provide between 8 and 12 enriched metrics")
    
    # Setup figure - increased size for better balance
    fig, ax = plt.subplots(figsize=(6, 7))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, len(enriched_metrics) + 3)
    ax.axis('off')
    
    # Header with player and team - moved to right to make space for image
    ax.text(1.4, len(enriched_metrics) + 1.4, player_name, fontsize=14, color='white', 
            fontweight='bold', ha='left', va='center', family='DejaVu Sans')
    ax.text(1.4, len(enriched_metrics) + 0.9, team_name, fontsize=10, color='white', 
            ha='left', va='center', family='DejaVu Sans')
    
    # Player image in top left if provided
    if player_image_path and os.path.exists(player_image_path):
        try:
            player_img = Image.open(player_image_path)
            player_ax = fig.add_axes([0.075, 0.825, 0.20, 0.15])  # [x, y, width, height] - top left
            player_ax.imshow(player_img)
            player_ax.axis('off')
        except Exception as e:
            pass  # Skip image if loading fails
    
    # Logo in top right corner
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.575, 0.75, 0.3, 0.25])  # [x, y, width, height] - top right, double size
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        pass  # Skip logo if not found
    
    # Stats table - enriched format
    for i, (metric_name, metric_value) in enumerate(enriched_metrics):
        y_pos = len(enriched_metrics) - i
        
        # Alternating row background - narrower
        if i % 2 == 0:
            rect = Rectangle((0.3, y_pos - 0.4), 4.4, 0.8, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        # Metric name (left) - closer to center
        ax.text(0.5, y_pos, metric_name, fontsize=11, color='white', 
                ha='left', va='center', family='DejaVu Sans', fontweight='bold')
        
        # Enriched value (right) - much closer to names
        ax.text(4.2, y_pos, metric_value, fontsize=11, color='white', 
                ha='right', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def create_spatial_actions_chart(events_df, player_name, save_path='spatial_actions.png', show_plot=True):
    """
    Create simplified spatial chart: only successful vs unsuccessful actions.
    
    Uses colors from pass_network.py: deepskyblue for successful, white for failed.
    Dimensions sized to match total stats table height.
    
    Args:
        events_df: DataFrame with match events
        player_name: Name of player to analyze
        save_path: Output file path
        show_plot: Whether to display the plot
        
    Returns:
        Path to saved visualization file
    """
    # Filter player events with valid coordinates (exclude passes)
    player_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['event_type'] != 'Pass')  # Exclude passes - they go to separate chart
    ].copy()
    
    if len(player_events) == 0:
        raise ValueError(f"No spatial data found for player {player_name}")
    
    # Professional pitch setup - dimensions to match table height
    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR, 
        line_color='white', 
        linewidth=2, 
        pitch_type='opta'
    )
    
    # Uniform figure size for all fields
    fig, ax = pitch.draw(figsize=(4, 6))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Colors from pass_network.py
    success_color = 'deepskyblue'  # From pass_network node_cmap
    failure_color = 'white'
    
    # Separate by success/failure
    successful_actions = player_events[player_events['is_successful'] == True]
    failed_actions = player_events[player_events['is_successful'] == False]
    
    # Plot successful actions (blue)
    if len(successful_actions) > 0:
        ax.scatter(successful_actions['y'], successful_actions['x'], 
                  c=success_color, s=60, marker='o', alpha=0.8, 
                  edgecolors='white', linewidths=1, zorder=3)
    
    # Plot failed actions (white)
    if len(failed_actions) > 0:
        ax.scatter(failed_actions['y'], failed_actions['x'], 
                  c=failure_color, s=60, marker='o', alpha=0.8, 
                  edgecolors='black', linewidths=1, zorder=3)
    
    # Simple legend
    from matplotlib.lines import Line2D
    legend_handles = []
    
    if len(successful_actions) > 0:
        legend_handles.append(Line2D([0], [0], marker='o', color='w', 
                                   markerfacecolor=success_color, markersize=8, 
                                   markeredgecolor='white', markeredgewidth=1))
    
    if len(failed_actions) > 0:
        legend_handles.append(Line2D([0], [0], marker='o', color='w', 
                                   markerfacecolor=failure_color, markersize=8, 
                                   markeredgecolor='black', markeredgewidth=1))
    
    legend_labels = []
    if len(successful_actions) > 0:
        legend_labels.append(f'Ganadas ({len(successful_actions)})')
    if len(failed_actions) > 0:
        legend_labels.append(f'Perdidas ({len(failed_actions)})')
    
    if legend_handles:
        ax.legend(legend_handles, legend_labels, 
                 loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2,
                 frameon=False, fontsize=9, 
                 labelcolor='white', prop={'family': 'DejaVu Sans'})
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def create_spatial_passes_chart(events_df, player_name, save_path='spatial_passes.png', show_plot=True):
    """
    Create professional spatial chart showing player pass distribution with directional arrows.
    
    Uses mplsoccer VerticalPitch with pass flow arrows matching pass_network.py colors.
    Shows pass flow with directional arrows like in the reference image.
    
    Args:
        events_df: DataFrame with match events
        player_name: Name of player to analyze
        save_path: Output file path
        show_plot: Whether to display the plot
        
    Returns:
        Path to saved visualization file
    """
    # Filter player pass events with valid coordinates and end coordinates
    pass_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['event_type'] == 'Pass') &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['end_x'].notna()) & 
        (events_df['end_y'].notna())
    ].copy()
    
    if len(pass_events) == 0:
        raise ValueError(f"No pass data found for player {player_name}")
    
    # Professional pitch setup - uniform dimensions
    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR, 
        line_color='white', 
        linewidth=2, 
        pitch_type='opta'
    )
    
    fig, ax = pitch.draw(figsize=(4, 6))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Colors from pass_network.py
    success_color = 'deepskyblue'  # From pass_network node_cmap - successful passes
    failure_color = 'white'        # Failed passes
    
    # Separate successful and unsuccessful passes
    successful_passes = pass_events[pass_events['is_successful'] == True]
    unsuccessful_passes = pass_events[pass_events['is_successful'] == False]
    
    # Draw arrows for successful passes (sample to avoid clutter)
    if len(successful_passes) > 0:
        sample_passes = successful_passes.sample(min(25, len(successful_passes)))
        for _, pass_event in sample_passes.iterrows():
            start_y = pass_event['y']
            start_x = pass_event['x'] 
            end_y = pass_event['end_y']
            end_x = pass_event['end_x']
            
            # Draw arrow from start to end position
            dx = end_x - start_x
            dy = end_y - start_y
            
            ax.annotate('', xy=(end_y, end_x), xytext=(start_y, start_x),
                       arrowprops=dict(arrowstyle='->', color=success_color, alpha=0.6,
                                     lw=1.5, connectionstyle="arc3,rad=0.1"))
    
    # Draw arrows for unsuccessful passes (smaller sample)
    if len(unsuccessful_passes) > 0:
        sample_fails = unsuccessful_passes.sample(min(10, len(unsuccessful_passes)))
        for _, pass_event in sample_fails.iterrows():
            start_y = pass_event['y']
            start_x = pass_event['x'] 
            end_y = pass_event['end_y']
            end_x = pass_event['end_x']
            
            # Draw arrow from start to end position
            ax.annotate('', xy=(end_y, end_x), xytext=(start_y, start_x),
                       arrowprops=dict(arrowstyle='->', color=failure_color, alpha=0.8,
                                     lw=1.2, connectionstyle="arc3,rad=0.1"))
    
    # Legend with pass_network.py colors
    from matplotlib.lines import Line2D
    legend_handles = []
    legend_labels = []
    
    if len(successful_passes) > 0:
        legend_handles.append(Line2D([0], [0], color=success_color, linewidth=2, 
                                   alpha=0.8, marker='>', markersize=6))
        legend_labels.append(f'Precisos ({len(successful_passes)})')
    
    if len(unsuccessful_passes) > 0:
        legend_handles.append(Line2D([0], [0], color=failure_color, linewidth=2, 
                                   alpha=0.8, marker='>', markersize=6))
        legend_labels.append(f'No precisos ({len(unsuccessful_passes)})')
    
    if legend_handles:
        ax.legend(legend_handles, legend_labels, 
                 loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2,
                 frameon=False, fontsize=9,
                 labelcolor='white', prop={'family': 'DejaVu Sans'})
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def create_combined_player_analysis(player_name, team_name, enriched_metrics, events_df, 
                                   player_image_path=None, save_path='combined_analysis.png', show_plot=True):
    """
    Create combined professional visualization with enriched stats table and spatial charts.
    
    Combines enriched stats table (left) with two vertical spatial charts (right) 
    in a side-by-side layout matching professional FootballDecoded standards.
    
    Args:
        player_name: Player name string
        team_name: Team name string
        enriched_metrics: List of tuples (metric_name, formatted_value)
        events_df: DataFrame with match events
        player_image_path: Optional path to player image file
        save_path: Output file path
        show_plot: Whether to display the plot
        
    Returns:
        Path to saved combined visualization
    """
    # Create individual components
    table_path = 'temp_enriched_table.png'
    actions_path = 'temp_spatial_actions.png'
    passes_path = 'temp_spatial_passes.png'
    
    # Generate individual charts
    create_enriched_stats_table(player_name, team_name, enriched_metrics, 
                                table_path, False, player_image_path)
    create_spatial_actions_chart(events_df, player_name, actions_path, False)
    create_spatial_passes_chart(events_df, player_name, passes_path, False)
    
    # Load images
    table_img = Image.open(table_path)
    actions_img = Image.open(actions_path)
    passes_img = Image.open(passes_path)
    
    # Professional layout calculations for vertical fields side by side
    table_width, table_height = table_img.size
    chart_width, chart_height = actions_img.size
    
    # Create combined canvas - charts side by side, not stacked
    charts_total_width = chart_width * 2  # Two charts side by side
    total_width = table_width + charts_total_width
    total_height = max(table_height, chart_height)
    
    combined = Image.new('RGB', (total_width, total_height), color=BACKGROUND_COLOR)
    
    # Paste table on left (centered vertically)
    table_y = (total_height - table_height) // 2
    combined.paste(table_img, (0, table_y))
    
    # Paste charts side by side on right (centered vertically)
    charts_start_x = table_width
    chart_y = (total_height - chart_height) // 2
    
    # Actions chart (left of the two charts)
    combined.paste(actions_img, (charts_start_x, chart_y))
    
    # Passes chart (right of the two charts)
    combined.paste(passes_img, (charts_start_x + chart_width, chart_y))
    
    # Save combined image with proper DPI
    combined.save(save_path, dpi=(300, 300))
    
    # Clean up temporary files
    os.remove(table_path)
    os.remove(actions_path)
    os.remove(passes_path)
    
    if show_plot:
        combined.show()
    
    return save_path

def extract_enriched_stats(player_name, events_df, aggregates_df):
    """
    Extract enriched statistics with success/attempt format for a player.
    
    Combines data from match events and aggregates to create enriched metrics
    showing both raw counts and success rates in format "completed/attempted percentage%".
    
    Args:
        player_name: Name of player to analyze
        events_df: DataFrame with match events
        aggregates_df: DataFrame with match aggregates
        
    Returns:
        List of tuples (metric_name, formatted_value)
    """
    # Get player aggregate data
    player_agg = aggregates_df[
        aggregates_df['entity_name'].str.contains(player_name, case=False, na=False)
    ]
    if len(player_agg) == 0:
        raise ValueError(f"No aggregate data found for player {player_name}")
    player_agg = player_agg.iloc[0]
    
    # Filter player events
    player_events = events_df[events_df['player'] == player_name]
    
    enriched_metrics = []
    
    # 1. Passes (from aggregates - more reliable)
    passes_comp = int(player_agg.get('passes_completed', 0))
    passes_att = int(player_agg.get('passes_attempted', 0))
    pass_pct = player_agg.get('pass_completion_pct', 0)
    enriched_metrics.append(("Passes", f"{passes_comp}/{passes_att} {pass_pct:.0f}%"))
    
    # 2. Shots (shots on target first: Goals + SavedShot)
    goals = len(player_events[player_events['event_type'] == 'Goal'])
    saved_shots = len(player_events[player_events['event_type'] == 'SavedShot'])
    missed_shots = len(player_events[player_events['event_type'] == 'MissedShot'])
    
    shots_on_target = goals + saved_shots  # Shots on target (a puerta)
    shots_total = goals + saved_shots + missed_shots
    shot_accuracy = (shots_on_target / shots_total * 100) if shots_total > 0 else 0
    enriched_metrics.append(("Shots", f"{shots_on_target}/{shots_total} {shot_accuracy:.0f}%"))
    
    # 3. Take-ons
    takeons_total = len(player_events[player_events['event_type'] == 'TakeOn'])
    takeons_successful = len(player_events[
        (player_events['event_type'] == 'TakeOn') & 
        (player_events['is_successful'] == True)
    ])
    takeon_success = (takeons_successful / takeons_total * 100) if takeons_total > 0 else 0
    enriched_metrics.append(("Take Ons", f"{takeons_successful}/{takeons_total} {takeon_success:.0f}%"))
    
    # 4. Tackles
    tackles_total = len(player_events[player_events['event_type'] == 'Tackle'])
    tackles_successful = len(player_events[
        (player_events['event_type'] == 'Tackle') & 
        (player_events['is_successful'] == True)
    ])
    tackle_success = (tackles_successful / tackles_total * 100) if tackles_total > 0 else 0
    enriched_metrics.append(("Tackles", f"{tackles_successful}/{tackles_total} {tackle_success:.0f}%"))
    
    # 5. Aerial Duels
    aerials_total = len(player_events[player_events['event_type'] == 'Aerial'])
    aerials_won = len(player_events[
        (player_events['event_type'] == 'Aerial') & 
        (player_events['is_successful'] == True)
    ])
    aerial_success = (aerials_won / aerials_total * 100) if aerials_total > 0 else 0
    enriched_metrics.append(("Aerial Duels", f"{aerials_won}/{aerials_total} {aerial_success:.0f}%"))
    
    # 6. Goals and xG
    xg_total = player_events['xg'].fillna(0).sum()
    enriched_metrics.append(("Goals / xG", f"{goals} / {xg_total:.2f}"))
    
    # 7. Minutes
    minutes = int(player_agg.get('minutes_active', 0))
    enriched_metrics.append(("Minutes", f"{minutes}"))
    
    # 8. xThreat
    xthreat = player_agg.get('xthreat_total', 0)
    enriched_metrics.append(("xThreat", f"{xthreat:.2f}"))
    
    # 9. Progressive Actions
    prog_passes = int(player_agg.get('progressive_passes', 0))
    prog_carries = int(player_agg.get('progressive_carries', 0))
    enriched_metrics.append(("Progressive", f"{prog_passes}p / {prog_carries}c"))
    
    # 10. Box Entries
    box_entries = int(player_agg.get('box_entries', 0))
    enriched_metrics.append(("Box Entries", f"{box_entries}"))
    
    return enriched_metrics

def create_spatial_charts_by_halves_complete(events_df, player_name, save_path_prefix='spatial_charts', show_plot=False):
    """
    Create 4 spatial charts: actions and passes for both halves.
    
    Generates 4 individual charts:
    - Actions 1st half (1-44 mins): ganadas/perdidas
    - Passes 1st half (1-44 mins): with arrows
    - Actions 2nd half (46-90 mins): ganadas/perdidas  
    - Passes 2nd half (46-90 mins): with arrows
    
    Args:
        events_df: DataFrame with match events
        player_name: Name of player to analyze
        save_path_prefix: Prefix for saved files
        show_plot: Whether to display the plots
        
    Returns:
        Dictionary with paths to 4 generated charts
    """
    paths = {}
    
    # 1. Actions 1st half
    actions_1st_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] <= 44) &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['event_type'] != 'Pass')
    ].copy()
    
    if len(actions_1st_events) > 0:
        pitch = VerticalPitch(pitch_color=BACKGROUND_COLOR, line_color='white', linewidth=2, pitch_type='opta')
        fig, ax = pitch.draw(figsize=(2.5, 3.5))
        fig.set_facecolor(BACKGROUND_COLOR)
        
        successful_actions = actions_1st_events[actions_1st_events['is_successful'] == True]
        failed_actions = actions_1st_events[actions_1st_events['is_successful'] == False]
        
        if len(successful_actions) > 0:
            ax.scatter(successful_actions['y'], successful_actions['x'], 
                      c='deepskyblue', s=60, marker='o', alpha=0.8, 
                      edgecolors='white', linewidths=1, zorder=3)
        
        if len(failed_actions) > 0:
            ax.scatter(failed_actions['y'], failed_actions['x'], 
                      c='white', s=60, marker='o', alpha=0.8, 
                      edgecolors='black', linewidths=1, zorder=3)
        
        ax.set_title('Acciones 1º Tiempo', color='white', fontsize=12, pad=20)
        paths['actions_1st'] = f"{save_path_prefix}_actions_1st.png"
        plt.savefig(paths['actions_1st'], dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
        if show_plot: plt.show()
        else: plt.close()
    
    # 2. Passes 1st half
    pass_1st_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] <= 44) &
        (events_df['event_type'] == 'Pass') &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['end_x'].notna()) & 
        (events_df['end_y'].notna())
    ].copy()
    
    if len(pass_1st_events) > 0:
        pitch = VerticalPitch(pitch_color=BACKGROUND_COLOR, line_color='white', linewidth=2, pitch_type='opta')
        fig, ax = pitch.draw(figsize=(2.5, 3.5))
        fig.set_facecolor(BACKGROUND_COLOR)
        
        successful_passes = pass_1st_events[pass_1st_events['is_successful'] == True]
        unsuccessful_passes = pass_1st_events[pass_1st_events['is_successful'] == False]
        
        # Draw arrows for successful passes (deepskyblue, more visible)
        if len(successful_passes) > 0:
            sample_passes = successful_passes.sample(min(15, len(successful_passes)))
            for _, pass_event in sample_passes.iterrows():
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='deepskyblue', alpha=0.9, 
                                         lw=2.0, connectionstyle="arc3,rad=0.05"))
        
        # Draw arrows for unsuccessful passes (white with black edge for contrast)
        if len(unsuccessful_passes) > 0:
            sample_fails = unsuccessful_passes.sample(min(8, len(unsuccessful_passes)))
            for _, pass_event in sample_fails.iterrows():
                # First draw black outline
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='black', alpha=1.0, 
                                         lw=2.5, connectionstyle="arc3,rad=0.05"))
                # Then draw white arrow on top
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='white', alpha=0.9, 
                                         lw=1.8, connectionstyle="arc3,rad=0.05"))
        
        ax.set_title('Pases 1º Tiempo', color='white', fontsize=12, pad=20)
        paths['passes_1st'] = f"{save_path_prefix}_passes_1st.png"
        plt.savefig(paths['passes_1st'], dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
        if show_plot: plt.show()
        else: plt.close()
    
    # 3. Actions 2nd half
    actions_2nd_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] >= 46) &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['event_type'] != 'Pass')
    ].copy()
    
    if len(actions_2nd_events) > 0:
        pitch = VerticalPitch(pitch_color=BACKGROUND_COLOR, line_color='white', linewidth=2, pitch_type='opta')
        fig, ax = pitch.draw(figsize=(2.5, 3.5))
        fig.set_facecolor(BACKGROUND_COLOR)
        
        successful_actions = actions_2nd_events[actions_2nd_events['is_successful'] == True]
        failed_actions = actions_2nd_events[actions_2nd_events['is_successful'] == False]
        
        if len(successful_actions) > 0:
            ax.scatter(successful_actions['y'], successful_actions['x'], 
                      c='deepskyblue', s=60, marker='o', alpha=0.8, 
                      edgecolors='white', linewidths=1, zorder=3)
        
        if len(failed_actions) > 0:
            ax.scatter(failed_actions['y'], failed_actions['x'], 
                      c='white', s=60, marker='o', alpha=0.8, 
                      edgecolors='black', linewidths=1, zorder=3)
        
        ax.set_title('Acciones 2º Tiempo', color='white', fontsize=12, pad=20)
        paths['actions_2nd'] = f"{save_path_prefix}_actions_2nd.png"
        plt.savefig(paths['actions_2nd'], dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
        if show_plot: plt.show()
        else: plt.close()
    
    # 4. Passes 2nd half
    pass_2nd_events = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] >= 46) &
        (events_df['event_type'] == 'Pass') &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['end_x'].notna()) & 
        (events_df['end_y'].notna())
    ].copy()
    
    if len(pass_2nd_events) > 0:
        pitch = VerticalPitch(pitch_color=BACKGROUND_COLOR, line_color='white', linewidth=2, pitch_type='opta')
        fig, ax = pitch.draw(figsize=(2.5, 3.5))
        fig.set_facecolor(BACKGROUND_COLOR)
        
        successful_passes = pass_2nd_events[pass_2nd_events['is_successful'] == True]
        unsuccessful_passes = pass_2nd_events[pass_2nd_events['is_successful'] == False]
        
        # Draw arrows for successful passes (deepskyblue, more visible)
        if len(successful_passes) > 0:
            sample_passes = successful_passes.sample(min(15, len(successful_passes)))
            for _, pass_event in sample_passes.iterrows():
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='deepskyblue', alpha=0.9, 
                                         lw=2.0, connectionstyle="arc3,rad=0.05"))
        
        # Draw arrows for unsuccessful passes (white with black edge for contrast)
        if len(unsuccessful_passes) > 0:
            sample_fails = unsuccessful_passes.sample(min(8, len(unsuccessful_passes)))
            for _, pass_event in sample_fails.iterrows():
                # First draw black outline
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='black', alpha=1.0, 
                                         lw=2.5, connectionstyle="arc3,rad=0.05"))
                # Then draw white arrow on top
                ax.annotate('', xy=(pass_event['end_y'], pass_event['end_x']), 
                           xytext=(pass_event['y'], pass_event['x']),
                           arrowprops=dict(arrowstyle='->', color='white', alpha=0.9, 
                                         lw=1.8, connectionstyle="arc3,rad=0.05"))
        
        ax.set_title('Pases 2º Tiempo', color='white', fontsize=12, pad=20)
        paths['passes_2nd'] = f"{save_path_prefix}_passes_2nd.png"
        plt.savefig(paths['passes_2nd'], dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
        if show_plot: plt.show()
        else: plt.close()
    
    return paths

def create_player_analysis_complete(player_name, team_name, enriched_metrics, events_df, 
                                   player_image_path=None, save_path='complete_analysis.png', show_plot=True):
    """
    Create complete professional visualization: large stats table + 4 spatial charts (2x2).
    
    Layout: [LARGE TABLE] | [ACTIONS 1ST] [PASSES 1ST]
                          | [ACTIONS 2ND] [PASSES 2ND]
    
    Args:
        player_name: Player name string
        team_name: Team name string
        enriched_metrics: List of tuples (metric_name, formatted_value) - 8-12 metrics
        events_df: DataFrame with match events
        player_image_path: Optional path to player image file
        save_path: Output file path
        show_plot: Whether to display the plot
        
    Returns:
        Path to saved combined visualization
    """
    # Create large stats table
    table_path = 'temp_large_table.png'
    create_enriched_stats_table_large(player_name, team_name, enriched_metrics, 
                                     table_path, False, player_image_path)
    
    # Create 4 spatial charts
    charts_paths = create_spatial_charts_by_halves_complete(events_df, player_name, 
                                                           'temp_spatial', False)
    
    # Load all images
    table_img = Image.open(table_path)
    
    # Load spatial charts (handle missing charts gracefully)
    chart_images = {}
    for key in ['actions_1st', 'passes_1st', 'actions_2nd', 'passes_2nd']:
        if key in charts_paths and os.path.exists(charts_paths[key]):
            chart_images[key] = Image.open(charts_paths[key])
        else:
            # Create placeholder blank chart if missing (smaller size)
            chart_images[key] = Image.new('RGB', (500, 700), color=BACKGROUND_COLOR)
    
    # Calculate layout dimensions
    table_width, table_height = table_img.size
    chart_width, chart_height = chart_images['actions_1st'].size  # Use actual chart dimensions
    
    # Total dimensions: table + 2x2 grid of charts
    charts_grid_width = chart_width * 2
    charts_grid_height = chart_height * 2
    
    total_width = table_width + charts_grid_width
    total_height = max(table_height, charts_grid_height)
    
    # Create combined canvas
    combined = Image.new('RGB', (total_width, total_height), color=BACKGROUND_COLOR)
    
    # Paste large table on left (centered vertically)
    table_y = (total_height - table_height) // 2
    combined.paste(table_img, (0, table_y))
    
    # Paste 4 charts in 2x2 grid on right
    charts_start_x = table_width
    
    # Top row: Actions 1st | Passes 1st
    combined.paste(chart_images['actions_1st'], (charts_start_x, 0))
    combined.paste(chart_images['passes_1st'], (charts_start_x + chart_width, 0))
    
    # Bottom row: Actions 2nd | Passes 2nd  
    combined.paste(chart_images['actions_2nd'], (charts_start_x, chart_height))
    combined.paste(chart_images['passes_2nd'], (charts_start_x + chart_width, chart_height))
    
    # Save combined image
    combined.save(save_path, dpi=(300, 300))
    
    # Clean up temporary files
    os.remove(table_path)
    for path in charts_paths.values():
        if os.path.exists(path):
            os.remove(path)
    
    if show_plot:
        combined.show()
    
    return save_path

def create_enriched_stats_table_large(player_name, team_name, enriched_metrics, 
                                     save_path='large_stats.png', show_plot=True, player_image_path=None):
    """
    Create large enriched statistical table for 4-chart layout.
    
    Larger version of enriched stats table with increased height to balance
    with 4 spatial charts in 2x2 grid layout.
    
    Args:
        player_name: Player name string
        team_name: Team name string  
        enriched_metrics: List of tuples (metric_name, formatted_value)
        save_path: Output file path
        show_plot: Whether to display the plot
        player_image_path: Optional path to player image file
        
    Returns:
        Path to saved visualization file
    """
    # Validate inputs
    if not (8 <= len(enriched_metrics) <= 12):
        raise ValueError("Must provide between 8 and 12 enriched metrics")
    
    # Setup figure - increased height for better balance with 4 charts
    fig, ax = plt.subplots(figsize=(6, 8))  # Increased from (5,5) to (6,8)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 6)  # Increased width
    ax.set_ylim(0, len(enriched_metrics) + 3)  # Increased height
    ax.axis('off')
    
    # Header with player and team
    ax.text(1.6, len(enriched_metrics) + 2, player_name, fontsize=16, color='white', 
            fontweight='bold', ha='left', va='center', family='DejaVu Sans')
    ax.text(1.6, len(enriched_metrics) + 1.4, team_name, fontsize=12, color='white', 
            ha='left', va='center', family='DejaVu Sans')
    
    # Player image in top left if provided
    if player_image_path and os.path.exists(player_image_path):
        try:
            player_img = Image.open(player_image_path)
            player_ax = fig.add_axes([0.075, 0.82, 0.22, 0.16])  # Larger image
            player_ax.imshow(player_img)
            player_ax.axis('off')
        except Exception as e:
            pass  # Skip image if loading fails
    
    # Logo in top right corner
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.55, 0.75, 0.35, 0.23])  # Larger logo
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        pass  # Skip logo if not found
    
    # Stats table - larger spacing
    for i, (metric_name, metric_value) in enumerate(enriched_metrics):
        y_pos = len(enriched_metrics) - i + 0.5
        
        # Alternating row background
        if i % 2 == 0:
            rect = Rectangle((0.4, y_pos - 0.45), 5.2, 0.9, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        # Metric name (left)
        ax.text(0.6, y_pos, metric_name, fontsize=12, color='white', 
                ha='left', va='center', family='DejaVu Sans', fontweight='bold')
        
        # Value (right)
        ax.text(5.2, y_pos, metric_value, fontsize=12, color='white', 
                ha='right', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path