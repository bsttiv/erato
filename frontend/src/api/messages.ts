import type { ApiError } from './client'
import { StorageError } from './demos'

export const copy = {
  required: 'Este campo es obligatorio.',
  username: 'Usa de 3 a 30 letras minúsculas, números o guiones, sin guiones al inicio, al final ni seguidos.',
  displayName: 'Debe tener entre 1 y 60 caracteres.',
  password: 'Debe tener entre 8 y 128 caracteres.',
  mismatch: 'Las contraseñas no coinciden.',
  generic: 'No se pudo completar la acción. Inténtalo de nuevo.',
  passwordFailure: 'No se pudo cambiar la contraseña. Inténtalo de nuevo.',
}
export const validUsername = (value: string): boolean => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value) && value.length >= 3 && value.length <= 30
export const validPassword = (value: string): boolean => [...value].length >= 8 && [...value].length <= 128
export function errorMessage(error: ApiError, password = false): string {
  if (!error.status) return 'No hay conexión con el servidor. Inténtalo de nuevo.'
  if (error.code === 'username_taken') return 'Ese nombre de usuario ya está en uso.'
  if (error.code === 'email_taken') return 'Ese correo ya está en uso.'
  if (error.code === 'invalid_credentials') return password ? 'La contraseña actual no es correcta.' : 'El correo o la contraseña no son correctos.'
  if (error.status === 429 && Number.isFinite(error.retryAfter) && error.retryAfter > 0) {
    const minutes = Math.ceil(error.retryAfter / 60)
    return `Demasiados intentos. Espera ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'} e inténtalo de nuevo.`
  }
  return password ? copy.passwordFailure : copy.generic
}

/**
 * Messages for the sharing and demo screens. 401 is handled by the client
 * (refresh, then login); 403 and 404 follow file 06: 404 hides what the caller
 * cannot see, 403 means it is visible but not allowed.
 */
export function accessMessage(error: ApiError): string {
  if (error.code === 'already_member') return 'Ya tienes acceso a este destino.'
  if (error.code === 'owner_must_transfer') return 'El dueño de la banda debe transferirla antes de abandonarla.'
  if (error.status === 403) return 'No tienes permiso para hacer esto.'
  if (error.status === 404) return 'No se encontró o no tienes acceso.'
  if (error.code === 'storage_unavailable') return 'Las demos no están disponibles en este momento.'
  return errorMessage(error)
}

/** Messages for the demo upload: the API's 422 codes plus the direct upload to storage. */
export function uploadMessage(error: unknown): string {
  if (error instanceof StorageError) return 'No se pudo subir el archivo. Revisa tu conexión e inténtalo de nuevo.'
  const api = error as ApiError
  if (api.code === 'quota_exceeded') return 'No hay espacio para más demos: se alcanzó el límite de 2 GB.'
  if (api.status === 422) return 'El archivo no es un audio válido, pesa más de 100 MB o dura más de 20 minutos.'
  return accessMessage(api)
}
