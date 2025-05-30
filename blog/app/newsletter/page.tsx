import { genPageMetadata } from 'app/seo'
import NewsletterForm from '@/components/NewsletterForm'

export const metadata = genPageMetadata({
  title: 'Newsletter - FootballDecoded Semanal',
  description:
    'Suscríbete y recibe cada lunes las 5 noticias más importantes del mundo del fútbol, contadas con criterio y opinión propia.',
})

export default function Newsletter() {
  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {/* Header compacto */}
        <div className="space-y-2 pt-6 pb-6 md:space-y-5">
          <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14 dark:text-gray-100">
            Newsletter
          </h1>
          <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
            Las 5 noticias más importantes del fútbol cada lunes, contadas con criterio
          </p>
        </div>

        {/* FORMULARIO PRINCIPAL - FULL WIDTH con diseño hero */}
        <div className="pt-8">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-50 via-white to-primary-50/30 dark:from-primary-900/10 dark:via-gray-800 dark:to-primary-900/5">
            {/* Patrón de fondo sutil */}
            <div className="absolute inset-0 opacity-5">
              <svg className="h-full w-full" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <defs>
                  <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                    <circle cx="5" cy="5" r="1" fill="currentColor" />
                  </pattern>
                </defs>
                <rect width="100" height="100" fill="url(#grid)" />
              </svg>
            </div>

            <div className="relative px-6 py-16 sm:px-8 lg:px-12">
              <div className="mx-auto max-w-4xl text-center">
                {/* Icono grande */}
                <div className="mb-8">
                  <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
                    <svg className="h-10 w-10 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>

                {/* Título y descripción principales */}
                <h2 className="mb-4 text-3xl font-bold leading-tight text-gray-900 sm:text-4xl lg:text-5xl dark:text-gray-100">
                  Suscríbete a la newsletter de 
                  <span className="text-primary-600 dark:text-primary-400"> FootballDecoded</span>
                </h2>
                <p className="mb-8 text-xl leading-relaxed text-gray-600 dark:text-gray-400">
                  Cada lunes, en tu correo: <strong>las 5 noticias más importantes del mundo del fútbol</strong>, 
                  contadas con criterio, sin ruido, y con algo de opinión propia.
                </p>

                {/* FORMULARIO DE NEWSLETTER - GRANDE Y CENTRADO */}
                <div className="mb-12">
                  <NewsletterForm className="mx-auto max-w-2xl" />
                </div>

                {/* Stats o testimonial */}
                <div className="flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-x-8 sm:space-y-0">
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <svg className="mr-2 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Sin spam garantizado
                  </div>
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <svg className="mr-2 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Cancela cuando quieras
                  </div>
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <svg className="mr-2 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Solo los lunes
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CONTENIDO INFORMATIVO - dos columnas */}
        <div className="pt-12">
          <div className="mx-auto max-w-6xl">
            <div className="grid gap-8 lg:grid-cols-2">
              
              {/* Columna izquierda - ¿Qué incluye? */}
              <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">
                  ¿Qué puede incluir cada edición?
                </h3>

                <div className="space-y-6">
                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        Resultados y partidos clave
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Lo más importante que pasó en el campo durante el fin de semana, explicado sin exageraciones.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        Movimientos de mercado
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Altas, bajas, rumores potentes y operaciones que podrían cambiar dinámicas.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        Golazos y momentos virales
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Lo que se compartió, lo que generó conversación, y lo que vale la pena volver a ver.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        Una reflexión personal
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Un comentario rápido mío sobre algo que me llamó la atención, siempre relacionado con el juego.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        Recomendaciones de la semana
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Un tuit, un vídeo o un artículo que no te deberías perder.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Columna derecha - Detalles y frecuencia */}
              <div className="space-y-8">
                
                {/* Frecuencia */}
                <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                  <div className="text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
                      <svg className="h-8 w-8 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-gray-100">
                      Periodicidad
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      <strong>Cada lunes por la mañana</strong>
                    </p>
                    <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
                      Perfecto para empezar la semana al día con el fútbol
                    </p>
                  </div>
                </div>

                {/* Ejemplo visual */}
                <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                  <h3 className="mb-4 text-xl font-bold text-gray-900 dark:text-gray-100">
                    ¿Cómo es una edición?
                  </h3>
                  <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-700/50">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <p className="mb-2"><strong>📧 Asunto:</strong> 5 cosas del fútbol (Semana 23)</p>
                      <p className="mb-3"><strong>⏱️ Tiempo de lectura:</strong> 3-4 minutos</p>
                      <div className="space-y-1 text-xs">
                        <p>🔥 Lo que pasó este fin de semana</p>
                        <p>💰 Mercado: Real Madrid y el fichaje sorpresa</p>
                        <p>⚡ Viral: El golazo que está dando vueltas</p>
                        <p>🤔 Mi opinión: ¿Crisis en el City?</p>
                        <p>📖 Recomendación: El análisis que no te puedes perder</p>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}