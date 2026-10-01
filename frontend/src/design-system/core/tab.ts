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
