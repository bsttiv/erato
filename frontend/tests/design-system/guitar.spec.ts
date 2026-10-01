import { describe, it, expect } from 'vitest'
import { TUNING, STR, fretsToMidi, autoBase } from '@/design-system/core/guitar'

describe('guitar core helpers', () => {
  it('defines standard guitar tuning and string names', () => {
    expect(TUNING).toEqual([40, 45, 50, 55, 59, 64])
    expect(STR).toEqual(['E', 'A', 'D', 'G', 'B', 'e'])
  })

  it('converts open strings to MIDI numbers', () => {
    expect(fretsToMidi([0, 0, 0, 0, 0, 0])).toEqual([40, 45, 50, 55, 59, 64])
  })

  it('omits muted (-1) strings in fretsToMidi', () => {
    // Open C chord: x-3-2-0-1-0
    const cFrets = [-1, 3, 2, 0, 1, 0]
    expect(fretsToMidi(cFrets)).toEqual([48, 52, 55, 60, 64])
  })

  it('returns empty array when all strings are muted', () => {
    expect(fretsToMidi([-1, -1, -1, -1, -1, -1])).toEqual([])
  })

  it('calculates autoBase: returns 1 for chords at or below fret 5', () => {
    expect(autoBase([-1, 3, 2, 0, 1, 0])).toBe(1)
    expect(autoBase([0, 0, 0, 0, 0, 0])).toBe(1)
    expect(autoBase([0, 2, 2, 4, 5, 0])).toBe(1) // max is 5
  })

  it('calculates autoBase: returns lowest pressed fret when max fret > 5', () => {
    // Em barre at 7th fret: x-7-9-9-8-7
    expect(autoBase([-1, 7, 9, 9, 8, 7])).toBe(7)
    // High voicing: x-x-12-14-13-12
    expect(autoBase([-1, -1, 12, 14, 13, 12])).toBe(12)
  })

  it('calculates autoBase: returns 1 when no frets > 0 are pressed', () => {
    expect(autoBase([-1, -1, -1, -1, -1, -1])).toBe(1)
  })
})
