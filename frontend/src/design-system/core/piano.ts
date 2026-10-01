/* ── Piano: disposición de teclas blancas y negras ───────────────── */
export const WHITE: readonly number[] = [0, 2, 4, 5, 7, 9, 11]

export const BLACK_AFTER: Readonly<Record<number, number>> = {
  0: 1,
  2: 3,
  5: 6,
  7: 8,
  9: 10,
}
