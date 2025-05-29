import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'

export const POSTS_PER_PAGE = 4

// Obtener todos los posts publicados ordenados por fecha
export function getAllPublishedPosts(): CoreContent<Blog>[] {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  return allPosts.filter(post => !post.draft)
}

// Obtener posts filtrados por sección
export function getPostsBySection(section: string): CoreContent<Blog>[] {
  const publishedPosts = getAllPublishedPosts()
  return publishedPosts.filter(post => post.section === section)
}

// Calcular paginación para un conjunto de posts
export function calculatePagination(
  posts: CoreContent<Blog>[], 
  currentPage: number = 1
) {
  const totalPages = Math.ceil(posts.length / POSTS_PER_PAGE)
  
  // Validaciones
  if (currentPage <= 0 || currentPage > totalPages) {
    return null // Esto debería resultar en 404
  }

  const startIndex = (currentPage - 1) * POSTS_PER_PAGE
  const endIndex = startIndex + POSTS_PER_PAGE
  const displayPosts = posts.slice(startIndex, endIndex)

  return {
    posts: displayPosts,
    pagination: {
      currentPage,
      totalPages,
    },
    totalPosts: posts.length
  }
}

// Generar parámetros estáticos para paginación
export function generatePaginationParams(posts: CoreContent<Blog>[]) {
  const totalPages = Math.ceil(posts.length / POSTS_PER_PAGE)
  return Array.from({ length: totalPages }, (_, i) => ({ 
    page: (i + 1).toString() 
  }))
}