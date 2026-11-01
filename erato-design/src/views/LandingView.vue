<script setup>
import { ref, computed } from 'vue'
import LandingNav from '../components/landing/LandingNav.vue'
import FeatureSection from '../components/landing/FeatureSection.vue'
import SiteFooter from '../components/landing/SiteFooter.vue'
import CompositionPreview from '../components/landing/CompositionPreview.vue'
import StageLamp from '../components/ui/StageLamp.vue'
import Fretboard from '../components/music/Fretboard.vue'
import LyricSheet from '../components/music/LyricSheet.vue'
import DemoPlayer from '../components/music/DemoPlayer.vue'
import BandCard from '../components/app/BandCard.vue'
import HistoryList from '../components/app/HistoryList.vue'
import ShareLinkBar from '../components/app/ShareLinkBar.vue'
import { chordFromFrets, keyFromShapes } from '../lib/chords.js'
import { songChords, songLines, takes, band, history, formatTime } from '../data/sample.js'

const heroChecks = ['No se requiere pago', 'Herramientas curadas', 'Interfaz amigable', 'Edición colaborativa']

// Escribir: el acorde se nombra solo
const CMAJ7 = [0, 0, 0, 2, 3, -1]
const frets = ref(CMAJ7.slice())
const songKey = keyFromShapes(songChords.map((c) => c.frets))
const chord = computed(() => chordFromFrets(frets.value, songKey))
const setFrets = (next) => (frets.value = next)
const resetChord = () => (frets.value = CMAJ7.slice())

// Leer: desplazamiento automático
const speed = ref(1)
const rollStyle = computed(() => ({ animationDuration: (36 / speed.value).toFixed(1) + 's' }))
const slower = () => (speed.value = Math.max(0.5, Math.round((speed.value - 0.1) * 10) / 10))
const faster = () => (speed.value = Math.min(2.5, Math.round((speed.value + 0.1) * 10) / 10))
const readingLines = songLines.slice(0, 8)

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
          <div class="pointer-events-none absolute inset-x-[-10%] top-24 bottom-[-20%] bg-lamp" aria-hidden="true"></div>
          <StageLamp :cord="110"></StageLamp>
          <div class="relative"><CompositionPreview></CompositionPreview></div>
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
              <p class="mt-1 font-display text-[64px] leading-none text-brass sm:text-[80px]" aria-live="polite">{{ chord.name }}</p>
              <p class="mt-1 text-base">{{ chord.notes }}</p>
            </div>
            <button type="button" class="btn-ghost btn-sm" @click="resetChord">Volver a Cmaj7</button>
          </div>
          <div class="mt-6"><Fretboard :frets="frets" @change="setFrets"></Fretboard></div>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="card">
            <p class="text-sm text-muted">Coro</p>
            <div class="mt-3"><LyricSheet :lines="songLines.slice(6, 8)" text-class="text-xl leading-snug"></LyricSheet></div>
          </div>
          <div class="card">
            <p class="text-sm text-muted">Riff del intro</p>
            <pre class="mt-3 overflow-x-auto font-mono text-[15px] leading-snug text-ink" aria-label="Tablatura del riff del intro">e|-----------|-----5----|
B|-----------|---8------|
G|-------5b7-|----------|
D|---5-7-----|----------|
A|-7---------|----------|
E|5---7h8----|----------|</pre>
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
        <div class="grid sm:grid-cols-[minmax(0,1fr)_200px]">
          <div class="relative h-[360px] min-w-0 overflow-hidden px-5 sm:h-[420px]">
            <div class="animate-roll" :style="rollStyle">
              <div v-for="n in 2" :key="n" class="pb-6 pt-4"><LyricSheet :lines="readingLines"></LyricSheet></div>
            </div>
          </div>
          <div class="flex items-center gap-5 bg-[#241b14] px-5 py-5 sm:block">
            <div>
              <p class="text-sm text-muted">Siguiente acorde</p>
              <p class="mt-1 font-display text-[56px] leading-none text-brass">D9</p>
              <p class="mt-1 text-[15px]">D · F# · C · E · A</p>
            </div>
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
          <DemoPlayer :key="selectedTake" :take="takes[selectedTake]" :compact="true"></DemoPlayer>
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
          <HistoryList :items="history"></HistoryList>
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
    <section class="relative overflow-hidden bg-surface bg-lamp pb-24 pt-52 text-center sm:pb-32">
      <StageLamp :cord="130"></StageLamp>
      <div class="page-x relative">
        <h2 class="mx-auto max-w-[20ch] text-[48px] leading-[0.98] sm:text-[72px] lg:text-[88px]">Tu próxima canción empieza esta noche.</h2>
        <p class="mx-auto mt-6 max-w-[40ch] text-lg leading-normal">Erato es gratis y open source. Escribe solo o invita a tu banda cuando quieras.</p>
        <div class="mt-9 flex flex-wrap justify-center gap-3">
          <router-link to="/registro" class="btn-primary min-h-[52px] px-7 text-[17px]">Empieza gratis</router-link>
          <a href="https://github.com" class="btn-ghost min-h-[52px] bg-ground px-7 text-[17px]">Ver en GitHub</a>
        </div>
      </div>
    </section>

    <SiteFooter></SiteFooter>
  </div>
</template>
