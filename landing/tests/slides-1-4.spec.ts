import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import fs from 'node:fs'
import path from 'node:path'
import App from '../src/App.vue'
import { checkCopyViolations } from './helpers/sfc-check'

describe('Slides 1 to 4 (L2)', () => {
  beforeEach(() => {
    vi.useRealTimers()
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('renders slides in order according to useSlideNav (Inicio, Escribir, Leer, Escuchar)', async () => {
    const wrapper = mount(App, {
      attachTo: document.body,
    })

    // Index 0: Inicio
    expect(wrapper.find('section[aria-label="Inicio"]').exists()).toBe(true)

    // Advance to 1: Escribir
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('section[aria-label="Características: escritura"]').exists()).toBe(true)

    // Advance to 2: Leer
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('section[aria-label="Características: lectura"]').exists()).toBe(true)

    // Advance to 3: Escuchar
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('section[aria-label="Características: audio"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('header has <nav aria-label="Secciones"> with 7 navlinks, active has aria-current="true", and clicking navigates', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    const header = wrapper.find('header')
    expect(header.exists()).toBe(true)

    const nav = header.find('nav[aria-label="Secciones"]')
    expect(nav.exists()).toBe(true)

    const links = nav.findAll('button.er-navlink')
    expect(links.length).toBe(7)

    const expectedLabels = ['Inicio', 'Escribir', 'Leer', 'Escuchar', 'Colaborar', 'Cómo funciona', 'Precios']
    expectedLabels.forEach((label, idx) => {
      expect(links[idx].text()).toBe(label)
    })

    // At slide 0, link 0 has aria-current="true", others do not have the attribute
    expect(links[0].attributes('aria-current')).toBe('true')
    for (let i = 1; i < 7; i++) {
      expect(links[i].attributes('aria-current')).toBeUndefined()
    }

    // Click link 2 (Leer)
    await links[2].trigger('click')
    expect(links[2].attributes('aria-current')).toBe('true')
    expect(links[0].attributes('aria-current')).toBeUndefined()
    expect(wrapper.find('section[aria-label="Características: lectura"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('each slide is a section with reference aria-label and exactly one heading (h1 in Inicio, h2 in others)', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    // Slide 0: Inicio
    const sec0 = wrapper.find('section[aria-label="Inicio"]')
    expect(sec0.exists()).toBe(true)
    expect(sec0.findAll('h1').length).toBe(1)
    expect(sec0.findAll('h2').length).toBe(0)

    // Slide 1: Escribir
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    const sec1 = wrapper.find('section[aria-label="Características: escritura"]')
    expect(sec1.exists()).toBe(true)
    expect(sec1.findAll('h1').length).toBe(0)
    expect(sec1.findAll('h2').length).toBe(1)

    // Slide 2: Leer
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    const sec2 = wrapper.find('section[aria-label="Características: lectura"]')
    expect(sec2.exists()).toBe(true)
    expect(sec2.findAll('h1').length).toBe(0)
    expect(sec2.findAll('h2').length).toBe(1)

    // Slide 3: Escuchar
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await wrapper.vm.$nextTick()
    const sec3 = wrapper.find('section[aria-label="Características: audio"]')
    expect(sec3.exists()).toBe(true)
    expect(sec3.findAll('h1').length).toBe(0)
    expect(sec3.findAll('h2').length).toBe(1)

    wrapper.unmount()
  })

  it('side dots are buttons with aria-label, and the active dot has aria-current="true"', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    const dots = wrapper.findAll('button.er-dot')
    expect(dots.length).toBe(7)
    expect(dots[0].attributes('aria-label')).toBe('Inicio')
    expect(dots[1].attributes('aria-label')).toBe('Escribir')
    expect(dots[2].attributes('aria-label')).toBe('Leer')
    expect(dots[3].attributes('aria-label')).toBe('Escuchar')

    // At slide 0, dot 0 is active
    expect(dots[0].attributes('aria-current')).toBe('true')
    expect(dots[1].attributes('aria-current')).not.toBe('true')

    // Click dot 2 -> active slide becomes Leer, dot 2 has aria-current="true"
    await dots[2].trigger('click')
    expect(dots[2].attributes('aria-current')).toBe('true')
    expect(wrapper.find('section[aria-label="Características: lectura"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('logo button has aria-label "Erato, ir al inicio" and returns to index 0', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    // Move away from 0 first
    const dots = wrapper.findAll('button.er-dot')
    await dots[2].trigger('click')
    expect(wrapper.find('section[aria-label="Características: lectura"]').exists()).toBe(true)

    // Click logo button
    const logoBtn = wrapper.find('button[aria-label="Erato, ir al inicio"]')
    expect(logoBtn.exists()).toBe(true)
    await logoBtn.trigger('click')

    expect(wrapper.find('section[aria-label="Inicio"]').exists()).toBe(true)
    expect(dots[0].attributes('aria-current')).toBe('true')

    wrapper.unmount()
  })

  it('"Revisa las características" button in Inicio navigates to slide 1', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    const revBtn = wrapper.find('button.er-btn--quiet')
    expect(revBtn.exists()).toBe(true)
    expect(revBtn.text()).toContain('Revisa las características')

    await revBtn.trigger('click')
    expect(wrapper.find('section[aria-label="Características: escritura"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('"Empieza gratis" in Inicio is a native anchor with class er-btn', () => {
    const wrapper = mount(App, { attachTo: document.body })

    const startBtn = wrapper.find('section[aria-label="Inicio"] a.er-btn')
    expect(startBtn.exists()).toBe(true)
    expect(startBtn.text()).toContain('Empieza gratis')

    wrapper.unmount()
  })

  it('interactive demos are wrapped inside elements with data-scroll-exclusion', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    // Slide 1 (Escribir) has chord editor in scroll exclusion
    const dots = wrapper.findAll('button.er-dot')
    await dots[1].trigger('click')
    const sec1 = wrapper.find('section[aria-label="Características: escritura"]')
    const chordEditorInSec1 = sec1.find('.er-chord')
    expect(chordEditorInSec1.exists()).toBe(true)
    expect(chordEditorInSec1.element.closest('[data-scroll-exclusion]')).not.toBeNull()

    // Slide 2 (Leer) has lyrics viewer in scroll exclusion
    await dots[2].trigger('click')
    const sec2 = wrapper.find('section[aria-label="Características: lectura"]')
    const lyricsViewer = sec2.find('.er-lyrics')
    expect(lyricsViewer.exists()).toBe(true)
    expect(lyricsViewer.element.closest('[data-scroll-exclusion]')).not.toBeNull()

    // Slide 3 (Escuchar) has demo player in scroll exclusion
    await dots[3].trigger('click')
    const sec3 = wrapper.find('section[aria-label="Características: audio"]')
    const player = sec3.find('.er-player')
    expect(player.exists()).toBe(true)
    expect(player.element.closest('[data-scroll-exclusion]')).not.toBeNull()

    wrapper.unmount()
  })

  it('slide components contain no "!" or emoji in copy and use Spanish tuteo', () => {
    const slidesDir = path.resolve(__dirname, '../src/slides')
    const slideFiles = ['SlideInicio.vue', 'SlideEscribir.vue', 'SlideLeer.vue', 'SlideEscuchar.vue']

    for (const file of slideFiles) {
      const fullPath = path.join(slidesDir, file)
      expect(fs.existsSync(fullPath)).toBe(true)
      const content = fs.readFileSync(fullPath, 'utf-8')
      const violations = checkCopyViolations(content, file)
      expect(violations).toEqual([])
    }
  })
})
