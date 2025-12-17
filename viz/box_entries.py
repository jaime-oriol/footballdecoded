"""
FootballDecoded Box Entries Visualization Module
=================================================

Shows penetration into the box with entry type and outcome.
Visualizes how player enters the penalty area.

Key Features:
- Full pitch horizontal layout
- Arrows from origin to box entry point
- Color by outcome (shot, assist, nothing)
- Shape by entry type (pass, carry, dribble)
- Conversion rate statistics

Technical Implementation:
- Horizontal pitch (mplsoccer)
- Arrow + marker combination
- Color-coded outcomes
- Entry type differentiation

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

# Outcome colors
OUTCOME_COLORS = {
    'shot': '#FF6B6B',         # Red - led to shot
    'assist': '#51CF66',       # Green - led to assist
    'nothing': '#868E96'       # Grey - no outcome
}

# Entry type markers
ENTRY_MARKERS = {
    'Pass': 'o',               # Circle
    'Carry': 'D',              # Diamond
    'Dribble': '^'             # Triangle
}

def plot_box_entries(csv_path, player_name, face_path=None, team_name=None,
                    competition=None, season=None, save_path=None):
    """
    Create box entries visualization showing penetration patterns.

    Generates full pitch with arrows showing entries into the penalty area,
    colored by outcome and shaped by entry type.

    Features:
    - Arrows from origin to box entry
    - Color by outcome (shot/assist/nothing)
    - Shape by entry type (pass/carry/dribble)
    - Conversion rate statistics

    Args:
        csv_path: Path to entries CSV with coordinates and outcomes
        player_name: Name of player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with box entries analysis

    CSV Requirements:
        - x, y: Origin coordinates (Opta 0-100)
        - entry_x, entry_y: Box entry coordinates
        - entry_type: 'Pass', 'Carry', or 'Dribble'
        - outcome: 'shot', 'assist', or 'nothing'
    """
    # Load entries data
    entries_df = pd.read_csv(csv_path)

    # Unified typography system
    font = 'DejaVu Sans'

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

    # Plot each entry
    for _, entry in entries_df.iterrows():
        if pd.notna(entry['x']) and pd.notna(entry['entry_x']):
            # Get entry details
            entry_type = entry.get('entry_type', 'Pass')
            outcome = entry.get('outcome', 'nothing')

            # Arrow from origin to entry point (thinner)
            pitch.arrows(
                entry['x'], entry['y'],
                entry['entry_x'], entry['entry_y'],
                color=OUTCOME_COLORS[outcome],
                alpha=0.5,
                width=1,
                headwidth=0,
                headlength=0,
                zorder=1,
                ax=ax
            )

            # Marker at entry point
            marker = ENTRY_MARKERS.get(entry_type, 'o')
            pitch.scatter(
                entry['entry_x'], entry['entry_y'],
                s=150,
                marker=marker,
                c=OUTCOME_COLORS[outcome],
                edgecolors='white',
                linewidths=1.5,
                alpha=0.9,
                zorder=3,
                ax=ax
            )

    # LEGEND: Entry types (bottom left)
    legend_ax = fig.add_axes([0.075, 0.02, 0.25, 0.08])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 1])
    legend_ax.set_ylim([0, 1])

    legend_ax.text(0.1, 0.85, "Entry Type:", color='white', fontsize=9,
                  fontweight='bold', fontfamily=font)

    y_positions = [0.55, 0.3, 0.05]
    for i, (entry_type, marker) in enumerate(ENTRY_MARKERS.items()):
        y_pos = y_positions[i]
        legend_ax.scatter(0.15, y_pos, marker=marker, s=120, c=PITCH_COLOR,
                         edgecolors='white', linewidths=1.5)
        legend_ax.text(0.3, y_pos, entry_type, color='white', fontsize=8,
                      va='center', fontfamily=font)

    # LEGEND: Outcomes (bottom middle)
    legend_ax2 = fig.add_axes([0.35, 0.02, 0.25, 0.08])
    legend_ax2.axis("off")
    legend_ax2.set_xlim([0, 1])
    legend_ax2.set_ylim([0, 1])

    legend_ax2.text(0.1, 0.85, "Outcome:", color='white', fontsize=9,
                   fontweight='bold', fontfamily=font)

    y_positions2 = [0.55, 0.3, 0.05]
    outcome_labels = {'shot': 'Led to Shot', 'assist': 'Led to Assist', 'nothing': 'No Outcome'}

    for i, (outcome, color) in enumerate(OUTCOME_COLORS.items()):
        y_pos = y_positions2[i]
        legend_ax2.scatter(0.15, y_pos, marker='o', s=120, c=color,
                          edgecolors='white', linewidths=1.5)
        legend_ax2.text(0.3, y_pos, outcome_labels[outcome], color='white',
                       fontsize=8, va='center', fontfamily=font)

    # TITLES (above pitch)
    title_text = f"{player_name} - Box Entries"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # STATISTICS PANEL (top right)
    total_entries = len(entries_df)
    entries_by_type = entries_df['entry_type'].value_counts().to_dict()
    entries_by_outcome = entries_df['outcome'].value_counts().to_dict()

    # Conversion rate (shots + assists / total)
    dangerous = entries_by_outcome.get('shot', 0) + entries_by_outcome.get('assist', 0)
    conversion_rate = (dangerous / total_entries * 100) if total_entries > 0 else 0

    fig.text(0.75, 1.03, "Total Entries:", fontweight="bold", fontsize=11, color='w', fontfamily=font)
    fig.text(0.75, 1.005, "Pass Entries:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.98, "Carry Entries:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.955, "Dribble Entries:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.87, 1.03, f"{total_entries}", fontweight="regular", fontsize=11, color='w', fontfamily=font)
    fig.text(0.87, 1.005, f"{entries_by_type.get('Pass', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.98, f"{entries_by_type.get('Carry', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.955, f"{entries_by_type.get('Dribble', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # Right column - outcomes
    fig.text(0.75, 0.93, "To Shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.905, "To Assist:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.88, "Conversion:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.87, 0.93, f"{entries_by_outcome.get('shot', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.905, f"{entries_by_outcome.get('assist', 0)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.88, f"{conversion_rate:.0f}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)

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
