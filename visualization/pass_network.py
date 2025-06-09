# ====================================================================
# FootballDecoded - Pass Network Visualization Engine
# ====================================================================
# Visualización modular de redes de pases estilo StatsBomb/The Athletic
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import seaborn as sns

# ====================================================================
# CONFIGURACIÓN VISUAL - ESTILO STATSBOMB
# ====================================================================

FIELD_CONFIG = {
    'length': 105,  # meters
    'width': 68,    # meters
    'color': 'white',  # Campo blanco como StatsBomb
    'line_color': '#000000',  # Líneas del campo negras
    'line_width': 2.0,
    'goal_color': '#888888',  # Color gris más oscuro para porterías
    'goal_width': 5.0  # Portería más gruesa
}

# Configuración específica de conexiones estilo StatsBomb
CONNECTION_CONFIG = {
    'min_passes': 5,  # Mínimo 5 pases para mostrar conexión
    'thickness_tiers': [5, 10, 15, 20, 25],  # Escalones de grosor cada 5 pases
    'line_widths': [2.0, 3.5, 5.0, 6.5, 8.0],  # Grosores correspondientes
    'max_width': 8.0,
    'direction_offset': 0.8,  # Separación entre líneas direccionales
    'alpha': 0.7
}

# Colores por defecto para equipos
TEAM_COLORS = {
    'default': {'primary': '#3B82F6', 'secondary': '#1E40AF'},
    'Barcelona': {'primary': '#A50044', 'secondary': '#004D98'},
    'Real Madrid': {'primary': '#FEBE10', 'secondary': '#00529F'},
    'Athletic': {'primary': '#EE2E24', 'secondary': '#000000'},
    'Manchester City': {'primary': '#6CABDD', 'secondary': '#1C2C5B'},
    'Liverpool': {'primary': '#C8102E', 'secondary': '#00B2A9'}
}

# ====================================================================
# PROCESAMIENTO DE DATOS
# ====================================================================

def process_pass_network_data(network_data: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa datos crudos del extractor y calcula métricas para visualización.
    
    Args:
        network_data: Dict con 'passes', 'players', 'connections'
        
    Returns:
        (positions_processed, connections_processed)
    """
    # Verificar si tenemos datos de jugadores (puede venir como 'players' o 'positions')
    players_key = 'players' if 'players' in network_data else 'positions'
    
    if not network_data or players_key not in network_data or network_data[players_key].empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Usar datos ya procesados del extractor
    positions_df = network_data[players_key].copy()
    connections_df = network_data['connections'].copy() if 'connections' in network_data and not network_data['connections'].empty else pd.DataFrame()
    
    # Convertir coordenadas y centrar correctamente en el campo
    positions_df['field_x'] = positions_df['avg_x']  # Ya están en metros
    positions_df['field_y'] = positions_df['avg_y']  # Ya están en metros
    
    # Calcular tamaño de nodo basado en pases totales (más grande)
    positions_df['node_size'] = _calculate_node_sizes_enhanced(positions_df['total_passes'])
    
    # Procesar conexiones direccionales si existen
    if not connections_df.empty:
        connections_df['line_width'] = _calculate_line_widths_enhanced(connections_df['pass_count'])
        # Crear conexiones direccionales (A->B y B->A por separado)
        connections_processed = _create_directional_connections(connections_df, network_data['passes'])
    else:
        connections_processed = pd.DataFrame()
    
    return positions_df, connections_processed


def _calculate_node_sizes_enhanced(pass_counts: pd.Series, min_size: int = 800, max_size: int = 2000) -> pd.Series:
    """Calcula tamaños de nodos más grandes y proporcionales."""
    if pass_counts.empty:
        return pd.Series()
    
    min_passes = pass_counts.min()
    max_passes = pass_counts.max()
    
    if max_passes == min_passes:
        return pd.Series([min_size] * len(pass_counts), index=pass_counts.index)
    
    # Normalización con raíz cuadrada para mejor escalado visual
    normalized = np.sqrt((pass_counts - min_passes) / (max_passes - min_passes))
    sizes = min_size + (normalized * (max_size - min_size))
    
    return sizes


def _calculate_line_widths_enhanced(pass_counts: pd.Series) -> pd.Series:
    """Calcula grosor de líneas estilo StatsBomb mejorado."""
    if pass_counts.empty:
        return pd.Series()
    
    def get_enhanced_width(count):
        """Obtiene grosor con mejor diferenciación."""
        if count < CONNECTION_CONFIG['min_passes']:
            return 0  # No mostrar
        elif count < 10:
            return 2.5
        elif count < 15:
            return 4.0
        elif count < 20:
            return 5.5
        elif count < 25:
            return 7.0
        else:
            return 8.5  # Máximo grosor
    
    return pass_counts.apply(get_enhanced_width)


def _create_directional_connections(connections_df: pd.DataFrame, passes_df: pd.DataFrame) -> pd.DataFrame:
    """Crea conexiones simplificadas desde los datos existentes."""
    if connections_df.empty:
        return pd.DataFrame()
    
    directional_connections = []
    processed_pairs = set()  # Para evitar duplicados
    
    for _, conn in connections_df.iterrows():
        source = conn['source']
        target = conn['target']
        pass_count = conn['pass_count']
        
        # Crear identificador único para el par (ordenado)
        pair_id = tuple(sorted([source, target]))
        
        # Solo procesar si no hemos visto este par antes
        if pair_id not in processed_pairs and pass_count >= CONNECTION_CONFIG['min_passes']:
            processed_pairs.add(pair_id)
            
            directional_connections.append({
                'source': source,
                'target': target,
                'pass_count': pass_count,
                'line_width': _calculate_line_widths_enhanced(pd.Series([pass_count])).iloc[0],
                'direction': 'main'
            })
    
    return pd.DataFrame(directional_connections)


# ====================================================================
# VISUALIZACIÓN DEL CAMPO
# ====================================================================

def draw_football_pitch(ax, half_pitch: bool = False):
    """Dibuja un campo de fútbol profesional con líneas negras y porterías grises."""
    length = FIELD_CONFIG['length']
    width = FIELD_CONFIG['width']
    
    if half_pitch:
        length = length / 2
    
    # Campo base blanco
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0,
                            edgecolor='none',
                            facecolor=FIELD_CONFIG['color'])
    ax.add_patch(pitch)
    
    # Línea central (negra)
    if not half_pitch:
        ax.plot([length/2, length/2], [0, width], 
               color=FIELD_CONFIG['line_color'], 
               linewidth=FIELD_CONFIG['line_width'])
    
    # Círculo central (negro)
    if not half_pitch:
        circle = patches.Circle((length/2, width/2), 9.15, 
                              linewidth=FIELD_CONFIG['line_width'],
                              edgecolor=FIELD_CONFIG['line_color'],
                              facecolor='none')
        ax.add_patch(circle)
    
    # Áreas y porterías
    _draw_penalty_areas(ax, length, width)
    _draw_goals(ax, length, width)
    
    # Bordes del campo (negro)
    border = patches.Rectangle((0, 0), length, width,
                             linewidth=FIELD_CONFIG['line_width'],
                             edgecolor=FIELD_CONFIG['line_color'],
                             facecolor='none')
    ax.add_patch(border)
    
    ax.set_xlim(-2, length + 2)
    ax.set_ylim(-2, width + 2)
    ax.set_aspect('equal')
    ax.axis('off')


def _draw_penalty_areas(ax, length: float, width: float):
    """Dibuja áreas de penalti con líneas negras."""
    # Área grande (16.5m)
    penalty_length = 16.5
    penalty_width = 40.32
    penalty_y_start = (width - penalty_width) / 2
    
    # Área izquierda
    penalty_left = patches.Rectangle((0, penalty_y_start), penalty_length, penalty_width,
                                   linewidth=FIELD_CONFIG['line_width'],
                                   edgecolor=FIELD_CONFIG['line_color'],
                                   facecolor='none')
    ax.add_patch(penalty_left)
    
    # Área derecha
    penalty_right = patches.Rectangle((length - penalty_length, penalty_y_start), 
                                    penalty_length, penalty_width,
                                    linewidth=FIELD_CONFIG['line_width'],
                                    edgecolor=FIELD_CONFIG['line_color'],
                                    facecolor='none')
    ax.add_patch(penalty_right)
    
    # Área pequeña (5.5m)
    small_area_length = 5.5
    small_area_width = 18.32
    small_y_start = (width - small_area_width) / 2
    
    # Área pequeña izquierda
    small_left = patches.Rectangle((0, small_y_start), small_area_length, small_area_width,
                                 linewidth=FIELD_CONFIG['line_width'],
                                 edgecolor=FIELD_CONFIG['line_color'],
                                 facecolor='none')
    ax.add_patch(small_left)
    
    # Área pequeña derecha
    small_right = patches.Rectangle((length - small_area_length, small_y_start), 
                                  small_area_length, small_area_width,
                                  linewidth=FIELD_CONFIG['line_width'],
                                  edgecolor=FIELD_CONFIG['line_color'],
                                  facecolor='none')
    ax.add_patch(small_right)


def _draw_goals(ax, length: float, width: float):
    """Dibuja las porterías con líneas grises más gruesas."""
    goal_width = 7.32
    goal_y_start = (width - goal_width) / 2
    
    # Portería izquierda (línea gruesa gris)
    ax.plot([0, 0], [goal_y_start, goal_y_start + goal_width],
           color=FIELD_CONFIG['goal_color'],
           linewidth=FIELD_CONFIG['goal_width'],
           solid_capstyle='round')
    
    # Portería derecha (línea gruesa gris)  
    ax.plot([length, length], [goal_y_start, goal_y_start + goal_width],
           color=FIELD_CONFIG['goal_color'], 
           linewidth=FIELD_CONFIG['goal_width'],
           solid_capstyle='round')


# ====================================================================
# VISUALIZACIÓN PRINCIPAL
# ====================================================================

def plot_pass_network(network_data: Dict, team_name: str, 
                     show_player_names: bool = True,
                     title: Optional[str] = None,
                     figsize: Tuple[int, int] = (16, 11)) -> plt.Figure:
    """
    Genera visualización completa de red de pases estilo StatsBomb mejorado.
    
    Args:
        network_data: Datos del wrapper de WhoScored
        team_name: Nombre del equipo
        show_player_names: Mostrar nombres de jugadores
        title: Título personalizado
        figsize: Tamaño de la figura
        
    Returns:
        Figure de matplotlib
    """
    # Procesar datos
    positions_df, connections_df = process_pass_network_data(network_data)
    
    if positions_df.empty:
        raise ValueError(f"No se encontraron datos para {team_name}")
    
    # Configurar figura con fondo blanco
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    
    # Dibujar campo
    draw_football_pitch(ax)
    
    # Obtener colores del equipo o usar por defecto
    team_colors = TEAM_COLORS.get(team_name, TEAM_COLORS['default'])
    
    # SIEMPRE dibujar nodos de jugadores (incluso sin conexiones)
    _draw_player_nodes_enhanced(ax, positions_df, team_colors['primary'])
    
    # Dibujar conexiones solo si existen
    if not connections_df.empty:
        _draw_connections_statsbomb_enhanced(ax, connections_df, positions_df, team_colors['secondary'])
        connections_count = len(connections_df)
    else:
        connections_count = 0
        print(f"⚠️ No hay conexiones para {team_name} (mostrar solo posiciones medias)")
    
    # Añadir nombres de jugadores más cerca
    if show_player_names:
        _add_player_labels_enhanced(ax, positions_df)
    
    # Configurar título
    if title is None:
        total_passes = len(network_data['passes']) if 'passes' in network_data else 0
        if connections_count > 0:
            title = f"{team_name} - Red de Pases\nPases completados: {total_passes} | Conexiones: {connections_count}"
        else:
            title = f"{team_name} - Posiciones Medias\nPases completados: {total_passes} | Sin conexiones suficientes"
    
    ax.set_title(title, color='black', fontsize=18, fontweight='bold', pad=25)
    
    plt.tight_layout()
    return fig


def _draw_connections_statsbomb_enhanced(ax, connections_df: pd.DataFrame, positions_df: pd.DataFrame, color: str):
    """Dibuja conexiones simplificadas."""
    if connections_df.empty:
        return
        
    for _, connection in connections_df.iterrows():
        source_player = connection['source']
        target_player = connection['target']
        
        # Buscar posiciones de los jugadores
        source_pos = positions_df[positions_df['player'] == source_player]
        target_pos = positions_df[positions_df['player'] == target_player]
        
        if source_pos.empty or target_pos.empty:
            continue
        
        x1, y1 = source_pos.iloc[0]['field_x'], source_pos.iloc[0]['field_y']
        x2, y2 = target_pos.iloc[0]['field_x'], target_pos.iloc[0]['field_y']
        
        # Usar grosor calculado
        line_width = connection['line_width']
        
        # Solo dibujar si el grosor es > 0 (≥5 pases)
        if line_width > 0:
            ax.plot([x1, x2], [y1, y2], 
                   color=color, 
                   linewidth=line_width,
                   alpha=CONNECTION_CONFIG['alpha'],
                   solid_capstyle='round',
                   zorder=1)


def _draw_player_nodes_enhanced(ax, positions_df: pd.DataFrame, color: str):
    """Dibuja nodos de jugadores más grandes con mejor contraste."""
    for _, player in positions_df.iterrows():
        ax.scatter(player['field_x'], player['field_y'],
                  s=player['node_size'],
                  c=color,
                  edgecolors='white',
                  linewidth=4,  # Borde aún más grueso
                  alpha=0.95,
                  zorder=3)


def _add_player_labels_enhanced(ax, positions_df: pd.DataFrame):
    """Añade etiquetas de jugadores más grandes y más cerca del círculo."""
    for _, player in positions_df.iterrows():
        # Usar apellido si el nombre es muy largo
        player_name = player['player']
        if len(player_name) > 12:
            player_name = player_name.split()[-1]
        
        # Calcular offset basado en tamaño del nodo (más cerca)
        node_radius = np.sqrt(player['node_size'] / np.pi) / 12  # Radio más pequeño
        offset = node_radius + 0.8  # Mucho más cerca del círculo
        
        ax.text(player['field_x'], player['field_y'] - offset,
               player_name,
               ha='center', va='top',
               color='black',
               fontsize=12,  # Texto más grande
               fontweight='bold',
               zorder=4)


# ====================================================================
# FUNCIÓN PRINCIPAL DE USO
# ====================================================================

def create_pass_network_from_data(processed_data: Dict[str, pd.DataFrame], 
                                team_name: str,
                                save_path: Optional[str] = None) -> plt.Figure:
    """
    Función optimizada para crear visualización desde datos ya procesados.
    
    Args:
        processed_data: Dict con DataFrames ya procesados ('passes', 'players', 'connections')
        team_name: Nombre del equipo
        save_path: Ruta para guardar la imagen (opcional)
        
    Returns:
        Figure de matplotlib
    """
    print(f"🎨 Creando visualización para {team_name}...")
    
    # Debug: Verificar estructura de datos
    print(f"🔍 Claves disponibles: {list(processed_data.keys())}")
    players_key = 'players' if 'players' in processed_data else 'positions'
    print(f"🔍 Usando clave: {players_key}")
    
    # Debug: Verificar columnas en los datos
    if 'passes' in processed_data:
        print(f"🔍 Columnas en passes: {list(processed_data['passes'].columns)}")
    if 'connections' in processed_data:
        print(f"🔍 Columnas en connections: {list(processed_data['connections'].columns)}")
    
    # Filtrar datos del equipo específico
    team_data = _filter_team_data(processed_data, team_name)
    
    if team_data['players'].empty:
        raise ValueError(f"No se encontraron datos para {team_name}")
    
    # Crear visualización
    fig = plot_pass_network(team_data, team_name)
    
    # Guardar si se especifica ruta
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📊 Visualización guardada: {save_path}")
    
    return fig


def _filter_team_data(processed_data: Dict[str, pd.DataFrame], team_name: str) -> Dict[str, pd.DataFrame]:
    """Filtra datos para un equipo específico."""
    
    # Determinar clave correcta para datos de jugadores
    players_key = 'players' if 'players' in processed_data else 'positions'
    
    # Filtrar cada DataFrame por equipo
    team_players = processed_data[players_key][processed_data[players_key]['team'] == team_name]
    team_connections = processed_data['connections'][processed_data['connections']['team'] == team_name] if 'connections' in processed_data else pd.DataFrame()
    team_passes = processed_data['passes'][processed_data['passes']['team'] == team_name]
    
    # Crear estructura compatible con la función plot_pass_network usando 'players' como clave estándar
    return {
        'passes': team_passes,
        'players': team_players,  # Usar 'players' como clave estándar
        'connections': team_connections
    }


# ====================================================================
# EJEMPLO DE USO CON DATOS PROCESADOS
# ====================================================================

if __name__ == "__main__":
    # Ejemplo usando datos ya extraídos
    try:
        # Opción 1: Cargar datos previamente guardados
        print("📂 Cargando datos previamente procesados...")
        from match_data import load_processed_data
        
        processed_data = load_processed_data("./match_data", 1821769)
        
        # Crear visualización para Barcelona
        fig_barca = create_pass_network_from_data(
            processed_data=processed_data,
            team_name="Barcelona",
            save_path="barcelona_pass_network_statsbomb.png"
        )
        
        # Crear visualización para Athletic
        fig_athletic = create_pass_network_from_data(
            processed_data=processed_data,
            team_name="Athletic",
            save_path="athletic_pass_network_statsbomb.png"
        )
        
        plt.show()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Primero ejecuta: quick_data_extractor.py para extraer los datos")