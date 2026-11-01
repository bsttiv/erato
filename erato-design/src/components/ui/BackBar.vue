<script setup>
import Wordmark from './Wordmark.vue'

defineProps({
  to: { type: String, default: '/composiciones' },
  label: { type: String, default: 'Composiciones' },
})
</script>

<template>
  <header class="flex items-center justify-between gap-3 bg-[#17110d] px-4 py-3 sm:px-8">
    <router-link :to="to" class="inline-flex min-h-[44px] items-center gap-2.5 text-base text-ink no-underline hover:text-brass">
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M11 3 L5 9 L11 15" fill="none" stroke="currentColor" stroke-width="2"></path></svg>{{ label }}
    </router-link>
    <Wordmark to="/composiciones" size="text-[26px]"></Wordmark>
  </header>
</template>
