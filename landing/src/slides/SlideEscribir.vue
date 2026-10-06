<script setup lang="ts">
import { ErChordEditor } from '@ds-vue'

const chordWrite = [-1, 3, 2, 0, 0, 0]
</script>

<template>
  <section class="er-slide" aria-label="Características: escritura">
    <div class="er-wrap">
      <div class="er-slide-col">
        <div class="er-label">
          // características · escritura
        </div>
        <h2 class="er-h2">
          Escribe la canción <em class="er-highlight">completa</em>.
        </h2>
        <ul class="er-feat">
          <li><b>01</b><span>Mantén tus letras organizadas por sección</span></li>
          <li><b>02</b><span>Agrega acordes a la sílaba correspondiente</span></li>
          <li><b>03</b><span>Edita los acordes utilizados e identifica sus nomenclaturas</span></li>
          <li><b>04</b><span>Crea tablaturas de guitarra</span></li>
        </ul>
      </div>
      <div
        class="er-visual er-visual--escribir"
        data-scroll-exclusion
      >
        <div class="er-panel er-panel-lyrics">
          <div class="er-lyrics-section er-lyrics-section-title">
            Coro
          </div>
          <p class="er-lyric er-lyric-line">
            <span class="er-seg-lyr er-lyric-seg">
              <span class="er-seg-chord er-lyric-chord">Dm7</span>
              Quédate un&nbsp;
            </span>
            <span class="er-seg-lyr er-lyric-seg">
              <span class="er-seg-chord er-lyric-chord">G7</span>
              rato más
            </span>
          </p>
          <p class="er-lyric er-lyric-line">
            <span class="er-seg-lyr er-lyric-seg">
              <span class="er-seg-chord er-lyric-chord">Cmaj7</span>
              que la banda no ha&nbsp;
            </span>
            <span class="er-seg-lyr er-lyric-seg">
              <span class="er-seg-chord er-lyric-chord">Am7</span>
              terminado
            </span>
          </p>
        </div>
        <div class="er-panel er-panel-tab">
          <div class="er-label">
            // riff del intro
          </div>
          <pre class="er-tab-code">e|-----------|-----5----|
B|-----------|---8------|
G|-------5b7-|----------|
D|---5-7-----|----------|
A|-7---------|----------|
E|5---7h8----|----------|</pre>
        </div>
        <ErChordEditor
          :default-frets="chordWrite"
          :hide-switch="true"
          class="er-block"
        />
      </div>
    </div>
  </section>
</template>
