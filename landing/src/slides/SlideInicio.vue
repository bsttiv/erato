<script setup lang="ts">
import { ErTag } from '@ds-vue'
import { getRegisterUrl } from '../config'

const registerUrl = getRegisterUrl()

defineEmits<{
  (e: 'go-features'): void
}>()
</script>

<template>
  <section class="er-slide" aria-label="Inicio">
    <div
      aria-hidden="true"
      class="er-hero-glow"
    />
    <div class="er-wrap er-wrap--hero">
      <div class="er-hero-content">
        <div class="er-hero-tags">
          <ErTag tone="amber" :dot="true">open source · AGPL-3.0</ErTag>
          <ErTag>para bandas y compositores</ErTag>
        </div>
        <h1 class="er-h1">
          El cancionero moderno <em class="er-highlight">Open-Source</em>
        </h1>
        <p class="er-hero-desc">
          Organiza, compone y comparte tus composiciones en un mismo lugar.
        </p>
        <div class="er-hero-ctas">
          <a
            :href="registerUrl"
            class="er-btn er-btn--primary er-btn-hero-primary"
          >
            Empieza gratis
          </a>
          <button
            type="button"
            class="er-btn er-btn--quiet er-btn-hero-quiet"
            @click="$emit('go-features')"
          >
            Revisa las características
          </button>
        </div>
        <ul class="er-hero-benefits">
          <li class="er-hero-benefit-item">
            <span class="er-hero-check">✓</span>No se requiere pago
          </li>
          <li class="er-hero-benefit-item">
            <span class="er-hero-check">✓</span>Herramientas curadas
          </li>
          <li class="er-hero-benefit-item">
            <span class="er-hero-check">✓</span>Interfaz amigable
          </li>
          <li class="er-hero-benefit-item">
            <span class="er-hero-check">✓</span>Edición colaborativa
          </li>
        </ul>
      </div>
      <div class="er-visual er-visual--hero" aria-hidden="true">
        <div class="er-hero-shape-1" />
        <div class="er-hero-shape-2" />
        <div class="er-hero-shape-3" />
        <div class="er-hero-shape-4" />
        <div class="er-hero-shape-5" />
        <div class="er-hero-line er-hero-line--46" />
        <div class="er-hero-line er-hero-line--50" />
        <div class="er-hero-line er-hero-line--54" />
        <div class="er-hero-line er-hero-line--58" />
        <div class="er-hero-line er-hero-line--62" />
        <div class="er-hero-line er-hero-line--66" />
      </div>
    </div>
  </section>
</template>
