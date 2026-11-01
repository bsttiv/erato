<script setup lang="ts">
import { useCompositionPath } from '../../api/compositionPath'
const compositionPath = useCompositionPath()
defineProps({
  isPublic: { type: Boolean, default: true },
  url: { type: String, default: '' },
})
</script>

<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded bg-raised px-5 py-4 text-base">
    <span class="chip" :class="isPublic ? 'chip-on' : ''">{{ isPublic ? 'Pública' : 'Privada' }}</span>
    <span class="break-all font-medium">{{ url || compositionPath }}</span>
    <span class="text-muted">{{ isPublic ? 'cualquiera con el enlace puede verla' : 'solo las personas invitadas' }}</span>
  </div>
</template>
