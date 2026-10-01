/* ── Guitarra: afinación estándar y funciones auxiliares ─────────── */
export const TUNING: readonly number[] = [40, 45, 50, 55, 59, 64]
export const STR: readonly string[] = ["E", "A", "D", "G", "B", "e"]

/** Convierte un array de 6 trastes en notas MIDI absolutas (omite cuerdas apagadas -1). */
export function fretsToMidi(fr: number[]): number[] {
  const out: number[] = []
  fr.forEach((f, i) => {
    if (f >= 0) out.push(TUNING[i] + f)
  })
  return out
}

/** Calcula el traste base óptimo para visualizar el diagrama de mástil. */
export function autoBase(fr: number[]): number {
  const pos = fr.filter((f) => f > 0)
  if (!pos.length) return 1
  const mx = Math.max.apply(null, pos)
  const mn = Math.min.apply(null, pos)
  return mx <= 5 ? 1 : mn
}
