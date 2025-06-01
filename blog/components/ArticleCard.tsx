import { formatDate } from 'pliny/utils/formatDate'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'
import Link from '@/components/Link'
import Image from '@/components/Image'
import siteMetadata from '@/content/siteMetadata'

interface ArticleCardProps {
  post: CoreContent<Blog>
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

const getSectionColor = (section: string) => {
  switch (section) {
    case 'tactical-structures':
      return 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-200'
    case 'scouting':
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200'
    case 'tactical-metrics-lab':
      return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200'
    default:
      return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
  }
}

export default function ArticleCard({ post }: ArticleCardProps) {
  const { slug, date, title, section, image, summary } = post
  const displayImage = image || '/static/images/default-article.jpg'

  return (
    <article className="group overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all duration-200 hover:shadow-md dark:border-slate-700 dark:bg-slate-800">
      <Link href={`/blog/${slug}`} className="flex items-stretch">
        {/* Imagen a la izquierda - optimizada para lectura técnica */}
        <div className="relative w-64 flex-shrink-0 overflow-hidden">
          <div className="absolute inset-0">
            <Image
              src={displayImage}
              alt={title}
              fill
              className="object-cover transition-transform duration-200 group-hover:scale-105"
            />
            {/* Overlay sutil para mejor contraste */}
            <div className="absolute inset-0 bg-gradient-to-r from-black/5 to-transparent opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
          </div>
        </div>

        {/* Contenido principal - tipografía FootballDecoded */}
        <div className="min-w-0 flex-1 space-y-4 p-6">
          {/* Badge de sección con colores semánticos */}
          {section && (
            <div>
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 font-mono text-sm font-medium ${getSectionColor(section)}`}
              >
                {getSectionLabel(section)}
              </span>
            </div>
          )}

          {/* Título con Inter, optimizado para scan reading */}
          <h3 className="font-headings text-xl leading-tight font-semibold tracking-tight text-slate-900 transition-colors group-hover:text-sky-700 lg:text-2xl dark:text-slate-100 dark:group-hover:text-sky-400">
            {title}
          </h3>

          {/* Summary/descripción si existe */}
          {summary && (
            <p className="font-body line-clamp-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
              {summary}
            </p>
          )}

          {/* Footer con CTA y fecha */}
          <div className="flex items-center justify-between pt-2">
            {/* CTA - lenguaje directo para profesionales */}
            <div className="flex items-center text-sm font-medium text-sky-700 transition-all duration-200 group-hover:text-sky-600 dark:text-sky-400 dark:group-hover:text-sky-300">
              <span className="font-body">Leer análisis</span>
              <svg
                className="ml-2 h-4 w-4 transition-transform duration-200 group-hover:translate-x-1"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </div>

            {/* Fecha con formato monospace para consistencia */}
            <time
              dateTime={date}
              className="flex-shrink-0 font-mono text-sm text-slate-500 dark:text-slate-400"
            >
              {formatDate(date, siteMetadata.locale)}
            </time>
          </div>
        </div>
      </Link>
    </article>
  )
}
