import { genPageMetadata } from 'app/seo'

export const metadata = genPageMetadata({
  title: 'Contacto - FootballDecoded',
  description:
    'Contacta con FootballDecoded para colaboraciones técnicas, consultas analíticas y oportunidades profesionales en cuerpos técnicos de fútbol.',
})

export default function Contact() {
  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        <div className="space-y-2 pt-6 pb-8 md:space-y-5">
          <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14 dark:text-gray-100">
            Contacto
          </h1>
          <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
            Colaboraciones técnicas y oportunidades profesionales
          </p>
        </div>

        <div className="pt-8">
          <div className="mx-auto max-w-2xl">
            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800">
              {/* Información de contacto */}
              <div className="mb-8">
                <h2 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Hablemos de fútbol y análisis
                </h2>

                <div className="space-y-4 text-gray-600 dark:text-gray-400">
                  <p>
                    Estoy interesado en colaboraciones técnicas, proyectos de análisis y
                    oportunidades para integrar cuerpos técnicos de clubes profesionales.
                  </p>

                  <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-700/50">
                    <h3 className="mb-2 font-semibold text-gray-900 dark:text-gray-100">
                      Áreas de especialización:
                    </h3>
                    <ul className="space-y-1 text-sm">
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
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Email *
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    required
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="tu@email.com"
                  />
                </div>

                <div>
                  <label
                    htmlFor="subject"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Motivo del contacto *
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    required
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
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
                  <label
                    htmlFor="organization"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Organización / Club
                  </label>
                  <input
                    type="text"
                    id="organization"
                    name="organization"
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="Nombre del club o organización"
                  />
                </div>

                <div>
                  <label
                    htmlFor="message"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Mensaje *
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    rows={6}
                    required
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="Describe tu consulta, proyecto o propuesta..."
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    className="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 flex w-full justify-center rounded-md border border-transparent px-4 py-3 text-sm font-medium text-white shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none"
                  >
                    Enviar mensaje
                  </button>
                </div>
              </form>

              {/* Información adicional */}
              <div className="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
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
                    </a>{' '}
                    para ver mis proyectos técnicos.
                  </p>
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
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
