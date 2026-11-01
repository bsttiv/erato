<script setup>
import LyricSheet from '../music/LyricSheet.vue'
import { songLines } from '../../data/sample.js'

const lines = songLines.slice(5, 8)
const chords = ['Dm7', 'G7', 'Cmaj7', 'Am7']
</script>

<template>
  <div class="overflow-hidden rounded-md bg-surface">
    <div class="flex flex-wrap items-center justify-between gap-3 bg-[#221a13] px-5 py-4">
      <div class="flex flex-wrap items-baseline gap-x-3">
        <span class="font-display text-[26px]">Noche de otoño</span>
        <span class="text-sm text-muted">Los Faroles · Re menor · 92 bpm</span>
      </div>
      <div class="flex flex-wrap gap-1.5">
        <span class="chip chip-on">Letra</span><span class="chip">Acordes</span><span class="chip">Demos</span>
      </div>
    </div>
    <div class="grid sm:grid-cols-[minmax(0,1fr)_200px]">
      <div class="min-w-0 px-5 py-5">
        <LyricSheet :lines="lines" text-class="text-xl leading-snug"></LyricSheet>
      </div>
      <div class="bg-[#241b14] px-5 py-5">
        <p class="text-sm text-muted">Acordes</p>
        <div class="mt-3 grid grid-cols-4 gap-2 sm:grid-cols-2">
          <span v-for="c in chords" :key="c" class="rounded px-2 py-3 text-center text-lg font-semibold" :class="c === 'Cmaj7' ? 'bg-brass text-brass-ink' : 'bg-ground'">{{ c }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
