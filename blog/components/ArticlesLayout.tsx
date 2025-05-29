'use client'

import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'
import Link from '@/components/Link'
import ArticlesSidebar from '@/components/ArticlesSidebar'
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
    <div className="flex items-center justify-between border-t border-gray-200 pt-8 dark:border-gray-700">
      <div className="flex w-0 flex-1 justify-start">
        {prevPage ? (
          <Link
            href={currentPage - 1 === 1 ? basePath : `${basePath}/page/${currentPage - 1}`}
            className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <svg className="mr-3 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
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
        <span className="text-sm text-gray-700 dark:text-gray-300">
          Página <span className="font-medium">{currentPage}</span> de{' '}
          <span className="font-medium">{totalPages}</span>
        </span>
      </div>

      <div className="flex w-0 flex-1 justify-end">
        {nextPage ? (
          <Link
            href={`${basePath}/page/${currentPage + 1}`}
            className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Siguiente
            <svg className="ml-3 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
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

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 xl:px-0">
      <div className="flex gap-8">
        {/* Sidebar - Consistente en todas las vistas */}
        <ArticlesSidebar />

        {/* Main Content */}
        <main className="min-w-0 flex-1">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-5xl md:leading-14 dark:text-gray-100">
              {title}
            </h1>
            {section && (
              <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">
                {section === 'tactical-structures' &&
                  'Análisis de sistemas, fases y principios del juego moderno.'}
                {section === 'scouting' &&
                  'Identificación de perfiles por función táctica mediante datos.'}
                {section === 'tactical-metrics-lab' &&
                  'Cuantificación avanzada del impacto táctico mediante datos y programación.'}
              </p>
            )}
          </div>

          {/* Empty State */}
          {!displayPosts.length && (
            <div className="py-16 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
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
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-gray-100">
                Próximamente
              </h3>
              <p className="mt-2 text-gray-500 dark:text-gray-400">
                {section
                  ? `Los análisis de ${section.replace('-', ' ')} estarán disponibles pronto.`
                  : 'Los primeros análisis estarán disponibles pronto.'}
              </p>
            </div>
          )}

          {/* Articles Grid - Single Column, max 4 per page */}
          {displayPosts.length > 0 && (
            <div className="space-y-6">
              {displayPosts.map((post) => (
                <ArticleCard key={post.slug} post={post} />
              ))}
            </div>
          )}

          {/* Pagination - Solo si hay más de 1 página */}
          {pagination && pagination.totalPages > 1 && (
            <div className="mt-12">
              <Pagination
                currentPage={pagination.currentPage}
                totalPages={pagination.totalPages}
                basePath={section ? `/blog/${section}` : '/blog'}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
