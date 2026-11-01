<script setup lang="ts">
import type { RevisionItem } from '../../stores/song'
defineProps<{ items: RevisionItem[]; canRestore?: boolean; busy?: boolean }>()
defineEmits<{ read: [item: RevisionItem]; restore: [item: RevisionItem] }>()
</script>

<template>
  <ul class="grid list-none gap-2 p-0">
    <li v-for="(h, i) in items" :key="h.version ? `${h.section}-${h.version}` : i" class="grid grid-cols-1 gap-x-4 gap-y-1 rounded bg-surface px-5 py-4 text-base sm:grid-cols-[minmax(0,1fr)_11rem] sm:text-[17px]">
      <span><b class="font-semibold">{{ h.author?.display_name || h.author?.username || h.who || 'Autor no disponible' }}</b> <template v-if="h.summary">{{ h.summary }}</template><template v-else-if="h.version">· Versión {{ h.version }}</template><slot v-else name="description" :item="h">{{ h.what }}</slot></span>
      <span class="whitespace-nowrap text-muted sm:text-right">{{ h.created_at ? new Date(h.created_at).toLocaleString('es') : h.when }}</span>
      <div v-if="h.version" class="mt-2 flex gap-2 sm:col-span-2"><button type="button" class="btn-ghost btn-sm" :disabled="busy" @click="$emit('read', h)">Ver</button><button v-if="canRestore" type="button" class="btn-ghost btn-sm" :disabled="busy" @click="$emit('restore', h)">Restaurar</button></div>
    </li>
  </ul>
</template>
