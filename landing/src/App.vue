<script setup lang="ts">
import { computed } from 'vue'
import { ErBrand } from '@ds-vue'
import { useSlideNav } from './composables/useSlideNav'
import { getLoginUrl, getRegisterUrl } from './config'
import LandingFooter from './components/LandingFooter.vue'
import SlideInicio from './slides/SlideInicio.vue'
import SlideEscribir from './slides/SlideEscribir.vue'
import SlideLeer from './slides/SlideLeer.vue'
import SlideEscuchar from './slides/SlideEscuchar.vue'
import SlideColaborar from './slides/SlideColaborar.vue'
import SlideComoFunciona from './slides/SlideComoFunciona.vue'
import SlidePrecios from './slides/SlidePrecios.vue'

const { activeIndex, prefersReducedMotion, goTo, next, prev, counter } = useSlideNav()

const loginUrl = getLoginUrl()
const registerUrl = getRegisterUrl()

const sectionLabels = [
  'Inicio',
  'Escribir',
  'Leer',
  'Escuchar',
  'Colaborar',
  'Cómo funciona',
  'Precios',
]

const headerNavLabels = sectionLabels.slice(1)

const currentSlideComponent = computed(() => {
  switch (activeIndex.value) {
    case 0:
      return SlideInicio
    case 1:
      return SlideEscribir
    case 2:
      return SlideLeer
    case 3:
      return SlideEscuchar
    case 4:
      return SlideColaborar
    case 5:
      return SlideComoFunciona
    case 6:
      return SlidePrecios
    default:
      return null
  }
})
</script>

<template>
  <div class="er-landing-root" :class="{ 'reduced-motion': prefersReducedMotion }">
    <header class="er-landing-header">
      <button
        type="button"
        class="er-brand-btn"
        aria-label="Erato, ir al inicio"
        @click="goTo(0)"
      >
        <ErBrand />
      </button>

      <nav class="er-topnav" aria-label="Secciones">
        <button
          v-for="(label, i) in headerNavLabels"
          :key="i"
          type="button"
          class="er-navlink"
          :aria-current="activeIndex === i + 1 ? 'true' : undefined"
          @click="goTo(i + 1)"
        >
          {{ label }}
        </button>
      </nav>

      <div class="er-landing-header-actions">
        <a
          :href="loginUrl"
          class="er-btn er-btn--ghost er-btn--sm"
        >
          Iniciar sesión
        </a>
        <a
          :href="registerUrl"
          class="er-btn er-btn--primary er-btn--sm"
        >
          Empieza gratis
        </a>
      </div>
    </header>

    <main class="er-landing-main">
      <component
        :is="currentSlideComponent"
        v-if="currentSlideComponent"
        :key="activeIndex"
        :class="{ 'er-slide--reduced-motion': prefersReducedMotion }"
        @go-features="goTo(1)"
        @go-pricing="goTo(6)"
      />

      <div class="er-dots">
        <button
          v-for="(label, i) in sectionLabels"
          :key="i"
          type="button"
          class="er-dot"
          :aria-label="label"
          :aria-current="activeIndex === i ? 'true' : undefined"
          @click="goTo(i)"
        >
          <span>{{ label }}</span>
          <i />
        </button>
      </div>
    </main>

    <LandingFooter
      :active-index="activeIndex"
      :total-slides="sectionLabels.length"
      :counter="counter"
      @prev="prev"
      @next="next"
    />
  </div>
</template>
