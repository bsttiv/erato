<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSong, type RevisionItem, type RevisionSnapshot } from '../stores/song'
import { client } from '../stores/session'
import { errorMessage } from '../api/messages'
import CompositionHeader from '../components/organisms/CompositionHeader.vue'
import HistoryList from '../components/molecules/HistoryList.vue'

const SECTIONS = ['lyrics', 'chords', 'tabs', 'tasks', 'meta']
const { song, loading, error, canEdit, isPublic, notice, load } = useSong()
const history = ref<RevisionItem[]>([])
const snapshot = ref<RevisionSnapshot | null>(null)
const historyError = ref('')
const busy = ref(false)

const newestFirst = (a: RevisionItem, b: RevisionItem) => (b.created_at ?? '').localeCompare(a.created_at ?? '')

async function fetchHistory() {
  if (!song.value?.id || isPublic.value) return
  busy.value = true
  historyError.value = ''
  snapshot.value = null
  try {
    const rows = await Promise.all(SECTIONS.map(section => client.request<RevisionItem[]>(`/songs/${song.value!.id}/revisions/${section}`)))
    history.value = rows.flat().sort(newestFirst)
  } catch (cause) {
    history.value = []
    historyError.value = errorMessage(cause)
  } finally { busy.value = false }
}
async function readRevision(item: RevisionItem) {
  busy.value = true
  historyError.value = ''
  try { snapshot.value = await client.request(`/songs/${song.value!.id}/revisions/${item.section}/${item.version}`) }
  catch (cause) { historyError.value = errorMessage(cause) }
  finally { busy.value = false }
}
async function restoreRevision(item: RevisionItem) {
  busy.value = true
  historyError.value = ''
  try {
    const result = await client.request(`/songs/${song.value!.id}/revisions/${item.section}/${item.version}/restore`, {
      method: 'POST', body: { base_version: song.value!.section_versions![item.section!] },
    })
    if (result.conflicts?.length) historyError.value = 'La sección está desactualizada. Recarga antes de restaurar.'
    else {
      await load()
      if (result.key_reset) notice.value = 'La tonalidad cambió porque la selección anterior ya no está entre las candidatas.'
    }
  } catch (cause) {
    historyError.value = cause.code === 'version_conflict' ? 'La sección está desactualizada. Recarga antes de restaurar.' : errorMessage(cause)
  } finally { busy.value = false }
}
watch([() => song.value?.id, isPublic], fetchHistory, { immediate: true })
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="historial" crumb="Historial"></CompositionHeader>
    <main class="max-w-[820px] px-4 pb-16 pt-8 sm:px-8">
      <p v-if="loading" role="status">Cargando composición…</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <template v-if="song">
        <h1 class="mb-2 font-sans text-sm font-normal text-muted">Historial · {{ song.title }}</h1>
        <p v-if="notice" role="status" class="mb-3 rounded bg-surface px-5 py-4">{{ notice }}</p>
        <p v-if="busy" role="status">Cargando historial…</p>
        <p v-if="historyError" role="alert">{{ historyError }}</p>
        <HistoryList :items="history" :can-restore="canEdit" :busy="busy" @read="readRevision" @restore="restoreRevision" />
        <p v-if="!busy && !historyError && !history.length" class="text-sm text-muted">Aún no hay cambios.</p>
        <div v-if="snapshot" class="mt-3 rounded bg-surface px-5 py-4">
          <h2 class="text-[22px]">Versión {{ snapshot.version }}</h2>
          <pre class="overflow-x-auto text-sm">{{ JSON.stringify(snapshot.content, null, 2) }}</pre>
          <button type="button" class="btn-ghost btn-sm" @click="snapshot = null">Cerrar</button>
        </div>
      </template>
    </main>
  </div>
</template>
