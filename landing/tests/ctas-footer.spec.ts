import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import fs from 'node:fs'
import path from 'node:path'
import App from '../src/App.vue'
import { getAppUrl, getLoginUrl, getRegisterUrl } from '../src/config'
import { checkCopyViolations } from './helpers/sfc-check'

describe('Unit L3: slides 5-7, footer, CTAs, responsive and a11y', () => {
  beforeEach(() => {
    vi.useRealTimers()
    vi.unstubAllEnvs()
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
    vi.unstubAllEnvs()
  })

  describe('config.ts URL resolution', () => {
    it('config.ts trims trailing slashes from import.meta.env.VITE_APP_URL and never returns relative fallback', () => {
      vi.stubEnv('VITE_APP_URL', 'https://app.example///')
      expect(getAppUrl()).toBe('https://app.example')
      expect(getLoginUrl()).toBe('https://app.example/login')
      expect(getRegisterUrl()).toBe('https://app.example/register')

      // Without trailing slash
      vi.stubEnv('VITE_APP_URL', 'https://app.example')
      expect(getLoginUrl()).toBe('https://app.example/login')
      expect(getRegisterUrl()).toBe('https://app.example/register')

      // When empty, it falls back to http://localhost:5173
      vi.stubEnv('VITE_APP_URL', '')
      expect(getAppUrl()).toBe('http://localhost:5173')
      expect(getLoginUrl()).toBe('http://localhost:5173/login')
      expect(getRegisterUrl()).toBe('http://localhost:5173/register')
    })
  })

  it('renders slides 4, 5 and 6 (Colaborar, Cómo funciona, Precios) in App and header nav has 6 buttons (excluding Inicio)', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    const navLinks = wrapper.findAll('button.er-navlink')
    expect(navLinks.length).toBe(6)
    const expectedLabels = ['Escribir', 'Leer', 'Escuchar', 'Colaborar', 'Cómo funciona', 'Precios']
    expectedLabels.forEach((label, idx) => {
      expect(navLinks[idx].text()).toBe(label)
    })

    // Navigate to slide 4 (Colaborar) via navLinks[3]
    await navLinks[3].trigger('click')
    expect(wrapper.find('section[aria-label="Características: colaboración"]').exists()).toBe(true)

    // Navigate to slide 5 (Cómo funciona) via navLinks[4]
    await navLinks[4].trigger('click')
    expect(wrapper.find('section[aria-label="Cómo funciona"]').exists()).toBe(true)

    // Navigate to slide 6 (Precios) via navLinks[5]
    await navLinks[5].trigger('click')
    expect(wrapper.find('section[aria-label="Precios"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('header and slide CTAs use VITE_APP_URL via stubEnv and point to /login or /register', async () => {
    vi.stubEnv('VITE_APP_URL', 'https://app.erato.test/')
    const wrapper = mount(App, { attachTo: document.body })

    const header = wrapper.find('header')
    expect(header.exists()).toBe(true)

    // Login link in header
    const loginLink = header.find('a[href="https://app.erato.test/login"]')
    expect(loginLink.exists()).toBe(true)
    expect(loginLink.classes()).toContain('er-btn')
    expect(loginLink.text()).toContain('Iniciar sesión')

    // Primary CTA in header
    const headerRegister = header.find('a[href="https://app.erato.test/register"]')
    expect(headerRegister.exists()).toBe(true)
    expect(headerRegister.classes()).toContain('er-btn')
    expect(headerRegister.text()).toContain('Empieza gratis')

    // Slide 0 CTA: Empieza gratis
    const slide0Register = wrapper.find('section[aria-label="Inicio"] a[href="https://app.erato.test/register"]')
    expect(slide0Register.exists()).toBe(true)
    expect(slide0Register.classes()).toContain('er-btn')

    // Navigate to slide 5 (Cómo funciona)
    const navLinks = wrapper.findAll('button.er-navlink')
    await navLinks[4].trigger('click')
    const slide5Register = wrapper.find('section[aria-label="Cómo funciona"] a[href="https://app.erato.test/register"]')
    expect(slide5Register.exists()).toBe(true)
    expect(slide5Register.classes()).toContain('er-btn')

    // Navigate to slide 6 (Precios)
    await navLinks[5].trigger('click')
    const planCtas = wrapper.findAll('section[aria-label="Precios"] a[href="https://app.erato.test/register"]')
    expect(planCtas.length).toBe(3)
    planCtas.forEach((cta) => {
      expect(cta.classes()).toContain('er-btn')
    })

    wrapper.unmount()
  })

  it('footer uses counter prop ("1 de 7"), placeholder links, and disabled state on navigation arrows', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    const footer = wrapper.find('footer.er-foot')
    expect(footer.exists()).toBe(true)

    const privacyLink = footer.find('a[href="#privacidad"]')
    expect(privacyLink.exists()).toBe(true)
    expect(privacyLink.text()).toBe('Política de privacidad')

    const termsLink = footer.find('a[href="#terminos"]')
    expect(termsLink.exists()).toBe(true)
    expect(termsLink.text()).toBe('Términos de servicio')

    // Counter uses useSlideNav counter format ("1 de 7")
    expect(footer.text()).toContain('1 de 7')

    // Prev button is disabled at index 0
    const prevBtn = footer.find('button[aria-label="Sección anterior"]')
    const nextBtn = footer.find('button[aria-label="Sección siguiente"]')
    expect(prevBtn.attributes('disabled')).toBeDefined()
    expect(nextBtn.attributes('disabled')).toBeUndefined()

    // Advance to end (slide 6)
    const navLinks = wrapper.findAll('button.er-navlink')
    await navLinks[5].trigger('click') // index 6 Precios
    expect(footer.text()).toContain('7 de 7')
    expect(nextBtn.attributes('disabled')).toBeDefined()
    expect(prevBtn.attributes('disabled')).toBeUndefined()

    wrapper.unmount()
  })

  it('plan rows expose visually-hidden screen reader status ("Incluido", "No incluido", "Próximamente") and mark has aria-hidden="true"', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    const navLinks = wrapper.findAll('button.er-navlink')
    await navLinks[5].trigger('click') // Go to Precios

    const rows = wrapper.findAll('.er-plan-row')
    expect(rows.length).toBeGreaterThan(0)

    rows.forEach((row) => {
      const mark = row.find('.er-plan-mark')
      expect(mark.attributes('aria-hidden')).toBe('true')

      const srText = row.find('.er-sr-only')
      expect(srText.exists()).toBe(true)
      expect(['Incluido', 'No incluido', 'Próximamente']).toContain(srText.text())
    })

    wrapper.unmount()
  })

  it('"Ver los planes" in SlideComoFunciona navigates to slide 6 (Precios)', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    const navLinks = wrapper.findAll('button.er-navlink')
    await navLinks[4].trigger('click') // Slide 5: Cómo funciona

    const goPricingBtn = wrapper.find('section[aria-label="Cómo funciona"] button.er-btn--ghost')
    expect(goPricingBtn.exists()).toBe(true)
    expect(goPricingBtn.text()).toContain('Ver los planes')

    await goPricingBtn.trigger('click')
    expect(wrapper.find('section[aria-label="Precios"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('each new slide (Colaborar, Cómo funciona, Precios) has exactly one <h2> heading', () => {
    const wrapper = mount(App, { attachTo: document.body })

    const slidesDir = path.resolve(__dirname, '../src/slides')
    const newSlideFiles = ['SlideColaborar.vue', 'SlideComoFunciona.vue', 'SlidePrecios.vue']

    for (const file of newSlideFiles) {
      const content = fs.readFileSync(path.join(slidesDir, file), 'utf-8')
      const h1Count = (content.match(/<h1[\s>]/g) || []).length
      const h2Count = (content.match(/<h2[\s>]/g) || []).length
      expect(h1Count).toBe(0)
      expect(h2Count).toBe(1)
    }

    wrapper.unmount()
  })

  it('verifies copy violations across slides 4-6 and LandingFooter (no ! or emojis, Spanish tuteo)', () => {
    const componentsToCheck = [
      { path: path.resolve(__dirname, '../src/slides/SlideColaborar.vue'), name: 'SlideColaborar.vue' },
      { path: path.resolve(__dirname, '../src/slides/SlideComoFunciona.vue'), name: 'SlideComoFunciona.vue' },
      { path: path.resolve(__dirname, '../src/slides/SlidePrecios.vue'), name: 'SlidePrecios.vue' },
      { path: path.resolve(__dirname, '../src/components/LandingFooter.vue'), name: 'LandingFooter.vue' },
    ]

    for (const comp of componentsToCheck) {
      const content = fs.readFileSync(comp.path, 'utf-8')
      const violations = checkCopyViolations(content, comp.name)
      expect(violations).toEqual([])
    }
  })

  it('has no waitlist form, email input or legal body text', () => {
    const wrapper = mount(App, { attachTo: document.body })
    expect(wrapper.find('input[type="email"]').exists()).toBe(false)
    expect(wrapper.find('form').exists()).toBe(false)

    const text = wrapper.text()
    expect(text.toLowerCase()).not.toContain('waitlist')
    expect(text.toLowerCase()).not.toContain('lista de espera')

    wrapper.unmount()
  })
})
