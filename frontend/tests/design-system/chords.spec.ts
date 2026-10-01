import { describe, it, expect } from 'vitest'
import { detectChord, NOTE, QUAL, key } from '@/design-system/core/chords'

describe('detectChord (theory & recognition)', () => {
  const cases: Array<{
    description: string
    notes: number[]
    expectedName: string | null
    expectedRoot: number
    expectedQuality: string | null
    expectedBass: number
    expectedNotes: string[]
  }> = [
    {
      description: 'simple major triad (C)',
      notes: [60, 64, 67], // C4, E4, G4
      expectedName: 'C',
      expectedRoot: 0,
      expectedQuality: '',
      expectedBass: 0,
      expectedNotes: ['C', 'E', 'G'],
    },
    {
      description: 'slash chord (D/F#)',
      notes: [42, 50, 57, 62], // F#2, D3, A3, D4
      expectedName: 'D/F#',
      expectedRoot: 2,
      expectedQuality: '',
      expectedBass: 6,
      expectedNotes: ['F#', 'D', 'A'],
    },
    {
      description: 'extended chord: Cmaj7',
      notes: [60, 64, 67, 71], // C4, E4, G4, B4
      expectedName: 'Cmaj7',
      expectedRoot: 0,
      expectedQuality: 'maj7',
      expectedBass: 0,
      expectedNotes: ['C', 'E', 'G', 'B'],
    },
    {
      description: 'extended chord: F#m7b5',
      notes: [54, 57, 60, 64], // F#3, A3, C4, E4
      expectedName: 'F#m7b5',
      expectedRoot: 6,
      expectedQuality: 'm7b5',
      expectedBass: 6,
      expectedNotes: ['F#', 'A', 'C', 'E'],
    },
    {
      description: 'extended chord: D9',
      notes: [50, 54, 57, 60, 64], // D3, F#3, A3, C4, E4
      expectedName: 'D9',
      expectedRoot: 2,
      expectedQuality: '9',
      expectedBass: 2,
      expectedNotes: ['D', 'F#', 'A', 'C', 'E'],
    },
    {
      description: 'fifth-less voicing: C7 without 5th',
      notes: [60, 64, 70], // C4, E4, Bb4
      expectedName: 'C7',
      expectedRoot: 0,
      expectedQuality: '7',
      expectedBass: 0,
      expectedNotes: ['C', 'E', 'Bb'],
    },
    {
      description: 'single-note case: C',
      notes: [60],
      expectedName: 'C',
      expectedRoot: 0,
      expectedQuality: 'nota',
      expectedBass: 0,
      expectedNotes: ['C'],
    },
  ]

  for (const c of cases) {
    it(`identifies ${c.description}`, () => {
      const res = detectChord(c.notes)
      expect(res).not.toBeNull()
      expect(res?.name).toBe(c.expectedName)
      expect(res?.root).toBe(c.expectedRoot)
      expect(res?.quality).toBe(c.expectedQuality)
      expect(res?.bass).toBe(c.expectedBass)
      expect(res?.notes).toEqual(c.expectedNotes)
    })
  }

  it('returns null for empty notes array', () => {
    expect(detectChord([])).toBeNull()
  })

  it('preserves NOTE and QUAL constants matching bundle.js', () => {
    expect(NOTE.length).toBe(12)
    expect(NOTE[0]).toBe('C')
    expect(NOTE[11]).toBe('B')
    expect(QUAL.length).toBe(27)
    expect(key([7, 0, 4])).toBe('0,4,7')
  })
})
