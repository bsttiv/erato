<template>
  <section id="sec-chords" class="er-section">
    <div class="er-section-head">
      <h2 class="er-label">
        // ACORDES DE LA CANCIÓN
      </h2>

      <div class="er-field-row">
        <ErSegmented
          v-if="editable"
          :model-value="currentInstrument"
          label="Instrumento"
          :options="[
            { value: 'guitar', label: 'guitarra' },
            { value: 'piano', label: 'piano' },
          ]"
          @update:model-value="onInstrumentChange"
        />
        <ErButton
          v-if="editable"
          variant="primary"
          icon="plus"
          data-test="add-chord-btn"
          @click="addChord"
        >
          Agregar acorde
        </ErButton>
      </div>
    </div>

    <div v-if="entries.length" class="er-chord-palette">
      <span
        v-for="(entry, idx) in entries"
        :key="idx"
        class="er-chord-chip"
      >
        {{ entry.name }}
      </span>
    </div>

    <div
      v-if="entries.length"
      class="er-chord-carousel"
      role="group"
      aria-roledescription="carrusel"
      aria-label="Acordes"
    >
      <div class="er-chord-nav">
        <button
          type="button"
          class="er-btn er-btn--ghost"
          data-test="chord-prev"
          aria-label="Acorde anterior"
          @click="scrollPrev"
        >
          <ErIcon name="left" />
        </button>
        <button
          type="button"
          class="er-btn er-btn--ghost"
          data-test="chord-next"
          aria-label="Acorde siguiente"
          @click="scrollNext"
        >
          <ErIcon name="right" />
        </button>
      </div>

      <div
        ref="trackRef"
        class="er-chord-grid"
        tabindex="0"
      >
        <div
          v-for="(entry, idx) in entries"
          :key="idx"
          class="er-field"
        >
          <ErChordEditor
            :default-frets="entry.notes"
            :default-instrument="currentInstrument"
            :editable="editable"
            hide-switch
            @change="onChordChange(idx, $event)"
          />
          <div v-if="editable" class="er-field-row">
            <ErButton
              variant="ghost"
              data-test="remove-chord-btn"
              @click="removeChord(idx)"
            >
              Eliminar
            </ErButton>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="er-empty">
      No hay acordes agregados a esta canción.
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ErButton, ErSegmented, ErChordEditor, ErIcon, type ChordValue } from '@/design-system'
import type { ChordsSection, ChordEntry } from '@/api/compositions'

const props = withDefaults(
  defineProps<{
    chords?: ChordsSection | null
    editable?: boolean
  }>(),
  {
    chords: null,
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'update:chords', value: ChordsSection): void
}>()

const trackRef = ref<HTMLElement | null>(null)

function getScrollBehavior(): ScrollBehavior {
  if (typeof window !== 'undefined' && window.matchMedia) {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return 'auto'
  }
  return 'smooth'
}

function scrollPrev() {
  if (!trackRef.value) return
  const w = trackRef.value.clientWidth || 300
  trackRef.value.scrollBy({ left: -w, behavior: getScrollBehavior() })
}

function scrollNext() {
  if (!trackRef.value) return
  const w = trackRef.value.clientWidth || 300
  trackRef.value.scrollBy({ left: w, behavior: getScrollBehavior() })
}

const currentInstrument = ref<'guitar' | 'piano'>(
  (props.chords?.instrument as 'guitar' | 'piano') || 'guitar'
)

const entries = computed<ChordEntry[]>(() => {
  return props.chords?.entries ? [...props.chords.entries] : []
})

watch(
  () => props.chords?.instrument,
  (newInst) => {
    if (newInst === 'guitar' || newInst === 'piano') {
      currentInstrument.value = newInst
    }
  }
)

function onInstrumentChange(inst: string) {
  const newInst = inst as 'guitar' | 'piano'
  currentInstrument.value = newInst
  emit('update:chords', {
    instrument: newInst,
    entries: [...entries.value],
  })
}

function addChord() {
  const nextBar = entries.value.length + 1
  const defaultNotes = [-1, 3, 2, 0, 1, 0] // C major
  const newEntries: ChordEntry[] = [
    ...entries.value,
    { bar: nextBar, notes: defaultNotes, name: 'C' },
  ]
  emit('update:chords', {
    instrument: currentInstrument.value,
    entries: newEntries,
  })
}

function removeChord(idx: number) {
  const newEntries = entries.value.filter((_, i) => i !== idx)
  emit('update:chords', {
    instrument: currentInstrument.value,
    entries: newEntries,
  })
}

function onChordChange(idx: number, val: ChordValue) {
  const updatedEntries = [...entries.value]
  updatedEntries[idx] = {
    bar: updatedEntries[idx]?.bar || idx + 1,
    notes: val.frets.slice(),
    name: val.name || 'Desconocido',
  }
  emit('update:chords', {
    instrument: currentInstrument.value,
    entries: updatedEntries,
  })
}
</script>
