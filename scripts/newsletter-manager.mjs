// scripts/newsletter-manager.mjs
// Usar fetch nativo de Node.js 18+
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

// Configuración
const API_URL = 'https://football-decoded-pi.vercel.app'

const OUTPUT_DIR = path.join(process.cwd(), 'exports')

async function getSubscribersFromAPI() {
  try {
    console.log(`🔗 Conectando a: ${API_URL}/api/newsletter/subscribe`)

    const response = await fetch(`${API_URL}/api/newsletter/subscribe`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Si necesitas autenticación, añádela aquí
        // 'Authorization': 'Bearer your-token'
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('❌ Error conectando a la API:', error.message)
    console.log('\n💡 Asegúrate de que:')
    console.log('   1. El servidor esté corriendo (npm run dev)')
    console.log('   2. La URL sea correcta')
    console.log('   3. El endpoint /api/newsletter/subscribe funcione')
    return null
  }
}

async function exportEmailsFromAPI() {
  const stats = await getSubscribersFromAPI()

  if (!stats || !stats.latest) {
    console.log('❌ No se pudieron obtener los datos de la API')
    return
  }

  // Filtrar solo confirmados
  const confirmedSubscribers = stats.latest.filter((sub) => sub.confirmed)

  if (confirmedSubscribers.length === 0) {
    console.log('📭 No hay emails confirmados.')
    return
  }

  // Crear directorio de exports si no existe
  if (!existsSync(OUTPUT_DIR)) {
    await mkdir(OUTPUT_DIR, { recursive: true })
  }

  const today = new Date().toISOString().split('T')[0]

  try {
    // 1. Lista simple de emails
    const emailsList = confirmedSubscribers.map((sub) => sub.email).join('\n')
    const emailsFile = path.join(OUTPUT_DIR, 'confirmed-emails.txt')
    await writeFile(emailsFile, emailsList)

    // 2. Lista con fechas
    const emailsWithDates = confirmedSubscribers
      .map((sub) => {
        const date = new Date(sub.confirmedAt || sub.subscribedAt).toLocaleDateString()
        return `${sub.email} - ${date}`
      })
      .join('\n')
    const detailedFile = path.join(OUTPUT_DIR, 'emails-with-dates.txt')
    await writeFile(detailedFile, emailsWithDates)

    // 3. CSV
    const csvContent = [
      'email,fecha_confirmacion,fecha_suscripcion',
      ...confirmedSubscribers.map((sub) => {
        const confirmedDate = sub.confirmedAt || 'N/A'
        const subscribedDate = sub.subscribedAt || 'N/A'
        return `${sub.email},${confirmedDate},${subscribedDate}`
      }),
    ].join('\n')

    const csvFile = path.join(OUTPUT_DIR, `emails-${today}.csv`)
    await writeFile(csvFile, csvContent)

    console.log('\n✅ ARCHIVOS EXPORTADOS:')
    console.log(`📧 Emails simples: ${emailsFile}`)
    console.log(`📅 Con fechas: ${detailedFile}`)
    console.log(`📊 CSV del día: ${csvFile}`)
    console.log(`\n📈 Total confirmados: ${confirmedSubscribers.length}`)

    // Mostrar emails para copy/paste
    console.log('\n📋 EMAILS PARA COPIAR:')
    console.log('='.repeat(40))
    confirmedSubscribers.forEach((sub) => console.log(sub.email))
    console.log('='.repeat(40))
  } catch (error) {
    console.error('❌ Error escribiendo archivos:', error.message)
  }
}

async function showListFromAPI() {
  const stats = await getSubscribersFromAPI()

  if (!stats) {
    console.log('❌ No se pudieron obtener los datos')
    return
  }

  const confirmed = stats.confirmed || 0
  const total = stats.total || 0
  const pending = stats.pending || 0

  console.log('\n📧 ESTADÍSTICAS NEWSLETTER:')
  console.log('='.repeat(40))
  console.log(`📊 Total: ${total}`)
  console.log(`✅ Confirmados: ${confirmed}`)
  console.log(`⏳ Pendientes: ${pending}`)
  console.log('='.repeat(40))

  if (stats.latest && stats.latest.length > 0) {
    const confirmedSubs = stats.latest.filter((sub) => sub.confirmed)

    if (confirmedSubs.length > 0) {
      console.log('\n📧 EMAILS CONFIRMADOS:')
      confirmedSubs.forEach((sub, index) => {
        const date = sub.confirmedAt
          ? new Date(sub.confirmedAt).toLocaleDateString()
          : new Date(sub.subscribedAt).toLocaleDateString()
        console.log(`${index + 1}. ${sub.email} - ${date}`)
      })
    }
  }
}

async function testConnection() {
  console.log('🧪 PROBANDO CONEXIÓN A LA API...')
  console.log(`🔗 URL: ${API_URL}/api/newsletter/subscribe`)

  const stats = await getSubscribersFromAPI()

  if (stats) {
    console.log('✅ Conexión exitosa!')
    console.log('📊 Datos recibidos:', JSON.stringify(stats, null, 2))
  } else {
    console.log('❌ No se pudo conectar')
    console.log('\n🌐 Verificando conexión a producción:')
    console.log('   URL: https://football-decoded-pi.vercel.app')
    console.log('   ¿El sitio está desplegado y funcionando?')
  }
}

// Comando principal
const command = process.argv[2]

switch (command) {
  case 'list':
    await showListFromAPI()
    break
  case 'export':
    await exportEmailsFromAPI()
    break
  case 'test':
    await testConnection()
    break
  default:
    console.log(`
📧 NEWSLETTER MANAGER - PRODUCCIÓN
==================================

Conecta a: https://football-decoded-pi.vercel.app

Comandos disponibles:

  npm run newsletter list     - Ver emails confirmados
  npm run newsletter export   - Exportar a archivos locales  
  npm run newsletter test     - Probar conexión a producción

Los archivos se guardan en: exports/
(esta carpeta está excluida del repositorio)

Ejemplos:
  npm run newsletter test     # Verificar que funciona
  npm run newsletter list     # Ver emails actuales
  npm run newsletter export   # Descargar a archivos
`)
}
