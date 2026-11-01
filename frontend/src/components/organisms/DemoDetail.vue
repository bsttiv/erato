<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Waveform from '../atoms/Waveform.vue'
import { formatTime } from '../../data/sample'
import type { Demo, DemoComment } from '../../api/demos'

// Reproductor de una demo real (URL firmada) con comentarios en un segundo exacto.
// Es presentacional: el padre trae los datos y atiende los eventos; se reinicia con :key.
const props = defineProps<{
  demo: Demo
  url: string
  comments: DemoComment[]
  canEdit: boolean
  canManage: boolean
  me: string
  busy: boolean
}>()
const emit = defineEmits<{
  rename: [title: string]
  remove: []
  'add-comment': [timestamp: number, text: string]
  'edit-comment': [id: string, text: string]
  'remove-comment': [id: string]
  'playback-error': []
}>()

const audio = ref<HTMLAudioElement | null>(null)
const position = ref(0)
const playing = ref(false)
const draft = ref('')
const renaming = ref(false)
const title = ref(props.demo.title)
const confirmRemove = ref(false)
const editingId = ref('')
const editText = ref('')

const length = computed(() => Math.max(props.demo.duration_s, 1))
const seed = computed(() => [...props.demo.id].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % 12 + 1)
const marks = computed(() => [...new Set(props.comments.map((c) => c.timestamp_s))])
const meta = computed(() => [
  props.demo.uploaded_at ? new Date(props.demo.uploaded_at).toLocaleDateString('es', { day: 'numeric', month: 'short' }) : '',
  props.demo.author ? `subida por ${props.demo.author.display_name}` : '',
].filter(Boolean).join(' · '))
watch(() => props.demo.title, (value) => { title.value = value })

function toggle() {
  const el = audio.value
  if (!el || !props.url) return
  if (el.paused) el.play().catch(() => emit('playback-error'))
  else el.pause()
}
function seek(at: number) {
  position.value = at
  if (audio.value) audio.value.currentTime = at
}
function jump(at: number) {
  seek(at)
  if (audio.value?.paused) audio.value.play().catch(() => emit('playback-error'))
}
function saveRename() {
  const value = title.value.trim()
  if (!value) return
  renaming.value = false
  if (value !== props.demo.title) emit('rename', value)
}
function addComment() {
  const text = draft.value.trim()
  if (!text) return
  emit('add-comment', Math.min(Math.floor(position.value), props.demo.duration_s), text)
  draft.value = ''
}
function startEdit(c: DemoComment) { editingId.value = c.id; editText.value = c.text }
function saveEdit() {
  const text = editText.value.trim()
  if (!text) return
  emit('edit-comment', editingId.value, text)
  editingId.value = ''
}
const mine = (c: DemoComment) => !!props.me && c.author?.username === props.me
</script>

<template>
  <div>
    <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <form v-if="renaming" class="flex min-w-0 flex-1 flex-wrap gap-2" @submit.prevent="saveRename">
        <label for="demo-title" class="sr-only">Nombre de la demo</label>
        <input id="demo-title" v-model="title" type="text" class="field-input-dark min-w-0 flex-[1_1_200px]" />
        <button type="submit" class="btn-primary btn-sm" :disabled="busy">Guardar</button>
        <button type="button" class="btn-ghost btn-sm" @click="renaming = false; title = demo.title">Cancelar</button>
      </form>
      <h2 v-else class="text-[34px] leading-none sm:text-[40px]">{{ demo.title }}</h2>
      <p class="text-[15px] text-muted">{{ meta }}</p>
    </div>
    <div v-if="canEdit && !renaming" class="mt-3 flex flex-wrap gap-2">
      <button type="button" class="btn-ghost btn-sm" :disabled="busy" @click="renaming = true">Renombrar</button>
      <button v-if="!confirmRemove" type="button" class="btn-ghost btn-sm" :disabled="busy" @click="confirmRemove = true">Borrar demo</button>
      <template v-else>
        <button type="button" class="btn-primary btn-sm" :disabled="busy" @click="emit('remove')">Confirmar: borrar demo y sus comentarios</button>
        <button type="button" class="btn-ghost btn-sm" @click="confirmRemove = false">Cancelar</button>
      </template>
    </div>

    <audio
      ref="audio"
      :src="url || undefined"
      preload="metadata"
      class="hidden"
      @timeupdate="position = audio?.currentTime ?? 0"
      @play="playing = true"
      @pause="playing = false"
      @ended="playing = false"
      @error="emit('playback-error')"
    ></audio>
    <div class="mt-8 flex items-center gap-4 sm:gap-5">
      <button type="button" class="btn-primary h-14 w-14 shrink-0 rounded-full px-0" :disabled="!url" :aria-label="playing ? 'Pausar' : 'Reproducir'" @click="toggle">
        <svg v-if="playing" width="18" height="20" viewBox="0 0 18 20" aria-hidden="true"><rect x="2" y="1" width="5" height="18" fill="#1a1108"></rect><rect x="11" y="1" width="5" height="18" fill="#1a1108"></rect></svg>
        <svg v-else width="18" height="20" viewBox="0 0 18 20" aria-hidden="true"><path d="M3 1 L17 10 L3 19 Z" fill="#1a1108"></path></svg>
      </button>
      <div class="min-w-0 flex-1">
        <Waveform :seed="seed" :length="length" :position="position" :bars="80" :marks="marks" height="h-24" @seek="seek"></Waveform>
        <div class="mt-2 flex justify-between text-sm tabular-nums text-muted">
          <span>{{ formatTime(position) }}</span><span>{{ formatTime(demo.duration_s) }}</span>
        </div>
      </div>
    </div>

    <ul class="mt-5 list-none p-0" aria-label="Comentarios">
      <li v-for="c in comments" :key="c.id" class="grid grid-cols-[60px_1fr] gap-3 rounded px-2 py-3 text-base leading-snug hover:bg-raised">
        <button type="button" class="cursor-pointer border-0 bg-transparent p-0 text-left font-semibold tabular-nums text-brass" :aria-label="'Ir a ' + formatTime(c.timestamp_s)" @click="jump(c.timestamp_s)">{{ formatTime(c.timestamp_s) }}</button>
        <div>
          <form v-if="editingId === c.id" class="flex flex-wrap gap-2" @submit.prevent="saveEdit">
            <label :for="'edit-' + c.id" class="sr-only">Editar comentario</label>
            <input :id="'edit-' + c.id" v-model="editText" type="text" class="field-input-dark min-w-0 flex-[1_1_200px]" />
            <button type="submit" class="btn-primary btn-sm" :disabled="busy">Guardar</button>
            <button type="button" class="btn-ghost btn-sm" @click="editingId = ''">Cancelar</button>
          </form>
          <p v-else><b class="font-semibold">{{ c.author?.display_name || 'Alguien' }}</b> {{ c.text }}</p>
          <p v-if="editingId !== c.id && (mine(c) || canManage)" class="mt-1 flex gap-3 text-sm">
            <button v-if="mine(c)" type="button" class="cursor-pointer border-0 bg-transparent p-0 text-muted underline hover:text-ink" :disabled="busy" @click="startEdit(c)">Editar</button>
            <button type="button" class="cursor-pointer border-0 bg-transparent p-0 text-muted underline hover:text-ink" :disabled="busy" @click="emit('remove-comment', c.id)">Borrar</button>
          </p>
        </div>
      </li>
      <li v-if="!comments.length" class="px-2 py-3 text-base text-muted">Esta toma aún no tiene comentarios.</li>
    </ul>

    <form v-if="canEdit" class="mt-3 flex flex-wrap gap-2" @submit.prevent="addComment">
      <span class="inline-flex min-h-[48px] items-center rounded bg-ground px-3.5 font-semibold tabular-nums text-brass">{{ formatTime(position) }}</span>
      <label for="demo-comment" class="sr-only">Comentario en {{ formatTime(position) }}</label>
      <input id="demo-comment" v-model="draft" type="text" placeholder="Comenta este segundo" class="field-input-dark min-w-0 flex-[1_1_200px]" />
      <button type="submit" class="btn-ghost" :disabled="busy">Comentar</button>
    </form>
  </div>
</template>
