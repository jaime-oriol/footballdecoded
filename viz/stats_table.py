import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
from PIL import Image
import os

def create_stats_table(df_data, player_1_id, metrics, metric_titles, 
                      player_2_id=None, team_colors=None, 
                      save_path='stats_table.png', show_plot=True):
    """
    Crea tabla de estadísticas con estilo visual del swarm radar.
    """
    
    if team_colors is None:
        team_colors = ['#FF6B6B', '#4ECDC4']
    
    # Datos jugadores
    p1 = df_data[df_data['unique_player_id'] == player_1_id].iloc[0]
    p2 = None
    if player_2_id is not None:
        p2 = df_data[df_data['unique_player_id'] == player_2_id].iloc[0]
    
    # Setup figura
    fig_width = 4.5 if p2 is not None else 3.5
    fig = plt.figure(figsize=(fig_width, 6.5), facecolor='#313332')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#313332')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # HEADER
    y_start = 13.5
    
    # Jugador 1
    ax.text(2, y_start, p1['player_name'], 
            fontweight='bold', fontsize=11, color=team_colors[0], ha='center')
    ax.text(2, y_start - 0.4, f"{p1['league']} {p1['season']}", 
            fontsize=8, color='white', alpha=0.8, ha='center')
    
    # Jugador 2
    if p2 is not None:
        ax.text(6, y_start, p2['player_name'], 
                fontweight='bold', fontsize=11, color=team_colors[1], ha='center')
        ax.text(6, y_start - 0.4, f"{p2['league']} {p2['season']}", 
                fontsize=8, color='white', alpha=0.8, ha='center')
    
    # Línea separadora
    y_line = y_start - 0.7
    ax.plot([0.5, 9.5 if p2 is not None else 3.5], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.5)
    
    # CONTEXTO (Minutos y Partidos)
    y_context = y_start - 1.2
    
    # Minutes
    ax.text(0.7, y_context, "Minutes", fontsize=8, color='white', alpha=0.9)
    min1 = int(p1.get('minutes_played', 0))
    ax.text(2, y_context, f"{min1}", fontsize=8, color='white', ha='center')
    if p2 is not None:
        min2 = int(p2.get('minutes_played', 0))
        ax.text(6, y_context, f"{min2}", fontsize=8, color='white', ha='center')
    
    # Matches
    y_context -= 0.4
    ax.text(0.7, y_context, "Matches", fontsize=8, color='white', alpha=0.9)
    mat1 = int(p1.get('matches_played', 0))
    ax.text(2, y_context, f"{mat1}", fontsize=8, color='white', ha='center')
    if p2 is not None:
        mat2 = int(p2.get('matches_played', 0))
        ax.text(6, y_context, f"{mat2}", fontsize=8, color='white', ha='center')
    
    # Línea separadora
    y_line = y_context - 0.3
    ax.plot([0.5, 9.5 if p2 is not None else 3.5], [y_line, y_line], 
            color='grey', linewidth=0.5, alpha=0.5)
    
    # MÉTRICAS
    y_metrics = y_context - 0.7
    row_height = 0.9
    
    for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
        y_pos = y_metrics - (idx * row_height)
        
        # Fondo alternado
        if idx % 2 == 0:
            rect = Rectangle((0.5, y_pos - 0.35), 
                           9 if p2 is not None else 3, 0.7, 
                           facecolor='white', alpha=0.03)
            ax.add_patch(rect)
        
        # Título métrica sin saltos de línea
        clean_title = title.replace('\n', ' ')
        ax.text(0.7, y_pos, clean_title, fontsize=8, color='white', alpha=0.9)
        
        # Jugador 1: valor y percentil
        val_1 = p1.get(metric, 0)
        # Buscar percentil con sufijo _pct
        pct_col = f"{metric}_pct"
        pct_1 = p1.get(pct_col, 0)
        
        # Si es NaN, usar 0
        if pd.isna(pct_1):
            pct_1 = 0
        
        # Formateo valor
        if pd.isna(val_1):
            val_str_1 = "0.0"
        elif 0 < val_1 < 1:
            val_str_1 = f"{val_1:.2f}"
        elif val_1 < 10:
            val_str_1 = f"{val_1:.1f}"
        else:
            val_str_1 = f"{int(val_1)}"
        
        # Color percentil
        if pct_1 > 85:
            pct_color_1 = '#4CAF50'  # Verde
        elif pct_1 < 15:
            pct_color_1 = '#F44336'  # Rojo
        else:
            pct_color_1 = 'white'
        
        ax.text(1.7, y_pos, val_str_1, fontsize=8, color='white', ha='right')
        ax.text(2.3, y_pos, f"{int(pct_1)}", 
                fontsize=8, color=pct_color_1, ha='left', fontweight='bold')
        
        # Jugador 2
        if p2 is not None:
            val_2 = p2.get(metric, 0)
            pct_2 = p2.get(pct_col, 0)
            
            # Si es NaN, usar 0
            if pd.isna(pct_2):
                pct_2 = 0
            
            # Formateo valor
            if pd.isna(val_2):
                val_str_2 = "0.0"
            elif 0 < val_2 < 1:
                val_str_2 = f"{val_2:.2f}"
            elif val_2 < 10:
                val_str_2 = f"{val_2:.1f}"
            else:
                val_str_2 = f"{int(val_2)}"
            
            # Color percentil
            if pct_2 > 85:
                pct_color_2 = '#4CAF50'  # Verde
            elif pct_2 < 15:
                pct_color_2 = '#F44336'  # Rojo
            else:
                pct_color_2 = 'white'
            
            ax.text(5.7, y_pos, val_str_2, fontsize=8, color='white', ha='right')
            ax.text(6.3, y_pos, f"{int(pct_2)}", 
                    fontsize=8, color=pct_color_2, ha='left', fontweight='bold')
    
    # Footer
    ax.text(5 if p2 is not None else 2, 0.5, "Percentiles vs dataset", 
            fontsize=7, color='white', alpha=0.5, ha='center', style='italic')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#313332')
    
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return save_path


def combine_radar_and_table(radar_path, table_path, output_path='combined_visualization.png'):
    """Combina radar y tabla horizontalmente."""
    
    radar_img = Image.open(radar_path)
    table_img = Image.open(table_path)
    
    r_w, r_h = radar_img.size
    t_w, t_h = table_img.size
    
    # Escalar tabla a altura del radar
    scale = r_h / t_h
    new_t_w = int(t_w * scale)
    table_resized = table_img.resize((new_t_w, r_h), Image.Resampling.LANCZOS)
    
    # Combinar
    combined = Image.new('RGB', (r_w + new_t_w, r_h), color='#313332')
    combined.paste(radar_img, (0, 0))
    combined.paste(table_resized, (r_w, 0))
    
    combined.save(output_path, dpi=(300, 300))
    
    return output_path