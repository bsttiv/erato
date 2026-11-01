<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  initial: { type: Array, default: () => [] },
})
const todos = ref(props.initial.map((t) => ({ ...t })))
const draft = ref('')
const doneCount = computed(() => todos.value.filter((t) => t.done).length)

function toggle(i) {
  todos.value[i].done = !todos.value[i].done
}
function add() {
  const text = draft.value.trim()
  if (!text) return
  todos.value.push({ text, done: false })
  draft.value = ''
}
</script>

<template>
  <div>
    <p class="text-sm text-muted">{{ doneCount }} de {{ todos.length }} listas</p>
    <ul class="mt-2 list-none p-0">
      <li v-for="(t, i) in todos" :key="i">
        <button type="button" class="flex min-h-[44px] w-full cursor-pointer items-center gap-3 border-0 bg-transparent py-1 text-left text-base text-ink" :aria-pressed="t.done ? 'true' : 'false'" @click="toggle(i)">
          <span class="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-[3px] border-2 border-solid transition-colors" :class="t.done ? 'border-brass bg-brass' : 'border-fret'" aria-hidden="true">
            <svg v-if="t.done" width="12" height="10" viewBox="0 0 12 10"><path d="M1 5 L4.5 8.5 L11 1" fill="none" stroke="#1a1108" stroke-width="2"></path></svg>
          </span>
          <span :class="t.done ? 'text-muted line-through' : ''">{{ t.text }}</span>
        </button>
      </li>
    </ul>
    <form class="mt-3 flex gap-2" @submit.prevent="add">
      <label for="todo-new" class="sr-only">Nueva tarea</label>
      <input id="todo-new" v-model="draft" type="text" placeholder="Nueva tarea" class="field-input-dark min-h-[44px] min-w-0 flex-1" />
      <button type="submit" class="btn-ghost btn-sm bg-ground">Agregar</button>
    </form>
  </div>
</template>
