import { GUITAR_STRINGS } from './chords'
import type { Chord } from './chords'

/** A chord draft ready to be saved; notes are always present (chords need at least two of them). */
export type ChordDraft = Omit<Chord, 'name' | 'notes'> & { name?: string; notes: number[] }

export function guitarInput(frets: number[]): ChordDraft {
  const notes: number[] = []
  const pressed: number[] = []
  const strings: number[] = []
  frets.forEach((fret, index) => {
    if (fret < 0) return
    notes.push(GUITAR_STRINGS[index].midi + fret)
    pressed.push(fret)
    strings.push(index + 1)
  })
  return { instrument: 'guitar', notes, frets: pressed, strings }
}

export const pianoInput = (keys: number[], baseMidi = 48): ChordDraft => ({
  instrument: 'piano', notes: keys.map((key) => baseMidi + key), frets: null, strings: null,
})
export const hasChordNotes = (notes: number[]): boolean => new Set(notes.map((note) => note % 12)).size >= 2
export function fretsForChord(chord: Chord): number[] {
  const frets: number[] = [-1, -1, -1, -1, -1, -1]
  chord.strings?.forEach((string, index) => { frets[string - 1] = chord.frets![index] })
  return frets
}
export function chordInput(chord: Chord): ChordDraft {
  const input: ChordDraft = {
    instrument: chord.instrument,
    notes: [...(chord.notes ?? [])],
    frets: chord.frets ? [...chord.frets] : null,
    strings: chord.strings ? [...chord.strings] : null,
  }
  if (chord.id) input.id = chord.id
  return input
}
