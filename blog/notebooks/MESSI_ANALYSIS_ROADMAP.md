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
- Comparación: Messi distribuye amplio vs otros fijan duplass