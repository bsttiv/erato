import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SharingModal from '@/features/sharing/SharingModal.vue'
import AppModal from '@/shared/AppModal.vue'
import * as sharingApi from '@/api/sharing'
import type { MemberDetail, InviteResponse } from '@/api/sharing'

const sampleMembers: MemberDetail[] = [
  {
    user_id: 'user-owner',
    display_name: 'Carlos Santana',
    email: 'carlos@santana.com',
    initials: 'CS',
    role: 'owner',
    pending: false,
  },
  {
    user_id: 'user-editor',
    display_name: 'Ana Pérez',
    email: 'ana@perez.com',
    initials: 'AP',
    role: 'editor',
    pending: false,
  },
  {
    user_id: 'user-viewer',
    display_name: 'Juan Domínguez',
    email: 'juan@dominguez.com',
    initials: 'JD',
    role: 'viewer',
    pending: false,
  },
  {
    user_id: null,
    invite_id: 'inv-pending',
    display_name: null,
    email: 'pendiente@banda.com',
    initials: null,
    role: 'editor',
    pending: true,
  },
]

describe('SharingModal feature', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(sharingApi, 'listMembers').mockResolvedValue(sampleMembers)
    vi.spyOn(sharingApi, 'listInvites').mockResolvedValue([])
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    })
  })

  it('is wrapped inside AppModal and emits close on escape or modal close', async () => {
    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'public',
        shareSlug: 'bajo-el-farol-xyz',
      },
    })
    await flushPromises()

    const appModal = wrapper.findComponent(AppModal)
    expect(appModal.exists()).toBe(true)
    expect(appModal.props('open')).toBe(true)

    // Trigger close on AppModal
    appModal.vm.$emit('close')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('presents exactly two visibility options: Con enlace and Privada (D7)', async () => {
    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'private',
        shareSlug: 'bajo-el-farol-xyz',
      },
    })
    await flushPromises()

    const cards = wrapper.findAll('.er-share-card')
    expect(cards.length).toBe(2)
    expect(cards[0].text()).toContain('Con enlace')
    expect(cards[1].text()).toContain('Privada')
  })

  it('toggling visibility calls setVisibility with correct arguments', async () => {
    const setVisSpy = vi.spyOn(sharingApi, 'setVisibility').mockResolvedValue({
      id: 'comp-100',
      owner_id: 'user-owner',
      title: 'Bajo el farol',
      visibility: 'public',
      is_public: true,
      todos: [],
      members: [],
      demos: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'private',
        shareSlug: 'bajo-el-farol-xyz',
      },
    })
    await flushPromises()

    const publicCard = wrapper.findAll('.er-share-card')[0]
    await publicCard.trigger('click')
    await flushPromises()

    expect(setVisSpy).toHaveBeenCalledWith('comp-100', 'public')
    expect(wrapper.emitted('visibilityChanged')?.[0]).toEqual(['public'])
  })

  it('displays read-only share link with working copy button when public', async () => {
    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'public',
        shareSlug: 'bajo-el-farol-xyz',
      },
    })
    await flushPromises()

    const linkContainer = wrapper.find('.er-share-link')
    expect(linkContainer.exists()).toBe(true)

    const input = linkContainer.find('input[readonly]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toContain('/c/bajo-el-farol-xyz')

    const copyBtn = linkContainer.find('button')
    expect(copyBtn.text()).toContain('Copiar')

    await copyBtn.trigger('click')
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('/c/bajo-el-farol-xyz')
    )
  })

  it('displays permission checklist explaining access rules', async () => {
    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'public',
      },
    })
    await flushPromises()

    const permList = wrapper.find('.er-perm-list')
    expect(permList.exists()).toBe(true)
    expect(permList.text().toLowerCase()).toContain('ver letra y acordes')
    expect(permList.text().toLowerCase()).toContain('escuchar demos')
  })

  const createdInvite = {
    id: 'inv-new',
    composition_id: 'comp-100',
    role: 'viewer',
    expires_at: '2026-10-08T12:00:00Z',
    invite_url: 'http://localhost/invite/plain-token',
  } as InviteResponse

  function mountPrivate() {
    return mount(SharingModal, {
      props: { compositionId: 'comp-100', title: 'Bajo el farol', visibility: 'private' },
    })
  }

  it('invite row has no email input, a role dropdown and an enabled create-link button', async () => {
    const wrapper = mountPrivate()
    await flushPromises()

    const inviteRow = wrapper.find('.er-invite-row')
    expect(inviteRow.exists()).toBe(true)
    expect(inviteRow.find('input[type="email"]').exists()).toBe(false)
    expect(wrapper.html()).not.toContain('correo@ejemplo.com')

    const roleSelect = inviteRow.find('select')
    expect(roleSelect.text()).toContain('Editor')
    expect(roleSelect.text()).toContain('Solo ver')

    const inviteBtn = inviteRow.find('button[data-test="send-invite-btn"]')
    expect(inviteBtn.text()).toContain('Crear enlace de invitación')
    expect(inviteBtn.attributes('disabled')).toBeUndefined()
  })

  it('creates the invite without invited_email and with the selected role', async () => {
    const createSpy = vi.spyOn(sharingApi, 'createInvite').mockResolvedValue(createdInvite)
    const wrapper = mountPrivate()
    await flushPromises()

    await wrapper.find('.er-invite-row select').setValue('viewer')
    await wrapper.find('button[data-test="send-invite-btn"]').trigger('click')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    expect(createSpy).toHaveBeenCalledWith('comp-100', { role: 'viewer' })
  })

  it('shows the created link and the expiry date derived from expires_at', async () => {
    vi.spyOn(sharingApi, 'createInvite').mockResolvedValue(createdInvite)
    const wrapper = mountPrivate()
    await flushPromises()

    await wrapper.find('button[data-test="send-invite-btn"]').trigger('click')
    await flushPromises()

    const result = wrapper.find('[data-test="invite-result"]')
    expect(result.exists()).toBe(true)
    const input = result.find('input[readonly]')
    expect((input.element as HTMLInputElement).value).toBe('http://localhost/invite/plain-token')

    const expected = new Date('2026-10-08T12:00:00Z').toLocaleDateString('es')
    expect(result.text()).toContain(`Vence el ${expected}`)
    expect(result.text().toLowerCase()).not.toContain('un solo uso')
  })

  it('copy button writes the invite link to the clipboard and confirms', async () => {
    vi.spyOn(sharingApi, 'createInvite').mockResolvedValue(createdInvite)
    const wrapper = mountPrivate()
    await flushPromises()

    await wrapper.find('button[data-test="send-invite-btn"]').trigger('click')
    await flushPromises()

    const copyBtn = wrapper.find('[data-test="copy-invite-btn"]')
    expect(copyBtn.text()).toContain('Copiar enlace')
    await copyBtn.trigger('click')
    await flushPromises()

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('http://localhost/invite/plain-token')
    expect(wrapper.find('[data-test="invite-result"]').text()).toContain('Enlace copiado')
  })

  it('does not crash when the clipboard write fails', async () => {
    vi.spyOn(sharingApi, 'createInvite').mockResolvedValue(createdInvite)
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
    })
    const wrapper = mountPrivate()
    await flushPromises()

    await wrapper.find('button[data-test="send-invite-btn"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="copy-invite-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="invite-result"]').text()).not.toContain('Enlace copiado')
  })

  it('renders a pending invite without email as role plus pending label, never undefined', async () => {
    vi.spyOn(sharingApi, 'listMembers').mockResolvedValue([
      {
        user_id: null,
        invite_id: 'inv-x',
        display_name: null,
        email: null,
        initials: null,
        role: 'viewer',
        pending: true,
      },
    ])
    const wrapper = mountPrivate()
    await flushPromises()

    const item = wrapper.find('.er-member')
    const text = item.text()
    expect(text.toLowerCase()).toContain('invitación pendiente')
    expect(text).toContain('Solo ver')
    expect(text).not.toContain('undefined')
    expect(text).not.toContain('null')
    expect(text).not.toContain('()')
    expect(item.find('.er-member-id').text()).toBe('Invitación por enlace')
  })

  it('member list displays owner, active members, and pending invitations with initials, name, email and role badge', async () => {
    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-100',
        title: 'Bajo el farol',
        visibility: 'private',
      },
    })
    await flushPromises()

    const memberList = wrapper.find('.er-invites-list')
    expect(memberList.exists()).toBe(true)

    const items = memberList.findAll('.er-member')
    expect(items.length).toBe(4)

    // Owner item
    expect(items[0].text()).toContain('CS')
    expect(items[0].text()).toContain('Carlos Santana')
    expect(items[0].text()).toContain('carlos@santana.com')
    expect(items[0].text().toLowerCase()).toContain('dueño')

    // Editor item
    expect(items[1].text()).toContain('AP')
    expect(items[1].text()).toContain('Ana Pérez')
    expect(items[1].text()).toContain('ana@perez.com')
    expect(items[1].text().toLowerCase()).toContain('editor')

    // Viewer item
    expect(items[2].text()).toContain('JD')
    expect(items[2].text()).toContain('Juan Domínguez')
    expect(items[2].text()).toContain('juan@dominguez.com')
    expect(items[2].text().toLowerCase()).toContain('solo ver')

    // Pending invitation item
    expect(items[3].text()).toContain('pendiente@banda.com')
    expect(items[3].text().toLowerCase()).toContain('invitación pendiente')
  })
})
