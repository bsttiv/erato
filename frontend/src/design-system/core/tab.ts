/* ── TabEditor: helpers y exportación de tablatura ASCII ─────────── */
export const EMPTY = (): string[] => ["", "", "", "", "", ""]

export function blankTab(n: number): string[][] {
  const a: string[][] = []
  for (let i = 0; i < n; i++) a.push(EMPTY())
  return a
}

export type TabColumn = string[] | "|"

/** tabToText(columns, names) → plain ASCII tab. Columns: arrays of 6 strings (high e first) or "|" for a bar line. */
export function tabToText(cols: TabColumn[], names?: string[]): string {
  const strNames = names || ["e", "B", "G", "D", "A", "E"]
  return strNames.map((n, s) => {
    return n + "|" + cols.map((c) => {
      if (c === "|") return "|"
      const w = Math.max.apply(null, c.map((v) => v.length).concat([1]))
      let v = c[s] || ""
      while (v.length < w) v += "-"
      return v + "-"
    }).join("") + "|"
  }).join("\n")
}

export const TECH = "hpbrs/\\~xv"

export interface TabEntry {
  id: string
  title: string
  strings: number
  columns: TabColumn[]
}

export function newTabId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'tab_' + Math.random().toString(36).slice(2, 11)
}

export function newTabEntry(titleOrIndex?: string | number, strings: number = 6): TabEntry {
  let title = 'Tablatura'
  if (typeof titleOrIndex === 'number') {
    title = `Tablatura ${titleOrIndex + 1}`
  } else if (typeof titleOrIndex === 'string') {
    title = titleOrIndex
  }
  return {
    id: newTabId(),
    title,
    strings,
    columns: blankTab(16),
  }
}
