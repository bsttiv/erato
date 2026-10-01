import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChordGrid from '@/features/compositions/ChordGrid.vue'
import type { ChordsSection } from '@/api/compositions'

describe('ChordGrid feature component', () => {
  const sampleChords: ChordsSection = {
    instrument: 'guitar',
    entries: [
      { bar: 1, notes: [-1, 3, 2, 0, 1, 0], name: 'C' },
      { bar: 2, notes: [-1, 0, 0, 2, 3, 2], name: 'D' },
      { bar: 3, notes: [0, 2, 2, 0, 0, 0], name: 'Em' },
    ],
  }

  it('renders a grid of ErChordEditor components from entries', () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: true,
      },
    })

    const grid = wrapper.find('.er-chord-grid')
    expect(grid.exists()).toBe(true)

    const chordEditors = wrapper.findAllComponents({ name: 'ErChordEditor' })
    expect(chordEditors.length).toBe(3)
  })

  it('supports adding a new chord diagram', async () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: true,
      },
    })

    const addBtn = wrapper.find('[data-test="add-chord-btn"]')
    expect(addBtn.exists()).toBe(true)
    await addBtn.trigger('click')

    expect(wrapper.emitted('update:chords')).toBeTruthy()
    const emitted = wrapper.emitted('update:chords')![0][0] as ChordsSection
    expect(emitted.entries.length).toBe(4)
  })

  it('supports removing an existing chord diagram', async () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: true,
      },
    })

    const removeBtns = wrapper.findAll('[data-test="remove-chord-btn"]')
    expect(removeBtns.length).toBe(3)
    await removeBtns[1].trigger('click')

    expect(wrapper.emitted('update:chords')).toBeTruthy()
    const emitted = wrapper.emitted('update:chords')![0][0] as ChordsSection
    expect(emitted.entries.length).toBe(2)
    expect(emitted.entries[0].name).toBe('C')
    expect(emitted.entries[1].name).toBe('Em')
  })

  it('emits updated ChordsSection payload when any chord changes', async () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: true,
      },
    })

    const chordEditors = wrapper.findAllComponents({ name: 'ErChordEditor' })
    // Simulate chord change on first editor
    await chordEditors[0].vm.$emit('change', {
      instrument: 'guitar',
      frets: [0, 0, 2, 2, 1, 0],
      notes: [45, 52, 57, 60, 64],
      name: 'Am',
    })

    expect(wrapper.emitted('update:chords')).toBeTruthy()
    const emitted = wrapper.emitted('update:chords')![0][0] as ChordsSection
    expect(emitted.entries[0].name).toBe('Am')
    expect(emitted.entries[0].notes).toEqual([0, 0, 2, 2, 1, 0])
  })

  it('instrument toggle switches global instrument between guitar and piano', async () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: true,
      },
    })

    const segButtons = wrapper.findAll('.er-seg-opt')
    const pianoBtn = segButtons.find((b) => b.text().toLowerCase().includes('piano'))
    expect(pianoBtn).toBeDefined()
    await pianoBtn!.trigger('click')

    expect(wrapper.emitted('update:chords')).toBeTruthy()
    const emitted = wrapper.emitted('update:chords')![0][0] as ChordsSection
    expect(emitted.instrument).toBe('piano')
  })

  it('hides edit and remove buttons when editable is false', () => {
    const wrapper = mount(ChordGrid, {
      props: {
        chords: sampleChords,
        editable: false,
      },
    })

    expect(wrapper.find('[data-test="add-chord-btn"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="remove-chord-btn"]').length).toBe(0)
  })
})
