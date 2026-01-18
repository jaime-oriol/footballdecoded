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

3. [Análisis de Casos: Cadenas de Sustitución](#3-análisis-de-casos-cadenas-de-sustitución)............................................................................... 6
   - 3.1. [Villarreal CF: Modelo de Renovación Continua](#31-villarreal-cf-modelo-de-renovación-continua)................................................................. 6
      - 3.1.1. [Delantero Centro](#311-delantero-centro) ........................................................................................................... 6
      - 3.1.2. [Extremo/Segundo Delantero](#312-extremosegundo-delantero) ........................................................................................ 6
      - 3.1.3 [Extremos](#313-extremos)............................................................................................................................. 6
      - 3.1.4. [Portero](#314-portero)........................................................................................................................... 6
      - 3.1.5 [Defensa Central](#315-defensa-central) .............................................................................................................. 6
      - 3.1.6. [Lateral Izquierdo](#316-lateral-izquierdo)........................................................................................................... 7
      - 3.1.7. [Mediapunta / Extremo](#317-mediapunta--extremo) .................................................................................................. 7
      - 3.1.8. [Fichajes Estratégicos sin Coste](#318-fichajes-estratégicos-sin-coste)..................................................................................... 7
   - 3.2. [Eintracht Frankfurt: Modelo de Plusvalías Extremas](#32-eintracht-frankfurt-modelo-de-plusvalías-extremas) ....................................................... 7
      - 3.2.1. [Delantero Centro](#321-delantero-centro)........................................................................................................... 7
      - 3.2.2. [Defensa Central](#322-defensa-central)............................................................................................................. 7
   - 3.3. [LOSC Lille: Desarrollo de Canteranos e Importación Selectiva](#33-losc-lille-desarrollo-de-canteranos-e-importación-selectiva)........................................ 8
      - 3.3.1. [Defensa Central](#331-defensa-central) ............................................................................................................. 8
      - 3.3.2. [Extremo](#332-extremo) .............................................................................¡Error! Marcador no definido.
      - 3.3.3. [Lateral Izquierdo](#333-lateral-izquierdo)........................................................................................................... 8
      - 3.3.3. [Mediocampista Defensivo](#333-mediocampista-defensivo) ............................................................................................ 8
      - 3.3.4. [Delantero Centro](#334-delantero-centro) .......................................................................................................... 8
      - 3.3.5. [Producción de Cantera de Alto Valor](#335-producción-de-cantera-de-alto-valor)........................................................................... 8
   - 3.4. [Evolución de Valor de Plantilla y Rendimiento Competitivo](#34-evolución-de-valor-de-plantilla-y-rendimiento-competitivo)........................................... 9
      - 3.4.1. [Villarreal CF](#341-villarreal-cf)................................................................................................................... 9
      - 3.4.2. [LOSC Lille](#342-losc-lille)...................................................................................................................... 9
      - 3.4.3. [Eintracht Frankfurt](#343-eintracht-frankfurt)..................................................................................................... 10
      - 3.4.4. [Comparativa Interliga](#344-comparativa-interliga) ................................................................................................ 10

[ANEXOS](#anexos) ....................................................................................................................................... 11

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
3. Implementar dos algoritmos complementarios **(POR DEFINIR)** para identificar similitudes entre jugadores vendidos y sus reemplazos
4. Validar mediante triangulación metodológica si las sustituciones ejecutadas se fundamentan en proximidad estadística objetiva
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

- **Comparación estadística:** Radares de rendimiento y mapas de calor con datos de la temporada inmediatamente anterior al fichaje

- **Análisis de similitud:** Identificación de coincidencias y divergencias en perfiles

Este método replica el análisis post-hoc que un departamento de scouting realizaría para validar sus decisiones, demostrando si las sustituciones se fundamentan en proximidad cuantificable de perfiles o fueron decisiones oportunistas sin criterio estadístico.

**Limitación reconocida:** No permite identificar targets alternativos que los clubes pudieron haber considerado, solo valida si los fichajes ejecutados tienen sentido comparativo con el jugador vendido.

---

## 2. Metodología Analítica

_El diseño metodológico de este trabajo combina análisis descriptivo de cadenas de sustitución documentadas con validación cuantitativa mediante algoritmos de machine learning. Este enfoque dual permite, por un lado, contextualizar las decisiones de fichaje dentro de las restricciones reales del mercado y, por otro, demostrar si dichas decisiones responden a criterios estadísticos objetivos._

**Fuentes de datos.** _La recopilación de información se estructura en tres niveles complementarios. Para datos de rendimiento individual se emplean FBref (estadísticas avanzadas derivadas de StatsBomb) y WyScout (métricas event-data y mapas de calor), priorizando métricas normalizadas por 90 minutos que permiten comparación entre jugadores con diferente volumen de participación. La información transaccional (valores de traspaso, fechas de operación, duración de contratos) proviene de Transfermarkt, base de datos más completa para el período 2022-2026 en acceso público. Finalmente, los datos contextuales sobre rendimiento de equipos (clasificaciones ligueras, participación europea) se extraen de fuentes oficiales de UEFA y las respectivas federaciones nacionales._

**Normalización temporal crítica.** _Para cada sustitución analizada en temporada X, el análisis estadístico utiliza exclusivamente datos de rendimiento de la temporada X-1. Esta restricción metodológica replica las condiciones reales de toma de decisión: cuando el Villarreal fichó a Sørloth en verano 2023 para reemplazar a Jackson, el departamento de scouting solo disponía de las estadísticas 22/23 de ambos jugadores. Cualquier análisis retrospectivo que empleara datos de la temporada 23/24 incurriría en sesgo de información futura (look-ahead bias), invalidando la validación del proceso de decisión._

**Selección de variables.** _El conjunto de métricas empleado abarca cinco dimensiones del rendimiento posicional: producción ofensiva (goles, asistencias, xG, xA por 90'), contribución en construcción (pases progresivos, pases al área rival, creación de ocasiones), eficiencia técnica (porcentaje de pases completados, toques en área rival), trabajo defensivo (recuperaciones, intercepciones, duelos ganados) y métricas físicas (distancia recorrida, sprints). La selección específica de variables se ajusta por demarcación: para delanteros centro se prioriza finalización y movimientos en área; para defensas centrales, métricas de duelo aéreo y anticipación; para mediocampistas, progresión y distribución. Este enfoque posicional evita comparaciones espurias entre perfiles funcionalmente distintos._

**Algoritmo: PCA con Similitud Coseno.** _El método emplea Análisis de Componentes Principales (PCA) para proyectar el espacio de alta dimensionalidad (141 variables per90) a un subespacio reducido (20-29 componentes) que retiene 85% de la varianza explicada. Esta reducción dimensional elimina redundancias estadísticas entre métricas correlacionadas (ej: xG y goles, pases completados y asistencias) conservando la información discriminante entre perfiles. Sobre esta representación simplificada se calcula la similitud coseno entre el vector del jugador vendido y cada jugador del pool de análisis. La similitud coseno cuantifica la proximidad angular entre vectores independientemente de su magnitud, oscilando entre -1 (perfiles completamente opuestos) y 1 (perfiles idénticos en proporciones relativas). Valores >0.5 indican similitud fuerte; valores entre 0.3-0.5 similitud moderada; valores <0.3 perfiles estadísticamente distantes._

**Sistema de validación por ranking.** _Para cada jugador vendido se genera un ranking completo de similitud coseno sobre la población filtrada (posición, liga Big 5, edad <30 años, valor mercado <30M EUR, minutos >1250). El sistema clasifica el reemplazo ejecutado en tres categorías: (a) VALIDADO si figura en posiciones 1-10 del ranking, demostrando que el club identificó una de las opciones estadísticamente óptimas; (b) PARCIAL si figura en posiciones 11-30, indicando similitud moderada pero existencia de alternativas superiores no ejecutadas; (c) NO_VALIDADO si figura en posición >30, señalando que el fichaje responde a criterios no estadísticos (oportunidad de mercado, potencial proyectado, factores cualitativos). Este sistema cuantifica el grado de fundamentación data-driven de cada decisión._

**Criterios de interpretación.** _Un reemplazo clasificado como VALIDADO confirma que el departamento de scouting identificó correctamente un perfil estadísticamente equivalente al vendido, demostrando proceso analítico robusto. Un reemplazo PARCIAL sugiere que, aunque existe similitud cuantificable, el club pudo haber optimizado la decisión considerando alternativas de mayor proximidad estadística. Un reemplazo NO_VALIDADO no implica fracaso deportivo, sino que la decisión priorizó factores no capturados por métricas de rendimiento: precio de oportunidad (agente libre, fin de contrato), potencial de desarrollo (juveniles), encaje táctico específico, o restricciones económicas que limitaron el universo de targets viables. El algoritmo valida la fundamentación estadística de decisiones ejecutadas, no predice éxito futuro ni considera viabilidad real de fichajes alternativos._

**Limitaciones del método.** _El algoritmo retiene 85% de varianza explicada mediante PCA, descartando 15% de información presente en el espacio original de 141 dimensiones. Esta compresión puede eliminar matices distintivos entre perfiles híbridos o roles tácticos específicos. Adicionalmente, la similitud coseno mide proporciones relativas entre métricas, no magnitudes absolutas: dos jugadores con similitud 0.9 pueden tener volúmenes de producción diferentes (uno promedia 3 goles/90 y otro 6 goles/90, pero ambos distribuyen su producción proporcionalmente igual entre goles, asistencias, y creación). Finalmente, el método no captura factores cualitativos determinantes: intensidad defensiva sin balón, liderazgo, adaptación a sistemas tácticos específicos, o compatibilidad con compañeros de línea._

**Limitaciones reconocidas.** _Este diseño no permite identificar el universo completo de alternativas que los clubes consideraron durante el proceso de fichaje, solo valida la fundamentación estadística de las decisiones ejecutadas. Asimismo, el análisis cuantitativo no captura factores cualitativos determinantes en contexto real: viabilidad económica del traspaso, disposición del jugador a fichar, encaje con filosofía del entrenador, o consideraciones extradeportivas (edad, situación contractual, potencial de reventa). La metodología debe interpretarse como condición necesaria pero no suficiente: la similitud estadística entre vendido y fichado demuestra criterio analítico, pero no garantiza éxito deportivo ni explica por qué un club seleccionó ese target específico entre múltiples opciones estadísticamente equivalentes._

---

## 3. Análisis de Casos: Cadenas de Sustitución

Los tres equipos seleccionados presentan modelos de negocio convergentes, pero con matices tácticos distintivos. A continuación se documentan las principales cadenas de sustitución ejecutadas entre 2022 y 2026, estructuradas por posición y secuencia temporal.

### 3.1. Villarreal CF: Modelo de Renovación Continua

El Villarreal ha implementado una política de reinversión sistemática caracterizada por:

- Venta de activos canteranos en pico de valor (Pau Torres 33M€, Jackson 37M€, Baena 55M€)
- Reemplazo mediante combinación de fichajes de coste medio (15-25M€) y agentes libres estratégicos
- Mantenimiento de núcleo táctico estable (Parejo, Foyth, Gerard) que absorbe rotación posicional

#### 3.1.1. Delantero Centro

**Nicolas Jackson** (cantera → vendido 37M€)

→ 23/24: **Alexander Sørloth** (fichado 10M€ → vendido 32M€) _Datos a analizar: 22/23_

→ 24/25: **Thierno Barry** (fichado 20M€ **SUPERLIGA SUIZA** → vendido 30M€) _Datos a analizar: 23/24_
https://fbref.com/en/comps/57/history/Swiss-Super-League-Seasons

→ 25/26: **Tani Oluwaseyi** (fichado 8M€ **MLS** → actualmente en plantilla) _Datos a analizar: 24/25_
https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons

#### 3.1.2. Extremo/Segundo Delantero

**Ben Brereton Díaz** (agente libre → vendido 8,3M€)

→ 24/25: **Ayoze Pérez** (fichado 4M€) _Datos a analizar: 23/24_

#### 3.1.3 Extremos

**Samuel Chukwueze** (cantera → vendido 21M€)

→ 23/24: **Ilias Akhomach** (agente libre) _Datos a analizar: 22/23_

→ 24/25: **Tajon Buchanan** (cedido + opción compra 9M€, ejecutada 25/26) _Datos a analizar: 23/24_

**Yeremy Pino** (cantera → vendido 30M€) _Datos a analizar: temporada 24/25_

→ 25/26: **George Mikautadze** (fichado 31M€) + **Solomon** (cedido) _Datos a analizar: 24/25_

#### 3.1.4. Portero

**Gerónimo Rulli** (cantera → vendido 8M€)

→ 22/23: **Filip Jörgensen** (cantera → vendido 24,5M€) _NO HAY DATA POR SER CANTERA_

→ 24/25: **Luiz Junior** (fichado 12M€ **LIGA PORTUGUESA**) _Datos a analizar: 23/24_

#### 3.1.5 Defensa Central

**Pau Torres** (cantera → vendido 33M€)

→ 23/24: **Eric Bailly** (agente libre **TURQUIA**) + **Jorge Cuenca/Raúl Albiol** (promoción interna) _temporada 22/23_

Además, Bailly fue fichado por el United por 38M€ en 2016, habiendo sido fichado 1 año antes del Español por 5.7M€ (otro ejemplo de gestión TOP del Villareal)

→ 24/25: **Logan Costa** (fichado 18M€) _Datos a analizar: temporada 23/24_

→ 25/26 (tras lesión de Costa): **Renato Veiga** (24,5M€) + **Rafa Marín** (cedido 1M€) + **Santiago Mouriño** (10M€) _Datos a analizar: temporada 24/25_

#### 3.1.6. Lateral Izquierdo

**Pervis Estupiñán** (fichado 16,4M€ → vendido 17,8M€)

→ 22/23: **Johan Mojica** (fichado 5,5M€ → vendido 1,5M€) _Datos a analizar: temporada 21/22_

→ 24/25: **Sergi Cardona** (agente libre) _Datos a analizar: temporada 23/24_

#### 3.1.7. Mediapunta / Extremo

**Álex Baena** (cantera → vendido 55M€: 42M + 13M variables)

→ 25/26: **Alberto Moleiro** (fichado 16M€) _Datos a analizar: temporada 24/25_

#### 3.1.8. Fichajes Estratégicos sin Coste

Paralelamente a las cadenas de sustitución, el Villarreal ha incorporado jugadores de alto rendimiento en condición de agentes libres:

- Nicola Pépé
- Pape Gueye
- Santi Comesaña
- Thomas Partey

Estos fichajes representan valor oculto: jugadores con métricas estadísticas preservadas pero deprecación de mercado por edad (28-30 años) o situación contractual.

### 3.2. Eintracht Frankfurt: Modelo de Plusvalías Extremas

El Frankfurt opera con menor frecuencia transaccional que Villarreal pero con márgenes unitarios superiores. Especialización en detección de talento infravalorado en ligas secundarias (Ligue 1, Eredivisie) y desarrollo acelerado en contexto Bundesliga.

#### 3.2.1. Delantero Centro

**Randal Kolo Muani** (agente libre Nantes → vendido PSG 95M€)

→ 23/24: **Omar Marmoush** (agente libre → vendido Manchester City 75M€, invierno 24/25) _Datos a analizar: 22/23_

→ 23/24: **Hugo Ekitike** (cedido PSG) _Datos a analizar: 22/23_

→ 24/25: **Elye Wahi** (fichado 26M€, invierno 24/25) _Datos a analizar: 23/24_

→ 24/25: **Hugo Ekitike** (fichado 31,5M€, verano 24/25 → vendido Liverpool 90M€)

→ 25/26: **Jonathan Burkardt** (fichado Mainz 21M€) _Datos a analizar: 24/25_

#### 3.2.2. Defensa Central

**Evan Ndicka** (agente libre → Roma, valor mercado ~30M€)

→ 23/24: **Willian Pacho** (fichado 13,65M€ **LIGA BELGA** → vendido PSG 40M€) _Datos a analizar: 22/23_

→ 24/25: **Arthur Theate** (fichado 13M€) _Datos a analizar: 23/24_

**Modelo operativo Frankfurt:** Ventanas de desarrollo de 12-18 meses. Adquisición de talento probado en ligas de nivel 2-3 (Francia, Bélgica, Países Bajos), exposición a Bundesliga y UCL/UEL, venta a top-6 europeo. ROI medio: 250-300%.

### 3.3. LOSC Lille: Desarrollo de Canteranos e Importación Selectiva

Lille presenta híbrido entre cantera propia (Yoro 62M€, Chevalier 40M€) y detección temprana en mercados africanos y sudamericanos. Horizonte temporal más largo (2-3 temporadas de desarrollo) que Frankfurt.

#### 3.3.1. Defensa Central

**Gabriel Magalhães** (fichado 3M€ → vendido Arsenal 26M€)

→ 20/21: **Sven Botman** (fichado 8M€ **HOLANDA** → vendido Newcastle 37M€) _Datos a analizar: 19/20_

→ 22/23: **Bafodé Diakité** (fichado 3M€ → vendido 35M€) _Datos a analizar: 21/22_

→ 25/26: **Nathan Ngoy** (fichado 3,5M€ **LIGA BELGA**) _Datos a analizar: 24/25_

#### 3.3.2. Lateral Izquierdo

**Gabriel Gudmundsson** (fichado 6M€ → vendido Fiorentina 11,6M€)

→ 25/26: **Romain Perraud** (fichado 3M€)  _Datos a analizar: 24/25_

#### 3.3.3. Mediocampista Defensivo

**Boubakary Soumaré** (cantera → vendido 20M€)

→ 21/22: **Amadou Onana** (fichado 13,5M€ → vendido 40M€) _Datos a analizar: 20/21_

→ 22/23: **Carlos Baleba** (filial → vendido 27M€) _NO HAY DATA POR SER CANTERA_

→ 23/24: **Nabil Bentaleb** (fichajes fallidos) _Datos a analizar: 22/23_

#### 3.3.4. Delantero Centro

**Victor Osimhen** (fichado 22,5M€ → vendido Napoli 79M€)

→ 20/21: **Jonathan David** (fichado 27M€ **LIGA BELGA** → agente libre 2025, caso de mala gestión contractual) _Datos a analizar: 19/20_

→ 25/26: **Hamza Igamane** (fichado 11,5M€ **ESCOCIA**) _Datos a analizar: 24/25_
https://fbref.com/en/comps/40/history/Scottish-Premiership-Seasons

#### 3.3.5. Producción de Cantera de Alto Valor

**Leny Yoro** (vendido Manchester United 62M€)

**Lucas Chevalier** (vendido PSG 40M€)

Estos casos representan ROI infinito (coste formación amortizado). Lille mantiene pipeline de canteranos con proyección de selección nacional sub-21, fundamental para sostenibilidad del modelo a largo plazo.

**Nota metodológica crítica:** Para los fichajes listados en temporada X (ej: 23/24), el análisis de machine learning utilizará estadísticas de la temporada X-1 (ej: 22/23), replicando la situación real de toma de decisión donde solo se dispone de rendimiento pasado para evaluar targets de fichaje.

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

### A.1. FBref - Estadísticas Avanzadas (185 métricas totales, 153 per90)

**Categoría A: Goles y Finalización**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| goals | per90 | Big 5 + Extras |
| non_penalty_goals | per90 | Big 5 + Extras |
| penalty_kicks_made | per90 | Big 5 + Extras |
| penalty_kicks_attempted | per90 | Big 5 + Extras |
| shots | per90 | Big 5 + Extras |
| shots_on_target | per90 | Big 5 + Extras |
| shots_on_target_pct | NO (porcentaje) | Big 5 + Extras |
| avg_shot_distance | NO (métrica absoluta) | Big 5 + Extras |
| shots_free_kicks | per90 | Big 5 + Extras |
| penalty_kicks_won | per90 | Big 5 + Extras |
| penalty_kicks_conceded | per90 | Big 5 + Extras |

**Categoría B: Pases**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| passes_completed | per90 | Big 5 + Extras |
| passes_attempted | per90 | Big 5 + Extras |
| pass_completion_pct | NO (porcentaje) | Big 5 + Extras |
| passes_total_distance | per90 | Big 5 + Extras |
| passes_progressive_distance | per90 | Big 5 + Extras |
| passes_completed_short | per90 | Big 5 + Extras |
| passes_attempted_short | per90 | Big 5 + Extras |
| passes_completed_medium | per90 | Big 5 + Extras |
| passes_attempted_medium | per90 | Big 5 + Extras |
| passes_completed_long | per90 | Big 5 + Extras |
| passes_attempted_long | per90 | Big 5 + Extras |
| assists | per90 | Big 5 + Extras |
| expected_assists | per90 | Big 5 + Extras |
| key_passes | per90 | Big 5 + Extras |
| passes_into_final_third | per90 | Big 5 + Extras |
| passes_into_penalty_area | per90 | Big 5 + Extras |
| crosses_into_penalty_area | per90 | Big 5 + Extras |
| progressive_passes | per90 | Big 5 + Extras |

**Categoría C: Tipos de Pase (Pass Types)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| passes_live | per90 | Big 5 + Extras |
| passes_dead | per90 | Big 5 + Extras |
| passes_from_free_kicks | per90 | Big 5 + Extras |
| through_balls | per90 | Big 5 + Extras |
| switches | per90 | Big 5 + Extras |
| crosses | per90 | Big 5 + Extras |
| throw_ins | per90 | Big 5 + Extras |
| corner_kicks | per90 | Big 5 + Extras |
| corner_kicks_inswinging | per90 | Big 5 + Extras |
| corner_kicks_outswinging | per90 | Big 5 + Extras |
| corner_kicks_straight | per90 | Big 5 + Extras |
| passes_offside | per90 | Big 5 + Extras |
| passes_blocked | per90 | Big 5 + Extras |

**Categoría D: Creación de Ocasiones (Goal and Shot Creation - SCA/GCA)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| SCA_SCA | per90 | Big 5 + Extras |
| SCA_PassLive | per90 | Big 5 + Extras |
| SCA_PassDead | per90 | Big 5 + Extras |
| SCA_TO | per90 | Big 5 + Extras |
| SCA_Sh | per90 | Big 5 + Extras |
| SCA_Fld | per90 | Big 5 + Extras |
| SCA_Def | per90 | Big 5 + Extras |
| GCA_GCA | per90 | Big 5 + Extras |
| GCA_PassLive | per90 | Big 5 + Extras |
| GCA_PassDead | per90 | Big 5 + Extras |
| GCA_TO | per90 | Big 5 + Extras |
| GCA_Sh | per90 | Big 5 + Extras |
| GCA_Fld | per90 | Big 5 + Extras |
| GCA_Def | per90 | Big 5 + Extras |

**Categoría E: Acciones Defensivas**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| tackles | per90 | Big 5 + Extras |
| tackles_won | per90 | Big 5 + Extras |
| tackles_def_3rd | per90 | Big 5 + Extras |
| tackles_mid_3rd | per90 | Big 5 + Extras |
| tackles_att_3rd | per90 | Big 5 + Extras |
| challenge_tackles | per90 | Big 5 + Extras |
| challenges | per90 | Big 5 + Extras |
| challenge_tackles_pct | NO (porcentaje) | Big 5 + Extras |
| challenges_lost | per90 | Big 5 + Extras |
| blocked_shots | per90 | Big 5 + Extras |
| blocked_passes | per90 | Big 5 + Extras |
| interceptions | per90 | Big 5 + Extras |
| clearances | per90 | Big 5 + Extras |
| errors | per90 | Big 5 + Extras |

**Categoría F: Posesión y Toques (Possession)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| touches | per90 | Big 5 + Extras |
| touches_def_pen_area | per90 | Big 5 + Extras |
| touches_def_3rd | per90 | Big 5 + Extras |
| touches_mid_3rd | per90 | Big 5 + Extras |
| touches_att_3rd | per90 | Big 5 + Extras |
| touches_att_pen_area | per90 | Big 5 + Extras |
| touches_live_ball | per90 | Big 5 + Extras |
| take_ons_attempted | per90 | Big 5 + Extras |
| take_ons_successful | per90 | Big 5 + Extras |
| take_ons_successful_pct | NO (porcentaje) | Big 5 + Extras |
| take_ons_tackled | per90 | Big 5 + Extras |
| carries | per90 | Big 5 + Extras |
| carries_total_distance | per90 | Big 5 + Extras |
| carries_progressive_distance | per90 | Big 5 + Extras |
| progressive_carries | per90 | Big 5 + Extras |
| carries_into_final_third | per90 | Big 5 + Extras |
| carries_into_penalty_area | per90 | Big 5 + Extras |
| miscontrols | per90 | Big 5 + Extras |
| dispossessed | per90 | Big 5 + Extras |
| passes_received | per90 | Big 5 + Extras |
| progressive_passes_received | per90 | Big 5 + Extras |

**Categoría G: Duelos Aéreos**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| aerials_won | per90 | Big 5 + Extras |
| aerials_lost | per90 | Big 5 + Extras |
| aerials_won_pct | NO (porcentaje) | Big 5 + Extras |

**Categoría H: Disciplina**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| fouls_committed | per90 | Big 5 + Extras |
| fouls_drawn | per90 | Big 5 + Extras |
| offsides | per90 | Big 5 + Extras |
| yellow_cards | per90 | Big 5 + Extras |
| red_cards | per90 | Big 5 + Extras |
| second_yellow_cards | per90 | Big 5 + Extras |

**Categoría I: Expected Goals (xG)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| expected_goals | per90 | Big 5 + Extras |
| non_penalty_expected_goals | per90 | Big 5 + Extras |
| non_penalty_expected_goals_plus_assists | NO (suma compuesta) | Big 5 + Extras |
| expected_goals_on_target | per90 | Big 5 + Extras |
| expected_goals_buildup | per90 | Big 5 + Extras |

**Categoría J: Porteros (excluidas del análisis outfield)**
| Métrica | Normalización | Disponibilidad |
|---------|---------------|----------------|
| saves | per90 | Big 5 + Extras |
| save_pct | NO (porcentaje) | Big 5 + Extras |
| clean_sheets | NO (absoluto) | Big 5 + Extras |
| goals_against_per_90 | Ya per90 | Big 5 + Extras |
| psxg_minus_goals_allowed | per90 | Big 5 + Extras |
| launched_passes_completed | per90 | Big 5 + Extras |
| goal_kicks_launched | per90 | Big 5 + Extras |
| sweeper_defensive_actions_outside_pen_area | per90 | Big 5 + Extras |

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
| own_goals | per90 | Big 5 + Extras |
| goals_against | per90 | Big 5 + Extras |
| goals_from_penalties | per90 | Big 5 + Extras |
| goals_from_free_kicks | per90 | Big 5 + Extras |
| goals_from_corners | per90 | Big 5 + Extras |

### A.2. Understat - Métricas xG Granulares (10 métricas totales, 7 per90)

| Métrica | Normalización | Disponibilidad | Descripción |
|---------|---------------|----------------|-------------|
| understat_xg | per90 | Big 5 | xG total acumulado (shots xG) |
| understat_xg_assist | per90 | Big 5 | xA total (expected assists) |
| understat_xg_chain | per90 | Big 5 | xG generado en cadenas ofensivas donde participó |
| understat_xg_buildup | per90 | Big 5 | xG generado en buildups donde participó (excluye shot y key pass) |
| understat_shots | per90 | Big 5 | Total de tiros registrados |
| understat_key_passes | per90 | Big 5 | Pases clave que generan shot |
| understat_npxg | per90 | Big 5 | Non-penalty xG |
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
| Post per90 | 153 | 7 | 0 (filtro) | 160 |
| Post excl. GK | 141 | 7 | 0 | 148 |
| Input PCA | 141 per90 | + metadata (position, league, season) |

**Nota final:** La reducción de 148 métricas a 141 se debe a la exclusión automática de columnas con <5 valores válidos en el pool analizado, lo cual varía por posición y temporada.

