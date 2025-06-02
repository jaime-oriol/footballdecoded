// app/Main.tsx
import Link from '@/components/Link'
import ArticleCard from '@/components/ArticleCard'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'

// Constantes de configuración
const MAX_DISPLAY = 3

// Tipos específicos para este componente
interface MainProps {
  posts: CoreContent<Blog>[]
}

/**
 * Componente principal de la homepage de FootballDecoded
 *
 * Estructura:
 * - Sección introductoria con descripción del proyecto
 * - Lista de artículos recientes (máximo 3)
 * - CTA hacia todos los artículos
 * - CTA de suscripción a newsletter
 */
export default function Main({ posts }: MainProps) {
  return (
    <div className="divide-y divide-slate-200 dark:divide-slate-700">
      {/* === SECCIÓN INTRODUCTORIA === */}
      <IntroSection />

      {/* === ARTÍCULOS RECIENTES === */}
      <RecentArticlesSection posts={posts} />

      {/* === NEWSLETTER CTA === */}
      <NewsletterSection />
    </div>
  )
}

/**
 * Sección introductoria con descripción del proyecto
 */
function IntroSection() {
  return (
    <section className="mx-auto w-full space-y-6 px-4 pt-8 pb-10 sm:px-6">
      {/* Título principal */}
      <h1 className="font-headings text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl dark:text-slate-100">
        FootballDecoded
      </h1>

      {/* Cita destacada */}
      <blockquote className="border-l-4 border-slate-400 pl-4 italic">
        <p className="font-body text-lg leading-relaxed text-slate-600 dark:text-slate-400">
          "El fútbol es como el ajedrez, pero sin dados." — Lukas Podolski
        </p>
      </blockquote>

      {/* Descripción del proyecto */}
      <div className="font-body space-y-6 leading-relaxed text-slate-700 dark:text-slate-300">
        <p className="text-lg">
          FootballDecoded nace precisamente de esta aparente contradicción: el fútbol tiene
          estructuras, patrones y decisiones estratégicas claras, pero siempre mantiene algo que se
          escapa a los números. Justo ahí, en la tensión constante entre lo previsible y lo
          inesperado, surge la verdadera esencia del análisis.
        </p>

        <p>
          Este blog no es una colección de estadísticas frías ni un libro de jugadas tácticas. Es un
          intento honesto de entender el juego a través de datos, visualizaciones claras y modelos
          rigurosos. Aquí uso el análisis cuantitativo no para simplificar el fútbol, sino para
          revelar lo que realmente importa: los patrones, los detalles estratégicos, las claves
          ocultas que definen victorias y derrotas.
        </p>

        <p>
          Trabajo con herramientas avanzadas de ciencia de datos, modelos predictivos validados y
          visualizaciones tácticas intuitivas, siempre orientado a transformar información compleja
          en conocimiento práctico para entrenadores, analistas y responsables deportivos.
        </p>

        <p className="text-slate-600 italic dark:text-slate-400">
          <em>FootballDecoded</em> es mi laboratorio personal y profesional, diseñado para explorar,
          medir y comprender el fútbol con rigor y curiosidad.
        </p>
      </div>
    </section>
  )
}

/**
 * Sección de artículos recientes
 */
function RecentArticlesSection({ posts }: { posts: CoreContent<Blog>[] }) {
  const recentPosts = posts.slice(0, MAX_DISPLAY)
  const hasArticles = recentPosts.length > 0

  return (
    <section className="pt-10">
      <div className="w-full px-4 sm:px-6">
        <h2 className="font-headings mb-8 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
          Análisis Recientes
        </h2>
      </div>

      {/* Estado vacío */}
      {!hasArticles && <EmptyArticlesState />}

      {/* Lista de artículos */}
      {hasArticles && (
        <>
          <div className="w-full space-y-6 px-4 sm:px-6">
            {recentPosts.map((post) => (
              <ArticleCard key={post.slug} post={post} />
            ))}
          </div>

          {/* CTA hacia todos los artículos */}
          <div className="pt-10 text-center">
            <Link
              href="/blog"
              className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 shadow-sm transition-all duration-200 hover:bg-slate-50 hover:shadow-md dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <span className="font-body">Ver todos los artículos</span>
              <ArrowRightIcon />
            </Link>
          </div>
        </>
      )}
    </section>
  )
}

/**
 * Estado cuando no hay artículos publicados
 */
function EmptyArticlesState() {
  return (
    <div className="w-full px-4 py-16 text-center sm:px-6">
      <DocumentIcon />
      <h3 className="font-headings mb-2 text-xl font-medium text-slate-900 dark:text-slate-100">
        Próximamente
      </h3>
      <p className="font-body text-slate-500 dark:text-slate-400">
        Los primeros análisis tácticos, scouting funcional y métricas avanzadas estarán disponibles
        muy pronto.
      </p>
    </div>
  )
}

/**
 * Sección de newsletter con CTA
 */
function NewsletterSection() {
  return (
    <section className="pt-10">
      <div className="w-full px-4 sm:px-6">
        <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-sky-50 to-white p-6 shadow-sm dark:border-slate-700 dark:from-sky-900/10 dark:to-slate-800">
          <div className="space-y-4 text-center">
            <h2 className="font-headings text-xl font-semibold text-slate-900 dark:text-slate-100">
              Newsletter Semanal
            </h2>

            <p className="font-body text-slate-600 dark:text-slate-400">
              Cada lunes, las{' '}
              <strong className="text-concept">
                5 noticias más importantes del mundo del fútbol
              </strong>{' '}
              contadas con criterio, sin ruido, y con algo de opinión propia.
            </p>

            <Link
              href="/newsletter"
              className="inline-flex items-center rounded-lg bg-sky-600 px-6 py-3 font-medium text-white shadow-sm transition-colors hover:bg-sky-700 focus:ring-2 focus:ring-sky-500 focus:ring-offset-2"
            >
              <span className="font-body">Suscribirse gratis</span>
              <ArrowRightIcon />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

/**
 * Componentes de iconos reutilizables
 */
function ArrowRightIcon() {
  return (
    <svg className="ml-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
        clipRule="evenodd"
      />
    </svg>
  )
}

function DocumentIcon() {
  return (
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
  )
}
