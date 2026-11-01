<script setup>
defineProps({
  band: { type: Object, required: true },
  compositions: { type: Number, default: 12 },
})
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-5 rounded-md bg-raised px-5 py-5 sm:px-7">
    <div>
      <p class="font-display text-[36px] leading-none sm:text-[40px]">{{ band.name }}</p>
      <p class="mt-2 text-[15px]">Espacio de banda · {{ band.members.length }} integrantes · {{ compositions }} composiciones</p>
    </div>
    <div class="flex flex-wrap items-center gap-4">
      <div class="flex" :aria-label="band.members.length + ' integrantes'">
        <span v-for="(m, i) in band.members" :key="m.initials" class="avatar h-11 w-11 text-sm ring-2 ring-raised" :class="i ? '-ml-2.5' : ''" :style="{ background: m.color }">{{ m.initials }}</span>
      </div>
      <router-link to="/bandas/nueva" class="btn-ghost btn-sm bg-ground">Invitar</router-link>
    </div>
  </div>
</template>
