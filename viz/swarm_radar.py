"""
FootballDecoded Swarm Radar Visualization Module
================================================

Advanced radar chart system with integrated distribution context (swarm plots).
Creates sophisticated player comparison visualizations combining radar charts
with statistical distribution context.

Key Features:
- Dual visualization modes: Swarm Radar (with distribution context) and Traditional Radar
- 10-metric radar system with dynamic metric reordering for visual balance
- Integrated swarm plots showing metric distribution across dataset
- Advanced color alternation system for single-player analysis
- Comprehensive statistical context with percentile positioning
- Professional sports analytics aesthetics with FootballDecoded branding

Swarm Radar System:
- Distribution Context: Swarm plots show where each metric value sits within dataset
- Radar Integration: Individual floating axes for each metric with custom positioning
- Color Psychology: Alternating ring colors for single-player depth analysis
- Mathematical Precision: Polar coordinate system with precise angular positioning

Traditional Radar System:
- Clean geometric design with percentile-based scaling
- Ring-based alternating colors for single-player analysis  
- Solid color comparison for dual-player mode
- Professional concentric circle grid system

Technical Implementation:
- PyPizza integration for professional radar visualization
- Floating axes system for swarm plot integration
- Affine transformations for precise metric positioning
- Advanced color management with mathematical alternation patterns
- Temporary file management for component integration

Visual Design:
- Unified FootballDecoded design language
- Professional sports broadcast aesthetics
- Mathematical precision in layout and positioning
- Brand consistency with logo and typography integration

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
Specialization: Advanced radar charts with statistical context
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

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'  # Professional dark theme across all modules

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
                       save_path='player_radar.png',
                       show_plot=True,
                       use_swarm=True,
                       team_logos=None):
    """
    Create advanced radar chart visualization with optional distribution context.
    
    Generates sophisticated radar charts with two distinct modes:
    1. Swarm Radar: Integrates distribution context via swarm plots around radar
    2. Traditional Radar: Clean geometric radar with advanced color systems
    
    Features:
    - 10-metric radar system with mathematical precision
    - Dynamic metric reordering for visual balance
    - Single vs dual-player comparison modes
    - Advanced color alternation for single-player depth
    - Professional statistical visualization standards
    - Integrated FootballDecoded branding system
    
    Args:
        df_data: DataFrame with player statistics and dataset context
        player_1_id: Primary player unique identifier
        metrics: List of 10 statistical metric column names
        metric_titles: List of 10 display titles for metrics
        player_2_id: Optional secondary player for comparison
        player_1_color: Primary player color (overridden by team_colors)
        player_2_color: Secondary player color (overridden by team_colors)
        team_colors: Optional team-based color scheme [primary, secondary] per player
        radar_title: Visualization title (unused but kept for compatibility)
        radar_description: Description text (unused but kept for compatibility)
        negative_metrics: Legacy parameter (unused but kept for compatibility)
        save_path: Output file path for saved visualization
        show_plot: Whether to display the plot
        use_swarm: True for Swarm Radar, False for Traditional Radar
        team_logos: Team logo integration (unused but kept for compatibility)
        
    Returns:
        None (saves visualization to specified path)
        
    Raises:
        ValueError: If metrics count != 10 or metric_titles count != 10
        
    Note:
        Requires exactly 10 metrics for proper radar geometry
        Swarm mode requires seaborn for distribution visualization
        Uses temporary files for component integration in swarm mode
    """
    
    # Legacy parameter maintained for backward compatibility
    if negative_metrics is None:
        negative_metrics = []
    
    # Validate radar geometry requirements
    if len(metrics) != 10 or len(metric_titles) != 10:
        raise ValueError("Must provide exactly 10 metrics and 10 titles")
    
    # Unified color system with team_colors taking priority
    if team_colors is None:
        colors = [player_1_color, player_2_color]  # Fallback to individual colors
    else:
        colors = team_colors  # Use team-based color scheme
    
    # Extract player data from dataset
    player_1_data = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    player_2_data = None
    if player_2_id:
        player_2_data = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    # Route to appropriate visualization mode
    if use_swarm:
        _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                           colors, save_path, show_plot)
    else:
        _create_traditional_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                                 colors, save_path, show_plot)

def _create_swarm_radar(df_data, player_1_data, player_2_data, metrics, metric_titles,
                       colors, save_path, show_plot):
    """
    Create advanced swarm radar with integrated distribution context.
    
    Combines traditional radar visualization with swarm plots showing
    statistical distribution context for each metric. Uses sophisticated
    floating axes system for precise positioning.
    
    Technical Implementation:
    - Individual swarm plots for each metric positioned around radar
    - Floating axes with affine transformations for precise positioning
    - Dynamic metric reordering (first metric + reversed remainder)
    - Integrated PyPizza radar with swarm distribution context
    - Temporary file management for component integration
    
    Args:
        df_data: Complete dataset for distribution context
        player_1_data: Primary player statistics
        player_2_data: Optional secondary player statistics
        metrics: List of metric column names
        metric_titles: List of display titles
        colors: Color scheme for players
        save_path: Output file path
        show_plot: Display flag
    """
    
    comparison_df = df_data[['unique_player_id'] + metrics].copy()
    
    comparison_df['Primary Player'] = 'Untagged'
    comparison_df.loc[comparison_df['unique_player_id'] == player_1_data['unique_player_id'], 'Primary Player'] = 'Primary 1'
    if player_2_data is not None:
        comparison_df.loc[comparison_df['unique_player_id'] == player_2_data['unique_player_id'], 'Primary Player'] = 'Primary 2'
    
    comparison_df = comparison_df.sort_values('Primary Player')
    
    path_eff = [path_effects.Stroke(linewidth=2, foreground=BACKGROUND_COLOR), path_effects.Normal()]
    
    theta_mid = np.radians(np.linspace(0, 360, 10+1))[:-1] + np.pi/2
    theta_mid = [x if x < 2*np.pi else x - 2*np.pi for x in theta_mid]
    
    r_base = [0.231 if (angle > np.pi/4 and angle < 3*np.pi/4) or (angle > 5*np.pi/4 and angle < 7*np.pi/4) 
              else 0.25 for angle in theta_mid]
    
    x_base, y_base = 0.325 + np.array(r_base) * np.cos(theta_mid), 0.3 + 0.89 * np.array(r_base) * np.sin(theta_mid)
    
    # MANTENER LA ALTURA ORIGINAL para que esté alineado con la tabla
    fig = plt.figure(constrained_layout=False, figsize=(9, 11), facecolor=BACKGROUND_COLOR)
    
    theta = np.linspace(0, 2*np.pi, 100)
    # RADAR BASE: Central polar axis for background circles and radial lines
    # Position maintained for alignment with swarm distribution plots
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
                           labelsize=8, zorder=10, pad=0, colors='w')  # Reducido de 9 a 8
        
        rotation = 180 if theta_mid[idx] >= np.pi/2 and theta_mid[idx] <= 3*np.pi/2 else 0
        plt.xticks(path_effects=path_eff, fontweight='bold', rotation=rotation, family='DejaVu Sans')  # Añadido family='DejaVu Sans'
        
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
                     fontsize=10, color='w', family='DejaVu Sans',  # Añadido family='DejaVu Sans'
                     rotation=text_rotation_delta + (180/np.pi) * theta_mid[idx])
        
        plt.close(fig_save)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    radar_ax.set_rmax(1)
    
    # PIZZA RADAR: PyPizza integration axis for statistical radar overlay
    # Positioned to align with swarm plots and maintain visual balance
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
    
    # UNIFIED FOOTER: Consistent FootballDecoded branding hierarchy
    fig.text(0.1, 0.115, "Created by Jaime Oriol", ha="center", fontsize=10, color="white", 
             weight='bold', family='DejaVu Sans')  # Creator attribution position
    
    # Logo Football Decoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.82, 0.10, 0.2, 0.08])  # [x, y, width, height]
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        fig.text(0.87, 0.115, "Football Decoded", ha="center", fontsize=14, color="white", 
                 weight='bold', family='DejaVu Sans')  # Primary brand position
    
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
                             colors, save_path, show_plot):
    """
    Create traditional geometric radar chart with advanced color systems.
    
    Generates clean geometric radar visualization with sophisticated
    color management for single vs dual-player scenarios.
    
    Single Player Mode:
    - Ring-based alternating color pattern for visual depth
    - Mathematical color alternation starting with secondary color
    - Comprehensive value labeling on concentric circles
    
    Dual Player Mode:
    - Solid color overlay system for clear comparison
    - Clean geometric polygons with team-based colors
    - Professional sports analytics presentation
    
    Technical Implementation:
    - Percentile-based range calculation (1st-99th percentile)
    - 8 concentric circles with mathematical spacing
    - Precise angular positioning for 10-metric system
    - Advanced polygon clipping for ring-based coloring
    
    Args:
        df_data: Complete dataset for range calculation
        player_1_data: Primary player statistics
        player_2_data: Optional secondary player statistics
        metrics: List of metric column names
        metric_titles: List of display titles
        colors: Color scheme for players
        save_path: Output file path
        show_plot: Display flag
    """
    
    # Usar la misma lógica de ordenamiento que el swarm radar
    reordered_metrics = [metrics[0]] + list(reversed(metrics[1:]))
    reordered_titles = [metric_titles[0]] + list(reversed(metric_titles[1:]))
    
    # Calcular percentiles para ranges
    ranges = []
    for metric in reordered_metrics:
        metric_data = df_data[metric].dropna()
        min_val = np.percentile(metric_data, 1)
        max_val = np.percentile(metric_data, 99)
        ranges.append((min_val, max_val))
    
    # Configuración visual - más pequeño
    fig, ax = plt.subplots(figsize=(9, 10), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_aspect('equal')
    ax.set(xlim=(-22, 22), ylim=(-23, 25))  # Más pequeño
    
    # Valores del jugador
    player_1_values = [player_1_data[m] for m in reordered_metrics]
    player_2_values = [player_2_data[m] for m in reordered_metrics] if player_2_data is not None else None
    
    # 8 círculos concéntricos (más pequeños)
    radius_circles = [3, 5.5, 8, 10.5, 13, 15.5, 18, 20.5]
    for i, rad in enumerate(radius_circles):
        if i == 0:  # Círculo interior
            continue
        elif i == len(radius_circles)-1:  # Círculo exterior
            color, lw, alpha = 'white', 1.2, 1.0
        else:  # Círculos intermedios
            color, lw, alpha = 'grey', 1, 0.4
            
        circle = plt.Circle(xy=(0, 0), radius=rad, fc='none', ec=color, lw=lw, alpha=alpha)
        ax.add_patch(circle)
    
    # Coordenadas para labels
    n_params = len(reordered_metrics)
    angles = np.linspace(0, 2*np.pi, n_params, endpoint=False)
    
    # Labels de métricas (más cerca)
    label_radius = 21.5
    for i, (angle, title) in enumerate(zip(angles, reordered_titles)):
        x = label_radius * np.sin(angle)
        y = label_radius * np.cos(angle)
        
        # Rotación del texto
        rot_deg = -np.rad2deg(angle)
        if y < 0:
            rot_deg += 180
            
        ax.text(x, y, title, rotation=rot_deg, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white', family='DejaVu Sans')  # Añadido family='DejaVu Sans'
    
    # Líneas radiales (más cortas)
    for angle in angles:
        x_end = 20.5 * np.sin(angle)
        y_end = 20.5 * np.cos(angle)
        ax.plot([0, x_end], [0, y_end], color='grey', linewidth=0.5, alpha=0.4)
    
    # 7 valores en círculos - CORREGIDO PARA USAR MISMOS RANGES QUE EL POLÍGONO
    range_radius = [4.25, 6.75, 9.25, 11.75, 14.25, 16.75, 19.25]
    
    for rad_idx, rad in enumerate(range_radius):
        for i, (angle, metric) in enumerate(zip(angles, reordered_metrics)):
            min_val, max_val = ranges[i]
            
            # Calcular valor usando divisiones lineales del rango del polígono
            range_total = max_val - min_val
            if range_total == 0:
                val = min_val
            else:
                # Convertir radio a posición en el rango [0, 1]
                rad_normalized = (rad - 3) / (20.5 - 3)  # 3 es radio mínimo, 20.5 máximo
                val = min_val + rad_normalized * range_total
            
            x = rad * np.sin(angle)
            y = rad * np.cos(angle)
            
            # Formatear valor
            if val < 0.01:
                label = f'{val:.3f}'
            elif val < 1:
                label = f'{val:.2f}'
            elif val < 10:
                label = f'{val:.1f}'
            else:
                label = f'{int(val)}'
            
            ax.text(x, y, label, ha='center', va='center', size=7, color='white',  # Reducido de 8 a 7
                   bbox=dict(boxstyle='round,pad=0.15', facecolor=BACKGROUND_COLOR, 
                           edgecolor='none', alpha=0.9), family='DejaVu Sans')  # Añadido family='DejaVu Sans'
    
    # Función para convertir valor a coordenada (rango más pequeño)
    def get_radar_coordinates(values, ranges):
        vertices = []
        for i, (value, (min_val, max_val)) in enumerate(zip(values, ranges)):
            # Normalizar valor al rango 3-20.5
            if max_val == min_val:
                norm_value = 11.75  # Punto medio
            else:
                norm_value = 3 + (value - min_val) / (max_val - min_val) * 17.5
            
            # Limitar al rango de círculos
            norm_value = max(3, min(20.5, norm_value))
            
            angle = angles[i]
            x = norm_value * np.sin(angle)
            y = norm_value * np.cos(angle)
            vertices.append([x, y])
        
        return vertices
    
    # Polígono jugador 1
    vertices_1 = get_radar_coordinates(player_1_values, ranges)
    
    if player_2_data is None:
        # Solo un jugador - alternar colores por ANILLOS dentro del polígono
        # EMPEZAR CON colors[1] en el centro
        
        # Primero crear el polígono base del jugador
        polygon_1 = Polygon(vertices_1, fc='none', alpha=1.0, zorder=1)
        ax.add_patch(polygon_1)
        
        # RELLENAR EL CÍRCULO CENTRAL
        central_circle = plt.Circle(xy=(0, 0), radius=radius_circles[0], 
                                fc=colors[0], ec='none', alpha=0.45, zorder=2)
        central_circle.set_clip_path(polygon_1)
        ax.add_patch(central_circle)
        
        # Crear anillos alternados SOLO dentro del polígono del jugador
        theta = np.linspace(0, 2*np.pi, 100)
        
        for i in range(len(radius_circles)-1):
            inner_radius = radius_circles[i]
            outer_radius = radius_circles[i+1]
            
            # Alternar colores por anillo - EMPEZAR CON colors[1]
            color_idx = (i + 1) % 2  # Cambiado para empezar con colors[1]
            
            # Crear anillo como diferencia entre dos círculos
            x_outer = outer_radius * np.cos(theta)
            y_outer = outer_radius * np.sin(theta)
            x_inner = inner_radius * np.cos(theta)
            y_inner = inner_radius * np.sin(theta)
            
            # Crear el anillo
            ring_vertices = list(zip(x_outer, y_outer)) + list(zip(x_inner[::-1], y_inner[::-1]))
            ring_polygon = Polygon(ring_vertices, fc=colors[color_idx], alpha=0.45, zorder=2)
            
            # Limitar el anillo al área del polígono del jugador
            ring_polygon.set_clip_path(polygon_1)
            ax.add_patch(ring_polygon)
        
        # Contorno del jugador encima
        vertices_1_closed = vertices_1 + [vertices_1[0]]
        x_coords_1 = [v[0] for v in vertices_1_closed]
        y_coords_1 = [v[1] for v in vertices_1_closed]
        ax.plot(x_coords_1, y_coords_1, color=colors[0], linewidth=3, zorder=10)
        
    else:
        # Dos jugadores - colores sólidos
        polygon_1 = Polygon(vertices_1, fc=colors[0], alpha=0.35, zorder=2)
        ax.add_patch(polygon_1)
        
        # Contorno jugador 1
        vertices_1_closed = vertices_1 + [vertices_1[0]]
        x_coords_1 = [v[0] for v in vertices_1_closed]
        y_coords_1 = [v[1] for v in vertices_1_closed]
        ax.plot(x_coords_1, y_coords_1, color=colors[0], linewidth=3, zorder=3)
        
        # Polígono jugador 2
        vertices_2 = get_radar_coordinates(player_2_values, ranges)
        polygon_2 = Polygon(vertices_2, fc=colors[1], alpha=0.35, zorder=2)
        ax.add_patch(polygon_2)
        
        # Contorno jugador 2
        vertices_2_closed = vertices_2 + [vertices_2[0]]
        x_coords_2 = [v[0] for v in vertices_2_closed]
        y_coords_2 = [v[1] for v in vertices_2_closed]
        ax.plot(x_coords_2, y_coords_2, color=colors[1], linewidth=3, zorder=3)
    
    # UNIFIED FOOTER: Consistent brand positioning across modules
    ax.text(-18, -21.5, "Created by Jaime Oriol", ha='center', fontsize=10, color='white', 
            weight='bold', family='DejaVu Sans')  # Creator attribution - left position
    
    # Logo Football Decoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.82, 0.02, 0.2, 0.08])  # [x, y, width, height]
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except Exception as e:
        # Fallback al texto si no se encuentra la imagen
        ax.text(18, -21.5, "Football Decoded", ha='center', fontsize=14, color='white', 
                weight='bold', family='DejaVu Sans')  # Primary brand - right position
    
    ax.axis('off')
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    if show_plot:
        plt.show()
    else:
        plt.close()