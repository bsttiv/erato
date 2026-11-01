<script setup lang="ts">
import { ref } from 'vue'
import { MAX_DEMO_BYTES } from '../../api/demos'

// Subida de una demo: elige un audio y avisa al padre; el padre hace la subida y muestra el progreso.
defineProps<{ busy: boolean; progress: number }>()
const emit = defineEmits<{ pick: [file: File]; reject: [message: string] }>()
const input = ref<HTMLInputElement | null>(null)

function choose(event: Event) {
  const el = event.target as HTMLInputElement
  const file = el.files?.[0]
  el.value = ''
  if (!file) return
  if (file.size > MAX_DEMO_BYTES) { emit('reject', 'El archivo pesa más de 100 MB.'); return }
  emit('pick', file)
}
</script>

<template>
  <div id="subir" class="mt-4 rounded-md bg-surface p-6 text-center">
    <p class="text-base">{{ busy ? 'Subiendo demo…' : 'Sube un audio' }}</p>
    <p id="subir-ayuda" class="mt-1.5 text-sm text-muted">MP3, WAV o M4A, hasta 100 MB</p>
    <progress v-if="busy" class="mt-3 w-full" max="100" :value="Math.round(progress * 100)" aria-label="Progreso de la subida"></progress>
    <p v-if="busy" role="status" class="mt-1.5 text-sm tabular-nums">{{ Math.round(progress * 100) }} %</p>
    <label v-else class="btn-ghost relative mt-3.5 bg-ground">Elegir archivo<input ref="input" type="file" accept="audio/*" class="absolute inset-0 cursor-pointer opacity-0" aria-describedby="subir-ayuda" @change="choose" /></label>
  </div>
</template>
