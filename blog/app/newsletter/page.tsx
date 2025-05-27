import { genPageMetadata } from 'app/seo'
import NewsletterForm from 'pliny/ui/NewsletterForm'

export const metadata = genPageMetadata({
    title: 'Newsletter - Análisis Táctico Avanzado',
    description: 'Suscríbete al newsletter de FootballDecoded para recibir análisis tácticos exclusivos, métricas avanzadas y tendencias del fútbol profesional.'
})

export default function Newsletter() {
    return (
        <>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
                <div className="space-y-2 pb-8 pt-6 md:space-y-5">
                    <h1 className="text-3xl font-extrabold leading-9 tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
                        Newsletter
                    </h1>
                    <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
                        Análisis táctico avanzado para profesionales del fútbol
                    </p>
                </div>

                <div className="pt-8">
                    <div className="mx-auto max-w-2xl">
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border border-gray-200 dark:border-gray-700">
                            <div className="text-center mb-8">
                                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                                    Únete a la comunidad técnica
                                </h2>
                                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                                    Recibe contenido exclusivo diseñado para entrenadores, analistas y profesionales
                                    del fútbol que buscan profundizar en aspectos tácticos y analíticos del juego moderno.
                                </p>
                            </div>

                            {/* Formulario de Newsletter */}
                            <div className="mb-8">
                                <NewsletterForm />
                            </div>

                            {/* Información sobre el contenido */}
                            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                                    ¿Qué incluye el newsletter?
                                </h3>

                                <div className="space-y-4">
                                    <div className="flex items-start">
                                        <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                                        <div className="ml-3">
                                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                                Análisis Tácticos Exclusivos
                                            </h4>
                                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                                Desgloses detallados de sistemas de juego, presión y transiciones de equipos de élite.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start">
                                        <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                                        <div className="ml-3">
                                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                                Métricas Avanzadas
                                            </h4>
                                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                                Implementación práctica de métricas como xThreat, PPDA, y análisis cuantitativos aplicados.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start">
                                        <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                                        <div className="ml-3">
                                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                                Tendencias del Fútbol Moderno
                                            </h4>
                                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                                Identificación temprana de patrones emergentes y evolución táctica en el fútbol profesional.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start">
                                        <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                                        <div className="ml-3">
                                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                                Herramientas y Recursos
                                            </h4>
                                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                                Scripts, plantillas y metodologías para análisis táctico aplicado.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Información sobre frecuencia */}
                            <div className="border-t border-gray-200 dark:border-gray-700 pt-6 mt-6">
                                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                    <div className="text-center">
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            <strong>Periodicidad:</strong> Quincenal •
                                            <strong> Audiencia:</strong> Profesionales técnicos •
                                            <strong> Formato:</strong> Análisis aplicado
                                        </p>
                                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
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