import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({ 
  title: 'Artículos',
  description: 'Análisis táctico avanzado, scouting funcional y métricas aplicadas al fútbol profesional.'
})

export default async function BlogPage() {
  const posts = allCoreContent(sortPosts(allBlogs))
  const pageNumber = 1
  const totalPages = Math.ceil(posts.length / POSTS_PER_PAGE)
  const initialDisplayPosts = posts.slice(0, POSTS_PER_PAGE * pageNumber)
  const pagination = {
    currentPage: pageNumber,
    totalPages: totalPages,
  }

  return (
    <ArticlesLayout
      posts={posts}
      initialDisplayPosts={initialDisplayPosts}
      pagination={pagination}
      title="Todos los Artículos"
    />
  )
}