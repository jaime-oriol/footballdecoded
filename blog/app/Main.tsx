import Link from '@/components/Link'
import siteMetadata from '@/content/siteMetadata'
import { formatDate } from 'pliny/utils/formatDate'
import NewsletterForm from 'pliny/ui/NewsletterForm'
import ArticleCardHome from '@/components/ArticleCardHome'

const MAX_DISPLAY = 3

export default function Home({ posts }) {
  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {/* === SECCIÓN INTRODUCTORIA PROFESIONAL === */}
        <div className="space-y-2 pt-6 pb-8 md:space-y-5">
          <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14 dark:text-gray-100">
            FootballDecoded
          </h1>
          <div className="prose max-w-none text-lg text-gray-500 dark:text-gray-400">
            <blockquote className="border-primary-500 mb-6 border-l-4 pl-4 italic">
              "El fútbol es como el ajedrez, pero sin dados." — Lukas Podolski
            </blockquote>

            <div className="space-y-4 leading-relaxed text-gray-600 dark:text-gray-300">
              <p>
                <strong>FootballDecoded</strong> parte de esa idea: el fútbol está lleno de
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

              <p>
                <em>FootballDecoded</em> es mi proyecto académico y profesional. Una forma de
                construir criterio, compartir ideas y aportar una visión rigurosa, visual y práctica
                sobre el fútbol de élite. Porque si el juego es cada vez más complejo, merece
                también una forma más profunda - y honesta - de contarlo.
              </p>
            </div>
          </div>
        </div>

        {/* === SECCIÓN DE ARTÍCULOS RECIENTES === */}
        <div className="pt-8">
          <h2 className="mb-8 text-2xl leading-8 font-bold tracking-tight text-gray-900 dark:text-gray-100">
            Análisis Recientes
          </h2>

          {!posts.length && (
            <div className="py-16 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Próximamente
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                Los primeros análisis tácticos, scouting funcional y métricas avanzadas estarán disponibles muy pronto.
              </p>
            </div>
          )}

          {/* Lista de artículos con ArticleCardHome - mejor spacing */}
          {posts.length > 0 && (
            <div className="space-y-6">
              {posts.slice(0, MAX_DISPLAY).map((post) => (
                <ArticleCardHome key={post.slug} post={post} />
              ))}
            </div>
          )}
        </div>

        {/* === ENLACE A TODOS LOS ARTÍCULOS === */}
        {posts.length > 0 && (
          <div className="flex justify-center pt-10">
            <Link
              href="/blog"
              className="border-primary-500 text-primary-600 hover:bg-primary-50 hover:text-primary-700 dark:text-primary-400 dark:border-primary-400 dark:hover:text-primary-300 inline-flex items-center rounded-lg border bg-white px-8 py-3 text-base font-medium transition-all duration-200 shadow-sm hover:shadow-md dark:bg-gray-800 dark:hover:bg-gray-700"
            >
              Ver todos los artículos
              <svg className="ml-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
        )}

        {/* === SECCIÓN DE NEWSLETTER === */}
        <div className="pt-8">
          <div className="rounded-lg bg-gray-50 p-6 dark:bg-gray-800/50">
            <h3 className="mb-3 text-xl font-semibold text-gray-900 dark:text-gray-100">
              Newsletter de Análisis Táctico
            </h3>
            <p className="mb-4 text-gray-600 dark:text-gray-400">
              Recibe análisis exclusivos, métricas avanzadas y tendencias tácticas directamente en
              tu correo.
            </p>
            {siteMetadata.newsletter?.provider && <NewsletterForm />}
          </div>
        </div>

        {/* === ACCESO AL FEED RSS === */}
        <div className="pt-6 pb-4">
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <div>
              <Link href="/about" className="hover:text-primary-600 dark:hover:text-primary-400">
                Jaime Oriol
              </Link>
              {' • '}
              <span>© 2024 FootballDecoded</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/feed.xml"
                className="hover:text-primary-600 dark:hover:text-primary-400 flex items-center transition-colors"
                title="Feed RSS - FootballDecoded"
              >
                <svg className="mr-1 h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248S0 22.546 0 20.752s1.456-3.248 3.252-3.248 3.251 1.454 3.251 3.248zM1.677 6.155v4.301c5.493 0 9.942 4.448 9.942 9.94h4.299c0-7.837-6.403-14.241-14.241-14.241zM1.677.014v4.301C9.447.314 15.686 6.553 15.686 14.323H19.985C19.985 7.036 12.964.014 1.677.014z" />
                </svg>
                RSS Feed
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}