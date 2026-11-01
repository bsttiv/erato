<script setup>
import { ref, computed } from 'vue'
import AuthLayout from '../components/app/AuthLayout.vue'

const name = ref('Bastián Valencia')
const email = ref('bastian@losfaroles.cl')
const password = ref('Farol')

const rules = computed(() => [
  { label: '8 caracteres o más', ok: password.value.length >= 8 },
  { label: 'Un número', ok: /\d/.test(password.value) },
  { label: 'Una mayúscula', ok: /[A-ZÁÉÍÓÚÑ]/.test(password.value) },
])
const points = ['Letras, acordes y tablaturas en el mismo lugar', 'Demos con comentarios en el segundo exacto', 'Un espacio personal y otro para cada banda']
</script>

<template>
  <AuthLayout headline="Tu primera canción cabe en una hoja." :points="points">
    <form @submit.prevent>
      <h1 class="text-[48px] leading-none sm:text-[56px]">Crea tu cuenta</h1>
      <p class="mt-3.5 text-[17px] leading-normal">Gratis y con todas las funciones. Después podrás crear una banda o unirte a una.</p>

      <div class="mt-8">
        <label for="reg-name" class="field-label">Nombre</label>
        <input id="reg-name" v-model="name" type="text" autocomplete="name" class="field-input" />
      </div>
      <div class="mt-4">
        <label for="reg-email" class="field-label">Correo</label>
        <input id="reg-email" v-model="email" type="email" autocomplete="email" class="field-input" />
      </div>
      <div class="mt-4">
        <label for="reg-password" class="field-label">Contraseña</label>
        <input id="reg-password" v-model="password" type="password" autocomplete="new-password" class="field-input" aria-describedby="reg-rules" />
        <ul id="reg-rules" class="mt-2.5 flex list-none flex-wrap gap-x-5 gap-y-2 p-0">
          <li v-for="r in rules" :key="r.label" class="flex items-center gap-2 text-sm" :class="r.ok ? 'text-ink' : 'text-muted'">
            <span class="h-2 w-2 rounded-full transition-colors" :class="r.ok ? 'bg-brass' : 'bg-fret'" aria-hidden="true"></span>{{ r.label }}
          </li>
        </ul>
      </div>
      <label class="mt-5 flex cursor-pointer items-start gap-2.5 text-[15px] leading-snug">
        <input type="checkbox" checked class="mt-0.5 h-5 w-5 shrink-0 accent-brass" />
        <span>Acepto los <a href="#terminos">términos de servicio</a> y la <a href="#privacidad">política de privacidad</a>.</span>
      </label>
      <router-link to="/composiciones" class="btn-primary mt-6 min-h-[52px] w-full text-[17px]">Crear cuenta</router-link>
      <p class="mt-6 text-base">¿Ya tienes cuenta? <router-link to="/login">Inicia sesión</router-link></p>
    </form>
  </AuthLayout>
</template>
