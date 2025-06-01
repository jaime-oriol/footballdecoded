import { genPageMetadata } from 'app/seo'
import PhotoCarousel from '@/components/PhotoCarousel'
import BioSection from '@/components/BioSection'

export const metadata = genPageMetadata({ title: 'About' })

export default function Page() {
  return (
    <div className="w-full">
      {/* Galería de fotos profesional - ancho completo */}
      <PhotoCarousel />

      {/* Sección biográfica con tipografía FootballDecoded - ancho completo */}
      <BioSection />
    </div>
  )
}
