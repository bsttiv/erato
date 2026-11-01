<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { session } from '../stores/session'
import { errorMessage } from '../api/messages'
import AuthLayout from '../components/organisms/AuthLayout.vue'

const email = ref('')
const password = ref('')
const router = useRouter()
const route = useRoute()
const busy = ref(false)
const error = ref('')
async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await session.login({ email: email.value, password: password.value })
    const target = route.query.redirect
    await router.replace(typeof target === 'string' && target.startsWith('/') && !target.startsWith('//') ? target : '/canciones')
  } catch (failure) { error.value = errorMessage(failure) }
  finally { password.value = ''; busy.value = false }
}
const showPassword = ref(false)
</script>

<template>
  <AuthLayout headline="Vuelve a tu cancionero.">
    <form @submit.prevent="submit">
      <h1 class="text-[48px] leading-none sm:text-[56px]">Iniciar sesión</h1>
      <p class="mt-3.5 text-[17px] leading-normal">Entra a tus composiciones y a las de tus bandas.</p>

      <div class="mt-9">
        <label for="login-email" class="field-label">Correo</label>
        <input id="login-email" v-model="email" required type="email" autocomplete="email" class="field-input" />
      </div>
      <div class="mt-5">
        <div class="flex items-baseline justify-between">
          <label for="login-password" class="field-label">Contraseña</label>

        </div>
        <div class="relative">
          <input id="login-password" v-model="password" required :type="showPassword ? 'text' : 'password'" autocomplete="current-password" class="field-input pr-28" />
          <button type="button" class="absolute bottom-1 right-1 top-1 cursor-pointer rounded-[3px] border-0 bg-raised px-3.5 text-sm font-medium text-ink" @click="showPassword = !showPassword">{{ showPassword ? 'Ocultar' : 'Mostrar' }}</button>
        </div>
      </div>
      <p v-if="error" role="alert" class="mt-4">{{ error }}</p>
      <p v-if="$route.query.registered" role="status" class="mt-4">Tu cuenta está creada. Inicia sesión.</p>
      <button type="submit" :disabled="busy" class="btn-primary mt-5 min-h-[52px] w-full text-[17px]">{{ busy ? 'Cargando…' : 'Entrar' }}</button>
      <p class="mt-7 text-base">¿Aún no tienes cuenta? <router-link :to="{ path: '/registro', query: route.query.redirect ? { redirect: route.query.redirect } : {} }">Regístrate gratis</router-link></p>
    </form>
  </AuthLayout>
</template>
