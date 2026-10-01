<template>
  <form class="er-auth-form" @submit.prevent="handleSubmit">
    <div class="er-auth-header">
      <h2 class="er-auth-title">Crea tu cuenta</h2>
      <p class="er-auth-subtitle">Organiza las canciones de tu banda en un solo lugar.</p>
    </div>

    <div v-if="error" class="er-auth-error">
      {{ error }}
    </div>

    <div class="er-field">
      <label for="reg-name" class="er-label">Tu nombre</label>
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
      <div class="er-password-field">
        <input
          id="reg-password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          class="er-input"
          placeholder="Al menos 8 caracteres"
          minlength="8"
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
      {{ loading ? 'Creando cuenta…' : 'Crear cuenta' }}
    </ErButton>

    <div class="er-auth-links">
      <router-link :to="crossLink" class="er-auth-link">
        ¿Ya tienes cuenta? Inicia sesión
      </router-link>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { safeNextPath } from '@/router/safeNext'
import { ErButton } from '@/design-system'
import { register } from '@/api/auth'

const emit = defineEmits<{
  (e: 'success'): void
}>()

const route = useRoute()
const crossLink = computed(() => {
  const next = safeNextPath(route?.query?.next)
  return next === '/' ? '/login' : { path: '/login', query: { next } }
})

const displayName = ref('')
const email = ref('')
const password = ref('')
const showPassword = ref(false)
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
