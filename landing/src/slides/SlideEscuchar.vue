<script setup lang="ts">
import { ErDemoPlayer, type DemoTake } from '@ds-vue'

const takes: DemoTake[] = [
  {
    id: 't3',
    title: 'Toma 3 — ensayo',
    date: '28 sep',
    duration: 214,
    note: 'sala B, un mic',
    comments: [
      { t: 18, author: 'Ana', text: 'La entrada del bajo va medio tiempo antes.' },
      { t: 71, author: 'Tomás', text: 'Acá probar el Gmaj7 en vez de G.' },
      { t: 150, author: 'Ana', text: 'Este puente es el bueno.' },
    ],
  },
  {
    id: 't2',
    title: 'Toma 2',
    date: '21 sep',
    duration: 198,
    comments: [{ t: 40, author: 'Leo', text: 'Muy rápido.' }],
  },
  {
    id: 't1',
    title: 'Idea de voz',
    date: '14 sep',
    duration: 62,
    note: 'nota de voz',
    comments: [],
  },
]
</script>

<template>
  <section class="er-slide" aria-label="Características: audio">
    <div class="er-wrap">
      <div style="display: flex; flex-direction: column; gap: var(--space-6);">
        <div class="er-label">
          // características · audio
        </div>
        <h2 class="er-h2">
          Cada toma, en su <em style="color: var(--amber); font-weight: 500;">lugar</em>.
        </h2>
        <ul class="er-feat">
          <li><b>01</b><span>Agrega audios de demos de tu composición</span></li>
          <li><b>02</b><span>Escribe comentarios en timestamps específicos</span></li>
          <li><b>03</b><span>Guarda varias tomas por composición y elige cuál escuchar</span></li>
          <li><b>04</b><span>Salta a cualquier comentario y escucha justo ese momento</span></li>
        </ul>
      </div>
      <div class="er-visual" data-scroll-exclusion>
        <ErDemoPlayer
          :takes="takes"
          author="Tú"
          style="display: block;"
        />
      </div>
    </div>
  </section>
</template>
