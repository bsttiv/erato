<template>
  <form class="er-auth-form" @submit.prevent="submit">
    <p v-if="error" role="alert" class="er-auth-error">{{ error }}</p>
    <div class="er-field">
      <label for="band-create-name" class="er-label">Nombre de la banda</label>
      <input id="band-create-name" v-model="name" class="er-input" required maxlength="80" :disabled="busy">
    </div>
    <div class="er-comp-header-nav-left">
      <ErButton type="submit" variant="primary" :disabled="busy || !name.trim()">Crear banda</ErButton>
      <ErButton :disabled="busy" @click="emit('cancel')">Cancelar</ErButton>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErButton } from '@/design-system'
import { createBand, type BandResponse } from '@/api/bands'
import { bandErrorMessage } from './bandErrors'

const emit = defineEmits<{ created: [band: BandResponse]; cancel: [] }>()
const name = ref('')
const busy = ref(false)
const error = ref('')
async function submit() {
  if (busy.value || !name.value.trim()) return
  busy.value = true
  error.value = ''
  try { emit('created', await createBand(name.value.trim())) }
  catch (reason) { error.value = bandErrorMessage(reason) }
  finally { busy.value = false }
}
</script>
