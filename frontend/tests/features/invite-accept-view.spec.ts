import { it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import InviteAcceptView from '@/features/sharing/InviteAcceptView.vue'
import * as sharing from '@/api/sharing'
import { HttpError } from '@/api/compositions'
const refresh = vi.hoisted(() => vi.fn())
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({ refresh }) }))
beforeEach(() => { vi.restoreAllMocks(); refresh.mockReset().mockResolvedValue(undefined) })
async function setup() {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: { template: '<div />' } },
    { path: '/invite/:token', component: InviteAcceptView },
    { path: '/bands/:id', component: { template: '<div />' } },
  ] })
  await router.push('/invite/token'); await router.isReady()
  return { router, w: mount(InviteAcceptView, { global: { plugins: [router] } }) }
}
it('speaks about joining a band, uses the brand and follows copy rules', async () => {
  const { w } = await setup()
  expect(w.text()).toContain('Te invitaron a una banda')
  expect(w.find('.er-brand').exists()).toBe(true)
  expect(w.text()).not.toMatch(/!|\p{Extended_Pictographic}/u)
})
it.each(['joined', 'already_member'] as const)('refreshes before routing to the band for %s', async status => {
  vi.spyOn(sharing, 'redeemInvite').mockResolvedValue({ band_id: 'b', status })
  let resolve!: () => void
  refresh.mockReturnValue(new Promise<void>(r => { resolve = r }))
  const { w, router } = await setup()
  await w.find('button').trigger('click'); await flushPromises()
  expect(sharing.redeemInvite).toHaveBeenCalledWith('token'); expect(refresh).toHaveBeenCalledOnce()
  expect(router.currentRoute.value.path).toBe('/invite/token')
  expect(w.find('button').attributes('disabled')).toBeDefined()
  resolve(); await flushPromises(); expect(router.currentRoute.value.path).toBe('/bands/b')
})
it.each([
  ['invitation_expired', 'venció'], ['invitation_legacy', 'antigua'],
  ['band_full', 'plazas'], ['band_inactive', 'inactiva'], ['not_found', 'invitación no'],
])('maps %s in Spanish', async (code, text) => {
  vi.spyOn(sharing, 'redeemInvite').mockRejectedValue(new HttpError('internal', 410, code))
  const { w, router } = await setup(); await w.find('button').trigger('click'); await flushPromises()
  expect(w.find('[role="alert"]').text()).toContain(text)
  expect(w.text()).not.toMatch(/!|\p{Extended_Pictographic}/u)
  expect(refresh).not.toHaveBeenCalled(); expect(router.currentRoute.value.path).toBe('/invite/token')
})
it('reports unexpected failures without navigating', async () => {
  vi.spyOn(sharing, 'redeemInvite').mockRejectedValue(new Error('network'))
  const { w } = await setup(); await w.find('button').trigger('click'); await flushPromises()
  expect(w.find('[role="alert"]').text()).toContain('No se pudo completar')
})
