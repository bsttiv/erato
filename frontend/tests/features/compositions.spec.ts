import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CompositionDetailView from '@/features/compositions/CompositionDetailView.vue'
import type { CompositionResponse } from '@/api/compositions'

describe('Compositions feature views', () => {
  const sampleComposition: CompositionResponse = {
    id: 'comp-1',
    title: 'Bajo el farol',
    slug: 'bajo-el-farol',
    owner_id: 'user-1',
    visibility: 'private',
    is_public: false,
    todos: [],
    members: [],
    demos: [],
    sections: {
      chords: {
        frets: [-1, 3, 2, 0, 1, 0],
        instrument: 'guitar',
      },
      tab: {
        columns: [['0', '', '', '', '', '']],
      },
      lyrics: {
        text: '[Am7]Bajo el farol...',
      },
      todos: {
        items: [{ id: 't1', text: 'Mezclar demo', done: false }],
      },
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_role: 'viewer',
  }

  it('hides or disables editing controls when user role is viewer', () => {
    const wrapper = mount(CompositionDetailView, {
      props: {
        composition: {
          ...sampleComposition,
          user_role: 'viewer',
        },
      },
    })

    // ChordEditor editable should be false
    const chordEditor = wrapper.findComponent({ name: 'ErChordEditor' })
    expect(chordEditor.exists()).toBe(true)
    expect(chordEditor.props('editable')).toBe(false)

    // Save/edit buttons should be hidden for viewer
    const saveButtons = wrapper.findAll('.er-save-btn')
    expect(saveButtons.length).toBe(0)

    // Role badge indicates viewer
    expect(wrapper.find('.er-role-tag').text()).toContain('Lector')
  })

  it('enables editing controls when user role is editor or owner', () => {
    const wrapper = mount(CompositionDetailView, {
      props: {
        composition: {
          ...sampleComposition,
          user_role: 'editor',
        },
      },
    })

    const chordEditor = wrapper.findComponent({ name: 'ErChordEditor' })
    expect(chordEditor.exists()).toBe(true)
    expect(chordEditor.props('editable')).toBe(true)

    // Save buttons or editable controls exist
    expect(wrapper.find('.er-save-btn').exists()).toBe(true)
    expect(wrapper.find('.er-role-tag').text()).toContain('Editor')
  })
})
