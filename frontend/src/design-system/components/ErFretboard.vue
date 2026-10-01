<template>
  <svg
    class="er-fretboard-svg"
    :width="W"
    :height="H"
    :viewBox="`0 0 ${W} ${H}`"
    role="img"
    aria-label="Diagrama de guitarra"
  >
    <!-- Strings (horizontal) -->
    <line
      v-for="r in 6"
      :key="`str-${r - 1}`"
      class="er-fb-string"
      :x1="X0"
      :x2="X0 + COLS * DX"
      :y1="Y0 + (r - 1) * DY"
      :y2="Y0 + (r - 1) * DY"
    />

    <!-- Nut / Frets (vertical) -->
    <template v-if="base === 1">
      <line
        class="er-fb-nut"
        :x1="X0"
        :x2="X0"
        :y1="Y0 - 1"
        :y2="Y0 + 5 * DY + 1"
      />
      <line
        v-for="col in COLS"
        :key="`fret-${col}`"
        class="er-fb-fret"
        :x1="X0 + col * DX"
        :x2="X0 + col * DX"
        :y1="Y0"
        :y2="Y0 + 5 * DY"
      />
    </template>
    <template v-else>
      <line
        v-for="col in COLS + 1"
        :key="`fret-${col - 1}`"
        class="er-fb-fret"
        :x1="X0 + (col - 1) * DX"
        :x2="X0 + (col - 1) * DX"
        :y1="Y0"
        :y2="Y0 + 5 * DY"
      />
    </template>

    <!-- Base fret indicator (above first fret column) -->
    <text
      v-if="base > 1"
      class="er-fb-base"
      :x="X0 + DX / 2"
      :y="Y0 - 8"
    >
      {{ base }}fr
    </text>

    <!-- Markers, dots, labels and hit areas per string -->
    <template v-for="(f, s) in frets" :key="`s-${s}`">
      <!-- Mute marker (X) -->
      <path
        v-if="f === -1"
        class="er-fb-mute"
        :d="`M${X0 - 16 - 5} ${Y0 + (5 - s) * DY - 5}l10 10M${X0 - 16 + 5} ${Y0 + (5 - s) * DY - 5}l-10 10`"
      />

      <!-- Open marker (O) -->
      <circle
        v-else-if="f === 0"
        class="er-fb-mark"
        :cx="X0 - 16"
        :cy="Y0 + (5 - s) * DY"
        :r="5.5"
        :style="isRoot(s, f) ? { stroke: 'var(--wine)' } : undefined"
      />

      <!-- Fretted dot -->
      <template v-else-if="f >= base && f < base + COLS">
        <circle
          :class="['er-fb-dot', isRoot(s, f) && 'er-fb-dot--root']"
          :cx="X0 + (f - base) * DX + DX / 2"
          :cy="Y0 + (5 - s) * DY"
          :r="8.5"
        />
        <text
          class="er-fb-dotlabel"
          :x="X0 + (f - base) * DX + DX / 2"
          :y="Y0 + (5 - s) * DY"
        >
          {{ NOTE[(TUNING[s] + f) % 12] }}
        </text>
      </template>

      <!-- Right string label / note name -->
      <text
        class="er-fb-txt"
        :x="X0 + COLS * DX + 14"
        :y="Y0 + (5 - s) * DY + 3"
      >
        {{ f >= 0 ? NOTE[(TUNING[s] + f) % 12] : STR[s] }}
      </text>

      <!-- Hit areas for editing -->
      <template v-if="editable">
        <!-- Open / mute marker hit area -->
        <rect
          class="er-fb-hit"
          :x="4"
          :y="Y0 + (5 - s) * DY - DY / 2"
          :width="X0 - 8"
          :height="DY"
          :rx="4"
          @click="emit('set', s, f === -1 ? 0 : f === 0 ? -1 : 0)"
        >
          <title>{{ STR[s] }}: al aire / apagada</title>
        </rect>

        <!-- Fret column hits -->
        <rect
          v-for="col in COLS"
          :key="`hit-${s}-${col - 1}`"
          class="er-fb-hit"
          :x="X0 + (col - 1) * DX + 1"
          :y="Y0 + (5 - s) * DY - DY / 2"
          :width="DX - 2"
          :height="DY"
          :rx="4"
          @click="emit('set', s, f === base + (col - 1) ? 0 : base + (col - 1))"
        >
          <title>{{ STR[s] }}, traste {{ base + (col - 1) }}</title>
        </rect>
      </template>
    </template>
  </svg>
</template>

<script setup lang="ts">
import { TUNING, STR } from '../core/guitar'
import { NOTE } from '../core/chords'

const props = withDefaults(
  defineProps<{
    frets: number[]
    base?: number
    root?: number
    editable?: boolean
  }>(),
  {
    base: 1,
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'set', stringIndex: number, fret: number): void
}>()

const X0 = 34
const DX = 32
const Y0 = 28
const DY = 22
const COLS = 5
const W = X0 + DX * COLS + 24
const H = Y0 + DY * 5 + 18

function isRoot(s: number, f: number): boolean {
  if (f < 0 || props.root === undefined) return false
  const midi = TUNING[s] + f
  return ((midi % 12) + 12) % 12 === props.root
}
</script>
