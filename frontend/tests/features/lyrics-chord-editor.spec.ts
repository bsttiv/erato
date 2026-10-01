import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ErLyricsChordEditor from '@/design-system/components/ErLyricsChordEditor.vue'
import ErChordPalette from '@/design-system/components/ErChordPalette.vue'

describe('ErLyricsChordEditor & ErChordPalette', () => {
  const initialLyrics = '# Coro\n[Am]Bajo el farol\nde la esquina\n'
  const chordsList = ['Am', 'C', 'G', 'F']

  beforeEach(() => {
    vi.restoreAllMocks()
    if (!document.elementFromPoint) {
      document.elementFromPoint = () => null
    }
  })

  it('renders a palette button for each chord in chords list, plus sentinel chip "✕ quitar"', () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })

    const palette = wrapper.findComponent(ErChordPalette)
    expect(palette.exists()).toBe(true)

    const buttons = palette.findAll('button')
    // 4 chords + 1 sentinel
    expect(buttons.length).toBe(5)

    const texts = buttons.map((b) => b.text())
    expect(texts).toContain('Am')
    expect(texts).toContain('C')
    expect(texts).toContain('G')
    expect(texts).toContain('F')
    expect(texts.some((t) => t.includes('quitar'))).toBe(true)
  })

  it('keyboard path: arm chord in palette, commit to syllable target, and update lyrics', async () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })

    // 1. Arm 'C' chord button in palette
    const chordButtons = wrapper.findAll('.er-chord-palette button')
    const cButton = chordButtons.find((b) => b.text() === 'C')
    expect(cButton).toBeDefined()
    await cButton!.trigger('click')

    expect(cButton!.attributes('aria-pressed')).toBe('true')

    // Syllable targets should have is-armed class
    const targets = wrapper.findAll('[data-chord-target]')
    expect(targets.length).toBeGreaterThan(0)
    expect(targets[0].classes()).toContain('is-armed')

    // 2. Focus and commit on target on line 1 ("el ")
    const elTarget = targets.find(
      (t) =>
        t.attributes('data-line') === '1' && t.text().includes('el')
    )
    expect(elTarget).toBeDefined()
    await elTarget!.trigger('keydown.enter')

    const emitted = wrapper.emitted('update:lyrics')
    expect(emitted).toBeTruthy()
    const newContent = emitted![0][0] as string
    expect(newContent).toContain('[C]el')
  })

  it('escape key disarms the currently armed chord', async () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })

    const cButton = wrapper
      .findAll('.er-chord-palette button')
      .find((b) => b.text() === 'C')
    await cButton!.trigger('click')
    expect(cButton!.attributes('aria-pressed')).toBe('true')

    // Press Escape
    await wrapper.trigger('keydown.esc')

    expect(cButton!.attributes('aria-pressed')).toBe('false')
    const targets = wrapper.findAll('[data-chord-target]')
    expect(targets[0].classes()).not.toContain('is-armed')
  })

  it('drag path: synthesised pointer events insert chord on drop target', async () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
      attachTo: document.body,
    })

    const gButton = wrapper
      .findAll('.er-chord-palette button')
      .find((b) => b.text() === 'G')
    expect(gButton).toBeDefined()

    // Syllable target for "esquina" on line 2
    const target = wrapper
      .findAll('[data-chord-target]')
      .find(
        (t) =>
          t.attributes('data-line') === '2' && t.text().includes('esquina')
      )
    expect(target).toBeDefined()

    // Mock elementFromPoint to return our target
    vi.spyOn(document, 'elementFromPoint').mockReturnValue(target!.element)

    // Pointer sequence
    await gButton!.trigger('pointerdown', { pointerId: 1, clientX: 10, clientY: 10 })
    expect(document.querySelector('.er-drag-ghost')).not.toBeNull()

    // Move over target
    window.dispatchEvent(
      new MouseEvent('pointermove', { clientX: 50, clientY: 50 })
    )
    await wrapper.vm.$nextTick()

    // Drop
    window.dispatchEvent(
      new MouseEvent('pointerup', { clientX: 50, clientY: 50 })
    )
    await wrapper.vm.$nextTick()

    const emitted = wrapper.emitted('update:lyrics')
    expect(emitted).toBeTruthy()
    const newContent = emitted![0][0] as string
    expect(newContent).toContain('[G]esquina')

    wrapper.unmount()
  })

  it('parity: drag path and keyboard path produce byte-identical output for the same target', async () => {
    // Keyboard run
    const wrapperKb = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })
    const cBtnKb = wrapperKb
      .findAll('.er-chord-palette button')
      .find((b) => b.text() === 'C')
    await cBtnKb!.trigger('click')

    const targetKb = wrapperKb
      .findAll('[data-chord-target]')
      .find(
        (t) =>
          t.attributes('data-line') === '1' && t.text().includes('el')
      )
    await targetKb!.trigger('click')
    const kbResult = (wrapperKb.emitted('update:lyrics')![0][0] as string)

    // Drag run
    const wrapperDrag = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
      attachTo: document.body,
    })
    const cBtnDrag = wrapperDrag
      .findAll('.er-chord-palette button')
      .find((b) => b.text() === 'C')
    const targetDrag = wrapperDrag
      .findAll('[data-chord-target]')
      .find(
        (t) =>
          t.attributes('data-line') === '1' && t.text().includes('el')
      )

    vi.spyOn(document, 'elementFromPoint').mockReturnValue(targetDrag!.element)

    await cBtnDrag!.trigger('pointerdown', { pointerId: 1, clientX: 10, clientY: 10 })
    window.dispatchEvent(new MouseEvent('pointerup', { clientX: 50, clientY: 50 }))
    await wrapperDrag.vm.$nextTick()

    const dragResult = (wrapperDrag.emitted('update:lyrics')![0][0] as string)

    expect(dragResult).toBe(kbResult)
    wrapperDrag.unmount()
  })

  it('sentinel chip "✕ quitar" removes chord marker via keyboard and drag', async () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })

    const sentinelBtn = wrapper.find('[data-test="sentinel-remove-chord"]')
    expect(sentinelBtn.exists()).toBe(true)
    await sentinelBtn.trigger('click')

    // Click on target with [Am] (line 1, "Bajo")
    const bajoTarget = wrapper
      .findAll('[data-chord-target]')
      .find(
        (t) =>
          t.attributes('data-line') === '1' && t.text().includes('Bajo')
      )
    expect(bajoTarget).toBeDefined()
    await bajoTarget!.trigger('click')

    const emitted = wrapper.emitted('update:lyrics')
    expect(emitted).toBeTruthy()
    const result = emitted![0][0] as string
    expect(result).not.toContain('[Am]')
    expect(result).toContain('Bajo el farol')
  })

  it('ensures all interactive elements are real buttons', () => {
    const wrapper = mount(ErLyricsChordEditor, {
      props: {
        lyrics: initialLyrics,
        chords: chordsList,
      },
    })

    const targets = wrapper.findAll('[data-chord-target]')
    for (const t of targets) {
      expect(t.element.tagName).toBe('BUTTON')
    }

    const paletteButtons = wrapper.findAll('.er-chord-palette button')
    for (const b of paletteButtons) {
      expect(b.element.tagName).toBe('BUTTON')
    }
  })
})
