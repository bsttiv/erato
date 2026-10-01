import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErButton from '@/design-system/components/ErButton.vue'

describe('ErButton component', () => {
  it('renders a native <button type="button"> with default er-btn and er-btn--quiet classes', () => {
    const wrapper = mount(ErButton, {
      slots: { default: 'Click me' },
    })
    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.attributes('type')).toBe('button')
    expect(wrapper.classes()).toContain('er-btn')
    expect(wrapper.classes()).toContain('er-btn--quiet')
    expect(wrapper.text()).toBe('Click me')
  })

  it('supports variants: primary, quiet, ghost, danger', () => {
    const variants = ['primary', 'quiet', 'ghost', 'danger'] as const
    for (const v of variants) {
      const wrapper = mount(ErButton, { props: { variant: v } })
      expect(wrapper.classes()).toContain(`er-btn--${v}`)
    }
  })

  it('supports size="sm" with er-btn--sm class', () => {
    const wrapper = mount(ErButton, { props: { size: 'sm' } })
    expect(wrapper.classes()).toContain('er-btn--sm')
  })

  it('renders icon when icon prop is provided', () => {
    const wrapper = mount(ErButton, {
      props: { icon: 'plus' },
      slots: { default: 'Nueva' },
    })
    expect(wrapper.find('svg.er-ico').exists()).toBe(true)
  })
})
