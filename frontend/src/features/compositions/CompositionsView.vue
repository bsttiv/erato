<template>
  <div class="er-compositions-view">
    <div class="er-layout">
      <!-- Sidebar navigation -->
      <aside class="er-sidebar">
        <ErSideNav
          :items="navItems"
          :model-value="selectedId"
          brand="Erato"
          subtitle="cancionero"
          heading="composiciones"
          @update:model-value="onSelectComposition"
        />
        <div style="padding: var(--space-4)">
          <ErButton
            variant="primary"
            icon="plus"
            @click="showCreateModal = true"
          >
            Nueva composición
          </ErButton>
        </div>
      </aside>

      <!-- Main content area -->
      <main class="er-main">
        <div v-if="loading" class="er-loading">
          Cargando composiciones…
        </div>
        <div v-else-if="!selectedComposition" class="er-panel">
          Selecciona una composición o crea una nueva.
        </div>
        <CompositionDetailView
          v-else
          :composition="selectedComposition"
        />
      </main>
    </div>

    <!-- Create modal -->
    <CompositionCreateModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="onCompositionCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ErSideNav, ErButton, type SideNavItem } from '@/design-system'
import { listCompositions, type CompositionResponse, type CompositionListItem } from '@/api/compositions'
import CompositionDetailView from './CompositionDetailView.vue'
import CompositionCreateModal from './CompositionCreateModal.vue'

const compositions = ref<(CompositionListItem | CompositionResponse)[]>([])
const selectedId = ref<string>('')
const loading = ref(false)
const showCreateModal = ref(false)

const navItems = computed<SideNavItem[]>(() => {
  return compositions.value.map((c) => ({
    id: c.id,
    label: c.title,
    meta: c.visibility === 'public' ? 'Pública' : 'Privada',
  }))
})

const selectedComposition = computed<CompositionResponse | undefined>(() => {
  const c = compositions.value.find((item) => item.id === selectedId.value)
  if (!c) return undefined
  return {
    todos: [],
    members: [],
    demos: [],
    ...c,
    visibility: c.visibility,
  } as CompositionResponse
})

async function fetchCompositions() {
  loading.value = true
  try {
    const list = await listCompositions()
    compositions.value = list
    if (list.length && !selectedId.value) {
      selectedId.value = list[0].id
    }
  } catch {
    compositions.value = []
  } finally {
    loading.value = false
  }
}

function onSelectComposition(id: string) {
  selectedId.value = id
}

function onCompositionCreated(comp: CompositionResponse) {
  showCreateModal.value = false
  compositions.value.push(comp)
  selectedId.value = comp.id
}

onMounted(() => {
  fetchCompositions()
})
</script>
