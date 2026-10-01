<template>
  <div class="er-chord-palette" role="toolbar" aria-label="Paleta de acordes">
    <ErButton
      v-for="chord in uniqueChords"
      :key="chord"
      size="sm"
      class="er-chord-chip"
      :variant="armedChord === chord ? 'primary' : 'quiet'"
      :aria-pressed="armedChord === chord ? 'true' : 'false'"
      :data-chord="chord"
      @click="onSelect(chord)"
      @pointerdown="onPointerDown($event, chord)"
    >
      {{ chord }}
    </ErButton>

    <ErButton
      size="sm"
      class="er-chord-chip"
      :variant="isSentinelArmed ? 'danger' : 'ghost'"
      :aria-pressed="isSentinelArmed ? 'true' : 'false'"
      data-test="sentinel-remove-chord"
      :data-chord="''"
      @click="onSelect(SENTINEL_REMOVE)"
      @pointerdown="onPointerDown($event, SENTINEL_REMOVE)"
    >
      ✕ quitar
    </ErButton>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ErButton from './ErButton.vue'
import { SENTINEL_REMOVE } from '../core/lyrics'

const props = defineProps<{
  chords: string[] | { entries?: Array<{ name: string }> }
  armedChord?: string | null
}>()

const emit = defineEmits<{
  (e: 'arm', chord: string): void
  (e: 'drag-start', event: PointerEvent, chord: string): void
}>()

const uniqueChords = computed(() => {
  let list: string[] = []
  if (Array.isArray(props.chords)) {
    list = props.chords
  } else if (props.chords && Array.isArray(props.chords.entries)) {
    list = props.chords.entries.map((e) => e.name)
  }
  const seen = new Set<string>()
  const result: string[] = []
  for (const c of list) {
    if (c && !seen.has(c)) {
      seen.add(c)
      result.push(c)
    }
  }
  return result
})

const isSentinelArmed = computed(() => {
  return props.armedChord === SENTINEL_REMOVE || props.armedChord === ''
})

function onSelect(chord: string) {
  emit('arm', chord)
}

function onPointerDown(e: PointerEvent, chord: string) {
  emit('drag-start', e, chord)
}
</script>
