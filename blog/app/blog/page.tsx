import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({
  title: 'Artículos',
  description:
    'Análisis táctico avanzado, scouting funcional y métricas aplicadas al fútbol profesional.',
})

export default async function BlogPage() {
  // Obtener TODOS los posts y ordenarlos (más reciente primero)
  const allPosts = allCoreContent(sortPosts(allBlogs))

  // Filtrar solo los posts publicados (no drafts)
  const publishedPosts = allPosts.filter((post) => !post.draft)

  const pageNumber = 1
  const totalPages = Math.ceil(publishedPosts.length / POSTS_PER_PAGE)

  // Mostrar exactamente los primeros 4 artículos
  const initialDisplayPosts = publishedPosts.slice(0, POSTS_PER_PAGE)

  const pagination = {
    currentPage: pageNumber,
    totalPages: totalPages,
  }

  return (
    <ArticlesLayout
      posts={publishedPosts}
      initialDisplayPosts={initialDisplayPosts}
      pagination={pagination}
      title="Todos los Artículos"
    />
  )
}
