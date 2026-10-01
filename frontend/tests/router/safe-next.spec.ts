import { describe, it, expect } from 'vitest'
import { safeNextPath } from '@/router/safeNext'

describe('safeNextPath', () => {
  it('accepts internal absolute paths with query and hash', () => {
    expect(safeNextPath('/invite/abc')).toBe('/invite/abc')
    expect(safeNextPath('/compositions/1?tab=x#y')).toBe('/compositions/1?tab=x#y')
  })

  it('falls back to / for missing or non-string values', () => {
    expect(safeNextPath(undefined)).toBe('/')
    expect(safeNextPath(null)).toBe('/')
    expect(safeNextPath('')).toBe('/')
    expect(safeNextPath(['/a', '/b'])).toBe('/')
  })

  it('rejects external, protocol-relative and backslash targets', () => {
    expect(safeNextPath('https://evil.com')).toBe('/')
    expect(safeNextPath('//evil.com')).toBe('/')
    expect(safeNextPath('/\\evil.com')).toBe('/')
    expect(safeNextPath('javascript:alert(1)')).toBe('/')
    expect(safeNextPath('invite/abc')).toBe('/')
  })
})
