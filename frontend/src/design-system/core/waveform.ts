/* ── DemoPlayer: forma de onda sintética determinista (PRNG congruencial lineal) ── */

/**
 * Genera una forma de onda pseudo-aleatoria determinista basada en la semilla dada.
 * Transcripción literal de bundle.js:343-347 utilizando constantes exactas.
 */
export function peaks(seed: string, n: number): number[] {
  let x = 0
  for (let i = 0; i < seed.length; i++) {
    x = (x * 31 + seed.charCodeAt(i)) >>> 0
  }
  const out: number[] = []
  for (let j = 0; j < n; j++) {
    x = (x * 1664525 + 1013904223) >>> 0
    const r = x / 4294967296
    const env = 0.45 + 0.55 * Math.sin((Math.PI * (j + 1)) / (n + 1))
    out.push(Math.max(0.12, env * (0.35 + 0.65 * r)))
  }
  return out
}
