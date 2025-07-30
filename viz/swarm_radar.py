#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import PyPizza
from matplotlib import font_manager
import warnings
warnings.filterwarnings('ignore')

class PlayerPizzaChart:
    """
    Generador de pizza charts reutilizable para métricas de jugadores.
    
    Usage:
        pizza = PlayerPizzaChart(df_final)
        fig = pizza.create_chart(
            player_id="8c50fb1a1662d90f", 
            metrics_config=midfielder_config,
            title_suffix="FC Barcelona - Temporada 2023/24"
        )
    """
    
    def __init__(self, df, slice_color='#1A78CF'):
        self.df = df
        self.slice_color = slice_color
        
    def create_chart(self, player_id, metrics_config, title_suffix="", figsize=(8, 8.5)):
        """
        Crear pizza chart para un jugador específico.
        
        Args:
            player_id: unique_player_id del jugador (debe existir en df['unique_player_id'])
            metrics_config: Diccionario con 'metrics' y 'titles'
            title_suffix: Sufijo para el título (equipo, temporada, etc.)
            figsize: Tamaño de la figura
            
        Returns:
            matplotlib.figure.Figure
        """
        # Validar jugador existe
        player_data = self._get_player_data(player_id)
        if player_data is None:
            raise ValueError(f"Jugador '{player_id}' no encontrado")
            
        # Validar configuración
        if not self._validate_config(metrics_config):
            raise ValueError("metrics_config debe tener 'metrics' y 'titles' con mismo número de elementos")
            
        # Extraer valores y configuración
        params, values = self._process_metrics(player_data, metrics_config)
        
        if not params:
            raise ValueError("No se encontraron métricas válidas para el jugador")
            
        # Colores uniformes
        slice_colors = [self.slice_color] * len(params)
        text_colors = ['#F2F2F2'] * len(params)
        
        # Crear pizza chart
        fig = self._generate_pizza(params, values, slice_colors, text_colors, figsize)
        
        # Añadir títulos
        self._add_titles(fig, player_data['player_name'], title_suffix)
        
        return fig
    
    def _get_player_data(self, player_id):
        """Extraer datos del jugador específico por unique_player_id."""
        player_rows = self.df[self.df['unique_player_id'] == player_id]
        if player_rows.empty:
            return None
        return player_rows.iloc[0]
    
    def _validate_config(self, config):
        """Validar estructura de configuración."""
        if not isinstance(config, dict):
            return False
        if 'metrics' not in config or 'titles' not in config:
            return False
        if len(config['metrics']) != len(config['titles']):
            return False
        if not (5 <= len(config['metrics']) <= 12):
            return False
        return True
    
    def _process_metrics(self, player_data, config):
        """Procesar métricas y extraer valores."""
        params = []
        values = []
        
        for metric, title in zip(config['metrics'], config['titles']):
            # Buscar columna percentil
            pct_col = f"{metric}_pct"
            
            if pct_col in self.df.columns:
                value = player_data[pct_col]
                if pd.notna(value):
                    params.append(title)
                    values.append(int(value))
        
        return params, values
    
    def _generate_pizza(self, params, values, slice_colors, text_colors, figsize):
        """Generar el pizza chart base."""
        baker = PyPizza(
            params=params,
            background_color="#222222",
            straight_line_color="#000000",
            straight_line_lw=1,
            last_circle_color="#000000",
            last_circle_lw=1,
            other_circle_lw=0,
            inner_circle_size=20
        )
        
        fig, ax = baker.make_pizza(
            values,
            figsize=figsize,
            color_blank_space="same",
            slice_colors=slice_colors,
            value_colors=text_colors,
            value_bck_colors=slice_colors,
            blank_alpha=0.4,
            kwargs_slices=dict(
                edgecolor="#000000", zorder=2, linewidth=1
            ),
            kwargs_params=dict(
                color="#F2F2F2", fontsize=11, va="center"
            ),
            kwargs_values=dict(
                color="#F2F2F2", fontsize=11, zorder=3,
                bbox=dict(
                    edgecolor="#000000", facecolor="cornflowerblue",
                    boxstyle="round,pad=0.2", lw=1
                )
            )
        )
        
        return fig
    
    def _add_titles(self, fig, player_id, title_suffix):
        """Añadir títulos y créditos."""
        # Título principal
        main_title = f"{player_id}"
        if title_suffix:
            main_title += f" - {title_suffix}"
            
        fig.text(0.515, 0.975, main_title, size=16, ha="center", 
                color="#F2F2F2", weight='bold')
        
        # Subtítulo
        fig.text(0.515, 0.955, 
                "Percentile Rank vs Top-Five League Players", 
                size=13, ha="center", color="#F2F2F2", weight='bold')
        
        # Créditos
        fig.text(0.99, 0.02, "data: fbref via footballdecoded\nviz: custom pizza chart", 
                size=9, color="#F2F2F2", ha="right", style='italic')

# =============================================================================
# FUNCIÓN DE CONVENIENCIA
# =============================================================================

def create_pizza_chart(df, player_id, metrics_config, title_suffix="", slice_color="#1A78CF", figsize=(8, 8.5)):
    """
    Función directa para crear pizza chart.
    
    Args:
        df: DataFrame con datos de jugadores
        player_id: unique_player_id del jugador (debe existir en df['unique_player_id'])
        metrics_config: Dict con 'metrics' y 'titles'
        title_suffix: Sufijo del título
        slice_color: Color único para todas las métricas
        figsize: Tamaño de figura
        
    Returns:
        matplotlib.figure.Figure
    """
    pizza = PlayerPizzaChart(df, slice_color=slice_color)
    return pizza.create_chart(player_id, metrics_config, title_suffix, figsize)