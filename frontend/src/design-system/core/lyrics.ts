/* ── LyricsViewer: segmentación de acordes sobre sílabas ──────────── */

export interface LyricSegment {
  chord: string | null
  text: string
}

/**
 * Parsea una línea de texto con marcas de acordes en formato bracket (ej. `[Am7]Bajo el farol...`)
 * separándola en segmentos con el acorde y el texto alineado correspondiente.
 */
export function parseLine(line: string): LyricSegment[] {
  const segs: LyricSegment[] = []
  const re = /\[([^\]]+)\]/g
  let last = 0
  let chord: string | null = null
  let m: RegExpExecArray | null

  while ((m = re.exec(line))) {
    if (m.index > last || chord !== null) {
      segs.push({ chord: chord, text: line.slice(last, m.index) })
    }
    chord = m[1]
    last = re.lastIndex
  }
  segs.push({ chord: chord, text: line.slice(last) })

  return segs.filter((s) => s.chord !== null || s.text.length > 0)
}
