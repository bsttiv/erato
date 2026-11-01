// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import DemosView from './DemosView.vue'

const mocks = vi.hoisted(() => ({ request: vi.fn(), state: null as any }))
vi.mock('vue-router', () => ({ useRoute: () => ({ params: { id: 's1' } }) }))
vi.mock('../stores/session', () => ({
  client: { request: mocks.request }, session: { user: { username: 'alice' } }, profileApi: { getMe: vi.fn() },
}))
vi.mock('../stores/song', () => ({ useSong: () => mocks.state }))

beforeEach(() => {
  vi.clearAllMocks()
  mocks.state = {
    song: ref({ id: 's1', title: 'Song', demos: [{ id: 'd1', title: 'Take', duration_s: 60 }] }),
    loading: ref(false), error: ref(''), canEdit: ref(true), canManage: ref(true), isPublic: ref(false),
  }
  mocks.request.mockImplementation(async (path: string) =>
    path.endsWith('/url') ? { url: 'https://example.test/audio', expires_in: 900 } : [])
})

describe('CLD-104 storage unavailable in demo actions', () => {
  it.each(['play', 'rename', 'delete'])('shows the storage message on %s without changing the demo', async (action) => {
    const unavailable = { status: 503, code: 'storage_unavailable' }
    if (action === 'play') {
      mocks.request.mockImplementation(async (path: string) => {
        if (path.endsWith('/url')) throw unavailable
        return []
      })
    }
    const before = JSON.stringify(mocks.state.song.value)
    const wrapper = mount(DemosView, { global: { stubs: {
      CompositionHeader: true, DemoDetail: true, DemoUpload: true, DemoList: true,
    } } })
    await flushPromises()
    if (action !== 'play') {
      mocks.request.mockRejectedValueOnce(unavailable)
      wrapper.findComponent({ name: 'DemoDetail' }).vm.$emit(action === 'rename' ? 'rename' : 'remove', 'New title')
      await flushPromises()
      expect(mocks.request).toHaveBeenLastCalledWith('/songs/s1/demos/d1', action === 'rename'
        ? { method: 'PATCH', body: { title: 'New title' } } : { method: 'DELETE' })
    } else {
      expect(mocks.request).toHaveBeenCalledWith('/songs/s1/demos/d1/url', {})
    }
    expect(wrapper.get('[role="alert"]').text()).toBe('Las demos no están disponibles en este momento.')
    expect(JSON.stringify(mocks.state.song.value)).toBe(before)
    wrapper.unmount()
  })
})
