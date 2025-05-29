import { sortPosts, allCoreContent } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import Main from './Main'

export default async function Page() {
  // Obtener todos los posts ordenados por fecha (más reciente primero)
  const sortedPosts = sortPosts(allBlogs)

  // Filtrar solo posts publicados (no drafts)
  const publishedPosts = allCoreContent(sortedPosts).filter((post) => !post.draft)

  // Obtener solo los 3 más recientes para la homepage
  const recentPosts = publishedPosts.slice(0, 3)

  return <Main posts={recentPosts} />
}
