import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SharingModal from '@/features/sharing/SharingModal.vue'
import * as sharingApi from '@/api/sharing'

describe('SharingModal component', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('toggles visibility from private to public', async () => {
    const setVisSpy = vi.spyOn(sharingApi, 'setVisibility').mockResolvedValueOnce({
      id: 'comp-1',
      owner_id: 'user-1',
      title: 'Song',
      visibility: 'public',
      is_public: true,
      todos: [],
      members: [],
      demos: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    vi.spyOn(sharingApi, 'listInvites').mockResolvedValueOnce([])

    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-1',
        isPublic: false,
        canManage: true,
      },
    })
    await flushPromises()

    const publicCard = wrapper.findAll('.er-share-card')[0]
    await publicCard.trigger('click')
    await flushPromises()

    expect(setVisSpy).toHaveBeenCalledWith('comp-1', 'public')
    expect(wrapper.emitted('visibilityChanged')?.[0]).toEqual([true])
  })

  it('creates an invite and lists it', async () => {
    vi.spyOn(sharingApi, 'listInvites').mockResolvedValueOnce([])
    vi.spyOn(sharingApi, 'listMembers').mockResolvedValueOnce([])
    const createSpy = vi.spyOn(sharingApi, 'createInvite').mockResolvedValueOnce({
      id: 'inv-1',
      composition_id: 'comp-1',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 86400000).toISOString(),
      token: 'secret-invite-token',
      role: 'editor',
    })

    const wrapper = mount(SharingModal, {
      props: {
        compositionId: 'comp-1',
        isPublic: false,
        canManage: true,
      },
    })
    await flushPromises()

    const emailInput = wrapper.find('.er-invite-row input[type="email"]')
    await emailInput.setValue('colaborador@banda.com')

    const createBtn = wrapper.find('.er-invites-block button[data-test="send-invite-btn"]')
    await createBtn.trigger('click')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledWith('comp-1', {
      invited_email: 'colaborador@banda.com',
      role: 'editor',
    })
    expect(wrapper.find('.er-invite-created').text()).toContain('secret-invite-token')
  })
})
