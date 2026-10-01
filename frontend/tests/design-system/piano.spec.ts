import { describe, it, expect } from 'vitest'
import { WHITE, BLACK_AFTER } from '@/design-system/core/piano'

describe('piano core layout constants', () => {
  it('defines the 7 white key pitch classes in order', () => {
    // C, D, E, F, G, A, B
    expect(WHITE).toEqual([0, 2, 4, 5, 7, 9, 11])
  })

  it('maps black keys to the white key preceding them', () => {
    // 0 (C) -> 1 (C#)
    // 2 (D) -> 3 (Eb / D#)
    // 5 (F) -> 6 (F#)
    // 7 (G) -> 8 (Ab / G#)
    // 9 (A) -> 10 (Bb / A#)
    expect(BLACK_AFTER).toEqual({
      0: 1,
      2: 3,
      5: 6,
      7: 8,
      9: 10,
    })
  })

  it('ensures E (4) and B (11) have no following black key', () => {
    expect(BLACK_AFTER[4]).toBeUndefined()
    expect(BLACK_AFTER[11]).toBeUndefined()
  })
})
