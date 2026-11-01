import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, expect, it, vi } from 'vitest'
import NewCompositionView from './NewCompositionView.vue'
const mocks = vi.hoisted(() => ({ request: vi.fn(), push: vi.fn() }))
vi.mock('../stores/session', () => ({ client: { request: mocks.request }, session: { restore: vi.fn() } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }), useRoute: () => ({ query: {} }) }))
beforeEach(() => { vi.clearAllMocks() })
// Decision 09 §1 and decision 14 approved SONG area rules; original numeric rows unavailable.
it('SONG-rule creates through the API and navigates using the returned identity', async () => {
  mocks.request.mockResolvedValue({ id: 'server-id', title: 'Nueva canción' })
  const wrapper = mount(NewCompositionView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' }, BackBar: true } } })
  await wrapper.get('#nc-title').setValue('Nueva canción')
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(mocks.request).toHaveBeenCalledWith('/songs', expect.objectContaining({ method: 'POST', body: expect.objectContaining({ title: 'Nueva canción' }) }))
  expect(mocks.push).toHaveBeenCalledWith('/canciones/server-id')
  wrapper.unmount()
})
