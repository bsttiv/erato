<script setup>
import { ref, computed } from 'vue'
import CompositionHeader from '../components/app/CompositionHeader.vue'
import Fretboard from '../components/music/Fretboard.vue'
import PianoKeys from '../components/music/PianoKeys.vue'
import { chordFromFrets, chordFromKeys, keyFromShapes, keysFromFrets } from '../lib/chords.js'
import { songChords } from '../data/sample.js'

const selected = ref(3)
const instrument = ref('guitarra')
const frets = ref(songChords[3].frets.slice())
const keys = ref(keysFromFrets(songChords[3].frets))

const songKey = keyFromShapes(songChords.map((c) => c.frets))
const chord = computed(() =>
  instrument.value === 'guitarra' ? chordFromFrets(frets.value, songKey) : chordFromKeys(keys.value, songKey),
)
const usage = computed(() => (selected.value >= 0 ? songChords[selected.value].usage : 'Todavía no está en la letra. Guárdalo y arrástralo sobre una sílaba.'))

function choose(i) {
  selected.value = i
  frets.value = songChords[i].frets.slice()
  keys.value = keysFromFrets(songChords[i].frets)
}
function clearChord() {
  selected.value = -1
  frets.value = [-1, -1, -1, -1, -1, -1]
  keys.value = []
}
function setFrets(next) {
  frets.value = next
  keys.value = keysFromFrets(next)
}
const setKeys = (next) => (keys.value = next)
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="acordes" crumb="Acordes">
      <router-link to="/c/noche-de-otono" class="btn-ghost btn-sm">Cancelar</router-link>
      <router-link to="/c/noche-de-otono" class="btn-primary btn-sm">Guardar acorde</router-link>
    </CompositionHeader>

    <div class="grid gap-8 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[260px_minmax(0,1fr)] lg:gap-10">
      <aside aria-label="Acordes de la canción">
        <h1 class="text-[40px] leading-none">Acordes</h1>
        <p class="mt-2 text-[15px] text-muted">Elige uno para editarlo.</p>
        <div class="mt-5 grid grid-cols-3 gap-1 lg:grid-cols-1">
          <button
            v-for="(c, i) in songChords"
            :key="c.name"
            type="button"
            class="flex min-h-[52px] cursor-pointer items-center justify-between rounded border-0 px-4 text-left text-lg font-semibold text-ink transition-colors hover:bg-surface"
            :class="selected === i ? 'bg-raised' : 'bg-transparent'"
            :aria-pressed="selected === i ? 'true' : 'false'"
            @click="choose(i)"
          >
            {{ c.name }}<span v-if="selected === i" class="h-2 w-2 rounded-full bg-brass" aria-hidden="true"></span>
          </button>
        </div>
        <button type="button" class="btn-ghost mt-3.5 w-full" @click="clearChord">Acorde nuevo</button>
      </aside>

      <main class="min-w-0">
        <div class="rounded-md bg-surface bg-lamp p-5 sm:p-8">
          <div class="flex flex-wrap items-start justify-between gap-5">
            <div>
              <p class="text-sm text-muted">Nombre detectado</p>
              <p class="mt-1 font-display text-[72px] leading-none text-brass sm:text-[112px]" aria-live="polite">{{ chord.name }}</p>
              <p class="mt-2 text-lg">{{ chord.notes }}</p>
            </div>
            <div class="segmented bg-ground" role="group" aria-label="Instrumento">
              <button type="button" class="segmented-item" :class="instrument === 'guitarra' ? 'segmented-item-on' : ''" :aria-pressed="instrument === 'guitarra' ? 'true' : 'false'" @click="instrument = 'guitarra'">Guitarra</button>
              <button type="button" class="segmented-item" :class="instrument === 'piano' ? 'segmented-item-on' : ''" :aria-pressed="instrument === 'piano' ? 'true' : 'false'" @click="instrument = 'piano'">Piano</button>
            </div>
          </div>

          <div v-if="instrument === 'guitarra'" class="mt-9">
            <Fretboard :frets="frets" :fret-count="7" :show-notes="true" @change="setFrets"></Fretboard>
            <p class="mt-4 text-[15px] leading-normal text-muted">Toca un traste para poner un dedo. Toca la columna de la izquierda para dejar la cuerda al aire (○) o silenciarla (×).</p>
          </div>
          <div v-else class="mt-9">
            <PianoKeys :keys="keys" @change="setKeys"></PianoKeys>
            <p class="mt-4 text-[15px] leading-normal text-muted">La nota más grave que marques se toma como bajo del acorde.</p>
          </div>
        </div>

        <div class="mt-3.5 grid gap-3.5 md:grid-cols-2">
          <div class="card">
            <p class="text-sm text-muted">Se usa en</p>
            <p class="mt-2 text-[17px] leading-normal">{{ usage }}</p>
          </div>
          <div class="card">
            <label for="chord-alias" class="field-label">Nombre a mostrar (opcional)</label>
            <input id="chord-alias" type="text" :placeholder="chord.name" class="field-input-dark min-h-[44px]" />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
