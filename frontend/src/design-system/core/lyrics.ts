/* ── LyricsViewer: segmentación de acordes sobre sílabas ──────────── */

export interface LyricSegment {
  chord: string | null
  text: string
}

export interface ChordMark {
  offset: number
  chord: string
}

export interface SyllableToken {
  offset: number
  text: string
  chord: string | null
}

export type DecomposedLine = SyllableToken[] & {
  text: string
  marks: ChordMark[]
  tokens: SyllableToken[]
}

export const SENTINEL_REMOVE = '__REMOVE__'


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

/**
 * Divide una línea de texto con markup en su texto plano visible, las marcas de acordes
 * con sus offsets, y tokens de sílabas/palabras listos para interacción.
 */
export function decomposeLine(line: string): DecomposedLine {
  const marks: ChordMark[] = []
  const re = /\[([^\]]+)\]/g
  let last = 0
  let plainText = ''
  let m: RegExpExecArray | null

  while ((m = re.exec(line))) {
    plainText += line.slice(last, m.index)
    marks.push({ offset: plainText.length, chord: m[1] })
    last = re.lastIndex
  }
  plainText += line.slice(last)

  const tokens: SyllableToken[] = []

  if (plainText.length === 0) {
    if (marks.length > 0) {
      for (const mk of marks) {
        tokens.push({ offset: 0, text: '', chord: mk.chord })
      }
    }
  } else {
    // Busca límites de palabras (\S+\s*) y subdivide si hay marcas intermedias
    const wordRe = /\S+\s*/g
    let wm: RegExpExecArray | null

    while ((wm = wordRe.exec(plainText))) {
      const start = wm.index
      const fullText = wm[0]
      const end = start + fullText.length

      const splits: number[] = [start]
      for (const mk of marks) {
        if (mk.offset > start && mk.offset < end && !splits.includes(mk.offset)) {
          splits.push(mk.offset)
        }
      }
      splits.sort((a, b) => a - b)
      splits.push(end)

      for (let i = 0; i < splits.length - 1; i++) {
        const segStart = splits[i]
        const segEnd = splits[i + 1]
        const segText = plainText.slice(segStart, segEnd)
        const chord = marks.find((mk) => mk.offset === segStart)?.chord || null
        tokens.push({
          offset: segStart,
          text: segText,
          chord,
        })
      }
    }

    if (tokens.length > 0 && tokens[0].offset > 0) {
      const leadingText = plainText.slice(0, tokens[0].offset)
      const chord = marks.find((mk) => mk.offset === 0)?.chord || null
      tokens.unshift({
        offset: 0,
        text: leadingText,
        chord,
      })
    } else if (tokens.length === 0 && plainText.length > 0) {
      const chord = marks.find((mk) => mk.offset === 0)?.chord || null
      tokens.push({
        offset: 0,
        text: plainText,
        chord,
      })
    }

    for (const mk of marks) {
      if (mk.offset >= plainText.length) {
        tokens.push({
          offset: mk.offset,
          text: '',
          chord: mk.chord,
        })
      }
    }
  }

  const result = Object.assign([...tokens], {
    text: plainText,
    marks,
    tokens,
  }) as DecomposedLine

  return result
}

/**
 * Reconstruye el texto con corchetes a partir de texto + marcas, objeto DecomposedLine o tokens.
 */
export function composeLine(
  textOrInput:
    | string
    | { text: string; marks?: ChordMark[]; tokens?: SyllableToken[] }
    | SyllableToken[],
  marksOrUndefined?: ChordMark[]
): string {
  if (typeof textOrInput === 'string') {
    const text = textOrInput
    const marks = marksOrUndefined || []
    if (marks.length === 0) return text

    const sortedMarks = [...marks].sort((a, b) => a.offset - b.offset)
    let result = ''
    let last = 0

    for (const mk of sortedMarks) {
      const off = Math.max(0, Math.min(mk.offset, text.length))
      result += text.slice(last, off)
      result += `[${mk.chord}]`
      last = off
    }
    result += text.slice(last)
    return result
  }

  if (textOrInput && typeof textOrInput === 'object') {
    if (
      'text' in textOrInput &&
      'marks' in textOrInput &&
      Array.isArray((textOrInput as any).marks)
    ) {
      return composeLine((textOrInput as any).text, (textOrInput as any).marks)
    }

    if (Array.isArray(textOrInput)) {
      return textOrInput
        .map((t) => (t.chord ? `[${t.chord}]` : '') + t.text)
        .join('')
    }
  }

  return ''
}

/**
 * Único camino de escritura para acordes en letras.
 * Inserta, reemplaza o remueve (con null/vacio) el acorde en la linea y offset dados.
 */
export function setChordAt(
  content: string,
  target: { line: number; offset: number },
  chord: string | null
): string {
  if (typeof content !== 'string') return content
  const lines = content.split('\n')

  if (target.line < 0 || target.line >= lines.length) {
    return content
  }

  const line = lines[target.line]
  const decomposed = decomposeLine(line)

  if (target.offset < 0 || target.offset > decomposed.text.length) {
    return content
  }

  const existingMarks = decomposed.marks.filter((m) => m.offset !== target.offset)

  if (chord && chord.trim() !== '') {
    existingMarks.push({ offset: target.offset, chord: chord.trim() })
  }

  existingMarks.sort((a, b) => a.offset - b.offset)
  lines[target.line] = composeLine(decomposed.text, existingMarks)

  return lines.join('\n')
}
