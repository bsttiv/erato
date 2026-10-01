<template>
  <Teleport to="body" :disabled="!teleport">
    <div
      v-if="open"
      class="er-modal-backdrop"
      @click.self="onBackdropClick"
    >
      <div
        ref="modalRef"
        class="er-modal er-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="title || undefined"
      >
        <div v-if="title || $slots.header" class="er-modal-head">
          <slot name="header">
            <span v-if="title" class="er-modal-title er-label">{{ title }}</span>
          </slot>
          <button
            type="button"
            class="er-modal-close"
            aria-label="Cerrar"
            @click="emit('close')"
          >
            ×
          </button>
        </div>
        <div class="er-modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="er-modal-foot">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, toRef, onMounted, onUnmounted } from 'vue'
import { useFocusTrap } from './useFocusTrap'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    teleport?: boolean
  }>(),
  {
    open: false,
    title: '',
    teleport: false,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
}>()

const modalRef = ref<HTMLElement | null>(null)
const openRef = toRef(props, 'open')

useFocusTrap(modalRef, openRef)

function onBackdropClick() {
  emit('close')
}

function onGlobalKeydown(e: KeyboardEvent) {
  if (props.open && e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>
