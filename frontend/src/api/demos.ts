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

/** Modal-facing shape (Cloudinary upload response + title); mapped to the backend body. */
export interface ConfirmUploadPayload {
  public_id: string
  version: number | string
  signature: string
  title: string
  /** Seconds, as reported by Cloudinary; may be missing for some files. */
  duration?: number
}

interface DemoResponse {
  demo_id: string
  cloudinary_public_id: string
  title: string
  duration_s: number
  uploaded_by: string
  uploaded_at: string
}

interface CommentResponse {
  id: string
  composition_id: string
  demo_id: string
  author_id: string
  timestamp_s: number
  text: string
  created_at: string
}

function toDemoTake(d: DemoResponse): DemoTake {
  return {
    id: d.demo_id,
    title: d.title,
    public_id: d.cloudinary_public_id,
    duration: d.duration_s,
    date: d.uploaded_at,
  }
}

function toDemoComment(c: CommentResponse): DemoComment {
  return {
    id: c.id,
    t: c.timestamp_s,
    author: c.author_id,
    text: c.text,
    created_at: c.created_at,
  }
}

/** Backend envelope is `{error, message, detail, details}`; always yield a string. */
async function errorMessage(res: Response, fallback: string): Promise<string> {
  const err = await res.json().catch(() => ({}))
  if (typeof err?.detail === 'string' && err.detail) return err.detail
  if (typeof err?.message === 'string' && err.message) return err.message
  return fallback
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
    throw new Error(await errorMessage(res, 'Error al obtener firma de subida'))
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
    body: JSON.stringify({
      public_id: payload.public_id,
      version: String(payload.version),
      signature: payload.signature,
      title: payload.title,
      duration_s: payload.duration ?? 0,
    }),
  })
  if (!res.ok) {
    throw new Error(await errorMessage(res, 'Error al confirmar demo'))
  }
  return toDemoTake(await res.json())
}

export async function getPlaybackUrl(
  compositionId: string,
  demoId: string
): Promise<{ url: string; expires_at: number }> {
  const res = await apiClient(`/compositions/${compositionId}/demos/${demoId}/url`)
  if (!res.ok) {
    throw new Error(await errorMessage(res, 'Error al obtener enlace de reproducción'))
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
    body: JSON.stringify({ text, timestamp_s: t }),
  })
  if (!res.ok) {
    throw new Error(await errorMessage(res, 'Error al agregar comentario'))
  }
  return toDemoComment(await res.json())
}

export async function listComments(
  compositionId: string,
  demoId: string
): Promise<DemoComment[]> {
  const res = await apiClient(`/compositions/${compositionId}/demos/${demoId}/comments`)
  if (!res.ok) {
    throw new Error(await errorMessage(res, 'Error al listar comentarios'))
  }
  const list: CommentResponse[] = await res.json()
  return list.map(toDemoComment)
}
