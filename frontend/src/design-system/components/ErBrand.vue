<template>
  <span class="er-brand">
    <span class="er-nav-lamp" aria-hidden="true" />
    <span class="er-nav-name">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string
  }>(),
  {
    label: 'Erato',
  }
)
</script>
