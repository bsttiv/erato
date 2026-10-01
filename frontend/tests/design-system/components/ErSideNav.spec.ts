import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErSideNav from '@/design-system/components/ErSideNav.vue'

describe('ErSideNav component', () => {
  const items = [
    { id: '1', label: 'Bajo el farol', meta: '3 tomas' },
    { id: '2', label: 'Catedral', meta: '1 toma' },
  ]

  it('renders <nav class="er-nav"> with brand, heading and item list', () => {
    const wrapper = mount(ErSideNav, {
      props: {
        brand: 'Erato',
        subtitle: 'cancionero',
        heading: 'composiciones',
        items,
        modelValue: '1',
      },
    })
    expect(wrapper.element.tagName).toBe('NAV')
    expect(wrapper.classes()).toContain('er-nav')
    expect(wrapper.find('.er-nav-name').text()).toBe('Erato')
    expect(wrapper.find('.er-nav-sub').text()).toBe('cancionero')
    expect(wrapper.find('.er-nav-heading').text()).toBe('// composiciones')
    expect(wrapper.findAll('li').length).toBe(2)
  })

  it('marks active item with aria-current="true"', () => {
    const wrapper = mount(ErSideNav, {
      props: {
        items,
        modelValue: '2',
      },
    })
    const buttons = wrapper.findAll('button.er-nav-item')
    expect(buttons[0].attributes('aria-current')).toBeUndefined()
    expect(buttons[1].attributes('aria-current')).toBe('true')
  })

  it('formats item index numbers with pad2 (00, 01)', () => {
    const wrapper = mount(ErSideNav, {
      props: { items },
    })
    const nums = wrapper.findAll('.er-nav-num')
    expect(nums[0].text()).toBe('00')
    expect(nums[1].text()).toBe('01')
  })

  it('emits update:modelValue and select on item click', async () => {
    const wrapper = mount(ErSideNav, {
      props: { items, modelValue: '1' },
    })
    const buttons = wrapper.findAll('button.er-nav-item')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['2'])
    expect(wrapper.emitted('select')?.[0]).toEqual(['2'])
  })
})
