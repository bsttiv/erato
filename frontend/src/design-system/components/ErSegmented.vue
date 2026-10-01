<template>
  <div class="er-seg" :role="role || 'group'" :aria-label="label" :aria-disabled="disabled ? 'true' : undefined">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="er-seg-opt"
      :disabled="disabled"
      :role="role === 'tablist' ? 'tab' : undefined"
      :aria-pressed="opt.value === modelValue ? 'true' : 'false'"
      :aria-selected="opt.value === modelValue ? 'true' : 'false'"
      @click="!disabled && select(opt.value)"
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
  role?: string
  disabled?: boolean
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
