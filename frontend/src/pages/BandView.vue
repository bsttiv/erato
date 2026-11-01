<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BackBar from '../components/molecules/BackBar.vue'
import InviteLinkBox from '../components/molecules/InviteLinkBox.vue'
import { bandsApi, invitationsApi, invitationLink, type Band, type Invitation, type Member } from '../api/bands'
import { accessMessage } from '../api/messages'
import { session, profileApi } from '../stores/session'

// Integrantes y enlaces de una banda. Los permisos los decide el servidor:
// quien no es dueño recibe 403 al quitar o transferir, y aquí se muestra ese aviso.
const route = useRoute()
const router = useRouter()
const bandId = computed(() => String(route.params.id))
const band = ref<Band | null>(null)
const members = ref<Member[]>([])
const links = ref<Invitation[]>([])
const link = ref('')
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const confirming = ref<{ action: 'remove' | 'transfer' | 'leave'; username: string } | null>(null)

const me = computed(() => session.user?.username || '')
const dateFormat = (value: string) => new Date(value).toLocaleDateString('es')

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (!session.user) await profileApi.getMe()
    band.value = await bandsApi.read(bandId.value)
    ;[members.value, links.value] = await Promise.all([
      bandsApi.members(bandId.value),
      // Listing links needs the editor right; a band member always has it.
      invitationsApi.list('band', bandId.value).catch(() => [] as Invitation[]),
    ])
  } catch (failure) { error.value = accessMessage(failure) }
  finally { loading.value = false }
}
onMounted(load)

async function run(task: () => Promise<unknown>) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try { await task() }
  catch (failure) { error.value = accessMessage(failure) }
  finally { busy.value = false; confirming.value = null }
}
const askConfirm = (action: 'remove' | 'transfer' | 'leave', username: string) => { confirming.value = { action, username } }
const isConfirming = (action: string, username: string) => confirming.value?.action === action && confirming.value.username === username

const removeMember = (username: string) => run(async () => {
  await bandsApi.removeMember(bandId.value, username)
  members.value = await bandsApi.members(bandId.value)
})
const transfer = (username: string) => run(async () => {
  band.value = await bandsApi.transfer(bandId.value, username)
  members.value = await bandsApi.members(bandId.value)
})
const leave = () => run(async () => {
  await bandsApi.removeMember(bandId.value, 'me')
  await router.replace('/canciones')
})
const createLink = () => run(async () => {
  const created = await invitationsApi.create('band', bandId.value, null)
  link.value = invitationLink(created.url)
  links.value = await invitationsApi.list('band', bandId.value)
})
const revoke = (id: string) => run(async () => {
  await invitationsApi.revoke(id)
  links.value = links.value.filter((row) => row.id !== id)
})
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <BackBar></BackBar>
    <main class="mx-auto max-w-[860px] px-4 pb-16 pt-10 sm:px-8">
      <p v-if="loading" role="status">Cargando banda…</p>
      <p v-if="error" role="alert" class="mb-4">{{ error }}</p>

      <template v-if="band">
        <h1 class="text-[44px] leading-none sm:text-[56px]">{{ band.name }}</h1>
        <p class="mt-3 text-[17px]">Espacio de banda · {{ members.length }} {{ members.length === 1 ? 'integrante' : 'integrantes' }}</p>
        <router-link :to="{ path: '/canciones', query: { band_id: band.id } }" class="btn-ghost btn-sm mt-5">Ver composiciones</router-link>

        <section class="mt-10" aria-labelledby="members-title">
          <h2 id="members-title" class="text-[32px]">Integrantes</h2>
          <ul class="mt-3 grid list-none gap-2 p-0">
            <li v-for="m in members" :key="m.username" class="flex flex-wrap items-center gap-3.5 rounded bg-surface px-4 py-3">
              <span class="avatar h-10 w-10 bg-brass text-[13px]">{{ m.display_name.slice(0, 2).toUpperCase() }}</span>
              <span class="min-w-0 flex-1"><span class="block truncate font-medium">{{ m.display_name }}<template v-if="m.username === me"> (tú)</template></span><span class="block truncate text-sm text-muted">@{{ m.username }}</span></span>
              <template v-if="m.username === me">
                <button v-if="!isConfirming('leave', m.username)" type="button" class="btn-ghost btn-sm" :disabled="busy" @click="askConfirm('leave', m.username)">Abandonar</button>
                <button v-else type="button" class="btn-primary btn-sm" :disabled="busy" @click="leave">Confirmar: abandonar</button>
              </template>
              <template v-else>
                <button v-if="!isConfirming('transfer', m.username)" type="button" class="btn-ghost btn-sm" :disabled="busy" @click="askConfirm('transfer', m.username)">Transferir banda</button>
                <button v-else type="button" class="btn-primary btn-sm" :disabled="busy" @click="transfer(m.username)">Confirmar: transferir a {{ m.display_name }}</button>
                <button v-if="!isConfirming('remove', m.username)" type="button" class="btn-ghost btn-sm" :disabled="busy" @click="askConfirm('remove', m.username)">Quitar</button>
                <button v-else type="button" class="btn-primary btn-sm" :disabled="busy" @click="removeMember(m.username)">Confirmar: quitar</button>
              </template>
            </li>
          </ul>
          <p class="mt-2 text-sm text-muted">Solo el dueño de la banda puede quitar integrantes o transferirla.</p>
        </section>

        <section class="mt-10" aria-labelledby="links-title">
          <h2 id="links-title" class="text-[32px]">Enlaces de invitación</h2>
          <p class="mt-2 text-base">Cualquiera que abra el enlace con su cuenta se une como integrante mientras esté vigente (7 días).</p>
          <div class="mt-4">
            <InviteLinkBox v-if="link" id="band-link" :link="link"></InviteLinkBox>
            <button type="button" class="btn-ghost mt-3" :disabled="busy" @click="createLink">Crear enlace nuevo</button>
          </div>
          <ul class="mt-4 grid list-none gap-2 p-0">
            <li v-for="l in links" :key="l.id" class="flex flex-wrap items-center gap-3.5 rounded bg-surface px-4 py-3">
              <span class="min-w-0 flex-1"><span class="block font-medium">Creado el {{ dateFormat(l.created_at) }}</span><span class="block text-sm text-muted">Vence el {{ dateFormat(l.expires_at) }}</span></span>
              <button type="button" class="btn-ghost btn-sm" :disabled="busy" @click="revoke(l.id)">Revocar</button>
            </li>
            <li v-if="!links.length" class="text-muted">No hay enlaces vigentes.</li>
          </ul>
        </section>
      </template>
    </main>
  </div>
</template>
