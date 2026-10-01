import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import AuthView from '@/features/auth/AuthView.vue'
import LoginForm from '@/features/auth/LoginForm.vue'
import RegisterForm from '@/features/auth/RegisterForm.vue'

function setupTestRouter(initialPath: string = '/login') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: AuthView },
      { path: '/register', name: 'register', component: AuthView },
      { path: '/', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
    ],
  })
  router.push(initialPath)
  return router
}

describe('AuthView and Split-Screen Shell', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders 50/50 split-screen layout with hero panel and form panel', async () => {
    const router = setupTestRouter('/login')
    await router.isReady()

    const wrapper = mount(AuthView, {
      global: {
        plugins: [router],
        stubs: {
          RouterLink: false,
        },
      },
    })

    expect(wrapper.find('.er-auth-split').exists()).toBe(true)
    expect(wrapper.find('.er-auth-hero').exists()).toBe(true)
    expect(wrapper.find('.er-auth-pane').exists()).toBe(true)
  })

  it('hero panel renders wordmark, tagline, and pure-CSS geometric bars without image elements', async () => {
    const router = setupTestRouter('/login')
    await router.isReady()

    const wrapper = mount(AuthView, {
      global: {
        plugins: [router],
      },
    })

    const hero = wrapper.find('.er-auth-hero')
    expect(hero.exists()).toBe(true)

    const wordmark = hero.find('.er-auth-wordmark')
    expect(wordmark.exists()).toBe(true)
    expect(wordmark.text()).toContain('Erato')

    const tagline = hero.find('.er-auth-tagline')
    expect(tagline.exists()).toBe(true)
    expect(tagline.text()).toContain('Tu música, tus acordes, tu banda.')

    expect(hero.find('.er-auth-bars').exists()).toBe(true)

    // No network <img> element or external assets
    expect(hero.findAll('img').length).toBe(0)
  })

  it('switches between LoginForm and RegisterForm based on route', async () => {
    const router = setupTestRouter('/login')
    await router.isReady()

    const wrapper = mount(AuthView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.findComponent(LoginForm).exists()).toBe(true)
    expect(wrapper.findComponent(RegisterForm).exists()).toBe(false)

    await router.push('/register')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(RegisterForm).exists()).toBe(true)
    expect(wrapper.findComponent(LoginForm).exists()).toBe(false)
  })

  it('LoginForm renders PDF copy, password toggle, and no D11 controls', async () => {
    const router = setupTestRouter('/login')
    await router.isReady()

    const wrapper = mount(LoginForm, {
      global: {
        plugins: [router],
      },
    })

    // Required PDF copy
    expect(wrapper.text()).toContain('Inicia sesión')
    expect(wrapper.text()).toContain('Bienvenido de vuelta a tu espacio de composición.')

    // Form inputs
    const emailInput = wrapper.find('input[type="email"]')
    expect(emailInput.exists()).toBe(true)

    const passwordInput = wrapper.find('#login-password')
    expect(passwordInput.exists()).toBe(true)
    expect(passwordInput.attributes('type')).toBe('password')

    // Password visibility toggle
    const toggleBtn = wrapper.find('.er-password-toggle')
    expect(toggleBtn.exists()).toBe(true)
    expect(toggleBtn.text().toLowerCase()).toContain('mostrar')

    await toggleBtn.trigger('click')
    expect(passwordInput.attributes('type')).toBe('text')
    expect(toggleBtn.text().toLowerCase()).toContain('ocultar')

    // Primary action button
    const submitBtn = wrapper.find('button[type="submit"]')
    expect(submitBtn.exists()).toBe(true)
    expect(submitBtn.text()).toContain('Entrar')

    // Navigation link to register
    const registerLink = wrapper.find('a[href="/register"]')
    expect(registerLink.exists()).toBe(true)
    expect(registerLink.text()).toContain('Regístrate')

    // D11 deferred controls MUST NOT be rendered
    const textLower = wrapper.text().toLowerCase()
    expect(textLower).not.toContain('google')
    expect(textLower).not.toContain('olvidaste')
    expect(textLower).not.toContain('recuperar')
  })

  it('RegisterForm renders PDF copy, password toggle, and no D11 controls', async () => {
    const router = setupTestRouter('/register')
    await router.isReady()

    const wrapper = mount(RegisterForm, {
      global: {
        plugins: [router],
      },
    })

    // Required PDF copy
    expect(wrapper.text()).toContain('Crea tu cuenta')
    expect(wrapper.text()).toContain('Organiza las canciones de tu banda en un solo lugar.')

    // Form inputs
    expect(wrapper.find('#reg-name').exists()).toBe(true)
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)

    const passwordInput = wrapper.find('#reg-password')
    expect(passwordInput.exists()).toBe(true)
    expect(passwordInput.attributes('type')).toBe('password')

    // Password visibility toggle
    const toggleBtn = wrapper.find('.er-password-toggle')
    expect(toggleBtn.exists()).toBe(true)
    expect(toggleBtn.text().toLowerCase()).toContain('mostrar')

    await toggleBtn.trigger('click')
    expect(passwordInput.attributes('type')).toBe('text')
    expect(toggleBtn.text().toLowerCase()).toContain('ocultar')

    // Primary action button
    const submitBtn = wrapper.find('button[type="submit"]')
    expect(submitBtn.exists()).toBe(true)
    expect(submitBtn.text()).toContain('Crear cuenta')

    // Navigation link to login
    const loginLink = wrapper.find('a[href="/login"]')
    expect(loginLink.exists()).toBe(true)
    expect(loginLink.text()).toContain('Inicia sesión')

    // D11 deferred controls MUST NOT be rendered
    const textLower = wrapper.text().toLowerCase()
    expect(textLower).not.toContain('google')
    expect(textLower).not.toContain('términos')
    expect(textLower).not.toContain('privacidad')
    expect(wrapper.find('input[name="band"]').exists()).toBe(false)
    expect(wrapper.find('input[placeholder*="banda" i]').exists()).toBe(false)
    const labels = wrapper.findAll('label').map((l) => l.text().toLowerCase())
    expect(labels.some((text) => text.includes('banda'))).toBe(false)
  })
})
