import { computed, ref, watch, type Ref } from 'vue'
import { useRoute } from 'vue-router'
import { client, session } from './session'
import type { ConflictItem } from '../api/client'
import { errorMessage } from '../api/messages'
import type { Chord } from '../lib/chords'
import type { LyricsLine } from '../lib/lyrics'
import type { Demo } from '../api/demos'

export interface SongLyrics { lines: LyricsLine[] }
export interface SongTask { id?: string; title?: string; text?: string; done: boolean }
export interface SongTab { id?: string; title?: string; tuning?: string[]; columns: string[][] }
/** Server-owned chord: the identity-carrying fields are always present. */
export interface SongChord {
  id?: string
  name: string
  instrument: 'guitar' | 'piano'
  notes: number[]
  frets?: number[] | null
  strings?: number[] | null
}

/** Shape of the sections PUT response that views consume after saveSections. */
export interface SectionSaveResult {
  song: Song
  saved?: { section: string; version: number }[]
  conflicts?: ConflictItem[]
  key_reset?: boolean
}

/** One entry of a song-section history, as rendered by HistoryList. */
export interface RevisionItem {
  section?: string
  version?: number
  author?: { display_name?: string; username?: string } | null
  summary?: string | null
  who?: string
  what?: string
  when?: string
  created_at?: string
}
/** A single revision read back from the history endpoint. */
export interface RevisionSnapshot {
  version: number
  content: unknown
}

export interface Song {
  id?: string
  title?: string
  key?: string | null
  key_mode?: string
  key_candidates?: string[]
  tempo?: number | null
  time_signature?: string | null
  status?: string | null
  visibility?: string | null
  owner_type?: string | null
  share_slug?: string | null
  permissions?: { edit?: boolean; manage?: boolean }
  section_versions?: Record<string, number | undefined>
  lyrics?: SongLyrics | null
  chords?: SongChord[]
  tablatures?: SongTab[]
  tasks?: SongTask[]
  demos?: Demo[]
}

const song = ref<Song | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const conflicts = ref<ConflictItem[]>([])
const notice = ref('')
const isPublic = ref(true)
const rights = ref({ edit: false, manage: false })
let activeSlug: string | undefined
let generation = 0
// True while a load restores the session itself: that token change is not a login.
let restoring = false
// Logout or login invalidates what was loaded under the previous identity, even
// if the next visitor (or the same one, signed in) opens the same URL.
watch(() => session.accessToken, (token, previous) => {
  if (restoring) return
  if (!!previous !== !!token) {
    generation++
    activeSlug = undefined
    song.value = null
    rights.value = { edit: false, manage: false }
    isPublic.value = true
    conflicts.value = []
    notice.value = ''
    error.value = ''
    loading.value = false
    saving.value = false
  }
}, { flush: 'sync' })

export function songPath(value: { id?: string | null; share_slug?: string | null }): string {
  return value.id ? `/canciones/${encodeURIComponent(value.id)}` : `/c/${encodeURIComponent(String(value.share_slug))}`
}

export function useSong() {
  const route = useRoute()
  async function load(): Promise<void> {
    const slug = String(route.params.id || route.params.slug || '')
    const requestGeneration = ++generation
    activeSlug = slug
    loading.value = true
    saving.value = false
    song.value = null
    error.value = ''
    conflicts.value = []
    notice.value = ''
    rights.value = { edit: false, manage: false }
    isPublic.value = true
    try {
      // Internal IDs are used only for authenticated own access; public slugs
      // remain anonymous even when a different account happens to be signed in.
      let result: Song | undefined
      let access = { edit: false, manage: false }
      let publicRead = true
      let authenticated = false
      restoring = true
      try { authenticated = await session.restore() } catch { /* Public reads still work. */ } finally { restoring = false }
      if (authenticated && /^[a-f\d]{24}$/i.test(slug)) {
        try {
          result = await client.request<Song>(`/songs/${encodeURIComponent(slug)}`)
          publicRead = false
          const rows: { id?: string; origin?: string }[] = await client.request('/songs?workspace=all')
          const own = rows.find((row) => row?.id === result?.id)
          access = {
            edit: own?.origin === 'own' || own?.origin === 'band',
            manage: own?.origin === 'own',
          }
          if (own?.origin === 'shared') {
            // Use the documented public username membership projection, never
            // token claims or a write request, to distinguish editor and reader.
            try {
              const [me, members] = await Promise.all([
                client.request<{ username: string }>('/me'),
                client.request<{ username: string; role: string }[]>(`/songs/${encodeURIComponent(String(result.id))}/members`),
              ])
              access.edit = members.some((member) => member.username === me.username && member.role === 'editor')
            } catch { /* Older backends may not expose memberships: fail closed. */ }
          }
        } catch (failure) {
          if (![401, 404].includes(failure.status)) throw failure
        }
      }
      if (!result) result = await client.request<Song>(`/c/${encodeURIComponent(slug)}`, { authenticated: false })
      if (requestGeneration !== generation) return
      song.value = result
      isPublic.value = publicRead
      rights.value = access
    } catch (failure) {
      if (requestGeneration === generation) error.value = failure.status === 404 ? 'No se encontró la composición o no tienes acceso.' : errorMessage(failure)
    } finally {
      if (requestGeneration === generation) loading.value = false
    }
  }
  watch(() => route.params.id || route.params.slug, (slug) => {
    if (String(slug || '') !== activeSlug) load()
  }, { immediate: true })
  // Signing in while this screen is open must reload under the new identity.
  watch(() => session.accessToken, (token, previous) => {
    const slug = String(route.params.id || route.params.slug || '')
    if (token && !previous && !restoring && slug && slug !== activeSlug) load()
  }, { flush: 'sync' })
  async function saveSections(sections: Record<string, any>): Promise<SectionSaveResult | null> {
    if (!rights.value.edit || saving.value || !song.value?.id) return null
    saving.value = true
    error.value = ''
    conflicts.value = []
    notice.value = ''
    const requestGeneration = generation
    const body = {
      sections,
      base_versions: Object.fromEntries(Object.keys(sections).map((section) => [section, song.value!.section_versions?.[section]])),
    }
    if (sections.chords) body.sections = { ...sections, chords: sections.chords.map(({ id, instrument, notes, frets, strings }: any) => ({ ...(id ? { id } : {}), instrument, notes, frets, strings })) }
    try {
      const result: SectionSaveResult = await client.request(`/songs/${encodeURIComponent(song.value!.id)}/sections`, { method: 'PUT', body })
      if (requestGeneration !== generation) return null
      conflicts.value = result.conflicts || []
      // Keep stale bases for conflicted drafts: retrying must not silently
      // overwrite the other author's changes with an automatically rebased draft.
      const next = result.song
      for (const conflict of conflicts.value) next.section_versions![conflict.section] = song.value!.section_versions?.[conflict.section]
      song.value = next
      if (result.key_reset) notice.value = 'La tonalidad cambió porque la selección anterior ya no está entre las candidatas.'
      return result
    } catch (failure) {
      if (requestGeneration !== generation) return null
      conflicts.value = failure.conflicts || []
      error.value = failure.status === 409 ? 'Hay secciones desactualizadas. Conserva tus cambios y vuelve a cargar antes de combinarlos.' : errorMessage(failure)
      return null
    } finally { if (requestGeneration === generation) saving.value = false }
  }
  return { song: song as Ref<Song | null>, loading, saving, error, conflicts, notice, isPublic, load, saveSections,
    canEdit: computed(() => !isPublic.value && rights.value.edit === true),
    canManage: computed(() => !isPublic.value && rights.value.manage === true) }
}
