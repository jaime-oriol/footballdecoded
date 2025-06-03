#!/usr/bin/env python3
"""
PSG Analysis Configuration
==========================

Configuración específica para el análisis del PSG de Luis Enrique.
Define parámetros, mappings y constantes para la extracción y análisis de datos.

Author: FootballDecoded
Created: 2025-06-03
"""

from pathlib import Path
from typing import Dict, List, Set

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================

# Temporadas objetivo
TARGET_SEASONS = ["2023-24", "2024-25"]

# Ligas objetivo  
TARGET_LEAGUES = ["FRA-Ligue 1"]

# Variaciones del nombre del PSG en diferentes fuentes
PSG_TEAM_NAMES = {
    "fbref": [
        "Paris S-G",
        "Paris Saint-Germain",
        "PSG"
    ],
    "understat": [
        "PSG",
        "Paris Saint-Germain"
    ],
    "fotmob": [
        "Paris Saint-Germain",
        "PSG",
        "Paris SG"
    ],
    "standard": [
        "Paris Saint-Germain",
        "Paris S-G", 
        "PSG",
        "Paris SG"
    ]
}

# Compilar todas las variaciones
ALL_PSG_VARIATIONS: Set[str] = set()
for source_variations in PSG_TEAM_NAMES.values():
    ALL_PSG_VARIATIONS.update(source_variations)

# ============================================================================
# CONFIGURACIÓN DE MÉTRICAS Y ESTADÍSTICAS
# ============================================================================

# Métricas de rendimiento colectivo prioritarias
TEAM_PRIORITY_METRICS = {
    'ofensivas': [
        'goals', 'shots', 'shots_on_target', 'xg', 'npxg',
        'progressive_passes', 'passes_into_final_third',
        'passes_into_penalty_area', 'crosses', 'corners',
        'touches_att_pen_area', 'progressive_carries'
    ],
    'defensivas': [
        'goals_against', 'shots_against', 'xga', 'clean_sheets',
        'tackles', 'interceptions', 'blocks', 'clearances',
        'aerial_duels_won', 'pressures', 'pressure_regains'
    ],
    'posesion': [
        'possession', 'pass_completion_pct', 'progressive_passes',
        'touches', 'carries', 'carry_distance', 'pass_distance'
    ],
    'presion': [
        'pressures', 'pressure_regains', 'pressures_def_3rd',
        'pressures_mid_3rd', 'pressures_att_3rd', 'ppda'
    ]
}

# Métricas de rendimiento individual prioritarias
PLAYER_PRIORITY_METRICS = {
    'ofensivas': [
        'goals', 'assists', 'xg', 'xa', 'npxg', 'shots',
        'shots_on_target', 'goals_per_shot', 'key_passes',
        'progressive_passes', 'passes_into_final_third',
        'passes_into_penalty_area', 'crosses', 'dribbles_completed'
    ],
    'defensivas': [
        'tackles', 'tackles_won', 'interceptions', 'blocks',
        'clearances', 'aerial_duels_won', 'duels_won',
        'pressures', 'pressure_regains', 'recoveries'
    ],
    'distribucion': [
        'passes_completed', 'pass_completion_pct', 'progressive_passes',
        'pass_distance', 'passes_short', 'passes_medium', 'passes_long',
        'pass_completion_short', 'pass_completion_medium', 'pass_completion_long'
    ],
    'disciplina': [
        'cards_yellow', 'cards_red', 'fouls', 'fouled',
        'offsides', 'pens_won', 'pens_conceded'
    ]
}

# Métricas avanzadas específicas para análisis táctico
TACTICAL_METRICS = {
    'progresion': [
        'progressive_carries', 'carries_into_final_third',
        'carries_into_penalty_area', 'progressive_passes_received',
        'touches_def_pen_area', 'touches_att_pen_area'
    ],
    'creatividad': [
        'shot_creating_actions', 'goal_creating_actions',
        'key_passes', 'through_balls', 'switches', 'crosses'
    ],
    'intensidad': [
        'pressures', 'pressure_regains', 'tackles',
        'interceptions', 'distance_covered', 'sprints'
    ]
}

# ============================================================================
# CONFIGURACIÓN DE FUENTES DE DATOS
# ============================================================================

# Prioridad de fuentes para diferentes tipos de datos
DATA_SOURCE_PRIORITY = {
    'team_basic_stats': ['fbref', 'understat', 'fotmob'],
    'player_basic_stats': ['fbref', 'understat'],
    'xg_data': ['understat', 'fbref'],
    'pressure_data': ['fbref'],
    'match_events': ['fbref', 'fotmob'],
    'shot_data': ['understat', 'fbref']
}

# Configuración específica por fuente
SOURCE_CONFIG = {
    'fbref': {
        'rate_limit': 7,  # segundos entre requests
        'stat_types': [
            'standard', 'shooting', 'passing', 'passing_types',
            'goal_shot_creation', 'defense', 'possession', 'misc'
        ],
        'team_stat_types': [
            'standard', 'keeper', 'shooting', 'passing', 'passing_types',
            'goal_shot_creation', 'defense', 'possession', 'misc'
        ]
    },
    'understat': {
        'rate_limit': 3,
        'provides': ['xg', 'shots', 'team_stats', 'player_stats']
    },
    'fotmob': {
        'rate_limit': 2,
        'stat_types': ['Top stats', 'Shots', 'Expected goals (xG)', 'Passes', 'Defence']
    }
}

# ============================================================================
# CONFIGURACIÓN DE PROCESAMIENTO
# ============================================================================

# Normalización de nombres de columnas
COLUMN_MAPPINGS = {
    'goals_for': ['goals', 'gf', 'goals_scored'],
    'goals_against': ['goals_against', 'ga', 'goals_conceded'],
    'expected_goals': ['xg', 'expected_goals', 'xg_for'],
    'expected_goals_against': ['xga', 'expected_goals_against', 'xg_against'],
    'shots_on_target': ['sot', 'shots_on_target', 'shots_on_goal'],
    'pass_completion': ['pass_completion_pct', 'pass_accuracy', 'pass_pct']
}

# Métricas calculadas a añadir
CALCULATED_METRICS = {
    'efficiency_ratios': [
        'goals_per_shot', 'goals_per_xg', 'shot_accuracy',
        'xg_overperformance', 'defensive_efficiency'
    ],
    'performance_indices': [
        'attacking_index', 'defensive_index', 'possession_index',
        'pressure_index', 'overall_performance_index'
    ]
}

# ============================================================================
# CONFIGURACIÓN DE ANÁLISIS COMPARATIVO
# ============================================================================

# Estructura para comparación entre temporadas
COMPARISON_STRUCTURE = {
    'temporal': {
        'current_season': "2024-25",
        'previous_season': "2023-24",
        'comparison_periods': [
            'first_half_season',  # Primeros 19 partidos
            'full_season',        # Temporada completa
            'monthly_evolution'   # Evolución mensual
        ]
    },
    'contextual': {
        'league_position': 'relative_to_league',
        'european_competitions': 'champions_league_impact',
        'injury_impact': 'player_availability'
    }
}

# ============================================================================
# CONFIGURACIÓN DE VALIDACIÓN DE DATOS
# ============================================================================

# Reglas de validación para asegurar calidad de datos
VALIDATION_RULES = {
    'completeness': {
        'min_matches_per_season': 15,  # Mínimo de partidos para análisis válido
        'min_minutes_per_player': 90,  # Mínimo de minutos para análisis individual
        'required_metrics': ['goals', 'xg', 'shots', 'passes']
    },
    'consistency': {
        'max_goals_per_match': 10,
        'max_xg_per_match': 8.0,
        'max_shots_per_match': 40,
        'pass_completion_range': (0.0, 1.0)
    }
}

# ============================================================================
# CONFIGURACIÓN DE EXPORTACIÓN
# ============================================================================

# Formatos de salida
OUTPUT_FORMATS = {
    'raw_data': 'csv',
    'processed_data': 'parquet',
    'summary_reports': 'json',
    'visualizations': 'png'
}

# Estructura de directorios de salida
OUTPUT_STRUCTURE = {
    'raw': 'data/PSG_Analysis/raw',
    'processed': 'data/PSG_Analysis/processed', 
    'reports': 'data/PSG_Analysis/reports',
    'visualizations': 'data/PSG_Analysis/visualizations'
}

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

# Configuración específica de logging para PSG
PSG_LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'data/PSG_Analysis/logs/psg_extraction.log',
    'console_output': True,
    'detailed_timing': True
}

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def get_psg_variations(source: str = 'standard') -> List[str]:
    """
    Obtiene las variaciones del nombre PSG para una fuente específica.
    
    Parameters
    ----------
    source : str
        Fuente de datos ('fbref', 'understat', 'fotmob', 'standard')
        
    Returns
    -------
    List[str]
        Lista de variaciones del nombre PSG
    """
    return PSG_TEAM_NAMES.get(source, PSG_TEAM_NAMES['standard'])

def get_priority_metrics(category: str, metric_type: str = 'team') -> List[str]:
    """
    Obtiene las métricas prioritarias para una categoría específica.
    
    Parameters
    ----------
    category : str
        Categoría de métricas ('ofensivas', 'defensivas', etc.)
    metric_type : str
        Tipo de métricas ('team' o 'player')
        
    Returns
    -------
    List[str]
        Lista de métricas prioritarias
    """
    if metric_type == 'team':
        return TEAM_PRIORITY_METRICS.get(category, [])
    elif metric_type == 'player':
        return PLAYER_PRIORITY_METRICS.get(category, [])
    else:
        return []

def validate_season_format(season: str) -> bool:
    """
    Valida el formato de temporada.
    
    Parameters
    ----------
    season : str
        Temporada a validar (ej: '2023-24')
        
    Returns
    -------
    bool
        True si el formato es válido
    """
    import re
    pattern = r'^\d{4}-\d{2}$'
    return bool(re.match(pattern, season))

def get_source_config(source: str) -> Dict:
    """
    Obtiene la configuración específica para una fuente de datos.
    
    Parameters
    ----------
    source : str
        Nombre de la fuente ('fbref', 'understat', 'fotmob')
        
    Returns
    -------
    Dict
        Configuración de la fuente
    """
    return SOURCE_CONFIG.get(source, {})

def normalize_column_name(column: str) -> str:
    """
    Normaliza nombres de columnas usando los mappings definidos.
    
    Parameters
    ----------
    column : str
        Nombre de columna original
        
    Returns
    -------
    str
        Nombre de columna normalizado
    """
    column_lower = column.lower()
    
    for standard_name, variations in COLUMN_MAPPINGS.items():
        if column_lower in [v.lower() for v in variations]:
            return standard_name
    
    return column

# ============================================================================
# CONFIGURACIÓN DE CALIDAD DE DATOS
# ============================================================================

# Umbrales de calidad para diferentes métricas
QUALITY_THRESHOLDS = {
    'team_metrics': {
        'goals': {'min': 0, 'max': 150, 'type': 'int'},
        'xg': {'min': 0.0, 'max': 120.0, 'type': 'float'},
        'possession': {'min': 0.0, 'max': 1.0, 'type': 'float'},
        'pass_completion_pct': {'min': 0.0, 'max': 1.0, 'type': 'float'}
    },
    'player_metrics': {
        'goals': {'min': 0, 'max': 50, 'type': 'int'},
        'assists': {'min': 0, 'max': 30, 'type': 'int'},
        'minutes': {'min': 0, 'max': 4000, 'type': 'int'},
        'pass_completion_pct': {'min': 0.0, 'max': 1.0, 'type': 'float'}
    }
}