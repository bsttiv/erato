<script setup lang="ts">
import { ErChordEditor } from '@ds-vue'

const chordWrite = [-1, 3, 2, 0, 0, 0]
</script>

<template>
  <section class="er-slide" aria-label="Características: escritura">
    <div class="er-wrap">
      <div style="display: flex; flex-direction: column; gap: var(--space-6);">
        <div class="er-label">
          // características · escritura
        </div>
        <h2 class="er-h2">
          Escribe la canción <em style="color: var(--amber); font-weight: 500;">completa</em>.
        </h2>
        <ul class="er-feat">
          <li><b>01</b><span>Mantén tus letras organizadas por sección</span></li>
          <li><b>02</b><span>Agrega acordes a la sílaba correspondiente</span></li>
          <li><b>03</b><span>Edita los acordes utilizados e identifica sus nomenclaturas</span></li>
          <li><b>04</b><span>Crea tablaturas de guitarra</span></li>
        </ul>
      </div>
      <div
        class="er-visual"
        data-scroll-exclusion
        style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-4); align-items: start;"
      >
        <div class="er-panel" style="grid-column: 1 / 3; display: flex; flex-direction: column; gap: var(--space-1); background: var(--bg-200); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 1.25rem;">
          <div class="er-lyrics-section" style="margin-top: 0; font-family: var(--font-mono); font-size: 0.75rem; color: var(--amber); text-transform: uppercase; letter-spacing: 0.05em;">
            Coro
          </div>
          <p class="er-lyric" style="margin: 0; font-family: var(--font-sans); font-size: 1.0625rem; line-height: 1.75rem;">
            <span class="er-seg-lyr" style="display: inline-flex; flex-direction: column;">
              <span class="er-seg-chord" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--amber); line-height: 1;">Dm7</span>
              Quédate un&nbsp;
            </span>
            <span class="er-seg-lyr" style="display: inline-flex; flex-direction: column;">
              <span class="er-seg-chord" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--amber); line-height: 1;">G7</span>
              rato más
            </span>
          </p>
          <p class="er-lyric" style="margin: 0; font-family: var(--font-sans); font-size: 1.0625rem; line-height: 1.75rem;">
            <span class="er-seg-lyr" style="display: inline-flex; flex-direction: column;">
              <span class="er-seg-chord" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--amber); line-height: 1;">Cmaj7</span>
              que la banda no ha&nbsp;
            </span>
            <span class="er-seg-lyr" style="display: inline-flex; flex-direction: column;">
              <span class="er-seg-chord" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--amber); line-height: 1;">Am7</span>
              terminado
            </span>
          </p>
        </div>
        <div class="er-panel" style="display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; background: var(--bg-200); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 1.25rem;">
          <div class="er-label">
            // riff del intro
          </div>
          <pre style="margin: 0; font-family: var(--font-mono); font-size: 0.875rem; line-height: 1.375rem; color: var(--ink-muted); overflow-x: auto;">e|-----------|-----5----|
B|-----------|---8------|
G|-------5b7-|----------|
D|---5-7-----|----------|
A|-7---------|----------|
E|5---7h8----|----------|</pre>
        </div>
        <ErChordEditor
          :default-frets="chordWrite"
          :hide-switch="true"
          style="display: block;"
        />
      </div>
    </div>
  </section>
</template>
