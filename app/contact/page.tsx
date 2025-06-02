import { genPageMetadata } from 'app/seo'
import Link from '@/components/Link'

export const metadata = genPageMetadata({ title: 'Contacto' })

export default function Contact() {
  return (
    <>
      <div className="divide-y divide-slate-200 dark:divide-slate-700">
        {/* Header profesional */}
        <div className="w-full space-y-3 px-4 pt-8 pb-8 sm:px-6">
          <h1 className="font-headings text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl dark:text-slate-100">
            Contacto
          </h1>
          <p className="font-body text-xl text-slate-600 dark:text-slate-400">
            Colaboraciones, feedback técnico y consultoría analítica
          </p>
        </div>

        <div className="pt-8">
          <div className="w-full px-4 sm:px-6">
            {/* Card principal de contacto */}
            <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
              {/* Áreas de especialización */}
              <div className="mb-8">
                <h2 className="font-headings mb-6 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  Áreas de especialización
                </h2>
                <div className="grid gap-4 md:grid-cols-2">
                  {[
                    {
                      title: 'Análisis táctico',
                      description: 'Estructuras de juego, sistemas y principios del fútbol moderno',
                      icon: '🎯',
                    },
                    {
                      title: 'Scouting funcional',
                      description:
                        'Identificación de perfiles por rol y función táctica específica',
                      icon: '🔍',
                    },
                    {
                      title: 'Métricas avanzadas',
                      description: 'Desarrollo de KPIs y modelos cuantitativos aplicados',
                      icon: '📊',
                    },
                    {
                      title: 'Visualización de datos',
                      description: 'Dashboards interactivos y reportes ejecutivos para clubes',
                      icon: '📈',
                    },
                  ].map((area, index) => (
                    <div
                      key={index}
                      className="flex items-start space-x-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-700/50"
                    >
                      <div className="flex-shrink-0 text-lg">{area.icon}</div>
                      <div className="min-w-0">
                        <h3 className="font-headings mb-1 font-medium text-slate-900 dark:text-slate-100">
                          {area.title}
                        </h3>
                        <p className="font-body text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                          {area.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Guía para el contacto */}
              <div className="mb-8 rounded-lg border border-slate-300 bg-slate-50 p-6 dark:border-slate-600 dark:bg-slate-800/50">
                <h3 className="font-headings mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Qué incluir en tu mensaje
                </h3>

                <div className="font-body space-y-3 text-slate-700 dark:text-slate-300">
                  <div className="flex items-start">
                    <span className="mr-3 text-sky-500 dark:text-sky-400">•</span>
                    <div>
                      <strong className="text-slate-900 dark:text-slate-100">
                        Motivo del contacto:
                      </strong>{' '}
                      Colaboración, consultoría, feedback o propuesta específica
                    </div>
                  </div>

                  <div className="flex items-start">
                    <span className="mr-3 text-sky-500 dark:text-sky-400">•</span>
                    <div>
                      <strong className="text-slate-900 dark:text-slate-100">
                        Contexto profesional:
                      </strong>{' '}
                      Tu rol, organización o proyecto actual
                    </div>
                  </div>

                  <div className="flex items-start">
                    <span className="mr-3 text-sky-500 dark:text-sky-400">•</span>
                    <div>
                      <strong className="text-slate-900 dark:text-slate-100">Alcance:</strong>{' '}
                      Detalles del proyecto, timeline y objetivos específicos
                    </div>
                  </div>
                </div>
              </div>

              {/* EMAIL principal - destacado */}
              <div className="mb-8">
                <a
                  href="mailto:joriolgo@gmail.com"
                  className="font-body block w-full rounded-lg bg-sky-600 px-6 py-4 text-center text-lg font-semibold text-white shadow-lg transition-all duration-200 hover:bg-sky-700 hover:shadow-xl focus:ring-4 focus:ring-sky-500/25"
                >
                  <svg
                    className="mr-3 inline h-5 w-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  joriolgo@gmail.com
                </a>
              </div>

              {/* Información adicional */}
              <div className="border-t border-slate-200 pt-6 dark:border-slate-700">
                <div className="space-y-3 text-center">
                  <p className="font-body text-sm text-slate-600 dark:text-slate-400">
                    También puedes encontrarme en{' '}
                    <a
                      href="https://github.com/jaime-oriol"
                      className="text-concept font-medium transition-colors hover:text-sky-600 dark:hover:text-sky-300"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      GitHub
                    </a>{' '}
                    para revisar mis proyectos técnicos
                  </p>
                  <div className="flex items-center justify-center space-x-4 font-mono text-xs text-slate-500 dark:text-slate-500">
                    <span>• Respuesta típica: 24-48h</span>
                    <span>• Zona horaria: CET (Madrid)</span>
                    <span>• Idiomas: ES/EN</span>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA complementario */}
            <div className="mt-8 text-center">
              <p className="font-body mb-4 text-slate-600 dark:text-slate-400">
                ¿Prefieres ver mi trabajo antes de contactar?
              </p>
              <div className="flex flex-col justify-center gap-4 sm:flex-row">
                <Link
                  href="/blog"
                  className="font-body inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  Explorar análisis
                </Link>
                <Link
                  href="/newsletter"
                  className="font-body inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  Leer newsletter
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
