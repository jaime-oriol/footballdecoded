"""
Query Helpers para análisis TFM

Funciones de alto nivel para consultar la base de datos con filtros avanzados
de Transfermarkt (posición específica, valor de mercado) y añadir jugadores exógenos
de otras ligas/temporadas.

Uso típico:
    from tfm.query_helpers import query_player_pool, add_exogenous_player, get_positions

    # Query pool con filtros Transfermarkt
    pool = query_player_pool(
        league='ESP-La Liga',
        season='2425',
        positions=get_positions('WINGERS'),  # ['LW', 'RW']
        max_market_value=50_000_000,
        min_minutes=500
    )

    # Añadir target de otra temporada
    full_df = add_exogenous_player(pool, 'Vinicius', 'ESP-La Liga', '2324', 'Real Madrid')
"""

import pandas as pd
from typing import Optional, Union, List, Dict
from sqlalchemy import text
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from database.connection import get_db_manager


# ============================================================================
# CONSTANTES
# ============================================================================

# Posiciones Transfermarkt (códigos cortos REALES de la BD)
POSITIONS = {
    'GK': ['GK'],
    'DF': ['CB', 'RB', 'LB'],
    'MF': ['CDM', 'CM', 'CAM', 'RM', 'LM'],
    'FW': ['LW', 'RW', 'ST', 'SS'],
    'WINGERS': ['LW', 'RW'],
    'STRIKERS': ['ST', 'SS'],
    'FULLBACKS': ['RB', 'LB'],
    'ALL': ['GK', 'CB', 'RB', 'LB', 'CDM', 'CM', 'CAM', 'RM', 'LM',
            'LW', 'RW', 'ST', 'SS']
}


# ============================================================================
# FUNCIONES PÚBLICAS
# ============================================================================

def get_positions(position_group: str) -> List[str]:
    """
    Helper para obtener lista de posiciones por grupo.

    Args:
        position_group: Key de POSITIONS ('FW', 'WINGERS', 'STRIKERS', etc.)

    Returns:
        Lista de códigos de posición Transfermarkt

    Raises:
        ValueError: Si position_group no existe

    Example:
        >>> get_positions('WINGERS')
        ['LW', 'RW']
        >>> get_positions('FW')
        ['LW', 'RW', 'ST', 'SS']
    """
    if position_group not in POSITIONS:
        raise ValueError(
            f"Invalid position group '{position_group}'. "
            f"Available: {list(POSITIONS.keys())}"
        )
    return POSITIONS[position_group]


def query_player_pool(
    league: str,
    season: str,
    positions: Optional[Union[str, List[str]]] = None,
    max_market_value: Optional[int] = None,
    min_minutes: int = 0,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    table_type: str = 'domestic',
    additional_filters: Optional[str] = None
) -> pd.DataFrame:
    """
    Query pool de jugadores con filtros avanzados de Transfermarkt.

    Args:
        league: Liga ('ESP-La Liga', 'ENG-Premier League', etc.)
        season: Temporada ('2425', '2324', etc.)
        positions: Código(s) de posición Transfermarkt. String único o lista.
                  Ej: 'LW' o ['LW', 'RW'] o get_positions('WINGERS')
        max_market_value: Valor máximo de mercado en EUR (ej: 50000000 = 50M).
                         Solo aplica al POOL (no afecta target exógeno).
        min_minutes: Minutos mínimos jugados (FBref)
        min_age: Edad mínima (ej: 18)
        max_age: Edad máxima (ej: 28)
        table_type: Tipo de tabla ('domestic', 'european', 'extras')
        additional_filters: Filtros SQL adicionales (ej: "AND team = 'Barcelona'")

    Returns:
        DataFrame con columnas: unique_player_id, player_name, team, league,
                               season, position, fbref_metrics, understat_metrics,
                               transfermarkt_metrics

    Raises:
        ValueError: Si league/season inválidos o positions no válidas

    Example:
        >>> pool = query_player_pool(
        ...     'ESP-La Liga', '2425',
        ...     positions=['LW', 'RW'],
        ...     max_market_value=50_000_000,
        ...     min_minutes=500,
        ...     min_age=18,
        ...     max_age=28
        ... )
    """
    # Validar table_type
    valid_tables = {'domestic', 'european', 'extras'}
    if table_type not in valid_tables:
        raise ValueError(f"table_type must be one of {valid_tables}")

    # Determinar nombre de tabla
    if table_type == 'domestic':
        table_name = 'footballdecoded.players_domestic'
        field_name = 'league'
    elif table_type == 'european':
        table_name = 'footballdecoded.players_european'
        field_name = 'competition'
    else:  # extras
        table_name = 'footballdecoded.players_extras'
        field_name = 'league'

    # Construir query base
    query_parts = [f"""
        SELECT unique_player_id, player_name, team, {field_name} as league,
               season, position, age,
               fbref_metrics, understat_metrics, transfermarkt_metrics
        FROM {table_name}
        WHERE {field_name} = :league
          AND season = :season
    """]

    params = {'league': league, 'season': season}

    # Filtro de posiciones (Transfermarkt)
    if positions is not None:
        if isinstance(positions, str):
            positions = [positions]

        # Validar que sean posiciones válidas
        all_positions = POSITIONS['ALL']
        for pos in positions:
            if pos not in all_positions:
                raise ValueError(
                    f"Invalid position '{pos}'. Must be one of: {all_positions}"
                )

        query_parts.append(
            "  AND transfermarkt_metrics->>'transfermarkt_position_specific' = ANY(:positions)"
        )
        params['positions'] = positions

    # Filtro de valor de mercado (usar ::numeric porque valor es string con decimales)
    if max_market_value is not None:
        query_parts.append(
            "  AND (transfermarkt_metrics->>'transfermarkt_market_value_eur')::numeric <= :max_value"
        )
        params['max_value'] = max_market_value

    # Filtro de minutos mínimos
    if min_minutes > 0:
        query_parts.append(
            "  AND (fbref_metrics->>'minutes_played')::float >= :min_minutes"
        )
        params['min_minutes'] = min_minutes

    # Filtro de edad mínima
    if min_age is not None:
        query_parts.append(
            "  AND age >= :min_age"
        )
        params['min_age'] = min_age

    # Filtro de edad máxima
    if max_age is not None:
        query_parts.append(
            "  AND age <= :max_age"
        )
        params['max_age'] = max_age

    # Filtros adicionales
    if additional_filters:
        query_parts.append(f"  {additional_filters}")

    # Ordenar
    query_parts.append("ORDER BY team, player_name")

    query_str = '\n'.join(query_parts)

    # Ejecutar query
    db = get_db_manager()
    try:
        df = pd.read_sql(text(query_str), db.engine, params=params)
    finally:
        db.close()

    if len(df) == 0:
        print(f"WARNING: No players found with filters:")
        print(f"  League: {league}, Season: {season}")
        if positions:
            print(f"  Positions: {positions}")
        if max_market_value:
            print(f"  Max market value: {max_market_value:,} EUR")
        if min_minutes > 0:
            print(f"  Min minutes: {min_minutes}")
        if min_age is not None:
            print(f"  Min age: {min_age}")
        if max_age is not None:
            print(f"  Max age: {max_age}")

    return df


def query_single_player(
    player_name: str,
    league: str,
    season: str,
    team: Optional[str] = None,
    table_type: str = 'domestic'
) -> pd.DataFrame:
    """
    Query jugador único (útil para añadir target exógeno).

    Args:
        player_name: Nombre del jugador (parcial, case-insensitive)
        league: Liga del jugador
        season: Temporada del jugador
        team: Equipo (requerido si hay múltiples coincidencias)
        table_type: Tipo de tabla ('domestic', 'european', 'extras')

    Returns:
        DataFrame con 1 fila (mismo schema que query_player_pool)

    Raises:
        ValueError: Si no se encuentra jugador
        ValueError: Si múltiples coincidencias y team=None

    Example:
        >>> player = query_single_player('Vinicius', 'ESP-La Liga', '2324', 'Real Madrid')
    """
    # Validar table_type
    valid_tables = {'domestic', 'european', 'extras'}
    if table_type not in valid_tables:
        raise ValueError(f"table_type must be one of {valid_tables}")

    # Determinar nombre de tabla
    if table_type == 'domestic':
        table_name = 'footballdecoded.players_domestic'
        field_name = 'league'
    elif table_type == 'european':
        table_name = 'footballdecoded.players_european'
        field_name = 'competition'
    else:  # extras
        table_name = 'footballdecoded.players_extras'
        field_name = 'league'

    # Construir query (ILIKE para case-insensitive)
    query_str = f"""
        SELECT unique_player_id, player_name, team, {field_name} as league,
               season, position, age,
               fbref_metrics, understat_metrics, transfermarkt_metrics
        FROM {table_name}
        WHERE {field_name} = :league
          AND season = :season
          AND player_name ILIKE :player_name
    """

    params = {
        'league': league,
        'season': season,
        'player_name': f'%{player_name}%'
    }

    if team is not None:
        query_str += " AND team = :team"
        params['team'] = team

    # Ejecutar query
    db = get_db_manager()
    try:
        df = pd.read_sql(text(query_str), db.engine, params=params)
    finally:
        db.close()

    # Validar resultados
    if len(df) == 0:
        raise ValueError(
            f"Player '{player_name}' not found in {league} {season}" +
            (f" for team '{team}'" if team else "")
        )

    if len(df) > 1 and team is None:
        teams = df['team'].unique().tolist()
        raise ValueError(
            f"Multiple players found for '{player_name}' in {league} {season}.\n"
            f"Specify team parameter. Available teams: {teams}"
        )

    return df


def add_exogenous_player(
    pool_df: pd.DataFrame,
    player_name: str,
    league: str,
    season: str,
    team: Optional[str] = None,
    table_type: str = 'domestic'
) -> pd.DataFrame:
    """
    Añade jugador exógeno (de otra liga/temporada) al DataFrame de pool.

    IMPORTANTE: Se añade ANTES de extract_metrics() y normalización per90.

    Args:
        pool_df: DataFrame del pool (de query_player_pool)
        player_name: Nombre del jugador a añadir
        league: Liga del jugador exógeno
        season: Temporada del jugador exógeno
        team: Equipo (requerido si múltiples coincidencias)
        table_type: Tipo de tabla del jugador exógeno

    Returns:
        DataFrame concatenado [pool + target exógeno] con índices reseteados

    Raises:
        ValueError: Si jugador no encontrado
        ValueError: Si columnas incompatibles

    Example:
        >>> pool = query_player_pool('ESP-La Liga', '2425', ['LW', 'RW'])
        >>> full_df = add_exogenous_player(pool, 'Vinicius', 'ESP-La Liga', '2324', 'Real Madrid')
    """
    # Query jugador exógeno
    player_df = query_single_player(player_name, league, season, team, table_type)

    # Validar que columnas sean compatibles
    pool_cols = set(pool_df.columns)
    player_cols = set(player_df.columns)

    if pool_cols != player_cols:
        missing_in_player = pool_cols - player_cols
        missing_in_pool = player_cols - pool_cols

        error_msg = "Column mismatch between pool and exogenous player:\n"
        if missing_in_player:
            error_msg += f"  Missing in player: {missing_in_player}\n"
        if missing_in_pool:
            error_msg += f"  Missing in pool: {missing_in_pool}\n"

        raise ValueError(error_msg)

    # Concatenar
    full_df = pd.concat([pool_df, player_df], ignore_index=True)

    print(f"Added exogenous player: {player_df.iloc[0]['player_name']} "
          f"({player_df.iloc[0]['team']}, {player_df.iloc[0]['league']} {player_df.iloc[0]['season']})")
    print(f"Total players in DataFrame: {len(full_df)}")

    return full_df


def validate_required_metrics(
    df: pd.DataFrame,
    target_player_id: str,
    required_fbref: Optional[List[str]] = None,
    required_understat: Optional[List[str]] = None,
    raise_on_missing: bool = True
) -> Dict[str, List[str]]:
    """
    Valida que el target tenga métricas requeridas (DESPUÉS de extract_metrics).

    Args:
        df: DataFrame procesado (YA con extract_metrics aplicado, columnas expandidas)
        target_player_id: unique_player_id del target
        required_fbref: Lista de columnas FBref requeridas (ej: ['goals', 'assists'])
        required_understat: Lista de columnas Understat requeridas (ej: ['understat_xg'])
        raise_on_missing: Si True, raise ValueError. Si False, solo retorna dict.

    Returns:
        Dict con métricas faltantes: {'fbref_missing': [...], 'understat_missing': [...]}

    Raises:
        ValueError: Si raise_on_missing=True y hay métricas faltantes

    Example:
        >>> validate_required_metrics(
        ...     df_final, target_id,
        ...     required_fbref=['goals', 'assists', 'shots'],
        ...     required_understat=['understat_xg']
        ... )
    """
    # Validar que target existe
    if target_player_id not in df['unique_player_id'].values:
        raise ValueError(f"Target player '{target_player_id}' not found in DataFrame")

    target_row = df[df['unique_player_id'] == target_player_id].iloc[0]

    missing = {
        'fbref_missing': [],
        'understat_missing': []
    }

    # Validar FBref
    if required_fbref:
        for metric in required_fbref:
            if metric not in df.columns:
                missing['fbref_missing'].append(f"{metric} (column not in DataFrame)")
            elif pd.isna(target_row[metric]):
                missing['fbref_missing'].append(f"{metric} (value is NaN)")

    # Validar Understat
    if required_understat:
        for metric in required_understat:
            if metric not in df.columns:
                missing['understat_missing'].append(f"{metric} (column not in DataFrame)")
            elif pd.isna(target_row[metric]):
                missing['understat_missing'].append(f"{metric} (value is NaN)")

    # Si hay missing y raise_on_missing=True, error
    total_missing = len(missing['fbref_missing']) + len(missing['understat_missing'])

    if total_missing > 0 and raise_on_missing:
        error_msg = f"\n{'='*60}\n"
        error_msg += f"ERROR: Target missing {total_missing} required metrics\n"
        error_msg += f"{'='*60}\n"

        if missing['fbref_missing']:
            error_msg += f"\nFBref missing ({len(missing['fbref_missing'])}):\n"
            for m in missing['fbref_missing']:
                error_msg += f"  - {m}\n"

        if missing['understat_missing']:
            error_msg += f"\nUnderstat missing ({len(missing['understat_missing'])}):\n"
            for m in missing['understat_missing']:
                error_msg += f"  - {m}\n"

        error_msg += f"\nPossible causes:\n"
        error_msg += f"  1. Target from incompatible league/season\n"
        error_msg += f"  2. Target has insufficient playing time\n"
        error_msg += f"  3. extract_metrics() filtered out columns\n"
        error_msg += f"\nSolutions:\n"
        error_msg += f"  - Check target league has data coverage\n"
        error_msg += f"  - Verify target has min_minutes >= 300\n"
        error_msg += f"  - Review extract_metrics() thresholds\n"
        error_msg += f"{'='*60}"

        raise ValueError(error_msg)

    return missing
