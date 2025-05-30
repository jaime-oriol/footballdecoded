import TOCInline from 'pliny/ui/TOCInline'
import Pre from 'pliny/ui/Pre'
import BlogNewsletterForm from 'pliny/ui/BlogNewsletterForm'
import type { MDXComponents } from 'mdx/types'
import Image from './Image'
import CustomLink from './Link'

// Table wrapper inline - ya no necesitamos archivo separado
const TableWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full overflow-x-auto">
    <table>{children}</table>
  </div>
)

export const components: MDXComponents = {
  Image,
  TOCInline,
  a: CustomLink,
  pre: Pre,
  table: TableWrapper,
  BlogNewsletterForm,
}
