<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import ChordHint from './ChordHint.vue'
import { chordLabel, chordShape, dropColumn, placeChord, type Lyrics } from '../../lib/lyrics'
import type { Chord } from '../../lib/chords'

const props = defineProps<{ lyrics: Lyrics | null; chords: Chord[] }>()
const emit = defineEmits<{ 'update:lyrics': [lyrics: Lyrics] }>()

interface Drag {
  chordId: string
  label: string
  x: number
  y: number
  startX: number
  startY: number
  from?: { line: number; col: number }
}
const CLICK_DISTANCE = 4
const drag = ref<Drag | null>(null)
const hint = ref<{ chord: Chord; anchor: DOMRect } | null>(null)
const selectedForm = reactive<Record<string, number>>({})
const groups = computed(() => {
  const byName = new Map<string, Chord[]>()
  for (const chord of props.chords) byName.set(chord.name, [...(byName.get(chord.name) || []), chord])
  return [...byName].map(([name, forms]) => ({ name, forms }))
})
const formIndex = (name: string, count: number) => (selectedForm[name] ?? 0) % count
const lineWidth = (text: string, cols: number[]) => Math.max(text.length, ...cols.map(col => col + 8), 40)
const findChord = (id: string) => props.chords.find(chord => chord.id === id)

function stepForm(event: Event, name: string, count: number, delta: number) {
  selectedForm[name] = (formIndex(name, count) + delta + count) % count
  const chip = (event.currentTarget as HTMLElement).parentElement!.querySelector<HTMLElement>('[data-chord-chip]')!
  showHint(chip, groups.value.find(group => group.name === name)!.forms[selectedForm[name]])
}
function showHint(element: HTMLElement, chord?: Chord) {
  if (chord && !drag.value) hint.value = { chord, anchor: element.getBoundingClientRect() }
}
function move(event: PointerEvent) {
  if (!drag.value) return
  drag.value.x = event.clientX
  drag.value.y = event.clientY
}
function stop() {
  drag.value = null
  window.removeEventListener('pointermove', move)
  window.removeEventListener('pointerup', drop)
  window.removeEventListener('pointercancel', stop)
}
function drop(event: PointerEvent) {
  const active = drag.value
  stop()
  if (!active) return
  // A click on a chord only shows its shape; it must not move it.
  if (Math.hypot(event.clientX - active.startX, event.clientY - active.startY) < CLICK_DISTANCE) return
  const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-lyric-line]')
  if (!target && !active.from) return
  let next = props.lyrics
  if (active.from) next = placeChord(next, active.from.line, active.from.col)
  if (target) {
    const unit = target.querySelector<HTMLElement>('[data-char-unit]')!
    const left = unit.parentElement!.getBoundingClientRect().left
    const col = dropColumn(event.clientX, left, unit.getBoundingClientRect().width)
    next = placeChord(next, Number(target.dataset.lyricLine), col, active.chordId)
  }
  emit('update:lyrics', next!)
}
function start(event: PointerEvent, chord: Chord, from?: Drag['from']) {
  if (event.button !== 0) return
  event.preventDefault()
  hint.value = null
  const { clientX: x, clientY: y } = event
  drag.value = { chordId: chord.id!, label: chordLabel(chord, props.chords), x, y, startX: x, startY: y, from }
  window.addEventListener('pointermove', move)
  window.addEventListener('pointerup', drop)
  window.addEventListener('pointercancel', stop)
}
function remove(line: number, col: number) {
  hint.value = null
  emit('update:lyrics', placeChord(props.lyrics, line, col))
}
onBeforeUnmount(stop)
</script>

<template>
  <div>
    <p class="text-sm text-muted">Arrastra un acorde sobre una línea. Pasa el cursor para ver su forma.</p>
    <div class="mt-2 flex flex-wrap gap-2">
      <div v-for="group in groups" :key="group.name" class="flex items-center rounded bg-raised" @pointerleave="hint = null">
        <button v-if="group.forms.length > 1" type="button" class="min-h-[40px] px-2 text-muted hover:text-brass" :aria-label="'Forma anterior de ' + group.name" @click="stepForm($event, group.name, group.forms.length, -1)" @blur="hint = null">‹</button>
        <span
          data-chord-chip
          tabindex="0"
          class="cursor-grab touch-none select-none px-3 py-1.5 font-semibold text-brass"
          :aria-label="chordLabel(group.forms[formIndex(group.name, group.forms.length)], chords) + ': ' + chordShape(group.forms[formIndex(group.name, group.forms.length)])"
          @pointerdown="start($event, group.forms[formIndex(group.name, group.forms.length)])"
          @pointerenter="showHint($event.currentTarget as HTMLElement, group.forms[formIndex(group.name, group.forms.length)])"
          @pointerleave="hint = null"
          @focus="showHint($event.currentTarget as HTMLElement, group.forms[formIndex(group.name, group.forms.length)])"
          @blur="hint = null"
        >{{ group.name }}<span v-if="group.forms.length > 1" class="ml-1.5 text-xs font-normal text-muted">{{ formIndex(group.name, group.forms.length) + 1 }}/{{ group.forms.length }}</span></span>
        <button v-if="group.forms.length > 1" type="button" class="min-h-[40px] px-2 text-muted hover:text-brass" :aria-label="'Forma siguiente de ' + group.name" @click="stepForm($event, group.name, group.forms.length, 1)" @blur="hint = null">›</button>
      </div>
    </div>
    <div class="mt-3 overflow-x-auto pt-5">
      <template v-for="(line, i) in lyrics?.lines || []" :key="i">
        <p v-if="line.section" class="lyric-section">{{ line.section }}</p>
        <div v-else :data-lyric-line="i" class="mt-5 first:mt-0">
          <div class="lyric-chord relative rounded bg-raised text-[15px] sm:text-base" :style="{ minWidth: lineWidth(line.text, line.chords.map(c => c.col)) + 'ch' }">
            <span data-char-unit class="invisible absolute" style="width: 1ch"></span>
            <span aria-hidden="true">&nbsp;</span>
            <span
              v-for="c in line.chords"
              :key="c.col"
              class="group absolute top-0 cursor-grab touch-none select-none"
              :style="{ left: c.col + 'ch' }"
              @pointerdown="findChord(c.chord_id) && start($event, findChord(c.chord_id)!, { line: i, col: c.col })"
              @pointerenter="showHint($event.currentTarget as HTMLElement, findChord(c.chord_id))"
              @pointerleave="hint = null"
            >{{ chordLabel(findChord(c.chord_id), chords) }}<button
              type="button"
              class="absolute -top-4 left-1/2 flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-full bg-ivory text-base font-bold leading-none text-ground ring-2 ring-ground opacity-0 focus:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
              :aria-label="'Quitar ' + chordLabel(findChord(c.chord_id), chords)"
              @pointerdown.stop
              @click="remove(i, c.col)"
            >×</button></span>
          </div>
          <p class="lyric-text text-xl leading-snug">{{ line.text || ' ' }}</p>
        </div>
      </template>
    </div>
    <ChordHint v-if="hint" :chord="hint.chord" :anchor="hint.anchor" :chords="chords" />
    <span v-if="drag" class="pointer-events-none fixed z-50 -translate-x-1/2 -translate-y-1/2 rounded bg-brass px-3 py-1.5 font-semibold text-brass-ink" :style="{ left: drag.x + 'px', top: drag.y + 'px' }">{{ drag.label }}</span>
  </div>
</template>
