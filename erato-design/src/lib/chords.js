// Detección de acordes y tonalidad según el algoritmo del autor
// (archivos/autonomo_automatico.md). Es un port de backend/app/detection.py,
// que sigue siendo la implementación de referencia.

// Solo para rotular teclas y trastes; los nombres de acordes usan la tonalidad.
export const NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

// Cuerdas de la guitarra en el orden en que se dibujan: de la más aguda (arriba) a la más grave.
export const GUITAR_STRINGS = [
  { name: 'e', pc: 4, midi: 64 },
  { name: 'B', pc: 11, midi: 59 },
  { name: 'G', pc: 7, midi: 55 },
  { name: 'D', pc: 2, midi: 50 },
  { name: 'A', pc: 9, midi: 45 },
  { name: 'E', pc: 4, midi: 40 },
]

// Sufijo y pares [semitonos, grado diatónico]. La fundamental [0, 1] es implícita.
const QUALITIES = [
  ['', [[4, 3], [7, 5]]],
  ['m', [[3, 3], [7, 5]]],
  ['dim', [[3, 3], [6, 5]]],
  ['+', [[4, 3], [8, 5]]],
  ['7', [[4, 3], [7, 5], [10, 7]]],
  ['maj7', [[4, 3], [7, 5], [11, 7]]],
  ['m7', [[3, 3], [7, 5], [10, 7]]],
  ['6', [[4, 3], [7, 5], [9, 6]]],
  ['m7b5', [[3, 3], [6, 5], [10, 7]]],
  ['dim7', [[3, 3], [6, 5], [9, 7]]],
  ['sus2', [[2, 2], [7, 5]]],
  ['sus4', [[5, 4], [7, 5]]],
  ['add9', [[4, 3], [7, 5], [2, 9]]],
  ['9', [[4, 3], [7, 5], [10, 7], [2, 9]]],
  ['maj9', [[4, 3], [7, 5], [11, 7], [2, 9]]],
  ['m9', [[3, 3], [7, 5], [10, 7], [2, 9]]],
  ['11', [[4, 3], [7, 5], [10, 7], [2, 9], [5, 11]]],
  ['m11', [[3, 3], [7, 5], [10, 7], [2, 9], [5, 11]]],
  ['13', [[4, 3], [7, 5], [10, 7], [2, 9], [5, 11], [9, 13]]],
  ['5', [[7, 5]]],
  ['(no5)', [[4, 3]]],
  ['m(no5)', [[3, 3]]],
]
const ALTERABLE_QUALITIES = 19 // Las díadas no admiten tensiones alteradas.

// Etiquetas del nombre de respaldo, usando la grafía aprobada para 1 y 6.
const INTERVALS = ['1', 'b9', '9', 'b3', '3', '11', '#11', '5', 'b13', '13', 'b7', '7']
const DEGREES = [1, 9, 9, 3, 3, 11, 11, 5, 13, 13, 7, 7]
const ALTERATIONS = [[1, 9, 'b9'], [3, 9, '#9'], [6, 11, '#11'], [8, 13, 'b13']]
const MAJOR_KEYS = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'Db', 'Ab', 'Eb', 'Bb', 'F']
const MINOR_KEYS = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm', 'Dm']
const LETTERS = 'CDEFGAB'
const NATURALS = [0, 2, 4, 5, 7, 9, 11]
const MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
const SHARP_KEYS = ['G', 'D', 'A', 'E', 'B', 'Em', 'Bm']

const mod = (n, m) => ((n % m) + m) % m
const pcsId = (pcs) => [...pcs].sort((a, b) => a - b).join(',')
const isSubset = (pcs, scale) => [...pcs].every((pc) => scale.has(pc))

function compare(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) return -1
    if (a[i] > b[i]) return 1
  }
  return 0
}

const minBy = (items, rank) =>
  items.map((item) => [rank(item), item]).reduce((best, next) => (compare(next[0], best[0]) < 0 ? next : best))[1]

function pitch(name) {
  const accidentals = name.split('#').length - name.split('b').length
  return mod(NATURALS[LETTERS.indexOf(name[0])] + accidentals, 12)
}

function letterName(pc, letter) {
  const delta = mod(pc - NATURALS[letter] + 6, 12) - 6
  return LETTERS[letter] + (delta > 0 ? '#'.repeat(delta) : 'b'.repeat(-delta))
}

function scaleOf(key) {
  const minor = key.endsWith('m')
  const tonic = minor ? key.slice(0, -1) : key
  const start = LETTERS.indexOf(tonic[0])
  if (start < 0) throw new Error(`Tonalidad no válida: ${key}`)
  const root = pitch(tonic)
  const scale = new Map()
  ;(minor ? MINOR_SCALE : NATURALS).forEach((step, i) => {
    const pc = mod(root + step, 12)
    scale.set(pc, letterName(pc, (start + i) % 7))
  })
  return scale
}

function parseNotes(notes) {
  if (notes.some((n) => !Number.isInteger(n) || n < 0 || n > 127)) {
    throw new Error('Las notas deben ser enteros MIDI entre 0 y 127')
  }
  const pcs = new Set(notes.map((n) => n % 12))
  if (pcs.size < 2) throw new Error('Un acorde necesita al menos dos clases de altura distintas')
  return { pcs, bass: Math.min(...notes) % 12 }
}

function combinations(items, count, start = 0) {
  if (count === 0) return [[]]
  const result = []
  for (let i = start; i <= items.length - count; i++) {
    for (const rest of combinations(items, count - 1, i + 1)) result.push([items[i], ...rest])
  }
  return result
}

function buildEntries() {
  const entries = QUALITIES.map(([suffix, tones]) => [suffix, [[0, 1], ...tones], false])
  // Las tensiones alteradas reemplazan a su extensión natural, si existe.
  for (const [suffix, tones] of QUALITIES.slice(0, ALTERABLE_QUALITIES)) {
    const semitones = new Set(tones.map(([s]) => s))
    if (!semitones.has(7) || !(semitones.has(4) || semitones.has(3))) continue
    for (let count = 1; count < 5; count++) {
      for (const alterations of combinations(ALTERATIONS, count)) {
        if (alterations.some(([s]) => semitones.has(s))) continue
        const degrees = new Set(alterations.map(([, d]) => d))
        const kept = tones.filter(([, d]) => !degrees.has(d))
        const added = alterations.map(([s, d]) => [s, d])
        const label = alterations.map(([, , text]) => text).join(',')
        entries.push([`${suffix}(${label})`, [[0, 1], ...kept, ...added], true])
      }
    }
  }
  return entries
}

// Mismo nombre que el acorde completo; las tríadas siguen siendo díadas con (no5).
function withoutFifth(entries) {
  const has = (tones, s, d) => tones.some((tone) => tone[0] === s && tone[1] === d)
  return entries
    .filter(([, tones]) => has(tones, 7, 5) && (has(tones, 4, 3) || has(tones, 3, 3)) && tones.length > 3)
    .map(([suffix, tones, altered]) => [suffix, tones.filter((tone) => !(tone[0] === 7 && tone[1] === 5)), altered])
}

function byPitches(entries) {
  const catalog = new Map()
  for (let root = 0; root < 12; root++) {
    entries.forEach(([suffix, tones, altered], index) => {
      const id = pcsId(new Set(tones.map(([s]) => (root + s) % 12)))
      if (!catalog.has(id)) catalog.set(id, [])
      catalog.get(id).push({ root, suffix, tones, altered, index })
    })
  }
  return catalog
}

const ENTRIES = buildEntries()
const CATALOG = byPitches(ENTRIES)
const NO_FIFTH_CATALOG = byPitches(withoutFifth(ENTRIES))

function reading(pcs, bass, key) {
  const id = pcsId(pcs)
  const options = CATALOG.get(id) || NO_FIFTH_CATALOG.get(id)
  if (!options) {
    const semitones = [...pcs].map((pc) => mod(pc - bass, 12)).sort((a, b) => a - b)
    const tones = semitones.map((s) => [s, DEGREES[s]])
    const labels = semitones.filter((s) => s).map((s) => INTERVALS[s])
    return { root: bass, suffix: `(${labels.join(',')})`, tones, altered: true, index: -1 }
  }
  const scale = scaleOf(key)
  return minBy(options, ({ root, tones, index }) => {
    let diatonic = isSubset(pcs, scale) && scale.has(root)
    if (diatonic) {
      const letter = LETTERS.indexOf(scale.get(root)[0])
      diatonic = tones.every(([s, d]) => scale.get((root + s) % 12)[0] === LETTERS[(letter + d - 1) % 7])
    }
    return [root !== bass, !diatonic, index, root]
  })
}

function spell(root, tones, key) {
  const scale = scaleOf(key)
  if (isSubset(new Set(tones.map(([s]) => (root + s) % 12)), scale)) return scale.get(root)
  const preferSharps = key.includes('#') || SHARP_KEYS.includes(key)
  const choices = []
  for (let letter = 0; letter < 7; letter++) {
    const name = letterName(root, letter)
    if (name.length > 2) continue
    const cost = tones.reduce(
      (sum, [s, d]) => sum + letterName((root + s) % 12, (letter + d - 1) % 7).length - 1,
      0,
    )
    choices.push([cost, name.includes(preferSharps ? 'b' : '#'), name])
  }
  return minBy(choices, (choice) => choice)[2]
}

/**
 * Nombra un acorde. El bajo es la nota más grave, no la primera de la lista.
 * @param {number[]} notes notas MIDI
 * @param {string|null} key tonalidad seleccionada; sin ella se usa la grafía de C
 */
export function nameChord(notes, key = null) {
  const { pcs, bass } = parseNotes(notes)
  const selected = key || 'C'
  const { root, suffix, tones } = reading(pcs, bass, selected)
  const name = spell(root, tones, selected) + suffix
  if (root === bass) return name
  return `${name}/${scaleOf(selected).get(bass) || spell(bass, [[0, 1]], selected)}`
}

// El puntaje no depende de la voz: con tensiones alteradas solo cuenta la tríada principal.
function scoringNotes(pcs) {
  const { root, tones, altered, index } = reading(pcs, Math.min(...pcs), 'C')
  const principal = new Set(tones.filter(([, d]) => [1, 3, 5].includes(d)).map(([s]) => (root + s) % 12))
  if (!altered) return pcs
  if (index >= 0) return principal
  return tones.some(([s]) => [1, 6, 8].includes(s)) ? principal : pcs
}

const qualityPcs = (root, suffix) => {
  const [, tones] = QUALITIES.find(([quality]) => quality === suffix)
  return pcsId(new Set([0, ...tones.map(([s]) => s)].map((s) => (root + s) % 12)))
}

/** Todas las tonalidades empatadas en el puntaje máximo, en orden de sugerencia. */
export function candidateKeys(chords) {
  const distinct = new Map()
  for (const notes of chords) {
    const { pcs } = parseNotes(notes)
    distinct.set(pcsId(pcs), pcs)
  }
  if (distinct.size === 0) return []
  const scoring = [...distinct.values()].map(scoringNotes)
  const keys = [...MAJOR_KEYS, ...MINOR_KEYS]
  const scores = new Map(
    keys.map((key) => [key, scoring.filter((pcs) => isSubset(pcs, scaleOf(key))).length]),
  )
  const maximum = Math.max(...scores.values())
  if (maximum === 0) return []

  const rank = (key) => {
    const minor = key.endsWith('m')
    const root = pitch(minor ? key.slice(0, -1) : key)
    const harmonic = new Set()
    if (minor) {
      for (const [offset, suffix] of [[7, ''], [7, '7'], [11, 'dim'], [11, 'dim7'], [3, '+']]) {
        harmonic.add(qualityPcs(root + offset, suffix))
      }
    }
    const tonic = [root, (root + (minor ? 3 : 4)) % 12, (root + 7) % 12]
    const tonicPresent = [...distinct.values()].some(
      (pcs) => tonic.every((pc) => pcs.has(pc)) && reading(pcs, Math.min(...pcs), key).root === root,
    )
    const harmonicCount = [...harmonic].filter((id) => distinct.has(id)).length
    return [-harmonicCount, !tonicPresent, minor, (minor ? MINOR_KEYS : MAJOR_KEYS).indexOf(key)]
  }
  return keys
    .filter((key) => scores.get(key) === maximum)
    .map((key) => [rank(key), key])
    .sort((a, b) => compare(a[0], b[0]))
    .map(([, key]) => key)
}

/** Recalcula candidatas y nombres, y conserva o reinicia la tonalidad previa. */
export function analyze(chords, keyMode = 'auto', selectedKey = null) {
  const candidates = candidateKeys(chords)
  if (keyMode !== 'auto' && keyMode !== 'manual') throw new Error('El modo debe ser auto o manual')
  if (keyMode === 'manual' && selectedKey === null) throw new Error('El modo manual requiere una tonalidad')
  let key = selectedKey
  if (keyMode === 'auto' && !candidates.includes(selectedKey)) key = candidates[0] ?? null
  return {
    candidates,
    key,
    names: chords.map((notes) => nameChord(notes, key)),
    keyReset: keyMode === 'auto' && selectedKey !== null && key !== selectedKey,
  }
}

// Nombre y notas para la interfaz; menos de dos notas es un aviso, no un acorde.
function describeChord(notes, key) {
  if (new Set(notes.map((n) => n % 12)).size < 2) return { name: '—', notes: 'Marca al menos dos notas' }
  const { pcs, bass } = parseNotes(notes)
  const selected = key || 'C'
  const { root, tones } = reading(pcs, bass, selected)
  const letter = LETTERS.indexOf(spell(root, tones, selected)[0])
  const spelled = tones.map(([s, d]) => letterName((root + s) % 12, (letter + d - 1) % 7))
  return { name: nameChord(notes, selected), notes: spelled.join(' · ') }
}

/** Notas MIDI de una posición de guitarra. -1 = cuerda silenciada, 0 = al aire. */
export function notesFromFrets(frets) {
  const notes = []
  frets.forEach((f, i) => {
    if (f >= 0) notes.push(GUITAR_STRINGS[i].midi + f)
  })
  return notes
}

export function chordFromFrets(frets, key = null) {
  return describeChord(notesFromFrets(frets), key)
}

/** Tonalidad de una canción a partir de sus posiciones: la primera candidata. */
export function keyFromShapes(shapes) {
  return analyze(shapes.map(notesFromFrets)).key
}

/**
 * Teclas de piano (0 = C3 … 23 = B4) equivalentes a una posición de guitarra.
 * El bajo cae en la primera octava y el resto sobre él, para conservar el nombre.
 */
export function keysFromFrets(frets) {
  const notes = notesFromFrets(frets)
  if (notes.length === 0) return []
  const lowest = Math.min(...notes)
  const base = lowest % 12
  const keys = []
  for (const note of notes) {
    let k = base + note - lowest
    while (k > 23) k -= 12
    if (!keys.includes(k)) keys.push(k)
  }
  return keys
}

export function chordFromKeys(keys, key = null) {
  return describeChord(keys.map((k) => k + 48), key)
}
