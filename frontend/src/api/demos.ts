import { apiClient } from './client'

export interface UploadSignatureResponse {
  signature: string
  timestamp: number
  folder: string
  api_key: string
  cloud_name: string
  resource_type: string
  type: string
  tags: string
}

export interface ConfirmUploadPayload {
  public_id: string
  version: number
  signature: string
  resource_type: string
  duration?: number
  format?: string
  bytes?: number
  title?: string
}

export interface DemoComment {
  id?: string
  t: number
  author: string
  text: string
  created_at?: string
}

export interface DemoTake {
  id: string
  title: string
  public_id: string
  duration: number
  date?: string
  note?: string
  src?: string
  comments?: DemoComment[]
}

export async function requestUploadSignature(
  compositionId: string
): Promise<UploadSignatureResponse> {
  const res = await apiClient(`/compositions/${compositionId}/demos/upload-signature`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al obtener firma de subida')
  }
  return res.json()
}

export async function confirmUpload(
  compositionId: string,
  payload: ConfirmUploadPayload
): Promise<DemoTake> {
  const res = await apiClient(`/compositions/${compositionId}/demos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al confirmar demo')
  }
  return res.json()
}

export async function getPlaybackUrl(
  compositionId: string,
  demoId: string
): Promise<{ url: string; expires_at: number }> {
  const res = await apiClient(`/compositions/${compositionId}/demos/${demoId}/url`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al obtener enlace de reproducción')
  }
  return res.json()
}

export async function addComment(
  compositionId: string,
  demoId: string,
  text: string,
  t: number
): Promise<DemoComment> {
  const res = await apiClient(`/compositions/${compositionId}/demos/${demoId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, t }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al agregar comentario')
  }
  return res.json()
}

export async function listComments(
  compositionId: string,
  demoId: string
): Promise<DemoComment[]> {
  const res = await apiClient(`/compositions/${compositionId}/demos/${demoId}/comments`)
  if (!res.ok) {
    throw new Error('Error al listar comentarios')
  }
  return res.json()
}
