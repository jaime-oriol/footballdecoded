import Link from '@/components/Link'
import { formatDate } from 'pliny/utils/formatDate'
import ArticleCard from '@/components/ArticleCard'

const MAX_DISPLAY = 3

export default function Home({ posts }) {
  return (
    <>
      <div className="divide-y divide-slate-200 dark:divide-slate-700">
        {/* === SECCIÓN INTRODUCTORIA PROFESIONAL === */}
        <div className="max-w-prose mx-auto px-4 sm:px-6 space-y-6 pt-8 pb-10">
          {/* Título principal con Inter */}
          <h1 className="font-headings text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            FootballDecoded
          </h1>
          
          {/* Cita destacada */}
          <div className="border-l-4 border-slate-400 pl-4 italic">
            <blockquote className="text-lg text-slate-600 dark:text-slate-400 font-body leading-relaxed">
              "El fútbol es como el ajedrez, pero sin dados." — Lukas Podolski
            </blockquote>
          </div>

          {/* Descripción principal con IBM Plex Sans */}
          <div className="space-y-6 font-body leading-relaxed text-slate-700 dark:text-slate-300">
            <p className="text-lg">
              <strong className="text-concept font-medium">FootballDecoded</strong> parte de esa idea: el fútbol está lleno de
              estructuras, decisiones y patrones… pero sigue siendo impredecible. No se deja
              atrapar del todo por los números, ni por la intuición. Y ahí, en ese espacio
              intermedio, es donde ocurre lo interesante.
            </p>

            <p>
              Este blog es mi forma de explorar el juego desde un lugar que conecta dos mundos: el
              análisis táctico y el pensamiento cuantitativo. Desde la ingeniería hasta la
              pizarra. Aquí no se trata de reducir el fútbol a datos, sino de usarlos para ver más
              claro. Para entender mejor.
            </p>

            <p>
              Trabajo con herramientas de análisis avanzadas, modelos de datos y visualizaciones
              tácticas, pero siempre con el foco en lo que pasa en el campo. Analizo sistemas de
              juego, identifico perfiles funcionales de jugadores, y desarrollo métricas que
              buscan traducir comportamientos colectivos en conocimiento útil y aplicable.
            </p>

            <p className="text-slate-600 dark:text-slate-400 italic">
              <em>FootballDecoded</em> es mi proyecto académico y profesional. Una forma de
              construir criterio, compartir ideas y aportar una visión rigurosa, visual y práctica
              sobre el fútbol de élite. Porque si el juego es cada vez más complejo, merece
              también una forma más profunda - y honesta - de contarlo.
            </p>
          </div>
        </div>

        {/* === SECCIÓN DE ARTÍCULOS RECIENTES === */}
        <div className="pt-10">
          <div className="max-w-prose mx-auto px-4 sm:px-6">
            <h2 className="font-headings text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100 mb-8">
              Análisis Recientes
            </h2>
          </div>

          {!posts.length && (
            <div className="max-w-prose mx-auto px-4 sm:px-6 py-16 text-center">
              <svg
                className="mx-auto mb-4 h-12 w-12 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="font-headings text-xl font-medium text-slate-900 dark:text-slate-100 mb-2">
                Próximamente
              </h3>
              <p className="text-slate-500 dark:text-slate-400 font-body">
                Los primeros análisis tácticos, scouting funcional y métricas avanzadas estarán
                disponibles muy pronto.
              </p>
            </div>
          )}

          {/* Lista de artículos con ArticleCard unificado */}
          {posts.length > 0 && (
            <div className="space-y-6">
              {posts.slice(0, MAX_DISPLAY).map((post) => (
                <ArticleCard key={post.slug} post={post} />
              ))}
            </div>
          )}
        </div>

        {/* === ENLACE A TODOS LOS ARTÍCULOS === */}
        {posts.length > 0 && (
          <div className="pt-10 text-center">
            <Link
              href="/blog"
              className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 shadow-sm transition-all duration-200 hover:bg-slate-50 hover:shadow-md dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <span className="font-body">Ver todos los artículos</span>
              <svg className="ml-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
          </div>
        )}

        {/* === CALL TO ACTION NEWSLETTER === */}
        <div className="pt-10">
          <div className="max-w-prose mx-auto px-4 sm:px-6">
            <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-sky-50 to-white p-6 shadow-sm dark:border-slate-700 dark:from-sky-900/10 dark:to-slate-800">
              <div className="text-center space-y-4">
                <h2 className="font-headings text-xl font-semibold text-slate-900 dark:text-slate-100">
                  Newsletter Semanal
                </h2>
                <p className="font-body text-slate-600 dark:text-slate-400">
                  Cada lunes, las <strong className="text-concept">5 noticias más importantes del mundo del fútbol</strong>{' '}
                  contadas con criterio, sin ruido, y con algo de opinión propia.
                </p>
                <Link
                  href="/newsletter"
                  className="inline-flex items-center rounded-lg bg-sky-600 px-6 py-3 font-medium text-white shadow-sm transition-colors hover:bg-sky-700 focus:ring-2 focus:ring-sky-500 focus:ring-offset-2"
                >
                  <span className="font-body">Suscribirse gratis</span>
                  <svg className="ml-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}