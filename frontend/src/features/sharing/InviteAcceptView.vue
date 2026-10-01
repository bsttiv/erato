<template>
  <div class="er-createshell">
    <header class="er-createbar">
      <router-link to="/" class="er-topbar-brand">
        Erato
      </router-link>
      <router-link to="/" class="er-auth-link">
        Ir al inicio
      </router-link>
    </header>

    <main class="er-form-card">
      <div class="er-label">
        // INVITACIÓN
      </div>
      <h1 class="er-dash-headline">
        Te invitaron a colaborar
      </h1>
      <p class="er-auth-subtitle">
        Al aceptar, la composición se suma a tu espacio y podrás trabajar en ella con el rol
        que te asignaron.
      </p>

      <div v-if="error" class="er-auth-error" role="alert">
        {{ error }}
      </div>

      <ErButton
        type="button"
        variant="primary"
        :disabled="redeeming"
        @click="accept"
      >
        {{ redeeming ? 'Aceptando…' : 'Aceptar invitación' }}
      </ErButton>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ErButton } from '@/design-system'
import { redeemInvite } from '@/api/sharing'

const route = useRoute()
const router = useRouter()

const redeeming = ref(false)
const error = ref<string | null>(null)

const INVALID_LINK_MESSAGE =
  'Este enlace de invitación no es válido o ya venció. Pide a quien te invitó que cree uno nuevo.'
const GENERIC_MESSAGE = 'No pudimos aceptar la invitación. Inténtalo de nuevo en unos minutos.'

function toMessage(err: unknown): string {
  const text = err instanceof Error ? err.message.toLowerCase() : ''
  if (/inv[aá]lid|expir|venc|no encontrad|not found|invalid/.test(text)) {
    return INVALID_LINK_MESSAGE
  }
  return GENERIC_MESSAGE
}

async function accept() {
  if (redeeming.value) return
  redeeming.value = true
  error.value = null
  try {
    const token = String(route.params.token ?? '')
    const res = await redeemInvite(token)
    await router.push(`/compositions/${res.composition_id}`)
  } catch (err) {
    error.value = toMessage(err)
  } finally {
    redeeming.value = false
  }
}
</script>
