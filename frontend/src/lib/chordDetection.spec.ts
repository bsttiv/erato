import { describe, expect, it } from 'vitest'
import { chordFromFrets, nameChord } from './chordDetection'

describe('landing chord detector', () => {
  it('LAND-010 names Cmaj7 and spells its notes', () => {
    expect(chordFromFrets([0, 0, 0, 2, 3, -1])).toEqual({ name: 'Cmaj7', notes: 'C · E · G · B' })
  })
  it('LAND-011 names E7 and spells its notes', () => {
    expect(chordFromFrets([0, 3, 1, 0, 2, 0])).toEqual({ name: 'E7', notes: 'E · G# · B · D' })
  })
  it('LAND-012 asks for two notes instead of naming one or none', () => {
    const prompt = { name: '—', notes: 'Marca al menos dos notas' }
    expect(chordFromFrets([-1, -1, -1, -1, -1, 0])).toEqual(prompt)
    expect(chordFromFrets([-1, -1, -1, -1, -1, -1])).toEqual(prompt)
  })
  it('LAND-013 names a chord without a fifth like the backend', () => {
    expect(nameChord([40, 55, 56, 62])).toBe('E7(#9)')
  })
})
