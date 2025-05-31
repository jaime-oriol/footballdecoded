'use client'

// layouts/PostLayout.tsx
import { ReactNode, useState } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import Comments from '@/components/Comments'
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
      case 'tactical-structures':
        return 'Tactical Structures'
      case 'scouting':
        return 'Scouting'
      case 'tactical-metrics-lab':
        return 'Tactical Metrics Lab'
      default:
        return 'Análisis'
    }
  }

  return (
    <>
      <ScrollTopAndComment />

      {/* Botón Volver a Artículos - SIEMPRE va a /blog */}
      <div className="mb-8">
        <Link
          href="/blog"
          className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 inline-flex items-center text-sm font-medium transition-colors"
        >
          <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
          Volver a artículos
        </Link>
      </div>

      <article>
        <div>
          {/* Banner de imagen de cabecera */}
          <header className="relative mb-8">
            <div className="relative aspect-[21/9] overflow-hidden rounded-lg">
              <Image src={displayImage} alt={title} fill className="object-cover" priority />
              {/* Overlay gradient para mejorar legibilidad */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />

              {/* Contenido sobre la imagen */}
              <div className="absolute right-0 bottom-0 left-0 p-8">
                <div className="mx-auto max-w-4xl">
                  {/* Sección */}
                  {section && (
                    <div className="mb-4">
                      <span className="inline-flex items-center rounded-full bg-white/20 px-3 py-1 text-sm font-medium text-white backdrop-blur-sm">
                        {getSectionLabel(section)}
                      </span>
                    </div>
                  )}

                  {/* Título */}
                  <h1 className="text-3xl leading-tight font-extrabold tracking-tight text-white sm:text-4xl md:text-5xl lg:text-6xl">
                    {title}
                  </h1>

                  {/* Fecha */}
                  <div className="mt-4">
                    <time dateTime={date} className="text-lg text-white/90">
                      {new Date(date).toLocaleDateString(siteMetadata.locale, postDateTemplate)}
                    </time>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Contenido del artículo */}
          <div className="mx-auto max-w-4xl">
            <div className="prose prose-lg dark:prose-invert max-w-none">{children}</div>

            {/* Información del autor */}
            {authorDetails.length > 0 && (
              <div className="mt-12 border-t border-gray-200 pt-8 dark:border-gray-700">
                <div className="flex items-center">
                  {authorDetails.map((author) => (
                    <div key={author.name} className="flex items-center">
                      {author.avatar && (
                        <Image
                          src={author.avatar}
                          width={48}
                          height={48}
                          alt="avatar"
                          className="mr-4 h-12 w-12 rounded-full"
                        />
                      )}
                      <div>
                        <div className="text-lg font-medium text-gray-900 dark:text-gray-100">
                          {author.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {author.occupation}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sistema de comentarios personalizado */}
            <div className="mt-12 border-t border-gray-200 pt-8 dark:border-gray-700">
              {/* Lista de comentarios existentes */}
              <CommentsList postSlug={slug} refreshTrigger={refreshComments} />

              {/* Formulario para nuevos comentarios */}
              <CommentForm postSlug={slug} onCommentAdded={handleCommentAdded} />
            </div>

            {/* Comentarios Giscus (comentado por ahora) */}
            {/* {siteMetadata.comments && (
              <div
                className="mt-12 border-t border-gray-200 pt-8 dark:border-gray-700"
                id="comment"
              >
                <Comments slug={slug} />
              </div>
            )} */}

            {/* Navegación entre artículos - CORREGIDO */}
            {(prev || next) && (
              <div className="mt-12 border-t border-gray-200 pt-8 dark:border-gray-700">
                <div className="flex justify-between">
                  {prev && (
                    <div className="w-1/2 pr-4">
                      <p className="mb-2 text-sm font-medium text-gray-500 uppercase dark:text-gray-400">
                        Artículo anterior
                      </p>
                      <Link
                        href={`/blog/${prev.slug}`}
                        className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 block text-lg font-medium transition-colors"
                      >
                        {prev.title}
                      </Link>
                    </div>
                  )}

                  {next && (
                    <div className="w-1/2 pl-4 text-right">
                      <p className="mb-2 text-sm font-medium text-gray-500 uppercase dark:text-gray-400">
                        Siguiente artículo
                      </p>
                      <Link
                        href={`/blog/${next.slug}`}
                        className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 block text-lg font-medium transition-colors"
                      >
                        {next.title}
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Botón final para volver */}
            <div className="mt-12 text-center">
              <Link
                href="/blog"
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-6 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
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
    </>
  )
}
