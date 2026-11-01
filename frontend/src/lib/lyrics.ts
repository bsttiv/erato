import type { Chord } from './chords'

export interface ChordPlacement {
  col: number
  chord_id: string
}
export interface LyricsLine {
  /** Section label line: no text or chords of its own. */
  section?: string
  text: string
  chords: ChordPlacement[]
}
/** A rendered sheet line: section marker, plain-text line, mock chord-string line, or chord-anchored line. */
export type SheetLine = { section?: string; text?: string; chords?: string | ChordPlacement[] }
export interface Lyrics {
  lines: LyricsLine[]
}

export function placeChord(lyrics: Lyrics | null | undefined, lineIndex: number, col: number, chordId?: string): Lyrics {
  if (!Number.isInteger(col) || col < 0) throw new Error('Invalid column')
  const lines = (lyrics?.lines || []).map(line => ({ ...line, chords: [...line.chords] }))
  if (!lines[lineIndex] || lines[lineIndex].section) throw new Error('Invalid line')
  lines[lineIndex].chords = lines[lineIndex].chords.filter(chord => chord.col !== col)
  if (chordId) lines[lineIndex].chords.push({ col, chord_id: chordId })
  lines[lineIndex].chords.sort((a, b) => a.col - b.col)
  return { lines }
}

const SECTION_MARK = /^#\s*(\S.*)$/
const SECTION_LENGTH = 40

function parseLine(text: string): LyricsLine {
  const section = text.match(SECTION_MARK)?.[1].trim().slice(0, SECTION_LENGTH)
  return section ? { section, text: '', chords: [] } : { text, chords: [] }
}

/** Editor text: sections are written as `#name`, one line each. */
export function lyricText(lyrics: Lyrics | null | undefined): string {
  return (lyrics?.lines || []).map(line => (line.section ? `#${line.section}` : line.text)).join('\n')
}

export function replaceLyricText(lyrics: Lyrics | null | undefined, text: string): Lyrics | null {
  if (!text) return null
  const previous = lyrics?.lines || []
  const used = new Set<number>()
  const parsed = text.split('\n').map(parseLine)
  // Unchanged lines keep their chords when another line is added above them.
  const moved = parsed.map(line => {
    const source = line.section ? -1 : previous.findIndex((old, index) => !used.has(index) && !old.section && old.text === line.text)
    if (source >= 0) used.add(source)
    return source
  })
  return {
    lines: parsed.map((line, index) => {
      if (line.section) return line
      let source = moved[index]
      if (source < 0 && previous[index] && !previous[index].section && !used.has(index)) {
        used.add(index)
        source = index
      }
      return source < 0 ? line : { text: line.text, chords: [...previous[source].chords] }
    }),
  }
}

export function dropColumn(pointerX: number, rowLeft: number, charWidth: number): number {
  return Math.max(0, Math.round((pointerX - rowLeft) / charWidth))
}

export function chordLabel(chord?: Chord | null, chords: Chord[] = []): string {
  if (!chord) return '—'
  const versions = chords.filter(item => item.name === chord.name)
  return versions.length > 1 ? `${chord.name} · ${versions.findIndex(item => item.id === chord.id) + 1}` : chord.name
}

export function chordShape(chord?: Chord | null): string {
  if (!chord) return ''
  if (chord.instrument === 'guitar') {
    const strings = Array.from({ length: 6 }, (_, index) => {
      const noteIndex = chord.strings?.indexOf(index + 1) ?? -1
      return `${index + 1}: ${noteIndex < 0 ? '×' : chord.frets![noteIndex]}`
    })
    return `Guitarra · cuerda: traste · ${strings.join(' · ')} · MIDI: ${chord.notes!.join(', ')}`
  }
  return `Piano · MIDI: ${chord.notes!.join(', ')}`
}
