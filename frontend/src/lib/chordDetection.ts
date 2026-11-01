// Chord naming for the public landing, which has no song to ask the API about.
// Port of name_chord in backend/app/detection.py, the reference implementation;
// a change to the rules must reach both files.
import { GUITAR_STRINGS } from './chords'

type Tone = [semitones: number, degree: number]
interface Entry {
  suffix: string
  tones: Tone[]
}
interface Reading extends Entry {
  root: number
  index: number
}

// Suffix and tones above the implicit root [0, 1].
const QUALITIES: [string, Tone[]][] = [
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
const ALTERABLE_QUALITIES = 19 // Dyads take no altered tensions.

const INTERVALS = ['1', 'b9', '9', 'b3', '3', '11', '#11', '5', 'b13', '13', 'b7', '7']
const DEGREES = [1, 9, 9, 3, 3, 11, 11, 5, 13, 13, 7, 7]
const ALTERATIONS: [number, number, string][] = [[1, 9, 'b9'], [3, 9, '#9'], [6, 11, '#11'], [8, 13, 'b13']]
const LETTERS = 'CDEFGAB'
const NATURALS = [0, 2, 4, 5, 7, 9, 11]
// The landing has no song, so names use the spelling of C, as the API does without a key.
const SCALE_PCS = new Set(NATURALS)

const mod = (value: number, size: number) => ((value % size) + size) % size
const pcsId = (pcs: Iterable<number>) => [...pcs].sort((a, b) => a - b).join(',')
const inScale = (pcs: Iterable<number>) => [...pcs].every(pc => SCALE_PCS.has(pc))
const hasTone = (tones: Tone[], [semitones, degree]: Tone) => tones.some(tone => tone[0] === semitones && tone[1] === degree)

function letterName(pc: number, letter: number): string {
  const delta = mod(pc - NATURALS[letter] + 6, 12) - 6
  return LETTERS[letter] + (delta > 0 ? '#'.repeat(delta) : 'b'.repeat(-delta))
}

function combinations<T>(items: T[], count: number, start = 0): T[][] {
  if (count === 0) return [[]]
  const result: T[][] = []
  for (let i = start; i <= items.length - count; i++) {
    for (const rest of combinations(items, count - 1, i + 1)) result.push([items[i], ...rest])
  }
  return result
}

function buildEntries(): Entry[] {
  const entries: Entry[] = QUALITIES.map(([suffix, tones]) => ({ suffix, tones: [[0, 1], ...tones] }))
  for (const [suffix, tones] of QUALITIES.slice(0, ALTERABLE_QUALITIES)) {
    const semitones = new Set(tones.map(([s]) => s))
    if (!semitones.has(7) || !(semitones.has(4) || semitones.has(3))) continue
    for (let count = 1; count < 5; count++) {
      for (const alterations of combinations(ALTERATIONS, count)) {
        if (alterations.some(([s]) => semitones.has(s))) continue
        const degrees = new Set(alterations.map(([, degree]) => degree))
        const kept = tones.filter(([, degree]) => !degrees.has(degree))
        const added = alterations.map(([s, degree]): Tone => [s, degree])
        const label = alterations.map(([, , text]) => text).join(',')
        entries.push({ suffix: `${suffix}(${label})`, tones: [[0, 1], ...kept, ...added] })
      }
    }
  }
  return entries
}

// The fifth may be omitted from a chord that keeps its third and one more tone.
function withoutFifth(entries: Entry[]): Entry[] {
  return entries
    .filter(({ tones }) => hasTone(tones, [7, 5]) && (hasTone(tones, [4, 3]) || hasTone(tones, [3, 3])) && tones.length > 3)
    .map(({ suffix, tones }) => ({ suffix, tones: tones.filter(tone => !(tone[0] === 7 && tone[1] === 5)) }))
}

function byPitches(entries: Entry[]): Map<string, Reading[]> {
  const catalog = new Map<string, Reading[]>()
  for (let root = 0; root < 12; root++) {
    entries.forEach(({ suffix, tones }, index) => {
      const id = pcsId(new Set(tones.map(([s]) => (root + s) % 12)))
      if (!catalog.has(id)) catalog.set(id, [])
      catalog.get(id)!.push({ root, suffix, tones, index })
    })
  }
  return catalog
}

const ENTRIES = buildEntries()
const CATALOG = byPitches(ENTRIES)
const NO_FIFTH_CATALOG = byPitches(withoutFifth(ENTRIES))

function compare(a: (number | boolean | string)[], b: (number | boolean | string)[]): number {
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) return -1
    if (a[i] > b[i]) return 1
  }
  return 0
}

function minBy<T>(items: T[], rank: (item: T) => (number | boolean | string)[]): T {
  return items.map((item): [(number | boolean | string)[], T] => [rank(item), item]).reduce((best, next) => (compare(next[0], best[0]) < 0 ? next : best))[1]
}

function scaleName(pc: number): string {
  return letterName(pc, NATURALS.indexOf(pc))
}

function reading(pcs: Set<number>, bass: number): Reading {
  const id = pcsId(pcs)
  const options = CATALOG.get(id) || NO_FIFTH_CATALOG.get(id)
  if (!options) {
    const semitones = [...pcs].map(pc => mod(pc - bass, 12)).sort((a, b) => a - b)
    const labels = semitones.filter(s => s).map(s => INTERVALS[s])
    return { root: bass, suffix: `(${labels.join(',')})`, tones: semitones.map(s => [s, DEGREES[s]]), index: -1 }
  }
  return minBy(options, ({ root, tones, index }) => {
    let diatonic = inScale(pcs) && SCALE_PCS.has(root)
    if (diatonic) {
      const letter = NATURALS.indexOf(root)
      diatonic = tones.every(([s, degree]) => NATURALS.indexOf((root + s) % 12) === (letter + degree - 1) % 7)
    }
    return [root !== bass, !diatonic, index, root]
  })
}

function spell(root: number, tones: Tone[]): string {
  if (inScale(tones.map(([s]) => (root + s) % 12))) return scaleName(root)
  const choices: [number, boolean, string][] = []
  for (let letter = 0; letter < 7; letter++) {
    const name = letterName(root, letter)
    if (name.length > 2) continue
    const cost = tones.reduce((sum, [s, degree]) => sum + letterName((root + s) % 12, (letter + degree - 1) % 7).length - 1, 0)
    choices.push([cost, name.includes('#'), name])
  }
  return minBy(choices, choice => choice)[2]
}

/** Names MIDI notes; the bass is the lowest note, not the first one listed. */
export function nameChord(notes: number[]): string {
  const pcs = new Set(notes.map(note => note % 12))
  if (pcs.size < 2) throw new Error('A chord requires at least two distinct pitch classes')
  const bass = Math.min(...notes) % 12
  const { root, suffix, tones } = reading(pcs, bass)
  const name = spell(root, tones) + suffix
  if (root === bass) return name
  return `${name}/${SCALE_PCS.has(bass) ? scaleName(bass) : spell(bass, [[0, 1]])}`
}

/** Name and spelled notes of a guitar shape; fewer than two notes is a prompt, not a chord. */
export function chordFromFrets(frets: number[]): { name: string; notes: string } {
  const notes = frets.flatMap((fret, index) => (fret < 0 ? [] : [GUITAR_STRINGS[index].midi + fret]))
  const pcs = new Set(notes.map(note => note % 12))
  if (pcs.size < 2) return { name: '—', notes: 'Marca al menos dos notas' }
  const { root, tones } = reading(pcs, Math.min(...notes) % 12)
  const letter = LETTERS.indexOf(spell(root, tones)[0])
  const spelled = tones.map(([s, degree]) => letterName((root + s) % 12, (letter + degree - 1) % 7))
  return { name: nameChord(notes), notes: spelled.join(' · ') }
}
