// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StageLamp from './StageLamp.vue'

describe('stage lamp rendering', () => {
  it('LAMP-013 keeps the default static appearance and ignores poses unless flexible is enabled', () => {
    const staticLamp = mount(StageLamp)
    const flexibleLamp = mount(StageLamp, { props: { flexible: true } })
    const points = [{ x: 0, y: 0 }, { x: 8, y: 80 }, { x: 15, y: 170 }]
    try {
      expect(staticLamp.props()).toEqual({ cord: 176, flexible: false })
      expect(staticLamp.attributes()).toMatchObject({ width: '120', height: '230', viewBox: '0 0 120 230', 'aria-hidden': 'true' })
      expect(staticLamp.find('path').attributes()).toMatchObject({ d: 'M60 0 L60 176', fill: 'none', stroke: '#5a4632', 'stroke-width': '2' })
      expect(staticLamp.find('g path').attributes()).toMatchObject({ d: 'M30 216 L42 178 L78 178 L90 216 Z', fill: '#8a6a3c' })
      expect(staticLamp.find('ellipse').attributes()).toMatchObject({ cx: '60', cy: '216', rx: '30', ry: '6', fill: '#ffd28a' })
      expect(staticLamp.element.style.overflow).toBe('')
      const original = staticLamp.html()
      staticLamp.vm.setPose(points)
      expect(staticLamp.html()).toBe(original)

      flexibleLamp.vm.setPose(points)
      expect(flexibleLamp.element.style.overflow).toBe('visible')
      expect(flexibleLamp.find('path').attributes('d')).toBe('M60 0 L68 80 L75 170')
      expect(flexibleLamp.find('g').attributes('transform')).toBe(`translate(15 -6) rotate(${-Math.atan2(15, 170) * 180 / Math.PI} 60 176)`)
      expect(flexibleLamp.find('g path').attributes('d')).toBe(staticLamp.find('g path').attributes('d'))
      expect(flexibleLamp.find('ellipse').attributes()).toEqual(staticLamp.find('ellipse').attributes())
    } finally {
      staticLamp.unmount()
      flexibleLamp.unmount()
    }
  })
})
