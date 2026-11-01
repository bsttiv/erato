<script setup>
import { ref } from 'vue'
import AuthLayout from '../components/app/AuthLayout.vue'

const email = ref('bastian@losfaroles.cl')
const password = ref('cancionero2026')
const showPassword = ref(false)
</script>

<template>
  <AuthLayout headline="Vuelve a tu cancionero.">
    <form @submit.prevent>
      <h1 class="text-[48px] leading-none sm:text-[56px]">Iniciar sesión</h1>
      <p class="mt-3.5 text-[17px] leading-normal">Entra a tus composiciones y a las de tus bandas.</p>

      <div class="mt-9">
        <label for="login-email" class="field-label">Correo</label>
        <input id="login-email" v-model="email" type="email" autocomplete="email" class="field-input" />
      </div>
      <div class="mt-5">
        <div class="flex items-baseline justify-between">
          <label for="login-password" class="field-label">Contraseña</label>
          <a href="#recuperar" class="text-sm">¿La olvidaste?</a>
        </div>
        <div class="relative">
          <input id="login-password" v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" class="field-input pr-28" />
          <button type="button" class="absolute bottom-1 right-1 top-1 cursor-pointer rounded-[3px] border-0 bg-raised px-3.5 text-sm font-medium text-ink" @click="showPassword = !showPassword">{{ showPassword ? 'Ocultar' : 'Mostrar' }}</button>
        </div>
      </div>
      <label class="mt-4 flex min-h-[44px] cursor-pointer items-center gap-2.5 text-base">
        <input type="checkbox" checked class="h-5 w-5 accent-brass" />Mantener la sesión abierta
      </label>
      <router-link to="/composiciones" class="btn-primary mt-5 min-h-[52px] w-full text-[17px]">Entrar</router-link>
      <p class="mt-7 text-base">¿Aún no tienes cuenta? <router-link to="/registro">Regístrate gratis</router-link></p>
    </form>
  </AuthLayout>
</template>
