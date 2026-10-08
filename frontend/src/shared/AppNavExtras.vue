<template>
  <template v-if="authenticated">
    <RouterLink v-for="(item, index) in payments?.navItems" :key="index"
      :to="item.to" class="er-btn er-btn--ghost">
      {{ item.label }}
    </RouterLink>
  </template>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { RouterLink } from 'vue-router'
import { PAYMENT_EXTENSION_KEY } from '@/extension'
import { isAuthenticated } from '@/router/authReady'

const payments = inject(PAYMENT_EXTENSION_KEY, undefined)
const authenticated = computed(isAuthenticated)
</script>
