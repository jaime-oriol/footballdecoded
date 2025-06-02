import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({
  title: 'Analytical Scouting',
  description:
    'Identificación de perfiles tácticos mediante segmentación avanzada, agrupación funcional y análisis comparativo.',
})

export default async function AnalyticalScoutingPage() {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)

  // Filtrar posts de esta sección y también posts legacy de 'scouting'
  const sectionPosts = publishedPosts.filter(
    (post) => post.section === 'analytical-scouting' || post.section === 'scouting'
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
      title="Analytical Scouting"
      section="analytical-scouting"
    />
  )
}
