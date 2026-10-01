import { describe, it, expect } from 'vitest'
import { STATUS_OPTIONS, statusLabel } from '@/features/compositions/status'

describe('status utilities', () => {
  it('STATUS_OPTIONS defines idea, in_progress, and ready with Spanish labels', () => {
    expect(STATUS_OPTIONS).toEqual([
      { value: 'idea', label: 'Idea' },
      { value: 'in_progress', label: 'En progreso' },
      { value: 'ready', label: 'Lista' },
    ])
  })

  it('statusLabel maps status values to Spanish human-readable labels', () => {
    expect(statusLabel('idea')).toBe('Idea')
    expect(statusLabel('in_progress')).toBe('En progreso')
    expect(statusLabel('ready')).toBe('Lista')
    expect(statusLabel(undefined)).toBe('Idea')
  })
})
