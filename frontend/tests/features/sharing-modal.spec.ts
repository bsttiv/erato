import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SharingModal from '@/features/sharing/SharingModal.vue'
import AppModal from '@/shared/AppModal.vue'
import * as sharing from '@/api/sharing'
import * as bands from '@/api/bands'
import * as compositions from '@/api/compositions'
import { HttpError } from '@/api/compositions'

const state = vi.hoisted(() => ({ allowed: true }))
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({
  entitlements: ref({ can_share_with_people: state.allowed }), refresh: vi.fn(),
}) }))
const song = { id: 'c1', owner_id: 'owner', title: 'Canción', visibility: 'private' as const,
  todos: [], members: [{ user_id: 'm1', role: 'viewer' as const }],
  band_id: 'b1', band_editable: false, created_at: '', updated_at: '' }
const band = { id: 'b1', name: 'Trío', owner_id: 'owner', user_role: 'member' as const,
  seats_used: 2, seat_limit: null, active: true, pending_transfer: null, created_at: '', updated_at: '',
  members: [{ user_id: 'owner', display_name: 'Dueño', initials: 'D', role: 'member' as const },
    { user_id: 'm1', display_name: 'Ana', initials: 'A', role: 'member' as const },
    { user_id: 'm2', display_name: 'Luis', initials: 'L', role: 'owner' as const }] }
function setup(props = {}) {
  return mount(SharingModal, { props: { compositionId: 'c1', visibility: 'public', shareSlug: 'slug', ...props } })
}
function button(w: ReturnType<typeof setup>, text: string) {
  return w.findAll('button').find(b => b.text() === text)!
}
beforeEach(() => {
  vi.restoreAllMocks(); state.allowed = true
  vi.spyOn(compositions, 'getComposition').mockResolvedValue(song)
  vi.spyOn(bands, 'listBands').mockResolvedValue([band])
  vi.spyOn(bands, 'getBand').mockResolvedValue(band)
  vi.spyOn(sharing, 'listMembers').mockResolvedValue([
    { user_id: 'owner', role: 'owner', pending: false },
    { user_id: 'm1', role: 'viewer', pending: false },
    { user_id: 'outsider', display_name: 'Fuera', role: 'editor', pending: false },
  ])
  Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } })
})
describe('SharingModal band sharing', () => {
  it('keeps two visibility cards, AppModal close and a separate labelled band control without invites', async () => {
    const w = setup(); await flushPromises()
    expect(w.findAll('.er-share-card')).toHaveLength(2)
    expect(w.findAll('.er-share-card').map(b => b.text())).toEqual([
      expect.stringContaining('Con enlace'), expect.stringContaining('Privada')])
    expect(w.find('select[aria-label="Banda"]').exists()).toBe(true)
    expect(w.text()).not.toContain('Crear enlace de invitación')
    expect(w.text()).not.toContain('invitación pendiente')
    expect(w.text()).not.toMatch(/!|\p{Extended_Pictographic}/u)
    w.findComponent(AppModal).vm.$emit('close'); expect(w.emitted('close')).toBeTruthy()
  })
  it('loads attached band and offers roles only to its members, excluding the composition owner', async () => {
    const w = setup(); await flushPromises()
    expect(bands.getBand).toHaveBeenCalledWith('b1')
    expect(w.find('select[aria-label="Banda"]').element).toHaveProperty('value', 'b1')
    expect(w.findAll('select[data-test="member-role"]')).toHaveLength(2)
    expect(w.text()).toContain('Ana'); expect(w.text()).toContain('Luis')
    expect(w.text()).not.toContain('Fuera')
    expect(w.find('select[aria-label="Rol de Ana"]').element).toHaveProperty('value', 'viewer')
  })
  it('attaches a selected user band with band_editable without changing visibility', async () => {
    const detachedSong = { ...song, band_id: null, members: [] }
    vi.spyOn(compositions, 'getComposition').mockResolvedValue(detachedSong)
    const save = vi.spyOn(sharing, 'setCompositionBand').mockResolvedValue({ ...song, band_editable: true })
    const visibility = vi.spyOn(sharing, 'setVisibility')
    const w = setup(); await flushPromises()
    await w.find('select[aria-label="Banda"]').setValue('b1')
    await w.find('input[type="checkbox"]').setValue(true)
    await button(w, 'Guardar banda').trigger('click'); await flushPromises()
    expect(save).toHaveBeenCalledWith('c1', 'b1', true)
    expect(visibility).not.toHaveBeenCalled()
  })
  it('sets a role for a band member', async () => {
    const save = vi.spyOn(sharing, 'setMemberRole').mockResolvedValue(undefined)
    const w = setup(); await flushPromises()
    await w.find('select[aria-label="Rol de Luis"]').setValue('editor'); await flushPromises()
    expect(save).toHaveBeenCalledWith('c1', 'm2', 'editor')
  })
  it('confirms or cancels detach inline, then clears roles', async () => {
    const save = vi.spyOn(sharing, 'setCompositionBand').mockResolvedValue({ ...song, band_id: null, members: [] })
    const w = setup(); await flushPromises()
    await button(w, 'Desvincular banda').trigger('click'); expect(save).not.toHaveBeenCalled()
    await button(w, 'No').trigger('click'); expect(button(w, 'Desvincular banda')).toBeDefined()
    await button(w, 'Desvincular banda').trigger('click')
    await button(w, 'Sí').trigger('click'); await flushPromises()
    expect(save).toHaveBeenCalledWith('c1', null, false)
    expect(w.findAll('[data-test="member-role"]')).toHaveLength(0)
  })
  it('confirms removal of a role and explains inherited band access', async () => {
    const remove = vi.spyOn(sharing, 'removeMember').mockResolvedValue(undefined)
    const w = setup(); await flushPromises()
    await button(w, 'Quitar rol').trigger('click'); expect(remove).not.toHaveBeenCalled()
    expect(w.text()).toContain('acceso de la banda')
    await button(w, 'Sí').trigger('click'); await flushPromises()
    expect(remove).toHaveBeenCalledWith('c1', 'm1')
  })
  it('explains the gate and keeps public link and visibility working', async () => {
    state.allowed = false
    const save = vi.spyOn(sharing, 'setVisibility').mockResolvedValue({ ...song, visibility: 'private' })
    const w = setup(); await flushPromises()
    expect(w.find('select[aria-label="Banda"]').exists()).toBe(false)
    expect(w.text()).toContain('Compartir con personas no está disponible')
    await button(w, 'Copiar enlace').trigger('click')
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('/c/slug'))
    await w.findAll('.er-share-card')[1].trigger('click'); await flushPromises()
    expect(save).toHaveBeenCalledWith('c1', 'private')
  })
  it.each(['plan_gate_sharing', 'band_inactive', 'not_a_band_member', 'forbidden', 'not_found'])('maps %s without losing displayed data', async code => {
    vi.spyOn(sharing, 'setMemberRole').mockRejectedValue(new HttpError('server', 403, code))
    const w = setup(); await flushPromises()
    await w.find('select[aria-label="Rol de Ana"]').setValue('editor'); await flushPromises()
    expect(w.find('[role="alert"]').text()).not.toContain('server')
    expect(w.find('[role="alert"]').text()).not.toMatch(/!|\p{Extended_Pictographic}/u)
    expect(w.find('select[aria-label="Rol de Ana"]').element).toHaveProperty('value', 'viewer')
  })
})
it('uses design-system focus styles on visibility cards and the band checkbox', async () => {
  const w = setup(); await flushPromises()
  expect(w.findAll('.er-share-card').every(b => b.classes().includes('er-focus'))).toBe(true)
  expect(w.find('input[type="checkbox"]').classes()).toContain('er-focus')
  expect(w.find('input[readonly]').attributes('aria-label')).toBe('Enlace de lectura')
})
it('keeps inactive band roles readable and disables their changes while permitting confirmed detach', async () => {
  vi.spyOn(bands, 'listBands').mockResolvedValue([{ ...band, active: false }])
  vi.spyOn(bands, 'getBand').mockResolvedValue({ ...band, active: false })
  const w = setup(); await flushPromises()
  expect(w.text()).toContain('inactiva')
  expect(w.find('select[data-test="member-role"]').attributes('disabled')).toBeDefined()
  expect(button(w, 'Guardar banda').attributes('disabled')).toBeDefined()
  expect(button(w, 'Desvincular banda').attributes('disabled')).toBeUndefined()
})
it('uses the newly minted public slug', async () => {
  vi.spyOn(sharing, 'setVisibility').mockResolvedValue({ ...song, visibility: 'public', share_slug: 'minted' })
  const w = setup({ visibility: 'private', shareSlug: null }); await flushPromises()
  await w.findAll('.er-share-card')[0].trigger('click'); await flushPromises()
  await button(w, 'Copiar enlace').trigger('click')
  expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('/c/minted'))
})
it('shows load and clipboard failures in Spanish', async () => {
  vi.spyOn(bands, 'getBand').mockRejectedValue(new HttpError('internal', 404, 'not_found'))
  const w = setup(); await flushPromises()
  expect(w.find('[role="alert"]').text()).toContain('No se encontró')
  vi.mocked(navigator.clipboard.writeText).mockRejectedValue(new Error('denied'))
  await button(w, 'Copiar enlace').trigger('click'); await flushPromises()
  expect(w.find('[role="alert"]').text()).toContain('Cópialo desde el campo')
})
