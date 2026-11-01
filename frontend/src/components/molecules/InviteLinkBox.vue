<script setup lang="ts">
import { ref, watch } from 'vue'

// Enlace de invitación recién creado: se muestra una sola vez (el servidor no lo guarda).
const props = defineProps<{ link: string; id: string }>()
const copied = ref(false)
const failed = ref(false)
watch(() => props.link, () => { copied.value = false; failed.value = false })

async function copy() {
  copied.value = false
  failed.value = false
  try {
    if (!navigator.clipboard) throw new Error('clipboardUnavailable')
    await navigator.clipboard.writeText(props.link)
    copied.value = true
  } catch { failed.value = true }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-2">
      <label :for="id" class="sr-only">Enlace de invitación</label>
      <input :id="id" type="text" readonly :value="link" class="field-input-dark min-w-0 flex-[1_1_240px]" @focus="($event.target as HTMLInputElement).select()" />
      <button type="button" class="btn-primary min-w-[136px]" @click="copy">{{ copied ? 'Copiado' : 'Copiar enlace' }}</button>
    </div>
    <p class="mt-2 text-sm text-muted" aria-live="polite">
      {{ failed ? 'No se pudo copiar el enlace. Puedes seleccionarlo y copiarlo manualmente.' : 'Cópialo ahora: por seguridad no se vuelve a mostrar.' }}
    </p>
  </div>
</template>
