"""
Swarm radar and traditional radar charts for player comparison.
10-metric system with distribution context (swarm plots) or
clean geometric radar with ring-based alternating colors.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from matplotlib.patches import Polygon
from matplotlib.transforms import Affine2D
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axes_grid1 import Divider
import mpl_toolkits.axes_grid1.axes_size as Size
import seaborn as sns
from mplsoccer import PyPizza
from PIL import Image
import os
import warnings
import textwrap

warnings.filterwarnings('ignore')
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

try:
    from soccerplots.radar_chart import Radar
    USE_SOCCERPLOTS = True
except ImportError:
    from mplsoccer import Radar
    USE_SOCCERPLOTS = False

BACKGROUND_COLOR = '#313332'

def _detect_id_column(df_data):
    """Detect whether dataframe uses player or team IDs."""
    if 'unique_player_id' in df_data.columns:
        return 'unique_player_id'
    elif 'unique_team_id' in df_data.columns:
        return 'unique_team_id'
    else:
        raise ValueError("DataFrame must contain either 'unique_player_id' or 'unique_team_id' column")

def create_player_radar(df_data,
                       player_1_id,
                       metrics,
                       metric_titles,
                       player_2_id=None,
                       player_1_color='#FF6B6B',
                       player_2_color='#4ECDC4',
                       team_colors=None,
                       radar_title='Player Comparison',
                       radar_description='Statistical comparison of selected players',
                       negative_metrics=None,
                       inverse_metrics=None,
                       save_path='player_radar.png',
                       show_plot=True,
                       use_swarm=True,
                       team_logos=None):
    """Create 10-metric radar chart (swarm or traditional). Requires exactly 10 metrics."""
    if negative_metrics is None:
        negative_metrics = []

    if inverse_metrics is None:
        inverse_metrics = []

    if len(metrics) != 10 or len(metric_titles) != 10:
        raise ValueError("Must provide exactly 10 metrics and 10 titles")
    
    if team_colors is None:
        colors = [player_1_color, player_2_color]
    else:
        colors = team_colors

    id_column = _detect_id_column(df_data)
    player_1_data = df_data[df_data[id_column] == player_1_id].iloc[0]
    player_2_data = None
    if player_2_id:
        player_2_data = df_data[df_data[id_column] == player_2_id].iloc[0]
    
    if use_swarm:
        _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                           colors, save_path, show_plot, id_column, inverse_metrics)
    else:
        _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                                 colors, save_path, show_plot, id_column, inverse_metrics)

def _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                       colors, save_path, show_plot, id_column, inverse_metrics=None):
    """Build radar with swarm plots showing dataset distribution around each metric."""
    
    comparison_df = df_data[[id_column] + metrics].copy()
    
    comparison_df['Primary Player'] = 'Untagged'
    comparison_df.loc[comparison_df[id_column] == player_1_data[id_column], 'Primary Player'] = 'Primary 1'
    if player_2_data is not None:
        comparison_df.loc[comparison_df[id_column] == player_2_data[id_column], 'Primary Player'] = 'Primary 2'
    
    comparison_df = comparison_df.sort_values('Primary Player')
    
    path_eff = [path_effects.Stroke(linewidth=2, foreground=BACKGROUND_COLOR), path_effects.Normal()]
    
    theta_mid = np.radians(np.linspace(0, 360, 10+1))[:-1] + np.pi/2
    theta_mid = [x if x < 2*np.pi else x - 2*np.pi for x in theta_mid]
    
    r_base = [0.231 if (angle > np.pi/4 and angle < 3*np.pi/4) or (angle > 5*np.pi/4 and angle < 7*np.pi/4) 
              else 0.25 for angle in theta_mid]
    
    x_base, y_base = 0.325 + np.array(r_base) * np.cos(theta_mid), 0.3 + 0.89 * np.array(r_base) * np.sin(theta_mid)
    
    # Height must match stats_table for side-by-side alignment
    fig = plt.figure(constrained_layout=False, figsize=(9, 11), facecolor=BACKGROUND_COLOR)
    
    theta = np.linspace(0, 2*np.pi, 100)
    radar_ax = fig.add_axes([0.025, 0, 0.95, 0.95], polar=True)
    radar_ax.plot(theta, theta*0 + 0.17, color='w', lw=1.2)
    for r in [0.3425, 0.5150, 0.6875, 0.86]:
        radar_ax.plot(theta, theta*0 + r, color='grey', lw=1, alpha=0.4)
    radar_ax.axis('off')
    
    ax_mins, ax_maxs = [], []
    
    for idx, metric in enumerate(metrics):
        fig_save, ax_save = plt.subplots(figsize=(4.5, 1.5))
        fig_save.set_facecolor(BACKGROUND_COLOR)
        fig_save.patch.set_alpha(0)
        
        sns.swarmplot(x=comparison_df[metric], y=[""]*len(comparison_df), 
                     color='grey', edgecolor='w', size=5, zorder=1)
        
        ax_save.legend([], [], frameon=False)
        ax_save.patch.set_alpha(0)
        ax_save.spines['bottom'].set_position(('axes', 0.5))
        ax_save.spines['bottom'].set_color('w')
        ax_save.spines['top'].set_color(None)
        ax_save.spines['right'].set_color('w')
        ax_save.spines['left'].set_color(None)
        ax_save.set_xlabel("")
        ax_save.tick_params(left=False, bottom=True, axis='both', which='major', 
                           labelsize=8, zorder=10, pad=0, colors='w')
        
        rotation = 180 if theta_mid[idx] >= np.pi/2 and theta_mid[idx] <= 3*np.pi/2 else 0
        plt.xticks(path_effects=path_eff, fontweight='bold', rotation=rotation, family='DejaVu Sans')
        
        ax_mins.append(ax_save.get_xlim()[0])
        ax_maxs.append(ax_save.get_xlim()[1])
        
        temp_path = f'temp_{idx}.png'
        fig_save.savefig(temp_path, dpi=300)
        
        scales = (0, 1, 0, 1)
        t = Affine2D().scale(3, 1).rotate_deg(theta_mid[idx]*(180/np.pi))
        h = floating_axes.GridHelperCurveLinear(t, scales)
        ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=h)
        
        ax = fig.add_subplot(ax)
        aux_ax = ax.get_aux_axes(t)
        
        horiz_scale = [Size.Scaled(1.04)]
        vert_scale = [Size.Scaled(1.0)]
        ax_div = Divider(fig, [x_base[idx], y_base[idx], 0.35, 0.35], horiz_scale, vert_scale, aspect=True)
        ax_loc = ax_div.new_locator(nx=0, ny=0)
        ax.set_axes_locator(ax_loc)
        
        img = Image.open(temp_path)
        aux_ax.imshow(img, extent=[-0.18, 1.12, -0.15, 1.15])
        ax.axis('off')
        for spine in ['right', 'top', 'bottom', 'left']:
            ax.axis[spine].set_visible(False)
        
        text_rotation_delta = 90 if theta_mid[idx] >= np.pi else -90
        radar_ax.text(theta_mid[idx], 0.92, metric_titles[idx], 
                     ha="center", va="center", fontweight="bold", 
                     fontsize=10, color='w', family='DejaVu Sans',
                     rotation=text_rotation_delta + (180/np.pi) * theta_mid[idx])
        
        plt.close(fig_save)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    radar_ax.set_rmax(1)
    
    pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82], polar=True)
    pizza_ax.set_theta_offset(17)
    pizza_ax.axis('off')
    
    pizza_metrics = [metrics[0]] + list(reversed(metrics[1:]))
    ax_mins_pizza = [ax_mins[0]] + list(reversed(ax_mins[1:]))
    ax_maxs_pizza = [ax_maxs[0]] + list(reversed(ax_maxs[1:]))
    
    radar_values_p1 = [player_1_data[m] for m in pizza_metrics]
    radar_values_p2 = [player_2_data[m] for m in pizza_metrics] if player_2_data is not None else None
    
    radar_object = PyPizza(params=pizza_metrics, background_color="w", straight_line_color="w",
                          min_range=ax_mins_pizza, max_range=ax_maxs_pizza,
                          straight_line_lw=1, straight_line_limit=100,
                          last_circle_lw=0.1, other_circle_lw=0.1, inner_circle_size=18)
    
    kwargs = {
        'values': radar_values_p1,
        'color_blank_space': 'same',
        'blank_alpha': 0,
        'bottom': 5,
        'kwargs_params': dict(fontsize=0, color='None'),
        'kwargs_values': dict(fontsize=0, color='None'),
        'kwargs_slices': dict(facecolor=colors[0], alpha=0.35, edgecolor=BACKGROUND_COLOR, linewidth=1, zorder=1),
        'ax': pizza_ax
    }
    
    if radar_values_p2:
        kwargs['compare_values'] = radar_values_p2
        kwargs['kwargs_compare_values'] = dict(fontsize=0, color='None')
        kwargs['kwargs_compare'] = dict(facecolor=colors[1], alpha=0.35, edgecolor=BACKGROUND_COLOR, linewidth=1, zorder=3)
    
    radar_object.make_pizza(**kwargs)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    if show_plot:
        plt.show()
    else:
        plt.close()

    for i in range(10):
        temp_file = f'temp_{i}.png'
        if os.path.exists(temp_file):
            os.remove(temp_file)

def _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                             colors, save_path, show_plot, id_column, inverse_metrics=None):
    """Build geometric radar with percentile ranges. Ring-alternating colors for 1 player, solid for 2."""
    
    # Same metric ordering as swarm radar
    reordered_metrics = [metrics[0]] + list(reversed(metrics[1:]))
    reordered_titles = [metric_titles[0]] + list(reversed(metric_titles[1:]))
    
    # Percentile-based ranges (1st-99th)
    ranges = []
    for metric in reordered_metrics:
        metric_data = df_data[metric].dropna()
        min_val = np.percentile(metric_data, 1)
        max_val = np.percentile(metric_data, 99)
        ranges.append((min_val, max_val))
    
    fig, ax = plt.subplots(figsize=(9, 10), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_aspect('equal')
    ax.set(xlim=(-22, 22), ylim=(-23, 25))

    player_1_values = [player_1_data[m] for m in reordered_metrics]
    player_2_values = [player_2_data[m] for m in reordered_metrics] if player_2_data is not None else None
    
    # Concentric circles
    radius_circles = [3, 5.5, 8, 10.5, 13, 15.5, 18, 20.5]
    for i, rad in enumerate(radius_circles):
        if i == 0:
            continue
        elif i == len(radius_circles)-1:
            color, lw, alpha = 'white', 1.2, 1.0
        else:
            color, lw, alpha = 'grey', 1, 0.4
            
        circle = plt.Circle(xy=(0, 0), radius=rad, fc='none', ec=color, lw=lw, alpha=alpha)
        ax.add_patch(circle)
    
    n_params = len(reordered_metrics)
    angles = np.linspace(0, 2*np.pi, n_params, endpoint=False)

    # Metric labels
    label_radius = 21.5
    for i, (angle, title) in enumerate(zip(angles, reordered_titles)):
        x = label_radius * np.sin(angle)
        y = label_radius * np.cos(angle)
        
        rot_deg = -np.rad2deg(angle)
        if y < 0:
            rot_deg += 180
            
        ax.text(x, y, title, rotation=rot_deg, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white', family='DejaVu Sans')
    
    # Radial lines
    for angle in angles:
        x_end = 20.5 * np.sin(angle)
        y_end = 20.5 * np.cos(angle)
        ax.plot([0, x_end], [0, y_end], color='grey', linewidth=0.5, alpha=0.4)
    
    # Value labels on concentric circles
    range_radius = [4.25, 6.75, 9.25, 11.75, 14.25, 16.75, 19.25]

    if inverse_metrics is None:
        inverse_metrics = []

    for rad_idx, rad in enumerate(range_radius):
        for i, (angle, metric) in enumerate(zip(angles, reordered_metrics)):
            min_val, max_val = ranges[i]

            range_total = max_val - min_val
            if range_total == 0:
                val = min_val
            else:
                rad_normalized = (rad - 3) / (20.5 - 3)

                if metric in inverse_metrics:
                    # Inverse: center=max, edge=min
                    val = max_val - rad_normalized * range_total
                else:
                    val = min_val + rad_normalized * range_total

            x = rad * np.sin(angle)
            y = rad * np.cos(angle)

            if val < 0.01:
                label = f'{val:.3f}'
            elif val < 1:
                label = f'{val:.2f}'
            elif val < 10:
                label = f'{val:.1f}'
            else:
                label = f'{int(val)}'

            ax.text(x, y, label, ha='center', va='center', size=7, color='white',
                   bbox=dict(boxstyle='round,pad=0.15', facecolor=BACKGROUND_COLOR,
                           edgecolor='none', alpha=0.9), family='DejaVu Sans')
    
    def get_radar_coordinates(values, ranges, inverse_metrics_list=None):
        """Convert metric values to polar coordinates within the radar radius."""
        if inverse_metrics_list is None:
            inverse_metrics_list = []

        vertices = []
        for i, (value, (min_val, max_val)) in enumerate(zip(values, ranges)):
            metric_name = reordered_metrics[i]

            if max_val == min_val:
                norm_value = 11.75
            else:
                if metric_name in inverse_metrics_list:
                    norm_value = 3 + (max_val - value) / (max_val - min_val) * 17.5
                else:
                    norm_value = 3 + (value - min_val) / (max_val - min_val) * 17.5

            norm_value = max(3, min(20.5, norm_value))

            angle = angles[i]
            x = norm_value * np.sin(angle)
            y = norm_value * np.cos(angle)
            vertices.append([x, y])

        return vertices
    
    # Player 1 polygon
    vertices_1 = get_radar_coordinates(player_1_values, ranges, inverse_metrics)
    
    if player_2_data is None:
        # Single player: alternating ring colors inside polygon
        polygon_1 = Polygon(vertices_1, fc='none', alpha=1.0, zorder=1)
        ax.add_patch(polygon_1)
        
        central_circle = plt.Circle(xy=(0, 0), radius=radius_circles[0], 
                                fc=colors[0], ec='none', alpha=0.45, zorder=2)
        central_circle.set_clip_path(polygon_1)
        ax.add_patch(central_circle)
        
        theta = np.linspace(0, 2*np.pi, 100)
        
        for i in range(len(radius_circles)-1):
            inner_radius = radius_circles[i]
            outer_radius = radius_circles[i+1]
            
            color_idx = (i + 1) % 2  # Start with colors[1]
            x_outer = outer_radius * np.cos(theta)
            y_outer = outer_radius * np.sin(theta)
            x_inner = inner_radius * np.cos(theta)
            y_inner = inner_radius * np.sin(theta)
            
            ring_vertices = list(zip(x_outer, y_outer)) + list(zip(x_inner[::-1], y_inner[::-1]))
            ring_polygon = Polygon(ring_vertices, fc=colors[color_idx], alpha=0.45, zorder=2)
            
            ring_polygon.set_clip_path(polygon_1)
            ax.add_patch(ring_polygon)
        
        # Player outline
        vertices_1_closed = vertices_1 + [vertices_1[0]]
        x_coords_1 = [v[0] for v in vertices_1_closed]
        y_coords_1 = [v[1] for v in vertices_1_closed]
        ax.plot(x_coords_1, y_coords_1, color=colors[0], linewidth=3, zorder=10)
        
    else:
        # Two players: solid color polygons
        polygon_1 = Polygon(vertices_1, fc=colors[0], alpha=0.35, zorder=2)
        ax.add_patch(polygon_1)
        
        vertices_1_closed = vertices_1 + [vertices_1[0]]
        x_coords_1 = [v[0] for v in vertices_1_closed]
        y_coords_1 = [v[1] for v in vertices_1_closed]
        ax.plot(x_coords_1, y_coords_1, color=colors[0], linewidth=3, zorder=3)
        
        # Player 2
        vertices_2 = get_radar_coordinates(player_2_values, ranges, inverse_metrics)
        polygon_2 = Polygon(vertices_2, fc=colors[1], alpha=0.35, zorder=2)
        ax.add_patch(polygon_2)
        
        vertices_2_closed = vertices_2 + [vertices_2[0]]
        x_coords_2 = [v[0] for v in vertices_2_closed]
        y_coords_2 = [v[1] for v in vertices_2_closed]
        ax.plot(x_coords_2, y_coords_2, color=colors[1], linewidth=3, zorder=3)
    
    ax.axis('off')
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    if show_plot:
        plt.show()
    else:
        plt.close()