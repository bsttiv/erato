import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useTakePlayback } from '@/design-system/composables/useTakePlayback'
import type { DemoTake } from '@design-system/components'

describe('useTakePlayback composable', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('runs fallback timer when no audio src is provided', () => {
    const take = ref<DemoTake>({
      id: 'take-1',
      title: 'Take acústica',
      duration: 10,
    })
    const audio = ref<HTMLAudioElement | null>(null)
    const { currentTime, playing, togglePlay } = useTakePlayback(take, audio)

    expect(currentTime.value).toBe(0)
    expect(playing.value).toBe(false)

    // Start playback
    togglePlay()
    expect(playing.value).toBe(true)

    // Advance 500ms
    vi.advanceTimersByTime(500)
    expect(currentTime.value).toBeGreaterThan(0.4)
    expect(currentTime.value).toBeLessThanOrEqual(0.6)

    // Pause
    togglePlay()
    expect(playing.value).toBe(false)
  })

  it('clamps seeking within [0, duration] and updates audio element if present', () => {
    const take = ref<DemoTake>({
      id: 'take-2',
      title: 'Demo',
      duration: 30,
      src: 'https://example.com/audio.mp3',
    })
    const fakeAudio = {
      currentTime: 0,
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
    } as unknown as HTMLAudioElement
    const audio = ref<HTMLAudioElement | null>(fakeAudio)

    const { currentTime, seek } = useTakePlayback(take, audio)

    // Normal seek
    seek(15)
    expect(currentTime.value).toBe(15)
    expect(fakeAudio.currentTime).toBe(15)

    // Seek past duration -> clamps to 30
    seek(50)
    expect(currentTime.value).toBe(30)
    expect(fakeAudio.currentTime).toBe(30)

    // Seek below 0 -> clamps to 0
    seek(-5)
    expect(currentTime.value).toBe(0)
    expect(fakeAudio.currentTime).toBe(0)
  })

  it('coordinates play/pause on the audio element when src is present', () => {
    const take = ref<DemoTake>({
      id: 'take-3',
      title: 'Demo con audio',
      duration: 20,
      src: 'https://example.com/demo.mp3',
    })
    const playMock = vi.fn().mockResolvedValue(undefined)
    const pauseMock = vi.fn()
    const fakeAudio = {
      currentTime: 0,
      play: playMock,
      pause: pauseMock,
    } as unknown as HTMLAudioElement
    const audio = ref<HTMLAudioElement | null>(fakeAudio)

    const { playing, togglePlay } = useTakePlayback(take, audio)

    togglePlay()
    expect(playing.value).toBe(true)
    expect(playMock).toHaveBeenCalled()

    togglePlay()
    expect(playing.value).toBe(false)
    expect(pauseMock).toHaveBeenCalled()
  })

  it('resets state when take changes', () => {
    const take = ref<DemoTake>({
      id: 'take-1',
      title: 'Take 1',
      duration: 10,
    })
    const audio = ref<HTMLAudioElement | null>(null)
    const { currentTime, playing, togglePlay, seek } = useTakePlayback(take, audio)

    togglePlay()
    seek(5)
    expect(currentTime.value).toBe(5)

    // Change take
    take.value = {
      id: 'take-2',
      title: 'Take 2',
      duration: 20,
    }

    expect(currentTime.value).toBe(0)
    expect(playing.value).toBe(false)
  })
})
