"""Half-pitch goal visualization classified by origin type.

Markers: hexagon (assisted), circle (after dribble), diamond (individual carry),
square (rebound). Colored by xG value. Stats panel with origin breakdown.
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

ORIGIN_MARKERS = {
    'Asistido': 'h',
    'Regate previo': 'o',
    'Carry individual': 'D',
    'Rebote': 's'
}

def plot_goals_origin(csv_path, player_name, face_path=None, team_name=None,
                     competition=None, season=None, save_path=None):
    """Plot goals on half-pitch with origin-based marker shapes and xG coloring.

    Args:
        csv_path: CSV with x, y, xg, origin_type columns.
        player_name: Player name for title.
        face_path: Optional player face image path.
        team_name: Team name for subtitle.
        competition: Competition name for subtitle.
        season: Season string.
        save_path: Optional output path.

    Returns:
        matplotlib Figure object.
    """
    goals_df = pd.read_csv(csv_path)
    font = 'DejaVu Sans'
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow',
        'gold', 'lightpink', 'tomato'
    ])

    mpl.rcParams['xtick.color'] = "white"
    mpl.rcParams['ytick.color'] = "white"
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    pitch = VerticalPitch(pitch_type='opta', half=True, pitch_color=PITCH_COLOR,
                         line_color='white', linewidth=1, stripe=False)
    fig, ax = pitch.grid(nrows=1, ncols=1, title_height=0.03, grid_height=0.7,
                        endnote_height=0.05, axis=False)
    fig.set_size_inches(9, 7)
    fig.set_facecolor(BACKGROUND_COLOR)

    # Goal markers by origin type
    cbar_ref = None
    for _, goal in goals_df.iterrows():
        if pd.notna(goal['x']) and pd.notna(goal['y']):
            xg_val = goal.get('xg', 0.1)
            origin = goal.get('origin_type', 'Rebote')
            marker = ORIGIN_MARKERS.get(origin, 's')

            scatter = ax['pitch'].scatter(
                goal['y'], goal['x'],  # (y, x) for VerticalPitch
                s=200,
                c=xg_val,
                cmap=node_cmap,
                vmin=-0.04, vmax=1.0,
                marker=marker,
                edgecolors='w',
                lw=2,
                zorder=3
            )
            if cbar_ref is None:
                cbar_ref = scatter

    # xG colorbar
    if cbar_ref is not None:
        cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
        cbar = fig.colorbar(cbar_ref, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)

    # Legend
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    legend_ax.scatter(0.2, 0.7, marker=ORIGIN_MARKERS['Asistido'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Assisted", color="w", fontfamily=font)

    legend_ax.scatter(0.2, 0.2, marker=ORIGIN_MARKERS['Regate previo'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.11, "After Dribble", color="w", fontfamily=font)

    legend_ax.scatter(1.7, 0.7, marker=ORIGIN_MARKERS['Carry individual'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(1.925, 0.61, "Indiv. Carry", color="w", fontfamily=font)

    legend_ax.scatter(1.7, 0.2, marker=ORIGIN_MARKERS['Rebote'], s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(1.925, 0.11, "Rebound", color="w", fontfamily=font)

    # Titles
    title_text = f"{player_name} - Goals by Origin"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=13, color='w', fontfamily=font)
    fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Statistics
    total_goals = len(goals_df)
    total_xg = goals_df['xg'].sum() if 'xg' in goals_df.columns else 0
    avg_xg = goals_df['xg'].mean() if 'xg' in goals_df.columns else 0

    xg_perf = total_goals - total_xg
    sign = '+' if xg_perf > 0 else ''
    perf_pct = int(round(100*xg_perf/total_xg, 0)) if total_xg > 0 else 0

    origin_counts = goals_df['origin_type'].value_counts() if 'origin_type' in goals_df.columns else {}

    fig.text(0.65, 0.925, "Goals:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.9, "xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "Avg xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.73, 0.925, f"{total_goals}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.9, f"{total_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.875, f"{avg_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.85, f"{sign}{perf_pct}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Origin breakdown
    fig.text(0.79, 0.927, "Assisted:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.9, "Dribble:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.875, "Carry:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.85, "Rebound:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.89, 0.925, f"{origin_counts.get('Asistido', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.9, f"{origin_counts.get('Regate previo', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.875, f"{origin_counts.get('Carry individual', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.85, f"{origin_counts.get('Rebote', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Footer
    fig.text(0.085, 0.02, "Created by Jaime Oriol", fontweight='bold', fontsize=10, color="white", fontfamily=font)

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path_fd = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path_fd)
        logo_ax = fig.add_axes([0.67, -0.018, 0.28, 0.12])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        fig.text(0.7, 0.02, "Football Decoded", fontweight='bold', fontsize=14, color="white", fontfamily=font)

    if face_path and os.path.exists(face_path):
        ax_logo = fig.add_axes([0.05, 0.82, 0.135, 0.135])
        ax_logo.axis("off")
        try:
            img = Image.open(face_path)
            ax_logo.imshow(img)
        except Exception as e:
            print(f"Error loading face image: {e}")
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    plt.tight_layout()
    return fig
