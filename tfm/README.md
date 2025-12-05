# TFM - Validación de Sustituciones con PCA + Cosine Similarity

Módulo para validar decisiones de fichaje mediante similitud estadística entre jugadores.

## Contenido

- `algorithms/pca_cosine_similarity.py`: Algoritmo PCA + Cosine Similarity
- `query_helpers.py`: Funciones para consultar BD con filtros avanzados
- `test_cases.py`: Script de prueba automatizado para casos documentados
- `example_cosine_validation.ipynb`: Notebook ejemplo (caso Baena → Moleiro)
- `tfm.md`: Documento completo del TFM con metodología y casos
- `RESULTADOS_CASOS.md`: Resultados detallados de casos probados

## Instalación

```bash
# Activar entorno
conda activate footballdecoded

# El módulo ya está en el path del proyecto
# No requiere instalación adicional
```

## Uso Rápido

### Opción 1: Wrapper Completo

```python
from tfm.query_helpers import validate_replacement

result = validate_replacement(
    vendido_name='Pau Torres',
    reemplazo_name='Logan Costa',
    season='2324',
    positions=['CB'],
    max_market_value=30_000_000,
    max_age=30,
    min_minutes=1250
)

print(f"Status: {result['replacement_info']['validation_status']}")
print(f"Rank: #{result['replacement_info']['rank']}")
print(f"Similitud: {result['replacement_info']['cosine_similarity']:.4f}")
```

### Opción 2: Pipeline Manual

```python
from tfm.query_helpers import query_player_pool, add_exogenous_player
from tfm.algorithms import find_similar_players_cosine
import pandas as pd
import numpy as np

# 1. Query pool Big 5
big5 = ['ENG-Premier League', 'ESP-La Liga', 'ITA-Serie A', 'GER-Bundesliga', 'FRA-Ligue 1']
pools = []
for league in big5:
    pool = query_player_pool(
        league=league,
        season='2324',
        positions=['CB'],
        max_market_value=30_000_000,
        max_age=30,
        min_minutes=1250
    )
    pools.append(pool)

pool_df = pd.concat(pools, ignore_index=True)

# 2. Añadir target exógeno si necesario
full_df = add_exogenous_player(pool_df, 'Pau Torres', 'ESP-La Liga', '2324', 'Aston Villa')

# 3. Extraer métricas JSONB (ver notebook para función completa)
# ... (código de extract_metrics y calcular per90)

# 4. Ejecutar algoritmo
result = find_similar_players_cosine(
    df=df_final,
    target_player_id=vendido_id,
    n_similar=30,
    replacement_id=reemplazo_id
)
```

## Interpretación de Resultados

### Status de Validación

| Status | Rank | Interpretación |
|--------|------|----------------|
| VALIDADO | 1-10 | Similitud estadística fuerte. Club identificó una de las opciones óptimas. |
| PARCIAL | 11-30 | Similitud moderada. Existen alternativas con mayor proximidad estadística. |
| NO_VALIDADO | >30 | Sin fundamentación estadística clara. Decisión por criterios cualitativos. |

### Scores de Similitud Coseno

- **>0.5**: Similitud fuerte (perfiles muy similares)
- **0.3-0.5**: Similitud moderada (cierta proximidad)
- **<0.3**: Perfiles estadísticamente distantes

## Ejemplo de Output

```python
result = validate_replacement(
    vendido_name='Pau Torres',
    reemplazo_name='Logan Costa',
    season='2324',
    positions=['CB']
)

# result['replacement_info']:
{
    'player_name': 'Logan Costa',
    'rank': 6,
    'cosine_similarity': 0.4936,
    'validation_status': 'VALIDADO',
    'similarity_percentile': 96.3
}

# result['similar_players']: DataFrame con TOP-30
   rank  player_name           team            cosine_similarity  validation_status
   1     Player A              Team A          0.7234            VALIDADO
   2     Player B              Team B          0.6891            VALIDADO
   ...
   6     Logan Costa           Toulouse        0.4936            VALIDADO  ← Reemplazo
   ...
```

## Casos de Uso Recomendados

### Caso 1: Validar Sustitución Ejecutada

```python
# Verificar si un fichaje tuvo fundamentación estadística
result = validate_replacement(
    vendido_name='Gabriel Gudmundsson',
    reemplazo_name='Romain Perraud',
    season='2425',
    positions=['LB']
)

if result['replacement_info']['validation_status'] == 'VALIDADO':
    print("Fichaje con sólida fundamentación data-driven")
```

### Caso 2: Identificar Alternativas Óptimas

```python
# Obtener lista de mejores opciones para reemplazar a un jugador
result = find_similar_players_cosine(
    df=df_final,
    target_player_id=vendido_id,
    n_similar=30
)

top10 = result['similar_players'].head(10)
print("Top-10 alternativas estadísticamente óptimas:")
print(top10[['player_name', 'team', 'cosine_similarity']])
```

### Caso 3: Análisis Multi-Temporada

```python
# Comparar evolución de perfil entre temporadas
for season in ['2223', '2324', '2425']:
    result = validate_replacement(
        vendido_name='Player X',
        reemplazo_name='Player Y',
        season=season,
        positions=['CM']
    )
    print(f"{season}: Rank #{result['replacement_info']['rank']}")
```

## Configuración de Filtros

### Filtros Recomendados por Posición

**Defensas (CB, LB, RB):**
```python
max_market_value=30_000_000  # 30M EUR
max_age=30
min_minutes=1250
```

**Mediocampistas (CDM, CM, CAM):**
```python
max_market_value=35_000_000  # 35M EUR
max_age=29
min_minutes=1500
```

**Delanteros (ST, LW, RW):**
```python
max_market_value=40_000_000  # 40M EUR
max_age=28
min_minutes=1000  # Más lesiones, menos disponibilidad
```

### Posiciones Transfermarkt

Usa `get_positions()` para obtener listas predefinidas:

```python
from tfm.query_helpers import get_positions

get_positions('FULLBACKS')  # ['RB', 'LB']
get_positions('WINGERS')    # ['LW', 'RW']
get_positions('STRIKERS')   # ['ST', 'SS']
get_positions('FW')         # ['LW', 'RW', 'ST', 'SS']
```

## Parámetros del Algoritmo

### `find_similar_players_cosine()`

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `df` | DataFrame | - | DataFrame procesado con métricas per90 |
| `target_player_id` | str | - | ID único del jugador vendido |
| `n_similar` | int | 30 | Número de similares a devolver |
| `pca_variance` | float | 0.85 | Varianza retenida en PCA (0-1) |
| `replacement_id` | str | None | ID del reemplazo (opcional, calcula validación) |
| `robust_scaling` | bool | False | Usar RobustScaler (robusto a outliers) |

### `validate_replacement()`

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `vendido_name` | str | - | Nombre jugador vendido |
| `reemplazo_name` | str | - | Nombre reemplazo |
| `season` | str | - | Temporada formato 'YXYY' (ej: '2324') |
| `positions` | List[str] | - | Posiciones Transfermarkt |
| `max_market_value` | int | 30M | Valor máximo EUR |
| `max_age` | int | 30 | Edad máxima |
| `min_minutes` | int | 1250 | Minutos mínimos jugados |
| `n_similar` | int | 30 | TOP-N a devolver |
| `pca_variance` | float | 0.85 | Varianza PCA |
| `robust_scaling` | bool | False | RobustScaler |

## Información PCA

El algoritmo reduce dimensionalidad de 141 métricas per90 a ~20-29 componentes:

```python
result['pca_info']:
{
    'n_components': 26,
    'explained_variance_ratio': 0.8534,
    'original_dimensions': 141,
    'reduced_dimensions': 26,
    'compression_ratio': 0.184,
    'top_5_components_variance': [0.170, 0.117, 0.086, 0.071, 0.061]
}
```

## Limitaciones

1. **Varianza perdida**: PCA retiene 85%, descarta 15% de información
2. **Similitud coseno mide proporciones**: Dos jugadores con similitud 0.9 pueden tener volúmenes de producción diferentes
3. **No captura factores cualitativos**: Intensidad sin balón, liderazgo, encaje táctico, compatibilidad con compañeros
4. **Solo Big 5 leagues**: Ligas secundarias tienen cobertura limitada de métricas
5. **Understat solo Big 5**: Métricas xG granulares no disponibles para ligas extras

## Métricas Empleadas

Ver **ANEXO A** en `tfm.md` para documentación completa de 169+ métricas:

- **FBref**: 185 métricas (153 per90) - Estadísticas avanzadas
- **Understat**: 10 métricas (7 per90) - xG granular (solo Big 5)
- **Transfermarkt**: 9 campos - Información contractual y mercado

## Test Cases

Ejecuta script de prueba automatizado:

```bash
python tfm/test_cases.py
```

Casos incluidos:
- Pau Torres → Logan Costa (2324, CB)
- Estupiñán → Cardona (2324, LB)
- Gudmundsson → Perraud (2425, LB)

Output esperado:
```
RESUMEN FINAL
Casos probados: 3
VALIDADO (1-10): 3
PARCIAL (11-30): 0
NO_VALIDADO (>30): 0
Éxitos totales: 3
```

## Notebook Ejemplo

Ver `example_cosine_validation.ipynb` para caso completo Baena → Moleiro con:

1. Query pool con filtros
2. Añadir jugador exógeno
3. Extraer métricas JSONB
4. Calcular per90
5. Ejecutar algoritmo
6. Interpretar resultados

## Contacto

Para dudas sobre el módulo, revisar:
- `tfm.md`: Metodología completa
- `RESULTADOS_CASOS.md`: Análisis detallado de casos
- `algorithms/pca_cosine_similarity.py`: Código fuente del algoritmo

## Referencias

- FBref: https://fbref.com/
- Understat: https://understat.com/
- Transfermarkt: https://www.transfermarkt.com/
- StatsBomb: https://statsbomb.com/
