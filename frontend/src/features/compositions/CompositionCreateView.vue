<template>
  <div class="er-createshell">
    <header class="er-createbar">
      <router-link to="/" class="er-topbar-brand">
        Erato
      </router-link>
      <router-link to="/" class="er-auth-link">
        Cancelar
      </router-link>
    </header>

    <main class="er-form-card">
      <div class="er-label">
        // CREAR
      </div>
      <h1 class="er-dash-headline">
        Nueva canción
      </h1>

      <form class="er-auth-form" @submit.prevent="handleSubmit">
        <div v-if="error" class="er-auth-error">
          {{ error }}
        </div>

        <div class="er-field">
          <label for="comp-title" class="er-label">Título de la canción</label>
          <input
            id="comp-title"
            v-model="title"
            type="text"
            class="er-input"
            placeholder="p. ej. Noche de otoño"
            required
          >
        </div>

        <div class="er-field-grid">
          <div class="er-field">
            <label for="comp-key" class="er-label">Tonalidad</label>
            <input
              id="comp-key"
              v-model="key"
              type="text"
              class="er-input"
              placeholder="p. ej. Am"
            >
          </div>
          <div class="er-field">
            <label for="comp-bpm" class="er-label">Tempo / BPM</label>
            <input
              id="comp-bpm"
              v-model.number="bpm"
              type="number"
              class="er-input"
              placeholder="120"
            >
          </div>
          <div class="er-field">
            <label for="comp-time-signature" class="er-label">Compás</label>
            <input
              id="comp-time-signature"
              v-model="timeSignature"
              type="text"
              class="er-input"
              placeholder="4/4"
            >
          </div>
        </div>

        <div class="er-field">
          <div class="er-label">
            Quién puede verla
          </div>
          <div class="er-share-cards">
            <label class="er-share-card">
              <input
                v-model="visibility"
                type="radio"
                value="public"
              >
              <div>
                <strong>Con enlace</strong>
                <p class="er-hint">
                  Cualquiera con el enlace puede ver acordes, letra y escuchar demos.
                </p>
              </div>
            </label>

            <label class="er-share-card">
              <input
                v-model="visibility"
                type="radio"
                value="private"
              >
              <div>
                <strong>Privada</strong>
                <p class="er-hint">
                  Solo los integrantes invitados pueden verla y editarla.
                </p>
              </div>
            </label>
          </div>
        </div>

        <div class="er-field">
          <div class="er-label">
            Secciones iniciales
          </div>
          <div class="er-usecards">
            <button
              type="button"
              class="er-usecard"
              :aria-pressed="sectionsEnabled.chords ? 'true' : 'false'"
              @click="sectionsEnabled.chords = !sectionsEnabled.chords"
            >
              acordes
            </button>
            <button
              type="button"
              class="er-usecard"
              :aria-pressed="sectionsEnabled.tablature ? 'true' : 'false'"
              @click="sectionsEnabled.tablature = !sectionsEnabled.tablature"
            >
              tablatura
            </button>
            <button
              type="button"
              class="er-usecard"
              :aria-pressed="sectionsEnabled.lyrics ? 'true' : 'false'"
              @click="sectionsEnabled.lyrics = !sectionsEnabled.lyrics"
            >
              letra
            </button>
            <button
              type="button"
              class="er-usecard"
              :aria-pressed="sectionsEnabled.demos ? 'true' : 'false'"
              @click="sectionsEnabled.demos = !sectionsEnabled.demos"
            >
              demos
            </button>
            <button
              type="button"
              class="er-usecard"
              :aria-pressed="sectionsEnabled.todos ? 'true' : 'false'"
              @click="sectionsEnabled.todos = !sectionsEnabled.todos"
            >
              tareas
            </button>
          </div>
        </div>

        <div class="er-field-row">
          <ErButton
            type="submit"
            variant="primary"
            :disabled="loading"
          >
            {{ loading ? 'Creando canción…' : 'Crear canción' }}
          </ErButton>
          <router-link to="/" class="er-btn er-btn--ghost">
            Cancelar
          </router-link>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ErButton } from '@/design-system'
import { createComposition, type Visibility, type SectionsEnabled } from '@/api/compositions'

const router = useRouter()

const title = ref('')
const key = ref('')
const bpm = ref<number | null>(null)
const timeSignature = ref('')
const visibility = ref<Visibility>('private')
const error = ref<string | null>(null)
const loading = ref(false)

const sectionsEnabled = reactive<SectionsEnabled>({
  chords: true,
  tablature: false,
  lyrics: true,
  demos: true,
  todos: true,
})

async function handleSubmit() {
  if (!title.value.trim()) return

  error.value = null
  loading.value = true

  try {
    const comp = await createComposition({
      title: title.value.trim(),
      visibility: visibility.value,
      key: key.value.trim() || undefined,
      bpm: bpm.value || undefined,
      time_signature: timeSignature.value.trim() || undefined,
      sections_enabled: { ...sectionsEnabled },
    })

    router.push(`/compositions/${comp.id}`)
  } catch (err: any) {
    error.value = err.message || 'Error al crear composición'
  } finally {
    loading.value = false
  }
}
</script>
