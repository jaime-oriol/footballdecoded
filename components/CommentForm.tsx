'use client'

import { useState } from 'react'
import { useSession, signIn } from 'next-auth/react'
import Image from '@/components/Image'

interface CommentFormProps {
  postSlug: string
  onCommentAdded?: () => void
}

export default function CommentForm({ postSlug, onCommentAdded }: CommentFormProps) {
  const { data: session } = useSession()
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!session) {
      signIn('google')
      return
    }

    setStatus('loading')
    setErrorMessage('')

    try {
      const response = await fetch(`/api/comments/${postSlug}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: session.user?.name || 'Usuario',
          email: session.user?.email || '',
          message,
          avatar: session.user?.image || '',
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage('')

        if (onCommentAdded) {
          onCommentAdded()
        }
      } else {
        setStatus('error')
        setErrorMessage(data.error || 'Error al enviar el comentario')
      }
    } catch (error) {
      setStatus('error')
      setErrorMessage('Error de conexión. Inténtalo de nuevo.')
    }
  }

  // Si no está logueado, mostrar botón de login
  if (!session) {
    return (
      <div className="mt-8">
        <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
          Deja tu comentario
        </h3>

        <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center dark:border-gray-700 dark:bg-gray-800/50">
          <svg
            className="mx-auto mb-4 h-12 w-12 text-gray-400"
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

          <h4 className="mb-2 text-lg font-medium text-gray-900 dark:text-gray-100">
            Inicia sesión para comentar
          </h4>
          <p className="mb-4 text-gray-600 dark:text-gray-400">
            Usa tu cuenta de Google para comentar de forma rápida y segura
          </p>

          <button
            onClick={() => signIn('google')}
            className="inline-flex items-center space-x-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span>Iniciar sesión con Google</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-8">
      <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
        Deja tu comentario
      </h3>

      {/* Mostrar usuario logueado */}
      <div className="mb-4 flex items-center space-x-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
        {session.user?.image && (
          <Image
            src={session.user.image}
            alt={session.user.name || 'Usuario'}
            width={40}
            height={40}
            className="rounded-full"
          />
        )}
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Comentando como <strong>{session.user?.name}</strong>
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{session.user?.email}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Solo el mensaje, nombre y email se toman de la sesión */}
        <div>
          <label
            htmlFor="comment-message"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Tu comentario *
          </label>
          <textarea
            id="comment-message"
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
            disabled={status === 'loading'}
            className="focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 shadow-sm disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            placeholder="Comparte tu opinión sobre este análisis..."
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Comparte tu opinión.</p>
        </div>

        {/* Botón de envío */}
        <div>
          <button
            type="submit"
            disabled={status === 'loading' || !message}
            className="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 inline-flex items-center rounded-md px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-gray-800"
          >
            {status === 'loading' ? (
              <>
                <svg className="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
                Enviando...
              </>
            ) : (
              <>
                <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
                Publicar comentario
              </>
            )}
          </button>
        </div>

        {/* Mensajes de estado */}
        {status === 'success' && (
          <div className="rounded-md bg-green-50 p-4 dark:bg-green-900/20">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                  ¡Comentario publicado!
                </h3>
                <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                  Gracias por tu aporte. Tu comentario ya está visible para otros lectores.
                </p>
              </div>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error al enviar
                </h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}
