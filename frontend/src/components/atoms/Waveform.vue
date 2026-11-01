<script setup lang="ts">
import { computed } from 'vue'
import { formatTime } from '../../data/sample'

const props = defineProps<{ seed?: number; length: number; position?: number; bars?: number; marks?: number[]; height?: string }>() // marks: segundos con comentario
const emit = defineEmits<{ seek: [at: number] }>()

const list = computed(() => {
  const out: { i: number; h: string; at: number; played: boolean }[] = []
  for (let i = 0; i < (props.bars ?? 64); i++) {
    const v = 0.2 + 0.8 * Math.abs(Math.sin((i * 0.37 * (props.seed ?? 3)) / 3) * Math.cos(i * 0.11 + (props.seed ?? 3)))
    const at = Math.round(i / (props.bars ?? 64) * props.length)
    out.push({ i, h: Math.round(v * 100) + '%', at, played: i / (props.bars ?? 64) < (props.position ?? 0) / props.length })
  }
  return out
})
const markList = computed(() => (props.marks ?? []).map((m) => ({ at: m, left: (m / props.length) * 100 + '%' })))
</script>

<template>
  <div class="relative flex items-center gap-[2px] sm:gap-[3px]" :class="height" role="group" aria-label="Forma de onda: toca para saltar a ese momento">
    <button
      v-for="b in list"
      :key="b.i"
      type="button"
      tabindex="-1"
      class="min-w-0 flex-1 cursor-pointer rounded-[1px] border-0 p-0 transition-colors hover:bg-[#ffd28a]"
      :class="b.played ? 'bg-brass' : 'bg-fret'"
      :style="{ height: b.h }"
      :aria-label="'Ir a ' + formatTime(b.at)"
      @click="emit('seek', b.at)"
    ></button>
    <button
      v-for="m in markList"
      :key="m.at"
      type="button"
      class="absolute -top-7 flex h-7 w-7 -translate-x-1/2 cursor-pointer items-center justify-center rounded-full border-0 bg-transparent p-0 after:h-3 after:w-3 after:rounded-full after:bg-ink after:content-['']"
      :style="{ left: m.left }"
      :aria-label="'Comentario en ' + formatTime(m.at)"
      @click="emit('seek', m.at)"
    ></button>
  </div>
</template>
