<template>
  <div v-if="!currentTake" :class="['er-player', 'er-panel', customClass]">
    Aún no hay demos.
  </div>

  <div v-else :class="['er-player', customClass]">
    <div class="er-takes">
      <div class="er-label">
        // demos
      </div>
      <button
        v-for="(x, i) in currentTakes"
        :key="x.id"
        type="button"
        class="er-take"
        :aria-current="x.id === curId ? 'true' : undefined"
        @click="curId = x.id"
      >
        <span class="er-take-idx">{{ pad2(i + 1) }}</span>
        <span class="er-take-title">{{ x.title }}</span>
        <span class="er-take-dur">{{ fmt(x.duration || 0) }}</span>
        <span class="er-take-meta">
          {{ (formatDate(x.date) ? formatDate(x.date) + ' · ' : '') + (x.comments ? x.comments.length : 0) }} coment.
        </span>
      </button>
    </div>

    <div class="er-now">
      <audio
        v-if="currentTake.src"
        ref="audioRef"
        :src="currentTake.src"
        preload="metadata"
        @timeupdate="onAudioTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @ended="playing = false"
      />

      <div class="er-now-head">
        <button
          type="button"
          class="er-play"
          :aria-label="playing ? 'Pausar' : 'Reproducir'"
          @click="togglePlay"
        >
          <ErIcon :name="playing ? 'pause' : 'play'" />
        </button>
        <div style="min-width: 0">
          <div class="er-now-title">
            {{ currentTake.title }}
          </div>
          <div class="er-now-sub">
            {{ [formatDate(currentTake.date), currentTake.note].filter(Boolean).join(' · ') }}
          </div>
        </div>
      </div>

      <div ref="waveRef" class="er-wave" @click="onWave">
        <button
          v-for="(c, i) in comments"
          :key="i"
          type="button"
          class="er-pin"
          :style="{ left: `${(c.t / duration) * 100}%` }"
          :aria-label="`${fmt(c.t)} — ${c.author}: ${c.text}`"
          :title="`${fmt(c.t)} — ${c.text}`"
          @click.stop="seek(c.t)"
        />
        <svg
          :viewBox="`0 0 ${N * 6} 64`"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <rect
            v-for="(v, i) in pk"
            :key="i"
            :class="['er-wave-bar', (i + 0.5) / N <= currentTime / duration && 'is-past']"
            :x="i * 6 + 1"
            :y="(64 - v * 60) / 2"
            width="3.5"
            :height="v * 60"
            rx="1.75"
          />
        </svg>
        <div
          class="er-wave-head"
          :style="{ left: `${(currentTime / duration) * 100}%` }"
        />
      </div>

      <div class="er-times">
        <b>{{ fmt(currentTime) }}</b>
        <span>{{ fmt(duration) }}</span>
      </div>

      <ul v-if="comments.length" class="er-comments">
        <li
          v-for="(c, i) in comments"
          :key="i"
          :class="['er-comment', Math.abs(c.t - currentTime) < 2.5 && 'is-near']"
          @click="seek(c.t)"
        >
          <span class="er-comment-t">{{ fmt(c.t) }}</span>
          <span>
            <span class="er-comment-who">{{ c.author }}</span>
            <span class="er-comment-txt">{{ c.text }}</span>
          </span>
        </li>
      </ul>

      <div class="er-compose">
        <input
          v-model="draft"
          class="er-input"
          :placeholder="`Comentar en ${fmt(currentTime)}…`"
          @keydown.enter="addComment"
        >
        <ErButton
          :disabled="!draft.trim()"
          @click="addComment"
        >
          Comentar
        </ErButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import ErIcon from './ErIcon.vue'
import ErButton from './ErButton.vue'
import { peaks } from '../core/waveform'
import { fmt, pad2, formatDate } from '../core/format'
import { useTakePlayback } from '../composables/useTakePlayback'

export interface DemoComment {
  t: number
  author: string
  text: string
}

export interface DemoTake {
  id: string
  title: string
  date?: string
  note?: string
  duration: number
  src?: string
  comments?: DemoComment[]
}

const props = withDefaults(
  defineProps<{
    takes: DemoTake[]
    defaultTakeId?: string
    author?: string
    customClass?: string
  }>(),
  {
    takes: () => [],
    author: 'Tú',
  }
)

const emit = defineEmits<{
  (e: 'comment', takeId: string, comment: DemoComment): void
}>()

const currentTakes = ref<DemoTake[]>(props.takes.slice())

watch(
  () => props.takes,
  (newTakes) => {
    currentTakes.value = newTakes.slice()
  },
  { deep: true }
)

const curId = ref<string>(
  props.defaultTakeId || (currentTakes.value[0] && currentTakes.value[0].id) || ''
)

watch(
  () => currentTakes.value,
  (newTakes) => {
    if (!newTakes.some((x) => x.id === curId.value)) {
      curId.value = (newTakes[0] && newTakes[0].id) || ''
    }
  }
)

const currentTake = computed<DemoTake | undefined>(() => {
  return (
    currentTakes.value.find((x) => x.id === curId.value) ||
    currentTakes.value[0]
  )
})

const comments = computed(() => {
  return currentTake.value?.comments || []
})

const audioRef = ref<HTMLAudioElement | null>(null)
const waveRef = ref<HTMLElement | null>(null)
const draft = ref('')

const { currentTime, playing, duration, loadedDuration, seek, togglePlay } =
  useTakePlayback(currentTake, audioRef)

const N = 72
const pk = computed(() => {
  return peaks(currentTake.value ? currentTake.value.id : 'x', N)
})

function onAudioTimeUpdate(e: Event) {
  const el = e.target as HTMLAudioElement
  currentTime.value = el.currentTime
}

function onLoadedMetadata(e: Event) {
  const el = e.target as HTMLAudioElement
  if (isFinite(el.duration)) {
    loadedDuration.value = el.duration
  }
}

function onWave(e: MouseEvent) {
  if (!waveRef.value) return
  const r = waveRef.value.getBoundingClientRect()
  seek(((e.clientX - r.left) / r.width) * duration.value)
}

function addComment() {
  const txt = draft.value.trim()
  if (!txt || !currentTake.value) return
  const c: DemoComment = {
    t: currentTime.value,
    author: props.author || 'Tú',
    text: txt,
  }
  const takeId = currentTake.value.id
  currentTakes.value = currentTakes.value.map((x) => {
    if (x.id === takeId) {
      const updatedComments = (x.comments || []).concat([c]).sort((a, b) => a.t - b.t)
      return { ...x, comments: updatedComments }
    }
    return x
  })
  draft.value = ''
  emit('comment', takeId, c)
}
</script>
