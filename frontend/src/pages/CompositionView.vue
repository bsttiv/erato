<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useCompositionPath } from '../api/compositionPath'
import { useSong, type SongLyrics, type SongTask } from '../stores/song'
import { lyricText, replaceLyricText, chordLabel, chordShape } from '../lib/lyrics'
import CompositionHeader from '../components/organisms/CompositionHeader.vue'
import LyricSheet from '../components/molecules/LyricSheet.vue'
import LyricPlacer from '../components/molecules/LyricPlacer.vue'
import AppModal from '../components/molecules/AppModal.vue'
import SongStatus from '../components/atoms/SongStatus.vue'
import SongDetailsModal from '../components/organisms/SongDetailsModal.vue'
import TodoList from '../components/molecules/TodoList.vue'
import { formatTime } from '../data/sample'
import type { Demo } from '../api/demos'

const compositionPath = useCompositionPath()
const { song, loading, error, canEdit, isPublic, conflicts, notice, saving, load, saveSections } = useSong()
const lyrics = ref<SongLyrics | null>(null)
const tasks = ref<SongTask[]>([])
const text = ref('')
const editingLyrics = ref(false)
const editingDetails = ref(false)
const instrument = ref('guitar')
const chords = computed(() => song.value?.chords || [])
const demoCount = computed(() => song.value?.demos?.length ?? 0)
const lastDemo = computed(() => {
  const rows = song.value?.demos ?? []
  return rows.reduce<Demo | null>((latest, demo) => (!latest || (demo.uploaded_at ?? '') >= (latest.uploaded_at ?? '') ? demo : latest), null)
})
const filteredChords = computed(() => chords.value.filter(chord => chord.instrument === instrument.value))
const equal = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b)
watch(song, (value, previous) => {
  if (!value) return
  const freshLoad = !previous || previous.id !== value.id
  if (freshLoad || equal(lyrics.value, previous.lyrics)) {
    lyrics.value = value.lyrics ? JSON.parse(JSON.stringify(value.lyrics)) : null
    text.value = lyricText(lyrics.value)
  } else if (lyrics.value) {
    // A removed chord must not leave an invalid reference in an unsaved draft.
    const ids = new Set(value.chords!.map(chord => chord.id))
    lyrics.value.lines.forEach(line => { line.chords = line.chords.filter(chord => ids.has(chord.chord_id)) })
  }
  if (freshLoad || equal(tasks.value, previous.tasks)) tasks.value = (value.tasks || []).map(task => ({ ...task }))
}, { immediate: true })
function updateText() { lyrics.value = replaceLyricText(lyrics.value, text.value) }
async function save() {
  const submittedLyrics = JSON.stringify(lyrics.value)
  const submittedTasks = JSON.stringify(tasks.value)
  const result = await saveSections({ lyrics: lyrics.value, tasks: tasks.value })
  // Errors and conflicts render on the page, which the modal would cover.
  if (!result || conflicts.value?.length) editingLyrics.value = false
  if (result) {
    if (result.saved?.some(item => item.section === 'lyrics') && JSON.stringify(lyrics.value) === submittedLyrics) {
      lyrics.value = result.song.lyrics ? JSON.parse(JSON.stringify(result.song.lyrics)) : null
      text.value = lyricText(lyrics.value)
      editingLyrics.value = false
    }
    if (result.saved?.some(item => item.section === 'tasks') && JSON.stringify(tasks.value) === submittedTasks) tasks.value = result.song.tasks!.map(task => ({ ...task }))
  }
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="letra">
      <router-link :to="compositionPath + '/escenario'" class="btn-ghost btn-sm">Modo escenario</router-link>
      <button v-if="canEdit" type="button" class="btn-ghost btn-sm" @click="editingDetails = true">Editar detalles</button>
      <router-link v-if="!isPublic" :to="compositionPath + '/compartir'" class="btn-primary btn-sm">Compartir</router-link>
    </CompositionHeader>
    <p v-if="loading" role="status" class="px-4 py-4">Cargando composición…</p>
    <p v-if="error" role="alert" class="px-4 py-4">{{ error }}</p>
    <div v-if="song" class="grid grid-cols-[minmax(0,1fr)] gap-10 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_360px]">
      <article class="min-w-0 max-w-[820px]" aria-labelledby="song-title">
        <h1 id="song-title" class="text-[44px] leading-none sm:text-[56px]">{{ song.title }}</h1>
        <p class="mt-2.5 flex flex-wrap items-center gap-x-3 text-base text-muted"><SongStatus :status="song.status" /><span>{{ song.key || 'Sin tonalidad' }} · {{ song.tempo || '—' }} bpm · {{ song.time_signature || '—' }} · {{ song.visibility === 'public' ? 'Pública' : 'Privada' }}</span></p>
        <p v-if="notice" role="status" class="mt-3.5 rounded bg-surface px-5 py-4">{{ notice }}</p>
        <div class="mt-8"><LyricSheet :lines="lyrics?.lines || []" :chords="chords" /></div>
        <p v-if="!lyrics" class="text-muted">Esta composición todavía no tiene letra.</p>
        <div v-if="canEdit" class="mt-6 flex flex-wrap gap-2.5">
          <button type="button" class="btn-ghost" @click="editingLyrics = true">Editar letra</button>
          <button type="button" class="btn-primary" :disabled="saving" @click="save">{{ saving ? 'Guardando…' : 'Guardar cambios' }}</button>
        </div>
        <SongDetailsModal v-if="canEdit" :open="editingDetails" @close="editingDetails = false" />
        <AppModal v-if="canEdit" :open="editingLyrics" title="Editar letra" @close="editingLyrics = false">
          <label for="lyrics-text" class="block text-sm text-muted">Letra (una línea por renglón). Nombra las secciones con #: #estrofa, #coro, #puente, #instrumental</label>
          <textarea id="lyrics-text" v-model="text" rows="10" class="field-input-dark mt-2 w-full" @input="updateText" />
          <div class="mt-4"><LyricPlacer v-model:lyrics="lyrics" :chords="chords" /></div>
          <button type="button" class="btn-primary mt-5" :disabled="saving" @click="save">{{ saving ? 'Guardando…' : 'Guardar cambios' }}</button>
        </AppModal>
        <div v-if="conflicts?.length" role="alert" class="mt-3.5 rounded bg-surface px-5 py-4"><p v-for="conflict in conflicts" :key="conflict.section">No se guardó {{ conflict.section }}: hay una versión más reciente ({{ conflict.current_version }}). Tu borrador sigue en pantalla.</p><button type="button" class="btn-ghost btn-sm" @click="load">Descartar borrador y recargar</button></div>
      </article>
      <aside class="grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-3.5" aria-label="Detalles de la composición">
        <section class="card">
          <div class="flex items-baseline justify-between"><h2 class="text-[26px]">Acordes</h2><router-link :to="compositionPath + '/acordes'" class="text-[15px]">{{ canEdit ? 'Editar' : 'Ver' }}</router-link></div>
          <label class="block text-sm text-muted mt-3">Instrumento<select v-model="instrument" class="field-input-dark block"><option value="guitar">Guitarra</option><option value="piano">Piano</option></select></label>
          <div class="mt-3.5 flex gap-2 overflow-x-auto [scrollbar-color:theme(colors.fret)_transparent] [scrollbar-width:thin]"><router-link v-for="chord in filteredChords" :key="chord.id" :to="compositionPath + '/acordes'" :title="chordShape(chord)" class="flex min-h-[52px] shrink-0 items-center justify-center rounded bg-ground px-4 text-lg font-semibold text-ink no-underline">{{ chordLabel(chord, chords) }}</router-link></div>
        </section>
        <section class="card"><h2 class="text-[26px]">Tareas</h2><div class="mt-2"><TodoList :initial="tasks" :readonly="!canEdit" @update="tasks = $event" /></div></section>
        <section class="card">
          <div class="flex items-baseline justify-between"><h2 class="text-[26px]">Última demo</h2><router-link :to="compositionPath + '/demos'" class="text-[15px]">{{ demoCount > 1 ? 'Ver las ' + demoCount : 'Ver demos' }}</router-link></div>
          <router-link v-if="lastDemo" :to="compositionPath + '/demos'" class="mt-3.5 flex items-center gap-3.5 text-ink no-underline hover:text-ink">
            <span class="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brass"><svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true"><path d="M2 1 L15 9 L2 17 Z" fill="#1a1108"></path></svg></span>
            <span><span class="block font-medium">{{ lastDemo.title }}</span><span class="block text-sm text-muted">{{ formatTime(lastDemo.duration_s) }}</span></span>
          </router-link>
          <p v-else class="mt-3.5 text-base text-muted">Aún no hay demos.</p>
        </section>
      </aside>
    </div>
  </div>
</template>
