// scripts/newsletter-manager.mjs
import { readFile, writeFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const DATA_DIR = path.join(process.cwd(), 'data')
const SUBSCRIBERS_FILE = path.join(DATA_DIR, 'newsletter-subscribers.json')

async function getSubscribers() {
  try {
    if (!existsSync(SUBSCRIBERS_FILE)) {
      console.log('No hay archivo de suscriptores todavía.')
      return []
    }
    const data = await readFile(SUBSCRIBERS_FILE, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('Error leyendo suscriptores:', error)
    return []
  }
}

async function exportToCSV() {
  const subscribers = await getSubscribers()
  const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)

  if (confirmedSubscribers.length === 0) {
    console.log('No hay suscriptores confirmados para exportar.')
    return
  }

  // Crear CSV
  const csvHeader = 'Email,Fecha de suscripción,Fecha de confirmación,IP\n'
  const csvRows = confirmedSubscribers
    .map(
      (sub) => `${sub.email},${sub.subscribedAt},${sub.confirmedAt || 'N/A'},${sub.ip || 'unknown'}`
    )
    .join('\n')

  const csvContent = csvHeader + csvRows
  const csvFile = path.join(
    DATA_DIR,
    `newsletter-confirmed-${new Date().toISOString().split('T')[0]}.csv`
  )

  await writeFile(csvFile, csvContent)
  console.log(`✅ Exportado a: ${csvFile}`)
  console.log(`📊 Total suscriptores confirmados: ${confirmedSubscribers.length}`)
}

async function showStats() {
  const subscribers = await getSubscribers()
  const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)
  const pendingSubscribers = subscribers.filter((sub) => !sub.confirmed)

  console.log('\n📈 ESTADÍSTICAS NEWSLETTER')
  console.log('='.repeat(40))
  console.log(`Total suscriptores: ${subscribers.length}`)
  console.log(`✅ Confirmados: ${confirmedSubscribers.length}`)
  console.log(`⏳ Pendientes: ${pendingSubscribers.length}`)

  if (subscribers.length > 0) {
    // Porcentaje de confirmación
    const confirmationRate = ((confirmedSubscribers.length / subscribers.length) * 100).toFixed(1)
    console.log(`📊 Tasa de confirmación: ${confirmationRate}%`)

    // Últimos 7 días
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    const recentConfirmed = confirmedSubscribers.filter(
      (sub) => new Date(sub.confirmedAt || sub.subscribedAt) > weekAgo
    )
    console.log(`🆕 Confirmados esta semana: ${recentConfirmed.length}`)

    if (confirmedSubscribers.length > 0) {
      // Primer y último confirmado
      const sortedConfirmed = [...confirmedSubscribers].sort(
        (a, b) =>
          new Date(a.confirmedAt || a.subscribedAt) - new Date(b.confirmedAt || b.subscribedAt)
      )
      console.log(
        `🥇 Primer confirmado: ${new Date(sortedConfirmed[0].confirmedAt || sortedConfirmed[0].subscribedAt).toLocaleDateString()}`
      )
      console.log(
        `🏆 Último confirmado: ${new Date(sortedConfirmed[sortedConfirmed.length - 1].confirmedAt || sortedConfirmed[sortedConfirmed.length - 1].subscribedAt).toLocaleDateString()}`
      )

      // Últimos 5 confirmados
      console.log('\n📧 Últimos 5 suscriptores confirmados:')
      confirmedSubscribers
        .slice(-5)
        .reverse()
        .forEach((sub, i) => {
          const confirmDate = sub.confirmedAt
            ? new Date(sub.confirmedAt).toLocaleDateString()
            : 'Confirmación pendiente'
          console.log(`${i + 1}. ${sub.email} - ${confirmDate}`)
        })
    }

    if (pendingSubscribers.length > 0) {
      console.log('\n⏳ Suscriptores pendientes de confirmación:')
      pendingSubscribers.slice(0, 5).forEach((sub, i) => {
        const subscribeDate = new Date(sub.subscribedAt).toLocaleDateString()
        console.log(`${i + 1}. ${sub.email} - Suscrito: ${subscribeDate}`)
      })
      if (pendingSubscribers.length > 5) {
        console.log(`... y ${pendingSubscribers.length - 5} más`)
      }
    }
  }
  console.log('='.repeat(40))
}

async function exportEmailList() {
  const subscribers = await getSubscribers()
  const confirmedSubscribers = subscribers.filter((sub) => sub.confirmed)

  if (confirmedSubscribers.length === 0) {
    console.log('No hay emails confirmados para exportar.')
    return
  }

  const emailList = confirmedSubscribers.map((sub) => sub.email).join('\n')
  const emailFile = path.join(
    DATA_DIR,
    `confirmed-emails-${new Date().toISOString().split('T')[0]}.txt`
  )

  await writeFile(emailFile, emailList)
  console.log(`✅ Lista de emails confirmados exportada a: ${emailFile}`)
  console.log(`📧 Total emails confirmados: ${confirmedSubscribers.length}`)
}

async function exportAllEmails() {
  const subscribers = await getSubscribers()

  if (subscribers.length === 0) {
    console.log('No hay emails para exportar.')
    return
  }

  const allEmailsList = subscribers
    .map((sub) => `${sub.email} - ${sub.confirmed ? 'Confirmado' : 'Pendiente'}`)
    .join('\n')
  const allEmailsFile = path.join(
    DATA_DIR,
    `all-emails-${new Date().toISOString().split('T')[0]}.txt`
  )

  await writeFile(allEmailsFile, allEmailsList)
  console.log(`✅ Lista completa exportada a: ${allEmailsFile}`)
  console.log(`📧 Total emails: ${subscribers.length}`)
}

// Comando principal
const command = process.argv[2]

switch (command) {
  case 'stats':
    await showStats()
    break
  case 'export-csv':
    await exportToCSV()
    break
  case 'export-emails':
    await exportEmailList()
    break
  case 'export-all':
    await exportAllEmails()
    break
  default:
    console.log(`
📧 NEWSLETTER MANAGER
====================

Comandos disponibles:

  npm run newsletter stats           - Mostrar estadísticas detalladas
  npm run newsletter export-csv      - Exportar solo confirmados a CSV
  npm run newsletter export-emails   - Exportar solo emails confirmados
  npm run newsletter export-all      - Exportar todos (confirmados + pendientes)

Ejemplos:
  npm run newsletter stats
  npm run newsletter export-emails
`)
}
