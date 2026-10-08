import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import CompositionDetailView from '@/features/compositions/CompositionDetailView.vue'
import * as api from '@/api/compositions'
import { resetAuthReadyForTesting, setAuthenticated } from '@/router/authReady'

vi.mock('@/features/plan/useEntitlements', () => ({
  useEntitlements: () => ({ entitlements: { value: null } }),
}))

const composition: api.CompositionResponse = {
  id: 'song', owner_id: 'owner', title: 'Ensayo', visibility: 'public',
  share_slug: 'ensayo', user_role: null, created_at: '', updated_at: '',
  todos: [], members: [],
  sections_enabled: { lyrics: false, chords: false, tablature: false, demos: false, todos: false },
}
let wrapper: VueWrapper | undefined

async function render(overrides: Partial<api.CompositionResponse> = {}, status?: number) {
  const load = vi.spyOn(api, 'getCompositionBySlug')
  if (status) load.mockRejectedValue(new api.HttpError('Unavailable', status))
  else load.mockResolvedValue({ ...composition, ...overrides })
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', name: 'dashboard', component: { template: '<div />' } },
    { path: '/c/:ref', name: 'composition-public', component: CompositionDetailView },
    { path: '/register', name: 'register', component: { template: '<div />' } },
  ] })
  await router.push('/c/ensayo')
  wrapper = mount(CompositionDetailView, { attachTo: document.body, global: { plugins: [router] } })
  await flushPromises()
  return { view: wrapper, router }
}

beforeEach(() => {
  resetAuthReadyForTesting()
  vi.spyOn(api, 'listCompositions').mockResolvedValue([])
})
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  resetAuthReadyForTesting()
  vi.restoreAllMocks()
})

describe('saved in Erato footer', () => {
  it('renders for an anonymous public viewer with Spanish copy and a keyboard reachable registration link', async () => {
    const { view, router } = await render()
    expect(api.getCompositionBySlug).toHaveBeenCalledWith('ensayo')
    const footer = view.get('footer')
    expect(footer.text()).toContain('Guardado en Erato')
    expect(footer.text()).not.toMatch(/[!¡\p{Extended_Pictographic}\p{Regional_Indicator}]/u)
    const link = footer.get<HTMLAnchorElement>('a')
    expect(link.text()).toBe('Crea tu cuenta gratis')
    expect(link.attributes('href')).toBe('/register')
    expect(link.classes()).toContain('er-btn')
    expect(link.element.tabIndex).toBe(0)
    link.element.focus()
    expect(document.activeElement).toBe(link.element)
    await link.trigger('click', { button: 0 })
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('register')
  })

  it.each([
    { label: 'owner', user_role: 'owner' as const },
    { label: 'invited editor', user_role: 'editor' as const },
    { label: 'invited viewer', user_role: 'viewer' as const },
    { label: 'band member', user_role: 'editor' as const, band_id: 'band', band_editable: true },
    { label: 'unrelated authenticated viewer', user_role: null },
  ])('hides the footer for $label', async ({ label: _label, ...overrides }) => {
    setAuthenticated(true)
    const { view } = await render(overrides)
    expect(view.find('footer').exists()).toBe(false)
  })

  it.each(['owner', 'editor', 'viewer'] as const)('hides the footer when the response grants role %s', async user_role => {
    const { view } = await render({ user_role })
    expect(view.find('footer').exists()).toBe(false)
  })

  it('hides the footer on a private composition', async () => {
    const { view } = await render({ visibility: 'private' })
    expect(view.find('footer').exists()).toBe(false)
  })

  it.each([403, 404])('shows no content or footer after HTTP %s', async status => {
    const { view } = await render({}, status)
    expect(view.find('.er-comp-detail').exists()).toBe(false)
    expect(view.find('footer').exists()).toBe(false)
    expect(view.text()).toContain('No se encontró la composición.')
  })
})
