"""Half-pitch assisted goals visualization with assist-to-shot connection lines.

Markers differentiate foot/header shots, colored by xG. Stats panel shows
xG performance and top receivers.
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
    """Plot assisted goals on half-pitch with assist-to-shot connection lines.

    Args:
        csv_path: CSV with x_assist, y_assist, x_shot, y_shot, xg, is_goal, body_part, shooter.
        player_name: Assisting player name for title.
        face_path: Optional player face image path.
        team_name: Team name for subtitle.
        competition: Competition name for subtitle.
        season: Season string.
        save_path: Optional output path.

    Returns:
        matplotlib Figure object.
    """
    shots_df = pd.read_csv(csv_path)
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

    # Assist-to-shot connection lines
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
                ax=ax['pitch']
            )

    # Shot markers by body part
    cbar_ref = None
    for _, shot in shots_df.iterrows():
        if pd.notna(shot['x_shot']) and pd.notna(shot['y_shot']):
            xg_val = shot.get('xg', 0.1)
            is_goal = shot.get('is_goal', False)
            body_part = str(shot.get('body_part', 'Foot'))

            marker = 'o' if 'Head' in body_part else 'h'

            linewidth = 2 if is_goal else 1

            scatter = ax['pitch'].scatter(
                shot['y_shot'], shot['x_shot'],  # (y, x) for VerticalPitch
                s=200,
                c=xg_val,
                cmap=node_cmap,
                vmin=-0.04, vmax=1.0,
                marker=marker,
                edgecolors='w',
                lw=linewidth,
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

    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Foot", color="w", fontfamily=font)

    legend_ax.scatter(0.2, 0.2, marker='o', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.11, "Header", color="w", fontfamily=font)

    mid_color = node_cmap(0.5)
    legend_ax.scatter(1.3, 0.7, marker='h', s=200, c='grey', edgecolors='w', lw=2)
    legend_ax.text(1.45, 0.61, "Goal", color="w", fontfamily=font)

    legend_ax.scatter(1.3, 0.2, marker='h', alpha=0.2, s=200, c=mid_color, edgecolors='w')
    legend_ax.text(1.465, 0.11, "No Goal", color="w", fontfamily=font)

    # Titles
    title_text = f"{player_name} - Assisted Goals"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=13, color='w', fontfamily=font)
    fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Statistics
    total_assists = len(shots_df)
    goals_scored = shots_df['is_goal'].sum() if 'is_goal' in shots_df.columns else 0
    total_xg = shots_df['xg'].sum() if 'xg' in shots_df.columns else 0
    avg_xg_per_goal = (total_xg / goals_scored) if goals_scored > 0 else 0

    xg_perf = goals_scored - total_xg
    sign = '+' if xg_perf > 0 else ''
    perf_pct = int(round(100 * xg_perf / total_xg, 0)) if total_xg > 0 else 0

    if 'shooter' in shots_df.columns:
        top_receivers = shots_df['shooter'].value_counts().head(3)
    else:
        top_receivers = pd.Series()

    fig.text(0.65, 0.925, "Assists:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.9, "xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "xG/Goal:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.73, 0.925, f"{total_assists}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.9, f"{total_xg:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.875, f"{avg_xg_per_goal:.2f}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.85, f"{sign}{perf_pct}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Top receivers
    fig.text(0.79, 0.927, "Top Receivers:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    y_positions = [0.9, 0.875, 0.85]
    for i, (receiver, count) in enumerate(top_receivers.items()):
        if i < 3:
            name_short = receiver.split()[-1] if ' ' in receiver else receiver[:10]
            fig.text(0.79, y_positions[i], f"{name_short}:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
            fig.text(0.89, y_positions[i], f"{count}", fontweight="regular", fontsize=10, color='w', fontfamily=font)

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
