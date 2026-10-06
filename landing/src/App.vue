<script setup lang="ts">
import { computed } from 'vue'
import { ErBrand } from '@ds-vue'
import { useSlideNav } from './composables/useSlideNav'
import SlideInicio from './slides/SlideInicio.vue'
import SlideEscribir from './slides/SlideEscribir.vue'
import SlideLeer from './slides/SlideLeer.vue'
import SlideEscuchar from './slides/SlideEscuchar.vue'

const { activeIndex, prefersReducedMotion, goTo } = useSlideNav()

const sectionLabels = [
  'Inicio',
  'Escribir',
  'Leer',
  'Escuchar',
  'Colaborar',
  'Cómo funciona',
  'Precios',
]

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
          v-for="(label, i) in sectionLabels"
          :key="i"
          type="button"
          class="er-navlink"
          :aria-current="activeIndex === i ? 'true' : undefined"
          @click="goTo(i)"
        >
          {{ label }}
        </button>
      </nav>

      <div class="er-landing-header-actions" />
    </header>

    <main class="er-landing-main">
      <component
        :is="currentSlideComponent"
        v-if="currentSlideComponent"
        :key="activeIndex"
        :class="{ 'er-slide--reduced-motion': prefersReducedMotion }"
        @go-features="goTo(1)"
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
  </div>
</template>
