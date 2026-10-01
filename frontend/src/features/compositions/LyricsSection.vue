<template>
  <section class="er-section" id="sec-lyrics">
    <div v-if="editable" class="er-section-head">
      <span />
      <ErButton
        size="sm"
        variant="ghost"
        data-test="toggle-lyrics-edit-btn"
        @click="isEditing = !isEditing"
      >
        {{ isEditing ? 'Ver letra' : 'Editar acordes' }}
      </ErButton>
    </div>

    <ErLyricsChordEditor
      v-if="isEditing && editable"
      :lyrics="lyrics"
      :chords="chords"
      @update:lyrics="onLyricsUpdate"
    />
    <ErLyricsViewer
      v-else
      :lyrics="lyrics"
      :title="title"
    />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ErButton from '@/design-system/components/ErButton.vue'
import ErLyricsViewer from '@/design-system/components/ErLyricsViewer.vue'
import ErLyricsChordEditor from '@/design-system/components/ErLyricsChordEditor.vue'

withDefaults(
  defineProps<{
    lyrics?: string
    title?: string
    chords?: string[] | { entries?: Array<{ name: string }> }
    editable?: boolean
  }>(),
  {
    lyrics: '',
    title: 'Letra',
    chords: () => [],
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'update:lyrics', val: string): void
  (e: 'update:modelValue', val: string): void
  (e: 'change', val: string): void
}>()

const isEditing = ref(false)

function onLyricsUpdate(val: string) {
  emit('update:lyrics', val)
  emit('update:modelValue', val)
  emit('change', val)
}
</script>
