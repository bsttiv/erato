import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  apiClient,
  setAccessToken,
  getAccessToken,
  setOnAuthFailure,
} from '@/api/client'

describe('API client', () => {
  beforeEach(() => {
    setAccessToken(null)
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.clear()
    }
    if (typeof window !== 'undefined' && window.sessionStorage) {
      window.sessionStorage.clear()
    }
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('keeps access token in memory and never writes to localStorage or sessionStorage', () => {
    setAccessToken('test-access-token-123')
    expect(getAccessToken()).toBe('test-access-token-123')
    if (typeof window !== 'undefined' && window.localStorage) {
      expect(window.localStorage.getItem('access_token')).toBeNull()
      expect(window.localStorage.getItem('token')).toBeNull()
    }
    if (typeof window !== 'undefined' && window.sessionStorage) {
      expect(window.sessionStorage.getItem('access_token')).toBeNull()
    }
  })

  it('attaches Authorization Bearer header when token is present', async () => {
    setAccessToken('my-token')
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    await apiClient('/compositions')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url).toContain('/api/compositions')
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBe('Bearer my-token')
  })

  it('attempts exactly one refresh on 401 and replays the original request on success', async () => {
    setAccessToken('expired-token')

    let callCount = 0
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
      callCount++
      const urlStr = url.toString()

      // First call to /compositions -> returns 401
      if (urlStr.includes('/compositions') && callCount === 1) {
        return new Response(JSON.stringify({ detail: 'Token expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // Refresh call -> returns new token
      if (urlStr.includes('/auth/refresh')) {
        return new Response(
          JSON.stringify({ access_token: 'new-valid-token', token_type: 'bearer' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }

      // Replayed call to /compositions -> returns 200
      if (urlStr.includes('/compositions') && callCount === 3) {
        const headers = new Headers(init?.headers)
        expect(headers.get('Authorization')).toBe('Bearer new-valid-token')
        return new Response(JSON.stringify([{ id: 'c1', title: 'Cancion 1' }]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response('Not found', { status: 404 })
    })

    const res = await apiClient('/compositions')
    expect(res.status).toBe(200)
    expect(getAccessToken()).toBe('new-valid-token')
    // 1st request + 1 refresh + 1 replay = 3 fetch calls
    expect(fetchSpy).toHaveBeenCalledTimes(3)
  })

  it('clears token and triggers auth failure callback when refresh fails', async () => {
    setAccessToken('bad-token')
    const authFailureSpy = vi.fn()
    setOnAuthFailure(authFailureSpy)

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      const urlStr = url.toString()
      if (urlStr.includes('/compositions')) {
        return new Response(JSON.stringify({ detail: 'Unauthorized' }), { status: 401 })
      }
      if (urlStr.includes('/auth/refresh')) {
        return new Response(JSON.stringify({ detail: 'Refresh expired' }), { status: 401 })
      }
      return new Response('Not found', { status: 404 })
    })

    const res = await apiClient('/compositions')
    expect(res.status).toBe(401)
    expect(getAccessToken()).toBeNull()
    expect(authFailureSpy).toHaveBeenCalledTimes(1)
  })
})
