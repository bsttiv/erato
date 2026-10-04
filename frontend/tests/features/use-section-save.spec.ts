import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'
import * as compApi from '@/api/compositions'
import { useSectionSave } from '@/features/compositions/useSectionSave'
import SectionConflictDialog from '@/features/compositions/SectionConflictDialog.vue'
import type { ChordsSection, TabEntry, TodoItem } from '@/api/compositions'

describe('useSectionSave composable and SectionConflictDialog', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('only dirty sections are sent; cleans dirty state and updates rev on 200', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([{ text: 'Buy strings', done: false }])

    const spies = {
      chords: vi.spyOn(compApi, 'updateChordsSection').mockResolvedValue({ instrument: 'guitar', entries: [], rev: 2 }),
      tablature: vi.spyOn(compApi, 'updateTablatureSection').mockResolvedValue({ tabs: [], rev: 3 }),
      lyrics: vi.spyOn(compApi, 'updateLyricsSection').mockResolvedValue({ content: 'Modified lyrics', rev: 4 }),
      todos: vi.spyOn(compApi, 'updateTodosSection').mockResolvedValue([{ text: 'Buy strings', done: false }]),
    }

    const { save, isDirty, revisions } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 2, lyrics: 3 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    // Initially clean
    expect(isDirty('lyrics')).toBe(false)
    expect(isDirty('chords')).toBe(false)
    expect(isDirty('tablature')).toBe(false)
    expect(isDirty('todos')).toBe(false)

    // Save with no changes -> no API calls
    await save()
    expect(spies.lyrics).not.toHaveBeenCalled()
    expect(spies.chords).not.toHaveBeenCalled()
    expect(spies.tablature).not.toHaveBeenCalled()
    expect(spies.todos).not.toHaveBeenCalled()

    // Modify only lyrics
    lyrics.value = 'Modified lyrics'
    expect(isDirty('lyrics')).toBe(true)

    await save()

    expect(spies.lyrics).toHaveBeenCalledTimes(1)
    expect(spies.lyrics).toHaveBeenCalledWith('comp-100', { content: 'Modified lyrics' }, 3)
    expect(spies.chords).not.toHaveBeenCalled()
    expect(spies.tablature).not.toHaveBeenCalled()
    expect(spies.todos).not.toHaveBeenCalled()

    // Baseline and revision updated
    expect(isDirty('lyrics')).toBe(false)
    expect(revisions.value.lyrics).toBe(4)
  })

  it('queues a conflict on 409 and leaves other successful saves intact', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflictErr = new compApi.HttpError(
      'Conflict',
      409,
      'section_conflict',
      {
        error: 'section_conflict',
        section: 'lyrics',
        current_rev: 8,
        content: { content: 'Remote edit lyrics' },
        author: { id: 'u2', display_name: 'Camila' },
        updated_at: '2026-10-04T15:00:00Z',
      }
    )

    const spies = {
      chords: vi.spyOn(compApi, 'updateChordsSection').mockResolvedValue({
        instrument: 'guitar',
        entries: [{ bar: 1, notes: [0, 2, 2, 0, 0, 0], name: 'Em' }],
        rev: 5,
      }),
      lyrics: vi.spyOn(compApi, 'updateLyricsSection').mockRejectedValue(conflictErr),
    }

    const { save, isDirty, revisions, activeConflict, conflicts } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 4, tablature: 1, lyrics: 7 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    // Modify both chords and lyrics
    chords.value = { instrument: 'guitar', entries: [{ bar: 1, notes: [0, 2, 2, 0, 0, 0], name: 'Em' }] }
    lyrics.value = 'Local edit lyrics'

    await save()

    // Chords succeeded: updated rev and not dirty
    expect(spies.chords).toHaveBeenCalledWith('comp-100', chords.value, 4)
    expect(revisions.value.chords).toBe(5)
    expect(isDirty('chords')).toBe(false)

    // Lyrics conflicted: queued conflict and still dirty
    expect(conflicts.value.length).toBe(1)
    expect(activeConflict.value?.section).toBe('lyrics')
    expect(activeConflict.value?.current_rev).toBe(8)
    expect(activeConflict.value?.author?.display_name).toBe('Camila')
    expect(isDirty('lyrics')).toBe(true)
  })

  it('resolves conflict with "Sobrescribir con la mía" by resaving with current_rev', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflictErr = new compApi.HttpError(
      'Conflict',
      409,
      'section_conflict',
      {
        error: 'section_conflict',
        section: 'lyrics',
        current_rev: 10,
        content: { content: 'Server text' },
        author: { id: 'u3', display_name: 'Pablo' },
      }
    )

    const lyricsSpy = vi.spyOn(compApi, 'updateLyricsSection')
      .mockRejectedValueOnce(conflictErr)
      .mockResolvedValueOnce({ content: 'My local lyrics', rev: 11 })

    const { save, revisions, isDirty, activeConflict, resolveOverwrite } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 9 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    lyrics.value = 'My local lyrics'
    await save()

    expect(activeConflict.value).not.toBeNull()

    // User chooses overwrite
    await resolveOverwrite(activeConflict.value!)

    expect(lyricsSpy).toHaveBeenCalledTimes(2)
    // Second call used current_rev 10 as expected_rev
    expect(lyricsSpy).toHaveBeenLastCalledWith('comp-100', { content: 'My local lyrics' }, 10)
    expect(revisions.value.lyrics).toBe(11)
    expect(isDirty('lyrics')).toBe(false)
    expect(activeConflict.value).toBeNull()
  })

  it('sobrescribir vuelve a entrar en conflicto reemplazando los datos del conflicto', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflict1 = new compApi.HttpError('Conflict 1', 409, 'section_conflict', {
      error: 'section_conflict',
      section: 'lyrics',
      current_rev: 5,
      content: { content: 'Server text v1' },
      author: { id: 'u1', display_name: 'Marcos' },
    })

    const conflict2 = new compApi.HttpError('Conflict 2', 409, 'section_conflict', {
      error: 'section_conflict',
      section: 'lyrics',
      current_rev: 6,
      content: { content: 'Server text v2' },
      author: { id: 'u2', display_name: 'Lucía' },
    })

    const lyricsSpy = vi.spyOn(compApi, 'updateLyricsSection')
      .mockRejectedValueOnce(conflict1) // initial save
      .mockRejectedValueOnce(conflict2) // first overwrite attempt
      .mockResolvedValueOnce({ content: 'My lyrics', rev: 7 }) // second overwrite attempt

    const { save, revisions, isDirty, activeConflict, resolveOverwrite, saveStateText } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 4 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    lyrics.value = 'My lyrics'
    await save()

    expect(activeConflict.value?.current_rev).toBe(5)
    expect(activeConflict.value?.author?.display_name).toBe('Marcos')

    // First overwrite attempt gets 409 with rev 6
    await resolveOverwrite(activeConflict.value!)

    expect(lyricsSpy).toHaveBeenNthCalledWith(2, 'comp-100', { content: 'My lyrics' }, 5)
    expect(activeConflict.value).not.toBeNull()
    expect(activeConflict.value?.current_rev).toBe(6)
    expect(activeConflict.value?.author?.display_name).toBe('Lucía')
    expect(saveStateText.value).toBe('error al guardar')

    // Second overwrite attempt uses updated rev 6 and resolves
    await resolveOverwrite(activeConflict.value!)

    expect(lyricsSpy).toHaveBeenNthCalledWith(3, 'comp-100', { content: 'My lyrics' }, 6)
    expect(revisions.value.lyrics).toBe(7)
    expect(isDirty('lyrics')).toBe(false)
    expect(activeConflict.value).toBeNull()
    expect(saveStateText.value).toBe('guardado')
  })

  it('leaves conflict in queue and sets error state on non-409 error during overwrite', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflict = new compApi.HttpError('Conflict', 409, 'section_conflict', {
      error: 'section_conflict',
      section: 'lyrics',
      current_rev: 5,
      content: { content: 'Remote' },
    })

    vi.spyOn(compApi, 'updateLyricsSection')
      .mockRejectedValueOnce(conflict)
      .mockRejectedValueOnce(new Error('Network error 500'))

    const { save, activeConflict, resolveOverwrite, saveStateText } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 4 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    lyrics.value = 'My edit'
    await save()

    await resolveOverwrite(activeConflict.value!)

    expect(activeConflict.value?.current_rev).toBe(5)
    expect(saveStateText.value).toBe('error al guardar')
  })

  it('resolveOverwrite and resolveLoadSaved return early if isSaving is true', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflict = new compApi.HttpError('Conflict', 409, 'section_conflict', {
      error: 'section_conflict',
      section: 'lyrics',
      current_rev: 5,
      content: { content: 'Remote' },
    })

    let resolveSavePromise: (value: any) => void = () => {}
    const slowSave = new Promise((resolve) => {
      resolveSavePromise = resolve
    })

    const lyricsSpy = vi.spyOn(compApi, 'updateLyricsSection')
      .mockRejectedValueOnce(conflict)
      .mockReturnValueOnce(slowSave as any)

    const { save, activeConflict, resolveOverwrite, resolveLoadSaved, isSaving } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 4 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    lyrics.value = 'My edit'
    await save()

    // Trigger overwrite - it hangs on slowSave
    const overwritePromise = resolveOverwrite(activeConflict.value!)
    expect(isSaving.value).toBe(true)

    // Double-click attempt while in-flight: must be ignored
    await resolveOverwrite(activeConflict.value!)
    resolveLoadSaved(activeConflict.value!)

    // Only 2 API calls happened (initial save + first overwrite), not 3
    expect(lyricsSpy).toHaveBeenCalledTimes(2)

    // Complete the in-flight request
    resolveSavePromise({ content: 'My edit', rev: 6 })
    await overwritePromise
    expect(isSaving.value).toBe(false)
  })

  it('resolves conflict with "Cargar la versión guardada" by updating value, baseline and revision', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflictErr = new compApi.HttpError(
      'Conflict',
      409,
      'section_conflict',
      {
        error: 'section_conflict',
        section: 'lyrics',
        current_rev: 12,
        content: { content: 'Server text restored' },
        author: null,
      }
    )

    vi.spyOn(compApi, 'updateLyricsSection').mockRejectedValueOnce(conflictErr)

    const { save, revisions, isDirty, activeConflict, resolveLoadSaved } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 11 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
      onLoadSection: (section, content) => {
        if (section === 'lyrics') {
          lyrics.value = typeof content === 'string' ? content : content.content
        }
      },
    })

    lyrics.value = 'My local text'
    await save()

    expect(activeConflict.value).not.toBeNull()

    // User chooses load saved
    resolveLoadSaved(activeConflict.value!)

    expect(lyrics.value).toBe('Server text restored')
    expect(revisions.value.lyrics).toBe(12)
    expect(isDirty('lyrics')).toBe(false)
    expect(activeConflict.value).toBeNull()
  })

  it('dismissing conflict keeps the local dirty edit intact', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Initial lyrics')
    const todos = ref<TodoItem[]>([])

    const conflictErr = new compApi.HttpError(
      'Conflict',
      409,
      'section_conflict',
      {
        error: 'section_conflict',
        section: 'lyrics',
        current_rev: 5,
        content: { content: 'Remote version' },
      }
    )

    vi.spyOn(compApi, 'updateLyricsSection').mockRejectedValueOnce(conflictErr)

    const { save, isDirty, activeConflict, dismissConflict } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 4 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    lyrics.value = 'My unsaved changes'
    await save()

    expect(activeConflict.value).not.toBeNull()

    // User dismisses dialog
    dismissConflict()

    expect(activeConflict.value).toBeNull()
    expect(lyrics.value).toBe('My unsaved changes')
    expect(isDirty('lyrics')).toBe(true)
  })

  it('todos are sent without expected_rev and only when dirty', async () => {
    const chords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
    const tabs = ref<TabEntry[]>([])
    const lyrics = ref<string>('Lyrics')
    const todos = ref<TodoItem[]>([{ text: 'Task 1', done: false }])

    const todosSpy = vi.spyOn(compApi, 'updateTodosSection').mockResolvedValue([
      { text: 'Task 1', done: true },
    ])

    const { save, isDirty } = useSectionSave({
      compositionId: () => 'comp-100',
      initialRevs: () => ({ chords: 1, tablature: 1, lyrics: 1 }),
      chords: () => chords.value,
      tabs: () => tabs.value,
      lyrics: () => lyrics.value,
      todos: () => todos.value,
    })

    todos.value = [{ text: 'Task 1', done: true }]
    expect(isDirty('todos')).toBe(true)

    await save()

    expect(todosSpy).toHaveBeenCalledTimes(1)
    expect(todosSpy).toHaveBeenCalledWith('comp-100', [{ text: 'Task 1', done: true }])
    expect(isDirty('todos')).toBe(false)
  })

  describe('SectionConflictDialog UI', () => {
    const sampleConflict = {
      section: 'lyrics' as const,
      current_rev: 7,
      content: { content: 'Contenido remoto' },
      author: { id: 'u2', display_name: 'Santiago' },
      updated_at: '2026-10-04T12:00:00Z',
    }

    it('renders with title, author info and buttons without exclamation or emoji', () => {
      const wrapper = mount(SectionConflictDialog, {
        props: {
          open: true,
          conflict: sampleConflict,
        },
      })

      const text = wrapper.text()
      expect(text).toContain('Conflicto en letra')
      expect(text).toContain('Santiago')
      expect(text).not.toContain('!')
      expect(text).not.toContain('¡')
      // No emoji in copy
      expect(/\p{Extended_Pictographic}/u.test(text)).toBe(false)

      const buttons = wrapper.findAll('button')
      const btnTexts = buttons.map(b => b.text())
      expect(btnTexts).toContain('Cargar la versión guardada')
      expect(btnTexts).toContain('Sobrescribir con la mía')
    })

    it('emits loadSaved and overwrite events on button clicks', async () => {
      const wrapper = mount(SectionConflictDialog, {
        props: {
          open: true,
          conflict: sampleConflict,
        },
      })

      const buttons = wrapper.findAll('button')
      const loadBtn = buttons.find(b => b.text().includes('Cargar la versión guardada'))!
      const overwriteBtn = buttons.find(b => b.text().includes('Sobrescribir con la mía'))!

      await loadBtn.trigger('click')
      expect(wrapper.emitted('loadSaved')).toBeTruthy()

      await overwriteBtn.trigger('click')
      expect(wrapper.emitted('overwrite')).toBeTruthy()
    })

    it('emits close on Escape or close button', async () => {
      const wrapper = mount(SectionConflictDialog, {
        props: {
          open: true,
          conflict: sampleConflict,
        },
        attachTo: document.body,
      })

      const closeBtn = wrapper.find('.er-modal-close')
      if (closeBtn.exists()) {
        await closeBtn.trigger('click')
        expect(wrapper.emitted('close')).toBeTruthy()
      }

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('close')).toBeTruthy()
      wrapper.unmount()
    })

    it('disables action buttons while isSaving is true', () => {
      const wrapper = mount(SectionConflictDialog, {
        props: {
          open: true,
          conflict: sampleConflict,
          isSaving: true,
        },
      })

      const actionButtons = wrapper.findAll('.er-conflict-actions button')
      expect(actionButtons.length).toBe(2)
      actionButtons.forEach(btn => {
        expect(btn.attributes('disabled')).toBeDefined()
      })
    })
  })
})
