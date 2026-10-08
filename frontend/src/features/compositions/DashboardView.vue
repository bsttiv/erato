<template>
  <div class="er-app-main">
    <header class="er-topbar">
      <router-link to="/" class="er-topbar-brand">
        <ErBrand />
      </router-link>

      <div class="er-field-row">
        <AppNavExtras />
        <router-link to="/compositions/new" class="er-btn er-btn--primary">
          Nueva canción
        </router-link>
        <div class="er-avatar" aria-label="Avatar del usuario">
          {{ userInitials }}
        </div>
      </div>
    </header>

    <main class="er-dash">
      <section class="er-dash-hero">
        <div class="er-label">
          // LA BANDA
        </div>
        <h1 class="er-dash-headline">
          Composiciones
        </h1>
        <p class="er-hint">
          Todo lo que la banda escribió. Acordes, tablaturas, letras y demos en un mismo lugar.
        </p>
      </section>

      <div class="er-filterbar">
        <ErSegmented
          v-model="filterMode"
          label="Filtrar por estado"
          :options="filterOptions"
        />
        <span class="er-dash-count">
          {{ countText }} · recientes
        </span>
      </div>

      <div class="er-comp-grid">
        <CompositionCard
          v-for="(comp, i) in filteredCompositions"
          :key="comp.id"
          :composition="comp"
          :index="i"
        />

        <router-link to="/compositions/new" class="er-card-new">
          <ErIcon name="plus" />
          <span>Empieza una canción nueva</span>
        </router-link>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ErSegmented, ErIcon, ErBrand, type SegmentedOption } from '@/design-system'
import { listCompositions, type CompositionListItem } from '@/api/compositions'
import { getMe } from '@/api/auth'
import CompositionCard from './CompositionCard.vue'
import AppNavExtras from '@/shared/AppNavExtras.vue'
import { statusLabel } from './status'

const compositions = ref<CompositionListItem[]>([])
const loading = ref(false)
const userInitials = ref('ER')
const filterMode = ref<'todas' | 'in_progress' | 'ready' | 'idea'>('todas')

const filterOptions: SegmentedOption[] = [
  { value: 'todas', label: 'Todas' },
  { value: 'in_progress', label: statusLabel('in_progress') },
  { value: 'ready', label: 'Listas' },
  { value: 'idea', label: 'Ideas' },
]

const filteredCompositions = computed(() => {
  if (filterMode.value === 'todas') {
    return compositions.value
  }
  return compositions.value.filter((c) => c.status === filterMode.value)
})

const countText = computed(() => {
  const n = filteredCompositions.value.length
  return n === 1 ? '1 canción' : `${n} canciones`
})

onMounted(async () => {
  loading.value = true
  try {
    const [list, user] = await Promise.all([
      listCompositions(),
      getMe().catch(() => null),
    ])
    compositions.value = list

    if (user && user.display_name) {
      const parts = user.display_name.trim().split(/\s+/)
      if (parts.length >= 2) {
        userInitials.value = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      } else {
        userInitials.value = parts[0].slice(0, 2).toUpperCase()
      }
    }
  } catch {
    compositions.value = []
  } finally {
    loading.value = false
  }
})
</script>
