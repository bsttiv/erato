import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErIcon from '@/design-system/components/ErIcon.vue'

describe('ErIcon component', () => {
  it('renders svg with er-ico class, viewBox 0 0 16 16 and aria-hidden="true"', () => {
    const wrapper = mount(ErIcon, {
      props: { name: 'plus' },
    })
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    expect(svg.classes()).toContain('er-ico')
    expect(svg.attributes('viewBox')).toBe('0 0 16 16')
    expect(svg.attributes('aria-hidden')).toBe('true')
  })

  it('renders play icon filled and others with fill="none"', () => {
    const playWrapper = mount(ErIcon, { props: { name: 'play' } })
    expect(playWrapper.find('svg').attributes('fill')).toBe('currentColor')

    const xWrapper = mount(ErIcon, { props: { name: 'x' } })
    expect(xWrapper.find('svg').attributes('fill')).toBe('none')
  })

  it('applies stroke-width 2.25 for pause icon and 1.5 for others', () => {
    const pauseWrapper = mount(ErIcon, { props: { name: 'pause' } })
    expect(pauseWrapper.find('svg').attributes('stroke-width')).toBe('2.25')

    const checkWrapper = mount(ErIcon, { props: { name: 'check' } })
    expect(checkWrapper.find('svg').attributes('stroke-width')).toBe('1.5')
  })
})
