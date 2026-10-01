import { describe, it, expect } from 'vitest'
import { parseLine, type LyricSegment } from '@/design-system/core/lyrics'

describe('parseLine (chord-over-syllable segmentation)', () => {
  it('parses chord at the beginning of the line: [Am7]Bajo el farol...', () => {
    const res = parseLine('[Am7]Bajo el farol...')
    expect(res).toEqual<LyricSegment[]>([
      { chord: 'Am7', text: 'Bajo el farol...' },
    ])
  })

  it('parses lines with text preceding the first chord', () => {
    const res = parseLine('Intro [C]verso [G]coro')
    expect(res).toEqual<LyricSegment[]>([
      { chord: null, text: 'Intro ' },
      { chord: 'C', text: 'verso ' },
      { chord: 'G', text: 'coro' },
    ])
  })

  it('handles consecutive chords without intervening text', () => {
    const res = parseLine('[C][G]final')
    expect(res).toEqual<LyricSegment[]>([
      { chord: 'C', text: '' },
      { chord: 'G', text: 'final' },
    ])
  })

  it('handles lines without any chords', () => {
    const res = parseLine('Sólo texto sin acordes')
    expect(res).toEqual<LyricSegment[]>([
      { chord: null, text: 'Sólo texto sin acordes' },
    ])
  })

  it('handles chord at the end of the line', () => {
    const res = parseLine('Termina en [Em]')
    expect(res).toEqual<LyricSegment[]>([
      { chord: null, text: 'Termina en ' },
      { chord: 'Em', text: '' },
    ])
  })

  it('returns empty array for an empty string', () => {
    expect(parseLine('')).toEqual([])
  })
})
