// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UserInitial from './UserInitial.vue'

describe('UserInitial — tests_md/propuesta-landing-app-2026-10-31.md', () => {
  it('LAPP-020 shows one uppercase initial in a hidden decorative circle', () => {
    const wrapper = mount(UserInitial, { props: { displayName: 'ana rojas', username: 'ana' } })
    expect(wrapper.text()).toBe('A')
    expect(wrapper.classes()).toContain('avatar')
    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })
  it.each(['', '   ', undefined])('LAPP-021 falls back to the username for display name %j', displayName => {
    expect(mount(UserInitial, { props: { displayName, username: 'tomas' } }).text()).toBe('T')
  })
})
