<template>
  <div :class="['er-chord', 'er-panel', 'er-chord-editor-card', customClass]">
    <div class="er-chord-head er-chord-editor-head">
      <div class="er-chord-editor-title-wrap">
        <ErChordName :info="info" />
        <div class="er-chord-notes er-chord-editor-notes">
          {{ info ? info.notes.join(' · ') : 'sin notas' }}
        </div>
      </div>
      <ErSegmented
        v-if="!hideSwitch"
        :model-value="inst"
        label="Instrumento"
        :options="[
          { value: 'guitar', label: 'guitarra' },
          { value: 'piano', label: 'piano' },
        ]"
        @update:model-value="setInst"
      />
    </div>

    <div class="er-chord-body er-chord-editor-body">
      <button
        v-if="inst === 'guitar' && editable"
        type="button"
        class="er-iconbtn"
        aria-label="Bajar traste"
        :disabled="base <= 1"
        @click="base = Math.max(1, base - 1)"
      >
        <ErIcon name="left" />
      </button>

      <ErFretboard
        v-if="inst === 'guitar'"
        :frets="fr"
        :base="base"
        :root="info ? info.root : undefined"
        :editable="editable"
        @set="setString"
      />
      <ErPiano
        v-else
        :notes="keys"
        :root="info ? info.root : undefined"
        :editable="editable"
        @toggle="toggleKey"
      />

      <button
        v-if="inst === 'guitar' && editable"
        type="button"
        class="er-iconbtn"
        aria-label="Subir traste"
        :disabled="base >= 15"
        @click="base = Math.min(15, base + 1)"
      >
        <ErIcon name="right" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ErIcon from './ErIcon.vue'
import ErSegmented from './ErSegmented.vue'
import ErFretboard from './ErFretboard.vue'
import ErPiano from './ErPiano.vue'
import ErChordName from './ErChordName.vue'
import { detectChord } from '../core/chords'
import { fretsToMidi, autoBase } from '../core/guitar'

export interface ChordValue {
  instrument: 'guitar' | 'piano'
  frets: number[]
  notes: number[]
  name: string | null
}

const props = withDefaults(
  defineProps<{
    defaultFrets?: number[]
    defaultBaseFret?: number
    defaultInstrument?: 'guitar' | 'piano'
    defaultNotes?: number[]
    editable?: boolean
    hideSwitch?: boolean
    customClass?: string
  }>(),
  {
    editable: true,
    hideSwitch: false,
    defaultInstrument: 'guitar',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: ChordValue): void
  (e: 'change', value: ChordValue): void
}>()

const initFr = props.defaultFrets || [-1, 3, 2, 0, 1, 0]
const fr = ref<number[]>(initFr.slice())
const base = ref<number>(props.defaultBaseFret || autoBase(initFr))
const inst = ref<'guitar' | 'piano'>(props.defaultInstrument)
const keys = ref<number[]>(props.defaultNotes ? props.defaultNotes.slice() : fretsToMidi(initFr))

const midi = computed(() => {
  return inst.value === 'guitar' ? fretsToMidi(fr.value) : keys.value
})

const info = computed(() => {
  return detectChord(midi.value)
})

function notifyChange() {
  const payload: ChordValue = {
    instrument: inst.value,
    frets: fr.value.slice(),
    notes: midi.value.slice(),
    name: info.value ? info.value.name : null,
  }
  emit('update:modelValue', payload)
  emit('change', payload)
}

function setInst(v: string) {
  const nextInst = v as 'guitar' | 'piano'
  if (nextInst === 'piano' && inst.value === 'guitar') {
    const folded: number[] = []
    fretsToMidi(fr.value).forEach((m) => {
      let note = m
      while (note < 48) note += 12
      while (note > 71) note -= 12
      if (!folded.includes(note)) folded.push(note)
    })
    keys.value = folded.sort((a, b) => a - b)
  }
  inst.value = nextInst
  notifyChange()
}

function setString(s: number, f: number) {
  const next = fr.value.slice()
  next[s] = f
  fr.value = next
  notifyChange()
}

function toggleKey(m: number) {
  const next = keys.value.slice()
  const idx = next.indexOf(m)
  if (idx >= 0) {
    next.splice(idx, 1)
  } else {
    next.push(m)
  }
  keys.value = next.sort((a, b) => a - b)
  notifyChange()
}
</script>
