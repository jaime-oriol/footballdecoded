# Match Data Processing - Documentación Técnica Completa

## Descripción General

El módulo `match_data.py` procesa datos de partidos combinando WhoScored y Understat para generar 5 CSVs optimizados para visualización. Aplica un pipeline de enriquecimiento que añade métricas avanzadas (xThreat, carries, progressive actions) y genera archivos perfectamente estructurados para análisis visual.

## Tabla de Contenidos
1. [Función Principal](#función-principal)
2. [Pipeline de Enriquecimiento](#pipeline-de-enriquecimiento)
3. [CSVs Generados](#csvs-generados)
   - [match_events.csv](#1-match_eventscsv)
   - [match_aggregates.csv](#2-match_aggregatescsv)
   - [player_network.csv](#3-player_networkcsv)
   - [spatial_analysis.csv](#4-spatial_analysiscsv)
   - [match_info.csv](#5-match_infocsv)

---

## Función Principal

### extract_match_complete()

#### Descripción
Extrae y procesa TODOS los datos de un partido, aplicando enriquecimiento avanzado y generando 5 CSVs optimizados para visualización.

#### Sintaxis
```python
extract_match_complete(
    ws_id: int,
    us_id: int,
    league: str,
    season: str,
    home_team: str,
    away_team: str,
    match_date: str
) -> Dict[str, pd.DataFrame]
```

#### Parámetros
- **ws_id** (int): ID del partido en WhoScored
- **us_id** (int): ID del partido en Understat
- **league** (str): Liga en formato estándar (ej: `"ESP-La Liga"`)
- **season** (str): Temporada en formato `"YYYY-YY"`
- **home_team** (str): Nombre del equipo local
- **away_team** (str): Nombre del equipo visitante
- **match_date** (str): Fecha del partido en formato `"YYYY-MM-DD"`

#### Retorno
Tipo: `Dict[str, pd.DataFrame]`
- `'status'`: 'complete' si exitoso
- `'events_count'`: Número total de eventos procesados

#### Archivos Generados
- `viz/data/match_events.csv`
- `viz/data/match_aggregates.csv`
- `viz/data/player_network.csv`
- `viz/data/spatial_analysis.csv`
- `viz/data/match_info.csv`

---

## Pipeline de Enriquecimiento

El pipeline aplica las siguientes transformaciones en orden:

### 1. Detección de Carries
- Identifica secuencias de posesión continua
- Añade eventos tipo "Carry" entre pases
- Trackea take-ons exitosos durante el carry

### 2. Cálculo de xThreat
- Aplica grid 12x8 con interpolación bilineal
- Calcula diferencia de threat entre origen y destino
- Campo `xthreat_gen` solo valores positivos

### 3. Detección de Pre-Assists
- Identifica pases que llevan a una asistencia
- Marca con `is_pre_assist = True`

### 4. Cadenas de Posesión
- Asigna `possession_id` único por secuencia
- Detecta cambios de equipo y período

### 5. Acciones Progresivas
- Criterios específicos por zona del campo:
  - Campo propio: 30m hacia portería rival
  - Cruzar medio campo: 15m mínimo
  - Campo rival: 10m hacia portería

### 6. Entradas al Área
- Detecta pases/carries que terminan en área rival
- Coordenadas área: x >= 83, 21.1 <= y <= 78.9

### 7. Clasificación de Pases
- `pass_outcome`: Goal, Shot, Assist, Key Pass, Retention, Unsuccessful

### 8. Clasificación de Acciones
- `action_type`: Offensive, Defensive, Neutral

### 9. Clasificación por Zonas
- 18 zonas (grilla 6x3)
- `zone_id`: 1-18 según posición en campo

### 10. Merge con xG de Understat
- Match por minuto y equipo
- Fuzzy matching ±2 minutos si no hay match exacto

---

## CSVs Generados

## 1. match_events.csv

**Descripción**: Todos los eventos del partido con enriquecimiento completo.

**Estructura**: 1810 filas × 55 columnas

### Campos Principales

#### IDENTIFICACIÓN (9 campos)
```python
{
    'game_id': int64,                # ID único del partido
    'match_id': int64,               # Duplicado de game_id
    'period': str,                   # "FirstHalf", "SecondHalf", "PostGame"
    'minute': float64,               # Minuto del evento (0-94)
    'second': float64,               # Segundo exacto
    'expanded_minute': int64,        # Minuto expandido (considera añadido)
    'team_id': int64,                # ID del equipo (53=Athletic, 65=Barcelona)
    'team': str,                     # Nombre del equipo
    'player_id': float64,            # ID del jugador (NaN para eventos equipo)
    'player': str                    # Nombre del jugador
}
```

#### TIPO Y RESULTADO (6 campos)
```python
{
    'type': str,                     # Tipo original WhoScored
    'event_type': str,               # Tipo normalizado
    'outcome_type': str,             # "Successful" o "Unsuccessful"
    'is_successful': bool,           # Simplificación de outcome
    'action_type': str,              # "Offensive", "Defensive", "Neutral"
    'field_zone': str                # Zona descriptiva (ej: "Middle_Center")
}
```

#### COORDENADAS (8 campos)
```python
{
    'x': float64,                    # Posición X inicial (0-100)
    'y': float64,                    # Posición Y inicial (0-100)
    'end_x': float64,                # Posición X final (pases/carries)
    'end_y': float64,                # Posición Y final
    'goal_mouth_y': float64,         # Y en línea de gol (solo shots)
    'goal_mouth_z': float64,         # Altura del disparo
    'blocked_x': float64,            # X donde fue bloqueado
    'blocked_y': float64             # Y donde fue bloqueado
}
```

#### MÉTRICAS CALCULADAS (11 campos)
```python
{
    'distance_to_goal': float64,     # Distancia euclidiana a portería
    'pass_distance': float64,        # Distancia del pase/carry
    'xthreat': float64,              # Diferencia de threat (-0.55 a 0.63)
    'xthreat_gen': float64,          # Threat generado (solo positivo)
    'xg': float64,                   # Expected Goals del disparo
    'possession_id': int64,          # ID de la posesión
    'possession_team': str,          # Equipo en posesión
    'zone_id': int64,                # ID de zona (1-18)
    'is_progressive': bool,          # Si es acción progresiva
    'is_box_entry': bool,            # Si entra al área
    'is_pre_assist': bool            # Si es pre-asistencia
}
```

#### METADATOS (9 campos)
```python
{
    'qualifiers': str,               # JSON con calificadores detallados
    'next_player': str,              # Receptor del pase
    'pass_outcome': str,             # Resultado del pase
    'event_id': float64,             # ID del evento carry (x.5)
    'take_ons_in_carry': float64,   # Take-ons durante el carry
    'is_assist': bool,               # Si es asistencia
    'is_shot': str,                  # "True" si es disparo
    'is_goal': str,                  # "True" si es gol
    'data_source': str               # Siempre "whoscored"
}
```

---

## 2. match_aggregates.csv

**Descripción**: Agregaciones por jugador y zona con separación perfecta de métricas.

**Estructura**: 68 filas × 36 columnas (32 jugadores + 36 zonas)

### Campos Comunes (Jugadores y Zonas)

#### IDENTIFICACIÓN (4 campos)
```python
{
    'entity_type': str,              # "player" o "zone"
    'entity_id': str,                # ID único (nombre o team_zone_X)
    'entity_name': str,              # Nombre descriptivo
    'team': str                      # Equipo
}
```

#### ACTIVIDAD (5 campos)
```python
{
    'total_actions': int64,          # Total de acciones
    'offensive_actions': int64,      # Acciones ofensivas
    'defensive_actions': int64,      # Acciones defensivas
    'neutral_actions': int64,        # Acciones neutrales
    'box_entries': int64             # Entradas al área
}
```

#### MÉTRICAS THREAT (2 campos)
```python
{
    'xthreat_total': float64,        # xThreat total generado
    'xthreat_per_action': float64    # xThreat promedio por acción
}
```

### Campos Exclusivos Jugadores (19 campos)

```python
{
    # TIEMPO Y RITMO
    'minutes_active': float64,       # Minutos en campo
    'actions_per_minute': float64,   # Ritmo de juego
    
    # POSICIONAMIENTO
    'avg_x': float64,                # Posición promedio X
    'avg_y': float64,                # Posición promedio Y
    'position_variance_x': float64,  # Varianza posicional X
    'position_variance_y': float64,  # Varianza posicional Y
    
    # PASES
    'passes_attempted': float64,     # Pases intentados
    'passes_completed': float64,     # Pases completados
    'pass_completion_pct': float64,  # % completado
    'progressive_passes': float64,   # Pases progresivos
    'pre_assists': float64,          # Pre-asistencias
    
    # CARRIES
    'carries': float64,              # Total carries
    'progressive_carries': float64,  # Carries progresivos
    'carry_distance_total': float64, # Distancia total
    
    # RESULTADOS DE PASES
    'passes_to_goal': float64,       # Pases que terminan en gol
    'passes_to_shot': float64,       # Pases que terminan en tiro
    'key_passes': float64            # Pases clave
}
```

### Campos Exclusivos Zonas (8 campos)

```python
{
    # IDENTIFICACIÓN ESPACIAL
    'zone_id': float64,              # ID de zona (1-18)
    'zone_x_center': float64,        # Centro X de la zona
    'zone_y_center': float64,        # Centro Y de la zona
    
    # CONTROL Y PRESIÓN
    'possession_pct': float64,       # % posesión del equipo
    'action_density': float64,       # Acciones por minuto
    'progressive_actions': float64,  # Acciones progresivas
    
    # FLUJO DE PASES
    'passes_through_zone': float64,  # Pases por la zona
    'successful_passes': float64     # Pases exitosos
}
```

---

## 3. player_network.csv

**Descripción**: Red de pases y posiciones para visualización de conexiones.

**Estructura**: 258 filas × 18 columnas (226 conexiones + 32 posiciones)

### Campos Principales

#### IDENTIFICACIÓN (5 campos)
```python
{
    'record_type': str,              # "connection" o "position"
    'team': str,                     # Equipo
    'source_player': str,            # Jugador origen
    'target_player': str,            # Jugador destino (None para position)
    'connection_id': str             # ID único de conexión
}
```

#### MÉTRICAS DE CONEXIÓN (7 campos)
```python
{
    'connection_strength': int64,    # Número de pases entre jugadores
    'avg_xthreat': float64,          # xThreat promedio de conexión
    'progressive_passes': int64,     # Pases progresivos
    'box_entries': int64,            # Entradas al área
    'pass_distance_avg': float64     # Distancia promedio
}
```

#### COORDENADAS (4 campos)
```python
{
    'avg_x_start': float64,          # X promedio origen
    'avg_y_start': float64,          # Y promedio origen
    'avg_x_end': float64,            # X promedio destino
    'avg_y_end': float64             # Y promedio destino
}
```

#### DATOS DE POSICIÓN (solo type="position", 4 campos)
```python
{
    'total_actions': float64,        # Total acciones del jugador
    'minutes_active': float64,       # Minutos jugados
    'position_variance_x': float64,  # Varianza X
    'position_variance_y': float64   # Varianza Y
}
```

---

## 4. spatial_analysis.csv

**Descripción**: Análisis espacial avanzado con 4 tipos de métricas.

**Estructura**: 50 filas × 29 columnas

### Tipos de Análisis

#### 1. CONVEX HULL (2 registros)
Forma del equipo en el campo
```python
{
    'coordinates_json': str,         # Lista de puntos del hull
    'hull_area': float64,            # Área del hull
    'hull_perimeter': float64,       # Perímetro
    'center_x': float64,             # Centro X del equipo
    'center_y': float64,             # Centro Y del equipo
    'area_percentage': float64       # % del campo cubierto
}
```

#### 2. PRESSURE MAP (36 registros)
Presión por zona (18 por equipo)
```python
{
    'zone_id': float64,              # ID de zona (1-18)
    'zone_center_x': float64,        # Centro X de zona
    'zone_center_y': float64,        # Centro Y de zona
    'pressure_intensity': float64,   # Intensidad de presión (0-0.13)
    'action_efficiency': float64,    # Eficiencia de acciones
    'avg_xthreat': float64,          # xThreat promedio
    'xthreat_total': float64,        # xThreat total
    'progressive_actions': float64   # Acciones progresivas
}
```

#### 3. TERRITORIAL CONTROL (6 registros)
Control por tercios del campo
```python
{
    'third_name': str,               # "defensive", "middle", "attacking"
    'x_range_min': float64,          # Límite X inferior
    'x_range_max': float64,          # Límite X superior
    'control_percentage': float64,   # % de control
    'avg_xthreat_per_action': float64, # xThreat por acción
    'box_entries': float64           # Entradas al área
}
```

#### 4. FLOW PATTERN (6 registros)
Patrones direccionales de juego
```python
{
    'flow_direction': str,           # "forward", "backward", "lateral"
    'pass_count': float64,           # Número de pases
    'avg_distance': float64,         # Distancia promedio
    'avg_xthreat': float64,          # xThreat promedio (puede ser negativo)
    'progressive_count': float64,    # Pases progresivos
    'flow_efficiency': float64       # Ratio progresivos/total
}
```

---

## 5. match_info.csv

**Descripción**: Metadata y contexto del partido para dashboards.

**Estructura**: 90 filas × 11 columnas

### Categorías de Información

#### MATCH_METADATA (8 registros)
```python
{
    'info_key': str,                 # Tipo de metadata
    'info_value': str,               # Valor
    # Keys: match_id, home_team, away_team, match_date, 
    #       league, season, total_events, match_duration_minutes
}
```

#### TEAM_STATS (20 registros, 10 por equipo)
```python
{
    'team': str,                     # Equipo
    'numeric_value': float64,        # Valor numérico
    # Keys: total_events, possession_pct, passes_attempted,
    #       passes_completed, pass_accuracy, xthreat_total,
    #       progressive_actions, box_entries, shots, xg_total
}
```

#### PLAYER_PARTICIPATION (32 registros)
```python
{
    'info_value': str,               # Nombre del jugador
    'team': str,                     # Equipo
    'first_minute': float64,         # Primera aparición
    'last_minute': float64,          # Última aparición
    'minutes_active': float64,       # Minutos activos
    'numeric_value': float64         # Total acciones
}
```

#### TIMELINE (24 registros)
```python
{
    'info_value': str,               # Descripción del evento
    'event_type': str,               # Tipo (Goal, Card, Substitution)
    'minute': float64,               # Minuto del evento
    'period': str,                   # Período
    'team': str                      # Equipo involucrado
}
```

#### DATA_QUALITY (6 registros)
```python
{
    'info_key': str,                 # Métrica de calidad
    'numeric_value': float64         # Valor
    # Keys: events_with_coordinates, events_with_xthreat,
    #       events_with_outcome, successful_events,
    #       unique_players, periods_played
}
```

---

## Ejemplo de Uso

```python
from viz.match_data import extract_match_complete

# Procesar partido completo
result = extract_match_complete(
    ws_id=1821769,
    us_id=16364,
    league="ESP-La Liga",
    season="2024-25",
    home_team="Athletic Club",
    away_team="Barcelona",
    match_date="2024-08-24"
)

# Output:
# 1. match_events.csv: 1810 events
# 2. match_aggregates.csv: 68 records
# 3. player_network.csv: 258 records
# 4. spatial_analysis.csv: 50 spatial records
# 5. match_info.csv: 90 info records
# 5 optimized visualization CSVs saved to: viz/data
```

## Notas de Implementación

1. **Separación de Datos**: Los campos NULL indican separación limpia entre tipos de entidad (jugador vs zona)

2. **Optimización para Viz**: 
   - Coordenadas redondeadas a 2 decimales
   - Métricas agregadas pre-calculadas
   - JSON procesable para coordenadas complejas

3. **Compatibilidad**: Todos los CSVs están diseñados para ser consumidos directamente por librerías de visualización (D3.js, Plotly, etc.)

4. **Performance**: El pipeline procesa ~2000 eventos en <5 segundos con todas las transformaciones