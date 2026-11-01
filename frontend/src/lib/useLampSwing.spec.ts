// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import { useLampSwing } from './useLampSwing'
import { createLamp, PHYSICS_STEP, pushLamp, stepLamp } from './lampPhysics'

function displacedLamp() {
  const lamp = createLamp(110)
  const angle = 16 * Math.PI / 180
  for (const point of lamp.points) {
    point.x = point.previousX = point.y * Math.sin(angle)
    point.y = point.previousY = point.y * Math.cos(angle)
  }
  return lamp
}

function release(fps: number) {
  const lamp = displacedLamp()
  let lowest = 0
  let settledAt = 0
  for (let frame = 1; frame <= fps * 5; frame++) {
    let settled = false
    for (let step = 0; step < 120 / fps; step++) settled = stepLamp(lamp, PHYSICS_STEP)
    lowest = Math.min(lowest, lamp.points.at(-1)!.x)
    if (!settledAt && settled) settledAt = frame / fps
  }
  return { lowest, settledAt }
}

function mediaMatches(matches: (query: string) => boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({ matches: matches(query) }))
}
const Host = defineComponent({
  setup() {
    useLampSwing(ref(null), ref(null))
    return () => h('div')
  },
})

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('lamp swing', () => {
  it('LAND-030 pushes the lamp in the direction the pointer moves', () => {
    const lamp = createLamp(110)
    pushLamp(lamp, 10, 50)
    stepLamp(lamp)
    expect(lamp.points.at(-1)!.x).toBeGreaterThan(0)
    pushLamp(lamp, 10, -100)
    for (let step = 0; step < 30; step++) stepLamp(lamp)
    expect(lamp.points.at(-1)!.x).toBeLessThan(0)
  })
  it('LAND-031 limits the push to 16 degrees', () => {
    for (const direction of [1, -1]) {
      const lamp = createLamp(110)
      for (let step = 0; step < 120; step++) {
        pushLamp(lamp, 10, direction * 900)
        stepLamp(lamp)
      }
      const bob = lamp.points.at(-1)!
      expect(Math.abs(Math.atan2(bob.x, bob.y) * 180 / Math.PI)).toBeLessThanOrEqual(16)
    }
  })
  it('LAND-032 falls freely when the pointer stops pushing', () => {
    const lamp = displacedLamp()
    const initialX = lamp.points.at(-1)!.x
    for (let step = 0; step < 60; step++) stepLamp(lamp)
    expect(lamp.points.at(-1)!.x).toBeLessThan(initialX)
  })
  it.each([60, 30])('LAND-033 passes rest and settles in under 3 s at %i fps', fps => {
    const { lowest, settledAt } = release(fps)
    expect(lowest).toBeLessThan(0)
    expect(settledAt).toBeGreaterThan(0)
    expect(settledAt).toBeLessThan(3)
  })
  it('LAND-034 adds no pointer listener with reduced motion or without hover', () => {
    const listen = vi.spyOn(window, 'addEventListener')
    mediaMatches(query => query.includes('reduce') || query.includes('hover'))
    mount(Host).unmount()
    mediaMatches(() => false)
    mount(Host).unmount()
    expect(listen.mock.calls.filter(([type]) => type === 'pointermove')).toEqual([])
    mediaMatches(query => query.includes('hover'))
    mount(Host).unmount()
    expect(listen.mock.calls.filter(([type]) => type === 'pointermove')).toHaveLength(1)
  })
})

// These tests mount the actual SVG painter: no mocked solver or pose implementation.
import StageLamp from '../components/atoms/StageLamp.vue'

function swingHarness(cord = 110) {
  let now = 0
  let nextFrame = 0
  const frames = new Map<number, FrameRequestCallback>()
  vi.spyOn(performance, 'now').mockImplementation(() => now)
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    frames.set(++nextFrame, callback)
    return nextFrame
  })
  vi.stubGlobal('cancelAnimationFrame', (id: number) => { frames.delete(id) })
  const queries = new Map<string, { matches: boolean; listeners: Set<EventListenerOrEventListenerObject> }>()
  vi.stubGlobal('matchMedia', (query: string) => {
    const state = { matches: query.includes('hover'), listeners: new Set<EventListenerOrEventListenerObject>() }
    queries.set(query, state)
    return {
      get matches() { return state.matches },
      addEventListener: (_type: string, listener: EventListenerOrEventListenerObject) => state.listeners.add(listener),
      removeEventListener: (_type: string, listener: EventListenerOrEventListenerObject) => state.listeners.delete(listener),
    }
  })
  const Component = defineComponent({
    setup() {
      const lamp = ref<InstanceType<typeof StageLamp> | null>(null)
      const light = ref<HTMLElement | null>(null)
      useLampSwing(lamp, light, cord)
      return () => h('div', [h(StageLamp, { ref: lamp, cord, flexible: true }), h('div', { ref: light, 'data-light': '' })])
    },
  })
  const wrapper = mount(Component)
  const svg = wrapper.get('svg').element
  vi.spyOn(svg, 'getBoundingClientRect').mockReturnValue({ left: 100, top: 0, width: 120, height: cord + 54, right: 220, bottom: cord + 54, x: 100, y: 0, toJSON() {} })
  const read = () => {
    const path = wrapper.get('svg > path').attributes('d')!
    const points = [...path.matchAll(/[ML]([\d.e+-]+) ([\d.e+-]+)/g)].map(match => ({ x: Number(match[1]) - 60, y: Number(match[2]) }))
    const transform = wrapper.get('svg > g').attributes('transform') ?? 'translate(0 0)'
    const translation = /translate\(([^ ]+) ([^)]+)\)/.exec(transform)!
    return { points, bob: points.at(-1)!, shade: { x: Number(translation[1]), y: Number(translation[2]) }, glow: (wrapper.get('[data-light]').element as HTMLElement).style.transform }
  }
  const pointer = (x: number, y: number, pointerType = 'mouse') => {
    const event = new MouseEvent('pointermove', { clientX: 160 + x, clientY: y })
    Object.defineProperty(event, 'pointerType', { value: pointerType })
    window.dispatchEvent(event)
  }
  const push = (y = cord + 24, direction = 1, pointerType = 'mouse') => {
    document.documentElement.dispatchEvent(new Event('pointerleave'))
    pointer(-30 * direction, y, pointerType)
    pointer(30 * direction, y, pointerType)
  }
  const advance = (milliseconds = 1000 / 60) => {
    now += milliseconds
    const pending = [...frames.values()]
    frames.clear()
    pending.forEach(callback => callback(now))
  }
  const media = (fragment: string, matches: boolean) => {
    const state = [...queries.entries()].find(([query]) => query.includes(fragment))![1]
    state.matches = matches
    state.listeners.forEach(listener => {
      const event = new Event('change')
      if (typeof listener === 'function') listener(event)
      else listener.handleEvent(event)
    })
  }
  return { wrapper, frames, queries, read, pointer, push, advance, media, cord }
}

function expectHanging(harness: ReturnType<typeof swingHarness>) {
  const pose = harness.read()
  expect(pose.bob).toEqual({ x: 0, y: harness.cord })
  expect(pose.points.every(point => point.x === 0)).toBe(true)
  expect(pose.points[0]).toEqual({ x: 0, y: 0 })
  expect(pose.shade).toEqual({ x: 0, y: 0 })
  expect(pose.glow).toBe('translate3d(0px, 0px, 0)')
}

describe('approved flexible landing lamp interactions', () => {
  it('LAMP-001 routes shade contact rightwards and opposes velocity without resetting position', () => {
    const harness = swingHarness()
    try {
      harness.push()
      harness.advance(1000 / 120)
      const before = harness.read().bob.x
      expect(before).toBeGreaterThan(0)
      harness.push(harness.cord + 24, -1)
      expect(harness.read().bob.x).toBe(before)
      harness.advance(1000 / 120)
      expect(harness.read().bob.x - before).toBeLessThan(before)
    } finally { harness.wrapper.unmount() }
  })

  it('LAMP-002 bends the contacted cord before transferring momentum to the bob without moving the anchor', () => {
    const harness = swingHarness()
    try {
      harness.push(55)
      harness.advance(1000 / 120)
      const first = harness.read()
      expect(first.points[0]).toEqual({ x: 0, y: 0 })
      expect(first.points[5]!.x).toBeGreaterThan(0)
      expect(first.points[5]!.x).toBeGreaterThan(first.bob.x)
      const bend = first.points[5]!.x - first.bob.x / 2
      expect(bend).toBeGreaterThan(0.1)
      for (let i = 0; i < 20; i++) harness.advance(1000 / 120)
      expect(harness.read().bob.x).toBeGreaterThan(first.bob.x)
      expect(harness.read().points[0]).toEqual({ x: 0, y: 0 })
    } finally { harness.wrapper.unmount() }
  })

  it('LAMP-003 continues a damped free swing when the pointer stays stationary beside the lamp', () => {
    const harness = swingHarness()
    try {
      harness.push()
      const positions: number[] = []
      for (let i = 0; i < 180; i++) {
        harness.pointer(30, harness.cord + 24)
        harness.advance()
        positions.push(harness.read().bob.x)
      }
      expect(Math.max(...positions)).toBeGreaterThan(1)
      expect(Math.min(...positions)).toBeLessThan(0)
      expectHanging(harness)
      expect(harness.frames.size).toBe(0)
    } finally { harness.wrapper.unmount() }
  })

  it('LAMP-004 transfers equal cord pushes at different heights with contact-dependent responses', () => {
    const responses = [22, 77].map(height => {
      const harness = swingHarness()
      try {
        harness.push(height)
        for (let i = 0; i < 15; i++) harness.advance()
        const pose = harness.read()
        expect(pose.bob.x).toBeGreaterThan(0)
        expect(pose.points[0]).toEqual({ x: 0, y: 0 })
        expect(pose.points.some((point, i) => Math.abs(point.x - pose.bob.x * i / 10) > 0.01)).toBe(true)
        return pose.bob.x
      } finally { harness.wrapper.unmount() }
    })
    expect(Math.abs(responses[0]! - responses[1]!)).toBeGreaterThan(0.1)
  })

  it('LAMP-005 uses equivalent fixed-step trajectories at 30/60/120 fps and bounds delayed-frame catch-up', () => {
    expect(PHYSICS_STEP).toBe(1 / 120)
    const trajectories = [30, 60, 120].map(fps => {
      const harness = swingHarness()
      try {
        harness.push()
        const samples = []
        for (let i = 1; i <= fps; i++) {
          harness.advance(1000 / fps)
          if (i % (fps / 10) === 0) samples.push(harness.read().bob)
        }
        return samples
      } finally { harness.wrapper.unmount() }
    })
    for (const trajectory of trajectories.slice(1)) {
      trajectory.forEach((bob, i) => {
        expect(Math.abs(bob.x - trajectories[0]![i]!.x)).toBeLessThan(0.5)
        expect(Math.abs(bob.y - trajectories[0]![i]!.y)).toBeLessThan(0.5)
      })
    }
    const reference = swingHarness()
    reference.push()
    reference.advance(1000 / 30)
    const expectedDelayedPoints = reference.read().points
    reference.wrapper.unmount()
    const harness = swingHarness()
    try {
      harness.push()
      harness.advance(2000)
      const pose = harness.read()
      // The capped frame must perform exactly the same work as one 30fps frame.
      expect(pose.points).toEqual(expectedDelayedPoints)
      expect(pose.points.every(point => Number.isFinite(point.x) && Number.isFinite(point.y))).toBe(true)
      expect(Math.abs(Math.atan2(pose.bob.x, pose.bob.y))).toBeLessThanOrEqual(16 * Math.PI / 180)
      for (let i = 0; i < 180; i++) harness.advance()
      expectHanging(harness)
      expect(harness.frames.size).toBe(0)
    } finally { harness.wrapper.unmount() }
  })

  it.each([110, 130])('LAMP-006 restores the exact hanging pose, sleeps and wakes after a fresh push for cord %i', cord => {
    const harness = swingHarness(cord)
    try {
      harness.push()
      harness.advance()
      expect(harness.read().shade.x).not.toBe(0)
      for (let i = 0; i < 240 && harness.frames.size; i++) harness.advance()
      expectHanging(harness)
      expect(harness.frames.size).toBe(0)
      harness.push()
      expect(harness.frames.size).toBe(1)
      harness.advance()
      expect(harness.read().bob.x).toBeGreaterThan(0)
    } finally { harness.wrapper.unmount() }
  })

  it.each(['shade', 'cord'])('LAMP-011 translates the glow by the actual shade displacement after a %s push', contact => {
    const harness = swingHarness()
    try {
      harness.push(contact === 'shade' ? harness.cord + 24 : 55)
      for (let i = 0; i < 12; i++) {
        harness.advance()
        const pose = harness.read()
        expect(pose.shade.x).toBeCloseTo(pose.bob.x, 12)
        expect(pose.shade.y).toBe(pose.bob.y - harness.cord)
        expect(pose.glow).toBe(`translate3d(${pose.shade.x}px, ${pose.shade.y}px, 0)`)
      }
      expect(harness.read().bob.x).not.toBe(0)
    } finally { harness.wrapper.unmount() }
  })

  it('LAMP-020 rejects hybrid-device touch events without creating an impulse or scheduling motion', () => {
    const harness = swingHarness()
    try {
      const initial = harness.read()
      harness.push(harness.cord + 24, 1, 'touch')
      expect(harness.frames.size).toBe(0)
      harness.advance()
      expect(harness.read()).toEqual(initial)
      harness.pointer(30, harness.cord + 24)
      expect(harness.frames.size).toBe(0)
    } finally { harness.wrapper.unmount() }
  })

  it.each(['reduce', 'hover'])('LAMP-021 cancels motion and resets pose when %s disables motion', preference => {
    const harness = swingHarness()
    try {
      harness.push()
      harness.advance()
      expect(harness.read().bob.x).toBeGreaterThan(0)
      harness.media(preference, preference === 'reduce')
      expect(harness.frames.size).toBe(0)
      expectHanging(harness)
      harness.push()
      harness.advance()
      expect(harness.frames.size).toBe(0)
      expectHanging(harness)
    } finally { harness.wrapper.unmount() }
  })

  it('LAMP-022 resumes fresh mouse pushes after restoring preferences without duplicate listeners', () => {
    const active = new Set<EventListenerOrEventListenerObject>()
    const realAdd = window.addEventListener.bind(window)
    const realRemove = window.removeEventListener.bind(window)
    vi.spyOn(window, 'addEventListener').mockImplementation((type, listener, options) => {
      if (type === 'pointermove') active.add(listener)
      realAdd(type, listener, options)
    })
    vi.spyOn(window, 'removeEventListener').mockImplementation((type, listener, options) => {
      if (type === 'pointermove') active.delete(listener)
      realRemove(type, listener, options)
    })
    const harness = swingHarness()
    try {
      for (let cycle = 0; cycle < 3; cycle++) {
        harness.media('reduce', true)
        harness.media('hover', false)
        expect(active.size).toBe(0)
        harness.media('reduce', false)
        harness.media('hover', true)
        expect(active.size).toBe(1)
      }
      harness.push()
      expect(harness.frames.size).toBe(1)
      harness.advance()
      expect(harness.read().bob.x).toBeGreaterThan(0)
    } finally { harness.wrapper.unmount() }
    expect(active.size).toBe(0)
  })

  it('LAMP-023 removes pending frames and all pointer/media listeners on unmount', () => {
    const windowRemove = vi.spyOn(window, 'removeEventListener')
    const documentRemove = vi.spyOn(document.documentElement, 'removeEventListener')
    const harness = swingHarness()
    harness.push()
    harness.advance()
    expect(harness.frames.size).toBe(1)
    windowRemove.mockClear()
    documentRemove.mockClear()
    harness.wrapper.unmount()
    expect(harness.frames.size).toBe(0)
    expect(windowRemove.mock.calls.some(([type]) => type === 'pointermove')).toBe(true)
    expect(documentRemove.mock.calls.some(([type]) => type === 'pointerleave')).toBe(true)
    expect([...harness.queries.values()].every(query => query.listeners.size === 0)).toBe(true)
    harness.push()
    harness.media('reduce', true)
    harness.advance()
    expect(harness.frames.size).toBe(0)
  })
})
