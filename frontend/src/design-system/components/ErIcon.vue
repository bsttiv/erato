<template>
  <svg
    :class="['er-ico', customClass]"
    viewBox="0 0 16 16"
    aria-hidden="true"
    :fill="name === 'play' ? 'currentColor' : 'none'"
    stroke="currentColor"
    :stroke-width="name === 'pause' ? 2.25 : 1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path :d="PATHS[name]" />
  </svg>
</template>

<script setup lang="ts">
export type IconName =
  | 'play'
  | 'pause'
  | 'plus'
  | 'x'
  | 'check'
  | 'max'
  | 'min'
  | 'left'
  | 'right'
  | 'bar'
  | 'guitar'
  | 'piano'
  | 'menu'

defineProps<{
  name: IconName
  customClass?: string
}>()

const PATHS: Record<IconName, string> = {
  play: 'M5 3.5v9l7.5-4.5z',
  pause: 'M5 3.5v9M11 3.5v9',
  plus: 'M8 3v10M3 8h10',
  x: 'M4 4l8 8M12 4l-8 8',
  check: 'M3.5 8.5l3 3 6-7',
  max: 'M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3',
  min: 'M6 3v3H3M10 3v3h3M6 13v-3H3M10 13v-3h3',
  left: 'M10 3.5L5.5 8 10 12.5',
  right: 'M6 3.5L10.5 8 6 12.5',
  bar: 'M8 3v10',
  guitar: 'M10.5 2.5l3 3M12 4L7.5 8.5M7 7.5c-1.5-1-3.5-.5-4 1s-.5 3 1 4.5 3.5 1.5 4.5 1 2-2.5 1-4',
  piano: 'M2.5 3.5h11v9h-11zM6 3.5v5M10 3.5v5M8 8.5v4',
  menu: 'M2.5 4h11M2.5 8h11M2.5 12h11',
}
</script>
