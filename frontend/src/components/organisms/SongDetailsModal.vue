<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppModal from '../molecules/AppModal.vue'
import { client } from '../../stores/session'
import { errorMessage, moveMessage } from '../../api/messages'
import { bandsApi, type Band } from '../../api/bands'
import { useSong } from '../../stores/song'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const { song, saving, error, conflicts, canManage, saveSections, load } = useSong()

const STATUSES = [['idea', 'Idea'], ['in_progress', 'En progreso'], ['ready', 'Lista']]
const VISIBILITIES = [['private', 'Privada'], ['public', 'Pública']]
const METERS = ['4/4', '3/4', '6/8']
const status = ref('idea')
const visibility = ref('private')
const tempo = ref<number | ''>('')
const meter = ref('')
const busy = ref(false)
const bands = ref<Band[]>([])
const bandId = ref('')
const meters = computed(() => (!meter.value || METERS.includes(meter.value) ? METERS : [meter.value, ...METERS]))
// Only the owner of a personal song can move it, and only to a band they belong to (file 06).
const movable = computed(() => canManage.value && song.value?.owner_type === 'user')

watch(() => props.open, open => {
  if (!open) return
  status.value = song.value?.status || 'idea'
  visibility.value = song.value?.visibility || 'private'
  tempo.value = song.value?.tempo ?? ''
  meter.value = song.value?.time_signature || ''
  bandId.value = ''
  bands.value = []
  if (movable.value) bandsApi.list().then(list => { bands.value = list }, () => { bands.value = [] })
}, { immediate: true })

function changedMeta() {
  const current = song.value!
  const next = { status: status.value, tempo: tempo.value === '' ? null : tempo.value, time_signature: meter.value || null }
  return Object.fromEntries(Object.entries(next).filter(([field, value]) => value !== (current[field as keyof typeof current] ?? null)))
}
async function save() {
  busy.value = true
  const meta = changedMeta()
  if (Object.keys(meta).length) {
    const result = await saveSections({ meta })
    // Errors and conflicts render on the page, which the modal would cover.
    if (!result || conflicts.value?.length) {
      busy.value = false
      emit('close')
      return
    }
  }
  const target = song.value!
  if (canManage.value && visibility.value !== target.visibility) {
    try {
      const updated = await client.request(`/songs/${encodeURIComponent(String(target.id))}/visibility`, { method: 'PATCH', body: { visibility: visibility.value } })
      if (song.value === target) song.value = updated
    } catch (failure) { error.value = errorMessage(failure) }
  }
  if (movable.value && bandId.value) {
    const current = song.value!
    try {
      const updated = await client.request(`/songs/${encodeURIComponent(String(current.id))}/move`, { method: 'POST', body: { band_id: bandId.value } })
      if (song.value === current) {
        song.value = updated
        // Manage rights change with the owner: on a band song only the band owner manages.
        void load()
      }
    } catch (failure) { error.value = moveMessage(failure) }
  }
  busy.value = false
  emit('close')
}
</script>

<template>
  <AppModal :open="open" title="Editar detalles" @close="emit('close')">
    <form class="grid gap-5" @submit.prevent="save">
      <div>
        <p class="field-label">Estado</p>
        <div class="segmented" role="group" aria-label="Estado">
          <button v-for="[value, label] in STATUSES" :key="value" type="button" class="segmented-item" :class="status === value ? 'segmented-item-on' : ''" :aria-pressed="status === value ? 'true' : 'false'" @click="status = value">{{ label }}</button>
        </div>
      </div>
      <div v-if="canManage">
        <p class="field-label">Visibilidad</p>
        <div class="segmented" role="group" aria-label="Visibilidad">
          <button v-for="[value, label] in VISIBILITIES" :key="value" type="button" class="segmented-item" :class="visibility === value ? 'segmented-item-on' : ''" :aria-pressed="visibility === value ? 'true' : 'false'" @click="visibility = value">{{ label }}</button>
        </div>
      </div>
      <div class="grid gap-5 sm:grid-cols-2">
        <div>
          <label for="details-bpm" class="field-label">Tempo (bpm)</label>
          <input id="details-bpm" v-model="tempo" type="number" min="20" max="400" step="1" class="field-input-dark w-full" />
        </div>
        <div>
          <label for="details-meter" class="field-label">Compás</label>
          <select id="details-meter" v-model="meter" class="field-input-dark w-full">
            <option value="">Sin compás</option>
            <option v-for="value in meters" :key="value">{{ value }}</option>
          </select>
        </div>
      </div>
      <div v-if="movable">
        <label for="details-band" class="field-label">Mover a una banda</label>
        <select id="details-band" v-model="bandId" class="field-input-dark w-full" :disabled="!bands.length" aria-describedby="details-band-hint">
          <option value="">No mover</option>
          <option v-for="band in bands" :key="band.id" :value="band.id">{{ band.name }}</option>
        </select>
        <p id="details-band-hint" class="mt-2 text-sm text-muted">Pasa a ser de la banda; no se puede volver a personal.</p>
      </div>
      <button type="submit" class="btn-primary" :disabled="saving || busy">{{ saving || busy ? 'Guardando…' : 'Guardar' }}</button>
    </form>
  </AppModal>
</template>
