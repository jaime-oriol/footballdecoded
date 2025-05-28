const BioSection = () => {
  return (
    <div className="relative bg-white dark:bg-gray-950">
      {/* Línea de separación sutil */}
      <div className="via-primary-500/30 absolute top-0 left-1/2 h-px w-24 -translate-x-1/2 bg-gradient-to-r from-transparent to-transparent"></div>

      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 xl:max-w-5xl xl:px-0">
        <div className="prose prose-lg dark:prose-invert max-w-none">
          <h2 className="relative mb-8 text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 dark:text-gray-100">
            Sobre mí
            {/* Pequeño acento visual */}
            <div className="bg-primary-500 absolute -bottom-2 left-0 h-0.5 w-12 rounded-full"></div>
          </h2>

          <div className="space-y-6 leading-relaxed text-gray-700 dark:text-gray-300">
            <p>
              La primera vez que vi fútbol de verdad fue viendo al Barça de Messi. Tenía unos 8 años
              y aquello me voló la cabeza. No era solo que ganaran: era <em>cómo</em> lo hacían. Esa
              precisión, esa sensación de que cada pase tenía un propósito, de que todo estaba
              conectado.
            </p>

            <p>
              Desde entonces no he parado: he jugado toda mi vida, he visto miles de partidos y, con
              el tiempo, he desarrollado una obsesión que va más allá del resultado. ¿Por qué un
              equipo que domina pierde? ¿Por qué un jugador que apenas aparece en las estadísticas
              puede ser la clave táctica de un sistema?
            </p>

            <p>
              Sí, soy del Barça. Pero si algo me ha enseñado analizar el juego en serio, es que los
              colores no pueden nublarte la vista. Aquí no hay privilegios. Si el Madrid hace algo
              brillante, se dice. Si el Barça se equivoca, se desmonta. El análisis riguroso no
              entiende de escudos.
            </p>

            <p>
              Lo que realmente me engancha no son los goles virales ni los highlights. Es lo
              invisible. Esa presión coordinada que desactiva al rival en 30 segundos. El
              centrocampista que no brilla en Instagram pero que mueve las piezas exactas. La
              cobertura silenciosa que salva un gol sin que nadie se dé cuenta.
            </p>

            <p>
              Cuando veo fútbol, no veo solo el balón: veo estructuras, decisiones, intenciones. Veo
              patrones que se repiten... hasta que alguien los rompe. Y siempre me hago la misma
              pregunta: <strong>¿se puede medir esto? ¿Se puede explicar?</strong>
            </p>

            <div className="border-primary-500/20 relative rounded-r-lg border-l-2 bg-gray-50/50 py-4 pr-4 pl-6 dark:bg-gray-800/30">
              <p className="mb-0">
                <strong className="text-primary-600 dark:text-primary-400">FootballDecoded</strong>{' '}
                nació de ahí. No es un blog de opinión. Es un espacio donde intento traducir el
                juego a datos, y los datos a juego. Combinar lo que se ve con lo que se puede
                probar. No elegir entre intuición y estadística, sino unirlas.
              </p>
            </div>

            <p>
              Estudio un doble grado en <em>Business Analytics e Ingeniería Informática</em>, porque
              creo que el futuro del análisis pasa justo por ahí: por saber de fútbol, pero también
              de datos, de visualización, de cómo hacer que la información cuente algo útil para
              quien toma decisiones.
            </p>

            <p>
              Este blog es mi laboratorio. Aquí encontrarás análisis tácticos serios,
              visualizaciones que cuentan cosas y muchas preguntas abiertas. Porque si hay algo que
              tengo claro es que las mejores respuestas no nacen del dogma.
            </p>

            <p className="relative text-lg font-medium text-gray-900 dark:text-gray-100">
              Nacen de observar, medir, comparar. Y, sobre todo, de la curiosidad de seguir
              preguntando.
              {/* Pequeño detalle visual al final */}
              <span className="bg-primary-500 ml-2 inline-block h-2 w-2 animate-pulse rounded-full"></span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BioSection
