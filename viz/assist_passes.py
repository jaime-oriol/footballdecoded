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
    cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
    cbar = fig.colorbar(sm, cax=cb_ax, orientation='horizontal')
    cbar.outline.set_edgecolor('w')
    cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)

    # LEGEND: Arrow widths
    legend_ax = fig.add_axes([0.075, 0.07, 0.45, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    # Arrow width examples
    legend_ax.arrow(0.1, 0.7, 0.4, 0, width=0.05, head_width=0.15,
                   head_length=0.08, fc='w', ec='w')
    legend_ax.text(0.6, 0.61, "Low xG", color="w", fontfamily=font, fontsize=9)

    legend_ax.arrow(1.2, 0.5, 0.4, 0, width=0.10, head_width=0.20,
                   head_length=0.08, fc='w', ec='w')
    legend_ax.text(1.7, 0.41, "Medium xG", color="w", fontfamily=font, fontsize=9)

    legend_ax.arrow(2.5, 0.3, 0.4, 0, width=0.15, head_width=0.25,
                   head_length=0.08, fc='w', ec='w')
    legend_ax.text(3.0, 0.21, "High xG", color="w", fontfamily=font, fontsize=9)

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
    fig.text(0.78, 1.03, "Assists:", fontweight="bold", fontsize=12, color='w', fontfamily=font)
    fig.text(0.78, 1.01, "Goals:", fontweight="bold", fontsize=12, color='w', fontfamily=font)
    fig.text(0.78, 0.99, "Avg xG:", fontweight="bold", fontsize=12, color='w', fontfamily=font)
    fig.text(0.78, 0.97, "Conv %:", fontweight="bold", fontsize=12, color='w', fontfamily=font)

    fig.text(0.88, 1.03, f"{total_assists}", fontweight="regular", fontsize=12, color='w', fontfamily=font)
    fig.text(0.88, 1.01, f"{goals_scored}", fontweight="regular", fontsize=12, color='w', fontfamily=font)
    fig.text(0.88, 0.99, f"{avg_xg:.2f}", fontweight="regular", fontsize=12, color='w', fontfamily=font)
    fig.text(0.88, 0.97, f"{conversion:.0f}%", fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # Right column - More stats
    fig.text(0.78, 0.95, "Avg Length:", fontweight="bold", fontsize=11, color='w', fontfamily=font)
    fig.text(0.88, 0.95, f"{avg_length:.1f}m", fontweight="regular", fontsize=11, color='w', fontfamily=font)

    # Top receivers below
    fig.text(0.78, 0.925, "Top Receivers:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    y_pos = 0.9
    for i, (receiver, count) in enumerate(top_receivers.items()):
        if i < 3:
            name_short = receiver.split()[-1] if ' ' in receiver else receiver[:10]
            fig.text(0.78, y_pos, f"{name_short}:", fontweight="regular", fontsize=9, color='w', fontfamily=font)
            fig.text(0.88, y_pos, f"{count}", fontweight="regular", fontsize=9, color='w', fontfamily=font)
            y_pos -= 0.02

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
    fig.text(0.085, -0.01, "Created by Jaime Oriol", fontweight='bold',
            fontsize=16, color="white", fontfamily=font)

    # Logo Football Decoded
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            logo_ax = fig.add_axes([0.675, -0.09, 0.32, 0.16])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass

    # SAVE
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    return fig
