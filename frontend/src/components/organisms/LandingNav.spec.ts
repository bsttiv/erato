// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LandingNav from './LandingNav.vue'
import UserInitial from '../atoms/UserInitial.vue'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const mocks = vi.hoisted(() => ({
  session: { user: null as { username: string; display_name: string } | null, restore: vi.fn() },
  getMe: vi.fn(),
}))
vi.mock('../../stores/session', () => ({ session: mocks.session, profileApi: { getMe: mocks.getMe } }))

async function render() {
  const wrapper = mount(LandingNav, {
    global: { stubs: { Wordmark: true, RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } } },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.session.user = null
})

describe('landing navigation session', () => {
  it('LAPP-020 shows the shared initial for a signed-in visitor', async () => {
    mocks.session.user = { username: 'ana', display_name: 'Ana Rojas' }
    const wrapper = await render()
    expect(wrapper.getComponent(UserInitial).text()).toBe('A')
  })
  it('LAPP-022 keeps the account link and its accessible name', async () => {
    mocks.session.user = { username: 'ana', display_name: 'Ana Rojas' }
    const link = (await render()).get('a[href="/canciones"]')
    expect(link.text()).toContain('Ana Rojas')
    expect(link.attributes('tabindex')).toBeUndefined()
    expect(readFileSync(resolve(process.cwd(), 'src/assets/main.css'), 'utf8')).toContain(':focus-visible')
  })
  it('LAND-001 shows the sign-in links without a session', async () => {
    mocks.session.restore.mockResolvedValue(false)
    const wrapper = await render()
    expect(wrapper.text()).toContain('Iniciar sesión')
    expect(wrapper.text()).toContain('Empieza gratis')
    expect(wrapper.find('.invisible').exists()).toBe(false)
    expect(mocks.getMe).not.toHaveBeenCalled()
  })
  it('LAND-002 links a signed-in visitor to their songs', async () => {
    mocks.session.restore.mockResolvedValue(true)
    mocks.getMe.mockImplementation(async () => { mocks.session.user = { username: 'ana', display_name: 'Ana Rojas' } })
    const wrapper = await render()
    await wrapper.vm.$forceUpdate()
    await flushPromises()
    expect(wrapper.find('a[href="/canciones"]').text()).toContain('Ana Rojas')
    expect(wrapper.text()).not.toContain('Iniciar sesión')
    expect(wrapper.text()).not.toContain('Empieza gratis')
  })
  it('LAND-003 keeps the sign-in links when the API is unreachable', async () => {
    mocks.session.restore.mockRejectedValue(new Error('offline'))
    const wrapper = await render()
    expect(wrapper.text()).toContain('Iniciar sesión')
    expect(wrapper.find('.invisible').exists()).toBe(false)
  })
})
