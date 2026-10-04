<template>
  <AppModal
    :open="open"
    :title="title"
    @close="emit('close')"
  >
    <div class="er-history-panel">
      <!-- Loading state -->
      <div v-if="loading" class="er-history-loading">
        Cargando historial...
      </div>

      <!-- Plan gate notice (when plan denies history) -->
      <div v-else-if="planGateNotice" class="er-history-notice">
        <p class="er-history-notice-title">Función no disponible</p>
        <p class="er-history-notice-msg">
          El historial de versiones no está disponible en tu plan actual.
        </p>
      </div>

      <!-- General error -->
      <div v-else-if="error" class="er-history-error">
        <p>{{ error }}</p>
      </div>

      <!-- History list & preview -->
      <div v-else class="er-history-body">
        <div v-if="items.length === 0" class="er-history-empty">
          No hay versiones anteriores guardadas para esta sección.
        </div>

        <div v-else class="er-history-content">
          <ul class="er-history-list" aria-label="Lista de versiones">
            <li
              v-for="item in items"
              :key="item.rev"
              :class="['er-history-item', { 'er-history-item--selected': selectedRev === item.rev }]"
            >
              <div class="er-history-item-info">
                <span class="er-history-item-rev">Versión {{ item.rev }}</span>
                <span v-if="item.author?.display_name" class="er-history-item-author">
                  por {{ item.author.display_name }}
                </span>
                <span class="er-history-item-date">{{ formatDate(item.created_at) }}</span>
              </div>

              <div class="er-history-item-actions">
                <button
                  type="button"
                  class="er-btn er-btn--sm"
                  data-test="preview-history-item-btn"
                  :disabled="restoringRev !== null"
                  @click="onSelectPreview(item.rev)"
                >
                  {{ selectedRev === item.rev ? 'Viendo' : 'Ver' }}
                </button>
                <button
                  v-if="canEdit"
                  type="button"
                  class="er-btn er-btn--sm er-btn--primary"
                  data-test="restore-history-btn"
                  :disabled="restoringRev !== null"
                  @click="onRestore(item.rev)"
                >
                  {{ restoringRev === item.rev ? 'Restaurando...' : 'Restaurar' }}
                </button>
              </div>
            </li>
          </ul>

          <div v-if="nextBeforeRev" class="er-history-more">
            <button
              type="button"
              class="er-btn"
              data-test="load-more-history-btn"
              :disabled="loadingMore"
              @click="onLoadMore"
            >
              {{ loadingMore ? 'Cargando...' : 'Cargar más versiones' }}
            </button>
          </div>

          <!-- Preview panel -->
          <div v-if="selectedRev !== null" class="er-history-preview">
            <div class="er-history-preview-header">
              <span class="er-label">Vista previa (Versión {{ selectedRev }})</span>
            </div>
            <div v-if="loadingPreview" class="er-history-preview-loading">
              Cargando vista previa...
            </div>
            <pre v-else class="er-history-preview-text">{{ previewText }}</pre>
          </div>
        </div>
      </div>
    </div>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import AppModal from '@/shared/AppModal.vue'
import {
  listSectionHistory,
  getHistoryRevision,
  restoreSectionHistory,
  type HistoryItemSummary,
} from '@/api/history'
import { formatDate } from '@/design-system/core/format'
import type { VersionedSectionKey, SectionConflict } from './useSectionSave'

const props = withDefaults(
  defineProps<{
    open: boolean
    compositionId: string
    section: VersionedSectionKey
    currentRev: number
    canEdit?: boolean
  }>(),
  {
    canEdit: true,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'restored', payload: { section: VersionedSectionKey; rev: number; content: any }): void
  (e: 'conflict', conflict: SectionConflict): void
}>()

const sectionLabels: Record<VersionedSectionKey, string> = {
  lyrics: 'letra',
  chords: 'acordes',
  tablature: 'tablatura',
}

const title = computed(() => {
  const name = sectionLabels[props.section] || props.section
  return `Historial de ${name}`
})

const items = ref<HistoryItemSummary[]>([])
const nextBeforeRev = ref<number | null | undefined>(undefined)
const loading = ref(false)
const loadingMore = ref(false)
const error = ref<string | null>(null)
const planGateNotice = ref(false)

const selectedRev = ref<number | null>(null)
const previewRaw = ref<any>(null)
const loadingPreview = ref(false)
const restoringRev = ref<number | null>(null)

const previewText = computed(() => {
  if (!previewRaw.value) return ''
  const c = previewRaw.value.content !== undefined ? previewRaw.value.content : previewRaw.value
  if (typeof c === 'string') return c
  if (c && typeof c.text === 'string') return c.text
  if (c && typeof c.content === 'string') return c.content
  if (c && Array.isArray(c.entries)) {
    return c.entries.map((e: any) => e.name || e.chord || JSON.stringify(e)).join(', ')
  }
  if (c && Array.isArray(c.tabs)) {
    return c.tabs.map((t: any) => t.title || t.name || 'Parte').join('\n')
  }
  return JSON.stringify(c, null, 2)
})

async function loadHistory() {
  if (!props.compositionId || !props.open) return
  loading.value = true
  error.value = null
  planGateNotice.value = false
  selectedRev.value = null
  previewRaw.value = null

  try {
    const res = await listSectionHistory(props.compositionId, props.section, 20)
    items.value = res.items || []
    nextBeforeRev.value = res.next_before_rev
  } catch (err: any) {
    if (err?.status === 403 && (err?.code === 'plan_gate_history' || err?.body?.error === 'plan_gate_history')) {
      planGateNotice.value = true
    } else {
      error.value = err?.message || 'Error al cargar el historial'
    }
  } finally {
    loading.value = false
  }
}

async function onLoadMore() {
  if (!props.compositionId || nextBeforeRev.value === undefined || nextBeforeRev.value === null || loadingMore.value) {
    return
  }
  loadingMore.value = true
  try {
    const res = await listSectionHistory(props.compositionId, props.section, 20, nextBeforeRev.value)
    items.value = [...items.value, ...(res.items || [])]
    nextBeforeRev.value = res.next_before_rev
  } catch (err: any) {
    error.value = err?.message || 'Error al cargar más versiones'
  } finally {
    loadingMore.value = false
  }
}

async function onSelectPreview(rev: number) {
  if (selectedRev.value === rev) {
    selectedRev.value = null
    previewRaw.value = null
    return
  }

  selectedRev.value = rev
  loadingPreview.value = true
  try {
    const res = await getHistoryRevision(props.compositionId, props.section, rev)
    previewRaw.value = res
  } catch (err: any) {
    previewRaw.value = 'No se pudo cargar la vista previa.'
  } finally {
    loadingPreview.value = false
  }
}

async function onRestore(rev: number) {
  if (restoringRev.value !== null) return
  restoringRev.value = rev

  try {
    const res = await restoreSectionHistory(props.compositionId, props.section, rev, props.currentRev)
    emit('restored', {
      section: props.section,
      rev: res.rev,
      content: res,
    })
    emit('close')
  } catch (err: any) {
    const reason = err?.body || err
    if (err?.status === 409 || err?.code === 'section_conflict' || reason?.error === 'section_conflict') {
      const conflict: SectionConflict = {
        section: (reason.section || props.section) as VersionedSectionKey,
        current_rev: reason.current_rev ?? 0,
        content: reason.content,
        author: reason.author ?? null,
        updated_at: reason.updated_at,
      }
      emit('conflict', conflict)
      emit('close')
    } else if (err?.status === 403 && (err?.code === 'plan_gate_history' || reason?.error === 'plan_gate_history')) {
      planGateNotice.value = true
    } else {
      error.value = err?.message || 'Error al restaurar la versión'
    }
  } finally {
    restoringRev.value = null
  }
}

watch(
  () => [props.open, props.compositionId, props.section],
  ([newOpen]) => {
    if (newOpen) {
      loadHistory()
    }
  },
  { immediate: true }
)
</script>
