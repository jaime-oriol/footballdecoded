/** @type {import("pliny/config").PlinyConfig } */
const siteMetadata = {
  // === IDENTIDAD CENTRAL ===
  title: 'FootballDecoded',
  author: 'Jaime Oriol',
  headerTitle: 'FootballDecoded',
  description:
    'Análisis táctico avanzado, métricas cuantitativas y scouting funcional para el fútbol profesional.',
  language: 'es-ES',
  locale: 'es-ES',

  // === CONFIGURACIÓN TÉCNICA ===
  theme: 'system',
  siteUrl: 'https://footballdecoded.com', // ← DOMINIO PERSONALIZADO
  siteRepo: 'https://github.com/jaime-oriol/FootballDecoded',
  siteLogo: `${process.env.BASE_PATH || ''}/static/images/logo.png`,
  socialBanner: `${process.env.BASE_PATH || ''}/static/images/football-decoded-banner.jpg`,

  // === CONTACTO ===
  email: 'joriolgo@gmail.com',
  github: 'https://github.com/jaime-oriol',
  x: 'https://x.com/JaimeOriol_',
  linkedin: 'https://www.linkedin.com/in/jaime-oriol-goicoechea-801313276/',
  instagram: 'https://www.instagram.com/orio1_/',

  // === HERRAMIENTAS ACTIVAS ===
  analytics: {
    umamiAnalytics: {
      umamiWebsiteId: '00cdd21e-95b5-41a4-b2c1-aa12fd3fde2b',
      umamiSrc: 'https://cloud.umami.is/script.js',
    },
  },

  comments: {
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

  search: {
    provider: 'kbar',
    kbarConfig: {
      searchDocumentsPath: `${process.env.BASE_PATH || ''}/search.json`,
    },
  },

  newsletter: {
    provider: 'convertkit',
  },
}

module.exports = siteMetadata
