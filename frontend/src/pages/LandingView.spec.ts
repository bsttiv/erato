// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import LandingView from './LandingView.vue'
import LoginView from './LoginView.vue'
import StageLamp from '../components/atoms/StageLamp.vue'
import SongStatus from '../components/atoms/SongStatus.vue'
import ChordDiagram from '../components/atoms/ChordDiagram.vue'
import ChordHint from '../components/molecules/ChordHint.vue'
import LyricSheet from '../components/molecules/LyricSheet.vue'
import { songChords, takes } from '../data/sample'
import { createMemoryHistory, createRouter } from 'vue-router'
import themeSource from '../../tailwind.theme.js?raw'

const Fretboard = { name: 'Fretboard', props: ['frets'], emits: ['change'], template: '<div />' }
function render(real: Record<string, boolean> = {}) {
  return mount(LandingView, {
    global: {
      stubs: {
        LandingNav: true,
        CompositionPreview: true,
        DemoPlayer: true,
        BandCard: true,
        HistoryList: true,
        ShareLinkBar: true,
        SiteFooter: true,
        Fretboard,
        RouterLink: { template: '<a><slot /></a>' },
        ...real,
      },
    },
  })
}

beforeEach(() => { vi.stubGlobal('matchMedia', () => ({ matches: false })) })
afterEach(() => { vi.unstubAllGlobals() })

describe('landing page', () => {
  it('LAND-014 updates the chord name and notes when a fret changes', async () => {
    const wrapper = render()
    expect(wrapper.text()).toContain('Cmaj7')
    wrapper.findComponent(Fretboard).vm.$emit('change', [0, 3, 1, 0, 2, 0])
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('E7')
    expect(wrapper.text()).toContain('E · G# · B · D')
  })
  it('LAND-020 does not advertise a next chord in Lectura', () => {
    expect(render().text()).not.toContain('Siguiente acorde')
  })
})


describe('landing lamp decoration', () => {
  it('LAMP-010 gives both lamps the existing centered radial glow without a hard starting edge', () => {
    const wrapper = render()
    try {
      const lamps = wrapper.findAllComponents(StageLamp)
      expect(lamps).toHaveLength(2)
      // jsdom cannot paint gradients; pin the real design token and placement instead.
      expect(themeSource).toContain("spot: 'radial-gradient(50% 50% at 50% 50%, rgba(240,164,58,.13), rgba(240,164,58,0) 70%)'")
      for (const [index, lamp] of lamps.entries()) {
        const glow = lamp.element.previousElementSibling!
        expect(glow.classList.contains('bg-spot')).toBe(true)
        expect(glow.classList.contains('h-[800px]')).toBe(true)
        expect(glow.classList.contains('inset-x-[-30%]')).toBe(true)
        expect(glow.classList.contains(index === 0 ? 'top-[-250px]' : 'top-[-230px]')).toBe(true)
        // The 400px radial center lands at y=150/170, beside each shade.
        expect(Number(lamp.props('cord')) + 40).toBe(index === 0 ? 150 : 170)
        expect(glow.getAttribute('aria-hidden')).toBe('true')
      }
    } finally { wrapper.unmount() }
  })

  it('LAMP-012 supplies noninteractive decoration and horizontal overflow containment', () => {
    const wrapper = render()
    try {
      expect(wrapper.classes()).toContain('overflow-x-hidden')
      const lamps = wrapper.findAllComponents(StageLamp)
      expect(lamps).toHaveLength(2)
      for (const lamp of lamps) {
        expect(lamp.classes()).toContain('pointer-events-none')
        expect(lamp.attributes('aria-hidden')).toBe('true')
        const glow = lamp.element.previousElementSibling!
        expect(glow.classList.contains('pointer-events-none')).toBe(true)
        expect(glow.classList.contains('absolute')).toBe(true)
      }
    } finally { wrapper.unmount() }
  })

  it.skip('LAMP-012 clicks controls through lamp/glow and checks horizontal scroll width at narrow/wide viewports: requires real browser layout and hit testing, unavailable in jsdom', () => {})

  it('LAMP-013 keeps the real sign-in lamp static while both landing lamps opt into flexible rendering', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/login', component: LoginView }, { path: '/', component: { template: '<div />' } }, { path: '/registro', component: { template: '<div />' } }] })
    await router.push('/login')
    await router.isReady()
    const signIn = mount(LoginView, { global: { plugins: [router] } })
    const landing = render()
    try {
      expect(signIn.find('h1').text()).toBe('Iniciar sesión')
      const staticLamp = signIn.getComponent(StageLamp)
      expect(staticLamp.props()).toEqual({ cord: 150, flexible: false })
      expect(staticLamp.attributes()).toMatchObject({ width: '120', height: '204', viewBox: '0 0 120 204' })
      expect(staticLamp.find('path').attributes('d')).toBe('M60 0 L60 150')
      expect(staticLamp.find('g path').attributes('d')).toBe('M30 190 L42 152 L78 152 L90 190 Z')
      expect(staticLamp.find('ellipse').attributes('cy')).toBe('190')
      expect(staticLamp.element.parentElement!.classList.contains('bg-lamp')).toBe(true)
      const original = staticLamp.html()
      staticLamp.vm.setPose([{ x: 0, y: 0 }, { x: 20, y: 145 }])
      expect(staticLamp.html()).toBe(original)
      const lamps = landing.findAllComponents(StageLamp)
      expect(lamps.map(lamp => lamp.props())).toEqual([{ cord: 110, flexible: true }, { cord: 130, flexible: true }])
      for (const lamp of lamps) {
        const cord = lamp.props('cord')
        lamp.vm.setPose([{ x: 0, y: 0 }, { x: 20, y: cord - 5 }])
        expect(lamp.find('path').attributes('d')).toBe(`M60 0 L80 ${cord - 5}`)
        expect(lamp.find('g').attributes('transform')).toBe(`translate(20 -5) rotate(${-Math.atan2(20, cord - 5) * 180 / Math.PI} 60 ${cord})`)
      }
    } finally {
      signIn.unmount()
      landing.unmount()
    }
  })
})

describe('landing preview — tests_md/propuesta-landing-app-2026-10-31.md', () => {
  type Wrapper = ReturnType<typeof render>
  const panel = (wrapper: Wrapper) => wrapper.get('.h-\\[248px\\]')
  const tab = (wrapper: Wrapper, label: string) => wrapper.get('[aria-label="Secciones de la composición de ejemplo"]').findAll('button').find(node => node.text() === label)!
  const hinted = (wrapper: Wrapper) => wrapper.findAllComponents(ChordHint).map(hint => hint.props('chord').name)
  async function expectHint(wrapper: Wrapper, chord: ReturnType<Wrapper['get']>, enter: string, leave: string, name: string) {
    await chord.trigger(enter)
    expect(hinted(wrapper)).toEqual([name])
    await chord.trigger(leave)
    expect(hinted(wrapper)).toEqual([])
  }

  it('LAPP-001 shows the real composition header, lyrics and tabs', () => {
    const wrapper = render()
    expect(wrapper.text()).toContain('Noche de otoño')
    expect(wrapper.findComponent(SongStatus).text()).toBe('En progreso')
    expect(wrapper.text()).toContain('Do mayor · 92 bpm · 4/4 · Privada')
    expect(panel(wrapper).findComponent(LyricSheet).text()).toContain('Quédate un rato más')
    expect(wrapper.get('[aria-label="Secciones de la composición de ejemplo"]').findAll('button').map(node => node.text())).toEqual(['Letra', 'Acordes', 'Tablatura', 'Demos'])
  })
  it('LAPP-001B shows each tab in the same fixed panel', async () => {
    const wrapper = render()
    await tab(wrapper, 'Acordes').trigger('click')
    expect(tab(wrapper, 'Acordes').attributes('aria-pressed')).toBe('true')
    expect(panel(wrapper).findAllComponents(ChordDiagram)).toHaveLength(6)
    await tab(wrapper, 'Tablatura').trigger('click')
    expect(panel(wrapper).get('pre').text()).toContain('e|')
    await tab(wrapper, 'Demos').trigger('click')
    expect(panel(wrapper).findAll('li').map(row => row.text())).toEqual(takes.slice(0, 3).map(take => expect.stringContaining(take.title)))
    await tab(wrapper, 'Letra').trigger('click')
    expect(panel(wrapper).findComponent(LyricSheet).exists()).toBe(true)
  })
  it('LAPP-002 shows the exact shape on hero lyrics, and no hint on figures', async () => {
    const wrapper = render()
    const chord = panel(wrapper).get('button')
    await expectHint(wrapper, chord, 'mouseenter', 'mouseleave', 'Dm7')
    await chord.trigger('focus')
    const shape = songChords.find(item => item.name === 'Dm7')!.frets.filter(fret => fret >= 0)
    expect(wrapper.findComponent(ChordHint).props('chord').frets).toEqual(shape)
    await chord.trigger('blur')
    await tab(wrapper, 'Acordes').trigger('click')
    expect(panel(wrapper).findAll('button')).toHaveLength(0)
  })
  it('LAPP-002 shows the hint in Escritura, Lectura and the history', async () => {
    const wrapper = render({ HistoryList: false })
    const named = (text: string) => wrapper.findAll('button').find(node => node.text() === text)!
    await expectHint(wrapper, named('Cmaj7'), 'focus', 'blur', 'Cmaj7')
    const reading = wrapper.get('.animate-roll').get('button')
    await expectHint(wrapper, reading, 'focus', 'blur', reading.text())
    await expectHint(wrapper, wrapper.get('li button'), 'mouseenter', 'mouseleave', wrapper.get('li button').text())
  })
  it('LAPP-003 updates the name, notes and hint with the frets', async () => {
    const wrapper = render()
    wrapper.findComponent(Fretboard).vm.$emit('change', [0, 3, 1, 0, 2, 0])
    await wrapper.vm.$nextTick()
    const chord = wrapper.findAll('button').find(node => node.text() === 'E7')!
    expect(wrapper.text()).toContain('E · G# · B · D')
    await chord.trigger('focus')
    expect(wrapper.findComponent(ChordHint).props('chord').frets).toEqual([0, 3, 1, 0, 2, 0])
    await chord.trigger('blur')
    wrapper.findComponent(Fretboard).vm.$emit('change', [-1, -1, -1, -1, -1, -1])
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('[aria-live="polite"] button')).toHaveLength(0)
  })
  it('LAPP-004 attaches the Lectura hint outside its moving container', async () => {
    const wrapper = render()
    const chord = wrapper.get('.animate-roll').get('button')
    expect(chord.attributes('tabindex')).toBeUndefined()
    await chord.trigger('focus')
    const hint = wrapper.findComponent(ChordHint)
    expect(hint.classes()).toContain('fixed')
    expect(hint.element.parentElement).toBe(document.body)
    await chord.trigger('blur')
  })
  it('LAPP-005 keeps both lamps, no prices and the signup call', () => {
    const wrapper = render()
    const lamps = wrapper.findAllComponents(StageLamp)
    expect(lamps.map(lamp => lamp.props('flexible'))).toEqual([true, true])
    lamps.forEach(lamp => expect(lamp.element.previousElementSibling!.classList).toContain('bg-spot'))
    expect(wrapper.text()).not.toMatch(/precio|\bplan(es)?\b|tarjeta|suscripci|\$\s*\d/i)
    expect(wrapper.text()).toContain('Empieza gratis')
  })
  it('LAPP-006 offers real hints on the demo alternatives', async () => {
    const wrapper = render()
    const alternative = wrapper.findAll('button').find(node => node.text() === 'Gmaj7')!
    await expectHint(wrapper, alternative, 'mouseenter', 'mouseleave', 'Gmaj7')
    await expectHint(wrapper, alternative, 'focus', 'blur', 'Gmaj7')
    expect(wrapper.findComponent({ name: 'DemoPlayer' }).exists() || wrapper.html().includes('demo-player-stub')).toBe(true)
  })
  it('LAPP-010 points every repository link and the credit to the author', () => {
    const wrapper = render({ SiteFooter: false })
    const hrefs = wrapper.findAll('a').map(link => link.attributes('href') || '')
    const repository = hrefs.filter(href => href.includes('github.com'))
    expect(repository.length).toBeGreaterThanOrEqual(2)
    repository.forEach(href => expect(href).toBe('https://github.com/bsttiv/erato'))
    expect(wrapper.findAll('a').find(link => link.text() === 'Bastián Valencia')!.attributes('href')).toBe('https://bsttiv.github.io')
  })
})
