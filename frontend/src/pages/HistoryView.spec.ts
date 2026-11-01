// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import HistoryView from './HistoryView.vue'

const mocks = vi.hoisted(() => ({ request: vi.fn(), state: null as any }))
vi.mock('../stores/session', () => ({ client: { request: mocks.request } }))
vi.mock('../stores/song', () => ({ useSong: () => mocks.state }))

const SONG = { id: 's1', title: 'Noche', section_versions: { lyrics: 4, meta: 2 } }
const row = (section: string, version: number, hour: number, summary: string) => ({
  section, version, summary, created_at: `2026-10-31T${String(hour).padStart(2, '0')}:00:00Z`, author: { display_name: 'Ana' },
})
const REVISIONS: Record<string, unknown[]> = {
  lyrics: [row('lyrics', 2, 12, 'editó la letra de Coro'), row('lyrics', 1, 9, 'agregó la letra')],
  meta: [row('meta', 2, 15, 'cambió el estado a Lista'), row('meta', 1, 8, 'creó la composición')],
}

function respond(revisions = REVISIONS) {
  mocks.request.mockImplementation(async (path: string) => revisions[path.split('/').pop()!] ?? [])
}
async function render(canEdit = true) {
  const song = ref<typeof SONG | null>({ ...SONG })
  mocks.state = {
    song, loading: ref(false), error: ref(''), canEdit: ref(canEdit), isPublic: ref(false), notice: ref(''),
    // The real load empties the song before it reads it again.
    load: vi.fn(async () => {
      song.value = null
      await nextTick()
      song.value = { ...SONG }
    }),
  }
  const wrapper = mount(HistoryView, { global: { stubs: { CompositionHeader: true } } })
  await flushPromises()
  return wrapper
}
type Wrapper = Awaited<ReturnType<typeof render>>
const rows = (wrapper: Wrapper) => wrapper.findAll('li').map(item => item.text())
const action = (wrapper: Wrapper, index: number, label: string) => wrapper.findAll('li')[index].findAll('button').find(node => node.text() === label)!

beforeEach(() => {
  vi.clearAllMocks()
  respond()
})

describe('history page — tests_md/propuesta-historial-2026-10-31.md', () => {
  it('HVW-004 shows the title and one list across sections, newest first', async () => {
    const wrapper = await render()
    expect(wrapper.get('h1').text()).toBe('Historial · Noche')
    expect(mocks.request.mock.calls.map(([path]) => path)).toEqual(
      ['lyrics', 'chords', 'tabs', 'tasks', 'meta'].map(section => `/songs/s1/revisions/${section}`),
    )
    const order = ['cambió el estado a Lista', 'editó la letra de Coro', 'agregó la letra', 'creó la composición']
    rows(wrapper).forEach((text, index) => expect(text).toContain(order[index]))
    expect(rows(wrapper)).toHaveLength(4)
  })
  it('HVW-005 keeps rows of two sections with the same version', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    expect(rows(await render()).filter(text => /letra de Coro|estado a Lista/.test(text))).toHaveLength(2)
    expect(warn.mock.calls.flat().join(' ')).not.toContain('Duplicate keys')
    warn.mockRestore()
  })
  it('HVW-006 reads the section and version of the row', async () => {
    const wrapper = await render()
    mocks.request.mockResolvedValueOnce({ version: 2, content: { lines: [] } })
    await action(wrapper, 0, 'Ver').trigger('click')
    await flushPromises()
    expect(mocks.request).toHaveBeenLastCalledWith('/songs/s1/revisions/meta/2')
    expect(wrapper.text()).toContain('Versión 2')
    expect(wrapper.get('pre').text()).toContain('"lines"')
  })
  it('HVW-007 restores the row with its base version and reloads', async () => {
    const wrapper = await render()
    mocks.request.mockClear()
    mocks.request.mockImplementation(async (path: string) => path.endsWith('/restore') ? {} : REVISIONS[path.split('/').pop()!] ?? [])
    await action(wrapper, 1, 'Restaurar').trigger('click')
    await flushPromises()
    expect(mocks.request).toHaveBeenCalledWith('/songs/s1/revisions/lyrics/2/restore', { method: 'POST', body: { base_version: 4 } })
    expect(mocks.state.load).toHaveBeenCalledOnce()
    expect(mocks.request.mock.calls).toHaveLength(6)
  })
  it('HVW-008 reports a stale section and keeps the list', async () => {
    const wrapper = await render()
    mocks.request.mockRejectedValueOnce(Object.assign(new Error('stale'), { code: 'version_conflict' }))
    await action(wrapper, 1, 'Restaurar').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toBe('La sección está desactualizada. Recarga antes de restaurar.')
    expect(rows(wrapper)).toHaveLength(4)
    expect(mocks.state.load).not.toHaveBeenCalled()
  })
  it('HVW-009 offers no restore to a reader', async () => {
    const wrapper = await render(false)
    expect(wrapper.findAll('button').map(node => node.text())).toEqual(['Ver', 'Ver', 'Ver', 'Ver'])
  })
  it('HVW-010 shows the error and no partial list', async () => {
    mocks.request.mockImplementation(async (path: string) => {
      if (path.endsWith('/tabs')) throw new Error('network')
      return REVISIONS[path.split('/').pop()!] ?? []
    })
    const wrapper = await render()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
    expect(rows(wrapper)).toEqual([])
    expect(wrapper.text()).not.toContain('Aún no hay cambios.')
  })
  it('HVW-011 says when there are no changes', async () => {
    respond({})
    expect((await render()).text()).toContain('Aún no hay cambios.')
  })
})
