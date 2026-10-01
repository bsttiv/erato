<template>
  <div class="er-comp-detail">
    <div class="er-comp-header er-row" style="justify-content: space-between; align-items: center">
      <div>
        <h2 class="er-comp-title">
          {{ composition.title }}
        </h2>
        <div class="er-comp-meta er-row" style="gap: var(--space-2); align-items: center">
          <ErTag :tone="composition.is_public ? 'moss' : 'neutral'">
            {{ composition.is_public ? 'Pública' : 'Privada' }}
          </ErTag>
          <ErTag class="er-role-tag" :tone="roleTone">
            {{ roleLabel }}
          </ErTag>
        </div>
      </div>

      <div v-if="canEdit" class="er-row" style="gap: var(--space-2)">
        <ErButton class="er-save-btn" variant="primary" @click="saveAll">
          Guardar cambios
        </ErButton>
      </div>
    </div>

    <!-- Layout of design-system components -->
    <div class="er-comp-grid">
      <div class="er-comp-column">
        <ErLyricsViewer
          :lyrics="lyricsText"
          :title="`Letra — ${composition.title}`"
        />
        <ErTodoList
          v-model="todoItems"
          title="Tareas y arreglos"
        />
      </div>

      <div class="er-comp-column">
        <ErChordEditor
          :default-frets="chordFrets"
          :default-instrument="chordInstrument"
          :editable="canEdit"
          @change="onChordChange"
        />
        <ErTabEditor
          v-model="tabCols"
          title="Tablatura"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  ErButton,
  ErTag,
  ErChordEditor,
  ErTabEditor,
  ErLyricsViewer,
  ErTodoList,
  type TodoItem,
  type TabColumn,
  type ChordValue,
} from '@/design-system'
import { updateSection, type CompositionResponse } from '@/api/compositions'

const props = defineProps<{
  composition: CompositionResponse
}>()

const canEdit = computed(() => {
  return props.composition.user_role === 'owner' || props.composition.user_role === 'editor'
})

const roleLabel = computed(() => {
  if (props.composition.user_role === 'owner') return 'Dueño'
  if (props.composition.user_role === 'editor') return 'Editor'
  return 'Lector'
})

const roleTone = computed(() => {
  if (props.composition.user_role === 'owner') return 'amber'
  if (props.composition.user_role === 'editor') return 'wine'
  return 'neutral'
})

// Section models
const chordsData = ref(props.composition.sections?.chords || {})
const chordFrets = computed(() => chordsData.value?.frets || [-1, 3, 2, 0, 1, 0])
const chordInstrument = computed(() => chordsData.value?.instrument || 'guitar')

const tabCols = ref<TabColumn[]>(props.composition.sections?.tab?.columns || [])
const lyricsText = computed(() => props.composition.sections?.lyrics?.text || '')
const todoItems = ref<TodoItem[]>(props.composition.sections?.todos?.items || [])

function onChordChange(val: ChordValue) {
  chordsData.value = val
}

async function saveAll() {
  if (!canEdit.value) return
  await Promise.all([
    updateSection(props.composition.id, 'chords', chordsData.value).catch(() => {}),
    updateSection(props.composition.id, 'tab', { columns: tabCols.value }).catch(() => {}),
    updateSection(props.composition.id, 'todos', { items: todoItems.value }).catch(() => {}),
  ])
}
</script>
