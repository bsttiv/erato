import type { CompositionStatus } from '@/api/compositions'
import type { SegmentedOption } from '@/design-system'

export const STATUS_OPTIONS: SegmentedOption[] = [
  { value: 'idea', label: 'Idea' },
  { value: 'in_progress', label: 'En progreso' },
  { value: 'ready', label: 'Lista' },
]

export function statusLabel(status?: CompositionStatus | string | null): string {
  switch (status) {
    case 'in_progress':
      return 'En progreso'
    case 'ready':
      return 'Lista'
    case 'idea':
    default:
      return 'Idea'
  }
}
