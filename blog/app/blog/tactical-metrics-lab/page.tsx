import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({ 
  title: 'Tactical Metrics Lab',
  description: 'Cuantificación avanzada del impacto táctico mediante datos y programación.'
})

export default async function TacticalMetricsLabPage() {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter(post => !post.draft)
  
  // Filtrar solo posts de esta sección
  const sectionPosts = publishedPosts.filter(post => post.section === 'tactical-metrics-lab')
  
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
      title="Tactical Metrics Lab"
      section="tactical-metrics-lab"
    />
  )
}