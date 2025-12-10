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
- ¿Cuántos toques tuvo Messi en la jugada previa?
- ¿Hubo regate exitoso en los segundos previos?
- ¿Desde qué zona empezó su participación? (zona_id)
- ¿Progresión del balón desde su primer toque? (delta_x)
- ¿Recibió bajo presión? (distancia a defensores)
- ¿Secuencia de acciones previas? (carry → regate → pase)
- ¿Hubo pre-asistencia de otro jugador a Messi?

**DURANTE la asistencia:**
- Tipo de pase (through ball, cross, short pass)
- Distancia del pase (metros)
- Zona desde donde asistió (zona_id, x, y)
- ¿Pase progresivo? (is_progressive)
- ¿Entrada a área? (is_box_entry)
- ¿Bajo presión al pasar? (distancia rival más cercano)
- xThreat generado por el pase (xthreat_gen)

**DESPUÉS de la asistencia:**
- ¿Desde dónde definió el compañero? (x, y del shot)
- xG del tiro asistido
- Marcador ANTES del gol (¿empató? ¿adelantó? ¿amplió?)
- Minuto del partido (¿decisivo en últimos 15min?)
- ¿Gol en jugada de estrategia o juego abierto?
- Importancia contextual (partido apretado vs goleada)

### 2. GOLES

**ANTES del gol:**
- ¿Cómo llegó el balón a Messi? (robo, pase, carry propio)
- ¿Quién le asistió? (si aplica)
- ¿Jugada individual o colectiva? (toques en secuencia previa)
- ¿Hubo regate exitoso previo al tiro?
- ¿Secuencia de pases previa? (número de pases en posesión)
- ¿Progresión desde zona defensiva? (delta_x total)
- ¿Contraataque o juego posicional? (tiempo de posesión)

**DURANTE el gol:**
- xG del tiro
- Tipo de tiro (pie derecho/izquierdo, cabeza)
- Zona del disparo (x, y)
- Distancia a portería
- Ángulo del tiro
- ¿Tiro dentro/fuera del área?
- ¿Bajo presión al tirar?

**DESPUÉS del gol:**
- ¿Cambió el marcador? (0-0 → 1-0 vs 3-0 → 4-0)
- Minuto del partido
- ¿Gol decisivo? (marcador final apretado)
- ¿Remontada? (estaban perdiendo)
- xG acumulado hasta ese momento

### 3. REGATES

**CONTEXTO del regate:**
- Zona del campo (defensiva, media, ofensiva)
- Número de rivales superados
- ¿Progresó hacia portería? (delta_x positivo)
- ¿Rompió líneas defensivas? (atravesó zonas)
- ¿Creó superioridad numérica? (2vs1 → 1vs0)

**IMPACTO del regate:**
- ¿Llevó a shot en los próximos 3 eventos?
- ¿Llevó a asistencia?
- ¿Generó entrada a área? (is_box_entry)
- xThreat generado post-regate
- ¿Ganó espacio para pase clave?
- ¿Desestabilizó estructura defensiva?

### 4. PASES CLAVE (no asistencias)

**Análisis de pases que casi asisten:**
- xG del tiro posterior (>0.15 = ocasión clara)
- ¿Por qué no fue gol? (save, miss, post)
- Distancia y tipo de pase
- Zona de pase vs zona de tiro
- ¿Cuántos pases clave NO terminaron en gol pero pudieron?

**Progresión de juego:**
- Pases progresivos totales (is_progressive)
- Pases que rompieron líneas
- Pases entre líneas
- Cambios de orientación

### 5. CREACIÓN DE JUEGO

**Secuencias de posesión:**
- Posesiones donde participó Messi (possession_id)
- Toques de Messi por posesión
- xG generado en posesiones con Messi vs sin Messi
- Duración de posesiones con su participación
- ¿Finalizaron en shot?

**xThreat agregado:**
- xThreat total generado por partido
- xThreat por acción (carry, pase, regate)
- Zonas donde genera más xThreat
- Evolución del xThreat por minuto jugado

**Pre-asistencias:**
- Pases que llevaron a asistencia de compañero
- Distancia entre pre-asistencia y asistencia
- Tipo de pre-asistencia (progresiva, cambio juego)

### 6. CARRIES (conducción)

**Análisis de carries:**
- Distancia total llevada con balón
- Progresión vertical (delta_x)
- ¿Cuántos carries progresivos? (>10 metros hacia portería)
- ¿Cuántos carries con regate exitoso?
- ¿Carries que llevaron a entrada de área?
- Velocidad de progresión (metros/segundo)

### 7. PRESIÓN DEFENSIVA

**Recuperaciones:**
- Robos de balón
- Intercepciones
- Pressing exitoso (distancia recorrida presionando)

**Impacto en recuperación:**
- ¿Contraataque inmediato tras recuperar?
- xG generado en 10 segundos post-recuperación

### 8. INFLUENCIA GLOBAL

**Mapa de calor contextual:**
- Zonas donde toca más balón
- Zonas donde genera más xThreat
- Zonas donde asiste/marca

**Impacto en resultado:**
- Win rate con Messi en campo vs sin él
- xG a favor/contra con Messi en campo
- Goles a favor/contra con Messi en campo
- Cambios de marcador con su participación

**Conexiones con compañeros:**
- Top 5 conexiones de pases (pass network)
- Jugadores que más asiste
- Jugadores que más le asisten
- Triángulos de juego más efectivos

### 9. MOMENTOS DECISIVOS

**Goles/asistencias por contexto:**
- Con empate (importancia alta)
- Ganando por 1 gol (cerrar partido)
- Perdiendo (remontada)
- Últimos 15 minutos del partido
- Primeros 15 minutos del partido

**Clutch performance:**
- xG en situaciones de presión (marcador apretado)
- Efectividad en momentos clave vs garbage time
- Big chances creadas/convertidas

### 10. COMPARACIÓN TEMPORAL

**Evolución durante la temporada:**
- xG per 90 por mes
- Asistencias per 90 por mes
- xThreat per 90 por mes
- ¿Mejor inicio o final de temporada?

**Consistencia:**
- Desviación estándar de métricas
- Partidos con >0.5 xG
- Partidos con >1.0 xThreat generado
- Racha de partidos con gol/asistencia

## Outputs Esperados

### Narrativas enriquecidas
- "Messi dio 12 asistencias, 8 vinieron tras regate exitoso, 5 fueron pases entre líneas, generaron 9.8 xG acumulado"
- "De sus 15 goles, 7 cambiaron el marcador, 4 fueron en remontadas, xG promedio de 0.28"

### Visualizaciones
- Timeline de acciones decisivas con contexto
- Mapa de calor de xThreat generado
- Network de conexiones con impacto
- Gráfico de clutch performance vs contexto

### Métricas derivadas
- Asistencias esperadas (xA) vs reales
- Goles esperados (xG) vs reales
- Impact score (combinación weighted de todas las dimensiones)
- Messi Influence Index por partido

## Data Sources

- **match_events.csv**: Event data completo (55 columnas)
- **shots_with_xg.csv**: Shots con xG de SofaScore
- **player_network.csv**: Conexiones entre jugadores
- **match_aggregates.csv**: Agregados por jugador/zona
- **spatial_analysis.csv**: Análisis espacial (convex hulls)

## Implementation Notes

- Usar possession_id para tracking de secuencias
- Calcular contexto de marcador en tiempo real
- Relacionar eventos por related_event_id y temporal proximity
- Filtrar eventos de Messi y expandir N eventos antes/después
- Clasificar importancia de acciones por momento del partido y marcador
