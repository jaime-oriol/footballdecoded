import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({
  title: 'Advanced Metrics',
  description:
    'Exploración profunda de métricas avanzadas, modelos predictivos y visualización de datos aplicada al fútbol profesional.',
})

export default async function AdvancedMetricsPage() {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)

  // Filtrar posts de esta sección y también posts legacy de 'tactical-metrics-lab'
  const sectionPosts = publishedPosts.filter(
    (post) => post.section === 'advanced-metrics' || post.section === 'tactical-metrics-lab'
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
      title="Advanced Metrics"
      section="advanced-metrics"
    />
  )
}
