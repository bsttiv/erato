<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status?: string | null }>()
const STATUSES: Record<string, { label: string; text: string; dot: string }> = {
  idea: { label: 'Idea', text: 'text-status-idea', dot: 'bg-status-idea' },
  in_progress: { label: 'En progreso', text: 'text-status-progress', dot: 'bg-status-progress' },
  ready: { label: 'Lista', text: 'text-status-ready', dot: 'bg-status-ready' },
}
const current = computed(() => STATUSES[props.status ?? ''])
</script>

<template>
  <span v-if="current" class="inline-flex items-center gap-2 rounded-full bg-raised px-3 py-1 text-sm font-medium" :class="current.text">
    <span class="h-2.5 w-2.5 rounded-full" :class="current.dot" aria-hidden="true"></span>{{ current.label }}
  </span>
</template>
