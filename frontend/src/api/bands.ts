import { apiClient } from './client'
import { HttpError } from './compositions'

export interface BandSummary {
  id: string
  name: string
  owner_id: string
  user_role: 'owner' | 'member'
  seats_used: number
  seat_limit: number | null
  active: boolean
}
export interface BandMember {
  user_id: string
  display_name: string | null
  initials: string | null
  role: 'owner' | 'member'
}
export interface BandResponse extends BandSummary {
  members: BandMember[]
  pending_transfer: { to_user_id: string; requested_at: string; expires_at: string } | null
  created_at: string
  updated_at: string
}
export interface BandInviteSummary { id: string; expires_at: string }
export interface BandInviteResponse extends BandInviteSummary { invite_url: string }

async function request<T>(path = '', method = 'GET', payload?: object): Promise<T> {
  const response = await apiClient(`/bands${path}`, {
    method,
    ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new HttpError('No se pudo completar la acción.', response.status, body.error, body)
  }
  return response.status === 204 ? (undefined as T) : response.json()
}
const path = (id: string) => `/${encodeURIComponent(id)}`
export const listBands = () => request<BandSummary[]>()
export const getBand = (id: string) => request<BandResponse>(path(id))
export const createBand = (name: string) => request<BandResponse>('', 'POST', { name })
export const renameBand = (id: string, name: string) => request<BandResponse>(path(id), 'PATCH', { name })
export const createBandInvite = (id: string) => request<BandInviteResponse>(`${path(id)}/invites`, 'POST', {})
export const listBandInvites = (id: string) => request<BandInviteSummary[]>(`${path(id)}/invites`)
export const deleteBandInvite = (id: string, inviteId: string) => request<void>(`${path(id)}/invites/${encodeURIComponent(inviteId)}`, 'DELETE')
export const leaveBand = (id: string) => request<void>(`${path(id)}/leave`, 'POST')
export const removeBandMember = (id: string, userId: string) => request<void>(`${path(id)}/members/${encodeURIComponent(userId)}`, 'DELETE')
export const requestBandTransfer = (id: string, userId: string) => request<BandResponse>(`${path(id)}/transfer`, 'POST', { to_user_id: userId })
export const cancelBandTransfer = (id: string) => request<void>(`${path(id)}/transfer`, 'DELETE')
export const rejectBandTransfer = cancelBandTransfer
export const acceptBandTransfer = (id: string) => request<BandResponse>(`${path(id)}/transfer/accept`, 'POST')
