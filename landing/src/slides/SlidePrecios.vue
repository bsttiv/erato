<script setup lang="ts">
import { ErTag } from '@ds-vue'
import { getRegisterUrl } from '../config'

const registerUrl = getRegisterUrl()

const plans = [
  {
    name: 'Gratis',
    price: '$0',
    period: 'para siempre',
    featured: false,
    blurb: 'Para escribir tus canciones y mostrarlas con un enlace.',
    rows: [
      { ok: true, text: 'Composiciones con acordes, tablaturas, letras y tareas' },
      { ok: true, text: 'Enlace público de solo lectura' },
      { ok: true, text: '1 demo de audio' },
      { ok: false, text: 'Compartir con personas' },
      { ok: false, text: 'Historial de versiones' },
    ],
    cta: 'Empieza gratis',
    featuredClass: '',
    btnClass: 'er-btn--quiet',
  },
  {
    name: 'Pro Individual',
    price: '$5.000',
    period: 'CLP al mes',
    featured: false,
    blurb: 'Para quien compone solo y quiere más espacio y memoria.',
    rows: [
      { ok: true, text: 'Todo lo del plan Gratis' },
      { ok: true, text: 'Más espacio para demos' },
      { ok: true, text: 'Historial de versiones de letras y acordes' },
      { soon: true, text: 'Edición en tiempo real (próximamente)' },
      { ok: false, text: 'Compartir con personas' },
    ],
    cta: 'Elegir Pro Individual',
    featuredClass: '',
    btnClass: 'er-btn--quiet',
  },
  {
    name: 'Pro Banda',
    price: '$8.000',
    period: 'CLP al mes',
    featured: true,
    blurb: 'Para tocar juntos: una banda, sus integrantes y sus canciones.',
    rows: [
      { ok: true, text: 'Todo lo de Pro Individual' },
      { ok: true, text: 'Banda de hasta 8 integrantes' },
      { ok: true, text: 'Integrante extra por $1.000 CLP al mes' },
      { ok: true, text: 'Compartir composiciones con la banda' },
      { soon: true, text: 'Edición en tiempo real (próximamente)' },
    ],
    cta: 'Elegir Pro Banda',
    featuredClass: 'er-plan-card--featured',
    btnClass: 'er-btn--primary',
  },
]
</script>

<template>
  <section class="er-slide" aria-label="Precios">
    <div class="er-wrap-full er-plans-wrap">
      <div class="er-plans-header">
        <div class="er-slide-col">
          <div class="er-label">// precios</div>
          <h2 class="er-h2 er-plans-h2">
            Gratis para empezar. <em class="er-highlight">Pro</em> para la banda.
          </h2>
        </div>
        <p class="er-plans-subtitle">
          Precios mensuales en pesos chilenos. ¿Prefieres hospedarlo tú? Erato es open source (AGPL-3.0) y en tu propio servidor no tiene límites.
          <a
            href="https://github.com/bsttiv/erato"
            target="_blank"
            rel="noopener noreferrer"
            class="er-plans-gh-link"
          >
            Ver en GitHub
          </a>
        </p>
      </div>

      <div class="er-plans-grid">
        <article
          v-for="(p, idx) in plans"
          :key="idx"
          class="er-panel er-plan-card"
          :class="p.featuredClass"
        >
          <div class="er-plan-top">
            <span class="er-plan-name">{{ p.name }}</span>
            <ErTag
              v-if="p.featured"
              tone="amber"
              :dot="true"
            >
              para bandas
            </ErTag>
          </div>

          <div class="er-plan-price-row">
            <span class="er-plan-price">{{ p.price }}</span>
            <span class="er-plan-period">{{ p.period }}</span>
          </div>

          <div class="er-plan-blurb">{{ p.blurb }}</div>

          <div class="er-plan-rows">
            <div
              v-for="(r, rIdx) in p.rows"
              :key="rIdx"
              class="er-plan-row"
            >
              <span
                class="er-plan-mark"
                :class="{
                  'er-plan-mark--ok': r.ok,
                  'er-plan-mark--off': r.ok === false,
                  'er-plan-mark--soon': r.soon,
                }"
              >
                {{ r.ok ? '✓' : r.soon ? '…' : '×' }}
              </span>
              <span
                class="er-plan-row-text"
                :class="{
                  'er-plan-row-text--faint': r.ok === false,
                  'er-plan-row-text--muted': r.soon,
                }"
              >
                {{ r.text }}
              </span>
            </div>
          </div>

          <a
            :href="registerUrl"
            class="er-btn er-plan-btn"
            :class="p.btnClass"
          >
            {{ p.cta }}
          </a>
        </article>
      </div>
    </div>
  </section>
</template>
