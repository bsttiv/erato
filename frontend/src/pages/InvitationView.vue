<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/organisms/AuthLayout.vue'
import { invitationsApi } from '../api/bands'
import { accessMessage } from '../api/messages'
import { session } from '../stores/session'

// Enlace de invitación /i/:token. La ruta es pública para poder llevar a quien no tiene sesión
// al login y devolverlo aquí; el servidor es quien decide si el enlace sirve.
const route = useRoute()
const router = useRouter()
const checking = ref(true)
const signedIn = ref(false)
const busy = ref(false)
const error = ref('')
const alreadyMember = ref(false)

onMounted(async () => {
  try { signedIn.value = await session.restore() }
  catch { signedIn.value = false }
  finally { checking.value = false }
})

async function join() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const membership = await invitationsApi.use(String(route.params.token))
    await router.replace(membership.target_type === 'band'
      ? { path: '/canciones', query: { band_id: membership.target_id } }
      : `/canciones/${encodeURIComponent(membership.target_id)}`)
  } catch (failure) {
    if (failure.status === 401) signedIn.value = false
    alreadyMember.value = failure.code === 'already_member'
    error.value = failure.status === 404 ? 'Este enlace venció o ya no existe. Pide uno nuevo a quien te invitó.' : accessMessage(failure)
  } finally { busy.value = false }
}
</script>

<template>
  <AuthLayout headline="Tu próximo ensayo empieza aquí.">
    <h1 class="text-[48px] leading-none">Invitación</h1>
    <p v-if="checking" role="status" class="mt-5">Revisando tu sesión…</p>
    <template v-else-if="signedIn">
      <p class="mt-5">Te invitaron a colaborar en Erato. Al aceptar, tendrás acceso con el rol que definió el enlace.</p>
      <p v-if="error" role="alert" class="mt-4">{{ error }}</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <button v-if="!alreadyMember" type="button" class="btn-primary" :disabled="busy" @click="join">Unirme</button>
        <router-link to="/canciones" class="btn-ghost">Ir a mis composiciones</router-link>
      </div>
    </template>
    <template v-else>
      <p class="mt-5">Inicia sesión o crea una cuenta para aceptar esta invitación.</p>
      <p v-if="error" role="alert" class="mt-4">{{ error }}</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <router-link :to="{ path: '/login', query: { redirect: $route.fullPath } }" class="btn-primary">Iniciar sesión</router-link>
        <router-link :to="{ path: '/registro', query: { redirect: $route.fullPath } }" class="btn-ghost">Crear cuenta</router-link>
      </div>
    </template>
  </AuthLayout>
</template>
