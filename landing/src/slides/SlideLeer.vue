<script setup lang="ts">
import { ErLyricsViewer, ErChordEditor } from '@ds-vue'

const chordRead = [-1, 5, 4, 5, 5, 5]

const lyrics = `# Verso 1
[Am7]Bajo el farol la [D9]noche se hace lenta
[Gmaj7]y la ciudad se [Cmaj7]apaga despacio
[F#m7b5]Tú pides otra [B7]copa, yo la cuenta
[Em]y el pianista [A7]toca sin espacio

# Coro
[Dm7]Quédate un [G7]rato más
[Cmaj7]que la banda no ha [Am7]terminado
[Dm7]Quédate, [E7]que el humo va
a [Am]borrar lo que no hemos [E7]cantado

# Verso 2
[Am7]Las luces bajan, [D9]nadie se levanta
[Gmaj7]el contrabajo [Cmaj7]camina en la penumbra
[F#m7b5]Y si me miras [B7]mientras nadie canta
[Em]sabré que esta canción [A7]ya nos alumbra`
</script>

<template>
  <section class="er-slide" aria-label="Características: lectura">
    <div class="er-wrap">
      <div style="display: flex; flex-direction: column; gap: var(--space-6);">
        <div class="er-label">
          // características · lectura
        </div>
        <h2 class="er-h2">
          Toca con las dos <em style="color: var(--amber); font-weight: 500;">manos</em>.
        </h2>
        <ul class="er-feat">
          <li><b>01</b><span>Lee tus letras sin tocar la pantalla con desplazamiento continuo, a la velocidad que elijas</span></li>
          <li><b>02</b><span>Obtén una vista previa del acorde a utilizar</span></li>
          <li><b>03</b><span>Revisa las tablaturas en una vista amigable</span></li>
          <li><b>04</b><span>Maximiza la letra a pantalla completa para el ensayo o el escenario</span></li>
        </ul>
      </div>
      <div
        class="er-visual"
        data-scroll-exclusion
        style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-4); align-items: start;"
      >
        <ErLyricsViewer
          title="Noche de otoño"
          :lyrics="lyrics"
          :height="440"
          :default-speed="30"
          style="display: block; min-width: 0;"
        />
        <div style="display: flex; flex-direction: column; gap: var(--space-2);">
          <div class="er-label">
            // siguiente acorde
          </div>
          <ErChordEditor
            :default-frets="chordRead"
            :default-base-fret="3"
            :editable="false"
            :hide-switch="true"
            style="display: block;"
          />
        </div>
      </div>
    </div>
  </section>
</template>
