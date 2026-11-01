<script setup>
import { computed } from 'vue'
import { formatTime } from '../../data/sample.js'

const props = defineProps({
  seed: { type: Number, default: 3 },
  length: { type: Number, required: true },
  position: { type: Number, default: 0 },
  bars: { type: Number, default: 64 },
  marks: { type: Array, default: () => [] }, // segundos con comentario
  height: { type: String, default: 'h-16' },
})
const emit = defineEmits(['seek'])

const list = computed(() => {
  const out = []
  for (let i = 0; i < props.bars; i++) {
    const v = 0.2 + 0.8 * Math.abs(Math.sin((i * 0.37 * props.seed) / 3) * Math.cos(i * 0.11 + props.seed))
    const at = Math.round((i / props.bars) * props.length)
    out.push({ i, h: Math.round(v * 100) + '%', at, played: i / props.bars < props.position / props.length })
  }
  return out
})
const markList = computed(() => props.marks.map((m) => ({ at: m, left: (m / props.length) * 100 + '%' })))
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
