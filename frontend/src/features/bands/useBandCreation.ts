import { computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { PAYMENT_EXTENSION_KEY } from '@/extension'
import { useEntitlements } from '@/features/plan/useEntitlements'

export function useBandCreation(openForm: () => void) {
  const payments = inject(PAYMENT_EXTENSION_KEY, undefined)
  const router = useRouter()
  const { entitlements } = useEntitlements()
  const actionable = computed(() => entitlements.value?.band_creation_mode === 'direct' ||
    (entitlements.value?.band_creation_mode === 'hand_off' && !!payments?.bandCreationEntry))
  const explanation = computed(() => actionable.value ? '' :
    'La creación de bandas no está disponible en esta instalación.')

  async function create(): Promise<void> {
    if (!actionable.value) return
    if (entitlements.value?.band_creation_mode === 'direct') openForm()
    else if (payments?.bandCreationEntry) await router.push(payments.bandCreationEntry)
  }
  return { actionable, explanation, create }
}
