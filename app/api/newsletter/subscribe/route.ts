// app/api/newsletter/subscribe/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { writeFile, readFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import { Resend } from 'resend'
import crypto from 'crypto'

const resend = new Resend(process.env.RESEND_API_KEY)

interface NewsletterSubscriber {
  email: string
  subscribedAt: string
  confirmed: boolean
  confirmationToken?: string
  ip?: string
  userAgent?: string
}

const DATA_DIR = path.join(process.cwd(), 'data')
const SUBSCRIBERS_FILE = path.join(DATA_DIR, 'newsletter-subscribers.json')

// Función para obtener la URL base correcta
function getBaseUrl(request: NextRequest): string {
  // En desarrollo
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:3000'
  }

  // En producción con Vercel
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`
  }

  // URL configurada manualmente
  if (process.env.NEXTAUTH_URL) {
    return process.env.NEXTAUTH_URL
  }

  // Fallback usando headers de la request
  const host = request.headers.get('host')
  const protocol = request.headers.get('x-forwarded-proto') || 'https'

  return `${protocol}://${host}`
}

// Función para leer suscriptores existentes
async function getSubscribers(): Promise<NewsletterSubscriber[]> {
  try {
    if (!existsSync(SUBSCRIBERS_FILE)) {
      return []
    }
    const data = await readFile(SUBSCRIBERS_FILE, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('Error reading subscribers:', error)
    return []
  }
}

// Función para guardar suscriptores
async function saveSubscribers(subscribers: NewsletterSubscriber[]): Promise<void> {
  try {
    // Crear directorio si no existe
    if (!existsSync(DATA_DIR)) {
      await mkdir(DATA_DIR, { recursive: true })
    }

    await writeFile(SUBSCRIBERS_FILE, JSON.stringify(subscribers, null, 2))
  } catch (error) {
    console.error('Error saving subscribers:', error)
    throw error
  }
}

// Validar email
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Generar token de confirmación
function generateConfirmationToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

// Enviar email de confirmación
async function sendConfirmationEmail(email: string, token: string, baseUrl: string) {
  const confirmationUrl = `${baseUrl}/newsletter/confirm?token=${token}`

  try {
    const { data, error } = await resend.emails.send({
      from: 'FootballDecoded Newsletter <newsletter@footballdecoded.com>',
      to: [email],
      subject: '⚽ Confirma tu suscripción a FootballDecoded',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Confirma tu suscripción</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
          
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #0ea5e9; font-size: 28px; margin-bottom: 10px;">⚽ FootballDecoded</h1>
            <p style="color: #666; font-size: 16px;">Confirma tu suscripción a la newsletter</p>
          </div>
          
          <div style="background: #f8fafc; border-radius: 8px; padding: 25px; margin-bottom: 25px;">
            <h2 style="color: #334155; font-size: 20px; margin-bottom: 15px;">¡Hola!</h2>
            <p style="margin-bottom: 15px;">Gracias por suscribirte a <strong>FootballDecoded Newsletter</strong>.</p>
            <p style="margin-bottom: 20px;">Cada lunes recibirás las <strong>5 noticias más importantes del mundo del fútbol</strong>, contadas con criterio, sin ruido, y con mi análisis personal.</p>
          </div>
          
          <div style="text-align: center; margin: 30px 0;">
            <a href="${confirmationUrl}" 
               style="background: #0ea5e9; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; display: inline-block;">
              Confirmar suscripción
            </a>
          </div>
          
          <div style="background: #f1f5f9; border-radius: 6px; padding: 15px; margin-top: 25px;">
            <p style="margin: 0; font-size: 14px; color: #64748b;">
              Si no te has suscrito a esta newsletter, puedes ignorar este email.
            </p>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: #94a3b8;">
              URL de confirmación: ${confirmationUrl}
            </p>
          </div>
          
          <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; font-size: 14px; color: #64748b;">
              FootballDecoded • Análisis del fútbol moderno
            </p>
          </div>
          
        </body>
        </html>
      `,
    })

    if (error) {
      console.error('Error sending confirmation email:', error)
      throw error
    }

    return data
  } catch (error) {
    console.error('Failed to send confirmation email:', error)
    throw error
  }
}

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()

    // Validaciones básicas
    if (!email) {
      return NextResponse.json({ error: 'Email es requerido' }, { status: 400 })
    }

    if (!isValidEmail(email)) {
      return NextResponse.json({ error: 'Email no válido' }, { status: 400 })
    }

    // Leer suscriptores existentes
    const subscribers = await getSubscribers()

    // Verificar si ya está suscrito
    const existingSubscriber = subscribers.find(
      (sub) => sub.email.toLowerCase() === email.toLowerCase()
    )
    if (existingSubscriber) {
      if (existingSubscriber.confirmed) {
        return NextResponse.json(
          { message: 'Ya estás suscrito y confirmado en la newsletter' },
          { status: 200 }
        )
      } else {
        // Reenviar email de confirmación
        if (existingSubscriber.confirmationToken) {
          const baseUrl = getBaseUrl(request)
          await sendConfirmationEmail(email, existingSubscriber.confirmationToken, baseUrl)
        }
        return NextResponse.json(
          { message: 'Te hemos reenviado el email de confirmación. Revisa tu bandeja de entrada.' },
          { status: 200 }
        )
      }
    }

    // Generar token de confirmación
    const confirmationToken = generateConfirmationToken()

    // Crear nuevo suscriptor
    const newSubscriber: NewsletterSubscriber = {
      email: email.toLowerCase(),
      subscribedAt: new Date().toISOString(),
      confirmed: false,
      confirmationToken,
      ip: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown',
      userAgent: request.headers.get('user-agent') || 'unknown',
    }

    // Añadir a la lista
    subscribers.push(newSubscriber)

    // Guardar
    await saveSubscribers(subscribers)

    // Enviar email de confirmación
    const baseUrl = getBaseUrl(request)
    await sendConfirmationEmail(email, confirmationToken, baseUrl)

    // Respuesta exitosa
    return NextResponse.json({
      message:
        '¡Perfecto! Te hemos enviado un email de confirmación. Revisa tu bandeja de entrada.',
      email: email,
    })
  } catch (error) {
    console.error('Newsletter subscription error:', error)
    return NextResponse.json({ error: 'Error interno del servidor' }, { status: 500 })
  }
}

// Endpoint GET para obtener estadísticas (opcional, para tu uso)
export async function GET() {
  try {
    const subscribers = await getSubscribers()
    const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)

    return NextResponse.json({
      total: subscribers.length,
      confirmed: confirmedSubscribers.length,
      pending: subscribers.length - confirmedSubscribers.length,
      latest: confirmedSubscribers.slice(-5).reverse(), // Últimos 5 confirmados
      recentCount: confirmedSubscribers.filter((sub) => {
        const subDate = new Date(sub.subscribedAt)
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        return subDate > weekAgo
      }).length,
    })
  } catch (error) {
    console.error('Error getting newsletter stats:', error)
    return NextResponse.json({ error: 'Error obteniendo estadísticas' }, { status: 500 })
  }
}
