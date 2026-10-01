import { apiClient } from './client'
import type { DemoTake } from './demos'

export interface CompositionSection {
  type: 'chords' | 'tab' | 'lyrics' | 'todos'
  content: any
}

export interface CompositionResponse {
  id: string
  title: string
  slug: string
  owner_id: string
  is_public: boolean
  sections: Record<string, any>
  demos?: DemoTake[]
  created_at: string
  updated_at: string
  user_role?: 'owner' | 'editor' | 'viewer' | null
}

export interface CreateCompositionPayload {
  title: string
  is_public?: boolean
}

export async function listCompositions(): Promise<CompositionResponse[]> {
  const res = await apiClient('/compositions')
  if (!res.ok) {
    throw new Error('Error al listar composiciones')
  }
  return res.json()
}

export async function getComposition(id: string): Promise<CompositionResponse> {
  const res = await apiClient(`/compositions/${id}`)
  if (!res.ok) {
    throw new Error('Composición no encontrada')
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
  data: CreateCompositionPayload
): Promise<CompositionResponse> {
  const res = await apiClient('/compositions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al crear composición')
  }
  return res.json()
}

export async function updateSection(
  compositionId: string,
  sectionType: string,
  content: any
): Promise<CompositionResponse> {
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
