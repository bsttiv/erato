<script setup lang="ts">
import { computed } from 'vue'
import { NOTE_NAMES } from '../../lib/chords'

// Teclado de dos octavas (C3–B4). keys: índices 0–23 marcados.
const props = defineProps<{ keys: number[]; disabled?: boolean; baseMidi?: number }>()
const emit = defineEmits<{ change: [next: number[]] }>()

const WHITE = [0, 2, 4, 5, 7, 9, 11]
const WHITE_NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
const BLACK: [number, number][] = [[1, 1], [3, 2], [6, 4], [8, 5], [10, 6]] // [semitono, tecla blanca a su derecha]

const whites = computed(() => {
  const out: { k: number; name: string }[] = []
  for (let o = 0; o < 2; o++) WHITE.forEach((s, j) => out.push({ k: o * 12 + s, name: WHITE_NAMES[j] + (Math.floor((props.baseMidi ?? 48) / 12) - 1 + o) }))
  return out
})
const blacks = computed(() => {
  const out: { k: number; name: string; left: string }[] = []
  for (let o = 0; o < 2; o++) BLACK.forEach(([s, after]) => out.push({ k: o * 12 + s, name: NOTE_NAMES[s] + (Math.floor((props.baseMidi ?? 48) / 12) - 1 + o), left: ((o * 7 + after) / 14) * 100 + '%' }))
  return out
})
const isOn = (k: number) => props.keys.includes(k)
function toggle(k: number) {
  if (props.disabled) return
  emit('change', isOn(k) ? props.keys.filter((x) => x !== k) : props.keys.concat([k]))
}
</script>

<template>
  <div class="overflow-x-auto">
    <div class="relative flex h-48 min-w-[520px] sm:h-56" role="group" aria-label="Teclado de dos octavas">
      <button
        v-for="w in whites"
        :key="w.k"
        type="button"
        :disabled="disabled"
        class="relative mx-px flex-1 cursor-pointer rounded-b-md border-0 transition-colors"
        :class="isOn(w.k) ? 'bg-brass' : 'bg-ivory hover:bg-[#fff4e2]'"
        :aria-pressed="isOn(w.k) ? 'true' : 'false'"
        :aria-label="w.name"
        @click="toggle(w.k)"
      >
        <span class="absolute inset-x-0 bottom-2.5 text-center text-[13px] font-medium text-[#5a4632]">{{ w.name }}</span>
      </button>
      <button
        v-for="b in blacks"
        :key="b.k"
        type="button"
        :disabled="disabled"
        class="absolute top-0 z-10 h-[62%] w-[4.4%] -translate-x-1/2 cursor-pointer rounded-b border-0 transition-colors"
        :class="isOn(b.k) ? 'bg-[#c47d1c]' : 'bg-[#1a120c] hover:bg-[#3a2a1d]'"
        :style="{ left: b.left }"
        :aria-pressed="isOn(b.k) ? 'true' : 'false'"
        :aria-label="b.name"
        @click="toggle(b.k)"
      ></button>
    </div>
  </div>
</template>
