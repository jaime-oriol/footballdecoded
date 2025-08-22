# FootballDecoded Wrappers - Documentación Técnica Completa

## Tabla de Contenidos
1. [FBref Wrapper](#fbref-wrapper)
2. [Understat Wrapper](#understat-wrapper)
3. [WhoScored Wrapper](#whoscored-wrapper)

---

# FBref Wrapper

El wrapper de FBref proporciona una interfaz simplificada y optimizada para extraer todas las estadísticas disponibles en FBref para jugadores y equipos, con soporte para fuzzy matching, manejo inteligente de caracteres especiales y normalización automática de datos.

## 1. fbref_extract_data()

### Descripción
Función principal del wrapper. Extrae todas las estadísticas disponibles en FBref para cualquier jugador o equipo.

### Sintaxis
```python
fbref_extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False
) -> Optional[Dict]
```

### Parámetros
- **entity_name** (str): Nombre del jugador o equipo. Soporta fuzzy matching, case-insensitive, maneja caracteres especiales
- **entity_type** (str): `"player"` o `"team"`
- **league** (str): Formato `"PAÍS-NombreLiga"` (ej: `"ENG-Premier League"`, `"ESP-La Liga"`)
- **season** (str): Formato `"YYYY-YY"` (ej: `"2023-24"`)
- **match_id** (str, opcional): 8 caracteres hexadecimales. Solo válido con `entity_type="player"`
- **include_opponent_stats** (bool, opcional): Solo válido con `entity_type="team"`. Añade ~190 campos adicionales

### Retorno

#### Para Jugadores (153 campos)
Tipo: `Dict[str, Union[str, int, float]]` o `None`

##### Grupos de campos:

**Identificación y Metadata (7 campos)**
```python
{
    'player_name': str,              # Nombre usado en búsqueda
    'normalized_name': str,          # Versión normalizada (clave única)
    'fbref_official_name': str,      # Nombre completo oficial FBref
    'team': str,                     # Equipo actual
    'league': str,                   # Liga (formato estándar)
    'season': str,                   # Temporada formato interno FBref
    'url': str                       # URL relativa en FBref
}
```

**Información Personal (4 campos)**
```python
{
    'nationality': str,              # Código ISO-3 del país
    'position': str,                 # "GK", "DF", "MF", "FW" (puede ser múltiple)
    'age': int,                      # Edad actual en años
    'birth_year': int                # Año de nacimiento
}
```

**Participación y Tiempo de Juego (11 campos)**
```python
{
    'matches_played': int,           # Partidos participados
    'matches_started': int,          # Partidos como titular
    'minutes_played': int,           # Total minutos jugados
    'full_matches_equivalent': float,# Equivalente en partidos de 90min
    'minutes_per_match': int,        # Media minutos por partido
    'Starts_Starts': int,            # Duplicado matches_started
    'Starts_Compl': int,             # Partidos completos (90 min)
    'Starts_Mn/Start': int,          # Minutos promedio como titular
    'Subs_Subs': int,                # Veces que entró de suplente
    'Subs_Mn/Sub': int,              # Minutos promedio como suplente
    'Subs_unSub': int                # Veces no utilizado en banquillo
}
```

**Producción de Goles (12 campos)**
```python
{
    'goals': int,                    # Total goles marcados
    'non_penalty_goals': int,        # Goles sin penales
    'penalty_goals': int,            # Goles de penal
    'penalty_attempts': int,         # Penales lanzados
    'Goals_FK': int,                 # Goles de tiro libre directo
    'Goals_CK': int,                 # Goles de córner directo
    'Goals_OG': int,                 # Autogoles provocados
    'goals_per_shot': float,         # Ratio goles/disparos totales
    'goals_per_shot_on_target': float, # Ratio goles/disparos a puerta
    'goals_per90': float,            # Goles por 90 minutos
    'PKcon': int,                    # Penales concedidos al rival
    'PKwon': int                     # Penales ganados para el equipo
}
```

**Expected Goals - xG (7 campos)**
```python
{
    'expected_goals': float,         # xG total acumulado
    'non_penalty_expected_goals': float, # xG sin penales
    'G-xG': float,                   # Diferencia goles reales vs esperados
    'np:G-xG': float,                # Diferencia sin penales
    'expected_goals_per90': float,   # xG por 90 minutos
    'np_expected_goals_per90': float,# npxG por 90 minutos
    'npxG/Sh': float                 # xG promedio por disparo sin penales
}
```

**Disparos (10 campos)**
```python
{
    'shots': int,                    # Total disparos intentados
    'shots_on_target': int,          # Disparos a puerta
    'shots_on_target_pct': float,    # % disparos a puerta
    'shots_per_90': float,           # Disparos por 90 minutos
    'shots_on_target_per90': float,  # Disparos a puerta por 90
    'avg_shot_distance': float,      # Distancia media en yardas
    'shots_free_kicks': int,         # Disparos de tiro libre
    'shots_on_target_free_kicks': int, # Tiros libres a puerta
    'FK': int,                       # Duplicado shots_free_kicks
    'npxG_per_shot': float           # Duplicado npxG/Sh
}
```

**Asistencias y Creación (9 campos)**
```python
{
    'assists': int,                  # Asistencias oficiales
    'expected_assists': float,       # Expected Assists
    'expected_assists_alt': float,   # xA método alternativo
    'A-xAG': float,                  # Diferencia asistencias reales vs esperadas
    'goals_plus_assists': int,       # Goles + Asistencias
    'G+A-PK': int,                   # G+A sin goles de penal
    'key_passes': int,               # Pases que llevan a disparo
    'xG+xAG': float,                 # (xG + xA) por 90 minutos
    'non_penalty_xG_plus_xAG': float # npxG + xA por 90
}
```

**Goal & Shot Creating Actions (16 campos)**
```python
{
    'GCA_GCA': int,                  # Acciones que llevan a gol (2 jugadas)
    'GCA_GCA90': float,              # GCA por 90 minutos
    'GCA Types_PassLive': int,       # GCA desde pase en juego
    'GCA Types_PassDead': int,       # GCA desde balón parado
    'GCA Types_TO': int,             # GCA por turnover
    'GCA Types_Sh': int,             # GCA por rebote disparo
    'GCA Types_Fld': int,            # GCA por falta sufrida
    'GCA Types_Def': int,            # GCA por acción defensiva
    'SCA_SCA': int,                  # Acciones que llevan a disparo
    'SCA_SCA90': float,              # SCA por 90 minutos
    'SCA Types_PassLive': int,       # SCA desde pase en juego
    'SCA Types_PassDead': int,       # SCA desde balón parado
    'SCA Types_TO': int,             # SCA por turnover
    'SCA Types_Sh': int,             # SCA por rebote disparo
    'SCA Types_Fld': int,            # SCA por falta sufrida
    'SCA Types_Def': int             # SCA por acción defensiva
}
```

**Pases - Volumen y Distancia (19 campos)**
```python
{
    'passes_completed': int,         # Pases completados
    'passes_attempted': int,         # Total pases intentados
    'pass_completion_pct': float,    # % éxito en pases
    'total_pass_distance': int,      # Distancia total en yardas
    'progressive_pass_distance': int,# Distancia pases progresivos
    'Passes_AvgLen': float,          # Longitud media en yardas
    'passes_final_third': int,       # Pases completados al tercio final
    'passes_penalty_area': int,      # Pases completados al área
    'crosses_penalty_area': int,     # Centros completados al área
    'progressive_passes': int,       # Pases que avanzan 10+ yardas
    'Passes_Thr': int,               # Through balls
    'Launched_Cmp': int,             # Pases largos completados
    'Launched_Att': int,             # Pases largos intentados
    'Launched_Cmp%': float,          # % éxito pases largos
    'Cmp': int,                      # Duplicado passes_completed
    'Att': int,                      # Duplicado passes_attempted
    'Cmp%': float,                   # Duplicado pass_completion_pct
    'TotDist': int,                  # Duplicado total_pass_distance
    'PrgDist': int                   # Duplicado progressive_pass_distance
}
```

**Pases por Tipo y Distancia (19 campos)**
```python
{
    'passes_completed_short': int,   # Pases cortos (5-15y) completados
    'passes_attempted_short': int,   # Pases cortos intentados
    'pass_completion_pct_short': float, # % éxito pases cortos
    'passes_completed_medium': int,  # Pases medios (15-30y) completados
    'passes_attempted_medium': int,  # Pases medios intentados
    'pass_completion_pct_medium': float, # % éxito pases medios
    'passes_completed_long': int,    # Pases largos (>30y) completados
    'passes_attempted_long': int,    # Pases largos intentados
    'pass_completion_pct_long': float, # % éxito pases largos
    'Pass Types_Live': int,          # Pases en juego abierto
    'Pass Types_Dead': int,          # Pases desde balón parado
    'Pass Types_FK': int,            # Pases de tiro libre
    'Pass Types_TB': int,            # Through balls
    'Pass Types_Sw': int,            # Switches (cambios orientación)
    'Pass Types_Crs': int,           # Centros totales
    'Pass Types_CK': int,            # Córners lanzados
    'Pass Types_TI': int,            # Saques de banda
    'Crs': int,                      # Duplicado Pass Types_Crs
    'CrsPA': int                     # Duplicado crosses_penalty_area
}
```

**Posesión - Toques (7 campos)**
```python
{
    'Touches_Touches': int,          # Total toques del balón
    'Touches_Live': int,             # Toques en juego vivo
    'Touches_Def Pen': int,          # Toques en área propia
    'Touches_Def 3rd': int,          # Toques en tercio defensivo
    'Touches_Mid 3rd': int,          # Toques en tercio medio
    'Touches_Att 3rd': int,          # Toques en tercio ofensivo
    'Touches_Att Pen': int           # Toques en área rival
}
```

**Posesión - Conducciones (11 campos)**
```python
{
    'Carries_Carries': int,          # Número de conducciones
    'Carries_TotDist': int,          # Distancia total conduciendo
    'Carries_PrgDist': int,          # Distancia progresiva conduciendo
    'Carries_PrgC': int,             # Conducciones progresivas
    'Carries_1/3': int,              # Conducciones al tercio final
    'Carries_CPA': int,              # Conducciones al área
    'Carries_Mis': int,              # Miscontrols
    'Carries_Dis': int,              # Veces desposeído
    'miscontrols': int,              # Duplicado Carries_Mis
    'dispossessed': int,             # Duplicado Carries_Dis
    'Progression_PrgC': int          # Duplicado Carries_PrgC
}
```

**Posesión - Recepciones (4 campos)**
```python
{
    'Receiving_Rec': int,            # Total recepciones
    'Receiving_PrgR': int,           # Recepciones progresivas
    'Progression_PrgR': int,         # Duplicado
    'Rec': int                       # Duplicado Receiving_Rec
}
```

**Regates/Take-Ons (8 campos)**
```python
{
    'Take-Ons_Att': int,             # Regates intentados
    'Take-Ons_Succ': int,            # Regates exitosos
    'Take-Ons_Succ%': float,         # % éxito regates
    'Take-Ons_Tkld': int,            # Veces tackleado en regate
    'Take-Ons_Tkld%': float,         # % veces tackleado
    'successful_take_ons': int,      # Duplicado Take-Ons_Succ
    'take_on_success_pct': float,    # Duplicado Take-Ons_Succ%
    'Att': int                       # Contexto: regates o tackles
}
```

**Duelos Aéreos (4 campos)**
```python
{
    'Aerial Duels_Won': int,         # Duelos aéreos ganados
    'Aerial Duels_Lost': int,        # Duelos aéreos perdidos
    'Aerial Duels_Won%': float,      # % victoria aéreos
    'Won': int                       # Total duelos ganados (incluye terrestres)
}
```

**Defensa - Tackles (9 campos)**
```python
{
    'Tackles_Tkl': int,              # Total tackles realizados
    'Tackles_TklW': int,             # Tackles exitosos
    'tackles': int,                  # Duplicado Tackles_Tkl
    'tackles_won': int,              # Duplicado Tackles_TklW
    'Tackles_Def 3rd': int,          # Tackles en tercio defensivo
    'Tackles_Mid 3rd': int,          # Tackles en tercio medio
    'Tackles_Att 3rd': int,          # Tackles en tercio ofensivo
    'Challenges_Tkl': int,           # Tackles en duelos 1v1
    'Challenges_Att': int            # Desafíos defensivos intentados
}
```

**Defensa - Intercepciones y Bloqueos (10 campos)**
```python
{
    'interceptions': int,            # Balones interceptados
    'Int': int,                      # Duplicado
    'Tkl+Int': int,                  # Suma tackles + intercepciones
    'Blocks_Blocks': int,            # Total bloqueos
    'Blocks_Sh': int,                # Disparos bloqueados
    'Blocks_Pass': int,              # Pases bloqueados
    'clearances': int,               # Despejes realizados
    'Clr': int,                      # Duplicado
    'errors': int,                   # Errores que llevan a disparo rival
    'Err': int                       # Duplicado
}
```

**Disciplina y Faltas (9 campos)**
```python
{
    'yellow_cards': int,             # Tarjetas amarillas
    'red_cards': int,                # Tarjetas rojas directas
    '2CrdY': int,                    # Dobles amarillas
    'CrdY': int,                     # Duplicado yellow_cards
    'CrdR': int,                     # Duplicado red_cards
    'Fls': int,                      # Faltas cometidas
    'Fld': int,                      # Faltas recibidas
    'Off': int,                      # Veces en fuera de juego
    'Recov': int                     # Balones recuperados
}
```

**Impacto en Equipo - Resultados (11 campos)**
```python
{
    'Team Success_onG': int,         # Goles del equipo con jugador en campo
    'Team Success_onGA': int,        # Goles en contra con jugador
    'Team Success_+/-': int,         # Diferencia con jugador
    'Team Success_+/-90': float,     # Diferencial por 90 minutos
    'Team Success_PPM': float,       # Puntos por partido
    'Team Success_On-Off': float,    # Diferencial con/sin jugador
    'wins': float,                   # Victorias cuando juega
    'draws': float,                  # Empates cuando juega
    'losses': float,                 # Derrotas cuando juega
    'goals_against': float,          # Goles en contra totales
    'W': int                         # Duplicado wins como int
}
```

**Impacto en Equipo - Expected (6 campos)**
```python
{
    'Team Success (xG)_onxG': float, # xG del equipo con jugador
    'Team Success (xG)_onxGA': float,# xG en contra con jugador
    'Team Success (xG)_xG+/-': float,# Diferencia xG con jugador
    'Team Success (xG)_xG+/-90': float,# Diferencial xG por 90
    'Team Success (xG)_On-Off': float,# Diferencial xG con/sin jugador
}
```

**Métricas de Portero (14 campos)**
```python
{
    'GA': int,                       # Goles encajados (0 para jugadores campo)
    'GA90': float,                   # Goles encajados por 90
    'SoTA': int,                     # Disparos a puerta enfrentados
    'Saves': int,                    # Paradas realizadas
    'Save%': float,                  # % paradas
    'CS': int,                       # Clean sheets
    'CS%': float,                    # % partidos sin encajar
    'PSxG': float,                   # Post-Shot Expected Goals
    'PSxG+/-': float,                # Rendimiento vs PSxG
    'PSxG/SoT': float,               # PSxG por disparo
    'PKsv': int,                     # Penales parados
    'PKA': int,                      # Penales enfrentados
    'Penalty Kicks_Save%': float,    # % penales parados
    'Sweeper_#OPA': int              # Acciones fuera del área
}
```

**Métricas Agregadas (13 campos)**
```python
{
    'OG': int,                       # Autogoles propios
    'Corner Kicks_In': int,          # Corners a favor provocados
    'Corner Kicks_Out': int,         # Corners concedidos
    'Progression_PrgP': int,         # Total pases progresivos
    'Min%': float,                   # % minutos disponibles jugados
    'Mn/MP': int,                    # Minutos promedio por partido
    'compl': int,                    # Partidos completos
    'playing_time_90s': float,       # Equivalente partidos 90min
    'touches': int,                  # Duplicado Touches_Touches
    'Lost': int,                     # Duelos perdidos totales
    'Won%': float,                   # % duelos ganados totales
    'url': str,                      # URL (condicional)
    'game': str                      # Descripción partido (si match_id)
}
```

#### Para Equipos (190 campos base + 190 opponent si include_opponent_stats=True)

Incluye todos los campos de jugador agregados para el equipo completo, más:

**Campos Exclusivos de Equipo (37 campos)**
```python
{
    # IDENTIFICACIÓN
    'team_name': str,                # Nombre usado en búsqueda
    'official_team_name': str,       # Nombre oficial FBref
    
    # RESULTADOS LIGA
    'wins': int, 'draws': int, 'losses': int,  # Resultados totales
    'points': int,                   # Puntos en liga
    'Pts': int,                      # Duplicado
    'Pts/MP': float,                 # Puntos por partido
    'xPts': float,                   # Puntos esperados según xG
    'W': int, 'D': int, 'L': int,   # Duplicados
    
    # GOLES EQUIPO
    'goals_for': int, 'goals_against': int, 'goal_difference': int,
    'GF': int, 'GA': int, 'GD': int,  # Duplicados
    
    # EXPECTED GOALS EQUIPO
    'expected_goals_for': float, 'expected_goals_against': float,
    'xGF': float, 'xGA': float,      # Duplicados
    
    # POSESIÓN
    'Poss': float,                   # % posesión media
    
    # PORTERÍA EQUIPO (12 campos)
    'CS': int,                       # Clean sheets
    'CS%': float,                    # % partidos sin encajar
    'Save%': float,                  # % paradas del portero
    'Saves': int,                    # Total paradas
    'SoTA': int,                     # Tiros a puerta contra
    'SoT/90': float,                 # Tiros enfrentados por 90
    'PSxG': float,                   # Post-Shot xG total
    'PSxG+/-': float,                # Rendimiento porteros
    'PSxG/SoT': float,               # PSxG por tiro
    'Penalty Kicks_Save%': float,    # % penales parados
    'Penalty Kicks_PKsv': int,       # Penales parados
    'Penalty Kicks_PKA': int,        # Penales enfrentados
    
    # DISTRIBUCIÓN PORTERO (8 campos)
    'Launched_Att': int,             # Pases largos portero
    'Launched_Cmp': int,             # Completados
    'Launched_Cmp%': float,          # % éxito
    'Passes_Att (GK)': int,          # Total pases portero
    'Passes_Launch%': float,         # % que son largos
    'Goal Kicks_Att': int,           # Saques de puerta
    'Goal Kicks_Launch%': float,     # % saques largos
    'Goal Kicks_AvgLen': float,      # Distancia media
    
    # ACCIONES PORTERO (3 campos)
    'Sweeper_#OPA': int,             # Acciones fuera del área
    'Sweeper_#OPA/90': float,        # Por 90 minutos
    'Sweeper_AvgDist': float,        # Distancia media OPA
    
    # PLANTILLA (4 campos)
    'players_used': int,             # Jugadores utilizados
    'average_age': float,            # Edad media
    'Age': float,                    # Duplicado
    'minutes_played_team': int       # Minutos totales
}
```

**Campos opponent_ (cuando include_opponent_stats=True)**
```python
{
    'opponent_goals': int,           # = goals_against
    'opponent_shots': int,           # Tiros rivales
    'opponent_shots_on_target': int, # A puerta rivales
    'opponent_passes_completed': int,# Pases rivales
    'opponent_tackles': int,         # Tackles rivales
    # ... (~190 campos con prefijo opponent_)
}
```

## 2. fbref_extract_multiple()

### Descripción
Extracción en lote de múltiples entidades. Retorna DataFrame unificado.

### Sintaxis
```python
fbref_extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False
) -> pd.DataFrame
```

### Parámetros
- **entities** (List[str]): Lista de nombres de jugadores o equipos
- **entity_type** (str): `"player"` o `"team"` (todos deben ser del mismo tipo)
- **league**, **season**, **match_id**, **include_opponent_stats**: Idénticos a `extract_data()`

### Retorno
Tipo: `pd.DataFrame`

#### Estructura:
- **Filas**: Una por cada entidad en `entities`
- **Columnas**: 153 (jugadores) o 190 (equipos) + metadata DataFrame
- **Tipos**: Numéricos convertidos a `float64` para permitir NaN
- **No encontrados**: Fila con NaN pero mantiene nombre original

#### Diferencias con extract_data():
- **Input**: Lista vs string único
- **Output**: DataFrame vs Dict/None
- **No encontrado**: Fila NaN vs None
- **Tipos**: float64 vs tipos originales

## 3. fbref_extract_league_players()

### Descripción
Extrae lista completa de jugadores registrados en una liga.

### Sintaxis
```python
fbref_extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None
) -> pd.DataFrame
```

### Parámetros
- **league** (str): Código liga formato FBref
- **season** (str): Formato `"YYYY-YY"`
- **team_filter** (str, opcional): Búsqueda parcial case-insensitive
- **position_filter** (str, opcional): `"GK"`, `"DF"`, `"MF"`, `"FW"` o múltiples

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (7 columnas):
```python
{
    'player': str,                   # Nombre completo oficial FBref
    'team': str,                     # Equipo en la temporada
    'league': str,                   # Liga (igual al parámetro)
    'season': str,                   # Temporada formato interno FBref
    'pos': str,                      # Posición(es): "GK", "DF", "MF", "FW", "DF,MF"
    'age': Int64,                    # Edad (nullable)
    'nation': str                    # Código ISO-3 país
}
```

#### Características:
- **Ordenamiento**: Por equipo (alfabético), luego jugador
- **Tamaño típico**: 450-600 jugadores según liga
- **Filtros**: `team_filter` usa `.str.contains()`, `position_filter` búsqueda literal

## 4. fbref_extract_league_schedule()

### Descripción
Extrae calendario completo de liga con resultados y metadatos.

### Sintaxis
```python
fbref_extract_league_schedule(
    league: str,
    season: str
) -> pd.DataFrame
```

### Parámetros
- **league** (str): Código liga formato FBref
- **season** (str): Formato `"YYYY-YY"`

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (15 columnas):
```python
{
    'week': Int64,                   # Jornada/Gameweek (nullable)
    'day': string,                   # Día semana: "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    'date': datetime64[ns],          # Fecha completa YYYY-MM-DD
    'time': string,                  # Hora local "HH:MM" (24h)
    'home_team': string,             # Equipo local
    'home_xg': Float64,              # Expected Goals local (NaN si no jugado)
    'score': string,                 # "2-1", "0-0", "Match Postponed", ""
    'away_xg': Float64,              # Expected Goals visitante
    'away_team': string,             # Equipo visitante
    'attendance': Int64,             # Asistencia (NaN si no disponible)
    'venue': string,                 # Nombre estadio
    'referee': string,               # Árbitro principal
    'match_report': object,          # URL relativa informe partido
    'notes': Int64,                  # Notas especiales (raramente usado)
    'game_id': object                # ID único 8 chars hexadecimales
}
```

#### Características:
- **Ordenamiento**: Por fecha, luego hora
- **Tamaño**: 380 partidos (20 equipos), 306 (18 equipos)
- **Estados**: NaN para no jugados, valores reales para finalizados

## 5. fbref_extract_match_events()

### Descripción
Extrae eventos detallados de un partido específico.

### Sintaxis
```python
fbref_extract_match_events(
    match_id: str,
    league: str,
    season: str,
    event_type: str = 'all'
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]
```

### Parámetros
- **match_id** (str): 8 caracteres hexadecimales
- **league** (str): Código liga formato FBref
- **season** (str): Formato `"YYYY-YY"`
- **event_type** (str): `'all'`, `'events'`, `'shots'`, `'lineups'`

### Retorno

#### event_type='all' → Dict[str, pd.DataFrame]
```python
{
    'events': pd.DataFrame,          # Eventos principales
    'shots': pd.DataFrame,           # Disparos detallados
    'lineups': pd.DataFrame          # Alineaciones
}
```

#### event_type='events' → pd.DataFrame
Estructura (6 columnas):
```python
{
    'minute': int,                   # Minuto del evento (1-90+)
    'player': str,                   # Jugador involucrado
    'team': str,                     # Equipo del jugador
    'event_type': str,               # "Goal", "Yellow Card", "Red Card", "Substitution"
    'detail': str,                   # Detalles: "Penalty", "Header", "Second Yellow", etc.
    'score': str                     # Marcador tras evento (solo para goles)
}
```

#### event_type='shots' → pd.DataFrame
Estructura (10 columnas):
```python
{
    'minute': int,                   # Minuto del disparo
    'player': str,                   # Jugador que dispara
    'team': str,                     # Equipo
    'xG': float,                     # Expected Goals (0.00-1.00)
    'outcome': str,                  # "Goal", "Saved", "Blocked", "Off Target", "Woodwork"
    'distance': float,               # Distancia en yardas
    'body_part': str,                # "Right Foot", "Left Foot", "Head", "Other"
    'notes': str,                    # "Penalty", "Free Kick", "From Corner", "Volley"
    'assisted_by': str,              # Jugador asistente
    'shot_type': str                 # "Open Play", "Set Piece", "Counter", "Penalty"
}
```

#### event_type='lineups' → pd.DataFrame
Estructura (7 columnas):
```python
{
    'player': str,                   # Nombre jugador
    'team': str,                     # Equipo
    'position': str,                 # "GK", "RB", "CB", "LB", "DM", "CM", "AM", "RW", "LW", "ST", "SUB"
    'number': int,                   # Dorsal (1-99)
    'captain': bool,                 # True si es capitán
    'starter': bool,                 # True si titular, False si suplente
    'formation_position': str        # Posición numérica en formación
}
```

## 6. fbref_export_to_csv()

### Descripción
Exporta datos a CSV con formato adecuado.

### Sintaxis
```python
fbref_export_to_csv(
    data: Union[Dict, pd.DataFrame],
    filename: str,
    include_timestamp: bool = True
) -> str
```

### Parámetros
- **data** (Dict/DataFrame): Datos a exportar
- **filename** (str): Nombre base del archivo
- **include_timestamp** (bool): Si incluir timestamp en el nombre

### Retorno
Tipo: `str` (nombre del archivo generado)

## 7. Funciones de Acceso Rápido

### fbref_get_player()
```python
fbref_get_player(player_name: str, league: str, season: str) -> Optional[Dict]
```
Wrapper simplificado de `extract_data()` para jugadores.

### fbref_get_team()
```python
fbref_get_team(team_name: str, league: str, season: str) -> Optional[Dict]
```
Wrapper simplificado de `extract_data()` para equipos.

### fbref_get_players()
```python
fbref_get_players(players: List[str], league: str, season: str) -> pd.DataFrame
```
Wrapper de `extract_multiple()` para múltiples jugadores.

### fbref_get_teams()
```python
fbref_get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame
```
Wrapper de `extract_multiple()` para múltiples equipos.

### fbref_get_league_players()
```python
fbref_get_league_players(league: str, season: str, team: Optional[str] = None) -> pd.DataFrame
```
Lista rápida de jugadores de liga.

### fbref_get_match_data()
```python
fbref_get_match_data(match_id: str, league: str, season: str, data_type: str = 'all') -> Union[pd.DataFrame, Dict]
```
Extracción rápida de datos de partido.

### fbref_get_schedule()
```python
fbref_get_schedule(league: str, season: str) -> pd.DataFrame
```
Extracción rápida de calendario de liga.

---

# Understat Wrapper

Especializado en métricas avanzadas exclusivas de Understat no disponibles en FBref, con formato compatible para merge automático.

## 1. understat_extract_data()

### Descripción
Motor unificado para extracción de métricas avanzadas de Understat.

### Sintaxis
```python
understat_extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str
) -> Optional[Dict]
```

### Parámetros
- **entity_name** (str): Nombre del jugador o equipo
- **entity_type** (str): `'player'` o `'team'`
- **league** (str): Identificador de liga
- **season** (str): Identificador de temporada

### Retorno

#### Para Jugadores
Tipo: `Dict[str, Union[str, int, float]]` o `None`

```python
{
    # IDENTIFICACIÓN (Compatible con FBref)
    'player_name': str,              # Compatible con FBref
    'team': str,                     # Compatible con FBref
    'league': str,                   # Compatible con FBref
    'season': str,                   # Compatible con FBref
    'official_player_name': str,     # Nombre exacto en Understat
    
    # MÉTRICAS EXCLUSIVAS BUILD-UP
    'understat_xg_chain': float,     # xG generado en cadenas donde participa
    'understat_xg_buildup': float,   # xG generado en build-up (sin disparo/asistencia)
    'understat_buildup_involvement_pct': float, # % participación en construcción
    
    # MÉTRICAS EXCLUSIVAS OFENSIVAS
    'understat_npxg_plus_xa': float, # Non-penalty xG + xA combinado
    'understat_key_passes': int,     # Pases clave totales
    'understat_np_xg': float,        # Non-penalty xG
    'understat_xa': float,           # Expected Assists
    'understat_np_goals': int,       # Goles sin penalti
    
    # IDENTIFICADORES ÚNICOS
    'understat_player_id': int,      # ID único del jugador en Understat
    'understat_team_id': int         # ID único del equipo en Understat
}
```

#### Para Equipos
Tipo: `Dict[str, Union[str, int, float]]` o `None`

```python
{
    # IDENTIFICACIÓN (Compatible con FBref)
    'team_name': str,                # Compatible con FBref
    'league': str,                   # Compatible con FBref
    'season': str,                   # Compatible con FBref
    'official_team_name': str,       # Nombre exacto en Understat
    
    # MÉTRICAS DE PRESIÓN DEFENSIVA
    'understat_ppda_avg': float,     # Passes Per Defensive Action promedio
    'understat_ppda_std': float,     # Desviación estándar PPDA
    
    # MÉTRICAS DE PENETRACIÓN OFENSIVA
    'understat_deep_completions_total': int,  # Pases completados en tercio final
    'understat_deep_completions_avg': float,   # Promedio por partido
    
    # MÉTRICAS DE RENDIMIENTO ESPERADO
    'understat_expected_points_total': float,  # Puntos esperados totales
    'understat_expected_points_avg': float,    # Promedio por partido
    'understat_points_efficiency': float,      # Eficiencia de puntos
    
    # MÉTRICAS xG DE EQUIPO
    'understat_np_xg_total': float,  # Non-penalty xG total
    'understat_np_xg_avg': float,    # Promedio por partido
    
    # CONTROL
    'understat_matches_analyzed': int # Partidos analizados
}
```

## 2. understat_extract_multiple()

### Descripción
Extracción eficiente en lote con métricas avanzadas.

### Sintaxis
```python
understat_extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str
) -> pd.DataFrame
```

### Parámetros
- **entities** (List[str]): Lista de nombres de jugadores o equipos
- **entity_type** (str): `'player'` o `'team'`
- **league** (str): Identificador de liga
- **season** (str): Identificador de temporada

### Retorno
Tipo: `pd.DataFrame` con métricas Understat para todas las entidades

**Estructura**: Todas las columnas de `extract_data()` en formato DataFrame

## 3. understat_extract_shot_events()

### Descripción
Eventos de disparo con coordenadas exactas y análisis espacial.

### Sintaxis
```python
understat_extract_shot_events(
    match_id: Union[int, str],
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None
) -> pd.DataFrame
```

### Parámetros
- **match_id** (int/str): ID de partido de Understat
- **league** (str): Identificador de liga
- **season** (str): Identificador de temporada
- **player_filter** (str, opcional): Filtro por nombre de jugador
- **team_filter** (str, opcional): Filtro por nombre de equipo

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (25 columnas):
```python
{
    # IDENTIFICADORES DE PARTIDO
    'league_id': str,                # ID de liga
    'season_id': int,                # ID de temporada
    'game_id': int,                  # ID de partido
    'date': datetime64[ns],          # Fecha y hora del partido
    'match_id': int,                 # ID de partido (duplicado)
    
    # IDENTIFICADORES DE DISPARO
    'shot_id': int,                  # ID único del disparo
    'team_id': int,                  # ID del equipo
    'player_id': int,                # ID del jugador
    
    # INFORMACIÓN DE ASISTENCIA
    'assist_player_id': int,         # ID del asistente (nullable)
    'assist_player_name': str,       # Nombre del asistente (nullable)
    'is_assisted': int,              # 1 si fue asistido, 0 si no
    
    # MÉTRICAS DEL DISPARO
    'shot_xg': float,                # Expected Goals del disparo
    'shot_location_x': float,        # Coordenada X (0-1)
    'shot_location_y': float,        # Coordenada Y (0-1)
    'shot_minute': int,              # Minuto del disparo
    
    # CARACTERÍSTICAS DEL DISPARO
    'shot_body_part': str,           # 'Right Foot', 'Left Foot', 'Head', etc.
    'shot_situation': str,           # 'Open Play', 'Set Piece', 'Counter', etc.
    'shot_result': str,              # 'Goal', 'Blocked Shot', 'Saved', etc.
    
    # FLAGS DE RESULTADO
    'is_goal': int,                  # 1 si fue gol, 0 si no
    'is_on_target': int,             # 1 si fue a puerta, 0 si no
    'is_blocked': int,               # 1 si fue bloqueado, 0 si no
    
    # ANÁLISIS ESPACIAL (CALCULADO)
    'shot_distance_to_goal': float,  # Distancia en metros
    'shot_zone': str,                # 'Penalty_Box', 'Penalty_Area_Edge', etc.
    
    # METADATA
    'data_source': str               # Siempre 'understat'
}
```

#### Valores de referencia:

**Zonas de Disparo (shot_zone)**:
- `"Penalty_Box"`: Dentro del área
- `"Penalty_Area_Edge"`: Borde del área
- `"Outside_Box"`: Fuera del área

**Situaciones de Juego (shot_situation)**:
- `"Open Play"`: Jugada abierta
- `"Set Piece"`: Jugada a balón parado
- `"Counter"`: Contraataque
- `"Direct Free Kick"`: Tiro libre directo
- `"Corner"`: Corner

**Partes del Cuerpo (shot_body_part)**:
- `"Right Foot"`: Pie derecho
- `"Left Foot"`: Pie izquierdo
- `"Head"`: Cabeza
- `"Other"`: Otras partes

## 4. understat_merge_with_fbref()

### Descripción
Fusión automática de datos FBref con métricas Understat.

### Sintaxis
```python
understat_merge_with_fbref(
    fbref_data: Union[pd.DataFrame, Dict],
    league: str,
    season: str,
    data_type: str = 'player'
) -> pd.DataFrame
```

### Parámetros
- **fbref_data** (DataFrame/Dict): Datos de FBref
- **league** (str): Identificador de liga
- **season** (str): Identificador de temporada
- **data_type** (str): `'player'` o `'team'`

### Retorno
Tipo: `pd.DataFrame` combinado sin duplicados

**Proceso**: Matching automático por nombre → Merge por claves → Eliminación duplicados

## 5. understat_export_to_csv()

### Descripción
Exportación con formato adecuado.

### Sintaxis
```python
understat_export_to_csv(
    data: Union[Dict, pd.DataFrame],
    filename: str,
    include_timestamp: bool = True
) -> str
```

### Parámetros
- **data** (Dict/DataFrame): Datos a exportar
- **filename** (str): Nombre base del archivo
- **include_timestamp** (bool): Si incluir timestamp

### Retorno
Tipo: `str` (nombre del archivo generado)

## 6. Funciones de Acceso Rápido

### understat_get_player()
```python
understat_get_player(player_name: str, league: str, season: str) -> Optional[Dict]
```
Wrapper simplificado de `extract_data()` para jugadores.

### understat_get_team()
```python
understat_get_team(team_name: str, league: str, season: str) -> Optional[Dict]
```
Wrapper simplificado de `extract_data()` para equipos.

### understat_get_players()
```python
understat_get_players(players: List[str], league: str, season: str) -> pd.DataFrame
```
Wrapper de `extract_multiple()` para múltiples jugadores.

### understat_get_teams()
```python
understat_get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame
```
Wrapper de `extract_multiple()` para múltiples equipos.

### understat_get_shots()
```python
understat_get_shots(match_id: Union[int, str], league: str, season: str) -> pd.DataFrame
```
Wrapper de `extract_shot_events()` sin filtros.

## 7. Referencia de Campos

### Métricas de Build-up (Jugadores)
- **understat_xg_chain**: xG total generado en cadenas de juego donde el jugador participa. Incluye disparos propios, asistencias y participación en jugadas.
- **understat_xg_buildup**: xG generado en construcción de jugadas, excluyendo el disparo final y la asistencia. Mide la contribución pura al build-up.
- **understat_buildup_involvement_pct**: Porcentaje de participación en construcción. Calculado como `(xg_chain / np_xg) * 100`.

### Métricas Ofensivas (Jugadores)
- **understat_npxg_plus_xa**: Métrica combinada de Non-penalty xG + Expected Assists. Indicador de peligro ofensivo total.
- **understat_key_passes**: Pases que llevan directamente a un disparo. Incluye asistencias y pre-asistencias.
- **understat_np_xg**: Expected Goals sin incluir penaltis. Calidad de las ocasiones de disparo.
- **understat_xa**: Expected Assists. Calidad de los pases que generan ocasiones.
- **understat_np_goals**: Goles anotados sin incluir penaltis.

### Métricas Defensivas (Equipos)
- **understat_ppda_avg**: Passes Per Defensive Action. Mide la intensidad de la presión (menor = más presión).
- **understat_ppda_std**: Desviación estándar del PPDA. Indica variabilidad en el estilo de presión.

### Métricas de Penetración (Equipos)
- **understat_deep_completions_total**: Total de pases completados en el tercio final del campo rival.
- **understat_deep_completions_avg**: Promedio por partido de pases profundos completados.

### Métricas de Rendimiento (Equipos)
- **understat_expected_points_total**: Puntos esperados basados en xG a favor y en contra.
- **understat_expected_points_avg**: Promedio de puntos esperados por partido.
- **understat_points_efficiency**: Ratio de eficiencia calculado como `expected_points / matches_analyzed`.

### Coordenadas y Zonas (Disparos)
- **shot_location_x/y**: Coordenadas normalizadas (0-1) donde 1,1 es la esquina superior derecha del campo.
- **shot_distance_to_goal**: Distancia euclidiana calculada en metros desde el punto de disparo hasta el centro de la portería.
- **shot_zone**: Clasificación automática basada en coordenadas.

---

# WhoScored Wrapper

Especializado en análisis espacial y eventos con coordenadas tácticas, proporcionando datos granulares de cada acción con posicionamiento exacto en el campo.

## 1. whoscored_extract_match_events()

### Descripción
Extrae TODOS los eventos de un partido con coordenadas espaciales completas.

### Sintaxis
```python
whoscored_extract_match_events(
    match_id: str,
    league: str,
    season: str,
    event_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    for_viz: bool = False,
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **match_id** (str): ID único del partido en WhoScored (string numérico)
- **league** (str): Liga en formato estándar (`"ESP-La Liga"`, `"ENG-Premier League"`)
- **season** (str): Temporada en formato `"YYYY-YY"`
- **event_filter** (str, opcional): Filtro por tipo de evento (`"Pass"`, `"Shot"`, `"Tackle"`, etc.)
- **player_filter** (str, opcional): Filtro por nombre exacto de jugador
- **team_filter** (str, opcional): Filtro por nombre exacto de equipo
- **for_viz** (bool, opcional): True reduce columnas para visualización (37 campos vs 42)
- **verbose** (bool, opcional): True imprime progreso de extracción

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (42 columnas completas):
```python
{
    # IDENTIFICACIÓN
    'game_id': int64,                # ID del partido
    'match_id': int64,               # Duplicado de game_id
    'team_id': int64,                # ID del equipo
    'team': object,                  # Nombre del equipo
    'player_id': float64,            # ID del jugador (NaN para eventos de equipo)
    'player': object,                # Nombre del jugador
    
    # TEMPORAL
    'period': object,                # "FirstHalf", "SecondHalf", "ExtraFirstHalf"
    'minute': int64,                 # Minuto del evento (0-90+)
    'second': float64,               # Segundo exacto del evento
    'expanded_minute': int64,        # Minuto considerando tiempo añadido
    
    # TIPO DE EVENTO
    'type': object,                  # "Pass", "SavedShot", "Goal", "Tackle", etc.
    'outcome_type': object,          # "Successful" o "Unsuccessful"
    'event_type': object,            # Categoría general del evento
    
    # COORDENADAS ESPACIALES
    'x': float64,                    # Posición X inicial (0-100)
    'y': float64,                    # Posición Y inicial (0-100)
    'end_x': float64,                # Posición X final (para pases/disparos)
    'end_y': float64,                # Posición Y final
    
    # ESPECÍFICO DE DISPAROS
    'goal_mouth_y': float64,         # Coordenada Y en la portería
    'goal_mouth_z': float64,         # Altura del disparo en portería
    'blocked_x': float64,            # Posición X donde fue bloqueado
    'blocked_y': float64,            # Posición Y donde fue bloqueado
    
    # DETALLES Y CONTEXTO
    'qualifiers': object,            # Lista de cualificadores del evento
    'is_touch': bool,                # Si el jugador tocó el balón
    'is_shot': object,               # Si es un disparo ("True"/"False"/NaN)
    'is_goal': object,               # Si resultó en gol
    'card_type': object,             # Tipo de tarjeta ("Yellow", "Red", None)
    'related_event_id': float64,     # ID de evento relacionado
    'related_player_id': float64,    # ID de jugador relacionado
    
    # METADATOS
    'data_source': object,           # Siempre "whoscored"
    'pass_length': object,           # Longitud del pase ("Short", "Medium", "Long")
    
    # FLAGS BOOLEANOS
    'is_longball': bool,             # Si es pase largo
    'is_header': bool,               # Si es de cabeza
    'is_cross': bool,                # Si es centro
    'is_through_ball': bool,         # Si es pase filtrado
    'is_assist': bool,               # Si es asistencia
    'is_successful': bool,           # Si fue exitoso
    
    # INFORMACIÓN ADICIONAL
    'shot_body_part': object,        # Parte del cuerpo en disparos
    'field_zone': object,            # Zona del campo (9 zonas)
    'possession_sequence': int64,    # Número de secuencia de posesión
    'next_player': object,           # Siguiente jugador en tocar balón
    
    # MÉTRICAS CALCULADAS
    'distance_to_goal': float64,     # Distancia a portería en metros
    'pass_distance': float64         # Distancia del pase en metros
}
```

#### Sistema de Coordenadas:
- **Origen (0,0)**: Esquina inferior izquierda del campo propio
- **X**: 0-100 (horizontal, izquierda a derecha)
- **Y**: 0-100 (vertical, abajo hacia arriba)
- **Portería propia**: X=0, **Portería rival**: X=100

#### Zonas del Campo (field_zone):
Campo dividido en 9 zonas: 3x3 grid
- **Formato**: `"{Tercio}_{Lateral}"`
- **Tercios**: `"Defensive"`, `"Middle"`, `"Attacking"`
- **Laterales**: `"Left"`, `"Center"`, `"Right"`
- **Ejemplos**: `"Attacking_Left"`, `"Middle_Center"`

#### Tipos de Eventos:
- **Con Balón**: Pass, Shot, Dribble, Touch, Carry, Clearance, Interception, Aerial, BallRecovery
- **Sin Balón**: Tackle, Foul, Card, Substitution, Offside
- **Portero**: Save, Claim, Punch, Smother
- **Especiales**: Goal, OwnGoal, PenaltyFaced, Start/End

## 2. whoscored_extract_pass_network()

### Descripción
Genera datos completos para visualización de redes de pases.

### Sintaxis
```python
whoscored_extract_pass_network(
    match_id: str,
    team: str,
    league: str,
    season: str,
    min_passes: int = 3,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]
```

### Parámetros
- **match_id** (str): ID del partido a analizar
- **team** (str): Nombre exacto del equipo (case-sensitive)
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **min_passes** (int, opcional): Mínimo de pases entre jugadores para incluir conexión
- **verbose** (bool, opcional): Imprime estadísticas de la red

### Retorno
Tipo: `Dict[str, pd.DataFrame]`

```python
{
    'passes': pd.DataFrame,          # Todos los pases del equipo
    'positions': pd.DataFrame,       # Posiciones promedio de jugadores
    'connections': pd.DataFrame      # Conexiones entre jugadores
}
```

#### DataFrame 'positions' (7 columnas):
```python
{
    'player': object,                # Nombre del jugador
    'avg_x': float64,                # Posición X promedio
    'avg_y': float64,                # Posición Y promedio
    'total_passes': int64,           # Total de pases realizados
    'crosses': int64,                # Número de centros
    'longballs': int64,              # Número de pases largos
    'team': object                   # Equipo
}
```

#### DataFrame 'connections' (9 columnas):
```python
{
    'team': object,                  # Equipo
    'source': object,                # Jugador que pasa
    'target': object,                # Jugador que recibe
    'pass_count': int64,             # Número de pases entre ellos
    'direction': object,             # "A_to_B" (unidireccional)
    'avg_source_x': float64,         # Posición X promedio del pasador
    'avg_source_y': float64,         # Posición Y promedio del pasador
    'avg_target_x': float64,         # Posición X promedio del receptor
    'avg_target_y': float64          # Posición Y promedio del receptor
}
```

## 3. whoscored_extract_player_heatmap()

### Descripción
Genera datos de mapa de calor para un jugador específico.

### Sintaxis
```python
whoscored_extract_player_heatmap(
    match_id: str,
    player_name: str,
    league: str,
    season: str,
    event_types: Optional[List[str]] = None,
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **match_id** (str): ID del partido
- **player_name** (str): Nombre exacto del jugador (case-sensitive)
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **event_types** (List[str], opcional): Lista de tipos de eventos a incluir
- **verbose** (bool, opcional): Activa debug

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (9 columnas):
```python
{
    'field_zone': object,            # Zona del campo
    'action_count': int64,           # Total de acciones en la zona
    'successful_actions': int64,     # Acciones exitosas
    'success_rate': float64,         # Porcentaje de éxito (0-100)
    'avg_x': float64,                # Posición X promedio en zona
    'avg_y': float64,                # Posición Y promedio en zona
    'player': object,                # Nombre del jugador
    'total_actions': int64,          # Total de acciones del jugador
    'zone_percentage': float64       # % de actividad en esta zona
}
```

## 4. whoscored_extract_shot_map()

### Descripción
Extrae todos los disparos de un partido con información espacial completa.

### Sintaxis
```python
whoscored_extract_shot_map(
    match_id: str,
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    player_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **match_id** (str): ID del partido
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **team_filter** (str, opcional): Filtra por equipo específico
- **player_filter** (str, opcional): Filtra por jugador específico
- **verbose** (bool, opcional): Debug mode

### Retorno
Tipo: `pd.DataFrame`

**Estructura**: Todas las columnas de match_events + 3 específicas:
```python
{
    # Todas las columnas de match_events +
    'is_on_target': bool,            # Si el disparo fue a puerta
    'is_blocked': bool,              # Si fue bloqueado
    'shot_zone': object              # Zona desde donde se disparó
}
```

#### Zonas de Disparo (shot_zone):
- `"Six_Yard_Box"`: Área pequeña
- `"Central_Penalty_Box"`: Centro del área
- `"Left_Penalty_Box"`: Lado izquierdo del área
- `"Right_Penalty_Box"`: Lado derecho del área
- `"Penalty_Area_Edge"`: Frontal del área
- `"Outside_Box"`: Fuera del área

#### Tipos de Disparo (type):
- `"Goal"`: Gol
- `"SavedShot"`: Parada del portero
- `"MissedShots"`: Disparo fuera
- `"ShotOnPost"`: Disparo al palo
- `"BlockedShot"`: Disparo bloqueado

## 5. whoscored_extract_field_occupation()

### Descripción
Analiza la ocupación espacial del campo por un equipo.

### Sintaxis
```python
whoscored_extract_field_occupation(
    match_id: str,
    team: str,
    league: str,
    season: str,
    period: str = "all",
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **match_id** (str): ID del partido
- **team** (str): Nombre exacto del equipo
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **period** (str, opcional): `"all"`, `"first_half"`, `"second_half"`
- **verbose** (bool, opcional): Debug mode

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (8 columnas):
```python
{
    'field_zone': object,            # Zona del campo
    'event_count': int64,            # Total de eventos en la zona
    'successful_events': int64,      # Eventos exitosos
    'success_rate': float64,         # Porcentaje de éxito
    'avg_x': float64,                # Posición X promedio
    'avg_y': float64,                # Posición Y promedio
    'occupation_percentage': float64,# % de ocupación total
    'team': object                   # Equipo
}
```

## 6. whoscored_extract_league_schedule()

### Descripción
Extrae el calendario completo de una liga con resultados y metadatos de partidos.

### Sintaxis
```python
whoscored_extract_league_schedule(
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **verbose** (bool, opcional): Debug mode

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (43 columnas principales):
```python
{
    # IDENTIFICACIÓN
    'stage_id': int64,               # ID de la jornada
    'game_id': int64,                # ID único del partido
    'status': int64,                 # Estado (6=Finalizado, 3=En juego, 0=Programado)
    
    # TEMPORAL
    'start_time': object,            # Fecha/hora programada
    'date': datetime64[ns, UTC],     # Fecha convertida
    'elapsed': object,               # Estado ("FT", "HT", etc.)
    
    # EQUIPOS
    'home_team_id': int64,           # ID equipo local
    'home_team': object,             # Nombre equipo local
    'away_team_id': int64,           # ID equipo visitante
    'away_team': object,             # Nombre equipo visitante
    
    # RESULTADO
    'home_score': int64,             # Goles local
    'away_score': int64,             # Goles visitante
    'winner_field': float64,         # 0=Local, 1=Visitante, NaN=Empate
    
    # DISCIPLINA
    'home_yellow_cards': int64,      # Amarillas local
    'home_red_cards': int64,         # Rojas local
    'away_yellow_cards': int64,      # Amarillas visitante
    'away_red_cards': int64,         # Rojas visitante
    
    # METADATOS
    'is_lineup_confirmed': bool,     # Si hay alineaciones
    'has_incidents_summary': bool,   # Si hay resumen
    'is_top_match': bool,            # Partido destacado
    'match_is_opta': bool,           # Datos Opta disponibles
    
    # INCIDENTES
    'incidents': object,             # Lista de goles y eventos clave
    
    # TIEMPOS UTC
    'started_at_utc': object,        # Inicio real
    'first_half_ended_at_utc': object,
    'second_half_started_at_utc': object
}
```

#### Estados de Partido (status):
- **0**: Programado
- **3**: En juego
- **4**: Media parte
- **6**: Finalizado
- **7**: Aplazado/Suspendido

## 7. whoscored_extract_missing_players()

### Descripción
Identifica jugadores lesionados o sancionados para un partido específico.

### Sintaxis
```python
whoscored_extract_missing_players(
    match_id: str,
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame
```

### Parámetros
- **match_id** (str): ID del partido
- **league** (str): Liga en formato estándar
- **season** (str): Temporada `"YYYY-YY"`
- **verbose** (bool, opcional): Debug mode

### Retorno
Tipo: `pd.DataFrame`

#### Estructura (4 columnas):
```python
{
    'game_id': int64,                # ID del partido
    'player_id': int64,              # ID del jugador
    'reason': object,                # Razón de ausencia
    'status': object                 # Estado del jugador
}
```

#### Razones de Ausencia (reason):
- `"injured"`: Lesionado
- `"suspended"`: Sancionado
- `"doubt"`: Duda
- `"international"`: Con selección

#### Estados (status):
- `"Out"`: Confirmado ausente
- `"Doubt"`: Duda para el partido

## 8. whoscored_export_to_csv()

### Descripción
Exporta cualquier estructura de datos a CSV con formato optimizado.

### Sintaxis
```python
whoscored_export_to_csv(
    data: Union[pd.DataFrame, Dict, List],
    filename: str,
    timestamp: bool = False,
    for_viz: bool = False
) -> str
```

### Parámetros
- **data** (DataFrame/Dict/List): Datos a exportar
- **filename** (str): Nombre base del archivo (sin extensión)
- **timestamp** (bool, opcional): Si True, añade timestamp al nombre
- **for_viz** (bool, opcional): Si True, aplica formato para visualización

### Retorno
Tipo: `str` (path del archivo creado)

#### Comportamiento Especial:
- **Diccionarios con DataFrames**: Crea un CSV por cada key
- **Listas**: Convierte a DataFrame antes de exportar
- **for_viz=True**: Reduce decimales y optimiza tamaño

## 9. Funciones de Acceso Rápido

### whoscored_get_match_events()
```python
whoscored_get_match_events(match_id: str, league: str, season: str) -> pd.DataFrame
```
Wrapper simplificado de `extract_match_events()` con parámetros mínimos.

### whoscored_get_match_events_viz()
```python
whoscored_get_match_events_viz(match_id: str, league: str, season: str) -> pd.DataFrame
```
Versión para visualización con columnas reducidas automáticamente.

### whoscored_get_pass_network()
```python
whoscored_get_pass_network(match_id: str, team: str, league: str, season: str) -> Dict[str, pd.DataFrame]
```
Acceso rápido a red de pases con defaults optimizados.

### whoscored_get_player_heatmap()
```python
whoscored_get_player_heatmap(match_id: str, player_name: str, league: str, season: str) -> pd.DataFrame
```
Mapa de calor rápido para un jugador.

### whoscored_get_shot_map()
```python
whoscored_get_shot_map(match_id: str, league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame
```
Mapa de disparos con opción de filtro por equipo.

### whoscored_get_field_occupation()
```python
whoscored_get_field_occupation(match_id: str, team: str, league: str, season: str) -> pd.DataFrame
```
Ocupación del campo de forma rápida.

### whoscored_get_schedule()
```python
whoscored_get_schedule(league: str, season: str) -> pd.DataFrame
```
Calendario de liga sin opciones adicionales.

### whoscored_get_missing_players()
```python
whoscored_get_missing_players(match_id: str, league: str, season: str) -> pd.DataFrame
```
Jugadores ausentes de forma directa.

## 10. Qualifiers de Eventos

Los qualifiers proporcionan contexto adicional para cada evento. 

### Estructura:
```json
[
    {
        "type": {
            "displayName": "Zone",
            "value": "56"
        },
        "value": "Center"          // Valor legible
    },
    {
        "type": {
            "displayName": "Length",
            "value": "212"
        },
        "value": "12.7"             // Distancia en metros
    }
]
```

### Qualifiers Comunes:
- **Zone (56)**: Zona del pase (Back/Center/Right/Left)
- **Length (212)**: Distancia del pase en metros
- **Angle (213)**: Ángulo del pase en radianes
- **PassEndX/Y (140/141)**: Coordenadas finales exactas
- **BigChance (214)**: Ocasión clara de gol
- **KeyPass (131)**: Pase clave (lleva a disparo)
- **IntentionalAssist (154)**: Asistencia intencional
- **FromCorner (22)**: Originado de córner
- **Throughball (4)**: Pase filtrado
- **Cross (2)**: Centro al área
- **HeadPass (3)**: Pase de cabeza

## 11. Transformaciones de Coordenadas

### Cálculos aplicados:
```python
# Cálculo de distancia a portería
distance = sqrt((100 - x)^2 + (50 - y)^2) * 1.05  # En metros

# Clasificación de zonas de disparo
if 86 <= x <= 100:
    if 30 <= y <= 70:
        zone = "Central_Penalty_Box"
    elif y < 30:
        zone = "Right_Penalty_Box"
    else:
        zone = "Left_Penalty_Box"

# Conversión a metros reales
real_x = x * 1.05  # Campo: 105m de largo
real_y = y * 0.68  # Campo: 68m de ancho
```

## 12. Secuencias de Posesión

Cada evento incluye `possession_sequence`:
- Incrementa con cada cambio de posesión
- Permite agrupar eventos por posesión
- Útil para análisis de transiciones
- Reinicia en cada período

---

## Notas de Uso

### Compatibilidad entre Wrappers
Los tres wrappers están diseñados para trabajar en conjunto:
1. **FBref**: Base completa de estadísticas
2. **Understat**: Métricas avanzadas exclusivas
3. **WhoScored**: Datos espaciales y eventos

### Ejemplo de uso combinado:
```python
# 1. Obtener estadísticas base
player_data = fbref_get_player("Vinícius Júnior", "ESP-La Liga", "2023-24")

# 2. Enriquecer con métricas avanzadas
understat_data = understat_get_player("Vinícius Júnior", "ESP-La Liga", "2023-24")

# 3. Fusionar datos
merged_data = understat_merge_with_fbref(player_data, "ESP-La Liga", "2023-24", "player")

# 4. Añadir análisis espacial de un partido específico
match_events = whoscored_get_match_events("1234567", "ESP-La Liga", "2023-24")
player_heatmap = whoscored_get_player_heatmap("1234567", "Vinícius Júnior", "ESP-La Liga", "2023-24")
```

### Consideraciones de rendimiento:
- Las funciones de FBref realizan múltiples llamadas internas (hasta 11 stat_types)
- Understat es más rápido al tener menos endpoints
- WhoScored requiere Selenium y puede ser más lento
- Usar `extract_multiple()` para lotes es más eficiente que llamadas individuales