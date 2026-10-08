<template>
  <AppModal
    :open="true"
    :title="`// COMPARTIR — ${title}`"
    @close="emit('close')"
  >
    <!-- Section: Quién puede abrirla (D7) -->
    <div class="er-field">
      <div class="er-label">
        // QUIÉN PUEDE ABRIRLA
      </div>
      <div class="er-share-cards">
        <button
          type="button"
          :class="['er-share-card er-focus', { 'is-active': currentVisibility === 'public' }]"
          :aria-pressed="currentVisibility === 'public'"
          :disabled="busy"
          @click="selectVisibility('public')"
        >
          <span class="er-label">Con enlace</span>
          <span class="er-hint">
            Cualquiera con el enlace puede ver la letra, acordes y escuchar los demos.
          </span>
        </button>

        <button
          type="button"
          :class="['er-share-card er-focus', { 'is-active': currentVisibility === 'private' }]"
          :aria-pressed="currentVisibility === 'private'"
          :disabled="busy"
          @click="selectVisibility('private')"
        >
          <span class="er-label">Privada</span>
          <span class="er-hint">
            Solo tú y los miembros de la banda vinculada pueden acceder a esta composición.
          </span>
        </button>
      </div>
    </div>

    <!-- Read-only link when public -->
    <div v-if="currentVisibility === 'public'" class="er-field">
      <div class="er-label">
        // ENLACE DE LECTURA
      </div>
      <div class="er-share-link">
        <input
          type="text"
          readonly
          aria-label="Enlace de lectura"
          :value="shareUrl"
          class="er-input"
        >
        <ErButton
          variant="quiet"
          @click="copyShareLink"
        >
          {{ copied ? 'Copiado' : 'Copiar enlace' }}
        </ErButton>
      </div>

      <!-- Permission checklist -->
      <div class="er-perm-list">
        <div>✓ ver letra y acordes</div>
        <div>✓ escuchar demos</div>
        <div>✕ editar sin cuenta</div>
        <div>✕ comentar sin cuenta</div>
      </div>
    </div>

    <p v-if="error" class="er-auth-error" role="alert">{{ error }}</p>
    <div v-if="canManage" class="er-invites-block">
      <div class="er-label">// COMPARTIR CON UNA BANDA</div>
      <p v-if="!canShare" class="er-hint" role="status">
        Compartir con personas no está disponible. Puedes cambiar la visibilidad y copiar el enlace público.
      </p>
      <template v-else>
        <p v-if="loading" class="er-hint" role="status">Cargando bandas…</p>
        <div class="er-field">
          <label for="sharing-band" class="er-label">Banda</label>
          <select id="sharing-band" v-model="selectedBand" aria-label="Banda"
            class="er-input er-select" :disabled="loading || busy" @change="confirmation = null">
            <option value="">Elige una banda</option>
            <option v-for="band in bands" :key="band.id" :value="band.id" :disabled="!band.active">
              {{ band.name }}{{ band.active ? '' : ' (inactiva)' }}
            </option>
          </select>
          <label class="er-checkbox-label">
            <input v-model="bandEditable" type="checkbox" class="er-focus" :disabled="loading || busy || !selectedBand">
            Los miembros de la banda pueden editar
          </label>
          <ErButton :disabled="loading || busy || !selectedBand || !selectedActive" @click="saveBand">
            Guardar banda
          </ErButton>
          <p v-if="!bands.length && !loading" class="er-hint">Aún no perteneces a ninguna banda.</p>
          <p v-if="attachedBand && !attachedBand.active" class="er-hint">
            Esta banda está inactiva. Puedes desvincularla; los roles guardados se conservan mientras siga vinculada.
          </p>
        </div>
        <div v-if="attachedBand" class="er-field">
          <p class="er-hint">Banda vinculada: {{ attachedBand.name }}</p>
          <div class="er-field-row">
            <ErButton v-if="confirmation !== 'band'" variant="ghost" :disabled="busy || loading"
              @click="confirmation = 'band'">Desvincular banda</ErButton>
            <template v-else>
              <span class="er-kbd">¿Desvincular la banda y quitar los roles?</span>
              <ErButton size="sm" variant="danger" :disabled="busy" @click="detachBand">Sí</ErButton>
              <ErButton size="sm" variant="ghost" :disabled="busy" @click="confirmation = null">No</ErButton>
            </template>
          </div>
          <div class="er-label">// ROLES EN ESTA COMPOSICIÓN</div>
          <p class="er-hint">Al quitar un rol, la persona conserva el acceso de la banda.</p>
          <ul class="er-invites-list">
            <li v-for="member in bandMembers" :key="member.user_id" class="er-member">
              <span>{{ member.display_name || 'Integrante de la banda' }}</span>
              <div class="er-field">
                <select :value="roles[member.user_id] || ''" class="er-input er-select"
                  data-test="member-role" :aria-label="`Rol de ${member.display_name || 'integrante'}`"
                  :disabled="busy || loading || !attachedBand.active" @change="changeRole(member.user_id, $event)">
                  <option value="" disabled>Acceso de la banda</option>
                  <option value="editor">Editor</option>
                  <option value="viewer">Solo ver</option>
                </select>
                <ErButton v-if="roles[member.user_id] && confirmation !== member.user_id" size="sm"
                  variant="ghost" :disabled="busy || loading || !attachedBand.active"
                  @click="confirmation = member.user_id">Quitar rol</ErButton>
                <div v-if="confirmation === member.user_id" class="er-field-row">
                  <span class="er-kbd">¿Quitar el rol?</span>
                  <ErButton size="sm" variant="danger" :disabled="busy" @click="deleteRole(member.user_id)">Sí</ErButton>
                  <ErButton size="sm" variant="ghost" :disabled="busy" @click="confirmation = null">No</ErButton>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </template>
    </div>

    <template #footer>
      <ErButton variant="ghost" @click="emit('close')">
        Cerrar
      </ErButton>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { ErButton } from '@/design-system'
import AppModal from '@/shared/AppModal.vue'
import { setVisibility, listMembers, setCompositionBand, setMemberRole, removeMember } from '@/api/sharing'
import { getComposition, type Visibility } from '@/api/compositions'
import { listBands, getBand, type BandSummary, type BandResponse } from '@/api/bands'
import { useEntitlements } from '@/features/plan/useEntitlements'
import { bandErrorMessage } from '@/features/bands/bandErrors'

const props = withDefaults(
  defineProps<{
    compositionId: string
    title?: string
    visibility?: Visibility
    isPublic?: boolean
    shareSlug?: string | null
    canManage?: boolean
  }>(),
  {
    title: 'Composición',
    visibility: undefined,
    isPublic: undefined,
    shareSlug: null,
    canManage: true,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'visibilityChanged', visibility: Visibility | boolean): void
}>()

const currentVisibility = ref<Visibility>(
  props.visibility || (props.isPublic ? 'public' : 'private')
)

const copied = ref(false)
const error = ref<string | null>(null)
const loading = ref(false)
const busy = ref(false)
const bands = ref<BandSummary[]>([])
const attachedBand = ref<BandResponse | null>(null)
const selectedBand = ref('')
const bandEditable = ref(false)
const ownerId = ref('')
const roles = ref<Record<string, 'editor' | 'viewer'>>({})
const confirmation = ref<string | null>(null)
const slug = ref(props.shareSlug)
const { entitlements } = useEntitlements()
const canShare = computed(() => entitlements.value?.can_share_with_people === true)
const selectedActive = computed(() => bands.value.some(b => b.id === selectedBand.value && b.active))
const bandMembers = computed(() => attachedBand.value?.members.filter(m => m.user_id !== ownerId.value) || [])
let generation = 0
onBeforeUnmount(() => { generation++ })

const shareUrl = computed(() => `${window.location.origin}/c/${slug.value || props.compositionId}`)

async function selectVisibility(vis: Visibility) {
  if (vis === currentVisibility.value || busy.value) return
  busy.value = true
  error.value = null
  try {
    const res = await setVisibility(props.compositionId, vis)
    currentVisibility.value = res.visibility
    slug.value = res.share_slug || slug.value
    emit('visibilityChanged', props.visibility !== undefined ? res.visibility : res.visibility === 'public')
  } catch (reason) {
    error.value = bandErrorMessage(reason)
  } finally { busy.value = false }
}

async function copyShareLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
  } catch { error.value = 'No pudimos copiar el enlace. Cópialo desde el campo.' }
}

async function loadSharing() {
  const current = ++generation
  if (!props.canManage || !canShare.value) return
  loading.value = true
  error.value = null
  try {
    const [composition, available, members] = await Promise.all([
      getComposition(props.compositionId), listBands(), listMembers(props.compositionId),
    ])
    // The modal loads its own band context so reopening always reflects backend state.
    const context = composition as typeof composition & { band_id?: string | null; band_editable?: boolean }
    const band = context.band_id ? await getBand(context.band_id) : null
    if (current !== generation) return
    ownerId.value = composition.owner_id
    bands.value = available
    attachedBand.value = band
    selectedBand.value = band?.id || ''
    bandEditable.value = context.band_editable ?? false
    roles.value = Object.fromEntries(members.filter(m => m.role !== 'owner').map(m => [m.user_id, m.role])) as typeof roles.value
  } catch (reason) {
    if (current === generation) error.value = bandErrorMessage(reason)
  } finally { if (current === generation) loading.value = false }
}

async function mutate(action: () => Promise<void>) {
  if (busy.value || loading.value || !canShare.value || !props.canManage) return
  busy.value = true
  error.value = null
  try { await action(); confirmation.value = null }
  catch (reason) { error.value = bandErrorMessage(reason) }
  finally { busy.value = false }
}

async function saveBand() {
  if (!selectedActive.value) return
  await mutate(async () => {
    await setCompositionBand(props.compositionId, selectedBand.value, bandEditable.value)
    await loadSharing()
  })
}
async function detachBand() {
  await mutate(async () => {
    await setCompositionBand(props.compositionId, null, false)
    attachedBand.value = null
    selectedBand.value = ''
    bandEditable.value = false
    roles.value = {}
  })
}
async function changeRole(userId: string, event: Event) {
  const select = event.target as HTMLSelectElement
  const role = select.value
  if (role !== 'editor' && role !== 'viewer') return
  await mutate(async () => {
    await setMemberRole(props.compositionId, userId, role)
    roles.value[userId] = role
  })
  select.value = roles.value[userId] || ''
}
async function deleteRole(userId: string) {
  await mutate(async () => {
    await removeMember(props.compositionId, userId)
    delete roles.value[userId]
  })
}
watch([canShare, () => props.canManage], loadSharing, { immediate: true })
</script>
