<template>
  <button
    type="button"
    :class="[
      'er-btn',
      `er-btn--${variant}`,
      size === 'sm' && 'er-btn--sm',
    ]"
    :disabled="disabled"
  >
    <ErIcon v-if="icon" :name="icon" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import ErIcon, { type IconName } from './ErIcon.vue'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'quiet' | 'ghost' | 'danger'
    size?: 'md' | 'sm'
    icon?: IconName
    disabled?: boolean
  }>(),
  {
    variant: 'quiet',
    size: 'md',
    disabled: false,
  }
)
</script>
