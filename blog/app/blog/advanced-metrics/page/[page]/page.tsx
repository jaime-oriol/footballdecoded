import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { notFound } from 'next/navigation'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const generateStaticParams = async () => {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)
  const sectionPosts = publishedPosts.filter(
    (post) => post.section === 'advanced-metrics' || post.section === 'tactical-metrics-lab'
  )
  const totalPages = Math.ceil(sectionPosts.length / POSTS_PER_PAGE)

  return Array.from({ length: totalPages }, (_, i) => ({
    page: (i + 1).toString(),
  }))
}

export default async function AdvancedMetricsPaginationPage(props: {
  params: Promise<{ page: string }>
}) {
  const params = await props.params
  const pageNumber = parseInt(params.page)

  if (isNaN(pageNumber) || pageNumber <= 0) {
    return notFound()
  }

  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter((post) => !post.draft)
  const sectionPosts = publishedPosts.filter(
    (post) => post.section === 'advanced-metrics' || post.section === 'tactical-metrics-lab'
  )
  const totalPages = Math.ceil(sectionPosts.length / POSTS_PER_PAGE)

  if (pageNumber > totalPages) {
    return notFound()
  }

  const startIndex = (pageNumber - 1) * POSTS_PER_PAGE
  const endIndex = startIndex + POSTS_PER_PAGE
  const initialDisplayPosts = sectionPosts.slice(startIndex, endIndex)

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
