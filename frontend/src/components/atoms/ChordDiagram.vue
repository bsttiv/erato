<script setup lang="ts">
import { computed } from 'vue'
import { chordShape } from '../../lib/lyrics'
import type { Chord } from '../../lib/chords'

// Read-only figure with a fixed size: a chord never changes its layout.
const props = defineProps<{ chord: Chord }>()
const WIDTH = 208
const NECK_LEFT = 22
const NECK_TOP = 6
const NECK_WIDTH = WIDTH - NECK_LEFT - 2
const ROW = 14
const ROWS = Array.from({ length: 6 }, (_, index) => NECK_TOP + index * ROW)
const NECK_BOTTOM = ROWS[5]
const MIN_FRETS = 5
const WHITE_KEY = WIDTH / 14
const BLACK_KEY = 8
const KEY_HEIGHT = 72
const WHITES = [0, 2, 4, 5, 7, 9, 11]
const BLACKS: [number, number][] = [[1, 1], [3, 2], [6, 4], [8, 5], [10, 6]]
const TWO_OCTAVES = [0, 1]

const frets = computed(() => Array.from({ length: 6 }, (_, index) => {
  const position = props.chord.strings?.indexOf(index + 1) ?? -1
  return position < 0 ? -1 : props.chord.frets![position]
}))
const neck = computed(() => {
  const pressed = frets.value.filter(fret => fret > 0)
  const highest = Math.max(0, ...pressed)
  const start = highest <= MIN_FRETS ? 1 : Math.min(...pressed)
  const count = Math.max(MIN_FRETS, highest - start + 1)
  return { start, count, cell: NECK_WIDTH / count }
})
const fretLines = computed(() => Array.from({ length: neck.value.count + 1 }, (_, index) => NECK_LEFT + index * neck.value.cell))
const fretCenter = (fret: number) => NECK_LEFT + (fret - neck.value.start + 0.5) * neck.value.cell

const baseNote = computed(() => {
  const lowest = Math.min(...(props.chord.notes || []))
  return lowest - lowest % 12
})
const fitsKeyboard = computed(() => !!props.chord.notes?.length && Math.max(...props.chord.notes) - baseNote.value < 24)
const isOn = (key: number) => props.chord.notes!.includes(baseNote.value + key)
const whites = computed(() => TWO_OCTAVES.flatMap(octave => WHITES.map((semitone, index) => ({ key: octave * 12 + semitone, x: (octave * 7 + index) * WHITE_KEY }))))
const blacks = computed(() => TWO_OCTAVES.flatMap(octave => BLACKS.map(([semitone, after]) => ({ key: octave * 12 + semitone, x: (octave * 7 + after) * WHITE_KEY - BLACK_KEY / 2 }))))
</script>

<template>
  <svg v-if="chord.instrument === 'guitar'" class="block w-full" :viewBox="`0 0 ${WIDTH} ${NECK_BOTTOM + 18}`" aria-hidden="true">
    <line v-for="y in ROWS" :key="y" :x1="NECK_LEFT" :x2="WIDTH - 2" :y1="y" :y2="y" class="stroke-fret" stroke-width="1" />
    <line v-for="x in fretLines" :key="x" :x1="x" :x2="x" :y1="NECK_TOP" :y2="NECK_BOTTOM" class="stroke-fret" stroke-width="1" />
    <line v-if="neck.start === 1" :x1="NECK_LEFT" :x2="NECK_LEFT" :y1="NECK_TOP" :y2="NECK_BOTTOM" class="stroke-ivory" stroke-width="2.5" />
    <template v-for="(fret, index) in frets" :key="index">
      <g v-if="fret < 0" data-muted-string class="stroke-ivory" stroke-width="2.25" stroke-linecap="round">
        <line x1="5" x2="13" :y1="ROWS[index] - 4" :y2="ROWS[index] + 4" />
        <line x1="5" x2="13" :y1="ROWS[index] + 4" :y2="ROWS[index] - 4" />
      </g>
      <circle v-else-if="fret === 0" data-open-string cx="9" :cy="ROWS[index]" r="4" class="fill-none stroke-muted" stroke-width="1.5" />
      <circle v-else data-pressed-string :cx="fretCenter(fret)" :cy="ROWS[index]" r="4.5" class="fill-brass" />
    </template>
    <text v-for="count in neck.count" :key="count" :x="fretCenter(neck.start + count - 1)" :y="NECK_BOTTOM + 15" text-anchor="middle" font-size="10" class="fill-muted">{{ neck.start + count - 1 }}</text>
  </svg>
  <svg v-else-if="fitsKeyboard" class="block w-full" :viewBox="`0 0 ${WIDTH} ${KEY_HEIGHT}`" aria-hidden="true">
    <rect v-for="white in whites" :key="white.key" :x="white.x + 0.5" y="0" :width="WHITE_KEY - 1" :height="KEY_HEIGHT" rx="1.5" :class="isOn(white.key) ? 'fill-brass' : 'fill-ivory'" />
    <rect v-for="black in blacks" :key="black.key" :x="black.x" y="0" :width="BLACK_KEY" :height="KEY_HEIGHT * 0.62" rx="1" :class="isOn(black.key) ? 'fill-[#c47d1c]' : 'fill-[#1a120c]'" />
  </svg>
  <p v-else class="text-sm text-muted">{{ chordShape(chord) }}</p>
</template>
