<script setup>
import { ref } from 'vue'
import Wordmark from '../ui/Wordmark.vue'
import { currentUser, band } from '../../data/sample.js'

// Barra lateral de la aplicación. En el teléfono se pliega bajo un botón de menú.
const props = defineProps({
  space: { type: String, default: 'band' }, // 'personal' | 'band' | ''
  active: { type: String, default: 'compositions' },
})
const emit = defineEmits(['select-space'])
const open = ref(false)

function choose(s) {
  emit('select-space', s)
  open.value = false
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink lg:flex">
    <div class="flex items-center justify-between bg-[#17110d] px-4 py-3 lg:hidden">
      <Wordmark to="/composiciones" size="text-[28px]"></Wordmark>
      <button type="button" class="btn-ghost btn-sm" :aria-expanded="open ? 'true' : 'false'" aria-controls="app-side" @click="open = !open">{{ open ? 'Cerrar' : 'Menú' }}</button>
    </div>

    <aside id="app-side" class="flex-col gap-7 bg-[#17110d] px-3.5 py-6 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-[260px] lg:shrink-0" :class="open ? 'flex' : 'hidden'" aria-label="Navegación de la aplicación">
      <div class="hidden px-3 lg:block"><Wordmark to="/composiciones" size="text-[30px]"></Wordmark></div>
      <nav aria-label="Espacios de trabajo">
        <p class="mb-1.5 px-3 text-[13px] text-muted">Espacios de trabajo</p>
        <button type="button" class="flex min-h-[44px] w-full cursor-pointer items-center gap-3 rounded border-0 px-3 text-left text-base text-ink transition-colors hover:bg-raised" :class="space === 'personal' ? 'bg-raised font-medium' : 'bg-transparent'" @click="choose('personal')">
          <span class="avatar h-[30px] w-[30px] text-xs" :style="{ background: currentUser.color }">{{ currentUser.initials }}</span>Personal
        </button>
        <button type="button" class="flex min-h-[44px] w-full cursor-pointer items-center gap-3 rounded border-0 px-3 text-left text-base text-ink transition-colors hover:bg-raised" :class="space === 'band' ? 'bg-raised font-medium' : 'bg-transparent'" @click="choose('band')">
          <span class="avatar h-[30px] w-[30px] bg-raised text-xs text-brass">{{ band.initials }}</span>{{ band.name }}
        </button>
        <router-link to="/bandas/nueva" class="flex min-h-[44px] items-center gap-3 rounded px-3 text-base text-ink no-underline transition-colors hover:bg-raised hover:text-ink">
          <span class="avatar h-[30px] w-[30px] bg-raised text-lg text-brass" aria-hidden="true">+</span>Crear banda
        </router-link>
      </nav>
      <nav aria-label="Cuenta" class="lg:mt-auto">
        <p class="mb-1.5 px-3 text-[13px] text-muted">Cuenta</p>
        <router-link to="/perfil" class="flex min-h-[44px] items-center gap-3 rounded px-3 text-base text-ink no-underline transition-colors hover:bg-raised hover:text-ink" :class="active === 'profile' ? 'bg-raised font-medium' : ''">
          <span class="avatar h-[30px] w-[30px] text-xs" :style="{ background: currentUser.color }">{{ currentUser.initials }}</span>{{ currentUser.name }}
        </router-link>
        <router-link to="/login" class="flex min-h-[44px] items-center rounded px-3 text-base text-muted no-underline hover:bg-raised hover:text-ink">Cerrar sesión</router-link>
      </nav>
    </aside>

    <main class="min-w-0 flex-1 px-4 pb-16 pt-7 sm:px-8 lg:px-11 lg:pt-9">
      <slot></slot>
    </main>
  </div>
</template>
