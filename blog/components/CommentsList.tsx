'use client'

import { useState, useEffect } from 'react'
import { formatDate } from 'pliny/utils/formatDate'
import siteMetadata from '@/content/siteMetadata'

interface Comment {
  id: string
  name: string
  message: string
  timestamp: string
}

interface CommentsListProps {
  postSlug: string
  refreshTrigger?: number // Para refrescar cuando se añade nuevo comentario
}

export default function CommentsList({ postSlug, refreshTrigger }: CommentsListProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchComments = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await fetch(`/api/comments/${postSlug}`)
      const data = await response.json()

      if (response.ok) {
        setComments(data.comments || [])
      } else {
        setError('Error cargando comentarios')
      }
    } catch (error) {
      setError('Error de conexión')
      console.error('Error fetching comments:', error)
    } finally {
      setLoading(false)
    }
  }

  // Cargar comentarios al montar el componente
  useEffect(() => {
    fetchComments()
  }, [postSlug])

  // Refrescar cuando se añade un nuevo comentario
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      fetchComments()
    }
  }, [refreshTrigger])

  // Función para formatear fecha relativa
  const getTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) {
      return 'Hace menos de una hora'
    } else if (diffInHours < 24) {
      return `Hace ${diffInHours} ${diffInHours === 1 ? 'hora' : 'horas'}`
    } else if (diffInHours < 48) {
      return 'Ayer'
    } else {
      return formatDate(timestamp, siteMetadata.locale)
    }
  }

  // Función para obtener iniciales del nombre
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  if (loading) {
    return (
      <div className="mt-8">
        <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
          Comentarios
        </h3>
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2 text-gray-500">
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span>Cargando comentarios...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-8">
        <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
          Comentarios
        </h3>
        <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <p className="ml-2 text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-8">
      <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
        {comments.length > 0 
          ? `Comentarios (${comments.length})` 
          : 'Comentarios'
        }
      </h3>

      {comments.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center dark:border-gray-600">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <h4 className="mt-4 text-lg font-medium text-gray-900 dark:text-gray-100">
            Sé el primero en comentar
          </h4>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            ¿Qué opinas sobre este análisis? Tu perspectiva es valiosa.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-start space-x-4">
                {/* Avatar con iniciales */}
                <div className="flex-shrink-0">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                    {getInitials(comment.name)}
                  </div>
                </div>

                {/* Contenido del comentario */}
                <div className="min-w-0 flex-1">
                  {/* Header: nombre y fecha */}
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {comment.name}
                    </h4>
                    <time
                      dateTime={comment.timestamp}
                      className="text-sm text-gray-500 dark:text-gray-400"
                      title={formatDate(comment.timestamp, siteMetadata.locale)}
                    >
                      {getTimeAgo(comment.timestamp)}
                    </time>
                  </div>

                  {/* Mensaje del comentario */}
                  <div className="mt-3">
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                      {comment.message}
                    </p>
                  </div>

                  {/* Acciones del comentario (futuro: responder, etc.) */}
                  <div className="mt-4 flex items-center space-x-4">
                    <button
                      type="button"
                      className="flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    >
                      <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                        />
                      </svg>
                      Me gusta
                    </button>
                    <button
                      type="button"
                      className="flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    >
                      <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                        />
                      </svg>
                      Responder
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}