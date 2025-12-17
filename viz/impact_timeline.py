"""
FootballDecoded Impact Timeline Visualization Module
=====================================================

Timeline showing when decisive moments happen during a match.
Shows goals, assists, key passes, and dribbles that lead to shots.

Key Features:
- Horizontal timeline from 0-90 minutes
- Color by match context (winning, drawing, losing)
- Size by temporal importance (last 15 min larger)
- Event type differentiation

Technical Implementation:
- Timeline with minute markers
- Event markers with context-based colors
- Legend showing event types and contexts
- Face/logo integration

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from PIL import Image
import os

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

# Context colors
CONTEXT_COLORS = {
    'drawing': '#FFA94D',      # Orange - empate
    'winning': '#51CF66',      # Green - ganando
    'losing': '#FF6B6B'        # Red - perdiendo
}

# Event markers
EVENT_MARKERS = {
    'goal': '*',               # Star
    'assist': 'D',             # Diamond
    'key_pass': 'o',           # Circle
    'dribble_to_shot': '^'     # Triangle
}

def plot_impact_timeline(csv_path, player_name, face_path=None, team_name=None,
                        competition=None, season=None, save_path=None):
    """
    Create impact timeline visualization showing decisive moments.

    Generates horizontal timeline with events colored by match context
    and sized by temporal importance.

    Features:
    - Goals, assists, key passes, dribbles that lead to shots
    - Context-based colors (winning, drawing, losing)
    - Size by importance (last 15 min larger)
    - Clear timeline with minute markers

    Args:
        csv_path: Path to events CSV with minute, event_type, score context
        player_name: Name of player for title
        face_path: Optional path to player face image
        team_name: Team name for subtitle (optional)
        competition: Competition name for subtitle (optional)
        season: Season string (optional)
        save_path: Path to save figure (optional)

    Returns:
        matplotlib Figure object with impact timeline

    CSV Requirements:
        - minute: Match minute
        - event_type: Type of event (goal, assist, key_pass, dribble_to_shot)
        - score_context: Match context (drawing, winning, losing)
        - description: Event description (optional)
    """
    # Load events data
    events_df = pd.read_csv(csv_path)

    # Unified typography system
    font = 'DejaVu Sans'

    # Setup figure with two timelines (first and second half)
    fig = plt.figure(figsize=(14, 8))
    fig.set_facecolor(BACKGROUND_COLOR)

    # Timeline axes - two separate timelines
    ax1 = fig.add_axes([0.1, 0.55, 0.8, 0.2])  # First half
    ax2 = fig.add_axes([0.1, 0.3, 0.8, 0.2])   # Second half

    ax1.set_facecolor(BACKGROUND_COLOR)
    ax1.set_xlim(-2, 47)
    ax1.set_ylim(0, 1)
    ax1.axis('off')

    ax2.set_facecolor(BACKGROUND_COLOR)
    ax2.set_xlim(43, 92)
    ax2.set_ylim(0, 1)
    ax2.axis('off')

    # Draw timeline bases
    ax1.plot([0, 45], [0.5, 0.5], color='white', linewidth=2, zorder=1)
    ax2.plot([45, 90], [0.5, 0.5], color='white', linewidth=2, zorder=1)

    # First half markers (every 15 minutes)
    for min_mark in [0, 15, 30, 45]:
        ax1.plot([min_mark, min_mark], [0.48, 0.52], color='white', linewidth=2, zorder=1)
        ax1.text(min_mark, 0.38, f"{min_mark}'", ha='center', va='top',
               color='white', fontsize=10, fontfamily=font)

    # Second half markers
    for min_mark in [45, 60, 75, 90]:
        # Adjust position for second timeline
        pos = min_mark
        ax2.plot([pos, pos], [0.48, 0.52], color='white', linewidth=2, zorder=1)
        ax2.text(pos, 0.38, f"{min_mark}'", ha='center', va='top',
               color='white', fontsize=10, fontfamily=font)

    # Half labels
    ax1.text(-1, 0.5, "1st Half", ha='right', va='center',
           color='white', fontsize=11, fontfamily=font, fontweight='bold')
    ax2.text(44, 0.5, "2nd Half", ha='right', va='center',
           color='white', fontsize=11, fontfamily=font, fontweight='bold')

    # Plot events on appropriate timeline
    for _, event in events_df.iterrows():
        minute = event['minute']
        event_type = event.get('event_type', 'key_pass')
        context = event.get('score_context', 'drawing')

        # Size by temporal importance (last 15 min larger)
        size = 400 if minute >= 75 else 250

        # Get marker and color
        marker = EVENT_MARKERS.get(event_type, 'o')
        color = CONTEXT_COLORS.get(context, CONTEXT_COLORS['drawing'])

        # Choose correct axis
        if minute <= 45:
            ax = ax1
        else:
            ax = ax2

        # Plot event
        ax.scatter(minute, 0.5, s=size, marker=marker, c=color,
                  edgecolors='white', linewidths=2, alpha=0.9, zorder=3)

    # LEGEND: Event types (bottom, larger axes)
    fig.text(0.1, 0.20, "Event Types:", color='white', fontsize=10,
            fontweight='bold', fontfamily=font)

    for i, (event_type, marker) in enumerate(EVENT_MARKERS.items()):
        x_pos = 0.1 + (i * 0.17)
        # Create larger axis for scatter to avoid clipping
        legend_ax = fig.add_axes([x_pos, 0.155, 0.035, 0.035])
        legend_ax.scatter(0.5, 0.5, s=300, marker=marker,
                         c=PITCH_COLOR, edgecolors='white', linewidths=2)
        legend_ax.axis('off')
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(0, 1)

        label = event_type.replace('_', ' ').title()
        fig.text(x_pos + 0.045, 0.167, label, color='white', fontsize=9,
                va='center', fontfamily=font)

    # LEGEND: Match context (bottom)
    fig.text(0.1, 0.10, "Match Context:", color='white', fontsize=10,
            fontweight='bold', fontfamily=font)

    for i, (context, color) in enumerate(CONTEXT_COLORS.items()):
        x_pos = 0.1 + (i * 0.17)
        # Create larger axis for scatter
        legend_ax = fig.add_axes([x_pos, 0.055, 0.035, 0.035])
        legend_ax.scatter(0.5, 0.5, s=300, marker='o',
                         c=color, edgecolors='white', linewidths=2)
        legend_ax.axis('off')
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(0, 1)

        label = context.title()
        fig.text(x_pos + 0.045, 0.067, label, color='white', fontsize=9,
                va='center', fontfamily=font)

    # TITLES (top)
    title_text = f"{player_name} - Impact Timeline"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 0.945, title_text, fontweight="bold", fontsize=18, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 0.920, subtitle_text, fontweight="regular", fontsize=14, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.895, subsubtitle_text, fontweight="regular", fontsize=11, color='w', fontfamily=font)

    # STATISTICS PANEL (top right)
    total_events = len(events_df)
    goals = len(events_df[events_df['event_type'] == 'goal'])
    assists = len(events_df[events_df['event_type'] == 'assist'])
    key_passes = len(events_df[events_df['event_type'] == 'key_pass'])

    # Clutch events (last 15 min)
    clutch_events = len(events_df[events_df['minute'] >= 75])
    clutch_pct = (clutch_events / total_events * 100) if total_events > 0 else 0

    fig.text(0.75, 0.97, "Total Events:", fontweight="bold", fontsize=11, color='w', fontfamily=font)
    fig.text(0.75, 0.945, "Goals:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.92, "Assists:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.75, 0.895, "Clutch %:", fontweight="bold", fontsize=10, color='w', fontfamily=font)

    fig.text(0.87, 0.97, f"{total_events}", fontweight="regular", fontsize=11, color='w', fontfamily=font)
    fig.text(0.87, 0.945, f"{goals}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.92, f"{assists}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.87, 0.895, f"{clutch_pct:.0f}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)

    # FACE/LOGO
    if face_path and os.path.exists(face_path):
        try:
            face_img = Image.open(face_path)
            face_ax = fig.add_axes([0.05, 0.86, 0.11, 0.11])
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
