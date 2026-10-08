import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { ref } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import BandView from '@/features/bands/BandView.vue'
import BandCreateForm from '@/features/bands/BandCreateForm.vue'
import AppNavExtras from '@/shared/AppNavExtras.vue'
import DashboardView from '@/features/compositions/DashboardView.vue'
import * as api from '@/api/bands'
import * as auth from '@/api/auth'
import * as compositions from '@/api/compositions'
import { HttpError } from '@/api/compositions'
import { PAYMENT_EXTENSION_KEY } from '@/extension'
import { routes } from '@/router/routes'

const entitlements = ref({ band_creation_mode: 'direct' })
const refresh = vi.fn().mockResolvedValue(undefined)
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({ entitlements, refresh }) }))
const base: api.BandResponse = {
  id: 'b', name: 'Jazz', owner_id: 'owner', user_role: 'owner', seats_used: 2, seat_limit: 8, active: true,
  members: [{ user_id: 'owner', display_name: 'Ana', initials: 'A', role: 'owner' },
    { user_id: 'member', display_name: 'Luis', initials: 'L', role: 'member' }],
  pending_transfer: null, created_at: '2026-10-07', updated_at: '2026-10-07',
}
let band: api.BandResponse
const wrappers: VueWrapper[] = []
async function setup(path = '/bands', entry = false, dashboard = false) {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: DashboardView }, { path: '/bands', component: BandView },
    { path: '/bands/:id', component: BandView },
    { path: '/plan/checkout', name: 'checkout', component: { template: '<p>Plan</p>' } },
    { path: '/compositions/new', component: { template: '<p />' } },
  ] })
  await router.push(path)
  const wrapper = mount(dashboard ? DashboardView : BandView, { global: { plugins: [router],
    provide: { [PAYMENT_EXTENSION_KEY as symbol]: entry ? { routes: [], bandCreationEntry: { name: 'checkout' } } : undefined },
  } })
  wrappers.push(wrapper)
  await flushPromises()
  return { wrapper, router }
}
async function click(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find(b => b.text() === text)
  expect(button, text).toBeDefined()
  await button!.trigger('click')
  await flushPromises()
}
beforeEach(() => {
  vi.restoreAllMocks()
  refresh.mockClear()
  band = structuredClone(base)
  entitlements.value = { band_creation_mode: 'direct' }
  vi.spyOn(auth, 'getMe').mockResolvedValue({ id: 'member', email: 'luis@example.com', display_name: 'Luis', created_at: '' })
  vi.spyOn(api, 'listBands').mockResolvedValue([base])
  vi.spyOn(api, 'getBand').mockImplementation(async () => structuredClone(band))
  vi.spyOn(api, 'listBandInvites').mockResolvedValue([{ id: 'i', expires_at: '2026-10-21' }])
  vi.spyOn(api, 'createBand').mockResolvedValue(base)
  vi.spyOn(api, 'renameBand').mockResolvedValue({ ...base, name: 'Swing' })
  vi.spyOn(api, 'createBandInvite').mockResolvedValue({ id: 'new', expires_at: '2026-10-21', invite_url: 'https://erato.test/invite/token' })
  for (const name of ['deleteBandInvite', 'removeBandMember', 'leaveBand', 'cancelBandTransfer', 'rejectBandTransfer'] as const)
    vi.spyOn(api, name).mockResolvedValue(undefined)
  vi.spyOn(api, 'requestBandTransfer').mockResolvedValue({ ...base, pending_transfer: { to_user_id: 'member', requested_at: '', expires_at: '2026-10-21' } })
  vi.spyOn(api, 'acceptBandTransfer').mockResolvedValue({ ...base, owner_id: 'member', user_role: 'owner', pending_transfer: null })
  vi.spyOn(compositions, 'listCompositions').mockResolvedValue([])
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: vi.fn().mockResolvedValue(undefined) } })
})
afterEach(() => { wrappers.splice(0).forEach(w => w.unmount()); vi.restoreAllMocks() })
describe('Band management', () => {
  it.each([
    ['Quitar a Luis', '¿Quitar a Luis?', 'removeBandMember', ['b', 'member']],
    ['Transferir a Luis', '¿Transferir la banda a Luis?', 'requestBandTransfer', ['b', 'member']],
    ['Salir de la banda', '¿Salir de la banda?', 'leaveBand', ['b']],
  ] as const)('confirms %s inline and allows cancellation', async (label, question, method, args) => {
    if (method === 'leaveBand') band.user_role = 'member'
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, label)
    expect(api[method]).not.toHaveBeenCalled()
    expect(wrapper.find('span.er-kbd').text()).toBe(question)
    expect(wrapper.findAll('button').find(b => b.text() === 'Sí')!.classes()).toContain('er-btn--danger')
    expect(wrapper.findAll('button').find(b => b.text() === 'Cancelar')!.classes()).toContain('er-btn--ghost')
    expect(wrapper.text()).not.toMatch(/[!¡]|\p{Extended_Pictographic}/u)
    await click(wrapper, 'Cancelar')
    expect(wrapper.find('span.er-kbd').exists()).toBe(false)
    expect(api[method]).not.toHaveBeenCalled()
    await click(wrapper, label)
    await click(wrapper, 'Sí')
    expect(api[method]).toHaveBeenCalledTimes(1)
    expect(api[method]).toHaveBeenCalledWith(...args)
    expect(wrapper.find('span.er-kbd').exists()).toBe(false)
  })
  it('keeps only one confirmation open and resets it after navigation', async () => {
    band.members.push({ user_id: 'other', display_name: 'Eva', initials: 'E', role: 'member' })
    const { wrapper, router } = await setup('/bands/b')
    await click(wrapper, 'Quitar a Luis')
    await click(wrapper, 'Transferir a Eva')
    expect(wrapper.findAll('span.er-kbd').map(s => s.text())).toEqual(['¿Transferir la banda a Eva?'])
    expect(api.removeBandMember).not.toHaveBeenCalled()
    expect(api.requestBandTransfer).not.toHaveBeenCalled()
    await click(wrapper, 'Sí')
    expect(api.requestBandTransfer).toHaveBeenCalledWith('b', 'other')
    expect(api.removeBandMember).not.toHaveBeenCalled()
    await click(wrapper, 'Quitar a Luis')
    await router.push('/bands'); await flushPromises()
    await router.push('/bands/b'); await flushPromises()
    expect(wrapper.find('span.er-kbd').exists()).toBe(false)
  })
  it('shows invitation expiry without ObjectIds and deletes without confirmation', async () => {
    const id = '507f1f77bcf86cd799439011'
    vi.mocked(api.listBandInvites).mockResolvedValue([{ id, expires_at: '2026-10-21' }])
    const { wrapper } = await setup('/bands/b')
    const expiry = new Date('2026-10-21').toLocaleDateString('es')
    expect(wrapper.text()).toContain(`Invitación · vence el ${expiry}`)
    expect(wrapper.html()).not.toContain(id)
    const button = wrapper.find(`button[aria-label="Eliminar la invitación que vence el ${expiry}"]`)
    expect(button.text()).toBe('Eliminar')
    await button.trigger('click'); await flushPromises()
    expect(api.deleteBandInvite).toHaveBeenCalledWith('b', id)
    expect(wrapper.find('span.er-kbd').exists()).toBe(false)
  })
  it('protects both routes and links from the dashboard', async () => {
    for (const path of ['/bands', '/bands/:id']) expect(routes.find(r => r.path === path)?.meta?.requiresAuth).toBe(true)
    const { wrapper } = await setup('/', false, true)
    expect(wrapper.find('a[href="/bands"]').text()).toContain('Bandas')
  })
  it('lists bands, links details, renders nav extras and respects copy rules', async () => {
    const { wrapper, router } = await setup()
    expect(wrapper.find('a[href="/bands/b"]').text()).toContain('Jazz')
    expect(wrapper.findComponent(AppNavExtras).exists()).toBe(true)
    expect(wrapper.text()).not.toMatch(/[!¡]|\p{Extended_Pictographic}/u)
    await router.push('/bands/b'); await flushPromises()
    expect(wrapper.text()).toContain('Luis')
    await router.push('/bands'); await flushPromises()
    expect(wrapper.find('a[href="/bands/b"]').exists()).toBe(true)
  })
  it('opens the direct form, validates a name and creates a band without payment controls', async () => {
    const { wrapper, router } = await setup()
    await click(wrapper, 'Crear banda')
    const form = wrapper.findComponent(BandCreateForm)
    expect(form.exists()).toBe(true)
    expect(wrapper.find('a[href^="/plan"]').exists()).toBe(false)
    expect(form.find('label[for="band-create-name"]').exists()).toBe(true)
    expect(form.find('input').attributes('maxlength')).toBe('80')
    await form.find('input').setValue('  ')
    await form.find('form').trigger('submit'); await flushPromises()
    expect(api.createBand).not.toHaveBeenCalled()
    await form.find('input').setValue(' Jazz ')
    await form.find('form').trigger('submit'); await flushPromises()
    expect(api.createBand).toHaveBeenCalledWith('Jazz')
    expect(router.currentRoute.value.path).toBe('/bands/b')
  })
  it('hands off to the registered payment entry', async () => {
    entitlements.value.band_creation_mode = 'hand_off'
    const { wrapper, router } = await setup('/bands', true)
    await click(wrapper, 'Crear banda')
    expect(router.currentRoute.value.name).toBe('checkout')
    expect(wrapper.findComponent(BandCreateForm).exists()).toBe(false)
    expect(api.createBand).not.toHaveBeenCalled()
  })
  it('disables hand-off without an entry and explains why', async () => {
    entitlements.value.band_creation_mode = 'hand_off'
    const { wrapper } = await setup()
    expect(wrapper.findAll('button').find(b => b.text() === 'Crear banda')?.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('La creación de bandas no está disponible en esta instalación.')
    expect(wrapper.findComponent(BandCreateForm).exists()).toBe(false)
  })
  it('shows members and seats, hides owner leave, renames and removes a member', async () => {
    const { wrapper } = await setup('/bands/b')
    expect(wrapper.text()).toContain('2 de 8 plazas')
    expect(wrapper.text()).toContain('Ana')
    expect(wrapper.text()).toContain('Luis')
    expect(wrapper.text()).not.toContain('Salir de la banda')
    await wrapper.find('#band-rename-name').setValue('Swing')
    await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(api.renameBand).toHaveBeenCalledWith('b', 'Swing')
    await click(wrapper, 'Quitar a Luis')
    await click(wrapper, 'Sí')
    expect(api.removeBandMember).toHaveBeenCalledWith('b', 'member')
  })
  it('creates, copies and deletes invite links without reconstructing stored tokens', async () => {
    const { wrapper } = await setup('/bands/b')
    expect(wrapper.findAll('button').filter(b => b.text() === 'Copiar enlace')).toHaveLength(0)
    await click(wrapper, 'Crear enlace de invitación')
    expect(api.createBandInvite).toHaveBeenCalledWith('b')
    expect(wrapper.find<HTMLInputElement>('input[readonly]').element.value).toBe('https://erato.test/invite/token')
    await click(wrapper, 'Copiar enlace')
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://erato.test/invite/token')
    expect(wrapper.text()).toContain('Enlace copiado')
    await wrapper.findAll('button').filter(b => b.text() === 'Eliminar').at(-1)!.trigger('click')
    await flushPromises()
    expect(api.deleteBandInvite).toHaveBeenCalledWith('b', 'new')
    expect(wrapper.find('input[readonly]').exists()).toBe(false)
  })
  it('requests and cancels ownership transfer', async () => {
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, 'Transferir a Luis')
    await click(wrapper, 'Sí')
    expect(api.requestBandTransfer).toHaveBeenCalledWith('b', 'member')
    expect(wrapper.text()).toContain(new Date('2026-10-21').toLocaleDateString('es'))
    expect(wrapper.text()).not.toContain('Transferir a Luis')
    await click(wrapper, 'Cancelar transferencia')
    expect(api.cancelBandTransfer).toHaveBeenCalledWith('b')
  })
  it('hides owner controls from members, leaves and refreshes entitlements', async () => {
    band.user_role = 'member'; band.seat_limit = null
    const { wrapper, router } = await setup('/bands/b')
    expect(wrapper.text()).toContain('2 plazas · sin límite')
    for (const text of ['Crear enlace', 'Quitar a', 'Transferir a', 'Guardar nombre']) expect(wrapper.text()).not.toContain(text)
    expect(api.listBandInvites).not.toHaveBeenCalled()
    await click(wrapper, 'Salir de la banda')
    await click(wrapper, 'Sí')
    expect(api.leaveBand).toHaveBeenCalledWith('b')
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(router.currentRoute.value.path).toBe('/bands')
  })
  it.each(['Aceptar', 'Rechazar'])('%s is available only to the transfer target', async action => {
    band.user_role = 'member'
    band.pending_transfer = { to_user_id: 'member', requested_at: '', expires_at: '2026-10-21' }
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, `${action} transferencia`)
    expect(action === 'Aceptar' ? api.acceptBandTransfer : api.rejectBandTransfer).toHaveBeenCalledWith('b')
    expect(refresh).toHaveBeenCalledTimes(action === 'Aceptar' ? 1 : 0)
  })
  it('hides target controls for other members', async () => {
    band.user_role = 'member'
    band.pending_transfer = { to_user_id: 'other', requested_at: '', expires_at: '2026-10-21' }
    const { wrapper } = await setup('/bands/b')
    expect(wrapper.text()).not.toContain('Aceptar transferencia')
    expect(wrapper.text()).not.toContain('Rechazar transferencia')
  })
  it('loads owner invitations after accepting ownership', async () => {
    band.user_role = 'member'
    band.pending_transfer = { to_user_id: 'member', requested_at: '', expires_at: '2026-10-21' }
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, 'Aceptar transferencia')
    expect(api.listBandInvites).toHaveBeenCalledWith('b')
    expect(wrapper.findAll('button').some(b => b.text() === 'Eliminar')).toBe(true)
    expect(wrapper.text()).not.toContain('Salir de la banda')
  })
  it('ignores an old detail response after navigating back to the list', async () => {
    let resolve!: (value: api.BandResponse) => void
    vi.mocked(api.getBand).mockReturnValueOnce(new Promise(r => { resolve = r }))
    const { wrapper, router } = await setup('/bands/b')
    await router.push('/bands'); await flushPromises()
    resolve(base); await flushPromises()
    expect(wrapper.find('h1').text()).toBe('Tus bandas')
    expect(wrapper.find('a[href="/bands/b"]').exists()).toBe(true)
    expect(api.listBandInvites).not.toHaveBeenCalled()
  })
  it('does not restore a detail when a transfer response arrives after navigation', async () => {
    let resolve!: (value: api.BandResponse) => void
    vi.mocked(api.requestBandTransfer).mockReturnValueOnce(new Promise(r => { resolve = r }))
    const { wrapper, router } = await setup('/bands/b')
    await click(wrapper, 'Transferir a Luis')
    await click(wrapper, 'Sí')
    await router.push('/bands'); await flushPromises()
    resolve({ ...base, pending_transfer: { to_user_id: 'member', requested_at: '', expires_at: '2026-10-21' } })
    await flushPromises()
    expect(wrapper.find('h1').text()).toBe('Tus bandas')
    expect(wrapper.find('a[href="/bands/b"]').exists()).toBe(true)
  })
  it('disables repeated actions until an invitation finishes', async () => {
    let resolve!: (value: api.BandInviteResponse) => void
    vi.mocked(api.createBandInvite).mockReturnValueOnce(new Promise(r => { resolve = r }))
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, 'Crear enlace de invitación')
    const button = wrapper.findAll('button').find(b => b.text() === 'Crear enlace de invitación')!
    expect(button.attributes('disabled')).toBeDefined()
    await button.trigger('click')
    expect(api.createBandInvite).toHaveBeenCalledTimes(1)
    resolve({ id: 'new', expires_at: '2026-10-21', invite_url: 'https://erato.test/invite/token' })
    await flushPromises()
    expect(button.attributes('disabled')).toBeUndefined()
  })
  it('reports clipboard failures without claiming the link was copied', async () => {
    vi.mocked(navigator.clipboard.writeText).mockRejectedValue(new Error('Denied!'))
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, 'Crear enlace de invitación')
    await click(wrapper, 'Copiar enlace')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Enlace copiado')
  })
  it('keeps a member in the view and does not refresh when leave fails', async () => {
    band.user_role = 'member'
    vi.mocked(api.leaveBand).mockRejectedValue(new HttpError('English!', 409, 'owner_must_transfer'))
    const { wrapper, router } = await setup('/bands/b')
    await click(wrapper, 'Salir de la banda')
    await click(wrapper, 'Sí')
    expect(router.currentRoute.value.path).toBe('/bands/b')
    expect(refresh).not.toHaveBeenCalled()
    expect(wrapper.find('[role="alert"]').text()).toContain('Transfiere la propiedad')
  })
  const errors = [
    ['band_full', 'No quedan plazas en esta banda.'],
    ['transfer_pending', 'Ya hay una transferencia pendiente.'],
    ['owner_must_transfer', 'Transfiere la propiedad antes de salir de la banda.'],
    ['not_a_band_member', 'Esta persona ya no pertenece a la banda.'],
    ['transfer_expired', 'La transferencia venció. Pide una nueva al dueño.'],
    ['transfer_not_found', 'Ya no hay una transferencia pendiente.'],
    ['transfer_not_confirmed', 'No se pudo confirmar la transferencia. Inténtalo de nuevo.'],
    ['plan_gate_band_creation', 'La creación de bandas no está disponible con tu plan.'],
    ['band_inactive', 'Esta banda está inactiva.'],
    ['validation_error', 'Revisa los datos. El nombre debe tener entre 1 y 80 caracteres.'],
  ]
  it.each(errors)('renders %s in Spanish without backend copy', async (code, message) => {
    vi.mocked(api.createBandInvite).mockRejectedValue(new HttpError('English!', 409, code))
    const { wrapper } = await setup('/bands/b')
    await click(wrapper, 'Crear enlace de invitación')
    expect(wrapper.find('[role="alert"]').text()).toBe(message)
    expect(wrapper.text()).not.toMatch(/[!¡]|\p{Extended_Pictographic}/u)
  })
  it('shows creation failures in the form and keeps the entered name', async () => {
    vi.mocked(api.createBand).mockRejectedValue(new HttpError('English!', 403, 'plan_gate_band_creation'))
    const { wrapper } = await setup()
    await click(wrapper, 'Crear banda')
    await wrapper.find('#band-create-name').setValue('Jazz')
    await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe(errors[7][1])
    expect(wrapper.find<HTMLInputElement>('#band-create-name').element.value).toBe('Jazz')
  })
  it('shows list failures and lets you retry', async () => {
    vi.mocked(api.listBands).mockRejectedValueOnce(new Error('Network!'))
    const { wrapper } = await setup()
    expect(wrapper.find('[role="alert"]').text()).toBe('No se pudo completar la acción. Inténtalo de nuevo.')
    await click(wrapper, 'Reintentar')
    expect(wrapper.find('a[href="/bands/b"]').exists()).toBe(true)
  })
})
