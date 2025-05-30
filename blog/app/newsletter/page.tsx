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
        <div className="space-y-2 pt-6 pb-8 md:space-y-5">
          <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14 dark:text-gray-100">
            Newsletter
          </h1>
          <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
            Las 5 noticias más importantes del fútbol cada lunes, contadas con criterio
          </p>
        </div>

        <div className="pt-8">
          <div className="mx-auto max-w-2xl">
            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-8 text-center">
                <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Suscríbete a la newsletter de FootballDecoded
                </h2>
                <p className="leading-relaxed text-gray-600 dark:text-gray-400">
                  Cada lunes, en tu correo:{' '}
                  <strong>las 5 noticias más importantes del mundo del fútbol</strong>, contadas con
                  criterio, sin ruido, y con algo de opinión propia.
                </p>
              </div>

              {/* Formulario de Newsletter */}
              <div className="mb-8">
                <NewsletterForm />
              </div>

              {/* Información sobre el contenido */}
              <div className="border-t border-gray-200 pt-6 dark:border-gray-700">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  ¿Qué puede incluir cada edición?
                </h3>

                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Resultados y partidos clave
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Lo más importante que pasó en el campo durante el fin de semana, explicado
                        sin exageraciones.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Movimientos de mercado
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Altas, bajas, rumores potentes y operaciones que podrían cambiar dinámicas.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Golazos, momentos virales y curiosidades
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Lo que se compartió, lo que generó conversación, y lo que vale la pena
                        volver a ver.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Una reflexión personal
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Un comentario rápido mío sobre algo que me llamó la atención, siempre
                        relacionado con el juego.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Recomendaciones de la semana
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Un tuit, un vídeo o un artículo que no te deberías perder.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Información sobre frecuencia */}
              <div className="mt-6 border-t border-gray-200 pt-6 dark:border-gray-700">
                <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-700/50">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      <strong>Periodicidad:</strong> Cada lunes por la mañana
                    </p>
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                      Sin spam. Cancela tu suscripción en cualquier momento.
                    </p>
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
