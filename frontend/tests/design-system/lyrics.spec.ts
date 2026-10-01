import { describe, it, expect } from 'vitest'
import {
  parseLine,
  decomposeLine,
  composeLine,
  setChordAt,
  type LyricSegment,
} from '@/design-system/core/lyrics'

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

describe('decomposeLine and composeLine algebra', () => {
  it('breaks a lyrics line into syllable tokens with their chord annotations and offset', () => {
    const decomposed = decomposeLine('[Am7]Bajo el farol [C]de la esquina')
    expect(decomposed.text).toBe('Bajo el farol de la esquina')
    expect(decomposed.marks).toEqual([
      { offset: 0, chord: 'Am7' },
      { offset: 14, chord: 'C' },
    ])

    // Syllable tokens have offset, text, and chord annotation
    expect(decomposed.length).toBeGreaterThan(0)
    expect(decomposed[0]).toEqual({
      offset: 0,
      text: 'Bajo ',
      chord: 'Am7',
    })
    const secondToken = decomposed.find((t) => t.text.includes('el'))
    expect(secondToken).toBeDefined()
    expect(secondToken?.chord).toBeNull()
  })

  it('reconstructs bracket markup string from tokens or decomposed line', () => {
    const original = '[Am7]Bajo el farol [C]de la esquina'
    const decomposed = decomposeLine(original)
    expect(composeLine(decomposed)).toBe(original)
    expect(composeLine(decomposed.text, decomposed.marks)).toBe(original)
  })

  it('maintains round-trip identity: parseLine(composeLine(decomposeLine(text))) equals parseLine(text)', () => {
    const fixtures = [
      '[Am7]Bajo el farol...',
      'Intro [C]verso [G]coro',
      '# Coro',
      'Texto sin ningun acorde',
      '[C][G]final',
      'Termina en [Em]',
      '',
    ]

    for (const f of fixtures) {
      const roundTripped = composeLine(decomposeLine(f))
      expect(roundTripped).toBe(f)
      expect(parseLine(roundTripped)).toEqual(parseLine(f))
    }
  })
})

describe('setChordAt (bracket markup mutation)', () => {
  const content = `# Coro\n[Am]Bajo el farol\n[C]de la esquina\n`

  it('inserts [Chord] before syllable text when placing chord on an unmarked syllable', () => {
    // line 1 is "[Am]Bajo el farol". Plain text is "Bajo el farol".
    // "el " starts at offset 5.
    const res = setChordAt(content, { line: 1, offset: 5 }, 'Em')
    expect(res).toBe(`# Coro\n[Am]Bajo [Em]el farol\n[C]de la esquina\n`)
  })

  it('replaces chord when placing a chord on an already marked syllable', () => {
    // line 1 offset 0 has [Am]. Replace with [Dm].
    const res = setChordAt(content, { line: 1, offset: 0 }, 'Dm')
    expect(res).toBe(`# Coro\n[Dm]Bajo el farol\n[C]de la esquina\n`)
  })

  it('deletes bracket marker without modifying lyric text when given null or empty string', () => {
    // line 1 offset 0 has [Am]. Remove it.
    const resNull = setChordAt(content, { line: 1, offset: 0 }, null)
    expect(resNull).toBe(`# Coro\nBajo el farol\n[C]de la esquina\n`)

    const resEmpty = setChordAt(content, { line: 1, offset: 0 }, '')
    expect(resEmpty).toBe(`# Coro\nBajo el farol\n[C]de la esquina\n`)
  })

  it('returns content untouched when line or offset is out of range', () => {
    expect(setChordAt(content, { line: -1, offset: 0 }, 'Am')).toBe(content)
    expect(setChordAt(content, { line: 99, offset: 0 }, 'Am')).toBe(content)
    expect(setChordAt(content, { line: 1, offset: 999 }, 'Am')).toBe(content)
    expect(setChordAt(content, { line: 1, offset: -5 }, 'Am')).toBe(content)
  })

  it('preserves every other line and trailing newline shape byte-for-byte', () => {
    const res = setChordAt(content, { line: 2, offset: 0 }, 'F')
    const lines = res.split('\n')
    expect(lines[0]).toBe('# Coro')
    expect(lines[1]).toBe('[Am]Bajo el farol')
    expect(lines[2]).toBe('[F]de la esquina')
    expect(lines[3]).toBe('') // trailing newline preserved
  })
})
