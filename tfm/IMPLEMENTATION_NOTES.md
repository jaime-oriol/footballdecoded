# TFM Algorithms - Implementation Notes

## Contexto General

Este documento resume la implementación de los algoritmos de machine learning para validar decisiones data-driven de fichajes (TFM - Trabajo Fin de Master).

**Objetivo**: Validar si las cadenas de sustitución de Villarreal, Eintracht Frankfurt y LOSC Lille siguen patrones estadísticos.

**Ejemplo**: Nicolas Jackson (vendido 37M€) → Alexander Sørloth (fichado 10M€)
**Pregunta**: ¿Son estadísticamente similares?

---

## Metodología: División de Responsabilidades

### NOTEBOOK (usuario hace):
1. **Query DB** con filtros (liga, posición, valor_mercado, temporada X-1)
2. **Extracción JSONB** (`fbref_metrics`, `understat_metrics`)
3. **Normalización per90** (exacto como `Etta_Eyong_radars.ipynb`)
4. **Combinar métricas** → DF con ~356 columnas listo
5. **Llamar algoritmo**: `find_similar_players_X(df, target_id)`

### ALGORITMO (implementado):
1. Recibir DF procesado
2. Seleccionar features automáticamente
3. Manejar NaNs
4. Escalar
5. Aplicar técnica (K-Means o PCA + Coseno)
6. Devolver top-N similares

---

## Algoritmos Implementados

### 1. K-Means Clustering (`kmeans_similarity.py`)

**Archivo**: `/home/jaime/FD/data/tfm/algorithms/kmeans_similarity.py`

**Firma**:
```python
def find_similar_players_kmeans(
    df: pd.DataFrame,          # DF procesado con métricas per90
    target_player_id: str,     # unique_player_id (YA está en df)
    n_similar: int = 10,
    k_clusters: int = None,    # None = método del codo
    use_pca: bool = False
) -> Dict
```

**Pipeline (8 pasos)**:
1. Validar target
2. Seleccionar features automáticamente (per90 + % + ratios)
3. Manejar NaNs (Understat → 0, FBref → drop)
4. Extraer matriz
5. Escalar (StandardScaler)
6. PCA opcional
7. Método del codo (si k=None)
8. K-Means + distancias euclidianas

**Output**:
```python
{
    'target_cluster': int,
    'similar_players': DataFrame,  # Top-N con distancias
    'cluster_info': {...},         # n_players, avg_distance, silhouette
    'distances_distribution': {...},  # min, q25, median, q75, max
    'metadata': {...}
}
```

**Criterios TFM**:
- ✅ Co-pertenencia: Target y reemplazo en mismo cluster
- ✅ Distancia Q1: Distancia euclidiana ≤ Q25
- ✅ Silhouette: > 0.3

---

### 2. PCA + Cosine Similarity (`pca_cosine_similarity.py`)

**Archivo**: `/home/jaime/FD/data/tfm/algorithms/pca_cosine_similarity.py`

**Firma**:
```python
def find_similar_players_cosine(
    df: pd.DataFrame,
    target_player_id: str,
    n_similar: int = 10,
    pca_variance: float = 0.85,    # 85% varianza retenida
    return_all_scores: bool = False
) -> Dict
```

**Pipeline (7 pasos)**:
1. Validar target
2. Seleccionar features automáticamente
3. Manejar NaNs
4. Extraer matriz
5. Escalar (StandardScaler)
6. PCA (reducir dimensiones)
7. Similitud coseno con TODOS

**Output**:
```python
{
    'similar_players': DataFrame,     # Top-N con cosine_similarity
    'all_scores': DataFrame,          # TODOS (si return_all_scores=True)
    'score_distribution': {...},      # min, q5, q25, median, q75, q95, max
    'pca_info': {...},                # n_components, varianza, reducción
    'metadata': {...}
}
```

**Criterios TFM**:
- ✅ Top-5: Reemplazo en top-5 (percentil ≤ 5)
- ✅ Similitud alta: cosine_similarity > Q75

---

## Selección Automática de Features

Ambos algoritmos usan la misma lógica:

```python
# Todas las _per90
per90_cols = [col for col in df.columns if col.endswith('_per90')]

# Porcentajes y ratios
pct_cols = [col for col in df.columns
            if any(x in col for x in ['%', '_pct', '/Sh', 'AvgLen', 'AvgDist'])]

# Understat ratios
understat_ratios = [col for col in df.columns
                    if 'understat_buildup_involvement_pct' in col]

# Combinar
feature_cols = list(set(per90_cols + pct_cols + understat_ratios))
```

**Resultado**: ~160 features usados automáticamente

---

## Manejo de NaNs

**Understat (faltante válido)**:
- Muchos jugadores no tienen datos Understat (solo 5 ligas)
- Solución: `df[col].fillna(0)`

**FBref (error)**:
- NaN en FBref indica problema de extracción
- Solución: `df.dropna(subset=fbref_cols)`

---

## Ejemplo de Uso

Ver notebook completo: `/home/jaime/FD/data/tfm/example_kmeans_usage.ipynb`

```python
import pandas as pd
import sys
sys.path.append('..')

from database.connection import get_db_manager
from tfm.algorithms import find_similar_players_kmeans, find_similar_players_cosine

# 1. Query DB (La Liga 22/23, delanteros)
db = get_db_manager()
query = """
SELECT unique_player_id, player_name, team, league, season, position,
       fbref_metrics, understat_metrics
FROM footballdecoded.players_domestic
WHERE league = 'ESP-La Liga' AND season = '2223'
  AND position LIKE '%FW%'
"""
df_raw = pd.read_sql(query, db.engine)

# 2. Extracción JSONB (función del notebook Etta_Eyong_radars.ipynb)
fbref_nums = extract_metrics(df_raw, 'fbref_metrics')
understat_nums = extract_metrics(df_raw, 'understat_metrics')

# 3. Normalización per90
exclude_per90 = {'pass_completion_pct', 'shots_per_90', 'minutes_played', ...}
fbref_per90 = (fbref_nums[~exclude].div(fbref_nums['minutes_played'], axis=0) * 90)
understat_per90 = (understat_nums[~exclude].div(fbref_nums['minutes_played'], axis=0) * 90)

# 4. Combinar
df_final = pd.concat([
    df_raw[['unique_player_id', 'player_name', 'team', 'league', 'season', 'position']],
    fbref_nums, understat_nums, fbref_per90, understat_per90
], axis=1)

# 5. Ejecutar algoritmos
jackson_id = 'abc123'

# K-Means
result_kmeans = find_similar_players_kmeans(df_final, jackson_id, n_similar=10)
print(result_kmeans['similar_players'])

# Cosine
result_cosine = find_similar_players_cosine(df_final, jackson_id, n_similar=10)
print(result_cosine['similar_players'])
```

---

## Validación de Cadenas

**13 cadenas documentadas en `tfm/tfm.md`**:

Ejemplo:
```
Nicolas Jackson (22/23) → Alexander Sørloth (22/23)
- Vendido: 37M€ (Chelsea)
- Fichado: 10M€ (desde Real Sociedad)
- Beneficio: +27M€
```

**Proceso de validación**:
1. Query liga/temporada X-1 con filtros (posición, valor)
2. Normalizar per90
3. Ejecutar AMBOS algoritmos
4. Verificar criterios:
   - K-Means: mismo cluster + distancia ≤ Q25 + silhouette > 0.3
   - Cosine: top-5 + similitud > Q75

**Éxito global**: Mínimo 10/13 cadenas (≥77%) con criterios cumplidos

---

## Archivos Críticos

### Algoritmos
- `/home/jaime/FD/data/tfm/algorithms/__init__.py` - Exports
- `/home/jaime/FD/data/tfm/algorithms/kmeans_similarity.py` - K-Means
- `/home/jaime/FD/data/tfm/algorithms/pca_cosine_similarity.py` - PCA + Coseno

### Referencias
- `/home/jaime/FD/data/tfm/tfm.md` - Documento TFM completo
- `/home/jaime/FD/data/tfm/Etta_Eyong_radars.ipynb` - Lógica de normalización
- `/home/jaime/FD/data/tfm/example_kmeans_usage.ipynb` - Ejemplo completo

### Plan
- `/home/jaime/.claude/plans/parsed-finding-cocoa.md` - Plan detallado

---

## Próximos Pasos

1. **Probar algoritmos** con cadenas reales del TFM
2. **Ajustar hiperparámetros** si es necesario:
   - K-Means: k_range, silhouette threshold
   - Cosine: pca_variance, top-N threshold
3. **Ejecutar validación completa** de 13 cadenas
4. **Análisis de resultados**:
   - Tasa de éxito global
   - Comparar ambos algoritmos
   - Triangulación de resultados
5. **Documentar hallazgos** en TFM

---

## Decisiones Técnicas Clave

1. **Features automáticos**: Algoritmo decide qué métricas usar (todas las per90 + %)
2. **PCA opcional en K-Means**: Solo si dataset pequeño (<50 jugadores)
3. **PCA obligatorio en Cosine**: Siempre reduce dimensiones (85% varianza)
4. **Método del codo**: Busca k óptimo en rango 3-8 (threshold 20%)
5. **Distancias euclidianas**: K-Means (dentro del cluster)
6. **Similitud coseno**: Rango TODOS los jugadores (0-1 scale)

---

## Notas de Implementación

- **Regla X-1**: Usar temporada X-1 para analizar fichajes de temporada X
- **Ejemplo**: Jackson vendido en verano 2023 → analizar temporada 22/23
- **Understat coverage**: Solo 5 ligas (Big 5), no Champions League
- **Transfermarkt**: Útil para filtrar por valor de mercado
- **PostgreSQL**: Base de datos con JSONB para métricas
- **Conda env**: `footballdecoded` (ver CONDA_SETUP.md)

---

**Fecha creación**: 2025-12-02
**Última actualización**: 2025-12-02
**Autor**: Claude Code (implementación) + Jaime (diseño TFM)
