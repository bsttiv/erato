// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CompositionView from './CompositionView.vue'

const mocks = vi.hoisted(() => ({ saveSections: vi.fn(), conflicts: null as { value: unknown[] } | null, error: null as { value: string } | null, canEdit: null as { value: boolean } | null, isPublic: null as { value: boolean } | null }))
vi.mock('../api/compositionPath', () => ({ useCompositionPath: () => '/canciones/s1' }))
vi.mock('../stores/session', () => ({ client: { request: vi.fn() } }))
vi.mock('../stores/song', async () => {
  const { ref } = await import('vue')
  const song = { id: 's1', title: 'Noche', status: 'ready', lyrics: { lines: [{ text: 'Hola', chords: [] }] }, chords: [], tasks: [], demos: [], section_versions: {} }
  const conflicts = ref<unknown[]>([])
  const error = ref('')
  const canEdit = ref(true)
  mocks.canEdit = canEdit
  const isPublic = ref(true)
  mocks.isPublic = isPublic
  mocks.conflicts = conflicts
  mocks.error = error
  return {
    useSong: () => ({
      song: ref(song), loading: ref(false), error, canEdit, isPublic, conflicts,
      notice: ref(''), saving: ref(false), load: vi.fn(), saveSections: mocks.saveSections,
    }),
  }
})

function render() {
  return mount(CompositionView, {
    attachTo: document.body,
    global: {
      stubs: {
        CompositionHeader: { template: '<header><slot /></header>' }, SongDetailsModal: true, LyricSheet: true, LyricPlacer: true, TodoList: true, HistoryList: true,
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}
type Wrapper = ReturnType<typeof render>
const dialog = (wrapper: Wrapper) => wrapper.get('dialog').element as HTMLDialogElement
const button = (wrapper: Wrapper, label: string) => wrapper.findAll('button').filter(node => node.text() === label)
async function openEditor(wrapper: Wrapper) {
  await button(wrapper, 'Editar letra')[0].trigger('click')
  await flushPromises()
}
async function saveFromModal(wrapper: Wrapper) {
  await wrapper.get('dialog .btn-primary').trigger('click')
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  document.body.innerHTML = ''
  mocks.conflicts!.value = []
  mocks.error!.value = ''
  mocks.canEdit!.value = true
  mocks.isPublic!.value = true
  // jsdom has no modal behavior of its own.
  HTMLDialogElement.prototype.showModal = function () { this.open = true }
  HTMLDialogElement.prototype.close = function () {
    this.open = false
    this.dispatchEvent(new Event('close'))
  }
})

describe('chord editor — tests_md/propuesta-editor-acordes-2026-10-31.md', () => {
  it('CHE-010 offers neither the instrumental button nor the placement form', async () => {
    const wrapper = render()
    await openEditor(wrapper)
    expect(wrapper.text()).not.toContain('Agregar parte instrumental')
    expect(wrapper.text()).not.toContain('Ubicar')
    expect(wrapper.find('dialog select').exists()).toBe(false)
    expect(wrapper.find('dialog input').exists()).toBe(false)
    expect(wrapper.get('label[for="lyrics-text"]').text()).toContain('#')
  })
  it('STA-001 shows the status on the song page', () => {
    expect(render().get('article').text()).toContain('Lista')
  })
  it('HVW-012 no longer shows the history on the Letra page', () => {
    mocks.isPublic!.value = false
    expect(render().text()).not.toContain('Historial')
  })
  it('DET-011 offers the details button next to Compartir, never to a reader', () => {
    expect(render().get('header').text()).toContain('Editar detalles')
    mocks.canEdit!.value = false
    expect(render().text()).not.toContain('Editar detalles')
  })
})

describe('lyrics modal', () => {
  it('MOD-001 opens the editor in a modal, not below the sheet', async () => {
    const wrapper = render()
    expect(dialog(wrapper).open).toBe(false)
    expect(wrapper.find('#lyrics-text').exists()).toBe(false)
    await openEditor(wrapper)
    expect(dialog(wrapper).open).toBe(true)
    expect(wrapper.find('dialog #lyrics-text').exists()).toBe(true)
  })
  it('MOD-002 closes with Cerrar or Escape and keeps the draft', async () => {
    const wrapper = render()
    await openEditor(wrapper)
    await wrapper.get('#lyrics-text').setValue('Borrador')
    await wrapper.get('dialog .btn-ghost.btn-sm').trigger('click')
    await flushPromises()
    expect(dialog(wrapper).open).toBe(false)
    await openEditor(wrapper)
    expect((wrapper.get('#lyrics-text').element as HTMLTextAreaElement).value).toBe('Borrador')
    // Escape makes the browser close the dialog and fire its close event.
    dialog(wrapper).close()
    await flushPromises()
    expect(wrapper.find('#lyrics-text').exists()).toBe(false)
    await openEditor(wrapper)
    expect((wrapper.get('#lyrics-text').element as HTMLTextAreaElement).value).toBe('Borrador')
  })
  it('MOD-003 closes after a successful save', async () => {
    const wrapper = render()
    await openEditor(wrapper)
    mocks.saveSections.mockResolvedValue({
      saved: [{ section: 'lyrics', version: 2 }],
      song: { lyrics: { lines: [{ text: 'Hola', chords: [] }] }, tasks: [] },
    })
    await saveFromModal(wrapper)
    expect(mocks.saveSections).toHaveBeenCalledOnce()
    expect(dialog(wrapper).open).toBe(false)
  })
  it('MOD-004 closes on a conflict or an error and keeps the draft', async () => {
    const wrapper = render()
    await openEditor(wrapper)
    await wrapper.get('#lyrics-text').setValue('Borrador')
    mocks.saveSections.mockImplementation(async () => {
      mocks.conflicts!.value = [{ section: 'lyrics', current_version: 5 }]
      return { saved: [], song: {} }
    })
    await saveFromModal(wrapper)
    expect(dialog(wrapper).open).toBe(false)
    expect(wrapper.text()).toContain('No se guardó lyrics')
    await openEditor(wrapper)
    mocks.saveSections.mockImplementation(async () => {
      mocks.error!.value = 'No se pudo guardar'
      return null
    })
    await saveFromModal(wrapper)
    expect(dialog(wrapper).open).toBe(false)
    expect(wrapper.text()).toContain('No se pudo guardar')
    await openEditor(wrapper)
    expect((wrapper.get('#lyrics-text').element as HTMLTextAreaElement).value).toBe('Borrador')
  })
})
