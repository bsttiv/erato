import { apiClient } from './client'
import { HttpError, type CompositionResponse, type Visibility } from './compositions'

export type MemberRole = 'owner' | 'editor' | 'viewer'
export interface MemberDetail {
  user_id: string
  display_name?: string | null
  email?: string | null
  initials?: string | null
  role: MemberRole
  pending: false
}
export interface BandSharingResponse extends CompositionResponse {
  band_id: string | null
  band_editable: boolean
  band_active?: boolean | null
}
export interface RedeemInviteResponse { band_id: string; status: 'joined' | 'already_member' }

async function request<T>(path: string, method = 'GET', payload?: object): Promise<T> {
  const response = await apiClient(path, {
    method,
    ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new HttpError('No se pudo completar la acción.', response.status, body.error, body)
  }
  return response.status === 204 ? (undefined as T) : response.json()
}
const path = (id: string) => `/compositions/${encodeURIComponent(id)}`
export async function setVisibility(compositionId: string, visibility: Visibility | boolean): Promise<CompositionResponse> {
  const value = typeof visibility === 'boolean' ? (visibility ? 'public' : 'private') : visibility
  const data = await request<CompositionResponse>(`${path(compositionId)}/visibility`, 'PATCH', { visibility: value })
  return { ...data, is_public: data.visibility === 'public' }
}
export const setCompositionBand = (id: string, bandId: string | null, bandEditable: boolean) =>
  request<BandSharingResponse>(`${path(id)}/band`, 'PATCH', { band_id: bandId, band_editable: bandEditable })
export const setMemberRole = (id: string, userId: string, role: 'editor' | 'viewer') =>
  request<void>(`${path(id)}/members/${encodeURIComponent(userId)}`, 'PUT', { role })
export const removeMember = (id: string, userId: string) =>
  request<void>(`${path(id)}/members/${encodeURIComponent(userId)}`, 'DELETE')
export const listMembers = (id: string) => request<MemberDetail[]>(`${path(id)}/members`)
export const redeemInvite = (token: string) => request<RedeemInviteResponse>('/auth/redeem-invite', 'POST', { token })
