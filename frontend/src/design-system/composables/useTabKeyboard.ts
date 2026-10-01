import { ref, type Ref } from 'vue'
import { EMPTY, TECH, type TabColumn } from '../core/tab'

export interface TabSelection {
  c: number
  s: number
}

export interface UseTabKeyboardOptions {
  names?: string[]
  initialSel?: TabSelection
}

export function useTabKeyboard(
  cols: Ref<TabColumn[]>,
  options?: UseTabKeyboardOptions
) {
  const names = options?.names || ["e", "B", "G", "D", "A", "E"]
  const sel = ref<TabSelection>(options?.initialSel || { c: 0, s: 0 })

  function move(dc: number, ds: number) {
    const c = Math.max(0, Math.min(cols.value.length - 1, sel.value.c + dc))
    const s = Math.max(0, Math.min(names.length - 1, sel.value.s + ds))
    sel.value = { c, s }
  }

  function insert(val: TabColumn) {
    const n = cols.value.slice()
    n.splice(sel.value.c + 1, 0, val)
    cols.value = n
    sel.value = { c: sel.value.c + 1, s: sel.value.s }
  }

  function pick(c: number, s: number) {
    sel.value = { c, s }
  }

  function onKey(e: KeyboardEvent | { key: string; preventDefault?: () => void }) {
    const c = sel.value.c
    const s = sel.value.s
    const col = cols.value[c]
    const k = e.key

    if (k === "ArrowRight" || k === " ") {
      e.preventDefault?.()
      if (c === cols.value.length - 1) {
        cols.value = cols.value.concat([EMPTY()])
      }
      sel.value = { c: c + 1, s: s }
      return
    }
    if (k === "ArrowLeft") {
      e.preventDefault?.()
      move(-1, 0)
      return
    }
    if (k === "ArrowUp") {
      e.preventDefault?.()
      move(0, -1)
      return
    }
    if (k === "ArrowDown") {
      e.preventDefault?.()
      move(0, 1)
      return
    }
    if (k === "Enter") {
      e.preventDefault?.()
      insert(EMPTY())
      return
    }
    if (k === "|") {
      e.preventDefault?.()
      insert("|")
      return
    }
    if (col === "|") {
      if (k === "Backspace" || k === "Delete") {
        e.preventDefault?.()
        const n0 = cols.value.slice()
        n0.splice(c, 1)
        cols.value = n0
        sel.value = { c: Math.max(0, c - 1), s: s }
      }
      return
    }
    const n = cols.value.slice()
    const colArr = col as string[]
    const cell = colArr[s]
    if (/^[0-9]$/.test(k)) {
      e.preventDefault?.()
      const run = (/[0-9]+$/.exec(cell) || [""])[0]
      let nv: string
      if (run.length === 1 && Number(run + k) <= 24) nv = cell + k
      else if (cell && !run) nv = cell + k
      else nv = k
      n[c] = colArr.slice()
      n[c][s] = nv.slice(0, 6)
      cols.value = n
      return
    }
    if (k.length === 1 && TECH.indexOf(k.toLowerCase()) >= 0) {
      e.preventDefault?.()
      if (!cell && k.toLowerCase() !== "x") return
      n[c] = colArr.slice()
      n[c][s] = (k.toLowerCase() === "x" ? "x" : cell + k.toLowerCase()).slice(0, 6)
      cols.value = n
      return
    }
    if (k === "Backspace") {
      e.preventDefault?.()
      if (cell) {
        n[c] = colArr.slice()
        n[c][s] = cell.slice(0, -1)
        cols.value = n
      } else {
        move(-1, 0)
      }
      return
    }
    if (k === "Delete") {
      e.preventDefault?.()
      n[c] = colArr.slice()
      n[c][s] = ""
      cols.value = n
      return
    }
  }

  return {
    sel,
    move,
    insert,
    pick,
    onKey,
  }
}
