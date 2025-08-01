import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from matplotlib.transforms import Affine2D
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axes_grid1 import Divider
import mpl_toolkits.axes_grid1.axes_size as Size
import seaborn as sns
from mplsoccer import PyPizza
from PIL import Image
import os
import warnings

# Suppress all font warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# Try importing Radar with fallback
try:
    from soccerplots.radar_chart import Radar
    USE_SOCCERPLOTS = True
except ImportError:
    from mplsoccer import Radar
    USE_SOCCERPLOTS = False

def create_player_radar(df_data, 
                       player_1_id,
                       metrics,
                       metric_titles,
                       player_2_id=None,
                       player_1_color='lightskyblue',
                       player_2_color='coral',
                       radar_title='Player Comparison',
                       radar_description='Statistical comparison of selected players',
                       negative_metrics=None,
                       save_path='player_radar.png',
                       show_plot=True,
                       use_swarm=True,
                       team_colors=None):
    """
    Create swarm radar or traditional radar for player comparison
    """
    if negative_metrics is None:
        negative_metrics = []
    
    if len(metrics) != 10 or len(metric_titles) != 10:
        raise ValueError("Must provide exactly 10 metrics and 10 titles")
    
    player_1_data = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    player_2_data = None
    if player_2_id:
        player_2_data = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    if use_swarm:
        _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                           player_1_color, player_2_color, radar_title, radar_description,
                           negative_metrics, save_path, show_plot)
    else:
        _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                                 radar_title, radar_description, save_path, show_plot, team_colors)

def _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                       player_1_color, player_2_color, radar_title, radar_description,
                       negative_metrics, save_path, show_plot):
    """Original swarm radar - unchanged"""
    
    comparison_df = df_data[['unique_player_id'] + metrics].copy()
    
    comparison_df['Primary Player'] = 'Untagged'
    comparison_df.loc[comparison_df['unique_player_id'] == player_1_data['unique_player_id'], 'Primary Player'] = 'Primary 1'
    if player_2_data is not None:
        comparison_df.loc[comparison_df['unique_player_id'] == player_2_data['unique_player_id'], 'Primary Player'] = 'Primary 2'
    
    comparison_df = comparison_df.sort_values('Primary Player')
    
    path_eff = [path_effects.Stroke(linewidth=2, foreground='#313332'), path_effects.Normal()]
    
    num_metrics = 10
    
    theta_mid = np.radians(np.linspace(0, 360, num_metrics+1))[:-1] + np.pi/2
    theta_mid = [x if x < 2*np.pi else x - 2*np.pi for x in theta_mid]
    
    r_base = []
    for angle in theta_mid:
        if (angle > np.pi/4 and angle < 3*np.pi/4) or (angle > 5*np.pi/4 and angle < 7*np.pi/4):
            r_base.append(0.231)
        else:
            r_base.append(0.25)
    
    x_base, y_base = 0.325 + np.array(r_base) * np.cos(theta_mid), 0.3 + 0.89 * np.array(r_base) * np.sin(theta_mid)
    
    fig = plt.figure(constrained_layout=False, figsize=(9, 11))
    fig.set_facecolor('#313332')
    
    theta = np.linspace(0, 2*np.pi, 100)
    radar_ax = fig.add_axes([0.025, 0, 0.95, 0.95], polar=True)
    radar_ax.plot(theta, theta*0 + 0.17, color='w', lw=1)
    radar_ax.plot(theta, theta*0 + 0.3425, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.5150, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.6875, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.86, color='grey', lw=1, alpha=0.3)
    radar_ax.axis('off')
    
    ax_mins = []
    ax_maxs = []
    
    for idx, metric in enumerate(metrics):
        fig_save, ax_save = plt.subplots(figsize=(4.5, 1.5))
        fig_save.set_facecolor('#313332')
        fig_save.patch.set_alpha(0)
        
        sns.swarmplot(x=comparison_df[metric], 
                     y=[""]*len(comparison_df), 
                     color='grey', 
                     edgecolor='w', 
                     size=3,
                     zorder=1)
        
        ax_save.legend([], [], frameon=False)
        ax_save.patch.set_alpha(0)
        ax_save.spines['bottom'].set_position(('axes', 0.5))
        ax_save.spines['bottom'].set_color('w')
        ax_save.spines['top'].set_color(None)
        ax_save.spines['right'].set_color('w')
        ax_save.spines['left'].set_color(None)
        ax_save.set_xlabel("")
        ax_save.tick_params(left=False, bottom=True)
        ax_save.tick_params(axis='both', which='major', labelsize=8, zorder=10, pad=0, colors='w')
        
        if theta_mid[idx] < np.pi/2 or theta_mid[idx] > 3*np.pi/2:
            plt.xticks(path_effects=path_eff, fontweight='bold')
        else:
            plt.xticks(path_effects=path_eff, fontweight='bold', rotation=180)
        
        if metric in negative_metrics:
            ax_save.invert_xaxis()
        
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
        ax.axis['right'].set_visible(False)
        ax.axis['top'].set_visible(False)
        ax.axis['bottom'].set_visible(False)
        ax.axis['left'].set_visible(False)
        
        if theta_mid[idx] >= np.pi:
            text_rotation_delta = 90
        else:
            text_rotation_delta = -90
        
        radar_ax.text(theta_mid[idx], 0.92, metric_titles[idx], 
                     ha="center", va="center", fontweight="bold", 
                     fontsize=10, color='w',
                     rotation=text_rotation_delta + (180/np.pi) * theta_mid[idx])
        
        plt.close(fig_save)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    radar_ax.set_rmax(1)
    
    fig.text(0.11, 0.953, player_1_data['player_name'], fontweight="bold", fontsize=14, color=player_1_color)
    fig.text(0.11, 0.931, player_1_data['team'], fontweight="bold", fontsize=12, color='w')
    fig.text(0.11, 0.909, f"{player_1_data['league']} {player_1_data['season']}", fontweight="bold", fontsize=12, color='w')
    minutes = int(player_1_data.get('minutes_played', 0))
    matches = int(player_1_data.get('matches_played', 0))
    fig.text(0.11, 0.887, f"{minutes} mins | {matches} matches", fontsize=10, color='w', alpha=0.8)
    
    if player_2_data is not None:
        fig.text(0.48, 0.953, player_2_data['player_name'], fontweight="bold", fontsize=14, color=player_2_color)
        fig.text(0.48, 0.931, player_2_data['team'], fontweight="bold", fontsize=12, color='w')
        fig.text(0.48, 0.909, f"{player_2_data['league']} {player_2_data['season']}", fontweight="bold", fontsize=12, color='w')
        minutes2 = int(player_2_data.get('minutes_played', 0))
        matches2 = int(player_2_data.get('matches_played', 0))
        fig.text(0.48, 0.887, f"{minutes2} mins | {matches2} matches", fontsize=10, color='w', alpha=0.8)
    
    pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82], polar=True)
    pizza_ax.set_theta_offset(17)
    pizza_ax.axis('off')
    
    pizza_metrics = [metrics[0]] + list(reversed(metrics[1:]))
    ax_mins = [ax_mins[0]] + list(reversed(ax_mins[1:]))
    ax_maxs = [ax_maxs[0]] + list(reversed(ax_maxs[1:]))
    
    radar_values_p1 = [player_1_data[m] for m in pizza_metrics]
    radar_values_p2 = [player_2_data[m] for m in pizza_metrics] if player_2_data is not None else None
    
    radar_object = PyPizza(params=pizza_metrics,
                          background_color="w",
                          straight_line_color="w",
                          min_range=ax_mins,
                          max_range=ax_maxs,
                          straight_line_lw=1,
                          straight_line_limit=100,
                          last_circle_lw=0.1,
                          other_circle_lw=0.1,
                          inner_circle_size=18)
    
    kwargs = {
        'values': radar_values_p1,
        'color_blank_space': 'same',
        'blank_alpha': 0,
        'bottom': 5,
        'kwargs_params': dict(fontsize=0, color='None'),
        'kwargs_values': dict(fontsize=0, color='None'),
        'kwargs_slices': dict(facecolor=player_1_color, alpha=0.3, edgecolor='#313332', linewidth=1, zorder=1),
        'ax': pizza_ax
    }
    
    if radar_values_p2:
        kwargs['compare_values'] = radar_values_p2
        kwargs['kwargs_compare_values'] = dict(fontsize=0, color='None')
        kwargs['kwargs_compare'] = dict(facecolor=player_2_color, alpha=0.3, edgecolor='#313332', linewidth=1, zorder=3)
    
    radar_object.make_pizza(**kwargs)
    
    title_x = 0.835
    fig.text(title_x, 0.953, radar_title, fontweight="bold", fontsize=12, color='w', ha='left')
    
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(radar_description, 40))
    fig.text(title_x, 0.935, wrapped_desc, fontweight="regular", fontsize=8, color='w', ha='left', va='top')
    
    fig.text(0.5, 0.02, "Created by Jaime Oriol", 
             fontstyle="italic", ha="center", fontsize=9, color="white")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    for i in range(10):
        temp_file = f'temp_{i}.png'
        if os.path.exists(temp_file):
            os.remove(temp_file)

def _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                             radar_title, radar_description, save_path, show_plot, team_colors):
    """Traditional radar with exact swarm layout and fixed percentile rings"""
    
    # Suppress font warnings completely
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Set colors
    if team_colors is None:
        if player_2_data is not None:
            colors = ['#FF6B6B', '#4ECDC4']  # Vibrant red-coral, vibrant teal
        else:
            colors = ['#FF6B6B', '#FFFFFF']  # Vibrant red-coral, white
    else:
        colors = team_colors
    
    # Create figure with exact swarm structure
    fig, ax = plt.subplots(figsize=(9, 11), facecolor='#313332')
    
    # Calculate 9 percentile values for each metric
    percentile_levels = [1, 14, 26, 38, 50, 62, 74, 86, 99]
    ranges = []
    
    for metric in metrics:
        metric_values = df_data[metric].dropna()
        percentile_values = np.percentile(metric_values, percentile_levels)
        ranges.append([percentile_values[0], percentile_values[-1]])  # min, max for range
    
    # Prepare data
    values_1 = [player_1_data[metric] for metric in metrics]
    
    if USE_SOCCERPLOTS:
        # Use soccerplots radar
        if player_2_data is None:
            # Single player
            radar = Radar(label_fontsize=13, range_fontsize=10, 
                         label_color='white', range_color='white')
            fig, ax = radar.plot_radar(ranges=ranges, params=metric_titles, values=values_1, 
                                      radar_color=colors, figax=(fig, ax))
        else:
            # Two players
            values_2 = [player_2_data[metric] for metric in metrics]
            values = [values_1, values_2]
            
            radar = Radar(label_fontsize=12, range_fontsize=9,
                         label_color='white', range_color='white')
            fig, ax = radar.plot_radar(ranges=ranges, params=metric_titles, values=values, 
                                      radar_color=colors, figax=(fig, ax), compare=True)
    else:
        # mplsoccer radar fallback
        min_ranges = [r[0] for r in ranges]
        max_ranges = [r[1] for r in ranges]
        
        # Calculate custom range values for 9 rings
        range_values = []
        for metric in metrics:
            metric_values = df_data[metric].dropna()
            percentile_values = np.percentile(metric_values, percentile_levels)
            range_values.append(percentile_values)
        
        radar = Radar(params=metric_titles, min_range=min_ranges, max_range=max_ranges,
                     num_rings=9, ring_width=1)
        fig, ax = radar.setup_axis(facecolor='#313332')
        
        rings_inner = radar.draw_circles(ax=ax, facecolor='#555', edgecolor='#777', linewidth=0.5)
        
        if player_2_data is None:
            radar_output = radar.draw_radar(values_1, ax=ax, 
                                          kwargs_radar={'facecolor': colors[0], 'alpha': 0.7,
                                                       'edgecolor': colors[0], 'linewidth': 2})
        else:
            values_2 = [player_2_data[metric] for metric in metrics]
            radar_output1 = radar.draw_radar(values_1, ax=ax, 
                                           kwargs_radar={'facecolor': colors[0], 'alpha': 0.5,
                                                        'edgecolor': colors[0], 'linewidth': 2})
            radar_output2 = radar.draw_radar(values_2, ax=ax, 
                                           kwargs_radar={'facecolor': colors[1], 'alpha': 0.5,
                                                        'edgecolor': colors[1], 'linewidth': 2})
        
        # Custom range labels with percentile values
        for i, (metric, percentile_vals) in enumerate(zip(metrics, range_values)):
            angle = 2 * np.pi * i / len(metrics)
            for j, val in enumerate(percentile_vals[::2]):  # Show every other value to avoid crowding
                radius = 0.2 + (0.8 * j / 4)  # Spread across 4 rings
                x = radius * np.cos(angle + np.pi/2)
                y = radius * np.sin(angle + np.pi/2)
                ax.text(x, y, f'{val:.2f}', fontsize=8, ha='center', va='center', 
                       color='white', fontweight='bold')
                
        param_labels = radar.draw_param_labels(ax=ax, fontsize=11, color='white', fontweight='bold')
    
    # Apply dark styling
    fig.patch.set_facecolor('#313332')
    if hasattr(ax, 'set_facecolor'):
        ax.set_facecolor('#313332')
    
    # EXACT swarm layout structure
    fig.text(0.11, 0.953, player_1_data['player_name'], fontweight="bold", fontsize=14, color=colors[0])
    fig.text(0.11, 0.931, player_1_data['team'], fontweight="bold", fontsize=12, color='w')
    fig.text(0.11, 0.909, f"{player_1_data['league']} {player_1_data['season']}", fontweight="bold", fontsize=12, color='w')
    minutes = int(player_1_data.get('minutes_played', 0))
    matches = int(player_1_data.get('matches_played', 0))
    fig.text(0.11, 0.887, f"{minutes} mins | {matches} matches", fontsize=10, color='w', alpha=0.8)
    
    if player_2_data is not None:
        fig.text(0.48, 0.953, player_2_data['player_name'], fontweight="bold", fontsize=14, color=colors[1])
        fig.text(0.48, 0.931, player_2_data['team'], fontweight="bold", fontsize=12, color='w')
        fig.text(0.48, 0.909, f"{player_2_data['league']} {player_2_data['season']}", fontweight="bold", fontsize=12, color='w')
        minutes2 = int(player_2_data.get('minutes_played', 0))
        matches2 = int(player_2_data.get('matches_played', 0))
        fig.text(0.48, 0.887, f"{minutes2} mins | {matches2} matches", fontsize=10, color='w', alpha=0.8)
    
    # Title and description - exact swarm position
    title_x = 0.835
    fig.text(title_x, 0.953, radar_title, fontweight="bold", fontsize=12, color='w', ha='left')
    
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(radar_description, 40))
    fig.text(title_x, 0.935, wrapped_desc, fontweight="regular", fontsize=8, color='w', ha='left', va='top')
    
    # Footer - exact swarm position (NO "Inspired by")
    fig.text(0.5, 0.02, "Created by Jaime Oriol", 
             fontstyle="italic", ha="center", fontsize=9, color="white")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    if show_plot:
        plt.show()
    else:
        plt.close()