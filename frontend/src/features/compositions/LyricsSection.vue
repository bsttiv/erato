<template>
  <section class="er-section" id="sec-lyrics">
    <div v-if="editable" class="er-section-head">
      <span />
      <div class="er-comp-tags">
        <ErButton
          size="sm"
          variant="ghost"
          data-test="edit-lyrics-text-btn"
          @click="toggleMode('text')"
        >
          {{ mode === 'text' ? 'Ver letra' : 'Editar letra' }}
        </ErButton>
        <ErButton
          size="sm"
          variant="ghost"
          data-test="toggle-lyrics-edit-btn"
          @click="toggleMode('chords')"
        >
          {{ mode === 'chords' ? 'Ver letra' : 'Editar acordes' }}
        </ErButton>
      </div>
    </div>

    <textarea
      v-if="mode === 'text' && editable"
      class="er-textarea"
      aria-label="Letra"
      data-test="lyrics-textarea"
      placeholder="Escribe la letra. Usa [Am7] antes de la sílaba para un acorde y # Coro para un rótulo."
      :value="lyrics"
      @input="onTextInput"
    />
    <ErLyricsChordEditor
      v-else-if="mode === 'chords' && editable"
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

type Mode = 'view' | 'text' | 'chords'
const mode = ref<Mode>('view')

function toggleMode(target: 'text' | 'chords') {
  mode.value = mode.value === target ? 'view' : target
}

function onTextInput(event: Event) {
  onLyricsUpdate((event.target as HTMLTextAreaElement).value)
}

function onLyricsUpdate(val: string) {
  emit('update:lyrics', val)
  emit('update:modelValue', val)
  emit('change', val)
}
</script>
