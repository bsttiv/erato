import { reactive } from 'vue'
import { ApiError, createClient, type ApiClient } from '../api/client'

const deviceKey = 'erato.deviceId'
export interface AuthTokens {
  access_token: string
}
export interface SessionUser {
  username: string
  display_name: string
}
/** One open session (device) as listed on the profile page. */
export interface SessionDevice {
  id: string
  device: string
  last_access_at: string
  current?: boolean
}
export const session = reactive({
  accessToken: null as string | null,
  user: null as SessionUser | null,
  deviceId(): string {
    let id = localStorage.getItem(deviceKey)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(deviceKey, id)
    }
    return id
  },
  setTokens(tokens: AuthTokens) {
    session.accessToken = tokens.access_token
  },
  clear() {
    session.accessToken = null
    session.user = null
  },
  async restore(): Promise<boolean> {
    if (session.accessToken) return true
    // The refresh cookie is httpOnly, so the only way to know it exists is to try it.
    try {
      await client.refresh()
      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) return false
      throw error
    }
  },
  async login(body: unknown): Promise<void> {
    session.setTokens(await client.request('/auth/login', { method: 'POST', body, authenticated: false }))
  },
  async register(body: unknown): Promise<boolean> {
    const result = await client.request('/auth/register', { method: 'POST', body, authenticated: false })
    if (result.access_token) session.setTokens(result)
    return Boolean(result.access_token)
  },
  async logout(): Promise<void> {
    await client.request('/auth/logout', { method: 'POST' })
    session.clear()
  },
})
export const client: ApiClient = createClient(session)
export const profileApiKey = Symbol('profileApi')
export const profileApi = {
  async getMe(): Promise<SessionUser> { return (session.user = await client.request<SessionUser>('/me')) },
  async updateMe(body: unknown): Promise<SessionUser> { return (session.user = await client.request<SessionUser>('/me', { method: 'PATCH', body })) },
  async changeEmail(body: unknown): Promise<SessionUser> { return (session.user = await client.request<SessionUser>('/me/email', { method: 'PATCH', body })) },
  listSessions: () => client.request<SessionDevice[]>('/me/sessions'),
  closeSession: (id: string) => client.request(`/me/sessions/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  changePassword: (body: unknown) => client.request('/me/password', { method: 'PATCH', body }),
}
