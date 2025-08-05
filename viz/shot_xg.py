# shot_xg_viz.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize
from mplsoccer.pitch import VerticalPitch
from PIL import Image
import os

# Configuración visual global
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def plot_shot_xg(csv_path, filter_by='all', logo_path=None, season='2024-2025', 
                 home_logo_path=None, away_logo_path=None):
    """
    Plot xG visualization from shot data CSV.
    
    Args:
        csv_path: Path to shots CSV file
        filter_by: 'all', team name, or player name
        logo_path: Path to logo image
        season: Season string for subtitle
    """
    # Read data
    shots_df = pd.read_csv(csv_path)
    
    # Setup colormap
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Get competition/teams info
    teams = shots_df['team'].unique()
    comp_name = f"{teams[0]} vs {teams[1]}" if len(teams) == 2 else teams[0]
    
    # Filter logic - IGUAL QUE ORIGINAL
    comp_selected = 0
    if filter_by.lower() == 'all':
        selected_shots = shots_df
        comp_selected = 1
    elif filter_by in shots_df['team'].values:
        selected_shots = shots_df[shots_df['team'] == filter_by]
        comp_selected = 0
    elif filter_by in shots_df['player'].values:
        selected_shots = shots_df[shots_df['player'] == filter_by]
        comp_selected = 0
    else:
        return print(f"No data found for: {filter_by}")
    
    # Convert data format
    selected_shots = selected_shots.copy()
    selected_shots['header_tag'] = (selected_shots['body_part'] == 'Head').astype(int)
    selected_shots['goal'] = selected_shots['is_goal'].astype(int)
    
    # Convert coordinates to yards
    selected_shots['x_yards'] = selected_shots['x'] * 0.6  # 0-100 to 0-60 yards
    selected_shots['c_yards'] = (selected_shots['y'] - 50) * 0.8  # 0-100 to -40 to 40 yards
    
    # Separate dataframes
    selected_ground_shots = selected_shots[selected_shots['header_tag']==0]
    selected_ground_goals = selected_ground_shots[selected_ground_shots['goal']==1]
    selected_headers = selected_shots[selected_shots['header_tag']==1]
    selected_headed_goals = selected_headers[selected_headers['goal']==1]
    
    # Find extremes
    lowest_xg_goal = selected_shots[selected_shots['goal']==1].sort_values('xg').head(1)
    highest_xg_miss = selected_shots[selected_shots['goal']==0].sort_values('xg', ascending=False).head(1)
    
    # Plot setup - EXACTAMENTE IGUAL
    mpl.rcParams['xtick.color'] = "white"
    mpl.rcParams['ytick.color'] = "white"
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    
    pitch = VerticalPitch(half=True, pitch_color=PITCH_COLOR, line_color='white', linewidth=1, stripe=False)
    fig, ax = pitch.grid(nrows=1, ncols=1, title_height=0.03, grid_height=0.7, endnote_height=0.05, axis=False)
    fig.set_size_inches(9, 7)
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Plot ground shots
    if not selected_ground_shots.empty:
        ax['pitch'].scatter(80/2 + selected_ground_shots['c_yards'], 120 - selected_ground_shots['x_yards'], 
                           marker='h', s=200, alpha=0.2, c=selected_ground_shots['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=2)
    
    if not selected_ground_goals.empty:
        p1 = ax['pitch'].scatter(80/2 + selected_ground_goals['c_yards'], 120 - selected_ground_goals['x_yards'], 
                                marker='h', s=200, c=selected_ground_goals['xg'], 
                                edgecolors='w', lw=2, vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=2)
    
    # Plot headers
    if not selected_headers.empty:
        ax['pitch'].scatter(80/2 + selected_headers['c_yards'], 120 - selected_headers['x_yards'], 
                           marker='o', s=200, alpha=0.2, c=selected_headers['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=2)
    
    if not selected_headed_goals.empty:
        ax['pitch'].scatter(80/2 + selected_headed_goals['c_yards'], 120 - selected_headed_goals['x_yards'], 
                           marker='o', s=200, c=selected_headed_goals['xg'], 
                           edgecolors='w', lw=2, vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=2)
    
    ax['pitch'].set_ylim([59.9, 125])
    
    # Plot extremes
    if not highest_xg_miss.empty:
        highxg_marker = 'o' if highest_xg_miss['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(80/2 + highest_xg_miss['c_yards'].iloc[0], 120 - highest_xg_miss['x_yards'].iloc[0], 
                           marker=highxg_marker, s=200, c='r', edgecolors='grey', 
                           lw=2.5, vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=3)
    
    if not lowest_xg_goal.empty:
        lowxg_marker = 'o' if lowest_xg_goal['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(80/2 + lowest_xg_goal['c_yards'].iloc[0], 120 - lowest_xg_goal['x_yards'].iloc[0], 
                           marker=lowxg_marker, s=200, c='g', edgecolors='w', 
                           lw=2.5, vmin=-0.04, vmax=0.4, cmap=node_cmap, zorder=3)
    
    # Colorbar - MISMA POSICIÓN
    if 'p1' in locals():
        cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
        cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5, family='serif')
    
    # Legend - EXACTAMENTE IGUAL
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])
    
    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.2, marker='o', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Foot", color="w", family='serif')
    legend_ax.text(0.35, 0.11, "Header", color="w", family='serif')
    
    # Usar color del medio del colormap en lugar de purple
    mid_color = node_cmap(0.5)
    legend_ax.scatter(1.3, 0.7, marker='h', s=200, c=mid_color, edgecolors='w', lw=2)
    legend_ax.scatter(1.3, 0.2, marker='h', alpha=0.2, s=200, c=mid_color, edgecolors='w')
    legend_ax.text(1.45, 0.61, "Goal", color="w", family='serif')
    legend_ax.text(1.465, 0.11, "No Goal", color="w", family='serif')
    
    legend_ax.scatter(2.4, 0.7, marker='h', s=200, c='g', edgecolors='w', lw=2.5)
    legend_ax.scatter(2.4, 0.2, marker='h', s=200, c='r', edgecolors='grey', lw=2.5)
    legend_ax.text(2.55, 0.61, "Lowest xG Goal", color="w", family='serif')
    legend_ax.text(2.565, 0.11, "Highest xG Miss", color="w", family='serif')
    
    # Title text - POSICIÓN IZQUIERDA
    subtitle_text = comp_name
    subsubtitle_text = season
    
    if comp_selected == 1:
        title_text = "Expected Goals"
    elif comp_selected == 0:
        title_text = f"{filter_by} Expected Goals"
    
    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', family='serif')
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=14, color='w', family='serif')
    fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', family='serif')
    
    # Stats - MISMAS POSICIONES
    if selected_shots['goal'].sum() - selected_shots['xg'].sum() > 0:
        sign = '+'
    else:
        sign = ''
    
    fig.text(0.65, 0.925, "Shots:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.65, 0.9, "xG:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.65, 0.875, "Goals:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', family='serif')
    
    fig.text(0.73, 0.925, f"{int(selected_shots.count()[0])}", fontweight="regular", fontsize=10, color='w', family='serif')
    fig.text(0.73, 0.9, f"{round(selected_shots['xg'].sum(), 1)}", fontweight="regular", fontsize=10, color='w', family='serif')
    fig.text(0.73, 0.875, f"{int(selected_shots['goal'].sum())}", fontweight="regular", fontsize=10, color='w', family='serif')
    
    # Evitar división por cero
    xg_sum = selected_shots['xg'].sum()
    if xg_sum > 0:
        perf_pct = int(round(100*(selected_shots['goal'].sum()-xg_sum)/xg_sum, 0))
    else:
        perf_pct = 0
    fig.text(0.73, 0.85, f"{sign}{perf_pct}%", fontweight="regular", fontsize=10, color='w', family='serif')
    
    fig.text(0.79, 0.927, "xG/shot:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.79, 0.9, "Goal/shot:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.79, 0.875, "L xG Goal:", fontweight="bold", fontsize=10, color='w', family='serif')
    fig.text(0.79, 0.85, "H xG Miss:", fontweight="bold", fontsize=10, color='w', family='serif')
    
    shot_count = selected_shots.count()[0]
    fig.text(0.89, 0.925, f"{round(selected_shots['xg'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', family='serif')
    fig.text(0.89, 0.9, f"{round(selected_shots['goal'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', family='serif')
    fig.text(0.89, 0.875, f"{round(lowest_xg_goal['xg'].iloc[0], 2)}" if not lowest_xg_goal.empty else "N/A", fontweight="regular", fontsize=10, color='w', family='serif')
    fig.text(0.89, 0.85, f"{round(highest_xg_miss['xg'].iloc[0], 2)}" if not highest_xg_miss.empty else "N/A", fontweight="regular", fontsize=10, color='w', family='serif')
    
    # Footer - Adaptado
    fig.text(0.5, 0.02, "Created by Jaime Oriol. Football Decoded",
             fontstyle="italic", ha="center", fontsize=9, color="white", family='serif')
    
    # Logo - MISMA POSICIÓN Y TAMAÑO
    if logo_path:
        ax = fig.add_axes([0.02, 0.8, 0.2, 0.2])
        ax.axis("off")
        try:
            img = Image.open(logo_path)
            ax.imshow(img)
        except:
            pass
    
    plt.tight_layout()
    return fig