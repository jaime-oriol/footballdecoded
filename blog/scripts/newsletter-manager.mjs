// scripts/newsletter-manager.mjs
import { readFile, writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const DATA_DIR = path.join(process.cwd(), 'data')
const SUBSCRIBERS_FILE = path.join(DATA_DIR, 'newsletter-subscribers.json')

async function getSubscribers() {
  try {
    if (!existsSync(SUBSCRIBERS_FILE)) {
      console.log('❌ No hay archivo de suscriptores.')
      return []
    }
    const data = await readFile(SUBSCRIBERS_FILE, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('❌ Error leyendo suscriptores:', error)
    return []
  }
}

async function exportEmails() {
  const subscribers = await getSubscribers()
  const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)

  if (confirmedSubscribers.length === 0) {
    console.log('📭 No hay emails confirmados.')
    return
  }

  // Crear directorio si no existe
  if (!existsSync(DATA_DIR)) {
    await mkdir(DATA_DIR, { recursive: true })
  }

  const today = new Date().toISOString().split('T')[0]

  // 1. Lista simple de emails (para copiar/pegar)
  const emailsList = confirmedSubscribers.map(sub => sub.email).join('\n')
  const emailsFile = path.join(DATA_DIR, 'confirmed-emails.txt')
  await writeFile(emailsFile, emailsList)

  // 2. Lista con fechas (más info)
  const emailsWithDates = confirmedSubscribers.map(sub => {
    const date = new Date(sub.confirmedAt || sub.subscribedAt).toLocaleDateString()
    return `${sub.email} - ${date}`
  }).join('\n')
  const detailedFile = path.join(DATA_DIR, 'emails-with-dates.txt')
  await writeFile(detailedFile, emailsWithDates)

  // 3. CSV simple
  const csvContent = [
    'email,fecha_confirmacion',
    ...confirmedSubscribers.map(sub => {
      const date = sub.confirmedAt || sub.subscribedAt
      return `${sub.email},${date}`
    })
  ].join('\n')
  
  const csvFile = path.join(DATA_DIR, `emails-${today}.csv`)
  await writeFile(csvFile, csvContent)

  console.log('\n✅ ARCHIVOS ACTUALIZADOS:')
  console.log(`📧 Emails simples: ${emailsFile}`)
  console.log(`📅 Con fechas: ${detailedFile}`)
  console.log(`📊 CSV del día: ${csvFile}`)
  console.log(`\n📈 Total confirmados: ${confirmedSubscribers.length}`)
  
  // Mostrar los emails en consola para copy/paste rápido
  console.log('\n📋 EMAILS PARA COPIAR:')
  console.log('='.repeat(40))
  confirmedSubscribers.forEach(sub => console.log(sub.email))
  console.log('='.repeat(40))
}

async function showList() {
  const subscribers = await getSubscribers()
  const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)

  if (confirmedSubscribers.length === 0) {
    console.log('📭 No hay emails confirmados.')
    return
  }

  console.log(`\n📧 LISTA ACTUALIZADA (${confirmedSubscribers.length} confirmados):`)
  console.log('='.repeat(50))
  
  confirmedSubscribers.forEach((sub, index) => {
    const date = new Date(sub.confirmedAt || sub.subscribedAt).toLocaleDateString()
    console.log(`${index + 1}. ${sub.email} - ${date}`)
  })
  
  console.log('='.repeat(50))
}

async function showAll() {
  const subscribers = await getSubscribers()

  if (subscribers.length === 0) {
    console.log('📭 No hay suscriptores.')
    return
  }

  console.log(`\n📋 TODOS LOS SUSCRIPTORES (${subscribers.length} total):`)
  console.log('='.repeat(60))
  
  subscribers.forEach((sub, index) => {
    const status = sub.confirmed ? '✅' : '⏳'
    const date = new Date(sub.subscribedAt).toLocaleDateString()
    console.log(`${index + 1}. ${status} ${sub.email} - ${date}`)
  })
  
  console.log('='.repeat(60))
  
  const confirmed = subscribers.filter(s => s.confirmed).length
  console.log(`\n📊 Confirmados: ${confirmed} | Pendientes: ${subscribers.length - confirmed}`)
}

// Comando principal
const command = process.argv[2]

switch (command) {
  case 'list':
    await showList()
    break
  case 'export':
    await exportEmails()
    break
  case 'all':
    await showAll()
    break
  default:
    console.log(`
📧 NEWSLETTER MANAGER - SIMPLE
==============================

Comandos disponibles:

  npm run newsletter list     - Ver emails confirmados
  npm run newsletter export   - Exportar a archivos locales
  npm run newsletter all      - Ver todos (confirmados + pendientes)

Ejemplos:
  npm run newsletter list     # Ver la lista actual
  npm run newsletter export   # Actualizar archivos locales
`)
}