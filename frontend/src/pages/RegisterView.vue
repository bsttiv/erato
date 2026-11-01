<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { session } from '../stores/session'
import { copy, validUsername, validPassword, errorMessage } from '../api/messages'
import AuthLayout from '../components/organisms/AuthLayout.vue'

const name = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')
const router = useRouter()
const route = useRoute()
// Same-site redirect only (e.g. back to an invitation link after signing up).
const redirect = () => { const target = route.query.redirect; return typeof target === 'string' && target.startsWith('/') && !target.startsWith('//') ? target : '/canciones' }
async function submit() {
  if (busy.value) return
  error.value = ''
  if (!validUsername(username.value)) { error.value = copy.username; return }
  if (![...name.value.trim()].length || [...name.value.trim()].length > 60) { error.value = copy.displayName; return }
  if (!validPassword(password.value)) { error.value = copy.password; return }
  busy.value = true
  try {
    const loggedIn = await session.register({ username: username.value, display_name: name.value.trim(), email: email.value, password: password.value })
    await router.replace(loggedIn ? redirect() : '/login?registered=1')
  } catch (failure) { error.value = errorMessage(failure) }
  finally { password.value = ''; busy.value = false }
}
const points = ['Letras, acordes y tablaturas en el mismo lugar', 'Demos con comentarios en el segundo exacto', 'Un espacio personal y otro para cada banda']
</script>

<template>
  <AuthLayout headline="Tu primera canción cabe en una hoja." :points="points">
    <form @submit.prevent="submit">
      <h1 class="text-[48px] leading-none sm:text-[56px]">Crea tu cuenta</h1>
      <p class="mt-3.5 text-[17px] leading-normal">Gratis y con todas las funciones. Después podrás crear una banda o unirte a una.</p>

      <div class="mt-8">
        <label for="reg-name" class="field-label">Nombre visible</label>
        <input id="reg-name" v-model="name" required type="text" autocomplete="name" class="field-input" />
      </div>
      <div class="mt-4">
        <label for="reg-username" class="field-label">Nombre de usuario</label>
        <input id="reg-username" v-model="username" required autocomplete="username" class="field-input" />
      </div>
      <div class="mt-4">
        <label for="reg-email" class="field-label">Correo</label>
        <input id="reg-email" v-model="email" required type="email" autocomplete="email" class="field-input" />
      </div>
      <div class="mt-4">
        <label for="reg-password" class="field-label">Contraseña</label>
        <input id="reg-password" v-model="password" required type="password" autocomplete="new-password" class="field-input" aria-describedby="reg-rules" />
        <p id="reg-rules" class="mt-2.5 text-sm">Debe tener entre 8 y 128 caracteres.</p>
      </div>
      <p v-if="error" role="alert" class="mt-4">{{ error }}</p>
      <button type="submit" :disabled="busy" class="btn-primary mt-6 min-h-[52px] w-full text-[17px]">{{ busy ? 'Cargando…' : 'Crear cuenta' }}</button>
      <p class="mt-6 text-base">¿Ya tienes cuenta? <router-link :to="{ path: '/login', query: route.query.redirect ? { redirect: route.query.redirect } : {} }">Inicia sesión</router-link></p>
    </form>
  </AuthLayout>
</template>
