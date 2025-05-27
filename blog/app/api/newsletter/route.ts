import { NewsletterAPI } from 'pliny/newsletter'
import siteMetadata from '@/content/siteMetadata'

export const dynamic = 'force-static'

const handler = NewsletterAPI({
  // @ts-ignore
  provider: siteMetadata.newsletter.provider,
})

export { handler as GET, handler as POST }
