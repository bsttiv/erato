// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import UserInitial from '../atoms/UserInitial.vue'
import AppShell from './AppShell.vue'

const mocks = vi.hoisted(() => ({ session: { accessToken: null, user: { username: 'ana', display_name: '  ' } } }))
vi.mock('vue-router', () => ({ useRoute: () => ({ path: '/canciones', query: {} }), useRouter: () => ({ replace: vi.fn() }) }))
vi.mock('../../stores/session', () => ({ session: mocks.session, profileApi: { getMe: vi.fn() } }))
vi.mock('../../api/bands', () => ({ bandsApi: { list: vi.fn().mockResolvedValue([]) } }))

async function render() {
  const wrapper = mount(AppShell, { global: { stubs: {
    Wordmark: true, RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' },
  } } })
  await flushPromises()
  return wrapper
}

describe('dashboard profile — tests_md/propuesta-landing-app-2026-10-31.md', () => {
  it('LAPP-021 uses the shared initial with the username fallback', async () => {
    const initials = (await render()).findAllComponents(UserInitial)
    expect(initials.length).toBeGreaterThan(0)
    initials.forEach(initial => expect(initial.text()).toBe('A'))
  })
  it('LAPP-022 keeps the profile link and its accessible name', async () => {
    const link = (await render()).get('a[href="/perfil"]')
    expect(link.text()).toContain('ana')
    expect(link.attributes('tabindex')).toBeUndefined()
  })
})
