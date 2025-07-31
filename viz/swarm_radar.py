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
warnings.filterwarnings('ignore')

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
                       show_plot=True):
    """
    Create a swarm radar visualization for player comparison
    
    Parameters:
    -----------
    df_data : pd.DataFrame
        DataFrame with player data including metrics and percentiles
    player_1_id : str
        unique_player_id for the primary player
    metrics : list
        List of 10 metric column names to display
    metric_titles : list
        List of 10 display titles for the metrics
    player_2_id : str, optional
        unique_player_id for the comparison player
    player_1_color : str
        Color for player 1 (default: 'lightskyblue')
    player_2_color : str
        Color for player 2 (default: 'coral')
    radar_title : str
        Title for the radar chart
    radar_description : str
        Description text for the radar
    negative_metrics : list, optional
        List of metrics where lower is better
    save_path : str
        Path to save the figure
    """
    
    if negative_metrics is None:
        negative_metrics = []
    
    # Validate inputs
    if len(metrics) != 10 or len(metric_titles) != 10:
        raise ValueError("Must provide exactly 10 metrics and 10 titles")
    
    # Get player data
    player_1_data = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    player_2_data = None
    if player_2_id:
        player_2_data = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    # Setup comparison data based on percentile columns
    percentile_metrics = [m + '_pct' if not m.endswith('_pct') else m for m in metrics]
    comparison_df = df_data[['unique_player_id'] + percentile_metrics].copy()
    
    # Tag primary players
    comparison_df['Primary Player'] = 'Untagged'
    comparison_df.loc[comparison_df['unique_player_id'] == player_1_id, 'Primary Player'] = 'Primary 1'
    if player_2_id:
        comparison_df.loc[comparison_df['unique_player_id'] == player_2_id, 'Primary Player'] = 'Primary 2'
    
    # Sort to highlight tagged players
    comparison_df = comparison_df.sort_values('Primary Player')
    
    # Path effects
    path_eff = [path_effects.Stroke(linewidth=2, foreground='#313332'), path_effects.Normal()]
    
    # Number of metrics (always 10)
    num_metrics = 10
    
    # Define positions for mini plots
    theta_mid = np.radians(np.linspace(0, 360, num_metrics+1))[:-1] + np.pi/2
    theta_mid = [x if x < 2*np.pi else x - 2*np.pi for x in theta_mid]
    r_base = np.linspace(0.25, 0.25, num_metrics+1)[:-1]
    x_base, y_base = 0.325 + r_base * np.cos(theta_mid), 0.3 + 0.89 * r_base * np.sin(theta_mid)
    
    # Create figure
    fig = plt.figure(constrained_layout=False, figsize=(9, 11))
    fig.set_facecolor('#313332')
    
    # Setup radar background
    theta = np.arange(0, 2*np.pi, 0.01)
    radar_ax = fig.add_axes([0.025, 0, 0.95, 0.95], polar=True)
    radar_ax.plot(theta, theta*0 + 0.17, color='w', lw=1)
    radar_ax.plot(theta, theta*0 + 0.3425, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.5150, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.6875, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.86, color='grey', lw=1, alpha=0.3)
    radar_ax.axis('off')
    
    # Store axis limits
    ax_mins = []
    ax_maxs = []
    
    # Create mini swarm plots
    for idx, (metric, pct_metric) in enumerate(zip(metrics, percentile_metrics)):
        # Create mini figure
        fig_save, ax_save = plt.subplots(figsize=(4.5, 1.5))
        fig_save.set_facecolor('#313332')
        fig_save.patch.set_alpha(0)
        
        # Plot swarm
        sns.swarmplot(x=comparison_df[pct_metric], 
                     y=[""]*len(comparison_df), 
                     color='grey', 
                     edgecolor='w', 
                     size=4, 
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
        ax_maxs.append(ax_save.get_xlim()[1]*1.05)
        
        # Save temp image
        temp_path = f'temp_{idx}.png'
        fig_save.savefig(temp_path, dpi=300)
        
        # Add to main figure
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
        
        # Add metric title
        if theta_mid[idx] >= np.pi:
            text_rotation_delta = 90
        else:
            text_rotation_delta = -90
        
        radar_ax.text(theta_mid[idx], 0.92, metric_titles[idx], 
                     ha="center", va="center", fontweight="bold", 
                     fontsize=10, color='w',
                     rotation=text_rotation_delta + (180/np.pi) * theta_mid[idx])
        
        plt.close(fig_save)
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    radar_ax.set_rmax(1)
    
    # Add player 1 info
    fig.text(0.11, 0.953, player_1_data['player_name'], fontweight="bold", fontsize=14, color=player_1_color)
    fig.text(0.11, 0.931, player_1_data['team'], fontweight="bold", fontsize=12, color='w')
    fig.text(0.11, 0.909, f"{player_1_data['league']} {player_1_data['season']}", fontweight="bold", fontsize=12, color='w')
    # Add minutes and matches info
    minutes = int(player_1_data.get('minutes_played', 0))
    matches = int(player_1_data.get('matches_played', 0))
    fig.text(0.11, 0.887, f"{minutes} mins | {matches} matches", fontsize=10, color='w', alpha=0.8)
    
    # Add player 2 info if exists
    if player_2_data is not None:
        fig.text(0.48, 0.953, player_2_data['player_name'], fontweight="bold", fontsize=14, color=player_2_color)
        fig.text(0.48, 0.931, player_2_data['team'], fontweight="bold", fontsize=12, color='w')
        fig.text(0.48, 0.909, f"{player_2_data['league']} {player_2_data['season']}", fontweight="bold", fontsize=12, color='w')
        minutes2 = int(player_2_data.get('minutes_played', 0))
        matches2 = int(player_2_data.get('matches_played', 0))
        fig.text(0.48, 0.887, f"{minutes2} mins | {matches2} matches", fontsize=10, color='w', alpha=0.8)
    
    # Add PyPizza radar
    pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82], polar=True)
    pizza_ax.set_theta_offset(17)
    pizza_ax.axis('off')
    
    # Reorder metrics for pizza
    pizza_metrics = [percentile_metrics[0]] + list(reversed(percentile_metrics[1:]))
    ax_mins = [ax_mins[0]] + list(reversed(ax_mins[1:]))
    ax_maxs = [ax_maxs[0]] + list(reversed(ax_maxs[1:]))
    
    # Get values for radar
    radar_values_p1 = [player_1_data[m] for m in pizza_metrics]
    radar_values_p2 = [player_2_data[m] for m in pizza_metrics] if player_2_data is not None else None
    
    # Create radar object
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
    
    # Plot radar
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
    
    # Add title and description
    fig.text(0.975, 0.953, radar_title, fontweight="bold", fontsize=12, color='w', ha='right')
    # Wrap description if too long
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(radar_description, 40))
    fig.text(0.975, 0.942, wrapped_desc, fontweight="regular", fontsize=8, color='w', ha='right', va='top')
    
    # Add footer
    fig.text(0.5, 0.02, "Created by Jaime Oriol", 
             fontstyle="italic", ha="center", fontsize=9, color="white")
    
    # Save figure
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    # Clean up any remaining temp files
    for i in range(10):
        temp_file = f'temp_{i}.png'
        if os.path.exists(temp_file):
            os.remove(temp_file)