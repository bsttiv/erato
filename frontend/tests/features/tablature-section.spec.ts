import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TablatureSection from '@/features/compositions/TablatureSection.vue'
import ErTabEditor from '@/design-system/components/ErTabEditor.vue'
import type { TabEntry } from '@/design-system/core/tab'

describe('TablatureSection.vue', () => {
  const sampleTabs: TabEntry[] = [
    {
      id: 'tab-1',
      title: 'Riff intro',
      strings: 6,
      columns: [['0', '', '', '', '', ''], '|', ['', '1', '', '', '', '']],
    },
    {
      id: 'tab-2',
      title: 'Solo',
      strings: 6,
      columns: [['', '', '12', '', '', '']],
    },
  ]

  it('renders tab strip with all tabs and a button to add a tab', () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    const buttons = wrapper.findAll('.er-tabs-strip button, .er-seg-opt')
    const titles = buttons.map((b) => b.text())
    expect(titles).toContain('Riff intro')
    expect(titles).toContain('Solo')

    const addBtn = wrapper.find('[data-test="add-tab-btn"]')
    expect(addBtn.exists()).toBe(true)
  })

  it('highlights active tab with aria-selected="true"', () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    const activeTab = wrapper.find('[aria-selected="true"]')
    expect(activeTab.exists()).toBe(true)
    expect(activeTab.text()).toContain('Riff intro')
  })

  it('switches active tab when clicked and remounts ErTabEditor with switched columns', async () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    // Find tab for 'Solo'
    const tabButtons = wrapper.findAll('.er-seg-opt, .er-tabs-strip button')
    const soloBtn = tabButtons.find((b) => b.text().includes('Solo'))
    expect(soloBtn).toBeDefined()
    await soloBtn!.trigger('click')

    // Active tab is now Solo
    const activeTab = wrapper.find('[aria-selected="true"]')
    expect(activeTab.text()).toContain('Solo')

    // Editor should be mounted with Solo's columns
    const editor = wrapper.findComponent(ErTabEditor)
    expect(editor.exists()).toBe(true)
    expect(editor.props('modelValue')).toEqual(sampleTabs[1].columns)
  })

  it('allows user to rename active tab inline', async () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    const renameBtn = wrapper.find('[data-test="rename-tab-btn"]')
    expect(renameBtn.exists()).toBe(true)
    await renameBtn.trigger('click')

    const input = wrapper.find('[data-test="rename-tab-input"]')
    expect(input.exists()).toBe(true)
    await input.setValue('Intro acustica')

    const saveBtn = wrapper.find('[data-test="save-rename-btn"]')
    await saveBtn.trigger('click')

    const emitted = wrapper.emitted('update:tabs')
    expect(emitted).toBeTruthy()
    const updatedTabs = emitted![0][0] as TabEntry[]
    expect(updatedTabs[0].title).toBe('Intro acustica')
  })

  it('allows user to delete active tab after confirmation', async () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    const deleteBtn = wrapper.find('[data-test="delete-tab-btn"]')
    expect(deleteBtn.exists()).toBe(true)
    await deleteBtn.trigger('click')

    // Confirm button appears
    const confirmBtn = wrapper.find('[data-test="confirm-delete-btn"]')
    expect(confirmBtn.exists()).toBe(true)
    await confirmBtn.trigger('click')

    const emitted = wrapper.emitted('update:tabs')
    expect(emitted).toBeTruthy()
    const updatedTabs = emitted![0][0] as TabEntry[]
    expect(updatedTabs.length).toBe(1)
    expect(updatedTabs[0].id).toBe('tab-2')
  })

  it('emits update:tabs when columns are updated in ErTabEditor', async () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: true,
      },
    })

    const editor = wrapper.findComponent(ErTabEditor)
    const newColumns = [['3', '', '', '', '', '']]
    await editor.vm.$emit('update:modelValue', newColumns)

    const emitted = wrapper.emitted('update:tabs')
    expect(emitted).toBeTruthy()
    const updatedTabs = emitted![0][0] as TabEntry[]
    expect(updatedTabs[0].columns).toEqual(newColumns)
  })

  it('renders ErTabEditor with readonly attribute and hides tab manipulation in read-only mode', () => {
    const wrapper = mount(TablatureSection, {
      props: {
        tabs: sampleTabs,
        editable: false,
      },
    })

    const addBtn = wrapper.find('[data-test="add-tab-btn"]')
    expect(addBtn.exists()).toBe(false)

    const renameBtn = wrapper.find('[data-test="rename-tab-btn"]')
    expect(renameBtn.exists()).toBe(false)

    const deleteBtn = wrapper.find('[data-test="delete-tab-btn"]')
    expect(deleteBtn.exists()).toBe(false)

    const editor = wrapper.findComponent(ErTabEditor)
    expect(editor.props('readonly')).toBe(true)
  })

  it('rename and delete buttons render plain Spanish text without emoji or glyphs', () => {
    const wrapper = mount(TablatureSection, {
      props: { tabs: sampleTabs, editable: true },
    })

    const rename = wrapper.find('[data-test="rename-tab-btn"]')
    const del = wrapper.find('[data-test="delete-tab-btn"]')
    expect(rename.text()).toBe('Renombrar')
    expect(del.text()).toBe('Borrar')
    for (const btn of [rename, del]) {
      expect(btn.text()).not.toMatch(/\p{Extended_Pictographic}/u)
      expect(btn.text()).not.toMatch(/[\u2700-\u27BF]/u)
    }
  })
})
