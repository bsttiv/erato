<template>
  <form class="er-auth-form" @submit.prevent="handleSubmit">
    <div class="er-auth-header">
      <h2 class="er-auth-title">Inicia sesión</h2>
      <p class="er-auth-subtitle">Bienvenido de vuelta a tu espacio de composición.</p>
    </div>

    <div v-if="error" class="er-auth-error">
      {{ error }}
    </div>

    <div class="er-field">
      <label for="login-email" class="er-label">Email</label>
      <input
        id="login-email"
        v-model="email"
        type="email"
        class="er-input"
        placeholder="tu@correo.com"
        required
      >
    </div>

    <div class="er-field">
      <label for="login-password" class="er-label">Contraseña</label>
      <div class="er-password-field">
        <input
          id="login-password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          class="er-input"
          placeholder="••••••••"
          required
        >
        <button
          type="button"
          class="er-password-toggle"
          @click="showPassword = !showPassword"
        >
          {{ showPassword ? 'ocultar' : 'mostrar' }}
        </button>
      </div>
    </div>

    <ErButton
      type="submit"
      variant="primary"
      :disabled="loading"
    >
      {{ loading ? 'Entrando…' : 'Entrar' }}
    </ErButton>

    <div class="er-auth-links">
      <router-link to="/register" class="er-auth-link">
        ¿No tienes cuenta? Regístrate
      </router-link>
    </div>

    <p class="er-auth-note">
      Si tienes un enlace a una canción pública, puedes verla sin cuenta.
    </p>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErButton } from '@/design-system'
import { login } from '@/api/auth'

const emit = defineEmits<{
  (e: 'success'): void
}>()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref<string | null>(null)
const loading = ref(false)

async function handleSubmit() {
  error.value = null
  loading.value = true
  try {
    await login(email.value, password.value)
    emit('success')
  } catch (err: any) {
    error.value = err.message || 'Credenciales incorrectas'
  } finally {
    loading.value = false
  }
}
</script>
