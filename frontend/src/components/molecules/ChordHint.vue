<script setup lang="ts">
import { computed } from 'vue'
import ChordDiagram from '../atoms/ChordDiagram.vue'
import { chordLabel } from '../../lib/lyrics'
import type { Chord } from '../../lib/chords'

// Fixed so that no scrolling lyric sheet or modal clips it.
const props = defineProps<{ chord: Chord; anchor: DOMRect; chords: Chord[] }>()
const WIDTH = 232
const HEIGHT = 152
const GAP = 8

const position = computed(() => {
  const centered = props.anchor.left + props.anchor.width / 2 - WIDTH / 2
  const left = Math.max(GAP, Math.min(window.innerWidth - WIDTH - GAP, centered))
  const above = props.anchor.top > HEIGHT + GAP
  return above
    ? { left: `${left}px`, bottom: `${window.innerHeight - props.anchor.top + GAP}px` }
    : { left: `${left}px`, top: `${props.anchor.bottom + GAP}px` }
})
</script>

<template>
  <div aria-hidden="true" class="pointer-events-none fixed z-50 w-[232px] rounded bg-raised p-3" :style="position">
    <p class="font-semibold text-brass">{{ chordLabel(chord, chords) }}</p>
    <div class="mt-2"><ChordDiagram :chord="chord" /></div>
  </div>
</template>
