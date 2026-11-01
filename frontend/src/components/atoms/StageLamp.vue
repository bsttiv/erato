<script setup lang="ts">
import { ref } from 'vue'
import type { CordPoint } from '../../lib/lampPhysics'

const props = defineProps({
  cord: { type: Number, default: 176 },
  flexible: { type: Boolean, default: false },
})
const rope = ref<SVGPathElement | null>(null)
const shade = ref<SVGGElement | null>(null)

// Paint only the small SVG geometry; the surrounding page does not re-render.
function setPose(points: CordPoint[]) {
  if (!props.flexible) return
  rope.value?.setAttribute('d', points.map((point, i) => `${i ? 'L' : 'M'}${60 + point.x} ${point.y}`).join(' '))
  const bob = points[points.length - 1]!
  const angle = -Math.atan2(bob.x, bob.y) * 180 / Math.PI
  shade.value?.setAttribute('transform', `translate(${bob.x} ${bob.y - props.cord}) rotate(${angle} 60 ${props.cord})`)
}
defineExpose({ setPose })
</script>

<template>
  <svg aria-hidden="true" width="120" :height="cord + 54" :viewBox="'0 0 120 ' + (cord + 54)" class="pointer-events-none absolute left-1/2 top-0 origin-top-left -translate-x-1/2" :style="flexible ? { overflow: 'visible' } : undefined">
    <path ref="rope" :d="`M60 0 L60 ${cord}`" fill="none" stroke="#5a4632" stroke-width="2"></path>
    <g ref="shade">
      <path :d="'M30 ' + (cord + 40) + ' L42 ' + (cord + 2) + ' L78 ' + (cord + 2) + ' L90 ' + (cord + 40) + ' Z'" fill="#8a6a3c"></path>
      <ellipse cx="60" :cy="cord + 40" rx="30" ry="6" fill="#ffd28a"></ellipse>
    </g>
  </svg>
</template>
