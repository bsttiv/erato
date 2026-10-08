<template>
  <div class="er-createshell">
    <header class="er-createbar">
      <router-link to="/" class="er-topbar-brand">
        <ErBrand />
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
        Te invitaron a una banda
      </h1>
      <p class="er-auth-subtitle">
        Al aceptar, te sumas a la banda y podrás abrir las composiciones que comparte contigo.
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
import { ErButton, ErBrand } from '@/design-system'
import { redeemInvite } from '@/api/sharing'
import { useEntitlements } from '@/features/plan/useEntitlements'
import { bandErrorMessage } from '@/features/bands/bandErrors'

const route = useRoute()
const router = useRouter()

const redeeming = ref(false)
const error = ref<string | null>(null)

const { refresh } = useEntitlements()

async function accept() {
  if (redeeming.value) return
  redeeming.value = true
  error.value = null
  try {
    const token = String(route.params.token ?? '')
    const res = await redeemInvite(token)
    await refresh()
    await router.push(`/bands/${res.band_id}`)
  } catch (err) {
    error.value = bandErrorMessage(err, 'invitation')
  } finally {
    redeeming.value = false
  }
}
</script>
