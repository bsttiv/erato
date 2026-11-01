<script setup>
import CompositionHeader from '../components/app/CompositionHeader.vue'
import LyricSheet from '../components/music/LyricSheet.vue'
import TodoList from '../components/music/TodoList.vue'
import HistoryList from '../components/app/HistoryList.vue'
import { songLines, songChords, band, history } from '../data/sample.js'

const todos = [
  { text: 'Cerrar la letra del puente', done: true },
  { text: 'Grabar toma con batería', done: false },
  { text: 'Probar Gmaj7 en el coro', done: false },
  { text: 'Definir final para el show', done: false },
]
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="letra">
      <div class="hidden sm:flex" :aria-label="band.members.length + ' integrantes con acceso'">
        <span v-for="(m, i) in band.members" :key="m.initials" class="avatar h-[34px] w-[34px] text-xs ring-2 ring-[#17110d]" :class="i ? '-ml-2' : ''" :style="{ background: m.color }">{{ m.initials }}</span>
      </div>
      <router-link to="/c/noche-de-otono/escenario" class="btn-ghost btn-sm">Modo escenario</router-link>
      <router-link to="/c/noche-de-otono/compartir" class="btn-primary btn-sm">Compartir</router-link>
    </CompositionHeader>

    <div class="grid gap-10 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_360px]">
      <article class="min-w-0 max-w-[820px]" aria-labelledby="song-title">
        <h1 id="song-title" class="text-[44px] leading-none sm:text-[56px]">Noche de otoño</h1>
        <p class="mt-2.5 text-base text-muted">Re menor · 92 bpm · 4/4 · Pública · editada por Ana hace 2 h</p>
        <div class="mt-8"><LyricSheet :lines="songLines"></LyricSheet></div>
        <div class="mt-6 flex flex-wrap gap-2.5">
          <button type="button" class="btn-ghost">Agregar sección</button>
          <button type="button" class="btn-ghost">Editar letra</button>
        </div>
      </article>

      <aside class="grid content-start gap-3.5" aria-label="Detalles de la composición">
        <section class="card">
          <div class="flex items-baseline justify-between"><h2 class="text-[26px]">Acordes</h2><router-link to="/c/noche-de-otono/acordes" class="text-[15px]">Editar</router-link></div>
          <div class="mt-3.5 grid grid-cols-3 gap-2">
            <router-link v-for="c in songChords" :key="c.name" to="/c/noche-de-otono/acordes" class="flex min-h-[52px] items-center justify-center rounded bg-ground text-lg font-semibold text-ink no-underline transition-colors hover:bg-[#2e2219] hover:text-ink">{{ c.name }}</router-link>
          </div>
        </section>
        <section class="card">
          <h2 class="text-[26px]">Tareas</h2>
          <div class="mt-2"><TodoList :initial="todos"></TodoList></div>
        </section>
        <section class="card">
          <div class="flex items-baseline justify-between"><h2 class="text-[26px]">Última demo</h2><router-link to="/c/noche-de-otono/demos" class="text-[15px]">Ver las 3</router-link></div>
          <router-link to="/c/noche-de-otono/demos" class="mt-3.5 flex items-center gap-3.5 text-ink no-underline hover:text-ink">
            <span class="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brass"><svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true"><path d="M2 1 L15 9 L2 17 Z" fill="#1a1108"></path></svg></span>
            <span><span class="block font-medium">Toma 3, ensayo</span><span class="block text-sm text-muted">03:34 · 3 comentarios</span></span>
          </router-link>
        </section>
        <section>
          <h2 class="mb-3 mt-2 text-[26px]">Historial</h2>
          <HistoryList :items="history.slice(0, 3)"></HistoryList>
        </section>
      </aside>
    </div>
  </div>
</template>
