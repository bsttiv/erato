<script setup lang="ts">
import { ref } from 'vue'
import ChordHint from './ChordHint.vue'
import { chordLabel, chordShape, type SheetLine } from '../../lib/lyrics'
import type { Chord } from '../../lib/chords'
const props = withDefaults(
  defineProps<{ lines: SheetLine[]; chords?: Chord[]; showChords?: boolean; textClass?: string; chordClass?: string }>(),
  { chords: () => [], showChords: true, textClass: 'text-xl sm:text-2xl leading-snug', chordClass: 'text-[15px] sm:text-base' },
)
const hint = ref<{ chord: Chord; anchor: DOMRect } | null>(null)
const findChord = (id?: string) => props.chords.find(chord => chord.id === id)
function showHint(event: Event, id: string) {
  const chord = findChord(id)
  if (chord) hint.value = { chord, anchor: (event.currentTarget as HTMLElement).getBoundingClientRect() }
}
</script>

<template>
  <div class="overflow-x-auto">
    <template v-for="(line, i) in lines" :key="i">
      <p v-if="line.section" class="lyric-section">{{ line.section }}</p>
      <div v-else>
        <p v-if="showChords && !Array.isArray(line.chords)" class="lyric-chord" :class="chordClass">{{ line.chords }}</p>
        <div v-else-if="showChords && Array.isArray(line.chords)" class="lyric-chord relative" :class="chordClass" :style="{ minWidth: Math.max((line.text || '').length, ...line.chords.map(c => c.col + chordLabel(findChord(c.chord_id), chords).length)) + 'ch' }">
          <span aria-hidden="true">&nbsp;</span>
          <button v-for="c in line.chords" :key="c.col" type="button" class="absolute top-0 border-0 bg-transparent p-0 text-brass" :style="{ left: c.col + 'ch' }" :aria-label="chordLabel(findChord(c.chord_id), chords) + ': ' + chordShape(findChord(c.chord_id))" @mouseenter="showHint($event, c.chord_id)" @mouseleave="hint = null" @focus="showHint($event, c.chord_id)" @blur="hint = null">{{ chordLabel(findChord(c.chord_id), chords) }}</button>
        </div>
        <p class="lyric-text" :class="textClass">{{ line.text || ' ' }}</p>
      </div>
    </template>
    <Teleport to="body"><ChordHint v-if="hint" :chord="hint.chord" :anchor="hint.anchor" :chords="chords" /></Teleport>
  </div>
</template>
