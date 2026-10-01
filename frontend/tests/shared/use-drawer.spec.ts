import { describe, it, expect } from 'vitest'
import { useDrawer } from '@/shared/useDrawer'

describe('useDrawer', () => {
  it('starts closed by default', () => {
    const drawer = useDrawer()
    expect(drawer.open.value).toBe(false)
  })

  it('toggle flips open state', () => {
    const drawer = useDrawer()
    drawer.toggle()
    expect(drawer.open.value).toBe(true)
    drawer.toggle()
    expect(drawer.open.value).toBe(false)
  })

  it('close sets open to false', () => {
    const drawer = useDrawer()
    drawer.open.value = true
    drawer.close()
    expect(drawer.open.value).toBe(false)
  })
})
