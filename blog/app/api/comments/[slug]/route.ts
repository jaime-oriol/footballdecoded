// app/api/comments/[slug]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { writeFile, readFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import crypto from 'crypto'

interface Comment {
  id: string
  name: string
  email: string
  message: string
  timestamp: string
  approved: boolean
  ip?: string
  userAgent?: string
  likes: number
  replies: Reply[]
  parentId?: string // Para respuestas anidadas
  avatar?: string // NUEVO: Avatar del usuario
}

interface Reply {
  id: string
  name: string
  email: string
  message: string
  timestamp: string
  approved: boolean
  likes: number
  avatar?: string // NUEVO: Avatar del usuario
}

interface CommentsData {
  postSlug: string
  comments: Comment[]
}

const DATA_DIR = path.join(process.cwd(), 'data', 'comments')

// Función para leer comentarios de un post
async function getCommentsForPost(slug: string): Promise<CommentsData> {
  const filePath = path.join(DATA_DIR, `${slug}.json`)

  try {
    if (!existsSync(filePath)) {
      return { postSlug: slug, comments: [] }
    }

    const data = await readFile(filePath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('Error reading comments:', error)
    return { postSlug: slug, comments: [] }
  }
}

// Función para guardar comentarios
async function saveCommentsForPost(slug: string, commentsData: CommentsData): Promise<void> {
  try {
    // Crear directorio si no existe
    if (!existsSync(DATA_DIR)) {
      await mkdir(DATA_DIR, { recursive: true })
    }

    const filePath = path.join(DATA_DIR, `${slug}.json`)
    await writeFile(filePath, JSON.stringify(commentsData, null, 2))
  } catch (error) {
    console.error('Error saving comments:', error)
    throw error
  }
}

// Validaciones
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function sanitizeInput(input: string): string {
  return input.trim().slice(0, 500) // Máximo 500 caracteres
}

function generateCommentId(): string {
  return `comment-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`
}

// Detectar spam básico
function isLikelySpam(name: string, message: string): boolean {
  const spamKeywords = ['viagra', 'casino', 'bitcoin', 'crypto', 'loan', 'mortgage']
  const text = `${name} ${message}`.toLowerCase()

  // Detectar múltiples enlaces
  const linkCount = (text.match(/https?:\/\//g) || []).length
  if (linkCount > 2) return true

  // Detectar palabras spam
  return spamKeywords.some((keyword) => text.includes(keyword))
}

// GET - Obtener comentarios aprobados de un post
export async function GET(request: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  try {
    const { slug } = await params
    const commentsData = await getCommentsForPost(slug)

    // Solo devolver comentarios aprobados
    const approvedComments = commentsData.comments.filter((comment) => comment.approved)

    return NextResponse.json({
      postSlug: slug,
      comments: approvedComments,
      total: approvedComments.length,
    })
  } catch (error) {
    console.error('Error getting comments:', error)
    return NextResponse.json({ error: 'Error obteniendo comentarios' }, { status: 500 })
  }
}

// POST - Agregar nuevo comentario
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params
    const { name, email, message, avatar } = await request.json()

    // Validaciones básicas
    if (!name || !email || !message) {
      return NextResponse.json({ error: 'Todos los campos son obligatorios' }, { status: 400 })
    }

    if (!isValidEmail(email)) {
      return NextResponse.json({ error: 'Email no válido' }, { status: 400 })
    }

    // Sanitizar inputs
    const cleanName = sanitizeInput(name)
    const cleanMessage = sanitizeInput(message)

    if (cleanMessage.length < 10) {
      return NextResponse.json(
        { error: 'El comentario debe tener al menos 10 caracteres' },
        { status: 400 }
      )
    }

    // Detectar spam
    if (isLikelySpam(cleanName, cleanMessage)) {
      return NextResponse.json({ error: 'Comentario detectado como spam' }, { status: 400 })
    }

    // Crear nuevo comentario
    const newComment: Comment = {
      id: generateCommentId(),
      name: cleanName,
      email: email.toLowerCase(),
      message: cleanMessage,
      timestamp: new Date().toISOString(),
      approved: true, // Aprobación automática como solicitaste
      ip: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown',
      userAgent: request.headers.get('user-agent') || 'unknown',
      likes: 0,
      replies: [],
      parentId: undefined,
      avatar: avatar || undefined, // NUEVO: Guardar avatar
    }

    // Leer comentarios existentes
    const commentsData = await getCommentsForPost(slug)

    // Añadir nuevo comentario
    commentsData.comments.push(newComment)

    // Guardar
    await saveCommentsForPost(slug, commentsData)

    // Respuesta exitosa
    return NextResponse.json({
      message: '¡Comentario publicado correctamente!',
      comment: {
        id: newComment.id,
        name: newComment.name,
        message: newComment.message,
        timestamp: newComment.timestamp,
        avatar: newComment.avatar,
      },
    })
  } catch (error) {
    console.error('Error adding comment:', error)
    return NextResponse.json({ error: 'Error interno del servidor' }, { status: 500 })
  }
}
