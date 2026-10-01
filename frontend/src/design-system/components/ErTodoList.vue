<template>
  <div :class="['er-todo', 'er-panel', customClass]">
    <div v-if="title" class="er-label">
      // {{ title }}
    </div>

    <div class="er-compose">
      <input
        v-model="draft"
        class="er-input"
        :placeholder="placeholder || 'Nueva tarea…'"
        @keydown.enter="add"
      >
      <ErButton
        variant="primary"
        :disabled="!draft.trim()"
        @click="add"
      >
        Agregar
      </ErButton>
    </div>

    <ul v-if="currentItems.length" class="er-todo-list">
      <li
        v-for="x in currentItems"
        :key="x.id"
        :class="['er-todo-item', x.done && 'is-done']"
      >
        <button
          type="button"
          role="checkbox"
          class="er-check"
          :aria-checked="x.done ? 'true' : 'false'"
          :aria-label="x.text"
          @click="toggle(x.id)"
        >
          <ErIcon v-if="x.done" name="check" />
        </button>
        <span class="er-todo-text">{{ x.text }}</span>
        <button
          type="button"
          class="er-iconbtn"
          :aria-label="`Borrar ${x.text}`"
          @click="remove(x.id)"
        >
          <ErIcon name="x" />
        </button>
      </li>
    </ul>
    <div v-else class="er-todo-empty">
      Nada pendiente. Toca otra vez desde el coro.
    </div>

    <div class="er-todo-foot">
      <span>
        {{ left }} {{ left === 1 ? 'pendiente' : 'pendientes' }} ·
        {{ done }} {{ done === 1 ? 'hecha' : 'hechas' }}
      </span>
      <ErButton
        v-if="done"
        size="sm"
        variant="ghost"
        @click="clearDone"
      >
        Limpiar hechas
      </ErButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import ErIcon from './ErIcon.vue'
import ErButton from './ErButton.vue'

export interface TodoItem {
  id: string
  text: string
  done: boolean
}

let uid = 0

const props = withDefaults(
  defineProps<{
    modelValue?: TodoItem[]
    defaultItems?: TodoItem[]
    title?: string
    placeholder?: string
    customClass?: string
  }>(),
  {
    placeholder: 'Nueva tarea…',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', items: TodoItem[]): void
  (e: 'change', items: TodoItem[]): void
}>()

const initial = props.modelValue || props.defaultItems || []
const currentItems = ref<TodoItem[]>(initial.slice())
const draft = ref('')

watch(
  () => props.modelValue,
  (newItems) => {
    if (newItems) {
      currentItems.value = newItems.slice()
    }
  },
  { deep: true }
)

const left = computed(() => currentItems.value.filter((x) => !x.done).length)
const done = computed(() => currentItems.value.length - left.value)

function notify(items: TodoItem[]) {
  currentItems.value = items
  emit('update:modelValue', items)
  emit('change', items)
}

function add() {
  const v = draft.value.trim()
  if (!v) return
  const newItem: TodoItem = {
    id: 't' + Date.now() + uid++,
    text: v,
    done: false,
  }
  draft.value = ''
  notify(currentItems.value.concat([newItem]))
}

function toggle(id: string) {
  const next = currentItems.value.map((x) =>
    x.id === id ? { ...x, done: !x.done } : x
  )
  notify(next)
}

function remove(id: string) {
  const next = currentItems.value.filter((x) => x.id !== id)
  notify(next)
}

function clearDone() {
  const next = currentItems.value.filter((x) => !x.done)
  notify(next)
}
</script>
