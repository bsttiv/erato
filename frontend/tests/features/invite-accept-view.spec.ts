import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import InviteAcceptView from '@/features/sharing/InviteAcceptView.vue'
import * as sharingApi from '@/api/sharing'

async function setup() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: { template: '<div />' } },
      { path: '/invite/:token', name: 'invite-redeem', component: InviteAcceptView },
      { path: '/compositions/:id', name: 'composition-detail', component: { template: '<div />' } },
    ],
  })
  await router.push('/invite/tok-abc')
  await router.isReady()
  const wrapper = mount(InviteAcceptView, { global: { plugins: [router] } })
  return { router, wrapper }
}

describe('InviteAcceptView', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows a Spanish explanation and the accept button', async () => {
    const { wrapper } = await setup()
    expect(wrapper.find('.er-form-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('Te invitaron a colaborar')
    const btn = wrapper.find('button')
    expect(btn.text()).toContain('Aceptar invitación')
    expect(btn.attributes('disabled')).toBeUndefined()
    expect(wrapper.text().toLowerCase()).not.toContain('un solo uso')
  })

  it('redeems with the route token and navigates to the composition', async () => {
    const spy = vi
      .spyOn(sharingApi, 'redeemInvite')
      .mockResolvedValue({ message: 'ok', composition_id: 'comp-9' })
    const { wrapper, router } = await setup()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(spy).toHaveBeenCalledWith('tok-abc')
    expect(router.currentRoute.value.path).toBe('/compositions/comp-9')
  })

  it('disables the button while redeeming', async () => {
    let resolve!: (v: { message: string; composition_id: string }) => void
    vi.spyOn(sharingApi, 'redeemInvite').mockReturnValue(
      new Promise((r) => {
        resolve = r
      })
    )
    const { wrapper } = await setup()

    await wrapper.find('button').trigger('click')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    expect(wrapper.find('button').text()).toContain('Aceptando')

    resolve({ message: 'ok', composition_id: 'c' })
    await flushPromises()
  })

  it('shows a clear error when the link is invalid or expired', async () => {
    vi.spyOn(sharingApi, 'redeemInvite').mockRejectedValue(new Error('Invitación inválida o expirada'))
    const { wrapper, router } = await setup()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    const err = wrapper.find('.er-auth-error')
    expect(err.exists()).toBe(true)
    expect(err.text()).toContain('no es válido o ya venció')
    expect(router.currentRoute.value.path).toBe('/invite/tok-abc')
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
  })

  it('shows a generic Spanish error for unexpected failures', async () => {
    vi.spyOn(sharingApi, 'redeemInvite').mockRejectedValue(new Error('Network down'))
    const { wrapper } = await setup()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.find('.er-auth-error').text()).toContain('No pudimos aceptar la invitación')
  })
})
