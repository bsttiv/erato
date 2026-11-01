<script setup lang="ts">
import { formatTime } from '../../data/sample'
import type { Demo } from '../../api/demos'

// Lista de tomas de una composición; la elegida suena en el reproductor.
defineProps<{ demos: Demo[]; selected: string; commentCounts?: Record<string, number> }>()
const emit = defineEmits<{ select: [id: string] }>()
const day = (value?: string) => (value ? new Date(value).toLocaleDateString('es', { day: 'numeric', month: 'short' }) : '')
</script>

<template>
  <div class="mt-4 grid gap-1">
    <button
      v-for="d in demos"
      :key="d.id"
      type="button"
      class="flex w-full cursor-pointer items-center justify-between gap-3 rounded border-0 p-4 text-left text-ink transition-colors hover:bg-surface"
      :class="d.id === selected ? 'bg-raised' : 'bg-transparent'"
      :aria-pressed="d.id === selected ? 'true' : 'false'"
      @click="emit('select', d.id)"
    >
      <span class="min-w-0">
        <span class="block truncate text-[17px] font-medium">{{ d.title }}</span>
        <span class="mt-1 block text-sm text-muted">{{ day(d.uploaded_at) }}<template v-if="d.author"> · subida por {{ d.author.display_name }}</template><template v-if="commentCounts && d.id in commentCounts"> · {{ commentCounts[d.id] }} coment.</template></span>
      </span>
      <span class="text-[15px] tabular-nums">{{ formatTime(d.duration_s) }}</span>
    </button>
  </div>
</template>
