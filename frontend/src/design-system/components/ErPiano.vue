<template>
  <svg
    :width="svgWidth"
    :height="WH + 2"
    :viewBox="`0 0 ${svgWidth} ${WH + 2}`"
    role="img"
    aria-label="Teclado de piano"
  >
    <!-- White keys -->
    <g v-for="w in whiteKeys" :key="`w${w.m}`">
      <rect
        :class="['er-pk-white', w.act && 'is-on', w.act && isRoot(w.m) && 'is-root']"
        :x="w.x + 1"
        :y="1"
        :width="WW - 2"
        :height="WH"
        :rx="4"
        @click="onToggle(w.m)"
      >
        <title>{{ NOTE[w.pc] }}</title>
      </rect>
      <text
        v-if="w.act"
        class="er-pk-lbl"
        :x="w.x + WW / 2"
        :y="WH - 10"
      >
        {{ NOTE[w.pc] }}
      </text>
      <text
        v-else-if="w.pc === 0"
        class="er-pk-c"
        :x="w.x + WW / 2"
        :y="WH - 10"
      >
        C{{ Math.floor(w.m / 12) - 1 }}
      </text>
    </g>

    <!-- Black keys -->
    <g v-for="b in blackKeys" :key="`b${b.bm}`">
      <rect
        :class="['er-pk-black', b.bact && 'is-on', b.bact && isRoot(b.bm) && 'is-root']"
        :x="b.bx"
        :y="1"
        :width="BW"
        :height="BH"
        :rx="3"
        @click="onToggle(b.bm)"
      >
        <title>{{ NOTE[b.bm % 12] }}</title>
      </rect>
      <text
        v-if="b.bact"
        class="er-pk-lbl"
        :x="b.bx + BW / 2"
        :y="BH - 8"
      >
        {{ NOTE[b.bm % 12].charAt(0) }}
      </text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WHITE, BLACK_AFTER } from '../core/piano'
import { NOTE } from '../core/chords'

const props = withDefaults(
  defineProps<{
    notes: number[]
    root?: number
    start?: number
    octaves?: number
    editable?: boolean
  }>(),
  {
    start: 48,
    octaves: 2,
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'toggle', note: number): void
}>()

const WW = 24
const WH = 112
const BW = 15
const BH = 70

function isRoot(m: number): boolean {
  if (props.root === undefined) return false
  return ((m % 12) + 12) % 12 === props.root
}

function onToggle(m: number) {
  if (props.editable) {
    emit('toggle', m)
  }
}

const keyData = computed(() => {
  const whites: Array<{ m: number; pc: number; x: number; act: boolean }> = []
  const blacks: Array<{ bm: number; bx: number; bact: boolean }> = []
  let wi = 0

  for (let o = 0; o < props.octaves; o++) {
    WHITE.forEach((pc) => {
      const m = props.start + o * 12 + pc
      const x = wi * WW
      const act = props.notes.includes(m)
      whites.push({ m, pc, x, act })

      const blackOffset = BLACK_AFTER[pc]
      if (blackOffset !== undefined) {
        const bm = props.start + o * 12 + blackOffset
        const bact = props.notes.includes(bm)
        const bx = x + WW - BW / 2
        blacks.push({ bm, bx, bact })
      }
      wi++
    })
  }

  return { whites, blacks, totalWidth: wi * WW + 2 }
})

const whiteKeys = computed(() => keyData.value.whites)
const blackKeys = computed(() => keyData.value.blacks)
const svgWidth = computed(() => keyData.value.totalWidth)
</script>
