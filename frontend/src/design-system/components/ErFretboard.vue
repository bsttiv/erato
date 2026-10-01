<template>
  <svg
    :width="W"
    :height="H"
    :viewBox="`0 0 ${W} ${H}`"
    role="img"
    aria-label="Diagrama de guitarra"
  >
    <!-- Strings -->
    <line
      v-for="s in 6"
      :key="`s${s - 1}`"
      class="er-fb-string"
      :x1="X0 + (s - 1) * DX"
      :x2="X0 + (s - 1) * DX"
      :y1="Y0"
      :y2="Y0 + DY * ROWS"
    />

    <!-- Frets / Nut -->
    <template v-for="r in ROWS + 1" :key="`f${r - 1}`">
      <line
        v-if="r - 1 === 0 && base === 1"
        class="er-fb-nut"
        :x1="X0 - 1"
        :x2="X0 + 5 * DX + 1"
        :y1="Y0"
        :y2="Y0"
      />
      <line
        v-else
        class="er-fb-fret"
        :x1="X0"
        :x2="X0 + 5 * DX"
        :y1="Y0 + (r - 1) * DY"
        :y2="Y0 + (r - 1) * DY"
      />
    </template>

    <!-- Base fret indicator -->
    <text
      v-if="base > 1"
      class="er-fb-base"
      :x="X0 - 10"
      :y="Y0 + DY / 2"
    >
      {{ base }}fr
    </text>

    <!-- String Markers, Fretted Dots, Labels, and Hit Targets -->
    <template v-for="(f, s) in frets" :key="`str-${s}`">
      <!-- Mute marker (X) -->
      <path
        v-if="f === -1"
        class="er-fb-mute"
        :d="`M${X0 + s * DX - 5} 11l10 10M${X0 + s * DX + 5} 11l-10 10`"
      />

      <!-- Open marker (O) -->
      <circle
        v-else-if="f === 0"
        class="er-fb-mark"
        :cx="X0 + s * DX"
        :cy="16"
        :r="5.5"
        :style="isRoot(s, f) ? { stroke: 'var(--wine)' } : undefined"
      />

      <!-- Dot on fretboard -->
      <template v-else-if="f >= base && f < base + ROWS">
        <circle
          :class="['er-fb-dot', isRoot(s, f) && 'er-fb-dot--root']"
          :cx="X0 + s * DX"
          :cy="Y0 + (f - base) * DY + DY / 2"
          :r="8.5"
        />
        <text
          class="er-fb-dotlabel"
          :x="X0 + s * DX"
          :y="Y0 + (f - base) * DY + DY / 2"
        >
          {{ NOTE[(TUNING[s] + f) % 12] }}
        </text>
      </template>

      <!-- Bottom text note or string name -->
      <text
        class="er-fb-txt"
        :x="X0 + s * DX"
        :y="H - 4"
      >
        {{ f >= 0 ? NOTE[(TUNING[s] + f) % 12] : STR[s] }}
      </text>

      <!-- Hit areas for editing -->
      <template v-if="editable">
        <rect
          class="er-fb-hit"
          :x="X0 + s * DX - DX / 2"
          :y="4"
          :width="DX"
          :height="Y0 - 8"
          :rx="4"
          @click="emit('set', s, f === -1 ? 0 : f === 0 ? -1 : 0)"
        >
          <title>{{ STR[s] }}: al aire / apagada</title>
        </rect>

        <rect
          v-for="row in ROWS"
          :key="`h${s}-${row - 1}`"
          class="er-fb-hit"
          :x="X0 + s * DX - DX / 2"
          :y="Y0 + (row - 1) * DY + 1"
          :width="DX"
          :height="DY - 2"
          :rx="4"
          @click="emit('set', s, f === base + (row - 1) ? 0 : base + (row - 1))"
        >
          <title>{{ STR[s] }}, traste {{ base + (row - 1) }}</title>
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

const X0 = 30
const DX = 22
const Y0 = 34
const DY = 32
const ROWS = 5
const W = X0 + DX * 5 + 16
const H = Y0 + DY * ROWS + 24

function isRoot(s: number, f: number): boolean {
  if (f < 0 || props.root === undefined) return false
  const midi = TUNING[s] + f
  return ((midi % 12) + 12) % 12 === props.root
}
</script>
