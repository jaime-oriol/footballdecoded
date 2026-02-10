"""Tournament bracket visualization with probability heatmap.

Displays World Cup bracket structure with team probabilities per round,
colored by championship probability (deepskyblue -> tomato gradient).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

BACKGROUND_COLOR = '#313332'
FONT = 'DejaVu Sans'
BRACKET_CMAP = mcolors.LinearSegmentedColormap.from_list("", [
    'deepskyblue', 'cyan', 'lawngreen', 'yellow',
    'gold', 'lightpink', 'tomato',
])


def plot_tournament_bracket(
    team_probabilities: pd.DataFrame,
    group_standings: dict = None,
    title: str = "World Cup 2026 Predictions",
    subtitle: str = "",
    figsize: tuple = (24, 16),
) -> plt.Figure:
    """Draw tournament bracket with probability annotations.

    Parameters
    ----------
    team_probabilities : pd.DataFrame
        Must contain: team, p_champion, p_final, p_sf, p_qf, p_r16, p_r32,
        p_group_advance. Sorted by p_champion descending.
    group_standings : dict, optional
        {group_letter: DataFrame} from simulation output.
    title : str
        Main title.
    subtitle : str
        Subtitle text.
    figsize : tuple
        Figure dimensions.

    Returns
    -------
    matplotlib Figure.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize, facecolor=BACKGROUND_COLOR,
                              gridspec_kw={"width_ratios": [1.5, 1]})

    ax_bracket = axes[0]
    ax_table = axes[1]

    # Bracket panel
    ax_bracket.set_facecolor(BACKGROUND_COLOR)
    ax_bracket.set_xlim(0, 100)
    ax_bracket.set_ylim(0, 100)
    ax_bracket.axis('off')

    _draw_bracket_structure(ax_bracket, team_probabilities)

    # Table panel: top 20 teams
    ax_table.set_facecolor(BACKGROUND_COLOR)
    ax_table.axis('off')
    _draw_probability_table(ax_table, team_probabilities)

    # Title
    fig.suptitle(
        title, fontsize=20, fontweight='bold', color='white',
        fontfamily=FONT, y=0.97,
    )
    if subtitle:
        fig.text(0.5, 0.93, subtitle, ha='center', fontsize=12,
                 color='#aaaaaa', fontfamily=FONT)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    return fig


def plot_group_overview(
    group_standings: dict,
    title: str = "Group Stage Probabilities",
    figsize: tuple = (20, 14),
) -> plt.Figure:
    """Draw all group standings with advance probabilities.

    Parameters
    ----------
    group_standings : dict
        {group_letter: DataFrame} with columns: team, p_1st, p_2nd, p_3rd,
        p_4th, avg_points, avg_gd.

    Returns
    -------
    matplotlib Figure.
    """
    n_groups = len(group_standings)
    if n_groups == 0:
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=BACKGROUND_COLOR)
        ax.text(0.5, 0.5, "No group data available", ha='center', va='center',
                color='white', fontsize=16, fontfamily=FONT)
        ax.set_facecolor(BACKGROUND_COLOR)
        ax.axis('off')
        return fig

    ncols = 4
    nrows = (n_groups + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, facecolor=BACKGROUND_COLOR)
    axes = axes.flatten() if n_groups > 1 else [axes]

    sorted_groups = sorted(group_standings.keys())

    for idx, letter in enumerate(sorted_groups):
        ax = axes[idx]
        ax.set_facecolor(BACKGROUND_COLOR)
        ax.axis('off')

        df = group_standings[letter]
        ax.set_title(f"Group {letter}", fontsize=14, fontweight='bold',
                     color='white', fontfamily=FONT, pad=10)

        # Header
        headers = ["Team", "1st", "2nd", "Pts", "GD"]
        x_positions = [0.05, 0.55, 0.70, 0.82, 0.93]
        y_start = 0.85
        row_height = 0.18

        for i, (h, x) in enumerate(zip(headers, x_positions)):
            ax.text(x, y_start + 0.05, h, ha='left' if i == 0 else 'center',
                    va='center', fontsize=9, fontweight='bold', color='#aaaaaa',
                    fontfamily=FONT, transform=ax.transAxes)

        # Rows
        for row_idx, (_, row) in enumerate(df.iterrows()):
            y = y_start - row_idx * row_height

            # Color by advance probability
            p_advance = row.get("p_1st", 0) + row.get("p_2nd", 0)
            color = BRACKET_CMAP(p_advance)

            team_name = row["team"]
            if len(team_name) > 16:
                team_name = team_name[:14] + ".."

            ax.text(x_positions[0], y, team_name, ha='left', va='center',
                    fontsize=10, color=color, fontfamily=FONT,
                    fontweight='bold', transform=ax.transAxes)
            ax.text(x_positions[1], y, f"{row.get('p_1st', 0):.0%}", ha='center',
                    va='center', fontsize=9, color='white', fontfamily=FONT,
                    transform=ax.transAxes)
            ax.text(x_positions[2], y, f"{row.get('p_2nd', 0):.0%}", ha='center',
                    va='center', fontsize=9, color='white', fontfamily=FONT,
                    transform=ax.transAxes)
            ax.text(x_positions[3], y, f"{row.get('avg_points', 0):.1f}", ha='center',
                    va='center', fontsize=9, color='#cccccc', fontfamily=FONT,
                    transform=ax.transAxes)
            ax.text(x_positions[4], y, f"{row.get('avg_gd', 0):+.1f}", ha='center',
                    va='center', fontsize=9, color='#cccccc', fontfamily=FONT,
                    transform=ax.transAxes)

    # Hide unused axes
    for idx in range(n_groups, len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle(title, fontsize=18, fontweight='bold', color='white',
                 fontfamily=FONT, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


def _draw_bracket_structure(ax, team_probs: pd.DataFrame):
    """Draw simplified bracket with top teams per round."""
    rounds = [
        ("R32", "p_r32", 8),
        ("R16", "p_r16", 8),
        ("QF", "p_qf", 8),
        ("SF", "p_sf", 4),
        ("Final", "p_final", 4),
        ("Champion", "p_champion", 3),
    ]

    x_positions = [5, 20, 38, 56, 74, 88]
    round_width = 14

    for round_idx, (label, col, n_show) in enumerate(rounds):
        x = x_positions[round_idx]

        # Round header
        ax.text(x + round_width / 2, 97, label, ha='center', va='center',
                fontsize=11, fontweight='bold', color='#aaaaaa',
                fontfamily=FONT)

        if col not in team_probs.columns:
            continue

        # Top N teams for this round
        sorted_df = team_probs.nlargest(n_show, col)
        y_start = 88
        y_step = 88 / (n_show + 1)

        for i, (_, row) in enumerate(sorted_df.iterrows()):
            y = y_start - i * y_step
            prob = row[col]

            if prob <= 0:
                continue

            # Color by probability
            color = BRACKET_CMAP(min(prob * 3, 1.0))  # Scale for visibility

            team_name = row["team"]
            if len(team_name) > 14:
                team_name = team_name[:12] + ".."

            # Team box
            rect = mpatches.FancyBboxPatch(
                (x, y - 2), round_width, 4,
                boxstyle="round,pad=0.3",
                facecolor=BACKGROUND_COLOR,
                edgecolor=color,
                linewidth=1.5,
                alpha=0.9,
            )
            ax.add_patch(rect)

            ax.text(x + 0.5, y, team_name, ha='left', va='center',
                    fontsize=8, color='white', fontfamily=FONT,
                    fontweight='bold')
            ax.text(x + round_width - 0.5, y, f"{prob:.0%}", ha='right',
                    va='center', fontsize=8, color=color, fontfamily=FONT)


def _draw_probability_table(ax, team_probs: pd.DataFrame):
    """Draw probability table for top 20 teams."""
    cols_to_show = [
        ("team", "Team", 0.02, "left"),
        ("p_champion", "Champ", 0.38, "center"),
        ("p_final", "Final", 0.52, "center"),
        ("p_sf", "SF", 0.64, "center"),
        ("p_qf", "QF", 0.75, "center"),
        ("p_group_advance", "Grp", 0.87, "center"),
    ]

    # Title
    ax.text(0.5, 0.97, "Championship Odds (Top 20)", ha='center', va='center',
            fontsize=13, fontweight='bold', color='white', fontfamily=FONT,
            transform=ax.transAxes)

    # Headers
    y = 0.93
    for col, label, x, ha in cols_to_show:
        ax.text(x, y, label, ha=ha, va='center', fontsize=9, fontweight='bold',
                color='#aaaaaa', fontfamily=FONT, transform=ax.transAxes)

    # Separator
    ax.plot([0.02, 0.98], [y - 0.015, y - 0.015], color='#555555',
            linewidth=0.5, transform=ax.transAxes)

    # Rows
    top20 = team_probs.head(20)
    row_height = 0.04

    for idx, (_, row) in enumerate(top20.iterrows()):
        y_pos = 0.89 - idx * row_height

        for col, label, x, ha in cols_to_show:
            if col == "team":
                name = row[col]
                if len(name) > 18:
                    name = name[:16] + ".."
                p_champ = row.get("p_champion", 0)
                color = BRACKET_CMAP(min(p_champ * 5, 1.0))
                ax.text(x, y_pos, f"{idx + 1}. {name}", ha=ha, va='center',
                        fontsize=9, color=color, fontfamily=FONT,
                        fontweight='bold', transform=ax.transAxes)
            else:
                val = row.get(col, 0)
                if val > 0:
                    text = f"{val:.0%}" if val >= 0.01 else "<1%"
                else:
                    text = "-"
                ax.text(x, y_pos, text, ha=ha, va='center', fontsize=9,
                        color='white', fontfamily=FONT, transform=ax.transAxes)
