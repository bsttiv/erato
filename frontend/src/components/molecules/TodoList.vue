<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SongTask } from '../../stores/song'
const props = defineProps<{ initial?: SongTask[]; readonly?: boolean }>()
const emit = defineEmits<{ update: [tasks: SongTask[]] }>()
const todos = ref<SongTask[]>([])
watch(() => props.initial ?? [], items => { todos.value = items.map(item => ({ ...item, title: item.title ?? item.text })) }, { immediate: true })
const draft = ref('')
const editing = ref(-1)
const title = ref('')
const doneCount = computed(() => todos.value.filter(t => t.done).length)
function update() { emit('update', todos.value.map(({ id, title, done }) => ({ ...(id ? { id } : {}), title, done }))) }
function toggle(index: number) { if (!props.readonly) { todos.value[index].done = !todos.value[index].done; update() } }
function add() {
  const text = draft.value.trim()
  if (!text || text.length > 200 || props.readonly) return
  todos.value.push({ title: text, done: false }); draft.value = ''; update()
}
function edit(index: number) { editing.value = index; title.value = todos.value[index].title ?? '' }
function saveTitle(index: number) {
  const value = title.value.trim()
  if (!value || value.length > 200) return
  todos.value[index].title = value; editing.value = -1; update()
}
function remove(index: number) { todos.value.splice(index, 1); update() }
</script>

<template>
  <div>
    <p class="text-sm text-muted">{{ doneCount }} de {{ todos.length }} listas</p>
    <ul class="mt-2 list-none p-0">
      <li v-for="(t, i) in todos" :key="t.id || i">
        <button v-if="!readonly" type="button" class="flex min-h-[44px] w-full items-center gap-3 border-0 bg-transparent py-1 text-left text-base text-ink" :aria-pressed="t.done" @click="toggle(i)">
          <span class="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-[3px] border-2 border-solid" :class="t.done ? 'border-brass bg-brass' : 'border-fret'" aria-hidden="true">{{ t.done ? '✓' : '' }}</span><span :class="t.done ? 'text-muted line-through' : ''">{{ t.title }}</span>
        </button>
        <p v-else class="py-1 text-base" :class="t.done ? 'text-muted line-through' : ''">{{ t.done ? '✓ ' : '' }}{{ t.title }}</p>
        <form v-if="editing === i && !readonly" class="flex gap-2" @submit.prevent="saveTitle(i)"><input v-model="title" aria-label="Título de la tarea" required maxlength="200" class="field-input-dark min-w-0" /><button class="btn-ghost btn-sm">Aceptar</button><button type="button" class="btn-ghost btn-sm" @click="editing = -1">Cancelar</button></form>
        <div v-else-if="!readonly" class="flex gap-2"><button type="button" class="btn-ghost btn-sm" @click="edit(i)">Editar</button><button type="button" class="btn-ghost btn-sm" @click="remove(i)">Borrar</button></div>
      </li>
    </ul>
    <form v-if="!readonly" class="mt-3 flex gap-2" @submit.prevent="add"><label for="todo-new" class="sr-only">Nueva tarea</label><input id="todo-new" v-model="draft" required maxlength="200" type="text" placeholder="Nueva tarea" class="field-input-dark min-h-[44px] min-w-0 flex-1" /><button type="submit" class="btn-ghost btn-sm bg-ground">Agregar</button></form>
  </div>
</template>
