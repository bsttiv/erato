// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ChordDiagram from './ChordDiagram.vue'
import type { Chord } from '../../lib/chords'

const guitar = (strings: number[], frets: number[]): Chord => ({ name: 'X', instrument: 'guitar', strings, frets, notes: [40] })
const piano = (notes: number[]): Chord => ({ name: 'X', instrument: 'piano', notes })
const render = (chord: Chord) => mount(ChordDiagram, { props: { chord } })
type Wrapper = ReturnType<typeof render>
const labels = (wrapper: Wrapper) => wrapper.findAll('text').map(node => node.text())
const size = (wrapper: Wrapper) => wrapper.get('svg').attributes('viewBox')

describe('ChordDiagram — tests_md/propuesta-figura-acorde-2026-10-31.md', () => {
  it('DIA-001 keeps the size and five frets for any position', () => {
    const open = render(guitar([1, 2, 3, 4, 5, 6], [0, 0, 1, 2, 2, 0]))
    const high = render(guitar([1, 2, 3, 4, 5], [12, 14, 14, 14, 12]))
    expect(size(high)).toBe(size(open))
    expect(labels(open)).toEqual(['1', '2', '3', '4', '5'])
    expect(labels(high)).toEqual(['12', '13', '14', '15', '16'])
  })
  it('DIA-002 starts the neck at the lowest fret and draws every note', () => {
    const wrapper = render(guitar([1, 2, 3, 4], [7, 9, 9, 8]))
    expect(labels(wrapper)[0]).toBe('7')
    expect(wrapper.findAll('[data-pressed-string]')).toHaveLength(4)
    const centers = wrapper.findAll('[data-pressed-string]').map(node => Number(node.attributes('cx')))
    const texts = wrapper.findAll('text')
    expect(centers[0]).toBe(Number(texts[0].attributes('x')))
    expect(centers[1]).toBe(Number(texts[2].attributes('x')))
    expect(centers[3]).toBe(Number(texts[1].attributes('x')))
  })
  it('DIA-003 marks muted, open and pressed strings', () => {
    const wrapper = render(guitar([1, 2, 3, 4], [0, 1, 0, 2]))
    expect(wrapper.findAll('[data-muted-string]')).toHaveLength(2)
    expect(wrapper.findAll('[data-open-string]')).toHaveLength(2)
    expect(wrapper.findAll('[data-pressed-string]')).toHaveLength(2)
  })
  it('DIA-004 starts the keyboard at the octave of the lowest note', () => {
    const wrapper = render(piano([73, 77, 80]))
    const lit = wrapper.findAll('rect').filter(key => key.classes().some(name => name === 'fill-brass' || name === 'fill-[#c47d1c]'))
    expect(lit).toHaveLength(3)
    expect(lit.map(key => key.classes().includes('fill-brass'))).toEqual([true, false, false])
    expect(wrapper.findAll('rect')).toHaveLength(24)
  })
  it('DIA-005 writes the shape of a chord wider than two octaves', () => {
    const wrapper = render(piano([48, 80]))
    expect(wrapper.find('svg').exists()).toBe(false)
    expect(wrapper.text()).toContain('48, 80')
  })
})
