import { Authors, allAuthors } from 'contentlayer/generated'
import { MDXLayoutRenderer } from 'pliny/mdx-components'
import AuthorLayout from '@/layouts/AuthorLayout'
import { coreContent } from 'pliny/utils/contentlayer'
import { genPageMetadata } from 'app/seo'
import PhotoCarousel from '@/components/PhotoCarousel'
import BioSection from '@/components/BioSection'

export const metadata = genPageMetadata({ title: 'About' })

export default function Page() {
  const author = allAuthors.find((p) => p.slug === 'default') as Authors
  const mainContent = coreContent(author)

  return (
    <>
      {/* Galería de fotos a pantalla completa */}
      <PhotoCarousel />

      {/* Nueva sección biográfica */}
      <BioSection />
    </>
  )
}
