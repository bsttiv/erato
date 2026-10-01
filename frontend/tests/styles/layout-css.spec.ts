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

    it('.er-textarea exists, mirrors .er-input tokens and holds no literal colors', () => {
      const body = rulesFor('.er-textarea')
      expect(body.length).toBeGreaterThan(0)
      expect(declaration(body, 'border')).toContain('var(--line-strong)')
      expect(declaration(body, 'background')).toBe('var(--bg-100)')
      expect(declaration(body, 'color')).toBe('var(--ink)')
      expect(declaration(body, 'border-radius')).toBe('var(--radius-control)')
      expect(declaration(body, 'width')).toBe('100%')
      expect(declaration(body, 'resize')).toBe('vertical')
      expect(declaration(body, 'padding')).toMatch(/var\(--space-/)
      expect(declaration(body, 'font-family')).toMatch(/var\(--font-/)
      expect(declaration(rulesFor('.er-textarea::placeholder'), 'color')).toBe('var(--ink-faint)')
      expect(declaration(rulesFor('.er-textarea:focus-visible'), 'outline')).toContain(
        'var(--focus-ring)'
      )
      expect(body.join('\n')).not.toMatch(/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/)
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

describe('modal opacity', () => {
  const css = stripCssComments(fs.readFileSync(LAYOUT_CSS_PATH, 'utf8'))

  function ruleBody(selector: string): string | null {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const match = new RegExp(`(?:^|})\\s*${escaped}\\s*\\{([^}]*)\\}`).exec(css)
    return match ? match[1] : null
  }

  it('does not apply opacity to the backdrop itself, which would also fade the dialog child', () => {
    const body = ruleBody('.er-modal-backdrop')
    expect(body).not.toBeNull()
    expect(body).not.toMatch(/(^|[;\s])opacity\s*:/)
  })

  it('dims the page through a separate backdrop layer that uses a token color', () => {
    const body = ruleBody('.er-modal-backdrop::before')
    expect(body).not.toBeNull()
    expect(body).toMatch(/background-color:\s*var\(--bg-000\)/)
    expect(body).toMatch(/opacity\s*:/)
  })

  it('keeps the dialog on an opaque background token', () => {
    const body = ruleBody('.er-modal')
    expect(body).not.toBeNull()
    expect(body).toMatch(/background-color:\s*var\(--bg-[0-9]+\)/)
    expect(body).not.toMatch(/opacity\s*:/)
  })
})

describe('er-field-grid and er-crumb layout rules', () => {
  const css = stripCssComments(fs.readFileSync(LAYOUT_CSS_PATH, 'utf8'))

  function ruleBody(selector: string): string | null {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const match = new RegExp(`(?:^|})\\s*${escaped}\\s*\\{([^}]*)\\}`).exec(css)
    return match ? match[1] : null
  }

  it('.er-field-grid uses minmax(0, 1fr) to prevent overflow', () => {
    const body = ruleBody('.er-field-grid')
    expect(body).not.toBeNull()
    expect(body).toMatch(/grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\)/)
  })

  it('.er-field-grid input and select have width: 100% and min-width: 0', () => {
    const match = css.match(/\.er-field-grid\s+(?:input|\.er-input)[^{]*\{([^}]*)\}/)
    expect(match, 'Expected .er-field-grid input/select rule').not.toBeNull()
    if (match) {
      expect(match[1]).toMatch(/width:\s*100%/)
      expect(match[1]).toMatch(/min-width:\s*0/)
    }
  })

  it('.er-crumb a has hover/underline rule with no hex or rgb literals', () => {
    const hoverMatch = css.match(/\.er-crumb\s+a:hover[^{]*\{([^}]*)\}/)
    expect(hoverMatch, 'Expected .er-crumb a:hover rule').not.toBeNull()
    if (hoverMatch) {
      expect(hoverMatch[1]).toMatch(/text-decoration:\s*underline/)
      expect(hoverMatch[1]).not.toMatch(/#([0-9a-fA-F]{3,8})\b/)
      expect(hoverMatch[1]).not.toMatch(/\b(rgb|rgba|hsl|hsla)\s*\(/i)
    }
  })
})

describe('er-brand and er-topbar-brand stylesheet contract', () => {
  const css = stripCssComments(fs.readFileSync(LAYOUT_CSS_PATH, 'utf8'))

  function ruleBody(selector: string): string | null {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const match = new RegExp(`(?:^|})\\s*${escaped}\\s*\\{([^}]*)\\}`).exec(css)
    return match ? match[1] : null
  }

  it('.er-brand rule exists and uses only tokens without hex or rgb literals', () => {
    const body = ruleBody('.er-brand')
    expect(body, 'Expected .er-brand rule in layout.css').not.toBeNull()
    if (body) {
      expect(body).not.toMatch(/#([0-9a-fA-F]{3,8})\b/)
      expect(body).not.toMatch(/\b(rgb|rgba|hsl|hsla)\s*\(/i)
    }
  })

  it('.er-topbar-brand has no text styling (font-family, font-size, letter-spacing, color)', () => {
    const body = ruleBody('.er-topbar-brand')
    expect(body).not.toBeNull()
    if (body) {
      expect(body).not.toMatch(/(?:^|[;\s])font-family\s*:/)
      expect(body).not.toMatch(/(?:^|[;\s])font-size\s*:/)
      expect(body).not.toMatch(/(?:^|[;\s])letter-spacing\s*:/)
      expect(body).not.toMatch(/(?:^|[;\s])color\s*:/)
    }
  })
})

describe('responsive 768px layout and drawer', () => {
  const rawCss = fs.readFileSync(LAYOUT_CSS_PATH, 'utf8')
  const css = stripCssComments(rawCss)

  function mediaBlock(source: string, query: string | RegExp): string | null {
    const pattern = typeof query === 'string' ? query : query.source
    const re = new RegExp(`@media[^{]*${pattern}[^{]*\\{`, 'i')
    const match = re.exec(source)
    if (!match) return null

    let depth = 1
    let index = match.index + match[0].length
    const startIndex = index

    while (index < source.length && depth > 0) {
      const char = source[index]
      if (char === '{') {
        depth++
      } else if (char === '}') {
        depth--
      }
      index++
    }

    if (depth === 0) {
      return source.slice(startIndex, index - 1)
    }
    return null
  }

  it('contains a single @media (max-width: 768px) block', () => {
    const block = mediaBlock(css, 'max-width:\\s*768px')
    expect(block, 'Expected @media (max-width: 768px) block').not.toBeNull()
  })

  it('media block mentions required responsive selectors', () => {
    const block = mediaBlock(css, 'max-width:\\s*768px')
    expect(block).not.toBeNull()
    if (block) {
      expect(block).toContain('.er-layout')
      expect(block).toContain('.er-comp-columns')
      expect(block).toContain('.er-auth')
      expect(block).toContain('.er-field-grid')
      expect(block).toContain('.er-sidebar--open')
    }
  })

  it('new selectors .er-drawer-toggle and .er-drawer-backdrop exist with token-only values', () => {
    expect(css).toMatch(/\.er-drawer-toggle\b/)
    expect(css).toMatch(/\.er-drawer-backdrop\b/)

    const toggleMatches = css.match(/\.er-drawer-toggle[^{]*\{([^}]*)\}/g) || []
    const backdropMatches = css.match(/\.er-drawer-backdrop[^{]*\{([^}]*)\}/g) || []
    const combined = [...toggleMatches, ...backdropMatches].join('\n')

    expect(combined).not.toMatch(/#([0-9a-fA-F]{3,8})\b/)
    expect(combined).not.toMatch(/\b(rgb|rgba|hsl|hsla)\s*\(/i)
    expect(combined).not.toMatch(/\b[0-9]+px\s+radius/i)
  })

  it('prefers-reduced-motion: reduce rule removes transitions', () => {
    const reducedMotionBlock = mediaBlock(css, 'prefers-reduced-motion:\\s*reduce')
    expect(reducedMotionBlock, 'Expected prefers-reduced-motion: reduce block').not.toBeNull()
    if (reducedMotionBlock) {
      expect(reducedMotionBlock).toMatch(/transition:\s*none/)
    }
  })

  it('backdrop uses --bg-000 on a ::before layer with no opacity on the panel container', () => {
    const backdropBeforeMatch = css.match(/\.er-drawer-backdrop::before\s*\{([^}]*)\}/)
    expect(backdropBeforeMatch, 'Expected .er-drawer-backdrop::before rule').not.toBeNull()
    if (backdropBeforeMatch) {
      expect(backdropBeforeMatch[1]).toMatch(/background(?:-color)?:\s*var\(--bg-000\)/)
      expect(backdropBeforeMatch[1]).toMatch(/opacity\s*:/)
    }

    const backdropRuleMatch = css.match(/\.er-drawer-backdrop\s*\{([^}]*)\}/)
    if (backdropRuleMatch) {
      expect(backdropRuleMatch[1]).not.toMatch(/(?:^|[;\s])opacity\s*:/)
    }
  })
})

describe('chord carousel and responsive polish in layout.css', () => {
  const rawCss = fs.readFileSync(LAYOUT_CSS_PATH, 'utf8')
  const css = stripCssComments(rawCss)

  function mediaBlock(source: string, query: string | RegExp): string | null {
    const pattern = typeof query === 'string' ? query : query.source
    const re = new RegExp(`@media[^{]*${pattern}[^{]*\\{`, 'i')
    const match = re.exec(source)
    if (!match) return null

    let depth = 1
    let index = match.index + match[0].length
    const startIndex = index

    while (index < source.length && depth > 0) {
      const char = source[index]
      if (char === '{') {
        depth++
      } else if (char === '}') {
        depth--
      }
      index++
    }

    if (depth === 0) {
      return source.slice(startIndex, index - 1)
    }
    return null
  }

  it('carousel rules: inside 768px block .er-chord-grid has scroll-snap-type and .er-field has scroll-snap-align', () => {
    const block = mediaBlock(css, 'max-width:\\s*768px')
    expect(block).not.toBeNull()
    if (block) {
      expect(block).toMatch(/\.er-chord-grid\b[^{]*\{[^}]*scroll-snap-type\s*:/)
      expect(block).toMatch(/\.er-chord-grid\s*>\s*\.er-field\b[^{]*\{[^}]*scroll-snap-align\s*:/)
    }
  })

  it('new selectors .er-chord-carousel and .er-chord-nav exist with token-only values and nav hidden above 768px', () => {
    expect(css).toMatch(/\.er-chord-carousel\b/)
    expect(css).toMatch(/\.er-chord-nav\b/)

    const baseNavMatch = css.match(/\.er-chord-nav\b[^{]*\{([^}]*)\}/)
    expect(baseNavMatch).not.toBeNull()
    if (baseNavMatch) {
      expect(baseNavMatch[1]).toMatch(/display\s*:\s*none/)
    }

    const carouselMatches = css.match(/\.er-chord-carousel[^{]*\{([^}]*)\}/g) || []
    const navMatches = css.match(/\.er-chord-nav[^{]*\{([^}]*)\}/g) || []
    const combined = [...carouselMatches, ...navMatches].join('\n')

    expect(combined).not.toMatch(/#([0-9a-fA-F]{3,8})\b/)
    expect(combined).not.toMatch(/\b(rgb|rgba|hsl|hsla)\s*\(/i)
    expect(combined).not.toMatch(/\b[0-9]+px\s+radius/i)
  })

  it('polish rules present in layout.css under 768px block', () => {
    const block = mediaBlock(css, 'max-width:\\s*768px')
    expect(block).not.toBeNull()
    if (block) {
      expect(block).toMatch(/overflow-x\s*:\s*auto/)
      expect(block).toMatch(/flex-wrap\s*:\s*wrap/)
      expect(block).toMatch(/min-width\s*:\s*0/)
      expect(block).toMatch(/flex-shrink\s*:\s*0/)
      expect(block).toMatch(/max-height/)
    }
  })
})




