import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErDemoPlayer from '@/design-system/components/ErDemoPlayer.vue'
import type { DemoTake } from '@design-system/components'

describe('ErDemoPlayer component', () => {
  const sampleTakes: DemoTake[] = [
    {
      id: 'take-1',
      title: 'Toma acústica',
      date: 'hace 2 días',
      note: 'afinación en Re',
      duration: 120,
      comments: [
        { t: 30, author: 'Sofi', text: 'Entrar con más fuerza acá' },
      ],
    },
    {
      id: 'take-2',
      title: 'Banda completa',
      duration: 180,
    },
  ]

  it('renders "Aún no hay demos." when takes array is empty', () => {
    const wrapper = mount(ErDemoPlayer, {
      props: { takes: [] },
    })
    expect(wrapper.classes()).toContain('er-player')
    expect(wrapper.text()).toContain('Aún no hay demos.')
  })

  it('renders takes list and current take with waveform and comments', () => {
    const wrapper = mount(ErDemoPlayer, {
      props: {
        takes: sampleTakes,
      },
    })
    expect(wrapper.find('.er-takes').exists()).toBe(true)
    expect(wrapper.findAll('.er-take').length).toBe(2)
    expect(wrapper.find('.er-now-title').text()).toBe('Toma acústica')

    // 72 waveform bars rendered via SVG
    const bars = wrapper.findAll('.er-wave-bar')
    expect(bars.length).toBe(72)

    // Comment pin and list
    expect(wrapper.find('.er-pin').exists()).toBe(true)
    expect(wrapper.find('.er-comment').text()).toContain('Sofi')
    expect(wrapper.find('.er-comment').text()).toContain('Entrar con más fuerza acá')
  })

  it('allows adding a comment via compose input', async () => {
    const wrapper = mount(ErDemoPlayer, {
      props: {
        takes: sampleTakes,
        author: 'Nico',
      },
    })
    const input = wrapper.find('.er-compose input')
    await input.setValue('Revisar puente')

    const button = wrapper.find('.er-compose button')
    await button.trigger('click')

    expect(wrapper.emitted('comment')?.[0]).toBeDefined()
    const [takeId, comment] = wrapper.emitted('comment')![0] as [string, any]
    expect(takeId).toBe('take-1')
    expect(comment.text).toBe('Revisar puente')
    expect(comment.author).toBe('Nico')
  })
})
