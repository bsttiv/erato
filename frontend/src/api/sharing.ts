import { apiClient } from './client'
import type { CompositionResponse, Visibility } from './compositions'

export type MemberRole = 'owner' | 'editor' | 'viewer'

export interface MemberDetail {
  user_id?: string | null
  invite_id?: string | null
  display_name?: string | null
  email?: string | null
  initials?: string | null
  role: MemberRole
  pending: boolean
}

export interface InviteResponse {
  id: string
  composition_id: string
  invite_url?: string | null
  invited_email?: string | null
  role: 'editor' | 'viewer'
  expires_at: string
  used_at?: string | null
  /** @deprecated Kept for transitional compatibility */
  token?: string
  /** @deprecated Kept for transitional compatibility */
  created_at?: string
}

export interface CreateInvitePayload {
  invited_email?: string | null
  email?: string | null
  role?: 'editor' | 'viewer'
}

export async function setVisibility(
  compositionId: string,
  visibility: Visibility | boolean
): Promise<CompositionResponse & { is_public?: boolean }> {
  const visString: Visibility =
    typeof visibility === 'boolean' ? (visibility ? 'public' : 'private') : visibility

  const res = await apiClient(`/compositions/${compositionId}/visibility`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ visibility: visString }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al cambiar visibilidad')
  }
  const data = await res.json()
  // Ensure backward-compatibility field is_public for existing consumers
  if (data && data.is_public === undefined) {
    data.is_public = data.visibility === 'public'
  }
  return data
}

export async function createInvite(
  compositionId: string,
  payload?: CreateInvitePayload
): Promise<InviteResponse> {
  const role = payload?.role ?? 'editor'
  const invited_email = payload?.invited_email ?? payload?.email ?? null

  const res = await apiClient(`/compositions/${compositionId}/invites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invited_email,
      role,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al crear invitación')
  }
  return res.json()
}

export async function listInvites(compositionId: string): Promise<InviteResponse[]> {
  const res = await apiClient(`/compositions/${compositionId}/invites`)
  if (!res.ok) {
    throw new Error('Error al listar invitaciones')
  }
  return res.json()
}

export async function revokeInvite(
  compositionId: string,
  inviteId: string
): Promise<void> {
  const res = await apiClient(`/compositions/${compositionId}/invites/${inviteId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al revocar invitación')
  }
}

export async function redeemInvite(
  token: string
): Promise<{ message: string; composition_id: string }> {
  const res = await apiClient('/auth/redeem-invite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al canjear invitación')
  }
  return res.json()
}

export async function listMembers(compositionId: string): Promise<MemberDetail[]> {
  const res = await apiClient(`/compositions/${compositionId}/members`)
  if (!res.ok) {
    throw new Error('Error al listar miembros')
  }
  return res.json()
}
