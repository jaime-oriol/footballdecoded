import Link from './Link'
import siteMetadata from '@/content/siteMetadata'
import SocialIcon from '@/components/social-icons'

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-700">
      <div className="mt-16 flex flex-col items-center">
        {/* Iconos de redes sociales */}
        <div className="mb-4 flex space-x-4">
          <SocialIcon kind="mail" href={`mailto:${siteMetadata.email}`} size={6} />
          <SocialIcon kind="linkedin" href={siteMetadata.linkedin} size={6} />
          <SocialIcon kind="x" href={siteMetadata.x} size={6} />
          <SocialIcon kind="github" href={siteMetadata.github} size={6} />
          <SocialIcon kind="instagram" href={siteMetadata.instagram} size={6} />
        </div>

        {/* Información de copyright - tipografía mono para datos técnicos */}
        <div className="mb-3 flex space-x-2 font-mono text-sm text-slate-500 dark:text-slate-400">
          <div>{siteMetadata.author}</div>
          <div>{` • `}</div>
          <div>{`© ${new Date().getFullYear()}`}</div>
          <div>{` • `}</div>
          <Link
            href="/"
            className="transition-colors hover:text-slate-700 dark:hover:text-slate-300"
          >
            {siteMetadata.title}
          </Link>
        </div>

        {/* Descripción profesional - estilo dossier */}
        <div className="mb-8 text-center">
          <p className="font-body text-sm text-slate-600 dark:text-slate-400">
            Análisis táctico y métricas avanzadas para el fútbol profesional
          </p>
        </div>
      </div>
    </footer>
  )
}
