<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Wordmark from '../atoms/Wordmark.vue'
import UserInitial from '../atoms/UserInitial.vue'
import { profileApi, session } from '../../stores/session'

const open = ref(false)
// Hidden until known, so a signed-in visitor never sees the sign-in links flash.
const checking = ref(!session.user)
const accountName = computed(() => session.user?.display_name.trim() || session.user?.username || 'Tu cuenta')

onMounted(async () => {
  try {
    if (!session.user && (await session.restore())) await profileApi.getMe()
  } catch {
    // An unreachable API leaves the visitor signed out on this public page.
  } finally {
    checking.value = false
  }
})
const links = [
  { href: '#escribir', label: 'Escribir' },
  { href: '#leer', label: 'Leer' },
  { href: '#escuchar', label: 'Escuchar' },
  { href: '#colaborar', label: 'Colaborar' },
  { href: '#como-funciona', label: 'Cómo funciona' },
]
</script>

<template>
  <header class="relative z-30">
    <div class="page-x flex min-h-[76px] items-center justify-between gap-4">
      <Wordmark></Wordmark>
      <nav class="hidden items-center gap-7 lg:flex" aria-label="Secciones">
        <a v-for="l in links" :key="l.href" :href="l.href" class="py-2.5 text-base text-ink no-underline transition-colors hover:text-brass">{{ l.label }}</a>
      </nav>
      <div class="flex items-center gap-2 sm:gap-4">
        <router-link v-if="session.user" to="/canciones" class="flex min-h-[44px] items-center gap-3 text-base text-ink no-underline hover:text-brass">
          <UserInitial :display-name="session.user.display_name" :username="session.user.username" />
          <span class="max-w-[16ch] truncate">{{ accountName }}</span>
        </router-link>
        <template v-else>
          <router-link to="/login" class="hidden py-2.5 text-base text-ink no-underline hover:text-brass sm:inline" :class="{ invisible: checking }">Iniciar sesión</router-link>
          <router-link to="/registro" class="btn-primary btn-sm" :class="{ invisible: checking }">Empieza gratis</router-link>
        </template>
        <button type="button" class="btn-ghost btn-sm lg:hidden" :aria-expanded="open ? 'true' : 'false'" aria-controls="menu-movil" @click="open = !open">{{ open ? 'Cerrar' : 'Menú' }}</button>
      </div>
    </div>
    <nav v-if="open" id="menu-movil" class="page-x pb-4 lg:hidden" aria-label="Secciones">
      <div class="grid gap-1 rounded-md bg-surface p-2">
        <a v-for="l in links" :key="l.href" :href="l.href" class="flex min-h-[48px] items-center rounded px-3 text-lg text-ink no-underline hover:bg-raised hover:text-ink" @click="open = false">{{ l.label }}</a>
        <router-link v-if="!session.user" to="/login" class="flex min-h-[48px] items-center rounded px-3 text-lg text-ink no-underline hover:bg-raised hover:text-ink">Iniciar sesión</router-link>
      </div>
    </nav>
  </header>
</template>
