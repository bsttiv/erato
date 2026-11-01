// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import ChordHint from './ChordHint.vue'
import LyricSheet from './LyricSheet.vue'

const chords = [{ id: 'a', name: 'C', instrument: 'piano', notes: [48, 52, 55] }]
const lines = [{ text: 'Hola', chords: [{ col: 1, chord_id: 'a' }] }]

afterEach(() => { document.body.innerHTML = '' })

describe('LyricSheet — tests_md/propuesta-editor-acordes-2026-10-31.md', () => {
  it('CHE-009 shows the chord figure on hover and on focus', async () => {
    const wrapper = mount(LyricSheet, { props: { lines, chords }, attachTo: document.body })
    const chord = wrapper.get('button')
    await chord.trigger('mouseenter')
    expect(wrapper.findComponent(ChordHint).props('chord').id).toBe('a')
    await chord.trigger('mouseleave')
    expect(wrapper.findComponent(ChordHint).exists()).toBe(false)
    await chord.trigger('focus')
    expect(wrapper.findComponent(ChordHint).props('chord').id).toBe('a')
    await chord.trigger('blur')
    expect(wrapper.findComponent(ChordHint).exists()).toBe(false)
  })
})
