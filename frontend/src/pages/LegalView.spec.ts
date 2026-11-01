// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import LegalView from './LegalView.vue'

const render = () => mount(LegalView, { global: { stubs: { Wordmark: true, RouterLink: { template: '<a><slot /></a>' } } } })

describe('legal page — tests_md/propuesta-landing-app-2026-10-31.md', () => {
  it('LAPP-011 holds both sections and links to them', () => {
    const wrapper = render()
    expect(wrapper.get('h1').text()).toBe('Términos de servicio y Política de privacidad')
    expect(wrapper.find('section#terminos').exists()).toBe(true)
    expect(wrapper.find('section#privacidad').exists()).toBe(true)
    expect(wrapper.find('a[href="#terminos"]').exists()).toBe(true)
    expect(wrapper.find('a[href="#privacidad"]').exists()).toBe(true)
  })
  it('LAPP-012 describes the real service and its contact details', () => {
    const text = render().text()
    for (const fact of ['cuenta', 'sesiones', 'composiciones', 'Cloudinary', 'MongoDB', 'Vercel', 'AGPL-3.0']) expect(text).toContain(fact)
    expect(text).toContain('Bastián Valencia')
    expect(text).toContain('bastian.valencia@ug.uchile.cl')
    expect(text).not.toMatch(/\[[^\]]+\]|\bChile\b|Santiago|jurisdicci|tribunal/i)
  })
})
