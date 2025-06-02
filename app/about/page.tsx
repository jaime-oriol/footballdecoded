import { genPageMetadata } from 'app/seo'
import PhotoCarousel from '@/components/PhotoCarousel'
import BioSection from '@/components/BioSection'

export const metadata = genPageMetadata({ title: 'About' })

export default function Page() {
  return (
    <div className="w-full">
      {/* Header de la sección - consistente con otras páginas */}
      <div className="w-full px-4 pt-8 pb-6 sm:px-6">
        <div className="space-y-4">
          <h1 className="font-headings text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl dark:text-slate-100">
            Sobre mí
          </h1>
          <p className="font-body text-xl leading-relaxed text-slate-600 dark:text-slate-400">
            La historia detrás de FootballDecoded
          </p>
        </div>
      </div>

      {/* Galería de fotos profesional - ancho completo */}
      <PhotoCarousel />

      {/* Sección biográfica con tipografía FootballDecoded - ancho completo */}
      <BioSection />
    </div>
  )
}
