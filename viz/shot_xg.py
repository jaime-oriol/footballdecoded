import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from mplsoccer.pitch import VerticalPitch
from PIL import Image
import os

# Configuración visual global
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def plot_shot_xg(csv_path, filter_by='all', logo_path=None, 
                 title_text=None, subtitle_text=None, subsubtitle_text=None):
    """
    Visualización de xG con coordenadas Opta y colormap unificado.
    
    Args:
        csv_path: Ruta al CSV de disparos
        filter_by: 'all', nombre de equipo, o nombre de jugador
        logo_path: Ruta a imagen de logo
        title_text: Título principal
        subtitle_text: Subtítulo
        subsubtitle_text: Sub-subtítulo
    """
    # Cargar datos
    shots_df = pd.read_csv(csv_path)
    
    # Configurar font unificado
    font = 'serif'
    
    # Colormap unificado con pass_network
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Extraer info de competición para defaults
    teams = shots_df['team'].unique()
    comp_name = f"{teams[0]} vs {teams[1]}" if len(teams) == 2 else teams[0]
    
    # Lógica de filtrado
    comp_selected = 0
    if filter_by.lower() == 'all':
        selected_shots = shots_df
        comp_selected = 1
    elif filter_by in shots_df['team'].values:
        selected_shots = shots_df[shots_df['team'] == filter_by]
        comp_selected = 0
    elif filter_by in shots_df['player'].values:
        selected_shots = shots_df[shots_df['player'] == filter_by]
        comp_selected = 0
    else:
        return print(f"No data found for: {filter_by}")
    
    # Preparar datos para visualización
    selected_shots = selected_shots.copy()
    selected_shots['header_tag'] = (selected_shots['body_part'] == 'Head').astype(int)
    selected_shots['goal'] = selected_shots['is_goal'].astype(int)
    
    # Separar por tipo y resultado
    selected_ground_shots = selected_shots[selected_shots['header_tag']==0]
    selected_ground_goals = selected_ground_shots[selected_ground_shots['goal']==1]
    selected_headers = selected_shots[selected_shots['header_tag']==1]
    selected_headed_goals = selected_headers[selected_headers['goal']==1]
    
    # Identificar extremos para highlights
    lowest_xg_goal = selected_shots[selected_shots['goal']==1].sort_values('xg').head(1)
    highest_xg_miss = selected_shots[selected_shots['goal']==0].sort_values('xg', ascending=False).head(1)
    
    # Configurar matplotlib
    mpl.rcParams['xtick.color'] = "white"
    mpl.rcParams['ytick.color'] = "white"
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    
    # Crear pitch y figura
    pitch = VerticalPitch(pitch_type='opta', half=True, pitch_color=PITCH_COLOR, 
                         line_color='white', linewidth=1, stripe=False)
    fig, ax = pitch.grid(nrows=1, ncols=1, title_height=0.03, grid_height=0.7, 
                        endnote_height=0.05, axis=False)
    fig.set_size_inches(9, 7)
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Disparos de pie (no gol) - transparentes
    if not selected_ground_shots.empty:
        ax['pitch'].scatter(selected_ground_shots['y'], selected_ground_shots['x'], 
                           marker='h', s=200, alpha=0.2, c=selected_ground_shots['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # Goles de pie - opacos
    if not selected_ground_goals.empty:
        p1 = ax['pitch'].scatter(selected_ground_goals['y'], selected_ground_goals['x'], 
                                marker='h', s=200, c=selected_ground_goals['xg'], 
                                edgecolors='w', lw=2, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # Headers (no gol) - transparentes
    if not selected_headers.empty:
        ax['pitch'].scatter(selected_headers['y'], selected_headers['x'], 
                           marker='o', s=200, alpha=0.2, c=selected_headers['xg'], 
                           edgecolors='w', vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # Goles de cabeza - opacos
    if not selected_headed_goals.empty:
        ax['pitch'].scatter(selected_headed_goals['y'], selected_headed_goals['x'], 
                           marker='o', s=200, c=selected_headed_goals['xg'], 
                           edgecolors='w', lw=2, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=2)
    
    # Highlights: Mayor xG fallado (color máximo del cmap)
    if not highest_xg_miss.empty:
        highxg_marker = 'o' if highest_xg_miss['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(highest_xg_miss['y'].iloc[0], highest_xg_miss['x'].iloc[0], 
                           marker=highxg_marker, s=200, c=node_cmap(1.0), edgecolors='grey', 
                           lw=2.5, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=3)
    
    # Highlights: Menor xG convertido (color mínimo del cmap)
    if not lowest_xg_goal.empty:
        lowxg_marker = 'o' if lowest_xg_goal['header_tag'].iloc[0]==1 else 'h'
        ax['pitch'].scatter(lowest_xg_goal['y'].iloc[0], lowest_xg_goal['x'].iloc[0], 
                           marker=lowxg_marker, s=200, c=node_cmap(0.0), edgecolors='w', 
                           lw=2.5, vmin=-0.04, vmax=1.0, cmap=node_cmap, zorder=3)
    
    # Colorbar horizontal
    if 'p1' in locals():
        cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
        cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)
    
    # Leyenda de símbolos y colores
    legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
    legend_ax.axis("off")
    plt.xlim([0, 5])
    plt.ylim([0, 1])
    
    # Tipo de disparo
    legend_ax.scatter(0.2, 0.7, marker='h', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.2, marker='o', s=200, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.35, 0.61, "Foot", color="w", fontfamily=font)
    legend_ax.text(0.35, 0.11, "Header", color="w", fontfamily=font)
    
    # Estado del disparo
    mid_color = node_cmap(0.5)
    legend_ax.scatter(1.3, 0.7, marker='h', s=200, c='grey', edgecolors='w', lw=2)
    legend_ax.scatter(1.3, 0.2, marker='h', alpha=0.2, s=200, c=mid_color, edgecolors='w')
    legend_ax.text(1.45, 0.61, "Goal", color="w", fontfamily=font)
    legend_ax.text(1.465, 0.11, "No Goal", color="w", fontfamily=font)
    
    # Extremos destacados
    legend_ax.scatter(2.4, 0.7, marker='h', s=200, c=node_cmap(0.0), edgecolors='w', lw=2.5)
    legend_ax.scatter(2.4, 0.2, marker='h', s=200, c=node_cmap(1.0), edgecolors='grey', lw=2.5)
    legend_ax.text(2.55, 0.61, "Lowest xG Goal", color="w", fontfamily=font)
    legend_ax.text(2.565, 0.11, "Highest xG Miss", color="w", fontfamily=font)
    
    # Títulos con defaults automáticos
    if not title_text:
        title_text = "Expected Goals" if comp_selected == 1 else f"{filter_by} Expected Goals"
    if not subtitle_text:
        subtitle_text = comp_name
    if not subsubtitle_text:
        subsubtitle_text = "2024-25"
    
    fig.text(0.18, 0.92, title_text, fontweight="bold", fontsize=16, color='w', fontfamily=font)
    fig.text(0.18, 0.883, subtitle_text, fontweight="regular", fontsize=14, color='w', fontfamily=font)
    fig.text(0.18, 0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Estadísticas calculadas
    sign = '+' if selected_shots['goal'].sum() - selected_shots['xg'].sum() > 0 else ''
    
    # Labels izquierda
    fig.text(0.65, 0.925, "Shots:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.9, "xG:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.875, "Goals:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.65, 0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    # Valores izquierda
    fig.text(0.73, 0.925, f"{int(selected_shots.count()[0])}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.9, f"{round(selected_shots['xg'].sum(), 1)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.73, 0.875, f"{int(selected_shots['goal'].sum())}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    xg_sum = selected_shots['xg'].sum()
    perf_pct = int(round(100*(selected_shots['goal'].sum()-xg_sum)/xg_sum, 0)) if xg_sum > 0 else 0
    fig.text(0.73, 0.85, f"{sign}{perf_pct}%", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Labels derecha
    fig.text(0.79, 0.927, "xG/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.9, "Goal/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.875, "L xG Goal:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.79, 0.85, "H xG Miss:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    # Valores derecha
    shot_count = selected_shots.count()[0]
    fig.text(0.89, 0.925, f"{round(selected_shots['xg'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.9, f"{round(selected_shots['goal'].sum()/shot_count, 2)}", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.875, f"{round(lowest_xg_goal['xg'].iloc[0], 2)}" if not lowest_xg_goal.empty else "N/A", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.89, 0.85, f"{round(highest_xg_miss['xg'].iloc[0], 2)}" if not highest_xg_miss.empty else "N/A", fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Footer unificado
    fig.text(0.075 , 0.02, "Created by Jaime Oriol", fontweight='bold', fontsize=10, color="white", fontfamily=font)
    fig.text(0.7, 0.02, "Football Decoded", fontweight='bold', fontsize=14, color="white", fontfamily=font)
    
    # Logo opcional
    if logo_path and os.path.exists(logo_path):
        ax_logo = fig.add_axes([0.05, 0.82, 0.15, 0.15])
        ax_logo.axis("off")
        try:
            img = Image.open(logo_path)
            ax_logo.imshow(img)
        except Exception as e:
            print(f"Error cargando logo: {e}")
    
    plt.tight_layout()
    return fig