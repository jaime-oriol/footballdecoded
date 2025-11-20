# Player Similarity System - UMAP + GMM

Sistema no supervisado de similitud de jugadores para identificación de reemplazos potenciales y análisis de arquetipos. Combina reducción dimensional (UMAP) con clustering probabilístico (GMM) sobre 220+ métricas normalizadas.

## Fundamento Científico

**Problema**: Identificar jugadores similares sin etiquetas previas, encontrar reemplazos potenciales y validar cadenas de transferencias.

**Solución**: Pipeline UMAP + GMM que descubre patrones ocultos en datos multidimensionales, asigna probabilidades de similitud (no decisiones binarias) y caracteriza arquetipos de jugadores.

**Ventajas vs K-Means/PCA**:
- UMAP preserva estructura local y global (PCA solo global, t-SNE solo local)
- GMM retorna probabilidades soft (K-Means solo hard assignments)
- Selección automática número clusters via BIC
- Más realista para scouting: jugadores pueden tener múltiples roles

## Arquitectura Sistema

```
PostgreSQL DB (220+ metrics)
        |
        v
DataPreparator (extracción, limpieza, outliers)
        |
        v
FeatureEngineer (selección, normalización por posición)
        |
        v
UMAPReducer (220+ features -> 5-10D embedding)
        |
        v
GMMClusterer (identificación arquetipos probabilística)
        |
        v
PlayerSimilarity (búsqueda multi-criterio)
        |
        v
[Validation + Visualization]
```

## Instalación

```bash
# Instalar dependencias
conda activate footballdecoded
pip install umap-learn scikit-learn scipy

# Verificar instalación
python -c "from similarity import PlayerSimilarity; print('OK')"
```

## Uso Rápido

```python
from similarity import DataPreparator, FeatureEngineer, UMAPReducer, GMMClusterer, PlayerSimilarity
from database.connection import get_db_manager

# 1. PREPARAR DATOS
db = get_db_manager()
prep = DataPreparator(db, table_type='domestic')
df = prep.load_players(['ESP-La Liga', 'ENG-Premier League'], '2526', 'FW', min_minutes=600)
df = prep.extract_all_metrics()
df = prep.handle_missing_values(strategy='median_by_position')
df = prep.detect_outliers(method='isolation_forest')

# 2. FEATURE ENGINEERING
eng = FeatureEngineer(position_type='FW')
df = eng.select_relevant_features(df, exclude_gk_metrics=True)
df = eng.remove_correlated_features(df, threshold=0.95)
df = eng.normalize_by_position(df, method='standard', fit_per_position=True)
X, metadata = eng.prepare_for_umap(df, return_dataframe=True)

# 3. UMAP
umap = UMAPReducer(n_components=5, n_neighbors=20, min_dist=0.0)
X_umap = umap.fit_transform(X, verbose=True)

# 4. GMM
gmm = GMMClusterer(covariance_type='full')
optimal = gmm.find_optimal_clusters(X_umap, min_clusters=3, max_clusters=12, criterion='bic')
gmm.fit(X_umap, n_components=optimal['optimal_n'])

# 5. SIMILITUD
embedding_df = umap.get_embedding_dataframe(metadata)
sim = PlayerSimilarity(
    embedding_df=embedding_df,
    gmm_proba=gmm.labels_proba,
    feature_df=df,
    weights={'umap_distance': 0.50, 'gmm_probability': 0.30, 'feature_similarity': 0.20}
)

# Buscar similares
similar = sim.find_similar_players('player_id', top_n=10, filters={'exclude_same_team': True})
print(similar[['player_name', 'team', 'similarity_score']])
```

## Casos de Uso

### 1. Encontrar Alternativas Baratas

```python
# Ejemplo: Alternativas a Kolo Muani pre-venta 95M
kolo_muani_id = embedding_df[embedding_df['player_name'].str.contains('Kolo Muani')]['unique_player_id'].iloc[0]

alternatives = sim.find_similar_players(
    kolo_muani_id,
    top_n=20,
    filters={'max_age': 26, 'exclude_same_league': True}
)
```

### 2. Validar Cadena Reemplazos

```python
# Ejemplo: Sorloth (20M) sustituye a Jackson (37M)?
chain = [sorloth_id, jackson_id]
validation = sim.validate_replacement_chain(chain, min_similarity=0.65)
print(validation)
```

### 3. Identificar Arquetipos

```python
# Caracterizar clusters
profiles = gmm.get_cluster_profiles(X, feature_names=eng.selected_features, top_n_features=10)
print(profiles[profiles['cluster_id'] == 0])

# Jugadores prototípicos de arquetipo
representatives = sim.find_cluster_representatives(cluster_id=0, n_representatives=5)
```

## Módulos

### DataPreparator

Extrae datos PostgreSQL, convierte JSON a DataFrame numérico, maneja valores faltantes y detecta outliers.

**Métodos clave**:
- `load_players()`: Query SQL con filtros (liga, temporada, posición, minutos)
- `extract_all_metrics()`: Convierte fbref_metrics/understat_metrics a columnas
- `handle_missing_values()`: Imputation por posición (median/mean)
- `detect_outliers()`: Isolation Forest multivariante

**Decisiones**: Median imputation robusto a outliers. Filtro >= 5 valores válidos por métrica.

### FeatureEngineer

Selecciona features relevantes por posición, elimina redundancias, normaliza por posición.

**Métodos clave**:
- `select_relevant_features()`: Filtro posición + varianza mínima
- `remove_correlated_features()`: Elimina features |corr| > threshold
- `normalize_by_position()`: StandardScaler separado por posición (CRÍTICO)
- `get_feature_importance()`: Ranking por varianza normalizada

**Decisiones**: Normalización por posición esencial (DF vs FW escalas diferentes). Features predefinidas por posición basadas en análisis fútbol.

### UMAPReducer

Reduce dimensionalidad 220+ features a 5-10D preservando estructura local y global.

**Métodos clave**:
- `fit_transform()`: Fit UMAP y transforma datos
- `transform()`: Transforma nuevos datos (útil añadir jugadores)
- `validate_embedding_stability()`: Multiple runs para verificar robustez
- `optimize_hyperparameters()`: Grid search BIC-guided
- `get_feature_contribution()`: Correlación features -> componentes UMAP

**Hiperparámetros recomendados**:
- `n_components=5-10`: Balance información/ruido
- `n_neighbors=15-30`: Trade-off estructura local/global
- `min_dist=0.0-0.1`: Clusters compactos vs dispersos
- `metric='euclidean'`: Estándar para features normalizadas

**Decisiones**: UMAP > t-SNE (más rápido, estructura global, transform nuevos datos). UMAP > PCA (captura no-linealidades).

### GMMClusterer

Clustering probabilístico GMM. Identifica arquetipos jugadores.

**Métodos clave**:
- `find_optimal_clusters()`: BIC/AIC para seleccionar n_clusters óptimo
- `fit()`: Fit GMM con EM algorithm
- `predict_proba()`: Probabilidades cluster (soft assignments)
- `get_cluster_profiles()`: Top features distintivas por cluster
- `cluster_stability()`: Bootstrap validation (ARI metric)

**Criterios selección**:
- BIC (Bayesian Information Criterion): Penaliza complejidad, conservador
- AIC (Akaike Information Criterion): Menos penalización
- Silhouette: Métrica geométrica alternativa

**Decisiones**: GMM > K-Means (probabilidades soft, clusters elípticos, no esféricos). BIC preferido (evita overfitting). Covariance 'full' máxima flexibilidad.

### PlayerSimilarity

Motor búsqueda similitud multi-criterio. API principal usuario.

**Métodos clave**:
- `find_similar_players()`: Top N similares con filtros contextuales
- `validate_replacement_chain()`: Verifica coherencia cadena A -> B -> C
- `get_similarity_matrix()`: Matriz NxN para análisis múltiples jugadores
- `find_cluster_representatives()`: Jugadores prototípicos arquetipo
- `explain_similarity()`: Interpretabilidad (por qué son similares)

**Score combinado**:
```
similarity = 0.50 * umap_distance_score +
             0.30 * gmm_probability_score +
             0.20 * feature_similarity_score
```

Pesos ajustables según prioridad análisis.

**Filtros disponibles**:
- `exclude_same_team/league`: Excluir mismo equipo/liga
- `max_age/min_age`: Rango edad
- `position`: Filtro posición (debe empezar con)
- `leagues`: Lista ligas permitidas

**Decisiones**: Score multi-componente más robusto que distancia única. Filtros contextuales esenciales para scouting real.

### PipelineValidator

Validación estadística end-to-end.

**Métodos**:
- `add_ground_truth_pair()`: Define pares conocidos similares
- `validate_known_pairs()`: Verifica recall@K para ground truth
- `generate_validation_report()`: Reporte agregado + recomendaciones

**Métricas**: Recall@K (% pares encontrados en top K). Objetivo: recall@10 > 80%.

### SimilarityVisualizer

Plots científicos (matplotlib + seaborn).

**Métodos**:
- `plot_umap_embedding()`: Scatter 2D con clusters GMM
- `plot_similarity_heatmap()`: Heatmap matriz NxN
- `plot_cluster_profiles()`: Bar plots features distintivas
- `plot_feature_importance()`: Ranking importancia features
- `plot_validation_metrics()`: Recall curves, distribución ranks

**Estilo**: Científico (sin decoraciones), publicación-ready, alta resolución.

## Hiperparámetros Críticos

### UMAP
- `n_components`: 5 (clustering), 2-3 (visualización)
- `n_neighbors`: 20 (balance general)
- `min_dist`: 0.0 (clusters compactos para GMM)

### GMM
- `n_components`: Auto via BIC (típicamente 5-12 para FW)
- `covariance_type`: 'full' (máxima flexibilidad)
- `max_iter`: 200 (suficiente convergencia)

### Similarity
- `weights`: {'umap_distance': 0.50, 'gmm_probability': 0.30, 'feature_similarity': 0.20}

## Validación Calidad

**UMAP estabilidad**: mean_correlation > 0.7 entre múltiples runs

**GMM estabilidad**: mean_ARI > 0.7 en bootstrap

**Similitud precision**: recall@10 > 80% para ground truth pairs

**Interpretabilidad**: Cluster profiles consistentes con conocimiento fútbol

## Troubleshooting

**Problema**: Low UMAP stability (< 0.7)
**Solución**: Aumentar `n_neighbors`, reducir `min_dist`, o aumentar datos

**Problema**: GMM no converge
**Solución**: Reducir `n_components`, cambiar `covariance_type='tied'`, aumentar `max_iter`

**Problema**: Clusters vacíos
**Solución**: Reducir n_clusters, verificar outliers no removidos

**Problema**: Similitud baja recall@10
**Solución**: Ajustar pesos similarity, revisar normalización por posición, aumentar UMAP components

## Performance

**Datos**: ~500 jugadores FW Big 5, 220 features
**Tiempo UMAP**: ~30 segundos (n_components=5)
**Tiempo GMM**: ~10 segundos (n_components=8)
**Búsqueda similitud**: < 1 segundo (vectorizado)

Escalable a ~5000 jugadores sin optimización adicional.

## Referencias Literatura

1. McInnes, Healy, Melville (2018): UMAP: Uniform Manifold Approximation and Projection
2. Schwarz (1978): Estimating the dimension of a model (BIC)
3. Fraley & Raftery (2002): Model-Based Clustering, Discriminant Analysis, and Density Estimation
4. Pappalardo et al. (2019): PlayeRank: data-driven performance evaluation and player ranking in soccer
5. Decroos et al. (2019): Actions speak louder than goals: Valuing player actions in soccer (VAEP)
6. Brooks, Kerr, Guttag (2016): Using machine learning to quantify talent in professional basketball
7. Little & Rubin (2002): Statistical Analysis with Missing Data
8. Becht et al. (2019): Dimensionality reduction for visualizing single-cell data using UMAP
9. Link et al. (2016): Real-time quantification of dangerousness in football
10. Vinh, Epps, Bailey (2010): Information theoretic measures for clusterings comparison (ARI)

## Template Notebook

Ver `umap_gmm_template.ipynb` para workflow completo end-to-end con 35 pasos ejecutables.

## Autor

FootballDecoded - Sistema UMAP + GMM v1.0.0

Implementación profesional adaptada 100% a BD PostgreSQL con 220+ métricas FBref + Understat. Sin emojis, código limpio, documentación científica completa.
