<script setup>
// Sección de característica: texto con cuatro puntos a la izquierda y la interfaz a la derecha.
defineProps({
  id: { type: String, required: true },
  kicker: { type: String, required: true },
  title: { type: String, required: true },
  points: { type: Array, required: true },
})
</script>

<template>
  <section :id="id" class="scroll-mt-6 py-20 sm:py-28 lg:py-32">
    <div class="page-x grid items-center gap-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
      <div>
        <p class="text-[15px] font-medium text-brass">{{ kicker }}</p>
        <h2 class="mt-4 max-w-[12ch] text-[44px] leading-[0.98] sm:text-[60px] lg:text-[72px]">{{ title }}</h2>
        <ol class="mt-10 grid list-none gap-6 p-0 sm:mt-12">
          <li v-for="(p, i) in points" :key="i" class="grid grid-cols-[44px_1fr] items-baseline gap-3 text-lg leading-normal">
            <span class="font-display text-[26px] leading-none text-brass">{{ String(i + 1).padStart(2, '0') }}</span>
            <span>{{ p }}</span>
          </li>
        </ol>
      </div>
      <div class="relative min-w-0">
        <div class="pointer-events-none absolute -inset-16 bg-spot" aria-hidden="true"></div>
        <div class="relative">
          <slot></slot>
        </div>
      </div>
    </div>
  </section>
</template>
