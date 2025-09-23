"""
Diamond scatter plot visualization adapted from original threat creators code.
Maintains exact visual aesthetic but works with FootballDecoded database structure.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from matplotlib.transforms import Affine2D
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axisartist.grid_finder import (MaxNLocator, DictFormatter)
from PIL import Image
import adjustText
import os

# Constants
BACKGROUND_COLOR = '#313332'
FONT_FAMILY = 'DejaVu Sans'

# Tu colormap personalizado
node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
    'deepskyblue', 'cyan', 'lawngreen', 'yellow',
    'gold', 'lightpink', 'tomato'
])

def format_axis_number(value):
    """
    Format axis numbers intelligently based on magnitude:
    - Numbers ≥100 (3+ digits): show as integer without decimals
    - Numbers <100 (1-2 digits): show with 2 decimals
    """
    if abs(value) >= 100:  # 3+ dígitos antes del punto
        return str(int(round(value)))
    else:  # 1-2 dígitos antes del punto
        return str(round(value, 2))

def create_diamond_scatter(df, x_metric, y_metric, title, save_filename):
    """
    Create diamond scatter plot (45° rotated axes) for two metrics.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with processed player data including metrics
    x_metric : str
        Column name for x-axis metric
    y_metric : str
        Column name for y-axis metric
    title : str
        Main title for the plot
    save_filename : str
        Filename to save the plot (will be saved in figures/ directory)
    """

    # Ensure figures directory exists
    os.makedirs('figures', exist_ok=True)

    # Get metrics and handle NaN values
    left_ax_plot = df[x_metric].copy()
    right_ax_plot = df[y_metric].copy()

    left_ax_plot.replace(np.nan, 0, inplace=True)
    right_ax_plot.replace(np.nan, 0, inplace=True)

    # Normalize for plotting (0-0.99 range)
    left_ax_norm_plot = 0.99 * left_ax_plot / max(left_ax_plot) if max(left_ax_plot) > 0 else left_ax_plot * 0
    right_ax_norm_plot = 0.99 * right_ax_plot / max(right_ax_plot) if max(right_ax_plot) > 0 else right_ax_plot * 0

    # Calculate quantiles for shading
    left_ax_quantile = left_ax_norm_plot.quantile([0.2, 0.5, 0.8]).tolist()
    right_ax_quantile = right_ax_norm_plot.quantile([0.2, 0.5, 0.8]).tolist()

    # Find top players to label (percentil 98+ en cualquiera de las dos métricas)
    # Asumiendo que el DF ya tiene columnas de percentiles con sufijo '_pct'
    x_pct_col = f"{x_metric}_pct"
    y_pct_col = f"{y_metric}_pct"

    if x_pct_col in df.columns and y_pct_col in df.columns:
        # NUEVA LÓGICA: Mínimo percentil 81 en ambas, luego TOP 10 por suma
        plot_player = df[(df[x_pct_col] >= 81) & (df[y_pct_col] >= 81)]

        # Si no hay suficientes con 81+, bajar
        if len(plot_player) < 5:
            plot_player = df[(df[x_pct_col] >= 75) & (df[y_pct_col] >= 75)]
        # Seleccionar TOP 10 por suma de percentiles
        if len(plot_player) > 0:
            plot_player_temp = plot_player.copy()
            plot_player_temp['_total_pct'] = plot_player_temp[x_pct_col] + plot_player_temp[y_pct_col]
            plot_player = plot_player_temp.nlargest(10, '_total_pct').drop(columns=['_total_pct'])
        else:
            # Último recurso: TOP 10 sin filtros
            df_temp = df.copy()
            df_temp['_total_pct'] = df_temp[x_pct_col] + df_temp[y_pct_col]
            plot_player = df_temp.nlargest(10, '_total_pct').drop(columns=['_total_pct'])
    else:
        # Fallback al método original si no hay percentiles
        plot_quantile_left = left_ax_norm_plot.quantile([0, 0.5, 0.9]).tolist()
        plot_quantile_right = right_ax_norm_plot.quantile([0, 0.5, 0.9]).tolist()
        plot_player = df[(left_ax_norm_plot > plot_quantile_left[2]) | (right_ax_norm_plot > plot_quantile_right[2])]
        # También limitar a 10 en el fallback
        if len(plot_player) > 10:
            plot_player = plot_player.head(10)

    # Set-up figure
    fig = plt.figure(figsize=(8.5, 9), facecolor=BACKGROUND_COLOR)

    # Set up diamond axis extent (normalized)
    left_extent = 1.001
    right_extent = 1.001
    plot_extents = 0, right_extent, 0, left_extent

    # Create reference dictionary for ticks (como original)
    ticks = list(np.arange(0, 1.1, 0.1))
    right_dict = {}
    left_dict = {}

    for i in ticks:
        if i == 0:
            left_dict[i] = ''
            right_dict[i] = ''
        else:
            left_value = (i * left_ax_plot.max()) / 0.99
            right_value = (i * right_ax_plot.max()) / 0.99
            left_dict[i] = format_axis_number(left_value)
            right_dict[i] = format_axis_number(right_value)

    tick_formatter1 = DictFormatter(right_dict)
    tick_formatter2 = DictFormatter(left_dict)

    # Define axis transformation, build axis and auxiliary axis
    transform = Affine2D().rotate_deg(45)
    helper = floating_axes.GridHelperCurveLinear(
        transform, plot_extents,
        grid_locator1=MaxNLocator(nbins=1+right_extent/0.1),
        grid_locator2=MaxNLocator(nbins=1+left_extent/0.1),
        tick_formatter1=tick_formatter1,
        tick_formatter2=tick_formatter2
    )
    ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=helper)
    ax.patch.set_alpha(0)
    ax.set_position([0.075, 0.07, 0.85, 0.8], which='both')
    aux_ax = ax.get_aux_axes(transform)

    # Add transformed axis
    ax = fig.add_axes(ax)
    aux_ax.patch = ax.patch

    # Format axes
    ax.axis['left'].line.set_color("w")
    ax.axis['bottom'].line.set_color("w")
    ax.axis['right'].set_visible(False)
    ax.axis['top'].set_visible(False)
    ax.axis['left'].major_ticklabels.set_rotation(0)
    ax.axis['left'].major_ticklabels.set_horizontalalignment("center")

    # Label axes
    ax.axis['left'].set_label(f"{x_metric}")
    ax.axis['left'].label.set_rotation(0)
    ax.axis['left'].label.set_color("w")
    ax.axis['left'].label.set_fontweight("bold")
    ax.axis['left'].label.set_fontsize(9)
    ax.axis['left'].LABELPAD += 7

    ax.axis['bottom'].set_label(f"{y_metric}")
    ax.axis['bottom'].label.set_color("w")
    ax.axis['bottom'].label.set_fontweight("bold")
    ax.axis['bottom'].label.set_fontsize(9)
    ax.axis['bottom'].LABELPAD += 7
    ax.axis['bottom'].major_ticklabels.set_pad(8)

    # Overwrite 0 labels
    z_ax1 = fig.add_axes([0.47, 0.05, 0.06, 0.0245])
    z_ax1.patch.set_color(BACKGROUND_COLOR)
    z_ax1.spines['right'].set_visible(False)
    z_ax1.spines['top'].set_visible(False)
    z_ax1.spines['bottom'].set_visible(False)
    z_ax1.spines['left'].set_visible(False)
    z_ax1.axes.xaxis.set_visible(False)
    z_ax1.axes.yaxis.set_visible(False)
    z_ax1.text(0.5, 0.5, 0, ha="center", va="center")

    # Axis grid
    ax.grid(alpha=0.2, color='w')

    # Plot points on auxiliary axis usando tu estética
    aux_ax.scatter(right_ax_norm_plot, left_ax_norm_plot,
                   c=left_ax_norm_plot + right_ax_norm_plot,
                   cmap=node_cmap, edgecolor='white', s=50, lw=0.5, zorder=2, alpha=0.7)

    # Add diagonal reference line (from bottom-left to top-right)
    aux_ax.plot([0, 100], [0, 100],
                color='white', linewidth=1.5, alpha=0.6, linestyle='--', zorder=1)

    # Add text annotations for top players with adjustText to prevent overlaps
    if len(plot_player) > 0:
        texts = []

        for idx, (i, player) in enumerate(plot_player.iterrows()):
            # Format player name
            if 'player_name' in player:
                name = player['player_name']
            elif 'name' in player:
                name = player['name']
            else:
                name = str(i)  # fallback to index

            if len(name.split(' ')) > 1:
                format_name = name.split(' ')[0][0] + " " + name.split(' ')[-1]
            else:
                format_name = name

            # Player point coordinates (normalized)
            point_x = right_ax_norm_plot.loc[i]
            point_y = left_ax_norm_plot.loc[i]

            # Create annotation
            text = aux_ax.annotate(format_name,
                                 xy=(point_x, point_y),
                                 color='yellow', fontsize=8, fontweight='bold',
                                 fontfamily=FONT_FAMILY, zorder=4,
                                 bbox=dict(boxstyle='round,pad=0.2', facecolor=BACKGROUND_COLOR,
                                         edgecolor='yellow', alpha=0.95, linewidth=1),
                                 ha='center', va='center',
                                 arrowprops=dict(arrowstyle='-', color='yellow', alpha=0.9,
                                               linewidth=1.2, connectionstyle='arc3,rad=0.05'))
            texts.append(text)

        # Use adjustText to prevent overlaps - labels alejados de nodos
        adjustText.adjust_text(texts, ax=aux_ax,
                             force_points=0.05,     # Mínima repulsión de puntos
                             force_text=1.5,        # Máxima separación entre textos
                             expand_points=(3.0, 3.0),  # Zona grande alrededor de puntos
                             expand_text=(2.0, 2.0),    # Separación grande entre textos
                             avoid_self_intersecting=True,
                             only_move={'points': 'xy', 'text': 'xy'},
                             arrowprops=dict(arrowstyle='-', color='yellow', alpha=0.9, linewidth=1.5))

    # Add axis shading (20th-80th percentiles)
    aux_ax.fill([right_ax_quantile[0], right_ax_quantile[0], right_ax_quantile[2], right_ax_quantile[2]],
                [0, 100, 100, 0], color='grey', alpha=0.15, zorder=0)
    aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [0, left_ax_quantile[0]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [left_ax_quantile[2], 100],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [0, left_ax_quantile[0]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [left_ax_quantile[2], 100],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)

    aux_ax.fill([0, right_ax_quantile[0], right_ax_quantile[0], 0],
                [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]],
                color='grey', alpha=0.15, zorder=0)
    aux_ax.fill([right_ax_quantile[2], 100, 100, right_ax_quantile[2]],
                [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]],
                color='grey', alpha=0.15, zorder=0)

    aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[0], left_ax_quantile[0]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[0], left_ax_quantile[0]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[2], left_ax_quantile[2]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)
    aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[2], left_ax_quantile[2]],
                color='w', lw=1, alpha=0.3, ls='dashed', zorder=0)

    # Add explanatory text areas
    # Left text axis
    text_ax_left = fig.add_axes([0.085, 0.47, 0.415, 0.392])   
    # Más arriba y más a la izquierda → restamos a x, sumamos a y
    dx, dy = -0.125, +0
    text_ax_left.plot([0.39+dx, 0.59+dx], [0.41+dy, 0.61+dy],
                    color='w', alpha=0.9, lw=0.5)
    text_ax_left.plot([0.49+dx, 0.36+dx], [0.51+dy, 0.64+dy],
                    color='w', alpha=0.9, lw=0.5)
    text_ax_left.text(0.125, 0.73, f"Players towards this\nside of the grid excel in\n{x_metric}",
                      ha="center", fontsize=9, alpha=0.8, color='w', fontfamily=FONT_FAMILY)
    text_ax_left.axis("off")
    text_ax_left.set_xlim([0, 1])
    text_ax_left.set_ylim([0, 1])


        
    # Right text axis
    text_ax_right = fig.add_axes([0.5, 0.47, 0.415, 0.392])    
    # Más arriba y más a la derecha → sumamos a x, sumamos a y
    dx, dy = +0.2, +0.05  
    text_ax_right.plot([0.61+dx, 0.41+dx], [0.41+dy, 0.61+dy],
                    color='w', alpha=0.9, lw=0.5)
    text_ax_right.plot([0.51+dx, 0.64+dx], [0.51+dy, 0.64+dy],
                    color='w', alpha=0.9, lw=0.5)
    text_ax_right.text(0.90, 0.73, f"Players towards this\nside of the grid excel in\n{y_metric}",
                       ha="center", fontsize=9, alpha=0.8, color='w', fontfamily=FONT_FAMILY)
    text_ax_right.axis("off")
    text_ax_right.set_xlim([0, 1])
    text_ax_right.set_ylim([0, 1])

    # Add bottom explanatory text
    text_ax_bottom = fig.add_axes([0.085, 0.078, 0.415, 0.392])
    text_ax_bottom.text(0.23, 0.05, "Shaded region represents\nplayers in the 20th to 80th\npercentile in either metric.",
                        ha="center", fontsize=9, alpha=0.8, color='w', fontfamily=FONT_FAMILY)
    text_ax_bottom.axis("off")
    text_ax_bottom.set_xlim([0, 1])
    text_ax_bottom.set_ylim([0, 1])

    # Title (sin subtítulo)
    fig.text(0.12, 0.935, title, fontweight="bold", fontsize=16, color='w', fontfamily=FONT_FAMILY)

    # Add competition logo (con fallback)
    try:
        logo_path = "../logos/competition_logo.png"
        if os.path.exists(logo_path):
            comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
            comp_ax.axis("off")
            comp_logo = Image.open(logo_path)
            comp_ax.imshow(comp_logo)
    except:
        pass  # No logo si no existe

    # Footer
    fig.text(0.08, 0.025, "Created by Jaime Oriol", fontweight='bold', fontsize=10,
             color="white", fontfamily=FONT_FAMILY)

    # Try to add logo
    try:
        logo_path = "../logo/Logo-blanco.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo_ax = plt.gcf().add_axes([0.685, -0.025, 0.32, 0.15])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        else:
            fig.text(0.6, 0.02, "Football Decoded", fontweight='bold', fontsize=14,
                     color="white", fontfamily=FONT_FAMILY)
    except:
        fig.text(0.6, 0.02, "Football Decoded", fontweight='bold', fontsize=14,
                 color="white", fontfamily=FONT_FAMILY)

    plt.tight_layout()

    # Save figure
    save_path = f'figures/{save_filename}'
    fig.savefig(save_path, dpi=300, facecolor=BACKGROUND_COLOR, bbox_inches='tight', edgecolor='none')

    return fig

# Overwrite rcparams for consistent styling
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'