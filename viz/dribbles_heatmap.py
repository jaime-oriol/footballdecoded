"""Full-pitch dribbles heatmap with KDE density and success/failure overlay.

Successful dribbles shown as green hexagons, failed as red squares.
KDE background (viridis) shows dribble density. Stats panel with success rate.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mplsoccer import Pitch
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'
SUCCESS_COLOR = '#00FF7F'
FAIL_COLOR = '#FF6B6B'

def plot_dribbles_heatmap(csv_path, player_name, face_path=None, team_name=None,
                         competition=None, season=None, match_count=None, save_path=None):
    """Plot dribbles heatmap with KDE density and success/failure scatter overlay.

    Args:
        csv_path: CSV with x, y, outcome_type columns (Opta 0-100).
        player_name: Player name for title.
        face_path: Optional player face image path.
        team_name: Team name for subtitle.
        competition: Competition name for subtitle.
        season: Season string.
        match_count: Number of matches for per-match stats.
        save_path: Optional output path.

    Returns:
        matplotlib Figure object.
    """
    dribbles_df = pd.read_csv(csv_path)
    dribbles_valid = dribbles_df[
        dribbles_df['x'].notna() &
        dribbles_df['y'].notna()
    ].copy()

    successful = dribbles_valid[dribbles_valid['outcome_type'] == 'Successful']
    failed = dribbles_valid[dribbles_valid['outcome_type'] != 'Successful']

    font = 'DejaVu Sans'
    pitch = Pitch(
        pitch_color=PITCH_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )

    fig, ax = pitch.draw(figsize=(16, 10))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # KDE heatmap
    if len(dribbles_valid) > 0:
        pitch.kdeplot(
            dribbles_valid['x'], dribbles_valid['y'],
            fill=True,
            levels=100,
            shade_lowest=True,
            cmap='viridis',
            cut=4,
            alpha=0.8,
            antialiased=True,
            zorder=0,
            ax=ax
        )

    # Successful dribbles (hexagons)
    if len(successful) > 0:
        pitch.scatter(
            successful['x'], successful['y'],
            s=120,
            marker='h',
            c=SUCCESS_COLOR,
            edgecolors='white',
            linewidths=1,
            alpha=0.8,
            zorder=3,
            ax=ax
        )

    # Failed dribbles (squares)
    if len(failed) > 0:
        pitch.scatter(
            failed['x'], failed['y'],
            s=120,
            marker='s',
            c=FAIL_COLOR,
            edgecolors='white',
            linewidths=1,
            alpha=0.8,
            zorder=3,
            ax=ax
        )

    # Legend
    legend_ax = fig.add_axes([0.075, 0.07, 0.45, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=SUCCESS_COLOR, edgecolors='w', lw=1.5)
    legend_ax.scatter(0.2, 0.2, marker='s', s=200, c=FAIL_COLOR, edgecolors='w', lw=1.5)
    legend_ax.text(0.35, 0.61, "Successful", color="w", fontfamily=font, fontsize=14)
    legend_ax.text(0.35, 0.11, "Failed", color="w", fontfamily=font, fontsize=14)

    # Titles
    title_text = f"{player_name} - Dribbles Heatmap"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # Statistics
    total_dribbles = len(dribbles_valid)
    successful_count = len(successful)
    failed_count = len(failed)
    success_rate = (successful_count / total_dribbles * 100) if total_dribbles > 0 else 0

    if match_count and match_count > 0:
        per_match = total_dribbles / match_count
    else:
        per_match = None

    fig.text(0.8, 1.04, "Success:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.8, 1.015, "Failed:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.8, 0.985, "Rate:", fontweight="bold", fontsize=14, color='w', fontfamily=font)

    fig.text(0.88, 1.04, f"{successful_count}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.88, 1.015, f"{failed_count}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.88, 0.985, f"{success_rate:.1f}%", fontweight="regular", fontsize=14, color='w', fontfamily=font)

    if per_match is not None:
        fig.text(0.8, 0.955, "Per Match:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
        fig.text(0.88, 0.955, f"{per_match:.1f}", fontweight="regular", fontsize=14, color='w', fontfamily=font)

    # Face/logo
    if face_path and os.path.exists(face_path):
        try:
            face_img = Image.open(face_path)
            face_ax = fig.add_axes([0.05, 0.95, 0.13, 0.13])
            face_ax.imshow(face_img)
            face_ax.axis('off')
        except:
            pass

    # Footer
    fig.text(0.085, -0.01, "Created by Jaime Oriol", fontweight='bold',
            fontsize=16, color="white", fontfamily=font)

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

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    return fig
