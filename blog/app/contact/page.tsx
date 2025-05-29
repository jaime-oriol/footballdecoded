'use client'

import { useState, useEffect } from 'react'
import { genPageMetadata } from 'app/seo'
import emailjs from '@emailjs/browser'

export default function Contact() {
  const [formData, setFormData] = useState({
    from_email: '',
    subject: '',
    organization: '',
    message: '',
    from_name: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState('')

  useEffect(() => {
    emailjs.init(process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY!)
  }, [])

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) return false
    
    const disposableDomains = [
      '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
      'tempmail.org', 'yopmail.com', 'trashmail.com'
    ]
    const domain = email.split('@')[1]?.toLowerCase()
    if (disposableDomains.includes(domain)) return false
    
    const validDomains = [
      'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com',
      'icloud.com', 'protonmail.com', 'live.com', 'msn.com'
    ]
    
    return validDomains.includes(domain) || domain.includes('.')
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setSubmitStatus('')

    if (!validateEmail(formData.from_email)) {
      setSubmitStatus('invalid-email')
      setIsSubmitting(false)
      return
    }

    try {
      const templateParams = {
        from_name: formData.organization || 'Usuario anónimo',
        from_email: formData.from_email,
        subject: formData.subject,
        organization: formData.organization,
        message: formData.message,
        reply_to: formData.from_email,
        to_name: 'Jaime Oriol',
        to_email: 'joriolgo@gmail.com'
      }

      const result = await emailjs.send(
        process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID!,
        process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID!,
        templateParams
      )

      if (result.status === 200) {
        setSubmitStatus('success')
        setFormData({ from_email: '', subject: '', organization: '', message: '', from_name: '' })
      } else {
        setSubmitStatus('error')
      }
    } catch (error) {
      console.error('Error al enviar:', error)
      setSubmitStatus('error')
    } finally {
      setIsSubmitting(false)
    }
  }

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
          <div className="mx-auto max-w-3xl px-4 sm:px-6 xl:max-w-5xl xl:px-0">
            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800">
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

              {submitStatus === 'success' && (
                <div className="mb-6 rounded-lg bg-green-50 p-4 border border-green-200 dark:bg-green-900/20 dark:border-green-800">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-green-800 dark:text-green-200">
                        ¡Mensaje enviado correctamente! Te responderé en las próximas 24-48 horas.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {submitStatus === 'invalid-email' && (
                <div className="mb-6 rounded-lg bg-yellow-50 p-4 border border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                        Por favor, usa un email válido de un proveedor reconocido (Gmail, Outlook, etc.)
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {submitStatus === 'error' && (
                <div className="mb-6 rounded-lg bg-red-50 p-4 border border-red-200 dark:bg-red-900/20 dark:border-red-800">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-red-800 dark:text-red-200">
                        Error al enviar el mensaje. Por favor, inténtalo de nuevo o contáctame directamente en joriolgo@gmail.com
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label
                    htmlFor="from_email"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Email *
                  </label>
                  <input
                    type="email"
                    id="from_email"
                    name="from_email"
                    value={formData.from_email}
                    onChange={handleChange}
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
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                  >
                    <option value="">Selecciona una opción</option>
                    <option value="Colaboración Técnica">Colaboración Técnica</option>
                    <option value="Oportunidad Laboral">Oportunidad Laboral</option>
                    <option value="Consultoría Analítica">Consultoría Analítica</option>
                    <option value="Proyecto Conjunto">Proyecto Conjunto</option>
                    <option value="Otro">Otro</option>
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="organization"
                    className="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    Organización / Club / Persona
                  </label>
                  <input
                    type="text"
                    id="organization"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="Nombre del club, empresa o tu nombre personal"
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
                    value={formData.message}
                    onChange={handleChange}
                    required
                    className="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="Describe tu consulta, proyecto o propuesta..."
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed flex w-full justify-center items-center rounded-md border border-transparent px-4 py-3 text-sm font-medium text-white shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none"
                  >
                    {isSubmitting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Enviando...
                      </>
                    ) : (
                      'Enviar mensaje'
                    )}
                  </button>
                </div>
              </form>

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
                    para ver mis proyectos técnicos o contactarme directamente en{' '}
                    <a
                      href="mailto:joriolgo@gmail.com"
                      className="text-primary-600 hover:text-primary-500 dark:text-primary-400"
                    >
                      joriolgo@gmail.com
                    </a>
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