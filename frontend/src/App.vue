<template>
  <div class="er-app" :data-theme="currentTheme">
    <header class="er-header er-row" style="justify-content: space-between; align-items: center; padding: var(--space-4); border-bottom: 1px solid var(--line)">
      <div class="er-row" style="gap: var(--space-4); align-items: center">
        <h1 style="font-family: var(--font-display); font-size: 1.5rem; margin: 0">
          Erato
        </h1>
        <ErSegmented
          v-model="currentView"
          label="Navegación principal"
          :options="[
            { value: 'compositions', label: 'Composiciones' },
            { value: 'auth', label: 'Cuenta' },
          ]"
        />
      </div>

      <div class="er-row" style="gap: var(--space-2); align-items: center">
        <ErButton size="sm" variant="ghost" @click="toggleTheme">
          {{ currentTheme === 'noche' ? '☀️ Matiné' : '🌙 Noche' }}
        </ErButton>
      </div>
    </header>

    <main class="er-app-main" style="padding: var(--space-4)">
      <CompositionsView v-if="currentView === 'compositions'" />
      <AuthView v-else @authenticated="currentView = 'compositions'" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErSegmented, ErButton } from '@/design-system'
import CompositionsView from '@/features/compositions/CompositionsView.vue'
import AuthView from '@/features/auth/AuthView.vue'

const currentView = ref<'compositions' | 'auth'>('compositions')
const currentTheme = ref<'noche' | 'matine'>('noche')

function toggleTheme() {
  currentTheme.value = currentTheme.value === 'noche' ? 'matine' : 'noche'
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', currentTheme.value)
  }
}
</script>
