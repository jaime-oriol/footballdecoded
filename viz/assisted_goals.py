"""
FootballDecoded Assisted Goals Visualization Module
====================================================

Specialized visualization system showing goals assisted by a player.
Creates focused half-pitch maps with assist-to-goal connections.

Key Features:
- Visual assist-to-goal connections with dotted lines
- Shot type differentiation (foot vs header markers)
- xG-based color coding with unified colormap
- Goal/miss differentiation with border thickness
- Comprehensive statistical panel with top receivers
- Face/logo integration and metadata display

Assist Visualization System:
- Dotted lines from assist position to shot location
- Hexagons for foot shots, circles for headers
- Goals: Double-thick white borders (linewidth=3)
- Misses: Single white borders (linewidth=1)
- xG-based fill colors using unified colormap

Statistical Analysis:
- Total assists and goals scored
- Average xG and conversion rate
- Top receivers (top 3 players)
- Efficiency metrics

Technical Implementation:
- Half-pitch Opta coordinate system (attacking direction)
- Y-axis coordinate flipping for proper visualization orientation
- Dynamic filtering system for player focus
- Automatic title generation
- Logo/face integration

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
Coordinate System: Half-pitch Opta (0-100, attacking toward 100)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from mplsoccer import VerticalPitch
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def plot_assisted_goals(csv_path, player_name, face_path=None, team_name=None,
                       competition=None, season=None, save_path=None):
    """
    Create assisted goals visualization with connection lines.

    Generates half-pitch analysis showing goals/shots assisted by the player.
    Dotted lines connect assist position to shot location.

    Features:
    - Visual assist-to-shot connections
    - Shot type differentiation (foot/header markers)
    - xG-based fill colors using unified colormap
    - Goal highlighting with thick white borders
    - Top receivers identification
    - Comprehensive statistical panel

    Args:
        csv_path: Path to assisted goals CSV file
        player_name: Name of assisting player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (e.g., "2024-25") (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with assisted goals analysis

    CSV Requirements:
        - x_assist, y_assist: Assist position coordinates (Opta 0-100)
        - x_shot, y_shot: Shot position coordinates (Opta 0-100)
        - xg: Expected goals value
        - is_goal: Boolean indicating if shot resulted in goal
        - body_part: Shot body part ('Head' or other for foot)
        - shooter: Name of player who took the shot
    """
    # Load assisted goals data
    shots_df = pd.read_csv(csv_path)

    # Unified typography system
    font = 'DejaVu Sans'

    # Unified colormap system
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow',
        'gold', 'lightpink', 'tomato'
    ])

    # Setup half-pitch
    pitch = VerticalPitch(
        pitch_color=PITCH_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta',
        half=True,
        pad_top=2
    )

    fig, ax = pitch.draw(figsize=(8, 10))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Plot assist-to-shot connections (dotted lines)
    for _, shot in shots_df.iterrows():
        if all(pd.notna(shot[['x_assist', 'y_assist', 'x_shot', 'y_shot']])):
            pitch.lines(
                shot['x_assist'], shot['y_assist'],
                shot['x_shot'], shot['y_shot'],
                linestyle='--',
                color='white',
                alpha=0.3,
                linewidth=1,
                zorder=1,
                ax=ax
            )

    # Plot shots
    for _, shot in shots_df.iterrows():
        if pd.notna(shot['x_shot']) and pd.notna(shot['y_shot']):
            xg_val = shot.get('xg', 0.1)
            is_goal = shot.get('is_goal', False)
            body_part = str(shot.get('body_part', 'Foot'))

            # Marker based on body part
            marker = 'o' if 'Head' in body_part else 'h'

            # Border thickness: thicker for goals
            linewidth = 3 if is_goal else 1

            # Plot shot
            pitch.scatter(
                shot['x_shot'], shot['y_shot'],
                s=200,
                c=xg_val,
                cmap=node_cmap,
                vmin=0, vmax=0.8,
                marker=marker,
                edgecolors='white',
                linewidths=linewidth,
                alpha=0.9,
                zorder=3,
                ax=ax
            )

    # xG COLOR SCALE: Horizontal colorbar
    sm = plt.cm.ScalarMappable(cmap=node_cmap, norm=plt.Normalize(vmin=0, vmax=0.8))
    sm.set_array([])
    cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
    cbar = fig.colorbar(sm, cax=cb_ax, orientation='horizontal')
    cbar.outline.set_edgecolor('w')
    cbar.ax.tick_params(colors='white')  # Color de los números
    cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)

    # LEGEND
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    # Shot type
    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.2, marker='o', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Foot", color="w", fontfamily=font)
    legend_ax.text(0.35, 0.11, "Header", color="w", fontfamily=font)

    # Shot outcome
    mid_color = node_cmap(0.5)
    legend_ax.scatter(1.3, 0.7, marker='h', s=200, c=mid_color, edgecolors='w', lw=3)
    legend_ax.scatter(1.3, 0.2, marker='h', s=200, c=mid_color, edgecolors='w', lw=1)
    legend_ax.text(1.45, 0.61, "Goal", color="w", fontfamily=font)
    legend_ax.text(1.45, 0.11, "Miss", color="w", fontfamily=font)

    # TITLES
    title_text = f"{player_name} - Assisted Shots"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=13, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # STATISTICS PANEL
    total_assists = len(shots_df)
    goals_scored = shots_df['is_goal'].sum() if 'is_goal' in shots_df.columns else 0
    avg_xg = shots_df['xg'].mean() if 'xg' in shots_df.columns else 0
    conversion = (goals_scored / total_assists * 100) if total_assists > 0 else 0

    # Top receivers
    if 'shooter' in shots_df.columns:
        top_receivers = shots_df['shooter'].value_counts().head(3)
    else:
        top_receivers = pd.Series()

    # Left column
    fig.text(0.65, 0.925, "Assists:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "Avg xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.75, 0.925, f"{total_assists}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.875, f"{avg_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Right column - Top receivers
    fig.text(0.82, 0.925, "Top Receivers:", fontweight="bold", fontsize=9, color='w', fontfamily=font)
    y_pos = 0.9
    for i, (receiver, count) in enumerate(top_receivers.items()):
        if i < 3:
            name_short = receiver.split()[-1] if ' ' in receiver else receiver[:10]
            fig.text(0.82, y_pos, f"{name_short}:", fontweight="regular", fontsize=8, color='w', fontfamily=font)
            fig.text(0.91, y_pos, f"{count}", fontweight="regular", fontsize=8, color='w', fontfamily=font)
            y_pos -= 0.025

    # FACE/LOGO
    if face_path and os.path.exists(face_path):
        try:
            face_img = Image.open(face_path)
            face_ax = fig.add_axes([0.05, 0.82, 0.135, 0.135])
            face_ax.imshow(face_img)
            face_ax.axis('off')
        except:
            pass

    # FOOTER
    fig.text(0.085, 0.02, "Created by Jaime Oriol", fontweight='bold',
            fontsize=10, color="white", fontfamily=font)

    # Logo Football Decoded
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            logo_ax = fig.add_axes([0.675, -0.018, 0.28, 0.12])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass

    # SAVE
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    return fig
