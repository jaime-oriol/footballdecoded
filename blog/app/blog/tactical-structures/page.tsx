import { allCoreContent, sortPosts } from 'pliny/utils/contentlayer'
import { allBlogs } from 'contentlayer/generated'
import { genPageMetadata } from 'app/seo'
import ArticlesLayout from '@/components/ArticlesLayout'

const POSTS_PER_PAGE = 4

export const metadata = genPageMetadata({ 
  title: 'Tactical Structures',
  description: 'Análisis de sistemas, fases y principios del juego moderno.'
})

export default async function TacticalStructuresPage() {
  const allPosts = allCoreContent(sortPosts(allBlogs))
  const publishedPosts = allPosts.filter(post => !post.draft)
  
  // Filtrar solo posts de esta sección
  const sectionPosts = publishedPosts.filter(post => post.section === 'tactical-structures')
  
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
      title="Tactical Structures"
      section="tactical-structures"
    />
  )
}