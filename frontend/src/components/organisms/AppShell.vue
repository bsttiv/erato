<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { session, profileApi } from '../../stores/session'
import { errorMessage } from '../../api/messages'
import Wordmark from '../atoms/Wordmark.vue'
import UserInitial from '../atoms/UserInitial.vue'
import { bandsApi, type Band } from '../../api/bands'

// Barra lateral de la aplicación. En el teléfono se pliega bajo un botón de menú.
const props = withDefaults(defineProps<{ space?: string; active?: string }>(), { space: 'band', active: 'compositions' }) // 'personal' | 'band' | ''
const emit = defineEmits<{ 'select-space': [space: string] }>()
const open = ref(false)
const router = useRouter()
const route = useRoute()
const bands = ref<Band[]>([])
const activeBand = computed(() => String(route.query.band_id || ''))
const logoutError = ref('')
const loggingOut = ref(false)
const accountName = computed(() => session.user?.display_name.trim() || session.user?.username || 'Tu cuenta')
onMounted(async () => {
  // A failed band list only hides the band entries; the rest of the shell works.
  if (session.accessToken) bandsApi.list().then((rows) => { bands.value = rows }).catch(() => { bands.value = [] })
  if (!session.accessToken || session.user) return
  try { await profileApi.getMe() }
  catch (error) {
    if (error.status === 401 && error.code === 'not_authenticated') await router.replace('/login')
    else logoutError.value = errorMessage(error)
  }
})
async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  logoutError.value = ''
  try { await session.logout(); await router.replace('/login') }
  catch (error) {
    if (error.status === 401 && error.code === 'not_authenticated') await router.replace('/login')
    else logoutError.value = errorMessage(error)
  } finally { loggingOut.value = false }
}

function choose(s: string) {
  emit('select-space', s)
  open.value = false
}
function chooseBand(id: string) {
  router.push({ path: '/canciones', query: { band_id: id } })
  choose('band')
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink lg:flex">
    <div class="flex items-center justify-between bg-[#17110d] px-4 py-3 lg:hidden">
      <Wordmark to="/canciones" size="text-[28px]"></Wordmark>
      <button type="button" class="btn-ghost btn-sm" :aria-expanded="open ? 'true' : 'false'" aria-controls="app-side" @click="open = !open">{{ open ? 'Cerrar' : 'Menú' }}</button>
    </div>

    <aside id="app-side" class="flex-col gap-7 bg-[#17110d] px-3.5 py-6 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-[260px] lg:shrink-0" :class="open ? 'flex' : 'hidden'" aria-label="Navegación de la aplicación">
      <div class="hidden px-3 lg:block"><Wordmark to="/canciones" size="text-[30px]"></Wordmark></div>
      <nav aria-label="Espacios de trabajo">
        <p class="mb-1.5 px-3 text-[13px] text-muted">Espacios de trabajo</p>
        <button type="button" class="flex min-h-[44px] w-full cursor-pointer items-center gap-3 rounded border-0 px-3 text-left text-base text-ink transition-colors hover:bg-raised" :class="space === 'personal' ? 'bg-raised font-medium' : 'bg-transparent'" @click="choose('personal')">
          <UserInitial :display-name="session.user?.display_name" :username="session.user?.username" />Personal
        </button>
        <button v-for="b in bands" :key="b.id" type="button" class="flex min-h-[44px] w-full cursor-pointer items-center gap-3 rounded border-0 px-3 text-left text-base text-ink transition-colors hover:bg-raised" :class="space === 'band' && activeBand === b.id ? 'bg-raised font-medium' : 'bg-transparent'" @click="chooseBand(b.id)">
          <span class="avatar h-[30px] w-[30px] bg-raised text-xs text-brass">{{ b.name.slice(0, 2).toUpperCase() }}</span>{{ b.name }}
        </button>
        <router-link to="/bandas/nueva" class="flex min-h-[44px] items-center gap-3 rounded px-3 text-base text-ink no-underline transition-colors hover:bg-raised hover:text-ink">
          <span class="avatar h-[30px] w-[30px] bg-raised text-lg text-brass" aria-hidden="true">+</span>Crear banda
        </router-link>
      </nav>
      <nav aria-label="Cuenta" class="lg:mt-auto">
        <p class="mb-1.5 px-3 text-[13px] text-muted">Cuenta</p>
        <router-link to="/perfil" class="flex min-h-[44px] items-center gap-3 rounded px-3 text-base text-ink no-underline transition-colors hover:bg-raised hover:text-ink" :class="active === 'profile' ? 'bg-raised font-medium' : ''">
          <UserInitial :display-name="session.user?.display_name" :username="session.user?.username" />{{ accountName }}
        </router-link>
        <button type="button" :disabled="loggingOut" class="btn-ghost w-full" @click="logout">Cerrar sesión</button>
        <p v-if="logoutError" role="alert" class="px-3 text-sm">{{ logoutError }}</p>
      </nav>
    </aside>

    <main class="min-w-0 flex-1 px-4 pb-16 pt-7 sm:px-8 lg:px-11 lg:pt-9">
      <slot></slot>
    </main>
  </div>
</template>
