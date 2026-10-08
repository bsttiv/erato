<template>
  <router-link :to="'/compositions/' + composition.id" class="er-card">
    <div>
      <div class="er-card-head">
        <span class="er-card-index">{{ pad2(index + 1) }}</span>
        <ErTag :tone="statusTone" dot>{{ label }}</ErTag>
      </div>

      <ErTag v-if="composition.via_band" tone="amber">Compartida con tu banda</ErTag>

      <h3 class="er-card-title">{{ composition.title }}</h3>

      <div class="er-card-chords">
        {{ chordsText }}
      </div>

      <div class="er-card-counts">
        {{ countsText }}
      </div>
    </div>

    <div class="er-card-foot">
      <span>{{ relativeTimeText }}</span>
      <span v-if="metaFootText">{{ metaFootText }}</span>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ErTag, type Tone } from '@/design-system'
import { pad2 } from '@/design-system/core/format'
import type { CompositionListItem } from '@/api/compositions'
import { statusLabel } from './status'

const props = defineProps<{
  composition: CompositionListItem
  index: number
}>()

const statusTone = computed<Tone>(() => {
  switch (props.composition.status) {
    case 'in_progress':
      return 'amber'
    case 'ready':
      return 'moss'
    case 'idea':
    default:
      return 'neutral'
  }
})

const label = computed<string>(() => statusLabel(props.composition.status))

const chordsText = computed<string>(() => {
  if (props.composition.chord_names && props.composition.chord_names.length) {
    return props.composition.chord_names.join(' · ')
  }
  return '—'
})

const countsText = computed<string>(() => {
  const c = props.composition.counts || {
    chords: 0,
    tabs: 0,
    demos: 0,
    todos_done: 0,
    todos_total: 0,
  }
  return `acordes ${c.chords} · tab ${c.tabs} · demos ${c.demos} · tareas ${c.todos_done}/${c.todos_total}`
})

const relativeTimeText = computed<string>(() => {
  if (!props.composition.updated_at) return 'editada recientemente'
  try {
    const diffMs = Date.now() - new Date(props.composition.updated_at).getTime()
    const diffSec = Math.max(0, Math.floor(diffMs / 1000))
    const diffMin = Math.floor(diffSec / 60)
    const diffHours = Math.floor(diffMin / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `editada hace ${diffDays} d`
    if (diffHours > 0) return `editada hace ${diffHours} h`
    if (diffMin > 0) return `editada hace ${diffMin} min`
    return 'editada recién'
  } catch {
    return 'editada recientemente'
  }
})

const metaFootText = computed<string | null>(() => {
  const parts: string[] = []
  if (props.composition.key) parts.push(props.composition.key)
  if (props.composition.bpm) parts.push(`${props.composition.bpm} bpm`)
  return parts.length ? parts.join(' · ') : null
})
</script>
