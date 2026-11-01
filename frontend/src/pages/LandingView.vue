<script setup lang="ts">
import { ref, computed } from 'vue'
import LandingNav from '../components/organisms/LandingNav.vue'
import FeatureSection from '../components/organisms/FeatureSection.vue'
import SiteFooter from '../components/organisms/SiteFooter.vue'
import SongStatus from '../components/atoms/SongStatus.vue'
import ChordDiagram from '../components/atoms/ChordDiagram.vue'
import Waveform from '../components/atoms/Waveform.vue'
import ChordHint from '../components/molecules/ChordHint.vue'
import { GUITAR_STRINGS, type Chord } from '../lib/chords'
import type { SheetLine } from '../lib/lyrics'
import StageLamp from '../components/atoms/StageLamp.vue'
import Fretboard from '../components/atoms/Fretboard.vue'
import LyricSheet from '../components/molecules/LyricSheet.vue'
import DemoPlayer from '../components/organisms/DemoPlayer.vue'
import BandCard from '../components/molecules/BandCard.vue'
import HistoryList from '../components/molecules/HistoryList.vue'
import ShareLinkBar from '../components/molecules/ShareLinkBar.vue'
import { songLines, songChords, takes, band, history, formatTime } from '../data/sample'
import { chordFromFrets } from '../lib/chordDetection'
import { useLampSwing } from '../lib/useLampSwing'

// Adapt the marketing fixtures to the same chord and lyric contracts as the app.
const shapes = [
  ...songChords,
  { name: 'F#m7b5', frets: [0, 1, 2, 2, -1, 2] },
  { name: 'B7', frets: [2, 0, 2, 1, 2, -1] },
  { name: 'Em', frets: [0, 0, 0, 2, 2, 0] },
  { name: 'A7', frets: [0, 2, 0, 2, 0, -1] },
  { name: 'G', frets: [3, 0, 0, 0, 2, 3] },
]
function guitarChord(name: string, frets: number[]): Chord {
  return {
    id: name, name, instrument: 'guitar',
    strings: frets.flatMap((fret, index) => fret < 0 ? [] : [index + 1]),
    frets: frets.filter(fret => fret >= 0),
    notes: frets.flatMap((fret, index) => fret < 0 ? [] : [GUITAR_STRINGS[index].midi + fret]),
  }
}
const previewChords = shapes.map(shape => guitarChord(shape.name, shape.frets))
const previewLines: SheetLine[] = songLines.map(line => ({
  ...line,
  chords: Array.from((line.chords || '').matchAll(/\S+/g), match => ({ col: match.index!, chord_id: match[0] })),
}))
const hint = ref<{ chord: Chord; anchor: DOMRect } | null>(null)
function showHint(event: Event, chord: Chord) {
  hint.value = { chord, anchor: (event.currentTarget as HTMLElement).getBoundingClientRect() }
}
// Free-text samples use the same focusable hints without changing shared demo/history components.
const chordTokens = (text: string) => text.split(/(Gmaj7|G)(?=\s|$)/).filter(Boolean)
const tokenChord = (token: string) => previewChords.find(chord => chord.name === token)

const heroTabs = ['Letra', 'Acordes', 'Tablatura', 'Demos']
const heroTab = ref('Letra')
const introRiff = `e|-----------|-----5----|
B|-----------|---8------|
G|-------5b7-|----------|
D|---5-7-----|----------|
A|-7---------|----------|
E|5---7h8----|----------|`

const heroChecks = ['No se requiere pago', 'Herramientas curadas', 'Interfaz amigable', 'Edición colaborativa']

const heroLamp = ref<InstanceType<typeof StageLamp> | null>(null)
const heroLight = ref<HTMLElement | null>(null)
const closingLamp = ref<InstanceType<typeof StageLamp> | null>(null)
const closingLight = ref<HTMLElement | null>(null)
useLampSwing(heroLamp, heroLight)
useLampSwing(closingLamp, closingLight, 130)

// Escribir: el acorde se nombra solo
const CMAJ7 = [0, 0, 0, 2, 3, -1]
const frets = ref(CMAJ7.slice())
const chord = computed(() => chordFromFrets(frets.value))
const detectedChord = computed(() => guitarChord(chord.value.name, frets.value))
const setFrets = (next: number[]) => (frets.value = next)
const resetChord = () => (frets.value = CMAJ7.slice())

// Leer: desplazamiento automático
const speed = ref(1)
const rollStyle = computed(() => ({ animationDuration: (36 / speed.value).toFixed(1) + 's' }))
const slower = () => (speed.value = Math.max(0.5, Math.round((speed.value - 0.1) * 10) / 10))
const faster = () => (speed.value = Math.min(2.5, Math.round((speed.value + 0.1) * 10) / 10))
const readingLines = previewLines.slice(0, 8)

// Escuchar
const selectedTake = ref(0)

const steps = [
  { title: 'Regístrate', text: 'Crea una cuenta gratis para acceder a todas las características.' },
  { title: 'Crea una composición', text: 'Ponle título, tonalidad y tempo, y elige qué secciones vas a usar.' },
  { title: 'Ponle música', text: 'Agrega las letras, los acordes y las tablaturas.' },
  { title: 'Finaliza', text: 'Deja tu composición guardada y compártela con los demás.' },
]
</script>

<template>
  <div class="overflow-x-hidden bg-ground text-ink">
    <LandingNav></LandingNav>

    <!-- Inicio -->
    <section class="relative pb-20 pt-10 sm:pb-28 lg:pb-32 lg:pt-16">
      <div class="page-x grid items-center gap-14 lg:grid-cols-[minmax(0,6fr)_minmax(0,6fr)] lg:gap-16">
        <div>
          <p class="text-[15px] text-muted">Open source · AGPL-3.0 · para bandas y compositores</p>
          <h1 class="mt-5 text-[56px] leading-[0.95] tracking-[-0.03em] sm:text-[80px] lg:text-[96px] xl:text-[112px]">El cancionero moderno y open source</h1>
          <p class="mt-7 max-w-[34ch] text-xl leading-normal sm:text-[22px]">Organiza, compone y comparte tus composiciones en un mismo lugar.</p>
          <div class="mt-9 flex flex-wrap gap-3">
            <router-link to="/registro" class="btn-primary min-h-[52px] px-7 text-[17px]">Empieza gratis</router-link>
            <a href="#escribir" class="btn-ghost min-h-[52px] px-7 text-[17px]">Revisa las características</a>
          </div>
          <ul class="mt-10 grid list-none grid-cols-1 gap-x-8 gap-y-3 p-0 text-base sm:grid-cols-2">
            <li v-for="c in heroChecks" :key="c" class="flex items-center gap-3">
              <svg width="16" height="12" viewBox="0 0 16 12" aria-hidden="true" class="shrink-0"><path d="M1 6 L5.5 10.5 L15 1" fill="none" stroke="#f0a43a" stroke-width="2"></path></svg>{{ c }}
            </li>
          </ul>
        </div>
        <div class="relative min-w-0 pt-32 lg:pt-44">
          <div ref="heroLight" class="pointer-events-none absolute inset-x-[-30%] top-[-250px] h-[800px] bg-spot" aria-hidden="true"></div>
          <StageLamp ref="heroLamp" :cord="110" flexible></StageLamp>
          <div class="relative rounded-md bg-surface p-5 sm:p-6" aria-label="Ejemplo de composición">
            <h2 class="text-[32px] leading-none">Noche de otoño</h2>
            <p class="mt-2.5 flex flex-wrap items-center gap-2 text-sm text-muted"><SongStatus status="in_progress" /><span>Do mayor · 92 bpm · 4/4 · Privada</span></p>
            <div class="-mx-1 mt-4 flex gap-1 overflow-x-auto border-b border-line pb-2" role="group" aria-label="Secciones de la composición de ejemplo">
              <button v-for="tab in heroTabs" :key="tab" type="button" class="tab" :class="heroTab === tab ? 'tab-on' : ''" :aria-pressed="heroTab === tab ? 'true' : 'false'" @click="heroTab = tab">{{ tab }}</button>
            </div>
            <div class="mt-4 h-[248px] overflow-y-auto [scrollbar-color:theme(colors.fret)_transparent] [scrollbar-width:thin]">
              <LyricSheet v-if="heroTab === 'Letra'" :lines="previewLines.slice(5, 9)" :chords="previewChords" text-class="text-base leading-snug" chord-class="text-sm" />
              <div v-else-if="heroTab === 'Acordes'" class="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <div v-for="item in previewChords.slice(0, 6)" :key="item.id" class="rounded bg-ground p-2.5">
                  <p class="text-sm font-semibold text-brass">{{ item.name }}</p>
                  <ChordDiagram :chord="item" class="mt-1" />
                </div>
              </div>
              <div v-else-if="heroTab === 'Tablatura'">
                <p class="text-sm text-muted">Riff del intro</p>
                <pre class="mt-3 overflow-x-auto font-mono text-[15px] leading-snug text-ink" aria-label="Tablatura del riff del intro">{{ introRiff }}</pre>
              </div>
              <ul v-else class="grid list-none gap-3 p-0">
                <li v-for="take in takes.slice(0, 3)" :key="take.title" class="rounded bg-ground px-3 py-2.5">
                  <p class="flex justify-between gap-3 text-[15px]"><span class="font-semibold">{{ take.title }}</span><span class="tabular-nums text-muted">{{ formatTime(take.length) }}</span></p>
                  <div inert class="mt-1"><Waveform :seed="take.seed" :length="take.length" :bars="48" height="h-6" /></div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Escribir -->
    <FeatureSection
      id="escribir"
      kicker="Escritura"
      title="Escribe la canción completa."
      :points="['Mantén tus letras organizadas por sección', 'Agrega acordes a la sílaba correspondiente', 'Edita los acordes y Erato identifica su nombre', 'Crea tablaturas de guitarra a mano']"
    >
      <div class="grid gap-3">
        <div class="card">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-sm text-muted">Toca las cuerdas y Erato nombra el acorde</p>
              <p class="mt-1 font-display text-[64px] leading-none text-brass sm:text-[80px]" aria-live="polite"><button v-if="detectedChord.notes && new Set(detectedChord.notes.map(note => note % 12)).size >= 2" type="button" class="border-0 bg-transparent p-0 text-left text-brass" @mouseenter="showHint($event, detectedChord)" @mouseleave="hint = null" @focus="showHint($event, detectedChord)" @blur="hint = null">{{ chord.name }}</button><span v-else>{{ chord.name }}</span></p>
              <p class="mt-1 text-base">{{ chord.notes }}</p>
            </div>
            <button type="button" class="btn-ghost btn-sm" @click="resetChord">Restablecer acorde</button>
          </div>
          <div class="mt-6"><Fretboard :frets="frets" @change="setFrets"></Fretboard></div>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="card">
            <p class="text-sm text-muted">Coro</p>
            <div class="mt-3"><LyricSheet :lines="previewLines.slice(5, 8)" :chords="previewChords" text-class="text-xl leading-snug"></LyricSheet></div>
          </div>
          <div class="card">
            <p class="text-sm text-muted">Riff del intro</p>
            <pre class="mt-3 overflow-x-auto font-mono text-[15px] leading-snug text-ink" aria-label="Tablatura del riff del intro">{{ introRiff }}</pre>
          </div>
        </div>
      </div>
    </FeatureSection>

    <!-- Leer -->
    <FeatureSection
      id="leer"
      kicker="Lectura"
      title="Toca con las dos manos."
      :points="['Lee tus letras sin tocar la pantalla, con desplazamiento continuo a la velocidad que elijas', 'Obtén una vista previa del próximo acorde', 'Revisa las tablaturas en una vista amigable', 'Maximiza la letra a pantalla completa para el ensayo o el escenario']"
    >
      <div class="overflow-hidden rounded-md bg-surface">
        <div class="flex flex-wrap items-center justify-between gap-3 bg-[#221a13] px-5 py-3">
          <span class="text-[15px] text-muted">Modo escenario · Noche de otoño</span>
          <div class="flex items-center gap-2">
            <button type="button" class="btn-ghost btn-icon" aria-label="Más lento" @click="slower">−</button>
            <span class="min-w-[56px] text-center text-lg font-semibold tabular-nums">{{ speed.toFixed(1) }}×</span>
            <button type="button" class="btn-ghost btn-icon" aria-label="Más rápido" @click="faster">+</button>
          </div>
        </div>
        <div class="relative h-[360px] min-w-0 overflow-hidden px-5 sm:h-[420px]">
          <div class="animate-roll" :style="rollStyle">
            <div v-for="n in 2" :key="n" class="pb-6 pt-4"><LyricSheet :lines="readingLines" :chords="previewChords"></LyricSheet></div>
          </div>
        </div>
      </div>
    </FeatureSection>

    <!-- Escuchar -->
    <FeatureSection
      id="escuchar"
      kicker="Audio"
      title="Cada toma, en su lugar."
      :points="['Agrega audios con las demos de tu composición', 'Escribe comentarios en segundos específicos', 'Guarda varias tomas por composición y elige cuál escuchar', 'Salta a cualquier comentario y escucha justo ese momento']"
    >
      <div class="overflow-hidden rounded-md bg-surface md:grid md:grid-cols-[230px_minmax(0,1fr)]">
        <div class="bg-[#221a13] p-3">
          <p class="px-2 pb-2 pt-1 text-sm text-muted">Demos</p>
          <button
            v-for="(t, i) in takes"
            :key="t.title"
            type="button"
            class="flex w-full cursor-pointer items-center justify-between gap-3 rounded border-0 px-3 py-3 text-left text-ink transition-colors hover:bg-raised"
            :class="i === selectedTake ? 'bg-raised' : 'bg-transparent'"
            :aria-pressed="i === selectedTake ? 'true' : 'false'"
            @click="selectedTake = i"
          >
            <span><span class="block text-base font-medium">{{ t.title }}</span><span class="mt-0.5 block text-sm text-muted">{{ t.comments.length }} coment.</span></span>
            <span class="text-sm tabular-nums">{{ formatTime(t.length) }}</span>
          </button>
        </div>
        <div class="min-w-0 p-5 sm:p-6">
          <DemoPlayer :key="selectedTake" :take="{ ...takes[selectedTake], comments: takes[selectedTake].comments.map(comment => ({ ...comment, text: comment.text.replace('Gmaj7 en vez de G', 'otra forma del acorde') })) }" :compact="true"></DemoPlayer>
          <p v-if="selectedTake === 0" class="mt-3 text-base"><span class="text-muted">Alternativas del ensayo: </span><template v-for="name in ['Gmaj7', 'G']" :key="name"><button type="button" class="btn-ghost btn-sm mr-2" @mouseenter="showHint($event, tokenChord(name)!)" @mouseleave="hint = null" @focus="showHint($event, tokenChord(name)!)" @blur="hint = null">{{ name }}</button></template></p>
        </div>
      </div>
    </FeatureSection>

    <!-- Colaborar -->
    <FeatureSection
      id="colaborar"
      kicker="Colaboración"
      title="La banda, en la misma página."
      :points="['Crea una banda y agrega a tus integrantes', 'Edita colaborativamente una composición', 'Revisa el historial de ediciones', 'Comparte tu composición con el público']"
    >
      <div class="grid gap-3">
        <BandCard :band="band"></BandCard>
        <div>
          <p class="mb-2 mt-3 text-sm text-muted">Historial · Noche de otoño</p>
          <HistoryList :items="history">
            <template #description="{ item }"><template v-for="(token, index) in chordTokens(item.what || '')" :key="index"><button v-if="tokenChord(token)" type="button" class="border-0 bg-transparent p-0 font-semibold text-brass" @mouseenter="showHint($event, tokenChord(token)!)" @mouseleave="hint = null" @focus="showHint($event, tokenChord(token)!)" @blur="hint = null">{{ token }}</button><template v-else>{{ token }}</template></template></template>
          </HistoryList>
        </div>
        <ShareLinkBar></ShareLinkBar>
      </div>
    </FeatureSection>

    <!-- Cómo funciona -->
    <section id="como-funciona" class="scroll-mt-6 py-20 sm:py-28 lg:py-32">
      <div class="page-x">
        <p class="text-[15px] font-medium text-brass">Cómo funciona</p>
        <h2 class="mt-4 max-w-[22ch] text-[44px] leading-[0.98] sm:text-[60px] lg:text-[72px]">De la idea al escenario, en cuatro pasos.</h2>
        <ol class="mt-14 grid list-none gap-3 p-0 sm:grid-cols-2 lg:grid-cols-4">
          <li v-for="(s, i) in steps" :key="s.title" class="card flex flex-col gap-3 sm:min-h-[220px]">
            <span class="font-display text-[44px] leading-none text-brass">{{ String(i + 1).padStart(2, '0') }}</span>
            <h3 class="mt-4 text-[30px] leading-tight">{{ s.title }}</h3>
            <p class="text-base leading-normal">{{ s.text }}</p>
          </li>
        </ol>
        <div class="mt-10 flex flex-wrap gap-3">
          <router-link to="/registro" class="btn-primary min-h-[52px] px-7 text-[17px]">Empieza gratis</router-link>
          <router-link to="/login" class="btn-ghost min-h-[52px] px-7 text-[17px]">Ya tengo cuenta</router-link>
        </div>
      </div>
    </section>

    <!-- Cierre -->
    <section class="relative overflow-hidden bg-surface pb-24 pt-52 text-center sm:pb-32">
      <div ref="closingLight" class="pointer-events-none absolute inset-x-[-30%] top-[-230px] h-[800px] bg-spot" aria-hidden="true"></div>
      <StageLamp ref="closingLamp" :cord="130" flexible></StageLamp>
      <div class="page-x relative">
        <h2 class="mx-auto max-w-[20ch] text-[48px] leading-[0.98] sm:text-[72px] lg:text-[88px]">Tu próxima canción empieza esta noche.</h2>
        <p class="mx-auto mt-6 max-w-[40ch] text-lg leading-normal">Erato es gratis y open source. Escribe solo o invita a tu banda cuando quieras.</p>
        <div class="mt-9 flex flex-wrap justify-center gap-3">
          <router-link to="/registro" class="btn-primary min-h-[52px] px-7 text-[17px]">Empieza gratis</router-link>
          <a href="https://github.com/bsttiv/erato" class="btn-ghost min-h-[52px] bg-ground px-7 text-[17px]">Ver en GitHub</a>
        </div>
      </div>
    </section>

    <Teleport to="body"><ChordHint v-if="hint" :chord="hint.chord" :anchor="hint.anchor" :chords="previewChords" /></Teleport>
    <SiteFooter></SiteFooter>
  </div>
</template>
