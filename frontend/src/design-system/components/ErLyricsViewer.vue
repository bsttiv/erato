<template>
  <section
    :class="['er-lyrics', 'er-lyrics-viewer-card', max && 'er-lyrics--max', customClass]"
    :style="max ? undefined : { height: height ? `${height}px` : '360px' }"
  >
    <div class="er-lyrics-top er-lyrics-viewer-top">
      <button
        type="button"
        class="er-iconbtn"
        :aria-label="playing ? 'Pausar desplazamiento' : 'Desplazar automáticamente'"
        :style="playing ? { color: 'var(--amber)' } : undefined"
        @click="togglePlay"
      >
        <ErIcon :name="playing ? 'pause' : 'play'" />
      </button>

      <div class="er-lyrics-title">
        {{ title || 'Letra' }}
      </div>

      <label class="er-lyrics-speed er-lyrics-viewer-speed">
        velocidad
        <input
          v-model.number="speed"
          type="range"
          class="er-range"
          min="6"
          max="120"
          step="2"
          aria-label="Velocidad de desplazamiento"
        >
        <output>{{ (speed / 24).toFixed(1) }}×</output>
      </label>

      <button
        type="button"
        class="er-iconbtn"
        :aria-label="max ? 'Salir de pantalla completa' : 'Maximizar'"
        @click="toggleMax"
      >
        <ErIcon :name="max ? 'min' : 'max'" />
      </button>
    </div>

    <div ref="boxRef" class="er-lyrics-scroll" style="flex: 1">
      <template v-for="(item, i) in parsedBody" :key="`line-${i}`">
        <div v-if="item.type === 'section'" class="er-lyrics-section">
          {{ item.text }}
        </div>
        <div v-else-if="item.type === 'gap'" class="er-lyric--gap" />
        <p v-else-if="item.type === 'plain'" class="er-lyric">
          {{ item.text }}
        </p>
        <p v-else-if="item.type === 'chords'" class="er-lyric">
          <span
            v-for="(seg, j) in item.segments"
            :key="`seg-${j}`"
            class="er-seg-lyr"
          >
            <span class="er-seg-chord">{{ seg.chord || '' }}</span>{{ seg.text || '\u00A0' }}
          </span>
        </p>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ErIcon from './ErIcon.vue'
import { parseLine, type LyricSegment } from '../core/lyrics'
import { useAutoScroll } from '../composables/useAutoScroll'

const props = withDefaults(
  defineProps<{
    lyrics: string
    title?: string
    defaultSpeed?: number
    height?: number
    showChords?: boolean
    customClass?: string
  }>(),
  {
    defaultSpeed: 24,
    showChords: true,
  }
)

const boxRef = ref<HTMLElement | null>(null)
const { playing, speed, max, togglePlay, toggleMax } = useAutoScroll(boxRef, {
  defaultSpeed: props.defaultSpeed,
})

type BodyItem =
  | { type: 'section'; text: string }
  | { type: 'gap' }
  | { type: 'plain'; text: string }
  | { type: 'chords'; segments: LyricSegment[] }

const parsedBody = computed<BodyItem[]>(() => {
  const text = props.lyrics || ''
  const hasChords = /\[[^\]]+\]/.test(text) && props.showChords !== false

  return text.split('\n').map((raw) => {
    const line = raw.replace(/\s+$/, '')
    if (/^#\s*/.test(line)) {
      return { type: 'section', text: line.replace(/^#\s*/, '') }
    }
    if (!line) {
      return { type: 'gap' }
    }
    if (!hasChords) {
      return { type: 'plain', text: line.replace(/\[[^\]]+\]/g, '') }
    }
    return { type: 'chords', segments: parseLine(line) }
  })
})
</script>
