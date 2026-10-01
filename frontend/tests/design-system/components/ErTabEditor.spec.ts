import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErTabEditor from '@/design-system/components/ErTabEditor.vue'
import { tabToText } from '@/design-system/core/tab'

describe('ErTabEditor component', () => {
  it('renders tab editor with bar, grid, string names, and hint', () => {
    const wrapper = mount(ErTabEditor, {
      props: {
        title: 'Intro riff',
        columns: 4,
      },
    })
    expect(wrapper.classes()).toContain('er-tab')
    expect(wrapper.classes()).toContain('er-panel')
    expect(wrapper.find('.er-tab-bar').text()).toContain('// Intro riff')
    expect(wrapper.find('.er-tab-grid').exists()).toBe(true)
    expect(wrapper.find('.er-tab-names').text()).toContain('eBGDAE')
    expect(wrapper.find('.er-tab-hint').exists()).toBe(true)
  })

  it('renders columns and responds to keyboard events via useTabKeyboard', async () => {
    const initialCols = [
      ['', '', '', '', '', ''],
      ['', '', '', '', '', ''],
    ]
    const wrapper = mount(ErTabEditor, {
      props: {
        modelValue: initialCols,
      },
    })
    const grid = wrapper.find('.er-tab-grid')
    expect(grid.exists()).toBe(true)

    // Type '7'
    await grid.trigger('keydown', { key: '7' })

    const cells = wrapper.findAll('.er-tab-cell')
    expect(cells[0].text()).toBe('7')

    // Exported text with tabToText contains 7
    const emitted = (wrapper.emitted('update:modelValue')?.[0]?.[0] || wrapper.emitted('change')?.[0]?.[0]) as any
    expect(emitted).toBeDefined()
    const text = tabToText(emitted)
    expect(text).toContain('7')
  })

  it('inserts bar line and 8 tiempos buttons work', async () => {
    const wrapper = mount(ErTabEditor, {
      props: {
        columns: 2,
      },
    })
    const buttons = wrapper.findAll('.er-tab-bar button')
    expect(buttons.length).toBe(2)

    // Click "compás" button
    await buttons[0].trigger('click')
    expect(wrapper.findAll('.er-tab-barline').length).toBe(1)

    // Click "8 tiempos" button
    await buttons[1].trigger('click')
    expect(wrapper.findAll('.er-tab-col').length).toBeGreaterThanOrEqual(10)
  })
})
