<script setup>
defineProps({
  items: { type: Array, required: true },
})
</script>

<template>
  <ul class="grid list-none gap-2 p-0">
    <li v-for="(h, i) in items" :key="i" class="flex flex-wrap justify-between gap-x-4 gap-y-1 rounded bg-surface px-5 py-4 text-base sm:text-[17px]">
      <span><b class="font-semibold">{{ h.who }}</b> {{ h.what }}</span>
      <span class="whitespace-nowrap text-muted">{{ h.when }}</span>
    </li>
  </ul>
</template>
