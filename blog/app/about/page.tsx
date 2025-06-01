import { genPageMetadata } from 'app/seo'
import PhotoCarousel from '@/components/PhotoCarousel'
import BioSection from '@/components/BioSection'

export const metadata = genPageMetadata({ title: 'About' })

export default function Page() {
  return (
    <>
      {/* Galería de fotos profesional */}
      <PhotoCarousel />

      {/* Sección biográfica con tipografía FootballDecoded */}
      <BioSection />
    </>
  )
}
