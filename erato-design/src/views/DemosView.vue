<script setup>
import { ref } from 'vue'
import CompositionHeader from '../components/app/CompositionHeader.vue'
import DemoPlayer from '../components/music/DemoPlayer.vue'
import { takes, formatTime } from '../data/sample.js'

const selected = ref(0)
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <CompositionHeader active="demos" crumb="Demos">
      <a href="#subir" class="btn-primary btn-sm">Subir demo</a>
    </CompositionHeader>

    <div class="grid gap-8 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[320px_minmax(0,1fr)]">
      <aside aria-label="Tomas">
        <h1 class="text-[40px] leading-none sm:text-[44px]">Demos</h1>
        <p class="mt-2 text-[15px] text-muted">{{ takes.length }} tomas de Noche de otoño</p>
        <div class="mt-4 grid gap-1">
          <button
            v-for="(t, i) in takes"
            :key="t.title"
            type="button"
            class="flex w-full cursor-pointer items-center justify-between gap-3 rounded border-0 p-4 text-left text-ink transition-colors hover:bg-surface"
            :class="i === selected ? 'bg-raised' : 'bg-transparent'"
            :aria-pressed="i === selected ? 'true' : 'false'"
            @click="selected = i"
          >
            <span><span class="block text-[17px] font-medium">{{ t.title }}</span><span class="mt-1 block text-sm text-muted">{{ t.meta }} · {{ t.comments.length }} coment.</span></span>
            <span class="text-[15px] tabular-nums">{{ formatTime(t.length) }}</span>
          </button>
        </div>
        <div id="subir" class="mt-4 rounded-md bg-surface p-6 text-center">
          <p class="text-base">Arrastra un audio aquí</p>
          <p id="subir-ayuda" class="mt-1.5 text-sm text-muted">MP3, WAV o M4A, hasta 50 MB</p>
          <label class="btn-ghost relative mt-3.5 bg-ground">Elegir archivo<input type="file" accept="audio/*" class="absolute inset-0 cursor-pointer opacity-0" aria-describedby="subir-ayuda" /></label>
        </div>
      </aside>

      <main class="min-w-0">
        <section class="rounded-md bg-surface bg-lamp p-5 sm:p-8" aria-label="Reproductor">
          <DemoPlayer :key="selected" :take="takes[selected]"></DemoPlayer>
        </section>
      </main>
    </div>
  </div>
</template>
