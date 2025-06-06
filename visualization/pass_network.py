# ====================================================================
# FootballDecoded - Pass Network Visualization (StatsBomb Style)
# ====================================================================
# Red de pases con datos de WhoScored: nodos por participación, 
# color por OBV, grosor por frecuencia de pases
# ====================================================================

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from typing import Optional, Tuple, Dict
import sys
import os

# Importar wrapper de WhoScored
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers.whoscored_data import extract_match_events

def create_pass_network_statsbomb(
    match_id: int,
    team_name: str,
    league: str,
    season: str,
    min_passes: int = 5,
    period: str = 'full',  # 'full', 'first_half', 'second_half'
    theme: str = 'light',
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None,
    verbose: bool = False
) -> plt.Figure:
    """
    Crear red de pases estilo StatsBomb con datos de WhoScored.
    
    Args:
        match_id: ID del partido en WhoScored
        team_name: Nombre del equipo para filtrar
        league: Liga (ej: "ENG-Premier League")
        season: Temporada (ej: "2023-24")
        min_passes: Mínimo de pases entre jugadores para mostrar conexión
        period: Período del partido a analizar
        theme: Tema visual ('light', 'dark')
        figsize: Tamaño de la figura
        save_path: Ruta para guardar
        verbose: Mostrar progreso
        
    Returns:
        Figura de matplotlib con la red de pases
    """
    
    if verbose:
        print(f"🔍 Extrayendo eventos de pases para {team_name}")
    
    # 1. EXTRAER DATOS DE WHOSCORED
    try:
        # Obtener todos los eventos del partido
        events_df = extract_match_events(
            match_id=match_id,
            league=league,
            season=season,
            team_filter=team_name,
            verbose=verbose
        )
        
        if events_df.empty:
            # Intentar con variaciones del nombre del equipo
            team_variations = {
                "Spain": ["España", "Spain", "ESP"],
                "England": ["Inglaterra", "England", "ENG"],
                "Barcelona": ["Barcelona", "FC Barcelona", "Barça"],
                "Real Madrid": ["Real Madrid", "Madrid", "Real Madrid CF"]
            }
            
            if team_name in team_variations:
                for variation in team_variations[team_name]:
                    if verbose:
                        print(f"   🔄 Intentando con '{variation}'...")
                    events_df = extract_match_events(
                        match_id=match_id,
                        league=league,
                        season=season,
                        team_filter=variation,
                        verbose=False
                    )
                    if not events_df.empty:
                        if verbose:
                            print(f"   ✅ Datos encontrados con '{variation}'")
                        break
            
            if events_df.empty:
                raise ValueError(f"No se encontraron datos para {team_name} en match {match_id}")
            
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        print(f"   💡 Verifica que el match_id {match_id} sea correcto")
        print(f"   💡 Verifica que el nombre del equipo '{team_name}' sea correcto")
        return plt.figure()
    
    # 2. FILTRAR SOLO EVENTOS DE PASES
    pass_events = events_df[
        events_df['event_type'].str.contains('Pass', case=False, na=False)
    ].copy()
    
    if len(pass_events) == 0:
        print(f"❌ No se encontraron eventos de pase para {team_name}")
        return plt.figure()
    
    # Filtrar por período si es necesario
    if period == 'first_half':
        pass_events = pass_events[pass_events['minute'] <= 45]
    elif period == 'second_half':
        pass_events = pass_events[pass_events['minute'] > 45]
    
    if verbose:
        print(f"   📊 {len(pass_events)} eventos de pase encontrados")
    
    # 3. PROCESAR DATOS PARA LA RED
    network_data = _process_pass_network_data(pass_events, min_passes, verbose)
    
    if not network_data['connections']:
        print(f"❌ No hay conexiones con ≥{min_passes} pases")
        return plt.figure()
    
    # 4. CREAR VISUALIZACIÓN
    fig = _create_network_visualization(
        network_data, team_name, match_id, period, theme, figsize, verbose
    )
    
    # 5. GUARDAR SI SE ESPECIFICA
    if save_path:
        # Usar configuración segura para evitar imágenes demasiado grandes
        fig.savefig(save_path, dpi=100, facecolor='white', bbox_inches=None)
        if verbose:
            print(f"💾 Gráfico guardado en: {save_path}")
    
    return fig


def _process_pass_network_data(
    pass_events: pd.DataFrame, 
    min_passes: int,
    verbose: bool = False
) -> Dict:
    """
    Procesar eventos de pase para crear datos de red.
    
    Args:
        pass_events: DataFrame con eventos de pase de WhoScored
        min_passes: Mínimo de pases para conexión
        verbose: Mostrar progreso
        
    Returns:
        Dict con datos procesados para la red
    """
    
    # Verificar columnas necesarias
    required_cols = ['player', 'start_x', 'start_y', 'is_successful']
    missing_cols = [col for col in required_cols if col not in pass_events.columns]
    
    if missing_cols:
        print(f"⚠️ Columnas faltantes: {missing_cols}")
        # Usar nombres alternativos si están disponibles
        if 'start_x' not in pass_events.columns and 'x' in pass_events.columns:
            pass_events['start_x'] = pass_events['x']
            pass_events['start_y'] = pass_events['y']
    
    # 1. CALCULAR POSICIONES PROMEDIO DE JUGADORES
    player_positions = pass_events.groupby('player').agg({
        'start_x': 'mean',
        'start_y': 'mean'
    }).round(3)
    
    # 2. CALCULAR PARTICIPACIÓN (número total de pases)
    player_participation = pass_events['player'].value_counts().to_dict()
    
    # 3. CALCULAR OBV (simulado si no está disponible)
    if 'obv' in pass_events.columns:
        player_obv = pass_events.groupby('player')['obv'].mean().to_dict()
    else:
        # Simular OBV basado en éxito de pases y posición
        player_obv = {}
        for player in player_participation.keys():
            player_passes = pass_events[pass_events['player'] == player]
            success_rate = player_passes['is_successful'].mean() if 'is_successful' in player_passes.columns else 0.8
            # OBV simulado: combina tasa de éxito con participación
            simulated_obv = (success_rate - 0.5) * (player_participation[player] / 100)
            player_obv[player] = simulated_obv
    
    # 4. CALCULAR CONEXIONES ENTRE JUGADORES
    # Para esto necesitamos identificar pases entre jugadores específicos
    # Simplificado: usar secuencias temporales de pases
    connections = {}
    
    # Ordenar pases por tiempo
    pass_events_sorted = pass_events.sort_values(['minute', 'second'] if 'second' in pass_events.columns else ['minute'])
    
    # Identificar pases consecutivos como conexiones potenciales
    for i in range(len(pass_events_sorted) - 1):
        current_pass = pass_events_sorted.iloc[i]
        next_pass = pass_events_sorted.iloc[i + 1]
        
        # Si el siguiente pase es del mismo equipo y está cerca en tiempo (≤30 segundos)
        time_diff = (next_pass['minute'] - current_pass['minute']) * 60
        if 'second' in pass_events_sorted.columns:
            time_diff += (next_pass.get('second', 0) - current_pass.get('second', 0))
        
        if (time_diff <= 30 and 
            current_pass.get('is_successful', False) and
            current_pass['player'] != next_pass['player']):
            
            passer = current_pass['player']
            receiver = next_pass['player']
            
            # Crear clave única para la conexión
            connection_key = tuple(sorted([passer, receiver]))
            
            if connection_key not in connections:
                connections[connection_key] = 0
            connections[connection_key] += 1
    
    # Filtrar conexiones por mínimo de pases
    filtered_connections = {
        conn: count for conn, count in connections.items() 
        if count >= min_passes
    }
    
    if verbose:
        print(f"   🔗 {len(filtered_connections)} conexiones con ≥{min_passes} pases")
        total_connections = sum(filtered_connections.values())
        print(f"   📊 Total pases en conexiones: {total_connections}")
    
    return {
        'positions': player_positions,
        'participation': player_participation,
        'obv': player_obv,
        'connections': filtered_connections
    }


def _create_network_visualization(
    network_data: Dict,
    team_name: str,
    match_id: int,
    period: str,
    theme: str,
    figsize: Tuple[int, int],
    verbose: bool = False
) -> plt.Figure:
    """
    Crear la visualización de la red de pases.
    
    Args:
        network_data: Datos procesados de la red
        team_name: Nombre del equipo
        match_id: ID del partido
        period: Período analizado
        theme: Tema visual
        figsize: Tamaño de figura
        verbose: Mostrar progreso
        
    Returns:
        Figura de matplotlib
    """
    
    # Configurar tema
    if theme == 'dark':
        bg_color = '#1a1a1a'
        pitch_color = '#2d4a3a'
        line_color = '#ffffff'
        text_color = '#ffffff'
    else:  # light
        bg_color = '#f8f8f8'
        pitch_color = '#2d5a3d'
        line_color = '#ffffff'
        text_color = '#000000'
    
    # Crear figura
    fig, ax = plt.subplots(figsize=figsize, facecolor=bg_color)
    ax.set_facecolor(pitch_color)
    
    # Dibujar campo de fútbol básico
    _draw_football_pitch(ax, line_color)
    
    # Obtener datos
    positions = network_data['positions']
    participation = network_data['participation']
    obv_values = network_data['obv']
    connections = network_data['connections']
    
    # 1. DIBUJAR CONEXIONES (LÍNEAS DE PASE)
    max_passes = max(connections.values()) if connections else 1
    min_passes = min(connections.values()) if connections else 1
    
    for (player1, player2), pass_count in connections.items():
        if player1 in positions.index and player2 in positions.index:
            # Coordenadas de los jugadores
            x1, y1 = positions.loc[player1, 'start_x'], positions.loc[player1, 'start_y']
            x2, y2 = positions.loc[player2, 'start_x'], positions.loc[player2, 'start_y']
            
            # Grosor de línea proporcional al número de pases
            line_width = 0.5 + (pass_count - min_passes) / (max_passes - min_passes) * 4
            
            # Color de línea (gris con transparencia)
            line_alpha = 0.3 + (pass_count - min_passes) / (max_passes - min_passes) * 0.4
            
            ax.plot([x1, x2], [y1, y2], 
                   color='gray', linewidth=line_width, alpha=line_alpha, zorder=1)
    
    # 2. DIBUJAR NODOS (JUGADORES)
    # Normalizar valores para tamaños y colores
    participation_values = list(participation.values())
    obv_list = list(obv_values.values())
    
    if verbose:
        print(f"   📊 Rango de participación: {min(participation_values)} - {max(participation_values)}")
        print(f"   📊 Rango de OBV: {min(obv_list):.3f} - {max(obv_list):.3f}")
        print(f"   📊 Primeros 3 jugadores:")
        for i, player in enumerate(list(positions.index)[:3]):
            x, y = positions.loc[player, 'start_x'], positions.loc[player, 'start_y']
            print(f"      {player}: pos=({x:.3f}, {y:.3f}), pases={participation.get(player, 0)}")
    
    # Tamaños de nodos (basados en participación)
    min_participation = min(participation_values)
    max_participation = max(participation_values)
    
    # Colores de nodos (basados en OBV)
    norm = Normalize(vmin=min(obv_list), vmax=max(obv_list))
    colormap = cm.get_cmap('RdYlBu_r')  # Rojo=bajo OBV, Azul=alto OBV
    
    for player in positions.index:
        if player in participation and player in obv_values:
            x, y = positions.loc[player, 'start_x'], positions.loc[player, 'start_y']
            
            # Verificar si las coordenadas están en rango válido
            if not (0 <= x <= 1 and 0 <= y <= 1):
                if verbose:
                    print(f"   ⚠️ Coordenadas fuera de rango para {player}: ({x:.3f}, {y:.3f})")
                # Normalizar coordenadas si están fuera del rango
                x = max(0, min(1, x / 100 if x > 1 else x))
                y = max(0, min(1, y / 100 if y > 1 else y))
                if verbose:
                    print(f"      Corregidas a: ({x:.3f}, {y:.3f})")
            
            # Tamaño del nodo
            participation_normalized = (participation[player] - min_participation) / (max_participation - min_participation)
            node_size = 200 + participation_normalized * 800  # 200-1000 pixels
            
            # Color del nodo
            obv_color = colormap(norm(obv_values[player]))
            
            # Dibujar nodo
            circle = Circle((x, y), radius=0.02, 
                          facecolor=obv_color, edgecolor='white', 
                          linewidth=2, zorder=3)
            ax.add_patch(circle)
            
            # Añadir nombre del jugador
            ax.text(x, y-0.08, player, ha='center', va='top', 
                   fontsize=8, fontweight='bold', color=text_color, zorder=4)
    
    # 3. CONFIGURAR EJES Y TÍTULO
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Título
    period_text = {'full': 'Partido Completo', 'first_half': 'Primera Parte', 'second_half': 'Segunda Parte'}
    title = f"Red de Pases - {team_name}\n{period_text.get(period, period)} | Match ID: {match_id}"
    fig.suptitle(title, fontsize=14, fontweight='bold', color=text_color, y=0.95)
    
    # 4. LEYENDA
    _add_legend(fig, ax, colormap, norm, text_color)
    
    # 5. ESTADÍSTICAS
    total_players = len(positions)
    total_connections = len(connections)
    total_passes = sum(connections.values())
    
    stats_text = f"Jugadores: {total_players} | Conexiones: {total_connections} | Pases: {total_passes}"
    ax.text(0.5, -0.05, stats_text, transform=ax.transAxes, 
           ha='center', va='top', fontsize=10, color=text_color)
    
    if verbose:
        print(f"   ✅ Red creada: {total_players} jugadores, {total_connections} conexiones")
    
    # Ajustar layout sin tight_layout para evitar warnings
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
    return fig


def _draw_football_pitch(ax: plt.Axes, line_color: str) -> None:
    """Dibujar campo de fútbol básico."""
    # Límites del campo
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color=line_color, linewidth=2)
    
    # Línea central
    ax.plot([0.5, 0.5], [0, 1], color=line_color, linewidth=2)
    
    # Círculo central
    circle = plt.Circle((0.5, 0.5), 0.1, fill=False, color=line_color, linewidth=2)
    ax.add_patch(circle)
    
    # Áreas de penalti (simplificadas)
    # Izquierda
    ax.plot([0, 0.17, 0.17, 0], [0.21, 0.21, 0.79, 0.79], color=line_color, linewidth=2)
    # Derecha  
    ax.plot([1, 0.83, 0.83, 1], [0.21, 0.21, 0.79, 0.79], color=line_color, linewidth=2)
    
    print(f"   ⚽ Campo dibujado con color: {line_color}")


def _add_legend(fig: plt.Figure, ax: plt.Axes, colormap, norm, text_color: str) -> None:
    """Añadir leyenda explicativa."""
    # Colorbar para OBV
    from matplotlib.colorbar import ColorbarBase
    
    # Crear subplot para colorbar
    cbar_ax = fig.add_axes([0.02, 0.15, 0.02, 0.3])
    cbar = ColorbarBase(cbar_ax, cmap=colormap, norm=norm, orientation='vertical')
    cbar.set_label('OBV Value', color=text_color, fontsize=10)
    cbar.ax.tick_params(colors=text_color, labelsize=8)
    
    # Leyenda de tamaños
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                   markersize=6, label='Pocos pases'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                   markersize=12, label='Muchos pases'),
        plt.Line2D([0], [0], color='gray', linewidth=1, label='Pocas conexiones'),
        plt.Line2D([0], [0], color='gray', linewidth=4, label='Muchas conexiones')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
             fancybox=True, shadow=True, fontsize=8)


# Función de conveniencia para uso rápido
def quick_pass_network(match_id: int, team_name: str, league: str, season: str):
    """Función rápida para generar red de pases."""
    return create_pass_network_statsbomb(
        match_id=match_id,
        team_name=team_name, 
        league=league,
        season=season,
        verbose=True
    )