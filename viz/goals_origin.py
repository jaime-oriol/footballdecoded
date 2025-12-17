"""
FootballDecoded Goals Origin Visualization Module
==================================================

Specialized goal visualization system showing the origin of each goal.
Creates focused half-pitch goal maps with origin classification.

Key Features:
- Goal origin classification (Assisted, After Dribble, Individual Carry, Rebound)
- Half-pitch visualization focused on goal locations
- xG-based color coding with unified colormap
- Border colors indicate goal origin
- Comprehensive statistical panel with origin breakdown
- Face/logo integration and metadata display

Goal Origin System:
- Assisted: Goals from passes by teammates (green border)
- After Dribble: Goals after successful dribbles (cyan border)
- Individual Carry: Goals after long individual carries (gold border)
- Rebound: Goals from rebounds or other situations (grey border)

Statistical Analysis:
- Total goals and average xG
- xG Performance vs expected
- Breakdown by origin type
- Top origin sources

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

# Origin markers
ORIGIN_MARKERS = {
    'Asistido': 'h',           # Hexágono
    'Regate previo': 'o',       # Círculo
    'Carry individual': 'D',    # Diamante
    'Rebote': 's'               # Cuadrado
}

def plot_goals_origin(csv_path, player_name, face_path=None, team_name=None,
                     competition=None, season=None, save_path=None):
    """
    Create goals visualization with origin classification.

    Generates half-pitch goal analysis with origin-based border colors.
    Shows where goals came from (assisted, dribble, carry, rebound).

    Features:
    - Goal origin classification with color-coded borders
    - xG-based fill colors using unified colormap
    - Comprehensive statistical analysis panel
    - Automatic title generation based on player name
    - Optional face/logo integration

    Args:
        csv_path: Path to goals CSV file with origin_type column
        player_name: Name of player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (e.g., "2024-25") (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with goals origin analysis

    CSV Requirements:
        - x, y: Shot coordinates (Opta 0-100)
        - xg: Expected goals value
        - origin_type: One of ('Asistido', 'Regate previo', 'Carry individual', 'Rebote')
        - minute: Match minute (optional, for additional analysis)
    """
    # Load goals data
    goals_df = pd.read_csv(csv_path)

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

    # Plot goals with origin-based markers
    for _, goal in goals_df.iterrows():
        if pd.notna(goal['x']) and pd.notna(goal['y']):
            xg_val = goal.get('xg', 0.1)
            origin = goal.get('origin_type', 'Rebote')
            marker = ORIGIN_MARKERS.get(origin, 's')

            # Plot with xG-based fill and origin-based marker shape
            pitch.scatter(
                goal['x'], goal['y'],
                s=200,
                c=xg_val,
                cmap=node_cmap,
                vmin=0, vmax=0.8,
                marker=marker,
                edgecolors='white',
                linewidths=2,
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

    # LEGEND: Origin types (same style as shot_xg.py)
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    # Column 1: Assisted
    legend_ax.scatter(0.2, 0.7, marker=ORIGIN_MARKERS['Asistido'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.4, 0.61, "Assisted", color="w", fontfamily=font)

    # Column 1: After Dribble
    legend_ax.scatter(0.2, 0.2, marker=ORIGIN_MARKERS['Regate previo'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.4, 0.11, "After Dribble", color="w", fontfamily=font)

    # Column 2: Individual Carry
    legend_ax.scatter(1.7, 0.7, marker=ORIGIN_MARKERS['Carry individual'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(1.925, 0.61, "Indiv. Carry", color="w", fontfamily=font)

    # Column 2: Rebound
    legend_ax.scatter(1.7, 0.2, marker=ORIGIN_MARKERS['Rebote'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(1.925, 0.11, "Rebound", color="w", fontfamily=font)

    # TITLES
    title_text = f"{player_name} - Goals by Origin"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=13, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # STATISTICS PANEL
    total_goals = len(goals_df)
    avg_xg = goals_df['xg'].mean() if 'xg' in goals_df.columns else 0
    total_xg = goals_df['xg'].sum() if 'xg' in goals_df.columns else 0
    xg_perf = total_goals - total_xg
    sign = '+' if xg_perf > 0 else ''

    # Origin breakdown
    origin_counts = goals_df['origin_type'].value_counts() if 'origin_type' in goals_df.columns else {}

    # Left column
    fig.text(0.65, 0.925, "Goals:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.9, "Avg xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "Total xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.75, 0.925, f"{total_goals}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.9, f"{avg_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.875, f"{total_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.85, f"{sign}{xg_perf:.1f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Right column - Origin breakdown
    y_pos = 0.925
    for origin in ['Asistido', 'Regate previo', 'Carry individual', 'Rebote']:
        count = origin_counts.get(origin, 0)
        if count > 0:
            label = origin[:8] + ":" if len(origin) > 8 else origin + ":"
            fig.text(0.82, y_pos, label, fontweight="bold", fontsize=9, color='w', fontfamily=font)
            fig.text(0.91, y_pos, f"{count}", fontweight="regular", fontsize=9, color='w', fontfamily=font)
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
