"""
FootballDecoded Progression & xThreat Visualization Module
===========================================================

Shows progressive carries and passes with xThreat generated.
Visualizes how player creates danger through progression.

Key Features:
- Full pitch horizontal layout
- Arrows for carries (blue) and progressive passes (green)
- Arrow thickness = xThreat generated
- Origin to destination visualization
- xThreat zones highlighted

Technical Implementation:
- Horizontal pitch (mplsoccer)
- Arrow width proportional to xThreat
- Color differentiation by action type
- xThreat scale legend

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
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

# Action colors
ACTION_COLORS = {
    'carry': '#00D9FF',        # Cyan - carries
    'pass': '#51CF66'          # Green - progressive passes
}

def plot_progression_xthreat(csv_path, player_name, face_path=None, team_name=None,
                             competition=None, season=None, save_path=None):
    """
    Create progression & xThreat visualization.

    Generates full pitch with progressive actions (carries/passes)
    sized by xThreat generated.

    Features:
    - Carries (cyan arrows) and progressive passes (green arrows)
    - Arrow thickness = xThreat generated
    - Shows zones of threat creation
    - xThreat scale reference

    Args:
        csv_path: Path to actions CSV with coordinates and xThreat
        player_name: Name of player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with progression analysis

    CSV Requirements:
        - x, y: Start coordinates (Opta 0-100)
        - end_x, end_y: End coordinates
        - xthreat: xThreat value generated
        - action_type: 'carry' or 'pass'
    """
    # Load actions data
    actions_df = pd.read_csv(csv_path)

    # Unified typography system
    font = 'DejaVu Sans'

    # Unified colormap for xThreat
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow',
        'gold', 'lightpink', 'tomato'
    ])

    # Setup horizontal pitch
    pitch = Pitch(
        pitch_color=PITCH_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )

    fig, ax = pitch.draw(figsize=(16, 10))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Separate carries and passes
    carries = actions_df[actions_df['action_type'] == 'carry']
    passes = actions_df[actions_df['action_type'] == 'pass']

    # Plot carries (cyan)
    if len(carries) > 0:
        for _, action in carries.iterrows():
            if pd.notna(action['x']) and pd.notna(action['end_x']):
                xthreat = action.get('xthreat', 0)
                # Width based on xThreat (min 1, max 4)
                width = 1 + (xthreat * 15) if xthreat > 0 else 1

                pitch.arrows(
                    action['x'], action['y'],
                    action['end_x'], action['end_y'],
                    color=ACTION_COLORS['carry'],
                    alpha=0.6,
                    width=width,
                    headwidth=4,
                    headlength=4,
                    zorder=2,
                    ax=ax
                )

    # Plot progressive passes (green)
    if len(passes) > 0:
        for _, action in passes.iterrows():
            if pd.notna(action['x']) and pd.notna(action['end_x']):
                xthreat = action.get('xthreat', 0)
                # Width based on xThreat (min 1, max 4)
                width = 1 + (xthreat * 15) if xthreat > 0 else 1

                pitch.arrows(
                    action['x'], action['y'],
                    action['end_x'], action['end_y'],
                    color=ACTION_COLORS['pass'],
                    alpha=0.6,
                    width=width,
                    headwidth=4,
                    headlength=4,
                    zorder=2,
                    ax=ax
                )

    # xTHREAT SCALE (bottom)
    cb_ax = fig.add_axes([0.25, 0.0, 0.5, 0.025])
    sm = plt.cm.ScalarMappable(cmap=node_cmap, norm=plt.Normalize(vmin=0, vmax=0.2))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cb_ax, orientation='horizontal')
    cbar.outline.set_edgecolor('w')
    cbar.ax.tick_params(labelsize=8, colors='white')
    cbar.set_label("xThreat Generated", loc="center", color='w', fontweight='bold', fontsize=9)

    # LEGEND: Action types (bottom left)
    legend_ax = fig.add_axes([0.075, 0.04, 0.15, 0.06])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 1])
    legend_ax.set_ylim([0, 1])

    # Carry
    legend_ax.arrow(0.1, 0.7, 0.3, 0, width=0.08, head_width=0.15,
                   head_length=0.1, fc=ACTION_COLORS['carry'], ec='white', linewidth=1.5)
    legend_ax.text(0.5, 0.7, "Carry", color="w", fontfamily=font, va='center', fontsize=8)

    # Pass
    legend_ax.arrow(0.1, 0.2, 0.3, 0, width=0.08, head_width=0.15,
                   head_length=0.1, fc=ACTION_COLORS['pass'], ec='white', linewidth=1.5)
    legend_ax.text(0.5, 0.2, "Progressive Pass", color="w", fontfamily=font, va='center', fontsize=8)

    # TITLES (above pitch)
    title_text = f"{player_name} - Progression & xThreat"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # STATISTICS PANEL (top right)
    total_actions = len(actions_df)
    total_carries = len(carries)
    total_passes = len(passes)
    total_xthreat = actions_df['xthreat'].sum()
    avg_xthreat = actions_df['xthreat'].mean() if len(actions_df) > 0 else 0

    fig.text(0.75, 1.03, "Actions:", fontweight="bold", fontsize=11, color='w', fontfamily=font)
    fig.text(0.75, 1.005, "Carries:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.98, "Prog Passes:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.955, "Total xT:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.87, 1.03, f"{total_actions}", fontweight="regular", fontsize=11, color='w', fontfamily=font)
    fig.text(0.87, 1.005, f"{total_carries}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.98, f"{total_passes}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.955, f"{total_xthreat:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # FACE/LOGO
    if face_path and os.path.exists(face_path):
        try:
            face_img = Image.open(face_path)
            face_ax = fig.add_axes([0.05, 0.88, 0.12, 0.12])
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
