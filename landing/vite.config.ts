/// <reference types="vitest" />
import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

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
    fs: {
      allow: ['..'],
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
