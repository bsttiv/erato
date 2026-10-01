import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useTabKeyboard } from '@/design-system/composables/useTabKeyboard'
import { blankTab, type TabColumn } from '@/design-system/core/tab'

describe('useTabKeyboard composable', () => {
  it('moves selection with arrow keys and clamps at boundaries', () => {
    const cols = ref<TabColumn[]>(blankTab(4))
    const { sel, onKey } = useTabKeyboard(cols)

    expect(sel.value).toEqual({ c: 0, s: 0 })

    // Move right
    onKey({ key: 'ArrowRight' })
    expect(sel.value).toEqual({ c: 1, s: 0 })

    // Move down
    onKey({ key: 'ArrowDown' })
    expect(sel.value).toEqual({ c: 1, s: 1 })

    // Move left
    onKey({ key: 'ArrowLeft' })
    expect(sel.value).toEqual({ c: 0, s: 1 })

    // Move up
    onKey({ key: 'ArrowUp' })
    expect(sel.value).toEqual({ c: 0, s: 0 })

    // Clamps at top-left
    onKey({ key: 'ArrowUp' })
    expect(sel.value).toEqual({ c: 0, s: 0 })
    onKey({ key: 'ArrowLeft' })
    expect(sel.value).toEqual({ c: 0, s: 0 })
  })

  it('extends columns at the end when pressing ArrowRight or Space', () => {
    const cols = ref<TabColumn[]>(blankTab(2))
    const { sel, onKey } = useTabKeyboard(cols)

    // Move to col 1 (last)
    onKey({ key: 'ArrowRight' })
    expect(sel.value.c).toBe(1)
    expect(cols.value.length).toBe(2)

    // Space extends by adding a new empty column
    onKey({ key: ' ' })
    expect(cols.value.length).toBe(3)
    expect(sel.value.c).toBe(2)

    // ArrowRight also extends at the end
    onKey({ key: 'ArrowRight' })
    expect(cols.value.length).toBe(4)
    expect(sel.value.c).toBe(3)
  })

  it('handles two-digit fret entry (1 -> 12) up to 24, and replaces above 24', () => {
    const cols = ref<TabColumn[]>(blankTab(2))
    const { onKey } = useTabKeyboard(cols)

    // Type '1'
    onKey({ key: '1' })
    expect((cols.value[0] as string[])[0]).toBe('1')

    // Type '2' -> combines into '12'
    onKey({ key: '2' })
    expect((cols.value[0] as string[])[0]).toBe('12')

    // Type '5' -> 125 > 24, replaces with '5'
    onKey({ key: '5' })
    expect((cols.value[0] as string[])[0]).toBe('5')
  })

  it('inserts technique characters (h, p, b, /, ~, x)', () => {
    const cols = ref<TabColumn[]>(blankTab(2))
    const { onKey } = useTabKeyboard(cols)

    // Empty cell ignores technique except 'x' (dead note)
    onKey({ key: 'h' })
    expect((cols.value[0] as string[])[0]).toBe('')

    onKey({ key: 'x' })
    expect((cols.value[0] as string[])[0]).toBe('x')

    // Clear and enter fret '5'
    onKey({ key: 'Delete' })
    onKey({ key: '5' })
    expect((cols.value[0] as string[])[0]).toBe('5')

    // Append technique 'h'
    onKey({ key: 'h' })
    expect((cols.value[0] as string[])[0]).toBe('5h')

    // Append next fret '7'
    onKey({ key: '7' })
    expect((cols.value[0] as string[])[0]).toBe('5h7')
  })

  it('inserts a bar line with | and enters an empty column with Enter', () => {
    const cols = ref<TabColumn[]>(blankTab(2))
    const { sel, onKey } = useTabKeyboard(cols)

    onKey({ key: '|' })
    expect(cols.value[1]).toBe('|')
    expect(sel.value.c).toBe(1)

    onKey({ key: 'Enter' })
    expect(cols.value[2]).toEqual(['', '', '', '', '', ''])
    expect(sel.value.c).toBe(2)
  })

  it('handles Backspace and Delete on a bar line and normal cells', () => {
    const cols = ref<TabColumn[]>([
      ['5', '', '', '', '', ''],
      '|',
      ['', '', '', '', '', ''],
    ])
    const { sel, onKey } = useTabKeyboard(cols, { initialSel: { c: 1, s: 0 } })

    // On bar line: Backspace removes bar line and moves left
    onKey({ key: 'Backspace' })
    expect(cols.value.length).toBe(2)
    expect(cols.value[0]).toEqual(['5', '', '', '', '', ''])
    expect(sel.value.c).toBe(0)

    // On cell with '5': Backspace clears it
    onKey({ key: 'Backspace' })
    expect((cols.value[0] as string[])[0]).toBe('')

    // On empty cell: Backspace moves left (clamped at 0)
    onKey({ key: 'Backspace' })
    expect(sel.value.c).toBe(0)
  })
})
