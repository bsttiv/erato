<script setup lang="ts">
import { computed } from 'vue'
import { GUITAR_STRINGS, NOTE_NAMES } from '../../lib/chords'

// Diapasón visto desde arriba: filas = cuerdas (aguda arriba), columnas = trastes.
// frets: 6 valores: -1 silenciada, 0 al aire, n traste
const props = defineProps<{ frets: number[]; fretCount?: number; showNotes?: boolean; disabled?: boolean; startFret?: number }>()
const emit = defineEmits<{ change: [next: number[]] }>()

const strings = GUITAR_STRINGS
const fretNumbers = computed(() => Array.from({ length: props.fretCount ?? 5 }, (_, i) => i + (props.startFret ?? 1)).filter((fret) => fret <= 24))
const gridStyle = computed(() => ({ gridTemplateColumns: '44px repeat(' + fretNumbers.value.length + ', minmax(0, 1fr))' }))

function setFret(i: number, value: number) {
  if (props.disabled) return
  const next = props.frets.slice()
  next[i] = value
  emit('change', next)
}
const toggleOpen = (i: number) => setFret(i, props.frets[i] === 0 ? -1 : 0)
const pick = (i: number, f: number) => setFret(i, props.frets[i] === f ? 0 : f)
const nutText = (i: number) => (props.frets[i] < 0 ? '×' : props.frets[i] === 0 ? '○' : strings[i].name)
const nutLabel = (i: number) => 'Cuerda ' + strings[i].name + ': ' + (props.frets[i] < 0 ? 'silenciada' : props.frets[i] === 0 ? 'al aire' : 'pisada')
const noteAt = (i: number, f: number) => NOTE_NAMES[(strings[i].pc + f) % 12]
</script>

<template>
  <div>
    <div class="grid" :style="gridStyle" role="group" aria-label="Diapasón de guitarra visto desde arriba">
      <template v-for="(s, i) in strings" :key="s.name">
        <button type="button" :disabled="disabled" class="nut-cell" :class="{ 'is-open': frets[i] === 0 }" :aria-label="nutLabel(i)" @click="toggleOpen(i)">{{ nutText(i) }}</button>
        <button
          v-for="f in fretNumbers"
          :key="f"
          type="button"
          :disabled="disabled"
          class="fret-cell"
          :class="{ 'is-on': frets[i] === f }"
          :aria-pressed="frets[i] === f ? 'true' : 'false'"
          :aria-label="'Cuerda ' + s.name + ', traste ' + f"
          @click="pick(i, f)"
        >
          <span class="fret-dot">{{ showNotes ? noteAt(i, f) : '' }}</span>
        </button>
      </template>
    </div>
    <div class="mt-2 grid text-center text-[13px] text-muted" :style="gridStyle" aria-hidden="true">
      <span></span>
      <span v-for="f in fretNumbers" :key="f">{{ f }}</span>
    </div>
  </div>
</template>
