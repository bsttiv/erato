<template>
  <div v-if="!info || !info.name" class="er-chord-name er-chord-empty">
    {{ info ? '¿?' : '—' }}
  </div>
  <div v-else class="er-chord-name" aria-live="polite">
    {{ baseNote }}<sup v-if="quality">{{ quality }}</sup><small v-if="slash">{{ slash }}</small>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NOTE, type ChordInfo } from '../core/chords'

const props = defineProps<{
  info: ChordInfo | null
}>()

const baseNote = computed(() => {
  if (!props.info || !props.info.name) return ''
  return NOTE[props.info.root]
})

const rest = computed(() => {
  if (!props.info || !props.info.name) return ''
  return props.info.name.slice(baseNote.value.length)
})

const slash = computed(() => {
  const r = rest.value
  const idx = r.indexOf('/')
  return idx >= 0 ? r.slice(idx) : ''
})

const quality = computed(() => {
  const r = rest.value
  const idx = r.indexOf('/')
  return idx >= 0 ? r.slice(0, idx) : r
})
</script>
