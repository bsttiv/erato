<script setup>
import { ref, computed } from 'vue'
import BackBar from '../components/ui/BackBar.vue'
import { currentUser } from '../data/sample.js'

const COLORS = ['#e8c79a', '#d98b5f', '#c9b28a', '#e0a96d', '#b89a74']
const name = ref('Los Faroles')
const email = ref('')
const message = ref('')
const invites = ref(['ana.rojas@correo.cl', 'tomas.pinto@correo.cl', 'leo.munoz@correo.cl'])

const count = computed(() => invites.value.length + 1)
function add() {
  const e = email.value.trim().toLowerCase()
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) {
    message.value = 'Escribe un correo válido, por ejemplo nombre@correo.cl'
    return
  }
  if (invites.value.includes(e)) {
    message.value = 'Esa persona ya está invitada.'
    return
  }
  invites.value.push(e)
  email.value = ''
  message.value = ''
}
const remove = (e) => (invites.value = invites.value.filter((x) => x !== e))
const color = (i) => COLORS[i % COLORS.length]
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <BackBar></BackBar>
    <div class="mx-auto grid max-w-[1240px] gap-12 px-4 pb-16 pt-10 sm:px-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] lg:gap-14">
      <form @submit.prevent="add">
        <h1 class="text-[44px] leading-none sm:text-[56px]">Crea tu banda</h1>
        <p class="mt-3 text-[17px] leading-normal">Un espacio compartido: todos los integrantes ven y editan las composiciones de la banda.</p>
        <div class="mt-9">
          <label for="band-name" class="field-label">Nombre de la banda</label>
          <input id="band-name" v-model="name" type="text" class="field-input" />
        </div>
        <div class="mt-4">
          <label for="band-desc" class="field-label">Descripción (opcional)</label>
          <textarea id="band-desc" rows="3" class="field-input py-3 leading-normal">Bolero y jazz de cerro. Ensayamos los jueves en la sala B.</textarea>
        </div>

        <h2 class="mt-10 text-[32px]">Invita a los integrantes</h2>
        <p class="mt-2 text-base">Les llegará un correo con el enlace para unirse.</p>
        <div class="mt-4 flex flex-wrap items-end gap-2.5">
          <div class="min-w-0 flex-[1_1_240px]">
            <label for="band-invite" class="field-label">Correo</label>
            <input id="band-invite" v-model="email" type="email" placeholder="nombre@correo.cl" class="field-input" aria-describedby="band-invite-msg" />
          </div>
          <button type="submit" class="btn-ghost">Agregar</button>
        </div>
        <p id="band-invite-msg" class="mt-2 min-h-[20px] text-sm text-brass" aria-live="polite">{{ message }}</p>

        <ul class="mt-2 grid list-none gap-2 p-0">
          <li class="flex items-center gap-3.5 rounded bg-surface px-4 py-3">
            <span class="avatar h-10 w-10 text-[13px]" :style="{ background: currentUser.color }">{{ currentUser.initials }}</span>
            <span class="min-w-0 flex-1"><span class="block font-medium">{{ currentUser.name }} (tú)</span><span class="block truncate text-sm text-muted">{{ currentUser.email }}</span></span>
            <span class="pr-2 text-[15px] text-muted">Creador</span>
          </li>
          <li v-for="(e, i) in invites" :key="e" class="flex items-center gap-3.5 rounded bg-surface px-4 py-3">
            <span class="avatar h-10 w-10 text-[13px]" :style="{ background: color(i) }">{{ e.slice(0, 2).toUpperCase() }}</span>
            <span class="min-w-0 flex-1"><span class="block truncate font-medium">{{ e }}</span><span class="block text-sm text-muted">Invitación pendiente</span></span>
            <button type="button" class="btn-icon btn cursor-pointer bg-transparent text-xl text-muted hover:bg-raised hover:text-ink" :aria-label="'Quitar a ' + e" @click="remove(e)">×</button>
          </li>
        </ul>

        <div class="mt-10 flex flex-wrap gap-3">
          <router-link to="/composiciones" class="btn-primary">Crear banda y enviar invitaciones</router-link>
          <router-link to="/composiciones" class="btn-ghost">Cancelar</router-link>
        </div>
      </form>

      <aside class="self-start rounded-md bg-surface bg-lamp px-6 pb-7 pt-20 sm:px-7" aria-label="Vista previa">
        <p class="text-sm text-muted">Tu banda en la barra lateral</p>
        <p class="mt-4 font-display text-[44px] leading-none sm:text-[56px]">{{ name.trim() || 'Tu banda' }}</p>
        <p class="mt-3 text-base">{{ count === 1 ? 'Solo tú, por ahora' : count + ' integrantes, contándote a ti' }}</p>
        <div class="mt-5 flex flex-wrap">
          <span class="avatar h-12 w-12 text-sm ring-2 ring-surface" :style="{ background: currentUser.color }">{{ currentUser.initials }}</span>
          <span v-for="(e, i) in invites" :key="e" class="avatar -ml-2.5 h-12 w-12 text-sm ring-2 ring-surface" :style="{ background: color(i) }">{{ e.slice(0, 2).toUpperCase() }}</span>
        </div>
      </aside>
    </div>
  </div>
</template>
