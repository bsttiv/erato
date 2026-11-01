import { afterEach, describe, expect, it, vi } from 'vitest'
import { createClient, type ClientSession } from './client'

function fakeSession(): ClientSession {
  return {
    accessToken: 'token',
    deviceId: () => 'device',
    setTokens: vi.fn(),
    clear: vi.fn(),
  } as unknown as ClientSession
}

function fakeLocks() {
  let tail: Promise<unknown> = Promise.resolve()
  return {
    request(_name: string, action: () => Promise<unknown>) {
      const run = tail.then(action)
      tail = run.catch(() => undefined)
      return run
    },
  }
}

function fetcher(events: string[]) {
  let count = 0
  return vi.fn(async () => {
    const call = ++count
    events.push(`start ${call}`)
    await new Promise((resolve) => setTimeout(resolve, 5))
    events.push(`end ${call}`)
    return new Response(JSON.stringify({ access_token: `new-${call}` }), { status: 200 })
  }) as unknown as typeof fetch
}

describe('refresh across tabs', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('MAE-044 serializes refreshes of two clients of the same browser', async () => {
    vi.stubGlobal('navigator', { locks: fakeLocks() })
    const events: string[] = []
    const send = fetcher(events)
    const first = fakeSession()
    const second = fakeSession()
    await Promise.all([createClient(first, send).refresh(), createClient(second, send).refresh()])
    expect(events).toEqual(['start 1', 'end 1', 'start 2', 'end 2'])
    expect(first.setTokens).toHaveBeenCalledWith({ access_token: 'new-1' })
    expect(second.setTokens).toHaveBeenCalledWith({ access_token: 'new-2' })
  })

  it('MAE-045 refreshes without a lock when the browser has none', async () => {
    vi.stubGlobal('navigator', {})
    const session = fakeSession()
    await createClient(session, fetcher([])).refresh()
    expect(session.setTokens).toHaveBeenCalledWith({ access_token: 'new-1' })
  })
})
