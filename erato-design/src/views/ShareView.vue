<script setup>
import { ref, computed } from 'vue'
import LyricSheet from '../components/music/LyricSheet.vue'
import { songLines, band } from '../data/sample.js'

const mode = ref(0)
const copied = ref(false)
const email = ref('')
const people = ref(['sofia.lagos@correo.cl'])
const modes = [
  { name: 'Pública', desc: 'Cualquiera con el enlace puede verla. Solo los invitados pueden editarla.' },
  { name: 'Privada', desc: 'Solo la banda y las personas invitadas pueden verla y editarla.' },
]
const linkLine = computed(() =>
  mode.value === 0 ? 'Quien abra el enlace verá la letra, los acordes y las demos, sin poder cambiar nada.' : 'Quien abra el enlace sin invitación verá un aviso de que la canción es privada.',
)

function choose(i) {
  mode.value = i
  copied.value = false
}
function copy() {
  try {
    navigator.clipboard && navigator.clipboard.writeText('https://erato.app/c/noche-de-otono')
  } catch (e) {
    /* sin permiso de portapapeles */
  }
  copied.value = true
}
function invite() {
  const v = email.value.trim().toLowerCase()
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v) || people.value.includes(v)) return
  people.value.push(v)
  email.value = ''
}
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-ground text-ink">
    <div class="px-4 py-8 opacity-30 sm:px-10" aria-hidden="true">
      <p class="font-display text-[56px] leading-none">Noche de otoño</p>
      <div class="mt-10 max-w-[720px]"><LyricSheet :lines="songLines.slice(0, 5)"></LyricSheet></div>
    </div>
    <div class="absolute inset-0 bg-[#080503]/75" aria-hidden="true"></div>

    <div class="absolute inset-0 flex items-start justify-center overflow-y-auto px-4 py-6 sm:items-center sm:py-10">
      <section role="dialog" aria-modal="true" aria-labelledby="share-title" class="w-full max-w-[600px] rounded-lg bg-surface p-5 shadow-[0_30px_80px_rgba(0,0,0,.55)] sm:p-8">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h1 id="share-title" class="text-[34px] leading-none sm:text-[40px]">Compartir canción</h1>
            <p class="mt-2 text-base text-muted">Noche de otoño · {{ band.name }}</p>
          </div>
          <router-link to="/c/noche-de-otono" aria-label="Cerrar" class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded bg-raised text-2xl text-ink no-underline hover:text-ink">×</router-link>
        </div>

        <div class="mt-7 grid gap-2.5" role="radiogroup" aria-label="Quién puede verla">
          <button v-for="(m, i) in modes" :key="m.name" type="button" role="radio" class="option-card flex items-start gap-3.5 bg-ground" :class="mode === i ? 'option-card-on' : ''" :aria-checked="mode === i ? 'true' : 'false'" @click="choose(i)">
            <span class="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-solid" :class="mode === i ? 'border-brass' : 'border-fret'" aria-hidden="true">
              <span v-if="mode === i" class="h-2.5 w-2.5 rounded-full bg-brass"></span>
            </span>
            <span><b class="block font-semibold">{{ m.name }}</b><span class="mt-0.5 block text-[15px] text-muted">{{ m.desc }}</span></span>
          </button>
        </div>

        <p class="field-label mt-6">Enlace</p>
        <div class="flex flex-wrap gap-2">
          <label for="share-link" class="sr-only">Enlace de la canción</label>
          <input id="share-link" type="text" readonly value="erato.app/c/noche-de-otono" class="field-input-dark min-w-0 flex-[1_1_240px]" />
          <button type="button" class="btn-primary min-w-[136px]" @click="copy">{{ copied ? 'Copiado' : 'Copiar enlace' }}</button>
        </div>
        <p class="mt-2.5 text-[15px] leading-normal" aria-live="polite">{{ linkLine }}</p>

        <h2 class="mt-7 text-[26px]">Invitar a editar</h2>
        <form class="mt-3 flex flex-wrap gap-2" @submit.prevent="invite">
          <label for="share-invite" class="sr-only">Correo de la persona</label>
          <input id="share-invite" v-model="email" type="email" placeholder="nombre@correo.cl" class="field-input-dark min-w-0 flex-[1_1_220px]" />
          <button type="submit" class="btn-ghost">Invitar</button>
        </form>
        <ul class="mt-3 grid list-none gap-1 p-0">
          <li class="flex items-center gap-3.5 py-2">
            <span class="avatar h-10 w-10 bg-raised text-[13px] text-brass">{{ band.initials }}</span>
            <span class="min-w-0 flex-1"><span class="block font-medium">{{ band.name }}</span><span class="block text-sm text-muted">{{ band.members.length }} integrantes de la banda</span></span>
            <span class="text-[15px] text-muted">Pueden editar</span>
          </li>
          <li v-for="p in people" :key="p" class="flex items-center gap-3.5 py-2">
            <span class="avatar h-10 w-10 bg-[#e0a96d] text-[13px]">{{ p.slice(0, 2).toUpperCase() }}</span>
            <span class="min-w-0 flex-1"><span class="block truncate font-medium">{{ p }}</span><span class="block text-sm text-muted">Invitada · fuera de la banda</span></span>
            <span class="text-[15px] text-muted">Puede editar</span>
          </li>
        </ul>
        <div class="mt-6 flex justify-end">
          <router-link to="/c/noche-de-otono" class="btn-primary">Listo</router-link>
        </div>
      </section>
    </div>
  </div>
</template>
