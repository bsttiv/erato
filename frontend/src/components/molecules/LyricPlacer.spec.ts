// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ChordHint from './ChordHint.vue'
import LyricPlacer from './LyricPlacer.vue'
import type { Lyrics } from '../../lib/lyrics'

const lyrics: Lyrics = { lines: [
  { section: 'Coro', text: '', chords: [] },
  { text: 'Hola', chords: [{ col: 2, chord_id: 'b' }] },
  { text: '', chords: [] },
] }
const chords = [{ id: 'a', name: 'C', instrument: 'piano', notes: [48, 52, 55] }, { id: 'b', name: 'G', instrument: 'piano', notes: [55, 59, 62] }]

const forms = [
  { id: 'a', name: 'C', instrument: 'piano', notes: [48, 52, 55] },
  { id: 'c', name: 'C', instrument: 'piano', notes: [52, 55, 60] },
  { id: 'b', name: 'G', instrument: 'piano', notes: [55, 59, 62] },
]

function setup(props: { lyrics?: Lyrics; chords?: typeof chords } = {}) {
  const wrapper = mount(LyricPlacer, { props: { lyrics, chords, ...props }, attachTo: document.body })
  wrapper.findAll('[data-char-unit]').forEach(unit => {
    unit.element.getBoundingClientRect = () => ({ width: 10 }) as DOMRect
    unit.element.parentElement!.getBoundingClientRect = () => ({ left: 100 }) as DOMRect
  })
  return wrapper
}
type Wrapper = ReturnType<typeof setup>
const pointer = (type: string, x: number) => new MouseEvent(type, { clientX: x, clientY: 5, button: 0, bubbles: true })
const line = (wrapper: Wrapper, index: number) => wrapper.find(`[data-lyric-line="${index}"]`).element
const paletteChip = (wrapper: Wrapper) => wrapper.find('[data-chord-chip]').element
const placedChip = (wrapper: Wrapper) => wrapper.find('.absolute.top-0.cursor-grab').element
function dropAt(target: Element | null, x: number) {
  document.elementFromPoint = vi.fn(() => target)
  window.dispatchEvent(pointer('pointerup', x))
}
const emitted = (wrapper: Wrapper) => wrapper.emitted('update:lyrics')![0][0] as Lyrics

afterEach(() => { document.body.innerHTML = '' })

describe('LyricPlacer', () => {
  it('LYR-106 drops a palette chord at the pointer column', () => {
    const wrapper = setup()
    paletteChip(wrapper).dispatchEvent(pointer('pointerdown', 10))
    dropAt(line(wrapper, 2), 150)
    expect(emitted(wrapper).lines[2].chords).toEqual([{ col: 5, chord_id: 'a' }])
    expect(emitted(wrapper).lines[0].section).toBe('Coro')
  })
  it('LYR-107 moves a placed chord to another line', () => {
    const wrapper = setup()
    placedChip(wrapper).dispatchEvent(pointer('pointerdown', 120))
    dropAt(line(wrapper, 2), 130)
    expect(emitted(wrapper).lines[1].chords).toEqual([])
    expect(emitted(wrapper).lines[2].chords).toEqual([{ col: 3, chord_id: 'b' }])
  })
  it('LYR-108 removes a placed chord dropped outside the lyrics', () => {
    const wrapper = setup()
    placedChip(wrapper).dispatchEvent(pointer('pointerdown', 120))
    dropAt(document.body, 900)
    expect(emitted(wrapper).lines[1].chords).toEqual([])
  })
  it('LYR-109 ignores a palette chord dropped outside the lyrics', () => {
    const wrapper = setup()
    paletteChip(wrapper).dispatchEvent(pointer('pointerdown', 10))
    dropAt(document.body, 900)
    expect(wrapper.emitted('update:lyrics')).toBeUndefined()
  })
  it('LYR-110 shows a section line but offers no drop target for it', () => {
    const wrapper = setup()
    expect(wrapper.text()).toContain('Coro')
    expect(wrapper.findAll('[data-lyric-line]').map(node => node.attributes('data-lyric-line'))).toEqual(['1', '2'])
  })
})

describe('chord forms — tests_md/propuesta-editor-acordes-2026-10-31.md', () => {
  const next = (wrapper: Wrapper, name = 'C') => wrapper.get(`[aria-label="Forma siguiente de ${name}"]`)
  const hinted = (wrapper: Wrapper) => wrapper.findComponent(ChordHint)

  it('CHE-001 groups the forms of a chord in one chip with form buttons', () => {
    const wrapper = setup({ chords: forms })
    const chips = wrapper.findAll('[data-chord-chip]')
    expect(chips.map(chip => chip.text())).toEqual(['C1/2', 'G'])
    expect(wrapper.find('[aria-label="Forma anterior de C"]').exists()).toBe(true)
    expect(next(wrapper).exists()).toBe(true)
  })
  it('CHE-002 offers no form buttons for a chord with one form', () => {
    const wrapper = setup({ chords: forms })
    expect(wrapper.find('[aria-label="Forma anterior de G"]').exists()).toBe(false)
    expect(wrapper.find('[aria-label="Forma siguiente de G"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-chord-chip]')[1].text()).not.toContain('/')
  })
  it('CHE-003 returns to the first form after the last one', async () => {
    const wrapper = setup({ chords: forms })
    await next(wrapper).trigger('click')
    expect(wrapper.get('[data-chord-chip]').text()).toBe('C2/2')
    await next(wrapper).trigger('click')
    expect(wrapper.get('[data-chord-chip]').text()).toBe('C1/2')
  })
  it('CHE-004 drags the selected form', async () => {
    const wrapper = setup({ chords: forms })
    await next(wrapper).trigger('click')
    paletteChip(wrapper).dispatchEvent(pointer('pointerdown', 10))
    dropAt(line(wrapper, 2), 150)
    expect(emitted(wrapper).lines[2].chords).toEqual([{ col: 5, chord_id: 'c' }])
  })
  it('CHE-005 shows the selected form on hover and on focus', async () => {
    const wrapper = setup({ chords: forms })
    const chip = wrapper.get('[data-chord-chip]')
    await chip.trigger('pointerenter')
    expect(hinted(wrapper).props('chord').id).toBe('a')
    await chip.trigger('pointerleave')
    expect(hinted(wrapper).exists()).toBe(false)
    await next(wrapper).trigger('click')
    await chip.trigger('blur')
    await chip.trigger('focus')
    expect(hinted(wrapper).props('chord').id).toBe('c')
    await chip.trigger('blur')
    expect(hinted(wrapper).exists()).toBe(false)
  })
  it('CHE-006 hides the figure when the pointer leaves the form buttons', async () => {
    const wrapper = setup({ chords: forms })
    await next(wrapper).trigger('click')
    expect(hinted(wrapper).props('chord').id).toBe('c')
    await wrapper.get('[data-chord-chip]').element.parentElement!.dispatchEvent(new Event('pointerleave'))
    await wrapper.vm.$nextTick()
    expect(hinted(wrapper).exists()).toBe(false)
  })
  it('CHE-007 removes only the chord whose X is pressed', async () => {
    const wrapper = setup({ lyrics: { lines: [{ text: 'Hola', chords: [{ col: 0, chord_id: 'a' }, { col: 9, chord_id: 'b' }] }] } })
    await wrapper.get('[aria-label="Quitar G"]').trigger('click')
    expect(emitted(wrapper).lines[0].chords).toEqual([{ col: 0, chord_id: 'a' }])
  })
  it('CHE-008 leaves a placed chord alone on a click without movement', () => {
    const wrapper = setup()
    placedChip(wrapper).dispatchEvent(pointer('pointerdown', 120))
    dropAt(document.body, 122)
    expect(wrapper.emitted('update:lyrics')).toBeUndefined()
  })
})
