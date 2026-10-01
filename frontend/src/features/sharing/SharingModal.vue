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
          :class="['er-share-card', { 'is-active': currentVisibility === 'public' }]"
          :aria-pressed="currentVisibility === 'public'"
          @click="selectVisibility('public')"
        >
          <span class="er-label">Con enlace</span>
          <span class="er-hint">
            Cualquiera con el enlace puede ver la letra, acordes y escuchar los demos.
          </span>
        </button>

        <button
          type="button"
          :class="['er-share-card', { 'is-active': currentVisibility === 'private' }]"
          :aria-pressed="currentVisibility === 'private'"
          @click="selectVisibility('private')"
        >
          <span class="er-label">Privada</span>
          <span class="er-hint">
            Solo las personas invitadas pueden acceder a esta composición.
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

    <!-- Invites and member list -->
    <div v-if="canManage" class="er-invites-block">
      <div class="er-label">
        // INVITAR A COLABORAR
      </div>

      <div class="er-invite-row">
        <input
          v-model="inviteEmail"
          type="email"
          placeholder="correo@ejemplo.com"
          class="er-input"
        >
        <select v-model="inviteRole" class="er-select">
          <option value="editor">
            Editor (puede editar)
          </option>
          <option value="viewer">
            Solo ver (lector)
          </option>
        </select>
        <ErButton
          data-test="send-invite-btn"
          variant="primary"
          :disabled="sendingInvite || !inviteEmail"
          @click="handleSendInvite"
        >
          Invitar
        </ErButton>
      </div>

      <!-- Newly created invite banner -->
      <div v-if="newInviteUrl" class="er-invite-created er-panel">
        <div class="er-label">
          Invitación creada
        </div>
        <p class="er-share-link">
          {{ newInviteUrl }}
        </p>
      </div>

      <!-- Member and pending invites list -->
      <div class="er-field">
        <div class="er-label">
          // MIEMBROS DE LA CANCIÓN
        </div>

        <div v-if="loadingMembers" class="er-loading">
          Cargando colaboradores...
        </div>
        <ul v-else-if="members.length" class="er-invites-list">
          <li
            v-for="(m, idx) in members"
            :key="m.user_id || m.invite_id || idx"
            class="er-member"
          >
            <div class="er-field-row">
              <span class="er-avatar">
                {{ m.initials || '?' }}
              </span>
              <div>
                <span class="er-member-id">{{ m.display_name || m.email }}</span>
                <span v-if="m.display_name && m.email" class="er-hint">
                  ({{ m.email }})
                </span>
              </div>
            </div>

            <div class="er-field-row">
              <ErTag v-if="m.pending" tone="amber">
                invitación pendiente
              </ErTag>
              <ErTag :tone="roleTone(m.role)">
                {{ roleLabel(m.role) }}
              </ErTag>
              <ErButton
                v-if="m.pending && m.invite_id"
                variant="ghost"
                size="sm"
                @click="handleRevoke(m.invite_id)"
              >
                Revocar
              </ErButton>
            </div>
          </li>
        </ul>
        <div v-else class="er-hint">
          No hay miembros agregados.
        </div>
      </div>
    </div>

    <template #footer>
      <ErButton variant="ghost" @click="emit('close')">
        Cerrar
      </ErButton>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ErButton, ErTag } from '@/design-system'
import AppModal from '@/shared/AppModal.vue'
import {
  setVisibility,
  createInvite,
  listMembers,
  revokeInvite,
  type MemberDetail,
  type MemberRole,
} from '@/api/sharing'
import type { Visibility } from '@/api/compositions'

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
const inviteEmail = ref('')
const inviteRole = ref<'editor' | 'viewer'>('editor')
const sendingInvite = ref(false)
const newInviteUrl = ref<string | null>(null)

const members = ref<MemberDetail[]>([])
const loadingMembers = ref(false)

const shareUrl = computed(() => {
  const slug = props.shareSlug || props.compositionId
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.origin}/c/${slug}`
  }
  return `/c/${slug}`
})

function roleLabel(role: MemberRole | string): string {
  if (role === 'owner') return 'Dueño'
  if (role === 'editor') return 'Editor'
  if (role === 'viewer') return 'Solo ver'
  return role
}

function roleTone(role: MemberRole | string): 'amber' | 'wine' | 'neutral' {
  if (role === 'owner') return 'amber'
  if (role === 'editor') return 'wine'
  return 'neutral'
}

async function selectVisibility(vis: Visibility) {
  if (vis === currentVisibility.value) return
  try {
    const res = await setVisibility(props.compositionId, vis)
    currentVisibility.value = res.visibility as Visibility
    if (props.visibility !== undefined) {
      emit('visibilityChanged', res.visibility as Visibility)
    } else {
      emit('visibilityChanged', res.visibility === 'public')
    }
  } catch {
    // Revert or show error
  }
}

async function copyShareLink() {
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(shareUrl.value)
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } catch {
      // Fallback
    }
  }
}

async function loadMembers() {
  if (!props.canManage) return
  loadingMembers.value = true
  try {
    members.value = await listMembers(props.compositionId)
  } catch {
    members.value = []
  } finally {
    loadingMembers.value = false
  }
}

async function handleSendInvite() {
  if (!inviteEmail.value) return
  sendingInvite.value = true
  newInviteUrl.value = null
  try {
    const res = await createInvite(props.compositionId, {
      invited_email: inviteEmail.value,
      role: inviteRole.value,
    })
    if (res.invite_url) {
      newInviteUrl.value = res.invite_url
    } else if (res.token) {
      newInviteUrl.value = `${window.location.origin}/invite/${res.token}`
    }
    inviteEmail.value = ''
    await loadMembers()
  } catch {
    // Error handling
  } finally {
    sendingInvite.value = false
  }
}

async function handleRevoke(inviteId: string) {
  try {
    await revokeInvite(props.compositionId, inviteId)
    await loadMembers()
  } catch {
    // Error handling
  }
}

onMounted(() => {
  loadMembers()
})
</script>
