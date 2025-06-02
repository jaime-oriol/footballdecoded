'use client'

import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'
import Link from '@/components/Link'
import SectionsNavigation from '@/components/SectionsNavigation'
import ArticleCard from '@/components/ArticleCard'

interface PaginationProps {
  totalPages: number
  currentPage: number
  basePath?: string
}

interface ArticlesLayoutProps {
  posts: CoreContent<Blog>[]
  title: string
  initialDisplayPosts?: CoreContent<Blog>[]
  pagination?: PaginationProps
  section?: string
}

function Pagination({ totalPages, currentPage, basePath = '/blog' }: PaginationProps) {
  const prevPage = currentPage - 1 > 0
  const nextPage = currentPage + 1 <= totalPages

  return (
    <div className="flex items-center justify-between border-t border-slate-200 pt-8 dark:border-slate-700">
      <div className="flex w-0 flex-1 justify-start">
        {prevPage ? (
          <Link
            href={currentPage - 1 === 1 ? basePath : `${basePath}/page/${currentPage - 1}`}
            className="font-body inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <svg className="mr-3 h-5 w-5 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Anterior
          </Link>
        ) : (
          <div></div>
        )}
      </div>

      <div className="hidden md:flex">
        <span className="font-mono text-sm text-slate-600 dark:text-slate-400">
          Página{' '}
          <span className="font-medium text-slate-900 dark:text-slate-100">{currentPage}</span> de{' '}
          <span className="font-medium text-slate-900 dark:text-slate-100">{totalPages}</span>
        </span>
      </div>

      <div className="flex w-0 flex-1 justify-end">
        {nextPage ? (
          <Link
            href={`${basePath}/page/${currentPage + 1}`}
            className="font-body inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Siguiente
            <svg className="ml-3 h-5 w-5 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </Link>
        ) : (
          <div></div>
        )}
      </div>
    </div>
  )
}

export default function ArticlesLayout({
  posts,
  title,
  initialDisplayPosts = [],
  pagination,
  section,
}: ArticlesLayoutProps) {
  const displayPosts = initialDisplayPosts.length > 0 ? initialDisplayPosts : posts

  const getSectionDescription = (section?: string) => {
    switch (section) {
      case 'tactical-analysis':
        return 'Estudio de estilos, partidos clave, entrenadores y dinámicas de juego a través de modelos, métricas y visualizaciones tácticas.'
      case 'tactical-structures': // Backward compatibility
        return 'Estudio de estilos, partidos clave, entrenadores y dinámicas de juego a través de modelos, métricas y visualizaciones tácticas.'
      case 'analytical-scouting':
        return 'Identificación de perfiles tácticos mediante segmentación avanzada, agrupación funcional y análisis comparativo.'
      case 'scouting': // Backward compatibility
        return 'Identificación de perfiles tácticos mediante segmentación avanzada, agrupación funcional y análisis comparativo.'
      case 'advanced-metrics':
        return 'Exploración profunda de métricas avanzadas, modelos predictivos y visualización de datos aplicada al fútbol profesional.'
      case 'tactical-metrics-lab': // Backward compatibility
        return 'Exploración profunda de métricas avanzadas, modelos predictivos y visualización de datos aplicada al fútbol profesional.'
      default:
        return 'Análisis táctico avanzado, métricas cuantitativas y scouting funcional.'
    }
  }

  return (
    <div className="w-full">
      {/* Header de la sección */}
      <div className="w-full px-4 pt-8 pb-6 sm:px-6">
        <div className="space-y-4">
          <h1 className="font-headings text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl dark:text-slate-100">
            {title}
          </h1>
          <p className="font-body text-xl leading-relaxed text-slate-600 dark:text-slate-400">
            {getSectionDescription(section)}
          </p>
        </div>
      </div>

      {/* Navegación de secciones */}
      <SectionsNavigation variant="bar" />

      {/* CONTENIDO PRINCIPAL */}
      <div className="w-full px-4 sm:px-6">
        <main className="py-10">
          {/* Empty State - cuando no hay artículos */}
          {!displayPosts.length && (
            <div className="space-y-6 py-16 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                <svg
                  className="h-8 w-8 text-slate-400"
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
              </div>
              <div className="space-y-2">
                <h3 className="font-headings text-xl font-medium text-slate-900 dark:text-slate-100">
                  Próximamente
                </h3>
                <p className="font-body text-slate-600 dark:text-slate-400">
                  {section
                    ? `Los análisis de ${section.replace('-', ' ')} estarán disponibles pronto.`
                    : 'Los primeros análisis tácticos estarán disponibles pronto.'}
                </p>
              </div>
            </div>
          )}

          {/* Lista de artículos */}
          {displayPosts.length > 0 && (
            <div className="space-y-8">
              {displayPosts.map((post) => (
                <ArticleCard key={post.slug} post={post} />
              ))}
            </div>
          )}

          {/* Paginación */}
          {pagination && pagination.totalPages > 1 && (
            <div className="mt-12">
              <Pagination
                currentPage={pagination.currentPage}
                totalPages={pagination.totalPages}
                basePath={section ? `/blog/${section}` : '/blog'}
              />
            </div>
          )}

          {/* Newsletter CTA al final */}
          {displayPosts.length > 0 && (
            <div className="mt-16 border-t border-slate-200 pt-8 dark:border-slate-700">
              <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-sky-50 to-white p-6 text-center dark:border-slate-700 dark:from-sky-900/10 dark:to-slate-800">
                <h3 className="font-headings mb-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
                  ¿Te gustó este análisis?
                </h3>
                <p className="font-body mb-4 text-slate-600 dark:text-slate-400">
                  Recibe contenido similar cada lunes en tu bandeja de entrada
                </p>
                <Link
                  href="/newsletter"
                  className="font-body inline-flex items-center rounded-lg bg-sky-600 px-4 py-2 font-medium text-white transition-colors hover:bg-sky-700 focus:ring-2 focus:ring-sky-500 focus:ring-offset-2"
                >
                  Suscribirse a la newsletter
                  <svg className="ml-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </Link>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
