import { client } from '../stores/session'

/** Author projection of a comment: only the public fields. */
export interface CommentAuthor { username: string; display_name: string }
export interface DemoComment {
  id: string
  demo_id: string
  timestamp_s: number
  text: string
  created_at: string
  updated_at: string
  author: CommentAuthor | null
}
/** A demo as embedded in the song. Public reads omit `uploaded_by`; they add `author`. */
export interface Demo {
  id: string
  title: string
  duration_s: number
  mime_type?: string
  size_bytes?: number
  uploaded_at?: string
  author?: CommentAuthor | null
}
export interface SignedUrl { url: string; expires_in: number }
export interface UploadTarget { upload_url: string; fields: Record<string, string | number> }

/** Client-side convenience only; the server enforces the real limit. */
export const MAX_DEMO_BYTES = 100 * 1024 ** 2

/** Thrown when the direct upload to storage fails; `status` is 0 for a network or CORS failure. */
export class StorageError extends Error {
  constructor(public status: number) { super('Storage upload failed') }
}

/** POST the file straight to storage with its signed fields, reporting progress as a 0..1 fraction. */
export function uploadToStorage(target: UploadTarget, file: File, onProgress: (fraction: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    Object.entries(target.fields).forEach(([name, value]) => form.append(name, String(value)))
    form.append('file', file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', target.upload_url)
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(e.loaded / e.total) }
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new StorageError(xhr.status)))
    xhr.onerror = () => reject(new StorageError(0))
    xhr.send(form)
  })
}

const id = encodeURIComponent

/**
 * Demo endpoints. Signed-in screens address the song by id; the public link
 * addresses it by slug and can only read (the server has no writes under /c/).
 */
export function demosApi(base: { songId?: string; slug?: string }) {
  const isPublic = !base.songId
  const root = isPublic ? `/c/${id(String(base.slug))}` : `/songs/${id(String(base.songId))}`
  const options = isPublic ? { authenticated: false } : {}
  return {
    playbackUrl: (demoId: string) => client.request<SignedUrl>(`${root}/demos/${id(demoId)}/url`, options),
    comments: (demoId: string) => client.request<DemoComment[]>(`${root}/demos/${id(demoId)}/comments`, options),
    uploadUrl: () => client.request<UploadTarget>(`${root}/demos/upload-url`, { method: 'POST' }),
    confirm: (publicId: string, title?: string) =>
      client.request<Demo>(`${root}/demos`, { method: 'POST', body: title ? { public_id: publicId, title } : { public_id: publicId } }),
    rename: (demoId: string, title: string) => client.request<Demo>(`${root}/demos/${id(demoId)}`, { method: 'PATCH', body: { title } }),
    remove: (demoId: string) => client.request(`${root}/demos/${id(demoId)}`, { method: 'DELETE' }),
    addComment: (demoId: string, timestamp_s: number, text: string) =>
      client.request<DemoComment>(`${root}/demos/${id(demoId)}/comments`, { method: 'POST', body: { timestamp_s, text } }),
    editComment: (demoId: string, commentId: string, text: string) =>
      client.request<DemoComment>(`${root}/demos/${id(demoId)}/comments/${id(commentId)}`, { method: 'PATCH', body: { text } }),
    removeComment: (demoId: string, commentId: string) =>
      client.request(`${root}/demos/${id(demoId)}/comments/${id(commentId)}`, { method: 'DELETE' }),
  }
}
