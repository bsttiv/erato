import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  setVisibility,
  createInvite,
  listInvites,
  revokeInvite,
  redeemInvite,
  listMembers,
} from '@/api/sharing'

describe('Sharing API client contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('setVisibility(id, visibility) sends PATCH /compositions/{id}/visibility with { visibility }', async () => {
    const mockResponse = {
      id: 'comp-1',
      owner_id: 'user-1',
      title: 'Song',
      visibility: 'public',
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await setVisibility('comp-1', 'public')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/visibility')
    expect(init?.method).toBe('PATCH')
    expect(JSON.parse(init?.body as string)).toEqual({ visibility: 'public' })
    expect(result.visibility).toBe('public')
  })

  it('createInvite(id, payload) sends POST /compositions/{id}/invites with { invited_email, role }', async () => {
    const mockInvite = {
      id: 'inv-1',
      composition_id: 'comp-1',
      invite_url: 'https://erato.app/invite/token123',
      invited_email: 'bandmate@example.com',
      role: 'viewer',
      expires_at: '2026-10-08T12:00:00Z',
      used_at: null,
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockInvite), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await createInvite('comp-1', {
      email: 'bandmate@example.com',
      role: 'viewer',
    })

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/invites')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({
      invited_email: 'bandmate@example.com',
      role: 'viewer',
    })
    expect(result.invite_url).toBe('https://erato.app/invite/token123')
    expect(result.role).toBe('viewer')
  })

  it('listInvites(id) calls GET /compositions/{id}/invites and returns InviteResponse[]', async () => {
    const mockInvites = [
      {
        id: 'inv-1',
        composition_id: 'comp-1',
        invite_url: null,
        invited_email: 'bandmate@example.com',
        role: 'editor',
        expires_at: '2026-10-08T12:00:00Z',
        used_at: null,
      },
    ]

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockInvites), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await listInvites('comp-1')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/invites')
    expect(result).toEqual(mockInvites)
  })

  it('revokeInvite(id, inviteId) calls DELETE /compositions/{id}/invites/{inviteId}', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Invitación revocada correctamente' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    await revokeInvite('comp-1', 'inv-1')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/invites/inv-1')
    expect(init?.method).toBe('DELETE')
  })

  it('redeemInvite(token) calls POST /auth/redeem-invite with { token }', async () => {
    const mockRedeem = {
      composition_id: 'comp-1',
      role: 'editor',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockRedeem), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await redeemInvite('secret-token')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/auth/redeem-invite')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ token: 'secret-token' })
    expect(result).toEqual(mockRedeem)
  })

  it('listMembers(id) calls GET /compositions/{id}/members and returns MemberDetail[]', async () => {
    const mockMembers = [
      {
        user_id: 'user-1',
        display_name: 'Miles Davis',
        email: 'miles@example.com',
        initials: 'MD',
        role: 'owner',
        pending: false,
      },
      {
        user_id: 'user-2',
        display_name: null,
        email: 'coltrane@example.com',
        initials: 'C',
        role: 'viewer',
        pending: true,
      },
    ]

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockMembers), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await listMembers('comp-1')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/members')
    expect(result).toEqual(mockMembers)
  })
})
