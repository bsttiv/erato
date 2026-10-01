import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import LoginForm from '@/features/auth/LoginForm.vue'
import RegisterForm from '@/features/auth/RegisterForm.vue'
import AuthView from '@/features/auth/AuthView.vue'
import * as authApi from '@/api/auth'

function createTestRouter(initialPath: string = '/login') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: AuthView },
      { path: '/register', name: 'register', component: AuthView },
    ],
  })
  router.push(initialPath)
  return router
}

describe('Auth feature views', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders login form and submits credentials to auth API', async () => {
    const loginSpy = vi.spyOn(authApi, 'login').mockResolvedValueOnce({
      access_token: 'fake-token',
      token_type: 'bearer',
      user: {
        id: 'u1',
        email: 'musico@erato.io',
        display_name: 'Músico',
        created_at: new Date().toISOString(),
      },
    })

    const router = createTestRouter('/login')
    await router.isReady()

    const wrapper = mount(LoginForm, {
      global: {
        plugins: [router],
      },
    })

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('#login-password')
    await emailInput.setValue('musico@erato.io')
    await passwordInput.setValue('Password123!')

    await wrapper.find('form').trigger('submit')

    expect(loginSpy).toHaveBeenCalledWith('musico@erato.io', 'Password123!')
    expect(wrapper.emitted('success')).toBeTruthy()
  })

  it('surfaces invalid-credentials error without revealing which field failed', async () => {
    vi.spyOn(authApi, 'login').mockRejectedValueOnce(
      new Error('Credenciales incorrectas')
    )

    const router = createTestRouter('/login')
    await router.isReady()

    const wrapper = mount(LoginForm, {
      global: {
        plugins: [router],
      },
    })

    await wrapper.find('input[type="email"]').setValue('wrong@erato.io')
    await wrapper.find('#login-password').setValue('wrongpass')
    await wrapper.find('form').trigger('submit')

    // Wait for promise resolution
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 10))

    const errorEl = wrapper.find('.er-auth-error')
    expect(errorEl.exists()).toBe(true)
    expect(errorEl.text()).toBe('Credenciales incorrectas')
    // Must not reveal whether email or password failed
    expect(errorEl.text().toLowerCase()).not.toContain('correo no existe')
    expect(errorEl.text().toLowerCase()).not.toContain('contraseña incorrecta')
  })

  it('allows switching between login and registration in AuthView via routing', async () => {
    const router = createTestRouter('/login')
    await router.isReady()

    const wrapper = mount(AuthView, {
      global: {
        plugins: [router],
      },
    })
    expect(wrapper.findComponent(LoginForm).exists()).toBe(true)
    expect(wrapper.findComponent(RegisterForm).exists()).toBe(false)

    // Navigate to register route
    await router.push('/register')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(RegisterForm).exists()).toBe(true)
    expect(wrapper.findComponent(LoginForm).exists()).toBe(false)
    expect(wrapper.find('#reg-email').exists()).toBe(true)
    expect(wrapper.text()).toContain('Crea tu cuenta')
  })
})
