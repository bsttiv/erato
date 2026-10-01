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

  it('renders horizontal fretboard: strings horizontal (y1 == y2) and nut vertical (x1 == x2)', () => {
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [0, 0, 0, 0, 0, 0],
      },
    })
    const strings = wrapper.findAll('line.er-fb-string')
    expect(strings.length).toBe(6)
    strings.forEach((str) => {
      const y1 = Number(str.attributes('y1'))
      const y2 = Number(str.attributes('y2'))
      expect(y1).toBe(y2)
    })

    const nut = wrapper.find('line.er-fb-nut')
    expect(nut.exists()).toBe(true)
    const x1 = Number(nut.attributes('x1'))
    const x2 = Number(nut.attributes('x2'))
    expect(x1).toBe(x2)
  })

  it('renders high-e row above low-E row', () => {
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [0, 0, 0, 0, 0, 0],
      },
    })
    const markerHits = wrapper.findAll('rect.er-fb-hit')
    const highEHit = markerHits.find((h) => h.find('title').text().startsWith('e:'))
    const lowEHit = markerHits.find((h) => h.find('title').text().startsWith('E:'))
    expect(highEHit).toBeDefined()
    expect(lowEHit).toBeDefined()
    expect(Number(highEHit!.attributes('y'))).toBeLessThan(Number(lowEHit!.attributes('y')))
  })

  it('clicking a fret cell emits set(s, fret) payload and marker click toggles open/mute', async () => {
    const wrapper = mount(ErChordEditor, {
      props: {
        defaultFrets: [-1, -1, -1, -1, -1, -1],
      },
    })
    const cellA3 = wrapper.findAll('rect.er-fb-hit').find((h) => h.find('title').text().includes('A, traste 3'))
    expect(cellA3).toBeDefined()
    await cellA3!.trigger('click')

    const emitted = wrapper.emitted('change')?.[0]?.[0] as any
    expect(emitted.frets[1]).toBe(3)

    const markerE = wrapper.findAll('rect.er-fb-hit').find((h) => h.find('title').text().startsWith('E:'))
    expect(markerE).toBeDefined()
    await markerE!.trigger('click')

    const lastEmitted = wrapper.emitted('change')?.[1]?.[0] as any
    expect(lastEmitted.frets[0]).toBe(0)
  })
})
