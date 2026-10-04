<template>
  <div v-if="loading" class="er-loading">
    Cargando composición...
  </div>
  <div v-else-if="!comp" class="er-empty">
    No se encontró la composición.
  </div>
  <div v-else :class="['er-layout', { 'er-layout--noside': !showSidebar }]">
    <!-- Mobile drawer backdrop -->
    <div
      v-if="showSidebar && drawer.open.value"
      class="er-drawer-backdrop"
      @click="drawer.close"
    />

    <!-- Persistent sidebar for authenticated users -->
    <aside
      v-if="showSidebar"
      id="er-sidebar"
      ref="sidebarRef"
      :class="['er-sidebar', { 'er-sidebar--open': drawer.open.value }]"
    >
      <ErSideNav
        :items="sidebarNavItems"
        :model-value="comp.id"
        @select="onSelectComposition"
      />
    </aside>

    <!-- Main composition content -->
    <main class="er-main">
      <div class="er-comp-detail">
        <!-- Top header -->
        <header class="er-comp-header">
          <!-- Navigation & Actions bar -->
          <div class="er-comp-header-nav">
            <div class="er-comp-header-nav-left">
              <button
                v-if="showSidebar"
                ref="toggleRef"
                type="button"
                class="er-drawer-toggle"
                aria-label="Abrir menú"
                aria-controls="er-sidebar"
                :aria-expanded="drawer.open.value ? 'true' : 'false'"
                @click="drawer.toggle"
              >
                <ErIcon name="menu" />
              </button>

              <router-link to="/" class="er-comp-back-btn" aria-label="Todas las composiciones">
                ← todas las composiciones
              </router-link>

              <nav class="er-crumb" aria-label="Miga de pan">
                <router-link to="/">
                  composiciones
                </router-link>
                <span> / </span>
                <span>{{ comp.title }}</span>
              </nav>
            </div>

            <div class="er-comp-header-nav-right">
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
          </div>

          <!-- Title bar: space-between layout for title and savestate -->
          <div class="er-comp-title-row">
            <h1 class="er-comp-title">
              {{ comp.title }}
            </h1>
            <span class="er-savestate">{{ saveStateText }}</span>
          </div>

          <!-- Metadata chips bar -->
          <div class="er-comp-meta">
            <ErSegmented
              v-if="canEdit"
              data-test="status-segmented"
              :model-value="comp.status || 'idea'"
              :options="STATUS_OPTIONS"
              label="Estado"
              :disabled="isUpdatingStatus"
              @update:model-value="onStatusChange"
            />
            <ErTag v-else :tone="statusTone" dot>
              {{ statusLabel(comp.status) }}
            </ErTag>
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
              @open-history="activeHistorySection = 'lyrics'"
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
          @open-history="activeHistorySection = 'chords'"
        />

        <TablatureSection
          v-if="isSectionEnabled('tablature')"
          id="sec-tablature"
          :tabs="compTabs"
          :editable="canEdit"
          @update:tabs="onTabsUpdate"
          @open-history="activeHistorySection = 'tablature'"
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

        <SectionConflictDialog
          :open="!!activeConflict"
          :conflict="activeConflict"
          :is-saving="isSaving"
          @close="dismissConflict"
          @overwrite="activeConflict && resolveOverwrite(activeConflict)"
          @load-saved="activeConflict && resolveLoadSaved(activeConflict)"
        />

        <SectionHistoryPanel
          v-if="comp && activeHistorySection"
          :open="!!activeHistorySection"
          :composition-id="comp.id"
          :section="activeHistorySection"
          :current-rev="activeHistoryCurrentRev"
          :can-edit="canEdit"
          @close="activeHistorySection = null"
          @restored="onHistoryRestored"
          @conflict="onHistoryConflict"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ErButton,
  ErTag,
  ErTodoList,
  ErSideNav,
  ErSegmented,
  ErIcon,
  formatDate,
  type SideNavItem,
  type TodoItem,
  type Tone,
} from '@/design-system'
import { useDrawer } from '@/shared/useDrawer'
import ChordGrid from './ChordGrid.vue'
import TablatureSection from './TablatureSection.vue'
import LyricsSection from './LyricsSection.vue'
import DemosSection from '@/features/demos/DemosSection.vue'
import { resolveCompositionRef } from './resolveCompositionRef'
import SharingModal from '@/features/sharing/SharingModal.vue'
import SectionConflictDialog from './SectionConflictDialog.vue'
import SectionHistoryPanel from './SectionHistoryPanel.vue'
import { useSectionSave, type VersionedSectionKey, type SectionConflict } from './useSectionSave'
import {
  normalizeChords,
  normalizeTablature,
  normalizeLyrics,
} from './normalizeSection'
import { STATUS_OPTIONS, statusLabel } from './status'
import type { TabEntry } from '@/design-system/core/tab'
import {
  getComposition,
  listCompositions,
  updateComposition,
  type CompositionResponse,
  type CompositionListItem,
  type CompositionStatus,
  type ChordsSection,
  type SectionsEnabled,
} from '@/api/compositions'
import type { DemoTake } from '@/design-system'

const props = defineProps<{
  composition?: CompositionResponse | null
}>()

const route = useRoute()
const router = useRouter()

const drawer = useDrawer()
const toggleRef = ref<HTMLButtonElement | null>(null)
const sidebarRef = ref<HTMLElement | null>(null)

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && drawer.open.value) {
    drawer.close()
  }
}

watch(drawer.open, async (isOpen, wasOpen) => {
  if (isOpen) {
    await nextTick()
    const firstLink = sidebarRef.value?.querySelector('a') as HTMLElement | null
    firstLink?.focus()
  } else if (wasOpen) {
    toggleRef.value?.focus()
  }
})

watch(
  () => route?.fullPath,
  () => {
    if (drawer.open.value) {
      drawer.close()
    }
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})

const loading = ref(false)
const showShareModal = ref(false)

const comp = ref<CompositionResponse | null>(props.composition || null)
const sidebarList = ref<CompositionListItem[]>([])

// Section states
const compChords = ref<ChordsSection>({ instrument: 'guitar', entries: [] })
const compTabs = ref<TabEntry[]>([])
const lyricsText = ref('')
const todoItems = ref<TodoItem[]>([])
const compDemos = ref<DemoTake[]>([])

const {
  revisions,
  conflicts,
  save: saveSections,
  resetBaselines,
  activeConflict,
  resolveOverwrite,
  resolveLoadSaved,
  dismissConflict,
  isSaving,
  saveStateText,
} = useSectionSave({
  compositionId: () => comp.value?.id,
  initialRevs: () => comp.value?.section_revs,
  chords: () => compChords.value,
  tabs: () => compTabs.value,
  lyrics: () => lyricsText.value,
  todos: () => todoItems.value,
  onLoadSection: (section, content) => {
    if (section === 'lyrics') {
      lyricsText.value = normalizeLyrics(content)
    } else if (section === 'chords') {
      compChords.value = normalizeChords(content)
    } else if (section === 'tablature') {
      compTabs.value = normalizeTablature(content)
    }
  },
})

const activeHistorySection = ref<VersionedSectionKey | null>(null)

const activeHistoryCurrentRev = computed(() => {
  if (!activeHistorySection.value) return 0
  return revisions.value[activeHistorySection.value] ?? 0
})

function onHistoryRestored(payload: { section: VersionedSectionKey; rev: number; content: any }) {
  const { section, rev, content } = payload
  if (section === 'lyrics') {
    const norm = normalizeLyrics(content.content !== undefined ? content.content : content)
    lyricsText.value = norm
    resetBaselines({ lyrics: norm, revs: { lyrics: rev } })
  } else if (section === 'chords') {
    const norm = normalizeChords(content.content !== undefined ? content.content : content)
    compChords.value = norm
    resetBaselines({ chords: norm, revs: { chords: rev } })
  } else if (section === 'tablature') {
    const norm = normalizeTablature(content.content !== undefined ? content.content : content)
    compTabs.value = norm
    resetBaselines({ tabs: norm, revs: { tablature: rev } })
  }
}

function onHistoryConflict(conflict: SectionConflict) {
  const alreadyQueued = conflicts.value.some((c) => c.section === conflict.section)
  if (!alreadyQueued) {
    conflicts.value.push(conflict)
  }
}

function normalizeCompositionData(c: CompositionResponse) {
  // Chords
  compChords.value = normalizeChords(c.chords || c.sections?.chords)

  // Tablature
  compTabs.value = normalizeTablature(c.tablature || c.sections?.tab)

  // Lyrics
  lyricsText.value = normalizeLyrics(c.lyrics || c.sections?.lyrics)

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
    date: formatDate(d.date || d.uploaded_at),
    note: d.note,
    src: d.src,
    comments: d.comments || [],
  }))

  resetBaselines({
    lyrics: lyricsText.value,
    chords: compChords.value,
    tabs: compTabs.value,
    todos: todoItems.value,
    revs: c.section_revs,
  })
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

const statusTone = computed<Tone>(() => {
  switch (comp.value?.status) {
    case 'in_progress':
      return 'amber'
    case 'ready':
      return 'moss'
    case 'idea':
    default:
      return 'neutral'
  }
})

const isUpdatingStatus = ref(false)

async function onStatusChange(newStatus: string) {
  if (!comp.value || isUpdatingStatus.value) return
  const prevStatus = comp.value.status || 'idea'
  if (newStatus === prevStatus) return

  // Optimistic update
  comp.value.status = newStatus as CompositionStatus
  isUpdatingStatus.value = true

  try {
    await updateComposition(comp.value.id, { status: newStatus as CompositionStatus })
    saveStateText.value = 'guardado'
  } catch (err: any) {
    // Revert optimistic update
    comp.value.status = prevStatus
    saveStateText.value = 'No se pudo guardar el estado. Intenta de nuevo.'
  } finally {
    isUpdatingStatus.value = false
  }
}

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
      if (route.name === 'composition-public' && route.params.ref) {
        const res = await resolveCompositionRef(route.params.ref as string)
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
  await saveSections()
}

onMounted(() => {
  loadData()
})
</script>
