import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import CompositionDetailView from '@/features/compositions/CompositionDetailView.vue'
import LyricsSection from '@/features/compositions/LyricsSection.vue'
import ChordGrid from '@/features/compositions/ChordGrid.vue'
import TablatureSection from '@/features/compositions/TablatureSection.vue'
import DemosSection from '@/features/demos/DemosSection.vue'
import SectionHistoryPanel from '@/features/compositions/SectionHistoryPanel.vue'
import type { CompositionResponse } from '@/api/compositions'
import type { Entitlements } from '@/api/entitlements'

const policy = ref<Entitlements | null>(null)
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({ entitlements: policy }) }))
vi.mock('@/api/compositions', async importOriginal => ({
  ...await importOriginal<typeof import('@/api/compositions')>(),
  listCompositions: vi.fn().mockResolvedValue([]),
}))

const composition = {
  id: 'song', owner_id: 'owner', title: 'Ensayo', visibility: 'private',
  band_id: 'band', band_editable: true, band_active: false, user_role: 'editor',
  lyrics: { content: 'Letra guardada' }, todos: [{ id: 'task', text: 'Grabar', done: true }],
  members: [], demos: [], created_at: '', updated_at: '',
} as CompositionResponse & { band_id: string; band_editable: boolean; band_active?: boolean | null }
const allowed: Entitlements = {
  can_share_with_people: true, can_create_band: true, can_view_history: true,
  demo_limit_per_composition: null, extensions_available: false, band_creation_mode: 'direct',
}

async function render(overrides: Partial<typeof composition> = {}) {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: { template: '<div />' } },
    { path: '/compositions/:id', component: CompositionDetailView },
  ] })
  await router.push('/compositions/song')
  const wrapper = mount(CompositionDetailView, {
    props: { composition: { ...composition, ...overrides } }, global: { plugins: [router] },
  })
  await flushPromises()
  return wrapper
}

function expectEditable(wrapper: Awaited<ReturnType<typeof render>>, editable: boolean) {
  for (const component of [LyricsSection, ChordGrid, TablatureSection]) {
    expect(wrapper.findComponent(component).props('editable')).toBe(editable)
  }
  expect(wrapper.findComponent(DemosSection).props('canEdit')).toBe(editable)
  const fieldset = wrapper.get('#sec-todos fieldset')
  expect(fieldset.attributes('disabled') !== undefined).toBe(!editable)
  expect(wrapper.get('#sec-todos').text()).toContain('Grabar')
  expect(wrapper.get('#sec-lyrics').text()).toContain('Letra guardada')
}

describe('inactive band and history policy', () => {
  beforeEach(() => { policy.value = allowed })

  it.each(['editor', 'viewer', null] as const)('explains inactivity and prevents edits for %s', async user_role => {
    const wrapper = await render({ user_role, visibility: 'public' })
    expect(wrapper.get('[role="status"] .er-tag').text()).toBe('Banda inactiva')
    expect(wrapper.get('[role="status"]').text()).toContain('La banda de esta composición está inactiva. Por ahora solo puedes verla; el contenido sigue guardado.')
    expectEditable(wrapper, false)
    expect(wrapper.find('.er-save-btn').exists()).toBe(false)
    expect(wrapper.find('[data-test="share-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="status-segmented"]').exists()).toBe(false)
    expect(wrapper.text()).not.toMatch(/[!\p{Extended_Pictographic}]/u)
    wrapper.unmount()
  })

  it('shows the owner notice and retains editing and sharing', async () => {
    const wrapper = await render({ user_role: 'owner' })
    expect(wrapper.get('[role="status"] .er-tag').text()).toBe('Banda inactiva')
    expect(wrapper.get('[role="status"]').text()).toContain('La banda de esta composición está inactiva. Puedes seguir editando porque la composición es tuya.')
    expectEditable(wrapper, true)
    expect(wrapper.get('.er-save-btn').attributes('disabled')).toBeUndefined()
    expect(wrapper.get('[data-test="share-btn"]').attributes('disabled')).toBeUndefined()
    expect(wrapper.text()).not.toMatch(/[!\p{Extended_Pictographic}]/u)
    wrapper.unmount()
  })

  it.each([true, null, undefined])('treats band_active=%s as active', async band_active => {
    const wrapper = await render({ band_active })
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
    expectEditable(wrapper, true)
    wrapper.unmount()
  })

  it('keeps active-band viewers read-only', async () => {
    const wrapper = await render({ band_active: true, user_role: 'viewer' })
    expectEditable(wrapper, false)
    wrapper.unmount()
  })

  it('shows all history buttons only after a grant and hides them on revocation', async () => {
    policy.value = null
    const wrapper = await render({ user_role: 'owner' })
    const selectors = ['lyrics', 'chords', 'tablature'].map(section => `[data-test="open-${section}-history-btn"]`)
    const expectButtons = (visible: boolean) => {
      for (const selector of selectors) expect(wrapper.find(selector).exists()).toBe(visible)
    }
    expectButtons(false)
    policy.value = { ...allowed, can_view_history: false }
    await flushPromises()
    expectButtons(false)
    policy.value = allowed
    await flushPromises()
    expectButtons(true)
    policy.value = null
    await flushPromises()
    expectButtons(false)
    wrapper.unmount()
  })

  it('does not flash history while loading or denied and allows it after a grant', async () => {
    policy.value = null
    const wrapper = await render({ user_role: 'owner' })
    wrapper.findComponent(LyricsSection).vm.$emit('openHistory')
    await flushPromises()
    expect(wrapper.findComponent(SectionHistoryPanel).exists()).toBe(false)
    policy.value = { ...allowed, can_view_history: false }
    await flushPromises()
    expect(wrapper.findComponent(SectionHistoryPanel).exists()).toBe(false)
    policy.value = allowed
    await flushPromises()
    expect(wrapper.findComponent(SectionHistoryPanel).exists()).toBe(true)
    policy.value = null
    await flushPromises()
    expect(wrapper.findComponent(SectionHistoryPanel).exists()).toBe(false)
    expect(wrapper.get('#sec-lyrics').text()).toContain('Letra guardada')
    wrapper.unmount()
  })

  it('renders no PDF affordance', async () => {
    const wrapper = await render({ user_role: 'owner' })
    expect(wrapper.findAll('button, a').some(control => /pdf/i.test(control.text() + JSON.stringify(control.attributes())))).toBe(false)
    wrapper.unmount()
  })
})
