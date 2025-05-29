import { formatDate } from 'pliny/utils/formatDate'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'
import Link from '@/components/Link'
import Image from '@/components/Image'
import siteMetadata from '@/content/siteMetadata'

interface ArticleCardHomeProps {
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

export default function ArticleCardHome({ post }: ArticleCardHomeProps) {
  const { slug, date, title, section, image } = post
  const displayImage = image || '/static/images/default-article.jpg'

  return (
    <article className="group rounded-lg border border-gray-200 bg-white shadow-sm transition-all duration-200 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
      <Link href={`/blog/${slug}`} className="flex items-stretch">
        {/* Imagen a la izquierda - MÁS GRANDE y pegada a bordes */}
        <div className="relative flex-shrink-0 w-40 overflow-hidden">
          <div className="absolute inset-0">
            <Image
              src={displayImage}
              alt={title}
              fill
              className="object-cover transition-transform duration-200 group-hover:scale-105"
            />
            {/* Subtle overlay en hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-black/5 to-transparent opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
          </div>
        </div>

        {/* Contenido a la derecha */}
        <div className="flex-1 min-w-0 p-5">
          {/* TÍTULO en negrita */}
          <h3 className="text-xl font-bold leading-snug text-gray-900 transition-colors group-hover:text-primary-600 dark:text-gray-100 dark:group-hover:text-primary-400 mb-3 line-clamp-2">
            {title}
          </h3>
          
          {/* SECCIÓN como pill - solo una */}
          {section && (
            <div className="mb-4">
              <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${getSectionColor(section)}`}>
                {getSectionLabel(section)}
              </span>
            </div>
          )}
          
          {/* Layout inferior: BOTÓN a la izquierda, FECHA a la derecha */}
          <div className="flex items-center justify-between">
            {/* LEER ANÁLISIS COMPLETO - siempre debajo, alineado a la izquierda */}
            <div className="flex items-center text-sm font-medium text-primary-600 transition-all duration-200 group-hover:text-primary-500 dark:text-primary-400 dark:group-hover:text-primary-300">
              <span>Leer análisis completo</span>
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
            
            {/* FECHA - abajo a la derecha */}
            <time 
              dateTime={date}
              className="text-sm font-medium text-gray-500 dark:text-gray-400 flex-shrink-0"
            >
              {formatDate(date, siteMetadata.locale)}
            </time>
          </div>
        </div>
      </Link>
    </article>
  )
}