<template>
  <div class="er-seg" role="group" :aria-label="label">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="er-seg-opt"
      :aria-pressed="opt.value === modelValue ? 'true' : 'false'"
      @click="select(opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
export interface SegmentedOption {
  value: string
  label: string
}

defineProps<{
  options: SegmentedOption[]
  modelValue: string
  label?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

function select(value: string) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>
