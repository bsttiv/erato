// Cell grammar and keyboard map: decisiones/09-secciones-de-cancion.md §3.
const fret = '(?:0|[1-9]|1[0-9]|2[0-4])'
const completeCell = new RegExp(`^${fret}(?:[hpbr/\\\\s]${fret}){0,3}[~v]?$`)
const transition = /^[hpbr/\\s]$/

/** Editing state of the six-string tab: columns of six cells (one per string). */
export interface TabState {
  columns: string[][]
  row: number
  col: number
}

/** Keyboard event subset used by editTab (real KeyboardEvents satisfy it). */
export interface TabEditEvent {
  key: string
  ctrlKey?: boolean
  metaKey?: boolean
  altKey?: boolean
  shiftKey?: boolean
}

export function isValidCell(value: unknown): boolean {
  return typeof value === 'string' && (['', 'x', '|'].includes(value) || completeCell.test(value))
}

export function normalizeCell(value: string): string {
  if (typeof value !== 'string') return value
  return value.replace(/X/g, 'x').replace(/\d+/g, (digits) => String(Number(digits)))
}

export function isCompleteTab(columns: string[][]): boolean {
  return columns.every((column) => column.length === 6 && column.every(isValidCell)
    && (!column.includes('|') || column.every((cell) => cell === '|')))
}

function isIncompleteCell(cell: string): boolean {
  if (!transition.test(cell.at(-1) || '')) return false
  const before = cell.slice(0, -1)
  return completeCell.test(before) && !/[~v]$/.test(before)
    && (before.match(/[hpbr/\\s]/g) || []).length < 3
}

export function editTab(state: TabState, event: TabEditEvent): TabState {
  const draft = { ...state, columns: state.columns.map((column) => [...column]) }
  const { key } = event
  if (event.ctrlKey || event.metaKey || event.altKey) return draft
  const last = Math.max(0, draft.columns.length - 1)
  if (key === 'ArrowLeft') draft.col = Math.max(0, draft.col - 1)
  else if (key === 'ArrowRight') draft.col = Math.min(last, draft.col + 1)
  else if (key === 'ArrowUp') draft.row = Math.max(0, draft.row - 1)
  else if (key === 'ArrowDown') draft.row = Math.min(5, draft.row + 1)
  else if (key === ' ') {
    const index = draft.columns.length ? draft.col + 1 : 0
    draft.columns.splice(index, 0, Array(6).fill(''))
    draft.col = index
  } else if (key === 'Delete' && event.shiftKey) {
    draft.columns.splice(draft.col, 1)
    draft.col = Math.min(draft.col, Math.max(0, draft.columns.length - 1))
  } else if (/^[0-9xX|~v]$/.test(key) || transition.test(key) || ['Backspace', 'Delete'].includes(key)) {
    if (!draft.columns.length) draft.columns.push(Array(6).fill(''))
    const column = draft.columns[draft.col]
    const cell = column[draft.row]
    let next = cell
    if (key === '|') {
      column.fill('|')
      return draft
    }
    if (key === 'Delete') next = ''
    else if (key === 'Backspace') next = cell.slice(0, -1)
    else if (/^[xX]$/.test(key)) next = 'x'
    else if (/^\d$/.test(key)) {
      if (['', 'x', '|'].includes(cell)) next = key
      else if (isIncompleteCell(cell)) next = cell + key
      else if (!/[~v]$/.test(cell)) {
        const digits = cell.match(/\d+$/)?.[0]
        if (digits) {
          const combined = Number(digits + key)
          next = cell.slice(0, -digits.length) + (combined <= 24 ? String(combined) : key)
        }
      }
    } else if (transition.test(key)) next = cell + key
    else if (/^[~v]$/.test(key) && completeCell.test(cell) && !/[~v]$/.test(cell)) next = cell + key
    if (isValidCell(next) || isIncompleteCell(next)) {
      if (column.includes('|') && next !== '|') column.fill('')
      column[draft.row] = next
    }
  }
  return draft
}
