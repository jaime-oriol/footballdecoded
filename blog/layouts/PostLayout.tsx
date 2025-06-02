'use client'

// layouts/PostLayout.tsx
import { ReactNode, useState } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import CommentForm from '@/components/CommentForm'
import CommentsList from '@/components/CommentsList'
import Link from '@/components/Link'
import Image from '@/components/Image'
import siteMetadata from '@/content/siteMetadata'
import ScrollTopAndComment from '@/components/ScrollTopAndComment'

const postDateTemplate: Intl.DateTimeFormatOptions = {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
}

interface LayoutProps {
  content: CoreContent<Blog>
  authorDetails: CoreContent<Authors>[]
  next?: { path: string; title: string; slug: string } | null
  prev?: { path: string; title: string; slug: string } | null
  children: ReactNode
}

export default function PostLayout({ content, authorDetails, next, prev, children }: LayoutProps) {
  const { filePath, path, slug, date, title, image, section } = content
  const displayImage = image || '/static/images/default-article-banner.jpg'

  // Estado para refrescar comentarios cuando se añade uno nuevo
  const [refreshComments, setRefreshComments] = useState(0)

  const handleCommentAdded = () => {
    setRefreshComments((prev) => prev + 1)
  }

  const getSectionLabel = (section: string) => {
    switch (section) {
      case 'tactical-analysis':
        return 'Tactical Analysis'
      case 'tactical-structures': // Backward compatibility
        return 'Tactical Analysis'
      case 'analytical-scouting':
        return 'Analytical Scouting'
      case 'scouting': // Backward compatibility
        return 'Analytical Scouting'
      case 'advanced-metrics':
        return 'Advanced Metrics'
      case 'tactical-metrics-lab': // Backward compatibility
        return 'Advanced Metrics'
      default:
        return 'Análisis'
    }
  }

  const getSectionColor = (section: string) => {
    switch (section) {
      case 'tactical-analysis':
        return 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-200'
      case 'tactical-structures': // Backward compatibility
        return 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-200'
      case 'analytical-scouting':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200'
      case 'scouting': // Backward compatibility
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200'
      case 'advanced-metrics':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200'
      case 'tactical-metrics-lab': // Backward compatibility
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200'
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
    }
  }

  const getSectionHref = (section: string) => {
    switch (section) {
      case 'tactical-analysis':
      case 'tactical-structures': // Redirect legacy to new
        return '/blog/tactical-analysis'
      case 'analytical-scouting':
      case 'scouting': // Redirect legacy to new
        return '/blog/analytical-scouting'
      case 'advanced-metrics':
      case 'tactical-metrics-lab': // Redirect legacy to new
        return '/blog/advanced-metrics'
      default:
        return '/blog'
    }
  }

  return (
    <div className="w-full">
      <ScrollTopAndComment />

      {/* Breadcrumb profesional */}
      <div className="mb-6 px-4 sm:px-6">
        <nav className="font-body flex items-center space-x-2 text-sm text-slate-500 dark:text-slate-400">
          <Link
            href="/"
            className="transition-colors hover:text-slate-700 dark:hover:text-slate-300"
          >
            Inicio
          </Link>
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <Link
            href="/blog"
            className="transition-colors hover:text-slate-700 dark:hover:text-slate-300"
          >
            Artículos
          </Link>
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <Link
            href={getSectionHref(section)}
            className="transition-colors hover:text-slate-700 dark:hover:text-slate-300"
          >
            {getSectionLabel(section)}
          </Link>
        </nav>
      </div>

      <article className="w-full px-4 sm:px-6">
        <div>
          {/* Header del artículo - diseño profesional */}
          <header className="relative mb-10">
            {/* Metadatos del artículo */}
            <div className="mb-6 space-y-4">
              {/* Badge de sección y fecha */}
              <div className="flex items-center justify-between">
                {section && (
                  <Link href={getSectionHref(section)}>
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1.5 font-mono text-sm font-medium transition-colors hover:opacity-80 ${getSectionColor(section)}`}
                    >
                      {getSectionLabel(section)}
                    </span>
                  </Link>
                )}
                <time
                  dateTime={date}
                  className="font-mono text-sm text-slate-500 dark:text-slate-400"
                >
                  {new Date(date).toLocaleDateString(siteMetadata.locale, postDateTemplate)}
                </time>
              </div>

              {/* Título principal */}
              <h1 className="font-headings text-3xl leading-tight font-bold tracking-tight text-slate-900 lg:text-4xl xl:text-5xl dark:text-slate-100">
                {title}
              </h1>
            </div>

            {/* Imagen destacada */}
            {displayImage && (
              <div className="relative mb-8 aspect-[16/9] overflow-hidden rounded-lg">
                <Image src={displayImage} alt={title} fill className="object-cover" priority />
                {/* Overlay sutil para mejor integración */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-transparent" />
              </div>
            )}
          </header>

          {/* Contenido del artículo con prose optimizado - ANCHO COMPLETO */}
          <div className="w-full">
            <div className="prose prose-slate prose-lg dark:prose-invert max-w-none">
              {children}
            </div>

            {/* Información del autor */}
            {authorDetails.length > 0 && (
              <div className="mt-12 border-t border-slate-200 pt-8 dark:border-slate-700">
                <div className="flex items-center space-x-4">
                  {authorDetails.map((author, index) => (
                    <div key={`${author.name}-${index}`} className="flex items-center">
                      {author.avatar && (
                        <Image
                          src={author.avatar}
                          width={56}
                          height={56}
                          alt="avatar"
                          className="mr-4 h-14 w-14 rounded-full"
                        />
                      )}
                      <div>
                        <div className="font-headings text-lg font-semibold text-slate-900 dark:text-slate-100">
                          {author.name}
                        </div>
                        <div className="font-body text-sm text-slate-600 dark:text-slate-400">
                          {author.occupation}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sistema de comentarios personalizado */}
            <div className="mt-12 border-t border-slate-200 pt-8 dark:border-slate-700">
              {/* Lista de comentarios existentes */}
              <CommentsList
                postSlug={slug.split('/').pop() || slug}
                refreshTrigger={refreshComments}
              />

              {/* Formulario para nuevos comentarios */}
              <CommentForm
                postSlug={slug.split('/').pop() || slug}
                onCommentAdded={handleCommentAdded}
              />
            </div>

            {/* Navegación entre artículos */}
            {(prev || next) && (
              <div className="mt-12 border-t border-slate-200 pt-8 dark:border-slate-700">
                <div className="grid gap-6 md:grid-cols-2">
                  {prev && (
                    <div className="group">
                      <p className="mb-2 font-mono text-xs font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
                        Artículo anterior
                      </p>
                      <Link
                        href={`/blog/${prev.slug}`}
                        className="block rounded-lg border border-slate-200 bg-white p-4 transition-all hover:shadow-md dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
                      >
                        <h3 className="font-headings text-lg font-medium text-slate-900 transition-colors group-hover:text-sky-700 dark:text-slate-100 dark:group-hover:text-sky-400">
                          {prev.title}
                        </h3>
                      </Link>
                    </div>
                  )}

                  {next && (
                    <div className="group">
                      <p className="mb-2 font-mono text-xs font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
                        Siguiente artículo
                      </p>
                      <Link
                        href={`/blog/${next.slug}`}
                        className="block rounded-lg border border-slate-200 bg-white p-4 transition-all hover:shadow-md dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
                      >
                        <h3 className="font-headings text-lg font-medium text-slate-900 transition-colors group-hover:text-sky-700 dark:text-slate-100 dark:group-hover:text-sky-400">
                          {next.title}
                        </h3>
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CTA final para volver al blog */}
            <div className="mt-12 text-center">
              <Link
                href="/blog"
                className="font-body inline-flex items-center rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                Volver a todos los artículos
              </Link>
            </div>
          </div>
        </div>
      </article>
    </div>
  )
}
