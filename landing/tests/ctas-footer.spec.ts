import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../src/App.vue'

describe('Unit L3: slides 5-7, footer, CTAs, responsive and a11y', () => {
  const originalEnv = process.env.VITE_APP_URL

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
    if (originalEnv === undefined) {
      delete process.env.VITE_APP_URL
    } else {
      process.env.VITE_APP_URL = originalEnv
    }
  })

  it('renders slides 4, 5 and 6 (Colaborar, Cómo funciona, Precios) in App', async () => {
    const wrapper = mount(App, { attachTo: document.body })

    // Navigate to slide 4 (Colaborar)
    const navLinks = wrapper.findAll('button.er-navlink')
    await navLinks[4].trigger('click')
    expect(wrapper.find('section[aria-label="Características: colaboración"]').exists()).toBe(true)

    // Navigate to slide 5 (Cómo funciona)
    await navLinks[5].trigger('click')
    expect(wrapper.find('section[aria-label="Cómo funciona"]').exists()).toBe(true)

    // Navigate to slide 6 (Precios)
    await navLinks[6].trigger('click')
    expect(wrapper.find('section[aria-label="Precios"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('header and slide CTAs use VITE_APP_URL and point to /login or /register', async () => {
    process.env.VITE_APP_URL = 'https://app.erato.test'
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
    await navLinks[5].trigger('click')
    const slide5Register = wrapper.find('section[aria-label="Cómo funciona"] a[href="https://app.erato.test/register"]')
    expect(slide5Register.exists()).toBe(true)
    expect(slide5Register.classes()).toContain('er-btn')

    // Navigate to slide 6 (Precios)
    await navLinks[6].trigger('click')
    const planCtas = wrapper.findAll('section[aria-label="Precios"] a[href="https://app.erato.test/register"]')
    // There are 3 plans: Gratis, Pro Individual, Pro Banda
    expect(planCtas.length).toBe(3)
    planCtas.forEach((cta) => {
      expect(cta.classes()).toContain('er-btn')
    })

    wrapper.unmount()
  })

  it('footer contains placeholder links #privacidad and #terminos, counter, and navigation arrows', async () => {
    const wrapper = mount(App, { attachTo: document.body })
    const footer = wrapper.find('footer.er-foot')
    expect(footer.exists()).toBe(true)

    const privacyLink = footer.find('a[href="#privacidad"]')
    expect(privacyLink.exists()).toBe(true)
    expect(privacyLink.text()).toBe('Política de privacidad')

    const termsLink = footer.find('a[href="#terminos"]')
    expect(termsLink.exists()).toBe(true)
    expect(termsLink.text()).toBe('Términos de servicio')

    // Footer counter shows slide position
    expect(footer.text()).toContain('01 / 07')

    // Prev / Next arrows exist and navigate
    const prevBtn = footer.find('button[aria-label="Sección anterior"]')
    const nextBtn = footer.find('button[aria-label="Sección siguiente"]')
    expect(prevBtn.exists()).toBe(true)
    expect(nextBtn.exists()).toBe(true)

    await nextBtn.trigger('click')
    expect(footer.text()).toContain('02 / 07')

    wrapper.unmount()
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
