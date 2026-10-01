<template>
  <div class="er-auth-split">
    <div class="er-auth-hero">
      <div>
        <h1 class="er-auth-wordmark">Erato</h1>
        <p class="er-auth-tagline">Tu música, tus acordes, tu banda.</p>
      </div>

      <div class="er-auth-bars">
        <div class="er-auth-bar" />
        <div class="er-auth-bar er-auth-bar--ivory" />
        <div class="er-auth-pill" />
        <div class="er-auth-bar er-auth-bar--wine" />
        <div class="er-auth-bar er-auth-bar--ember" />
        <div class="er-auth-rules" />
      </div>
    </div>

    <div class="er-auth-pane">
      <div class="er-auth-view">
        <LoginForm v-if="mode === 'login'" @success="onSuccess" />
        <RegisterForm v-else @success="onSuccess" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { safeNextPath } from '@/router/safeNext'
import LoginForm from './LoginForm.vue'
import RegisterForm from './RegisterForm.vue'

const props = defineProps<{
  initialMode?: 'login' | 'register'
}>()

const emit = defineEmits<{
  (e: 'authenticated'): void
}>()

const route = useRoute()
const router = useRouter()

const mode = computed<'login' | 'register'>(() => {
  if (props.initialMode) return props.initialMode
  if (route && (route.path === '/register' || route.name === 'register')) {
    return 'register'
  }
  return 'login'
})

function onSuccess() {
  emit('authenticated')
  if (router) {
    router.push(safeNextPath(route?.query?.next))
  }
}
</script>
