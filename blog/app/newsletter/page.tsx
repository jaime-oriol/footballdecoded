import { genPageMetadata } from 'app/seo'
import NewsletterForm from 'pliny/ui/NewsletterForm'

export const metadata = genPageMetadata({
  title: 'Newsletter - Análisis Táctico Avanzado',
  description:
    'Suscríbete al newsletter de FootballDecoded para recibir análisis tácticos exclusivos, métricas avanzadas y tendencias del fútbol profesional.',
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
            Análisis táctico avanzado para profesionales del fútbol
          </p>
        </div>

        <div className="pt-8">
          <div className="mx-auto max-w-2xl">
            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-8 text-center">
                <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Únete a la comunidad técnica
                </h2>
                <p className="leading-relaxed text-gray-600 dark:text-gray-400">
                  Recibe contenido exclusivo diseñado para entrenadores, analistas y profesionales
                  del fútbol que buscan profundizar en aspectos tácticos y analíticos del juego
                  moderno.
                </p>
              </div>

              {/* Formulario de Newsletter */}
              <div className="mb-8">
                <NewsletterForm />
              </div>

              {/* Información sobre el contenido */}
              <div className="border-t border-gray-200 pt-6 dark:border-gray-700">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  ¿Qué incluye el newsletter?
                </h3>

                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Análisis Tácticos Exclusivos
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Desgloses detallados de sistemas de juego, presión y transiciones de equipos
                        de élite.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Métricas Avanzadas
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Implementación práctica de métricas como xThreat, PPDA, y análisis
                        cuantitativos aplicados.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Tendencias del Fútbol Moderno
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Identificación temprana de patrones emergentes y evolución táctica en el
                        fútbol profesional.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="bg-primary-500 mt-2 h-2 w-2 flex-shrink-0 rounded-full"></div>
                    <div className="ml-3">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        Herramientas y Recursos
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Scripts, plantillas y metodologías para análisis táctico aplicado.
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
                      <strong>Periodicidad:</strong> Quincenal •<strong> Audiencia:</strong>{' '}
                      Profesionales técnicos •<strong> Formato:</strong> Análisis aplicado
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
