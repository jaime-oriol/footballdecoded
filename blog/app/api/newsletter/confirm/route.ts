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
      return new NextResponse(
        `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Error - FootballDecoded</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; background: #f8fafc; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .error { color: #ef4444; }
            .title { color: #0ea5e9; margin-bottom: 20px; }
            a { color: #0ea5e9; text-decoration: none; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1 class="title">⚽ FootballDecoded</h1>
            <h2 class="error">Token no válido</h2>
            <p>El enlace de confirmación no es válido o ha expirado.</p>
            <p><a href="https://footballdecoded.com">Volver al inicio</a></p>
          </div>
        </body>
        </html>
        `,
        {
          status: 400,
          headers: { 'Content-Type': 'text/html' },
        }
      )
    }

    // Leer suscriptores
    const subscribers = await getSubscribers()

    // Buscar suscriptor con este token
    const subscriberIndex = subscribers.findIndex((sub) => sub.confirmationToken === token)

    if (subscriberIndex === -1) {
      return new NextResponse(
        `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Error - FootballDecoded</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; background: #f8fafc; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .error { color: #ef4444; }
            .title { color: #0ea5e9; margin-bottom: 20px; }
            a { color: #0ea5e9; text-decoration: none; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1 class="title">⚽ FootballDecoded</h1>
            <h2 class="error">Token no encontrado</h2>
            <p>Este enlace de confirmación no existe o ya ha sido utilizado.</p>
            <p><a href="https://footballdecoded.com">Volver al inicio</a></p>
          </div>
        </body>
        </html>
        `,
        {
          status: 404,
          headers: { 'Content-Type': 'text/html' },
        }
      )
    }

    const subscriber = subscribers[subscriberIndex]

    // Si ya está confirmado
    if (subscriber.confirmed) {
      return new NextResponse(
        `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Ya confirmado - FootballDecoded</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; background: #f8fafc; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #10b981; }
            .title { color: #0ea5e9; margin-bottom: 20px; }
            a { color: #0ea5e9; text-decoration: none; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1 class="title">⚽ FootballDecoded</h1>
            <h2 class="success">Ya estás suscrito</h2>
            <p>Tu email ya había sido confirmado anteriormente.</p>
            <p>Recibirás la newsletter cada lunes por la mañana.</p>
            <p><a href="https://footballdecoded.com">Ir al blog</a></p>
          </div>
        </body>
        </html>
        `,
        {
          status: 200,
          headers: { 'Content-Type': 'text/html' },
        }
      )
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
    return new NextResponse(
      `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>¡Suscripción confirmada! - FootballDecoded</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: #f8fafc; 
            line-height: 1.6;
          }
          .container { 
            max-width: 600px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
          }
          .success { color: #10b981; font-size: 24px; margin-bottom: 20px; }
          .title { color: #0ea5e9; margin-bottom: 20px; font-size: 32px; }
          .highlight { background: #f0f9ff; padding: 20px; border-radius: 6px; margin: 20px 0; }
          .button { 
            display: inline-block; 
            background: #0ea5e9; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 6px; 
            margin: 20px 10px;
            font-weight: 500;
          }
          .button:hover { background: #0284c7; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1 class="title">⚽ FootballDecoded</h1>
          <h2 class="success">🎉 ¡Suscripción confirmada!</h2>
          
          <div class="highlight">
            <p><strong>¡Perfecto!</strong> Ya formas parte de la comunidad FootballDecoded.</p>
            <p>Cada <strong>lunes por la mañana</strong> recibirás las 5 noticias más importantes del mundo del fútbol, contadas con criterio y con mi análisis personal.</p>
          </div>
          
          <p>Mientras tanto, puedes:</p>
          
          <a href="https://footballdecoded.com" class="button">Explorar el blog</a>
          <a href="https://footballdecoded.com/newsletter" class="button">Saber más sobre la newsletter</a>
          
          <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">
            <p>Gracias por confiar en FootballDecoded.</p>
            <p>Si tienes alguna pregunta, puedes contactarme en <a href="mailto:newsletter@footballdecoded.com" style="color: #0ea5e9;">newsletter@footballdecoded.com</a></p>
          </div>
        </div>
      </body>
      </html>
      `,
      {
        status: 200,
        headers: { 'Content-Type': 'text/html' },
      }
    )
  } catch (error) {
    console.error('Newsletter confirmation error:', error)
    return new NextResponse(
      `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Error - FootballDecoded</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; background: #f8fafc; }
          .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
          .error { color: #ef4444; }
          .title { color: #0ea5e9; margin-bottom: 20px; }
          a { color: #0ea5e9; text-decoration: none; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1 class="title">⚽ FootballDecoded</h1>
          <h2 class="error">Error del servidor</h2>
          <p>Ha ocurrido un error al confirmar tu suscripción.</p>
          <p><a href="https://footballdecoded.com">Volver al inicio</a></p>
        </div>
      </body>
      </html>
      `,
      {
        status: 500,
        headers: { 'Content-Type': 'text/html' },
      }
    )
  }
}
