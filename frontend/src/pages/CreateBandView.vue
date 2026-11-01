<script setup lang="ts">
import { ref, computed } from 'vue'
import BackBar from '../components/molecules/BackBar.vue'
import InviteLinkBox from '../components/molecules/InviteLinkBox.vue'
import { bandsApi, invitationsApi, invitationLink, type Band } from '../api/bands'
import { accessMessage } from '../api/messages'
import { session } from '../stores/session'

// Paso 1: nombre de la banda. Paso 2: enlace de invitación (las invitaciones son enlaces, no correos).
const name = ref('')
const band = ref<Band | null>(null)
const link = ref('')
const busy = ref(false)
const error = ref('')

const initials = computed(() => (session.user?.display_name || '?').slice(0, 2).toUpperCase())
const bandPath = computed(() => (band.value ? { path: '/canciones', query: { band_id: band.value.id } } : '/canciones'))

async function create() {
  if (busy.value) return
  const value = name.value.trim()
  if (!value) { error.value = 'Escribe el nombre de la banda.'; return }
  busy.value = true
  error.value = ''
  try { band.value = await bandsApi.create(value) }
  catch (failure) { error.value = accessMessage(failure) }
  finally { busy.value = false }
}
async function createLink() {
  if (busy.value || !band.value) return
  busy.value = true
  error.value = ''
  try { link.value = invitationLink((await invitationsApi.create('band', band.value.id, null)).url) }
  catch (failure) { error.value = accessMessage(failure) }
  finally { busy.value = false }
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <BackBar></BackBar>
    <div class="mx-auto grid max-w-[1240px] gap-12 px-4 pb-16 pt-10 sm:px-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] lg:gap-14">
      <div>
        <h1 class="text-[44px] leading-none sm:text-[56px]">Crea tu banda</h1>
        <p class="mt-3 text-[17px] leading-normal">Un espacio compartido: todos los integrantes ven y editan las composiciones de la banda.</p>

        <form v-if="!band" class="mt-9" @submit.prevent="create">
          <label for="band-name" class="field-label">Nombre de la banda</label>
          <input id="band-name" v-model="name" type="text" class="field-input" autocomplete="off" />
          <p v-if="error" role="alert" class="mt-2 text-sm text-brass">{{ error }}</p>
          <div class="mt-10 flex flex-wrap gap-3">
            <button type="submit" class="btn-primary" :disabled="busy">Crear banda</button>
            <router-link to="/canciones" class="btn-ghost">Cancelar</router-link>
          </div>
        </form>

        <section v-else class="mt-9" aria-labelledby="band-invite-title">
          <p role="status" class="rounded bg-surface px-4 py-3">La banda «{{ band.name }}» está creada.</p>
          <h2 id="band-invite-title" class="mt-10 text-[32px]">Invita a los integrantes</h2>
          <p class="mt-2 text-base">Comparte un enlace: cualquiera que lo abra con su cuenta se une como integrante. Vale 7 días.</p>
          <div class="mt-4">
            <button v-if="!link" type="button" class="btn-ghost" :disabled="busy" @click="createLink">Crear enlace de invitación</button>
            <InviteLinkBox v-else id="band-invite-link" :link="link"></InviteLinkBox>
          </div>
          <p v-if="error" role="alert" class="mt-2 text-sm text-brass">{{ error }}</p>
          <div class="mt-10 flex flex-wrap gap-3">
            <router-link :to="bandPath" class="btn-primary">Ir a la banda</router-link>
            <router-link :to="'/bandas/' + encodeURIComponent(band.id)" class="btn-ghost">Ver integrantes</router-link>
          </div>
        </section>
      </div>

      <aside class="self-start rounded-md bg-surface bg-lamp px-6 pb-7 pt-20 sm:px-7" aria-label="Vista previa">
        <p class="text-sm text-muted">Tu banda en la barra lateral</p>
        <p class="mt-4 font-display text-[44px] leading-none sm:text-[56px]">{{ (band?.name || name).trim() || 'Tu banda' }}</p>
        <p class="mt-3 text-base">Solo tú, por ahora</p>
        <div class="mt-5 flex flex-wrap">
          <span class="avatar h-12 w-12 bg-brass text-sm ring-2 ring-surface">{{ initials }}</span>
        </div>
      </aside>
    </div>
  </div>
</template>
