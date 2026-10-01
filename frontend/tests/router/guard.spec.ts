import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { routes, setupNavigationGuard } from '@/router'
import {
  isAuthReady,
  setAuthenticated,
  resetAuthReadyForTesting,
} from '@/router/authReady'
import { setAccessToken } from '@/api/client'

describe('Router navigation guard and authReady contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    setAccessToken(null)
    resetAuthReadyForTesting()
  })

  function createTestRouter() {
    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    })
    setupNavigationGuard(router)
    return router
  }

  it('navigating to /login or /register when unauthenticated succeeds', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'No refresh token' }), { status: 401 })
    )

    const router = createTestRouter()
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/login')

    await router.push('/register')
    expect(router.currentRoute.value.path).toBe('/register')
  })

  it('navigating to / or /compositions/:id when unauthenticated redirects to /login', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'No refresh token' }), { status: 401 })
    )

    const router = createTestRouter()
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.next).toBe('/')

    await router.push('/compositions/comp-123')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.next).toBe('/compositions/comp-123')
  })

  it('navigating to /c/:ref when unauthenticated succeeds without redirecting', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'No refresh token' }), { status: 401 })
    )

    const router = createTestRouter()
    await router.push('/c/public-song-slug')
    expect(router.currentRoute.value.path).toBe('/c/public-song-slug')
  })

  it('navigating to /login when already authenticated redirects to /', async () => {
    setAccessToken('valid-jwt-token')
    setAuthenticated(true)
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ access_token: 'valid-jwt-token' }), { status: 200 })
    )

    const router = createTestRouter()
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('route navigation awaits authReady before evaluating the guard', async () => {
    let resolveRefresh: (res: Response) => void
    const refreshPromise = new Promise<Response>((resolve) => {
      resolveRefresh = resolve
    })

    vi.spyOn(globalThis, 'fetch').mockReturnValueOnce(refreshPromise)

    const router = createTestRouter()
    expect(isAuthReady()).toBe(false)

    const navigationPromise = router.push('/')
    // While refresh is pending, authReady is not resolved and navigation is blocked
    expect(isAuthReady()).toBe(false)

    // Resolve refresh with success
    resolveRefresh!(
      new Response(JSON.stringify({ access_token: 'refreshed-token' }), { status: 200 })
    )

    await navigationPromise
    expect(isAuthReady()).toBe(true)
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('public composition route exposes the ref param', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'No refresh token' }), { status: 401 })
    )
    const router = createTestRouter()
    await router.push('/c/64b7f0c2a1b2c3d4e5f60718')
    const current = router.currentRoute.value
    expect(current.name).toBe('composition-public')
    expect(current.params.ref).toBe('64b7f0c2a1b2c3d4e5f60718')
  })
})
