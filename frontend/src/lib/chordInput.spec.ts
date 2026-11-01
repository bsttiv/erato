import { describe, expect, it } from 'vitest'
import { guitarInput, pianoInput, hasChordNotes, fretsForChord } from './chordInput'

describe('Decision 09 §2 approved chord input rules', () => {
  it('CHD-rule guitar omits muted strings and sends matching standard-tuning MIDI notes', () => {
    expect(guitarInput([0, 1, 0, 2, 3, -1])).toEqual({ instrument: 'guitar', notes: [64, 60, 55, 52, 48], frets: [0, 1, 0, 2, 3], strings: [1, 2, 3, 4, 5] })
    expect(fretsForChord({ frets: [0, 3], strings: [1, 5] })).toEqual([0, -1, -1, -1, 3, -1])
  })
  it('CHD-rule piano sends MIDI notes with null fret and string arrays', () => {
    expect(pianoInput([0, 4, 7])).toEqual({ instrument: 'piano', notes: [48, 52, 55], frets: null, strings: null })
  })
  it('CHD-017 rejects a single pitch class including octave duplicates', () => {
    expect(hasChordNotes([48, 60])).toBe(false)
    expect(hasChordNotes([])).toBe(false)
  })
  it('CHD-018 accepts a two-note perfect fifth', () => {
    expect(hasChordNotes([48, 55])).toBe(true)
  })
})
