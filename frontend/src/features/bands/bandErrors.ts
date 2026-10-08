import { HttpError } from '@/api/compositions'

const messages: Record<string, string> = {
  plan_gate_sharing: 'Compartir con personas no está disponible con tu plan.',
  invitation_expired: 'Esta invitación venció. Pide un nuevo enlace a quien te invitó.',
  invitation_legacy: 'Esta invitación antigua ya no está disponible. Pide una invitación a la banda.',
  band_full: 'No quedan plazas en esta banda.',
  transfer_pending: 'Ya hay una transferencia pendiente.',
  owner_must_transfer: 'Transfiere la propiedad antes de salir de la banda.',
  not_a_band_member: 'Esta persona ya no pertenece a la banda.',
  transfer_expired: 'La transferencia venció. Pide una nueva al dueño.',
  transfer_not_found: 'Ya no hay una transferencia pendiente.',
  transfer_not_confirmed: 'No se pudo confirmar la transferencia. Inténtalo de nuevo.',
  plan_gate_band_creation: 'La creación de bandas no está disponible con tu plan.',
  band_inactive: 'Esta banda está inactiva.',
  validation_error: 'Revisa los datos. El nombre debe tener entre 1 y 80 caracteres.',
  forbidden: 'No tienes permiso para realizar esta acción.',
  not_found: 'No se encontró la banda o ya no tienes acceso.',
}
export function bandErrorMessage(error: unknown, context?: 'invitation'): string {
  if (context === 'invitation' && error instanceof HttpError && error.code === 'not_found') {
    return 'Esta invitación no existe. Pide un nuevo enlace a quien te invitó.'
  }
  return (error instanceof HttpError && messages[error.code || '']) ||
    'No se pudo completar la acción. Inténtalo de nuevo.'
}
