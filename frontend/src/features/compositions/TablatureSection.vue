<template>
  <section class="er-section" id="sec-tablature">
    <div class="er-tabs-strip">
      <!-- Tab selector when not renaming -->
      <ErSegmented
        v-if="!isRenaming && localTabs.length > 0"
        role="tablist"
        label="Partes de tablatura"
        :model-value="activeId"
        :options="segmentedOptions"
        @update:model-value="onSelectTab"
      />

      <!-- Inline rename form -->
      <div v-else-if="isRenaming" class="er-tab-actions" role="group" aria-label="Renombrar tablatura">
        <input
          v-model="renameValue"
          type="text"
          class="er-input"
          maxlength="80"
          data-test="rename-tab-input"
          @keydown.enter.prevent="saveRename"
          @keydown.esc="cancelRename"
        />
        <ErButton
          size="sm"
          variant="primary"
          data-test="save-rename-btn"
          @click="saveRename"
        >
          Guardar
        </ErButton>
        <ErButton
          size="sm"
          variant="ghost"
          data-test="cancel-rename-btn"
          @click="cancelRename"
        >
          Cancelar
        </ErButton>
      </div>

      <!-- Action buttons -->
      <div v-if="editable" class="er-tab-actions">
        <ErButton
          size="sm"
          variant="quiet"
          icon="plus"
          data-test="add-tab-btn"
          @click="onAddTab"
        >
          + Agregar
        </ErButton>

        <template v-if="activeTab && !isRenaming">
          <ErButton
            size="sm"
            variant="ghost"
            data-test="rename-tab-btn"
            @click="startRename"
          >
            Renombrar
          </ErButton>

          <template v-if="!confirmDelete">
            <ErButton
              size="sm"
              variant="ghost"
              data-test="delete-tab-btn"
              @click="confirmDelete = true"
            >
              Borrar
            </ErButton>
          </template>
          <template v-else>
            <span class="er-kbd">¿Borrar?</span>
            <ErButton
              size="sm"
              variant="danger"
              data-test="confirm-delete-btn"
              @click="onDeleteTab"
            >
              Sí
            </ErButton>
            <ErButton
              size="sm"
              variant="ghost"
              data-test="cancel-delete-btn"
              @click="confirmDelete = false"
            >
              No
            </ErButton>
          </template>

          <ErButton
            size="sm"
            variant="ghost"
            :disabled="isFirstTab"
            aria-label="Mover hacia la izquierda"
            @click="moveTab(-1)"
          >
            ◀
          </ErButton>
          <ErButton
            size="sm"
            variant="ghost"
            :disabled="isLastTab"
            aria-label="Mover hacia la derecha"
            @click="moveTab(1)"
          >
            ▶
          </ErButton>
        </template>
      </div>
    </div>

    <!-- Active Tab Editor or Empty state -->
    <ErTabEditor
      v-if="activeTab"
      :key="activeTab.id"
      :model-value="activeTab.columns"
      :readonly="!editable"
      @update:model-value="onColumnsUpdate"
    />
    <div v-else class="er-empty">
      <p>No hay tablaturas guardadas</p>
      <ErButton
        v-if="editable"
        size="sm"
        variant="quiet"
        icon="plus"
        data-test="add-tab-btn"
        @click="onAddTab"
      >
        + Agregar tablatura
      </ErButton>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import ErButton from '@/design-system/components/ErButton.vue'
import ErSegmented from '@/design-system/components/ErSegmented.vue'
import ErTabEditor from '@/design-system/components/ErTabEditor.vue'
import { newTabEntry, type TabEntry, type TabColumn } from '@/design-system/core/tab'

const props = withDefaults(
  defineProps<{
    tabs?: TabEntry[]
    editable?: boolean
  }>(),
  {
    tabs: () => [],
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'update:tabs', tabs: TabEntry[]): void
  (e: 'change', tabs: TabEntry[]): void
}>()

const localTabs = ref<TabEntry[]>([])
const activeId = ref<string>('')
const isRenaming = ref<boolean>(false)
const renameValue = ref<string>('')
const confirmDelete = ref<boolean>(false)

function initFromProps() {
  const incoming = Array.isArray(props.tabs) ? props.tabs : []
  localTabs.value = incoming.map((t) => ({
    ...t,
    columns: Array.isArray(t.columns) ? [...t.columns] : [],
  }))

  if (localTabs.value.length > 0) {
    if (!activeId.value || !localTabs.value.some((t) => t.id === activeId.value)) {
      activeId.value = localTabs.value[0].id
    }
  } else {
    activeId.value = ''
  }
}

initFromProps()

watch(
  () => props.tabs,
  () => {
    initFromProps()
  },
  { deep: true }
)

const segmentedOptions = computed(() =>
  localTabs.value.map((t) => ({
    value: t.id,
    label: t.title,
  }))
)

const activeTab = computed(() => {
  return localTabs.value.find((t) => t.id === activeId.value) || null
})

const activeIndex = computed(() => {
  return localTabs.value.findIndex((t) => t.id === activeId.value)
})

const isFirstTab = computed(() => activeIndex.value <= 0)
const isLastTab = computed(() => activeIndex.value >= localTabs.value.length - 1)

function onSelectTab(id: string) {
  activeId.value = id
  confirmDelete.value = false
  isRenaming.value = false
}

function onAddTab() {
  const newTab = newTabEntry(localTabs.value.length)
  localTabs.value.push(newTab)
  activeId.value = newTab.id
  confirmDelete.value = false
  isRenaming.value = false
  notifyChange()
}

function startRename() {
  if (!activeTab.value) return
  renameValue.value = activeTab.value.title
  isRenaming.value = true
}

function saveRename() {
  if (!activeTab.value) return
  const trimmed = renameValue.value.trim()
  if (trimmed) {
    activeTab.value.title = trimmed
    notifyChange()
  }
  isRenaming.value = false
}

function cancelRename() {
  isRenaming.value = false
}

function onDeleteTab() {
  const idx = activeIndex.value
  if (idx !== -1) {
    localTabs.value.splice(idx, 1)
    if (localTabs.value.length > 0) {
      const nextIdx = Math.min(idx, localTabs.value.length - 1)
      activeId.value = localTabs.value[nextIdx].id
    } else {
      activeId.value = ''
    }
    confirmDelete.value = false
    notifyChange()
  }
}

function moveTab(delta: number) {
  const from = activeIndex.value
  const to = from + delta
  if (from === -1 || to < 0 || to >= localTabs.value.length) return

  const item = localTabs.value.splice(from, 1)[0]
  localTabs.value.splice(to, 0, item)
  notifyChange()
}

function onColumnsUpdate(cols: TabColumn[]) {
  if (!activeTab.value) return
  activeTab.value.columns = cols
  notifyChange()
}

function notifyChange() {
  const payload = localTabs.value.map((t) => ({ ...t, columns: [...t.columns] }))
  emit('update:tabs', payload)
  emit('change', payload)
}
</script>
