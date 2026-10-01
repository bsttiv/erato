import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useAutoScroll } from '@/design-system/composables/useAutoScroll'

describe('useAutoScroll composable', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initializes with default playing=false, speed=24, and max=false', () => {
    const box = ref<HTMLElement | null>(null)
    const { playing, speed, max } = useAutoScroll(box)

    expect(playing.value).toBe(false)
    expect(speed.value).toBe(24)
    expect(max.value).toBe(false)
  })

  it('exits fullscreen (max=false) when Escape key is pressed', () => {
    const box = ref<HTMLElement | null>(null)
    const { max, toggleMax } = useAutoScroll(box)

    expect(max.value).toBe(false)
    toggleMax()
    expect(max.value).toBe(true)

    // Dispatch Escape key event on window
    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' })
    window.dispatchEvent(escEvent)

    expect(max.value).toBe(false)
  })

  it('starts and stops autoscroll via togglePlay', () => {
    const fakeEl = {
      scrollTop: 0,
      clientHeight: 200,
      scrollHeight: 1000,
    } as unknown as HTMLElement

    const box = ref<HTMLElement | null>(fakeEl)
    const { playing, togglePlay } = useAutoScroll(box)

    togglePlay()
    expect(playing.value).toBe(true)

    togglePlay()
    expect(playing.value).toBe(false)
  })

  it('resets scroll to top if already at the end when starting play', () => {
    const fakeEl = {
      scrollTop: 800,
      clientHeight: 200,
      scrollHeight: 1000,
    } as unknown as HTMLElement

    const box = ref<HTMLElement | null>(fakeEl)
    const { playing, togglePlay } = useAutoScroll(box)
    togglePlay()
    expect(fakeEl.scrollTop).toBe(0)
    expect(playing.value).toBe(true)
  })

  it('does not spawn duplicate rAF loops when speed changes during playback', async () => {
    let frameCount = 0
    const cancelSpy = vi.spyOn(window, 'cancelAnimationFrame')
    const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => ++frameCount)

    const fakeEl = {
      scrollTop: 0,
      clientHeight: 200,
      scrollHeight: 1000,
    } as unknown as HTMLElement

    const box = ref<HTMLElement | null>(fakeEl)
    const { playing, speed, togglePlay } = useAutoScroll(box)

    togglePlay() // playing.value = true
    await Promise.resolve()
    const callsAfterPlay = rafSpy.mock.calls.length
    expect(callsAfterPlay).toBe(1)

    // Changing speed while playing must not schedule an extra concurrent rAF loop
    speed.value = 48
    await Promise.resolve()
    expect(rafSpy.mock.calls.length).toBe(callsAfterPlay)

    // Pausing must cancel the running animation frame
    togglePlay() // playing.value = false
    await Promise.resolve()
    expect(cancelSpy).toHaveBeenCalled()
    expect(playing.value).toBe(false)
  })
})
