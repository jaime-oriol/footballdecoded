import { genPageMetadata } from 'app/seo'

export const metadata = genPageMetadata({
    title: 'Contacto - FootballDecoded',
    description: 'Contacta con FootballDecoded para colaboraciones técnicas, consultas analíticas y oportunidades profesionales en cuerpos técnicos de fútbol.'
})

export default function Contact() {
    return (
        <>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
                <div className="space-y-2 pb-8 pt-6 md:space-y-5">
                    <h1 className="text-3xl font-extrabold leading-9 tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
                        Contacto
                    </h1>
                    <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
                        Colaboraciones técnicas y oportunidades profesionales
                    </p>
                </div>

                <div className="pt-8">
                    <div className="mx-auto max-w-2xl">
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border border-gray-200 dark:border-gray-700">

                            {/* Información de contacto */}
                            <div className="mb-8">
                                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
                                    Hablemos de fútbol y análisis
                                </h2>

                                <div className="space-y-4 text-gray-600 dark:text-gray-400">
                                    <p>
                                        Estoy interesado en colaboraciones técnicas, proyectos de análisis y oportunidades
                                        para integrar cuerpos técnicos de clubes profesionales.
                                    </p>

                                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                                            Áreas de especialización:
                                        </h3>
                                        <ul className="text-sm space-y-1">
                                            <li>• Análisis táctico y estructural</li>
                                            <li>• Scouting funcional y player typing</li>
                                            <li>• Métricas avanzadas y programación aplicada</li>
                                            <li>• Visualización de datos deportivos</li>
                                            <li>• Consultoría analítica para clubes</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {/* Formulario de contacto */}
                            <form className="space-y-6">
                                <div>
                                    <label htmlFor="email" className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                        Email *
                                    </label>
                                    <input
                                        type="email"
                                        id="email"
                                        name="email"
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-gray-100"
                                        placeholder="tu@email.com"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="subject" className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                        Motivo del contacto *
                                    </label>
                                    <select
                                        id="subject"
                                        name="subject"
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-gray-100"
                                    >
                                        <option value="">Selecciona una opción</option>
                                        <option value="colaboracion">Colaboración Técnica</option>
                                        <option value="oportunidad">Oportunidad Laboral</option>
                                        <option value="consultoria">Consultoría Analítica</option>
                                        <option value="proyecto">Proyecto Conjunto</option>
                                        <option value="otro">Otro</option>
                                    </select>
                                </div>

                                <div>
                                    <label htmlFor="organization" className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                        Organización / Club
                                    </label>
                                    <input
                                        type="text"
                                        id="organization"
                                        name="organization"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-gray-100"
                                        placeholder="Nombre del club o organización"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="message" className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                        Mensaje *
                                    </label>
                                    <textarea
                                        id="message"
                                        name="message"
                                        rows={6}
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-gray-100"
                                        placeholder="Describe tu consulta, proyecto o propuesta..."
                                    />
                                </div>

                                <div>
                                    <button
                                        type="submit"
                                        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                                    >
                                        Enviar mensaje
                                    </button>
                                </div>
                            </form>

                            {/* Información adicional */}
                            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                                <div className="text-center">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        También puedes encontrarme en{' '}
                                        <a
                                            href="https://github.com/jaime-oriol"
                                            className="text-primary-600 hover:text-primary-500 dark:text-primary-400"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            GitHub
                                        </a>
                                        {' '}para ver mis proyectos técnicos.
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                                        Respondo normalmente en 24-48 horas.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}