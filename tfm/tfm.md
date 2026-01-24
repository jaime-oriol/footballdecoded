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

5. [Conclusiones](#5-conclusiones)................................................................................................................................ 14

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

**Limitaciones del método.** _El algoritmo retiene 85% de varianza explicada mediante PCA, descartando 15% de información que puede contener matices distintivos entre perfiles híbridos. La estandarización z-score implica que jugadores con perfiles proporcionales idénticos pero diferente nivel de producción (percentil 50 vs percentil 95) obtienen similitud moderada, no alta. Adicionalmente, el diseño no permite identificar alternativas que los clubes consideraron, solo valida decisiones ejecutadas. Factores cualitativos (liderazgo, adaptación táctica, viabilidad económica) quedan fuera del alcance del análisis cuantitativo. La sección 2.3 documenta exhaustivamente estas limitaciones._

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

Un fichaje VALIDADO significa que el club identificó un jugador estadísticamente similar al vendido, demostrando proceso de scouting fundamentado en datos. Sin embargo, similar no implica mejor ni garantiza rendimiento futuro. Un fichaje NO_VALIDADO indica que la decisión priorizó otros criterios (cambio táctico deliberado, potencial de desarrollo, restricciones económicas, oportunidad de mercado) igualmente válidos pero no capturables mediante métricas históricas.

**La similitud estadística es condición suficiente para validar criterio analítico, pero no es condición necesaria para éxito deportivo.** Un fichaje VALIDADO puede fracasar por factores no estadísticos (adaptación, lesiones, contexto táctico). Un fichaje NO_VALIDADO puede triunfar si el club deliberadamente buscó un perfil diferente o si el jugador mejora en el nuevo contexto.

**Caso especial: Upgrades que aparecen como NO_VALIDADO.** Un fichaje objetivamente superior puede clasificarse como NO_VALIDADO cuando el club busca un upgrade significativo, no un reemplazo equivalente. _Ejemplo:_ vender delantero con 0.45 xG/90 (percentil 60) y fichar uno con 0.85 xG/90 (percentil 95). La estandarización z-score sitúa sus vectores en posiciones distantes pese a perfil funcional análogo. **El método no distingue dirección de la diferencia**: NO_VALIDADO indica "perfil estadísticamente distante" sin especificar si es distante-inferior o distante-superior. Cuando el fichaje demuestre rendimiento superior al vendido, la explicación correcta es "el club buscó mejora, no equivalencia".

**Conclusión:** El algoritmo responde a "¿El fichaje tiene fundamento estadístico respecto al vendido?" La utilidad radica en distinguir decisiones data-driven de decisiones oportunistas, no en predecir cuáles funcionarán mejor.

### 2.3. Factores No Capturados por el Análisis

El proceso real de fichaje de un jugador profesional involucra docenas de variables que este análisis no puede capturar debido a limitaciones de acceso a datos, naturaleza cualitativa de la información, o ausencia de fuentes públicas fiables. Esta sección documenta exhaustivamente dichos factores para contextualizar correctamente el alcance y las limitaciones del método.

#### 2.3.1. Datos No Disponibles en Fuentes Públicas Gratuitas

**Datos físicos y de tracking.** _Las métricas de rendimiento físico constituyen una dimensión crítica en el scouting profesional que este análisis no incorpora. La distancia total recorrida por partido, número y velocidad de sprints, aceleraciones y desaceleraciones, velocidad máxima alcanzada, y métricas de intensidad de presión (PPDA individual, tiempo hasta recuperación) requieren sistemas de tracking GPS o datos de proveedores como Second Spectrum, SkillCorner o StatsPerform, cuyos costes de licencia superan el alcance de un trabajo académico. Un jugador puede presentar métricas estadísticas similares a otro pero con perfiles físicos radicalmente diferentes: uno basado en explosividad y duelos, otro en posicionamiento e inteligencia táctica._

**Datos de video y análisis cualitativo.** _El scouting profesional complementa las estadísticas con análisis de video que evalúa aspectos no cuantificables: calidad de los movimientos sin balón, timing de desmarques, comunicación con compañeros, comportamiento en situaciones de presión, lenguaje corporal tras errores, y posicionamiento defensivo en fases sin posesión. Estos elementos, determinantes para predecir adaptación a un nuevo contexto táctico, requieren horas de visualización por jugador y criterio experto que escapa al alcance metodológico de este trabajo._

**Datos médicos e historial de lesiones.** _La propensión a lesiones, historial de problemas musculares, recuperación de intervenciones quirúrgicas, y estado físico actual son factores decisivos en cualquier operación de fichaje. Un jugador con métricas excelentes pero tres roturas de ligamento cruzado representa un riesgo que ningún análisis estadístico de rendimiento puede capturar. Los clubes acceden a informes médicos confidenciales durante las negociaciones; las fuentes públicas solo registran lesiones reportadas en prensa, con información incompleta y frecuentemente inexacta._

**Factores psicológicos y de personalidad.** _La mentalidad competitiva, capacidad de liderazgo, comportamiento en vestuario, adaptabilidad a nuevos entornos culturales y lingüísticos, resistencia a la presión mediática, y estabilidad emocional son variables que los clubes evalúan mediante entrevistas, informes de entorno, y consultas con representantes y excompañeros. Ninguna métrica estadística captura si un jugador rendirá bajo la presión de 80.000 espectadores hostiles o si su personalidad encajará con la dinámica de grupo existente._

**Jugadores de cantera y categorías inferiores.** _Los jugadores procedentes de canteras o categorías inferiores no disponen de datos estadísticos en fuentes públicas gratuitas. FBref y Understat solo cubren primeras divisiones de las Big 5 más ligas secundarias seleccionadas (Eredivisie, Liga Portuguesa, etc.). Esto implica que fichajes como Carlos Baleba (cantera Lille) o canteranos promovidos no pueden evaluarse con datos previos a su debut profesional en primera división. En contexto real, los departamentos de scouting emplean datos propietarios de categorías inferiores, informes de ojeadores, y métricas internas que este análisis no puede replicar._

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

**Sesgo temporal.** _La forma actual de un jugador en el momento exacto del fichaje (pretemporada, primeros partidos de temporada) puede diferir significativamente de sus métricas de temporada anterior. Un jugador que terminó lesionado la temporada X-1 pero llegó recuperado a pretemporada presenta métricas que subestiman su estado real. Este desfase temporal es inherente al uso de datos históricos._

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

**Nota sobre período de análisis:** El período principal del estudio abarca 2022-2026. Sin embargo, algunas cadenas de sustitución incluyen operaciones anteriores (Gabriel 2017, Soumaré 2017, Osimhen 2019) para documentar la secuencia completa y demostrar la continuidad del modelo de negocio. El análisis algorítmico (PCA + similitud coseno) se aplica únicamente a sustituciones donde la disponibilidad de datos FBref lo permite, típicamente desde temporada 2019/20 en adelante para Big 5.

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

El análisis algorítmico evalúa 26 sustituciones ejecutadas por los tres clubes entre 2019 y 2025, aplicando PCA + similitud coseno para determinar si los fichajes presentan proximidad estadística con los jugadores vendidos.

**Resultados agregados:**

| Clasificación | Casos | Porcentaje | Criterio |
|---------------|-------|------------|----------|
| VALIDADO | 12 | 46% | Rank 1-10 en pool filtrado |
| PARCIAL | 4 | 15% | Rank 11-30 en pool filtrado |
| NO VALIDADO | 10 | 38% | Rank >30 en pool filtrado |

**Distribución por equipo:**

| Equipo | VAL | PAR | NO VAL | Plusvalía |
|--------|-----|-----|--------|-----------|
| Villarreal CF | 6 | 3 | 3 | +137M€ |
| Eintracht Frankfurt | 4 | 1 | 1 | +155M€ |
| LOSC Lille | 2 | 0 | 6 | +193M€ |

**Rango de similitud observado:**

| Métrica | Caso | Score |
|---------|------|-------|
| Máximo | Ndicka → Pacho | 0.845 |
| Mínimo VALIDADO | Kolo Muani → Ekitike | 0.006 |
| Mínimo PARCIAL | Sørloth → Barry | 0.035 |
| Mínimo (negativo) | Osimhen → David | -0.440 |

**Distribución por posición:**

| Posición | Casos | VALIDADO | Tasa |
|----------|-------|----------|------|
| Delantero Centro (ST) | 11 | 6 | 55% |
| Defensa Central (CB) | 7 | 3 | 43% |
| Lateral (LB/RB) | 5 | 3 | 60% |
| Mediocampista (CM/CDM) | 2 | 0 | 0% |
| Portero (GK) | 1 | 0 | 0% |

Las posiciones ofensivas y de banda presentan tasas de validación superiores, mientras que mediocampistas y porteros muestran mayor divergencia entre perfiles vendidos y fichados. Esto sugiere que las métricas disponibles capturan mejor los roles de finalización y progresión que los de organización y distribución.

La interpretación de estos resultados y la comparación entre modelos operativos se desarrolla en la sección 4.5.

### 4.2. Villarreal CF
4.2.1. Delantero Centro
Nicolas Jackson → Alexander Sørloth (22/23)
Alexander Sørloth aparece en posición #4 del pool filtrado (≤15M€, ≤26 años) con similitud de 0.137, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó un finalizador puro con perfil convergente pese al score moderado.
El radar revela similitud estructural clara en la dimensión fundamental: ambos delanteros comparten el perfil de nueves de área con métricas casi idénticas en xG (1.5 vs 1.6), volumen de disparo (7.8 ambos) y calidad de ocasiones (npxG/shot P95+). La convergencia es evidente: dos finalizadores puros con baja contribución creativa que viven de rematar ocasiones en zona de peligro.
La divergencia está en Goals-xG, y es lo que explica que la similitud sea moderada en lugar de alta. Jackson acumuló +4.2 (P96) en 22/23, un sobrerendimiento brutal que no es sostenible a largo plazo, mientras Sørloth marcó -0.7 (P35), claramente por debajo de lo esperado esa temporada en la Real Sociedad. El Villarreal apostó por que la divergencia era temporal, no estructural, y acertó: Sørloth produjo 0.83 xG/90 en 23/24, marcó 22 goles en liga y fue vendido al Atlético por 32M€. La operación generó +22M€ de plusvalía (10M€ fichaje → 32M€ venta).
 



Alexander Sørloth → Thierno Barry (23/24)
Thierno Barry aparece en posición #10 del pool filtrado (≤15M€, ≤24 años) con similitud de apenas 0.035, clasificándose como PARCIAL (por score, no por posición). El algoritmo detecta divergencia significativa, pero el resultado está fuertemente contaminado por un problema de calidad de datos.
El radar sugiere perfiles radicalmente diferentes: Sørloth domina en múltiples dimensiones ofensivas mientras Barry presenta métricas más limitadas. Sin embargo, el sesgo crítico es que Barry jugaba en la liga suiza, donde FBref ofrece cobertura estadística significativamente inferior a las Big 5. Crucialmente, la Swiss Super League no dispone de datos de toques, lo que obliga al algoritmo a normalizar las métricas por 90 minutos en lugar de per 100 touches. Esto penaliza artificialmente la similitud calculada.
El resultado PARCIAL refleja más las limitaciones de los datos disponibles que una evaluación robusta del perfil real de Barry. En contexto profesional, el Villarreal habría empleado proveedores premium (Wyscout, InStat) con cobertura completa de la Swiss League para validar el fichaje antes de invertir 20M€. La operación generó +10M€ de plusvalía (20M€ fichaje → 30M€ venta a Everton).
 




Thierno Barry → Tani Oluwaseyi (24/25)
Tani Oluwaseyi aparece en posición #3 del pool filtrado (≤20M€, ≤24 años) con similitud de 0.274, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó un finalizador con perfil convergente desde la MLS.
El radar revela convergencia fundamental entre ambos delanteros: finalizadores de área con métricas de generación de ocasiones en percentiles superiores (xG P95 vs P88, touches in box P96 vs P89). Ambos operan como nueves puros con baja contribución creativa (SCA P15 vs P27) y eficiencia de ocasiones equivalente (npxG per shot 0.17 vs 0.16).
La divergencia está en Goals-xG, que explica la similitud moderada. Barry acumuló -1.5 (P19) en 24/25 con el Villarreal, un subrendimiento severo que contrasta con el +0.40 (P60) de Oluwaseyi en la MLS. El fichaje responde a lógica de corrección estadística: reemplazar un delantero que generaba alto xG pero convertía mal con uno que mantiene perfil de finalización similar a precio inferior (8M€ desde Minnesota). El algoritmo valida correctamente un perfil funcionalmente equivalente, asumiendo que la métrica Goals-xG de Barry era corregible mediante cambio de entorno.
 



4.2.2. Portero
Filip Jørgensen → Luiz Júnior (23/24)
Luiz Júnior aparece en posición #15 del pool filtrado (≤15M€, ≤26 años) con similitud de 0.193, clasificándose como PARCIAL. El algoritmo detecta divergencias estructurales concentradas en la métrica más crítica para porteros: PSxG +/-.
El radar revela divergencia abismal en rendimiento. Jørgensen acumuló -2.2 (P36) en 23/24, encajando 2.2 goles más de lo esperado según la dificultad de los disparos recibidos, un rendimiento claramente por debajo del estándar. Luiz Júnior presentaba +10 (P98) en la liga portuguesa, evitando 10 goles más de lo esperado, un sobrerendimiento extremo. Esta divergencia de 12.2 goles en la métrica fundamental de calidad de parada invalida la similitud pese a convergencias en otras dimensiones como save % (72 vs 75), juego de pies (pass accuracy 80 vs 75) o posicionamiento como líbero (sweeper actions/distance similares).
El resultado PARCIAL confirma que el Villarreal no buscó un perfil estadísticamente equivalente sino un upgrade deliberado, fichando un portero con métricas de rendimiento superiores desde liga secundaria. El algoritmo correctamente rechaza la validación porque la distancia en PSxG +/- supera lo explicable por variabilidad temporal.
 


4.2.3. Defensa Central
Pau Torres → Logan Costa (22/23)
Logan Costa aparece en posición #2 del pool filtrado (≤15M€, ≤24 años) con similitud de 0.654, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó un central similar constructor con perfil convergente desde la liga francesa.
El radar revela convergencia clara en la dimensión fundamental: capacidad de construcción desde atrás. Costa replica métricas nucleares de Pau Torres: pass accuracy similar (83% vs 85%), progressive passes en percentiles altos (7.0 P80 vs 7.9 P91), y final third passes comparables (6.3 P82 vs 7.5 P95). Ambos centrales modernos que priorizan juego de pies sobre intensidad defensiva, capaces de romper líneas con pase y progresar balón controlado.
La divergencia está en la fase defensiva, pero refuerza la lógica del fichaje. Costa presenta perfil más físico: mayor volumen de duelos aéreos ganados (3.1 vs 2.4), mejor aerial success % (63 P81 vs 55 P49), y el doble de intercepciones (1.1 P26 vs 0.52 P2). Torres dominaba la construcción pero era vulnerable en duelos directos. Costa mantiene las capacidades de salida de balón añadiendo presencia física que complementa mejor a Albiol/Foyth. El algoritmo valida correctamente un reemplazo que preserva la función principal mientras corrige debilidades secundarias.
 



Logan Costa → Renato Veiga (24/25)
Renato Veiga aparece en posición #66 del pool filtrado (≤25M€, ≤26 años) con similitud negativa de -0.078, clasificándose como NO VALIDADO. El algoritmo rechaza correctamente la similitud porque los perfiles son arquetipos opuestos, pero esto no representa un error de fichaje sino un ajuste táctico deliberado.
El radar muestra perfiles complementarios, no equivalentes. Costa es un central constructor con métricas progresivas superiores: final third passes (6.0 P77 vs 4.8 P53), progressive passes (6.5 P72 vs 5.5 P51), y tackle success % élite (82% P97). Veiga es un central defensivo puro con dominio físico brutal: aerial success % (71% P94 vs 55% P53), clearances (11 P93 vs 6.4 P61), interceptions (2.6 P90 vs 1.2 P26), y shot blocks (1.8 P94 vs 0.78 P54).
El contexto explica el resultado NO VALIDADO: tras la lesión de Costa, el Villarreal no buscó un reemplazo like-for-like sino reconfigurar completamente la pareja de centrales. Foyth (lateral convertido a central diestro) + Veiga (zurdo físico) forma una dupla complementaria donde Foyth asume las funciones progresivas que Costa ejecutaba mientras Veiga aporta presencia física. El algoritmo valida que NO existe similitud estadística, confirmando que el fichaje responde a cambio táctico y no a sustitución directa.
 




Juan Foyth → Santiago Mouriño (24/25)
Santiago Mouriño aparece en posición #3 del pool filtrado (≤20M€, ≤26 años) con similitud de 0.460, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó un lateral derecho estadísticamente similar a Foyth en su última temporada en esa demarcación.
El radar revela convergencia fundamental en el balance híbrido entre construcción y defensa. Mouriño replica métricas clave de Foyth: aerial duels won comparables (4.0 P86 vs 3.4 P79), shot blocks similares (1.3 P80 vs 1.4 P85), y clearances en percentiles altos (12 P96 vs 10 P89). Ambos laterales con presencia física que aportan solidez defensiva sin renunciar completamente a progresión.
La divergencia está en pass accuracy (78% P25 vs 87% P71) e interceptions (3.0 P95 vs 1.6 P50), reflejando que Mouriño es más defensivo. Sin embargo, esta diferencia no invalida la similitud estructural: el algoritmo detecta correctamente que ambos son laterales completos con énfasis defensivo, donde Foyth priorizaba más la construcción y Mouriño el trabajo sin balón, pero mantienen el perfil funcional equivalente.
 




4.2.4. Lateral Izquierdo
Pervis Estupiñán → Johan Mojica (21/22)
Johan Mojica aparece en posición #9 del pool filtrado (≤15M€, ≤28 años) con similitud de 0.114, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó un lateral ofensivo con perfil convergente.
El radar revela similitud estructural clara en la dimensión ofensiva. Mojica replicaba métricas nucleares de Estupiñán: progressive passes superior (5.5 P53 vs 5.9 P61), box passes prácticamente idénticos (2.3 P91 vs 2.1 P88), expected assists equivalentes (0.20 P85 vs 0.24 P90), crosses en percentiles altos (5.8 P84 vs 7.2 P91), y touches final third ligeramente inferior (33 P90 vs 27 P78). Ambos laterales izquierdos con perfil ofensivo marcado, capaces de progresar por banda y generar ocasiones.
La divergencia está en tackles+interceptions donde Mojica sale perjudicado (4.8 P49 vs 3.3 P15), pero esto reforzaba la lógica del fichaje: buscar replicar la parte ofensiva por el sistema del Villarreal. El algoritmo validó un reemplazo estadísticamente fundamentado que preservaba las capacidades ofensivas perdiendo algo de trabajo defensivo. El fracaso posterior (cedido, vendido con pérdida) no invalida la similitud del perfil sino que refleja factores no cuantificables: edad (29→32 años), adaptación, competencia con Pedraza, o declive físico acelerado.
 



Johan Mojica → Sergi Cardona (23/24)
Sergi Cardona aparece en posición #20 del pool filtrado (≤10M€, ≤26 años) con similitud de 0.024, clasificándose como NO VALIDADO. El algoritmo rechaza correctamente la similitud porque los perfiles son arquetipos opuestos, confirmando que el Villarreal corrigió estratégicamente el fichaje fallido de Mojica.
El radar muestra divergencia radical. Mojica era un lateral ultraofensivo: crosses 8.1 (P93), box passes 2.5 (P94), touches final third 34 (P90), progressive carries 4.0 (P84). Cardona presenta perfil defensivo: tackles+interceptions 5.3 (P69) vs 3.6 (P30), pass accuracy 80% vs 72%, pero métricas ofensivas limitadas (crosses 3.4 P67, box passes 1.5 P71, touches final third 22 P62).
El contexto explica el resultado NO VALIDADO: tras el fracaso de Mojica, el Villarreal cambió completamente la filosofía del puesto. Fichó a Cardona como agente libre (valor mercado 6M€→10M€) para formar rotación complementaria con Alfonso Pedraza. El algoritmo valida correctamente que NO existe similitud con Mojica, confirmando ajuste táctico deliberado en lugar de reemplazo directo.
 




Alfonso Pedraza → Sergi Cardona (24/25)
Sergi Cardona aparece en posición #41 del pool filtrado (≤15M€, ≤26 años) con similitud negativa de -0.443, clasificándose como NO VALIDADO. El algoritmo confirma que estos NO son perfiles equivalentes sino complementarios en rotación táctica.
El radar demuestra divergencia radical. Pedraza es un wing-back ultraofensivo: progressive carries 7.6 (P98), crosses 7.9 (P93), box passes 3.3 (P98), expected assists 0.49 (P98), touches final third 30 (P82). Cardona presenta perfil equilibrado: tackles+interceptions 5.3 (P69), pass accuracy 80%, progressive passes 6.2 (P63), pero métricas ofensivas muy inferiores (crosses 3.4 P67, box passes 1.5 P71, expected assists 0.11 P62).
La similitud negativa valida precisamente la estrategia del Villarreal. El club fichó a Cardona como agente libre NO para reemplazar a Pedraza sino para formar dupla complementaria. Pedraza ataca constantemente como tercer extremo, Cardona entra cuando se necesita solidez defensiva o rotación. El resultado NO VALIDADO confirma diseño táctico intencional: dos laterales con roles diferenciados, no sustitución directa.
 






4.2.5. Mediapunta / Extremo
Álex Baena → Alberto Moleiro (24/25)
Alberto Moleiro aparece en posición #16 del pool filtrado (≤30M€, ≤26 años) con similitud de 0.075, clasificándose como PARCIAL. El algoritmo detecta convergencia parcial pero identifica divergencias significativas que explican la similitud moderada-baja.
El radar revela perfiles funcionalmente diferentes pese a compartir demarcación. Baena era un playmaker puro: expected assists 0.75 (P98), shot creating actions 5.9 (P98), crosses 13 (P96). Producción creativa élite en percentiles 95+. Moleiro presenta perfil más desequilibrante: dribbles 4.5 (P93) vs 1.3 (P45), touches in box 7.2 (P74) vs 5.7 (P65), pero creación limitada (xA 0.23 P54, SCA 3.5 P75, crosses 2.3 P40). La similitud fundamental está en el rol: ambos mediapuntas/extremos creativos con capacidad de desequilibrio, compartiendo xG comparable (0.45 P76 vs 0.40 P70).
El fichaje responde a oportunidad de mercado más que a reemplazo equivalente. Moleiro costó 16M€ aprovechando el descenso de Las Palmas (valor mercado 25M€→30M€), fichaje de potencial donde el Villarreal apostó por desarrollar un talento joven complementario a Gerard Moreno, no por replicar el perfil específico de Baena. La similitud PARCIAL refleja correctamente: misma demarcación, divergencia de estilo.
 




EXTRA: Gerard Moreno → Georges Mikautadze (24/25)
Georges Mikautadze aparece en posición #1 del pool filtrado (≤25M€, ≤26 años) con similitud de 0.472, clasificándose como VALIDADO. El algoritmo confirma que el Villarreal identificó anticipadamente un reemplazo generacional con perfil estructural convergente.
El radar revela similitud fundamental en la versatilidad ofensiva. Ambos delanteros completos capaces de finalizar y crear: Mikautadze presenta xG 1.6 (P89), goals 1.7 (P91), xA 0.66 (P94); Gerard mantiene xA 0.89 (P98), SCA 4.9 (P93). Los dos operan como referentes que generan ocasiones propias y para compañeros, no son nueves puros de área.
La divergencia refleja la transición generacional. Gerard acumula Goals-xG -1.2 (P23) y npxG/Shot 0.08 (P24), señales de declive físico que afectan conversión pese a mantener inteligencia táctica. Mikautadze está en pico: Goals-xG +0.70 (P68), touches in box 18 (P92) vs 11 (P63), shots 8.0 vs 5.7. El algoritmo valida correctamente un fichaje de sucesión: Mikautadze aporta más finalización directa preservando la capacidad creativa que define el rol de Gerard en el sistema del Villarreal.
 
Nota: Este no es un caso de cadena de sustitución puro de venta y beneficio, pero muestra cómo en un jugador clave como Gerard, ya más que amortizado, buscar un reemplazo similar es fundamental. Algo a destacar es cómo muchas veces el jugador elegido es de la propia liga española, lo que a nivel de adaptabilidad estará más "validado".

4.3. Eintracht Frankfurt
4.3.1. Delantero Centro
Randal Kolo Muani → Omar Marmoush (22/23)
Omar Marmoush aparece en posición #10 del pool filtrado (≤20M€, ≤25 años) con similitud de 0.173, clasificándose como VALIDADO. El algoritmo confirma que el Frankfurt identificó un perfil funcionalmente equivalente a coste cero, replicando su modelo de negocio paradigmático.
El radar demuestra que Marmoush es un "mini Kolo Muani". Mantiene la esencia del perfil: delantero móvil con capacidad de regate (dribbles 5.1 P87 vs 6.7 P95), finalización desde movimiento (xG 0.82 P64 vs 1.2 P83), y presencia en área (touches in box 12 P68 vs 18 P95). La diferencia está en el volumen: Marmoush opera a escala inferior pero preserva las proporciones del arquetipo. La divergencia crítica es xA (0.16 P10 vs 0.61 P93), donde Kolo Muani aportaba creación élite que Marmoush no replica.
Dos factores validan la operación más allá del score algorítmico. Primero, fichaje como agente libre desde Wolfsburgo, ROI infinito que replica el modelo Kolo Muani (gratis→95M€). Segundo, procedencia Bundesliga, eliminando riesgo de adaptación y acelerando integración táctica. El algoritmo valida correctamente un reemplazo data-driven donde el coste cero y la familiaridad contextual compensan la similitud moderada. La operación generó +75M€ de plusvalía (gratis → 75M€ venta a Man City).
 


Randal Kolo Muani → Hugo Ekitike (22/23)
Hugo Ekitike aparece en posición #8 del pool filtrado (≤25M€, ≤23 años) con similitud de 0.006, clasificándose como PARCIAL (por score, no por posición). El algoritmo rechaza correctamente la similitud porque el Frankfurt ejecutó una estrategia de desarrollo a largo plazo, no un reemplazo inmediato.
El radar confirma divergencias radicales. Ekitike presenta perfil significativamente inferior en todas las dimensiones: xG 0.78 (P62) vs 1.2 (P83), goals 0.63 vs 1.4, touches in box 13 (P76) vs 18 (P95), dribbles 3.4 (P64) vs 6.7 (P95), xA 0.34 (P51) vs 0.61 (P93). Crucialmente, Goals-xG de -0.7 (P35) indica subrendimiento severo que contrasta con el +1.8 (P83) de Kolo Muani.
El contexto explica el resultado PARCIAL: el Frankfurt fichó a Ekitike (20 años) primero cedido del PSG para evaluar su potencial sin compromiso. La cesión permitía desarrollo sin riesgo financiero. El algoritmo con filtros de edad restrictivos valida que Ekitike era apuesta de potencial, no sustitución data-driven.
 






Omar Marmoush → Elye Wahi (23/24)
Elye Wahi aparece en posición #10 del pool filtrado (≤40M€, ≤24 años) con similitud de 0.244, clasificándose como VALIDADO. El algoritmo identifica correctamente la convergencia estructural pero detecta la divergencia crítica que explica la similitud moderada.
El radar confirma que Wahi es estadísticamente superior en generación: xG 2.4 (P97) vs 1.2 (P80), shots 12 (P96) vs 8.2 (P81), touches in box 23 (P97) vs 16 (P85), npxG per shot 0.18 (P91) vs 0.13 (P66). Números de élite en todas las dimensiones ofensivas. Sin embargo, la métrica Goals-xG revela el problema: -2.5 (P9), un underperformance brutal. Wahi generó 2.4 xG pero solo marcó 1.9 goles, debería haber marcado ~4.4 goles.
Esta divergencia explica perfectamente la similitud moderada. El Frankfurt fichó (primero cedido del Marsella, luego comprado 26M€) un delantero con capacidad de generación de ocasiones superior a Marmoush pero con conversión deficiente. La apuesta era que el underperformance de Wahi era temporal y corregible en mejor contexto. El algoritmo valida un reemplazo donde el perfil funcional converge (delantero móvil, finalizador) pero la eficiencia diverge radicalmente, reflejando fichaje de alto riesgo-alta recompensa.
 





Hugo Ekitike → Jonathan Burkardt (24/25)
Jonathan Burkardt aparece en posición #9 del pool filtrado (≤40M€, ≤26 años) con similitud de 0.267, clasificándose como VALIDADO. El algoritmo detecta convergencia en la dimensión goleadora fundamental pero identifica el trade-off estratégico que ejecutó el Frankfurt.
El radar revela perfiles complementarios más que idénticos. Ekitike generaba ocasiones de élite: xG 2.0 (P95), xA 0.65 (P94), dribbles 4.9 (P91), SCA 3.5 (P71). Delantero creativo, móvil, asociativo. Pero convertía fatal: Goals-xG -6.6 (P1), el peor underperformance del dataset. Generaba 2.0 xG y solo marcaba 1.4 goles.
Burkardt invierte la ecuación. Genera menos creatividad: xA 0.39 (P62), dribbles 2.0 (P39), SCA 2.3 (P30). Pero convierte brutal: Goals-xG +3.2 (P92), marcó 2.3 goles con 1.9 xG. El Frankfurt sacrificó deliberadamente movilidad y asociación por eficiencia de conversión pura, manteniendo el xG similar (~2.0 vs 1.9) pero fichando un finalizador clínico en lugar de un creador que no remataba. El algoritmo valida un reemplazo donde el perfil goleador converge pero el estilo de juego diverge intencionalmente.
 





4.3.2. Defensa Central
Evan N'Dicka → Willian Pacho (22/23)
Willian Pacho aparece en posición #1 del pool filtrado (≤25M€, ≤26 años) con similitud de 0.845, clasificándose como VALIDADO con el score más alto del análisis completo. El algoritmo confirma que el Frankfurt identificó un central zurdo con convergencia estructural casi perfecta.
El radar revela similitud brutal en la dimensión constructor: pass accuracy prácticamente idéntico (86% P79 vs 85% P74), progressive passes convergentes (4.4 P20 vs 4.5 P23), aerial success % similar (61% vs 59%). Ambos centrales zurdos modernos con capacidad de salida de balón, perfil que define el estilo Frankfurt en defensa.
La divergencia está en el matiz físico-defensivo. N'Dicka dominaba más el juego aéreo (aerial duels won 3.6 P77, clearances 6.9 P82), mientras Pacho compensa con mayor actividad anticipatoria (interceptions 2.1 P60 vs 1.4 P29, tackles+interceptions 4.4 P41 vs 2.6 P7). Perfiles complementarios dentro del mismo arquetipo fundamental.
El resultado valida completamente el modelo Frankfurt: ficharon a Pacho (20 años, 11M€ desde liga belga) y lo vendieron al PSG por 40M€ tras una temporada. La operación generó +29M€ de plusvalía, replicando exactamente el patrón ejecutado con N'Dicka. El score 0.845 confirma precisión analítica máxima.
 




Willian Pacho → Arthur Theate (23/24)
Arthur Theate aparece en posición #67 del pool filtrado (≤25M€, ≤26 años) con similitud de 0.017, clasificándose como NO VALIDADO. El algoritmo rechaza correctamente la similitud porque el Frankfurt ejecutó un cambio táctico estructural, no una sustitución directa.
El contexto crítico es el cambio de sistema defensivo. En defensa de 3, Pacho operaba como central zurdo corrector con función física (clearances 5.7 P70, aerial duels), perfil especializado para ese rol específico. El Frankfurt pasó a defensa de 4, donde el central zurdo requiere completitud: Theate presenta progressive passes 8.0 (P92) vs 5.6 (P47), final third passes 6.9 (P89) vs 5.1 (P63), tackle success 64% (P74) vs 58% (P52), shot blocks 1.2 (P77) vs 0.83 (P56).
El radar muestra que Theate no es "similar pero mejor" sino funcionalmente diferente: constructor de élite (P89-92 en progresión) donde Pacho era corrector físico. Crucialmente, Theate puede operar también como falso lateral izquierdo en esquema 4-3-3/4-2-3-1, aportando versatilidad que Pacho no tenía. El resultado NO VALIDADO confirma cambio de filosofía táctica completo, no error algorítmico.
 




4.4. LOSC Lille
El caso Lille representa un contraste metodológico fundamental con Villarreal y Frankfurt. Mientras estos clubes buscan reemplazos estadísticamente similares, Lille opera bajo un modelo de desarrollo de talento joven donde la similitud de perfil es secundaria respecto al potencial de crecimiento. Los resultados algorítmicos, mayoritariamente NO VALIDADOS, no representan fracasos de identificación sino confirmación de una filosofía diferente.
4.4.1. Defensa Central
Gabriel Magalhães → Sven Botman (19/20)
Sven Botman aparece en posición #8 del pool filtrado (≤15M€, ≤24 años) con similitud de 0.439, clasificándose como VALIDADO. El algoritmo confirma que Lille identificó correctamente un central zurdo constructor con perfil convergente desde la Eredivisie.
El radar revela similitud estructural clara en la dimensión más crítica: capacidad de construcción desde atrás. Botman replica métricas nucleares de Gabriel: pass accuracy convergente (83% P63 vs 81% P59), progressive passes similares (5.7 P51 vs 6.1 P63), y aerial success % comparable (73% P95 vs 64% P82). Ambos centrales zurdos modernos que priorizan salida de balón sobre intensidad defensiva pura.
La divergencia está en el perfil físico-defensivo. Gabriel presentaba más clearances (4.9 P55 vs 6.8 P76) y shot blocks (1.0 P71 vs 0.66 P49), mientras Botman compensaba con mejor tackle success % (77% P67 vs 68% P81). El algoritmo valida correctamente un reemplazo donde el perfil constructor converge preservando la función principal del puesto en el sistema Lille. La operación generó +29M€ de plusvalía (8M€ fichaje → 37M€ venta a Newcastle).
 
Sven Botman → Bafodé Diakité (21/22 → 19/20 exógeno)
Bafodé Diakité (versión 19/20 en Toulouse, 3 años antes del fichaje) aparece en posición #16 del pool filtrado con similitud de 0.091, clasificándose como NO VALIDADO.
Nota metodológica: Se emplea temporada 19/20 porque Toulouse militaba en Ligue 2 durante 20/21 y 21/22, donde FBref no dispone de cobertura de datos. Esta limitación temporal debe considerarse al interpretar el resultado. El algoritmo detecta divergencia significativa pero el contexto explica la lógica operativa.
El radar confirma perfiles diferenciados. Botman 21/22 era un constructor consolidado: pass accuracy 87% (P70), progressive passes 4.5 (P28), aerial success 67% (P81). Diakité 19/20 presentaba perfil más físico-defensivo: tackle success 53% (P40), clearances 9.1 (P70), pero métricas progresivas inferiores (pass accuracy 85% P77, progressive passes 5.2 P46).
El resultado PARCIAL refleja la estrategia Lille de identificación temprana. Ficharon a Diakité a los 21 años por 3M€ desde Toulouse, apostando por desarrollo durante 3 temporadas antes de venderlo por 35M€ al Bournemouth. El algoritmo correctamente rechaza la similitud inmediata porque Lille no buscaba un reemplazo estadístico sino un proyecto de desarrollo con potencial de apreciación. La plusvalía de +32M€ valida la estrategia pese al resultado algorítmico.
 



Bafodé Diakité → Nathan Ngoy (24/25)
Nathan Ngoy aparece en posición #57 del pool filtrado (≤10M€, ≤24 años) con similitud negativa de -0.396, clasificándose como NO VALIDADO. El algoritmo rechaza categóricamente la similitud, confirmando que Lille ejecuta nuevamente el mismo patrón de desarrollo.
El radar demuestra divergencia radical. Diakité 24/25 había evolucionado a constructor de élite: pass accuracy 93% (P87), progressive passes 3.6 (P11), aerial success 72% (P96). Ngoy desde la liga belga presenta perfil inferior en construcción: pass accuracy 81% (P44), aerial success 57% (P63). Sin embargo, Ngoy destaca abismalmente en métricas defensivas respecto a Diakité: tackles+interceptions, clearances, y progressive passes 6.8 (P75) vs 3.6 (P11). La similitud negativa indica perfiles estadísticamente opuestos, similar al patrón observado en Botman → Diakité: central constructor reemplazado por central más físico-defensivo con potencial de desarrollo.
El contexto valida la lógica: Ngoy fichado por 3.5M€ desde Standard Liège replica exactamente el modelo Diakité (fichaje joven desde liga secundaria a precio bajo). Lille apuesta por que Ngoy desarrollará capacidades similares en 2-3 temporadas. El resultado NO VALIDADO confirma que el algoritmo detecta correctamente la ausencia de similitud actual, mientras Lille opera bajo hipótesis de convergencia futura mediante desarrollo interno.
 



4.4.2. Mediocampista Defensivo
Boubakary Soumaré → Amadou Onana (20/21 → 21/22)
Nota metodológica: Este es un análisis post-hoc. Onana fichó por Lille en agosto 2021 procedente del Hamburgo (2ª Bundesliga), donde no existían datos FBref disponibles. El análisis compara Soumaré 20/21 (última temporada en Lille) con Onana 21/22 (primera temporada completa en Lille), evaluando retrospectivamente si el fichaje "cumplió" el patrón de divergencia de perfil con éxito deportivo y financiero.
Amadou Onana aparece en posición #36 del pool filtrado (≤25M€, ≤25 años) con similitud negativa de -0.325, clasificándose como NO VALIDADO. El algoritmo rechaza la similitud porque los perfiles son arquetipos funcionalmente opuestos.
El radar revela divergencia estructural clara. Soumaré era un pivote progresivo-técnico: progressive passes 10 (P91), pass accuracy 86% (P88), interceptions 2.3 (P69), pero tackle success % limitado (40% P65). Onana presenta perfil físico-defensivo radicalmente diferente: tackles+interceptions 9.7 (P97), recoveries 12 (P83), progressive carries 3.0 (P46), pero progressive passes muy inferior (7.3 P48).
El análisis post-hoc confirma el patrón "NO SIMILAR pero TOP": Onana, pese a no replicar estadísticamente a Soumaré, demostró ser fichaje élite. Tras la venta de Soumaré (20M€), Lille no buscó replicar su perfil técnico sino complementar el sistema con características diferentes. Onana aportaba presencia física y capacidad de recuperación que Soumaré no tenía. El resultado NO VALIDADO confirma que el algoritmo detecta correctamente perfiles diferentes, pero el éxito financiero demuestra que la divergencia fue deliberada y rentable.
 

Carlos Baleba → Nabil Bentaleb (22/23)
Nabil Bentaleb aparece en posición #35 del pool filtrado (≤20M€, ≤28 años) con similitud negativa de -0.085, clasificándose como NO VALIDADO. El algoritmo rechaza la similitud, confirmando que este fichaje representa un error de identificación más que un cambio táctico deliberado.
El análisis presenta una limitación crítica: Baleba acumuló solo 478 minutos en 22/23 (por debajo del umbral estándar de 1000), lo que reduce la representatividad estadística de su perfil. Sin embargo, el radar disponible revela divergencia estructural clara. Baleba presentaba perfil físico-dinámico: progressive carries 4.2 (P63), recoveries 9.9 (P43), fouls drawn 4.7 (P69), tackle success 64% (P95). Bentaleb desde Angers mostraba perfil técnico-estático radicalmente diferente: progressive passes 8.1 (P57), pass accuracy 81% (P48), pero progressive carries muy inferior (2.1 P30) y recoveries limitadas (10 P56).
La divergencia más significativa está en el dinamismo: Baleba era un box-to-box físico capaz de progresar con balón y recuperar; Bentaleb era un distribuidor posicional sin movilidad. El fichaje como agente libre (27 años, valor residual) no generó pérdida económica directa, pero Bentaleb no logró replicar la función de Baleba en el sistema y fue considerado fichaje fallido. El resultado NO VALIDADO confirma que el algoritmo habría detectado la incompatibilidad de perfiles, validando su utilidad como herramienta de filtrado previo.
 
Nota metodológica: El caso Baleba ilustra una limitación del análisis retrospectivo: jugadores con minutos insuficientes no pueden ser evaluados con la misma robustez estadística. En contexto profesional, el departamento de scouting habría empleado datos de categorías inferiores o métricas cualitativas complementarias para evaluar un jugador de cantera con participación limitada en primer equipo.
4.4.3. Delantero Centro
Victor Osimhen → Jonathan David (19/20)
Jonathan David aparece en posición #55 del pool filtrado (≤40M€, ≤24 años) con similitud negativa de -0.440, clasificándose como NO VALIDADO. El algoritmo rechaza categóricamente la similitud porque los perfiles representan arquetipos de delantero centro radicalmente diferentes.
El radar confirma la divergencia fundamental. Osimhen era un finalizador puro de élite: xG 2.3 (P98), goals 1.9 (P94), touches in box 21 (P98), shots 12 (P96). Perfil de nueve de área con presencia física brutal y finalización en volumen. David presentaba perfil técnico-asociativo completamente diferente: xG 1.1 (P76), goals 1.7 (P90), touches in box 13 (P78), pero xA 0.38 (P58) y dribbles 3.7 (P63) superiores.
La métrica crítica es Goals-xG: Osimhen acumuló -2.5 (P6), un underperformance severo que sugería que su producción goleadora era incluso inferior a lo esperado por la calidad de sus ocasiones. David presentaba +6.4 (P98), elite absoluta, indicando una mejor eficiencia de conversión. El algoritmo rechaza correctamente la similitud porque David no es un "mini Osimhen" sino un delantero funcionalmente diferente: más móvil, más asociativo, menos dependiente de ocasiones en área.
El fichaje por 27M€ desde Gent fue apuesta por perfil complementario, no reemplazo estadístico. Sin embargo, la mala gestión contractual (David sale libre en 2025, -27M€ de pérdida) convierte esta operación en el mayor fracaso financiero del caso Lille, contrastando con el éxito de Osimhen (+56.5M€).
 

Jonathan David → Hamza Igamane (24/25)
Hamza Igamane aparece en posición #24 del pool filtrado (≤15M€, ≤24 años) con similitud negativa de -0.405, clasificándose como NO VALIDADO. El resultado debe contextualizarse por la limitación crítica de datos: la Scottish Premiership dispone solo de 44 métricas en FBref (vs +145 Big 5), forzando el análisis a usar únicamente 20 métricas comunes (como en Sorloth vs Barry)
El radar con métricas reducidas muestra convergencia parcial en la dimensión goleadora fundamental. David 24/25 presenta goals 0.56 (P90), G+A 0.74 (P90), shots 2.3 (P62). Igamane desde Rangers muestra goals 0.55 (P89), G+A 0.59 (P79), shots 4.1 (P90). Ambos delanteros con producción goleadora comparable en percentiles altos.
La divergencia está en la eficiencia: David presenta goals per shot 0.18 (P68), Igamane 0.13 (P61). David convierte mejor con menos volumen. Sin embargo, la similitud negativa refleja principalmente la incompatibilidad de datasets más que divergencia de perfiles reales. En contexto profesional, Lille habría empleado proveedores premium con cobertura completa de la Scottish Premiership.
El fichaje por 11.5M€ representa continuidad del modelo Lille: delantero joven (21 años) desde liga secundaria con potencial de desarrollo. El resultado algorítmico NO VALIDADO debe interpretarse con cautela por las limitaciones de datos, no como rechazo definitivo del perfil.
 



4.4.4. Lateral Izquierdo
EXTRA: Gabriel Gudmundsson → Romain Perraud (24/25)
Romain omain Perraud aparece en posición #4 del pool filtrado (≤15M€, ≤28 años) con similitud de 0.295, clasificándose como VALIDADO. El algoritmo confirma que Perraud representa un perfil convergente con Gudmundsson dentro de las restricciones económicas de Lille.
El radar revela convergencia sólida en las dimensiones fundamentales del lateral moderno. Ambos comparten producción ofensiva casi idéntica: crosses 4.7 (P78) vs 5.0 (P78), expected assists 0.11 (P64) vs 0.11 (P65), touches final third 32 (P86) vs 29 (P81). El trabajo defensivo también converge: tackles+interceptions 4.2 (P46) vs 4.1 (P42). La base funcional del rol es equivalente.
La divergencia está en la progresión y el regate. Gudmundsson destaca en progressive passes 7.2 (P84) vs 4.4 (P24), dribbles 1.6 (P89) vs 0.78 (P64), y progressive carries 5.6 (P94) vs 3.6 (P82). Gudmundsson es un lateral más vertical y desequilibrante; Perraud opera con perfil más conservador pero igualmente efectivo en la fase final. Tackle success % también diverge (63 P63 vs 45 P11), indicando que Gudmundsson gana más duelos individuales.
El ranking #10 en pool completo y #4/48 en pool filtrado demuestra que, aplicando restricciones realistas de mercado (≤15M€, ≤28 años), Perraud emerge como opción viable. Perraud (26 años, Betis, 5M€) aporta experiencia en Big 5 (Southampton, Niza, Betis) a coste reducido, compensando la menor verticalidad con madurez táctica.
Nota: Este es un caso de planificación de sucesión prospectiva, no de venta y beneficio inmediato. Demuestra cómo el algoritmo puede emplearse para identificar refuerzos o sucesores de jugadores titulares actuales, permitiendo al club anticiparse a futuras salidas o necesidades de rotación.
 

### 4.5. Síntesis Comparativa

Los resultados numéricos (sección 4.1) revelan tres modelos operativos diferenciados que explican las divergencias en tasas de validación:

**Villarreal: Equilibrio entre continuidad y adaptación**

El club alterna entre replicar perfiles exitosos (Jackson→Sørloth, Torres→Costa) y ejecutar ajustes tácticos deliberados donde la divergencia es intencional. Costa→Veiga ilustra este segundo caso: tras lesión de Costa, Foyth migra a central y Veiga cubre un rol diferente (central zurdo con salida de balón), no una sustitución directa. Mojica→Cardona representa corrección de error previo, no búsqueda de similitud. Los casos PARCIAL (Barry, Luiz Júnior, Moleiro) comparten denominador común: fichajes desde ligas con cobertura de datos limitada donde el algoritmo opera con información incompleta.

**Frankfurt: Precisión en ventanas cortas**

El modelo de desarrollo acelerado (12-18 meses de exposición antes de venta) requiere transiciones tácticas fluidas, lo que explica la búsqueda sistemática de perfiles convergentes. Ndicka→Pacho ejemplifica esta precisión: central zurdo constructor reemplazado por central zurdo constructor con métricas casi idénticas. Los dos casos NO VALIDADO (Ekitike, Theate) corresponden a cambios de sistema documentados post-salida del entrenador Glasner, no a fallos de identificación.

**Lille: Desarrollo sobre similitud**

La tasa baja refleja un modelo donde la similitud estadística inmediata es secundaria. Lille opera en mercados de captación temprana (Pro League belga, Ligue 2, ligas menores) donde: (a) los datos disponibles son limitados, (b) los jugadores están en fase formativa con perfiles incompletos, (c) la apuesta es por potencial de desarrollo, no por rendimiento actual comparable. Los casos validados (Gabriel→Botman, Gudmundsson→Perraud) demuestran que cuando opera en mercados con datos completos, Lille identifica perfiles con precisión equivalente a Frankfurt.

**Tipología de casos NO VALIDADO:**

El análisis identifica tres categorías distintas que invalidan la interpretación de "NO VALIDADO = error de scouting":

1. **Cambio táctico deliberado**: Costa→Veiga, Pacho→Theate, Mojica→Cardona. La divergencia es intencional porque el club busca un perfil diferente al vendido.

2. **Fichaje de desarrollo**: Botman→Diakité, Diakité→Ngoy, Kolo Muani→Ekitike. El club ficha potencial proyectado, no rendimiento actual comparable. El éxito se mide en plusvalía futura, no en similitud estadística.

3. **Limitación de datos**: Barry, Igamane, Onana (pre-fichaje). El algoritmo opera con información incompleta por cobertura insuficiente de ligas secundarias o ausencia de historial en primera división.

Solo **Baleba→Bentaleb** se identifica como potencial error de identificación: fichaje de perfil veterano que no replica las características del canterano vendido ni responde a cambio táctico documentado.

---

## 5. Conclusiones

Este trabajo ha analizado 26 sustituciones ejecutadas por Villarreal CF, Eintracht Frankfurt y LOSC Lille entre 2019 y 2025, aplicando un algoritmo de PCA + similitud coseno para determinar si los fichajes presentan proximidad estadística con los jugadores vendidos. Los tres clubes acumulan plusvalías combinadas de 485M€ manteniendo competitividad europea constante, validando la hipótesis de que existen estrategias data-driven replicables en el mercado de fichajes.

**Hallazgos principales:**

El análisis revela que el 61% de las sustituciones (VALIDADO + PARCIAL) presenta fundamentación estadística cuantificable, confirmando que estos clubes integran análisis de datos en sus procesos de decisión. Sin embargo, la distribución heterogénea entre equipos (Frankfurt 67%, Villarreal 50%, Lille 25%) demuestra que no existe un modelo único: cada club adapta el uso de datos a su estrategia operativa específica.

Frankfurt maximiza precisión estadística para facilitar transiciones tácticas en ventanas cortas de desarrollo. Villarreal equilibra continuidad de perfiles con ajustes tácticos deliberados donde la divergencia es intencional. Lille prioriza potencial de apreciación sobre similitud inmediata, operando en mercados de captación temprana donde los datos disponibles son estructuralmente limitados.

**El dato como apoyo, no como dogma:**

El hallazgo más relevante no es la tasa de validación agregada, sino la constatación de que los casos NO VALIDADO no implican fracaso. De las 10 sustituciones clasificadas como NO VALIDADO, solo una (Bentaleb) se identifica como potencial error de identificación. Las restantes responden a cambios tácticos deliberados, fichajes de desarrollo proyectado, o limitaciones inherentes de cobertura de datos en ligas secundarias.

Esta evidencia refuta la dicotomía simplista entre "scouting tradicional" y "análisis de datos". Los clubes exitosos no eligen entre ambos enfoques: los integran. El análisis cuantitativo identifica candidatos con perfiles convergentes, acota el universo de opciones, y fundamenta decisiones con criterio objetivo. El scouting tradicional evalúa factores no capturables (adaptación, mentalidad, contexto táctico específico), valida la viabilidad real de operaciones, y aporta juicio experto sobre potencial de desarrollo.

El algoritmo desarrollado en este trabajo no pretende reemplazar el criterio humano ni predecir éxito deportivo. Su valor reside en distinguir decisiones fundamentadas estadísticamente de decisiones puramente oportunistas, proporcionando una capa adicional de validación que complementa —nunca sustituye— el proceso integral de scouting profesional.

**Limitaciones y líneas futuras:**

El análisis opera con datos públicos gratuitos, excluyendo métricas físicas (tracking GPS), información contractual detallada, y cobertura completa de ligas secundarias. Estas limitaciones explican parcialmente los resultados NO VALIDADO en fichajes procedentes de Swiss Super League, Scottish Premiership o categorías inferiores. Futuras investigaciones podrían incorporar datos propietarios para evaluar si la tasa de validación aumenta con información más completa.

Adicionalmente, el enfoque retrospectivo (post-hoc) no permite evaluar la capacidad predictiva del algoritmo. Un estudio longitudinal que aplicara el método prospectivamente —identificando candidatos antes de que los clubes ejecuten fichajes— proporcionaría evidencia más robusta sobre su utilidad práctica en contexto real de scouting.

**Reflexión final:**

Este trabajo demuestra que Villarreal, Frankfurt y Lille han desarrollado la capacidad de convertir métricas de rendimiento en decisiones de mercado rentables, no porque los datos dicten sus fichajes, sino porque los datos informan un proceso de decisión donde el juicio experto sigue siendo insustituible.

*Dato sin contexto es ruido. Dato con contexto es información. Información con análisis es conocimiento. Conocimiento con capacidad de acción es insight.*

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

_Definiciones oficiales derivadas de StatsBomb vía FBref._

**Categoría A: Goles y Finalización**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| goals | per100t | Goles totales anotados |
| non_penalty_goals | per100t | Goles excluyendo penaltis |
| penalty_kicks_made | per100t | Penaltis convertidos |
| penalty_kicks_attempted | per100t | Penaltis lanzados |
| shots | per100t | Disparos totales (excluye penaltis) |
| shots_on_target | per100t | Disparos a puerta (habrían entrado sin portero/defensa) |
| shots_on_target_pct | % | Porcentaje de disparos a puerta |
| avg_shot_distance | abs | Distancia media de disparo en metros |
| shots_free_kicks | per100t | Disparos directos de falta |
| penalty_kicks_won | per100t | Penaltis provocados a favor |
| penalty_kicks_conceded | per100t | Penaltis cometidos |

**Categoría B: Pases**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| passes_completed | per100t | Pases completados |
| passes_attempted | per100t | Pases intentados |
| pass_completion_pct | % | Porcentaje de pases completados |
| passes_total_distance | per100t | Distancia total de pases en metros |
| passes_progressive_distance | per100t | Distancia progresiva de pases hacia portería rival |
| passes_completed_short | per100t | Pases cortos completados (<5 metros) |
| passes_attempted_short | per100t | Pases cortos intentados |
| passes_completed_medium | per100t | Pases medios completados (5-25 metros) |
| passes_attempted_medium | per100t | Pases medios intentados |
| passes_completed_long | per100t | Pases largos completados (>25 metros) |
| passes_attempted_long | per100t | Pases largos intentados |
| assists | per100t | Asistencias de gol |
| expected_assists | per100t | xA: probabilidad de que un pase termine en gol |
| key_passes | per100t | Pases que generan disparo (excluye asistencias) |
| passes_into_final_third | per100t | Pases completados al último tercio |
| passes_into_penalty_area | per100t | Pases completados al área rival |
| crosses_into_penalty_area | per100t | Centros completados al área rival |
| progressive_passes | per100t | Pases que avanzan ≥10 metros hacia portería o entran en área |

**Categoría C: Tipos de Pase (Pass Types)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| passes_live | per100t | Pases en juego vivo |
| passes_dead | per100t | Pases de balón parado |
| passes_from_free_kicks | per100t | Pases desde falta |
| through_balls | per100t | Pases entre líneas que rompen defensa |
| switches | per100t | Cambios de orientación (>40 metros) |
| crosses | per100t | Centros al área |
| throw_ins | per100t | Saques de banda |
| corner_kicks | per100t | Córners lanzados |
| corner_kicks_inswinging | per100t | Córners cerrados (hacia portería) |
| corner_kicks_outswinging | per100t | Córners abiertos (alejándose de portería) |
| corner_kicks_straight | per100t | Córners rectos |
| passes_offside | per100t | Pases que dejan en fuera de juego |
| passes_blocked | per100t | Pases bloqueados por rival |

**Categoría D: Creación de Ocasiones (SCA/GCA)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| SCA_SCA | per100t | Shot-Creating Actions: acciones que generan disparo (2 previas) |
| SCA_PassLive | per100t | SCA mediante pase en juego vivo |
| SCA_PassDead | per100t | SCA mediante balón parado |
| SCA_TO | per100t | SCA mediante regate exitoso |
| SCA_Sh | per100t | SCA mediante disparo (rebote/bloqueo) |
| SCA_Fld | per100t | SCA mediante falta recibida |
| SCA_Def | per100t | SCA mediante acción defensiva |
| GCA_GCA | per100t | Goal-Creating Actions: acciones que generan gol (2 previas) |
| GCA_PassLive | per100t | GCA mediante pase en juego vivo |
| GCA_PassDead | per100t | GCA mediante balón parado |
| GCA_TO | per100t | GCA mediante regate exitoso |
| GCA_Sh | per100t | GCA mediante disparo (rebote/bloqueo) |
| GCA_Fld | per100t | GCA mediante falta recibida |
| GCA_Def | per100t | GCA mediante acción defensiva |

**Categoría E: Acciones Defensivas**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| tackles | per100t | Entradas totales intentadas |
| tackles_won | per100t | Entradas ganadas (equipo recupera posesión) |
| tackles_def_3rd | per100t | Entradas en tercio defensivo |
| tackles_mid_3rd | per100t | Entradas en tercio medio |
| tackles_att_3rd | per100t | Entradas en tercio ofensivo |
| challenge_tackles | per100t | Entradas en duelos 1v1 |
| challenges | per100t | Duelos 1v1 intentados |
| challenge_tackles_pct | % | Porcentaje de duelos ganados |
| challenges_lost | per100t | Duelos perdidos (rival supera) |
| blocked_shots | per100t | Disparos bloqueados |
| blocked_passes | per100t | Pases bloqueados |
| interceptions | per100t | Intercepciones de pase rival |
| clearances | per100t | Despejes |
| errors | per100t | Errores que generan disparo rival |

**Categoría F: Posesión y Toques (Possession)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| touches | per100t | Toques totales de balón |
| touches_def_pen_area | per100t | Toques en área propia |
| touches_def_3rd | per100t | Toques en tercio defensivo |
| touches_mid_3rd | per100t | Toques en tercio medio |
| touches_att_3rd | per100t | Toques en tercio ofensivo |
| touches_att_pen_area | per100t | Toques en área rival |
| touches_live_ball | per100t | Toques en juego vivo (excluye balón parado) |
| take_ons_attempted | per100t | Regates intentados |
| take_ons_successful | per100t | Regates completados |
| take_ons_successful_pct | % | Porcentaje de regates exitosos |
| take_ons_tackled | per100t | Regates fallidos por entrada rival |
| carries | per100t | Conducciones (>1m con balón controlado) |
| carries_total_distance | per100t | Distancia total conducida en metros |
| carries_progressive_distance | per100t | Distancia progresiva conducida hacia portería |
| progressive_carries | per100t | Conducciones que avanzan ≥10 metros o entran en área |
| carries_into_final_third | per100t | Conducciones al último tercio |
| carries_into_penalty_area | per100t | Conducciones al área rival |
| miscontrols | per100t | Malos controles (pérdida de posesión) |
| dispossessed | per100t | Robos de balón sufridos |
| passes_received | per100t | Pases recibidos completados |
| progressive_passes_received | per100t | Pases progresivos recibidos |

**Categoría G: Duelos Aéreos**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| aerials_won | per100t | Duelos aéreos ganados |
| aerials_lost | per100t | Duelos aéreos perdidos |
| aerials_won_pct | % | Porcentaje de duelos aéreos ganados |

**Categoría H: Disciplina**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| fouls_committed | per100t | Faltas cometidas |
| fouls_drawn | per100t | Faltas recibidas |
| offsides | per100t | Fueras de juego |
| yellow_cards | per100t | Tarjetas amarillas |
| red_cards | per100t | Tarjetas rojas directas |
| second_yellow_cards | per100t | Segundas amarillas (expulsión) |

**Categoría I: Expected Goals (xG)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| expected_goals | per100t | xG: probabilidad acumulada de gol según calidad de disparos |
| non_penalty_expected_goals | per100t | npxG: xG excluyendo penaltis |
| non_penalty_expected_goals_plus_assists | abs | npxG + xA combinado |
| expected_goals_on_target | per100t | xGOT: xG solo de disparos a puerta |
| expected_goals_buildup | per100t | xG generado en fase de construcción |

**Categoría J: Porteros (excluidas del análisis outfield)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| saves | per100t | Paradas realizadas |
| save_pct | % | Porcentaje de paradas sobre disparos a puerta |
| clean_sheets | abs | Porterías a cero |
| goals_against_per_90 | per90 | Goles encajados por 90 minutos |
| psxg_minus_goals_allowed | per100t | PSxG-GA: goles evitados vs esperados (calidad de parada) |
| launched_passes_completed | per100t | Pases largos completados (>40 metros) |
| goal_kicks_launched | per100t | Saques de puerta largos |
| sweeper_defensive_actions_outside_pen_area | per100t | Acciones de líbero fuera del área |

**Categoría K: Métricas de Equipo (Team Success)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| on_goals_for | ctx | Goles a favor con jugador en campo |
| on_goals_against | ctx | Goles en contra con jugador en campo |
| plus_minus | ctx | Diferencial goles (GF - GA) con jugador en campo |
| on_xg_for | ctx | xG a favor con jugador en campo |
| on_xg_against | ctx | xG en contra con jugador en campo |
| xg_plus_minus | ctx | Diferencial xG con jugador en campo |

**Categoría L: Participación (Playing Time)**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| minutes_played | abs | Minutos totales jugados |
| games | abs | Partidos participados (titular o suplente) |
| games_started | abs | Partidos como titular |
| minutes_per_game | avg | Promedio de minutos por partido |
| games_subs | abs | Partidos entrando desde banquillo |
| unused_sub | abs | Convocatorias sin participar |
| points_per_game | ctx | Puntos promedio del equipo con jugador en campo |

**Categoría M: Resultados de Equipo**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| wins | abs | Victorias con jugador en campo |
| draws | abs | Empates con jugador en campo |
| losses | abs | Derrotas con jugador en campo |

**Categoría N: Eventos Específicos**
| Métrica | Norm. | Descripción |
|---------|-------|-------------|
| own_goals | per100t | Autogoles |
| goals_against | per100t | Goles encajados (contexto defensivo) |
| goals_from_penalties | per100t | Goles desde penalti |
| goals_from_free_kicks | per100t | Goles desde falta directa |
| goals_from_corners | per100t | Goles desde córner |

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

