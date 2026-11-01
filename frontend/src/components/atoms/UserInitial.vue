<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ displayName?: string; username?: string }>()
const initial = computed(() => {
  const name = props.displayName?.trim() || props.username?.trim() || '?'
  return Array.from(name)[0].toLocaleUpperCase('es')
})
</script>

<template>
  <span class="avatar h-[30px] w-[30px] bg-brass text-xs" aria-hidden="true">{{ initial }}</span>
</template>
