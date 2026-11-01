<script setup lang="ts">
import { useCompositionPath } from '../api/compositionPath'
const compositionPath = useCompositionPath()
import { ref, computed, watch } from 'vue'
import { client, session, profileApi } from '../stores/session'
import InviteLinkBox from '../components/molecules/InviteLinkBox.vue'
import { invitationsApi, invitationLink, songMembersApi, type Invitation, type Member } from '../api/bands'
import { useSong } from '../stores/song'
import { errorMessage, accessMessage } from '../api/messages'
const { song, loading, error, canManage, canEdit, isPublic } = useSong()
const busy = ref(false)
const link = computed(() => song.value?.share_slug ? `${window.location.origin}/c/${encodeURIComponent(song.value.share_slug)}` : '')
const songLines = computed(() => song.value?.lyrics?.lines || [])
const band = { name: 'Banda', initials: 'B', members: [] }
import LyricSheet from '../components/molecules/LyricSheet.vue'


const mode = computed(() => song.value?.visibility === 'public' ? 0 : 1)
const copied = ref(false)
const modes = [
  { name: 'Pública', desc: 'Cualquiera con el enlace puede verla. Solo los invitados pueden editarla.' },
  { name: 'Privada', desc: 'Solo la banda y las personas invitadas pueden verla y editarla.' },
]
const linkLine = computed(() =>
  mode.value === 0 ? 'Quien abra el enlace verá la letra, los acordes y las demos, sin poder cambiar nada.' : 'Quien abra el enlace sin invitación verá un aviso de que la canción es privada.',
)

async function choose(i: number) {
  if (!canManage.value || busy.value) return
  const target = song.value
  busy.value = true
  error.value = ''
  copied.value = false
  try {
    const updated = await client.request(`/songs/${encodeURIComponent(String(target!.id))}/visibility`, { method: 'PATCH', body: { visibility: i === 0 ? 'public' : 'private' } })
    if (song.value === target) song.value = updated
  }
  catch (failure) { if (song.value === target) error.value = errorMessage(failure) }
  finally { busy.value = false }
}
async function copy() {
  copied.value = false
  try {
    if (!link.value || !navigator.clipboard) throw new Error('clipboardUnavailable')
    await navigator.clipboard.writeText(link.value)
    copied.value = true
  } catch { error.value = 'No se pudo copiar el enlace. Puedes seleccionarlo y copiarlo manualmente.' }
}

// Invitaciones: enlaces de uso múltiple y lista de integrantes (el servidor decide cada permiso).
const songId = computed(() => (isPublic.value ? '' : String(song.value?.id || '')))
const role = ref<'editor' | 'viewer'>('viewer')
const inviteLink = ref('')
const links = ref<Invitation[]>([])
const members = ref<Member[]>([])
const inviteBusy = ref(false)
const inviteError = ref('')
const me = computed(() => session.user?.username || '')
const roleLabel = (value: string | null) => (value === 'editor' ? 'Puede editar' : 'Solo lectura')

async function loadSharing() {
  inviteError.value = ''
  inviteLink.value = ''
  links.value = []
  members.value = []
  if (!songId.value) return
  try {
    if (!session.user) await profileApi.getMe()
    members.value = await songMembersApi.list(songId.value)
    if (canEdit.value) links.value = await invitationsApi.list('song', songId.value)
  } catch (failure) { inviteError.value = accessMessage(failure) }
}
watch(songId, loadSharing, { immediate: true })

async function sharing(task: () => Promise<unknown>) {
  if (inviteBusy.value) return
  inviteBusy.value = true
  inviteError.value = ''
  try { await task() }
  catch (failure) { inviteError.value = accessMessage(failure) }
  finally { inviteBusy.value = false }
}
const createLink = () => sharing(async () => {
  inviteLink.value = invitationLink((await invitationsApi.create('song', songId.value, role.value)).url)
  links.value = await invitationsApi.list('song', songId.value)
})
const revoke = (id: string) => sharing(async () => {
  await invitationsApi.revoke(id)
  links.value = links.value.filter((row) => row.id !== id)
})
const changeRole = (m: Member) => sharing(async () => {
  const next = m.role === 'editor' ? 'viewer' : 'editor'
  Object.assign(m, await songMembersApi.setRole(songId.value, m.username, next))
})
const removeMember = (m: Member) => sharing(async () => {
  await songMembersApi.remove(songId.value, m.username)
  members.value = members.value.filter((row) => row.username !== m.username)
})
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-ground text-ink">
    <div class="px-4 py-8 opacity-30 sm:px-10" aria-hidden="true">
      <p class="font-display text-[56px] leading-none">{{ song?.title || 'Composición' }}</p>
      <div class="mt-10 max-w-[720px]"><LyricSheet :lines="songLines.slice(0, 5)" :chords="song?.chords || []"></LyricSheet></div>
    </div>
    <div class="absolute inset-0 bg-[#080503]/75" aria-hidden="true"></div>

    <div class="absolute inset-0 flex items-start justify-center overflow-y-auto px-4 py-6 sm:items-center sm:py-10">
      <section role="dialog" aria-modal="true" aria-labelledby="share-title" class="w-full max-w-[600px] rounded-lg bg-surface p-5 shadow-[0_30px_80px_rgba(0,0,0,.55)] sm:p-8">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h1 id="share-title" class="text-[34px] leading-none sm:text-[40px]">Compartir canción</h1>
            <p class="mt-2 text-base text-muted">{{ song?.title || 'Composición' }}</p>
          </div>
          <router-link :to="compositionPath" aria-label="Cerrar" class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded bg-raised text-2xl text-ink no-underline hover:text-ink">×</router-link>
        </div>

        <p v-if="loading" role="status">Cargando composición…</p>
        <p v-if="error" role="alert">{{ error }}</p>
        <div v-if="canManage" class="mt-7 grid gap-2.5" role="radiogroup" aria-label="Quién puede verla">
          <button v-for="(m, i) in modes" :key="m.name" type="button" :disabled="busy" role="radio" class="option-card flex items-start gap-3.5 bg-ground" :class="mode === i ? 'option-card-on' : ''" :aria-checked="mode === i ? 'true' : 'false'" @click="choose(i)">
            <span class="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-solid" :class="mode === i ? 'border-brass' : 'border-fret'" aria-hidden="true">
              <span v-if="mode === i" class="h-2.5 w-2.5 rounded-full bg-brass"></span>
            </span>
            <span><b class="block font-semibold">{{ m.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ m.desc }}</span></span>
          </button>
        </div>

        <p class="field-label mt-6">Enlace</p>
        <div class="flex flex-wrap gap-2">
          <label for="share-link" class="sr-only">Enlace de la canción</label>
          <input id="share-link" type="text" readonly :value="link" class="field-input-dark min-w-0 flex-[1_1_240px]" />
          <button type="button" class="btn-primary min-w-[136px]" :disabled="!link" @click="copy">{{ copied ? 'Copiado' : 'Copiar enlace' }}</button>
        </div>
        <p class="mt-2.5 text-[15px] leading-normal" aria-live="polite">{{ linkLine }}</p>

        <template v-if="songId">
        <h2 class="mt-7 text-[26px]">Invitar a la composición</h2>
        <p v-if="inviteError" role="alert" class="mt-2">{{ inviteError }}</p>
        <template v-if="canEdit">
          <p class="mt-1 text-[15px] text-muted">Quien abra el enlace con su cuenta entra con el rol elegido. Vale 7 días.</p>
          <div class="mt-3 flex flex-wrap items-center gap-2">
            <div class="segmented" role="group" aria-label="Rol del enlace">
              <button type="button" class="segmented-item" :class="role === 'viewer' ? 'segmented-item-on' : ''" :aria-pressed="role === 'viewer' ? 'true' : 'false'" @click="role = 'viewer'">Lector</button>
              <button type="button" class="segmented-item" :class="role === 'editor' ? 'segmented-item-on' : ''" :aria-pressed="role === 'editor' ? 'true' : 'false'" @click="role = 'editor'">Editor</button>
            </div>
            <button type="button" class="btn-ghost" :disabled="inviteBusy" @click="createLink">Crear enlace</button>
          </div>
          <div v-if="inviteLink" class="mt-3"><InviteLinkBox id="song-invite-link" :link="inviteLink"></InviteLinkBox></div>
          <ul v-if="links.length" class="mt-3 grid list-none gap-1 p-0" aria-label="Enlaces vigentes">
            <li v-for="l in links" :key="l.id" class="flex items-center gap-3.5 py-2">
              <span class="min-w-0 flex-1"><span class="block font-medium">{{ roleLabel(l.role) }}</span><span class="block text-sm text-muted">Vence el {{ new Date(l.expires_at).toLocaleDateString('es') }}</span></span>
              <button type="button" class="btn-ghost btn-sm" :disabled="inviteBusy" @click="revoke(l.id)">Revocar</button>
            </li>
          </ul>
        </template>
        <ul class="mt-4 grid list-none gap-1 p-0" aria-label="Personas con acceso">
          <li v-for="m in members" :key="m.username" class="flex flex-wrap items-center gap-3.5 py-2">
            <span class="avatar h-10 w-10 bg-brass text-[13px]">{{ m.display_name.slice(0, 2).toUpperCase() }}</span>
            <span class="min-w-0 flex-1"><span class="block truncate font-medium">{{ m.display_name }}<template v-if="m.username === me"> (tú)</template></span><span class="block text-sm text-muted">@{{ m.username }} · {{ roleLabel(m.role) }}</span></span>
            <template v-if="canManage && m.username !== me">
              <button type="button" class="btn-ghost btn-sm" :disabled="inviteBusy" @click="changeRole(m)">{{ m.role === 'editor' ? 'Pasar a lector' : 'Pasar a editor' }}</button>
              <button type="button" class="btn-ghost btn-sm" :disabled="inviteBusy" @click="removeMember(m)">Quitar</button>
            </template>
          </li>
        </ul>
        </template>
        <div class="mt-6 flex justify-end">
          <router-link :to="compositionPath" class="btn-primary">Listo</router-link>
        </div>
      </section>
    </div>
  </div>
</template>
