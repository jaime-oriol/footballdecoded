/** @type {import("pliny/config").PlinyConfig } */
const siteMetadata = {
  // === IDENTIDAD PROFESIONAL FOOTBALLDECODED ===
  title: 'FootballDecoded',
  author: 'Jaime Oriol',
  headerTitle: 'FootballDecoded',
  description:
    'Portfolio técnico y analítico de referencia en fútbol profesional. Análisis táctico avanzado, métricas cuantitativas y scouting funcional orientado a la integración en cuerpos técnicos de clubes de élite europeos.',
  language: 'es-ES',
  locale: 'es-ES',

  // === CONTACTO Y REDES SOCIALES ===
  email: 'joriolgo@gmail.com',
  github: 'https://github.com/jaime-oriol',
  x: 'https://x.com/JaimeOriol_',
  linkedin: 'https://www.linkedin.com/in/jaime-oriol-goicoechea-801313276/',
  instagram: 'https://www.instagram.com/orio1_/',
  
  // Otras redes no utilizadas (mantenidas para compatibilidad)
  twitter: '', // Dejamos vacío ya que usamos X
  facebook: '',
  youtube: '',
  bluesky: '',
  threads: '',
  medium: '',
  mastodon: '',

  // === CONFIGURACIÓN TÉCNICA PROFESIONAL ===
  theme: 'system', // system, dark or light
  siteUrl: 'https://footballdecoded.com',
  siteRepo: 'https://github.com/jaime-oriol/FootballDecoded',
  siteLogo: `${process.env.BASE_PATH || ''}/static/images/logo.png`,
  socialBanner: `${process.env.BASE_PATH || ''}/static/images/football-decoded-banner.jpg`,

  // === SEO TÉCNICO ESPECIALIZADO ===
  keywords: [
    'análisis táctico fútbol',
    'métricas avanzadas fútbol',
    'scouting funcional',
    'estructuras tácticas',
    'visualización datos deportivos',
    'análisis cuantitativo fútbol',
    'tactical analysis',
    'football analytics',
    'sports data science',
    'football scouting',
    'xG metrics',
    'PPDA analysis',
    'football tactical structures',
  ],

  // === CONFIGURACIÓN DE ANALYTICS PROFESIONAL ===
  analytics: {
    // Umami configurado y activo
    umamiAnalytics: {
      // Recomendado para portfolio profesional (privacidad)
      umamiWebsiteId: '00cdd21e-95b5-41a4-b2c1-aa12fd3fde2b',
      umamiSrc: 'https://cloud.umami.is/script.js',
    },
    // Otras opciones disponibles pero no activas
    plausibleAnalytics: {
      plausibleDataDomain: '', // e.g. footballdecoded.com
    },
    simpleAnalytics: {},
    posthogAnalytics: {
      posthogProjectApiKey: '', // e.g. 123e4567-e89b-12d3-a456-426614174000
    },
    googleAnalytics: {
      googleAnalyticsId: '', // e.g. G-XXXXXXX
    },
  },

  // === SISTEMA DE COMENTARIOS TÉCNICO ===
  comments: {
    // GitHub Discussions - Ideal para audiencia técnica
    giscusConfig: {
      repo: 'jaime-oriol/FootballDecoded',
      repositoryId: 'R_kgDOOxLT5g',
      category: 'General',
      categoryId: 'DIC_kwDOOxLT5s4Cqo_m',
      mapping: 'pathname',
      reactions: '1',
      metadata: '0',
      inputPosition: 'bottom',
      theme: 'preferred_color_scheme',
      lang: 'es',
      loading: 'lazy',
    },
  },

  // === CONFIGURACIÓN DE BÚSQUEDA TÉCNICA ===
  search: {
    provider: 'kbar', // kbar or algolia
    kbarConfig: {
      searchDocumentsPath: `${process.env.BASE_PATH || ''}/search.json`, // path to load documents to search
      // Términos técnicos priorizados para búsqueda
      defaultActions: [
        {
          id: 'tactical-structures',
          name: 'Tactical Structures',
          keywords: 'táctica estructuras sistemas formaciones',
          section: 'Análisis Técnico',
        },
        {
          id: 'functional-scouting',
          name: 'Functional Scouting',
          keywords: 'scouting funcional perfiles jugadores',
          section: 'Análisis Técnico',
        },
        {
          id: 'tactical-metrics',
          name: 'Tactical Metrics Lab',
          keywords: 'métricas avanzadas datos programación',
          section: 'Análisis Técnico',
        },
      ],
    },
    algoliaConfig: {
      appId: process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
      apiKey: process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY,
      indexName: process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME,
    },
  },

  // === CONFIGURACIÓN DE NEWSLETTER PROFESIONAL ===
  newsletter: {
    // Recomendado: ConvertKit para audiencia técnica profesional
    provider: 'convertkit',
  },

  // === CONFIGURACIÓN DE CONTACTO EMPRESARIAL ===
  contactForm: {
    provider: 'netlify', // netlify, formspree, or custom
    // Configuración específica para consultas profesionales
    subjects: [
      'Colaboración Técnica',
      'Oportunidad Laboral',
      'Consultoría Analítica',
      'Proyecto Conjunto',
      'Otro',
    ],
  },

  // === OPEN GRAPH PROFESIONAL ===
  openGraph: {
    type: 'website',
    site_name: 'FootballDecoded',
    title: 'FootballDecoded - Análisis Táctico y Métricas Avanzadas',
    description:
      'Portfolio técnico especializado en análisis táctico, scouting funcional y métricas avanzadas de fútbol profesional.',
    images: [
      {
        url: `${process.env.BASE_PATH || ''}/static/images/football-decoded-og.jpg`,
        width: 1200,
        height: 630,
        alt: 'FootballDecoded - Análisis Técnico de Fútbol Profesional',
      },
    ],
  },

  // === TWITTER CARDS TÉCNICO ===
  twitter: {
    card: 'summary_large_image',
    title: 'FootballDecoded - Análisis Táctico Profesional',
    description:
      'Portfolio técnico: análisis táctico, scouting funcional y métricas avanzadas para cuerpos técnicos de élite.',
    images: [`${process.env.BASE_PATH || ''}/static/images/football-decoded-twitter.jpg`],
  },

  // === STRUCTURED DATA PROFESIONAL ===
  structuredData: {
    type: 'ProfessionalService',
    name: 'FootballDecoded',
    description: 'Servicios de análisis táctico y métricas avanzadas para fútbol profesional',
    serviceType: 'Análisis Deportivo Profesional',
    areaServed: 'Europa',
    availableLanguage: ['es', 'en'],
    knowsAbout: [
      'Análisis Táctico',
      'Scouting Funcional',
      'Métricas Avanzadas',
      'Visualización de Datos Deportivos',
      'Programación Aplicada al Fútbol',
    ],
  },
}

module.exports = siteMetadata