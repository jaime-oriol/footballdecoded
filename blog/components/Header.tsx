import siteMetadata from '@/content/siteMetadata'
import headerNavLinks from '@/content/headerNavLinks'
import Logo from '@/content/logo.svg'
import Link from './Link'
import MobileNav from './MobileNav'
import ThemeSwitch from './ThemeSwitch'
import SearchButton from './SearchButton'
import ArticleDropdown from './ArticleDropdown'

const Header = () => {
  let headerClass = 'flex items-center w-full bg-white dark:bg-gray-950 justify-between py-10'
  if (siteMetadata.stickyNav) {
    headerClass += ' sticky top-0 z-50'
  }

  return (
    <header className={headerClass}>
      <Link href="/" aria-label={siteMetadata.headerTitle}>
        <div className="flex items-center justify-between">
          <div className="mr-3">
            <Logo />
          </div>
          {typeof siteMetadata.headerTitle === 'string' ? (
            <div className="hidden h-6 text-2xl font-semibold sm:block">
              {siteMetadata.headerTitle}
            </div>
          ) : (
            siteMetadata.headerTitle
          )}
        </div>
      </Link>
      <div className="flex items-center space-x-4 leading-5 sm:-mr-6 sm:space-x-6">
        {/* CAMBIO IMPORTANTE: Removemos overflow-x-auto y ajustamos para dropdown */}
        <div className="hidden items-center gap-x-4 sm:flex md:gap-x-6 lg:gap-x-8">
          {headerNavLinks
            .filter((link) => link.href !== '/')
            .map((link) => {
              // Si es el enlace de artículos, usar el dropdown
              if (link.title === 'Artículos') {
                return <ArticleDropdown key="articles" />
              }

              // Para el resto de enlaces, usar el componente normal
              return (
                <Link
                  key={link.title}
                  href={link.href}
                  className="hover:text-primary-500 dark:hover:text-primary-400 m-1 font-medium whitespace-nowrap text-gray-900 dark:text-gray-100"
                >
                  {link.title}
                </Link>
              )
            })}
        </div>
        <SearchButton />
        <ThemeSwitch />
        <MobileNav />
      </div>
    </header>
  )
}

export default Header
