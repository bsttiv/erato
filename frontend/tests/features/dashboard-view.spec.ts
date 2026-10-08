import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import DashboardView from '@/features/compositions/DashboardView.vue'
import CompositionCard from '@/features/compositions/CompositionCard.vue'
import * as compApi from '@/api/compositions'
import * as authApi from '@/api/auth'
import type { CompositionListItem } from '@/api/compositions'

const mockCompositions: CompositionListItem[] = [
  {
    id: 'comp1',
    owner_id: 'u1',
    title: 'Noche de otoño',
    visibility: 'private',
    status: 'in_progress',
    key: 'Am',
    bpm: 120,
    time_signature: '4/4',
    chord_names: ['Am', 'C', 'D', 'Em'],
    counts: { chords: 4, tabs: 1, demos: 2, todos_done: 1, todos_total: 3 },
    created_at: '2026-09-20T10:00:00Z',
    updated_at: '2026-09-28T10:00:00Z',
  },
  {
    id: 'comp2',
    owner_id: 'u1',
    title: 'Humo azul',
    visibility: 'public',
    status: 'ready',
    key: 'G',
    bpm: null,
    time_signature: '3/4',
    chord_names: ['G', 'Em'],
    counts: { chords: 2, tabs: 0, demos: 1, todos_done: 2, todos_total: 2 },
    created_at: '2026-09-25T10:00:00Z',
    updated_at: '2026-09-30T10:00:00Z',
  },
  {
    id: 'comp3',
    owner_id: 'u1',
    title: 'Vals de medianoche',
    visibility: 'private',
    status: 'idea',
    key: null,
    bpm: null,
    time_signature: null,
    chord_names: [],
    counts: { chords: 0, tabs: 0, demos: 0, todos_done: 0, todos_total: 0 },
    created_at: '2026-09-29T10:00:00Z',
    updated_at: '2026-09-29T10:00:00Z',
  },
]

function setupRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: DashboardView },
      { path: '/compositions/new', name: 'composition-create', component: { template: '<div>New</div>' } },
      { path: '/compositions/:id', name: 'composition-detail', component: { template: '<div>Detail</div>' } },
    ],
  })
}

describe('DashboardView and CompositionCard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(authApi, 'getMe').mockResolvedValue({
      id: 'u1',
      email: 'musico@erato.io',
      display_name: 'Músico Kool',
      created_at: '2026-01-01T00:00:00Z',
    })
    vi.spyOn(compApi, 'listCompositions').mockResolvedValue(mockCompositions)
  })

  it('lists band compositions with a marker only for band-derived access', async () => {
    const bandComposition = { ...mockCompositions[0], id: 'band-song', owner_id: 'other', band_id: 'band-1', via_band: true }
    vi.mocked(compApi.listCompositions).mockResolvedValue([bandComposition, mockCompositions[1]])
    const router = setupRouter()
    await router.push('/')
    const wrapper = mount(DashboardView, { global: { plugins: [router] } })
    await flushPromises()
    const cards = wrapper.findAllComponents(CompositionCard)
    expect(cards).toHaveLength(2)
    expect(cards[0].findAll('.er-tag--amber').map(tag => tag.text())).toContain('Compartida con tu banda')
    expect(cards[0].attributes('href')).toBe('/compositions/band-song')
    expect(cards[1].text()).not.toContain('Compartida con tu banda')
    expect(wrapper.text()).not.toMatch(/[!\p{Extended_Pictographic}]/u)
    wrapper.unmount()
  })

  it('renders top app bar with brand, new composition button, and user avatar', async () => {
    const router = setupRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(DashboardView, {
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 10))

    const topbar = wrapper.find('.er-topbar')
    expect(topbar.exists()).toBe(true)
    expect(topbar.find('.er-topbar-brand .er-brand').exists()).toBe(true)
    expect(topbar.find('.er-brand .er-nav-lamp').exists()).toBe(true)
    expect(topbar.find('.er-brand .er-nav-name').text()).toBe('Erato')

    const newBtn = topbar.find('a[href="/compositions/new"]')
    expect(newBtn.exists()).toBe(true)
    expect(newBtn.text()).toContain('Nueva canción')

    const avatar = topbar.find('.er-avatar')
    expect(avatar.exists()).toBe(true)
    expect(avatar.text()).toBe('MK')
  })

  it('renders headline, segmented filter and dynamic count', async () => {
    const router = setupRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(DashboardView, {
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 10))

    // Headline
    const headline = wrapper.find('.er-dash-headline')
    expect(headline.exists()).toBe(true)
    expect(headline.text()).toContain('Composiciones')

    // Segmented filter
    const filterbar = wrapper.find('.er-filterbar')
    expect(filterbar.exists()).toBe(true)
    expect(filterbar.text()).toContain('Todas')
    expect(filterbar.text()).toContain('En progreso')
    expect(filterbar.text()).toContain('Listas')
    expect(filterbar.text()).toContain('Ideas')

    // Initial count
    const countEl = wrapper.find('.er-dash-count')
    expect(countEl.exists()).toBe(true)
    expect(countEl.text()).toContain('3 canciones')

    // Card grid initial render
    const cards = wrapper.findAllComponents(CompositionCard)
    expect(cards.length).toBe(3)

    // Filter by 'in_progress'
    const segButtons = filterbar.findAll('.er-seg-opt')
    const inProgressBtn = segButtons.find((b) => b.text().includes('En progreso'))
    expect(inProgressBtn).toBeDefined()
    await inProgressBtn!.trigger('click')

    await wrapper.vm.$nextTick()
    expect(countEl.text()).toContain('1 canción')
    expect(wrapper.findAllComponents(CompositionCard).length).toBe(1)
  })

  it('CompositionCard renders index, status tag, title, chords, counts, and foot metadata', async () => {
    const router = setupRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(CompositionCard, {
      props: {
        composition: mockCompositions[0],
        index: 0,
      },
      global: { plugins: [router] },
    })

    // Index pad2
    expect(wrapper.find('.er-card-index').text()).toBe('01')

    // Status tag
    const tag = wrapper.find('.er-tag')
    expect(tag.exists()).toBe(true)
    expect(tag.text()).toContain('En progreso')

    const readyCard = mount(CompositionCard, {
      props: { composition: mockCompositions[1], index: 1 },
      global: { plugins: [router] },
    })
    expect(readyCard.find('.er-tag').text()).toContain('Lista')

    const ideaCard = mount(CompositionCard, {
      props: { composition: mockCompositions[2], index: 2 },
      global: { plugins: [router] },
    })
    expect(ideaCard.find('.er-tag').text()).toContain('Idea')

    // Title
    expect(wrapper.find('.er-card-title').text()).toBe('Noche de otoño')

    // Chord names line
    expect(wrapper.find('.er-card-chords').text()).toContain('Am · C · D · Em')

    // Counts line
    expect(wrapper.find('.er-card-counts').text()).toContain('acordes 4 · tab 1 · demos 2 · tareas 1/3')

    // Foot metadata
    const foot = wrapper.find('.er-card-foot')
    expect(foot.text()).toContain('editada')
    expect(foot.text()).toContain('Am · 120 bpm')

    // Navigates to /compositions/:id
    expect(wrapper.attributes('href')).toBe('/compositions/comp1')
  })

  it('CompositionCard omits missing metadata in foot', async () => {
    const router = setupRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(CompositionCard, {
      props: {
        composition: mockCompositions[1], // bpm is null
        index: 1,
      },
      global: { plugins: [router] },
    })

    const foot = wrapper.find('.er-card-foot')
    expect(foot.text()).toContain('G')
    expect(foot.text()).not.toContain('bpm')
  })

  it('does not render sidebar or drawer toggle', async () => {
    const router = setupRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(DashboardView, {
      global: { plugins: [router] },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.er-sidebar').exists()).toBe(false)
    expect(wrapper.find('.er-drawer-toggle').exists()).toBe(false)
  })
})
