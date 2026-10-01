import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErTag from '@/design-system/components/ErTag.vue'

describe('ErTag component', () => {
  it('renders a <span> with default er-tag class and slot content', () => {
    const wrapper = mount(ErTag, {
      slots: { default: 'Borrador' },
    })
    expect(wrapper.element.tagName).toBe('SPAN')
    expect(wrapper.classes()).toContain('er-tag')
    expect(wrapper.text()).toBe('Borrador')
  })

  it('applies tone classes for non-neutral tones (amber, ember, wine, moss)', () => {
    const tones = ['amber', 'ember', 'wine', 'moss'] as const
    for (const tone of tones) {
      const wrapper = mount(ErTag, { props: { tone } })
      expect(wrapper.classes()).toContain(`er-tag--${tone}`)
    }
  })

  it('renders dot indicator when dot prop is true', () => {
    const wrapper = mount(ErTag, { props: { dot: true } })
    const dot = wrapper.find('.er-tag-dot')
    expect(dot.exists()).toBe(true)
    expect(dot.attributes('aria-hidden')).toBe('true')
  })
})
