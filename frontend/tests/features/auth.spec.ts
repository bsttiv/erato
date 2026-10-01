import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginForm from '@/features/auth/LoginForm.vue'
import AuthView from '@/features/auth/AuthView.vue'
import * as authApi from '@/api/auth'

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

    const wrapper = mount(LoginForm)

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('input[type="password"]')
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

    const wrapper = mount(LoginForm)

    await wrapper.find('input[type="email"]').setValue('wrong@erato.io')
    await wrapper.find('input[type="password"]').setValue('wrongpass')
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

  it('allows switching between login and registration in AuthView', async () => {
    const wrapper = mount(AuthView)
    expect(wrapper.findComponent(LoginForm).exists()).toBe(true)

    // Switch to register tab
    const segButtons = wrapper.findAll('.er-seg-opt')
    expect(segButtons.length).toBe(2)
    await segButtons[1].trigger('click')

    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Registrarse')
  })
})
