import { it, expect, vi, afterEach } from 'vitest'
import * as sharing from '@/api/sharing'
import { HttpError } from '@/api/compositions'
afterEach(() => vi.restoreAllMocks())
it.each([
  ['setCompositionBand', ['c', 'b', true], '/compositions/c/band', 'PATCH', { band_id: 'b', band_editable: true }, 200],
  ['setCompositionBand', ['c', null, false], '/compositions/c/band', 'PATCH', { band_id: null, band_editable: false }, 200],
  ['setMemberRole', ['c', 'u', 'viewer'], '/compositions/c/members/u', 'PUT', { role: 'viewer' }, 204],
  ['removeMember', ['c', 'u'], '/compositions/c/members/u', 'DELETE', undefined, 204],
  ['redeemInvite', ['token'], '/auth/redeem-invite', 'POST', { token: 'token' }, 200],
  ['setVisibility', ['c', 'public'], '/compositions/c/visibility', 'PATCH', { visibility: 'public' }, 200],
  ['listMembers', ['c'], '/compositions/c/members', 'GET', undefined, 200],
])('%s follows its API contract', async (name, args, path, method, body, status) => {
  const payload = name === 'redeemInvite' ? { band_id: 'b', status: 'joined' } : { visibility: 'public' }
  const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(status === 204 ? null : JSON.stringify(payload), { status: Number(status) }))
  const result = await (sharing as any)[String(name)](...args as any[])
  const [url, init] = spy.mock.calls[0]
  expect(String(url)).toContain(`/api${path}`); expect(init?.method ?? 'GET').toBe(method)
  expect(init?.body ? JSON.parse(String(init.body)) : undefined).toEqual(body)
  expect(result).toEqual(status === 204 ? undefined : expect.objectContaining(payload))
})
it('removes legacy invite operations', () => {
  for (const name of ['createInvite', 'listInvites', 'revokeInvite']) expect(sharing).not.toHaveProperty(name)
})
it.each(['setCompositionBand', 'setMemberRole', 'removeMember', 'redeemInvite', 'listMembers', 'setVisibility'])('%s preserves machine-readable backend errors', async name => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ error: 'band_inactive', detail: 'internal' }), { status: 403 }))
  await expect((sharing as any)[name]('c', 'u', true)).rejects.toMatchObject({ code: 'band_inactive', status: 403 })
  await expect((sharing as any)[name]('c', 'u', true)).rejects.toBeInstanceOf(HttpError)
})
