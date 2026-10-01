<template>
  <div class="er-app" :data-theme="currentTheme">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'

const currentTheme = ref<'noche' | 'matine'>('noche')
</script>
