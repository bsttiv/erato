import { describe, expect, it } from 'vitest'
import { createLamp, PHYSICS_STEP, pushLamp, stepLamp } from './lampPhysics'

describe('approved weighted cord physics', () => {
  it('LAMP-001 adds directional momentum and reverses it without teleporting the bob', () => {
    const lamp = createLamp(110)
    pushLamp(lamp, 10, 30)
    const bob = lamp.points.at(-1)!
    expect(bob.x).toBe(0)
    expect(bob.x - bob.previousX).toBeGreaterThan(0)
    stepLamp(lamp)
    const position = { x: bob.x, y: bob.y }
    const incomingVelocity = bob.x - bob.previousX
    expect(incomingVelocity).toBeGreaterThan(0)
    pushLamp(lamp, 10, -10)
    expect({ x: bob.x, y: bob.y }).toEqual(position)
    expect(bob.x - bob.previousX).toBeLessThan(incomingVelocity)
    pushLamp(lamp, 10, -60)
    expect(bob.x - bob.previousX).toBeLessThan(0)
  })

  it('LAMP-002 propagates a local cord impulse through constrained segments with an immovable anchor', () => {
    const lamp = createLamp(110)
    const initial = structuredClone(lamp.points)
    pushLamp(lamp, 5, 60)
    expect(lamp.points[5]!.previousX).toBeLessThan(0)
    lamp.points.forEach((point, i) => {
      if (i !== 5) expect(point).toEqual(initial[i])
    })
    stepLamp(lamp)
    expect(lamp.points[5]!.x).toBeGreaterThan(lamp.points[10]!.x)
    for (let i = 0; i < 30; i++) {
      stepLamp(lamp)
      expect(lamp.points[0]).toEqual(initial[0])
      for (let segment = 1; segment < lamp.points.length; segment++) {
        const a = lamp.points[segment - 1]!
        const b = lamp.points[segment]!
        expect(Math.abs(Math.hypot(a.x - b.x, a.y - b.y) - 11)).toBeLessThan(0.5)
      }
    }
    expect(lamp.points[10]!.x).toBeGreaterThan(0)
  })

  it.each([110, 130])('LAMP-006 settles every particle and previous position exactly for the %i cord', length => {
    const lamp = createLamp(length)
    const initial = structuredClone(lamp.points)
    pushLamp(lamp, 10, 60)
    let settled = false
    for (let i = 0; i < 120 * 5 && !settled; i++) settled = stepLamp(lamp, PHYSICS_STEP)
    expect(settled).toBe(true)
    expect(lamp.points).toEqual(initial)
    pushLamp(lamp, 10, 60)
    expect(stepLamp(lamp)).toBe(false)
    expect(lamp.points[10]!.x).toBeGreaterThan(0)
  })
})
