export interface ConflictItem {
  section: string
  current_version?: number
}

/** Body of a failed response, narrow enough for the fields the UI reads. */
interface ErrorBody {
  detail?: string
  code?: string
  conflicts?: ConflictItem[]
}

export class ApiError extends Error {
  status: number
  code?: string
  detail?: string
  conflicts: ConflictItem[]
  retryAfter: number

  constructor(status: number, body: ErrorBody = {}, retryAfter = NaN) {
    super(body.detail || 'Request failed')
    this.status = status
    this.code = body.code
    this.detail = body.detail
    this.conflicts = body.conflicts || []
    this.retryAfter = retryAfter
  }
}

/** Session surface client.ts needs; the real session store satisfies it. */
export interface ClientSession {
  accessToken: string | null
  deviceId(): string
  setTokens(tokens: { access_token: string }): void
  clear(): void
}

export interface RequestOptions {
  method?: string
  body?: unknown
  authenticated?: boolean
  retry?: boolean
}

export interface ApiClient {
  request<T = any>(path: string, options?: RequestOptions): Promise<T>
  refresh(): Promise<unknown>
}

// Maestro treats two refreshes that overlap as a stolen token and ends the session.
function acrossTabs<T>(action: () => Promise<T>): Promise<T> {
  const locks = globalThis.navigator?.locks
  return locks ? locks.request('erato-refresh', action) as Promise<T> : action()
}

export function createClient(session: ClientSession, fetcher: typeof fetch = (...args) => fetch(...args)): ApiClient {
  let refreshing: Promise<unknown> | undefined
  async function request<T = any>(path: string, { method = 'GET', body, authenticated = true, retry = true }: RequestOptions = {} as RequestOptions): Promise<T> {
    const requestToken = session.accessToken
    const headers: Record<string, string> = { 'X-Device-Id': session.deviceId() }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (authenticated && requestToken) headers.Authorization = `Bearer ${requestToken}`
    const response = await fetcher(`/api${path}`, {
      method, headers, credentials: 'same-origin', ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
    const data = response.status === 204 ? undefined : await response.json().catch(() => ({}))
    if (response.ok) return data
    // Incorrect current passwords are field errors, not expired sessions.
    if (response.status === 401 && data.code === 'not_authenticated' && authenticated && retry) {
      // A delayed 401 may belong to the token another request already rotated.
      if (session.accessToken === requestToken) await refresh()
      return request(path, { method, body, authenticated, retry: false })
    }
    if (response.status === 401 && data.code === 'not_authenticated' && authenticated) session.clear()
    const rawRetry = response.headers.get('Retry-After')
    const seconds = rawRetry && /^\d+(\.\d+)?$/.test(rawRetry.trim()) ? Number(rawRetry) : NaN
    throw new ApiError(response.status, data, seconds > 0 ? seconds : NaN)
  }
  async function refresh(): Promise<unknown> {
    if (!refreshing) {
      refreshing = acrossTabs(() => request('/auth/refresh', {
        method: 'POST', authenticated: false,
      })).then((tokens) => session.setTokens(tokens as { access_token: string })).catch((error) => {
        if (error.status === 401) session.clear()
        throw error
      }).finally(() => { refreshing = undefined })
    }
    return refreshing
  }
  return { request, refresh }
}
