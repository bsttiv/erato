<script setup lang="ts">
import { songPath } from '../stores/song'
import { client } from '../stores/session'
import { errorMessage } from '../api/messages'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'
import BackBar from '../components/molecules/BackBar.vue'
import type { Song } from '../stores/song'

const title = ref('')
const router = useRouter()
const route = useRoute()
const tempo = ref('')
const meter = ref('4/4')
const key = ref('')
const busy = ref(false)
const error = ref('')
const created = ref<Song | null>(null)
const space = ref(route.query.band_id ? 1 : 0)
const access = ref(0)
const parts = ref([
  { name: 'Letra', on: true },
  { name: 'Acordes', on: true },
  { name: 'Tablatura', on: true },
  { name: 'Demos', on: false },
  { name: 'Tareas', on: true },
])
const spaces = [
  { name: 'Personal', desc: 'Solo tú, y quien invites.' },
  { name: 'Banda', desc: 'La ven sus integrantes.' },
]
const accesses = [
  { name: 'Privada', desc: 'Solo las personas invitadas.' },
  { name: 'Pública', desc: 'Cualquiera con el enlace puede verla.' },
]
const chosen = computed(() => parts.value.filter((p) => p.on).map((p) => p.name))
const accessLine = computed(() =>
  access.value === 0 ? 'Privada: solo las personas invitadas pueden verla y editarla.' : 'Pública: cualquiera con el enlace la ve; solo los invitados la editan.',
)
async function create() {
  if (busy.value || !title.value.trim()) return
  busy.value = true
  error.value = ''
  try {
    if (space.value === 1 && !route.query.band_id) throw new Error('missingBand')
    let createdValue: Song | null = created.value
    if (!createdValue) {
      createdValue = await client.request<Song>('/songs', { method: 'POST', body: {
        title: title.value.trim(),
        ...(tempo.value !== '' ? { tempo: Number(tempo.value) } : {}),
        time_signature: meter.value,
        ...(key.value ? { key: key.value, key_mode: 'manual' } : {}),
        ...(space.value === 1 ? { owner_type: 'band', owner_id: route.query.band_id } : {}),
      } })
      created.value = createdValue
    }
    if (access.value === 1 && createdValue.visibility !== 'public') {
      createdValue = await client.request<Song>(`/songs/${encodeURIComponent(String(createdValue.id))}/visibility`, { method: 'PATCH', body: { visibility: 'public' } })
      created.value = createdValue
    }
    await router.push(songPath(createdValue))
  } catch (failure) {
    error.value = failure.message === 'missingBand' ? 'Selecciona una banda desde su espacio de trabajo.' : created.value ? 'La composición se creó, pero no se pudo publicar. Reintenta o ábrela desde tu lista.' : errorMessage(failure)
  } finally { busy.value = false }
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <BackBar></BackBar>
    <div class="mx-auto grid max-w-[1240px] gap-12 px-4 pb-16 pt-10 sm:px-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] lg:gap-14">
      <form @submit.prevent="create">
        <p v-if="error" role="alert">{{ error }}</p>
        <h1 class="text-[44px] leading-none sm:text-[56px]">Nueva composición</h1>
        <p class="mt-3 text-[17px]">Todo es opcional salvo el título. Podrás cambiarlo después.</p>

        <div class="mt-9">
          <label for="nc-title" class="field-label">Título</label>
          <input id="nc-title" v-model="title" :disabled="!!created" required type="text" class="field-input" />
        </div>
        <div class="mt-4 grid gap-3.5 sm:grid-cols-3">
          <div>
            <label for="nc-key" class="field-label">Tonalidad</label>
            <select id="nc-key" v-model="key" class="field-input"><option value="">Automática</option><option v-for="k in ['C','Dm','G','Am','F','Bb','Em','Bm','D','A','E','B','F#','C#','Ab','Eb','Db','Cm','Gm','Fm','Bbm','Ebm','F#m','C#m','G#m','D#m']" :key="k" :value="k">{{ k }}</option></select>
          </div>
          <div>
            <label for="nc-bpm" class="field-label">Tempo (bpm)</label>
            <input id="nc-bpm" v-model="tempo" type="number" min="20" max="400" class="field-input" />
          </div>
          <div>
            <label for="nc-meter" class="field-label">Compás</label>
            <select id="nc-meter" v-model="meter" class="field-input"><option>4/4</option><option>3/4</option><option>6/8</option></select>
          </div>
        </div>

        <p class="field-label mt-8">Espacio de trabajo</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <button v-for="(s, i) in spaces" :key="s.name" type="button" class="option-card" :class="space === i ? 'option-card-on' : ''" :aria-pressed="space === i ? 'true' : 'false'" :disabled="i === 1 && !route.query.band_id" @click="space = i">
            <b class="block font-semibold">{{ s.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ s.desc }}</span>
          </button>
        </div>

        <p class="field-label mt-8">Secciones</p>
        <div class="flex flex-wrap gap-2">
          <button v-for="p in parts" :key="p.name" type="button" class="toggle" :class="p.on ? 'toggle-on' : ''" :aria-pressed="p.on ? 'true' : 'false'" @click="p.on = !p.on">
            <span class="h-2.5 w-2.5 rounded-full" :class="p.on ? 'bg-brass-ink' : 'bg-fret'" aria-hidden="true"></span>{{ p.name }}
          </button>
        </div>

        <p class="field-label mt-8">Acceso</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <button v-for="(a, i) in accesses" :key="a.name" type="button" class="option-card" :class="access === i ? 'option-card-on' : ''" :aria-pressed="access === i ? 'true' : 'false'" @click="access = i">
            <b class="block font-semibold">{{ a.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ a.desc }}</span>
          </button>
        </div>

        <div class="mt-10 flex flex-wrap gap-3">
          <button type="submit" :disabled="busy || !title.trim()" class="btn-primary">{{ busy ? 'Guardando…' : created ? 'Reintentar publicación' : 'Crear composición' }}</button>
          <router-link to="/canciones" class="btn-ghost">Cancelar</router-link>
        </div>
      </form>

      <aside class="self-start rounded-md bg-surface bg-lamp px-6 pb-6 pt-16 sm:px-7" aria-label="Vista previa">
        <p class="text-sm text-muted">Así se verá en tu lista</p>
        <div class="mt-3.5 rounded-md bg-ground p-6">
          <p class="font-display text-[36px] leading-[1.05]">{{ title.trim() || 'Sin título' }}</p>
          <p class="mt-2 text-[15px] text-muted">{{ spaces[space].name }} · {{ key || 'Automática' }} · {{ tempo || '—' }} bpm · {{ meter }}</p>
          <div class="mt-4 flex flex-wrap gap-1.5"><span v-for="c in chosen" :key="c" class="chip text-[13px]">{{ c }}</span></div>
          <p class="mt-4 text-[15px]">{{ accessLine }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>
