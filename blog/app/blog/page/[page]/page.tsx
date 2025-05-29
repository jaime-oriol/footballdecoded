import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { notFound } from 'next/navigation'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const generateStaticParams = async () => {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)
  const totalPages = Math.ceil(publishedPosts.length / POSTS_PER_PAGE)

  const paths = Array.from({ length: totalPages }, (_, i) => ({
    page: (i + 1).toString(),
  }))

  return paths
}

export default async function BlogPaginationPage(props: { params: Promise<{ page: string }> }) {
  const params = await props.params
  const pageNumber = parseInt(params.page)

  // Validar número de página
  if (isNaN(pageNumber) || pageNumber <= 0) {
    return notFound()
  }

  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)
  const totalPages = Math.ceil(publishedPosts.length / POSTS_PER_PAGE)

  // Validar que la página existe
  if (pageNumber > totalPages) {
    return notFound()
  }

  // Calcular índices para la paginación
  const startIndex = (pageNumber - 1) * POSTS_PER_PAGE
  const endIndex = startIndex + POSTS_PER_PAGE
  const initialDisplayPosts = publishedPosts.slice(startIndex, endIndex)

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
