import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const ROOT_DIR = path.resolve(__dirname, '../../../')
const LAYOUT_CSS_PATH = path.resolve(ROOT_DIR, 'frontend/src/styles/layout.css')
const BUNDLE_CSS_PATH = path.resolve(ROOT_DIR, 'erato-design-system/components/bundle.css')
const SRC_DIR = path.resolve(ROOT_DIR, 'frontend/src')
const FEATURES_DIR = path.resolve(ROOT_DIR, 'frontend/src/features')

function stripCssComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, '')
}

function extractKeyErClasses(css: string): Set<string> {
  const clean = stripCssComments(css)
  const keyClasses = new Set<string>()

  // Matches CSS rule blocks: selectors { declarations }
  // We handle nested @media blocks by flattening them
  const ruleRegex = /([^{}@]+)\{([^{}]+)\}/g
  let match: RegExpExecArray | null

  while ((match = ruleRegex.exec(clean)) !== null) {
    const rawSelectors = match[1].trim()
    if (rawSelectors.startsWith('@')) continue

    const selectorList = rawSelectors.split(',')
    for (const sel of selectorList) {
      const trimmed = sel.trim()
      if (!trimmed) continue

      // Rightmost compound selector
      const parts = trimmed.split(/[\s>+~]+/)
      const rightmost = parts[parts.length - 1]
      const classMatches = rightmost.match(/\.er-[a-z0-9-]+/g)
      if (classMatches) {
        for (const cls of classMatches) {
          keyClasses.add(cls.slice(1)) // remove leading '.'
        }
      }
    }
  }

  return keyClasses
}

function getAllDefinedErClasses(css: string): Set<string> {
  const clean = stripCssComments(css)
  const classes = new Set<string>()
  const matches = clean.match(/\.er-[a-z0-9-]+/g)
  if (matches) {
    for (const m of matches) {
      classes.add(m.slice(1))
    }
  }
  return classes
}

describe('layout.css stylesheet contract', () => {
  it('exists on disk', () => {
    expect(fs.existsSync(LAYOUT_CSS_PATH)).toBe(true)
  })

  it('maintains key-selector disjointness with bundle.css', () => {
    if (!fs.existsSync(LAYOUT_CSS_PATH)) {
      throw new Error(`layout.css not found at ${LAYOUT_CSS_PATH}`)
    }
    const layoutCss = fs.readFileSync(LAYOUT_CSS_PATH, 'utf-8')
    const bundleCss = fs.readFileSync(BUNDLE_CSS_PATH, 'utf-8')

    const layoutKeys = extractKeyErClasses(layoutCss)
    const bundleKeys = extractKeyErClasses(bundleCss)

    const intersection: string[] = []
    for (const key of layoutKeys) {
      if (bundleKeys.has(key)) {
        intersection.push(key)
      }
    }

    expect(
      intersection,
      `layout.css key selectors collide with bundle.css: ${intersection.join(', ')}`
    ).toEqual([])
  })

  it('holds no literal design values (colors, fonts, radii)', () => {
    if (!fs.existsSync(LAYOUT_CSS_PATH)) {
      throw new Error(`layout.css not found at ${LAYOUT_CSS_PATH}`)
    }
    const layoutCss = stripCssComments(fs.readFileSync(LAYOUT_CSS_PATH, 'utf-8'))

    // 1. No hex colors: #fff, #ffffff, etc.
    const hexMatch = layoutCss.match(/#([0-9a-fA-F]{3,8})\b/g)
    expect(hexMatch, `Found literal hex colors: ${hexMatch?.join(', ')}`).toBeNull()

    // 2. No rgb/rgba/hsl/hsla functions
    const rgbHslMatch = layoutCss.match(/\b(rgb|rgba|hsl|hsla)\s*\(/gi)
    expect(rgbHslMatch, `Found rgb/hsl color functions: ${rgbHslMatch?.join(', ')}`).toBeNull()

    // 3. font-family lines must only use var(--font-...) or inherit
    const lines = layoutCss.split('\n')
    for (const line of lines) {
      if (/^\s*font-family\s*:/i.test(line)) {
        const val = line.split(':')[1]?.trim().replace(/;$/, '')
        const isValid = /var\(--font-[a-z0-9-]+\)|inherit/i.test(val || '')
        expect(isValid, `Literal font-family forbidden: "${line.trim()}"`).toBe(true)
      }
    }

    // 4. border-radius lines must only use var(--radius-...), 0, 50%, or inherit
    for (const line of lines) {
      if (/^\s*border-radius\s*:/i.test(line)) {
        const val = line.split(':')[1]?.trim().replace(/;$/, '')
        const isValid = /var\(--radius-[a-z0-9-]+\)|0|50%|inherit/i.test(val || '')
        expect(isValid, `Literal border-radius forbidden: "${line.trim()}"`).toBe(true)
      }
    }
  })

  it('every referenced er-* class in frontend/src resolves in bundle.css or layout.css', () => {
    if (!fs.existsSync(LAYOUT_CSS_PATH)) {
      throw new Error(`layout.css not found at ${LAYOUT_CSS_PATH}`)
    }
    const layoutCss = fs.readFileSync(LAYOUT_CSS_PATH, 'utf-8')
    const bundleCss = fs.readFileSync(BUNDLE_CSS_PATH, 'utf-8')

    const definedClasses = new Set<string>([
      ...getAllDefinedErClasses(layoutCss),
      ...getAllDefinedErClasses(bundleCss),
    ])

    // Documented allowlist for dynamic or reference-faithful exceptions
    const allowlist = new Set<string>([
      'er-btn--', // dynamically constructed template prefix ('er-btn--' + variant)
      'er-tag--', // dynamically constructed template prefix ('er-tag--' + tone)
      'er-btn--quiet', // bundle.js default variant (reference-faithful inert class)
      'er-btn--primary',
      'er-btn--ghost',
      'er-btn--danger',
      'er-tag--amber',
      'er-tag--wine',
      'er-tag--moss',
      'er-tag--neutral',
      'er-tag--sm',
      'er-tag--dot',
      'er-tag--label',
      'er-lyrics--max', // toggled by useAutoScroll
      'er-chord-diagram',
      'er-guitar',
      'er-piano',
    ])

    function scanFiles(dir: string, fileList: string[] = []): string[] {
      const entries = fs.readdirSync(dir, { withFileTypes: true })
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name)
        if (entry.isDirectory()) {
          if (entry.name !== 'node_modules' && entry.name !== 'dist') {
            scanFiles(fullPath, fileList)
          }
        } else if (entry.isFile() && (entry.name.endsWith('.vue') || (entry.name.endsWith('.ts') && !entry.name.endsWith('.spec.ts')))) {
          fileList.push(fullPath)
        }
      }
      return fileList
    }

    const files = scanFiles(SRC_DIR)
    const missingClasses = new Set<string>()

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8')
      const matches = content.match(/\ber-[a-z0-9-]+/g)
      if (matches) {
        for (const cls of matches) {
          if (!definedClasses.has(cls) && !allowlist.has(cls)) {
            missingClasses.add(cls)
          }
        }
      }
    }

    expect(
      Array.from(missingClasses),
      `Unresolved er-* classes referenced in src: ${Array.from(missingClasses).join(', ')}`
    ).toEqual([])
  })

  describe('anchor and textarea rules', () => {
    const css = () => stripCssComments(fs.readFileSync(LAYOUT_CSS_PATH, 'utf-8'))

    function rulesFor(selector: string): string[] {
      const out: string[] = []
      const re = /([^{}@]+)\{([^{}]+)\}/g
      let m: RegExpExecArray | null
      const source = css()
      while ((m = re.exec(source)) !== null) {
        const sels = m[1].split(',').map((s) => s.trim())
        if (sels.includes(selector)) out.push(m[2])
      }
      return out
    }

    function declaration(body: string[], prop: string): string | undefined {
      for (const b of body) {
        const hit = b.match(new RegExp(`(?:^|[;\\s])${prop}\\s*:\\s*([^;]+)`))
        if (hit) return hit[1].trim()
      }
      return undefined
    }

    it.each([
      '.er-crumb a',
      '.er-sectionnav a',
      '.er-sidebar-foot a',
    ])('%s is styled with a token color and no underline', (selector) => {
      const body = rulesFor(selector)
      expect(body.length, `missing rule for ${selector}`).toBeGreaterThan(0)
      expect(declaration(body, 'color')).toMatch(/^var\(--[a-z0-9-]+\)$/)
      expect(declaration(body, 'text-decoration')).toBe('none')
    })

    it.each(['.er-crumb a', '.er-sectionnav a', '.er-sidebar-foot a'])(
      '%s has hover and keyboard focus rules using tokens',
      (selector) => {
        const hover = rulesFor(`${selector}:hover`)
        expect(declaration(hover, 'color')).toBe('var(--ink)')
        const focus = rulesFor(`${selector}:focus-visible`)
        expect(declaration(focus, 'outline')).toContain('var(--focus-ring)')
      }
    )

    it('jump-nav links carry vertical padding and an amber hover indicator', () => {
      const body = rulesFor('.er-sectionnav a')
      expect(declaration(body, 'padding')).toMatch(/var\(--space-/)
      const hover = rulesFor('.er-sectionnav a:hover')
      expect(declaration(hover, 'border-bottom-color')).toBe('var(--amber)')
    })
  })

  it('no inline style attributes exist in frontend/src/features/', () => {
    function scanFiles(dir: string, fileList: string[] = []): string[] {
      const entries = fs.readdirSync(dir, { withFileTypes: true })
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name)
        if (entry.isDirectory()) {
          scanFiles(fullPath, fileList)
        } else if (entry.isFile() && entry.name.endsWith('.vue')) {
          fileList.push(fullPath)
        }
      }
      return fileList
    }

    const vueFiles = scanFiles(FEATURES_DIR)
    const filesWithInlineStyles: string[] = []

    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8')
      // Look for style="..." or :style="..." in templates (not in <style> block)
      const templateMatch = content.match(/<template>([\s\S]*?)<\/template>/)
      if (templateMatch) {
        const templateContent = templateMatch[1]
        if (/\bstyle\s*=\s*["']/.test(templateContent)) {
          filesWithInlineStyles.push(path.relative(ROOT_DIR, file))
        }
      }
    }

    expect(
      filesWithInlineStyles,
      `Inline style attributes found in feature components: ${filesWithInlineStyles.join(', ')}`
    ).toEqual([])
  })
})
