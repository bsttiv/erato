import {
  getComposition,
  getCompositionBySlug,
  HttpError,
  type CompositionResponse,
} from '@/api/compositions'

const OBJECT_ID_PATTERN = /^[0-9a-f]{24}$/i

export function isObjectIdRef(ref: string): boolean {
  return OBJECT_ID_PATTERN.test(ref)
}

/**
 * Resolves a `/c/:ref` reference. A 24-char hex ref is tried as an id first and
 * falls back to the share slug only on a 404; any other ref is a slug.
 */
export async function resolveCompositionRef(ref: string): Promise<CompositionResponse> {
  if (!isObjectIdRef(ref)) {
    return getCompositionBySlug(ref)
  }
  try {
    return await getComposition(ref)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404) {
      return getCompositionBySlug(ref)
    }
    throw err
  }
}
