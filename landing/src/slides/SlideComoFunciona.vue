<script setup lang="ts">
import { getRegisterUrl } from '../config'

const registerUrl = getRegisterUrl()

defineEmits<{
  (e: 'go-pricing'): void
}>()

const steps = [
  { num: '01', title: 'Regístrate', text: 'Crea una cuenta gratis para acceder a todas las características.' },
  { num: '02', title: 'Crea una composición', text: 'Ponle título, tonalidad y tempo, y elige qué secciones vas a usar.' },
  { num: '03', title: 'Ponle música', text: 'Agrega las letras, los acordes y las tablaturas.' },
  { num: '04', title: 'Finaliza', text: 'Deja tu composición guardada y compártela con los demás.' },
]
</script>

<template>
  <section class="er-slide" aria-label="Cómo funciona">
    <div class="er-wrap-full">
      <div class="er-steps-header">
        <div class="er-label">// cómo funciona</div>
        <h2 class="er-h2">
          De la idea al <em class="er-highlight">escenario</em>, en cuatro pasos.
        </h2>
      </div>

      <ol class="er-steps-grid">
        <li
          v-for="(st, idx) in steps"
          :key="idx"
          class="er-panel er-step-card"
        >
          <span class="er-step-num">{{ st.num }}</span>
          <span class="er-step-spacer" />
          <span class="er-step-title">{{ st.title }}</span>
          <span class="er-step-desc">{{ st.text }}</span>
        </li>
      </ol>

      <div class="er-steps-actions">
        <a
          :href="registerUrl"
          class="er-btn er-btn--primary er-btn-hero-primary"
        >
          Empieza gratis
        </a>
        <button
          type="button"
          class="er-btn er-btn--ghost er-btn-hero-quiet"
          @click="$emit('go-pricing')"
        >
          Ver los planes
        </button>
      </div>
    </div>
  </section>
</template>
