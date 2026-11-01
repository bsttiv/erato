<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import Wordmark from '../components/atoms/Wordmark.vue'
import { session, profileApi, profileApiKey, type SessionUser, type SessionDevice } from '../stores/session'
import { copy, errorMessage, validUsername, validPassword } from '../api/messages'
import type { ApiError } from '../api/client'

const api = inject(profileApiKey, profileApi)
const router = useRouter()
const user = ref<SessionUser | null>(null)
const username = ref('')
const displayName = ref('')
const sessions = ref<SessionDevice[]>([])
const loading = ref(true)
const loadError = ref(false)
const dataMessage = ref('')
const sessionMessage = ref('')
const passwordMessage = ref('')
const emailMessage = ref('')
const email = ref('')
const emailPassword = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const repeatPassword = ref('')
const saving = ref(false)
const changingPassword = ref(false)
const changingEmail = ref(false)
const closing = ref<string[]>([])
const blocked = ref(false)
let unblockTimer: ReturnType<typeof setTimeout> | undefined
let alive = true
onUnmounted(() => { alive = false; clearTimeout(unblockTimer) })
function clearPasswords() {
  currentPassword.value = ''
  newPassword.value = ''
  repeatPassword.value = ''
}
async function handleError(error: ApiError, target: Ref<string>, password = false) {
  if (error.status === 401 && error.code === 'not_authenticated') {
    session.clear()
    await router.replace('/login')
  } else target.value = errorMessage(error, password)
}
function setUser(value: SessionUser) {
  user.value = value
  username.value = value.username
  displayName.value = value.display_name
}
async function load() {
  loading.value = true
  loadError.value = false
  try {
    const [me, devices] = await Promise.all([api.getMe(), api.listSessions()])
    if (alive) { setUser(me); sessions.value = devices }
  } catch (error) {
    loadError.value = true
    await handleError(error, dataMessage)
  } finally { loading.value = false }
}
onMounted(load)
async function save() {
  if (saving.value) return
  dataMessage.value = ''
  if (!username.value || !displayName.value.trim()) { dataMessage.value = copy.required; return }
  if (!validUsername(username.value)) { dataMessage.value = copy.username; return }
  if ([...displayName.value.trim()].length > 60) { dataMessage.value = copy.displayName; return }
  saving.value = true
  try {
    setUser(await api.updateMe({ username: username.value, display_name: displayName.value.trim() }))
    dataMessage.value = 'Cambios guardados.'
  } catch (error) { await handleError(error, dataMessage) }
  finally { saving.value = false }
}
async function close(device: SessionDevice) {
  if (closing.value.includes(device.id)) return
  closing.value.push(device.id)
  sessionMessage.value = ''
  try {
    await api.closeSession(device.id)
    sessions.value = sessions.value.filter((item) => item.id !== device.id)
    if (device.current) { session.clear(); await router.replace('/login') }
  } catch (error) { await handleError(error, sessionMessage) }
  finally { closing.value = closing.value.filter((id) => id !== device.id) }
}
async function changePassword() {
  if (changingPassword.value || blocked.value) return
  passwordMessage.value = ''
  if (!currentPassword.value || !newPassword.value || !repeatPassword.value) { passwordMessage.value = copy.required; return }
  if (!validPassword(newPassword.value)) { passwordMessage.value = copy.password; return }
  if (newPassword.value !== repeatPassword.value) { passwordMessage.value = copy.mismatch; return }
  changingPassword.value = true
  try {
    await api.changePassword({ current_password: currentPassword.value, new_password: newPassword.value })
    clearPasswords()
    sessions.value = sessions.value.filter((device) => device.current)
    passwordMessage.value = 'Contraseña actualizada. Cerramos tus otras sesiones.'
  } catch (error) {
    if (error.code === 'invalid_credentials' || error.status === 429) clearPasswords()
    if (error.status === 429 && Number.isFinite(error.retryAfter) && error.retryAfter > 0) {
      blocked.value = true
      unblockTimer = setTimeout(() => { blocked.value = false }, error.retryAfter * 1000)
    }
    await handleError(error, passwordMessage, true)
  } finally { changingPassword.value = false }
}
async function changeEmail() {
  if (changingEmail.value) return
  emailMessage.value = ''
  changingEmail.value = true
  try {
    setUser(await api.changeEmail({ email: email.value, current_password: emailPassword.value }))
    email.value = ''
    emailMessage.value = 'Cambios guardados.'
  } catch (error) { await handleError(error, emailMessage, true) }
  finally { emailPassword.value = ''; changingEmail.value = false }
}
function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('es', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <header class="flex items-center justify-between bg-surface px-4 py-4 sm:px-8">
      <Wordmark to="/canciones" size="text-[30px]" />
      <router-link v-if="user" to="/perfil" class="avatar h-11 w-11" :aria-label="'Tu cuenta: ' + user.display_name" aria-current="page">{{ user.display_name.slice(0, 1).toUpperCase() }}</router-link>
    </header>
    <main class="mx-auto max-w-[760px] px-4 py-8">
      <h1 class="text-[44px] leading-none sm:text-[56px]">Tu perfil</h1>
      <p v-if="loading" role="status" class="mt-8">Cargando…</p>
      <div v-else-if="loadError" class="card mt-8">
        <p role="alert">No se pudo cargar tu perfil.</p>
        <button type="button" class="btn-primary mt-4" @click="load">Reintentar</button>
      </div>
      <template v-else>
        <section class="card mt-8" aria-labelledby="profile-data">
          <h2 id="profile-data" class="text-[28px]">Datos</h2>
          <form class="mt-5 grid gap-4" novalidate @submit.prevent="save">
            <div><label for="profile-username" class="field-label">Nombre de usuario</label><input id="profile-username" v-model="username" autocomplete="username" class="field-input-dark" /></div>
            <div><label for="profile-name" class="field-label">Nombre visible</label><input id="profile-name" v-model="displayName" autocomplete="name" class="field-input-dark" /></div>
            <p v-if="dataMessage" role="status">{{ dataMessage }}</p>
            <button type="submit" :disabled="saving" class="btn-primary">Guardar</button>
          </form>
          <form class="mt-6 grid gap-4" @submit.prevent="changeEmail">
            <div><label for="profile-email" class="field-label">Correo nuevo</label><input id="profile-email" v-model="email" required type="email" autocomplete="email" class="field-input-dark" /></div>
            <div><label for="email-password" class="field-label">Contraseña actual</label><input id="email-password" v-model="emailPassword" required type="password" autocomplete="current-password" class="field-input-dark" /></div>
            <p v-if="emailMessage" role="status">{{ emailMessage }}</p>
            <button type="submit" :disabled="changingEmail" class="btn-primary">Cambiar correo</button>
          </form>
        </section>
        <section class="card mt-3.5" aria-labelledby="profile-sessions">
          <h2 id="profile-sessions" class="text-[28px]">Sesiones</h2>
          <p v-if="!sessions.length" class="mt-4">No hay sesiones abiertas.</p>
          <ul class="mt-4 grid list-none gap-4 p-0">
            <li v-for="device in sessions" :key="device.id" class="flex flex-wrap items-center gap-3">
              <div class="flex-1"><span>{{ device.device }}</span><time class="block text-sm text-muted" :datetime="device.last_access_at">{{ formatDate(device.last_access_at) }}</time></div>
              <span v-if="device.current" class="chip chip-on">Este dispositivo</span>
              <button type="button" class="btn-ghost btn-sm" :disabled="closing.includes(device.id)" :aria-label="'Cerrar sesión de ' + device.device" @click="close(device)">×</button>
            </li>
          </ul>
          <p v-if="sessionMessage" role="alert" class="mt-4">{{ sessionMessage }}</p>
        </section>
        <section class="card mt-3.5" aria-labelledby="profile-password">
          <h2 id="profile-password" class="text-[28px]">Contraseña</h2>
          <form class="mt-5 grid gap-4" novalidate @submit.prevent="changePassword">
            <div><label for="current-password" class="field-label">Contraseña actual</label><input id="current-password" v-model="currentPassword" type="password" autocomplete="current-password" class="field-input-dark" /></div>
            <div><label for="new-password" class="field-label">Contraseña nueva</label><input id="new-password" v-model="newPassword" type="password" autocomplete="new-password" class="field-input-dark" /></div>
            <div><label for="repeat-password" class="field-label">Repetir contraseña nueva</label><input id="repeat-password" v-model="repeatPassword" type="password" autocomplete="new-password" class="field-input-dark" /></div>
            <p v-if="passwordMessage" role="status">{{ passwordMessage }}</p>
            <button type="submit" :disabled="changingPassword || blocked" class="btn-primary">Cambiar contraseña</button>
          </form>
        </section>
      </template>
    </main>
  </div>
</template>
