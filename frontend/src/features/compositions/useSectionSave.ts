import { ref, computed } from 'vue'
import {
  updateChordsSection,
  updateTablatureSection,
  updateLyricsSection,
  updateTodosSection,
} from '@/api/compositions'
import type {
  ChordsSection,
  TabEntry,
  TodoItem,
  SectionConflictBody,
} from '@/api/compositions'

export type VersionedSectionKey = 'lyrics' | 'chords' | 'tablature'
export type SectionKey = VersionedSectionKey | 'todos'

export interface SectionConflict extends Omit<SectionConflictBody, 'error'> {
  error?: 'section_conflict'
}

export interface UseSectionSaveOptions {
  compositionId: () => string | undefined
  initialRevs?: () => { lyrics?: number; chords?: number; tablature?: number } | undefined
  chords: () => ChordsSection
  tabs: () => TabEntry[]
  lyrics: () => string
  todos: () => TodoItem[]
  onLoadSection?: (section: VersionedSectionKey, content: any) => void
}

function cloneDeep<T>(val: T): T {
  if (val === undefined || val === null) return val
  return JSON.parse(JSON.stringify(val))
}

export function useSectionSave(options: UseSectionSaveOptions) {
  const revisions = ref<{ lyrics: number; chords: number; tablature: number }>({
    lyrics: options.initialRevs?.()?.lyrics ?? 0,
    chords: options.initialRevs?.()?.chords ?? 0,
    tablature: options.initialRevs?.()?.tablature ?? 0,
  })

  // Baselines snapshotting the latest successfully loaded or saved state
  const baselines = ref({
    lyrics: cloneDeep(options.lyrics()),
    chords: cloneDeep(options.chords()),
    tablature: cloneDeep(options.tabs()),
    todos: cloneDeep(options.todos()),
  })

  const conflicts = ref<SectionConflict[]>([])
  const activeConflict = computed<SectionConflict | null>(() => conflicts.value[0] || null)

  const isSaving = ref<boolean>(false)
  const saveStateText = ref<string>('guardado')

  function resetBaselines(values?: {
    lyrics?: string
    chords?: ChordsSection
    tabs?: TabEntry[]
    todos?: TodoItem[]
    revs?: { lyrics?: number; chords?: number; tablature?: number }
  }) {
    if (values) {
      if (values.lyrics !== undefined) baselines.value.lyrics = cloneDeep(values.lyrics)
      if (values.chords !== undefined) baselines.value.chords = cloneDeep(values.chords)
      if (values.tabs !== undefined) baselines.value.tablature = cloneDeep(values.tabs)
      if (values.todos !== undefined) baselines.value.todos = cloneDeep(values.todos)
      if (values.revs) {
        if (values.revs.lyrics !== undefined) revisions.value.lyrics = values.revs.lyrics
        if (values.revs.chords !== undefined) revisions.value.chords = values.revs.chords
        if (values.revs.tablature !== undefined) revisions.value.tablature = values.revs.tablature
      }
    } else {
      baselines.value.lyrics = cloneDeep(options.lyrics())
      baselines.value.chords = cloneDeep(options.chords())
      baselines.value.tablature = cloneDeep(options.tabs())
      baselines.value.todos = cloneDeep(options.todos())
      const revs = options.initialRevs?.()
      if (revs) {
        revisions.value.lyrics = revs.lyrics ?? 0
        revisions.value.chords = revs.chords ?? 0
        revisions.value.tablature = revs.tablature ?? 0
      }
    }
  }

  function isDirty(section: SectionKey): boolean {
    if (section === 'lyrics') {
      return options.lyrics() !== baselines.value.lyrics
    }
    if (section === 'chords') {
      return JSON.stringify(options.chords()) !== JSON.stringify(baselines.value.chords)
    }
    if (section === 'tablature') {
      return JSON.stringify(options.tabs()) !== JSON.stringify(baselines.value.tablature)
    }
    if (section === 'todos') {
      return JSON.stringify(options.todos()) !== JSON.stringify(baselines.value.todos)
    }
    return false
  }

  async function save(): Promise<void> {
    const id = options.compositionId()
    if (!id || isSaving.value) return

    const dirtySections: SectionKey[] = []
    if (isDirty('lyrics')) dirtySections.push('lyrics')
    if (isDirty('chords')) dirtySections.push('chords')
    if (isDirty('tablature')) dirtySections.push('tablature')
    if (isDirty('todos')) dirtySections.push('todos')

    if (dirtySections.length === 0) {
      saveStateText.value = 'guardado'
      return
    }

    isSaving.value = true
    saveStateText.value = 'guardando...'

    const currentLyrics = options.lyrics()
    const currentChords = cloneDeep(options.chords())
    const currentTabs = cloneDeep(options.tabs())
    const currentTodos = cloneDeep(options.todos())

    const savePromises = dirtySections.map((section) => {
      if (section === 'lyrics') {
        return updateLyricsSection(id, { content: currentLyrics }, revisions.value.lyrics)
      }
      if (section === 'chords') {
        return updateChordsSection(id, currentChords, revisions.value.chords)
      }
      if (section === 'tablature') {
        return updateTablatureSection(id, { tabs: currentTabs }, revisions.value.tablature)
      }
      return updateTodosSection(id, currentTodos)
    })

    const results = await Promise.allSettled(savePromises)

    let hasError = false

    results.forEach((res, index) => {
      const section = dirtySections[index]
      if (res.status === 'fulfilled') {
        if (section === 'lyrics') {
          baselines.value.lyrics = currentLyrics
          revisions.value.lyrics = (res.value as { rev: number }).rev
        } else if (section === 'chords') {
          baselines.value.chords = currentChords
          revisions.value.chords = (res.value as { rev: number }).rev
        } else if (section === 'tablature') {
          baselines.value.tablature = currentTabs
          revisions.value.tablature = (res.value as { rev: number }).rev
        } else if (section === 'todos') {
          baselines.value.todos = currentTodos
        }
      } else {
        hasError = true
        const reason = res.reason
        if (reason?.status === 409 || reason?.code === 'section_conflict') {
          const body = reason.body || reason
          const conflict: SectionConflict = {
            section: (body.section || section) as VersionedSectionKey,
            current_rev: body.current_rev ?? 0,
            content: body.content,
            author: body.author ?? null,
            updated_at: body.updated_at,
          }
          const alreadyQueued = conflicts.value.some((c) => c.section === conflict.section)
          if (!alreadyQueued) {
            conflicts.value.push(conflict)
          }
        }
      }
    })

    if (hasError) {
      saveStateText.value = 'error al guardar'
    } else {
      saveStateText.value = 'guardado'
    }

    isSaving.value = false
  }

  async function resolveOverwrite(conflict: SectionConflict): Promise<void> {
    const id = options.compositionId()
    if (!id) return

    isSaving.value = true
    saveStateText.value = 'guardando...'

    try {
      if (conflict.section === 'lyrics') {
        const content = options.lyrics()
        const res = await updateLyricsSection(id, { content }, conflict.current_rev)
        revisions.value.lyrics = res.rev
        baselines.value.lyrics = content
      } else if (conflict.section === 'chords') {
        const chordsData = cloneDeep(options.chords())
        const res = await updateChordsSection(id, chordsData, conflict.current_rev)
        revisions.value.chords = res.rev
        baselines.value.chords = chordsData
      } else if (conflict.section === 'tablature') {
        const tabsData = cloneDeep(options.tabs())
        const res = await updateTablatureSection(id, { tabs: tabsData }, conflict.current_rev)
        revisions.value.tablature = res.rev
        baselines.value.tablature = tabsData
      }

      conflicts.value = conflicts.value.filter((c) => c.section !== conflict.section)
      if (conflicts.value.length === 0) {
        saveStateText.value = 'guardado'
      }
    } catch {
      saveStateText.value = 'error al guardar'
    } finally {
      isSaving.value = false
    }
  }

  function resolveLoadSaved(conflict: SectionConflict): void {
    if (options.onLoadSection) {
      options.onLoadSection(conflict.section, conflict.content)
    }

    if (conflict.section === 'lyrics') {
      const serverLyrics = typeof conflict.content === 'string'
        ? conflict.content
        : conflict.content?.content ?? ''
      baselines.value.lyrics = serverLyrics
      revisions.value.lyrics = conflict.current_rev
    } else if (conflict.section === 'chords') {
      baselines.value.chords = cloneDeep(conflict.content || { instrument: 'guitar', entries: [] })
      revisions.value.chords = conflict.current_rev
    } else if (conflict.section === 'tablature') {
      const tabs = conflict.content?.tabs || []
      baselines.value.tablature = cloneDeep(tabs)
      revisions.value.tablature = conflict.current_rev
    }

    conflicts.value = conflicts.value.filter((c) => c.section !== conflict.section)
    if (conflicts.value.length === 0) {
      saveStateText.value = 'guardado'
    }
  }

  function dismissConflict(): void {
    if (conflicts.value.length > 0) {
      conflicts.value.shift()
    }
  }

  return {
    revisions,
    isDirty,
    save,
    resetBaselines,
    conflicts,
    activeConflict,
    resolveOverwrite,
    resolveLoadSaved,
    dismissConflict,
    isSaving,
    saveStateText,
  }
}
