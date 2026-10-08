import { apiClient } from './client'
import type { DemoTake } from './demos'

export type Visibility = 'public' | 'private'
export type CompositionStatus = 'idea' | 'in_progress' | 'ready'
export type UserRole = 'owner' | 'editor' | 'viewer'
export type TabColumn = string[] | '|'

export interface TabEntry {
  id: string
  title: string
  strings: number
  columns: TabColumn[]
}

export interface TablatureSection {
  strings?: number
  content?: string
  tabs: TabEntry[]
}

export interface ChordEntry {
  bar: number
  notes: number[]
  name: string
}

export interface ChordsSection {
  instrument: string
  entries: ChordEntry[]
}

export interface LyricsSection {
  content: string
}

export interface TodoItem {
  id?: string
  text: string
  done: boolean
}

export interface MemberItem {
  user_id: string
  role: 'editor' | 'viewer'
  display_name?: string | null
  initials?: string | null
}

export interface DemoItem {
  demo_id: string
  cloudinary_public_id: string
  title: string
  duration_s: number
  uploaded_by: string
  uploaded_at: string
}

export interface SectionsEnabled {
  chords: boolean
  tablature: boolean
  lyrics: boolean
  demos: boolean
  todos: boolean
}

export interface CompositionCounts {
  chords: number
  tabs: number
  demos: number
  todos_done: number
  todos_total: number
}

export interface CompositionListItem {
  band_id?: string | null
  via_band?: boolean
  id: string
  owner_id: string
  title: string
  visibility: Visibility
  key?: string | null
  bpm?: number | null
  time_signature?: string | null
  style_tags?: string[]
  status?: CompositionStatus
  sections_enabled?: SectionsEnabled
  chord_names?: string[]
  counts?: CompositionCounts
  created_at: string
  updated_at: string
}

export interface CompositionResponse {
  band_id?: string | null
  band_editable?: boolean
  band_active?: boolean | null
  id: string
  owner_id: string
  title: string
  visibility: Visibility
  share_slug?: string | null
  key?: string | null
  bpm?: number | null
  time_signature?: string | null
  style_tags?: string[]
  status?: CompositionStatus
  sections_enabled?: SectionsEnabled
  chords?: ChordsSection | null
  tablature?: TablatureSection | null
  lyrics?: LyricsSection | null
  section_revs?: {
    lyrics?: number
    chords?: number
    tablature?: number
  }
  todos: TodoItem[]
  demos?: (DemoItem | DemoTake)[]
  members: MemberItem[]
  user_role?: UserRole | null
  created_at: string
  updated_at: string
  /** @deprecated Kept for transitional compatibility with pre-refactor views */
  is_public?: boolean
  /** @deprecated Kept for transitional compatibility with pre-refactor views */
  slug?: string
  /** @deprecated Kept for transitional compatibility with pre-refactor views */
  sections?: Record<string, any>
}

export interface CreateCompositionPayload {
  title: string
  visibility?: Visibility
  key?: string | null
  bpm?: number | null
  time_signature?: string | null
  style_tags?: string[]
  status?: CompositionStatus
  sections_enabled?: Partial<SectionsEnabled>
  /** @deprecated Kept for transitional compatibility */
  is_public?: boolean
}

export interface UpdateCompositionPayload {
  title?: string
  visibility?: Visibility
  key?: string | null
  bpm?: number | null
  time_signature?: string | null
  style_tags?: string[]
  status?: CompositionStatus
  sections_enabled?: Partial<SectionsEnabled>
}

export async function listCompositions(): Promise<CompositionListItem[]> {
  const res = await apiClient('/compositions')
  if (!res.ok) {
    throw new Error('Error al listar composiciones')
  }
  return res.json()
}

export interface SectionAuthor {
  id: string
  display_name: string
  avatar_url?: string | null
}

export interface SectionConflictBody {
  error: 'section_conflict'
  message?: string
  detail?: string
  section: 'lyrics' | 'chords' | 'tablature'
  current_rev: number
  content: any
  author?: SectionAuthor | null
  updated_at?: string
}

export interface ChordsWriteResponse extends ChordsSection {
  rev: number
}

export interface TablatureWriteResponse extends TablatureSection {
  rev: number
}

export interface LyricsWriteResponse extends LyricsSection {
  rev: number
}

/** Error carrying the HTTP status, machine-readable code, and parsed body so callers can branch on it. */
export class HttpError<T = any> extends Error {
  status: number
  code?: string
  body?: T

  constructor(message: string, status: number, code?: string, body?: T) {
    super(message)
    this.name = 'HttpError'
    this.status = status
    this.code = code
    this.body = body
  }
}

export async function getComposition(id: string): Promise<CompositionResponse> {
  const res = await apiClient(`/compositions/${id}`)
  if (!res.ok) {
    throw new HttpError('Composición no encontrada', res.status)
  }
  return res.json()
}

export async function getCompositionBySlug(slug: string): Promise<CompositionResponse> {
  const res = await apiClient(`/compositions/by-slug/${slug}`)
  if (!res.ok) {
    throw new Error('Composición no encontrada')
  }
  return res.json()
}

export async function createComposition(
  payload: CreateCompositionPayload
): Promise<CompositionResponse> {
  const body: Record<string, any> = { ...payload }
  if (body.is_public !== undefined && body.visibility === undefined) {
    body.visibility = body.is_public ? 'public' : 'private'
    delete body.is_public
  }

  const res = await apiClient('/compositions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al crear composición')
  }
  return res.json()
}

export async function updateComposition(
  id: string,
  payload: UpdateCompositionPayload
): Promise<CompositionResponse> {
  const res = await apiClient(`/compositions/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al actualizar composición')
  }
  return res.json()
}

export async function updateChordsSection(
  id: string,
  payload: ChordsSection,
  expectedRev?: number
): Promise<ChordsWriteResponse> {
  const query = expectedRev !== undefined ? `?expected_rev=${expectedRev}` : ''
  const res = await apiClient(`/compositions/${id}/chords${query}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new HttpError(
      err.detail || err.message || 'Error al actualizar acordes',
      res.status,
      err.error,
      err
    )
  }
  return res.json()
}

export async function updateTablatureSection(
  id: string,
  payload: TablatureSection,
  expectedRev?: number
): Promise<TablatureWriteResponse> {
  const query = expectedRev !== undefined ? `?expected_rev=${expectedRev}` : ''
  const res = await apiClient(`/compositions/${id}/tablature${query}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new HttpError(
      err.detail || err.message || 'Error al actualizar tablatura',
      res.status,
      err.error,
      err
    )
  }
  return res.json()
}

export async function updateLyricsSection(
  id: string,
  payload: LyricsSection,
  expectedRev?: number
): Promise<LyricsWriteResponse> {
  const query = expectedRev !== undefined ? `?expected_rev=${expectedRev}` : ''
  const res = await apiClient(`/compositions/${id}/lyrics${query}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new HttpError(
      err.detail || err.message || 'Error al actualizar letra',
      res.status,
      err.error,
      err
    )
  }
  return res.json()
}

export async function updateTodosSection(
  id: string,
  payload: TodoItem[]
): Promise<TodoItem[]> {
  const res = await apiClient(`/compositions/${id}/todos`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new HttpError(
      err.detail || err.message || 'Error al actualizar tareas',
      res.status,
      err.error,
      err
    )
  }
  return res.json()
}

// Aliases matching design.md shorthand
export const updateChords = updateChordsSection
export const updateTablature = updateTablatureSection
export const updateLyrics = updateLyricsSection
export const updateTodos = updateTodosSection

/** @deprecated Use dedicated typed section update functions */
export async function updateSection(
  compositionId: string,
  sectionType: string,
  content: any
): Promise<any> {
  const res = await apiClient(`/compositions/${compositionId}/sections/${sectionType}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al actualizar sección')
  }
  return res.json()
}
