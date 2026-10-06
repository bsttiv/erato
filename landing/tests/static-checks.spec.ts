// @vitest-environment node
import { describe, it, expect, afterEach } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { noindexPlugin, resolveAppUrl } from '../vite.config'
import { checkCopyViolations, findStaticStyleAttributes } from './helpers/sfc-check'

const LANDING_ROOT = path.resolve(__dirname, '..')
const SRC_DIR = path.resolve(LANDING_ROOT, 'src')
const INDEX_HTML_PATH = path.resolve(LANDING_ROOT, 'index.html')

function getAllFiles(dir: string): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  const files: string[] = []
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...getAllFiles(fullPath))
    } else {
      files.push(fullPath)
    }
  }
  return files
}

describe('landing static checks', () => {
  const originalVercelEnv = process.env.VERCEL_ENV

  afterEach(() => {
    if (originalVercelEnv === undefined) {
      delete process.env.VERCEL_ENV
    } else {
      process.env.VERCEL_ENV = originalVercelEnv
    }
  })

  describe('resolveAppUrl fail-closed resolution', () => {
    it('throws in production when VITE_APP_URL is missing or empty', () => {
      expect(() => resolveAppUrl('production', undefined)).toThrow(/VITE_APP_URL/)
      expect(() => resolveAppUrl('production', '')).toThrow(/VITE_APP_URL/)
      expect(() => resolveAppUrl('production', '   ')).toThrow(/VITE_APP_URL/)
    })

    it('returns the trimmed URL without trailing slashes in production when provided', () => {
      expect(resolveAppUrl('production', 'https://app.erato.com/')).toBe('https://app.erato.com')
      expect(resolveAppUrl('production', 'https://app.erato.com///')).toBe('https://app.erato.com')
    })

    it('falls back to http://localhost:5173 outside production when unset', () => {
      expect(resolveAppUrl('development', undefined)).toBe('http://localhost:5173')
      expect(resolveAppUrl('preview', '')).toBe('http://localhost:5173')
      expect(resolveAppUrl(undefined, undefined)).toBe('http://localhost:5173')
    })
  })

  it('extractor unit test: reports only "Ojo!" from AST and ignores directive expressions like v-if="!abierto"', () => {
    const sampleSfc = `<template><div v-if="!abierto"><template #a><p>Hola</p></template><span>Ojo!</span></div></template>`
    const violations = checkCopyViolations(sampleSfc, 'sample.vue')

    expect(violations).toEqual([
      {
        file: 'sample.vue',
        reason: 'exclamation mark in copy',
        line: 'Ojo!',
      },
    ])
  })

  it('extractor emoji check: permits copyright/trademark symbols (©, ®, ™) and flags real emojis like 🎸', () => {
    const validSfc = `<template><p>© 2026 Erato ® ™</p></template>`
    expect(checkCopyViolations(validSfc, 'valid.vue')).toEqual([])

    const emojiSfc = `<template><p>Música 🎸</p></template>`
    expect(checkCopyViolations(emojiSfc, 'emoji.vue')).toEqual([
      {
        file: 'emoji.vue',
        reason: 'emoji in copy',
        line: 'Música 🎸',
      },
    ])
  })

  it('landing.css includes prefers-reduced-motion media query and 980px collapse rules', () => {
    const landingCss = fs.readFileSync(path.resolve(SRC_DIR, 'styles/landing.css'), 'utf-8')

    // @media (prefers-reduced-motion: reduce)
    expect(landingCss).toMatch(/@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)/)
    const reducedMotionIdx = landingCss.indexOf('@media (prefers-reduced-motion: reduce)')
    const reducedMotionBlock = reducedMotionIdx !== -1 ? landingCss.slice(reducedMotionIdx, reducedMotionIdx + 400) : ''
    expect(reducedMotionBlock).toContain('.er-slide')
    expect(reducedMotionBlock).toContain('.er-dot')
    expect(reducedMotionBlock).toContain('.er-arrow')

    // @media (max-width: 980px)
    expect(landingCss).toMatch(/@media\s*\(\s*max-width:\s*980px\s*\)/)
    const collapseBlock = landingCss.match(/@media\s*\(\s*max-width:\s*980px\s*\)\s*\{([\s\S]*?)\n\}/)?.[0] || ''
    expect(collapseBlock).toMatch(/\.er-wrap[^}]*grid-template-columns:\s*1fr/)
    expect(collapseBlock).toMatch(/\.er-steps-grid[^}]*grid-template-columns:\s*1fr/)
    expect(collapseBlock).toMatch(/\.er-plans-grid[^}]*grid-template-columns:\s*1fr/)
    expect(collapseBlock).toMatch(/\.er-visual[^}]*display:\s*none/)
    expect(collapseBlock).toMatch(/\.er-topnav[^}]*display:\s*none/)
    expect(collapseBlock).toMatch(/\.er-dots[^}]*display:\s*none/)
  })

  it('contains no hex colors in landing/src (design system tokens only)', () => {
    const files = getAllFiles(SRC_DIR)
    const hexColorRegex = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-fA-F_a-zA-Z])/g

    const violations: { file: string; match: string }[] = []

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8')
      const matches = content.match(hexColorRegex)
      if (matches) {
        for (const m of matches) {
          violations.push({ file: path.relative(LANDING_ROOT, file), match: m })
        }
      }
    }

    expect(violations).toEqual([])
  })

  it('contains no exclamation marks or emoji in copy/templates', () => {
    const files = getAllFiles(SRC_DIR).filter((f) => f.endsWith('.vue'))
    const violations: { file: string; reason: string; line: string }[] = []

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8')
      violations.push(...checkCopyViolations(content, path.relative(LANDING_ROOT, file)))
    }

    expect(violations).toEqual([])
  })

  it('injects noindex meta in index.html outside of production and omits it in production', () => {
    const rawHtml = fs.readFileSync(INDEX_HTML_PATH, 'utf-8')
    expect(rawHtml).not.toContain('<meta name="robots" content="noindex">')

    const plugin = noindexPlugin()
    const transform = plugin.transformIndexHtml as (html: string) => string

    // In preview
    process.env.VERCEL_ENV = 'preview'
    const previewHtml = transform(rawHtml)
    expect(previewHtml).toContain('<meta name="robots" content="noindex">')

    // In development / undefined
    delete process.env.VERCEL_ENV
    const devHtml = transform(rawHtml)
    expect(devHtml).toContain('<meta name="robots" content="noindex">')

    // In production
    process.env.VERCEL_ENV = 'production'
    const prodHtml = transform(rawHtml)
    expect(prodHtml).not.toContain('<meta name="robots" content="noindex">')
  })

  it('contains no static style attributes in landing/src templates', () => {
    const vueFiles = getAllFiles(SRC_DIR).filter((f) => f.endsWith('.vue'))
    const violations: { file: string; style: string }[] = []

    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8')
      violations.push(...findStaticStyleAttributes(content, path.relative(LANDING_ROOT, file)))
    }

    expect(violations).toEqual([])
  })

  it('uses var(--token) or neutral values for theme/font/radius properties in landing/src styles', () => {
    const files = getAllFiles(SRC_DIR).filter((f) => f.endsWith('.css') || f.endsWith('.vue'))
    const propertiesToCheck = [
      'color',
      'background',
      'background-color',
      'border-color',
      'fill',
      'stroke',
      'border-radius',
      'font-family',
    ]

    const neutralValues = new Set(['transparent', 'currentColor', 'inherit', 'none', '0', '50%'])
    const violations: { file: string; prop: string; value: string }[] = []

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8')
      const cssChunks: string[] = []
      if (file.endsWith('.css')) {
        cssChunks.push(content)
      } else {
        const styleMatches = content.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)
        for (const match of styleMatches) {
          cssChunks.push(match[1])
        }
      }

      for (const chunk of cssChunks) {
        const cleanChunk = chunk.replace(/\/\*[\s\S]*?\*\//g, '')
        const declRegex = /([a-z-]+)\s*:\s*([^;{}]+)/gi
        let m: RegExpExecArray | null
        while ((m = declRegex.exec(cleanChunk)) !== null) {
          const prop = m[1].trim().toLowerCase()
          const val = m[2].trim()

          if (propertiesToCheck.includes(prop)) {
            const hasVar = val.includes('var(--')
            const isNeutral = neutralValues.has(val)
            if (!hasVar && !isNeutral) {
              violations.push({
                file: path.relative(LANDING_ROOT, file),
                prop,
                value: val,
              })
            }
          }
        }
      }
    }

    expect(violations).toEqual([])
  })

  it('ensures tokens on --bg-100 meet WCAG contrast >= 4.5 in both themes and landing.css sets slides background to var(--bg-100)', () => {
    const tokensCss = fs.readFileSync(path.resolve(LANDING_ROOT, '../erato-design-system/tokens.css'), 'utf-8')
    const landingCss = fs.readFileSync(path.resolve(SRC_DIR, 'styles/landing.css'), 'utf-8')

    function parseThemeTokens(block: string) {
      const map: Record<string, string> = {}
      const regex = /--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})/gi
      let match
      while ((match = regex.exec(block)) !== null) {
        map[match[1]] = match[2]
      }
      return map
    }

    const nocheBlock = tokensCss.match(/\[data-theme="noche"\]\s*\{([^}]+)\}/i)?.[1] ||
      tokensCss.match(/:root[^{]*\{([^}]+)\}/i)?.[1] || ''
    const matineBlock = tokensCss.match(/\[data-theme="matine"\]\s*\{([^}]+)\}/i)?.[1] || ''

    const nocheTokens = parseThemeTokens(nocheBlock)
    const matineTokens = parseThemeTokens(matineBlock)

    function luminance(hex: string) {
      const rgb = hex.replace('#', '').match(/.{2}/g)!.map(x => parseInt(x, 16) / 255)
      const a = rgb.map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4))
      return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722
    }
    function contrastRatio(h1: string, h2: string) {
      const l1 = luminance(h1), l2 = luminance(h2)
      return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
    }

    const checkColors = ['ink', 'ink-muted', 'ink-faint', 'amber', 'moss']

    for (const color of checkColors) {
      const nocheRatio = contrastRatio(nocheTokens[color], nocheTokens['bg-100'])
      expect(nocheRatio).toBeGreaterThanOrEqual(4.5)

      const matineRatio = contrastRatio(matineTokens[color], matineTokens['bg-100'])
      expect(matineRatio).toBeGreaterThanOrEqual(4.5)
    }

    const setsBg100 = /\.er-landing-main\s*\{[^}]*background:\s*var\(--bg-100\)/.test(landingCss) ||
      /\.er-slide\s*\{[^}]*background:\s*var\(--bg-100\)/.test(landingCss)
    expect(setsBg100).toBe(true)
  })
})
