'use client'

import { useState } from 'react'
import Link from '@/components/Link'

const ArticleDropdown = () => {
  const [isOpen, setIsOpen] = useState(false)

  const sections = [
    {
      href: '/blog',
      title: 'Todos los artículos',
      description: 'Vista completa',
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14-7l-7 7-7-7m14 18l-7-7-7 7" />
        </svg>
      )
    },
    {
      href: '/blog/tactical-structures',
      title: 'Tactical Structures',
      description: 'Análisis de sistemas, fases y principios del juego moderno.',
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      href: '/blog/scouting',
      title: 'Scouting',
      description: 'Identificación de perfiles por función táctica mediante datos.',
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      )
    },
    {
      href: '/blog/tactical-metrics-lab',
      title: 'Tactical Metrics Lab',
      description: 'Cuantificación avanzada del impacto táctico mediante datos y programación.',
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    }
  ]

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
      {isOpen && (
        <div className="absolute top-full left-1/2 z-50 mt-2 w-80 -translate-x-1/2 transform">
          {/* Arrow pointer */}
          <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-white border-l border-t border-gray-200 dark:bg-gray-800 dark:border-gray-700"></div>
          
          {/* Menu content */}
          <div className="rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            <div className="p-2">
              {sections.map((section, index) => (
                <Link
                  key={section.href}
                  href={section.href}
                  className="flex items-start rounded-md p-3 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <div className="text-primary-500 dark:text-primary-400 mr-3 mt-0.5 flex-shrink-0">
                    {section.icon}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {section.title}
                    </div>
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                      {section.description}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ArticleDropdown