<template>
  <div :class="['er-tab', 'er-panel', customClass]">
    <div class="er-tab-bar">
      <div v-if="title" class="er-label" style="margin-right: auto">
        // {{ title }}
      </div>
      <span v-else style="margin-right: auto" />

      <ErButton
        size="sm"
        variant="ghost"
        icon="bar"
        @click="onAddBar"
      >
        compás
      </ErButton>
      <ErButton
        size="sm"
        variant="quiet"
        icon="plus"
        @click="onAddEight"
      >
        8 tiempos
      </ErButton>
    </div>

    <div
      ref="gridRef"
      class="er-tab-grid"
      tabindex="0"
      role="grid"
      aria-label="Tablatura: usa las flechas y escribe números de traste"
      @keydown="handleKeyDown"
    >
      <div class="er-tab-names" aria-hidden="true">
        <span v-for="(n, i) in stringNames" :key="i">{{ n }}</span>
      </div>

      <template v-for="(col, c) in cols" :key="`c-${c}`">
        <div
          v-if="col === '|'"
          :class="['er-tab-barline', sel.c === c && 'is-sel']"
          @click="onPick(c, sel.s)"
        >
          <i />
        </div>
        <div
          v-else
          :class="['er-tab-col', sel.c === c && 'er-tab-colsel']"
        >
          <div
            v-for="(v, s) in col"
            :key="`cell-${c}-${s}`"
            role="gridcell"
            :aria-selected="sel.c === c && sel.s === s"
            :class="['er-tab-cell', sel.c === c && sel.s === s && 'is-sel']"
            @mousedown.prevent="onPick(c, s)"
          >
            <b v-if="v">{{ v }}</b>
          </div>
        </div>
      </template>
    </div>

    <div v-if="!hideHint" class="er-tab-hint">
      <span class="er-kbd">0–24</span> traste ·
      <span class="er-kbd">h p b / ~ x</span> técnica ·
      <span class="er-kbd">← → ↑ ↓</span> moverse ·
      <span class="er-kbd">espacio</span> avanzar ·
      <span class="er-kbd">enter</span> insertar tiempo ·
      <span class="er-kbd">|</span> compás
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import ErButton from './ErButton.vue'
import { blankTab, type TabColumn } from '../core/tab'
import { useTabKeyboard } from '../composables/useTabKeyboard'

const props = withDefaults(
  defineProps<{
    modelValue?: TabColumn[]
    defaultValue?: TabColumn[]
    columns?: number
    strings?: string[]
    title?: string
    hideHint?: boolean
    customClass?: string
  }>(),
  {
    columns: 16,
    hideHint: false,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', cols: TabColumn[]): void
  (e: 'change', cols: TabColumn[]): void
}>()

const stringNames = props.strings || ['e', 'B', 'G', 'D', 'A', 'E']
const initialCols = props.modelValue || props.defaultValue || blankTab(props.columns)
const cols = ref<TabColumn[]>(initialCols.slice())
const gridRef = ref<HTMLElement | null>(null)

const { sel, onKey, insert, pick } = useTabKeyboard(cols, { names: stringNames })

watch(
  cols,
  (newCols) => {
    emit('update:modelValue', newCols)
    emit('change', newCols)
  },
  { deep: true }
)

function handleKeyDown(e: KeyboardEvent) {
  onKey(e)
}

function onPick(c: number, s: number) {
  pick(c, s)
  gridRef.value?.focus()
}

function onAddBar() {
  insert('|')
  gridRef.value?.focus()
}

function onAddEight() {
  cols.value = cols.value.concat(blankTab(8))
  gridRef.value?.focus()
}
</script>
