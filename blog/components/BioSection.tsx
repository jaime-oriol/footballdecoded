const BioSection = () => {
  return (
    <div className="relative bg-white dark:bg-slate-900">
      {/* Línea de separación sutil */}
      <div className="absolute top-0 left-1/2 h-px w-24 -translate-x-1/2 bg-gradient-to-r from-transparent via-sky-500/30 to-transparent"></div>

      <div className="w-full space-y-10 px-4 py-16 sm:px-6">
        {/* Contenido biográfico - tipografía optimizada para lectura larga */}
        <div className="font-body space-y-6 leading-relaxed text-slate-700 dark:text-slate-300">
          <p className="text-lg">
            Mi primera memoria futbolística real fue el Barça de Messi. Tenía unos 8 años y lo
            recuerdo perfectamente: no era solo la victoria, era la precisión absoluta. Cada pase,
            cada movimiento, cada gol parecía parte de un plan perfecto.
          </p>

          <p>
            Desde entonces, esa admiración se convirtió en obsesión analítica. Dejé de centrarme
            solo en resultados para preguntarme constantemente por qué: ¿por qué un equipo que
            domina pierde?, ¿por qué un jugador sin goles o asistencias puede ser clave absoluta en
            un sistema táctico?
          </p>

          <p>
            Sí, soy del Barça, pero aprender a analizar con rigor significa mirar el juego sin
            privilegios ni prejuicios. Si algo brillante sucede en el Madrid, merece ser explicado
            claramente; si el Barça falla, lo analizo con la misma precisión. La lealtad en
            FootballDecoded es con la verdad y con los datos.
          </p>

          <p>
            Lo que realmente me apasiona no son los highlights virales ni los highlights. Es lo casi
            invisible: las estructuras tácticas profundas, los movimientos coordinados, la decisión
            estratégica sutil. La gran pregunta siempre es la misma:{' '}
            <strong className="text-concept">¿esto se puede medir? ¿Se puede explicar?</strong>
          </p>

          {/* Destacado principal */}
          <div className="relative rounded-r-lg border-l-2 border-sky-500/30 bg-sky-50/50 py-6 pr-6 pl-8 dark:border-sky-400/30 dark:bg-sky-900/10">
            <p className="mb-0 text-lg">
              <strong className="text-concept font-semibold">FootballDecoded</strong> nació de ahí.
              No es un blog de opinión. Es un espacio donde intento traducir el juego a datos, y los
              datos a juego. Combinar lo que se ve con lo que se puede probar. No elegir entre
              intuición y estadística, sino unirlas.
            </p>
          </div>

          <p>
            Estudio un doble grado en{' '}
            <em className="text-slate-600 dark:text-slate-400">
              Business Analytics e Ingeniería Informática
            </em>
            , porque creo que el futuro del análisis pasa justo por ahí: por saber de fútbol, pero
            también de datos, de visualización, de cómo hacer que la información cuente algo útil
            para quien toma decisiones.
          </p>

          <p>
            Este blog es mi laboratorio. Aquí encontrarás análisis tácticos serios, visualizaciones
            que cuentan cosas y muchas preguntas abiertas. Porque si hay algo que tengo claro es que
            las mejores respuestas no nacen del dogma.
          </p>

          {/* Conclusión con acento visual */}
          <div className="relative pt-4">
            <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
              Nacen de observar, medir, comparar. Y, sobre todo, de la curiosidad de seguir
              preguntando.
              {/* Punto de énfasis */}
              <span className="ml-2 inline-block h-2 w-2 animate-pulse rounded-full bg-sky-500"></span>
            </p>
          </div>
        </div>

        {/* Datos técnicos/académicos */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 dark:border-slate-700 dark:bg-slate-800/50">
          <h3 className="font-headings mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
            Perfil técnico
          </h3>
          <div className="grid gap-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-body text-slate-600 dark:text-slate-400">Formación</span>
              <span className="font-mono text-slate-900 dark:text-slate-100">
                Business Analytics + Ing. Informática
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-body text-slate-600 dark:text-slate-400">Especialización</span>
              <span className="font-mono text-slate-900 dark:text-slate-100">
                Análisis táctico + Métricas avanzadas
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-body text-slate-600 dark:text-slate-400">Herramientas</span>
              <span className="font-mono text-slate-900 dark:text-slate-100">
                Python, R, SQL, Tableau
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BioSection
