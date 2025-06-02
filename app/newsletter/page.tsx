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
      <div className="divide-y divide-slate-200 dark:divide-slate-700">
        {/* Header minimalista y directo */}
        <div className="w-full space-y-3 px-4 pt-8 pb-6 sm:px-6">
          <h1 className="font-headings text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl dark:text-slate-100">
            Newsletter
          </h1>
          <p className="font-body text-xl leading-relaxed text-slate-600 dark:text-slate-400">
            Análisis semanal directo, sin ruido
          </p>
        </div>

        {/* FORMULARIO PRINCIPAL - Hero section profesional */}
        <div className="pt-10">
          <div className="w-full px-4 sm:px-6">
            <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-gradient-to-br from-sky-50 via-white to-slate-50 dark:border-slate-700 dark:from-sky-900/10 dark:via-slate-800 dark:to-slate-900">
              {/* Patrón sutil de fondo */}
              <div className="absolute inset-0 opacity-5">
                <svg
                  className="h-full w-full"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 100 100"
                >
                  <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <circle cx="5" cy="5" r="1" fill="currentColor" />
                    </pattern>
                  </defs>
                  <rect width="100" height="100" fill="url(#grid)" />
                </svg>
              </div>

              <div className="relative px-8 py-12 lg:px-12 lg:py-16">
                <div className="mx-auto max-w-3xl space-y-8 text-center">
                  {/* Icono profesional */}
                  <div className="flex justify-center">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-sky-100 dark:bg-sky-900/30">
                      <svg
                        className="h-8 w-8 text-sky-600 dark:text-sky-400"
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
                    </div>
                  </div>

                  {/* Título y propuesta de valor */}
                  <div className="space-y-4">
                    <h2 className="font-headings text-3xl font-bold tracking-tight text-slate-900 lg:text-4xl dark:text-slate-100">
                      Newsletter FootballDecoded
                    </h2>
                    <p className="font-body text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                      Cada lunes,{' '}
                      <strong className="text-concept">
                        las 5 noticias más importantes del mundo del fútbol
                      </strong>
                      , analizadas con criterio técnico y sin ruido mediático.
                    </p>
                  </div>

                  {/* FORMULARIO - Diseño limpio y profesional */}
                  <div className="pt-4">
                    <NewsletterForm className="mx-auto max-w-md" />
                  </div>

                  {/* Garantías profesionales */}
                  <div className="flex flex-col items-center justify-center space-y-3 pt-4 sm:flex-row sm:space-y-0 sm:space-x-8">
                    <div className="font-body flex items-center text-sm text-slate-500 dark:text-slate-400">
                      <svg
                        className="mr-2 h-4 w-4 text-emerald-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Sin spam
                    </div>
                    <div className="font-body flex items-center text-sm text-slate-500 dark:text-slate-400">
                      <svg
                        className="mr-2 h-4 w-4 text-emerald-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Cancelación libre
                    </div>
                    <div className="font-body flex items-center text-sm text-slate-500 dark:text-slate-400">
                      <svg
                        className="mr-2 h-4 w-4 text-emerald-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Cada lunes
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CONTENIDO INFORMATIVO - Briefing profesional */}
        <div className="pt-12">
          <div className="w-full px-4 sm:px-6">
            <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
              <h3 className="font-headings mb-8 text-center text-2xl font-semibold text-slate-900 dark:text-slate-100">
                ¿Qué puede incluir cada edición?
              </h3>

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {[
                  {
                    title: 'Resultados clave',
                    description:
                      'Cuando haya pasado algo importante en el campo durante el fin de semana.',
                    icon: '🎯',
                  },
                  {
                    title: 'Movimientos de mercado',
                    description:
                      'Fichajes, rumores potentes u operaciones que merezcan atención técnica.',
                    icon: '📊',
                  },
                  {
                    title: 'Momentos destacados',
                    description: 'Jugadas, goles o situaciones que generen conversación táctica.',
                    icon: '⚡',
                  },
                  {
                    title: 'Reflexión personal',
                    description:
                      'Mi análisis sobre algo que me haya llamado la atención profesionalmente.',
                    icon: '💭',
                  },
                  {
                    title: 'Recomendaciones',
                    description: 'Contenido técnico, artículos o vídeos que no te deberías perder.',
                    icon: '📚',
                  },
                  {
                    title: 'Datos y métricas',
                    description: 'Estadísticas interesantes que ayuden a entender mejor el juego.',
                    icon: '📈',
                  },
                ].map((item, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 text-xl">{item.icon}</div>
                    <div className="min-w-0">
                      <h4 className="font-headings mb-1 font-medium text-slate-900 dark:text-slate-100">
                        {item.title}
                      </h4>
                      <p className="font-body text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CTA final minimalista */}
        <div className="pt-12 pb-8 text-center">
          <p className="font-body mb-4 text-slate-600 dark:text-slate-400">
            ¿Tienes preguntas sobre la newsletter?
          </p>
          <a
            href="mailto:joriolgo@gmail.com"
            className="font-body font-medium text-sky-700 transition-colors hover:text-sky-600 dark:text-sky-400 dark:hover:text-sky-300"
          >
            Contáctame directamente
          </a>
        </div>
      </div>
    </>
  )
}
