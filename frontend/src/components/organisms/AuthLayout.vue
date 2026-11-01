<script setup lang="ts">
import Wordmark from '../atoms/Wordmark.vue'
import StageLamp from '../atoms/StageLamp.vue'

// Pantalla dividida para inicio de sesión y registro: el escenario a un lado, el formulario al otro.
defineProps<{ headline: string; points?: string[] }>()
</script>

<template>
  <div class="min-h-screen bg-ground text-ink lg:grid lg:grid-cols-2">
    <div class="relative flex flex-col justify-between gap-10 overflow-hidden bg-surface bg-lamp px-4 pb-10 pt-5 sm:px-10 lg:min-h-screen lg:pb-14">
      <StageLamp :cord="150"></StageLamp>
      <div class="relative"><Wordmark size="text-[32px]"></Wordmark></div>
      <div class="relative mt-32 max-w-[520px] lg:mt-0">
        <p class="font-display text-[40px] leading-none tracking-tight sm:text-[56px] lg:text-[64px]">{{ headline }}</p>
        <ul v-if="points?.length" class="mt-8 hidden list-none gap-3 p-0 text-lg leading-snug sm:grid">
          <li v-for="p in points" :key="p" class="flex items-baseline gap-3"><span class="h-2 w-2 shrink-0 translate-y-[-2px] rounded-full bg-brass" aria-hidden="true"></span>{{ p }}</li>
        </ul>
      </div>
    </div>
    <main class="flex items-center justify-center px-4 py-12 sm:px-6">
      <div class="w-full max-w-[440px]">
        <slot></slot>
      </div>
    </main>
  </div>
</template>
