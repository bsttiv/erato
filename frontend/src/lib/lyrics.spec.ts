import { describe, it, expect } from 'vitest'
import { lyricText, placeChord, replaceLyricText, chordLabel, chordShape } from './lyrics'
import compositionView from '../pages/CompositionView.vue?raw'

describe('LYR lyrics editor — tests_md/propuesta-letra-2026-10-31.md', () => {
  it('LYR-101 stores a #name line as a section', () => {
    expect(replaceLyricText(null, '#coro')!.lines).toEqual([{ section: 'coro', text: '', chords: [] }])
  })
  it('LYR-102 keeps each line chords when a section is added above', () => {
    const original = { lines: [
      { text: 'Uno', chords: [{ col: 1, chord_id: 'a' }] },
      { text: 'Dos', chords: [{ col: 2, chord_id: 'b' }] },
    ] }
    expect(replaceLyricText(original, '#coro\nUno\nDos')!.lines).toEqual([
      { section: 'coro', text: '', chords: [] },
      original.lines[0],
      original.lines[1],
    ])
  })
  it('LYR-103 keeps a lone # as lyric text', () => {
    expect(replaceLyricText(null, '#')!.lines).toEqual([{ text: '#', chords: [] }])
  })
  it('LYR-104 shows sections as #name and retyping changes nothing', () => {
    const saved = { lines: [{ section: 'Coro', text: '', chords: [] }, { text: 'Hola', chords: [{ col: 0, chord_id: 'a' }] }] }
    expect(lyricText(saved)).toBe('#Coro\nHola')
    expect(replaceLyricText(saved, lyricText(saved))).toEqual(saved)
  })
  // jsdom has no layout, so this pins the tracks that stop the chord strip from widening the page.
  it('LYR-111 keeps the song page and its aside on shrinkable tracks', () => {
    expect(compositionView).toContain('class="grid grid-cols-[minmax(0,1fr)] gap-10')
    expect(compositionView).toContain('lg:grid-cols-[minmax(0,1fr)_360px]')
    expect(compositionView).toContain('<aside class="grid min-w-0 grid-cols-[minmax(0,1fr)]')
  })
})

describe('LYR rules — decision 09 section 4 (approved area)', () => {
  it('LYR-rule retains the exact chord ID and permits placement beyond text', () => {
    expect(placeChord({ lines: [{ text: 'Hola', chords: [] }] }, 0, 9, 'shape-2').lines[0]).toEqual({ text: 'Hola', chords: [{ col: 9, chord_id: 'shape-2' }] })
  })
  it('LYR-rule rejects negative columns and replaces a placement at the same column', () => {
    const lyrics = { lines: [{ text: '', chords: [{ col: 0, chord_id: 'a' }] }] }
    expect(() => placeChord(lyrics, 0, -1, 'b')).toThrow()
    expect(placeChord(lyrics, 0, 0, 'b').lines[0].chords).toEqual([{ col: 0, chord_id: 'b' }])
  })
  it('LYR-rule preserves placements when editing text and removes empty lyrics', () => {
    const original = { lines: [{ text: 'Antes', chords: [{ col: 12, chord_id: 'a' }] }] }
    expect(replaceLyricText(original, 'Después').lines[0].chords).toEqual(original.lines[0].chords)
    expect(replaceLyricText(original, '')).toBeNull()
  })
  it('LYR-rule resolves updated chord names and distinguishes exact versions', () => {
    const chords = [{ id: 'a', name: 'C', instrument: 'guitar', strings: [1, 3], frets: [0, 2], notes: [64, 57] }, { id: 'b', name: 'C', instrument: 'piano', notes: [48, 52, 55] }]
    expect(chordLabel(chords[1], chords)).toBe('C · 2')
    expect(chordShape(chords[0])).toContain('1: 0')
    expect(chordShape(chords[1])).toContain('48, 52, 55')
  })
})
