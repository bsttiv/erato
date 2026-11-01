<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import CompositionHeader from '../components/organisms/CompositionHeader.vue'
import DemoDetail from '../components/organisms/DemoDetail.vue'
import DemoUpload from '../components/molecules/DemoUpload.vue'
import DemoList from '../components/molecules/DemoList.vue'
import { useSong } from '../stores/song'
import { session, profileApi } from '../stores/session'
import { demosApi, uploadToStorage, type DemoComment } from '../api/demos'
import { accessMessage, uploadMessage } from '../api/messages'

// Demos de una composición: elegir una toma, oírla con URL firmada, renombrar, borrar y comentar
// en un segundo exacto. Por el enlace público (/c/:slug/demos) es solo lectura.
// Los editores suben audio directo al almacenamiento con campos firmados y luego se confirma en la API.
const route = useRoute()
const { song, loading, error, canEdit, canManage, isPublic } = useSong()

const api = computed(() => (route.params.id ? demosApi({ songId: String(route.params.id) }) : demosApi({ slug: String(route.params.slug) })))
const demos = computed(() => song.value?.demos ?? [])
const selectedId = ref('')
const selected = computed(() => demos.value.find((d) => d.id === selectedId.value) ?? null)
const url = ref('')
const comments = ref<DemoComment[]>([])
const counts = ref<Record<string, number>>({})
const detailLoading = ref(false)
const busy = ref(false)
const failure = ref('')
const uploading = ref(false)
const progress = ref(0)
const uploadFailure = ref('')
const me = computed(() => session.user?.username || '')
let generation = 0
let retried = false

watch(demos, (rows) => {
  if (!rows.some((d) => d.id === selectedId.value)) selectedId.value = rows[0]?.id ?? ''
}, { immediate: true })

async function openDemo(id: string) {
  const current = ++generation
  retried = false
  url.value = ''
  comments.value = []
  failure.value = ''
  if (!id) return
  detailLoading.value = true
  try {
    if (!isPublic.value && !session.user) await profileApi.getMe().catch(() => undefined)
    const [signed, rows] = await Promise.all([api.value.playbackUrl(id), api.value.comments(id)])
    if (current !== generation) return
    url.value = signed.url
    comments.value = rows
    counts.value = { ...counts.value, [id]: rows.length }
  } catch (e) { if (current === generation) failure.value = accessMessage(e) }
  finally { if (current === generation) detailLoading.value = false }
}
watch(selectedId, openDemo, { immediate: true })

async function refreshUrl() {
  // Signed URLs last 15 minutes: one silent renewal per selection, then show the error.
  if (retried || !selectedId.value) { failure.value = 'No se pudo reproducir esta demo.'; return }
  retried = true
  try { url.value = (await api.value.playbackUrl(selectedId.value)).url }
  catch (e) { failure.value = accessMessage(e) }
}

async function act(task: () => Promise<unknown>) {
  if (busy.value) return
  busy.value = true
  failure.value = ''
  try { await task() }
  catch (e) { failure.value = accessMessage(e) }
  finally { busy.value = false }
}
async function upload(file: File) {
  if (uploading.value) return
  uploading.value = true
  progress.value = 0
  uploadFailure.value = ''
  try {
    const target = await api.value.uploadUrl()
    await uploadToStorage(target, file, (fraction) => { progress.value = fraction })
    const created = await api.value.confirm(String(target.fields.public_id))
    if (song.value) song.value.demos = [...(song.value.demos ?? []), created]
    selectedId.value = created.id
  } catch (e) { uploadFailure.value = uploadMessage(e) }
  finally { uploading.value = false }
}
const byTime = (rows: DemoComment[]) => rows.slice().sort((a, b) => a.timestamp_s - b.timestamp_s)

const rename = (title: string) => act(async () => {
  const id = selectedId.value
  const updated = await api.value.rename(id, title)
  const target = demos.value.find((d) => d.id === id)
  if (target) target.title = updated.title
})
const remove = () => act(async () => {
  const id = selectedId.value
  await api.value.remove(id)
  if (song.value?.demos) song.value.demos = song.value.demos.filter((d) => d.id !== id)
})
const addComment = (timestamp: number, text: string) => act(async () => {
  const created = await api.value.addComment(selectedId.value, timestamp, text)
  comments.value = byTime([...comments.value, created])
  counts.value = { ...counts.value, [selectedId.value]: comments.value.length }
})
const editComment = (id: string, text: string) => act(async () => {
  const updated = await api.value.editComment(selectedId.value, id, text)
  comments.value = byTime(comments.value.map((c) => (c.id === id ? updated : c)))
})
const removeComment = (id: string) => act(async () => {
  await api.value.removeComment(selectedId.value, id)
  comments.value = comments.value.filter((c) => c.id !== id)
  counts.value = { ...counts.value, [selectedId.value]: comments.value.length }
})
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="demos" crumb="Demos"></CompositionHeader>

    <div class="grid gap-8 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[320px_minmax(0,1fr)]">
      <aside aria-label="Tomas">
        <h1 class="text-[40px] leading-none sm:text-[44px]">Demos</h1>
        <p v-if="song" class="mt-2 text-[15px] text-muted">{{ demos.length }} {{ demos.length === 1 ? 'toma' : 'tomas' }} de {{ song.title }}</p>
        <p v-if="loading" role="status" class="mt-3">Cargando demos…</p>
        <p v-if="error" role="alert" class="mt-3">{{ error }}</p>
        <DemoList v-if="demos.length" :demos="demos" :selected="selectedId" :comment-counts="counts" @select="selectedId = $event"></DemoList>
        <template v-if="canEdit">
          <DemoUpload :busy="uploading" :progress="progress" @pick="upload" @reject="uploadFailure = $event"></DemoUpload>
          <p v-if="uploadFailure" role="alert" class="mt-3">{{ uploadFailure }}</p>
        </template>
      </aside>

      <main class="min-w-0">
        <section v-if="selected" class="rounded-md bg-surface bg-lamp p-5 sm:p-8" aria-label="Reproductor">
          <p v-if="detailLoading" role="status" class="mb-3">Cargando demo…</p>
          <p v-if="failure" role="alert" class="mb-3">{{ failure }}</p>
          <DemoDetail
            :key="selected.id"
            :demo="selected"
            :url="url"
            :comments="comments"
            :can-edit="canEdit"
            :can-manage="canManage"
            :me="me"
            :busy="busy"
            @rename="rename"
            @remove="remove"
            @add-comment="addComment"
            @edit-comment="editComment"
            @remove-comment="removeComment"
            @playback-error="refreshUrl"
          ></DemoDetail>
        </section>
        <section v-else-if="song && !loading" class="rounded-md bg-surface px-5 py-16 text-center" aria-label="Sin demos">
          <p class="font-display text-[32px]">Aún no hay demos</p>
          <p class="mt-2.5 text-base">Cuando se agregue la primera toma de esta composición, aparecerá aquí para escucharla y comentarla.</p>
        </section>
      </main>
    </div>
  </div>
</template>
