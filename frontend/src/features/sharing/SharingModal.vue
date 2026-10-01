<template>
  <div class="er-modal-backdrop" @click.self="emit('close')">
    <div class="er-modal er-panel">
      <div class="er-label">
        // compartir composición
      </div>

      <!-- Visibility toggle -->
      <div class="er-field" style="margin: var(--space-4) 0">
        <label class="er-label">Visibilidad pública</label>
        <div class="er-row" style="gap: var(--space-2); align-items: center">
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
        <p class="er-hint" style="font-size: 0.85em; margin-top: var(--space-1)">
          {{
            isPublicLocal
              ? 'Cualquiera con el enlace público puede ver los acordes, letra y escuchar demos.'
              : 'Solo los colaboradores invitados con cuenta pueden acceder a esta composición.'
          }}
        </p>
      </div>

      <!-- Invites management -->
      <div v-if="canManage" class="er-invites-block" style="margin-top: var(--space-6)">
        <div class="er-label">
          // invitaciones para edición
        </div>

        <div style="margin: var(--space-2) 0">
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

        <div v-if="newInviteUrl" class="er-invite-created er-panel" style="margin-bottom: var(--space-4)">
          <div class="er-label" style="color: var(--amber)">
            ¡Invitación creada!
          </div>
          <p style="font-size: 0.85em; word-break: break-all">
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
            class="er-row"
            style="justify-content: space-between; align-items: center; padding: var(--space-2) 0; border-bottom: 1px solid var(--line)"
          >
            <span style="font-size: 0.85em; color: var(--ink-muted)">
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
        <div v-else style="font-size: 0.85em; color: var(--ink-faint)">
          No hay invitaciones activas.
        </div>
      </div>

      <div class="er-row" style="justify-content: flex-end; margin-top: var(--space-6)">
        <ErButton variant="ghost" @click="emit('close')">
          Cerrar
        </ErButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ErButton, ErTag } from '@/design-system'
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
