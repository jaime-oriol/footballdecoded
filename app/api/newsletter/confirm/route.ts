// app/api/newsletter/confirm/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { writeFile, readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

interface NewsletterSubscriber {
  email: string
  subscribedAt: string
  confirmed: boolean
  confirmationToken?: string
  confirmedAt?: string
  ip?: string
  userAgent?: string
}

const DATA_DIR = path.join(process.cwd(), 'data')
const SUBSCRIBERS_FILE = path.join(DATA_DIR, 'newsletter-subscribers.json')

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
    await writeFile(SUBSCRIBERS_FILE, JSON.stringify(subscribers, null, 2))
  } catch (error) {
    console.error('Error saving subscribers:', error)
    throw error
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const token = searchParams.get('token')

    if (!token) {
      return NextResponse.json({ error: 'Token de confirmación requerido' }, { status: 400 })
    }

    // Leer suscriptores
    const subscribers = await getSubscribers()

    // Buscar suscriptor con este token
    const subscriberIndex = subscribers.findIndex((sub) => sub.confirmationToken === token)

    if (subscriberIndex === -1) {
      return NextResponse.json(
        { error: 'Token de confirmación no válido o ya utilizado' },
        { status: 404 }
      )
    }

    const subscriber = subscribers[subscriberIndex]

    // Si ya está confirmado
    if (subscriber.confirmed) {
      return NextResponse.json({
        message: 'Tu suscripción ya había sido confirmada anteriormente',
        email: subscriber.email,
      })
    }

    // Confirmar suscripción
    subscribers[subscriberIndex] = {
      ...subscriber,
      confirmed: true,
      confirmedAt: new Date().toISOString(),
      confirmationToken: undefined, // Eliminar el token usado
    }

    // Guardar cambios
    await saveSubscribers(subscribers)

    // Respuesta de éxito
    return NextResponse.json({
      message: '¡Suscripción confirmada correctamente! Recibirás la newsletter cada lunes.',
      email: subscriber.email,
    })
  } catch (error) {
    console.error('Newsletter confirmation error:', error)
    return NextResponse.json({ error: 'Error interno del servidor' }, { status: 500 })
  }
}
