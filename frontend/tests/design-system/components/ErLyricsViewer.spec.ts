import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErLyricsViewer from '@/design-system/components/ErLyricsViewer.vue'

describe('ErLyricsViewer component', () => {
  const sampleLyrics = [
    '# Verso 1',
    '[Am7]Bajo el farol de la plaza',
    '',
    '[D7]buscando una señal',
  ].join('\n')

  it('renders section title, speed control, maximize button, and parsed lyrics', () => {
    const wrapper = mount(ErLyricsViewer, {
      props: {
        lyrics: sampleLyrics,
        title: 'Bajo el farol',
      },
    })
    expect(wrapper.classes()).toContain('er-lyrics')
    expect(wrapper.find('.er-lyrics-title').text()).toBe('Bajo el farol')
    expect(wrapper.find('.er-lyrics-section').text()).toBe('Verso 1')
    expect(wrapper.find('.er-lyric--gap').exists()).toBe(true)

    // Segment chords and texts
    const chordSpans = wrapper.findAll('.er-seg-chord')
    expect(chordSpans[0].text()).toBe('Am7')
    expect(chordSpans[1].text()).toBe('D7')
  })

  it('toggles fullscreen max mode and emits/applies er-lyrics--max class', async () => {
    const wrapper = mount(ErLyricsViewer, {
      props: { lyrics: sampleLyrics },
    })
    expect(wrapper.classes()).not.toContain('er-lyrics--max')

    const maxBtn = wrapper.find('button[aria-label="Maximizar"]')
    expect(maxBtn.exists()).toBe(true)
    await maxBtn.trigger('click')

    expect(wrapper.classes()).toContain('er-lyrics--max')
    expect(wrapper.find('button[aria-label="Salir de pantalla completa"]').exists()).toBe(true)
  })

  it('hides chords when showChords is false', () => {
    const wrapper = mount(ErLyricsViewer, {
      props: {
        lyrics: sampleLyrics,
        showChords: false,
      },
    })
    expect(wrapper.findAll('.er-seg-chord').length).toBe(0)
    expect(wrapper.text()).toContain('Bajo el farol de la plaza')
  })
})
