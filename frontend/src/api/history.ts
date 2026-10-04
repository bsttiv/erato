import { apiClient } from '@/api/client'
import { HttpError } from '@/api/compositions'
import type { VersionedSectionKey } from '@/features/compositions/useSectionSave'

export interface HistoryAuthor {
  id: string
  display_name?: string | null
}

export interface HistoryItemSummary {
  rev: number
  author?: HistoryAuthor | null
  created_at: string
}

export interface HistoryListResponse {
  items: HistoryItemSummary[]
  next_before_rev?: number | null
}

export interface HistoryDetailResponse {
  rev: number
  content: any
  author?: HistoryAuthor | null
  created_at: string
}

export async function listSectionHistory(
  compositionId: string,
  section: VersionedSectionKey,
  limit = 20,
  beforeRev?: number
): Promise<HistoryListResponse> {
  let url = `/compositions/${compositionId}/history/${section}?limit=${limit}`
  if (beforeRev !== undefined) {
    url += `&before_rev=${beforeRev}`
  }

  const res = await apiClient(url)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new HttpError(
      body.detail || body.message || 'Error al listar historial',
      res.status,
      body.error,
      body
    )
  }
  return res.json()
}

export async function getHistoryRevision(
  compositionId: string,
  section: VersionedSectionKey,
  rev: number
): Promise<HistoryDetailResponse> {
  const res = await apiClient(`/compositions/${compositionId}/history/${section}/${rev}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new HttpError(
      body.detail || body.message || 'Error al obtener revisión',
      res.status,
      body.error,
      body
    )
  }
  return res.json()
}

export async function restoreSectionHistory(
  compositionId: string,
  section: VersionedSectionKey,
  rev: number,
  expectedRev: number
): Promise<any> {
  const res = await apiClient(
    `/compositions/${compositionId}/history/${section}/${rev}/restore?expected_rev=${expectedRev}`,
    {
      method: 'POST',
    }
  )
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new HttpError(
      body.detail || body.message || 'Error al restaurar versión',
      res.status,
      body.error,
      body
    )
  }
  return res.json()
}
