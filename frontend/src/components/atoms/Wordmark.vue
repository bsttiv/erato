<script setup lang="ts">
import LogoMark from './LogoMark.vue'

defineProps({
  to: { type: String, default: '/' },
  size: { type: String, default: 'text-[32px]' },
})
</script>

<template>
  <router-link :to="to" class="inline-flex items-center gap-[0.28em] font-display leading-none tracking-tight text-ink no-underline hover:text-ink" :class="size">
    <LogoMark></LogoMark>Erato
  </router-link>
</template>
