<template>
  <div
    class="er-lyrics-edit"
    tabindex="-1"
    @keydown.esc="onEscape"
  >
    <!-- Chord Palette Toolbar -->
    <ErChordPalette
      :chords="chords"
      :armed-chord="armedChord"
      @arm="onArm"
      @drag-start="onDragStart"
    />

    <!-- Polite Live Region for Screen Readers -->
    <div
      aria-live="polite"
      style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0);"
    >
      {{ liveAnnouncement }}
    </div>

    <!-- Lyrics Editor Body -->
    <div>
      <template v-for="(line, lineIdx) in parsedLines" :key="`line-${lineIdx}`">
        <div v-if="line.type === 'section'" class="er-lyrics-section">
          {{ line.text }}
        </div>
        <div v-else-if="line.type === 'gap'" class="er-lyric--gap" />
        <p v-else class="er-lyric">
          <button
            v-for="(tok, tokIdx) in line.tokens"
            :key="`tok-${lineIdx}-${tokIdx}`"
            type="button"
            class="er-drop-target"
            :class="{
              'is-armed': Boolean(armedChord),
              'is-over': overTarget === `${lineIdx}:${tok.offset}`,
            }"
            data-chord-target
            :data-line="lineIdx"
            :data-offset="tok.offset"
            :aria-label="`Línea ${lineIdx + 1}, texto ${tok.text}, acorde ${tok.chord || 'ninguno'}`"
            @click="onTargetClick(lineIdx, tok.offset)"
            @keydown.enter.prevent="onTargetClick(lineIdx, tok.offset)"
            @keydown.space.prevent="onTargetClick(lineIdx, tok.offset)"
          >
            <span class="er-seg-chord">{{ tok.chord || '' }}</span>{{ tok.text || '\u00A0' }}
          </button>
        </p>
      </template>
    </div>

    <!-- Drag Ghost Teleported to Body -->
    <Teleport to="body">
      <div
        v-if="isDragging"
        class="er-drag-ghost"
        :style="{ left: `${ghostX}px`, top: `${ghostY}px` }"
      >
        <ErButton size="sm" variant="primary">
          {{ ghostChordText }}
        </ErButton>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import ErButton from './ErButton.vue'
import ErChordPalette from './ErChordPalette.vue'
import {
  decomposeLine,
  setChordAt,
  SENTINEL_REMOVE,
  type SyllableToken,
} from '../core/lyrics'

const props = withDefaults(
  defineProps<{
    lyrics: string
    chords: string[] | { entries?: Array<{ name: string }> }
  }>(),
  {
    lyrics: '',
  }
)

const emit = defineEmits<{
  (e: 'update:lyrics', val: string): void
  (e: 'update:modelValue', val: string): void
  (e: 'change', val: string): void
}>()

const armedChord = ref<string | null>(null)
const liveAnnouncement = ref('')

const isDragging = ref(false)
const draggedChord = ref<string | null>(null)
const ghostX = ref(0)
const ghostY = ref(0)
const ghostChordText = ref('')
const overTarget = ref<string | null>(null)

type LineItem =
  | { type: 'section'; text: string }
  | { type: 'gap' }
  | { type: 'lyrics'; tokens: SyllableToken[] }

const parsedLines = computed<LineItem[]>(() => {
  const text = props.lyrics || ''
  return text.split('\n').map((raw) => {
    const line = raw.replace(/\s+$/, '')
    if (/^#\s*/.test(line)) {
      return { type: 'section', text: line.replace(/^#\s*/, '') }
    }
    if (!line) {
      return { type: 'gap' }
    }
    const decomposed = decomposeLine(line)
    return { type: 'lyrics', tokens: decomposed.tokens || [...decomposed] }
  })
})

function onArm(chord: string) {
  if (armedChord.value === chord) {
    armedChord.value = null
    liveAnnouncement.value = 'Selección desarmada'
  } else {
    armedChord.value = chord
    liveAnnouncement.value =
      chord === SENTINEL_REMOVE
        ? 'Modo quitar acorde armado'
        : `Acorde ${chord} armado`
  }
}

function onEscape() {
  armedChord.value = null
  liveAnnouncement.value = 'Selección desarmada'
}

function onTargetClick(line: number, offset: number) {
  if (!armedChord.value) return
  const toSet = armedChord.value === SENTINEL_REMOVE ? null : armedChord.value
  commitChord(line, offset, toSet)
}

function commitChord(line: number, offset: number, chord: string | null) {
  const updated = setChordAt(props.lyrics, { line, offset }, chord)
  emit('update:lyrics', updated)
  emit('update:modelValue', updated)
  emit('change', updated)
}

function onDragStart(e: PointerEvent, chord: string) {
  isDragging.value = true
  draggedChord.value = chord
  ghostX.value = e.clientX
  ghostY.value = e.clientY
  ghostChordText.value = chord === SENTINEL_REMOVE ? '✕ quitar' : chord

  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerCancel)
}

function onPointerMove(e: PointerEvent) {
  if (!isDragging.value) return
  ghostX.value = e.clientX
  ghostY.value = e.clientY

  const el = document.elementFromPoint(e.clientX, e.clientY)?.closest('[data-chord-target]')
  if (el) {
    const line = el.getAttribute('data-line')
    const offset = el.getAttribute('data-offset')
    overTarget.value = `${line}:${offset}`
  } else {
    overTarget.value = null
  }
}

function onPointerUp(e: PointerEvent) {
  if (!isDragging.value) return

  const el = document.elementFromPoint(e.clientX, e.clientY)?.closest('[data-chord-target]')
  if (el && draggedChord.value !== null) {
    const line = Number(el.getAttribute('data-line'))
    const offset = Number(el.getAttribute('data-offset'))
    const toSet = draggedChord.value === SENTINEL_REMOVE ? null : draggedChord.value
    commitChord(line, offset, toSet)
  }

  cleanupDrag()
}

function onPointerCancel() {
  cleanupDrag()
}

function cleanupDrag() {
  isDragging.value = false
  draggedChord.value = null
  overTarget.value = null
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('pointercancel', onPointerCancel)
}

onUnmounted(() => {
  cleanupDrag()
})
</script>
