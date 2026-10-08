<template>
  <p role="status" class="er-hint">
    <ErTag tone="amber">Banda inactiva</ErTag>
    {{ owner
      ? 'La banda de esta composición está inactiva. Puedes seguir editando porque la composición es tuya.'
      : 'La banda de esta composición está inactiva. Por ahora solo puedes verla; el contenido sigue guardado.' }}
  </p>
</template>

<script setup lang="ts">
import { ErTag } from '@/design-system'

defineProps<{ owner: boolean }>()
</script>
