"""
FootballDecoded Dribbles Heatmap Visualization Module
======================================================

Specialized visualization system showing dribble locations and success.
Creates full-pitch heatmap with KDE density and scatter overlay.

Key Features:
- KDE (Kernel Density Estimation) heatmap showing dribble density
- Scatter overlay differentiating successful vs failed dribbles
- Success/failure color coding (green/red)
- Comprehensive statistical panel with success rate
- Face/logo integration and metadata display
- Full-pitch horizontal layout

Dribble Visualization System:
- KDE heatmap background (viridis colormap)
- Successful dribbles: Green circles (#00FF7F)
- Failed dribbles: Red circles (#FF6B6B)
- White borders for clarity
- Alpha transparency for layering

Statistical Analysis:
- Total dribbles attempted
- Successful and failed counts
- Success rate percentage
- Average dribbles per match (if match count provided)

Technical Implementation:
- Full-pitch Opta coordinate system (horizontal)
- KDE with 100 levels for smooth gradient
- Scatter overlay with fixed size (s=100)
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
    """
    Create dribbles heatmap with success/failure overlay.

    Generates full-pitch KDE heatmap showing dribble locations with
    scatter overlay differentiating successful vs failed attempts.

    Features:
    - KDE heatmap showing dribble density
    - Success/failure scatter overlay
    - Color-coded outcomes (green=success, red=fail)
    - Comprehensive statistical panel
    - Automatic title generation

    Args:
        csv_path: Path to dribbles CSV file
        player_name: Name of player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (e.g., "2024-25") (optional)
        match_count: Number of matches for per-match stats (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with dribbles heatmap analysis

    CSV Requirements:
        - x, y: Dribble location coordinates (Opta 0-100)
        - outcome_type: 'Successful' or other for failed
    """
    # Load dribbles data
    dribbles_df = pd.read_csv(csv_path)

    # Filter valid coordinates
    dribbles_valid = dribbles_df[
        dribbles_df['x'].notna() &
        dribbles_df['y'].notna()
    ].copy()

    # Separate successful and failed
    successful = dribbles_valid[dribbles_valid['outcome_type'] == 'Successful']
    failed = dribbles_valid[dribbles_valid['outcome_type'] != 'Successful']

    # Unified typography system
    font = 'DejaVu Sans'

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

    # KDE HEATMAP: Density background
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

    # SCATTER OVERLAY: Successful dribbles (hexagons)
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

    # SCATTER OVERLAY: Failed dribbles (squares)
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

    # LEGEND
    legend_ax = fig.add_axes([0.075, 0.07, 0.45, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])

    # Dribble outcome with shapes
    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=SUCCESS_COLOR, edgecolors='w', lw=1.5)
    legend_ax.scatter(0.2, 0.2, marker='s', s=200, c=FAIL_COLOR, edgecolors='w', lw=1.5)
    legend_ax.text(0.35, 0.61, "Successful", color="w", fontfamily=font, fontsize=14)
    legend_ax.text(0.35, 0.11, "Failed", color="w", fontfamily=font, fontsize=14)

    # TITLES
    title_text = f"{player_name} - Dribbles Heatmap"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # STATISTICS PANEL
    total_dribbles = len(dribbles_valid)
    successful_count = len(successful)
    failed_count = len(failed)
    success_rate = (successful_count / total_dribbles * 100) if total_dribbles > 0 else 0

    # Per match stats
    if match_count and match_count > 0:
        per_match = total_dribbles / match_count
    else:
        per_match = None

    # Stats positioning
    fig.text(0.8, 1.04, "Success:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.8, 1.015, "Failed:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.8, 0.985, "Rate:", fontweight="bold", fontsize=14, color='w', fontfamily=font)

    fig.text(0.88, 1.04, f"{successful_count}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.88, 1.015, f"{failed_count}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.88, 0.985, f"{success_rate:.1f}%", fontweight="regular", fontsize=14, color='w', fontfamily=font)

    if per_match is not None:
        fig.text(0.8, 0.955, "Per Match:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
        fig.text(0.88, 0.955, f"{per_match:.1f}", fontweight="regular", fontsize=14, color='w', fontfamily=font)

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
