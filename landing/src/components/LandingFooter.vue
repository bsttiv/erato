<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  activeIndex: number
  totalSlides: number
  counter: string
}>()

const emit = defineEmits<{
  (e: 'prev'): void
  (e: 'next'): void
}>()

const isFirst = computed(() => props.activeIndex <= 0)
const isLast = computed(() => props.activeIndex >= props.totalSlides - 1)
</script>

<template>
  <footer class="er-foot">
    <span>© 2026 Bastián Valencia</span>
    <a
      href="https://github.com/bsttiv/erato"
      target="_blank"
      rel="noopener noreferrer"
      class="er-foot-link"
    >
      GitHub
    </a>
    <a
      href="#privacidad"
      class="er-foot-link"
    >
      Política de privacidad
    </a>
    <a
      href="#terminos"
      class="er-foot-link"
    >
      Términos de servicio
    </a>
    <span class="er-foot-spacer" />
    <span class="er-foot-counter">{{ counter }}</span>
    <button
      type="button"
      class="er-arrow"
      aria-label="Sección anterior"
      :disabled="isFirst"
      :class="{ 'er-arrow--disabled': isFirst }"
      @click="emit('prev')"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M12.5 10L8 5.5 3.5 10" />
      </svg>
    </button>
    <button
      type="button"
      class="er-arrow"
      aria-label="Sección siguiente"
      :disabled="isLast"
      :class="{ 'er-arrow--disabled': isLast }"
      @click="emit('next')"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M3.5 6L8 10.5 12.5 6" />
      </svg>
    </button>
  </footer>
</template>
