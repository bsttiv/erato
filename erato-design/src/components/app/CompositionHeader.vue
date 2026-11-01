<script setup>
import Wordmark from '../ui/Wordmark.vue'
import { band } from '../../data/sample.js'

defineProps({
  active: { type: String, default: 'letra' },
  crumb: { type: String, default: '' },
})
const base = '/c/noche-de-otono'
const tabs = [
  { id: 'letra', label: 'Letra', to: base },
  { id: 'acordes', label: 'Acordes', to: base + '/acordes' },
  { id: 'tablatura', label: 'Tablatura', to: base + '/tablatura' },
  { id: 'demos', label: 'Demos', to: base + '/demos' },
]
</script>

<template>
  <header class="bg-[#17110d] px-4 pt-4 sm:px-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label="Ruta" class="flex min-w-0 flex-wrap items-center gap-2.5 text-[15px] text-muted">
        <Wordmark to="/composiciones" size="text-[26px]"></Wordmark>
        <span aria-hidden="true">/</span>
        <router-link to="/composiciones" class="text-muted">{{ band.name }}</router-link>
        <span aria-hidden="true">/</span>
        <router-link v-if="crumb" :to="base" class="text-muted">Noche de otoño</router-link>
        <span v-else>Noche de otoño</span>
        <template v-if="crumb"><span aria-hidden="true">/</span><span>{{ crumb }}</span></template>
      </nav>
      <div class="flex flex-wrap items-center gap-2.5">
        <slot></slot>
      </div>
    </div>
    <nav class="-mx-1 mt-4 flex gap-1 overflow-x-auto pb-2" aria-label="Secciones de la composición">
      <router-link v-for="t in tabs" :key="t.id" :to="t.to" class="tab" :class="active === t.id ? 'tab-on' : ''" :aria-current="active === t.id ? 'page' : null">{{ t.label }}</router-link>
    </nav>
  </header>
</template>
