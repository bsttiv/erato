import { describe, expect, it } from 'vitest'
import { isValidCell, normalizeCell, editTab, isCompleteTab } from './tabEditor'

// Approved area rules: decisiones/09-secciones-de-cancion.md §3;
// decisiones/14-testing.md §3–4. Original numeric EDT mappings are unavailable.
describe('EDT-rule cell grammar (decision 09 §3)', () => {
  it.each(['', 'x', '|', '0', '24', '3h5', '5p3', '7b9', '9r7', '3/5', '5\\3', '3s5', '5~', '5v', '5h7p5~', '3/5/7', '7b9r7'])('EDT-rule accepts approved cell %j', (cell) => {
    expect(isValidCell(cell)).toBe(true)
  })
  it.each(['25', '-1', '03', '3h', 'h5', '3q5', '3h25', '5~7', '5v7', '1h2h3h4h5', '5~h7', '5h7~~', '5hp7', '5h7p25', 'abc', '1.5', 3, 'x5', '||', '3 ', ' 3', 'X'])('EDT-rule rejects approved invalid cell %j', (cell) => {
    expect(isValidCell(cell)).toBe(false)
  })
  it('EDT-rule normalizes uppercase mute and leading zero', () => {
    expect(normalizeCell('X')).toBe('x')
    expect(normalizeCell('03')).toBe('3')
  })
})

function state(cell = '') {
  return { columns: [[cell, '', '', '', '', '']], row: 0, col: 0 }
}
function type(keys, initial = state()) {
  return [...keys].reduce((draft, key) => editTab(draft, { key }), initial)
}
describe('EDT-rule keyboard map (decision 09 §3)', () => {
  it('EDT-rule combines digits up to 24, replaces overflow and normalizes zero', () => {
    expect(type('12').columns[0][0]).toBe('12')
    expect(type('35').columns[0][0]).toBe('5')
    expect(type('05').columns[0][0]).toBe('5')
  })
  it('EDT-rule allows incomplete transitions but blocks sending them', () => {
    const incomplete = type('3h')
    expect(incomplete.columns[0][0]).toBe('3h')
    expect(isCompleteTab(incomplete.columns)).toBe(false)
    expect(type('5', incomplete).columns[0][0]).toBe('3h5')
  })
  it('EDT-rule ignores techniques without fret and after vibrato or three transitions', () => {
    expect(type('h').columns[0][0]).toBe('')
    expect(type('5h7p5~h').columns[0][0]).toBe('5h7p5~')
    expect(type('1h2h3h4h').columns[0][0]).toBe('1h2h3h4')
  })
  it('EDT-rule moves through strings and columns without crossing edges', () => {
    let draft = editTab(state(), { key: 'ArrowUp' })
    expect(draft.row).toBe(0)
    draft = editTab(draft, { key: ' ' })
    expect(draft.col).toBe(1)
    draft = editTab(draft, { key: 'ArrowLeft' })
    draft = editTab(draft, { key: 'ArrowDown' })
    expect([draft.row, draft.col]).toEqual([1, 0])
    expect(editTab(draft, { key: 'ArrowRight' }).col).toBe(1)
    expect(editTab({ ...draft, row: 5 }, { key: 'ArrowDown' }).row).toBe(5)
  })
  it('EDT-rule sets mute and full-column bar, never mixed bars', () => {
    expect(type('X').columns[0][0]).toBe('x')
    const barred = type('|')
    expect(barred.columns[0]).toEqual(Array(6).fill('|'))
    expect(isCompleteTab(barred.columns)).toBe(true)
    expect(isCompleteTab([['|', '', '', '', '', '']])).toBe(false)
    expect(type('3', barred).columns[0]).toEqual(['3', '', '', '', '', ''])
  })
  it('EDT-rule backspace removes one character while delete empties only the cell', () => {
    let draft = type('3h5')
    for (const expected of ['3h', '3', '']) {
      draft = editTab(draft, { key: 'Backspace' })
      expect(draft.columns[0][0]).toBe(expected)
    }
    draft = editTab(type('3h5'), { key: 'Delete' })
    expect(draft.columns).toEqual([Array(6).fill('')])
  })
  it('EDT-rule space inserts a column and shift-delete removes it', () => {
    const draft = editTab(type('3'), { key: ' ' })
    expect(draft.columns).toEqual([['3', '', '', '', '', ''], Array(6).fill('')])
    expect(draft.col).toBe(1)
    expect(editTab(draft, { key: 'Delete', shiftKey: true })).toEqual(type('3'))
  })
  it('EDT-rule escape preserves every cell', () => {
    const draft = type('3h5')
    expect(editTab(draft, { key: 'Escape' })).toEqual(draft)
  })
})
