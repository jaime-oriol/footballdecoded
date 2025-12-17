"""
FootballDecoded Assist Passes Visualization Module
===================================================

Specialized visualization system showing assist passes by a player.
Creates full-pitch pass maps with xG-based arrow styling.

Key Features:
- Arrow-based pass visualization from start to end position
- xG-based color coding with unified colormap
- Arrow width scaled by xG value
- Comprehensive statistical panel with top receivers
- Face/logo integration and metadata display
- Full-pitch horizontal layout

Pass Visualization System:
- Arrows from pass origin to destination
- Color by xG generated (unified colormap)
- Width by xG (thicker = higher xG)
- Alpha transparency for visual hierarchy
- Goal/miss outcome tracking

Statistical Analysis:
- Total assists and goals scored from assists
- Average xG and conversion rate
- Average pass length
- Top 3 receivers

Technical Implementation:
- Full-pitch Opta coordinate system (horizontal)
- Dynamic arrow sizing based on xG
- Automatic title generation
- Logo/face integration

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
Coordinate System: Full-pitch Opta (0-100 horizontal)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from mplsoccer import Pitch
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def plot_assist_passes(csv_path, player_name, face_path=None, team_name=None,
                      competition=None, season=None, save_path=None):
    """
    Create assist passes visualization with arrows.

    Generates full-pitch analysis showing assist passes by the player.
    Arrows show pass direction, colored and sized by xG.

    Features:
    - Arrow-based pass visualization
    - xG-based color and width coding
    - Top receivers identification
    - Comprehensive statistical panel
    - Automatic title generation

    Args:
        csv_path: Path to assists CSV file
        player_name: Name of assisting player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (e.g., "2024-25") (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with assist passes analysis

    CSV Requirements:
        - x, y: Pass origin coordinates (Opta 0-100)
        - end_x, end_y: Pass destination coordinates (Opta 0-100)
        - xg: Expected goals value for the resulting shot
        - pass_length: Length of pass (optional)
        - receiver: Name of player who received the pass
        - pass_outcome: 'Goal' if resulted in goal (optional)
    """
    # Load assists data
    assists_df = pd.read_csv(csv_path)

    # Unified typography system
    font = 'DejaVu Sans'

    # Unified colormap system
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow',
        'gold', 'lightpink', 'tomato'
    ])

    # Setup full-pitch horizontal
    pitch = Pitch(
        pitch_color=PITCH_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )

    fig, ax = pitch.draw(figsize=(16, 10))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Plot assist arrows
    for _, assist in assists_df.iterrows():
        if all(pd.notna(assist[['x', 'y', 'end_x', 'end_y']])):
            xg_val = assist.get('xg', 0.1)

            # Arrow width scaled by xG (2-6)
            width = 2 + (xg_val * 4)

            # Color by xG
            color_val = np.clip(xg_val, 0, 0.8)
            color = node_cmap(color_val / 0.8)

            # Plot arrow
            pitch.arrows(
                assist['x'], assist['y'],
                assist['end_x'], assist['end_y'],
                color=color,
                alpha=0.7,
                width=width,
                headwidth=6,
                headlength=6,
                zorder=2,
                ax=ax
            )

    # xG COLOR SCALE: Horizontal colorbar
    sm = plt.cm.ScalarMappable(cmap=node_cmap, norm=plt.Normalize(vmin=0, vmax=0.8))
    sm.set_array([])
    cb_ax = fig.add_axes([0.25, 0.0, 0.5, 0.025])
    cbar = fig.colorbar(sm, cax=cb_ax, orientation='horizontal')
    cbar.outline.set_edgecolor('w')
    cbar.ax.tick_params(labelsize=8, colors='w')
    cbar.set_label("xG Generated", loc="center", color='w', fontweight='bold', fontsize=12)

    # LEGEND: Arrow width explanation
    legend_ax = fig.add_axes([0.075, 0.065, 0.15, 0.045])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 1])
    legend_ax.set_ylim([0, 1])

    # Note about arrow width
    legend_ax.text(0.5, 0.5, "Arrow width = xG", color="w", fontfamily=font,
                  fontsize=14, ha='center', va='center', style='italic')

    # TITLES
    title_text = f"{player_name} - Assist Passes"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # STATISTICS PANEL
    total_assists = len(assists_df)

    # Goals scored from assists
    if 'pass_outcome' in assists_df.columns:
        goals_scored = (assists_df['pass_outcome'] == 'Goal').sum()
    else:
        goals_scored = 0

    avg_xg = assists_df['xg'].mean() if 'xg' in assists_df.columns else 0
    conversion = (goals_scored / total_assists * 100) if total_assists > 0 else 0

    # Average pass length
    if 'pass_length' in assists_df.columns:
        avg_length = assists_df['pass_length'].mean()
    else:
        # Calculate from coordinates
        assists_df['calc_length'] = np.sqrt(
            (assists_df['end_x'] - assists_df['x'])**2 +
            (assists_df['end_y'] - assists_df['y'])**2
        )
        avg_length = assists_df['calc_length'].mean()

    # Top receivers
    if 'receiver' in assists_df.columns:
        top_receivers = assists_df['receiver'].value_counts().head(3)
    else:
        top_receivers = pd.Series()

    # Left column
    fig.text(0.77, 1.03, "Assists:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.77, 1.00, "Avg Length:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.77, 0.97, "Avg xG:", fontweight="bold", fontsize=14, color='w', fontfamily=font)

    fig.text(0.87, 1.03, f"{total_assists}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.87, 1.00, f"{avg_length:.1f}m", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.87, 0.97, f"{avg_xg:.2f}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
   
    # FACE/LOGO
    if face_path and os.path.exists(face_path):
        try:
            face_img = Image.open(face_path)
            face_ax = fig.add_axes([0.05, 0.95, 0.13, 0.13])
            face_ax.imshow(face_img)
            face_ax.axis('off')
        except:
            pass

    # FOOTER
    fig.text(0.075, -0.01, "Created by Jaime Oriol", fontweight='bold',
            fontsize=14, color="white", fontfamily=font)

    # Logo Football Decoded
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            logo_ax = fig.add_axes([0.7, -0.09, 0.3, 0.14])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass

    # SAVE
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    return fig
