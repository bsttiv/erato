<script setup lang="ts">
import { useCompositionPath } from '../api/compositionPath'
const compositionPath = useCompositionPath()
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useSong } from '../stores/song'
import LyricSheet from '../components/molecules/LyricSheet.vue'
import { chordLabel } from '../lib/lyrics'
const { song, loading, error } = useSong()

const lines = computed(() => song.value?.lyrics?.lines || [])
const offset = ref(0)
const playing = ref(true)
const speed = ref(1)
const size = ref(44)
const showChords = ref(true)

const SECTION_H = 68
const lineHeight = computed(() => size.value * 1.25 + 18 + (showChords.value ? size.value * 0.5 * 1.3 : 0))
const tops = computed(() => {
  let acc = 0
  return lines.value.map((l) => {
    const t = acc
    acc += l.section ? SECTION_H : lineHeight.value
    return t
  })
})
const total = computed(() => lines.value.length ? tops.value[tops.value.length - 1] + lineHeight.value : 0)
const current = computed(() => {
  let idx = 0
  tops.value.forEach((t, i) => {
    if (t <= offset.value + 4) idx = i
  })
  return idx
})
const currentSection = computed(() => {
  return lines.value.length ? 'Línea ' + (current.value + 1) + ' de ' + lines.value.length : 'Sin letra'
})
const nextChord = computed(() => {
  for (let i = current.value + 1; i < lines.value.length; i++) {
    const id = lines.value[i].chords?.[0]?.chord_id
    if (id) return chordLabel(song.value?.chords!.find(chord => chord.id === id), song.value?.chords)
  }
  return '—'
})
const trackStyle = computed(() => ({ transform: 'translateY(' + -offset.value + 'px)' }))
const textStyle = computed(() => ({ fontSize: size.value + 'px' }))

watch(() => song.value, () => { offset.value = 0; playing.value = true })
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  timer = setInterval(() => {
    if (!playing.value || !lines.value.length) return
    const next = offset.value + speed.value * 1.6
    if (next >= total.value) {
      offset.value = total.value
      playing.value = false
    } else offset.value = next
  }, 40)
})
onUnmounted(() => clearInterval(timer))

const restart = () => {
  offset.value = 0
  playing.value = true
}
const smaller = () => (size.value = Math.max(24, size.value - 6))
const bigger = () => (size.value = Math.min(80, size.value + 6))
</script>

<template>
  <div class="flex h-[100dvh] flex-col bg-[#0d0907] bg-lamp text-ink">
    <header class="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-7">
      <div>
        <h1 class="text-[26px] leading-none sm:text-[30px]">{{ song?.title || 'Composición' }}</h1>
        <p class="mt-1 text-sm text-muted">{{ song?.key || 'Sin tonalidad' }} · {{ song?.tempo || '—' }} bpm</p>
      </div>
      <router-link :to="compositionPath" class="btn-ghost btn-sm">Salir</router-link>
    </header>

    <p v-if="loading" role="status" class="px-4">Cargando composición…</p>
    <p v-if="error" role="alert" class="px-4">{{ error }}</p>
    <div class="flex min-h-0 flex-1">
      <div class="relative min-w-0 flex-1 overflow-hidden px-4 sm:px-[6vw]">
        <div class="pb-[60vh] pt-[22vh] will-change-transform" :style="trackStyle">
          <template v-for="(l, i) in lines" :key="i">
            <p v-if="l.section" class="mb-2.5 mt-10 text-lg font-medium text-brass">{{ l.section }}</p>
            <div v-else class="transition-opacity duration-300" :class="i < current ? 'opacity-35' : ''">
              <div class="mb-[18px] leading-tight" :class="i === current ? 'text-[#fff8ec]' : ''" :style="textStyle"><LyricSheet :lines="[l]" :chords="song?.chords || []" :show-chords="showChords" text-class="text-[1em] leading-tight" chord-class="text-[0.5em]" /></div>
            </div>
          </template>
        </div>
        <div class="absolute right-4 top-3 rounded bg-surface px-3 py-2 md:hidden">
          <span class="text-sm text-muted">Siguiente</span> <span class="text-lg font-semibold text-brass">{{ nextChord }}</span>
        </div>
      </div>
      <aside class="hidden w-[260px] shrink-0 flex-col gap-2.5 bg-[#150f0b] p-7 md:flex" aria-label="Siguiente acorde">
        <p class="text-sm text-muted">Siguiente acorde</p>
        <p class="font-display text-[88px] leading-none text-brass" aria-live="polite">{{ nextChord }}</p>
        <p class="mt-6 text-sm text-muted">Sección</p>
        <p class="text-[22px]">{{ currentSection }}</p>
      </aside>
    </div>

    <footer class="flex flex-wrap items-center justify-center gap-x-6 gap-y-3 bg-[#150f0b] px-4 py-3.5">
      <button type="button" class="btn-primary min-w-[120px]" @click="playing = !playing">{{ playing ? 'Pausar' : 'Reproducir' }}</button>
      <button type="button" class="btn-ghost" @click="restart">Desde el inicio</button>
      <div class="flex items-center gap-3">
        <label for="stage-speed" class="text-[15px] text-muted">Velocidad</label>
        <input id="stage-speed" v-model.number="speed" type="range" min="0.5" max="2.5" step="0.1" class="w-36 accent-brass sm:w-44" />
        <span class="min-w-[44px] font-semibold tabular-nums">{{ speed.toFixed(1) }}×</span>
      </div>
      <div class="flex gap-1.5">
        <button type="button" class="btn-ghost btn-icon" aria-label="Texto más pequeño" @click="smaller">A−</button>
        <button type="button" class="btn-ghost btn-icon" aria-label="Texto más grande" @click="bigger">A+</button>
      </div>
      <button type="button" class="btn-ghost" :class="showChords ? 'bg-[#3a2914] text-brass hover:text-brass' : ''" :aria-pressed="showChords ? 'true' : 'false'" @click="showChords = !showChords">Acordes</button>
    </footer>
  </div>
</template>
