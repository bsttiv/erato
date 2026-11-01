<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Waveform from '../atoms/Waveform.vue'
import { formatTime, type Take } from '../../data/sample'

// Reproductor de una toma con comentarios en un segundo exacto.
// El padre le pone :key con la toma elegida para reiniciarlo al cambiar.
const props = withDefaults(defineProps<{ take: Take; compact?: boolean }>(), { compact: false })

const position = ref(props.take.comments.length ? props.take.comments[0].at : 0)
const playing = ref(false)
const comments = ref(props.take.comments.slice())
const draft = ref('')

const sorted = computed(() => comments.value.slice().sort((a, b) => a.at - b.at))
const marks = computed(() => sorted.value.map((c) => c.at))

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  timer = setInterval(() => {
    if (!playing.value) return
    if (position.value >= props.take.length) {
      playing.value = false
      return
    }
    position.value += 1
  }, 1000)
})
onUnmounted(() => clearInterval(timer))

function toggle() {
  if (position.value >= props.take.length) position.value = 0
  playing.value = !playing.value
}
function seek(at: number) {
  position.value = at
}
function jump(at: number) {
  position.value = at
  playing.value = true
}
function addComment() {
  const text = draft.value.trim()
  if (!text) return
  comments.value.push({ at: position.value, who: 'Tú', text })
  draft.value = ''
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <h3 :class="compact ? 'text-[28px] leading-tight' : 'text-[34px] leading-none sm:text-[40px]'">{{ take.title }}</h3>
      <p class="text-[15px] text-muted">{{ take.where }}</p>
    </div>

    <div class="mt-8 flex items-center gap-4 sm:gap-5">
      <button type="button" class="btn-primary h-14 w-14 shrink-0 rounded-full px-0" :aria-label="playing ? 'Pausar' : 'Reproducir'" @click="toggle">
        <svg v-if="playing" width="18" height="20" viewBox="0 0 18 20" aria-hidden="true"><rect x="2" y="1" width="5" height="18" fill="#1a1108"></rect><rect x="11" y="1" width="5" height="18" fill="#1a1108"></rect></svg>
        <svg v-else width="18" height="20" viewBox="0 0 18 20" aria-hidden="true"><path d="M3 1 L17 10 L3 19 Z" fill="#1a1108"></path></svg>
      </button>
      <div class="min-w-0 flex-1">
        <Waveform :seed="take.seed" :length="take.length" :position="position" :bars="compact ? 48 : 80" :marks="marks" :height="compact ? 'h-14' : 'h-24'" @seek="seek"></Waveform>
        <div class="mt-2 flex justify-between text-sm tabular-nums text-muted">
          <span>{{ formatTime(position) }}</span><span>{{ formatTime(take.length) }}</span>
        </div>
      </div>
    </div>

    <div class="mt-5">
      <button
        v-for="(c, i) in sorted"
        :key="i"
        type="button"
        class="grid w-full cursor-pointer grid-cols-[60px_1fr] gap-3 rounded border-0 bg-transparent px-2 py-3 text-left text-base leading-snug text-ink transition-colors hover:bg-raised"
        @click="jump(c.at)"
      >
        <span class="font-semibold tabular-nums text-brass">{{ formatTime(c.at) }}</span>
        <span><b class="font-semibold">{{ c.who }}</b> {{ c.text }}</span>
      </button>
      <p v-if="!sorted.length" class="px-2 py-3 text-base text-muted">Esta toma aún no tiene comentarios.</p>
    </div>

    <form class="mt-3 flex flex-wrap gap-2" @submit.prevent="addComment">
      <span class="inline-flex min-h-[48px] items-center rounded bg-ground px-3.5 font-semibold tabular-nums text-brass">{{ formatTime(position) }}</span>
      <label :for="'cm-' + take.seed" class="sr-only">Comentario en {{ formatTime(position) }}</label>
      <input :id="'cm-' + take.seed" v-model="draft" type="text" placeholder="Comenta este segundo" class="field-input-dark min-w-0 flex-[1_1_200px]" />
      <button type="submit" class="btn-ghost">Comentar</button>
    </form>
  </div>
</template>
