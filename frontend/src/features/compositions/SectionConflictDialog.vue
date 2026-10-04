<template>
  <AppModal
    :open="open && !!conflict"
    :title="title"
    @close="emit('close')"
  >
    <div class="er-conflict-dialog">
      <p class="er-conflict-msg">
        Otra persona guardó cambios en esta sección mientras la editabas.
        <span v-if="conflict?.author?.display_name">
          Guardado por {{ conflict.author.display_name }}.
        </span>
      </p>
      <p class="er-conflict-hint">
        Puedes cargar la versión remota y descartar tus cambios locales en esta sección, o sobrescribirla con tu versión.
      </p>
    </div>

    <template #footer>
      <div class="er-conflict-actions">
        <button
          type="button"
          class="er-btn"
          @click="emit('loadSaved')"
        >
          Cargar la versión guardada
        </button>
        <button
          type="button"
          class="er-btn er-btn--primary"
          @click="emit('overwrite')"
        >
          Sobrescribir con la mía
        </button>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppModal from '@/shared/AppModal.vue'
import type { SectionConflictBody } from '@/api/compositions'

export interface SectionConflict extends Omit<SectionConflictBody, 'error'> {
  error?: 'section_conflict'
}

const props = defineProps<{
  open: boolean
  conflict: SectionConflict | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'loadSaved'): void
  (e: 'overwrite'): void
}>()

const sectionLabels: Record<string, string> = {
  lyrics: 'letra',
  chords: 'acordes',
  tablature: 'tablatura',
}

const title = computed(() => {
  if (!props.conflict) return 'Conflicto de edición'
  const name = sectionLabels[props.conflict.section] || props.conflict.section
  return `Conflicto en ${name}`
})
</script>
