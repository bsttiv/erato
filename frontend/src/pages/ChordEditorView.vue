<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useCompositionPath } from '../api/compositionPath'
import { useSong } from '../stores/song'
import { client } from '../stores/session'
import { errorMessage } from '../api/messages'
import CompositionHeader from '../components/organisms/CompositionHeader.vue'
import Fretboard from '../components/atoms/Fretboard.vue'
import PianoKeys from '../components/atoms/PianoKeys.vue'
import { NOTE_NAMES } from '../lib/chords'
import { guitarInput, pianoInput, hasChordNotes, fretsForChord, chordInput } from '../lib/chordInput'

const compositionPath = useCompositionPath()
const { song, loading, error, canEdit, conflicts, notice, saving, saveSections } = useSong()
const selected = ref(-1)
const instrument = ref('guitar')
const frets = ref([-1, -1, -1, -1, -1, -1])
const keys = ref<number[]>([])
const baseMidi = ref(48)
const startFret = ref(1)
const previewName = ref('—')
const previewError = ref('')
const previewing = ref(false)
const keyMode = ref('auto')
const selectedKey = ref('')
const keyEdited = ref(false)
const allKeys = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'Db', 'Ab', 'Eb', 'Bb', 'F', 'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm', 'Dm']
const chords = computed(() => song.value?.chords || [])
const candidates = computed(() => song.value?.key_candidates || [])
const keyOptions = computed(() => keyMode.value === 'manual' ? allKeys : candidates.value)
const input = computed(() => instrument.value === 'guitar' ? guitarInput(frets.value) : pianoInput(keys.value, baseMidi.value))
const valid = computed(() => hasChordNotes(input.value.notes))
const chord = computed(() => ({ name: previewName.value, notes: input.value.notes.map((note) => NOTE_NAMES[note % 12] + (Math.floor(note / 12) - 1)).join(' · ') }))
const usage = computed(() => {
  const id = chords.value[selected.value]?.id
  const count = id ? (song.value?.lyrics?.lines || []).flatMap((line) => line.chords).filter((placement) => placement.chord_id === id).length : 0
  return count ? `${count} ubicaciones en la letra.` : 'Todavía no está en la letra. Guarda el acorde para ubicarlo sobre una sílaba.'
})
function choose(index: number) {
  const saved = chords.value[index]
  if (!saved) return clearChord()
  selected.value = index
  instrument.value = saved.instrument
  frets.value = fretsForChord(saved)
  startFret.value = Math.max(1, Math.min(...frets.value.filter((fret) => fret > 0), 18))
  baseMidi.value = saved.instrument === 'piano' ? Math.floor(Math.min(...saved.notes) / 12) * 12 : 48
  keys.value = saved.instrument === 'piano' ? saved.notes.map((note) => note - baseMidi.value) : []
  previewName.value = saved.name
}
function clearChord() {
  selected.value = -1
  frets.value = [-1, -1, -1, -1, -1, -1]
  keys.value = []
  previewName.value = '—'
}
function changeInstrument(value: string) {
  if (!canEdit.value) return
  clearChord()
  instrument.value = value
}
watch(() => song.value, (value, previous) => {
  if (!value) return
  const changedSong = !previous || value.id !== previous.id || value.share_slug !== previous.share_slug
  const keyDraftUnchanged = !previous || (keyMode.value === (previous.key_mode || 'auto') && selectedKey.value === (previous.key || ''))
  if (changedSong || keyDraftUnchanged) {
    keyMode.value = value.key_mode || 'auto'
    selectedKey.value = value.key || ''
    keyEdited.value = false
  }
  // Section saves must not discard a new chord draft or a conflicted shape.
  if (changedSong) {
    clearChord()
    if (chords.value.length) choose(0)
  }
}, { immediate: true })
let previewSequence = 0
watch([input, () => song.value?.key, canEdit], async () => {
  const sequence = ++previewSequence
  previewError.value = ''
  previewing.value = false
  if (!canEdit.value) {
    previewName.value = chords.value[selected.value]?.name || '—'
    return
  }
  previewName.value = '—'
  if (!valid.value || !song.value?.id) return
  previewing.value = true
  try {
    const result = await client.request(`/songs/${encodeURIComponent(song.value.id)}/chord-name`, { method: 'POST', body: input.value })
    if (sequence === previewSequence) previewName.value = result.name
  } catch (failure) {
    if (sequence === previewSequence) previewError.value = errorMessage(failure)
  } finally {
    if (sequence === previewSequence) previewing.value = false
  }
}, { immediate: true })
async function saveChord() {
  if (!canEdit.value || !valid.value) return
  const next = chords.value.map(chordInput)
  const updated = { ...input.value }
  if (selected.value >= 0) {
    updated.id = chords.value[selected.value].id
    next[selected.value] = updated
  } else next.push(updated)
  const index = selected.value >= 0 ? selected.value : next.length - 1
  const submitted = JSON.stringify(input.value)
  const result = await saveSections({ chords: next })
  if (result && !result.conflicts?.some((entry) => entry.section === 'chords') && JSON.stringify(input.value) === submitted) choose(index)
}
async function removeChord() {
  if (!canEdit.value || selected.value < 0) return
  const result = await saveSections({ chords: chords.value.filter((_, index) => index !== selected.value).map(chordInput) })
  if (result && !result.conflicts?.some((entry) => entry.section === 'chords')) clearChord()
}
async function saveKey() {
  if (!canEdit.value) return
  const meta: { key_mode: string; key?: string | null } = { key_mode: keyMode.value }
  // Let the server apply preserve/reset and report key_reset on manual → auto.
  if (!(keyMode.value === 'auto' && song.value!.key_mode === 'manual' && !keyEdited.value)) meta.key = selectedKey.value || null
  const submitted = JSON.stringify([keyMode.value, selectedKey.value])
  const result = await saveSections({ meta })
  if (result && !result.conflicts?.some((entry) => entry.section === 'meta') && JSON.stringify([keyMode.value, selectedKey.value]) === submitted) {
    keyMode.value = song.value!.key_mode || 'auto'
    selectedKey.value = song.value!.key || ''
    keyEdited.value = false
  }
}
function changeKeyMode() {
  keyEdited.value = false
  if (keyMode.value === 'auto' && !candidates.value.includes(selectedKey.value)) selectedKey.value = candidates.value[0] || ''
  if (keyMode.value === 'manual' && !selectedKey.value) selectedKey.value = 'C'
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="acordes" crumb="Acordes">
      <router-link :to="compositionPath" class="btn-ghost btn-sm">{{ canEdit ? 'Cancelar' : 'Volver' }}</router-link>
      <button v-if="canEdit" type="button" class="btn-primary btn-sm" :disabled="saving || !valid || previewing" @click="saveChord">Guardar acorde</button>
    </CompositionHeader>

    <p v-if="loading" class="px-4 text-muted" role="status">Cargando acordes…</p>
    <p v-if="error || previewError" class="px-4 text-muted" role="alert">{{ error || previewError }}</p>
    <p v-if="notice" class="card" role="status">{{ notice }}</p>
    <p v-for="conflict in conflicts" :key="conflict.section" class="card" role="alert">La sección {{ conflict.section }} ha cambiado. Recarga la canción antes de guardar de nuevo.</p>
    <div class="grid gap-8 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[260px_minmax(0,1fr)] lg:gap-10">
      <aside aria-label="Acordes de la canción">
        <h1 class="text-[40px] leading-none">Acordes</h1>
        <p class="mt-2 text-[15px] text-muted">{{ canEdit ? 'Elige uno para editarlo.' : 'Elige un acorde para ver su forma.' }}</p>
        <div class="mt-5 grid grid-cols-3 gap-1 lg:grid-cols-1">
          <button
            v-for="(c, i) in chords"
            :key="c.id"
            type="button"
            class="flex min-h-[52px] cursor-pointer items-center justify-between rounded border-0 px-4 text-left text-lg font-semibold text-ink transition-colors hover:bg-surface"
            :class="selected === i ? 'bg-raised' : 'bg-transparent'"
            :aria-pressed="selected === i ? 'true' : 'false'"
            @click="choose(i)"
          >
            {{ c.name }}<span v-if="selected === i" class="h-2 w-2 rounded-full bg-brass" aria-hidden="true"></span>
          </button>
        </div>
        <button v-if="canEdit" type="button" class="btn-ghost mt-3.5 w-full" @click="clearChord">Acorde nuevo</button>
      </aside>

      <main class="min-w-0">
        <div class="card mb-5">
          <template v-if="canEdit">
          <label for="key-mode" class="field-label">Modo de tonalidad</label>
          <select id="key-mode" v-model="keyMode" :disabled="!canEdit || saving" class="field-input-dark" @change="changeKeyMode">
            <option value="auto">Automático</option><option value="manual">Manual</option>
          </select>
          <label for="song-key" class="field-label mt-3.5">Tonalidad</label>
          <select id="song-key" v-model="selectedKey" @change="keyEdited = true" :disabled="!canEdit || saving || !keyOptions.length" class="field-input-dark">
            <option v-if="!keyOptions.length" value="">Sin tonalidad</option>
            <option v-for="candidate in keyOptions" :key="candidate" :value="candidate">{{ candidate }}</option>
          </select>
          </template>
          <p v-else class="text-sm text-muted">Tonalidad: {{ song?.key || 'Sin tonalidad' }} · {{ keyMode === 'auto' ? 'Automático' : 'Manual' }}</p>
          <p class="mt-2 text-sm text-muted">{{ candidates.length ? 'Candidatas: ' + candidates.join(', ') : (chords.length ? 'No hay tonalidades candidatas para estos acordes.' : 'Agrega acordes para ver tonalidades candidatas.') }}</p>
          <button v-if="canEdit" type="button" class="btn-ghost mt-3.5" :disabled="saving" @click="saveKey">Guardar tonalidad</button>
        </div>
        <div class="rounded-md bg-surface bg-lamp p-5 sm:p-8">
          <div class="flex flex-wrap items-start justify-between gap-5">
            <div>
              <p class="text-sm text-muted">Nombre detectado</p>
              <p class="mt-1 font-display text-[72px] leading-none text-brass sm:text-[112px]" aria-live="polite">{{ chord.name }}</p>
              <p class="mt-2 text-lg">{{ chord.notes }}</p>
            </div>
            <div v-if="canEdit" class="segmented bg-ground" role="group" aria-label="Instrumento">
              <button type="button" class="segmented-item" :class="instrument === 'guitar' ? 'segmented-item-on' : ''" :aria-pressed="instrument === 'guitar' ? 'true' : 'false'" :disabled="!canEdit" @click="changeInstrument('guitar')">Guitarra</button>
              <button type="button" class="segmented-item" :class="instrument === 'piano' ? 'segmented-item-on' : ''" :aria-pressed="instrument === 'piano' ? 'true' : 'false'" :disabled="!canEdit" @click="changeInstrument('piano')">Piano</button>
            </div>
          </div>

          <div v-if="instrument === 'guitar'" class="mt-9">
            <label for="first-fret" class="field-label">Primer traste visible</label>
            <input id="first-fret" v-model.number="startFret" type="number" min="1" max="24" class="field-input-dark" />
            <Fretboard :frets="frets" :fret-count="7" :start-fret="Math.max(1, Math.min(24, startFret || 1))" :show-notes="true" :disabled="!canEdit" @change="frets = $event"></Fretboard>
            <p v-if="canEdit" class="mt-4 text-[15px] leading-normal text-muted">Toca un traste para poner un dedo. Toca la columna de la izquierda para dejar la cuerda al aire (○) o silenciarla (×).</p>
          </div>
          <div v-else class="mt-9">
            <PianoKeys :keys="keys" :base-midi="baseMidi" :disabled="!canEdit" @change="keys = $event"></PianoKeys>
            <p class="mt-4 text-[15px] leading-normal text-muted">La nota más grave que marques se toma como bajo del acorde.</p>
          </div>
        </div>

        <div class="mt-3.5 grid gap-3.5 md:grid-cols-2">
          <div class="card">
            <p class="text-sm text-muted">Se usa en</p>
            <p class="mt-2 text-[17px] leading-normal">{{ usage }}</p>
          </div>
          <div class="card">
            <p class="text-sm text-muted">{{ previewing ? 'Detectando nombre…' : 'El servidor calcula el nombre según la tonalidad de la canción.' }}</p>
            <p v-if="canEdit && !valid" class="mt-2 text-sm text-muted">Selecciona al menos dos notas distintas.</p>
            <button v-if="canEdit && selected >= 0" type="button" class="btn-ghost mt-3.5" :disabled="saving" @click="removeChord">Eliminar acorde</button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
