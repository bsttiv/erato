<template>
  <div class="er-modal-backdrop" @click.self="emit('close')">
    <div class="er-modal er-panel">
      <div class="er-label">
        // nueva composición
      </div>
      <form @submit.prevent="handleSubmit">
        <div class="er-field">
          <label for="comp-title" class="er-label">Título</label>
          <input
            id="comp-title"
            v-model="title"
            type="text"
            class="er-input"
            placeholder="Título de la composición…"
            required
          >
        </div>

        <div class="er-field-row" style="margin: var(--space-4) 0">
          <label class="er-checkbox-label">
            <input v-model="isPublic" type="checkbox">
            Hacer pública desde el inicio
          </label>
        </div>

        <div v-if="error" class="er-auth-error">
          {{ error }}
        </div>

        <div class="er-row" style="gap: var(--space-2); justify-content: flex-end">
          <ErButton variant="ghost" @click="emit('close')">
            Cancelar
          </ErButton>
          <ErButton
            type="submit"
            variant="primary"
            :disabled="loading || !title.trim()"
          >
            {{ loading ? 'Creando…' : 'Crear' }}
          </ErButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErButton } from '@/design-system'
import { createComposition, type CompositionResponse } from '@/api/compositions'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', comp: CompositionResponse): void
}>()

const title = ref('')
const isPublic = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!title.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const comp = await createComposition({
      title: title.value.trim(),
      is_public: isPublic.value,
    })
    emit('created', comp)
  } catch (err: any) {
    error.value = err.message || 'Error al crear composición'
  } finally {
    loading.value = false
  }
}
</script>
