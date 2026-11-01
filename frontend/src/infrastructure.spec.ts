import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { mount } from '@vue/test-utils'
import LogoMark from './components/atoms/LogoMark.vue'

describe('Scaffold infrastructure', () => {
  it('INFRA-050 runs Vitest with Vue components and jsdom', () => {
    const wrapper = mount(LogoMark)
    expect(wrapper.element).toBeInstanceOf(Element)
    wrapper.unmount()
  })

  it('INFRA-055 does not depend on React or a reference bundle', () => {
    const root = process.cwd()
    const pkg = JSON.parse(readFileSync(`${root}/package.json`, 'utf8'))
    const dependencies = { ...pkg.dependencies, ...pkg.devDependencies }
    expect(dependencies).not.toHaveProperty('react')
    expect(dependencies).not.toHaveProperty('react-dom')
    for (const entry of readdirSync(`${root}/src`, { recursive: true, withFileTypes: true })) {
      if (entry.isFile() && /\.(js|ts|vue|css)$/.test(entry.name)) {
        expect(readFileSync(`${entry.parentPath}/${entry.name}`, 'utf8')).not.toMatch(/import\s.*bundle\.js/)
      }
    }
  })
})
