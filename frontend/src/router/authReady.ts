import { setAccessToken, getAccessToken } from '@/api/client'

let authReadyPromise: Promise<boolean> | null = null
let authReadyResolved = false
let authenticated = false

export function isAuthReady(): boolean {
  return authReadyResolved
}

export function isAuthenticated(): boolean {
  return !!getAccessToken() || authenticated
}

export function setAuthenticated(val: boolean): void {
  authenticated = val
}

export function ensureAuthReady(): Promise<boolean> {
  if (authReadyResolved && authReadyPromise) {
    return authReadyPromise
  }

  if (!authReadyPromise) {
    authReadyPromise = (async () => {
      try {
        const res = await fetch('/api/auth/refresh', {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (res.ok) {
          const data = await res.json()
          if (data && data.access_token) {
            setAccessToken(data.access_token)
            authenticated = true
            authReadyResolved = true
            return true
          }
        }
      } catch {
        // Network or fetch failure -> unauthenticated
      }

      setAccessToken(null)
      authenticated = false
      authReadyResolved = true
      return false
    })()
  }

  return authReadyPromise
}

export function resetAuthReadyForTesting(): void {
  authReadyPromise = null
  authReadyResolved = false
  authenticated = false
}
