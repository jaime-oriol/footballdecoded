'use client'

import { useState } from 'react'

interface CommentFormProps {
  postSlug: string
  onCommentAdded?: () => void
}

export default function CommentForm({ postSlug, onCommentAdded }: CommentFormProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    try {
      const response = await fetch(`/api/comments/${postSlug}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, message }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        // Limpiar formulario
        setName('')
        setEmail('')
        setMessage('')

        // Notificar al componente padre que se añadió un comentario
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

  return (
    <div className="mt-8">
      <h3 className="mb-6 text-xl font-bold text-gray-900 dark:text-gray-100">
        Deja tu comentario
      </h3>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Nombre y Email en una fila */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="comment-name"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Nombre *
            </label>
            <input
              id="comment-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={status === 'loading'}
              className="focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 shadow-sm disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              placeholder="Tu nombre"
            />
          </div>

          <div>
            <label
              htmlFor="comment-email"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Email *
            </label>
            <input
              id="comment-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={status === 'loading'}
              className="focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 shadow-sm disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              placeholder="tu@email.com"
            />
          </div>
        </div>

        {/* Mensaje */}
        <div>
          <label
            htmlFor="comment-message"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Comentario *
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
            minLength={10}
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Mínimo 10 caracteres. Tu email no será publicado.
          </p>
        </div>

        {/* Botón de envío */}
        <div>
          <button
            type="submit"
            disabled={status === 'loading' || !name || !email || !message}
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

      {/* Información adicional */}
      <div className="mt-6 rounded-md bg-gray-50 p-4 dark:bg-gray-800/50">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Los comentarios se publican automáticamente. Por favor, mantén un tono constructivo y
              relacionado con el análisis táctico.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
