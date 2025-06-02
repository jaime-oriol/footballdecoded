# 🛠️ Guía de Desarrollo - FootballDecoded

## Estructura del Proyecto

### Organización por Responsabilidades

- **`app/`** - Next.js App Router (páginas y API routes)
- **`components/`** - Componentes React reutilizables
- **`content/`** - Contenido MDX y configuración
- **`layouts/`** - Layouts especializados para diferentes tipos de página
- **`public/`** - Assets estáticos accesibles públicamente

### Convenciones de Nombres

#### Archivos y Componentes

- **Componentes React**: PascalCase (`ArticleCard.tsx`)
- **Páginas**: kebab-case (`about/page.tsx`)
- **Contenido MDX**: kebab-case (`analisis-presion-alta.mdx`)
- **Assets**: kebab-case (`imagen-destacada.jpg`)

#### Secciones del Blog

- `tactical-analysis` - Análisis táctico
- `analytical-scouting` - Scouting funcional
- `advanced-metrics` - Métricas avanzadas

## Creación de Contenido

### Nuevo Artículo

1. Crear archivo en la sección correspondiente:

   ```
   content/articles/{section}/nombre-articulo.mdx
   ```

2. Usar frontmatter estándar:

   ```yaml
   ---
   title: 'Título del Análisis'
   date: '2024-01-15'
   section: 'tactical-analysis'
   image: '/static/images/articles/imagen.jpg'
   tags: ['táctica', 'análisis']
   summary: 'Resumen del artículo'
   ---
   ```

3. Añadir imagen destacada en `public/static/images/articles/`

### Componentes MDX Disponibles

- `<TechnicalConcept>` - Para términos técnicos
- `<Callout>` - Para notas importantes
- `<StatCard>` - Para mostrar métricas
- `<TechnicalQuote>` - Para citas especializadas

## Desarrollo

### Scripts Principales

```bash
npm run dev          # Desarrollo local
npm run build        # Build de producción
npm run lint         # Linting
npm run newsletter   # Gestión de newsletter
```

### Variables de Entorno

Copiar `.env.example` a `.env.local` y configurar:

- NextAuth (OAuth Google)
- Resend (newsletter)
- Umami (analytics)

## Deployment

### Vercel (Producción)

1. Conectar repositorio en Vercel
2. Configurar variables de entorno
3. Deploy automático en push a `main`

### Variables de Producción

- `NEXTAUTH_URL` - URL del sitio
- `NEXTAUTH_SECRET` - Secret de autenticación
- `GOOGLE_CLIENT_ID/SECRET` - OAuth Google
- `RESEND_API_KEY` - Newsletter

## Mantenimiento

### Newsletter

```bash
npm run newsletter list    # Ver suscriptores
npm run newsletter export  # Exportar emails
```

### Assets

- Optimizar imágenes antes de subir
- Mantener estructura organizada en `public/static/`
- Verificar que todos los assets estén en uso

### Contenido

- Revisar enlaces internos regularmente
- Mantener consistencia en frontmatter
- Verificar que las secciones estén actualizadas
