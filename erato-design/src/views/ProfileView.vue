<script setup>
import { ref, computed } from 'vue'
import AppShell from '../components/app/AppShell.vue'
import { band } from '../data/sample.js'

const name = ref('Bastián Valencia')
const color = ref('#f0a43a')
const saved = ref(false)
const view = ref('Guitarra')
const notation = ref('C D E')
const swatches = [
  { c: '#f0a43a', label: 'Ámbar' },
  { c: '#e8c79a', label: 'Arena' },
  { c: '#d98b5f', label: 'Cobre' },
  { c: '#c9b28a', label: 'Latón' },
  { c: '#e07a6a', label: 'Coral' },
]
const instruments = ref([
  { name: 'Guitarra', on: true },
  { name: 'Bajo', on: false },
  { name: 'Voz', on: true },
  { name: 'Piano', on: false },
  { name: 'Batería', on: false },
  { name: 'Vientos', on: false },
])
const initials = computed(() => (name.value.trim().split(/\s+/).map((w) => w[0] || '').join('').slice(0, 2) || '?').toUpperCase())
const notationLine = computed(() => (notation.value === 'C D E' ? 'Los acordes se mostrarán como Dm7, G7, Cmaj7.' : 'Los acordes se mostrarán como Rem7, Sol7, Domaj7.'))
const touch = () => (saved.value = false)
</script>

<template>
  <AppShell space="" active="profile">
    <div class="max-w-[860px]">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-[44px] leading-none sm:text-[56px]">Editar perfil</h1>
          <p class="mt-3 text-[17px]">Así te ven tus bandas y las personas con quienes compartes.</p>
        </div>
        <button type="button" class="btn-primary min-w-[160px]" @click="saved = true">{{ saved ? 'Guardado' : 'Guardar cambios' }}</button>
      </div>

      <section class="card mt-8" aria-labelledby="p-id">
        <h2 id="p-id" class="text-[28px]">Identidad</h2>
        <div class="mt-5 flex flex-wrap items-center gap-7">
          <span class="avatar h-28 w-28 text-4xl" :style="{ background: color }">{{ initials }}</span>
          <div>
            <p class="field-label">Color de tu inicial</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="s in swatches"
                :key="s.c"
                type="button"
                class="h-11 w-11 cursor-pointer rounded-full border-[3px] border-solid p-0"
                :class="color === s.c ? 'border-ink' : 'border-transparent'"
                :style="{ background: s.c }"
                :aria-label="'Color ' + s.label"
                :aria-pressed="color === s.c ? 'true' : 'false'"
                @click="color = s.c; touch()"
              ></button>
            </div>
          </div>
        </div>
        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <div><label for="p-name" class="field-label">Nombre</label><input id="p-name" v-model="name" type="text" class="field-input-dark" @input="touch" /></div>
          <div><label for="p-email" class="field-label">Correo</label><input id="p-email" type="email" value="bastian@losfaroles.cl" class="field-input-dark" /></div>
        </div>
        <p class="field-label mt-6">Lo que tocas</p>
        <div class="flex flex-wrap gap-2">
          <button v-for="i in instruments" :key="i.name" type="button" class="toggle" :class="i.on ? 'toggle-on' : 'bg-ground'" :aria-pressed="i.on ? 'true' : 'false'" @click="i.on = !i.on; touch()">{{ i.name }}</button>
        </div>
      </section>

      <section class="card mt-3.5" aria-labelledby="p-pref">
        <h2 id="p-pref" class="text-[28px]">Preferencias de lectura</h2>
        <div class="mt-5 flex flex-wrap gap-8">
          <div>
            <p class="field-label">Vista de acordes</p>
            <div class="segmented bg-ground" role="group" aria-label="Vista de acordes">
              <button v-for="v in ['Guitarra', 'Piano']" :key="v" type="button" class="segmented-item" :class="view === v ? 'segmented-item-on' : ''" :aria-pressed="view === v ? 'true' : 'false'" @click="view = v; touch()">{{ v }}</button>
            </div>
          </div>
          <div>
            <p class="field-label">Nombres de las notas</p>
            <div class="segmented bg-ground" role="group" aria-label="Notación">
              <button v-for="n in ['C D E', 'Do Re Mi']" :key="n" type="button" class="segmented-item" :class="notation === n ? 'segmented-item-on' : ''" :aria-pressed="notation === n ? 'true' : 'false'" @click="notation = n; touch()">{{ n }}</button>
            </div>
          </div>
        </div>
        <p class="mt-4 text-[15px] text-muted">{{ notationLine }}</p>
      </section>

      <section class="card mt-3.5" aria-labelledby="p-pw">
        <h2 id="p-pw" class="text-[28px]">Contraseña</h2>
        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <div><label for="p-pw1" class="field-label">Contraseña actual</label><input id="p-pw1" type="password" autocomplete="current-password" class="field-input-dark" /></div>
          <div>
            <label for="p-pw2" class="field-label">Nueva contraseña</label>
            <input id="p-pw2" type="password" autocomplete="new-password" class="field-input-dark" aria-describedby="p-pw2-help" />
            <p id="p-pw2-help" class="mt-2 text-sm text-muted">8 caracteres o más, con un número y una mayúscula.</p>
          </div>
        </div>
      </section>

      <section class="card mt-3.5" aria-labelledby="p-bands">
        <h2 id="p-bands" class="text-[28px]">Tus bandas</h2>
        <div class="mt-4 flex flex-wrap items-center gap-3.5">
          <span class="avatar h-11 w-11 bg-raised text-sm text-brass">{{ band.initials }}</span>
          <span class="min-w-[200px] flex-1"><span class="block font-medium">{{ band.name }}</span><span class="block text-sm text-muted">Creador · {{ band.members.length }} integrantes · 12 composiciones</span></span>
          <router-link to="/bandas/nueva" class="btn-ghost btn-sm bg-ground">Administrar</router-link>
        </div>
      </section>

      <section class="mt-3.5 rounded-md border border-solid border-[#6e2a1f] bg-surface p-5 sm:p-6" aria-labelledby="p-del">
        <h2 id="p-del" class="text-[28px]">Eliminar cuenta</h2>
        <p class="mt-2.5 max-w-[60ch] text-base leading-normal">Se borran tus composiciones personales. Las de tus bandas siguen disponibles para los demás integrantes.</p>
        <button type="button" class="btn mt-4 border border-solid border-[#a5452f] bg-transparent text-[#f1a38c] hover:bg-[#2a1310]">Eliminar mi cuenta</button>
      </section>
    </div>
  </AppShell>
</template>
