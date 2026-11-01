// Contenido de ejemplo para ver el diseño con datos reales. Reemplazar por la API.

export const currentUser = { name: 'Bastián Valencia', initials: 'BV', email: 'bastian@losfaroles.cl', color: '#f0a43a' }

export const band = {
  name: 'Los Faroles',
  initials: 'LF',
  members: [
    { initials: 'BV', name: 'Bastián', color: '#f0a43a' },
    { initials: 'AR', name: 'Ana', color: '#e8c79a' },
    { initials: 'TO', name: 'Tomás', color: '#d98b5f' },
    { initials: 'LE', name: 'Leo', color: '#c9b28a' },
  ],
}

// Letra con acordes: { section } abre una sección, { chords, text } es una línea.
export const songLines = [
  { section: 'Verso 1' },
  { chords: 'Am7                D9', text: 'Bajo el farol la noche se hace lenta' },
  { chords: 'Gmaj7              Cmaj7', text: 'y la ciudad se apaga despacio' },
  { chords: 'F#m7b5          B7', text: 'Tú pides otra copa, yo la cuenta' },
  { chords: 'Em               A7', text: 'y el pianista toca sin espacio' },
  { section: 'Coro' },
  { chords: 'Dm7             G7', text: 'Quédate un rato más' },
  { chords: 'Cmaj7                Am7', text: 'que la banda no ha terminado' },
  { chords: 'Dm7          G7          Cmaj7', text: 'el último bolero es para dos' },
  { section: 'Verso 2' },
  { chords: 'Am7                D9', text: 'Las mesas vacías guardan el humo' },
  { chords: 'Gmaj7              Cmaj7', text: 'de todo lo que no dijimos' },
]

export const songChords = [
  { name: 'Am7', frets: [0, 1, 0, 2, 0, -1], usage: 'Verso 1 y verso 2' },
  { name: 'D9', frets: [5, 5, 5, 4, 5, -1], usage: 'Verso 1 y verso 2' },
  { name: 'Gmaj7', frets: [-1, 3, 4, 4, -1, 3], usage: 'Verso 1 y verso 2' },
  { name: 'Cmaj7', frets: [0, 0, 0, 2, 3, -1], usage: 'Intro, versos y coro' },
  { name: 'Dm7', frets: [1, 1, 2, 0, -1, -1], usage: 'Intro y coro' },
  { name: 'G7', frets: [1, 0, 0, 0, 2, 3], usage: 'Intro y coro' },
]

export const takes = [
  {
    title: 'Toma 3, ensayo',
    meta: '28 sep · subida por ti',
    where: 'Sala B, un micrófono',
    length: 214,
    seed: 3,
    comments: [
      { at: 18, who: 'Ana', text: 'La entrada del bajo va medio tiempo antes.' },
      { at: 71, who: 'Tomás', text: 'Acá probar el Gmaj7 en vez de G.' },
      { at: 150, who: 'Ana', text: 'Este puente es el bueno.' },
    ],
  },
  {
    title: 'Toma 2',
    meta: '21 sep · subida por Leo',
    where: 'Living de Leo',
    length: 198,
    seed: 7,
    comments: [{ at: 122, who: 'Leo', text: 'Se cae el tempo en el segundo coro.' }],
  },
  { title: 'Idea de voz', meta: '14 sep · subida por ti', where: 'Nota de voz del celular', length: 62, seed: 11, comments: [] },
]

export const history = [
  { who: 'Ana', what: 'cambió el acorde del coro a Gmaj7', when: 'hace 2 h' },
  { who: 'Tomás', what: 'editó la letra del verso 2', when: 'ayer' },
  { who: 'Tú', what: 'subiste la Toma 3', when: '28 sep' },
  { who: 'Leo', what: 'agregó la tablatura del intro', when: '21 sep' },
]

export const compositions = {
  personal: [
    { title: 'Bolero para nadie', sub: 'Idea suelta', key: 'Sol mayor · 70 bpm', parts: ['Letra', 'Acordes'], when: 'hoy', access: 'Privada' },
    { title: 'Humo azul', sub: 'Con Ana como invitada', key: 'Mi menor · 84 bpm', parts: ['Letra', 'Acordes', 'Demos'], when: 'hace 3 días', access: 'Privada' },
    { title: 'Carta a Valparaíso', sub: 'Borrador', key: 'La menor · 96 bpm', parts: ['Letra'], when: '12 oct', access: 'Pública' },
  ],
  band: [
    { title: 'Noche de otoño', sub: '3 demos · 2 tareas pendientes', key: 'Re menor · 92 bpm', parts: ['Letra', 'Acordes', 'Tablatura', 'Demos', 'Tareas'], when: 'hace 2 h', access: 'Pública' },
    { title: 'Último tren', sub: '1 demo', key: 'Do mayor · 120 bpm', parts: ['Letra', 'Acordes', 'Demos'], when: 'ayer', access: 'Privada' },
    { title: 'Farol de la esquina', sub: 'Lista para el show', key: 'Fa mayor · 104 bpm', parts: ['Letra', 'Acordes', 'Tablatura'], when: '2 oct', access: 'Pública' },
    { title: 'Swing del cerro', sub: 'Solo instrumental', key: 'Si bemol · 140 bpm', parts: ['Acordes', 'Tablatura', 'Demos'], when: '28 sep', access: 'Privada' },
    { title: 'Madrugada', sub: '5 tareas pendientes', key: 'Re mayor · 76 bpm', parts: ['Letra', 'Tareas'], when: '15 sep', access: 'Privada' },
    { title: 'Copa de más', sub: '2 demos', key: 'Sol menor · 88 bpm', parts: ['Letra', 'Acordes', 'Demos'], when: '3 sep', access: 'Pública' },
  ],
}

export const formatTime = (s) => String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(Math.floor(s % 60)).padStart(2, '0')
