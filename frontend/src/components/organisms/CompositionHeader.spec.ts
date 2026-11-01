// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import CompositionHeader from './CompositionHeader.vue'

const mocks = vi.hoisted(() => ({ state: null as any }))
vi.mock('../../api/compositionPath', async () => {
  const { ref } = await import('vue')
  return { useCompositionPath: () => ref('/canciones/s1') }
})
vi.mock('../../stores/song', () => ({ useSong: () => mocks.state }))

function render(isPublic: boolean) {
  mocks.state = { song: ref({ title: 'Noche' }), isPublic: ref(isPublic) }
  return mount(CompositionHeader, { global: { stubs: {
    Wordmark: true, RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' },
  } } })
}
const tabs = (wrapper: ReturnType<typeof render>) => wrapper.findAll('[aria-label="Secciones de la composición"] a')

describe('composition tabs — tests_md/propuesta-historial-2026-10-31.md', () => {
  it('HVW-001 links the history tab for a member', () => {
    const last = tabs(render(false)).at(-1)!
    expect(last.text()).toBe('Historial')
    expect(last.attributes('href')).toBe('/canciones/s1/historial')
  })
  it('HVW-002 hides the history tab on a public song', () => {
    expect(tabs(render(true)).map(tab => tab.text())).toEqual(['Letra', 'Acordes', 'Tablatura', 'Demos'])
  })
})
