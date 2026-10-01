<template>
  <form class="er-auth-form" @submit.prevent="handleSubmit">
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
      <input
        id="login-password"
        v-model="password"
        type="password"
        class="er-input"
        placeholder="••••••••"
        required
      >
    </div>

    <ErButton
      type="submit"
      variant="primary"
      :disabled="loading"
    >
      {{ loading ? 'Iniciando sesión…' : 'Iniciar sesión' }}
    </ErButton>
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
