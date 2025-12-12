# Messi Season Analysis - Roadmap

## Objetivo

Análisis exhaustivo de la temporada completa de Messi usando event data enriquecido. Ir más allá de métricas agregadas cuantitativas para explicar el CÓMO y el CONTEXTO de cada acción.

## Filosofía

No queremos saber solo QUE hizo (10 asistencias, 15 goles), sino:
- CÓMO lo hizo (secuencias, contexto táctico, presión)
- CUÁNDO lo hizo (momento del partido, marcador)
- QUÉ IMPACTO tuvo (cambió el marcador, generó xG, rompió líneas)

## Dimensiones de Análisis

### 1. ASISTENCIAS

**ANTES de la asistencia:**
- Cuántos toques tuvo Messi en la jugada previa
- Hubo regate exitoso en los segundos previos
- Desde qué zona empezó su participación (zona_id)
- Progresión del balón desde su primer toque (delta_x)
- Recibió bajo presión (distancia a defensores)
- Secuencia de acciones previas (carry + regate + pase)
- Hubo pre-asistencia de otro jugador a Messi
- Número total de eventos en la posesión antes de la asistencia
- Jugadores únicos que tocaron el balón en la secuencia
- Duración temporal de la secuencia (segundos)

**DURANTE la asistencia:**
- Tipo de pase (through ball, cross, short pass)
- Distancia del pase (metros)
- Zona desde donde asistió (zona_id, x, y)
- Pase progresivo (is_progressive)
- Entrada a área (is_box_entry)
- Bajo presión al pasar (distancia rival más cercano)
- xThreat generado por el pase (xthreat_gen)
- Ángulo del pase (horizontal, diagonal, vertical)
- Receptor del pase (next_player)

**DESPUÉS de la asistencia:**
- Desde dónde definió el compañero (x, y del shot)
- xG del tiro asistido
- Marcador ANTES del gol (empató, adelantó, amplió)
- Minuto del partido (decisivo en últimos 15min)
- Gol en jugada de estrategia o juego abierto
- Importancia contextual (partido apretado vs goleada)
- xG acumulado del equipo hasta ese momento
- Delta de xG tras la asistencia

### 2. GOLES

**ANTES del gol:**
- Cómo llegó el balón a Messi (robo, pase, carry propio)
- Quién le asistió (si aplica)
- Jugada individual o colectiva (toques en secuencia previa)
- Hubo regate exitoso previo al tiro
- Secuencia de pases previa (número de pases en posesión)
- Progresión desde zona defensiva (delta_x total)
- Contraataque o juego posicional (tiempo de posesión)
- Número de eventos en últimos 5 segundos antes del shot
- Tipos de eventos previos (pases/carries/regates)

**DURANTE el gol:**
- xG del tiro
- Tipo de tiro (pie derecho/izquierdo, cabeza)
- Zona del disparo (x, y)
- Distancia a portería
- Ángulo del tiro
- Tiro dentro/fuera del área
- Bajo presión al tirar
- Resultado del tiro (gol, atajado, poste, fuera)

**DESPUÉS del gol:**
- Cambió el marcador (0-0 a 1-0 vs 3-0 a 4-0)
- Minuto del partido
- Gol decisivo (marcador final apretado)
- Remontada (estaban perdiendo)
- xG acumulado hasta ese momento
- xG over/underperformance (gol vs xG esperado)

### 3. REGATES

**CONTEXTO del regate:**
- Zona del campo (defensiva, media, ofensiva)
- Número de rivales superados
- Progresó hacia portería (delta_x positivo)
- Rompió líneas defensivas (atravesó zonas)
- Creó superioridad numérica (2vs1 a 1vs0)
- Distancia total del carry con regate
- Success rate por zona del campo
- Contexto defensivo (número de defensores cercanos)

**IMPACTO del regate:**
- Llevó a shot en los próximos 3 eventos
- Llevó a asistencia
- Generó entrada a área (is_box_entry)
- xThreat generado post-regate
- Ganó espacio para pase clave
- Desestabilizó estructura defensiva
- Progresión conseguida (metros hacia portería)
- Comparación éxito vs zona (zona 7: 71%, zona 16: 0%)

### 4. PASES CLAVE (no asistencias)

**Análisis de pases que casi asisten:**
- xG del tiro posterior (>0.15 = ocasión clara)
- Por qué no fue gol (save, miss, post)
- Distancia y tipo de pase
- Zona de pase vs zona de tiro
- Cuántos pases clave NO terminaron en gol pero pudieron
- Expected Assists (xA) acumulado
- Gap entre xA y asistencias reales

**Progresión de juego:**
- Pases progresivos totales (is_progressive)
- Pases que rompieron líneas
- Pases entre líneas
- Cambios de orientación
- Distancia promedio de pases progresivos
- xThreat generado por pases progresivos
- Receptores más frecuentes de pases progresivos

### 5. CREACIÓN DE JUEGO

**Secuencias de posesión:**
- Posesiones donde participó Messi (possession_id)
- Toques de Messi por posesión
- xG generado en posesiones con Messi vs sin Messi
- Duración de posesiones con su participación
- Finalizaron en shot
- Eventos promedio por posesión (con/sin Messi)
- xThreat por posesión (con/sin Messi)
- Shots por posesión (con/sin Messi)
- Sequence Catalyst Rate (posesiones que terminan en shot)

**xThreat agregado:**
- xThreat total generado por partido
- xThreat por acción (carry, pase, regate)
- Zonas donde genera más xThreat
- Evolución del xThreat por minuto jugado
- Eficiencia de xThreat (xThreat por acción)
- Ranking de eficiencia vs otros jugadores
- Correlación xThreat alto vs resultado (gol/asistencia)

**Pre-asistencias:**
- Pases que llevaron a asistencia de compañero
- Distancia entre pre-asistencia y asistencia
- Tipo de pre-asistencia (progresiva, cambio juego)
- xA generado por pre-asistencias

### 6. CARRIES (conducción)

**Análisis de carries:**
- Distancia total llevada con balón
- Progresión vertical (delta_x)
- Cuántos carries progresivos (>10 metros hacia portería)
- Cuántos carries con regate exitoso
- Carries que llevaron a entrada de área
- Velocidad de progresión (metros/segundo)
- Distancia horizontal vs vertical de cada carry
- xThreat inicio vs xThreat final del carry
- Progressive Carry Impact (PCI) score
- Zona de inicio vs zona final

### 7. PRESIÓN DEFENSIVA

**Recuperaciones:**
- Robos de balón
- Intercepciones
- Pressing exitoso (distancia recorrida presionando)
- Zona de recuperación (defensiva, media, ofensiva)
- Tackles exitosos vs intentados

**Impacto en recuperación:**
- Contraataque inmediato tras recuperar
- xG generado en 10 segundos post-recuperación
- Tipo de acción inmediata tras recuperación (pase/carry/shot)
- Posesiones que terminan en shot tras recuperación de Messi

### 8. INFLUENCIA GLOBAL

**Mapa de calor contextual:**
- Zonas donde toca más balón
- Zonas donde genera más xThreat
- Zonas donde asiste/marca
- Heatmap de densidad de acciones por zona
- Comparación de zonas vs promedio de temporada

**Impacto en resultado:**
- Win rate con Messi en campo vs sin él
- xG a favor/contra con Messi en campo
- Goles a favor/contra con Messi en campo
- Cambios de marcador con su participación
- Dependencia estructural del equipo (shots con/sin)

**Conexiones con compañeros:**
- Top 5 conexiones de pases (pass network)
- Jugadores que más asiste
- Jugadores que más le asisten
- Triángulos de juego más efectivos
- Frecuencia de conexiones vs xG generado
- Diversidad de receptores (número de jugadores distintos)

### 9. MOMENTOS DECISIVOS

**Goles/asistencias por contexto:**
- Con empate (importancia alta)
- Ganando por 1 gol (cerrar partido)
- Perdiendo (remontada)
- Últimos 15 minutos del partido
- Primeros 15 minutos del partido
- Garbage time vs clutch time

**Clutch performance:**
- xG en situaciones de presión (marcador apretado)
- Efectividad en momentos clave vs garbage time
- Big chances creadas/convertidas
- Clutch Performance Score (CPS) por acción
- Multiplicador de contexto (perdiendo: 2.0x, últimos 15min: +0.5x)
- Porcentaje de impacto en situaciones críticas

### 10. COMPARACIÓN TEMPORAL

**Evolución durante la temporada:**
- xG per 90 por mes
- Asistencias per 90 por mes
- xThreat per 90 por mes
- Mejor inicio o final de temporada
- Picos y valles de actividad
- Tendencias de eficiencia (mejora/declive)

**Consistencia:**
- Desviación estándar de métricas
- Partidos con >0.5 xG
- Partidos con >1.0 xThreat generado
- Racha de partidos con gol/asistencia
- Coeficiente de variación de métricas clave

### 11. ANÁLISIS DE SECUENCIAS (NUEVO)

**Metodología de secuencias previas:**
- Extraer N eventos previos a cada shot/gol/asistencia
- Ventana temporal: últimos 10-30 segundos antes del momento clave
- Filtrar por equipo (solo eventos del mismo equipo)
- Métricas de secuencia:
  - Número de pases
  - Número de carries
  - Número de regates
  - Pases progresivos en secuencia
  - xThreat acumulado en secuencia
  - Progresión espacial total (delta_x desde inicio)
  - Duración temporal (segundos)
  - Eventos únicos por jugador

**Patrones de construcción:**
- Secuencias cortas (<5 eventos) vs largas (>10 eventos)
- Contraataques (duración <10s, progresión >30m) vs juego posicional
- Participación de Messi: selectiva (2-3 toques) vs dominante (5+ toques)
- Tipo de inicio: recuperación, pase rival, carry desde atrás
- Clasificar por tipo: rápido directo, construcción lateral, progresión central

**Análisis de red en secuencias:**
- Construir grafo de conexiones para cada secuencia
- Identificar jugador más conectado (hub)
- Camino crítico (shortest path desde inicio a finalización)
- Posición de Messi en la cadena (inicio, medio, final)

### 12. EFICIENCIA Y CONTEXTO (NUEVO)

**Métricas de eficiencia:**
- xThreat por acción (xThreat total / acciones totales)
- Asistencias por pase progresivo (conversion rate)
- Shots por entrada al área (conversion rate)
- Goles por shot (conversion rate vs xG)
- Ranking vs otros jugadores del equipo
- Ranking vs promedio de liga en misma posición

**Shot quality analysis:**
- xG promedio de shots propios
- xG promedio de shots que asiste
- Comparación: calidad de lo que genera vs lo que intenta
- Shot location: zonas preferidas vs zonas más efectivas
- Ángulo y distancia promedio de shots
- Clasificación: alta calidad (>0.15 xG) vs baja (<0.05 xG)

**Timing de actividad:**
- Dividir partido en franjas de 15 minutos
- Métricas por franja:
  - Acciones totales
  - Shots intentados
  - Asistencias
  - Regates exitosos
  - Pases progresivos
  - xThreat generado
- Identificar picos (alta actividad) y valles (baja actividad)
- Correlación entre picos de xThreat y conversión en goles

### 13. ENTRADAS AL ÁREA Y PENETRACIÓN (NUEVO)

**Box entries:**
- Total de entradas al área (is_box_entry)
- Por tipo de acción: pase, carry, regate
- Zona de origen de entradas exitosas
- Tasa de conversión: entradas que terminan en shot
- Comparación con otros jugadores (ranking)
- Entradas que generan asistencia vs shot propio

**Penetración vertical:**
- Pases que rompen última línea defensiva
- Carries hacia portería desde zona media
- Regates que superan último defensor
- xThreat ganado al penetrar
- Progresión promedio por penetración

### 14. RED DE PASES AVANZADA (NUEVO)

**Conexiones ponderadas:**
- Frecuencia de cada conexión (A -> B)
- xThreat generado por cada conexión
- Asistencias por conexión
- Tiempo promedio entre pases de cada dupla
- Distancia promedio de pases por conexión

**Análisis de centralidad:**
- Betweenness centrality: jugador intermediario clave
- Degree centrality: jugador más conectado
- Eigenvector centrality: conectado con jugadores importantes
- Comparar Messi vs otros hubs del equipo

**Patrones de distribución:**
- Diversidad de receptores (número único)
- Concentración vs dispersión (Gini index de conexiones)
- Comparación: Messi distribuye amplio vs otros fijan duplas

## Métricas Derivadas Avanzadas

### Messi Influence Index (MII)

Formula por posesión:
```
MII = (xThreat_generado * 0.3) +
      (Pases_progresivos * 0.2) +
      (Entradas_area * 0.15) +
      (Regates_exitosos * 0.1) +
      (Recuperaciones * 0.05) +
      (Asistencias * 0.2)
```

Aplicación:
- Calcular MII para cada posesión donde participa
- Comparar MII promedio vs resultado (shot/gol/pérdida)
- Identificar posesiones de máximo MII
- Correlación MII vs xG generado por posesión

### Clutch Performance Score (CPS)

Formula por acción:
```
CPS = Impacto_acción * Multiplicador_contexto

Multiplicador_contexto:
- Perdiendo: 2.0x
- Empatado: 1.5x
- Ganando por 1: 1.2x
- Ganando por 2+: 0.8x
- Últimos 15 min: +0.5x adicional
- Minutos 75-90: +0.3x adicional
```

Aplicación:
- Clasificar cada asistencia/gol/shot por CPS
- Comparar CPS promedio vs otros jugadores
- Identificar jugador más "clutch" del equipo
- Porcentaje de impacto en high-CPS moments

### Progressive Carry Impact (PCI)

Formula por carry:
```
PCI = (Progresión_metros / 10) * (1 + Regates_en_carry) * xThreat_zona_final

Componentes:
- Progresión en metros hacia portería (delta_x)
- Bonus por regates exitosos durante carry (multiplicador)
- Peso por xThreat de zona donde termina carry
```

Aplicación:
- Identificar carries de máximo impacto
- Comparar PCI vs otros jugadores con alta actividad de carry
- Correlación PCI vs shot posterior

### Expected Assists (xA) - Refinado

Formula:
```
xA = Sum(xG_tiro_posterior) solo si:
  1. Pase es progresivo O entrada a área
  2. Tiro ocurre en siguientes 2 eventos (misma posesión)
  3. Distancia de pase >5 metros

xA_real = xG solo de shots que resultaron en gol tras pase de Messi
```

Aplicación:
- Comparar xA vs asistencias reales
- Identificar over/underperformance
- xA acumulado por partido/temporada
- Gap analysis: xA esperado vs convertido

### Sequence Catalyst Rate (SCR)

Formula:
```
SCR = (Posesiones_con_jugador_que_terminan_en_shot / Posesiones_con_jugador_totales)

SCR_comparative = SCR_jugador / SCR_equipo_sin_jugador
```

Aplicación:
- Medir dependencia del equipo en jugador
- Comparar SCR en diferentes momentos de temporada
- Identificar partidos de máxima influencia (SCR >20%)

### Shot Creation Rate (ShCR)

Formula:
```
ShCR = Shots_generados_en_posesiones_con_jugador / Posesiones_totales_con_jugador

Shots_generados incluye:
- Shots propios
- Asistencias directas
- Pases clave que llevan a shot (no gol)
```

Aplicación:
- Frecuencia de generación de peligro
- Comparación vs promedio de equipo/liga
- Correlación ShCR vs xG del equipo

## Visualizaciones Propuestas

### 1. Timeline de Impacto Contextual

**Descripción:**
- Eje X: Minuto del partido (0-95)
- Eje Y dual:
  - Eje izquierdo: xThreat generado (barras apiladas por tipo de acción)
  - Eje derecho: Eventos clave (scatter plot)
- Elementos:
  - Asistencias: Puntos rojos grandes (tamaño = xG generado)
  - Shots: Puntos azules (tamaño = xG)
  - Regates exitosos: Puntos verdes pequeños
  - Recuperaciones: Puntos grises
  - Pases progresivos: Líneas verticales punteadas
- Marcadores verticales: Líneas de goles con contexto de marcador
- Zona de fondo: Colorear por contexto (perdiendo = rojo claro, ganando = verde claro)

**Insights revelados:**
- Picos de xThreat NO correlacionan directamente con goles
- Asistencias vienen de actividad concentrada en ventanas específicas
- Valles de inactividad entre picos de impacto
- Clutch moments identificados visualmente (últimos 15min + perdiendo)

### 2. Mapa de Calor Espacial - Triple Capa

**Descripción:**
- Base: Campo de fútbol dividido en 18 zonas
- Capa 1: Heatmap de densidad de acciones (transparencia por frecuencia)
- Capa 2: Vectores de progresión (flechas desde origen a destino de pases progresivos)
- Capa 3: Círculos para shots (tamaño = xG, color = resultado)
- Capa 4: Marcas de asistencias (estrellas en posición de pase)
- Gradiente de color: Azul (xThreat positivo) → Gris (neutral) → Rojo (xThreat negativo)

**Variaciones:**
- Filtro por resultado: Solo posesiones que terminan en shot
- Filtro por contexto: Solo momentos clutch (perdiendo, últimos 15min)
- Comparación lado a lado: Con Messi vs Sin Messi

**Insights revelados:**
- Epicentro de actividad (zona 13 para Messi)
- Asistencias desde zonas de construcción, NO de finalización
- Progresión preferida: diagonal desde derecha hacia centro
- Shots propios desde zonas de menor xThreat promedio

### 3. Sequence Flow Diagram - Anatomía de Goles

**Descripción:**
- Diagrama de flujo tipo Sankey para cada gol
- Nodos: Jugadores involucrados (tamaño = número de toques)
- Arcos: Tipo de acción entre nodos
  - Pase: Línea continua (grosor = distancia)
  - Carry: Línea punteada
  - Regate: Línea ondulada
- Color de arco: xThreat acumulado (gradiente azul a rojo)
- Anotaciones: Tipo de evento, zona, progresión (delta_x)
- Línea temporal: Segundos transcurridos desde inicio de posesión

**Ejemplo visual para gol De Paul:**
```
[Busquets] --(clearance)--> [Messi recovery zona 5] --(pass 12m)--> [De Paul]
--(carry 18m, zona 7->10)--> [Fray] --(pass 38m)--> [Busquets]
--(pass 13m)--> [Messi zona 13] ==PROGRESIVO 12m==> [De Paul carry zona 17]
--(shot 0.422 xG)--> GOAL
```

**Insights revelados:**
- Secuencias largas con participación selectiva de Messi (2-3 toques)
- Momento clave de Messi en cadena (no siempre al final)
- Progresión espacial total de la secuencia
- Tipo de construcción: posicional vs contraataque

### 4. Eficiencia Matrix - Scatter Plot

**Descripción:**
- Eje X: Acciones totales (volumen)
- Eje Y: xThreat total generado
- Color: Eficiencia (xThreat/acción) - escala de rojo (baja) a verde (alta)
- Tamaño de punto: Asistencias + Goles (output final)
- Forma: Círculo (Inter Miami), Triángulo (Vancouver)
- Etiquetas: Solo top 10 jugadores por impacto

**Cuadrantes:**
- Top-right: Alto volumen, alto xThreat (jugadores dominantes)
- Top-left: Bajo volumen, alto xThreat (eficientes)
- Bottom-right: Alto volumen, bajo xThreat (constructores/retentores)
- Bottom-left: Bajo impacto general

**Posición de Messi:**
- Alto volumen (62 acciones)
- Medio-bajo xThreat (0.427)
- PERO tamaño grande (2 asistencias)

**Insights revelados:**
- Desconexión entre xThreat y conversión final
- Messi en cuadrante "constructor" pero con output de "finalizador"
- Comparación de eficiencia vs otros jugadores clave

### 5. Radar de Contexto - Asistencias

**Descripción:**
- Radar de 8 ejes para cada asistencia:
  1. xG generado (0-1 normalizado)
  2. Distancia del pase (0-50m normalizado)
  3. xThreat previo (3 eventos antes, normalizado)
  4. Progresión en secuencia (delta_x total, normalizado)
  5. Presión defensiva (inverso de zona_id, zona 17 = máxima presión)
  6. Minuto crítico (score 0-100 basado en marcador + tiempo)
  7. Duración de secuencia (segundos, normalizado)
  8. Participación previa (toques de Messi antes de asistencia)

**Variaciones:**
- Overlay: Todas las asistencias de Messi en un solo radar (transparencia)
- Comparación: Asistencia 1 vs Asistencia 2 (colores diferentes)
- Benchmark: Promedio de asistencias de Inter Miami (línea punteada)

**Insights revelados:**
- Perfil de cada asistencia (oportunista vs construida)
- Consistencia o variabilidad en patrones
- Diferencia clutch (min 70, 95) vs early (min 3)

### 6. Possession Tree - Árbol de Decisión

**Descripción:**
- Estructura de árbol jerárquico
- Raíz: Inicio de cada posesión (recuperación/pase rival)
- Ramas: Cada evento (pase/carry/regate)
- Hojas: Resultado final (shot/pérdida/falta)
- Color de rama:
  - Verde: Posesión con participación de Messi
  - Gris: Posesión sin Messi
- Grosor de rama: xThreat acumulado en esa rama
- Anotaciones en nodos: Jugador, tipo de evento, zona

**Métricas por rama:**
- Duración (segundos)
- Eventos totales
- Jugadores únicos
- xThreat final
- Resultado (shot/gol/pérdida)

**Filtros:**
- Solo posesiones que terminan en shot
- Solo posesiones >5 eventos (construcción larga)
- Solo posesiones con Messi

**Insights revelados:**
- Árboles con Messi son más profundos (más eventos)
- Mayor probabilidad de terminar en shot
- Identificar ramas críticas (momento de entrada de Messi)

### 7. Network Graph - Conexiones Ponderadas

**Descripción:**
- Grafo no dirigido (o dirigido si queremos direccionalidad)
- Nodos: Jugadores de Inter Miami
  - Tamaño: Acciones totales
  - Color: xThreat generado (gradiente)
  - Posición: Basado en posición promedio en campo (x, y)
- Arcos: Conexiones de pases
  - Grosor: Frecuencia (número de pases entre jugadores)
  - Color: xThreat generado en esa conexión
  - Solo mostrar conexiones con 3+ pases
- Highlight: Conexiones de Messi en color diferente (rojo)

**Métricas anotadas:**
- Top 5 conexiones por frecuencia
- Top 5 conexiones por xThreat generado
- Jugador más central (betweenness centrality)

**Insights revelados:**
- Messi como nodo central con distribución diversa (7 receptores)
- Comparación con jugadores que tienen conexiones fijas
- Triángulos de juego más efectivos (A-B-C con alta frecuencia)

### 8. Shot Quality Funnel

**Descripción:**
- Embudo vertical en 4 etapas:
  1. Entradas al área (22 total)
  2. Shots generados (19 total)
  3. Shots on target (calcular desde outcome)
  4. Goles (4 total)
- Por jugador: Comparar Messi vs resto de equipo vs Vancouver
- En cada etapa:
  - Número absoluto (barras)
  - Tasa de conversión a siguiente etapa (%)
  - xG promedio (anotado)
- Color: Verde (Inter Miami), Azul (Messi), Rojo (Vancouver)

**Métricas derivadas:**
- Conversion rate: Entradas → Shots (Messi: 75%)
- Conversion rate: Shots → Goles (Messi: 0%)
- xG promedio por shot (Messi: 0.063, Equipo: 0.144)

**Insights revelados:**
- Messi convierte entradas en shots efectivamente
- Pero calidad de shots propios es baja
- Contraste con calidad de shots que asiste (0.422, 0.468 xG)

### 9. Timeline Doble - Con/Sin Messi

**Descripción:**
- Dos líneas temporales horizontales paralelas
- Superior: Posesiones CON participación de Messi
- Inferior: Posesiones SIN Messi (misma escala)
- Eje X: Cronología del partido (0-95 min)
- Cada posesión representada como:
  - Rectángulo (ancho = duración en segundos)
  - Color: Resultado (verde = shot, rojo = pérdida, gris = neutral)
  - Altura: xThreat de la posesión (escala)
- Marcas especiales:
  - Estrella: Shot generado
  - Círculo relleno: Gol

**Métricas agregadas:**
- Posesiones con Messi: 50 (promedio 4.0 eventos, 0.092 xThreat)
- Posesiones sin Messi: 196 (promedio 2.3 eventos, 0.033 xThreat)
- Shots: 7 vs 1
- Goles: 2 vs 0

**Insights revelados:**
- Concentración de peligro en posesiones con Messi
- Diferencia visual clara en altura de barras (xThreat)
- Frecuencia de shots mucho mayor con Messi

### 10. Regates Contextuales - 3D Scatter

**Descripción:**
- Plot 3D interactivo
- Eje X: Posición X del regate (0-100, campo horizontal)
- Eje Y: Posición Y del regate (0-100, campo vertical)
- Eje Z: Minuto del partido (0-95)
- Color: Éxito (verde) vs Fallo (rojo)
- Tamaño: Progresión conseguida tras regate (delta_x siguiente evento)
- Forma: Círculo (Messi), Triángulo (otros)

**Capas adicionales:**
- Campo de fútbol proyectado en plano XY
- Líneas de zona para identificar áreas
- Trayectoria de regates exitosos (línea conectando puntos)

**Vista 2D alternativa:**
- Proyección XY con color = éxito
- Facet por zona_id (small multiples)
- Success rate anotado por zona

**Insights revelados:**
- Cluster de regates fallados en zona 13-16 (alta presión defensiva)
- Regates exitosos en zona 7-10 (campo medio)
- Patrón temporal: más regates en min 15-30 (pico actividad)

### 11. Eficiencia Timeline - Líneas Múltiples

**Descripción:**
- Eje X: Minuto del partido (franjas de 15 min)
- Eje Y: Múltiples métricas normalizadas (0-1)
- Líneas:
  - xThreat generado (azul)
  - Asistencias (rojo, stepped line)
  - Shots (verde)
  - Pases progresivos (naranja)
  - Regates exitosos (púrpura)
- Área de fondo: Actividad total (gris, transparencia)
- Marcadores verticales: Goles del equipo

**Insights revelados:**
- Des-correlación entre xThreat alto (15-30 min) y conversión
- Picos de asistencias (60-75, 90+) con bajo xThreat
- Valles de inactividad (30-45, 75-90)

### 12. Heatmap de Impacto - Matriz

**Descripción:**
- Matriz 2D: Zona (filas) x Tipo de acción (columnas)
- Zonas: 1-18 (field zones)
- Tipos: Pase, Carry, Regate, Shot, Asistencia
- Color: Frecuencia (escala de blanco a azul oscuro)
- Anotaciones: xThreat promedio en cada celda
- Totales por fila y columna

**Insights revelados:**
- Zona 13: Máxima actividad en pases (12) y asistencias (2)
- Zona 17: Shots únicamente (2)
- Zona 7: Mix de regates (1) y carries (1)

## Data Sources

### Inputs

- **match_events.csv**: Event data completo (55 columnas)
  - Incluye: event_type, zona_id, x, y, end_x, end_y, xg, xthreat, xthreat_gen
  - Incluye: is_progressive, is_box_entry, is_shot, is_goal, is_assist
  - Incluye: possession_id, related_event_id, next_player
  - Incluye: take_ons_in_carry, outcome_type

- **shots_with_xg.csv**: Shots con xG de SofaScore (18 columnas)
  - xG y xgot por shot
  - Coordenadas (location_x, location_y, goal_mouth_y)
  - Metadata (body_part, situation, result)

- **player_network.csv**: Conexiones entre jugadores (18 columnas)
  - Passer, receiver, frequency
  - Métricas agregadas por conexión

- **match_aggregates.csv**: Agregados por jugador/zona (36 columnas)
  - Métricas acumuladas por jugador
  - Distribución por zona

- **spatial_analysis.csv**: Análisis espacial (29 columnas)
  - Convex hulls
  - Áreas de influencia

- **match_info.csv**: Metadatos del partido (11 columnas)
  - Equipos, fecha, resultado
  - IDs de match (WhoScored, SofaScore)

### Outputs esperados

**Archivos procesados:**
- **messi_actions_enriched.csv**: Todas las acciones de Messi con contexto adicional
  - Columnas originales + secuencias previas + métricas derivadas
  - MII, CPS, PCI, xA por acción

- **messi_sequences.csv**: Secuencias que incluyen a Messi
  - possession_id, duración, eventos totales, jugadores únicos
  - xThreat acumulado, resultado (shot/gol/pérdida)
  - Participación de Messi (toques, tipo de acciones)

- **messi_shots_analysis.csv**: Análisis detallado de shots
  - Shot propio + secuencia previa de 5 eventos
  - Contexto defensivo, zona, xG, resultado

- **messi_assists_analysis.csv**: Análisis profundo de asistencias
  - Asistencia + toda la secuencia de posesión
  - Receptor, xG generado, contexto de marcador, CPS

- **messi_carries_analysis.csv**: Análisis de carries
  - Carry + eventos inmediatamente después
  - PCI, distancia, progresión, regates incluidos

- **messi_dribbles_analysis.csv**: Análisis de regates
  - Regate + contexto (zona, presión, resultado posterior)
  - Success rate por zona, correlación con shots

## Implementation Notes

### Pipeline de procesamiento

**Paso 1: Filtrado y extracción**
```python
# Extraer todas las acciones de Messi
messi_events = df[df['player'] == 'Lionel Messi']

# Para cada acción, expandir N eventos antes/después
for idx, action in messi_events.iterrows():
    prev_events = get_previous_events(df, action, window=5)
    next_events = get_next_events(df, action, window=3)
```

**Paso 2: Enriquecimiento contextual**
```python
# Calcular contexto de marcador en tiempo real
scoreboard = calculate_scoreboard_timeline(goals_df)

# Agregar contexto a cada acción
messi_events['score_context'] = messi_events.apply(
    lambda x: get_score_context(x['minute'], scoreboard), axis=1
)

# Calcular Clutch Performance Score
messi_events['CPS'] = calculate_cps(messi_events, scoreboard)
```

**Paso 3: Análisis de secuencias**
```python
# Agrupar por possession_id
possessions = df.groupby('possession_id')

# Para cada posesión con Messi
messi_possessions = possessions.filter(
    lambda x: 'Lionel Messi' in x['player'].values
)

# Calcular métricas de secuencia
for poss_id, poss_data in messi_possessions:
    analyze_possession_sequence(poss_data)
```

**Paso 4: Métricas derivadas**
```python
# Messi Influence Index por posesión
mii = calculate_mii(messi_possessions)

# Expected Assists
xa = calculate_xa(messi_events, shots_df)

# Progressive Carry Impact
pci = calculate_pci(carries_df)

# Sequence Catalyst Rate
scr = calculate_scr(messi_possessions, all_possessions)
```

**Paso 5: Agregación temporal**
```python
# Dividir en franjas temporales
time_bins = [0, 15, 30, 45, 60, 75, 90, 120]
messi_events['time_bin'] = pd.cut(
    messi_events['minute'], bins=time_bins
)

# Agregar métricas por franja
temporal_aggregates = messi_events.groupby('time_bin').agg({
    'xthreat_gen': 'sum',
    'is_shot': 'sum',
    'is_assist': 'sum',
    'is_progressive': 'sum'
})
```

### Funciones clave

**get_previous_events()**
```python
def get_previous_events(df, action, window=5, time_window=30):
    """
    Extrae N eventos previos a una acción.

    Args:
        df: DataFrame completo de eventos
        action: Fila de la acción de referencia
        window: Número de eventos a extraer
        time_window: Ventana temporal en segundos

    Returns:
        DataFrame con eventos previos del mismo equipo
    """
    prev_events = df[
        (df['expanded_minute'] < action['expanded_minute']) &
        (df['expanded_minute'] >= action['expanded_minute'] - time_window/60) &
        (df['team'] == action['team'])
    ].tail(window)

    return prev_events
```

**calculate_cps()**
```python
def calculate_cps(actions, scoreboard):
    """
    Calcula Clutch Performance Score para cada acción.

    Args:
        actions: DataFrame de acciones
        scoreboard: Timeline de marcador

    Returns:
        Series con CPS por acción
    """
    def get_multiplier(minute, score_diff):
        base_multiplier = {
            'losing': 2.0,
            'tied': 1.5,
            'winning_by_1': 1.2,
            'winning_by_2plus': 0.8
        }[score_diff]

        time_bonus = 0.5 if minute >= 75 else 0.0

        return base_multiplier + time_bonus

    actions['score_diff'] = actions.apply(
        lambda x: get_score_diff(x['minute'], scoreboard), axis=1
    )

    actions['cps_multiplier'] = actions.apply(
        lambda x: get_multiplier(x['minute'], x['score_diff']), axis=1
    )

    # Impacto base según tipo de acción
    impact = {
        'is_assist': 1.0,
        'is_goal': 1.0,
        'is_shot': 0.5,
        'is_progressive': 0.3,
        'xthreat_gen': 0.2
    }

    actions['base_impact'] = actions.apply(
        lambda x: sum([
            impact[key] * x[key] for key in impact.keys()
            if key in x and x[key] > 0
        ]), axis=1
    )

    return actions['base_impact'] * actions['cps_multiplier']
```

**calculate_pci()**
```python
def calculate_pci(carries):
    """
    Calcula Progressive Carry Impact para carries.

    Formula:
    PCI = (Progresión_metros / 10) * (1 + Regates_en_carry) * xThreat_zona_final

    Args:
        carries: DataFrame de carries

    Returns:
        Series con PCI por carry
    """
    carries['progression'] = carries['end_x'] - carries['x']
    carries['progression'] = carries['progression'].clip(lower=0)  # Solo progresión positiva

    carries['dribble_bonus'] = 1 + carries['take_ons_in_carry'].fillna(0)

    carries['xthreat_final'] = carries['xthreat'] + carries['xthreat_gen']

    pci = (carries['progression'] / 10) * carries['dribble_bonus'] * carries['xthreat_final']

    return pci
```

**calculate_xa()**
```python
def calculate_xa(passes, shots):
    """
    Calcula Expected Assists (xA) para pases.

    Solo cuenta xG de shots que:
    1. Vienen de pase progresivo O entrada a área
    2. Ocurren en siguientes 2 eventos (misma posesión)
    3. Distancia de pase >5 metros

    Args:
        passes: DataFrame de pases
        shots: DataFrame de shots

    Returns:
        Series con xA por pase
    """
    xa_list = []

    for idx, pass_event in passes.iterrows():
        # Verificar condiciones
        if not (pass_event['is_progressive'] or pass_event['is_box_entry']):
            xa_list.append(0.0)
            continue

        if pass_event.get('pass_distance', 0) < 5:
            xa_list.append(0.0)
            continue

        # Buscar shot en siguientes 2 eventos
        next_shots = shots[
            (shots['expanded_minute'] > pass_event['expanded_minute']) &
            (shots['expanded_minute'] <= pass_event['expanded_minute'] + 0.05) &
            (shots['possession_id'] == pass_event['possession_id'])
        ]

        if len(next_shots) > 0:
            xa_list.append(next_shots.iloc[0]['xg'])
        else:
            xa_list.append(0.0)

    return pd.Series(xa_list, index=passes.index)
```

### Consideraciones técnicas

- **Manejo de timestamps**: Usar `expanded_minute` (decimal) para cálculos temporales precisos
- **Relacionar eventos**: Usar `related_event_id` cuando esté disponible, sino proximidad temporal (<0.05 min)
- **Normalización de zonas**: Asegurar consistencia en zone_id (1-18)
- **Filtrado de ruido**: Ignorar eventos de tipo "Start", "End", "FormationSet"
- **Posesiones**: Considerar cambio de posesión en eventos de tipo "Dispossessed", "Tackle", "Interception"
- **Ventanas temporales**: Usar ventanas adaptativas (5-30s) según tipo de análisis
- **Performance**: Pre-computar métricas costosas (secuencias, contextos)
- **Validación**: Cross-check métricas derivadas con stats oficiales cuando sea posible

### Outputs de visualización

**Formato recomendado:**
- Plots estáticos: PNG de alta resolución (300 DPI, tamaño A4)
- Plots interactivos: HTML con Plotly (standalone, embeddable)
- Network graphs: JSON exportable para Gephi/Cytoscape
- Tablas: Markdown o LaTeX para reportes

**Estructura de archivos:**
```
viz/
├── plots/
│   ├── timeline_impact.png
│   ├── heatmap_spatial.png
│   ├── sequence_flow_goal1.png
│   ├── sequence_flow_goal2.png
│   ├── efficiency_matrix.png
│   ├── radar_assists.png
│   ├── possession_tree.html
│   ├── network_connections.html
│   └── dribbles_3d.html
├── data/
│   ├── messi_actions_enriched.csv
│   ├── messi_sequences.csv
│   ├── messi_shots_analysis.csv
│   └── messi_assists_analysis.csv
└── reports/
    ├── messi_season_summary.md
    └── messi_match_report_YYYY-MM-DD.md
```
