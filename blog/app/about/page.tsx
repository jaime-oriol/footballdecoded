import { genPageMetadata } from 'app/seo'
import PhotoCarousel from '@/components/PhotoCarousel'
import BioSection from '@/components/BioSection'

export const metadata = genPageMetadata({ title: 'About' })

export default function Page() {
  return (
    <>
      {/* Galería de fotos a pantalla completa */}
      <PhotoCarousel />

      {/* Nueva sección biográfica */}
      <BioSection />
    </>
  )
}
