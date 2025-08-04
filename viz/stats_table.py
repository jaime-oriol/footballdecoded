import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize
from PIL import Image
import os

# Color de fondo unificado con pass_network
BACKGROUND_COLOR = '#313332'

def create_stats_table(df_data, player_1_id, metrics, metric_titles, 
                      player_2_id=None, team_colors=None, 
                      save_path='stats_table.png', show_plot=True,
                      team_logos=None, footer_text='Percentiles vs dataset'):
    """
    Crea tabla de estadísticas con estilo visual unificado con pass_network.
    
    Args:
        df_data: DataFrame con los datos de todos los jugadores
        player_1_id: ID único del primer jugador
        metrics: Lista de métricas a mostrar
        metric_titles: Lista de títulos para las métricas
        player_2_id: ID del segundo jugador (opcional)
        team_colors: Lista de colores para cada jugador
        save_path: Ruta donde guardar la imagen
        show_plot: Si mostrar el gráfico o no
        team_logos: Diccionario con rutas a logos de equipos
        footer_text: Texto personalizable para el footer
    
    Returns:
        save_path: Ruta donde se guardó la imagen
    """
    
    # Colores por defecto si no se especifican
    if team_colors is None:
        team_colors = ['#FF6B6B', '#4ECDC4']
    
    # Sistema de colores unificado con pass_network
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    percentile_norm = Normalize(vmin=0, vmax=100)
    
    # Extraer datos de los jugadores
    p1 = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    p2 = None
    if player_2_id is not None:
        p2 = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    # Configuración de la figura
    fig_width = 7.5 if p2 is not None else 6.5
    fig = plt.figure(figsize=(fig_width, 8.5), facecolor=BACKGROUND_COLOR)  # Altura aumentada para leyenda
    ax = fig.add_subplot(111)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 15)  # Límite aumentado para leyenda
    ax.axis('off')
    
    # === SECCIÓN HEADER ===
    y_start = 14.5
    
    # Posiciones X ajustadas para alinear con las columnas de valores
    if p2 is not None:
        # Comparación
        logo1_x = 3.85
        text1_x = 4.1
        p1_value_x = 4.6
        p1_pct_x = 5.0
        
        logo2_x = 6.45
        text2_x = 6.5
        p2_value_x = 7.0
        p2_pct_x = 7.4
    else:
        # Individual
        logo1_x = 4.35
        text1_x = 4.0
        p1_value_x = 4.6
        p1_pct_x = 5.0
    
    # Jugador 1 - Logo
    if team_logos and p1['team'] in team_logos:
        try:
            logo = Image.open(team_logos[p1['team']])
            logo_ax = fig.add_axes([logo1_x/10, (y_start-0.8)/15, 0.08, 0.08])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
        except:
            pass
    
    # Nombre y liga
    ax.text(text1_x, y_start, p1['player_name'], 
            fontweight='bold', fontsize=13, color=team_colors[0], ha='left', va='center', family='serif')
    ax.text(text1_x, y_start - 0.4, f"{p1['league']} {p1['season']}", 
            fontsize=10, color='white', alpha=0.9, ha='left', weight='normal', family='serif')
    
    # Jugador 2 (si existe)
    if p2 is not None:
        # Logo del Jugador 2
        if team_logos and p2['team'] in team_logos:
            try:
                logo = Image.open(team_logos[p2['team']])
                logo_ax = fig.add_axes([logo2_x/10, (y_start-0.8)/15, 0.08, 0.08])
                logo_ax.imshow(logo)
                logo_ax.axis('off')
            except:
                pass
        
        ax.text(text2_x, y_start, p2['player_name'],
                fontweight='bold', fontsize=13, color=team_colors[1], ha='left', va='center', family='serif')
        ax.text(text2_x, y_start - 0.4, f"{p2['league']} {p2['season']}", 
                fontsize=10, color='white', alpha=0.9, ha='left', weight='normal', family='serif')
    
    # Línea separadora header
    y_line = y_start - 0.7
    line_end = 8.5 if p2 is not None else 6.5
    ax.plot([0.5, line_end], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.6)
    
    # === SECCIÓN CONTEXTO (Minutos y Partidos) ===
    y_context = y_start - 1.2
    
    # Minutes
    ax.text(0.7, y_context, "Minutes Played", fontsize=10, color='white', weight='bold', family='serif')
    min1 = int(p1.get('minutes_played', 0))
    ax.text(p1_value_x, y_context, f"{min1}", fontsize=10, color='white', ha='right', weight='bold', family='serif')
    if p2 is not None:
        min2 = int(p2.get('minutes_played', 0))
        ax.text(p2_value_x, y_context, f"{min2}", fontsize=10, color='white', ha='right', weight='bold', family='serif')
    
    # Matches
    y_context -= 0.4
    ax.text(0.7, y_context, "Matches Played", fontsize=10, color='white', weight='bold', family='serif')
    mat1 = int(p1.get('matches_played', 0))
    ax.text(p1_value_x, y_context, f"{mat1}", fontsize=10, color='white', ha='right', weight='bold', family='serif')
    if p2 is not None:
        mat2 = int(p2.get('matches_played', 0))
        ax.text(p2_value_x, y_context, f"{mat2}", fontsize=10, color='white', ha='right', weight='bold', family='serif')
    
    # Línea separadora contexto
    y_line = y_context - 0.3
    ax.plot([0.5, line_end], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.6)
    
    # === SECCIÓN MÉTRICAS ===
    y_metrics = y_context - 0.7
    row_height = 1.0
    
    # Iterar sobre cada métrica
    for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
        y_pos = y_metrics - (idx * row_height)
        
        # Fondo alternado para mejor legibilidad
        if idx % 2 == 0:
            rect_width = 8.5 if p2 is not None else 6.5
            rect = Rectangle((0.5, y_pos - 0.4), 
                           rect_width, 0.8, 
                           facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        # Título de la métrica
        clean_title = title.replace('\n', ' ')
        ax.text(0.7, y_pos, clean_title, fontsize=10, color='white', weight='bold', va='center', family='serif')
        
        # === JUGADOR 1: Valor y Percentil ===
        val_1 = p1.get(metric, 0)
        pct_col = f"{metric}_pct"
        pct_1 = p1.get(pct_col, 0)
        
        # Manejar valores NaN
        if pd.isna(pct_1):
            pct_1 = 0
        
        # Formatear valor según su magnitud
        if pd.isna(val_1):
            val_str_1 = "0.0"
        elif 0 < val_1 < 1:
            val_str_1 = f"{val_1:.2f}"
        elif val_1 < 10:
            val_str_1 = f"{val_1:.1f}"
        else:
            val_str_1 = f"{int(val_1)}"
        
        # Color del percentil usando la escala xT
        pct_color_1 = node_cmap(percentile_norm(pct_1))
        
        # Mostrar valor y percentil
        ax.text(p1_value_x, y_pos, val_str_1, fontsize=10, color='white', ha='right', 
                weight='bold', va='center', family='serif')
        ax.text(p1_pct_x, y_pos, f"{int(pct_1)}", 
                fontsize=10, color=pct_color_1, ha='left', fontweight='bold', va='center', family='serif')
        
        # === JUGADOR 2: Valor y Percentil (si existe) ===
        if p2 is not None:
            val_2 = p2.get(metric, 0)
            pct_2 = p2.get(pct_col, 0)
            
            # Manejar valores NaN
            if pd.isna(pct_2):
                pct_2 = 0
            
            # Formatear valor según su magnitud
            if pd.isna(val_2):
                val_str_2 = "0.0"
            elif 0 < val_2 < 1:
                val_str_2 = f"{val_2:.2f}"
            elif val_2 < 10:
                val_str_2 = f"{val_2:.1f}"
            else:
                val_str_2 = f"{int(val_2)}"
            
            # Color del percentil usando la escala xT
            pct_color_2 = node_cmap(percentile_norm(pct_2))
            
            # Mostrar valor y percentil
            ax.text(p2_value_x, y_pos, val_str_2, fontsize=10, color='white', ha='right', 
                    weight='bold', va='center', family='serif')
            ax.text(p2_pct_x, y_pos, f"{int(pct_2)}", 
                    fontsize=10, color=pct_color_2, ha='left', fontweight='bold', va='center', family='serif')
    
    # === FOOTER ===
    footer_y = y_metrics - (len(metrics) * row_height)
    footer_x = 3.75 if p2 is not None else 3.25
    
    # Fondo para el footer si corresponde
    if len(metrics) % 2 == 1:
        rect_width = 8.5 if p2 is not None else 6.5
        rect = Rectangle((0.5, footer_y - 0.4), 
                       rect_width, 0.8, 
                       facecolor='white', alpha=0.05)
        ax.add_patch(rect)
    
    # Footer centrado en la tabla
    ax.text(footer_x, footer_y, footer_text, 
            fontsize=10, color='white', alpha=0.8, ha='center', style='italic', weight='bold', va='center', family='serif')
    
    # === LEYENDA DE PERCENTILES ===
    legend_y = footer_y - 0.8
    legend_x_center = footer_x
    
    # Definir intervalos y sus colores
    intervals = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
    interval_colors = [node_cmap(percentile_norm(i*25)) for i in range(5)]  # 0, 25, 50, 75, 100
    
    # Espaciado entre elementos de leyenda
    total_width = 4.0
    spacing = total_width / len(intervals)
    start_x = legend_x_center - total_width/2
    
    for i, ((low, high), color) in enumerate(zip(intervals, interval_colors)):
        x_pos = start_x + i * spacing
        
        # Línea horizontal representando el intervalo
        line_width = 0.7
        line_length = 0.5
        ax.plot([x_pos - line_length/2, x_pos + line_length/2], 
                [legend_y, legend_y], 
                color=color, linewidth=3, solid_capstyle='round')
        
        # Texto del intervalo
        ax.text(x_pos, legend_y - 0.3, f"{low}-{high}", 
                fontsize=8, color='white', ha='center', va='center', family='serif')
    
    # Guardar figura
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path

def combine_radar_and_table(radar_path, table_path, output_path='combined_visualization.png'):
    """
    Combina radar y tabla horizontalmente manteniendo proporciones.
    
    Args:
        radar_path: Ruta a la imagen del radar
        table_path: Ruta a la imagen de la tabla
        output_path: Ruta donde guardar la imagen combinada
    
    Returns:
        output_path: Ruta donde se guardó la imagen combinada
    """
    
    # Abrir ambas imágenes
    radar_img = Image.open(radar_path)
    table_img = Image.open(table_path)
    
    # Obtener dimensiones
    r_w, r_h = radar_img.size
    t_w, t_h = table_img.size
    
    # Escalar tabla para que tenga la misma altura que el radar
    scale = r_h / t_h
    new_t_w = int(t_w * scale)
    table_resized = table_img.resize((new_t_w, r_h), Image.Resampling.LANCZOS)
    
    # Crear imagen combinada con el color de fondo actualizado
    combined = Image.new('RGB', (r_w + new_t_w, r_h), color=BACKGROUND_COLOR)
    combined.paste(radar_img, (0, 0))
    combined.paste(table_resized, (r_w, 0))
    
    # Guardar imagen combinada
    combined.save(output_path, dpi=(300, 300))
    
    return output_path