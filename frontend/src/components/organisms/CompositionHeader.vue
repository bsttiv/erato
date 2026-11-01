<script setup lang="ts">
import { computed } from 'vue'
import { useCompositionPath } from '../../api/compositionPath'
import Wordmark from '../atoms/Wordmark.vue'
import { useSong } from '../../stores/song'
const { song, isPublic } = useSong()

defineProps<{ active?: string; crumb?: string }>()
const base = useCompositionPath()
const tabs = computed(() => [
  { id: 'letra', label: 'Letra', to: base.value },
  { id: 'acordes', label: 'Acordes', to: base.value + '/acordes' },
  { id: 'tablatura', label: 'Tablatura', to: base.value + '/tablatura' },
  { id: 'demos', label: 'Demos', to: base.value + '/demos' },
  // History needs an account: public links have no revisions route.
  ...(isPublic?.value ? [] : [{ id: 'historial', label: 'Historial', to: base.value + '/historial' }]),
])
</script>

<template>
  <header class="bg-[#17110d] px-4 pt-4 sm:px-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label="Ruta" class="flex min-w-0 flex-wrap items-center gap-2.5 text-[15px] text-muted">
        <Wordmark to="/canciones" size="text-[26px]"></Wordmark>
        <span aria-hidden="true">/</span>
        <router-link to="/canciones" class="text-muted">{{ song?.owner_type === 'band' ? 'Banda' : 'Personal' }}</router-link>
        <span aria-hidden="true">/</span>
        <router-link v-if="crumb" :to="base" class="text-muted">{{ song?.title || 'Composición' }}</router-link>
        <span v-else>{{ song?.title || 'Composición' }}</span>
        <template v-if="crumb"><span aria-hidden="true">/</span><span>{{ crumb }}</span></template>
      </nav>
      <div class="flex flex-wrap items-center gap-2.5">
        <slot></slot>
      </div>
    </div>
    <nav class="-mx-1 mt-4 flex gap-1 overflow-x-auto pb-2" aria-label="Secciones de la composición">
      <router-link v-for="t in tabs" :key="t.id" :to="t.to" class="tab" :class="active === t.id ? 'tab-on' : ''" :aria-current="active === t.id ? 'page' : undefined">{{ t.label }}</router-link>
    </nav>
  </header>
</template>
