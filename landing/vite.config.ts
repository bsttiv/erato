/// <reference types="vitest" />
import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export function resolveAppUrl(
  vercelEnv: string | undefined = process.env.VERCEL_ENV,
  rawUrl: string | undefined = process.env.VITE_APP_URL,
): string {
  const isProduction = vercelEnv === 'production'
  const trimmed = (rawUrl ?? '').trim().replace(/\/+$/, '')

  if (isProduction) {
    if (!trimmed) {
      throw new Error(
        'VITE_APP_URL is required in production (VERCEL_ENV === "production") and must not be empty.',
      )
    }
    return trimmed
  }

  return trimmed || 'http://localhost:5173'
}

export function noindexPlugin(): Plugin {
  return {
    name: 'erato-noindex',
    transformIndexHtml(html: string) {
      if (process.env.VERCEL_ENV !== 'production') {
        const metaTag = '    <meta name="robots" content="noindex">'
        if (html.includes('</head>')) {
          return html.replace('</head>', `${metaTag}\n  </head>`)
        }
        return `${metaTag}\n${html}`
      }
      return html
    },
  }
}

// Validate VITE_APP_URL at config evaluation time
resolveAppUrl()

export default defineConfig({
  plugins: [vue(), noindexPlugin()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@ds-vue': fileURLToPath(new URL('../frontend/src/design-system', import.meta.url)),
      '@design-system': fileURLToPath(new URL('../erato-design-system', import.meta.url)),
    },
  },
  server: {
    port: 5174,
    fs: {
      allow: ['..'],
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
