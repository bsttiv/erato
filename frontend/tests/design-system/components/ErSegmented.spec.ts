import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErSegmented from '@/design-system/components/ErSegmented.vue'

describe('ErSegmented component', () => {
  const options = [
    { value: 'guitar', label: 'guitarra' },
    { value: 'piano', label: 'piano' },
  ]

  it('renders a role="group" container with er-seg class', () => {
    const wrapper = mount(ErSegmented, {
      props: {
        modelValue: 'guitar',
        options,
        label: 'Instrumento',
      },
    })
    expect(wrapper.classes()).toContain('er-seg')
    expect(wrapper.attributes('role')).toBe('group')
    expect(wrapper.attributes('aria-label')).toBe('Instrumento')
  })

  it('renders option buttons with er-seg-opt and aria-pressed attributes', () => {
    const wrapper = mount(ErSegmented, {
      props: {
        modelValue: 'guitar',
        options,
      },
    })
    const buttons = wrapper.findAll('button.er-seg-opt')
    expect(buttons.length).toBe(2)
    expect(buttons[0].attributes('aria-pressed')).toBe('true')
    expect(buttons[1].attributes('aria-pressed')).toBe('false')
  })

  it('emits update:modelValue on click', async () => {
    const wrapper = mount(ErSegmented, {
      props: {
        modelValue: 'guitar',
        options,
      },
    })
    const buttons = wrapper.findAll('button.er-seg-opt')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['piano'])
  })
})
