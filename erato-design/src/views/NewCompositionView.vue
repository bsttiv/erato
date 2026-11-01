<script setup>
import { ref, computed } from 'vue'
import BackBar from '../components/ui/BackBar.vue'

const title = ref('Noche de otoño')
const space = ref(1)
const access = ref(0)
const parts = ref([
  { name: 'Letra', on: true },
  { name: 'Acordes', on: true },
  { name: 'Tablatura', on: true },
  { name: 'Demos', on: false },
  { name: 'Tareas', on: true },
])
const spaces = [
  { name: 'Personal', desc: 'Solo tú, y quien invites.' },
  { name: 'Los Faroles', desc: 'La ven los 4 integrantes.' },
]
const accesses = [
  { name: 'Privada', desc: 'Solo las personas invitadas.' },
  { name: 'Pública', desc: 'Cualquiera con el enlace puede verla.' },
]
const chosen = computed(() => parts.value.filter((p) => p.on).map((p) => p.name))
const accessLine = computed(() =>
  access.value === 0 ? 'Privada: solo las personas invitadas pueden verla y editarla.' : 'Pública: cualquiera con el enlace la ve; solo los invitados la editan.',
)
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <BackBar></BackBar>
    <div class="mx-auto grid max-w-[1240px] gap-12 px-4 pb-16 pt-10 sm:px-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] lg:gap-14">
      <form @submit.prevent>
        <h1 class="text-[44px] leading-none sm:text-[56px]">Nueva composición</h1>
        <p class="mt-3 text-[17px]">Todo es opcional salvo el título. Podrás cambiarlo después.</p>

        <div class="mt-9">
          <label for="nc-title" class="field-label">Título</label>
          <input id="nc-title" v-model="title" type="text" class="field-input" />
        </div>
        <div class="mt-4 grid gap-3.5 sm:grid-cols-3">
          <div>
            <label for="nc-key" class="field-label">Tonalidad</label>
            <select id="nc-key" class="field-input"><option>Re menor</option><option>Do mayor</option><option>Sol mayor</option><option>La menor</option></select>
          </div>
          <div>
            <label for="nc-bpm" class="field-label">Tempo (bpm)</label>
            <input id="nc-bpm" type="number" value="92" min="20" max="300" class="field-input" />
          </div>
          <div>
            <label for="nc-meter" class="field-label">Compás</label>
            <select id="nc-meter" class="field-input"><option>4/4</option><option>3/4</option><option>6/8</option></select>
          </div>
        </div>

        <p class="field-label mt-8">Espacio de trabajo</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <button v-for="(s, i) in spaces" :key="s.name" type="button" class="option-card" :class="space === i ? 'option-card-on' : ''" :aria-pressed="space === i ? 'true' : 'false'" @click="space = i">
            <b class="block font-semibold">{{ s.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ s.desc }}</span>
          </button>
        </div>

        <p class="field-label mt-8">Secciones</p>
        <div class="flex flex-wrap gap-2">
          <button v-for="p in parts" :key="p.name" type="button" class="toggle" :class="p.on ? 'toggle-on' : ''" :aria-pressed="p.on ? 'true' : 'false'" @click="p.on = !p.on">
            <span class="h-2.5 w-2.5 rounded-full" :class="p.on ? 'bg-brass-ink' : 'bg-fret'" aria-hidden="true"></span>{{ p.name }}
          </button>
        </div>

        <p class="field-label mt-8">Acceso</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <button v-for="(a, i) in accesses" :key="a.name" type="button" class="option-card" :class="access === i ? 'option-card-on' : ''" :aria-pressed="access === i ? 'true' : 'false'" @click="access = i">
            <b class="block font-semibold">{{ a.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ a.desc }}</span>
          </button>
        </div>

        <div class="mt-10 flex flex-wrap gap-3">
          <router-link to="/c/noche-de-otono" class="btn-primary">Crear composición</router-link>
          <router-link to="/composiciones" class="btn-ghost">Cancelar</router-link>
        </div>
      </form>

      <aside class="self-start rounded-md bg-surface bg-lamp px-6 pb-6 pt-16 sm:px-7" aria-label="Vista previa">
        <p class="text-sm text-muted">Así se verá en tu lista</p>
        <div class="mt-3.5 rounded-md bg-ground p-6">
          <p class="font-display text-[36px] leading-[1.05]">{{ title.trim() || 'Sin título' }}</p>
          <p class="mt-2 text-[15px] text-muted">{{ spaces[space].name }} · Re menor · 92 bpm · 4/4</p>
          <div class="mt-4 flex flex-wrap gap-1.5"><span v-for="c in chosen" :key="c" class="chip text-[13px]">{{ c }}</span></div>
          <p class="mt-4 text-[15px]">{{ accessLine }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>
