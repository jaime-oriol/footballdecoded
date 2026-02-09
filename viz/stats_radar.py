"""
Statistical comparison table with percentile-based performance indicators.
Single or dual-player mode with team logos, color-coded percentiles,
and fixed dimensions for swarm_radar integration.
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

BACKGROUND_COLOR = '#313332'

def _detect_id_column(df_data):
    """Detect whether dataframe uses player or team IDs."""
    if 'unique_player_id' in df_data.columns:
        return 'unique_player_id'
    elif 'unique_team_id' in df_data.columns:
        return 'unique_team_id'
    else:
        raise ValueError("DataFrame must contain either 'unique_player_id' or 'unique_team_id' column")

def _shorten_long_name(name, max_length=13):
    """Shorten long names to Initial + Surname format (e.g., 'D. Szoboszlai')."""
    if len(name) <= max_length:
        return name
    
    parts = name.split()
    if len(parts) >= 2:
        # Return first initial + last name
        return f"{parts[0][0]}. {parts[-1]}"
    else:
        # If single name, truncate if too long
        return name[:max_length] + "..." if len(name) > max_length else name

# Fixed dimensions for radar integration alignment
SWARM_TOTAL_SIZE = (4945, 2755)
SWARM_RADAR_SIZE = (2625, 2755)
SWARM_TABLE_SIZE = (2320, 2755)

TRADITIONAL_TOTAL_SIZE = (4820, 2755)
TRADITIONAL_RADAR_SIZE = (2500, 2755)
TRADITIONAL_TABLE_SIZE = (2320, 2755)

def create_stats_table(df_data, player_1_id, metrics, metric_titles, 
                      player_2_id=None, team_colors=None, 
                      save_path='stats_table.png', show_plot=True,
                      team_logos=None, footer_text='Percentiles vs dataset'):
    """Create stats table with percentile-colored metrics. Expects '{metric}_pct' columns."""
    if team_colors is None:
        team_colors = ['#FF6B6B', '#4ECDC4']

    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    percentile_norm = Normalize(vmin=0, vmax=100)

    id_column = _detect_id_column(df_data)
    p1 = df_data[df_data[id_column] == player_1_id].iloc[0]
    p2 = None
    if player_2_id is not None:
        p2 = df_data[df_data[id_column] == player_2_id].iloc[0]

    fig = plt.figure(figsize=(7.5, 8.5), facecolor=BACKGROUND_COLOR)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 15)
    ax.axis('off')

    # Layout coordinates
    y_start = 14.5
    logo1_x, text1_x, p1_value_x, p1_pct_x = 3.0, 3.4, 4.1, 4.5
    logo2_x, text2_x, p2_value_x, p2_pct_x = 6.2, 6.2, 6.7, 7.1
    
    # Player 1 header
    team1_name = p1.get('team') or p1.get('team_name', '')
    player1_id = p1.get('unique_player_id', '')
    logo_key = player1_id if (team_logos and player1_id in team_logos) else team1_name
    if team_logos and logo_key in team_logos:
        try:
            logo = Image.open(team_logos[logo_key])
            logo_ax = fig.add_axes([logo1_x/10, (y_start-0.8)/15, 0.08, 0.08])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except Exception as e:
            print(f"Logo load error for {logo_key}: {e}")
            print(f"Path: {team_logos[logo_key]}")
    
    name1 = p1.get('player_name') or p1.get('team_name', 'Unknown')
    name1_short = _shorten_long_name(name1)
    ax.text(text1_x, y_start, name1_short, 
            fontweight='bold', fontsize=14, color=team_colors[0], ha='left', va='center', family='DejaVu Sans')
    ax.text(text1_x, y_start - 0.425, f"{p1['league']} {p1['season']}", 
            fontsize=10, color='white', alpha=0.9, ha='left', fontweight='regular', family='DejaVu Sans')
    
    # Player 2 header
    if p2 is not None:
        team2_name = p2.get('team') or p2.get('team_name', '')
        player2_id = p2.get('unique_player_id', '')
        logo_key2 = player2_id if (team_logos and player2_id in team_logos) else team2_name
        if team_logos and logo_key2 in team_logos:
            try:
                logo = Image.open(team_logos[logo_key2])
                logo_ax = fig.add_axes([logo2_x/10, (y_start-0.8)/15, 0.08, 0.08])
                logo_ax.imshow(logo)
                logo_ax.axis('off')
            except Exception as e:
                print(f"Logo load error for {logo_key2}: {e}")
                print(f"Path: {team_logos[logo_key2]}")
        
        name2 = p2.get('player_name') or p2.get('team_name', 'Unknown')
        name2_short = _shorten_long_name(name2)
        ax.text(text2_x, y_start, name2_short,
                fontweight='bold', fontsize=14, color=team_colors[1], ha='left', va='center', family='DejaVu Sans')
        ax.text(text2_x, y_start - 0.425, f"{p2['league']} {p2['season']}", 
                fontsize=10, color='white', alpha=0.9, ha='left', fontweight='regular', family='DejaVu Sans')
    # Invisible placeholders to preserve layout when single player
    if p2 is None:
        ax.text(text2_x, y_start, "", 
                fontweight='bold', fontsize=14, color='white', alpha=0, ha='left', va='center', family='DejaVu Sans')
        ax.text(text2_x, y_start - 0.425, "", 
                fontsize=10, color='white', alpha=0, ha='left', fontweight='regular', family='DejaVu Sans')
    
    y_line = y_start - 0.7
    ax.plot([0.5, 8.5], [y_line, y_line], color='grey', linewidth=0.5, alpha=0.6)
    
    # Context: minutes and matches
    y_context = y_start - 1.2
    ax.text(0.7, y_context, "Minutes Played", fontsize=10, color='white', fontweight='bold', family='DejaVu Sans')
    min1 = int(p1.get('minutes_played', 0))
    ax.text(p1_value_x, y_context, f"{min1}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    if p2 is not None:
        min2 = int(p2.get('minutes_played', 0))
        ax.text(p2_value_x, y_context, f"{min2}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    else:
        ax.text(p2_value_x, y_context, "", fontsize=11, color='white', alpha=0, ha='right', fontweight='regular', family='DejaVu Sans')
    
    y_context -= 0.4
    ax.text(0.7, y_context, "Matches Played", fontsize=10, color='white', fontweight='bold', family='DejaVu Sans')
    mat1 = int(p1.get('matches_played', 0))
    ax.text(p1_value_x, y_context, f"{mat1}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    if p2 is not None:
        mat2 = int(p2.get('matches_played', 0))
        ax.text(p2_value_x, y_context, f"{mat2}", fontsize=11, color='white', ha='right', fontweight='regular', family='DejaVu Sans')
    else:
        ax.text(p2_value_x, y_context, "", fontsize=11, color='white', alpha=0, ha='right', fontweight='regular', family='DejaVu Sans')
    
    y_line = y_context - 0.3
    ax.plot([0.5, 8.5], [y_line, y_line], color='grey', linewidth=0.5, alpha=0.6)
    
    # Metric rows
    y_metrics = y_context - 0.7
    row_height = 1.0
    
    for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
        y_pos = y_metrics - (idx * row_height)
        
        if idx % 2 == 0:
            rect = Rectangle((0.5, y_pos - 0.4), 8.0, 0.8, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        clean_title = title.replace('\n', ' ')
        ax.text(0.7, y_pos, clean_title, fontsize=10, color='white', fontweight='bold', va='center', family='DejaVu Sans')
        
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
            ax.text(p2_value_x, y_pos, "", fontsize=11, color='white', alpha=0, ha='right',
                    fontweight='regular', va='center', family='DejaVu Sans')
            ax.text(p2_pct_x, y_pos, "",
                    fontsize=10, color='white', alpha=0, ha='left', fontweight='regular', va='center', family='DejaVu Sans')
    
    footer_y = y_metrics - (len(metrics) * row_height)
    
    if len(metrics) % 2 == 1:
        rect = Rectangle((0.5, footer_y - 0.4), 8.0, 0.8, facecolor='white', alpha=0.05)
        ax.add_patch(rect)
    
    ax.text(0.7, footer_y, f"*{footer_text}", 
            fontsize=10, color='white', ha='left', style='italic', fontweight='bold', va='center', family='DejaVu Sans')
    
    # Percentile legend
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
    
    arrow_y = legend_y - 0.8
    arrow_start_x = 1.2
    arrow_end_x = 4.0
    
    ax.annotate('', xy=(arrow_end_x, arrow_y), xytext=(arrow_start_x, arrow_y),
                arrowprops=dict(arrowstyle='->', color='white', lw=1))
    
    ax.text(arrow_start_x - 0.1, arrow_y, 'LOW', fontsize=9, color='white', 
            ha='right', va='center', family='DejaVu Sans')
    ax.text(arrow_end_x + 0.1, arrow_y, 'HIGH', fontsize=9, color='white', 
            ha='left', va='center', family='DejaVu Sans')
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.5, 0.025, 0.4, 0.16])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        ax.text(5.75, 0.5, "Football Decoded", fontsize=10, color='white',
                fontweight='bold', ha='center', va='center', family='DejaVu Sans')

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
    """Combine radar chart and stats table side-by-side. Auto-detects swarm vs traditional."""
    
    radar_img = Image.open(radar_path)
    table_img = Image.open(table_path)

    if radar_type == 'auto':
        aspect_ratio = radar_img.size[0] / radar_img.size[1]
        radar_type = 'traditional' if 0.8 <= aspect_ratio <= 1.0 else 'swarm'

    if radar_type == 'traditional':
        total_size = TRADITIONAL_TOTAL_SIZE
        radar_size = TRADITIONAL_RADAR_SIZE
        table_size = TRADITIONAL_TABLE_SIZE
        table_x_offset = TRADITIONAL_RADAR_SIZE[0]
    else:
        total_size = SWARM_TOTAL_SIZE
        radar_size = SWARM_RADAR_SIZE
        table_size = SWARM_TABLE_SIZE
        table_x_offset = SWARM_RADAR_SIZE[0]

    radar_resized = radar_img.resize(radar_size, Image.Resampling.LANCZOS)
    table_resized = table_img.resize(table_size, Image.Resampling.LANCZOS)

    combined = Image.new('RGB', total_size, color=BACKGROUND_COLOR)
    combined.paste(radar_resized, (0, 0))
    combined.paste(table_resized, (table_x_offset, 0))

    combined.save(output_path, dpi=(300, 300))
    
    return output_path