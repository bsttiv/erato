<template>
  <AppModal :open="true" title="// compartir composición" @close="emit('close')">
    <!-- Visibility toggle -->
    <div class="er-field">
      <label class="er-label">Visibilidad pública</label>
      <div class="er-field-row">
        <ErTag :tone="isPublicLocal ? 'moss' : 'neutral'">
          {{ isPublicLocal ? 'Pública' : 'Privada' }}
        </ErTag>
        <ErButton
          v-if="canManage"
          size="sm"
          variant="ghost"
          :disabled="toggling"
          @click="toggleVisibility"
        >
          {{ isPublicLocal ? 'Hacer privada' : 'Hacer pública' }}
        </ErButton>
      </div>
      <p class="er-hint">
        {{
          isPublicLocal
            ? 'Cualquiera con el enlace público puede ver los acordes, letra y escuchar demos.'
            : 'Solo los colaboradores invitados con cuenta pueden acceder a esta composición.'
        }}
      </p>
    </div>

    <!-- Invites management -->
    <div v-if="canManage" class="er-invites-block">
      <div class="er-label">
        // invitaciones para edición
      </div>

      <div>
        <ErButton
          size="sm"
          variant="primary"
          icon="plus"
          :disabled="creatingInvite"
          @click="handleCreateInvite"
        >
          Generar enlace de invitación
        </ErButton>
      </div>

      <div v-if="newInviteUrl" class="er-invite-created er-panel">
        <div class="er-label">
          ¡Invitación creada!
        </div>
        <p class="er-share-link">
          {{ newInviteUrl }}
        </p>
      </div>

      <div v-if="loadingInvites" class="er-loading">
        Cargando invitaciones activas…
      </div>
      <ul v-else-if="invites.length" class="er-invites-list">
        <li
          v-for="inv in invites"
          :key="inv.id"
          class="er-member"
        >
          <span class="er-member-role">
            Expira: {{ new Date(inv.expires_at).toLocaleDateString() }}
          </span>
          <ErButton
            size="sm"
            variant="danger"
            icon="x"
            @click="handleRevoke(inv.id)"
          >
            Revocar
          </ErButton>
        </li>
      </ul>
      <div v-else class="er-hint">
        No hay invitaciones activas.
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
import { ref, onMounted } from 'vue'
import { ErButton, ErTag } from '@/design-system'
import AppModal from '@/shared/AppModal.vue'
import {
  setVisibility,
  createInvite,
  listInvites,
  revokeInvite,
  type InviteResponse,
} from '@/api/sharing'

const props = withDefaults(
  defineProps<{
    compositionId: string
    isPublic: boolean
    canManage?: boolean
  }>(),
  {
    canManage: false,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'visibilityChanged', isPublic: boolean): void
}>()

const isPublicLocal = ref(props.isPublic)
const toggling = ref(false)
const invites = ref<InviteResponse[]>([])
const loadingInvites = ref(false)
const creatingInvite = ref(false)
const newInviteUrl = ref<string | null>(null)

async function toggleVisibility() {
  toggling.value = true
  try {
    const next = !isPublicLocal.value
    const res = await setVisibility(props.compositionId, next ? 'public' : 'private')
    isPublicLocal.value = res.visibility === 'public'
    emit('visibilityChanged', res.visibility === 'public')
  } catch {
    // revert
  } finally {
    toggling.value = false
  }
}

async function fetchInvites() {
  if (!props.canManage) return
  loadingInvites.value = true
  try {
    invites.value = await listInvites(props.compositionId)
  } catch {
    invites.value = []
  } finally {
    loadingInvites.value = false
  }
}

async function handleCreateInvite() {
  creatingInvite.value = true
  newInviteUrl.value = null
  try {
    const res = await createInvite(props.compositionId, { role: 'editor' })
    invites.value.push(res)
    if (res.token) {
      newInviteUrl.value = `${window.location.origin}/invite/${res.token}`
    } else if (res.invite_url) {
      newInviteUrl.value = res.invite_url
    }
  } catch {
    // handle error
  } finally {
    creatingInvite.value = false
  }
}

async function handleRevoke(inviteId: string) {
  try {
    await revokeInvite(props.compositionId, inviteId)
    invites.value = invites.value.filter((i) => i.id !== inviteId)
  } catch {
    // handle error
  }
}

onMounted(() => {
  fetchInvites()
})
</script>
