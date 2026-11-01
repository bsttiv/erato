import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
const mocks = vi.hoisted(() => ({ request: vi.fn(), restore: vi.fn(), route: { params: { slug: 'a'.repeat(24) } } }))
vi.mock('./session', () => ({ client: { request: mocks.request }, session: { restore: mocks.restore } }))
vi.mock('vue-router', () => ({ useRoute: () => mocks.route }))
const initial = () => ({ id: 'a'.repeat(24), chords: [], tasks: [], section_versions: { chords: 1, tasks: 1 }, title: 'Canción' })
beforeEach(() => { vi.resetModules(); vi.clearAllMocks(); mocks.route.params.slug = 'a'.repeat(24); mocks.restore.mockResolvedValue(true) })
async function open() {
  const { useSong } = await import('./song')
  const store = useSong()
  await flushPromises()
  return store
}
function ownSong() {
  mocks.request.mockImplementation(async (path) => path.includes('?workspace') ? [{ ...initial(), origin: 'own' }] : initial())
}
// Decisions 09 §6 and 14 approve REV rules; original numeric case rows are unavailable.
it('REV-rule sends each section with its current base version', async () => {
  ownSong()
  const store = await open()
  mocks.request.mockResolvedValue({ song: { ...initial(), section_versions: { chords: 1, tasks: 2 } }, saved: [{ section: 'tasks', version: 2 }], conflicts: [] })
  await store.saveSections({ tasks: [{ title: 'Grabar', done: false }] })
  expect(mocks.request).toHaveBeenLastCalledWith(`/songs/${'a'.repeat(24)}/sections`, { method: 'PUT', body: { sections: { tasks: [{ title: 'Grabar', done: false }] }, base_versions: { tasks: 1 } } })
  expect(store.song.value.section_versions.tasks).toBe(2)
})
it('REV-rule reports partial conflicts without rebasing the conflicted draft', async () => {
  ownSong()
  const store = await open()
  mocks.request.mockResolvedValue({ song: { ...initial(), section_versions: { chords: 3, tasks: 2 } }, saved: [{ section: 'tasks', version: 2 }], conflicts: [{ section: 'chords', current_version: 3 }] })
  await store.saveSections({ chords: [], tasks: [] })
  expect(store.conflicts.value).toEqual([{ section: 'chords', current_version: 3 }])
  expect(store.song.value.section_versions).toEqual({ chords: 1, tasks: 2 })
})
// Decision 06 permission matrix: public visibility does not grant writes.
it('PERM-rule public song readers cannot save sections', async () => {
  mocks.route.params.slug = 'public-slug'
  mocks.restore.mockResolvedValue(false)
  mocks.request.mockResolvedValue({ title: 'Pública', chords: [], section_versions: { chords: 1 } })
  const store = await open()
  expect(store.canEdit.value).toBe(false)
  expect(store.canManage.value).toBe(false)
  expect(await store.saveSections({ chords: [] })).toBeNull()
  expect(mocks.request).toHaveBeenCalledTimes(1)
  expect(mocks.request).toHaveBeenCalledWith('/c/public-slug', { authenticated: false })
})
// Decision 06: explicit editor invitation grants edits; viewer invitation does not.
it.each([['editor', true], ['viewer', false]])('PERM-rule own shared %s membership controls editing', async (role, expected) => {
  mocks.request.mockImplementation(async (path) => {
    if (path.includes('?workspace')) return [{ ...initial(), origin: 'shared' }]
    if (path === '/me') return { username: 'bob', display_name: 'Bob' }
    if (path.endsWith('/members')) return [{ username: 'bob', display_name: 'Bob', role }]
    return initial()
  })
  const store = await open()
  expect(store.canEdit.value).toBe(expected)
  expect(store.canManage.value).toBe(false)
})
