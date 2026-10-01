import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const FRONTEND_DIR = path.resolve(__dirname, '../../')
const indexHtml = fs.readFileSync(path.resolve(FRONTEND_DIR, 'index.html'), 'utf-8')
const mainTs = fs.readFileSync(path.resolve(FRONTEND_DIR, 'src/main.ts'), 'utf-8')

describe('CSS entrypoint', () => {
  it('index.html has no stylesheet link to the design system', () => {
    const links = indexHtml.match(/<link[^>]*rel=["']stylesheet["'][^>]*>/g) ?? []
    expect(links.filter((l) => l.includes('erato-design-system'))).toEqual([])
  })

  it('main.ts imports tokens, bundle and layout in order', () => {
    const tokens = mainTs.indexOf("'@design-system/tokens.css'")
    const bundle = mainTs.indexOf("'@design-system/components/bundle.css'")
    const layout = mainTs.indexOf("'./styles/layout.css'")
    expect(tokens).toBeGreaterThanOrEqual(0)
    expect(bundle).toBeGreaterThan(tokens)
    expect(layout).toBeGreaterThan(bundle)
  })
})
