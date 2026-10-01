import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LyricsSection from '@/features/compositions/LyricsSection.vue'
import ErLyricsViewer from '@/design-system/components/ErLyricsViewer.vue'
import ErLyricsChordEditor from '@/design-system/components/ErLyricsChordEditor.vue'

describe('LyricsSection.vue', () => {
  const sampleLyrics = '# Coro\n[Am]Bajo el farol\n[C]de la esquina\n'
  const sampleChords = ['Am', 'C', 'G']

  it('in read mode, renders ErLyricsViewer with auto-scroll and title', () => {
    const wrapper = mount(LyricsSection, {
      props: {
        lyrics: sampleLyrics,
        chords: sampleChords,
        editable: true,
      },
    })

    expect(wrapper.findComponent(ErLyricsViewer).exists()).toBe(true)
    expect(wrapper.findComponent(ErLyricsChordEditor).exists()).toBe(false)
  })

  it('renders "Editar acordes" toggle button for authorized editors', async () => {
    const wrapper = mount(LyricsSection, {
      props: {
        lyrics: sampleLyrics,
        chords: sampleChords,
        editable: true,
      },
    })

    const toggleBtn = wrapper.find('[data-test="toggle-lyrics-edit-btn"]')
    expect(toggleBtn.exists()).toBe(true)
    expect(toggleBtn.text().toLowerCase()).toContain('editar acordes')

    // Click toggle to enter edit mode
    await toggleBtn.trigger('click')

    expect(wrapper.findComponent(ErLyricsChordEditor).exists()).toBe(true)
    expect(wrapper.findComponent(ErLyricsViewer).exists()).toBe(false)
    expect(toggleBtn.text().toLowerCase()).toContain('ver letra')
  })

  it('hides edit toggle completely for read-only visitors', () => {
    const wrapper = mount(LyricsSection, {
      props: {
        lyrics: sampleLyrics,
        chords: sampleChords,
        editable: false,
      },
    })

    expect(wrapper.find('[data-test="toggle-lyrics-edit-btn"]').exists()).toBe(false)
    expect(wrapper.findComponent(ErLyricsViewer).exists()).toBe(true)
    expect(wrapper.findComponent(ErLyricsChordEditor).exists()).toBe(false)
  })

  it('emits update:lyrics when chords are edited in ErLyricsChordEditor', async () => {
    const wrapper = mount(LyricsSection, {
      props: {
        lyrics: sampleLyrics,
        chords: sampleChords,
        editable: true,
      },
    })

    // Switch to edit mode
    await wrapper.find('[data-test="toggle-lyrics-edit-btn"]').trigger('click')

    const editor = wrapper.findComponent(ErLyricsChordEditor)
    expect(editor.exists()).toBe(true)

    const updatedContent = '# Coro\n[G]Bajo el farol\n[C]de la esquina\n'
    await editor.vm.$emit('update:lyrics', updatedContent)

    expect(wrapper.emitted('update:lyrics')).toBeTruthy()
    expect(wrapper.emitted('update:lyrics')![0][0]).toBe(updatedContent)
  })

  describe('text editing mode', () => {
    function mountEditable(editable = true) {
      return mount(LyricsSection, {
        props: { lyrics: sampleLyrics, chords: sampleChords, editable },
      })
    }

    it('shows the textarea with the current lyrics on "Editar letra"', async () => {
      const wrapper = mountEditable()
      const btn = wrapper.find('[data-test="edit-lyrics-text-btn"]')
      expect(btn.text()).toBe('Editar letra')
      await btn.trigger('click')

      const textarea = wrapper.find('[data-test="lyrics-textarea"]')
      expect(textarea.exists()).toBe(true)
      expect(textarea.classes()).toContain('er-textarea')
      expect(textarea.attributes('aria-label')).toBe('Letra')
      expect((textarea.element as HTMLTextAreaElement).value).toBe(sampleLyrics)
      expect(wrapper.findComponent(ErLyricsViewer).exists()).toBe(false)
      expect(wrapper.findComponent(ErLyricsChordEditor).exists()).toBe(false)
      expect(btn.text()).toBe('Ver letra')
    })

    it('emits update:lyrics, update:modelValue and change on every input', async () => {
      const wrapper = mountEditable()
      await wrapper.find('[data-test="edit-lyrics-text-btn"]').trigger('click')
      await wrapper.find('[data-test="lyrics-textarea"]').setValue('# Verso\n[Dm]Nueva letra')

      for (const evt of ['update:lyrics', 'update:modelValue', 'change']) {
        expect(wrapper.emitted(evt)![0][0]).toBe('# Verso\n[Dm]Nueva letra')
      }
    })

    it('clicking the active button returns to the viewer', async () => {
      const wrapper = mountEditable()
      const btn = wrapper.find('[data-test="edit-lyrics-text-btn"]')
      await btn.trigger('click')
      await btn.trigger('click')
      expect(wrapper.find('[data-test="lyrics-textarea"]').exists()).toBe(false)
      expect(wrapper.findComponent(ErLyricsViewer).exists()).toBe(true)
    })

    it('switching between text and chord modes keeps one mode active', async () => {
      const wrapper = mountEditable()
      await wrapper.find('[data-test="edit-lyrics-text-btn"]').trigger('click')
      await wrapper.find('[data-test="toggle-lyrics-edit-btn"]').trigger('click')
      expect(wrapper.find('[data-test="lyrics-textarea"]').exists()).toBe(false)
      expect(wrapper.findComponent(ErLyricsChordEditor).exists()).toBe(true)
    })

    it('does not render the textarea or its button when not editable', () => {
      const wrapper = mountEditable(false)
      expect(wrapper.find('[data-test="edit-lyrics-text-btn"]').exists()).toBe(false)
      expect(wrapper.find('[data-test="lyrics-textarea"]').exists()).toBe(false)
    })
  })
})
