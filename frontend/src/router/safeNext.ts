/**
 * Returns a post-login redirect target only when it is an internal path.
 * Anything else (external URLs, protocol-relative, backslashes) falls back to '/'.
 */
export function safeNextPath(raw: unknown): string {
  if (typeof raw !== 'string' || raw.length === 0) return '/'
  if (!raw.startsWith('/')) return '/'
  if (raw.startsWith('//') || raw.includes('\\')) return '/'
  return raw
}
