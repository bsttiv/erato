<script setup lang="ts">
import Wordmark from '../atoms/Wordmark.vue'
</script>

<template>
  <footer class="bg-ground">
    <div class="page-x flex flex-col gap-6 py-10 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-wrap items-baseline gap-x-5 gap-y-2">
        <Wordmark size="text-[28px]"></Wordmark>
        <p class="text-[15px] text-muted">© 2026 <a href="https://bsttiv.github.io" class="text-muted underline underline-offset-4 hover:text-ink">Bastián Valencia</a></p>
      </div>
      <nav class="flex flex-wrap gap-x-6 gap-y-1" aria-label="Pie de página">
        <a href="https://github.com/bsttiv/erato" class="py-2 text-[15px] text-ink no-underline hover:text-brass">GitHub</a>
        <router-link to="/legal#privacidad" class="py-2 text-[15px] text-ink no-underline hover:text-brass">Política de privacidad</router-link>
        <router-link to="/legal#terminos" class="py-2 text-[15px] text-ink no-underline hover:text-brass">Términos de servicio</router-link>
      </nav>
    </div>
  </footer>
</template>
