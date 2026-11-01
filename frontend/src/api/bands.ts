import { client } from '../stores/session'

export interface Band {
  id: string
  name: string
  owner_id?: string
  created_at?: string
  updated_at?: string
}
/** Public projection of a member; `role` is null for band members. */
export interface Member {
  username: string
  display_name: string
  role: 'editor' | 'viewer' | null
}
export type InvitationTarget = 'song' | 'band'
/** Link metadata. The token only exists in the response that creates the link. */
export interface Invitation {
  id: string
  target_type: InvitationTarget
  target_id: string
  role: 'editor' | 'viewer' | null
  created_by?: string
  created_at: string
  expires_at: string
}
export interface CreatedInvitation extends Invitation {
  token: string
  url: string
}
export interface Membership {
  id: string
  target_type: InvitationTarget
  target_id: string
  role: 'editor' | 'viewer' | null
}

const id = encodeURIComponent

export const bandsApi = {
  list: () => client.request<Band[]>('/bands'),
  create: (name: string) => client.request<Band>('/bands', { method: 'POST', body: { name } }),
  read: (bandId: string) => client.request<Band>(`/bands/${id(bandId)}`),
  members: (bandId: string) => client.request<Member[]>(`/bands/${id(bandId)}/members`),
  removeMember: (bandId: string, username: string) => client.request(`/bands/${id(bandId)}/members/${id(username)}`, { method: 'DELETE' }),
  transfer: (bandId: string, username: string) => client.request<Band>(`/bands/${id(bandId)}/transfer`, { method: 'POST', body: { username } }),
}

export const songMembersApi = {
  list: (songId: string) => client.request<Member[]>(`/songs/${id(songId)}/members`),
  setRole: (songId: string, username: string, role: 'editor' | 'viewer') =>
    client.request<Member>(`/songs/${id(songId)}/members/${id(username)}`, { method: 'PATCH', body: { role } }),
  remove: (songId: string, username: string) => client.request(`/songs/${id(songId)}/members/${id(username)}`, { method: 'DELETE' }),
}

export const invitationsApi = {
  list: (targetType: InvitationTarget, targetId: string) =>
    client.request<Invitation[]>(`/invitations?target_type=${targetType}&target_id=${id(targetId)}`),
  create: (targetType: InvitationTarget, targetId: string, role: 'editor' | 'viewer' | null) =>
    client.request<CreatedInvitation>('/invitations', {
      method: 'POST',
      body: { target_type: targetType, target_id: targetId, ...(role ? { role } : {}) },
    }),
  revoke: (invitationId: string) => client.request(`/invitations/${id(invitationId)}`, { method: 'DELETE' }),
  use: (token: string) => client.request<Membership>(`/invitations/${id(token)}/use`, { method: 'POST' }),
}

/** Absolute shareable address of a link created by the API (`url` is relative). */
export const invitationLink = (url: string): string => `${window.location.origin}${url}`
