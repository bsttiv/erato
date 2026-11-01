// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SongStatus from './SongStatus.vue'
import theme from '../../../tailwind.theme.js'

describe('SongStatus — tests_md/propuesta-editor-acordes-2026-10-31.md', () => {
  it.each([
    ['idea', 'Idea', 'status-idea', '#c9a4ff'],
    ['in_progress', 'En progreso', 'status-progress', '#f2d14e'],
    ['ready', 'Lista', 'status-ready', '#7fd08a'],
  ])('STA-001 shows %s with its label and color', (status, label, token, color) => {
    const wrapper = mount(SongStatus, { props: { status } })
    expect(wrapper.text()).toBe(label)
    expect(wrapper.classes()).toContain(`text-${token}`)
    expect(wrapper.get('[aria-hidden="true"]').classes()).toContain(`bg-${token}`)
    expect(theme.colors.status[token.replace('status-', '') as 'idea']).toBe(color)
  })
  it.each(['archived', '', null, undefined])('STA-002 shows nothing for status %s', status => {
    expect(mount(SongStatus, { props: { status } }).find('span').exists()).toBe(false)
  })
})
