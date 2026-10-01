import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErBrand from '@/design-system/components/ErBrand.vue'

describe('ErBrand', () => {
  it('renders .er-brand with .er-nav-lamp (aria-hidden) and .er-nav-name', () => {
    const wrapper = mount(ErBrand)
    const brand = wrapper.find('.er-brand')
    expect(brand.exists()).toBe(true)

    const lamp = wrapper.find('.er-nav-lamp')
    expect(lamp.exists()).toBe(true)
    expect(lamp.attributes('aria-hidden')).toBe('true')

    const name = wrapper.find('.er-nav-name')
    expect(name.exists()).toBe(true)
    expect(name.text()).toBe('Erato')
  })

  it('honors custom label prop', () => {
    const wrapper = mount(ErBrand, {
      props: { label: 'Mi Banda' },
    })
    const name = wrapper.find('.er-nav-name')
    expect(name.text()).toBe('Mi Banda')
  })
})
