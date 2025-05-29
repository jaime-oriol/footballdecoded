'use client'

import Link from '@/components/Link'
import { usePathname } from 'next/navigation'

const ArticlesSidebar = () => {
  const pathname = usePathname()

  const sections = [
    {
      href: '/blog',
      title: 'Todos los artículos',
      count: 0, // Se actualizará dinámicamente
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14-7l-7 7-7-7m14 18l-7-7-7 7" />
        </svg>
      )
    },
    {
      href: '/blog/tactical-structures',
      title: 'Tactical Structures',
      subtitle: 'Sistemas y principios',
      count: 0,
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      )
    },
    {
      href: '/blog/scouting',
      title: 'Scouting',
      subtitle: 'Perfiles funcionales',
      count: 0,
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      )
    },
    {
      href: '/blog/tactical-metrics-lab',
      title: 'Tactical Metrics Lab',
      subtitle: 'Métricas avanzadas',
      count: 0,
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      )
    }
  ]

  return (
    <aside className="w-64 flex-shrink-0">
      <div className="sticky top-24 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          Secciones
        </h3>
        
        <nav className="space-y-1">
          {sections.map((section) => {
            const isActive = pathname === section.href
            
            return (
              <Link
                key={section.href}
                href={section.href}
                className={`flex items-center rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50'
                }`}
              >
                <div className={`mr-3 ${isActive ? 'text-primary-500' : 'text-gray-400'}`}>
                  {section.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">
                    {section.title}
                  </div>
                  {section.subtitle && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {section.subtitle}
                    </div>
                  )}
                </div>
                {section.count > 0 && (
                  <span className={`ml-2 inline-flex items-center justify-center px-2 py-1 text-xs font-medium rounded-full ${
                    isActive
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-800 dark:text-primary-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                  }`}>
                    {section.count}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Información adicional */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p className="mb-2">
              <strong>Tactical Structures:</strong> Análisis de sistemas, fases y principios del juego moderno.
            </p>
            <p className="mb-2">
              <strong>Scouting:</strong> Identificación de perfiles por función táctica mediante datos.
            </p>
            <p>
              <strong>Metrics Lab:</strong> Cuantificación avanzada del impacto táctico.
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default ArticlesSidebar