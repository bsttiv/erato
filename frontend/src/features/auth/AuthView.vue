<template>
  <div class="er-auth-view er-panel">
    <div class="er-auth-header">
      <div class="er-label">
        // cuenta
      </div>
      <ErSegmented
        v-model="mode"
        label="Modo de autenticación"
        :options="[
          { value: 'login', label: 'Iniciar sesión' },
          { value: 'register', label: 'Registrarse' },
        ]"
      />
    </div>

    <LoginForm v-if="mode === 'login'" @success="onSuccess" />
    <RegisterForm v-else @success="onSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErSegmented } from '@/design-system'
import LoginForm from './LoginForm.vue'
import RegisterForm from './RegisterForm.vue'

const emit = defineEmits<{
  (e: 'authenticated'): void
}>()

const mode = ref<'login' | 'register'>('login')

function onSuccess() {
  emit('authenticated')
}
</script>
