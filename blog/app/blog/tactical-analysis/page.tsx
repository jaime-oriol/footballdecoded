import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({
  title: 'Tactical Analysis',
  description:
    'Estudio de estilos, partidos clave, entrenadores y dinámicas de juego a través de modelos, métricas y visualizaciones tácticas.',
})

export default async function TacticalAnalysisPage() {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)

  // Filtrar posts de esta sección y también posts legacy de 'tactical-structures'
  const sectionPosts = publishedPosts.filter(
    (post) => post.section === 'tactical-analysis' || post.section === 'tactical-structures'
  )

  const pageNumber = 1
  const totalPages = Math.ceil(sectionPosts.length / POSTS_PER_PAGE)
  const initialDisplayPosts = sectionPosts.slice(0, POSTS_PER_PAGE)

  const pagination = {
    currentPage: pageNumber,
    totalPages: totalPages,
  }

  return (
    <ArticlesLayout
      posts={sectionPosts}
      initialDisplayPosts={initialDisplayPosts}
      pagination={pagination}
      title="Tactical Analysis"
      section="tactical-analysis"
    />
  )
}
