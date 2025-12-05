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


def validate_replacement(
    vendido_name: str,
    reemplazo_name: str,
    season: str,
    positions: List[str],
    vendido_team: Optional[str] = None,
    reemplazo_team: Optional[str] = None,
    max_market_value: int = 30_000_000,
    max_age: int = 30,
    min_minutes: int = 1250,
    n_similar: int = 30,
    pca_variance: float = 0.85,
    robust_scaling: bool = False
) -> Dict:
    """
    Wrapper completo para validar sustitución de jugadores.

    Ejecuta todo el pipeline:
    1. Query pool con filtros Transfermarkt
    2. Añadir jugador vendido como exógeno si necesario
    3. Extraer métricas JSONB a columnas
    4. Calcular métricas per90
    5. Ejecutar PCA + Cosine Similarity
    6. Devolver resultado con validación

    Args:
        vendido_name: Nombre del jugador vendido
        reemplazo_name: Nombre del reemplazo
        season: Temporada de análisis (formato '2324', '2425', etc.)
        positions: Lista de posiciones Transfermarkt (['LW', 'RW'], ['CB'], etc.)
        vendido_team: Equipo del vendido (si múltiples coincidencias)
        reemplazo_team: Equipo del reemplazo (si múltiples coincidencias)
        max_market_value: Valor máximo mercado en EUR (default: 30M)
        max_age: Edad máxima (default: 30)
        min_minutes: Minutos mínimos (default: 1250)
        n_similar: Número de similares a devolver (default: 30)
        pca_variance: Varianza PCA (default: 0.85)
        robust_scaling: Usar RobustScaler (default: False)

    Returns:
        Dict con resultado de find_similar_players_cosine:
        - target_info: Info del jugador vendido
        - replacement_info: Info y ranking del reemplazo
        - similar_players: DataFrame con TOP-N
        - score_distribution: Estadísticas de similitud
        - pca_info: Información PCA
        - metadata: Metadata del proceso

    Raises:
        ValueError: Si jugadores no encontrados o datos insuficientes

    Example:
        >>> result = validate_replacement(
        ...     vendido_name='Pau Torres',
        ...     reemplazo_name='Logan Costa',
        ...     season='2324',
        ...     positions=['CB'],
        ...     max_market_value=30_000_000,
        ...     max_age=30,
        ...     min_minutes=1250
        ... )
        >>> print(result['replacement_info']['validation_status'])
        'VALIDADO'
    """
    import numpy as np
    from tfm.algorithms import find_similar_players_cosine

    # Helper para extraer métricas JSONB
    def _extract_metrics(df, col_name):
        result = pd.DataFrame(index=df.index)
        all_keys = set()
        for _, row in df.iterrows():
            if isinstance(row[col_name], dict):
                all_keys.update(row[col_name].keys())

        for key in all_keys:
            values = []
            for _, row in df.iterrows():
                if isinstance(row[col_name], dict) and key in row[col_name]:
                    raw_value = row[col_name][key]
                    converted_value = _convert_to_float(raw_value)
                    values.append(converted_value)
                else:
                    values.append(np.nan)

            valid_count = pd.Series(values).notna().sum()
            if valid_count >= 5:
                result[key] = values

        return result

    # Helper para convertir a float
    def _convert_to_float(value):
        if isinstance(value, (int, float)):
            return float(value)
        if value is None or pd.isna(value):
            return np.nan
        if isinstance(value, str):
            if value.strip() == '' or value.lower().strip() in ['nan', 'none', 'null', '-']:
                return np.nan
            try:
                return float(value)
            except (ValueError, TypeError):
                return np.nan
        return np.nan

    print(f"\n{'='*80}")
    print(f"VALIDACIÓN: {vendido_name} → {reemplazo_name}")
    print(f"{'='*80}")

    # 1. Query pool de todas las Big 5
    print(f"\n1. Query pool (season={season}, positions={positions})")

    big5_leagues = [
        'ENG-Premier League',
        'ESP-La Liga',
        'ITA-Serie A',
        'GER-Bundesliga',
        'FRA-Ligue 1'
    ]

    pools = []
    for league in big5_leagues:
        try:
            league_pool = query_player_pool(
                league=league,
                season=season,
                positions=positions,
                max_market_value=max_market_value,
                max_age=max_age,
                min_minutes=min_minutes,
                table_type='domestic'
            )
            if len(league_pool) > 0:
                pools.append(league_pool)
        except Exception as e:
            print(f"   WARNING: {league} error: {e}")

    if len(pools) == 0:
        raise ValueError("No players found in Big 5 leagues with specified filters")

    pool = pd.concat(pools, ignore_index=True)
    print(f"   Pool: {len(pool)} jugadores (Big 5)")

    # 2. Buscar vendido en pool
    vendido_in_pool = pool[pool['player_name'].str.contains(vendido_name, case=False, na=False)]
    if vendido_team:
        vendido_in_pool = vendido_in_pool[vendido_in_pool['team'] == vendido_team]

    if len(vendido_in_pool) == 0:
        print(f"   Target '{vendido_name}' no en pool, añadiendo como exógeno")
        # Buscar en otras ligas/temporadas
        try:
            full_df = add_exogenous_player(pool, vendido_name, 'ESP-La Liga', season, vendido_team)
        except ValueError:
            raise ValueError(f"Target '{vendido_name}' no encontrado en BD")
    else:
        print(f"   Target '{vendido_name}' ya en pool")
        full_df = pool

    # 3. Buscar reemplazo en pool
    reemplazo_rows = full_df[full_df['player_name'].str.contains(reemplazo_name, case=False, na=False)]
    if reemplazo_team:
        reemplazo_rows = reemplazo_rows[reemplazo_rows['team'] == reemplazo_team]

    if len(reemplazo_rows) == 0:
        raise ValueError(f"Reemplazo '{reemplazo_name}' no encontrado en pool")
    elif len(reemplazo_rows) > 1:
        teams = reemplazo_rows['team'].unique().tolist()
        raise ValueError(
            f"Múltiples '{reemplazo_name}' encontrados: {teams}. "
            f"Especificar reemplazo_team"
        )

    vendido_id = vendido_in_pool.iloc[0]['unique_player_id'] if len(vendido_in_pool) > 0 else \
                 full_df[full_df['player_name'].str.contains(vendido_name, case=False, na=False)].iloc[0]['unique_player_id']
    reemplazo_id = reemplazo_rows.iloc[0]['unique_player_id']

    print(f"   Vendido ID: {vendido_id}")
    print(f"   Reemplazo ID: {reemplazo_id}")

    # 4. Extraer métricas JSONB
    print(f"\n2. Extraer métricas JSONB")
    fbref_df = _extract_metrics(full_df, 'fbref_metrics')
    understat_df = _extract_metrics(full_df, 'understat_metrics')
    transfermarkt_df = _extract_metrics(full_df, 'transfermarkt_metrics')

    print(f"   FBref: {len(fbref_df.columns)} columnas")
    print(f"   Understat: {len(understat_df.columns)} columnas")
    print(f"   Transfermarkt: {len(transfermarkt_df.columns)} columnas")

    # 5. Calcular per90
    print(f"\n3. Calcular métricas per90")

    exclude_per90 = {
        'minutes_played', 'age', 'birth_year', 'games_started', 'minutes_per_game',
        'minutes_per_start', 'games', 'games_subs', 'unused_sub', 'points_per_game',
        'on_goals_for', 'on_goals_against', 'plus_minus', 'plus_minus_per90',
        'plus_minus_wowy', 'on_xg_for', 'on_xg_against', 'xg_plus_minus',
        'xg_plus_minus_per90', 'xg_plus_minus_wowy'
    }

    fbref_nums = fbref_df.select_dtypes(include=[np.number])
    understat_nums = understat_df.select_dtypes(include=[np.number])

    fbref_per90 = fbref_nums.loc[:, ~fbref_nums.columns.isin(exclude_per90)]
    fbref_per90 = (fbref_per90.div(fbref_nums['minutes_played'], axis=0) * 90).round(3)
    fbref_per90.columns = [f'{col}_per90' for col in fbref_per90.columns]

    understat_per90 = understat_nums.loc[:, ~understat_nums.columns.isin(exclude_per90)]
    understat_per90 = (understat_per90.div(fbref_nums['minutes_played'], axis=0) * 90).round(3)
    understat_per90.columns = [f'{col}_per90' for col in understat_per90.columns]

    print(f"   FBref per90: {len(fbref_per90.columns)} columnas")
    print(f"   Understat per90: {len(understat_per90.columns)} columnas")

    # 6. Concatenar todo
    df_final = pd.concat([
        full_df[['unique_player_id', 'player_name', 'team', 'league', 'season', 'position']],
        fbref_df,
        understat_df,
        transfermarkt_df,
        fbref_per90,
        understat_per90
    ], axis=1)

    print(f"   DataFrame final: {len(df_final)} filas x {len(df_final.columns)} columnas")

    # 7. Ejecutar algoritmo
    print(f"\n4. Ejecutar PCA + Cosine Similarity")
    result = find_similar_players_cosine(
        df=df_final,
        target_player_id=vendido_id,
        n_similar=n_similar,
        pca_variance=pca_variance,
        return_all_scores=False,
        replacement_id=reemplazo_id,
        robust_scaling=robust_scaling
    )

    print(f"\n{'='*80}")
    print(f"RESULTADO")
    print(f"{'='*80}")
    print(f"Reemplazo: {result['replacement_info']['player_name']}")
    print(f"Posición: #{result['replacement_info']['rank']}")
    print(f"Similitud: {result['replacement_info']['cosine_similarity']:.4f}")
    print(f"Status: {result['replacement_info']['validation_status']}")
    print(f"{'='*80}\n")

    return result
