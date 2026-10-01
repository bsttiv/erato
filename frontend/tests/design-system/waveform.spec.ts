import { describe, it, expect } from 'vitest'
import { peaks } from '@/design-system/core/waveform'

describe('peaks (deterministic seeded waveform generator)', () => {
  it('generates an array with length equal to n', () => {
    const res = peaks('take-1', 72)
    expect(res).toHaveLength(72)
  })

  it('is strictly deterministic for a fixed seed', () => {
    const runA = peaks('take-rock-version', 64)
    const runB = peaks('take-rock-version', 64)
    expect(runA).toEqual(runB)
  })

  it('produces different waveforms for different seeds', () => {
    const wave1 = peaks('take-1', 48)
    const wave2 = peaks('take-2', 48)
    expect(wave1).not.toEqual(wave2)
  })

  it('bounds all peak values between 0.12 and 1.0', () => {
    const res = peaks('any-seed-value', 100)
    for (const p of res) {
      expect(p).toBeGreaterThanOrEqual(0.12)
      expect(p).toBeLessThanOrEqual(1.0)
    }
  })

  it('matches the reference LCG numerical output exactly for a test seed', () => {
    const res = peaks('demo', 4)
    expect(res).toHaveLength(4)
    // First value: (3079651 * 1664525 + 1013904223) >>> 0 => 3274017366 / 4294967296 => peak ≈ 0.6538
    expect(res[0]).toBeCloseTo(0.6538, 4)
  })
})
