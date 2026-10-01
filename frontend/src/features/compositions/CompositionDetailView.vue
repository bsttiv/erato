<template>
  <div v-if="loading" class="er-loading">
    Cargando composición...
  </div>
  <div v-else-if="!comp" class="er-empty">
    No se encontró la composición.
  </div>
  <div v-else :class="['er-layout', { 'er-layout--noside': !showSidebar }]">
    <!-- Persistent sidebar for authenticated users -->
    <aside v-if="showSidebar" class="er-sidebar">
      <ErSideNav
        :items="sidebarNavItems"
        :model-value="comp.id"
        @select="onSelectComposition"
      />
      <div class="er-sidebar-foot">
        <router-link to="/">
          ← todas las composiciones
        </router-link>
      </div>
    </aside>

    <!-- Main composition content -->
    <main class="er-main">
      <div class="er-comp-detail">
        <!-- Top header -->
        <header class="er-comp-header">
          <div>
            <nav class="er-crumb" aria-label="Miga de pan">
              <router-link to="/">
                composiciones
              </router-link>
              <span> / </span>
              <span>{{ comp.title }}</span>
            </nav>

            <div class="er-field-row">
              <h1 class="er-comp-title">
                {{ comp.title }}
              </h1>
              <span class="er-savestate">{{ saveStateText }}</span>
            </div>

            <div class="er-comp-meta">
              <ErTag v-if="comp.key" tone="neutral">
                {{ comp.key }}
              </ErTag>
              <ErTag v-if="comp.bpm" tone="neutral">
                {{ comp.bpm }} bpm
              </ErTag>
              <ErTag v-if="comp.time_signature" tone="neutral">
                {{ comp.time_signature }}
              </ErTag>
              <ErTag
                v-for="tag in comp.style_tags || []"
                :key="tag"
                tone="neutral"
              >
                {{ tag }}
              </ErTag>
              <ErTag :tone="isPublic ? 'moss' : 'neutral'">
                {{ isPublic ? 'Pública' : 'Privada' }}
              </ErTag>
              <ErTag class="er-role-tag" :tone="roleTone">
                {{ roleLabel }}
              </ErTag>
            </div>
          </div>

          <div class="er-field-row">
            <!-- Member avatar stack -->
            <div v-if="comp.members && comp.members.length" class="er-avatars">
              <span
                v-for="m in comp.members"
                :key="m.user_id"
                class="er-avatar"
                :title="m.display_name || undefined"
              >
                {{ m.initials }}
              </span>
            </div>

            <!-- Action buttons for editor / owner -->
            <div v-if="canEdit" class="er-comp-tags">
              <ErButton
                data-test="share-btn"
                variant="ghost"
                @click="showShareModal = true"
              >
                Compartir
              </ErButton>
              <ErButton
                class="er-save-btn"
                variant="primary"
                :disabled="isSaving"
                @click="saveAll"
              >
                Guardar cambios
              </ErButton>
            </div>
          </div>
        </header>

        <!-- Jump nav strip with live counts -->
        <nav class="er-sectionnav" aria-label="Secciones de la composición">
          <a v-if="isSectionEnabled('lyrics')" href="#sec-lyrics">letra</a>
          <a v-if="isSectionEnabled('chords')" href="#sec-chords">acordes {{ chordCount }}</a>
          <a v-if="isSectionEnabled('tablature')" href="#sec-tablature">tablatura {{ tabCount }}</a>
          <a v-if="isSectionEnabled('demos')" href="#sec-demos">demos {{ demoCount }}</a>
          <a v-if="isSectionEnabled('todos')" href="#sec-todos">tareas {{ todosDoneCount }}/{{ todosTotalCount }}</a>
        </nav>

        <!-- Two-column band: Lyrics & Todos -->
        <div class="er-comp-columns">
          <div class="er-comp-column">
            <LyricsSection
              v-if="isSectionEnabled('lyrics')"
              id="sec-lyrics"
              :lyrics="lyricsText"
              :title="`Letra — ${comp.title}`"
              :chords="compChords"
              :editable="canEdit"
              @update:lyrics="onLyricsUpdate"
            />
          </div>

          <div class="er-comp-column">
            <section
              v-if="isSectionEnabled('todos')"
              id="sec-todos"
              class="er-section"
            >
              <ErTodoList
                v-model="todoItems"
                title="Tareas y arreglos"
              />
            </section>
          </div>
        </div>

        <!-- Stacked panels: Chords, Tablature, Demos -->
        <ChordGrid
          v-if="isSectionEnabled('chords')"
          id="sec-chords"
          :chords="compChords"
          :editable="canEdit"
          @update:chords="onChordsUpdate"
        />

        <TablatureSection
          v-if="isSectionEnabled('tablature')"
          id="sec-tablature"
          :tabs="compTabs"
          :editable="canEdit"
          @update:tabs="onTabsUpdate"
        />

        <section
          v-if="isSectionEnabled('demos')"
          id="sec-demos"
          class="er-section"
        >
          <DemosSection
            :composition-id="comp.id"
            :demos="compDemos"
            :can-edit="canEdit"
            @updated="onDemosUpdated"
          />
        </section>

        <!-- Sharing modal -->
        <SharingModal
          v-if="showShareModal && comp"
          :composition-id="comp.id"
          :title="comp.title"
          :visibility="comp.visibility"
          :share-slug="comp.share_slug"
          :can-manage="canEdit"
          @close="showShareModal = false"
          @visibility-changed="onVisibilityChanged"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ErButton,
  ErTag,
  ErTodoList,
  ErSideNav,
  type SideNavItem,
  type TodoItem,
} from '@/design-system'
import ChordGrid from './ChordGrid.vue'
import TablatureSection from './TablatureSection.vue'
import LyricsSection from './LyricsSection.vue'
import DemosSection from '@/features/demos/DemosSection.vue'
import SharingModal from '@/features/sharing/SharingModal.vue'
import type { TabEntry } from '@/design-system/core/tab'
import {
  getComposition,
  getCompositionBySlug,
  listCompositions,
  updateSection,
  type CompositionResponse,
  type CompositionListItem,
  type ChordsSection,
  type SectionsEnabled,
} from '@/api/compositions'
import type { DemoTake } from '@/design-system'

const props = defineProps<{
  composition?: CompositionResponse | null
}>()

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const isSaving = ref(false)
const saveStateText = ref('guardado')
const showShareModal = ref(false)

const comp = ref<CompositionResponse | null>(props.composition || null)
const sidebarList = ref<CompositionListItem[]>([])

// Section states
const compChords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
const compTabs = ref<TabEntry[]>([])
const lyricsText = ref('')
const todoItems = ref<TodoItem[]>([])
const compDemos = ref<DemoTake[]>([])

function normalizeCompositionData(c: CompositionResponse) {
  // Chords
  if (c.chords && c.chords.entries) {
    compChords.value = {
      instrument: c.chords.instrument || 'guitar',
      entries: [...c.chords.entries],
    }
  } else if (c.sections?.chords) {
    const legacy = c.sections.chords as any
    if (legacy.entries) {
      compChords.value = {
        instrument: legacy.instrument || 'guitar',
        entries: [...legacy.entries],
      }
    } else if (legacy.frets) {
      compChords.value = {
        instrument: legacy.instrument || 'guitar',
        entries: [{ bar: 1, notes: legacy.frets, name: 'Acorde' }],
      }
    }
  } else {
    compChords.value = { instrument: 'guitar', entries: [] }
  }

  // Tablature
  if (c.tablature && c.tablature.tabs && c.tablature.tabs.length > 0) {
    compTabs.value = c.tablature.tabs.map((t) => ({
      ...t,
      columns: Array.isArray(t.columns) ? [...t.columns] : [],
    }))
  } else if (c.sections?.tab?.columns) {
    compTabs.value = [
      {
        id: 'tab-1',
        title: 'Tablatura',
        strings: 6,
        columns: [...c.sections.tab.columns],
      },
    ]
  } else {
    compTabs.value = []
  }

  // Lyrics
  lyricsText.value = c.lyrics?.content || c.sections?.lyrics?.text || ''

  // Todos
  if (c.todos && c.todos.length > 0) {
    todoItems.value = c.todos.map((t, idx) => ({
      id: t.id || `todo-${idx}`,
      text: t.text,
      done: t.done,
    }))
  } else if (c.sections?.todos?.items) {
    todoItems.value = c.sections.todos.items.map((t: any, idx: number) => ({
      id: t.id || `todo-${idx}`,
      text: t.text,
      done: t.done,
    }))
  } else {
    todoItems.value = []
  }

  // Demos
  compDemos.value = (c.demos || []).map((d: any) => ({
    id: d.id || d.demo_id || '',
    title: d.title || 'Demo',
    duration: d.duration || d.duration_s || 0,
    date: d.date || d.uploaded_at,
    note: d.note,
    src: d.src,
    comments: d.comments || [],
  }))
}

watch(
  () => props.composition,
  (newVal) => {
    if (newVal) {
      comp.value = newVal
      normalizeCompositionData(newVal)
    }
  },
  { immediate: true, deep: true }
)

const canEdit = computed(() => {
  return comp.value?.user_role === 'owner' || comp.value?.user_role === 'editor'
})

const isPublic = computed(() => {
  return comp.value?.visibility === 'public' || comp.value?.is_public === true
})

const showSidebar = computed(() => {
  if (!comp.value) return false
  if (route?.name === 'composition-public') {
    return !!comp.value.user_role
  }
  return comp.value.user_role !== undefined
})

const roleLabel = computed(() => {
  if (comp.value?.user_role === 'owner') return 'Dueño'
  if (comp.value?.user_role === 'editor') return 'Editor'
  return 'Lector'
})

const roleTone = computed(() => {
  if (comp.value?.user_role === 'owner') return 'amber'
  if (comp.value?.user_role === 'editor') return 'wine'
  return 'neutral'
})

const sidebarNavItems = computed<SideNavItem[]>(() => {
  return sidebarList.value.map((item) => ({
    id: item.id,
    label: item.title,
    meta: item.key || undefined,
  }))
})

function isSectionEnabled(sec: keyof SectionsEnabled): boolean {
  if (!comp.value?.sections_enabled) return true
  return comp.value.sections_enabled[sec] !== false
}

// Live counts for jump nav
const chordCount = computed(() => compChords.value.entries?.length || 0)

const tabCount = computed(() => {
  return compTabs.value.length
})

const demoCount = computed(() => compDemos.value.length)

const todosDoneCount = computed(() => {
  return todoItems.value.filter((t) => t.done).length
})

const todosTotalCount = computed(() => {
  return todoItems.value.length
})

function onChordsUpdate(val: ChordsSection) {
  compChords.value = val
}

function onTabsUpdate(val: TabEntry[]) {
  compTabs.value = val
}

function onLyricsUpdate(val: string) {
  lyricsText.value = val
}

function onDemosUpdated(demos: DemoTake[]) {
  compDemos.value = demos
}

function onSelectComposition(id: string) {
  if (router) {
    router.push(`/compositions/${id}`)
  }
}

function onVisibilityChanged(vis: any) {
  if (comp.value) {
    comp.value.visibility = (typeof vis === 'string' ? vis : (vis ? 'public' : 'private')) as any
  }
}

async function loadData() {
  if (!props.composition && route) {
    loading.value = true
    try {
      if (route.name === 'composition-public' && route.params.slug) {
        const res = await getCompositionBySlug(route.params.slug as string)
        comp.value = res
        normalizeCompositionData(res)
      } else if (route.params.id) {
        const res = await getComposition(route.params.id as string)
        comp.value = res
        normalizeCompositionData(res)
      }
    } catch {
      comp.value = null
    } finally {
      loading.value = false
    }
  }

  // Load sidebar list if authenticated
  if (comp.value?.user_role) {
    try {
      const list = await listCompositions()
      sidebarList.value = list
    } catch {
      // Fallback
    }
  }
}

async function saveAll() {
  if (!canEdit.value || !comp.value) return
  isSaving.value = true
  saveStateText.value = 'guardando...'

  try {
    await Promise.all([
      updateSection(comp.value.id, 'chords', compChords.value).catch(() => {}),
      updateSection(comp.value.id, 'tablature', { tabs: compTabs.value }).catch(() => {}),
      updateSection(comp.value.id, 'lyrics', { content: lyricsText.value }).catch(() => {}),
      updateSection(comp.value.id, 'todos', { items: todoItems.value }).catch(() => {}),
    ])
    saveStateText.value = 'guardado'
  } catch {
    saveStateText.value = 'error al guardar'
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
