import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import CompositionDetailView from '@/features/compositions/CompositionDetailView.vue'
import ChordGrid from '@/features/compositions/ChordGrid.vue'
import DemosSection from '@/features/demos/DemosSection.vue'
import * as compApi from '@/api/compositions'
import type { CompositionResponse, CompositionListItem } from '@/api/compositions'

const sampleComposition: CompositionResponse = {
  id: 'comp-100',
  owner_id: 'user-owner',
  title: 'Noche de otoño',
  visibility: 'private',
  share_slug: 'slug-100',
  key: 'Am',
  bpm: 120,
  time_signature: '4/4',
  style_tags: ['jazz', 'bossa'],
  status: 'in_progress',
  sections_enabled: {
    chords: true,
    tablature: true,
    lyrics: true,
    demos: true,
    todos: true,
  },
  user_role: 'owner',
  chords: {
    instrument: 'guitar',
    entries: [
      { bar: 1, notes: [0, 0, 2, 2, 1, 0], name: 'Am' },
      { bar: 2, notes: [-1, 3, 2, 0, 1, 0], name: 'C' },
    ],
  },
  tablature: {
    strings: 6,
    content: 'e|---',
    tabs: [{ id: 'tab1', title: 'Intro', strings: 6, columns: [] }],
  },
  lyrics: {
    content: '[Am]Bajo el farol [C]de la esquina',
  },
  todos: [
    { id: 't1', text: 'Grabar solo', done: true },
    { id: 't2', text: 'Mezclar voz', done: false },
  ],
  demos: [],
  members: [
    { user_id: 'u2', role: 'editor', display_name: 'Ana Pérez', initials: 'AP' },
  ],
  created_at: '2026-09-01T12:00:00Z',
  updated_at: '2026-09-10T12:00:00Z',
}

const sampleSidebarList: CompositionListItem[] = [
  {
    id: 'comp-100',
    owner_id: 'user-owner',
    title: 'Noche de otoño',
    visibility: 'private',
    key: 'Am',
    created_at: '2026-09-01T12:00:00Z',
    updated_at: '2026-09-10T12:00:00Z',
  },
]

async function setupRouter(initialPath: string = '/compositions/comp-100') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
      { path: '/compositions/:id', name: 'composition-detail', component: CompositionDetailView },
      { path: '/c/:slug', name: 'composition-public', component: CompositionDetailView },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('CompositionDetailView', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(compApi, 'getComposition').mockResolvedValue(sampleComposition)
    vi.spyOn(compApi, 'listCompositions').mockResolvedValue(sampleSidebarList)
  })

  it('renders persistent sidebar with link back to dashboard in footer', async () => {
    const router = await setupRouter('/compositions/comp-100')

    const wrapper = mount(CompositionDetailView, {
      props: { composition: sampleComposition },
      global: { plugins: [router] },
    })

    const sidebar = wrapper.find('.er-sidebar')
    expect(sidebar.exists()).toBe(true)

    const sideNav = wrapper.findComponent({ name: 'ErSideNav' })
    expect(sideNav.exists()).toBe(true)

    const backLink = sidebar.find('.er-sidebar-foot a[href="/"]')
    expect(backLink.exists()).toBe(true)
    expect(backLink.text()).toContain('todas las composiciones')
  })

  it('unauthenticated visitor on public route drops sidebar (er-layout--noside)', async () => {
    const publicComp: CompositionResponse = {
      ...sampleComposition,
      visibility: 'public',
      user_role: undefined,
    }
    vi.spyOn(compApi, 'getCompositionBySlug').mockResolvedValue(publicComp)

    const router = await setupRouter('/c/slug-100')

    const wrapper = mount(CompositionDetailView, {
      props: { composition: publicComp },
      global: { plugins: [router] },
    })

    expect(wrapper.find('.er-layout--noside').exists()).toBe(true)
    expect(wrapper.find('.er-sidebar').exists()).toBe(false)
  })

  it('header displays breadcrumb, title, save status, metadata chips, avatars, and actions', async () => {
    const router = await setupRouter('/compositions/comp-100')

    const wrapper = mount(CompositionDetailView, {
      props: { composition: sampleComposition },
      global: { plugins: [router] },
    })

    // Breadcrumb
    const crumb = wrapper.find('.er-crumb')
    expect(crumb.exists()).toBe(true)
    expect(crumb.text()).toContain('composiciones')
    expect(crumb.text().toLowerCase()).toContain('noche de otoño')

    // Title
    expect(wrapper.find('.er-comp-title').text()).toBe('Noche de otoño')

    // Metadata chips
    const meta = wrapper.find('.er-comp-meta')
    expect(meta.text()).toContain('Am')
    expect(meta.text()).toContain('120 bpm')
    expect(meta.text()).toContain('4/4')
    expect(meta.text()).toContain('jazz')
    expect(meta.text()).toContain('bossa')

    // Collaborator avatars
    const avatars = wrapper.find('.er-avatars')
    expect(avatars.exists()).toBe(true)
    expect(avatars.text()).toContain('AP')

    // Action buttons for owner
    expect(wrapper.find('[data-test="share-btn"]').exists()).toBe(true)
    expect(wrapper.find('.er-save-btn').exists()).toBe(true)
  })

  it('hides edit and save controls for viewer or anonymous visitors', async () => {
    const viewerComp: CompositionResponse = {
      ...sampleComposition,
      user_role: 'viewer',
    }

    const router = await setupRouter('/compositions/comp-100')

    const wrapper = mount(CompositionDetailView, {
      props: { composition: viewerComp },
      global: { plugins: [router] },
    })

    expect(wrapper.find('.er-save-btn').exists()).toBe(false)
    expect(wrapper.find('[data-test="share-btn"]').exists()).toBe(false)
  })

  it('renders count-bearing jump nav with all enabled sections stacked in page', async () => {
    const router = await setupRouter('/compositions/comp-100')

    const wrapper = mount(CompositionDetailView, {
      props: { composition: sampleComposition },
      global: { plugins: [router] },
    })

    const sectionNav = wrapper.find('.er-sectionnav')
    expect(sectionNav.exists()).toBe(true)

    // Verify live counts in anchors
    expect(sectionNav.text()).toContain('letra')
    expect(sectionNav.text()).toContain('acordes 2')
    expect(sectionNav.text()).toContain('tablatura 1')
    expect(sectionNav.text()).toContain('demos 0')
    expect(sectionNav.text()).toContain('tareas 1/2')

    // All section panels stacked simultaneously in document
    expect(wrapper.find('#sec-lyrics').exists()).toBe(true)
    expect(wrapper.find('#sec-todos').exists()).toBe(true)
    expect(wrapper.find('#sec-chords').exists()).toBe(true)
    expect(wrapper.find('#sec-tablature').exists()).toBe(true)
    expect(wrapper.find('#sec-demos').exists()).toBe(true)

    // Components rendered
    expect(wrapper.findComponent(ChordGrid).exists()).toBe(true)
    expect(wrapper.findComponent(DemosSection).exists()).toBe(true)
  })
})
