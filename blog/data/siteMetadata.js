/** @type {import("pliny/config").PlinyConfig } */
const siteMetadata = {
  title: 'FootballDecoded',
  author: 'Jaime Oriol Goicoechea',
  headerTitle: 'FootballDecoded',
  description: 'Análisis táctico y técnico del fútbol de élite desde la estructura, los datos y la ingeniería aplicada. Portfolio especializado en la intersección entre táctica, métricas cuantitativas y metodologías avanzadas de análisis futbolístico.',
  language: 'es-ES',
  theme: 'system', // system, dark or light
  siteUrl: 'https://footballdecoded.com', // Actualizar cuando tengas el dominio definitivo
  siteRepo: 'https://github.com/jaime-oriol/footballdecoded', // Repositorio público del proyecto
  siteLogo: `${process.env.BASE_PATH || ''}/static/images/logo.png`,
  socialBanner: `${process.env.BASE_PATH || ''}/static/images/footballdecoded-social-banner.png`,
  mastodon: '',
  email: 'joriolgo@gmail.com',
  github: 'https://github.com/jaime-oriol',
  x: 'https://x.com/JaimeOriol_',
  twitter: 'https://twitter.com/JaimeOriol_', // Mantener ambos por compatibilidad
  facebook: '',
  youtube: '', // Preparado para futuras visualizaciones en video
  linkedin: 'https://www.linkedin.com/in/jaime-oriol-goicoechea-801313276/',
  threads: '',
  instagram: 'https://www.instagram.com/orio1_/',
  medium: '', // Preparado para cross-posting de artículos técnicos
  bluesky: '',
  locale: 'es-ES',

  // Configuración de navegación
  stickyNav: true, // Navegación fija para mejor experiencia en análisis largos

  // Configuración de analytics para tracking profesional
  analytics: {
    // Umami Analytics - Recomendado para privacidad y análisis detallado
    umamiAnalytics: {
      umamiWebsiteId: process.env.NEXT_UMAMI_ID,
      // src: 'https://eu.umami.is/script.js' // Si usas servidor europeo
    },

    // Google Analytics - Alternativa para análisis más profundo
    // googleAnalytics: {
    //   googleAnalyticsId: process.env.NEXT_GA_ID, // e.g. G-XXXXXXX
    // },

    // Plausible Analytics - Alternativa centrada en privacidad
    // plausibleAnalytics: {
    //   plausibleDataDomain: 'footballdecoded.com',
    //   src: 'https://plausible.io/js/script.js'
    // },

    // Simple Analytics - Opción minimalista
    // simpleAnalytics: {},

    // PostHog - Para análisis de comportamiento avanzado
    // posthogAnalytics: {
    //   posthogProjectApiKey: process.env.NEXT_POSTHOG_KEY,
    // },
  },

  // Configuración de newsletter para audiencia técnica
  newsletter: {
    // Buttondown - Recomendado para contenido técnico y análisis
    // provider: 'buttondown',

    // Mailchimp - Para audiencia más amplia
    // provider: 'mailchimp',

    // ConvertKit - Para funnel de contenido profesional
    // provider: 'convertkit',

    // Klaviyo - Para segmentación avanzada
    // provider: 'klaviyo',

    // EmailOctopus - Alternativa económica
    // provider: 'emailoctopus',

    // Beehive - Para creators de contenido técnico
    // provider: 'beehiiv',

    provider: '', // Activar cuando esté listo para captar audiencia
  },

  // Sistema de comentarios profesional
  comments: {
    provider: 'giscus', // GitHub Discussions - ideal para audiencia técnica
    giscusConfig: {
      // Configuración para GitHub Discussions
      // Visita https://giscus.app/ para configurar
      repo: process.env.NEXT_PUBLIC_GISCUS_REPO, // 'jaime-oriol/footballdecoded'
      repositoryId: process.env.NEXT_PUBLIC_GISCUS_REPOSITORY_ID,
      category: process.env.NEXT_PUBLIC_GISCUS_CATEGORY, // 'General' o 'Announcements'
      categoryId: process.env.NEXT_PUBLIC_GISCUS_CATEGORY_ID,
      mapping: 'pathname', // Mapeo por URL - más estable para SEO
      reactions: '1', // Habilitar reacciones para engagement
      metadata: '0', // No enviar metadata por privacidad
      theme: 'light', // Tema por defecto
      darkTheme: 'transparent_dark', // Tema para modo oscuro
      themeURL: '', // URL de tema personalizado si se necesita
      lang: 'es', // Idioma de la interfaz
    },

    // Utterances - Alternativa basada en GitHub Issues
    // utterancesConfig: {
    //   repo: process.env.NEXT_PUBLIC_UTTERANCES_REPO,
    //   issueTerm: 'pathname',
    //   label: 'Comment 💬',
    //   theme: 'github-light',
    //   darkTheme: 'github-dark',
    // },

    // Disqus - Para audiencia más general
    // disqusConfig: {
    //   shortname: process.env.NEXT_PUBLIC_DISQUS_SHORTNAME,
    // },
  },

  // Sistema de búsqueda
  search: {
    provider: 'kbar', // Búsqueda local con comando ⌘+K
    kbarConfig: {
      searchDocumentsPath: `${process.env.BASE_PATH || ''}/search.json`,
      // Configuración adicional para búsqueda avanzada
      // defaultActions: definidos en SearchProvider personalizado
      // onSearchDocumentsLoad: función personalizada para procesamiento
    },

    // Algolia DocSearch - Para búsqueda más avanzada cuando crezca el contenido
    // provider: 'algolia',
    // algoliaConfig: {
    //   appId: process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
    //   apiKey: process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY,
    //   indexName: 'footballdecoded',
    //   contextualSearch: true,
    //   externalUrlRegex: 'external\\.com|domain\\.com',
    //   searchParameters: {},
    //   searchPagePath: 'search',
    // },
  },
}

module.exports = siteMetadata