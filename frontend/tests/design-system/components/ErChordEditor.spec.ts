import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErChordEditor from '@/design-system/components/ErChordEditor.vue'

describe('ErChordEditor component', () => {
  it('renders chord editor with fretboard by default and displays chord name C', () => {
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [-1, 3, 2, 0, 1, 0], // C major
      },
    })
    expect(wrapper.classes()).toContain('er-chord')
    expect(wrapper.find('.er-chord-name').text()).toContain('C')
    expect(wrapper.find('svg[aria-label="Diagrama de guitarra"]').exists()).toBe(true)
  })

  it('switches between guitar and piano and performs octave folding into [48, 71]', async () => {
    // Open E: [0, 2, 2, 1, 0, 0] -> fretsToMidi produces E2 (40) which is < 48
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [0, 2, 2, 1, 0, 0],
        defaultInstrument: 'guitar',
      },
    })
    // Switch to piano
    const segmentedButtons = wrapper.findAll('.er-seg-opt')
    expect(segmentedButtons.length).toBe(2)
    await segmentedButtons[1].trigger('click')

    // Now piano is rendered
    expect(wrapper.find('svg[aria-label="Teclado de piano"]').exists()).toBe(true)
    const emitted = wrapper.emitted('change') || wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()

    // Notes folded: all notes in keys are between 48 and 71
    const lastEmit = (wrapper.emitted('change')?.[0]?.[0] || wrapper.emitted('update:modelValue')?.[0]?.[0]) as any
    expect(lastEmit.instrument).toBe('piano')
    for (const note of lastEmit.notes) {
      expect(note).toBeGreaterThanOrEqual(48)
      expect(note).toBeLessThanOrEqual(71)
    }
  })

  it('allows changing base fret with navigation buttons', async () => {
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [-1, 7, 9, 9, 8, 7], // Em barre
        defaultBaseFret: 7,
      },
    })
    const upBtn = wrapper.find('button[aria-label="Subir traste"]')
    expect(upBtn.exists()).toBe(true)
    await upBtn.trigger('click')

    expect(wrapper.find('.er-fb-base').text()).toBe('8fr')
  })
})
