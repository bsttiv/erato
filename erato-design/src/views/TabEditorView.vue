<script setup>
import { ref, computed } from 'vue'
import CompositionHeader from '../components/app/CompositionHeader.vue'
import { GUITAR_STRINGS } from '../lib/chords.js'

const strings = GUITAR_STRINGS
const STEPS_PER_BAR = 8
const grid = ref(strings.map(() => Array(16).fill('')))
grid.value[5][0] = '5'
grid.value[4][1] = '7'
grid.value[3][3] = '5'
grid.value[3][4] = '7'
grid.value[5][5] = '7h8'
grid.value[2][6] = '5b7'
grid.value[1][11] = '8'
grid.value[0][13] = '5'

const row = ref(2)
const col = ref(6)
const columns = computed(() => grid.value[0].length)
const gridStyle = computed(() => ({ gridTemplateColumns: '36px repeat(' + columns.value + ', minmax(40px, 1fr))', minWidth: 36 + columns.value * 44 + 'px' }))
const keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
const techniques = [
  { v: 'h', label: 'Hammer-on' },
  { v: 'p', label: 'Pull-off' },
  { v: 'b', label: 'Bend' },
  { v: '/', label: 'Slide' },
  { v: '~', label: 'Vibrato' },
  { v: 'x', label: 'Nota muerta' },
]
const status = computed(
  () => 'Cuerda ' + strings[row.value].name + ', tiempo ' + (col.value + 1) + ' · compás ' + (Math.floor(col.value / STEPS_PER_BAR) + 1) + '. Elige un traste y el cursor avanza solo.',
)

function select(r, c) {
  row.value = r
  col.value = c
}
function writeFret(v) {
  grid.value[row.value][col.value] = v
  col.value = Math.min(col.value + 1, columns.value - 1)
}
function writeTechnique(v) {
  grid.value[row.value][col.value] = grid.value[row.value][col.value] + v
}
function erase() {
  grid.value[row.value][col.value] = ''
}
function next() {
  col.value = Math.min(col.value + 1, columns.value - 1)
}
function addBar() {
  grid.value = grid.value.map((r) => r.concat(Array(STEPS_PER_BAR).fill('')))
}
function cellClass(r, c) {
  const v = grid.value[r][c]
  const selected = r === row.value && c === col.value
  return [
    c % STEPS_PER_BAR === STEPS_PER_BAR - 1 ? 'border-r-[3px] border-solid border-string' : '',
    c === col.value && !selected ? 'bg-brass/[.07]' : '',
    selected ? 'is-selected' : v ? 'has-value' : '',
  ]
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="tablatura" crumb="Tablatura">
      <router-link to="/c/noche-de-otono" class="btn-ghost btn-sm">Cancelar</router-link>
      <router-link to="/c/noche-de-otono" class="btn-primary btn-sm">Guardar tablatura</router-link>
    </CompositionHeader>

    <div class="px-4 pb-16 pt-8 sm:px-8">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-[40px] leading-none sm:text-[48px]">Riff del intro</h1>
          <p class="mt-2 text-base text-muted">Afinación estándar · {{ columns / 8 }} compases · editado por Leo el 21 sep</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn-ghost btn-sm" @click="addBar">Agregar compás</button>
          <button type="button" class="btn-ghost btn-sm">Nuevo riff</button>
        </div>
      </div>

      <div class="mt-7 grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="min-w-0 rounded-md bg-surface p-4 sm:p-6">
          <div class="overflow-x-auto">
            <div class="grid" :style="gridStyle" role="group" aria-label="Tablatura de seis cuerdas">
              <template v-for="(s, r) in strings" :key="s.name">
                <span class="flex h-[46px] items-center text-base font-semibold text-muted">{{ s.name }}</span>
                <button
                  v-for="(v, c) in grid[r]"
                  :key="c"
                  type="button"
                  class="group relative h-[46px] cursor-pointer border-0 bg-transparent p-0 text-lg font-semibold tabular-nums text-ink before:absolute before:inset-x-0 before:top-1/2 before:h-0.5 before:bg-fret before:content-['']"
                  :class="cellClass(r, c)"
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

        <aside class="card" aria-label="Teclado de trastes">
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
