<script setup>
import { computed } from 'vue'
import { GUITAR_STRINGS, NOTE_NAMES } from '../../lib/chords.js'

// Diapasón visto desde arriba: filas = cuerdas (aguda arriba), columnas = trastes.
const props = defineProps({
  frets: { type: Array, required: true }, // 6 valores: -1 silenciada, 0 al aire, n traste
  fretCount: { type: Number, default: 5 },
  showNotes: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const strings = GUITAR_STRINGS
const fretNumbers = computed(() => Array.from({ length: props.fretCount }, (_, i) => i + 1))
const gridStyle = computed(() => ({ gridTemplateColumns: '44px repeat(' + props.fretCount + ', minmax(0, 1fr))' }))

function setFret(i, value) {
  const next = props.frets.slice()
  next[i] = value
  emit('change', next)
}
const toggleOpen = (i) => setFret(i, props.frets[i] === 0 ? -1 : 0)
const pick = (i, f) => setFret(i, props.frets[i] === f ? 0 : f)
const nutText = (i) => (props.frets[i] < 0 ? '×' : props.frets[i] === 0 ? '○' : strings[i].name)
const nutLabel = (i) => 'Cuerda ' + strings[i].name + ': ' + (props.frets[i] < 0 ? 'silenciada' : props.frets[i] === 0 ? 'al aire' : 'pisada')
const noteAt = (i, f) => NOTE_NAMES[(strings[i].pc + f) % 12]
</script>

<template>
  <div>
    <div class="grid" :style="gridStyle" role="group" aria-label="Diapasón de guitarra visto desde arriba">
      <template v-for="(s, i) in strings" :key="s.name">
        <button type="button" class="nut-cell" :class="{ 'is-open': frets[i] === 0 }" :aria-label="nutLabel(i)" @click="toggleOpen(i)">{{ nutText(i) }}</button>
        <button
          v-for="f in fretNumbers"
          :key="f"
          type="button"
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
