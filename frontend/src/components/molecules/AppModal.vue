<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

const props = defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)

function sync(open: boolean) {
  if (open && !dialog.value?.open) dialog.value?.showModal()
  if (!open && dialog.value?.open) dialog.value.close()
}
watch(() => props.open, sync, { flush: 'post' })
onMounted(() => sync(props.open))
</script>

<template>
  <dialog ref="dialog" class="m-auto max-h-[90dvh] w-[min(760px,calc(100vw-2rem))] overflow-y-auto rounded-md bg-surface p-5 text-ink backdrop:bg-black/70 sm:p-8" :aria-label="title" @close="emit('close')">
    <div v-if="open">
      <div class="flex items-baseline justify-between gap-4">
        <h2 class="text-[26px]">{{ title }}</h2>
        <button type="button" class="btn-ghost btn-sm" @click="emit('close')">Cerrar</button>
      </div>
      <div class="mt-4"><slot></slot></div>
    </div>
  </dialog>
</template>
