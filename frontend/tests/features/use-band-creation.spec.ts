import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { PAYMENT_EXTENSION_KEY } from '@/app'
import { useBandCreation } from '@/features/bands/useBandCreation'

const entitlements = ref({ band_creation_mode: 'direct' })
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({ entitlements }) }))
afterEach(() => vi.restoreAllMocks())
describe('Band creation mode', () => {
  it.each(['direct', 'hand_off', 'unavailable'])('handles %s without plan names', async mode => {
    entitlements.value = { band_creation_mode: mode === 'direct' ? 'direct' : 'hand_off' }
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<p />' } }, { path: '/plan', name: 'checkout', component: { template: '<p />' } }] })
    const push = vi.spyOn(router, 'push').mockResolvedValue()
    const openForm = vi.fn()
    let creation!: ReturnType<typeof useBandCreation>
    const wrapper = mount({ setup() { creation = useBandCreation(openForm); return () => null } }, {
      global: { plugins: [router], provide: { [PAYMENT_EXTENSION_KEY as symbol]: mode === 'hand_off' ? { routes: [], bandCreationEntry: { name: 'checkout' } } : undefined } },
    })
    expect(creation.actionable.value).toBe(mode !== 'unavailable')
    await creation.create()
    expect(openForm).toHaveBeenCalledTimes(mode === 'direct' ? 1 : 0)
    if (mode === 'hand_off') expect(push).toHaveBeenCalledWith({ name: 'checkout' })
    else expect(push).not.toHaveBeenCalled()
    if (mode === 'unavailable') expect(creation.explanation.value).toBe('La creación de bandas no está disponible en esta instalación.')
    wrapper.unmount()
  })
})
