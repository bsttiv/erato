<template>
  <div class="er-app-main">
    <header class="er-topbar">
      <RouterLink to="/" class="er-btn er-btn--ghost" aria-label="Ir a composiciones"><ErBrand /></RouterLink>
      <nav class="er-comp-header-nav-right" aria-label="Navegación">
        <RouterLink to="/bands" class="er-btn er-btn--ghost">Bandas</RouterLink>
        <AppNavExtras />
      </nav>
    </header>
    <main class="er-dash" :aria-busy="loading || busy">
      <h1 class="er-dash-headline">{{ band?.name || 'Tus bandas' }}</h1>
      <div v-if="error" role="alert" class="er-auth-error">{{ error }}</div>
      <ErButton v-if="error && !band && !bands.length" :disabled="loading" @click="load">Reintentar</ErButton>
      <p v-if="loading" role="status" class="er-loading">Cargando bandas…</p>
      <template v-else-if="!route.params.id">
        <div class="er-section">
          <ErButton v-if="!showCreate" variant="primary" :disabled="!creation.actionable.value"
            @click="creation.create">Crear banda</ErButton>
          <p v-if="creation.explanation.value" class="er-hint">{{ creation.explanation.value }}</p>
          <section v-if="showCreate" class="er-panel er-section" aria-label="Crear banda">
            <BandCreateForm @created="created" @cancel="showCreate = false" />
          </section>
        </div>
        <p v-if="!bands.length && !error" class="er-hint">Aún no formas parte de una banda.</p>
        <div class="er-comp-grid">
          <section v-for="item in bands" :key="item.id" class="er-card">
            <RouterLink :to="`/bands/${item.id}`" class="er-btn er-btn--ghost">{{ item.name }}</RouterLink>
            <p class="er-hint">{{ seats(item) }} · {{ item.user_role === 'owner' ? 'dueño' : 'integrante' }}</p>
            <ErTag :tone="item.active ? 'moss' : 'neutral'">{{ item.active ? 'activa' : 'inactiva' }}</ErTag>
          </section>
        </div>
      </template>
      <template v-else-if="band">
        <p class="er-hint">{{ seats(band) }}</p>
        <ErTag :tone="band.active ? 'moss' : 'neutral'">{{ band.active ? 'activa' : 'inactiva' }}</ErTag>
        <form v-if="owner" class="er-auth-form" @submit.prevent="rename">
          <label for="band-rename-name" class="er-label">Nombre de la banda</label>
          <input id="band-rename-name" v-model="name" class="er-input" maxlength="80" required :disabled="busy">
          <ErButton type="submit" :disabled="busy || !name.trim()">Guardar nombre</ErButton>
        </form>
        <section class="er-panel er-section" aria-labelledby="band-members">
          <h2 id="band-members" class="er-label">// integrantes</h2>
          <div v-for="member in band.members" :key="member.user_id" class="er-comp-header-nav">
            <div class="er-field">
              <span>{{ member.display_name || 'Integrante sin nombre' }}</span>
              <span class="er-hint">{{ member.role === 'owner' ? 'dueño' : 'integrante' }}</span>
            </div>
            <div v-if="owner && member.role !== 'owner'" class="er-comp-header-nav-right">
              <template v-if="confirmation?.userId === member.user_id">
                <span class="er-kbd">{{ confirmation.question }}</span>
                <ErButton variant="danger" :disabled="busy" @click="confirmAction">Sí</ErButton>
                <ErButton variant="ghost" :disabled="busy" @click="confirmation = null">Cancelar</ErButton>
              </template>
              <template v-else>
                <ErButton variant="danger" :disabled="busy" @click="ask('remove', member)">Quitar a {{ member.display_name || 'integrante' }}</ErButton>
                <ErButton v-if="!band.pending_transfer" :disabled="busy" @click="ask('transfer', member)">Transferir a {{ member.display_name || 'integrante' }}</ErButton>
              </template>
            </div>
          </div>
        </section>
        <section v-if="owner" class="er-panel er-section" aria-labelledby="band-invites">
          <h2 id="band-invites" class="er-label">// invitaciones</h2>
          <ErButton :disabled="busy" @click="invite">Crear enlace de invitación</ErButton>
          <p class="er-hint">Copia el enlace al crearlo. Por seguridad, no podrás recuperarlo después.</p>
          <div v-if="newInvite" class="er-field">
            <label for="band-invite-link" class="er-label">Enlace de invitación</label>
            <input id="band-invite-link" class="er-input" :value="newInvite.invite_url" readonly>
            <ErButton :disabled="busy" @click="copyInvite">Copiar enlace</ErButton>
            <p v-if="copied" role="status" class="er-hint">Enlace copiado</p>
          </div>
          <div v-for="item in invites" :key="item.id" class="er-comp-header-nav">
            <span class="er-hint">Invitación · vence el {{ date(item.expires_at) }}</span>
            <ErButton variant="danger" :disabled="busy" :aria-label="`Eliminar la invitación que vence el ${date(item.expires_at)}`" @click="deleteInvite(item.id)">Eliminar</ErButton>
          </div>
        </section>
        <section v-if="band.pending_transfer" class="er-panel er-section" aria-labelledby="band-transfer">
          <h2 id="band-transfer" class="er-label">// transferencia pendiente</h2>
          <p class="er-hint">Para {{ transferName }} · vence el {{ date(band.pending_transfer.expires_at) }}</p>
          <ErButton v-if="owner" :disabled="busy" @click="clearTransfer(false)">Cancelar transferencia</ErButton>
          <div v-else-if="band.pending_transfer.to_user_id === userId" class="er-comp-header-nav-left">
            <ErButton :disabled="busy" @click="accept">Aceptar transferencia</ErButton>
            <ErButton :disabled="busy" @click="clearTransfer(true)">Rechazar transferencia</ErButton>
          </div>
        </section>
        <div v-if="!owner" class="er-comp-header-nav-left">
          <template v-if="confirmation?.kind === 'leave'">
            <span class="er-kbd">{{ confirmation.question }}</span>
            <ErButton variant="danger" :disabled="busy" @click="confirmAction">Sí</ErButton>
            <ErButton variant="ghost" :disabled="busy" @click="confirmation = null">Cancelar</ErButton>
          </template>
          <ErButton v-else variant="danger" :disabled="busy" @click="ask('leave')">Salir de la banda</ErButton>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ErBrand, ErButton, ErTag } from '@/design-system'
import * as api from '@/api/bands'
import { getMe } from '@/api/auth'
import AppNavExtras from '@/shared/AppNavExtras.vue'
import { useEntitlements } from '@/features/plan/useEntitlements'
import { useBandCreation } from './useBandCreation'
import { bandErrorMessage } from './bandErrors'
import BandCreateForm from './BandCreateForm.vue'

const route = useRoute()
const router = useRouter()
const { refresh } = useEntitlements()
const bands = ref<api.BandSummary[]>([])
const band = ref<api.BandResponse | null>(null)
const invites = ref<api.BandInviteSummary[]>([])
const newInvite = ref<api.BandInviteResponse | null>(null)
const userId = ref('')
const name = ref('')
const error = ref('')
const loading = ref(false)
const busy = ref(false)
const copied = ref(false)
const showCreate = ref(false)
type ConfirmationKind = 'remove' | 'transfer' | 'leave'
const confirmation = ref<{ kind: ConfirmationKind; userId?: string; question: string } | null>(null)
function ask(kind: ConfirmationKind, member?: api.BandMember) {
  const memberName = member?.display_name || 'integrante'
  confirmation.value = {
    kind, userId: member?.user_id,
    question: kind === 'leave' ? '¿Salir de la banda?' :
      kind === 'remove' ? `¿Quitar a ${memberName}?` : `¿Transferir la banda a ${memberName}?`,
  }
}
function confirmAction() {
  if (busy.value || !confirmation.value) return
  const action = confirmation.value
  confirmation.value = null
  if (action.kind === 'leave') void leave()
  else if (action.userId) void (action.kind === 'remove' ? remove(action.userId) : transfer(action.userId))
}
const creation = useBandCreation(() => { showCreate.value = true })
const owner = computed(() => band.value?.user_role === 'owner')
const transferName = computed(() => band.value?.members.find(m => m.user_id === band.value?.pending_transfer?.to_user_id)?.display_name || 'Integrante sin nombre')
const seats = (item: api.BandSummary) => item.seat_limit === null ? `${item.seats_used} plazas · sin límite` : `${item.seats_used} de ${item.seat_limit} plazas`
const date = (value: string) => new Date(value).toLocaleDateString('es')
let generation = 0

async function load() {
  const current = ++generation
  const id = String(route.params.id || '')
  loading.value = true
  error.value = ''
  band.value = null
  bands.value = []
  invites.value = []
  newInvite.value = null
  copied.value = false
  showCreate.value = false
  confirmation.value = null
  try {
    if (!id) {
      const result = await api.listBands()
      if (current === generation) bands.value = result
    } else {
      const [result, user] = await Promise.all([api.getBand(id), getMe()])
      if (current !== generation) return
      band.value = result
      userId.value = user.id
      name.value = result.name
      if (result.user_role === 'owner') {
        const resultInvites = await api.listBandInvites(id)
        if (current === generation) invites.value = resultInvites
      }
    }
  } catch (reason) { if (current === generation) error.value = bandErrorMessage(reason) }
  finally { if (current === generation) loading.value = false }
}
async function run(action: (id: string) => Promise<() => unknown>) {
  if (busy.value || !band.value) return
  const current = generation
  busy.value = true
  error.value = ''
  try {
    const apply = await action(band.value.id)
    if (current === generation) await apply()
  } catch (reason) { if (current === generation) error.value = bandErrorMessage(reason) }
  finally { busy.value = false }
}
async function created(result: api.BandResponse) { await router.push(`/bands/${result.id}`) }
function rename() {
  if (name.value.trim()) void run(async id => {
    const result = await api.renameBand(id, name.value.trim())
    return () => { band.value = result }
  })
}
function remove(user: string) { return run(async id => { await api.removeBandMember(id, user); return load }) }
function transfer(user: string) {
  return run(async id => {
    const result = await api.requestBandTransfer(id, user)
    return () => { band.value = result }
  })
}
function clearTransfer(reject: boolean) {
  return run(async id => { await (reject ? api.rejectBandTransfer : api.cancelBandTransfer)(id); return load })
}
function accept() {
  return run(async id => {
    const result = await api.acceptBandTransfer(id)
    await refresh()
    const resultInvites = await api.listBandInvites(id)
    return () => { band.value = result; invites.value = resultInvites }
  })
}
function leave() {
  return run(async id => { await api.leaveBand(id); await refresh(); return () => router.push('/bands') })
}
function invite() {
  return run(async id => {
    const result = await api.createBandInvite(id)
    return () => { newInvite.value = result; copied.value = false; invites.value.push(result) }
  })
}
function deleteInvite(inviteId: string) {
  return run(async id => {
    await api.deleteBandInvite(id, inviteId)
    return () => {
      invites.value = invites.value.filter(item => item.id !== inviteId)
      if (newInvite.value?.id === inviteId) newInvite.value = null
    }
  })
}
function copyInvite() {
  return run(async () => {
    copied.value = false
    if (!navigator.clipboard || !newInvite.value) throw new Error('Clipboard unavailable')
    await navigator.clipboard.writeText(newInvite.value.invite_url)
    return () => { copied.value = true }
  })
}
watch(() => route.params.id, load, { immediate: true })
onUnmounted(() => { generation++ })
</script>
