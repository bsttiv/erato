/* ── Formateo y utilidades generales del sistema de diseño ─────────── */

/** Une clases CSS condicionales filtrando valores falsy (bundle.js:10). */
export function cx(...args: unknown[]): string {
  return args.filter(Boolean).join(" ")
}

/** Formatea un entero con al menos dos dígitos rellenando con cero a la izquierda (bundle.js:95). */
export function pad2(n: number): string {
  return (n < 10 ? "0" : "") + n
}

/** Formatea segundos en formato mm:ss (bundle.js:342). */
export function fmt(t: number): string {
  const s = Math.max(0, Math.floor(t))
  return pad2(Math.floor(s / 60)) + ":" + pad2(s % 60)
}

const esDateFormatter = new Intl.DateTimeFormat('es', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

/**
 * Formatea una fecha ISO o timestamp a español (ej. "1 oct 2026").
 * Retorna '' para null/undefined/cadena vacía.
 * Si la fecha no es válida, retorna el valor crudo en string, nunca "Invalid Date".
 */
export function formatDate(value: string | number | Date | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return ''
  }
  const date = value instanceof Date ? value : new Date(value)
  if (isNaN(date.getTime())) {
    return String(value)
  }
  return esDateFormatter.format(date)
}

