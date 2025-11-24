# Eficiencia económica y deportiva en el mercado de fichajes: un análisis data-driven de las 5 grandes ligas europeas (2022–2026)

**Trabajo Fin de Master**

Máster en Big data aplicado al Scouting en Fútbol – Sevilla FC

Sport Data Campus

**Jaime Oriol Goicoechea**

---

## Índice de contenidos

1. [Introducción](#1-introducción)
   - 1.1. [Objetivos del Estudio](#11-objetivos-del-estudio)
   - 1.2. [Contexto Competitivo](#12-contexto-competitivo)
   - 1.3. [Justificación Metodológica](#13-justificación-metodológica)
2. [Análisis de Casos: Cadenas de Sustitución](#2-análisis-de-casos-cadenas-de-sustitución)
   - 2.1. [Villarreal CF: Modelo de Renovación Continua](#21-villarreal-cf-modelo-de-renovación-continua)
   - 2.2. [Eintracht Frankfurt: Modelo de Plusvalías Extremas](#22-eintracht-frankfurt-modelo-de-plusvalías-extremas)
   - 2.3. [LOSC Lille: Modelo de Desarrollo de Canteranos e Importación Selectiva](#23-losc-lille-modelo-de-desarrollo-de-canteranos-e-importación-selectiva)
   - 2.4. [Evolución de Valor de Plantilla y Rendimiento Competitivo](#24-evolución-de-valor-de-plantilla-y-rendimiento-competitivo)
     - 2.4.1. [Villarreal CF](#241-villarreal-cf)
     - 2.4.2. [LOSC Lille](#242-losc-lille)
     - 2.4.3. [Eintracht Frankfurt](#243-eintracht-frankfurt)
     - 2.4.4. [Comparativa Interliga](#244-comparativa-interliga)
3. [Metodología Analítica](#3-metodología-analítica)
   - 3.1. [Selección de Algoritmos](#31-selección-de-algoritmos)
     - 3.1.1. [UMAP + Gaussian Mixture Models (GMM)](#311-umap--gaussian-mixture-models-gmm)
     - 3.1.2. [Variational Autoencoder (VAE)](#312-variational-autoencoder-vae)
     - 3.1.3. [Estrategia de Triangulación Metodológica](#313-estrategia-de-triangulación-metodológica)

---

## 1. Introducción

El mercado de fichajes en el fútbol europeo presenta dos modelos claramente diferenciados. Por un lado, los grandes clubes de la Premier League y la Serie A operan con déficits estructurales, priorizando el rendimiento inmediato sobre la sostenibilidad económica. Por otro, un grupo reducido de equipos en La Liga, Bundesliga y Ligue 1 ha desarrollado estrategias data-driven que generan beneficios sistemáticos sin sacrificar competitividad deportiva.

Este trabajo analiza tres casos paradigmáticos de eficiencia en el mercado: Villarreal CF, Eintracht Frankfurt y LOSC Lille. Durante el período 2022-2026, estos clubes han generado plusvalías superiores a los 137, 155 y 193 millones de euros respectivamente, manteniendo simultáneamente presencia constante en competiciones europeas y posiciones de media-alta tabla en sus ligas domésticas.

La hipótesis central sostiene que existe un patrón estadísticamente identificable en las decisiones de fichaje de estos equipos, fundamentado en análisis cuantitativo de perfiles de jugadores. A diferencia del modelo italiano —basado en volumen masivo de operaciones pequeñas— o del británico —sustentado en gasto neto elevado—, los casos seleccionados ejecutan cadenas de sustitución estratégicas: venden activos en momentos de máxima valoración y los reemplazan con perfiles estadísticamente similares adquiridos a fracciones del precio de venta.

### 1.1. Objetivos del Estudio

**Objetivo principal:** Demostrar mediante algoritmos de machine learning que las sustituciones exitosas de jugadores responden a patrones cuantificables en datos de rendimiento, validando la existencia de estrategias data-driven replicables.

**Objetivos específicos:**

1. Documentar las cadenas de sustitución históricas (2022-2026) de los tres equipos seleccionados
2. Analizar la evolución del valor de plantilla y rendimiento deportivo en el período estudiado
3. Implementar dos algoritmos complementarios (UMAP + GMM y VAE) para identificar similitudes entre jugadores vendidos y sus reemplazos
4. Validar mediante triangulación metodológica si las sustituciones ejecutadas se fundamentan en proximidad estadística objetiva
5. Identificar las variables más discriminantes en la determinación de sustitutos óptimos

### 1.2. Contexto Competitivo

El análisis preliminar de las cinco grandes ligas europeas revela diferencias estructurales significativas:

**Premier League:** Ecosistema de gasto neto negativo generalizado. 23 de 25 clubes analizados presentan balances deficitarios. Leicester City emerge como outlier estadístico, generando 105M€ mediante cesiones y agentes libres (la temporada pasada), estrategia que resultó en devaluación de plantilla y descenso competitivo.

**Serie A:** Modelo de alta rotación (166-189 altas/bajas por club) basado en acumulación de operaciones de bajo valor. Si bien genera beneficios para equipos, la eficiencia proviene de volumen transaccional más que de precisión analítica. Los clubes estudiados operan principalmente en mitad de tabla sin presencia europea regular.

**La Liga, Bundesliga, Ligue 1:** Villarreal, Frankfurt y Lille operan con 58-90 operaciones en el período, significativamente menos que la Serie A, pero con plusvalías unitarias superiores. Crucialmente, estos equipos mantienen competitividad europea constante, sugiriendo que la eficiencia no compromete el proyecto deportivo.

### 1.3. Justificación Metodológica

La validación de estrategias data-driven requiere demostrar que las decisiones de fichaje no son arbitrarias ni producto exclusivo de scouting cualitativo, sino que responden a proximidad mensurable en espacios de características. Los algoritmos de clustering no supervisado y deep learning permiten:

- **Objetividad:** Eliminan sesgos cognitivos humanos en la evaluación de similitud
- **Multidimensionalidad:** Procesan simultáneamente 220+ variables estadísticas
- **Replicabilidad:** Generan criterios reproducibles para identificar reemplazos óptimos
- **Validación cruzada:** La convergencia entre metodologías independientes establece robustez de hallazgos

Este enfoque dual (geométrico + neural) constituye el estándar actual en research de player similarity, superando aproximaciones univariadas o basadas únicamente en intuición experta.

---

## 2. Análisis de Casos: Cadenas de Sustitución

Los tres equipos seleccionados presentan modelos de negocio convergentes pero con matices tácticos distintivos. A continuación se documentan las principales cadenas de sustitución ejecutadas entre 2022 y 2026, estructuradas por posición y secuencia temporal.

### 2.1. Villarreal CF: Modelo de Renovación Continua

El Villarreal ha implementado una política de reinversión sistemática caracterizada por:

- Venta de activos canteranos en pico de valor (Pau Torres 33M€, Jackson 37M€, Baena 55M€)
- Reemplazo mediante combinación de fichajes de coste medio (15-25M€) y agentes libres estratégicos
- Mantenimiento de núcleo táctico estable (Parejo, Foyth, Gerard) que absorbe rotación posicional

#### Delantero Centro

**Nicolas Jackson** (cantera → vendido 37M€)

→ 23/24: **Alexander Sørloth** (fichado 20M€ → vendido 32M€) *Datos a analizar: temporada 22/23*

→ 24/25: **Thierno Barry** (fichado 20M€ → vendido 30M€) *Datos a analizar: temporada 23/24*

→ 25/26: **Tani Oluwaseyi** (fichado 8M€ → actualmente en plantilla) *Datos a analizar: temporada 24/25*

**Análisis:** Cadena de cuatro sustituciones en cuatro temporadas. Cada reemplazo genera plusvalía (12M€ + 10M€) con coste de entrada decreciente (20M→20M→8M), indicando refinamiento del proceso de scouting hacia targets de menor riesgo financiero.

#### Extremo/Segundo Delantero

**Ben Brereton Díaz** (agente libre → vendido 8,3M€)

→ 24/25: **Ayoze Pérez** (fichado 4M€) *Datos a analizar: temporada 23/24*

**Análisis:** Operación de máxima eficiencia. Entrada sin coste, venta por 8,3M€, reemplazo a mitad de precio. Perfil típico: jugador experimentado en decline de mercado pero con rendimiento estadístico preservado.

#### Extremos

**Samuel Chukwueze** (cantera → vendido 21M€)

→ 23/24: **Ilias Akhomach** (agente libre) *Datos a analizar: temporada 22/23*

→ 24/25: **Tajon Buchanan** (cedido + opción compra 9M€, ejecutada 25/26) *Datos a analizar: temporada 23/24*

**Yeremy Pino** (cantera → vendido 30M€) *Datos a analizar: temporada 24/25*

→ 25/26: **George Mikautadze** (fichado 31M€) + **Solomon** (cedido) *Datos a analizar: temporada 24/25*

**Análisis:** Dos cadenas paralelas. Chukwueze reemplazado secuencialmente por agente libre y cesión con opción (riesgo mínimo). Pino sustituido en misma ventana de mercado, patrón atípico que sugiere reemplazo no planificado (posiblemente oferta inesperada por Pino).

#### Portero

**Gerónimo Rulli** (cantera → vendido 8M€)

→ 22/23: **Filip Jörgensen** (cantera → vendido 24,5M€) *Datos a analizar: temporada 21/22*

→ 24/25: **Luiz Junior** (fichado 12M€) *Datos a analizar: temporada 23/24*

**Análisis:** Cadena singular donde el reemplazo inicial (Jörgensen) supera en valor de mercado al vendido (Rulli), generando plusvalía secundaria. Modelo cantera→cantera→fichaje tras agotar pipeline interno.

#### Defensa Central

**Pau Torres** (cantera → vendido 33M€)

→ 23/24: **Eric Bailly** (agente libre) + **Jorge Cuenca/Raúl Albiol** (promoción interna)

→ 24/25: **Logan Costa** (fichado 18M€) *Datos a analizar: temporada 23/24*

→ 25/26 (tras lesión de Costa): **Renato Veiga** (24,5M€) + **Rafa Marín** (cedido 1M€) + **Javier Mouriño** (10M€) *Datos a analizar: temporada 24/25*

**Análisis:** Cadena reactiva a lesión grave. Primera sustitución (Bailly) sin coste. Segundo reemplazo (Costa) a 55% del valor de venta de Torres. Tercera ola de fichajes forzada por injury crisis, desvío del modelo estándar.

#### Lateral Izquierdo

**Pervis Estupiñán** (fichado 16,4M€ → vendido 17,8M€)

→ 22/23: **Johan Mojica** (fichado 5,5M€ → vendido 1,5M€) *Datos a analizar: temporada 21/22*

→ 24/25: **Sergi Cardona** (agente libre) *Datos a analizar: temporada 23/24*

**Análisis:** Secuencia de decremento de inversión (16M→5,5M→0M) manteniendo funcionalidad posicional. Patrón característico de posiciones no críticas donde el mercado ofrece abundancia de oferta.

#### Mediapunta/Interior

**Álex Baena** (cantera → vendido 55M€: 42M + 13M variables)

→ 25/26: **Alberto Moleiro** (fichado 16M€) *Datos a analizar: temporada 24/25*

**Análisis:** Venta récord del club en la era moderna. Reemplazo inmediato por perfil similar (mediapunta creativo sub-23) a menos del 30% del precio de venta. Caso paradigmático del modelo Villarreal.

#### Fichajes Estratégicos sin Coste

Paralelamente a las cadenas de sustitución, el Villarreal ha incorporado jugadores de alto rendimiento en condición de agentes libres:

- Nicola Pépé
- Pape Gueye
- Santi Comesaña
- Thomas Partey

Estos fichajes representan valor oculto: jugadores con métricas estadísticas preservadas pero deprecación de mercado por edad (28-30 años) o situación contractual.

### 2.2. Eintracht Frankfurt: Modelo de Plusvalías Extremas

El Frankfurt opera con menor frecuencia transaccional que Villarreal pero con márgenes unitarios superiores. Especialización en detección de talento infravalorado en ligas secundarias (Ligue 1, Eredivisie) y desarrollo acelerado en contexto Bundesliga.

#### Delantero Centro

**Randal Kolo Muani** (agente libre Nantes → vendido PSG 95M€)

→ 23/24: **Omar Marmoush** (agente libre VfL Wolfsburg → vendido Manchester City 75M€, invierno 24/25) *Datos a analizar: temporada 22/23 (Wolfsburg)*

→ 23/24: **Hugo Ekitike** (cedido PSG) *Datos a analizar: temporada 22/23 (PSG)*

→ 24/25: **Elye Wahi** (fichado 26M€, invierno 24/25) *Datos a analizar: temporada 23/24 (Lens)*

→ 24/25: **Hugo Ekitike** (fichado 31,5M€, verano 24/25 → vendido Liverpool 90M€) *Datos a analizar: temporada 23/24 (cesión Frankfurt)*

→ 25/26: **Jonathan Burkardt** (fichado Mainz 21M€) *Datos a analizar: temporada 24/25 (Mainz)*

**Análisis:** Cadena de seis movimientos en cuatro temporadas. Dos operaciones sin coste generan 170M€ combinados. Patrón distintivo: fichaje de delanteros en decline de grandes clubes (Ekitike ex-PSG) que recuperan forma en sistema Frankfurt, generando revalorización explosiva (+185% en caso Ekitike).

#### Defensa Central

**Evan Ndicka** (agente libre → Roma, valor mercado ~30M€)

→ 23/24: **Willian Pacho** (fichado 13,65M€ → vendido PSG 40M€) *Datos a analizar: temporada 22/23 (Royal Antwerp)*

→ 24/25: **Arthur Theate** (fichado 13M€) *Datos a analizar: temporada 23/24 (Rennes)*

**Análisis:** Pérdida de agente libre compensada con reemplazo que triplica su valor en una temporada (13,65M→40M). Segundo sustituto adquirido a precio equivalente, estableciendo pipeline de rotación. Target profile: defensores de ligas francófona sub-25 con métricas defensivas avanzadas.

**Modelo operativo Frankfurt:** Ventanas de desarrollo de 12-18 meses. Adquisición de talento probado en ligas de nivel 2-3 (Francia, Bélgica, Países Bajos), exposición a Bundesliga y UCL/UEL, venta a top-6 europeo. ROI medio: 250-300%.

### 2.3. LOSC Lille: Modelo de Desarrollo de Canteranos e Importación Selectiva

Lille presenta híbrido entre cantera propia (Yoro 62M€, Chevalier 40M€) y detección temprana en mercados africanos y sudamericanos. Horizonte temporal más largo (2-3 temporadas de desarrollo) que Frankfurt.

#### Defensa Central

**Gabriel Magalhães** (fichado 3M€ → vendido Arsenal 26M€)

→ 20/21: **Sven Botman** (fichado 8M€ Ajax → vendido Newcastle 37M€) *Datos a analizar: temporada 19/20 (Ajax)*

→ 22/23: **Bafodé Diakité** (fichado 3M€ Toulouse → vendido Bourmouth 35M€) *Datos a analizar: temporada 21/22 (Toulouse)*

→ 25/26: **Nathan Ngoy** (fichado 3,5M€ Gent) *Datos a analizar: temporada 24/25 (Gent)*

**Análisis:** Cadena de cuatro centrales en seis temporadas. Coste entrada consistente (3-8M€), venta entre 26-37M€. Multipliers de 4-8x. Perfil target: defensores sub-23 de ligas secundarias europeas (Eredivisie, Ligue 2, Jupiler League) con proyección física y métricas de duelos aéreos superiores.

#### Extremo

**Edon Zhegrova** (fichado 7M€ → vendido Galatasaray 15,5M€)

→ 25/26: **Marius Broholm** (fichado 6M€ Randers) o **Félix Correia** (fichado 7M€ Valencia) *Datos a analizar: temporada 24/25*

**Análisis:** Sustitución estándar con margen del 120%. Reemplazo dual sugiere incertidumbre en adaptación o sistema táctico que requiere dos perfiles complementarios.

#### Lateral Izquierdo

**Gabriel Gudmundsson** (fichado 6M€ → vendido Fiorentina 11,6M€)

→ 25/26: **Romain Perraud** (fichado 3M€ Southampton) + **Calvin Verdonk** (fichado 3M€ NEC) *Datos a analizar: temporada 24/25*

**Análisis:** ROI del 93% con reemplazo dual a mitad del coste total. Estrategia de hedging de riesgo mediante dos adquisiciones de bajo coste en lugar de un fichaje único de precio medio.

#### Mediocampista Defensivo

**Boubakary Soumaré** (cantera → vendido Leicester 20M€)

→ 21/22: **Amadou Onana** (fichado 13,5M€ → vendido Everton 40M€) *Datos a analizar: temporada 20/21 (Hamburgo)*

→ 22/23: **Carlos Baleba** (filial → vendido Brighton 27M€) *Datos a analizar: temporada 21/22 (Lille B)*

→ 23/24: **Nabil Bentaleb** + **Ignacio Miramón** (fichajes fallidos) *Datos a analizar: temporada 22/23*

**Análisis crítico:** Cadena de tres sustituciones exitosas generando 87M€ acumulados. Ruptura del patrón en cuarta iteración con dos fichajes consecutivos de bajo rendimiento. Este caso será particularmente relevante para validar si los algoritmos habrían desaconsejado estos fichajes basándose en disimilitud estadística con predecesores exitosos.

#### Delantero Centro

**Victor Osimhen** (fichado 22,5M€ → vendido Napoli 79M€)

→ 20/21: **Jonathan David** (fichado 27M€ → agente libre 2025, caso de mala gestión contractual) *Datos a analizar: temporada 19/20 (Gent)*

→ 25/26: **Hamza Igamane** (fichado 11,5M€ Rangers) *Datos a analizar: temporada 24/25 (Rangers)*

**Análisis crítico:** Osimhen representa el pico de eficiencia (multiplier 3,5x). David mantiene rendimiento pero salida sin traspaso constituye pérdida de 40-50M€ en valor de mercado. Lección: excelencia deportiva no garantiza eficiencia económica sin gestión contractual proactiva.

#### Producción de Cantera de Alto Valor

- **Leny Yoro** (vendido Manchester United 62M€)
- **Lucas Chevalier** (vendido PSG 40M€)

Estos casos representan ROI infinito (coste formación amortizado). Lille mantiene pipeline de canteranos con proyección de selección nacional sub-21, fundamental para sostenibilidad del modelo a largo plazo.

**Nota metodológica crítica:** Para los fichajes listados en temporada X (ej: 23/24), el análisis de machine learning utilizará estadísticas de la temporada X-1 (ej: 22/23), replicando la situación real de toma de decisión donde solo se dispone de rendimiento pasado para evaluar targets de fichaje.

### 2.4. Evolución de Valor de Plantilla y Rendimiento Competitivo

Un elemento diferenciador de estos tres clubes frente a modelos de liquidación de activos es el mantenimiento del valor total de plantilla pese al flujo constante de entradas y salidas. Esta estabilidad, combinada con presencia europea regular, valida la hipótesis de que la eficiencia económica no compromete el proyecto deportivo.

#### 2.4.1. Villarreal CF

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 363,50 M€ | 26,4 | 8,45 M€ | La Liga: 5º | UECL: Ronda de 16 |
| 23/24 | 252,50 M€ | 27,2 | 6,47 M€ | La Liga: 8º | UEL: Ronda de 16 |
| 24/25 | 264,25 M€ | 26,2 | 7,34 M€ | La Liga: 5º | No participó |
| 25/26 | 280,30 M€ | 26,3 | 10,38 M€ | En curso | En curso |

**Análisis:** Caída inicial del valor de plantilla en 23/24 (-111M€) coincide con salidas de Pau Torres (33M€), Jackson (37M€) y Chukwueze (21M€). Recuperación progresiva en 24/25 y 25/26 mediante fichajes de mayor precio unitario (Mikautadze 31M€, Veiga 24,5M€). Edad media estable entre 26,2-27,2 años, ventana óptima de rendimiento-valor de reventa.

**Rendimiento deportivo:** Cinco temporadas consecutivas en top-8 La Liga, cuatro participaciones europeas con clasificación a fase eliminatoria en tres ocasiones. Valor plantilla/posición liga muestra eficiencia: equipos con plantillas valoradas en 400-500M€ (Athletic, Betis) obtienen posiciones similares.

#### 2.4.2. LOSC Lille

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 347,95 M€ | 25,3 | 7,51 M€ | Ligue 1: 5º | Clasificó UECL 23/24 |
| 23/24 | 329,90 M€ | 23,8 | 8,02 M€ | Ligue 1: 4º | UECL: Cuartos |
| 24/25 | 336,60 M€ | 25,4 | 8,42 M€ | Ligue 1: 5º | UCL: Ronda de 16 |
| 25/26 | 215,60 M€ | 26,4 | 7,99 M€ | En curso | En curso |

**Análisis:** Notable consistencia en valor de plantilla (330-350M€) durante 22/23-24/25 pese a ventas acumuladas superiores a 300M€. Caída pronunciada en 25/26 (-121M€) atribuible a salidas simultáneas de Yoro (62M€), Chevalier (40M€) y Diakité (35M€) sin reemplazos inmediatos de valor equivalente.

Edad media excepcionalmente baja (23,8 años en 23/24), la más joven de Ligue 1 entre equipos top-6. Estrategia de "comprar jóvenes, vender prime" difiere de Villarreal (comprar prime jóvenes, vender prime establecidos).

**Rendimiento deportivo:** Cuatro temporadas consecutivas en top-5 Ligue 1, progresión europea desde UECL a UCL. Calificación a ronda eliminatoria UCL con plantilla valorada en ~70% de la media de clasificados (Benfica, Inter, RB Salzburg), evidencia de eficiencia táctica.

#### 2.4.3. Eintracht Frankfurt

| Temporada | Valor Plantilla | Edad Media | Valor Medio/Jugador | Competición Doméstica | Competición Europea |
|-----------|----------------|------------|---------------------|----------------------|---------------------|
| 22/23 | 324,55 M€ | 25,6 | 9,02 M€ | Bundesliga: 7º | UCL: Ronda de 16 |
| 23/24 | 326,25 M€ | 24,7 | 7,10 M€ | Bundesliga: 6º | UECL: K.O. Playoffs |
| 24/25 | 431,25 M€ | 24,6 | 13,07 M€ | Bundesliga: 3º | UEL: Cuartos |
| 25/26 | 383,90 M€ | 25,7 | 13,71 M€ | En curso | En curso |

**Análisis:** Incremento sustancial del valor de plantilla (+106M€) en 24/25 pese a venta de Marmoush (75M€). Explicación: fichajes de Ekitike (31,5M€), Wahi (26M€) y retención de talento joven que experimenta revalorización durante temporada (Skhiri, Götze recuperados).

Valor medio por jugador más alto de los tres casos (13-14M€ en 24/25-25/26), sugiere estrategia de menor rotación con fichajes de precio unitario superior. Frankfurt opera como "escalón intermedio" entre clubes de desarrollo (Lille) y establecimientos (Villarreal).

**Rendimiento deportivo:** Progresión clara de 7º→6º→3º Bundesliga. Participación europea ininterrumpida 2022-2026, incluyendo presencia en UCL (nivel superior). Frankfurt presenta correlación más fuerte entre valor plantilla y rendimiento que Lille o Villarreal, posiblemente debido a competitividad superior de Bundesliga vs Ligue 1.

#### 2.4.4. Comparativa Interliga

**Métrica de eficiencia:** Beneficio neto / Valor promedio plantilla (2022-2025)

- **Villarreal:** 137M€ / 290M€ = 47,2% ROI
- **Frankfurt:** 155M€ / 360M€ = 43,1% ROI
- **Lille:** 193M€ / 305M€ = 63,3% ROI

Lille emerge como el modelo más eficiente en términos puramente financieros, si bien opera en liga de menor exigencia competitiva. Frankfurt y Villarreal presentan ROI similares (~45%) con contextos competitivos más demandantes (Bundesliga top-4, La Liga top-6).

**Conclusión:** Los tres casos demuestran que beneficios sostenidos en el mercado son compatibles con:

- Estabilidad en valor total de plantilla (±15% variación)
- Edad media óptima (24-27 años)
- Clasificación a torneos europeos (80-100% de temporadas)
- Posiciones de media-alta tabla doméstica (3º-8º)

Esta evidencia empírica refuta la narrativa de que la generación de plusvalías requiere sacrificio del proyecto deportivo, validando la viabilidad de modelos data-driven integrales.

---

## 3. Metodología Analítica

### 3.1. Selección de Algoritmos

El presente trabajo implementa dos algoritmos complementarios de aprendizaje no supervisado para identificar y validar patrones de sustitución de jugadores en el mercado de fichajes. La selección responde a criterios de complementariedad metodológica, robustez estadística y validación cruzada.

#### 3.1.1. UMAP + Gaussian Mixture Models (GMM)

**Fundamento metodológico:**

UMAP (Uniform Manifold Approximation and Projection) constituye un método de reducción dimensional basado en topología de variedades que preserva tanto la estructura local como global de los datos, superando las limitaciones lineales del PCA tradicional. Su aplicación a las 220+ variables disponibles permite proyectar el espacio de características en dimensiones reducidas (10-15) manteniendo relaciones de similitud significativas.

Los Gaussian Mixture Models complementan esta reducción mediante clustering probabilístico soft, donde cada jugador obtiene probabilidades de pertenencia a múltiples arquetipos tácticos. Esta aproximación refleja la realidad del fútbol moderno, donde los roles posicionales son híbridos y no mutuamente excluyentes.

**Justificación para el proyecto:**

- **Detección de patrones de sustitución:** Identifica jugadores estadísticamente similares a los transferidos, considerando el espacio completo de características sin sesgos previos
- **Cuantificación de similitud:** Genera probabilidades de reemplazo óptimo en lugar de clasificaciones binarias
- **Validación de eficiencia:** Permite verificar si las sustituciones históricas ejecutadas responden a criterios objetivos basados en datos

**Ventaja competitiva:** Metodología no supervisada que descubre estructuras latentes sin asumir relaciones predefinidas entre variables, esencial para identificar estrategias data-driven genuinas.

#### 3.1.2. Variational Autoencoder (VAE)

**Fundamento metodológico:**

Los Variational Autoencoders constituyen arquitecturas de aprendizaje profundo generativo que aprenden representaciones latentes comprimidas mediante redes neuronales encoder-decoder. A diferencia de métodos geométricos, los VAE optimizan una función de pérdida que balancea reconstrucción de datos y regularización del espacio latente, forzando distribuciones normales que facilitan interpolación y generalización.

**Justificación para el proyecto:**

- **Validación metodológica cruzada:** Implementa una aproximación fundamentalmente distinta (optimización neural vs. geometría de variedades) para verificar robustez de hallazgos
- **Detección de overfitting:** La capacidad de reconstrucción actúa como métrica de validación; baja reconstrucción indica ajuste a ruido en lugar de patrones reales
- **Generalización predictiva:** Permite codificar nuevos jugadores en el espacio latente aprendido, habilitando predicción de sustitutos para transferencias futuras
- **Respaldo industrial:** Metodología validada en sistemas comerciales de scouting (Comparisonator), vinculando investigación académica con aplicación profesional

**Ventaja competitiva:** Arquitectura de deep learning que captura relaciones no lineales complejas imposibles de modelar mediante métodos estadísticos tradicionales, proporcionando segunda capa de validación independiente.

#### 3.1.3. Estrategia de Triangulación Metodológica

La implementación simultánea de ambos algoritmos responde a principios de validación científica robusta:

**Convergencia de resultados** → Si UMAP+GMM y VAE identifican conjuntos similares de reemplazos óptimos para las mismas transferencias históricas, se establece evidencia de patrones data-driven objetivos y replicables.

**Divergencia controlada** → Discrepancias entre metodologías permiten análisis de casos límite, identificando condiciones de contorno donde una aproximación supera a la otra, enriqueciendo las conclusiones del estudio.

**Eliminación de sesgo algorítmico** → La utilización de paradigmas completamente distintos (geometría topológica vs. optimización neural) minimiza riesgo de artefactos metodológicos específicos de un único enfoque.

Esta estrategia dual garantiza que las conclusiones sobre eficiencia económico-deportiva se fundamenten en evidencia estadística robusta y metodológicamente independiente, cumpliendo estándares de rigor científico para investigación aplicada en analytics deportivo.
