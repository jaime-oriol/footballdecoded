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
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300'
    case 'scouting':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
    case 'tactical-metrics-lab':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
  }
}

export default function ArticleCard({ post }: ArticleCardProps) {
  const { slug, date, title, section, image } = post
  const displayImage = image || '/static/images/default-article.jpg'

  return (
    <article className="group relative overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-all duration-200 hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <Link href={`/blog/${slug}`} className="block">
        {/* Imagen más pequeña - reducida a aspect-[16/8] */}
        <div className="relative aspect-[16/8] overflow-hidden">
          <Image
            src={displayImage}
            alt={title}
            fill
            className="object-cover transition-transform duration-200 group-hover:scale-105"
          />
          {/* Overlay gradient sutil */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
        </div>

        {/* Content */}
        <div className="p-5">
          {/* Fecha y Sección - Layout mejorado */}
          <div className="mb-3 flex items-center justify-between">
            <time 
              dateTime={date}
              className="text-sm text-gray-500 dark:text-gray-400"
            >
              {formatDate(date, siteMetadata.locale)}
            </time>
            
            {/* Solo UNA sección principal como pill */}
            {section && (
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getSectionColor(section)}`}>
                {getSectionLabel(section)}
              </span>
            )}
          </div>

          {/* Título - Sin tags múltiples debajo */}
          <h2 className="mb-4 text-lg font-bold leading-tight text-gray-900 transition-colors group-hover:text-primary-600 dark:text-gray-100 dark:group-hover:text-primary-400 line-clamp-2">
            {title}
          </h2>

          {/* Botón "Leer más" - Mejorado */}
          <div className="flex items-center justify-between">
            <div className="flex items-center text-sm font-medium text-primary-600 transition-colors group-hover:text-primary-500 dark:text-primary-400 dark:group-hover:text-primary-300">
              <span>Leer más</span>
              <svg 
                className="ml-1 h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" 
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
            
            {/* Tiempo de lectura estimado */}
            <span className="text-xs text-gray-400 dark:text-gray-500">
              ~3 min
            </span>
          </div>
        </div>
      </Link>
    </article>
  )
}