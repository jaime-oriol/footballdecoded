import React from 'react'
import TOCInline from 'pliny/ui/TOCInline'
import Pre from 'pliny/ui/Pre'
import BlogNewsletterForm from 'pliny/ui/BlogNewsletterForm'
import type { MDXComponents } from 'mdx/types'
import Image from './Image'
import CustomLink from './Link'

// Table wrapper con diseño profesional
const TableWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
    <table className="w-full border-collapse bg-white dark:bg-slate-800">{children}</table>
  </div>
)

// Componente para destacar conceptos técnicos
const TechnicalConcept = ({
  children,
  type = 'default',
}: {
  children: React.ReactNode
  type?: 'metric' | 'role' | 'system' | 'default'
}) => {
  const getStyles = (type: string) => {
    switch (type) {
      case 'metric':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200 font-mono'
      case 'role':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200'
      case 'system':
        return 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-200'
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
    }
  }

  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-sm font-medium ${getStyles(type)}`}
    >
      {children}
    </span>
  )
}

// Callout para notas importantes
const Callout = ({
  children,
  type = 'info',
}: {
  children: React.ReactNode
  type?: 'info' | 'warning' | 'success' | 'insight'
}) => {
  const getStyles = (type: string) => {
    switch (type) {
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-700/50 dark:bg-yellow-900/20 dark:text-yellow-200'
      case 'success':
        return 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-700/50 dark:bg-emerald-900/20 dark:text-emerald-200'
      case 'insight':
        return 'border-indigo-200 bg-indigo-50 text-indigo-800 dark:border-indigo-700/50 dark:bg-indigo-900/20 dark:text-indigo-200'
      default:
        return 'border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-700/50 dark:bg-sky-900/20 dark:text-sky-200'
    }
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return '⚠️'
      case 'success':
        return '✅'
      case 'insight':
        return '💡'
      default:
        return 'ℹ️'
    }
  }

  return (
    <div className={`rounded-lg border p-4 ${getStyles(type)}`}>
      <div className="flex items-start space-x-3">
        <span className="text-lg">{getIcon(type)}</span>
        <div className="font-body leading-relaxed">{children}</div>
      </div>
    </div>
  )
}

// Stat card para métricas
const StatCard = ({
  title,
  value,
  description,
  trend,
}: {
  title: string
  value: string
  description?: string
  trend?: 'up' | 'down' | 'neutral'
}) => {
  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <span className="text-emerald-500">↗️</span>
      case 'down':
        return <span className="text-red-500">↘️</span>
      default:
        return null
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-center justify-between">
        <h3 className="font-body text-sm font-medium text-slate-600 dark:text-slate-400">
          {title}
        </h3>
        {getTrendIcon(trend)}
      </div>
      <div className="mt-2 flex items-baseline">
        <span className="font-mono text-2xl font-semibold text-slate-900 dark:text-slate-100">
          {value}
        </span>
      </div>
      {description && (
        <p className="font-body mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>
      )}
    </div>
  )
}

// Quote personalizado para citas técnicas
const TechnicalQuote = ({ children, source }: { children: React.ReactNode; source?: string }) => (
  <blockquote className="border-l-4 border-slate-300 bg-slate-50 py-4 pr-4 pl-6 italic dark:border-slate-600 dark:bg-slate-800/50">
    <div className="font-body text-lg leading-relaxed text-slate-700 dark:text-slate-300">
      {children}
    </div>
    {source && (
      <cite className="font-body mt-2 block text-sm text-slate-500 dark:text-slate-400">
        — {source}
      </cite>
    )}
  </blockquote>
)

// Función helper para verificar si hay contenido válido
const hasValidContent = (children: React.ReactNode): boolean => {
  if (!children) return false
  if (typeof children === 'string') {
    return children.trim().length > 0
  }
  if (React.isValidElement(children)) {
    return true
  }
  if (Array.isArray(children)) {
    return children.some((child) => hasValidContent(child))
  }
  return true
}

export const components: MDXComponents = {
  // Componentes base
  Image,
  TOCInline,
  a: CustomLink,
  pre: Pre,
  table: TableWrapper,
  BlogNewsletterForm,

  // Componentes personalizados FootballDecoded
  TechnicalConcept,
  Callout,
  StatCard,
  TechnicalQuote,

  // Headings con verificación de contenido y accesibilidad
  h1: (props) => {
    // Solo renderizar si hay contenido válido
    if (!hasValidContent(props.children)) {
      return null
    }
    return (
      // eslint-disable-next-line jsx-a11y/heading-has-content
      <h1
        className="font-headings mt-8 mb-4 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100"
        {...props}
      />
    )
  },

  h2: (props) => {
    // Solo renderizar si hay contenido válido
    if (!hasValidContent(props.children)) {
      return null
    }
    return (
      // eslint-disable-next-line jsx-a11y/heading-has-content
      <h2
        className="font-headings mt-8 mb-4 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100"
        {...props}
      />
    )
  },

  h3: (props) => {
    // Solo renderizar si hay contenido válido
    if (!hasValidContent(props.children)) {
      return null
    }
    return (
      // eslint-disable-next-line jsx-a11y/heading-has-content
      <h3
        className="font-headings mt-6 mb-3 text-xl font-semibold text-slate-900 dark:text-slate-100"
        {...props}
      />
    )
  },

  // Párrafos optimizados
  p: (props) => (
    <p className="font-body mb-4 leading-relaxed text-slate-700 dark:text-slate-300" {...props} />
  ),

  // Listas con mejor espaciado
  ul: (props) => (
    <ul className="font-body space-y-2 text-slate-700 dark:text-slate-300" {...props} />
  ),
  ol: (props) => (
    <ol className="font-body space-y-2 text-slate-700 dark:text-slate-300" {...props} />
  ),

  // Código inline con monospace
  code: (props) => (
    <code
      className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-sm text-slate-900 dark:bg-slate-800 dark:text-slate-100"
      {...props}
    />
  ),

  // Strong/emphasis con colores semánticos
  strong: (props) => (
    <strong className="font-semibold text-slate-900 dark:text-slate-100" {...props} />
  ),
  em: (props) => <em className="text-slate-600 italic dark:text-slate-400" {...props} />,
}
