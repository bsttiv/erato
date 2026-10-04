import type { ChordsSection, TabEntry } from '@/api/compositions'

export function normalizeChords(chords: any): ChordsSection {
  if (chords && Array.isArray(chords.entries)) {
    return {
      instrument: chords.instrument || 'guitar',
      entries: [...chords.entries],
    }
  } else if (chords && Array.isArray(chords.frets)) {
    return {
      instrument: chords.instrument || 'guitar',
      entries: [{ bar: 1, notes: chords.frets, name: 'Acorde' }],
    }
  }
  return { instrument: 'guitar', entries: [] }
}

export function normalizeTablature(tablature: any): TabEntry[] {
  const tabs = tablature?.tabs || (Array.isArray(tablature) ? tablature : null)
  if (Array.isArray(tabs) && tabs.length > 0) {
    return tabs.map((t: any) => ({
      ...t,
      columns: Array.isArray(t.columns) ? [...t.columns] : [],
    }))
  }
  if (tablature && Array.isArray(tablature.columns)) {
    return [
      {
        id: 'tab-1',
        title: 'Tablatura',
        strings: 6,
        columns: [...tablature.columns],
      },
    ]
  }
  return []
}

export function normalizeLyrics(lyrics: any): string {
  if (typeof lyrics === 'string') return lyrics
  return lyrics?.content || lyrics?.text || ''
}
