<template>
  <nav class="er-nav" :aria-label="heading || 'Navegación'">
    <div class="er-nav-brand">
      <div>
        <ErBrand :label="brand" />
        <div v-if="subtitle" class="er-nav-sub">{{ subtitle }}</div>
      </div>
    </div>
    <div class="er-label er-nav-heading">// {{ heading || 'composiciones' }}</div>
    <ul class="er-nav-list">
      <li v-for="(it, i) in items" :key="it.id">
        <button
          type="button"
          class="er-nav-item"
          :aria-current="it.id === currentActiveId ? 'true' : undefined"
          @click="selectItem(it.id)"
        >
          <span class="er-nav-num">{{ pad2(i) }}</span>
          <span>{{ it.label }}</span>
          <span v-if="it.meta" class="er-nav-meta">{{ it.meta }}</span>
        </button>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ErBrand from './ErBrand.vue'
import { pad2 } from '../core/format'

export interface SideNavItem {
  id: string
  label: string
  meta?: string
}

const props = withDefaults(
  defineProps<{
    brand?: string
    subtitle?: string
    heading?: string
    items: SideNavItem[]
    modelValue?: string
    activeId?: string
    defaultActiveId?: string
  }>(),
  {
    brand: 'Erato',
    heading: 'composiciones',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', id: string): void
  (e: 'select', id: string): void
}>()

const currentActiveId = computed(() => {
  return props.modelValue || props.activeId || props.defaultActiveId || props.items[0]?.id
})

function selectItem(id: string) {
  emit('update:modelValue', id)
  emit('select', id)
}
</script>
