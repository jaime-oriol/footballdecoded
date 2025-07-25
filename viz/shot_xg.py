# shot_xg_viz.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from mplsoccer.pitch import VerticalPitch
from PIL import Image
import requests
from io import BytesIO

def plot_shot_xg(csv_path, filter_by='all', logo_path=None, season='2024-2025'):
    """
    Plot xG visualization from shot data CSV.
    
    Args:
        csv_path: Path to shots CSV file
        filter_by: 'all', team name, or player name
        logo_path: Path to logo image (e.g., 'viz/images/barcelona.png')
        season: Season string for subtitle
    """
    # Read data
    shots_df = pd.read_csv(csv_path)
    
    # Filter shots and handle long names
    display_name = filter_by
    if filter_by.lower() == 'all':
        selected_shots = shots_df
        title_text = "Expected Goals"
    elif filter_by in shots_df['team'].values:
        selected_shots = shots_df[shots_df['team'] == filter_by]
        title_text = f"{filter_by} Expected Goals"
    elif filter_by in shots_df['player'].values:
        selected_shots = shots_df[shots_df['player'] == filter_by]
        # Check name length and use only last name if too long
        if len(filter_by) > 15:
            display_name = filter_by.split()[-1]
        title_text = f"{display_name} Expected Goals"
    else:
        return print(f"No data found for: {filter_by}")
    
    # Separate by type
    ground_shots = selected_shots[selected_shots['body_part'] != 'Head']
    ground_goals = ground_shots[ground_shots['is_goal'] == True]
    headers = selected_shots[selected_shots['body_part'] == 'Head']
    headed_goals = headers[headers['is_goal'] == True]
    
    # Find extremes
    goals = selected_shots[selected_shots['is_goal'] == True]
    misses = selected_shots[selected_shots['is_goal'] == False]
    lowest_xg_goal = goals.nsmallest(1, 'xg') if not goals.empty else pd.DataFrame()
    highest_xg_miss = misses.nlargest(1, 'xg') if not misses.empty else pd.DataFrame()
    
    # Plot setup
    mpl.rcParams.update({'xtick.color': 'white', 'ytick.color': 'white',
                         'xtick.labelsize': 10, 'ytick.labelsize': 10})
    
    pitch = VerticalPitch(half=True, pitch_color='#313332', line_color='white', linewidth=1)
    fig, ax = pitch.grid(nrows=1, ncols=1, title_height=0.03, grid_height=0.7,
                         endnote_height=0.05, axis=False)
    fig.set_size_inches(9, 7)
    fig.set_facecolor('#313332')
    
    # Convert coordinates from percentage to pitch coordinates
    def convert_coords(x, y):
        pitch_x = y * 0.8
        pitch_y = 60 + (x * 0.6)
        return pitch_x, pitch_y
    
    # Plot ground shots
    if not ground_shots.empty:
        coords = ground_shots.apply(lambda r: convert_coords(r['x'], r['y']), axis=1)
        px = [c[0] for c in coords]
        py = [c[1] for c in coords]
        ax['pitch'].scatter(px, py, marker='h', s=200, alpha=0.2, c=ground_shots['xg'].values,
                            edgecolors='w', vmin=-0.04, vmax=0.4, cmap=plt.cm.inferno, zorder=2)
    
    if not ground_goals.empty:
        coords = ground_goals.apply(lambda r: convert_coords(r['x'], r['y']), axis=1)
        px = [c[0] for c in coords]
        py = [c[1] for c in coords]
        p1 = ax['pitch'].scatter(px, py, marker='h', s=200, c=ground_goals['xg'].values,
                                 edgecolors='w', lw=2, vmin=-0.04, vmax=0.4, cmap=plt.cm.inferno, zorder=2)
    
    # Plot headers
    if not headers.empty:
        coords = headers.apply(lambda r: convert_coords(r['x'], r['y']), axis=1)
        px = [c[0] for c in coords]
        py = [c[1] for c in coords]
        ax['pitch'].scatter(px, py, marker='o', s=200, alpha=0.2, c=headers['xg'].values,
                            edgecolors='w', vmin=-0.04, vmax=0.4, cmap=plt.cm.inferno, zorder=2)
    
    if not headed_goals.empty:
        coords = headed_goals.apply(lambda r: convert_coords(r['x'], r['y']), axis=1)
        px = [c[0] for c in coords]
        py = [c[1] for c in coords]
        ax['pitch'].scatter(px, py, marker='o', s=200, c=headed_goals['xg'].values,
                            edgecolors='w', lw=2, vmin=-0.04, vmax=0.4, cmap=plt.cm.inferno, zorder=2)
    
    # Plot extremes
    if not lowest_xg_goal.empty:
        px, py = convert_coords(lowest_xg_goal['x'].iloc[0], lowest_xg_goal['y'].iloc[0])
        marker = 'o' if lowest_xg_goal['body_part'].iloc[0] == 'Head' else 'h'
        ax['pitch'].scatter(px, py, marker=marker, s=200, c='g', edgecolors='w', lw=2.5, zorder=3)
    
    if not highest_xg_miss.empty:
        px, py = convert_coords(highest_xg_miss['x'].iloc[0], highest_xg_miss['y'].iloc[0])
        marker = 'o' if highest_xg_miss['body_part'].iloc[0] == 'Head' else 'h'
        ax['pitch'].scatter(px, py, marker=marker, s=200, c='r', edgecolors='grey', lw=2.5, zorder=3)
    
    # Colorbar
    if 'p1' in locals():
        cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
        cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)
    
    # Legend
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 5])
    legend_ax.set_ylim([0, 1])
    
    legend_items = [
        (0.2, 0.7, 'h', '#313332', 'w', 1, "Foot", 0.35, 0.61),
        (0.2, 0.2, 'o', '#313332', 'w', 1, "Header", 0.35, 0.11),
        (1.3, 0.7, 'h', 'purple', 'w', 2, "Goal", 1.45, 0.61),
        (1.3, 0.2, 'h', 'purple', 'w', 0.2, "No Goal", 1.465, 0.11),
        (2.4, 0.7, 'h', 'g', 'w', 2.5, "Lowest xG Goal", 2.55, 0.61),
        (2.4, 0.2, 'h', 'r', 'grey', 2.5, "Highest xG Miss", 2.565, 0.11)
    ]
    
    for x, y, mark, col, edge, lw, txt, tx, ty in legend_items:
        alpha = 0.2 if lw == 0.2 else 1
        lw = 1 if lw == 0.2 else lw
        legend_ax.scatter(x, y, marker=mark, s=200, c=col, edgecolors=edge, lw=lw, alpha=alpha)
        legend_ax.text(tx, ty, txt, color="w")
    
    # Title and subtitle
    teams = shots_df['team'].unique()
    subtitle_text = f"{teams[0]} vs {teams[1]}" if len(teams) == 2 else teams[0]
    
    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w')
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=14, color='w')
    fig.text(0.18, 0.852, season, fontweight="regular", fontsize=10, color='w')
    
    # Stats
    shots_count = len(selected_shots)
    xg_sum = selected_shots['xg'].sum()
    goals_sum = selected_shots['is_goal'].sum()
    xg_perf = goals_sum - xg_sum
    sign = '+' if xg_perf > 0 else ''
    
    stats_left = [
        ("Shots:", shots_count, 0.925),
        ("xG:", f"{xg_sum:.1f}", 0.9),
        ("Goals:", goals_sum, 0.875),
        ("xG Perf:", f"{sign}{int(100*xg_perf/xg_sum if xg_sum > 0 else 0)}%", 0.85)
    ]
    
    stats_right = [
        ("xG/shot:", f"{xg_sum/shots_count:.2f}" if shots_count > 0 else "0.00", 0.925),
        ("Goal/shot:", f"{goals_sum/shots_count:.2f}" if shots_count > 0 else "0.00", 0.9),
        ("L xG Goal:", f"{lowest_xg_goal['xg'].iloc[0]:.2f}" if not lowest_xg_goal.empty else "N/A", 0.875),
        ("H xG Miss:", f"{highest_xg_miss['xg'].iloc[0]:.2f}" if not highest_xg_miss.empty else "N/A", 0.85)
    ]
    
    for label, value, y in stats_left:
        fig.text(0.65, y, label, fontweight="bold", fontsize=10, color='w')
        fig.text(0.73, y, str(value), fontweight="regular", fontsize=10, color='w')
    
    for label, value, y in stats_right:
        fig.text(0.79, y, label, fontweight="bold", fontsize=10, color='w')
        fig.text(0.89, y, str(value), fontweight="regular", fontsize=10, color='w')
    
    # Logo
    if logo_path:
        ax_logo = fig.add_axes([0.02, 0.8, 0.2, 0.2])
        ax_logo.axis("off")
        try:
            img = Image.open(logo_path)
            ax_logo.imshow(img)
        except:
            pass
    
    plt.tight_layout()
    return fig