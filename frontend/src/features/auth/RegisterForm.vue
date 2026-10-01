<template>
  <form class="er-auth-form" @submit.prevent="handleSubmit">
    <div v-if="error" class="er-auth-error">
      {{ error }}
    </div>

    <div class="er-field">
      <label for="reg-name" class="er-label">Nombre artístico / display name</label>
      <input
        id="reg-name"
        v-model="displayName"
        type="text"
        class="er-input"
        placeholder="Tu nombre"
        required
      >
    </div>

    <div class="er-field">
      <label for="reg-email" class="er-label">Email</label>
      <input
        id="reg-email"
        v-model="email"
        type="email"
        class="er-input"
        placeholder="tu@correo.com"
        required
      >
    </div>

    <div class="er-field">
      <label for="reg-password" class="er-label">Contraseña</label>
      <input
        id="reg-password"
        v-model="password"
        type="password"
        class="er-input"
        placeholder="Al menos 8 caracteres"
        minlength="8"
        required
      >
    </div>

    <ErButton
      type="submit"
      variant="primary"
      :disabled="loading"
    >
      {{ loading ? 'Creando cuenta…' : 'Registrarse' }}
    </ErButton>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErButton } from '@/design-system'
import { register } from '@/api/auth'

const emit = defineEmits<{
  (e: 'success'): void
}>()

const displayName = ref('')
const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)

async function handleSubmit() {
  error.value = null
  loading.value = true
  try {
    await register(email.value, password.value, displayName.value)
    emit('success')
  } catch (err: any) {
    error.value = err.message || 'Error al registrar usuario'
  } finally {
    loading.value = false
  }
}
</script>
