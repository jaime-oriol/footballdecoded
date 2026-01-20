# Eficiencia económica y deportiva en el mercado de fichajes: un análisis data-driven de las 5 grandes ligas europeas (2022–2026)

**Trabajo Fin de Master**

Máster en Big data aplicado al Scouting en Fútbol – Sevilla FC

Sport Data Campus

**Jaime Oriol Goicoechea**

---

## Índice de contenidos

1. [Introducción](#1-introducción) .............................................................................................................................. 3
   - 1.1. [Objetivos del Estudio](#11-objetivos-del-estudio)........................................................................................................... 3
   - 1.2. [Contexto Competitivo](#12-contexto-competitivo) ......................................................................................................... 3
   - 1.3. [Justificación Metodológica](#13-justificación-metodológica) ................................................................................................. 3

2. [Metodología Analítica](#2-metodología-analítica)............................................................................................................... 4
   - 2.1. [Workflow del Algoritmo PCA + Similitud Coseno](#21-workflow-del-algoritmo-pca--similitud-coseno)..................................................................... 4
   - 2.2. [Interpretación de Resultados: Similar ≠ Mejor](#22-interpretación-de-resultados-similar--mejor)....................................................................... 5
   - 2.3. [Factores No Capturados por el Análisis](#23-factores-no-capturados-por-el-análisis)................................................................................. 5

3. [Análisis de Casos: Cadenas de Sustitución](#3-análisis-de-casos-cadenas-de-sustitución)............................................................................... 6
   - 3.1. [Villarreal CF: Modelo de Renovación Continua](#31-villarreal-cf-modelo-de-renovación-continua)................................................................. 6
      - 3.1.1. [Delantero Centro](#311-delantero-centro) ........................................................................................................... 6
      - 3.1.2. [Portero](#312-portero)........................................................................................................................... 6
      - 3.1.3. [Defensa Central](#313-defensa-central) .............................................................................................................. 6
      - 3.1.4. [Lateral Izquierdo](#314-lateral-izquierdo)........................................................................................................... 7
      - 3.1.5. [Mediapunta / Extremo](#315-mediapunta--extremo) .................................................................................................. 7
      - 3.1.6. [Fichajes Estratégicos sin Coste](#316-fichajes-estratégicos-sin-coste)..................................................................................... 7
   - 3.2. [Eintracht Frankfurt: Modelo de Plusvalías Extremas](#32-eintracht-frankfurt-modelo-de-plusvalías-extremas) ....................................................... 7
      - 3.2.1. [Delantero Centro](#321-delantero-centro)........................................................................................................... 7
      - 3.2.2. [Defensa Central](#322-defensa-central)............................................................................................................. 7
   - 3.3. [LOSC Lille: Desarrollo de Canteranos e Importación Selectiva](#33-losc-lille-desarrollo-de-canteranos-e-importación-selectiva)........................................ 8
      - 3.3.1. [Defensa Central](#331-defensa-central) ............................................................................................................. 8
      - 3.3.2. [Mediocampista Defensivo](#332-mediocampista-defensivo) ............................................................................................ 8
      - 3.3.3. [Delantero Centro](#333-delantero-centro) .......................................................................................................... 8
      - 3.3.4. [Producción de Cantera de Alto Valor](#334-producción-de-cantera-de-alto-valor)........................................................................... 8
   - 3.4. [Evolución de Valor de Plantilla y Rendimiento Competitivo](#34-evolución-de-valor-de-plantilla-y-rendimiento-competitivo)........................................... 9
      - 3.4.1. [Villarreal CF](#341-villarreal-cf)................................................................................................................... 9
      - 3.4.2. [LOSC Lille](#342-losc-lille)...................................................................................................................... 9
      - 3.4.3. [Eintracht Frankfurt](#343-eintracht-frankfurt)..................................................................................................... 10
      - 3.4.4. [Comparativa Interliga](#344-comparativa-interliga) ................................................................................................ 10

4. [Resultados del Análisis](#4-resultados-del-análisis)......................................................................................................... 11
   - 4.1. [Resumen Ejecutivo](#41-resumen-ejecutivo)............................................................................................................. 11
   - 4.2. [Villarreal CF](#42-villarreal-cf)........................................................................................................................ 11
   - 4.3. [Eintracht Frankfurt](#43-eintracht-frankfurt)......................................................................................................... 12
   - 4.4. [LOSC Lille](#44-losc-lille)............................................................................................................................. 12
   - 4.5. [Síntesis Comparativa](#45-síntesis-comparativa)....................................................................................................... 13

[ANEXOS](#anexos) ....................................................................................................................................... 14
   - [ANEXO A: Métricas Utilizadas](#anexo-a-métricas-utilizadas)........................................................................................... 14
   - [ANEXO B: Perfiles de Radar por Posición](#anexo-b-perfiles-de-radar-por-posición)...................................................................... 14
   - [ANEXO C: Visualizaciones Completas](#anexo-c-visualizaciones-completas)............................................................................... 14

---

## 1. Introducción

El mercado de fichajes en el fútbol europeo presenta dos modelos claramente diferenciados. Por un lado, los grandes clubes de la Premier League y la Serie A operan con déficits estructurales, priorizando el rendimiento inmediato sobre la sostenibilidad económica. Por otro, un grupo reducido de equipos en La Liga, Bundesliga y Ligue 1 ha desarrollado estrategias data-driven que generan beneficios sistemáticos sin sacrificar competitividad deportiva.

Este trabajo analiza tres casos paradigmáticos de eficiencia en el mercado: **Villarreal CF, Eintracht Frankfurt y LOSC Lille**. Durante el período 2022-2026, estos clubes han generado plusvalías superiores a los 137, 155 y 193 millones de euros respectivamente, manteniendo simultáneamente presencia constante en competiciones europeas y posiciones de media-alta tabla en sus ligas domésticas.

La hipótesis central sostiene que existe un patrón estadísticamente identificable en las decisiones de fichaje de estos equipos, fundamentado en análisis cuantitativo de perfiles de jugadores. A diferencia del modelo italiano —basado en volumen masivo de operaciones pequeñas— o del británico —sustentado en gasto neto elevado—, los casos seleccionados ejecutan cadenas de sustitución estratégicas: venden activos en momentos de máxima valoración y los reemplazan con perfiles estadísticamente similares adquiridos a fracciones del precio de venta.

### 1.1. Objetivos del Estudio

**Objetivo principal:** Demostrar mediante algoritmos de machine learning que las sustituciones exitosas de jugadores responden a patrones cuantificables en datos de rendimiento, validando la existencia de estrategias data-driven replicables.

**Objetivos específicos:**

1. Documentar las cadenas de sustitución históricas (2022-2026) de los tres equipos seleccionados
2. Analizar la evolución del valor de plantilla y rendimiento deportivo en el período estudiado
3. Implementar un algoritmo de similitud basado en PCA y distancia coseno para identificar proximidad estadística entre jugadores vendidos y sus reemplazos
4. Validar mediante ranking de similitud si las sustituciones ejecutadas se fundamentan en proximidad estadística objetiva
5. Identificar las variables más discriminantes en la determinación de sustitutos óptimos

### 1.2. Contexto Competitivo

El análisis preliminar de las cinco grandes ligas europeas revela diferencias estructurales significativas:

**Premier League:** Ecosistema de gasto neto negativo generalizado. 23 de 25 clubes analizados presentan balances deficitarios. Leicester City emerge como outlier estadístico, generando 105M€ mediante cesiones y agentes libres (la temporada pasada), estrategia que resultó en devaluación de plantilla y descenso competitivo.

**Serie A:** Modelo de alta rotación (166-189 altas/bajas por club) basado en acumulación de operaciones de bajo valor. Si bien genera beneficios para equipos, la eficiencia proviene de volumen transaccional más que de precisión analítica. Los clubes estudiados operan principalmente en mitad de tabla sin presencia europea regular.

**La Liga, Bundesliga, Ligue 1:** Villarreal, Frankfurt y Lille operan con 58-90 operaciones en el período, significativamente menos que la Serie A, pero con plusvalías unitarias superiores. Crucialmente, estos equipos mantienen competitividad europea constante, sugiriendo que la eficiencia no compromete el proyecto deportivo.

### 1.3. Justificación Metodológica

La validación de estrategias data-driven requiere demostrar que las decisiones de fichaje responden a criterios cuantificables, no a intuición arbitraria. Idealmente, esto se ejecutaría mediante:

1. **Filtrado contextual previo:** Reducir el universo de jugadores (10,000+) a pools viables (30-50) usando datos de mercado (valor, contrato, situación club)
2. **Comparación estadística:** Analizar similitudes de rendimiento solo entre candidatos realistas

_Sin embargo, esta aproximación es **inviable en contexto académico con fuentes gratuitas**: datos contractuales (años restantes, cláusulas), valores de mercado actualizados y situación financiera de clubes no están disponibles para obtener/scrapear en fuentes gratuitas._

**Enfoque adoptado:**

Ante la imposibilidad de pre-filtrado sistemático, el análisis se centra directamente en las **cadenas de sustitución documentadas** (Sección 2). Para cada reemplazo ejecutado por Villarreal/Frankfurt/Lille, se realiza:

- **Evaluación situacional:** Contexto del jugador vendido y fichado (minutos, rol, nivel de equipo) usando datos públicos disponibles

- **Comparación estadística:** Radares de rendimiento con datos de la temporada inmediatamente anterior al fichaje

- **Análisis de similitud:** Identificación de coincidencias y divergencias en perfiles

Este método replica el análisis post-hoc que un departamento de scouting realizaría para validar sus decisiones, demostrando si las sustituciones se fundamentan en proximidad cuantificable de perfiles o fueron decisiones oportunistas sin criterio estadístico.

**Limitación reconocida:** No permite identificar targets alternativos que los clubes pudieron haber considerado, solo valida si los fichajes ejecutados tienen sentido comparativo con el jugador vendido.

---

## 2. Metodología Analítica

_El diseño metodológico de este trabajo combina análisis descriptivo de cadenas de sustitución documentadas con validación cuantitativa mediante algoritmos de machine learning. Este enfoque dual permite, por un lado, contextualizar las decisiones de fichaje dentro de las restricciones reales del mercado y, por otro, demostrar si dichas decisiones responden a criterios estadísticos objetivos._

**Fuentes de datos.** _La recopilación de información se estructura en tres niveles complementarios. Para datos de rendimiento individual se emplea FBref (estadísticas avanzadas derivadas de StatsBomb) complementado con Understat (métricas xG granulares para Big 5), priorizando métricas normalizadas por 100 toques que permiten comparación entre jugadores independientemente de su volumen de participación. La información transaccional (valores de traspaso, fechas de operación, duración de contratos) proviene de Transfermarkt, base de datos más completa para el período 2022-2026 en acceso público. Finalmente, los datos contextuales sobre rendimiento de equipos (clasificaciones ligueras, participación europea) se extraen de fuentes oficiales de UEFA y las respectivas federaciones nacionales._

**Normalización temporal crítica.** _Para cada sustitución analizada en temporada X, el análisis estadístico utiliza exclusivamente datos de rendimiento de la temporada X-1. Esta restricción metodológica replica las condiciones reales de toma de decisión: cuando el Villarreal fichó a Sørloth en verano 2023 para reemplazar a Jackson, el departamento de scouting solo disponía de las estadísticas 22/23 de ambos jugadores. Cualquier análisis retrospectivo que empleara datos de la temporada 23/24 incurriría en sesgo de información futura (look-ahead bias), invalidando la validación del proceso de decisión._

**Selección de variables.** _El conjunto de métricas empleado abarca cuatro dimensiones del rendimiento posicional: producción ofensiva (goles, asistencias, xG, xA por 90'), contribución en construcción (pases progresivos, pases al área rival, creación de ocasiones), eficiencia técnica (porcentaje de pases completados, toques en área rival) y trabajo defensivo (recuperaciones, intercepciones, duelos ganados). La selección específica de variables se ajusta por demarcación: para delanteros centro se prioriza finalización y movimientos en área; para defensas centrales, métricas de duelo aéreo y anticipación; para mediocampistas, progresión y distribución. Este enfoque posicional evita comparaciones espurias entre perfiles funcionalmente distintos._

**Algoritmo: PCA con Similitud Coseno.** _El método emplea Análisis de Componentes Principales (PCA) para proyectar el espacio de alta dimensionalidad (~150-170 variables per100touches) a un subespacio reducido que retiene 85% de la varianza explicada. El número de componentes resultante (típicamente 20-30) varía según el pool analizado, adaptándose automáticamente a la estructura de los datos. Esta reducción dimensional elimina redundancias estadísticas entre métricas correlacionadas (ej: xG y goles, pases completados con asistencias) conservando la información discriminante entre perfiles. Sobre esta representación simplificada se calcula la similitud coseno entre el vector del jugador vendido y cada jugador del pool de análisis. La similitud coseno oscila entre -1 (perfiles completamente opuestos) y 1 (perfiles idénticos), donde valores cercanos a 1 indican mayor proximidad estadística. Dado que los datos se estandarizan (z-score) antes del PCA, la similitud coseno captura tanto las proporciones relativas entre métricas como la posición del jugador respecto a la media poblacional._

**Sistema de validación por ranking.** _Para cada jugador vendido se genera un ranking completo de similitud coseno sobre la población filtrada (posición, ligas Big 5 + extras, edad ≤30 años, minutos ≥1000). El sistema clasifica el reemplazo ejecutado en tres categorías: (a) VALIDADO si figura en posiciones 1-10 del ranking, demostrando que el club identificó una de las opciones estadísticamente óptimas; (b) PARCIAL si figura en posiciones 11-30, indicando similitud moderada pero existencia de alternativas superiores no ejecutadas; (c) NO_VALIDADO si figura en posición >30, señalando que el fichaje responde a criterios no estadísticos (oportunidad de mercado, potencial proyectado, factores cualitativos). Este sistema cuantifica el grado de fundamentación data-driven de cada decisión._

**Criterios de interpretación.** _Un reemplazo clasificado como VALIDADO confirma que el departamento de scouting identificó correctamente un perfil estadísticamente equivalente al vendido, demostrando proceso analítico robusto. Un reemplazo PARCIAL sugiere que, aunque existe similitud cuantificable, el club pudo haber optimizado la decisión considerando alternativas de mayor proximidad estadística. Un reemplazo NO_VALIDADO no implica fracaso deportivo, sino que la decisión priorizó factores no capturados por métricas de rendimiento: precio de oportunidad (agente libre, fin de contrato), potencial de desarrollo (juveniles), encaje táctico específico, o restricciones económicas que limitaron el universo de targets viables. El algoritmo valida la fundamentación estadística de decisiones ejecutadas, no predice éxito futuro ni considera viabilidad real de fichajes alternativos._

**Limitaciones del método.** _El algoritmo retiene 85% de varianza explicada mediante PCA, descartando 15% de información presente en el espacio original (~150-170 dimensiones). Esta compresión puede eliminar matices distintivos entre perfiles híbridos o roles tácticos específicos. Adicionalmente, dado que los datos se estandarizan mediante z-score antes del PCA, la similitud coseno no solo captura proporciones entre métricas sino también posición relativa en la distribución: dos jugadores con idéntica distribución proporcional entre goles, asistencias y creación pero con volúmenes de producción muy diferentes (uno en percentil 50, otro en percentil 95) pueden obtener similitud moderada en lugar de alta. Finalmente, el método no captura factores cualitativos determinantes: intensidad defensiva sin balón, liderazgo, adaptación a sistemas tácticos específicos, o compatibilidad con compañeros de línea._

**Limitaciones reconocidas.** _Este diseño no permite identificar el universo completo de alternativas que los clubes consideraron durante el proceso de fichaje, solo valida la fundamentación estadística de las decisiones ejecutadas. Asimismo, el análisis cuantitativo no captura factores cualitativos determinantes en contexto real: viabilidad económica del traspaso, disposición del jugador a fichar, encaje con filosofía del entrenador, o consideraciones extradeportivas (edad, situación contractual, potencial de reventa). La metodología debe interpretarse como condición necesaria pero no suficiente: la similitud estadística entre vendido y fichado demuestra criterio analítico, pero no garantiza éxito deportivo ni explica por qué un club seleccionó ese target específico entre múltiples opciones estadísticamente equivalentes._

### 2.1. Workflow del Algoritmo PCA + Similitud Coseno

El proceso de análisis sigue una secuencia de 7 pasos, desde la extracción de datos brutos hasta la generación del ranking de similitud:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 1: EXTRACCIÓN DE DATOS                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  FBref (185 métricas) + Understat (10 métricas) + Transfermarkt (9 campos)  │
│  → Almacenamiento en PostgreSQL con estructura JSONB                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 2: FILTRADO DE POOL                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Criterios: posición compatible, edad ≤30, minutos ≥1000, ligas Big 5       │
│  → De ~15.000 registros a ~2.000-4.000 jugadores según posición             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 3: NORMALIZACIÓN PER 100 TOUCHES                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Cada métrica se divide entre toques totales × 100                          │
│  → Elimina sesgo de volumen: jugadores con 1000 o 3000 minutos comparables  │
│  Excluidas: porcentajes inherentes, ratios, métricas de portero             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 4: ESTANDARIZACIÓN (Z-SCORE)                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Cada variable se transforma a media=0 y desviación estándar=1              │
│  → Métricas con diferentes escalas (0-1 vs 0-100) quedan equiparadas        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 5: REDUCCIÓN DIMENSIONAL (PCA)                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ~150-170 variables → N componentes (retienen 85% varianza)                 │
│  Típicamente N = 20-30 componentes según estructura del pool                │
│  → Elimina redundancia: xG correlacionado con goles se comprime             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 6: CÁLCULO DE SIMILITUD COSENO                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Para cada jugador del pool: cos(θ) = (A·B) / (||A|| × ||B||)               │
│  Donde A = vector del jugador vendido, B = vector del candidato             │
│  → Resultado: valor entre -1 (opuestos) y 1 (idénticos)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PASO 7: GENERACIÓN DE RANKING Y VALIDACIÓN                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Ordenación descendente por similitud coseno                                │
│  Clasificación del reemplazo: VALIDADO (1-10), PARCIAL (11-30), NO (>30)    │
│  → Output: posición del fichaje real en el ranking + similitud numérica     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**¿Por qué PCA y no comparación directa de métricas?**

Comparar 140+ métricas directamente genera tres problemas que PCA resuelve:

1. **Multicolinealidad:** Muchas métricas miden conceptos similares (xG correlaciona con goles, pases completados con asistencias). PCA colapsa variables correlacionadas en componentes independientes, evitando contar dos veces la misma información.

2. **Ruido estadístico:** Variables con poca varianza entre jugadores (ej: todos los delanteros tienen ~0 intercepciones) añaden ruido sin información discriminante. PCA las elimina automáticamente al retener solo el 85% de varianza explicada.

3. **Maldición de la dimensionalidad:** En espacios de alta dimensión, las distancias euclidianas pierden significado (todos los puntos quedan "igual de lejos"). Reducir a 20-30 dimensiones preserva estructura geométrica interpretable.

**¿Por qué similitud coseno y no distancia euclidiana?**

La similitud coseno mide el ángulo entre vectores, priorizando la dirección del perfil sobre la magnitud absoluta. Sin embargo, dado que nuestro pipeline aplica estandarización z-score antes del PCA, el efecto es matizado:

- **Sin z-score**: Dos jugadores con proporciones idénticas (uno con 0.5 xG y otro con 1.0 xG, ambos con ratio xG:xA:shots similar) tendrían similitud coseno ~1.0.
- **Con z-score**: Los valores se transforman a posición relativa en la distribución. Un jugador en percentil 50 de xG y otro en percentil 95 obtienen z-scores diferentes (ej: 0 vs +2), alterando la dirección del vector resultante.

Esta combinación es deliberada: permite que jugadores con perfiles funcionalmente similares pero diferente nivel de producción aparezcan como "similares pero no idénticos", reflejando la realidad de que un delantero de 8 goles en equipo modesto puede tener el mismo perfil que uno de 15 goles en equipo top, pero no son intercambiables sin ajuste de expectativas.

La distancia euclidiana amplificaría excesivamente las diferencias absolutas, mientras que la similitud coseno sobre datos z-scored balancea ambos factores: perfil proporcional y nivel relativo de producción.

### 2.2. Interpretación de Resultados: Similar ≠ Mejor

**El objetivo del algoritmo es validar criterio analítico, no predecir éxito deportivo.**

Cuando un fichaje se clasifica como VALIDADO, significa que el club identificó un jugador estadísticamente similar al vendido. Esto demuestra proceso de scouting fundamentado en datos. Sin embargo, similar no implica mejor ni garantiza rendimiento futuro.

**Escenario 1: Buscar similar tiene sentido cuando el vendido funcionaba.**

Si el Villarreal vende a Nicolas Jackson (delantero goleador, 17 goles en temporada) y ficha a Sørloth (perfil similar según PCA), la lógica es clara: replicar un perfil que ya demostró encajar en el sistema táctico del equipo. El algoritmo valida que esta decisión tiene fundamento estadístico.

**Escenario 2: NO similar no implica peor fichaje.**

Supongamos que el Frankfurt vende a Kolo Muani (delantero móvil, asociativo, xA alto) y ficha a un 9 puro de área (perfil diferente, baja similitud). El algoritmo clasificaría esto como NO_VALIDADO, pero esto no significa fracaso:

- Quizás el entrenador cambió de sistema y ahora necesita un perfil diferente
- Quizás Kolo Muani no encajaba tan bien como sugieren sus números y el cambio de perfil es intencional
- Quizás el jugador fichado tiene potencial de desarrollo no capturado en métricas históricas
- Quizás era la única opción viable dentro del presupuesto disponible

**La similitud estadística es condición suficiente para validar criterio analítico, pero no es condición necesaria para éxito deportivo.**

Un fichaje NO_VALIDADO puede triunfar si:
- El club deliberadamente buscó un perfil diferente para cambiar dinámica táctica
- El jugador mejora en el nuevo contexto (mejor equipo, más minutos, confianza del entrenador)
- Factores no estadísticos (liderazgo, mentalidad, adaptación) compensan la diferencia de perfil

Un fichaje VALIDADO puede fracasar si:
- El jugador no se adapta al nuevo país/liga/idioma/cultura
- Sufre lesiones que no permiten mostrar su nivel previo
- El contexto táctico del nuevo equipo es diferente pese a la similitud estadística
- Factores psicológicos (presión, expectativas) afectan rendimiento

**Caso especial: Upgrades que aparecen como NO_VALIDADO.**

En la mayoría de sustituciones exitosas, el fichaje aparece como similar al vendido. Sin embargo, existe un escenario donde un fichaje objetivamente superior puede clasificarse como NO_VALIDADO: cuando el club deliberadamente busca un upgrade significativo, no un reemplazo equivalente.

_Ejemplo concreto:_ Un equipo vende un delantero con 0.45 xG/90 (percentil 60 entre delanteros Big 5) y ficha uno con 0.85 xG/90 (percentil 95). Aunque ambos sean "delanteros goleadores", el proceso de estandarización z-score sitúa sus vectores en posiciones muy distantes del espacio multidimensional: uno está cerca de la media poblacional, el otro en el extremo superior. La similitud coseno, calculada sobre estos vectores estandarizados, puede ser moderada o baja pese a que el perfil funcional sea análogo.

Este escenario NO representa un fallo del algoritmo sino una limitación inherente: **el método no distingue dirección de la diferencia**. Un resultado NO_VALIDADO indica "perfil estadísticamente distante" sin especificar si es distante-inferior o distante-superior. La interpretación requiere contexto adicional: si el fichaje produce más xG, más goles, más xA que el vendido, la baja similitud refleja upgrade deliberado, no error de scouting.

_Implicación práctica:_ Cuando un caso de uso resulte NO_VALIDADO pero el fichaje demuestre rendimiento superior al vendido, la explicación correcta es "el club buscó mejora, no equivalencia" y no "el club falló en identificar perfil similar". El algoritmo valida búsqueda de similitud; no penaliza búsqueda de superioridad.

**Conclusión metodológica:**

El algoritmo responde a la pregunta: "¿El fichaje ejecutado tiene fundamento estadístico respecto al jugador vendido?" Si la respuesta es VALIDADO, el club demostró criterio analítico. Si la respuesta es NO_VALIDADO, el fichaje responde a otros criterios (oportunidad, proyecto, restricciones) que pueden ser igualmente válidos pero no son capturables mediante métricas de rendimiento histórico.

La utilidad del método radica en distinguir decisiones data-driven de decisiones oportunistas, no en predecir cuáles funcionarán mejor a futuro.

### 2.3. Factores No Capturados por el Análisis

El proceso real de fichaje de un jugador profesional involucra docenas de variables que este análisis no puede capturar debido a limitaciones de acceso a datos, naturaleza cualitativa de la información, o ausencia de fuentes públicas fiables. Esta sección documenta exhaustivamente dichos factores para contextualizar correctamente el alcance y las limitaciones del método.

#### 2.3.1. Datos No Disponibles en Fuentes Públicas Gratuitas

**Datos físicos y de tracking.** _Las métricas de rendimiento físico constituyen una dimensión crítica en el scouting profesional que este análisis no incorpora. La distancia total recorrida por partido, número y velocidad de sprints, aceleraciones y desaceleraciones, velocidad máxima alcanzada, y métricas de intensidad de presión (PPDA individual, tiempo hasta recuperación) requieren sistemas de tracking GPS o datos de proveedores como Second Spectrum, SkillCorner o StatsPerform, cuyos costes de licencia superan el alcance de un trabajo académico. Un jugador puede presentar métricas estadísticas similares a otro pero con perfiles físicos radicalmente diferentes: uno basado en explosividad y duelos, otro en posicionamiento e inteligencia táctica._

**Datos de video y análisis cualitativo.** _El scouting profesional complementa las estadísticas con análisis de video que evalúa aspectos no cuantificables: calidad de los movimientos sin balón, timing de desmarques, comunicación con compañeros, comportamiento en situaciones de presión, lenguaje corporal tras errores, y posicionamiento defensivo en fases sin posesión. Estos elementos, determinantes para predecir adaptación a un nuevo contexto táctico, requieren horas de visualización por jugador y criterio experto que escapa al alcance metodológico de este trabajo._

**Datos médicos e historial de lesiones.** _La propensión a lesiones, historial de problemas musculares, recuperación de intervenciones quirúrgicas, y estado físico actual son factores decisivos en cualquier operación de fichaje. Un jugador con métricas excelentes pero tres roturas de ligamento cruzado representa un riesgo que ningún análisis estadístico de rendimiento puede capturar. Los clubes acceden a informes médicos confidenciales durante las negociaciones; las fuentes públicas solo registran lesiones reportadas en prensa, con información incompleta y frecuentemente inexacta._

**Factores psicológicos y de personalidad.** _La mentalidad competitiva, capacidad de liderazgo, comportamiento en vestuario, adaptabilidad a nuevos entornos culturales y lingüísticos, resistencia a la presión mediática, y estabilidad emocional son variables que los clubes evalúan mediante entrevistas, informes de entorno, y consultas con representantes y excompañeros. Ninguna métrica estadística captura si un jugador rendirá bajo la presión de 80.000 espectadores hostiles o si su personalidad encajará con la dinámica de grupo existente._

#### 2.3.2. Factores de Mercado No Scrapeables

**Situación contractual detallada.** _Aunque Transfermarkt proporciona fechas de inicio y fin de contrato, los detalles críticos para una negociación real permanecen confidenciales: salario actual y estructura de bonificaciones, cláusula de rescisión (si existe y su cuantía exacta), cláusulas de salida condicionales, porcentajes de futura venta retenidos por clubes anteriores, y derechos de imagen. Un jugador estadísticamente ideal puede ser inviable si su cláusula es prohibitiva o si un porcentaje significativo de cualquier venta futura pertenece a un tercer club._

**Voluntad del jugador y situación personal.** _La disposición del jugador a fichar por un club específico es determinante y completamente opaca al análisis cuantitativo. Preferencias geográficas (clima, idioma, proximidad familiar), ambición deportiva (jugar Champions vs consolidarse en liga menor), situación familiar (pareja, hijos, colegios), y percepción del proyecto deportivo filtran el universo teórico de candidatos a una fracción de opciones realmente viables. Un jugador puede rechazar ofertas económicamente superiores por factores personales inaccesibles a cualquier base de datos._

**Ecosistema de agentes y representación.** _Las relaciones entre agentes y clubes, estructuras de comisiones, conflictos de interés (agentes que representan simultáneamente a jugador y comprador), y "paquetes" de representación (fichaje condicionado a contratar otros jugadores del mismo agente) configuran una capa de complejidad transaccional invisible en datos públicos. Clubes como el Villarreal o el Lille pueden tener relaciones privilegiadas con ciertos agentes que facilitan operaciones imposibles para competidores directos._

**Competencia de mercado y timing.** _El momento exacto de una operación y la existencia de otros clubes interesados alteran radicalmente las condiciones. Un jugador identificado como similar estadísticamente puede ser inalcanzable si tres clubes de Premier League compiten simultáneamente por él. El análisis retrospectivo no captura estas dinámicas: solo observamos fichajes ejecutados, no los que fracasaron por competencia de mercado o timing inadecuado._

#### 2.3.3. Factores del Club Comprador

**Restricciones económicas reales.** _El presupuesto disponible para fichajes depende de variables no públicas: situación de Fair Play Financiero, amortizaciones pendientes de fichajes anteriores, necesidades de venta obligatorias para cuadrar balances, líneas de crédito disponibles, y acuerdos con propietarios o fondos de inversión. Un club puede identificar el reemplazo estadísticamente óptimo pero carecer de capacidad financiera para ejecutar la operación, optando por alternativas subóptimas pero viables económicamente._

**Proyecto táctico específico.** _Cada entrenador implementa un sistema con requerimientos posicionales específicos que las categorías genéricas (ST, CB, CM) no capturan. Un delantero centro en el sistema de Emery puede requerir características diferentes a uno en el sistema de Slot. El análisis agrupa bajo "ST" perfiles tan diversos como un 9 de área, un falso 9, un delantero de presión, o un asociativo de espaldas. La similitud estadística entre dos delanteros no garantiza que ambos encajen en el mismo sistema táctico._

**Compatibilidad con plantilla existente.** _Los fichajes no ocurren en vacío: deben complementar a los jugadores ya presentes. Si un equipo tiene un extremo derecho que recorta constantemente hacia dentro, puede necesitar un lateral derecho con proyección ofensiva para dar amplitud. Estas sinergias tácticas, dependientes de la configuración específica de cada plantilla, escapan a un análisis de similitud individual._

**Necesidades puntuales y urgencias.** _Lesiones de titulares, sanciones, conflictos de vestuario, o rendimiento catastrófico pueden forzar fichajes de urgencia que priorizan disponibilidad inmediata sobre perfil estadístico óptimo. El mercado de invierno, en particular, opera bajo restricciones temporales que limitan el universo de opciones a jugadores cuyas situaciones contractuales o deportivas permiten salidas mid-season._

#### 2.3.4. Sesgos Contextuales de los Datos

**Efecto de ascensos y descensos.** _Las métricas de un jugador en Segunda División o en ligas de menor nivel (Eredivisie, Liga Belga, Championship) no son directamente comparables con las de Primera División de las Big 5. Un delantero que promedia 0.7 xG/90 en la Eredivisie puede promediar 0.4 xG/90 en la Premier League debido a la diferencia de nivel defensivo. El algoritmo trata todas las métricas como equivalentes, introduciendo sesgo cuando el pool incluye jugadores de contextos competitivos dispares._

**Cambios de entrenador y sistema.** _Las métricas de una temporada reflejan el rol asignado por un entrenador específico en un sistema específico. Un mediocampista puede acumular métricas defensivas excepcionales bajo un entrenador y métricas ofensivas bajo otro, sin que su calidad haya cambiado. El análisis asume estabilidad de rol que no siempre existe: Foyth pasó de lateral a central, alterando completamente su perfil estadístico._

**Lesiones durante la temporada analizada.** _Un jugador que sufre una lesión muscular en octubre y juega el resto de temporada al 70% de capacidad presentará métricas inferiores a su nivel real. El análisis no distingue entre rendimiento genuino y rendimiento afectado por lesiones no incapacitantes. Transfermarkt registra solo ausencias completas, no partidos jugados con molestias._

**Contexto de equipo y estilo de juego.** _Las métricas individuales están parcialmente determinadas por el contexto colectivo. Un delantero en equipo dominante (70% posesión, 20 disparos/partido) acumulará más xG que el mismo delantero en equipo defensivo (40% posesión, 8 disparos/partido). El algoritmo captura esto parcialmente mediante normalización per 100 touches, pero no elimina completamente el sesgo: un delantero en equipo que no crea ocasiones tendrá bajo xG independientemente de su calidad individual._

#### 2.3.5. Sesgos Metodológicos Inherentes

**Sesgo de supervivencia.** _El filtro de minutos mínimos (≥1000) excluye sistemáticamente a jugadores jóvenes con alto potencial pero poca participación. Un canterano de 19 años con 400 minutos excepcionales no aparece en el pool de análisis, pese a poder ser el reemplazo óptimo a largo plazo. Este sesgo favorece jugadores establecidos sobre talentos emergentes, contradiciendo parcialmente el modelo de negocio de clubes como Lille que apuestan por desarrollo temprano._

**Sesgo temporal (look-ahead invertido).** _El análisis usa datos de temporada X-1 para evaluar fichajes de temporada X, replicando las condiciones de información del momento de decisión. Sin embargo, la forma actual de un jugador en el momento exacto del fichaje (pretemporada, primeros partidos de temporada) puede diferir significativamente de sus métricas de temporada anterior. Un jugador que terminó lesionado la temporada X-1 pero llegó recuperado a pretemporada presenta métricas que subestiman su estado real._

**Sesgo de liga y nivel de oposición.** _Comparar jugadores de Ligue 1 con jugadores de Premier League asume equivalencia de contexto competitivo que no existe. Las métricas defensivas en Ligue 1 (liga con menor intensidad de presión media) no son equivalentes a las mismas métricas en Premier League. El algoritmo no ajusta por dificultad de liga, introduciendo sesgo cuando el pool mezcla jugadores de contextos competitivos heterogéneos._

**Sesgo de clasificación posicional.** _La categorización en posiciones discretas (ST, CB, CM, etc.) agrupa perfiles funcionalmente diversos. Bajo "ST" coexisten nueves de área (Haaland), falsos nueves (Firmino), delanteros de presión (Kolo Muani), y segundos delanteros (Griezmann). La similitud estadística entre dos "ST" puede ser baja simplemente porque ocupan subroles diferentes, no porque sean peores opciones de reemplazo. El algoritmo no distingue estas sutilezas posicionales._

#### 2.3.6. Implicaciones para la Interpretación de Resultados

La exhaustiva documentación de factores no capturados tiene una implicación central: **un resultado VALIDADO confirma fundamentación estadística, pero no garantiza que el fichaje fuera la mejor opción real disponible; un resultado NO_VALIDADO indica ausencia de similitud estadística, pero no implica error de scouting si la decisión respondió a factores aquí documentados.**

El valor del análisis reside en su capacidad para distinguir decisiones con fundamento cuantitativo de decisiones puramente oportunistas o intuitivas. No pretende reemplazar el proceso completo de scouting profesional —que integra todas las dimensiones aquí documentadas— sino validar una de sus componentes: la proximidad estadística de perfiles de rendimiento.

Los clubes analizados (Villarreal, Frankfurt, Lille) operan con acceso a información que este estudio no posee. Sus decisiones de fichaje integran datos físicos, médicos, contractuales, y contextuales que el algoritmo ignora. La elevada tasa de validación estadística observada sugiere que la similitud de perfiles de rendimiento es condición frecuente (aunque no suficiente) en sus procesos de decisión, compatible con la hipótesis de estrategias data-driven sofisticadas que complementan el análisis cuantitativo con evaluación cualitativa integral.

---

## 3. Análisis de Casos: Cadenas de Sustitución

<!--
TODO: VERIFICAR EN TRANSFERMARKT - Formato estándar por jugador:
**Jugador** | Fecha fichaje | Club origen → Club destino | Precio fichaje | Precio venta | Plusvalía

VILLARREAL:
- [ ] Nicolas Jackson: fecha venta, precio exacto Chelsea
- [ ] Alexander Sørloth: club origen (¿Real Sociedad?), fechas, precios exactos
- [ ] Thierno Barry: club origen Suiza (¿Basel?), fechas, precios
- [ ] Tani Oluwaseyi: club origen MLS (¿Minnesota?), fecha, precio
- [ ] Yeremy Pino: fecha venta, club destino, precio exacto
- [ ] George Mikautadze: club origen (¿Lyon?), fecha, precio
- [ ] Filip Jörgensen: fecha venta Chelsea, precio exacto
- [ ] Luiz Junior: club origen Portugal (¿Gil Vicente?), fecha, precio
- [ ] Pau Torres: fecha venta Aston Villa, precio exacto
- [ ] Logan Costa: fecha fichaje, precio exacto Toulouse
- [ ] Renato Veiga: club origen (¿Chelsea?), fecha, precio
- [ ] Santiago Mouriño: fecha, precio exacto Celta
- [ ] Pervis Estupiñán: fechas y precios exactos
- [ ] Johan Mojica: club origen (¿Elche?), fechas, precios
- [ ] Sergi Cardona: fecha llegada
- [ ] Alfonso Pedraza: fecha venta Betis, precio
- [ ] Álex Baena: fecha venta, club destino (¿Atlético?), precio exacto
- [ ] Alberto Moleiro: fecha, precio exacto Las Palmas

FRANKFURT:
- [ ] Randal Kolo Muani: fecha fichaje/venta, precios exactos
- [ ] Omar Marmoush: club origen (¿Wolfsburg?), fechas, precios
- [ ] Hugo Ekitike: fechas cesión/compra/venta, precios
- [ ] Elye Wahi: fecha, precio exacto Marsella
- [ ] Jonathan Burkardt: fecha, precio exacto Mainz
- [ ] Evan Ndicka: fecha salida Roma
- [ ] Willian Pacho: club origen Bélgica (¿Antwerp?), fechas, precios
- [ ] Arthur Theate: fecha, precio exacto Rennes

LILLE:
- [ ] Gabriel Magalhães: fechas, precios exactos
- [ ] Sven Botman: club origen Holanda (¿Ajax?), fechas, precios
- [ ] Bafodé Diakité: club origen (¿Toulouse?), fechas, precios, club destino venta
- [ ] Nathan Ngoy: club origen Bélgica (¿Standard?), fecha, precio
- [ ] Gabriel Gudmundsson: club origen (¿Groningen?), fechas, precios
- [ ] Romain Perraud: club origen (¿Betis/Southampton?), fecha, precio
- [ ] Boubakary Soumaré: fecha venta Leicester, precio exacto
- [ ] Amadou Onana: club origen (¿Hoffenheim?), fechas, precios Everton
- [ ] Carlos Baleba: fecha venta Brighton, precio exacto
- [ ] Nabil Bentaleb: club origen, fecha
- [ ] Victor Osimhen: club origen (¿Charleroi?), fechas, precios Napoli
- [ ] Jonathan David: club origen Bélgica (¿Gent?), fecha, precio
- [ ] Hamza Igamane: club origen Escocia (¿Rangers?), fecha, precio
-->

Los tres equipos seleccionados presentan modelos de negocio convergentes, pero con matices tácticos distintivos. A continuación se documentan las principales cadenas de sustitución ejecutadas entre 2022 y 2026, estructuradas por posición y secuencia temporal.

### 3.1. Villarreal CF: Modelo de Renovación Continua

El Villarreal ha implementado una política de reinversión sistemática caracterizada por:

- Venta de activos canteranos en pico de valor (Pau Torres 33M€, Jackson 37M€, Baena 55M€)
- Reemplazo mediante combinación de fichajes de coste medio (15-25M€) y agentes libres estratégicos
- Mantenimiento de núcleo táctico estable (Parejo, Foyth, Gerard) que absorbe rotación posicional

#### 3.1.1. Delantero Centro

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Nicolas Jackson | Cantera | Villarreal → Chelsea | — | 37 M€ | **+37 M€** |
| **↳** Alexander Sørloth | 25/07/2023 | Leipzig → Villarreal → Atlético | 10 M€ | 32 M€ | **+22 M€** |
| **↳** Thierno Barry | 21/08/2024 | FC Basel → Villarreal → Everton | 20 M€ | 30 M€ | **+10 M€** |
| **↳** Tani Oluwaseyi | 29/08/2025 | Minnesota → Villarreal | 8 M€ | — | — |

**Cadena analizada:** Jackson → Sørloth → Barry → Oluwaseyi

#### 3.1.2. Portero

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Gerónimo Rulli | 04/09/2020 | Real Sociedad → Villarreal → Ajax | 5 M€ | 8 M€ | **+3 M€** |
| **↳** Filip Jørgensen | Cantera | Villarreal → Chelsea | — | 24,5 M€ | **+24,5 M€** |
| **↳** Luiz Junior | 20/08/2024 | Famalicão → Villarreal | 12 M€ | — | — |

**Cadena analizada:** Rulli → Jørgensen → Luiz Junior

#### 3.1.3. Defensa Central

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Pau Torres | Cantera | Villarreal → Aston Villa | — | 33 M€ | **+33 M€** |
| **↳** Logan Costa | 22/08/2024 | Toulouse → Villarreal | 18 M€ | — | — |
| **↳** Renato Veiga | 22/08/2025 | Chelsea → Villarreal | 24,5 M€ | — | — |
| Santiago Mouriño | 01/08/2025 | Atlético de Madrid → Villarreal | 10 M€ | — | — |

**Contexto táctico:** Tras la salida de Pau Torres (verano 2023), el club optó por soluciones temporales (Eric Bailly como agente libre, promoción de Jorge Cuenca y Raúl Albiol) durante la temporada 22/23, fichajes de transición que no se incluyen en el análisis por no representar inversión estratégica a largo plazo.

La temporada 24/25 incorpora a Logan Costa como reemplazo estructural. Tras su lesión en 25/26, el Villarreal ejecuta un ajuste posicional: Juan Foyth (lateral derecho de origen) se consolida como central diestro, lo que genera necesidad de cubrir el lateral. Se ficha a Santiago Mouriño (10M€) como lateral derecho, mientras Renato Veiga (24,5M€) aporta un perfil diferenciado como central zurdo.

**Nota histórica:** Eric Bailly representa un caso previo de gestión óptima del Villarreal: fichado del Espanyol por 5,7M€ en 2015, vendido al Manchester United por 38M€ un año después.

**Cadena analizada:** Pau Torres → Logan Costa

#### 3.1.4. Lateral Izquierdo

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Pervis Estupiñán | 16/09/2020 | Watford → Villarreal → Brighton | 16,4 M€ | 17,8 M€ | **+1,4 M€** |
| **↳** Johan Mojica | 01/09/2022 | Elche → Villarreal → Mallorca | 5,5 M€ | 1,5 M€ | **-4 M€** |
| **↳** Sergi Cardona | 18/07/2024 | Las Palmas → Villarreal | Gratis | — | — |

**Contexto táctico:** Mojica (29 años en el momento del fichaje) no alcanzó el rendimiento esperado y fue cedido al Osasuna. El club buscaba un perfil que complementara a Alfonso Pedraza —lateral más ofensivo, utilizado como extremo en fases de ataque— en lugar de un sustituto directo. Sergi Cardona, incorporado como agente libre (valor de mercado 6M€, actualmente 10M€), ofrece un perfil más defensivo que equilibra la rotación.

**Cadena analizada:** Estupiñán → Mojica → Sergi Cardona (complemento a Pedraza)

#### 3.1.5. Mediapunta / Extremo

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Álex Baena | Cantera | Villarreal → Atlético de Madrid | — | 42 M€ (+13 M€ variables) | **+42 M€** (+13) |
| **↳** Alberto Moleiro | 01/07/2025 | Las Palmas → Villarreal | 16 M€ | — | — |

**Contexto de mercado:** Moleiro fue fichado por 16M€ con valor de mercado de 25M€ (actualmente 30M€), aprovechando el descenso de Las Palmas a Segunda División que debilitó la posición negociadora del club vendedor.

**Cadena analizada:** Baena → Moleiro

#### 3.1.6. Fichajes Estratégicos sin Coste

Paralelamente a las cadenas de sustitución, el Villarreal ha incorporado jugadores de alto rendimiento en condición de agentes libres:

| Jugador | Procedencia | Edad llegada | Contexto |
|---------|-------------|--------------|----------|
| Nicola Pépé | Arsenal | 29 | Ex-fichaje récord Arsenal (72M€), depreciado por irregularidad |
| Pape Gueye | Olympique Marsella | 28 | Pivote defensivo, fin de contrato |
| Santi Comesaña | Rayo Vallecano | 28 | Centrocampista polivalente, fin de contrato |
| Thomas Partey | Arsenal | 31 | Internacional Ghana, reducción salarial por edad |

Estos fichajes representan valor oculto: jugadores con métricas estadísticas preservadas pero depreciación de mercado por edad (28-31 años) o situación contractual. No generan plusvalías pero aportan rendimiento inmediato sin inversión de capital.

### 3.2. Eintracht Frankfurt: Modelo de Plusvalías Extremas

El Frankfurt opera con menor frecuencia transaccional que Villarreal pero con márgenes unitarios superiores. Especialización en detección de talento infravalorado en ligas secundarias (Ligue 1, Eredivisie, Pro League belga) y desarrollo acelerado en contexto Bundesliga.

#### 3.2.1. Delantero Centro

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Randal Kolo Muani | 01/07/2022 | Nantes (libre) → Frankfurt → PSG | Gratis | 95 M€ | **+95 M€** |
| **↳** Omar Marmoush | 01/07/2023 | Wolfsburgo (libre) → Frankfurt → Man City | Gratis | 75 M€ | **+75 M€** |
| **↳** Hugo Ekitike | 23/24 cesión | PSG → Frankfurt (cesión) | — | — | — |
| **↳** Hugo Ekitike | verano 24/25 | PSG → Frankfurt → Liverpool | 31,5 M€ | 90 M€ | **+58,5 M€** |
| **↳** Elye Wahi | 24/01/2025 | Marsella → Frankfurt → Lille (cesión) | 26 M€ | — | — |
| **↳** Jonathan Burkardt | 04/07/2025 | Mainz → Frankfurt | 21 M€ | — | — |

**Contexto operativo:** La posición de delantero centro presenta una estructura de rotación más compleja que el modelo lineal del Villarreal. Kolo Muani genera la plusvalía récord (95M€ sobre coste cero). Su sustitución se ejecuta mediante doble vía:

1. **Línea Marmoush:** Agente libre que replica el modelo Kolo Muani (coste cero → venta 75M€). Su salida en invierno 24/25 se cubre con Wahi (26M€), actualmente cedido al Lille.

2. **Línea Ekitike:** Primero evaluado mediante cesión (23/24), posteriormente adquirido (31,5M€) y vendido a Liverpool (90M€). Su sustituto estructural es Burkardt (21M€).

**Cadenas analizadas:** Kolo Muani → Marmoush → Wahi | Ekitike → Burkardt

#### 3.2.2. Defensa Central

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Evan Ndicka | 05/07/2018 | Auxerre → Frankfurt → Roma (libre) | 5,5 M€ | Gratis | — |
| **↳** Willian Pacho | 01/07/2023 | Royal Amberes → Frankfurt → PSG | 13,65 M€ | 40 M€ | **+26,35 M€** |
| **↳** Arthur Theate | 18/08/2024 | Stade Rennes (cesión) → Frankfurt | 13 M€ | — | — |

**Contexto operativo:** Ndicka, desarrollado durante 5 temporadas, sale como agente libre hacia Roma (valor de mercado ~28M€), plusvalía no monetizada pero con amortización completa. Su reemplazo, Willian Pacho, replica el patrón de desarrollo acelerado: adquirido de liga belga, expuesto a Bundesliga y UCL durante una temporada, vendido al PSG con margen del 193%. Theate, inicialmente cedido del Rennes, se incorpora como reemplazo estructural (13M€ con valor de mercado de 20M€).

**Cadena analizada:** Ndicka → Pacho → Theate

---

**Modelo operativo Frankfurt:** Ventanas de desarrollo de 12-18 meses. Adquisición de talento probado en ligas de nivel 2-3 (Ligue 1, Pro League belga, Eredivisie), exposición intensiva a Bundesliga y competiciones europeas (UCL/UEL), venta a clubes top-6 europeo. ROI medio observado: 250-300%.

### 3.3. LOSC Lille: Desarrollo de Canteranos e Importación Selectiva

Lille presenta un modelo híbrido entre cantera propia (Yoro 62M€, Chevalier 40M€) y detección temprana en mercados africanos y sudamericanos. Horizonte temporal más largo (2-3 temporadas de desarrollo) que Frankfurt.

#### 3.3.1. Defensa Central

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Gabriel Magalhães | 31/01/2017 | Avaí FC → Lille → Arsenal | 3 M€ | 26 M€ | **+23 M€** |
| **↳** Sven Botman | 31/07/2020 | Ajax → Lille → Newcastle | 8 M€ | 37 M€ | **+29 M€** |
| **↳** Bafodé Diakité | 05/08/2022 | Toulouse → Lille → Bournemouth | 3 M€ | 35 M€ | **+32 M€** |
| **↳** Nathan Ngoy | 24/07/2025 | Standard Lieja → Lille | 3,5 M€ | — | — |

**Contexto operativo:** Cadena de centrales con patrón de inversión consistente (3-8M€) y multiplicadores de venta superiores a 4x. Gabriel, Botman y Diakité demuestran capacidad de desarrollo desde ligas menores (Brasil, Eredivisie, Ligue 2) hasta transferencias a Premier League. Ngoy continúa el modelo: adquisición temprana desde liga belga a coste controlado.

**Cadena analizada:** Gabriel → Botman → Diakité → Ngoy

#### 3.3.2. Mediocampista Defensivo

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Boubakary Soumaré | 12/07/2017 | PSG B (libre) → Lille → Leicester | Gratis | 20 M€ | **+20 M€** |
| **↳** Amadou Onana | 05/08/2021 | Hamburgo → Lille → Everton | 13,5 M€ | 40 M€ | **+26,5 M€** |
| **↳** Carlos Baleba | Cantera | Lille → Brighton | — | 27 M€ | **+27 M€** |
| **↳** Nabil Bentaleb | 28/08/2023 | Angers → Lille | 4,5 M€ | — | — |

**Contexto operativo:** Posición con alternancia entre productos de cantera (Soumaré, Baleba) y fichajes externos (Onana, Bentaleb). Carlos Baleba no se incluye en el análisis PCA por ausencia de datos previos al debut profesional en Lille. Bentaleb representa perfil veterano de consolidación (32 años, experiencia Bundesliga/Ligue 1) más que proyección de plusvalía.

**Cadena analizada:** Soumaré → Onana → Bentaleb

#### 3.3.3. Delantero Centro

| Jugador | Fecha | Operación | Precio fichaje | Precio venta | Plusvalía |
|---------|-------|-----------|----------------|--------------|-----------|
| Victor Osimhen | 01/08/2019 | Charleroi → Lille → Napoli | 22,5 M€ | 79 M€ | **+56,5 M€** |
| **↳** Jonathan David | 11/08/2020 | KAA Gante → Lille → Juventus (libre) | 27 M€ | Gratis | **-27 M€** |
| **↳** Hamza Igamane | 29/08/2025 | Rangers FC → Lille | 11,5 M€ | — | — |

**Contexto operativo:** Caso de contraste entre gestión óptima (Osimhen: +56,5M€) y deficiente (David: -27M€). Osimhen representa el fichaje más rentable del período estudiado en términos absolutos. David, pese a rendimiento deportivo sostenido (84 goles en 5 temporadas), sale como agente libre a la Juventus en 2025, error de planificación contractual que anula la plusvalía potencial (valor de mercado ~50M€ en su pico). Igamane, adquirido de liga escocesa, inicia nuevo ciclo.

**Cadena analizada:** Osimhen → David → Igamane

#### 3.3.4. Producción de Cantera de Alto Valor

| Jugador | Posición | Club destino | Precio venta |
|---------|----------|--------------|--------------|
| Leny Yoro | Defensa Central | Manchester United | **62 M€** |
| Lucas Chevalier | Portero | PSG | **40 M€** |

Estos casos representan ROI infinito (coste de formación amortizado en estructura de cantera). Lille mantiene pipeline de canteranos con proyección de selección nacional sub-21, fundamental para sostenibilidad del modelo a largo plazo. La venta de Yoro (18 años) y Chevalier (23 años) demuestra capacidad de monetizar talento propio antes de alcanzar madurez contractual crítica.

### 3.4. Evolución de Valor de Plantilla y Rendimiento Competitivo

Un elemento diferenciador de estos tres clubes frente a modelos de liquidación de activos es el mantenimiento del valor total de plantilla pese al flujo constante de entradas y salidas. Esta estabilidad, combinada con presencia europea regular, valida la hipótesis de que la eficiencia económica no compromete el proyecto deportivo.

#### 3.4.1. Villarreal CF

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 363,50 M€ | 26,4 | 8,45 M€ | La Liga: 5º | UECL: Ronda de 16 |
| 23/24 | 252,50 M€ | 27,2 | 6,47 M€ | La Liga: 8º | UEL: Ronda de 16 |
| 24/25 | 264,25 M€ | 26,2 | 7,34 M€ | La Liga: 5º | No participó |
| 25/26 | 280,30 M€ | 26,3 | 10,38 M€ | En curso | En curso |

**Análisis:** Caída inicial del valor de plantilla en 23/24 (-111M€) coincide con salidas de Pau Torres (33M€), Jackson (37M€) y Chukwueze (21M€). Recuperación progresiva en 24/25 y 25/26 mediante fichajes de mayor precio unitario (Mikautadze 31M€, Veiga 24,5M€). Edad media estable entre 26,2-27,2 años, ventana óptima de rendimiento-valor de reventa.

**Rendimiento deportivo:** Cinco temporadas consecutivas en top-8 La Liga, cuatro participaciones europeas con clasificación a fase eliminatoria en tres ocasiones. Valor plantilla/posición liga muestra eficiencia: equipos con plantillas valoradas en 400-500M€ (Athletic, Betis) obtienen posiciones similares.

#### 3.4.2. LOSC Lille

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 347,95 M€ | 25,3 | 7,51 M€ | Ligue 1: 5º | Clasificó UECL 23/24 |
| 23/24 | 329,90 M€ | 23,8 | 8,02 M€ | Ligue 1: 4º | UECL: Cuartos |
| 24/25 | 336,60 M€ | 25,4 | 8,42 M€ | Ligue 1: 5º | UCL: Ronda de 16 |
| 25/26 | 215,60 M€ | 26,4 | 7,99 M€ | En curso | En curso |

**Análisis:** Notable consistencia en valor de plantilla (330-350M€) durante 22/23-24/25 pese a ventas acumuladas superiores a 300M€. Caída pronunciada en 25/26 (-121M€) atribuible a salidas simultáneas de Yoro (62M€), Chevalier (40M€) y Diakité (35M€) sin reemplazos inmediatos de valor equivalente.

Edad media excepcionalmente baja (23,8 años en 23/24), la más joven de Ligue 1 entre equipos top-6. Estrategia de "comprar jóvenes, vender prime" difiere de Villarreal (comprar prime jóvenes, vender prime establecidos).

**Rendimiento deportivo:** Cuatro temporadas consecutivas en top-5 Ligue 1, progresión europea desde UECL a UCL. Calificación a ronda eliminatoria UCL con plantilla valorada en ~70% de la media de clasificados (Benfica, Inter, RB Salzburg), evidencia de eficiencia táctica.

#### 3.4.3. Eintracht Frankfurt

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 324,55 M€ | 25,6 | 9,02 M€ | Bundesliga: 7º | UCL: Ronda de 16 |
| 23/24 | 326,25 M€ | 24,7 | 7,10 M€ | Bundesliga: 6º | UECL: K.O. Playoffs |
| 24/25 | 431,25 M€ | 24,6 | 13,07 M€ | Bundesliga: 3º | UEL: Cuartos |
| 25/26 | 383,90 M€ | 25,7 | 13,71 M€ | En curso | En curso |

**Análisis:** Incremento sustancial del valor de plantilla (+106M€) en 24/25 pese a venta de Marmoush (75M€). Explicación: fichajes de Ekitike (31,5M€), Wahi (26M€) y retención de talento joven que experimenta revalorización durante temporada (Skhiri, Götze recuperados).

Valor medio por jugador más alto de los tres casos (13-14M€ en 24/25-25/26), sugiere estrategia de menor rotación con fichajes de precio unitario superior. Frankfurt opera como "escalón intermedio" entre clubes de desarrollo (Lille) y establecimientos (Villarreal).

**Rendimiento deportivo:** Progresión clara de 7º→6º→3º Bundesliga. Participación europea ininterrumpida 2022-2026, incluyendo presencia en UCL (nivel superior). Frankfurt presenta correlación más fuerte entre valor plantilla y rendimiento que Lille o Villarreal, posiblemente debido a competitividad superior de Bundesliga vs Ligue 1.

#### 3.4.4. Comparativa Interliga

**Métrica de eficiencia:** Beneficio neto / Valor promedio plantilla (2022-2025)

- **Villarreal:** 137M€ / 290M€ = **47,2% ROI**
- **Frankfurt:** 155M€ / 360M€ = **43,1% ROI**
- **Lille:** 193M€ / 305M€ = **63,3% ROI**

Lille emerge como el modelo más eficiente en términos puramente financieros, si bien opera en liga de menor exigencia competitiva. Frankfurt y Villarreal presentan ROI similares (~45%) con contextos competitivos más demandantes (Bundesliga top-4, La Liga top-6).

**Conclusión:** Los tres casos demuestran que beneficios sostenidos en el mercado son compatibles con:

- Estabilidad en valor total de plantilla (±15% variación)
- Edad media óptima (24-27 años)
- Clasificación a torneos europeos (80-100% de temporadas)
- Posiciones de media-alta tabla doméstica (3º-8º)

Esta evidencia empírica refuta la narrativa de que la generación de plusvalías requiere sacrificio del proyecto deportivo, validando la viabilidad de modelos data-driven integrales.

---

## 4. Resultados del Análisis

### 4.1. Resumen Ejecutivo

[TODO]

### 4.2. Villarreal CF

#### 4.2.1. Delantero Centro
#### 4.2.2. Portero
#### 4.2.3. Defensa Central
#### 4.2.4. Lateral Izquierdo
#### 4.2.5. Mediapunta / Extremo

### 4.3. Eintracht Frankfurt

#### 4.3.1. Delantero Centro
#### 4.3.2. Defensa Central

### 4.4. LOSC Lille

#### 4.4.1. Defensa Central
#### 4.4.2. Mediocampista Defensivo
#### 4.4.3. Delantero Centro

### 4.5. Síntesis Comparativa

[TODO]

---

## ANEXOS

### La Liga - Balance Transferencias 2022-2026

| # | Club | Gastos | Altas | Ingresos | Bajas | Balance |
|---|------|--------|-------|----------|-------|---------|
| 1 | Villarreal CF | 189,98 mill. € | 75 | 327,10 mill. € | 72 | **137,12 mill. €** |
| 2 | Sevilla FC | 82,65 mill. € | 82 | 205,95 mill. € | 79 | **123,30 mill. €** |
| 3 | Real Sociedad | 142,10 mill. € | 58 | 257,15 mill. € | 56 | **115,05 mill. €** |
| 4 | Valencia CF | 37,37 mill. € | 61 | 139,63 mill. € | 64 | **102,25 mill. €** |
| 5 | Granada CF | 27,23 mill. € | 90 | 85,50 mill. € | 96 | **58,27 mill. €** |
| 6 | RC Celta de Vigo | 82,13 mill. € | 82 | 135,15 mill. € | 72 | **53,02 mill. €** |
| 7 | Real Betis Balompié | 161,95 mill. € | 73 | 208,28 mill. € | 74 | **46,33 mill. €** |
| 8 | Levante UD | 6,87 mill. € | 67 | 45,89 mill. € | 70 | **39,02 mill. €** |
| 9 | RCD Espanyol | 38,90 mill. € | 82 | 77,65 mill. € | 83 | **38,75 mill. €** |
| 10 | Real Valladolid CF | 35,08 mill. € | 98 | 69,15 mill. € | 98 | **34,08 mill. €** |
| 11 | UD Almería | 113,73 mill. € | 81 | 147,65 mill. € | 82 | **33,92 mill. €** |
| 12 | Getafe CF | 40,25 mill. € | 75 | 70,94 mill. € | 78 | **30,69 mill. €** |
| 13 | CD Leganés | 7,36 mill. € | 88 | 26,00 mill. € | 91 | **18,65 mill. €** |
| 14 | Girona FC | 117,65 mill. € | 85 | 134,45 mill. € | 82 | **16,80 mill. €** |
| 15 | Elche CF | 24,26 mill. € | 75 | 40,49 mill. € | 74 | **16,23 mill. €** |
| 16 | Deportivo Alavés | 31,52 mill. € | 83 | 46,04 mill. € | 86 | **14,52 mill. €** |
| 17 | UD Las Palmas | 11,65 mill. € | 70 | 24,23 mill. € | 70 | **12,59 mill. €** |
| 18 | CA Osasuna | 21,55 mill. € | 30 | 25,50 mill. € | 34 | **3,95 mill. €** |
| 19 | RCD Mallorca | 48,57 mill. € | 57 | 50,90 mill. € | 58 | **2,33 mill. €** |
| 20 | Real Oviedo | 6,65 mill. € | 68 | 3,30 mill. € | 66 | **-3,35 mill. €** |
| 21 | Cádiz CF | 20,60 mill. € | 85 | 15,00 mill. € | 86 | **-5,60 mill. €** |
| 22 | FC Barcelona | 280,40 mill. € | 64 | 261,00 mill. € | 68 | **-19,40 mill. €** |
| 23 | Athletic Club | 40,00 mill. € | 57 | 13,45 mill. € | 53 | **-26,55 mill. €** |
| 24 | Rayo Vallecano | 38,70 mill. € | 52 | 7,90 mill. € | 51 | **-30,80 mill. €** |
| 25 | Atlético de Madrid | 450,00 mill. € | 82 | 314,33 mill. € | 79 | **-135,68 mill. €** |
| 26 | Real Madrid CF | 456,00 mill. € | 38 | 124,15 mill. € | 38 | **-331,85 mill. €** |

### Bundesliga - Balance Transferencias 2022-2026

| # | Club | Gastos | Altas | Ingresos | Bajas | Balance |
|---|------|--------|-------|----------|-------|---------|
| 1 | Eintracht Fráncfort | 267,05 mill. € | 88 | 422,63 mill. € | 90 | **155,58 mill. €** |
| 2 | VfB Stuttgart | 183,89 mill. € | 83 | 299,02 mill. € | 82 | **115,13 mill. €** |
| 3 | RB Leipzig | 502,15 mill. € | 91 | 579,47 mill. € | 88 | **77,32 mill. €** |
| 4 | Hertha Berlín | 13,60 mill. € | 89 | 84,10 mill. € | 86 | **70,50 mill. €** |
| 5 | 1.FSV Mainz 05 | 58,55 mill. € | 64 | 114,10 mill. € | 60 | **55,55 mill. €** |
| 6 | FC Schalke 04 | 20,68 mill. € | 105 | 67,67 mill. € | 100 | **46,99 mill. €** |
| 7 | SC Friburgo | 77,80 mill. € | 41 | 110,53 mill. € | 40 | **32,73 mill. €** |
| 8 | FC Augsburgo | 62,89 mill. € | 89 | 92,80 mill. € | 89 | **29,91 mill. €** |
| 9 | VfL Bochum | 5,39 mill. € | 77 | 26,40 mill. € | 76 | **21,02 mill. €** |
| 10 | SV Werder Bremen | 29,83 mill. € | 59 | 48,51 mill. € | 56 | **18,69 mill. €** |
| 11 | 1.FC Heidenheim 1846 | 12,10 mill. € | 38 | 25,60 mill. € | 37 | **13,50 mill. €** |
| 12 | Borussia Mönchengladbach | 78,73 mill. € | 46 | 90,55 mill. € | 43 | **11,82 mill. €** |
| 13 | TSG 1899 Hoffenheim | 166,35 mill. € | 82 | 170,05 mill. € | 79 | **3,70 mill. €** |
| 14 | FC St. Pauli | 21,65 mill. € | 51 | 22,50 mill. € | 51 | **850 mil €** |
| 15 | SV Darmstadt 98 | 11,30 mill. € | 64 | 11,88 mill. € | 63 | **575 mil €** |
| 16 | Holstein Kiel | 17,00 mill. € | 55 | 15,78 mill. € | 53 | **-1,23 mill. €** |
| 17 | FC Colonia | 42,13 mill. € | 70 | 39,82 mill. € | 68 | **-2,31 mill. €** |
| 18 | Bayer 04 Leverkusen | 350,15 mill. € | 61 | 339,55 mill. € | 60 | **-10,60 mill. €** |
| 19 | Borussia Dortmund | 363,05 mill. € | 50 | 350,70 mill. € | 51 | **-12,35 mill. €** |
| 20 | Hamburgo SV | 29,70 mill. € | 75 | 15,92 mill. € | 69 | **-13,78 mill. €** |
| 21 | 1.FC Unión Berlín | 98,50 mill. € | 89 | 81,92 mill. € | 87 | **-16,58 mill. €** |
| 22 | VfL Wolfsburgo | 198,20 mill. € | 77 | 157,83 mill. € | 76 | **-40,37 mill. €** |
| 23 | Bayern Múnich | 571,80 mill. € | 66 | 480,62 mill. € | 69 | **-91,18 mill. €** |

### Ligue 1 - Balance Transferencias 2022-2026

| # | Club | Gastos | Altas | Ingresos | Bajas | Balance |
|---|------|--------|-------|----------|-------|---------|
| 1 | LOSC Lille | 128,29 mill. € | 68 | 321,47 mill. € | 63 | **193,18 mill. €** |
| 2 | AS Mónaco | 229,85 mill. € | 61 | 390,87 mill. € | 60 | **161,02 mill. €** |
| 3 | Stade de Reims | 91,20 mill. € | 96 | 225,68 mill. € | 96 | **134,48 mill. €** |
| 4 | Stade Rennais FC | 390,80 mill. € | 98 | 518,20 mill. € | 103 | **127,40 mill. €** |
| 5 | RC Lens | 187,29 mill. € | 92 | 305,83 mill. € | 87 | **118,54 mill. €** |
| 6 | FC Metz | 30,26 mill. € | 86 | 100,96 mill. € | 88 | **70,71 mill. €** |
| 7 | Toulouse FC | 51,50 mill. € | 74 | 120,50 mill. € | 76 | **69,00 mill. €** |
| 8 | Angers SCO | 6,65 mill. € | 60 | 73,87 mill. € | 57 | **67,22 mill. €** |
| 9 | Olympique de Lyon | 300,04 mill. € | 98 | 361,65 mill. € | 102 | **61,61 mill. €** |
| 10 | Montpellier HSC | 19,58 mill. € | 53 | 79,55 mill. € | 57 | **59,97 mill. €** |
| 11 | FC Lorient | 67,40 mill. € | 82 | 125,31 mill. € | 81 | **57,91 mill. €** |
| 12 | ESTAC Troyes | 40,05 mill. € | 107 | 88,60 mill. € | 105 | **48,55 mill. €** |
| 13 | Clermont Foot 63 | 9,40 mill. € | 97 | 44,10 mill. € | 96 | **34,70 mill. €** |
| 14 | FC Nantes | 54,95 mill. € | 75 | 88,60 mill. € | 71 | **33,65 mill. €** |
| 15 | Stade Brestois 29 | 27,15 mill. € | 70 | 45,40 mill. € | 72 | **18,25 mill. €** |
| 16 | Le Havre AC | 3,40 mill. € | 80 | 20,55 mill. € | 78 | **17,15 mill. €** |
| 17 | OGC Niza | 189,88 mill. € | 90 | 200,09 mill. € | 86 | **10,21 mill. €** |
| 18 | AC Ajaccio | 400 mil € | 65 | 4,10 mill. € | 69 | **3,70 mill. €** |
| 19 | AJ Auxerre | 14,10 mill. € | 68 | 12,40 mill. € | 71 | **-1,70 mill. €** |
| 20 | AS Saint-Étienne | 56,90 mill. € | 73 | 52,90 mill. € | 76 | **-4,00 mill. €** |
| 21 | Paris FC | 63,60 mill. € | 69 | 14,40 mill. € | 68 | **-49,20 mill. €** |
| 22 | Racing Club de Estrasburgo | 240,60 mill. € | 98 | 139,70 mill. € | 92 | **-100,90 mill. €** |
| 23 | Olympique de Marsella | 430,85 mill. € | 107 | 296,88 mill. € | 102 | **-133,98 mill. €** |
| 24 | París Saint-Germain FC | 950,42 mill. € | 94 | 481,55 mill. € | 104 | **-468,87 mill. €** |

### Serie A - Balance Transferencias 2022-2026

| # | Club | Gastos | Altas | Ingresos | Bajas | Balance |
|---|------|--------|-------|----------|-------|---------|
| 1 | Hellas Verona | 88,83 mill. € | 176 | 208,00 mill. € | 175 | **119,17 mill. €** |
| 2 | US Sassuolo | 140,10 mill. € | 166 | 246,62 mill. € | 168 | **106,52 mill. €** |
| 3 | Empoli FC | 34,20 mill. € | 182 | 135,41 mill. € | 179 | **101,21 mill. €** |
| 4 | Atalanta de Bérgamo | 432,51 mill. € | 166 | 524,26 mill. € | 164 | **91,75 mill. €** |
| 5 | Génova | 97,98 mill. € | 189 | 160,30 mill. € | 193 | **62,32 mill. €** |
| 6 | US Lecce | 62,81 mill. € | 119 | 119,55 mill. € | 113 | **56,75 mill. €** |
| 7 | UC Sampdoria | 24,42 mill. € | 174 | 67,93 mill. € | 171 | **43,51 mill. €** |
| 8 | Torino FC | 139,01 mill. € | 127 | 178,19 mill. € | 126 | **39,17 mill. €** |
| 9 | Spezia | 39,54 mill. € | 130 | 75,57 mill. € | 130 | **36,04 mill. €** |
| 10 | Cagliari | 82,41 mill. € | 114 | 111,32 mill. € | 112 | **28,91 mill. €** |
| 11 | Frosinone Calcio | 16,39 mill. € | 145 | 38,99 mill. € | 141 | **22,60 mill. €** |
| 12 | Udinese | 167,36 mill. € | 108 | 189,78 mill. € | 101 | **22,42 mill. €** |
| 13 | AS Roma | 224,57 mill. € | 102 | 243,35 mill. € | 105 | **18,78 mill. €** |
| 14 | Venezia FC | 44,52 mill. € | 139 | 47,64 mill. € | 140 | **3,12 mill. €** |
| 15 | Bolonia | 253,05 mill. € | 124 | 254,60 mill. € | 125 | **1,56 mill. €** |
| 16 | Parma | 121,86 mill. € | 115 | 104,03 mill. € | 117 | **-17,83 mill. €** |
| 17 | Fiorentina | 243,83 mill. € | 164 | 220,73 mill. € | 161 | **-23,10 mill. €** |
| 18 | SS Lazio | 165,53 mill. € | 113 | 138,55 mill. € | 111 | **-26,98 mill. €** |
| 19 | US Salernitana 1919 | 79,30 mill. € | 159 | 51,53 mill. € | 169 | **-27,77 mill. €** |
| 20 | Pisa Sporting Club | 46,90 mill. € | 149 | 16,68 mill. € | 145 | **-30,23 mill. €** |
| 21 | AC Monza | 110,78 mill. € | 116 | 65,80 mill. € | 117 | **-44,98 mill. €** |
| 22 | US Cremonese | 63,25 mill. € | 166 | 13,54 mill. € | 162 | **-49,71 mill. €** |
| 23 | SSC Nápoles | 465,87 mill. € | 126 | 397,84 mill. € | 123 | **-68,03 mill. €** |
| 24 | Inter de Milán | 309,08 mill. € | 151 | 219,01 mill. € | 151 | **-90,07 mill. €** |
| 25 | AC Milan | 485,17 mill. € | 111 | 314,93 mill. € | 117 | **-170,23 mill. €** |
| 26 | Juventus de Turín | 558,60 mill. € | 99 | 376,85 mill. € | 100 | **-181,75 mill. €** |
| 27 | Como 1907 | 217,76 mill. € | 123 | 17,85 mill. € | 119 | **-199,91 mill. €** |

### Premier League - Balance Transferencias 2022-2026

| # | Club | Gastos | Altas | Ingresos | Bajas | Balance |
|---|------|--------|-------|----------|-------|---------|
| 1 | Leicester City | 186,94 mill. € | 53 | 292,00 mill. € | 55 | **105,06 mill. €** |
| 2 | Southampton FC | 354,76 mill. € | 82 | 362,00 mill. € | 78 | **7,24 mill. €** |
| 3 | Sheffield United | 99,09 mill. € | 77 | 102,55 mill. € | 68 | **3,47 mill. €** |
| 4 | Brighton & Hove Albion | 524,00 mill. € | 95 | 523,39 mill. € | 92 | **-610 mil €** |
| 5 | Everton FC | 303,52 mill. € | 64 | 283,15 mill. € | 67 | **-20,37 mill. €** |
| 6 | Leeds United | 345,91 mill. € | 77 | 318,98 mill. € | 78 | **-26,93 mill. €** |
| 7 | Luton Town | 62,57 mill. € | 98 | 30,55 mill. € | 97 | **-32,02 mill. €** |
| 8 | Wolverhampton Wanderers | 537,91 mill. € | 92 | 487,77 mill. € | 93 | **-50,14 mill. €** |
| 9 | Aston Villa | 469,20 mill. € | 74 | 399,48 mill. € | 78 | **-69,72 mill. €** |
| 10 | Brentford FC | 318,70 mill. € | 71 | 243,65 mill. € | 67 | **-75,05 mill. €** |
| 11 | Crystal Palace | 261,60 mill. € | 60 | 180,31 mill. € | 54 | **-81,30 mill. €** |
| 12 | Burnley FC | 339,76 mill. € | 115 | 224,39 mill. € | 106 | **-115,38 mill. €** |
| 13 | Fulham FC | 285,32 mill. € | 54 | 164,40 mill. € | 57 | **-120,92 mill. €** |
| 14 | Ipswich Town | 219,99 mill. € | 82 | 90,54 mill. € | 83 | **-129,45 mill. €** |
| 15 | Sunderland AFC | 218,16 mill. € | 85 | 79,82 mill. € | 72 | **-138,35 mill. €** |
| 16 | AFC Bournemouth | 496,29 mill. € | 75 | 306,00 mill. € | 75 | **-190,30 mill. €** |
| 17 | West Ham United | 629,36 mill. € | 60 | 330,06 mill. € | 56 | **-299,30 mill. €** |
| 18 | Manchester City | 864,40 mill. € | 79 | 513,17 mill. € | 74 | **-351,23 mill. €** |
| 19 | Newcastle United | 686,15 mill. € | 52 | 324,21 mill. € | 51 | **-361,94 mill. €** |
| 20 | Nottingham Forest | 672,38 mill. € | 125 | 303,42 mill. € | 119 | **-368,96 mill. €** |
| 21 | Liverpool FC | 837,80 mill. € | 48 | 407,30 mill. € | 54 | **-430,50 mill. €** |
| 22 | Tottenham Hotspur | 847,95 mill. € | 74 | 258,25 mill. € | 68 | **-589,70 mill. €** |
| 23 | Arsenal FC | 823,90 mill. € | 65 | 187,09 mill. € | 61 | **-636,81 mill. €** |
| 24 | Manchester United | 950,85 mill. € | 64 | 278,82 mill. € | 70 | **-672,02 mill. €** |
| 25 | Chelsea FC | 1,72 mil mill. € | 116 | 918,71 mill. € | 113 | **-796,69 mill. €** |
---

## ANEXO A: Métricas Disponibles

Este anexo documenta las 169+ métricas empleadas en el análisis cuantitativo de similitud entre jugadores. Las métricas provienen de tres fuentes complementarias: FBref (estadísticas avanzadas derivadas de StatsBomb), Understat (métricas xG granulares), y Transfermarkt (información contractual y de mercado).

**Nota sobre normalización:** Las tablas siguientes muestran las métricas en su formato original (FBref proporciona valores absolutos o per90). Durante el pipeline de análisis, todas las métricas marcadas como "per100touches" se transforman dividiendo por toques totales × 100, eliminando el sesgo de volumen de participación.

### A.1. FBref - Estadísticas Avanzadas (185 métricas totales, ~150 normalizadas)

**Categoría A: Goles y Finalización**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| goals | per100touches | Big 5 + Extras |
| non_penalty_goals | per100touches | Big 5 + Extras |
| penalty_kicks_made | per100touches | Big 5 + Extras |
| penalty_kicks_attempted | per100touches | Big 5 + Extras |
| shots | per100touches | Big 5 + Extras |
| shots_on_target | per100touches | Big 5 + Extras |
| shots_on_target_pct | NO (porcentaje) | Big 5 + Extras |
| avg_shot_distance | NO (métrica absoluta) | Big 5 + Extras |
| shots_free_kicks | per100touches | Big 5 + Extras |
| penalty_kicks_won | per100touches | Big 5 + Extras |
| penalty_kicks_conceded | per100touches | Big 5 + Extras |

**Categoría B: Pases**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| passes_completed | per100touches | Big 5 + Extras |
| passes_attempted | per100touches | Big 5 + Extras |
| pass_completion_pct | NO (porcentaje) | Big 5 + Extras |
| passes_total_distance | per100touches | Big 5 + Extras |
| passes_progressive_distance | per100touches | Big 5 + Extras |
| passes_completed_short | per100touches | Big 5 + Extras |
| passes_attempted_short | per100touches | Big 5 + Extras |
| passes_completed_medium | per100touches | Big 5 + Extras |
| passes_attempted_medium | per100touches | Big 5 + Extras |
| passes_completed_long | per100touches | Big 5 + Extras |
| passes_attempted_long | per100touches | Big 5 + Extras |
| assists | per100touches | Big 5 + Extras |
| expected_assists | per100touches | Big 5 + Extras |
| key_passes | per100touches | Big 5 + Extras |
| passes_into_final_third | per100touches | Big 5 + Extras |
| passes_into_penalty_area | per100touches | Big 5 + Extras |
| crosses_into_penalty_area | per100touches | Big 5 + Extras |
| progressive_passes | per100touches | Big 5 + Extras |

**Categoría C: Tipos de Pase (Pass Types)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| passes_live | per100touches | Big 5 + Extras |
| passes_dead | per100touches | Big 5 + Extras |
| passes_from_free_kicks | per100touches | Big 5 + Extras |
| through_balls | per100touches | Big 5 + Extras |
| switches | per100touches | Big 5 + Extras |
| crosses | per100touches | Big 5 + Extras |
| throw_ins | per100touches | Big 5 + Extras |
| corner_kicks | per100touches | Big 5 + Extras |
| corner_kicks_inswinging | per100touches | Big 5 + Extras |
| corner_kicks_outswinging | per100touches | Big 5 + Extras |
| corner_kicks_straight | per100touches | Big 5 + Extras |
| passes_offside | per100touches | Big 5 + Extras |
| passes_blocked | per100touches | Big 5 + Extras |

**Categoría D: Creación de Ocasiones (Goal and Shot Creation - SCA/GCA)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| SCA_SCA | per100touches | Big 5 + Extras |
| SCA_PassLive | per100touches | Big 5 + Extras |
| SCA_PassDead | per100touches | Big 5 + Extras |
| SCA_TO | per100touches | Big 5 + Extras |
| SCA_Sh | per100touches | Big 5 + Extras |
| SCA_Fld | per100touches | Big 5 + Extras |
| SCA_Def | per100touches | Big 5 + Extras |
| GCA_GCA | per100touches | Big 5 + Extras |
| GCA_PassLive | per100touches | Big 5 + Extras |
| GCA_PassDead | per100touches | Big 5 + Extras |
| GCA_TO | per100touches | Big 5 + Extras |
| GCA_Sh | per100touches | Big 5 + Extras |
| GCA_Fld | per100touches | Big 5 + Extras |
| GCA_Def | per100touches | Big 5 + Extras |

**Categoría E: Acciones Defensivas**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| tackles | per100touches | Big 5 + Extras |
| tackles_won | per100touches | Big 5 + Extras |
| tackles_def_3rd | per100touches | Big 5 + Extras |
| tackles_mid_3rd | per100touches | Big 5 + Extras |
| tackles_att_3rd | per100touches | Big 5 + Extras |
| challenge_tackles | per100touches | Big 5 + Extras |
| challenges | per100touches | Big 5 + Extras |
| challenge_tackles_pct | NO (porcentaje) | Big 5 + Extras |
| challenges_lost | per100touches | Big 5 + Extras |
| blocked_shots | per100touches | Big 5 + Extras |
| blocked_passes | per100touches | Big 5 + Extras |
| interceptions | per100touches | Big 5 + Extras |
| clearances | per100touches | Big 5 + Extras |
| errors | per100touches | Big 5 + Extras |

**Categoría F: Posesión y Toques (Possession)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| touches | per100touches | Big 5 + Extras |
| touches_def_pen_area | per100touches | Big 5 + Extras |
| touches_def_3rd | per100touches | Big 5 + Extras |
| touches_mid_3rd | per100touches | Big 5 + Extras |
| touches_att_3rd | per100touches | Big 5 + Extras |
| touches_att_pen_area | per100touches | Big 5 + Extras |
| touches_live_ball | per100touches | Big 5 + Extras |
| take_ons_attempted | per100touches | Big 5 + Extras |
| take_ons_successful | per100touches | Big 5 + Extras |
| take_ons_successful_pct | NO (porcentaje) | Big 5 + Extras |
| take_ons_tackled | per100touches | Big 5 + Extras |
| carries | per100touches | Big 5 + Extras |
| carries_total_distance | per100touches | Big 5 + Extras |
| carries_progressive_distance | per100touches | Big 5 + Extras |
| progressive_carries | per100touches | Big 5 + Extras |
| carries_into_final_third | per100touches | Big 5 + Extras |
| carries_into_penalty_area | per100touches | Big 5 + Extras |
| miscontrols | per100touches | Big 5 + Extras |
| dispossessed | per100touches | Big 5 + Extras |
| passes_received | per100touches | Big 5 + Extras |
| progressive_passes_received | per100touches | Big 5 + Extras |

**Categoría G: Duelos Aéreos**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| aerials_won | per100touches | Big 5 + Extras |
| aerials_lost | per100touches | Big 5 + Extras |
| aerials_won_pct | NO (porcentaje) | Big 5 + Extras |

**Categoría H: Disciplina**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| fouls_committed | per100touches | Big 5 + Extras |
| fouls_drawn | per100touches | Big 5 + Extras |
| offsides | per100touches | Big 5 + Extras |
| yellow_cards | per100touches | Big 5 + Extras |
| red_cards | per100touches | Big 5 + Extras |
| second_yellow_cards | per100touches | Big 5 + Extras |

**Categoría I: Expected Goals (xG)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| expected_goals | per100touches | Big 5 + Extras |
| non_penalty_expected_goals | per100touches | Big 5 + Extras |
| non_penalty_expected_goals_plus_assists | NO (suma compuesta) | Big 5 + Extras |
| expected_goals_on_target | per100touches | Big 5 + Extras |
| expected_goals_buildup | per100touches | Big 5 + Extras |

**Categoría J: Porteros (excluidas del análisis outfield)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| saves | per100touches | Big 5 + Extras |
| save_pct | NO (porcentaje) | Big 5 + Extras |
| clean_sheets | NO (absoluto) | Big 5 + Extras |
| goals_against_per_90 | Ya per90 | Big 5 + Extras |
| psxg_minus_goals_allowed | per100touches | Big 5 + Extras |
| launched_passes_completed | per100touches | Big 5 + Extras |
| goal_kicks_launched | per100touches | Big 5 + Extras |
| sweeper_defensive_actions_outside_pen_area | per100touches | Big 5 + Extras |

**Categoría K: Métricas de Equipo (Team Success)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| on_goals_for | NO (contexto) | Big 5 + Extras |
| on_goals_against | NO (contexto) | Big 5 + Extras |
| plus_minus | NO (diferencial) | Big 5 + Extras |
| on_xg_for | NO (contexto) | Big 5 + Extras |
| on_xg_against | NO (contexto) | Big 5 + Extras |
| xg_plus_minus | NO (diferencial) | Big 5 + Extras |

**Categoría L: Participación (Playing Time)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| minutes_played | NO (base normalización) | Big 5 + Extras |
| games | NO (absoluto) | Big 5 + Extras |
| games_started | NO (absoluto) | Big 5 + Extras |
| minutes_per_game | NO (promedio) | Big 5 + Extras |
| games_subs | NO (absoluto) | Big 5 + Extras |
| unused_sub | NO (absoluto) | Big 5 + Extras |
| points_per_game | NO (métrica equipo) | Big 5 + Extras |

**Categoría M: Resultados de Equipo**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| wins | NO (absoluto) | Big 5 + Extras |
| draws | NO (absoluto) | Big 5 + Extras |
| losses | NO (absoluto) | Big 5 + Extras |

**Categoría N: Eventos Específicos**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| own_goals | per100touches | Big 5 + Extras |
| goals_against | per100touches | Big 5 + Extras |
| goals_from_penalties | per100touches | Big 5 + Extras |
| goals_from_free_kicks | per100touches | Big 5 + Extras |
| goals_from_corners | per100touches | Big 5 + Extras |

### A.2. Understat - Métricas xG Granulares (10 métricas totales, 7 normalizadas)

| Métrica | Normalización | Disponibilidad | Descripción |
|---------|---------------|----------------|-------------|
| understat_xg | per100touches | Big 5 | xG total acumulado (shots xG) |
| understat_xg_assist | per100touches | Big 5 | xA total (expected assists) |
| understat_xg_chain | per100touches | Big 5 | xG generado en cadenas ofensivas donde participó |
| understat_xg_buildup | per100touches | Big 5 | xG generado en buildups donde participó (excluye shot y key pass) |
| understat_shots | per100touches | Big 5 | Total de tiros registrados |
| understat_key_passes | per100touches | Big 5 | Pases clave que generan shot |
| understat_npxg | per100touches | Big 5 | Non-penalty xG |
| understat_buildup_involvement_pct | NO (porcentaje) | Big 5 | % de buildups del equipo donde participó |
| understat_player_id | NO (ID) | Big 5 | Identificador interno Understat |
| understat_team_id | NO (ID) | Big 5 | Identificador equipo Understat |

**Nota:** Understat solo cubre las Big 5 leagues (ENG, ESP, ITA, GER, FRA). Ligas extras (Portugal, Países Bajos, etc.) NO tienen datos Understat. El algoritmo rellena con 0 las métricas Understat faltantes para evitar exclusión de jugadores de ligas secundarias.

### A.3. Transfermarkt - Información Contractual y de Mercado (9 campos)

| Campo | Tipo | Disponibilidad | Descripción |
|-------|------|----------------|-------------|
| transfermarkt_player_id | ID | Todas | Identificador único Transfermarkt |
| transfermarkt_market_value_eur | Numérico | Todas | Valor de mercado en EUR (actualizado semestralmente) |
| transfermarkt_birth_date | Fecha | Todas | Fecha nacimiento (YYYY-MM-DD) |
| transfermarkt_club | String | Todas | Club actual según Transfermarkt |
| transfermarkt_contract_start_date | Fecha | Todas | Inicio contrato actual |
| transfermarkt_contract_end_date | Fecha | Todas | Fin contrato actual |
| transfermarkt_contract_is_current | Boolean | Todas | Si contrato sigue vigente |
| transfermarkt_position_specific | String | Todas | Posición específica (CB, LW, ST, CAM, etc.) |
| transfermarkt_primary_foot | String | Todas | Pie dominante (left, right, both) |

**Uso en análisis:** Los campos Transfermarkt se emplean para filtrado pre-algoritmo (max_market_value, max_age, positions) pero NO se normalizan per90 ni se incluyen en el cálculo de similitud. Solo las métricas de rendimiento (FBref + Understat) participan en PCA + Cosine.

### A.4. Métricas Derivadas Generadas en el Pipeline

Durante el procesamiento se generan métricas adicionales:

| Métrica | Fuente | Descripción |
|---------|--------|-------------|
| age | Transfermarkt | Edad calculada desde birth_date |
| unique_player_id | Hash | SHA256(name + birth_year + nationality) → 16 chars |
| data_quality_score | Interno | 0.0-1.0, mide completitud de métricas |
| is_transfer | Interno | Boolean, detecta cambios de equipo entre temporadas |
| transfer_count | Interno | Número de transferencias detectadas |

### A.5. Exclusiones del Análisis

**Métricas excluidas de normalización per90:**
- Porcentajes inherentes: `pass_completion_pct`, `shots_on_target_pct`, `take_ons_successful_pct`, `aerials_won_pct`, `save_pct`
- Métricas ya normalizadas: `goals_against_per_90`, `plus_minus_per90`, `xg_plus_minus_per90`
- Ratios y promedios: `npxG/Sh`, `avg_shot_distance`, `minutes_per_game`
- Métricas contextuales de equipo: `on_goals_for`, `on_xg_for`, `points_per_game`, `wins`, `draws`, `losses`
- IDs y metadata: `understat_player_id`, `transfermarkt_player_id`, `birth_date`

**Métricas de portero excluidas para outfield players:**
Todas las métricas que contienen keywords GK: `['Save', 'PSxG', 'CS_per90', 'CS%', 'GA90', 'SoTA', 'Goal Kicks', 'Launched', 'Passes_Att (GK)', 'Sweeper', 'Penalty Kicks_PK']`

### A.6. Total de Métricas por Fase

| Fase | FBref | Understat | Transfermarkt | Total |
|------|-------|-----------|---------------|-------|
| Raw JSONB | 185 | 10 | 9 | 204 |
| Post per100touches | 153 | 7 | 0 (filtro) | 160 |
| Post excl. GK | 141 | 7 | 0 | 148 |
| Input PCA | ~140-150 per100touches | + metadata (position, league, season) |

**Nota sobre normalización:** A diferencia de la normalización per90 (métricas divididas entre minutos jugados × 90), este análisis emplea normalización **per 100 touches** (métricas divididas entre toques totales × 100). Esta aproximación elimina el sesgo de volumen de participación: dos jugadores con estilos similares pero diferente tiempo en campo mostrarán perfiles comparables, independientemente de si uno juega 2000 minutos y otro 1000.

---

## ANEXO B: Perfiles de Radar por Posición

Este anexo documenta las 10 métricas seleccionadas para cada perfil posicional en los radares comparativos. Cada métrica se justifica por su relevancia funcional para evaluar el rendimiento específico de esa demarcación.

### B.1. Delantero Centro (ST / CF)

El delantero centro tiene una función principal: convertir ocasiones en goles. Las métricas seleccionadas evalúan su capacidad de finalización, generación de oportunidades propias y contribución al juego asociativo.

| # | Métrica | Qué mide | Por qué importa para un delantero centro |
|---|---------|----------|------------------------------------------|
| 1 | **Expected Goals (xG)** | Suma del valor de todas las ocasiones que tuvo el jugador, donde cada disparo vale entre 0 y 1 según la probabilidad de que termine en gol | Un delantero que acumula alto xG se posiciona bien y genera ocasiones de calidad; indica que llega a zonas peligrosas aunque no siempre marque |
| 2 | **Goals** | Goles marcados | La producción final; lo que aparece en el marcador y define el rendimiento histórico del jugador |
| 3 | **Shots** | Número total de disparos intentados | Mide volumen de finalización; un delantero que dispara poco no cumple su función aunque tenga buena puntería |
| 4 | **Touches in Box** | Toques de balón dentro del área rival | Indica presencia en zona de peligro; un delantero que toca poco el balón en el área no genera amenaza constante |
| 5 | **Expected Assists (xA)** | Suma del valor esperado de los pases que dieron lugar a disparo, ponderados por la probabilidad de que ese disparo termine en gol | Mide capacidad de generar ocasiones para compañeros; relevante para delanteros que combinan o asisten además de rematar |
| 6 | **Dribbles Completed** | Regates exitosos que superan a un rival | Indica capacidad de desequilibrio individual; útil para delanteros que encaran en el uno contra uno |
| 7 | **npxG per Shot** | xG sin penaltis dividido entre número de disparos | Mide calidad de las ocasiones: un valor alto indica que dispara desde posiciones favorables, no desde lejos o en ángulos difíciles |
| 8 | **Goals - xG** | Diferencia entre goles reales y goles esperados | Indica si el jugador rinde por encima o debajo de lo esperado; valores positivos sugieren buena definición, negativos mala puntería o mala suerte |
| 9 | **Fouls Drawn** | Faltas recibidas | Mide capacidad de provocar errores rivales; un delantero que atrae faltas en zona de peligro genera tiros libres y tarjetas |
| 10 | **Shot Creating Actions (SCA)** | Acciones (pases, regates, faltas recibidas) que desembocan en un disparo de un compañero | Mide contribución a la creación de ocasiones del equipo más allá de los propios disparos |

### B.2. Extremo (LW / RW)

El extremo combina funciones ofensivas de banda con penetración hacia el área. Sus métricas evalúan desequilibrio individual, producción de gol y asistencia, y contribución al juego colectivo desde posiciones amplias.

| # | Métrica | Qué mide | Por qué importa para un extremo |
|---|---------|----------|--------------------------------|
| 1 | **Expected Goals (xG)** | Valor acumulado de las ocasiones de disparo | Un extremo moderno debe generar ocasiones propias, no solo asistir; el xG mide su amenaza directa |
| 2 | **Shots** | Disparos intentados | Volumen ofensivo; extremos que disparan poco no aprovechan las llegadas al área |
| 3 | **Expected Assists (xA)** | Valor esperado de los pases que generan disparo | Función clásica del extremo: centrar, asistir, filtrar balones al área |
| 4 | **Dribbles Completed** | Regates exitosos | Capacidad de superar rivales en el uno contra uno; esencial para un jugador de banda |
| 5 | **Touches in Box** | Toques dentro del área rival | Indica si el extremo busca el gol entrando al área o se queda en banda sin profundidad |
| 6 | **Shot Creating Actions (SCA)** | Acciones que desembocan en disparo de un compañero | Mide contribución total a la creación ofensiva del equipo |
| 7 | **Crosses** | Centros al área | Función tradicional del extremo; capacidad de poner balones peligrosos desde banda |
| 8 | **Progressive Carries** | Conducciones que avanzan el balón significativamente hacia portería rival | Mide capacidad de transportar el balón en transiciones y ataques posicionales |
| 9 | **npxG per Shot** | Calidad media de las ocasiones | Indica si el extremo dispara desde buenas posiciones o fuerza tiros difíciles |
| 10 | **Fouls Drawn** | Faltas recibidas | Un extremo que provoca faltas genera tiros libres en zonas peligrosas y desgasta a los laterales rivales |

### B.3. Mediocampista (CM / CAM)

El mediocampista es el enlace entre defensa y ataque. Sus métricas evalúan capacidad de progresión, contribución creativa, y equilibrio entre funciones ofensivas y defensivas.

| # | Métrica | Qué mide | Por qué importa para un mediocampista |
|---|---------|----------|--------------------------------------|
| 1 | **Progressive Passes** | Pases que avanzan el balón significativamente hacia portería rival | Función principal del medio: conectar líneas y hacer progresar el juego |
| 2 | **Progressive Carries** | Conducciones que avanzan el balón hacia zonas de peligro | Capacidad de romper líneas con el balón en los pies, no solo pasando |
| 3 | **Shot Creating Actions (SCA)** | Acciones que desembocan en disparo de compañero | Mide aportación a la fase final del ataque |
| 4 | **Expected Assists (xA)** | Valor esperado de pases que generan disparo | Capacidad de filtrar el último pase o asistencia |
| 5 | **Passes into Penalty Area** | Pases completados al área rival | Mide capacidad de meter balones peligrosos en zona de finalización |
| 6 | **Dribbles Completed** | Regates exitosos | Capacidad de superar la presión y crear superioridades |
| 7 | **Tackles + Interceptions** | Suma de entradas ganadas e intercepciones | Contribución defensiva; un mediocampista debe ayudar en recuperación |
| 8 | **Interceptions** | Balones cortados | Capacidad de leer el juego y anticipar pases rivales |
| 9 | **Fouls Drawn** | Faltas recibidas | Indica capacidad de proteger el balón bajo presión y generar faltas |
| 10 | **Pass Accuracy %** | Porcentaje de pases completados | Fiabilidad en la distribución; un mediocampista que pierde muchos balones desestabiliza el equipo |

### B.4. Pivote Defensivo (CDM / DM)

El pivote es el ancla del equipo: protege la defensa, distribuye juego y marca el tempo. Sus métricas priorizan recuperación, seguridad en el pase y capacidad de progresión controlada.

| # | Métrica | Qué mide | Por qué importa para un pivote |
|---|---------|----------|-------------------------------|
| 1 | **Pass Accuracy %** | Porcentaje de pases completados | Un pivote que pierde balones en zona de construcción genera ocasiones rivales; la seguridad es prioritaria |
| 2 | **Progressive Passes** | Pases que avanzan el juego | Capacidad de encontrar líneas de pase hacia adelante, no solo pasar en horizontal |
| 3 | **Tackles + Interceptions** | Entradas ganadas + intercepciones | Función defensiva principal: cortar ataques rivales y recuperar posesión |
| 4 | **Interceptions** | Balones cortados | Lectura de juego; capacidad de anticipar y cortar pases |
| 5 | **Tackle Success %** | Porcentaje de entradas ganadas sobre intentadas | Eficiencia defensiva; un pivote que falla entradas deja huecos peligrosos |
| 6 | **Progressive Carries** | Conducciones hacia adelante | Capacidad de conducir para atraer presión y liberar compañeros |
| 7 | **Shot Creating Actions (SCA)** | Acciones que generan disparo | Aportación ofensiva; pivotes modernos contribuyen a la creación |
| 8 | **Recoveries** | Balones recuperados (incluye duelos y segundas jugadas) | Volumen de trabajo defensivo; cuántas veces recupera el balón para su equipo |
| 9 | **Fouls Drawn** | Faltas recibidas | Capacidad de aguantar presión y provocar faltas que frenan transiciones rivales |
| 10 | **Expected Assists (xA)** | Valor esperado de pases que generan disparo | Capacidad de filtrar pases peligrosos desde posiciones retrasadas |

### B.5. Defensa Central (CB)

El central protege la portería y construye desde atrás. Sus métricas evalúan solidez defensiva, capacidad en duelos y contribución a la salida de balón.

| # | Métrica | Qué mide | Por qué importa para un central |
|---|---------|----------|--------------------------------|
| 1 | **Pass Accuracy %** | Porcentaje de pases completados | Un central que pierde balones en salida regala ocasiones; la seguridad es fundamental |
| 2 | **Tackle Success %** | Porcentaje de entradas ganadas | Eficiencia en duelos directos; un central que falla entradas permite progresión rival |
| 3 | **Aerial Duels Won** | Duelos aéreos ganados (total) | Volumen de dominio aéreo; fundamental en balones largos, centros y balón parado |
| 4 | **Aerial Duel Success %** | Porcentaje de duelos aéreos ganados | Eficiencia en el juego aéreo; indica superioridad física y técnica de cabeceo |
| 5 | **Passes into Final Third** | Pases completados al tercio ofensivo | Capacidad de construir juego y filtrar pases que rompen líneas |
| 6 | **Clearances** | Despejes | Capacidad de alejar el peligro; indica solvencia en situaciones defensivas comprometidas |
| 7 | **Progressive Passes** | Pases que avanzan el juego | Función de central moderno: no solo despejar, sino iniciar jugadas |
| 8 | **Tackles + Interceptions** | Entradas + intercepciones | Volumen de acciones defensivas; cuánto trabajo defensivo realiza |
| 9 | **Interceptions** | Balones cortados | Lectura de juego y anticipación; capacidad de cortar pases antes de que lleguen |
| 10 | **Blocked Shots** | Disparos bloqueados | Capacidad de poner el cuerpo; última línea de defensa antes del portero |

### B.6. Lateral (LB / RB)

El lateral moderno combina funciones defensivas con proyección ofensiva. Sus métricas equilibran contribución en ataque con solidez en defensa.

| # | Métrica | Qué mide | Por qué importa para un lateral |
|---|---------|----------|--------------------------------|
| 1 | **Pass Accuracy %** | Porcentaje de pases completados | Seguridad en la distribución; un lateral que pierde balones compromete la salida |
| 2 | **Progressive Passes** | Pases que avanzan el juego | Capacidad de conectar con mediocampistas y extremos en progresión |
| 3 | **Progressive Carries** | Conducciones hacia adelante | Capacidad de subir la banda con el balón controlado |
| 4 | **Crosses** | Centros al área | Función ofensiva clásica del lateral; capacidad de poner balones peligrosos |
| 5 | **Passes into Penalty Area** | Pases al área rival | Capacidad de meter balones en zona de finalización desde posiciones abiertas |
| 6 | **Expected Assists (xA)** | Valor esperado de pases que generan disparo | Contribución directa a la creación de ocasiones |
| 7 | **Touches in Attacking Third** | Toques en tercio ofensivo | Indica proyección ofensiva; un lateral que toca poco arriba no sube la banda |
| 8 | **Tackles + Interceptions** | Entradas + intercepciones | Contribución defensiva; un lateral debe defender su banda |
| 9 | **Tackle Success %** | Porcentaje de entradas ganadas | Eficiencia en duelos con extremos rivales |
| 10 | **Dribbles Completed** | Regates exitosos | Capacidad de superar rivales en banda; útil para laterales ofensivos |

### B.7. Portero (GK)

El portero tiene funciones únicas: evitar goles y distribuir juego. Sus métricas combinan capacidad de parada con contribución al juego con los pies.

| # | Métrica | Qué mide | Por qué importa para un portero |
|---|---------|----------|--------------------------------|
| 1 | **Save %** | Porcentaje de disparos a puerta detenidos | Función principal: parar tiros; indica capacidad de evitar goles |
| 2 | **PSxG +/-** | Diferencia entre goles esperados post-disparo y goles encajados | Indica si el portero rinde por encima o debajo de lo esperado según la dificultad de los disparos recibidos |
| 3 | **Clean Sheet %** | Porcentaje de partidos sin encajar gol | Indicador de solidez global; aunque depende del equipo, refleja rendimiento defensivo conjunto |
| 4 | **Goals Against per 90** | Goles encajados por partido | Producción negativa directa; cuántos goles recibe de media |
| 5 | **Pass Accuracy %** | Porcentaje de pases completados | Fiabilidad en juego con los pies; fundamental en equipos que construyen desde atrás |
| 6 | **Long Pass Completion %** | Porcentaje de pases largos completados | Capacidad de encontrar compañeros en largo; útil para equipos que juegan directo |
| 7 | **Goal Kicks Long %** | Porcentaje de saques de puerta largos | Indica estilo de juego: alto = juego directo, bajo = construcción corta |
| 8 | **Sweeper Actions per 90** | Acciones fuera del área (salidas, anticipaciones) | Capacidad de actuar como líbero; fundamental en equipos con línea alta |
| 9 | **Sweeper Average Distance** | Distancia media de acciones fuera del área | Indica hasta dónde sale el portero; porteros proactivos tienen mayor distancia |
| 10 | **Shots Faced per 90** | Disparos recibidos por partido | Contexto defensivo; más disparos = más trabajo pero también más oportunidades de lucirse |

### B.8. Justificación del Sistema de 10 Métricas

La selección de exactamente 10 métricas por posición responde a criterios de visualización y comparabilidad:

1. **Legibilidad del radar:** 10 ejes permiten representación clara sin saturación visual
2. **Cobertura funcional:** Suficientes métricas para capturar las dimensiones relevantes de cada posición
3. **Comparabilidad directa:** Mismo número de métricas para todos los perfiles facilita comparaciones cross-position
4. **Balance ofensivo-defensivo:** Cada perfil incluye métricas de ambas fases del juego en proporción adecuada a la posición

Las métricas que aparecen en porcentaje (Pass Accuracy %, Tackle Success %, Aerial Duel %) NO se normalizan per 100 touches porque ya son ratios inherentes. Las demás métricas se expresan per 100 touches para eliminar el sesgo de volumen de participación.

**Nota final:** La reducción de 148 métricas a 141 se debe a la exclusión automática de columnas con <5 valores válidos en el pool analizado, lo cual varía por posición y temporada.

---

## ANEXO C: Visualizaciones Completas

### C.1. Villarreal CF

#### C.1.1. Delantero Centro
#### C.1.2. Portero
#### C.1.3. Defensa Central
#### C.1.4. Lateral Izquierdo
#### C.1.5. Mediapunta / Extremo

### C.2. Eintracht Frankfurt

#### C.2.1. Delantero Centro
#### C.2.2. Defensa Central

### C.3. LOSC Lille

#### C.3.1. Defensa Central
#### C.3.2. Mediocampista Defensivo
#### C.3.3. Delantero Centro

