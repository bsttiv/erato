<script setup>
import { ref, computed } from 'vue'
import AppShell from '../components/app/AppShell.vue'
import { compositions, band } from '../data/sample.js'

const space = ref('band')
const filter = ref('Todas')
const query = ref('')
const filters = ['Todas', 'Públicas', 'Privadas']

const title = computed(() => (space.value === 'band' ? band.name : 'Personal'))
const description = computed(() =>
  space.value === 'band'
    ? band.members.length + ' integrantes · todas las composiciones son visibles para la banda.'
    : 'Solo tú ves estas composiciones, salvo que invites a alguien.',
)
const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  return compositions[space.value]
    .filter((r) => filter.value === 'Todas' || (filter.value === 'Públicas' ? r.access === 'Pública' : r.access === 'Privada'))
    .filter((r) => !q || (r.title + ' ' + r.key).toLowerCase().includes(q))
})
const selectSpace = (s) => (space.value = s)
</script>

<template>
  <AppShell :space="space" @select-space="selectSpace">
    <div class="flex flex-wrap items-end justify-between gap-5">
      <div>
        <h1 class="text-[44px] leading-none sm:text-[56px]">{{ title }}</h1>
        <p class="mt-3 text-[17px]">{{ description }}</p>
      </div>
      <div class="flex flex-wrap gap-2.5">
        <router-link v-if="space === 'band'" to="/bandas/nueva" class="btn-ghost btn-sm">Integrantes</router-link>
        <router-link to="/composiciones/nueva" class="btn-primary btn-sm">Nueva composición</router-link>
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
      <div class="hidden grid-cols-[minmax(220px,2.2fr)_1fr_2fr_1fr_110px] gap-4 px-5 pb-2 text-[13px] text-muted lg:grid" aria-hidden="true">
        <span>Título</span><span>Tonalidad</span><span>Contenido</span><span>Actualizada</span><span>Acceso</span>
      </div>
      <router-link
        v-for="r in rows"
        :key="r.title"
        to="/c/noche-de-otono"
        class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 rounded px-3 py-4 text-ink no-underline transition-colors hover:bg-surface hover:text-ink sm:px-5 lg:grid-cols-[minmax(220px,2.2fr)_1fr_2fr_1fr_110px]"
      >
        <span class="min-w-0">
          <span class="block font-display text-[26px] leading-tight">{{ r.title }}</span>
          <span class="mt-1 block text-sm text-muted">{{ r.sub }}<span class="lg:hidden"> · {{ r.key }}</span></span>
        </span>
        <span class="hidden text-base lg:block">{{ r.key }}</span>
        <span class="hidden flex-wrap gap-1.5 lg:flex"><span v-for="p in r.parts" :key="p" class="chip text-[13px]">{{ p }}</span></span>
        <span class="hidden text-[15px] text-muted lg:block">{{ r.when }}</span>
        <span><span class="chip text-[13px]" :class="r.access === 'Pública' ? 'chip-on' : ''">{{ r.access }}</span></span>
      </router-link>
      <div v-if="!rows.length" class="rounded-md bg-surface px-5 py-16 text-center">
        <p class="font-display text-[32px]">Ninguna canción coincide</p>
        <p class="mt-2.5 text-base">Prueba con otro título o crea una composición nueva.</p>
      </div>
    </div>
  </AppShell>
</template>
