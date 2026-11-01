<script setup>
import Wordmark from '../ui/Wordmark.vue'
</script>

<template>
  <footer class="bg-ground">
    <div class="page-x flex flex-col gap-6 py-10 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-wrap items-baseline gap-x-5 gap-y-2">
        <Wordmark size="text-[28px]"></Wordmark>
        <p class="text-[15px] text-muted">© 2026 Bastián Valencia</p>
      </div>
      <nav class="flex flex-wrap gap-x-6 gap-y-1" aria-label="Pie de página">
        <a href="https://github.com" class="py-2 text-[15px] text-ink no-underline hover:text-brass">GitHub</a>
        <a href="#privacidad" class="py-2 text-[15px] text-ink no-underline hover:text-brass">Política de privacidad</a>
        <a href="#terminos" class="py-2 text-[15px] text-ink no-underline hover:text-brass">Términos de servicio</a>
      </nav>
    </div>
  </footer>
</template>
