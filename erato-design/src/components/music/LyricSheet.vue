<script setup>
// Letra con acordes sobre cada línea. Las líneas de acordes no se cortan: en pantallas
// angostas el bloque se desplaza horizontalmente en vez de desalinear los acordes.
defineProps({
  lines: { type: Array, required: true },
  showChords: { type: Boolean, default: true },
  textClass: { type: String, default: 'text-xl sm:text-2xl leading-snug' },
  chordClass: { type: String, default: 'text-[15px] sm:text-base' },
})
</script>

<template>
  <div class="overflow-x-auto">
    <template v-for="(line, i) in lines" :key="i">
      <p v-if="line.section" class="lyric-section">{{ line.section }}</p>
      <div v-else>
        <p v-if="showChords" class="lyric-chord" :class="chordClass">{{ line.chords }}</p>
        <p class="lyric-text" :class="textClass">{{ line.text }}</p>
      </div>
    </template>
  </div>
</template>
