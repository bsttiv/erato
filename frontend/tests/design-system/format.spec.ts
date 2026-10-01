import { describe, it, expect } from 'vitest'
import { formatDate } from '@/design-system/core/format'

describe('formatDate', () => {
  it('formats valid ISO date string into day, month prefix, and year', () => {
    const formatted = formatDate('2026-10-01T12:00:00Z')
    // Matches e.g. "1 oct 2026" or "1 oct. 2026"
    expect(formatted).toMatch(/1\s+oct\.?\s+2026/i)
  })

  it('returns empty string for null, undefined, or empty string', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDate(undefined)).toBe('')
    expect(formatDate('')).toBe('')
  })

  it('returns raw string for invalid date input, never "Invalid Date"', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date')
    expect(formatDate('invalid')).not.toContain('Invalid')
  })
})
