import { afterEach, describe, expect, it, vi } from 'vitest'
import * as bands from '@/api/bands'
import { HttpError } from '@/api/compositions'

const cases: [string, () => Promise<unknown>, string, string, unknown?][] = [
  ['list', () => bands.listBands(), '/api/bands', 'GET'],
  ['get', () => bands.getBand('b'), '/api/bands/b', 'GET'],
  ['create', () => bands.createBand('Jazz'), '/api/bands', 'POST', { name: 'Jazz' }],
  ['rename', () => bands.renameBand('b', 'Swing'), '/api/bands/b', 'PATCH', { name: 'Swing' }],
  ['create invite', () => bands.createBandInvite('b'), '/api/bands/b/invites', 'POST', {}],
  ['list invites', () => bands.listBandInvites('b'), '/api/bands/b/invites', 'GET'],
  ['delete invite', () => bands.deleteBandInvite('b', 'i'), '/api/bands/b/invites/i', 'DELETE'],
  ['leave', () => bands.leaveBand('b'), '/api/bands/b/leave', 'POST'],
  ['remove', () => bands.removeBandMember('b', 'u'), '/api/bands/b/members/u', 'DELETE'],
  ['request transfer', () => bands.requestBandTransfer('b', 'u'), '/api/bands/b/transfer', 'POST', { to_user_id: 'u' }],
  ['cancel transfer', () => bands.cancelBandTransfer('b'), '/api/bands/b/transfer', 'DELETE'],
  ['accept transfer', () => bands.acceptBandTransfer('b'), '/api/bands/b/transfer/accept', 'POST'],
  ['reject transfer', () => bands.rejectBandTransfer('b'), '/api/bands/b/transfer', 'DELETE'],
]
afterEach(() => vi.restoreAllMocks())
describe('Band API contract', () => {
  it.each(cases)('%s uses the backend endpoint and payload', async (_, call, url, method, payload) => {
    const empty = ['DELETE'].includes(method) || url.endsWith('/leave')
    const data = { id: 'b', name: 'Jazz' }
    const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      empty ? new Response(null, { status: 204 }) : new Response(JSON.stringify(data)),
    )
    expect(await call()).toEqual(empty ? undefined : data)
    const [actualUrl, options] = fetch.mock.calls[0]
    expect(actualUrl).toBe(url)
    expect(options?.method || 'GET').toBe(method)
    expect(options?.body ? JSON.parse(options.body as string) : undefined).toEqual(payload)
    if (payload) expect(new Headers(options?.headers).get('Content-Type')).toBe('application/json')
  })
  it.each(cases)('%s preserves structured backend failures', async (_, call) => {
    const body = { error: 'band_full', message: 'Backend message' }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(body), { status: 409 }))
    await expect(call()).rejects.toMatchObject({ name: 'HttpError', status: 409, code: 'band_full', body })
    await expect(call()).rejects.toBeInstanceOf(HttpError)
  })
  it('handles a non-JSON failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('unavailable', { status: 503 }))
    await expect(bands.listBands()).rejects.toMatchObject({ status: 503 })
  })
})
