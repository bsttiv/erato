<script setup>
// Marca de Erato: una lira (atributo de la musa) dentro de la luz ámbar de la lámpara.
// Es el mismo dibujo que public/favicon.svg.
defineProps({
  size: { type: String, default: '0.85em' },
  label: { type: String, default: '' }, // vacío = decorativo (va junto al nombre)
})
</script>

<template>
  <svg
    viewBox="0 0 32 32"
    :width="size"
    :height="size"
    class="shrink-0"
    :role="label ? 'img' : null"
    :aria-label="label || null"
    :aria-hidden="label ? null : 'true'"
  >
    <circle cx="16" cy="16" r="16" fill="#f0a43a"></circle>
    <g fill="none" stroke="#1a1108" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12.4 20C8.4 17.4 7.6 12.4 10.2 9.4C11.3 8 11 6.6 9.2 6" stroke-width="2.2"></path>
      <path d="M19.6 20C23.6 17.4 24.4 12.4 21.8 9.4C20.7 8 21 6.6 22.8 6" stroke-width="2.2"></path>
      <path d="M10.4 10.2H21.6" stroke-width="1.9"></path>
      <path d="M14 10.2V20M16 10.2V20M18 10.2V20" stroke-width="1.2"></path>
    </g>
    <path d="M11 19.4H21C20.6 23.6 18.6 25.6 16 25.6S11.4 23.6 11 19.4Z" fill="#1a1108"></path>
  </svg>
</template>
