<script setup>
// Lámpara colgante: la única fuente de luz de cada escena.
defineProps({
  cord: { type: Number, default: 176 },
})
</script>

<template>
  <svg aria-hidden="true" width="120" :height="cord + 54" :viewBox="'0 0 120 ' + (cord + 54)" class="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2">
    <line x1="60" y1="0" x2="60" :y2="cord" stroke="#5a4632" stroke-width="2"></line>
    <path :d="'M30 ' + (cord + 40) + ' L42 ' + (cord + 2) + ' L78 ' + (cord + 2) + ' L90 ' + (cord + 40) + ' Z'" fill="#8a6a3c"></path>
    <ellipse cx="60" :cy="cord + 40" rx="30" ry="6" fill="#ffd28a"></ellipse>
  </svg>
</template>
