// Note helpers only. Chord names are supplied by the backend.

/** A chord as produced by the server or a local draft; only name-bearing chords come from the server. */
export interface Chord {
  id?: string
  name: string
  instrument?: string
  notes?: number[]
  frets?: number[] | null
  strings?: number[] | null
}

export const NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

export interface GuitarString {
  name: string
  pc: number
  midi: number
}

// Cuerdas de la guitarra en el orden en que se dibujan: de la más aguda (arriba) a la más grave.
export const GUITAR_STRINGS: GuitarString[] = [
  { name: 'e', pc: 4, midi: 64 },
  { name: 'B', pc: 11, midi: 59 },
  { name: 'G', pc: 7, midi: 55 },
  { name: 'D', pc: 2, midi: 50 },
  { name: 'A', pc: 9, midi: 45 },
  { name: 'E', pc: 4, midi: 40 },
]

/** Teclas de piano (0 = C3 … 23 = B4) equivalentes a una posición de guitarra. */
export function keysFromFrets(frets: number[]): number[] {
  const keys: number[] = []
  frets.forEach((f, i) => {
    if (f < 0) return
    let k = GUITAR_STRINGS[i].midi + f - 48
    while (k < 0) k += 12
    while (k > 23) k -= 12
    if (!keys.includes(k)) keys.push(k)
  })
  return keys
}
