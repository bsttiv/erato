<script setup lang="ts">
import { ErTag } from '@ds-vue'

defineEmits<{
  (e: 'go-features'): void
}>()
</script>

<template>
  <section class="er-slide" aria-label="Inicio">
    <div
      aria-hidden="true"
      style="position: absolute; left: -10%; top: -30%; width: 70%; height: 120%; background: radial-gradient(closest-side, var(--lamp), transparent); pointer-events: none;"
    />
    <div class="er-wrap er-wrap--hero">
      <div style="display: flex; flex-direction: column; gap: var(--space-6); position: relative;">
        <div style="display: flex; gap: var(--space-2); flex-wrap: wrap;">
          <ErTag tone="amber" :dot="true">open source · AGPL-3.0</ErTag>
          <ErTag>para bandas y compositores</ErTag>
        </div>
        <h1 class="er-h1">
          El cancionero moderno <em style="color: var(--amber); font-weight: 500;">Open-Source</em>
        </h1>
        <p style="margin: 0; max-width: 35rem; font-size: 1.3125rem; line-height: 2rem; font-weight: 300; color: var(--ink-muted);">
          Organiza, compone y comparte tus composiciones en un mismo lugar.
        </p>
        <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
          <a
            href="#"
            class="er-btn er-btn--primary"
            style="text-decoration: none; height: 3.25rem; padding: 0 2rem; font-size: 0.9375rem;"
          >
            Empieza gratis
          </a>
          <button
            type="button"
            class="er-btn er-btn--quiet"
            style="height: 3.25rem; padding: 0 1.75rem; font-size: 0.9375rem;"
            @click="$emit('go-features')"
          >
            Revisa las características
          </button>
        </div>
        <ul style="list-style: none; margin: 0; padding: 0; display: flex; gap: 0.5rem 1.5rem; flex-wrap: wrap; font-family: var(--font-mono); font-size: 0.75rem; color: var(--ink-muted);">
          <li style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="color: var(--moss);">✓</span>No se requiere pago
          </li>
          <li style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="color: var(--moss);">✓</span>Herramientas curadas
          </li>
          <li style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="color: var(--moss);">✓</span>Interfaz amigable
          </li>
          <li style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="color: var(--moss);">✓</span>Edición colaborativa
          </li>
        </ul>
      </div>
      <div class="er-visual" aria-hidden="true" style="position: relative; height: 32.5rem;">
        <div style="position: absolute; left: 0; top: 0; width: 34%; height: 78%; border-radius: var(--radius-lg); background: var(--amber); box-shadow: 0 0 8.75rem var(--amber-soft);" />
        <div style="position: absolute; left: 38%; top: 8%; width: 28%; height: 12%; border-radius: var(--radius-md); background: var(--ink);" />
        <div style="position: absolute; left: 38%; top: 24%; width: 28%; height: 54%; border-radius: var(--radius-lg); background: var(--wine);" />
        <div style="position: absolute; left: 70%; top: 14%; width: 30%; height: 64%; border-radius: var(--radius-lg); background: var(--ember);" />
        <div style="position: absolute; left: 0; top: 84%; width: 3.5rem; height: 1.75rem; border-radius: 0.875rem; background: var(--moss);" />
        <div style="position: absolute; left: 0; right: 0; top: 46%; height: 1.5px; background: var(--bg-100);" />
        <div style="position: absolute; left: 0; right: 0; top: 50%; height: 1.5px; background: var(--bg-100);" />
        <div style="position: absolute; left: 0; right: 0; top: 54%; height: 1.5px; background: var(--bg-100);" />
        <div style="position: absolute; left: 0; right: 0; top: 58%; height: 1.5px; background: var(--bg-100);" />
        <div style="position: absolute; left: 0; right: 0; top: 62%; height: 1.5px; background: var(--bg-100);" />
        <div style="position: absolute; left: 0; right: 0; top: 66%; height: 1.5px; background: var(--bg-100);" />
      </div>
    </div>
  </section>
</template>
