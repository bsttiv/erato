<script setup lang="ts">
import { ErTag, ErButton } from '@ds-vue'

const historyItems = [
  { who: 'Ana', what: 'cambió el acorde del coro a Gmaj7', when: 'hace 2 h', tone: 'amber' },
  { who: 'Tomás', what: 'editó la letra del verso 2', when: 'ayer', tone: 'ember' },
  { who: 'Tú', what: 'subiste la Toma 3', when: '28 sep', tone: 'wine' },
  { who: 'Leo', what: 'agregó la tablatura del intro', when: '21 sep', tone: 'moss' },
]
</script>

<template>
  <section class="er-slide" aria-label="Características: colaboración">
    <div class="er-wrap">
      <div class="er-slide-col">
        <div class="er-label">// características · colaboración</div>
        <h2 class="er-h2">
          La banda, en la misma <em class="er-highlight">página</em>.
        </h2>
        <ul class="er-feat">
          <li><b>01</b><span>Crea una banda y agrega a tus miembros</span></li>
          <li><b>02</b><span>Edita colaborativamente una composición</span></li>
          <li><b>03</b><span>Revisa el historial de ediciones</span></li>
          <li><b>04</b><span>Comparte tu composición con el público</span></li>
        </ul>
      </div>
      <div class="er-visual er-collab-visual">
        <div class="er-panel er-collab-band-panel">
          <div class="er-collab-band-info">
            <div class="er-label">// banda</div>
            <div class="er-collab-band-name">Los Faroles</div>
            <div class="er-collab-band-count">4 de 8 integrantes</div>
          </div>
          <div class="er-collab-avatars">
            <span class="er-collab-avatar er-collab-avatar--wine">BV</span>
            <span class="er-collab-avatar er-collab-avatar--amber">AN</span>
            <span class="er-collab-avatar er-collab-avatar--ember">TO</span>
            <span class="er-collab-avatar er-collab-avatar--moss">LE</span>
          </div>
          <ErButton size="sm" icon="plus">Invitar</ErButton>
        </div>

        <div class="er-panel er-collab-history-panel">
          <div class="er-label er-collab-history-label">// historial · noche de otoño</div>
          <div
            v-for="(item, idx) in historyItems"
            :key="idx"
            class="er-collab-history-row"
          >
            <span
              class="er-collab-dot"
              :class="`er-collab-dot--${item.tone}`"
            />
            <span class="er-collab-history-text">
              <strong class="er-collab-history-author">{{ item.who }}</strong>
              <span class="er-collab-history-action">{{ item.what }}</span>
            </span>
            <span class="er-collab-history-when">{{ item.when }}</span>
          </div>
        </div>

        <div class="er-panel er-collab-share-panel">
          <ErTag tone="moss" :dot="true">pública</ErTag>
          <span class="er-collab-share-url">erato.app/c/noche-de-otono</span>
          <span class="er-collab-share-note">cualquiera con el enlace puede verla</span>
        </div>
      </div>
    </div>
  </section>
</template>
