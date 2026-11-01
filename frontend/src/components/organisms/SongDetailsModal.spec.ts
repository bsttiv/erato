// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import SongDetailsModal from './SongDetailsModal.vue'

const mocks = vi.hoisted(() => ({ request: vi.fn(), saveSections: vi.fn(), state: null as any }))
vi.mock('../../stores/session', () => ({ client: { request: mocks.request } }))
vi.mock('../../stores/song', () => ({ useSong: () => mocks.state }))

const original = { id: 's1', status: 'idea', visibility: 'private', tempo: 92, time_signature: '4/4' }

function render(song: Record<string, unknown> = original, canManage = true) {
  mocks.state = {
    song: ref({ ...song }), saving: ref(false), error: ref(''), conflicts: ref([]), canManage: ref(canManage),
    saveSections: mocks.saveSections,
  }
  return mount(SongDetailsModal, { props: { open: true }, attachTo: document.body })
}
type Wrapper = ReturnType<typeof render>
const choose = (wrapper: Wrapper, label: string) => wrapper.findAll('button').find(node => node.text() === label)!.trigger('click')
const pressed = (wrapper: Wrapper) => wrapper.findAll('[aria-pressed="true"]').map(node => node.text())
const tempo = (wrapper: Wrapper) => wrapper.get('#details-bpm')
const meter = (wrapper: Wrapper) => wrapper.get('#details-meter')
async function submit(wrapper: Wrapper) {
  await wrapper.get('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  document.body.innerHTML = ''
  mocks.saveSections.mockResolvedValue({ saved: [], song: {} })
  HTMLDialogElement.prototype.showModal = function () { this.open = true }
  HTMLDialogElement.prototype.close = function () { this.open = false }
})

describe('SongDetailsModal — tests_md/propuesta-detalles-cancion-2026-10-31.md', () => {
  it('DET-002 shows the current details', () => {
    const wrapper = render({ ...original, status: 'in_progress', visibility: 'public' })
    expect(pressed(wrapper)).toEqual(['En progreso', 'Pública'])
    expect((tempo(wrapper).element as HTMLInputElement).value).toBe('92')
    expect((meter(wrapper).element as HTMLSelectElement).value).toBe('4/4')
  })
  it('DET-003 sends only the changed meta fields and closes', async () => {
    const wrapper = render()
    await choose(wrapper, 'Lista')
    await tempo(wrapper).setValue(120)
    await meter(wrapper).setValue('3/4')
    await submit(wrapper)
    expect(mocks.saveSections).toHaveBeenCalledWith({ meta: { status: 'ready', tempo: 120, time_signature: '3/4' } })
    expect(mocks.request).not.toHaveBeenCalled()
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
  it('DET-004 sends a null tempo when it is emptied', async () => {
    const wrapper = render()
    await tempo(wrapper).setValue('')
    await submit(wrapper)
    expect(mocks.saveSections).toHaveBeenCalledWith({ meta: { tempo: null } })
  })
  it('DET-005 sends nothing without changes and closes', async () => {
    const wrapper = render()
    await submit(wrapper)
    expect(mocks.saveSections).not.toHaveBeenCalled()
    expect(mocks.request).not.toHaveBeenCalled()
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
  it('DET-006 lets the owner change the visibility', async () => {
    const wrapper = render()
    const updated = { ...original, visibility: 'public' }
    mocks.request.mockResolvedValue(updated)
    await choose(wrapper, 'Pública')
    await submit(wrapper)
    expect(mocks.request).toHaveBeenCalledWith('/songs/s1/visibility', { method: 'PATCH', body: { visibility: 'public' } })
    expect(mocks.state.song.value).toEqual(updated)
    expect(mocks.saveSections).not.toHaveBeenCalled()
  })
  it('DET-007 offers no visibility control to a non-owner', async () => {
    const wrapper = render(original, false)
    expect(wrapper.text()).not.toContain('Visibilidad')
    await tempo(wrapper).setValue(100)
    await submit(wrapper)
    expect(mocks.saveSections).toHaveBeenCalledOnce()
    expect(mocks.request).not.toHaveBeenCalled()
  })
  it('DET-008 stops before the visibility when meta fails or conflicts', async () => {
    const failed = render()
    await choose(failed, 'Pública')
    await tempo(failed).setValue(100)
    mocks.saveSections.mockResolvedValue(null)
    await submit(failed)
    expect(failed.emitted('close')).toHaveLength(1)
    const conflicted = render()
    await choose(conflicted, 'Pública')
    await tempo(conflicted).setValue(100)
    mocks.saveSections.mockImplementation(async () => {
      mocks.state.conflicts.value = [{ section: 'meta', current_version: 5 }]
      return { saved: [], song: {} }
    })
    await submit(conflicted)
    expect(conflicted.emitted('close')).toHaveLength(1)
    expect(mocks.request).not.toHaveBeenCalled()
  })
  it('DET-009 closes and reports a failed visibility change', async () => {
    const wrapper = render()
    mocks.request.mockRejectedValue(new Error('network'))
    await choose(wrapper, 'Pública')
    await submit(wrapper)
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(mocks.state.error.value).not.toBe('')
    expect(mocks.state.song.value.visibility).toBe('private')
  })
  it('DET-010 keeps a time signature outside the usual list', async () => {
    const wrapper = render({ ...original, time_signature: '7/8' })
    expect((meter(wrapper).element as HTMLSelectElement).value).toBe('7/8')
    await submit(wrapper)
    expect(mocks.saveSections).not.toHaveBeenCalled()
  })
})
