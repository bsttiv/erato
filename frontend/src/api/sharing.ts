import { apiClient } from './client'

export interface InviteResponse {
  id: string
  composition_id: string
  created_at: string
  expires_at: string
  token?: string
  invite_url?: string
}

export async function setVisibility(
  compositionId: string,
  isPublic: boolean
): Promise<{ is_public: boolean }> {
  const res = await apiClient(`/compositions/${compositionId}/visibility`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_public: isPublic }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error al cambiar visibilidad')
  }
  return res.json()
}

export async function createInvite(compositionId: string): Promise<InviteResponse> {
  const res = await apiClient(`/compositions/${compositionId}/invites`, {
    method: 'POST',
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

export async function redeemInvite(token: string): Promise<{ composition_id: string; role: string }> {
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
