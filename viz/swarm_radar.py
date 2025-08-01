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
                       team_colors=None,
                       team_logos=None):
    """
    Create swarm radar or traditional radar for player comparison
    
    Args:
        team_logos: dict mapping team names to logo paths {'Barcelona': 'path/to/barca.png'}
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
                           negative_metrics, save_path, show_plot, team_logos)
    else:
        _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                                 radar_title, radar_description, save_path, show_plot, team_colors, team_logos)

def _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                       player_1_color, player_2_color, radar_title, radar_description,
                       negative_metrics, save_path, show_plot, team_logos):
    """Original swarm radar with logo support"""
    
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
    
    # Adjusted figure with less vertical space
    fig = plt.figure(constrained_layout=False, figsize=(9, 10))
    fig.set_facecolor('#313332')
    
    # FIXED: Use the same axes position for both radar_ax and pizza_ax
    axes_position = [0.09, 0.10, 0.82, 0.82]
    
    theta = np.linspace(0, 2*np.pi, 100)
    radar_ax = fig.add_axes(axes_position, polar=True)
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
    
    # Team logos if provided
    if team_logos and player_1_data['team'] in team_logos:
        try:
            logo_1 = Image.open(team_logos[player_1_data['team']])
            logo_ax_1 = fig.add_axes([0.05, 0.945, 0.04, 0.04])
            logo_ax_1.imshow(logo_1)
            logo_ax_1.axis('off')
            text_x_1 = 0.11
        except:
            text_x_1 = 0.11
    else:
        text_x_1 = 0.11
    
    # Player 1 info
    fig.text(text_x_1, 0.963, player_1_data['player_name'], fontweight="bold", fontsize=14, color=player_1_color)
    fig.text(text_x_1, 0.941, player_1_data['team'], fontweight="bold", fontsize=12, color='w')
    fig.text(text_x_1, 0.919, f"{player_1_data['league']} {player_1_data['season']}", fontweight="bold", fontsize=12, color='w')
    minutes = int(player_1_data.get('minutes_played', 0))
    matches = int(player_1_data.get('matches_played', 0))
    fig.text(text_x_1, 0.897, f"{minutes} mins | {matches} matches", fontsize=10, color='w', alpha=0.8)
    
    if player_2_data is not None:
        # Team 2 logo if provided
        if team_logos and player_2_data['team'] in team_logos:
            try:
                logo_2 = Image.open(team_logos[player_2_data['team']])
                logo_ax_2 = fig.add_axes([0.42, 0.945, 0.04, 0.04])
                logo_ax_2.imshow(logo_2)
                logo_ax_2.axis('off')
                text_x_2 = 0.48
            except:
                text_x_2 = 0.48
        else:
            text_x_2 = 0.48
            
        fig.text(text_x_2, 0.963, player_2_data['player_name'], fontweight="bold", fontsize=14, color=player_2_color)
        fig.text(text_x_2, 0.941, player_2_data['team'], fontweight="bold", fontsize=12, color='w')
        fig.text(text_x_2, 0.919, f"{player_2_data['league']} {player_2_data['season']}", fontweight="bold", fontsize=12, color='w')
        minutes2 = int(player_2_data.get('minutes_played', 0))
        matches2 = int(player_2_data.get('matches_played', 0))
        fig.text(text_x_2, 0.897, f"{minutes2} mins | {matches2} matches", fontsize=10, color='w', alpha=0.8)
    
    # FIXED: Use the same axes position as radar_ax
    pizza_ax = fig.add_axes(axes_position, polar=True)
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
    fig.text(title_x, 0.963, radar_title, fontweight="bold", fontsize=12, color='w', ha='left')
    
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(radar_description, 40))
    fig.text(title_x, 0.945, wrapped_desc, fontweight="regular", fontsize=8, color='w', ha='left', va='top')
    
    # Footer moved up - NO "Inspired by"
    fig.text(0.5, 0.05, "Created by Jaime Oriol", 
             fontstyle="italic", ha="center", fontsize=9, color="white")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    # Cleanup temp files
    for i in range(10):
        temp_file = f'temp_{i}.png'
        if os.path.exists(temp_file):
            os.remove(temp_file)

def _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                             radar_title, radar_description, save_path, show_plot, team_colors, team_logos):
    """Traditional radar with fixed percentile rings and swarm layout"""
    
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Set colors
    if team_colors is None:
        colors = ['#FF6B6B', '#4ECDC4'] if player_2_data is not None else ['#FF6B6B', '#FFFFFF']
    else:
        colors = team_colors
    
    # Create figure with exact swarm dimensions and spacing
    fig = plt.figure(figsize=(9, 10), facecolor='#313332')
    
    # Calculate 9 percentile values for each metric
    percentile_levels = [1, 14, 26, 38, 50, 62, 74, 86, 99]
    percentile_values_all = []
    
    for metric in metrics:
        metric_data = df_data[metric].dropna()
        percentiles = np.percentile(metric_data, percentile_levels)
        percentile_values_all.append(percentiles)
    
    # Create radar axis - match swarm positioning
    ax = fig.add_subplot(111, projection='polar', position=[0.09, 0.10, 0.82, 0.75])
    
    # Setup angles
    num_vars = len(metrics)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    
    # Configure radar
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_facecolor('#313332')
    
    # Draw the 9 rings with exact swarm styling
    ring_positions = np.linspace(0.17, 0.86, 9)  # Match swarm ring positions
    for i, pos in enumerate(ring_positions):
        if i == 0:
            ax.plot(angles, [pos]*len(angles), color='white', linewidth=1, alpha=1.0)
        else:
            ax.plot(angles, [pos]*len(angles), color='grey', linewidth=1, alpha=0.3)
    
    # Add grid lines from center to edge
    for angle in angles[:-1]:
        ax.plot([angle, angle], [0, 0.86], color='grey', linewidth=0.5, alpha=0.3)
    
    # Add percentile value labels - ONE PER RING ON EACH SPOKE
    for metric_idx, percentiles in enumerate(percentile_values_all):
        angle = angles[metric_idx]
        
        for ring_idx, (ring_pos, percentile_val) in enumerate(zip(ring_positions, percentiles)):
            # Format value based on magnitude
            if percentile_val < 0.01:
                label = f'{percentile_val:.3f}'
            elif percentile_val < 1:
                label = f'{percentile_val:.2f}'
            elif percentile_val < 10:
                label = f'{percentile_val:.1f}'
            else:
                label = f'{int(percentile_val)}'
            
            # Position label on the ring
            ax.text(angle, ring_pos, label,
                   ha='center', va='center',
                   size=7, color='white', weight='normal',
                   bbox=dict(boxstyle='round,pad=0.15', facecolor='#313332', 
                            edgecolor='none', alpha=0.9))
    
    # Plot player data
    def get_percentile_position(value, percentiles):
        """Convert value to radar position based on percentiles"""
        # Handle edge cases
        if value <= percentiles[0]:
            return ring_positions[0]
        if value >= percentiles[-1]:
            return ring_positions[-1]
            
        # Find which percentile range the value falls into
        for i in range(len(percentiles) - 1):
            if percentiles[i] <= value <= percentiles[i + 1]:
                # Interpolate between ring positions
                fraction = (value - percentiles[i]) / (percentiles[i + 1] - percentiles[i])
                return ring_positions[i] + fraction * (ring_positions[i + 1] - ring_positions[i])
        
        return ring_positions[-1]
    
    # Player 1 data
    player_1_positions = []
    for metric, percentiles in zip(metrics, percentile_values_all):
        val = player_1_data[metric]
        pos = get_percentile_position(val, percentiles)
        player_1_positions.append(pos)
    player_1_positions += player_1_positions[:1]
    
    # Plot player 1 - if single player, use alternating pattern
    if player_2_data is None:
        # Create alternating pattern using both team colors
        ax.plot(angles, player_1_positions, color=colors[0], linewidth=3)
        
        # Fill with alternating colors
        for i in range(len(angles) - 1):
            angle_slice = [angles[i], angles[i + 1]]
            values_slice = [player_1_positions[i], player_1_positions[i + 1]]
            color_idx = i % 2  # Alternate between 0 and 1
            ax.fill(angle_slice + [0, 0], values_slice + [0, 0], 
                   color=colors[color_idx], alpha=0.4, edgecolor=colors[0], linewidth=1)
    else:
        # Two players - normal solid fills
        ax.plot(angles, player_1_positions, color=colors[0], linewidth=2.5)
        ax.fill(angles, player_1_positions, color=colors[0], alpha=0.3)
    
    # Player 2 data if exists
    if player_2_data is not None:
        player_2_positions = []
        for metric, percentiles in zip(metrics, percentile_values_all):
            val = player_2_data[metric]
            pos = get_percentile_position(val, percentiles)
            player_2_positions.append(pos)
        player_2_positions += player_2_positions[:1]
        
        ax.plot(angles, player_2_positions, color=colors[1], linewidth=2.5)
        ax.fill(angles, player_2_positions, color=colors[1], alpha=0.3)
    
    # Add metric labels - BACK TO ORIGINAL METHOD BUT CLOSER
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_titles, size=10, weight='bold', color='white')
    
    # TRICK: Set label position much closer using pad
    ax.tick_params(axis='x', pad=1)  # Negative pad brings labels closer
    
    # Clean up radar appearance
    ax.set_ylim(0, 0.95)  # Slightly increase to give more room for labels
    ax.set_yticks([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    
    # EXACT SWARM LAYOUT - Player info and logos
    # Player 1
    if team_logos and player_1_data['team'] in team_logos:
        try:
            logo_1 = Image.open(team_logos[player_1_data['team']])
            logo_ax_1 = fig.add_axes([0.05, 0.945, 0.04, 0.04])
            logo_ax_1.imshow(logo_1)
            logo_ax_1.axis('off')
        except:
            pass
    
    fig.text(0.11, 0.963, player_1_data['player_name'], fontweight="bold", fontsize=14, color=colors[0])
    fig.text(0.11, 0.941, player_1_data['team'], fontweight="bold", fontsize=12, color='w')
    fig.text(0.11, 0.919, f"{player_1_data['league']} {player_1_data['season']}", fontweight="bold", fontsize=12, color='w')
    minutes = int(player_1_data.get('minutes_played', 0))
    matches = int(player_1_data.get('matches_played', 0))
    fig.text(0.11, 0.897, f"{minutes} mins | {matches} matches", fontsize=10, color='w', alpha=0.8)
    
    # Player 2
    if player_2_data is not None:
        if team_logos and player_2_data['team'] in team_logos:
            try:
                logo_2 = Image.open(team_logos[player_2_data['team']])
                logo_ax_2 = fig.add_axes([0.42, 0.945, 0.04, 0.04])
                logo_ax_2.imshow(logo_2)
                logo_ax_2.axis('off')
            except:
                pass
                
        fig.text(0.48, 0.963, player_2_data['player_name'], fontweight="bold", fontsize=14, color=colors[1])
        fig.text(0.48, 0.941, player_2_data['team'], fontweight="bold", fontsize=12, color='w')
        fig.text(0.48, 0.919, f"{player_2_data['league']} {player_2_data['season']}", fontweight="bold", fontsize=12, color='w')
        minutes2 = int(player_2_data.get('minutes_played', 0))
        matches2 = int(player_2_data.get('matches_played', 0))
        fig.text(0.48, 0.897, f"{minutes2} mins | {matches2} matches", fontsize=10, color='w', alpha=0.8)
    
    # Title and description - exact swarm position
    title_x = 0.835
    fig.text(title_x, 0.963, radar_title, fontweight="bold", fontsize=12, color='w', ha='left')
    
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(radar_description, 40))
    fig.text(title_x, 0.945, wrapped_desc, fontweight="regular", fontsize=8, color='w', ha='left', va='top')
    
    # Footer - exact swarm position
    fig.text(0.5, 0.05, "Created by Jaime Oriol", 
             fontstyle="italic", ha="center", fontsize=9, color="white")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    if show_plot:
        plt.show()
    else:
        plt.close()