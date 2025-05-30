// app/newsletter/confirm/page.tsx
'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from '@/components/Link'

function ConfirmContent() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'invalid'>('loading')
  const [message, setMessage] = useState('')
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  useEffect(() => {
    const confirmSubscription = async () => {
      if (!token) {
        setStatus('invalid')
        setMessage('Token de confirmación no válido')
        return
      }

      try {
        const response = await fetch(`/api/newsletter/confirm?token=${token}`)
        const data = await response.json()

        if (response.ok) {
          setStatus('success')
          setMessage(data.message || '¡Suscripción confirmada correctamente!')
        } else {
          setStatus('error')
          setMessage(data.error || 'Error al confirmar la suscripción')
        }
      } catch (error) {
        setStatus('error')
        setMessage('Error de conexión al confirmar la suscripción')
      }
    }

    confirmSubscription()
  }, [token])

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 xl:max-w-5xl xl:px-0">
      <div className="text-center">
        {/* Loading */}
        {status === 'loading' && (
          <div className="space-y-4">
            <div className="border-primary-200 border-t-primary-600 mx-auto h-12 w-12 animate-spin rounded-full border-4"></div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Confirmando suscripción...
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Por favor espera mientras procesamos tu confirmación.
            </p>
          </div>
        )}

        {/* Success */}
        {status === 'success' && (
          <div className="space-y-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
              <svg className="h-8 w-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>

            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                ¡Suscripción confirmada!
              </h1>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
                Perfecto, ya formas parte de la comunidad FootballDecoded.
              </p>
            </div>

            <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-6">
              <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">
                ¿Qué viene ahora?
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Cada <strong>lunes por la mañana</strong> recibirás las 5 noticias más importantes
                del mundo del fútbol, contadas con criterio y con mi análisis personal.
              </p>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/"
                className="bg-primary-600 hover:bg-primary-700 inline-flex items-center justify-center rounded-lg px-6 py-3 text-base font-medium text-white transition-colors"
              >
                Explorar el blog
              </Link>
              <Link
                href="/newsletter"
                className="inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white px-6 py-3 text-base font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Saber más sobre la newsletter
              </Link>
            </div>
          </div>
        )}

        {/* Error */}
        {status === 'error' && (
          <div className="space-y-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <svg className="h-8 w-8 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>

            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Error al confirmar
              </h1>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">{message}</p>
            </div>

            <div className="rounded-lg bg-yellow-50 p-6 dark:bg-yellow-900/20">
              <p className="text-yellow-800 dark:text-yellow-200">
                Si el problema persiste, puedes contactarme en{' '}
                <a href="mailto:newsletter@footballdecoded.com" className="underline">
                  newsletter@footballdecoded.com
                </a>
              </p>
            </div>

            <Link
              href="/newsletter"
              className="bg-primary-600 hover:bg-primary-700 inline-flex items-center justify-center rounded-lg px-6 py-3 text-base font-medium text-white transition-colors"
            >
              Volver a la newsletter
            </Link>
          </div>
        )}

        {/* Invalid Token */}
        {status === 'invalid' && (
          <div className="space-y-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/20">
              <svg className="h-8 w-8 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>

            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Enlace no válido
              </h1>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
                Este enlace de confirmación no es válido o ha expirado.
              </p>
            </div>

            <Link
              href="/newsletter"
              className="bg-primary-600 hover:bg-primary-700 inline-flex items-center justify-center rounded-lg px-6 py-3 text-base font-medium text-white transition-colors"
            >
              Suscribirse de nuevo
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default function NewsletterConfirmPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 xl:max-w-5xl xl:px-0">
          <div className="text-center">
            <div className="border-primary-200 border-t-primary-600 mx-auto h-12 w-12 animate-spin rounded-full border-4"></div>
            <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
              Cargando...
            </h1>
          </div>
        </div>
      }
    >
      <ConfirmContent />
    </Suspense>
  )
}
