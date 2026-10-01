<template>
  <span :class="['er-tag', tone !== 'neutral' && `er-tag--${tone}`]">
    <span v-if="dot" class="er-tag-dot" aria-hidden="true" />
    <slot />
  </span>
</template>

<script setup lang="ts">
export type Tone = 'neutral' | 'amber' | 'ember' | 'wine' | 'moss'

withDefaults(
  defineProps<{
    tone?: Tone
    dot?: boolean
  }>(),
  {
    tone: 'neutral',
    dot: false,
  }
)
</script>
