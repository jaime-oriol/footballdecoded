"""Full-pitch assist pass visualization with xG-based arrow styling.

Arrows colored and sized by xG value. Includes stats panel and top receivers.
Coordinate system: Opta (0-100 horizontal).
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
    """Plot assist passes as arrows on full pitch, colored and sized by xG.

    Args:
        csv_path: CSV with x, y, end_x, end_y, xg, receiver columns.
        player_name: Player name for title.
        face_path: Optional player face image path.
        team_name: Team name for subtitle.
        competition: Competition name for subtitle.
        season: Season string (e.g. '2024-25').
        save_path: Optional output path.

    Returns:
        matplotlib Figure object.
    """
    assists_df = pd.read_csv(csv_path)
    font = 'DejaVu Sans'
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow',
        'gold', 'lightpink', 'tomato'
    ])

    pitch = Pitch(
        pitch_color=PITCH_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )

    fig, ax = pitch.draw(figsize=(16, 10))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    for _, assist in assists_df.iterrows():
        if all(pd.notna(assist[['x', 'y', 'end_x', 'end_y']])):
            xg_val = assist.get('xg', 0.1)

            width = 2 + (xg_val * 4)  # Arrow width scaled by xG
            color_val = np.clip(xg_val, 0, 0.8)
            color = node_cmap(color_val / 0.8)

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

    # xG colorbar
    sm = plt.cm.ScalarMappable(cmap=node_cmap, norm=plt.Normalize(vmin=0, vmax=0.8))
    sm.set_array([])
    cb_ax = fig.add_axes([0.25, 0.0, 0.5, 0.025])
    cbar = fig.colorbar(sm, cax=cb_ax, orientation='horizontal')
    cbar.outline.set_edgecolor('w')
    cbar.ax.tick_params(labelsize=8, colors='w')
    cbar.set_label("xG Generated", loc="center", color='w', fontweight='bold', fontsize=12)

    # Legend
    legend_ax = fig.add_axes([0.075, 0.065, 0.15, 0.045])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 1])
    legend_ax.set_ylim([0, 1])

    legend_ax.text(0.5, 0.5, "Arrow width = xG", color="w", fontfamily=font,
                  fontsize=14, ha='center', va='center', style='italic')

    # Titles
    title_text = f"{player_name} - Assist Passes"
    subtitle_text = team_name if team_name else ""
    subsubtitle_text = f"{competition} {season}" if competition and season else (season if season else "")

    fig.text(0.18, 1.03, title_text, fontweight="bold", fontsize=20, color='w', fontfamily=font)
    if subtitle_text:
        fig.text(0.18, 1.0, subtitle_text, fontweight="regular", fontsize=16, color='w', fontfamily=font)
    if subsubtitle_text:
        fig.text(0.18, 0.975, subsubtitle_text, fontweight="regular", fontsize=12, color='w', fontfamily=font)

    # Statistics
    total_assists = len(assists_df)
    if 'pass_outcome' in assists_df.columns:
        goals_scored = (assists_df['pass_outcome'] == 'Goal').sum()
    else:
        goals_scored = 0

    avg_xg = assists_df['xg'].mean() if 'xg' in assists_df.columns else 0
    conversion = (goals_scored / total_assists * 100) if total_assists > 0 else 0

    if 'pass_length' in assists_df.columns:
        avg_length = assists_df['pass_length'].mean()
    else:
        assists_df['calc_length'] = np.sqrt(
            (assists_df['end_x'] - assists_df['x'])**2 +
            (assists_df['end_y'] - assists_df['y'])**2
        )
        avg_length = assists_df['calc_length'].mean()

    if 'receiver' in assists_df.columns:
        top_receivers = assists_df['receiver'].value_counts().head(3)
    else:
        top_receivers = pd.Series()

    fig.text(0.77, 1.03, "Assists:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.77, 1.00, "Avg Length:", fontweight="bold", fontsize=14, color='w', fontfamily=font)
    fig.text(0.77, 0.97, "Avg xG:", fontweight="bold", fontsize=14, color='w', fontfamily=font)

    fig.text(0.87, 1.03, f"{total_assists}", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.87, 1.00, f"{avg_length:.1f}m", fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.87, 0.97, f"{avg_xg:.2f}", fontweight="regular", fontsize=14, color='w', fontfamily=font)

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
    fig.text(0.075, -0.01, "Created by Jaime Oriol", fontweight='bold',
            fontsize=14, color="white", fontfamily=font)

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
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)

    return fig
