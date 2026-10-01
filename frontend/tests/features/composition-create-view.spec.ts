import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import CompositionCreateView from '@/features/compositions/CompositionCreateView.vue'
import * as compApi from '@/api/compositions'

function setupRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
      { path: '/compositions/new', name: 'composition-create', component: CompositionCreateView },
      { path: '/compositions/:id', name: 'composition-detail', component: { template: '<div>Detail</div>' } },
    ],
  })
}

describe('CompositionCreateView', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders full-page creation shell with minimal bar and centered form card (not a modal)', async () => {
    const router = setupRouter()
    await router.push('/compositions/new')
    await router.isReady()

    const wrapper = mount(CompositionCreateView, {
      global: { plugins: [router] },
    })

    expect(wrapper.find('.er-createshell').exists()).toBe(true)
    expect(wrapper.find('.er-createbar').exists()).toBe(true)
    expect(wrapper.find('.er-form-card').exists()).toBe(true)
    expect(wrapper.find('.er-modal').exists()).toBe(false)

    // Minimal bar contains brand and NO top Cancel link
    expect(wrapper.find('.er-topbar-brand').text()).toContain('Erato')
    expect(wrapper.find('.er-createbar').text()).not.toContain('Cancelar')

    // There is exactly one Cancelar action in the view (at the bottom)
    const cancelLinks = wrapper.findAll('a').filter((l) => l.text().trim() === 'Cancelar')
    expect(cancelLinks.length).toBe(1)
    expect(cancelLinks[0].attributes('href')).toBe('/')
  })

  it('contains title, 3-column metadata inputs, two-option visibility, and section include cards', async () => {
    const router = setupRouter()
    await router.push('/compositions/new')
    await router.isReady()

    const wrapper = mount(CompositionCreateView, {
      global: { plugins: [router] },
    })

    // Title input
    const titleInput = wrapper.find('#comp-title')
    expect(titleInput.exists()).toBe(true)

    // 3-column metadata row
    expect(wrapper.find('.er-field-grid').exists()).toBe(true)
    expect(wrapper.find('#comp-key').exists()).toBe(true)
    expect(wrapper.find('#comp-bpm').exists()).toBe(true)
    expect(wrapper.find('#comp-time-signature').exists()).toBe(true)

    // Visibility: exactly 2 options (Con enlace / Privada) - D7
    const radios = wrapper.findAll('input[type="radio"]')
    expect(radios.length).toBe(2)
    expect(wrapper.text()).toContain('Con enlace')
    expect(wrapper.text()).toContain('Privada')
    expect(wrapper.text().toLowerCase()).not.toContain('banda')

    // Section include cards
    const useCards = wrapper.findAll('.er-usecard')
    expect(useCards.length).toBe(5)

    // Default states: chords (true), tablature (false), lyrics (true), demos (true), todos (true)
    const chordsCard = useCards.find((c) => c.text().toLowerCase().includes('acordes'))
    const tabCard = useCards.find((c) => c.text().toLowerCase().includes('tablatura'))
    const lyricsCard = useCards.find((c) => c.text().toLowerCase().includes('letra'))
    const demosCard = useCards.find((c) => c.text().toLowerCase().includes('demos'))
    const todosCard = useCards.find((c) => c.text().toLowerCase().includes('tareas'))

    expect(chordsCard?.attributes('aria-pressed')).toBe('true')
    expect(tabCard?.attributes('aria-pressed')).toBe('false')
    expect(lyricsCard?.attributes('aria-pressed')).toBe('true')
    expect(demosCard?.attributes('aria-pressed')).toBe('true')
    expect(todosCard?.attributes('aria-pressed')).toBe('true')

    // Toggling tablature card toggles aria-pressed
    await tabCard!.trigger('click')
    expect(tabCard?.attributes('aria-pressed')).toBe('true')
  })

  it('submits creation request and navigates to composition detail page', async () => {
    const createSpy = vi.spyOn(compApi, 'createComposition').mockResolvedValueOnce({
      id: 'new-comp-123',
      owner_id: 'u1',
      title: 'Zamba de mi esperanza',
      visibility: 'public',
      status: 'idea',
      key: 'Em',
      bpm: 80,
      time_signature: '6/8',
      sections_enabled: {
        chords: true,
        tablature: true,
        lyrics: true,
        demos: true,
        todos: true,
      },
      todos: [],
      members: [],
      demos: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    const router = setupRouter()
    await router.push('/compositions/new')
    await router.isReady()

    const wrapper = mount(CompositionCreateView, {
      global: { plugins: [router] },
    })

    await wrapper.find('#comp-title').setValue('Zamba de mi esperanza')
    await wrapper.find('#comp-key').setValue('Em')
    await wrapper.find('#comp-bpm').setValue('80')
    await wrapper.find('#comp-time-signature').setValue('6/8')

    // Select public visibility
    const publicRadio = wrapper.find('input[type="radio"][value="public"]')
    await publicRadio.setValue()

    // Toggle tablature card to true
    const useCards = wrapper.findAll('.er-usecard')
    const tabCard = useCards.find((c) => c.text().toLowerCase().includes('tablatura'))
    await tabCard!.trigger('click')

    // Submit form
    await wrapper.find('form').trigger('submit')

    expect(createSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Zamba de mi esperanza',
        visibility: 'public',
        key: 'Em',
        bpm: 80,
        time_signature: '6/8',
        sections_enabled: expect.objectContaining({
          chords: true,
          tablature: true,
          lyrics: true,
          demos: true,
          todos: true,
        }),
      })
    )

    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 10))
    expect(router.currentRoute.value.path).toBe('/compositions/new-comp-123')
  })
})
