import { genPageMetadata } from 'app/seo'

export const metadata = genPageMetadata({ title: 'Contacto' })

export default function Contact() {
  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        <div className="space-y-2 pt-6 pb-8 md:space-y-5">
          <h1 className="text-3xl leading-9 font-extrabold tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14 dark:text-gray-100">
            Contacto
          </h1>
        </div>

        <div className="pt-8">
          <div className="mx-auto max-w-3xl px-4 sm:px-6 xl:max-w-5xl xl:px-0">
            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800">
              
              {/* ÁREAS DE ESPECIALIZACIÓN */}
              <div className="mb-8">
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

              {/* INFORMACIÓN SIMPLE PARA EL EMAIL */}
              <div className="mb-8 rounded-lg border border-gray-300 bg-gray-50 p-6 dark:border-gray-600 dark:bg-gray-800/50">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Qué incluir en tu email
                </h3>
                
                <div className="space-y-3 text-gray-700 dark:text-gray-300">
                  <div className="flex items-start">
                    <span className="mr-3 text-gray-500 dark:text-gray-400">•</span>
                    <div>
                      <strong>Motivo del contacto:</strong> Por qué me escribes
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <span className="mr-3 text-gray-500 dark:text-gray-400">•</span>
                    <div>
                      <strong>Nombre y organización:</strong> Quién eres y dónde trabajas
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <span className="mr-3 text-gray-500 dark:text-gray-400">•</span>
                    <div>
                      <strong>Mensaje:</strong> Detalles del proyecto o propuesta
                    </div>
                  </div>
                </div>
              </div>

              {/* EMAIL CLICKEABLE ANCHO COMPLETO */}
              <a 
                href="mailto:joriolgo@gmail.com"
                className="mb-8 block w-full rounded-lg bg-primary-600 px-6 py-4 text-center text-lg font-semibold text-white shadow-lg transition-all duration-200 hover:bg-primary-700 hover:shadow-xl focus:ring-4 focus:ring-primary-500/25"
              >
                <svg className="mr-3 inline h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                joriolgo@gmail.com
              </a>

              {/* INFORMACIÓN ADICIONAL Y FOOTER */}
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
                    para ver mis proyectos técnicos
                  </p>
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    Respondo normalmente en 24-48 horas
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