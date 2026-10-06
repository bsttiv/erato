// @vitest-environment node
import { describe, it, expect, afterEach } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { noindexPlugin } from '../vite.config'
import { checkCopyViolations } from './helpers/sfc-check'

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
})
