# viz/swarm_radar.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.transforms import Affine2D
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axes_grid1 import Divider
import mpl_toolkits.axes_grid1.axes_size as Size
from mplsoccer import PyPizza
from PIL import Image
import seaborn as sns
import textwrap as tw
import json
import os
from scipy import stats

def create_swarm_radar(df, player_ids, metrics_config, comparison_text, 
                      min_minutes=800, colors=['lightskyblue', 'coral'],
                      save_path=None):
    """
    Genera swarm radar adaptativo para métricas footballdecoded
    
    Args:
        df: DataFrame con estructura footballdecoded
        player_ids: Lista de 1-2 unique_player_ids
        metrics_config: Dict con 'metrics', 'titles', 'negative_metrics'
        comparison_text: Texto descriptivo
        min_minutes: Filtro minutos para percentiles
        colors: Colores jugadores
        save_path: Ruta guardar imagen
    """
    
    df_expanded = _extract_metrics_to_columns(df, metrics_config['metrics'])
    df_expanded = _calculate_per90_metrics(df_expanded, metrics_config['metrics'])
    
    df_percentiles = df_expanded[_get_minutes_played(df_expanded) >= min_minutes].copy()
    
    for metric in metrics_config['metrics']:
        df_expanded[f'{metric}_percentile'] = _calculate_percentile(
            df_expanded[metric], df_percentiles[metric]
        )
    
    fig = _generate_radar_visualization(
        df_expanded, player_ids, metrics_config, comparison_text, colors
    )
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    
    return fig

def _extract_metrics_to_columns(df, metrics):
    """Extrae métricas de JSON a columnas"""
    df_expanded = df.copy()
    
    for metric in metrics:
        df_expanded[metric] = None
        
        for idx, row in df.iterrows():
            fbref_metrics = row['fbref_metrics'] if row['fbref_metrics'] else {}
            understat_metrics = row['understat_metrics'] if row['understat_metrics'] else {}
            
            if metric in fbref_metrics:
                df_expanded.loc[idx, metric] = fbref_metrics[metric]
            elif metric in understat_metrics:
                df_expanded.loc[idx, metric] = understat_metrics[metric]
        
        df_expanded[metric] = pd.to_numeric(df_expanded[metric], errors='coerce')
    
    return df_expanded

def _calculate_per90_metrics(df, metrics):
    """Calcula métricas por 90 minutos"""
    minutes_col = _get_minutes_played(df)
    
    per90_metrics = ['goals', 'assists', 'shots', 'expected_goals', 'tackles', 
                    'interceptions', 'passes_completed', 'yellow_cards']
    
    for metric in metrics:
        if any(per90_metric in metric for per90_metric in per90_metrics):
            if not metric.endswith('_90') and not metric.endswith('_per_90'):
                df[f'{metric}_per90'] = (df[metric] / minutes_col * 90).round(2)
    
    return df

def _get_minutes_played(df):
    """Obtiene columna de minutos jugados"""
    if 'minutes_played' in df.columns:
        return df['minutes_played']
    elif 'fbref_metrics' in df.columns:
        minutes = []
        for _, row in df.iterrows():
            fbref = row['fbref_metrics'] if row['fbref_metrics'] else {}
            minutes.append(fbref.get('minutes_played', 0))
        return pd.Series(minutes)
    else:
        return pd.Series([0] * len(df))

def _calculate_percentile(player_values, reference_values):
    """Calcula percentiles de jugador vs referencia"""
    percentiles = []
    ref_clean = reference_values.dropna()
    
    for value in player_values:
        if pd.isna(value):
            percentiles.append(0)
        else:
            percentile = stats.percentileofscore(ref_clean, value)
            percentiles.append(percentile)
    
    return pd.Series(percentiles)

def _generate_radar_visualization(df, player_ids, metrics_config, comparison_text, colors):
    """Genera visualización completa"""
    
    df['primary_player'] = 'Other'
    df['plot_size'] = 7
    
    for i, player_id in enumerate(player_ids):
        mask = df['unique_player_id'] == player_id
        df.loc[mask, 'primary_player'] = f'Player_{i+1}'
        df.loc[mask, 'plot_size'] = 9
    
    df = df.sort_values('primary_player')
    
    num_metrics = len(metrics_config['metrics'])
    
    theta_mid = np.radians(np.linspace(0, 360, num_metrics+1))[:-1] + np.pi/2
    theta_mid = [x if x < 2*np.pi else x - 2*np.pi for x in theta_mid]
    
    r_base = np.linspace(0.25, 0.25, num_metrics+1)[:-1]
    x_base = 0.325 + r_base * np.cos(theta_mid)
    y_base = 0.3 + 0.89 * r_base * np.sin(theta_mid)
    
    fig = plt.figure(constrained_layout=False, figsize=(9, 11))
    fig.set_facecolor('#313332')
    
    radar_ax = fig.add_axes([0.025, 0, 0.95, 0.95], polar=True)
    theta = np.arange(0, 2*np.pi, 0.01)
    radar_ax.plot(theta, theta*0 + 0.17, color='w', lw=1)
    radar_ax.plot(theta, theta*0 + 0.3425, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.5150, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.6875, color='grey', lw=1, alpha=0.3)
    radar_ax.plot(theta, theta*0 + 0.86, color='grey', lw=1, alpha=0.3)
    radar_ax.axis('off')
    
    ax_mins, ax_maxs = [], []
    path_eff = [path_effects.Stroke(linewidth=2, foreground='#313332'), path_effects.Normal()]
    
    for idx, metric in enumerate(metrics_config['metrics']):
        
        fig_save, ax_save = plt.subplots(figsize=(4.5, 1.5))
        fig_save.set_facecolor('#313332')
        fig_save.patch.set_alpha(0)
        
        # Colores por jugador
        colors_list = []
        for _, row in df.iterrows():
            if row['primary_player'] == 'Player_1':
                colors_list.append(colors[0])
            elif row['primary_player'] == 'Player_2' and len(player_ids) > 1:
                colors_list.append(colors[1])
            else:
                colors_list.append('grey')
        
        sns.scatterplot(x=df[metric], y=[""]*len(df), 
                       c=colors_list, s=df['plot_size']*10, 
                       edgecolor='w', linewidth=0.5, alpha=0.8)
        
        # Percentiles de jugadores principales
        for i, player_id in enumerate(player_ids):
            player_data = df[df['unique_player_id'] == player_id]
            if not player_data.empty:
                percentile = player_data[f'{metric}_percentile'].iloc[0]
                value = player_data[metric].iloc[0]
                ax_save.axvline(value, color=colors[i], alpha=0.7, linestyle='--', linewidth=2)
                ax_save.text(value, 0.1, f'{percentile:.0f}%', 
                           ha='center', va='bottom', color=colors[i], 
                           fontweight='bold', fontsize=8)
        
        ax_save.patch.set_alpha(0)
        ax_save.set_ylim(-0.5, 0.5)
        ax_save.spines['bottom'].set_position(('axes', 0.5))
        ax_save.spines['bottom'].set_color('w')
        ax_save.spines['top'].set_visible(False)
        ax_save.spines['right'].set_color('w')
        ax_save.spines['left'].set_visible(False)
        ax_save.set_xlabel("")
        ax_save.set_ylabel("")
        ax_save.tick_params(left=False, bottom=True, colors='w', labelsize=8)
        
        if theta_mid[idx] < np.pi/2 or theta_mid[idx] > 3*np.pi/2:
            plt.setp(ax_save.get_xticklabels(), path_effects=path_eff, fontweight='bold')
        else:
            plt.setp(ax_save.get_xticklabels(), path_effects=path_eff, fontweight='bold', rotation=180)
        
        if metric in metrics_config.get('negative_metrics', []):
            ax_save.invert_xaxis()
        
        ax_mins.append(ax_save.get_xlim()[0])
        ax_maxs.append(ax_save.get_xlim()[1] * 1.05)
        
        fig_save.savefig('temp_swarm.png', dpi=300, bbox_inches='tight', facecolor='#313332')
        
        # Posicionar en radar
        scales = (0, 1, 0, 1)
        t = Affine2D().scale(3, 1).rotate_deg(theta_mid[idx] * (180/np.pi))
        h = floating_axes.GridHelperCurveLinear(t, scales)
        ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=h)
        ax = fig.add_subplot(ax)
        aux_ax = ax.get_aux_axes(t)
        
        horiz_scale = [Size.Scaled(1.04)]
        vert_scale = [Size.Scaled(1.0)]
        ax_div = Divider(fig, [x_base[idx], y_base[idx], 0.35, 0.35], horiz_scale, vert_scale, aspect=True)
        ax_loc = ax_div.new_locator(nx=0, ny=0)
        ax.set_axes_locator(ax_loc)
        
        img = Image.open('temp_swarm.png')
        aux_ax.imshow(img, extent=[-0.18, 1.12, -0.15, 1.15])
        ax.axis('off')
        
        # Título métrica
        text_rotation = 90 if theta_mid[idx] >= np.pi else -90
        radar_ax.text(theta_mid[idx], 0.92, metrics_config['titles'][idx], 
                     ha="center", va="center", fontweight="bold", 
                     fontsize=10, color='w',
                     rotation=text_rotation + (180/np.pi) * theta_mid[idx])
        
        plt.close(fig_save)
    
    # Info jugadores
    for i, player_id in enumerate(player_ids):
        player_data = df[df['unique_player_id'] == player_id]
        if not player_data.empty:
            row = player_data.iloc[0]
            
            # Logo equipo (si existe)
            logo_path = f'viz/logos/{row["team"]}.png'
            if os.path.exists(logo_path):
                logo_ax = fig.add_axes([0.015 + i*0.37, 0.897, 0.09, 0.09])
                logo_ax.axis("off")
                logo_ax.imshow(Image.open(logo_path))
            
            # Textos
            x_pos = 0.11 + i*0.37
            fig.text(x_pos, 0.953, row['player_name'], fontweight="bold", 
                    fontsize=14, color=colors[i])
            fig.text(x_pos, 0.931, row['team'], fontweight="bold", 
                    fontsize=12, color='w')
            fig.text(x_pos, 0.909, f"{row['league']} {row['season']}", 
                    fontweight="bold", fontsize=12, color='w')
    
    # Pizza radar central
    _add_pizza_radar(fig, df, player_ids, metrics_config, ax_mins, ax_maxs, colors)
    
    # Texto descriptivo
    fig.text(0.975, 0.953, "Player Comparison", fontweight="bold", 
            fontsize=12, color='w', ha='right')
    description_text = "\n".join(tw.wrap(comparison_text, 30, break_long_words=False))
    fig.text(0.975, 0.942, description_text, fontweight="regular", 
            fontsize=8, color='w', ha='right', va='top')
    
    # Footer
    fig.text(0.5, 0.02, "Created with FootballDecoded", 
            fontstyle="italic", ha="center", fontsize=9, color="white")
    
    # Limpiar archivos temporales
    if os.path.exists('temp_swarm.png'):
        os.remove('temp_swarm.png')
    
    radar_ax.set_rmax(1)
    return fig

def _add_pizza_radar(fig, df, player_ids, metrics_config, ax_mins, ax_maxs, colors):
    """Añade radar pizza central"""
    
    pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82], polar=True)
    pizza_ax.set_theta_offset(17)
    pizza_ax.axis('off')
    
    pizza_metrics = [metrics_config['metrics'][0]] + list(reversed(metrics_config['metrics'][1:]))
    pizza_mins = [ax_mins[0]] + list(reversed(ax_mins[1:]))
    pizza_maxs = [ax_maxs[0]] + list(reversed(ax_maxs[1:]))
    
    radar_object = PyPizza(params=pizza_metrics,
                          background_color="w",
                          straight_line_color="w",
                          min_range=pizza_mins,
                          max_range=pizza_maxs,
                          straight_line_lw=1,
                          straight_line_limit=100,
                          last_circle_lw=0.1,
                          other_circle_lw=0.1,
                          inner_circle_size=18)
    
    # Valores jugadores
    player_values = []
    for player_id in player_ids:
        player_data = df[df['unique_player_id'] == player_id]
        if not player_data.empty:
            values = player_data[pizza_metrics].values[0].tolist()
            player_values.append(values)
    
    if len(player_values) == 1:
        radar_object.make_pizza(values=player_values[0],
                               color_blank_space='same',
                               blank_alpha=0,
                               kwargs_slices=dict(facecolor=colors[0], alpha=0.3, 
                                                 edgecolor='#313332', linewidth=1),
                               ax=pizza_ax)
    elif len(player_values) == 2:
        radar_object.make_pizza(values=player_values[0],
                               compare_values=player_values[1],
                               color_blank_space='same',
                               blank_alpha=0,
                               kwargs_slices=dict(facecolor=colors[0], alpha=0.3, 
                                                 edgecolor='#313332', linewidth=1),
                               kwargs_compare=dict(facecolor=colors[1], alpha=0.3, 
                                                  edgecolor='#313332', linewidth=1),
                               ax=pizza_ax)