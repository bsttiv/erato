import { apiClient } from './client'
import { HttpError } from './compositions'

export interface Entitlements {
  can_share_with_people: boolean
  can_create_band: boolean
  can_view_history: boolean
  demo_limit_per_composition: number | null
  extensions_available: boolean
  band_creation_mode: 'direct' | 'hand_off'
}

export async function getEntitlements(): Promise<Entitlements> {
  const response = await apiClient('/me/entitlements')
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new HttpError('No se pudieron cargar tus permisos', response.status, body.error, body)
  }
  return response.json()
}
