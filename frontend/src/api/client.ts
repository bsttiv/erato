let inMemoryAccessToken: string | null = null
let onAuthFailureCallback: (() => void) | null = null
let refreshPromise: Promise<string | null> | null = null

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken
}

export function setOnAuthFailure(cb: () => void): void {
  onAuthFailureCallback = cb
}

async function executeRefresh(): Promise<string | null> {
  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!res.ok) {
      setAccessToken(null)
      if (onAuthFailureCallback) {
        onAuthFailureCallback()
      }
      return null
    }
    const data = await res.json()
    if (data && data.access_token) {
      setAccessToken(data.access_token)
      return data.access_token
    }
    setAccessToken(null)
    return null
  } catch {
    setAccessToken(null)
    if (onAuthFailureCallback) {
      onAuthFailureCallback()
    }
    return null
  } finally {
    refreshPromise = null
  }
}

export async function apiClient(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = path.startsWith('/api') ? path : `/api${path.startsWith('/') ? '' : '/'}${path}`

  const headers = new Headers(options.headers || {})
  if (inMemoryAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${inMemoryAccessToken}`)
  }

  const reqOptions: RequestInit = {
    ...options,
    headers,
    credentials: options.credentials || 'same-origin',
  }

  let response = await fetch(url, reqOptions)

  // If 401 and not calling auth endpoints directly, attempt transparent token refresh once
  if (response.status === 401 && !path.includes('/auth/login') && !path.includes('/auth/refresh')) {
    if (!refreshPromise) {
      refreshPromise = executeRefresh()
    }
    const newToken = await refreshPromise

    if (newToken) {
      // Replay original request with new token
      const retryHeaders = new Headers(options.headers || {})
      retryHeaders.set('Authorization', `Bearer ${newToken}`)
      response = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: options.credentials || 'same-origin',
      })
    }
  }

  return response
}
