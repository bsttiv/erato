<template>
  <div class="er-modal-backdrop" @click.self="emit('close')">
    <div class="er-modal er-panel">
      <div class="er-label">
        // subir demo
      </div>
      <form @submit.prevent="handleSubmit">
        <div class="er-field">
          <label for="demo-title" class="er-label">Título de la toma</label>
          <input
            id="demo-title"
            v-model="title"
            type="text"
            class="er-input"
            placeholder="Ej. Toma acústica en Re"
            required
          >
        </div>

        <div class="er-field" style="margin: var(--space-4) 0">
          <label for="demo-file" class="er-label">Archivo de audio</label>
          <input
            id="demo-file"
            type="file"
            accept="audio/*"
            class="er-input"
            required
            @change="handleFileChange"
          >
        </div>

        <div v-if="error" class="er-auth-error">
          {{ error }}
        </div>

        <div v-if="uploading" class="er-loading" style="margin-bottom: var(--space-2)">
          Subiendo audio directamente a almacenamiento seguro…
        </div>

        <div class="er-row" style="gap: var(--space-2); justify-content: flex-end">
          <ErButton variant="ghost" :disabled="uploading" @click="emit('close')">
            Cancelar
          </ErButton>
          <ErButton
            type="submit"
            variant="primary"
            :disabled="uploading || !selectedFile || !title.trim()"
          >
            {{ uploading ? 'Subiendo…' : 'Subir demo' }}
          </ErButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ErButton } from '@/design-system'
import {
  requestUploadSignature,
  confirmUpload,
  type DemoTake,
} from '@/api/demos'

const props = defineProps<{
  compositionId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'uploaded', demo: DemoTake): void
}>()

const title = ref('')
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref<string | null>(null)

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  } else {
    selectedFile.value = null
  }
}

async function handleSubmit() {
  if (!selectedFile.value || !title.value.trim()) return

  uploading.value = true
  error.value = null

  try {
    // 1. Request signed upload parameters from backend (never sending file bytes)
    const sig = await requestUploadSignature(props.compositionId)

    // 2. Build form data for direct-to-Cloudinary upload
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('api_key', sig.api_key)
    formData.append('timestamp', String(sig.timestamp))
    formData.append('signature', sig.signature)
    formData.append('folder', sig.folder)
    formData.append('tags', sig.tags)
    formData.append('type', sig.type)

    // 3. Direct POST to Cloudinary endpoint
    const cloudUrl = `https://api.cloudinary.com/v1_1/${sig.cloud_name}/auto/upload`
    const cloudRes = await fetch(cloudUrl, {
      method: 'POST',
      body: formData,
    })

    if (!cloudRes.ok) {
      throw new Error('Error al subir el archivo de audio a Cloudinary')
    }

    const cloudData = await cloudRes.json()

    // 4. Confirm upload on backend to verify signature and persist demo reference
    const confirmedDemo = await confirmUpload(props.compositionId, {
      public_id: cloudData.public_id,
      version: cloudData.version,
      signature: cloudData.signature,
      resource_type: cloudData.resource_type || 'video',
      duration: cloudData.duration,
      format: cloudData.format,
      bytes: cloudData.bytes,
      title: title.value.trim(),
    })

    emit('uploaded', confirmedDemo)
  } catch (err: any) {
    error.value = err.message || 'Error durante la subida del demo'
  } finally {
    uploading.value = false
  }
}
</script>
