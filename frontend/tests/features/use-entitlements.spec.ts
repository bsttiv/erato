import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { useEntitlements, refreshEntitlements } from '@/features/plan/useEntitlements'
import * as api from '@/api/entitlements'
import { setAccessToken } from '@/api/client'
import { createEratoRouter } from '@/app'
import { resetAuthReadyForTesting } from '@/router/authReady'

const gates = { can_share_with_people: false, can_create_band: false, can_view_history: true,
  demo_limit_per_composition: 1, extensions_available: true, band_creation_mode: 'hand_off' as const }
beforeEach(async () => {
  setAccessToken(null)
  resetAuthReadyForTesting()
  await flushPromises()
  vi.restoreAllMocks()
})
describe('Entitlements cache', () => {
  it('invalidates a return-from-payment refresh even before a consumer mounts', async () => {
    vi.spyOn(api, 'getEntitlements').mockResolvedValue(gates)
    setAccessToken('jwt')
    await refreshEntitlements()
    setAccessToken(null)
    expect(useEntitlements().entitlements.value).toBeNull()
  })
  it('keeps login refresh active after its first consumer unmounts', async () => {
    const get = vi.spyOn(api, 'getEntitlements').mockResolvedValue(gates)
    const wrapper = mount({ setup() { useEntitlements(); return () => null } })
    wrapper.unmount()
    setAccessToken('jwt')
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(1)
  })
  it('uses apiClient and preserves endpoint fields', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(gates)))
    expect(await api.getEntitlements()).toEqual(gates)
    expect(fetch).toHaveBeenCalledWith('/api/me/entitlements', expect.any(Object))
  })
  it('caches concurrent callers, refreshes on login and logout, and ignores stale responses', async () => {
    const get = vi.spyOn(api, 'getEntitlements').mockResolvedValue(gates)
    const first = useEntitlements()
    setAccessToken('jwt')
    await flushPromises()
    const second = useEntitlements()
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(1)
    expect(first.entitlements.value).toEqual(gates)
    expect(second.entitlements.value).toBe(first.entitlements.value)
    await first.refresh()
    expect(get).toHaveBeenCalledTimes(2)
    let finish!: (value: typeof gates) => void
    get.mockReturnValueOnce(new Promise(resolve => { finish = resolve }))
    const pending = first.refresh()
    setAccessToken(null)
    finish(gates)
    await pending
    expect(first.entitlements.value).toBeNull()
    setAccessToken('other-jwt')
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(4)
  })
  it('refreshes after returning from a payment route, not between payment pages', async () => {
    const get = vi.spyOn(api, 'getEntitlements').mockResolvedValue(gates)
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ access_token: 'jwt' })))
    const router = createEratoRouter({ routes: [
      { path: '/plan', component: { template: '<p />' }, meta: { requiresAuth: true } },
      { path: '/plan/checkout', component: { template: '<p />' }, meta: { requiresAuth: true } },
    ] })
    useEntitlements()
    await router.push('/plan')
    await flushPromises()
    const count = get.mock.calls.length
    await router.push('/plan/checkout')
    expect(get).toHaveBeenCalledTimes(count)
    await router.push('/login')
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(count + 1)
  })
  it('keeps denied gates unavailable when refresh fails and allows retry', async () => {
    const get = vi.spyOn(api, 'getEntitlements').mockRejectedValue(new Error('offline'))
    const state = useEntitlements()
    setAccessToken('jwt')
    await flushPromises()
    expect(state.entitlements.value).toBeNull()
    expect(state.error.value).toBeTruthy()
    get.mockResolvedValue(gates)
    await state.refresh()
    expect(state.entitlements.value).toEqual(gates)
  })
})
