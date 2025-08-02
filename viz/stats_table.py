import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
from PIL import Image
import os

def create_stats_table(df_data, 
                      player_1_id,
                      metrics,
                      metric_titles,
                      player_2_id=None,
                      team_colors=None,
                      save_path='stats_table.png',
                      show_plot=True):
    """
    Crea una tabla de estadísticas con el mismo estilo visual del swarm radar.
    
    Args:
        df_data: DataFrame con todos los datos
        player_1_id: ID del jugador 1
        metrics: Lista de métricas a mostrar (10)
        metric_titles: Títulos legibles de las métricas (10)
        player_2_id: ID del jugador 2 (opcional)
        team_colors: Colores de los equipos
        save_path: Ruta para guardar la imagen
        show_plot: Si mostrar el plot
    """
    
    # Colores por defecto
    if team_colors is None:
        team_colors = ['#FF6B6B', '#4ECDC4']
    
    # Obtener datos de jugadores
    player_1_data = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    player_2_data = None
    if player_2_id:
        player_2_data = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    # Configurar figura
    fig_width = 4.5 if player_2_data else 3.5
    fig = plt.figure(figsize=(fig_width, 6.5), facecolor='#313332')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#313332')
    
    # Ocultar ejes
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # HEADER - Nombres de jugadores
    y_start = 13.5
    
    # Jugador 1
    ax.text(2, y_start, player_1_data['player_name'], 
            fontweight='bold', fontsize=11, color=team_colors[0], ha='center')
    
    # Liga y temporada combinadas
    league_season = f"{player_1_data['league']} {player_1_data['season']}"
    ax.text(2, y_start - 0.4, league_season, 
            fontsize=8, color='white', alpha=0.8, ha='center')
    
    # Jugador 2 (si existe)
    if player_2_data:
        ax.text(6, y_start, player_2_data['player_name'], 
                fontweight='bold', fontsize=11, color=team_colors[1], ha='center')
        
        league_season_2 = f"{player_2_data['league']} {player_2_data['season']}"
        ax.text(6, y_start - 0.4, league_season_2, 
                fontsize=8, color='white', alpha=0.8, ha='center')
    
    # Línea separadora después del header
    y_line = y_start - 0.7
    ax.plot([0.5, 9.5] if player_2_data else [0.5, 3.5], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.5)
    
    # FILAS DE CONTEXTO (Minutos y Partidos)
    y_context = y_start - 1.2
    
    # Minutos jugados
    ax.text(0.7, y_context, "Minutes Played", fontsize=8, color='white', alpha=0.9)
    ax.text(2, y_context, f"{int(player_1_data.get('minutes_played', 0))}", 
            fontsize=8, color='white', ha='center')
    if player_2_data:
        ax.text(6, y_context, f"{int(player_2_data.get('minutes_played', 0))}", 
                fontsize=8, color='white', ha='center')
    
    # Partidos jugados
    y_context -= 0.4
    ax.text(0.7, y_context, "Matches Played", fontsize=8, color='white', alpha=0.9)
    ax.text(2, y_context, f"{int(player_1_data.get('matches_played', 0))}", 
            fontsize=8, color='white', ha='center')
    if player_2_data:
        ax.text(6, y_context, f"{int(player_2_data.get('matches_played', 0))}", 
                fontsize=8, color='white', ha='center')
    
    # Línea separadora después del contexto
    y_line = y_context - 0.3
    ax.plot([0.5, 9.5] if player_2_data else [0.5, 3.5], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.5)
    
    # FILAS DE MÉTRICAS
    y_metrics = y_context - 0.7
    row_height = 0.9
    
    for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
        y_pos = y_metrics - (idx * row_height)
        
        # Fondo alternado para legibilidad
        if idx % 2 == 0:
            rect = Rectangle((0.5, y_pos - 0.35), 
                           9 if player_2_data else 3, 0.7, 
                           facecolor='white', alpha=0.03)
            ax.add_patch(rect)
        
        # Título de la métrica (usando el título legible)
        # Reemplazar saltos de línea por espacios para la tabla
        clean_title = title.replace('\n', ' ')
        ax.text(0.7, y_pos, clean_title, fontsize=8, color='white', alpha=0.9)
        
        # Valor y percentil jugador 1
        value_1 = player_1_data.get(metric, 0)
        percentile_col = f"{metric}_pct"
        percentile_1 = player_1_data.get(percentile_col, 50)
        
        # Formatear valor
        if value_1 < 0.01 and value_1 > 0:
            value_str_1 = f"{value_1:.3f}"
        elif value_1 < 1:
            value_str_1 = f"{value_1:.2f}"
        else:
            value_str_1 = f"{value_1:.1f}"
        
        # Color del percentil
        if pd.notna(percentile_1):
            if percentile_1 > 85:
                pct_color_1 = '#4CAF50'  # Verde
            elif percentile_1 < 15:
                pct_color_1 = '#F44336'  # Rojo
            else:
                pct_color_1 = 'white'
        else:
            pct_color_1 = 'grey'
            percentile_1 = '-'
        
        # Mostrar valor y percentil
        ax.text(1.7, y_pos, value_str_1, fontsize=8, color='white', ha='right')
        ax.text(2.3, y_pos, f"({int(percentile_1) if percentile_1 != '-' else '-'})", 
                fontsize=7, color=pct_color_1, ha='left', alpha=0.9)
        
        # Jugador 2 (si existe)
        if player_2_data:
            value_2 = player_2_data.get(metric, 0)
            percentile_2 = player_2_data.get(percentile_col, 50)
            
            # Formatear valor
            if value_2 < 0.01 and value_2 > 0:
                value_str_2 = f"{value_2:.3f}"
            elif value_2 < 1:
                value_str_2 = f"{value_2:.2f}"
            else:
                value_str_2 = f"{value_2:.1f}"
            
            # Color del percentil
            if pd.notna(percentile_2):
                if percentile_2 > 85:
                    pct_color_2 = '#4CAF50'
                elif percentile_2 < 15:
                    pct_color_2 = '#F44336'
                else:
                    pct_color_2 = 'white'
            else:
                pct_color_2 = 'grey'
                percentile_2 = '-'
            
            ax.text(5.7, y_pos, value_str_2, fontsize=8, color='white', ha='right')
            ax.text(6.3, y_pos, f"({int(percentile_2) if percentile_2 != '-' else '-'})", 
                    fontsize=7, color=pct_color_2, ha='left', alpha=0.9)
    
    # Footer
    ax.text(5 if player_2_data else 2, 0.5, "Percentiles vs dataset", 
            fontsize=7, color='white', alpha=0.5, ha='center', style='italic')
    
    # Guardar
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path


def combine_radar_and_table(radar_path, table_path, output_path='combined_visualization.png'):
    """
    Combina el radar y la tabla en una sola imagen.
    
    Args:
        radar_path: Ruta del archivo del radar
        table_path: Ruta del archivo de la tabla
        output_path: Ruta donde guardar la imagen combinada
    """
    # Abrir ambas imágenes
    radar_img = Image.open(radar_path)
    table_img = Image.open(table_path)
    
    # Obtener dimensiones
    radar_width, radar_height = radar_img.size
    table_width, table_height = table_img.size
    
    # Escalar la tabla para que tenga la misma altura que el radar
    scale_factor = radar_height / table_height
    new_table_width = int(table_width * scale_factor)
    table_img_resized = table_img.resize((new_table_width, radar_height), Image.Resampling.LANCZOS)
    
    # Crear nueva imagen combinada
    combined_width = radar_width + new_table_width
    combined_img = Image.new('RGB', (combined_width, radar_height), color='#313332')
    
    # Pegar ambas imágenes
    combined_img.paste(radar_img, (0, 0))
    combined_img.paste(table_img_resized, (radar_width, 0))
    
    # Guardar
    combined_img.save(output_path, dpi=(300, 300))
    
    return output_path