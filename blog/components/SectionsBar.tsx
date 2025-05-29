'use client'

import Link from '@/components/Link'
import { usePathname } from 'next/navigation'

const SectionsBar = () => {
  const pathname = usePathname()

  // Las 4 secciones oficiales con descripciones optimizadas
  const sections = [
    {
      href: '/blog',
      title: 'Todos los artículos',
      description: 'Vista completa de análisis',
    },
    {
      href: '/blog/tactical-structures',
      title: 'Tactical Structures',
      description: 'Análisis estructural del juego moderno',
    },
    {
      href: '/blog/scouting',
      title: 'Scouting',
      description: 'Perfiles funcionales y tácticos por rol',
    },
    {
      href: '/blog/tactical-metrics-lab',
      title: 'Tactical Metrics Lab',
      description: 'Métricas aplicadas al rendimiento colectivo e individual',
    },
  ]

  return (
    <div className="w-full border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-950">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 xl:px-0">
        {/* Barra de secciones */}
        <nav className="flex space-x-8 overflow-x-auto scrollbar-hide" aria-label="Secciones">
          {sections.map((section) => {
            const isActive = pathname === section.href

            return (
              <Link
                key={section.href}
                href={section.href}
                className={`group relative flex min-w-0 flex-col py-4 text-center transition-colors duration-200 ${
                  isActive
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                {/* Título de la sección - sin descripción */}
                <span className="whitespace-nowrap text-sm font-semibold lg:text-base">
                  {section.title}
                </span>

                {/* Indicador activo - línea inferior */}
                <div
                  className={`absolute bottom-0 left-0 right-0 h-0.5 rounded-full transition-all duration-200 ${
                    isActive
                      ? 'bg-primary-500 opacity-100'
                      : 'bg-transparent opacity-0 group-hover:bg-gray-300 group-hover:opacity-50 dark:group-hover:bg-gray-600'
                  }`}
                />
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}

export default SectionsBar