'use client'

import { useState } from 'react'
import Link from '@/components/Link'
import { usePathname } from 'next/navigation'

interface Section {
  href: string
  title: string
  description: string
  icon: React.ReactNode
}

const sections: Section[] = [
  {
    href: '/blog',
    title: 'Todos los artículos',
    description: 'Vista completa de análisis',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 11H5m14-7l-7 7-7-7m14 18l-7-7-7 7"
        />
      </svg>
    ),
  },
  {
    href: '/blog/tactical-structures',
    title: 'Tactical Structures',
    description: 'Análisis estructural del juego moderno',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
        />
      </svg>
    ),
  },
  {
    href: '/blog/scouting',
    title: 'Scouting',
    description: 'Perfiles funcionales y tácticos por rol',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
    ),
  },
  {
    href: '/blog/tactical-metrics-lab',
    title: 'Tactical Metrics Lab',
    description: 'Métricas aplicadas al rendimiento colectivo e individual',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
    ),
  },
]

interface SectionsNavigationProps {
  variant: 'dropdown' | 'bar' | 'sidebar'
}

export default function SectionsNavigation({ variant }: SectionsNavigationProps) {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  if (variant === 'dropdown') {
    return (
      <div
        className="relative"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
      >
        {/* Trigger Button */}
        <button className="hover:text-primary-500 dark:hover:text-primary-400 flex items-center font-medium text-gray-900 dark:text-gray-100">
          Artículos
          <svg
            className={`ml-1 h-4 w-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        <div
          className={`absolute top-full left-1/2 mt-2 w-auto -translate-x-1/2 transform transition-all duration-200 ${
            isOpen
              ? 'visible z-[9999] translate-y-0 opacity-100'
              : 'invisible z-[-1] -translate-y-2 opacity-0'
          }`}
          style={{ zIndex: isOpen ? 9999 : -1 }}
        >
          {/* Arrow pointer */}
          <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-t border-l border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"></div>

          {/* Menu content */}
          <div className="rounded-lg border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-800">
            <div className="p-3">
              <div className="flex space-x-2">
                {sections.map((section) => (
                  <Link
                    key={section.href}
                    href={section.href}
                    className="flex min-w-[140px] flex-col items-center rounded-md p-3 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <div className="text-primary-500 dark:text-primary-400 mb-2 flex-shrink-0">
                      {section.icon}
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {section.title}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (variant === 'bar') {
    return (
      <div className="w-full border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-950">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 xl:px-0">
          <nav className="scrollbar-hide flex space-x-8 overflow-x-auto" aria-label="Secciones">
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
                  <span className="text-sm font-semibold whitespace-nowrap lg:text-base">
                    {section.title}
                  </span>
                  <div
                    className={`absolute right-0 bottom-0 left-0 h-0.5 rounded-full transition-all duration-200 ${
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

  // variant === 'sidebar'
  return (
    <aside className="w-64 flex-shrink-0">
      <div className="sticky top-24 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h3 className="mb-6 text-lg font-semibold text-gray-900 dark:text-gray-100">Secciones</h3>
        <nav className="space-y-2">
          {sections.map((section) => {
            const isActive = pathname === section.href
            return (
              <Link
                key={section.href}
                href={section.href}
                className={`group flex items-start rounded-lg px-3 py-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50'
                }`}
              >
                <div
                  className={`mt-0.5 mr-3 flex-shrink-0 ${isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}`}
                >
                  {section.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">{section.title}</div>
                  <div className="mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                    {section.description}
                  </div>
                </div>
              </Link>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}
