interface Project {
  title: string
  description: string
  href?: string
  imgSrc?: string
}

const projectsData: Project[] = [
  {
    title: 'FootballDecoded Data System',
    description: `Sistema integral de ingesta, transformación y almacenamiento de datos futbolísticos. 
    Automatización completa del flujo ETL desde extracción web hasta preparación para análisis, 
    integrando múltiples fuentes: FBref, Understat, StatsBomb Open Data y Football-Data.co.uk. 
    Incluye scripts reutilizables, validación de calidad y exportación a formatos CSV y SQLite.`,
    imgSrc: '/static/images/projects/data-system.png',
    href: '/projects/data-system',
  },
  {
    title: 'Tactical Pressure Analysis Framework',
    description: `Framework especializado en análisis de sistemas de presión alta y media. 
    Implementa métricas como PPDA, intensidad de presión y mapeo posicional mediante Python y mplsoccer. 
    Incluye visualizaciones interactivas y comparativas entre equipos de élite, 
    con especial enfoque en las estructuras de Guardiola, Klopp y técnicos contemporáneos.`,
    imgSrc: '/static/images/projects/pressure-analysis.png',
    href: '/projects/pressure-analysis',
  },
  {
    title: 'Player Role Classification Engine',
    description: `Motor de clasificación funcional de jugadores basado en clustering y machine learning. 
    Utiliza algoritmos de reducción dimensional y análisis de comportamiento para identificar perfiles 
    tácticamente compatibles. Implementado en Python con scikit-learn, incluye modelos predictivos 
    para búsqueda de reemplazos y análisis de ajuste rol-equipo.`,
    imgSrc: '/static/images/projects/player-classification.png',
    href: '/projects/player-classification',
  },
  {
    title: 'xThreat & Advanced Metrics Suite',
    description: `Suite completa de métricas tácticas avanzadas que van más allá del xG tradicional. 
    Implementa xThreat, Buildup Disruption, Pass Network Centrality y métricas personalizadas 
    para cuantificación contextualizada del rendimiento. Desarrollado con visualizaciones automáticas 
    y scripts de análisis comparativo entre jugadores y equipos.`,
    imgSrc: '/static/images/projects/advanced-metrics.png',
    href: '/projects/advanced-metrics',
  },
  {
    title: 'Tactical Visualization Dashboard',
    description: `Dashboard interactivo desarrollado en React y D3.js para visualización táctica avanzada. 
    Incluye mapas de calor posicionales, redes de pase, análisis de transiciones y comparativas 
    estructurales. Integra datos en tiempo real y permite análisis detallado de fases específicas 
    del juego con exportación de reportes automatizados.`,
    imgSrc: '/static/images/projects/visualization-dashboard.png',
    href: '/projects/visualization-dashboard',
  },
  {
    title: 'Match Analysis Automation Pipeline',
    description: `Pipeline automatizado para análisis post-partido que procesa datos de eventos, 
    genera métricas clave y produce reportes ejecutivos. Incluye detección automática de patrones 
    tácticos, análisis de efectividad de cambios y evaluación de rendimiento individual y colectivo. 
    Optimizado para integración con flujos de trabajo de cuerpos técnicos profesionales.`,
    imgSrc: '/static/images/projects/automation-pipeline.png',
    href: '/projects/automation-pipeline',
  },
]

export default projectsData