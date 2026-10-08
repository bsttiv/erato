import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SectionHistoryPanel from '@/features/compositions/SectionHistoryPanel.vue'
import CompositionDetailView from '@/features/compositions/CompositionDetailView.vue'
import * as historyApi from '@/api/history'
import * as compApi from '@/api/compositions'
import { HttpError } from '@/api/compositions'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('@/features/plan/useEntitlements', () => ({
  useEntitlements: () => ({ entitlements: { value: { can_view_history: true } } }),
}))

const mockHistoryItems: historyApi.HistoryItemSummary[] = [
  {
    rev: 2,
    author: { id: 'u2', display_name: 'Miles Davis' },
    created_at: '2026-10-04T12:00:00Z',
  },
  {
    rev: 1,
    author: { id: 'u1', display_name: 'John Coltrane' },
    created_at: '2026-10-04T10:00:00Z',
  },
]

describe('SectionHistoryPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('lists revisions with author and date on open', async () => {
    const listSpy = vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isDirty: false,
      },
    })

    await flushPromises()

    expect(listSpy).toHaveBeenCalledWith('comp-123', 'lyrics', 20)
    const items = wrapper.findAll('.er-history-item')
    expect(items.length).toBe(2)
    expect(items[0].text()).toContain('2')
    expect(items[0].text()).toContain('Miles Davis')
    expect(items[1].text()).toContain('1')
    expect(items[1].text()).toContain('John Coltrane')
  })

  it('paginates when next_before_rev is present', async () => {
    vi.spyOn(historyApi, 'listSectionHistory')
      .mockResolvedValueOnce({
        items: [mockHistoryItems[0]],
        next_before_rev: 2,
      })
      .mockResolvedValueOnce({
        items: [mockHistoryItems[1]],
        next_before_rev: undefined,
      })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
      },
    })

    await flushPromises()

    let items = wrapper.findAll('.er-history-item')
    expect(items.length).toBe(1)

    const moreBtn = wrapper.find('[data-test="load-more-history-btn"]')
    expect(moreBtn.exists()).toBe(true)
    await moreBtn.trigger('click')
    await flushPromises()

    items = wrapper.findAll('.er-history-item')
    expect(items.length).toBe(2)
    expect(historyApi.listSectionHistory).toHaveBeenCalledWith('comp-123', 'lyrics', 20, 2)
  })

  it('when load-more fails, loaded items remain intact and retry resets error', async () => {
    vi.spyOn(historyApi, 'listSectionHistory')
      .mockResolvedValueOnce({
        items: [mockHistoryItems[0]],
        next_before_rev: 2,
      })
      .mockRejectedValueOnce(new Error('Fallo de red al paginar'))
      .mockResolvedValueOnce({
        items: [mockHistoryItems[1]],
        next_before_rev: undefined,
      })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
      },
    })

    await flushPromises()
    expect(wrapper.findAll('.er-history-item').length).toBe(1)

    const moreBtn = wrapper.find('[data-test="load-more-history-btn"]')
    await moreBtn.trigger('click')
    await flushPromises()

    // Items are NOT wiped out
    expect(wrapper.findAll('.er-history-item').length).toBe(1)
    const loadMoreError = wrapper.find('[data-test="load-more-error"]')
    expect(loadMoreError.exists()).toBe(true)
    expect(loadMoreError.text()).toContain('Fallo de red al paginar')

    // Retry succeeds and resets the error
    await moreBtn.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.er-history-item').length).toBe(2)
    expect(wrapper.find('[data-test="load-more-error"]').exists()).toBe(false)
  })

  it('previews content of selected revision', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })
    const getDetailSpy = vi.spyOn(historyApi, 'getHistoryRevision').mockResolvedValue({
      rev: 1,
      content: { text: 'Verso original bajo el farol' },
      author: { id: 'u1', display_name: 'John Coltrane' },
      created_at: '2026-10-04T10:00:00Z',
    })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
      },
    })

    await flushPromises()

    const itemBtns = wrapper.findAll('[data-test="preview-history-item-btn"]')
    expect(itemBtns.length).toBe(2)
    await itemBtns[1].trigger('click')
    await flushPromises()

    expect(getDetailSpy).toHaveBeenCalledWith('comp-123', 'lyrics', 1)
    const preview = wrapper.find('.er-history-preview')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('Verso original bajo el farol')
  })

  it('shows preview error separately without quotes when getHistoryRevision fails', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })
    vi.spyOn(historyApi, 'getHistoryRevision').mockRejectedValue(new Error('Error de red'))

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
      },
    })

    await flushPromises()

    const itemBtns = wrapper.findAll('[data-test="preview-history-item-btn"]')
    await itemBtns[0].trigger('click')
    await flushPromises()

    const errorEl = wrapper.find('.er-history-preview-error')
    expect(errorEl.exists()).toBe(true)
    expect(errorEl.text()).toBe('No se pudo cargar la vista previa.')
    expect(wrapper.find('.er-history-preview-text').exists()).toBe(false)
  })

  it('restores clean section directly without confirmation, reloads list, does not close panel', async () => {
    const listSpy = vi.spyOn(historyApi, 'listSectionHistory')
      .mockResolvedValueOnce({
        items: mockHistoryItems,
        next_before_rev: undefined,
      })
      .mockResolvedValueOnce({
        items: [
          { rev: 3, author: { id: 'u2', display_name: 'Miles Davis' }, created_at: '2026-10-04T12:05:00Z' },
          ...mockHistoryItems,
        ],
        next_before_rev: undefined,
      })

    const restoreSpy = vi.spyOn(historyApi, 'restoreSectionHistory').mockResolvedValue({
      content: 'Verso original restaurado',
      rev: 3,
    })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isDirty: false,
      },
    })

    await flushPromises()

    const restoreBtns = wrapper.findAll('[data-test="restore-history-btn"]')
    expect(restoreBtns.length).toBeGreaterThan(0)
    await restoreBtns[1].trigger('click')
    await flushPromises()

    // No confirmation when isDirty is false
    expect(wrapper.find('[data-test="history-restore-confirm"]').exists()).toBe(false)
    expect(restoreSpy).toHaveBeenCalledWith('comp-123', 'lyrics', 1, 2)
    expect(wrapper.emitted('restored')).toBeTruthy()
    expect(wrapper.emitted('restored')![0][0]).toEqual({
      section: 'lyrics',
      rev: 3,
      content: { content: 'Verso original restaurado', rev: 3 },
    })

    // Panel does NOT close; reloads list so newest revision appears at top
    expect(wrapper.emitted('close')).toBeFalsy()
    expect(listSpy).toHaveBeenCalledTimes(2)
    expect(wrapper.findAll('.er-history-item')[0].text()).toContain('3')
  })

  it('when isDirty is true, shows confirmation before restoring; canceling aborts and keeps local content', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })
    const restoreSpy = vi.spyOn(historyApi, 'restoreSectionHistory')

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isDirty: true,
      },
    })

    await flushPromises()

    const restoreBtns = wrapper.findAll('[data-test="restore-history-btn"]')
    await restoreBtns[1].trigger('click')
    await flushPromises()

    // Confirmation must appear
    const confirmBox = wrapper.find('[data-test="history-restore-confirm"]')
    expect(confirmBox.exists()).toBe(true)
    expect(confirmBox.text()).toContain('Tienes cambios sin guardar en esta sección; restaurar los descartará.')

    const cancelBtn = confirmBox.find('[data-test="cancel-restore-btn"]')
    expect(cancelBtn.exists()).toBe(true)
    expect(cancelBtn.text()).toBe('Cancelar')

    const confirmBtn = confirmBox.find('[data-test="confirm-restore-btn"]')
    expect(confirmBtn.exists()).toBe(true)
    expect(confirmBtn.text()).toBe('Restaurar')

    // Click cancel
    await cancelBtn.trigger('click')
    await flushPromises()

    expect(restoreSpy).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="history-restore-confirm"]').exists()).toBe(false)
    expect(wrapper.emitted('restored')).toBeFalsy()
  })

  it('when isDirty is true, confirming restore proceeds and restores', async () => {
    vi.spyOn(historyApi, 'listSectionHistory')
      .mockResolvedValueOnce({
        items: mockHistoryItems,
        next_before_rev: undefined,
      })
      .mockResolvedValueOnce({
        items: [
          { rev: 3, author: { id: 'u2', display_name: 'Miles Davis' }, created_at: '2026-10-04T12:05:00Z' },
          ...mockHistoryItems,
        ],
        next_before_rev: undefined,
      })

    const restoreSpy = vi.spyOn(historyApi, 'restoreSectionHistory').mockResolvedValue({
      content: 'Verso original restaurado',
      rev: 3,
    })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isDirty: true,
      },
    })

    await flushPromises()

    const restoreBtns = wrapper.findAll('[data-test="restore-history-btn"]')
    await restoreBtns[1].trigger('click')
    await flushPromises()

    const confirmBtn = wrapper.find('[data-test="confirm-restore-btn"]')
    await confirmBtn.trigger('click')
    await flushPromises()

    expect(restoreSpy).toHaveBeenCalledWith('comp-123', 'lyrics', 1, 2)
    expect(wrapper.emitted('restored')).toBeTruthy()
    expect(wrapper.emitted('close')).toBeFalsy()
  })

  it('disables restore buttons while isSaving is true', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isSaving: true,
      },
    })

    await flushPromises()

    const restoreBtns = wrapper.findAll('[data-test="restore-history-btn"]')
    expect(restoreBtns.length).toBeGreaterThan(0)
    for (const btn of restoreBtns) {
      expect((btn.element as HTMLButtonElement).disabled).toBe(true)
    }
  })

  it('emits conflict on restore 409 section_conflict', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: mockHistoryItems,
      next_before_rev: undefined,
    })
    const conflictBody = {
      error: 'section_conflict',
      section: 'lyrics',
      current_rev: 4,
      content: { content: 'Texto más nuevo de otro usuario' },
      author: { id: 'u3', display_name: 'Thelonious Monk' },
      updated_at: '2026-10-04T12:05:00Z',
    }
    vi.spyOn(historyApi, 'restoreSectionHistory').mockRejectedValue(
      new HttpError('Conflicto', 409, 'section_conflict', conflictBody)
    )

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
        isDirty: false,
      },
    })

    await flushPromises()

    const restoreBtns = wrapper.findAll('[data-test="restore-history-btn"]')
    await restoreBtns[0].trigger('click')
    await flushPromises()

    expect(wrapper.emitted('conflict')).toBeTruthy()
    expect(wrapper.emitted('conflict')![0][0]).toEqual({
      section: 'lyrics',
      current_rev: 4,
      content: { content: 'Texto más nuevo de otro usuario' },
      author: { id: 'u3', display_name: 'Thelonious Monk' },
      updated_at: '2026-10-04T12:05:00Z',
    })
  })

  it('shows notice on 403 plan_gate_history without data loss', async () => {
    vi.spyOn(historyApi, 'listSectionHistory').mockRejectedValue(
      new HttpError('Operación bloqueada por el plan', 403, 'plan_gate_history', {
        error: 'plan_gate_history',
        detail: 'Operación bloqueada por el plan: plan_gate_history',
      })
    )

    const wrapper = mount(SectionHistoryPanel, {
      props: {
        open: true,
        compositionId: 'comp-123',
        section: 'lyrics',
        currentRev: 2,
        canEdit: true,
      },
    })

    await flushPromises()

    expect(wrapper.find('.er-history-item').exists()).toBe(false)
    const notice = wrapper.find('.er-history-notice')
    expect(notice.exists()).toBe(true)
    expect(notice.text().toLowerCase()).toContain('no está disponible')
    expect(wrapper.emitted('restored')).toBeFalsy()
  })
})

describe('CompositionDetailView history trigger and restore integration', () => {
  const sampleComp: compApi.CompositionResponse = {
    id: 'comp-1',
    owner_id: 'user-1',
    title: 'Noche de jazz',
    visibility: 'private',
    user_role: 'editor',
    lyrics: { content: 'Bajo el farol...' },
    chords: { instrument: 'guitar', entries: [] },
    tablature: { tabs: [] },
    section_revs: { lyrics: 4, chords: 2, tablature: 1 },
    todos: [],
    members: [],
    created_at: '2026-10-04T00:00:00Z',
    updated_at: '2026-10-04T00:00:00Z',
  }

  function setupRouter() {
    return createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/compositions/:id', component: { template: '<div />' } }],
    })
  }

  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(compApi, 'getComposition').mockResolvedValue(sampleComp)
    vi.spyOn(compApi, 'listCompositions').mockResolvedValue([])
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({ items: [], next_before_rev: undefined })
  })

  it('renders history triggers for editors and owners', async () => {
    const router = setupRouter()
    const wrapper = mount(CompositionDetailView, {
      props: { composition: sampleComp },
      global: { plugins: [router] },
    })

    await flushPromises()

    expect(wrapper.find('[data-test="open-lyrics-history-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="open-chords-history-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="open-tablature-history-btn"]').exists()).toBe(true)
  })

  it('hides history triggers for viewers', async () => {
    const router = setupRouter()
    const viewerComp: compApi.CompositionResponse = {
      ...sampleComp,
      user_role: 'viewer',
    }
    const wrapper = mount(CompositionDetailView, {
      props: { composition: viewerComp },
      global: { plugins: [router] },
    })

    await flushPromises()

    expect(wrapper.find('[data-test="open-lyrics-history-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="open-chords-history-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="open-tablature-history-btn"]').exists()).toBe(false)
  })

  it('restoring a version updates content, resets dirty baseline and sends expected_rev matching current rev', async () => {
    const router = setupRouter()
    vi.spyOn(historyApi, 'listSectionHistory').mockResolvedValue({
      items: [
        { rev: 2, author: { id: 'u1', display_name: 'Miles' }, created_at: '2026-10-04T10:00:00Z' },
      ],
    })
    const restoreSpy = vi.spyOn(historyApi, 'restoreSectionHistory').mockResolvedValue({
      content: 'Verso restaurado desde el historial',
      rev: 5,
    })

    const wrapper = mount(CompositionDetailView, {
      props: { composition: sampleComp },
      global: { plugins: [router] },
    })
    await flushPromises()

    // Mutate lyrics locally so it is dirty
    await wrapper.find('[data-test="edit-lyrics-text-btn"]').trigger('click')
    await flushPromises()
    const textarea = wrapper.find('[data-test="lyrics-textarea"]')
    expect(textarea.exists()).toBe(true)
    await textarea.setValue('Cambio local sin guardar')
    await flushPromises()

    // Open lyrics history panel
    await wrapper.find('[data-test="open-lyrics-history-btn"]').trigger('click')
    await flushPromises()

    const historyModal = wrapper.findComponent(SectionHistoryPanel)
    expect(historyModal.exists()).toBe(true)
    expect(historyModal.props('isDirty')).toBe(true)

    // Click restore rev 2 -> confirmation should appear because it is dirty
    const restoreBtn = historyModal.find('[data-test="restore-history-btn"]')
    await restoreBtn.trigger('click')
    await flushPromises()

    const confirmBox = historyModal.find('[data-test="history-restore-confirm"]')
    expect(confirmBox.exists()).toBe(true)

    // Cancel first
    await confirmBox.find('[data-test="cancel-restore-btn"]').trigger('click')
    await flushPromises()
    expect(restoreSpy).not.toHaveBeenCalled()
    expect((wrapper.find('[data-test="lyrics-textarea"]').element as HTMLTextAreaElement).value).toBe('Cambio local sin guardar')

    // Click restore again, then confirm
    await restoreBtn.trigger('click')
    await flushPromises()
    await historyModal.find('[data-test="confirm-restore-btn"]').trigger('click')
    await flushPromises()

    // Sent expected_rev=4 (matching initialRevs.lyrics=4)
    expect(restoreSpy).toHaveBeenCalledWith('comp-1', 'lyrics', 2, 4)

    // Editor content is updated with restored content
    expect((wrapper.find('[data-test="lyrics-textarea"]').element as HTMLTextAreaElement).value).toBe('Verso restaurado desde el historial')

    // Section is no longer dirty!
    expect(historyModal.props('isDirty')).toBe(false)
  })
})
