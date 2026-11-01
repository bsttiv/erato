<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useCompositionPath } from '../api/compositionPath'
import { useSong, type SongTab } from '../stores/song'
import CompositionHeader from '../components/organisms/CompositionHeader.vue'
import { editTab, isValidCell, isCompleteTab, normalizeCell } from '../lib/tabEditor'

const compositionPath = useCompositionPath()
const { song, loading, error, canEdit, saving, conflicts, saveSections } = useSong()
const STEPS_PER_BAR = 8
const tuning = ['E4', 'B3', 'G3', 'D3', 'A2', 'E2']
const tabs = ref<SongTab[]>([])
const selectedTab = ref(0)
const row = ref(0)
const col = ref(0)
const editor = ref<HTMLDivElement | null>(null)
const activeTab = computed(() => tabs.value[selectedTab.value])
const strings = computed(() => (activeTab.value?.tuning || tuning).map((name) => ({ name })))
const tabColumns = computed(() => activeTab.value?.columns || [])
const columns = computed(() => tabColumns.value.length)
const grid = computed(() => strings.value.map((_, r) => tabColumns.value.map((column) => column[r])))
const complete = computed(() => tabs.value.every((tab) => isCompleteTab(tab.columns)))
const gridStyle = computed(() => ({ gridTemplateColumns: '36px repeat(' + columns.value + ', minmax(40px, 1fr))', minWidth: 36 + columns.value * 44 + 'px' }))
const keys = Array.from({ length: 25 }, (_, index) => String(index))
const techniques = [
  { v: 'h', label: 'Hammer-on' }, { v: 'p', label: 'Pull-off' },
  { v: 'b', label: 'Bend' }, { v: 'r', label: 'Release' },
  { v: '/', label: 'Slide ascendente' }, { v: '\\', label: 'Slide descendente' },
  { v: 's', label: 'Slide' }, { v: '~', label: 'Vibrato' },
  { v: 'v', label: 'Vibrato' }, { v: 'x', label: 'Nota muerta' },
  { v: '|', label: 'Barra de compás' },
]
const status = computed(() => {
  if (!activeTab.value) return 'No hay tablaturas.'
  const position = 'Cuerda ' + strings.value[row.value].name + ', tiempo ' + (col.value + 1) + '.'
  return position + (complete.value ? ' Usa las flechas para moverte; Espacio inserta una columna.' : ' Hay una celda incompleta: complétala o bórrala antes de guardar.')
})
watch(song, (value, previous) => {
  if (!value) return
  if (previous && value.id === previous.id && JSON.stringify(tabs.value) !== JSON.stringify(previous.tablatures || [])) return
  tabs.value = (JSON.parse(JSON.stringify(value.tablatures || [])) as SongTab[]).map((tab) => ({
    ...tab, columns: tab.columns.map((column) => column.map(normalizeCell)),
  }))
  selectedTab.value = Math.min(selectedTab.value, Math.max(0, tabs.value.length - 1))
  row.value = 0
  col.value = 0
}, { immediate: true })

function select(r: number, c: number) {
  row.value = r
  col.value = c
  editor.value?.focus()
}
function chooseTab() {
  row.value = 0
  col.value = 0
}
function applyKey(event: { key: string }) {
  if (!canEdit.value || !activeTab.value) return
  const draft = editTab({ columns: tabColumns.value, row: row.value, col: col.value }, event)
  activeTab.value.columns = draft.columns
  row.value = draft.row
  col.value = draft.col
}
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    ;(event.target as HTMLElement).blur()
    return
  }
  if (!canEdit.value || event.ctrlKey || event.metaKey || event.altKey) return
  if (/^[0-9hpbr/\\sxX~v|]$/.test(event.key) || ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' ', 'Backspace', 'Delete'].includes(event.key)) {
    event.preventDefault()
    applyKey(event)
  }
}
function writeFret(value: string) {
  applyKey({ key: 'Delete' })
  for (const key of value) applyKey({ key })
  editor.value?.focus()
}
function writeTechnique(key: string) {
  applyKey({ key })
  editor.value?.focus()
}
function erase() { applyKey({ key: 'Delete' }) }
function next() { applyKey({ key: 'ArrowRight' }) }
function addBar() {
  if (!canEdit.value || !activeTab.value) return
  activeTab.value.columns.push(...Array.from({ length: STEPS_PER_BAR }, () => Array(6).fill('')))
}
function newTab() {
  if (!canEdit.value) return
  tabs.value.push({ title: 'Tablatura ' + (tabs.value.length + 1), tuning: [...tuning], columns: Array.from({ length: 16 }, () => Array(6).fill('')) })
  selectedTab.value = tabs.value.length - 1
  chooseTab()
}
function removeTab() {
  if (!canEdit.value) return
  tabs.value.splice(selectedTab.value, 1)
  selectedTab.value = Math.max(0, selectedTab.value - 1)
  chooseTab()
}
async function save() {
  if (!canEdit.value || !complete.value) return
  const submitted = JSON.stringify(tabs.value)
  const result = await saveSections({ tabs: tabs.value })
  if (result && !result.conflicts?.some((conflict) => conflict.section === 'tabs') && JSON.stringify(tabs.value) === submitted) tabs.value = JSON.parse(JSON.stringify(result.song.tablatures))
}
function cellClass(r: number, c: number) {
  const value = grid.value[r][c]
  const selected = r === row.value && c === col.value
  return [
    c % STEPS_PER_BAR === STEPS_PER_BAR - 1 ? 'border-r-[3px] border-solid border-string' : '',
    c === col.value && !selected ? 'bg-brass/[.07]' : '',
    selected ? 'is-selected' : value ? 'has-value' : '',
  ]
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="tablatura" crumb="Tablatura">
      <router-link :to="compositionPath" class="btn-ghost btn-sm">Cancelar</router-link>
      <button v-if="canEdit" type="button" class="btn-primary btn-sm" :disabled="saving || !complete" @click="save">Guardar tablatura</button>
    </CompositionHeader>

    <div class="px-4 pb-16 pt-8 sm:px-8">
      <p v-if="loading" role="status">Cargando tablatura…</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-if="conflicts.some((conflict) => conflict.section === 'tabs')" role="alert">La tablatura cambió en otra sesión. Tu versión no se guardó; conserva tus cambios antes de recargar.</p>
      <label v-if="tabs.length" class="er-label" for="tab-choice">Tablatura</label>
      <select v-if="tabs.length" id="tab-choice" v-model="selectedTab" class="btn-ghost btn-sm" @change="chooseTab">
        <option v-for="(tab, index) in tabs" :key="tab.id || index" :value="index">{{ tab.title }}</option>
      </select>
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <input v-if="activeTab && canEdit" v-model="activeTab.title" aria-label="Título de la tablatura" class="text-[40px] leading-none sm:text-[48px] bg-transparent" />
          <h1 v-else class="text-[40px] leading-none sm:text-[48px]">{{ activeTab?.title || 'Tablaturas' }}</h1>
          <p class="mt-2 text-base text-muted">{{ strings.map((string) => string.name).join(' · ') }} · {{ columns }} tiempos</p>
        </div>
        <div v-if="canEdit" class="flex flex-wrap gap-2">
          <button type="button" class="btn-ghost btn-sm" :disabled="!activeTab" @click="addBar">Agregar compás</button>
          <button type="button" class="btn-ghost btn-sm" @click="newTab">Nuevo riff</button>
          <button v-if="activeTab" type="button" class="btn-ghost btn-sm" @click="removeTab">Borrar tablatura</button>
        </div>
      </div>

      <div class="mt-7 grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="min-w-0 rounded-md bg-surface p-4 sm:p-6">
          <div class="overflow-x-auto">
            <div ref="editor" class="grid" :style="gridStyle" role="group" tabindex="0" aria-label="Tablatura de seis cuerdas" @keydown="onKeydown">
              <template v-for="(s, r) in strings" :key="s.name">
                <span class="flex h-[46px] items-center text-base font-semibold text-muted">{{ s.name }}</span>
                <button
                  v-for="(v, c) in grid[r]"
                  :key="c"
                  type="button"
                  class="group relative h-[46px] cursor-pointer border-0 bg-transparent p-0 text-lg font-semibold tabular-nums text-ink before:absolute before:inset-x-0 before:top-1/2 before:h-0.5 before:bg-fret before:content-['']"
                  :class="cellClass(r, c)"
                  :aria-invalid="!isValidCell(v) || undefined"
                  :aria-label="'Cuerda ' + s.name + ', tiempo ' + (c + 1) + (v ? ': ' + v : ': vacío')"
                  @click="select(r, c)"
                >
                  <span
                    class="relative z-10 inline-flex h-[30px] min-w-[30px] items-center justify-center rounded px-1 group-hover:bg-raised"
                    :class="r === row && c === col ? 'bg-brass text-brass-ink group-hover:bg-brass' : v ? 'bg-surface' : ''"
                  >{{ v }}</span>
                </button>
              </template>
            </div>
          </div>
          <p class="mt-4 text-[15px] text-muted" aria-live="polite">{{ status }}</p>
        </div>

        <aside v-if="canEdit && activeTab" class="card" aria-label="Teclado de trastes">
          <h2 class="text-[26px]">Traste</h2>
          <div class="mt-3.5 grid grid-cols-4 gap-1.5 sm:grid-cols-8 xl:grid-cols-4">
            <button v-for="k in keys" :key="k" type="button" class="min-h-[52px] cursor-pointer rounded border-0 bg-raised text-xl font-semibold text-ink transition hover:bg-[#35281d] active:scale-95" @click="writeFret(k)">{{ k }}</button>
          </div>
          <h2 class="mt-6 text-[26px]">Técnica</h2>
          <div class="mt-3.5 grid grid-cols-3 gap-1.5 sm:grid-cols-6 xl:grid-cols-3">
            <button v-for="t in techniques" :key="t.v" type="button" class="min-h-[52px] cursor-pointer rounded border-0 bg-raised text-base font-medium text-ink transition hover:bg-[#35281d] active:scale-95" :aria-label="t.label" :title="t.label" @click="writeTechnique(t.v)">{{ t.v }}</button>
          </div>
          <div class="mt-4 grid grid-cols-2 gap-1.5">
            <button type="button" class="btn-ghost" @click="erase">Borrar</button>
            <button type="button" class="btn-ghost" @click="next">Siguiente →</button>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>
