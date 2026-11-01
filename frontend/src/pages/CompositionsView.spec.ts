// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import SongStatus from '../components/atoms/SongStatus.vue'
import CompositionsView from './CompositionsView.vue'

const mocks = vi.hoisted(() => ({ request: vi.fn() }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
vi.mock('../stores/session', () => ({ client: { request: mocks.request }, session: { accessToken: null } }))

describe('song list — tests_md/propuesta-detalles-cancion-2026-10-31.md', () => {
  it('DET-001 shows the status badge of each song', async () => {
    mocks.request.mockResolvedValue(['idea', 'in_progress', 'ready'].map(status => ({
      id: status, title: status, status, updated_at: '2026-10-31T00:00:00Z', visibility: 'private', owner_type: 'user',
    })))
    const wrapper = mount(CompositionsView, { global: { stubs: {
      AppShell: { template: '<main><slot /></main>' },
      RouterLink: { template: '<a><slot /></a>' },
    } } })
    await flushPromises()
    expect(wrapper.findAllComponents(SongStatus).map(badge => badge.text())).toEqual(['Idea', 'En progreso', 'Lista'])
  })
})
