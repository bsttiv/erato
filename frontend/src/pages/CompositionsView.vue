<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { songPath, type Song } from '../stores/song'
import { client } from '../stores/session'
import { errorMessage } from '../api/messages'
import AppShell from '../components/organisms/AppShell.vue'
import SongStatus from '../components/atoms/SongStatus.vue'
const route = useRoute()
const space = ref('personal')
const filter = ref('Todas')
const query = ref('')
type SongRow = Song & { updated_at: string }
const songs = ref<SongRow[]>([])
const loading = ref(false)
const error = ref('')
const filters = ['Todas', 'Públicas', 'Privadas']
const partFields: [keyof Song, string][] = [['lyrics', 'Letra'], ['chords', 'Acordes'], ['tablatures', 'Tablatura'], ['tasks', 'Tareas']]
const title = computed(() => space.value === 'band' ? 'Banda' : 'Personal')
const description = computed(() => space.value === 'band' ? 'Composiciones de la banda.' : 'Solo tú ves estas composiciones, salvo que invites a alguien.')
const rows = computed(() => songs.value
  .filter((song) => space.value !== 'band' || song.owner_type === 'band')
  .filter((song) => filter.value === 'Todas' || song.visibility === (filter.value === 'Públicas' ? 'public' : 'private'))
  .filter((song) => !query.value.trim() || `${song.title} ${song.key || ''}`.toLowerCase().includes(query.value.trim().toLowerCase()))
  .map((song) => ({ ...song, sub: song.owner_type === 'band' ? 'Banda' : 'Personal',
    parts: partFields.filter(([field]) => {
      const value = song[field]
      return !!value && (!Array.isArray(value) || value.length > 0)
    }).map(([, label]) => label),
    when: new Date(song.updated_at).toLocaleDateString('es'), access: song.visibility === 'public' ? 'Pública' : 'Privada' })))
let generation = 0
watch([space, () => route.query.band_id], async () => {
  const current = ++generation
  songs.value = []
  loading.value = true
  error.value = ''
  try {
    const path = space.value === 'personal' ? '/songs?workspace=personal' : route.query.band_id ? `/songs?workspace=band&band_id=${encodeURIComponent(String(route.query.band_id))}` : '/songs?workspace=all'
    const result = await client.request(path)
    if (current === generation) songs.value = result
  } catch (failure) { if (current === generation) error.value = errorMessage(failure) }
  finally { if (current === generation) loading.value = false }
}, { immediate: true })
const selectSpace = (value: string) => { space.value = value }
</script>

<template>
  <AppShell :space="space" @select-space="selectSpace">
    <div class="flex flex-wrap items-end justify-between gap-5">
      <div>
        <h1 class="text-[44px] leading-none sm:text-[56px]">{{ title }}</h1>
        <p class="mt-3 text-[17px]">{{ description }}</p>
      </div>
      <div class="flex flex-wrap gap-2.5">
        <router-link v-if="space === 'band' && route.query.band_id" :to="'/bandas/' + encodeURIComponent(String(route.query.band_id))" class="btn-ghost btn-sm">Integrantes</router-link>
        <router-link :to="{ path: '/canciones/nueva', query: space === 'band' ? route.query : {} }" class="btn-primary btn-sm">Nueva composición</router-link>
      </div>
    </div>

    <div class="mt-9 flex flex-wrap items-center justify-between gap-4">
      <div class="segmented" role="group" aria-label="Filtrar por acceso">
        <button v-for="f in filters" :key="f" type="button" class="segmented-item" :class="filter === f ? 'segmented-item-on' : ''" :aria-pressed="filter === f ? 'true' : 'false'" @click="filter = f">{{ f }}</button>
      </div>
      <div class="w-full sm:w-80">
        <label for="search" class="sr-only">Buscar composición</label>
        <input id="search" v-model="query" type="search" placeholder="Buscar por título o tonalidad" class="field-input min-h-[44px]" />
      </div>
    </div>

    <div class="mt-6">
      <p v-if="loading" role="status">Cargando composiciones…</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <div class="hidden grid-cols-[minmax(220px,2.2fr)_1fr_2fr_1fr_110px] gap-4 px-5 pb-2 text-[13px] text-muted lg:grid" aria-hidden="true">
        <span>Título</span><span>Tonalidad</span><span>Contenido</span><span>Actualizada</span><span>Acceso</span>
      </div>
      <router-link
        v-for="r in rows"
        :key="r.id"
        :to="songPath(r)"
        class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 rounded px-3 py-4 text-ink no-underline transition-colors hover:bg-surface hover:text-ink sm:px-5 lg:grid-cols-[minmax(220px,2.2fr)_1fr_2fr_1fr_110px]"
      >
        <span class="min-w-0">
          <span class="block font-display text-[26px] leading-tight">{{ r.title }}</span>
          <span class="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-sm text-muted"><SongStatus :status="r.status" /><span>{{ r.sub }}<span class="lg:hidden"> · {{ r.key }}</span></span></span>
        </span>
        <span class="hidden text-base lg:block">{{ r.key }}</span>
        <span class="hidden flex-wrap gap-1.5 lg:flex"><span v-for="p in r.parts" :key="p" class="chip text-[13px]">{{ p }}</span></span>
        <span class="hidden text-[15px] text-muted lg:block">{{ r.when }}</span>
        <span><span class="chip text-[13px]" :class="r.access === 'Pública' ? 'chip-on' : ''">{{ r.access }}</span></span>
      </router-link>
      <div v-if="!rows.length && !loading && !error" class="rounded-md bg-surface px-5 py-16 text-center">
        <p class="font-display text-[32px]">Ninguna canción coincide</p>
        <p class="mt-2.5 text-base">Prueba con otro título o crea una composición nueva.</p>
      </div>
    </div>
  </AppShell>
</template>
