import { apiClient, setAccessToken } from './client'

export interface UserResponse {
  id: string
  email: string
  display_name: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await apiClient('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Credenciales incorrectas')
  }
  const data: AuthResponse = await res.json()
  setAccessToken(data.access_token)
  return data
}

export async function register(
  email: string,
  password: string,
  displayName: string
): Promise<AuthResponse> {
  const res = await apiClient('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, display_name: displayName }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Error al registrar usuario')
  }
  const data: AuthResponse = await res.json()
  setAccessToken(data.access_token)
  return data
}

export async function logout(): Promise<void> {
  await apiClient('/auth/logout', { method: 'POST' }).catch(() => {})
  setAccessToken(null)
}

export async function getMe(): Promise<UserResponse> {
  const res = await apiClient('/auth/me')
  if (!res.ok) {
    throw new Error('No autenticado')
  }
  return res.json()
}
