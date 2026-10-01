/* ── Teoría: nombres de notas y detección de acordes ─────────────── */
export const NOTE = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

export const QUAL: Array<[string, number[]]> = [
  ["", [0, 4, 7]], ["m", [0, 3, 7]], ["7", [0, 4, 7, 10]], ["maj7", [0, 4, 7, 11]], ["m7", [0, 3, 7, 10]],
  ["sus4", [0, 5, 7]], ["sus2", [0, 2, 7]], ["dim", [0, 3, 6]], ["aug", [0, 4, 8]], ["5", [0, 7]],
  ["6", [0, 4, 7, 9]], ["m6", [0, 3, 7, 9]], ["m7b5", [0, 3, 6, 10]], ["dim7", [0, 3, 6, 9]], ["mMaj7", [0, 3, 7, 11]],
  ["7sus4", [0, 5, 7, 10]], ["add9", [0, 2, 4, 7]], ["madd9", [0, 2, 3, 7]], ["9", [0, 2, 4, 7, 10]],
  ["maj9", [0, 2, 4, 7, 11]], ["m9", [0, 2, 3, 7, 10]], ["6/9", [0, 2, 4, 7, 9]], ["7b9", [0, 1, 4, 7, 10]],
  ["7#9", [0, 3, 4, 7, 10]], ["13", [0, 2, 4, 7, 9, 10]], ["maj7#11", [0, 4, 6, 7, 11]], ["aug7", [0, 4, 8, 10]]
]

export function key(arr: number[]): string {
  return arr.slice().sort((a, b) => a - b).join(",")
}

export interface ChordInfo {
  name: string | null
  root: number
  quality: string | null
  bass: number
  notes: string[]
}

/** detectChord(notes) — notes: MIDI numbers (the lowest is the bass) or pitch classes 0–11.
 *  Returns {name, root, quality, bass, notes} or null. Handles slash chords and 7th/9th chords without a 5th. */
export function detectChord(notes: number[]): ChordInfo | null {
  if (!notes || !notes.length) return null
  const bass = ((Math.min.apply(null, notes) % 12) + 12) % 12
  const pcs: number[] = []
  notes.forEach((n) => {
    const p = ((n % 12) + 12) % 12
    if (pcs.indexOf(p) < 0) pcs.push(p)
  })
  if (pcs.length === 1) return { name: NOTE[pcs[0]], root: pcs[0], quality: "nota", bass: bass, notes: [NOTE[pcs[0]]] }
  let best: { score: number; root: number; q: string } | null = null
  for (const r of pcs) {
    const iv = key(pcs.map((p) => (p - r + 12) % 12))
    for (let qi = 0; qi < QUAL.length; qi++) {
      const q = QUAL[qi]
      const full = key(q[1])
      const no5 = q[1].length >= 4 ? key(q[1].filter((x) => x !== 7)) : null
      const s = iv === full ? 0 : (iv === no5 ? 1 : -1)
      if (s < 0) continue
      const score = s * 3 + (r === bass ? 0 : 2) + qi * 0.01
      if (!best || score < best.score) best = { score: score, root: r, q: q[0] }
    }
  }
  const names = pcs.map((p) => NOTE[p])
  if (!best) return { name: null, root: bass, quality: null, bass: bass, notes: names }
  const matched = best
  const nm = NOTE[matched.root] + matched.q + (matched.root !== bass ? "/" + NOTE[bass] : "")
  return { name: nm, root: matched.root, quality: matched.q, bass: bass, notes: names }
}
