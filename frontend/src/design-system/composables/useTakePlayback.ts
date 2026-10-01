import { ref, computed, watch, getCurrentScope, onScopeDispose, type Ref } from 'vue'

export interface PlaybackTake {
  id: string
  title: string
  duration: number
  src?: string
}

export function useTakePlayback(
  take: Ref<PlaybackTake | undefined>,
  audio: Ref<HTMLAudioElement | null>
) {
  const currentTime = ref(0)
  const playing = ref(false)
  const loadedDuration = ref<number | null>(null)

  const duration = computed(() => {
    return loadedDuration.value || take.value?.duration || 1
  })

  let intervalId: any = null

  function stopTimer() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function startTimer() {
    stopTimer()
    let last = Date.now()
    intervalId = setInterval(() => {
      const now = Date.now()
      const dt = (now - last) / 1000
      last = now
      const D = duration.value
      currentTime.value = Math.min(D, currentTime.value + dt)
      if (currentTime.value >= D) {
        playing.value = false
        stopTimer()
      }
    }, 100)
  }

  // Handle take change
  watch(
    () => take.value?.id,
    () => {
      currentTime.value = 0
      playing.value = false
      loadedDuration.value = null
      stopTimer()
      if (audio.value) {
        audio.value.pause()
      }
    },
    { flush: 'sync' }
  )

  // Handle playing state
  watch(
    [playing, () => take.value?.src],
    ([isPlaying, hasSrc]) => {
      const currentTake = take.value
      if (!currentTake) return

      if (hasSrc && audio.value) {
        stopTimer()
        if (isPlaying) {
          audio.value.play().catch(() => {
            playing.value = false
          })
        } else {
          audio.value.pause()
        }
      } else {
        if (isPlaying) {
          startTimer()
        } else {
          stopTimer()
        }
      }
    },
    { flush: 'sync' }
  )

  function seek(v: number) {
    const D = duration.value
    const clamped = Math.max(0, Math.min(D, v))
    currentTime.value = clamped
    if (audio.value && take.value?.src) {
      audio.value.currentTime = clamped
    }
  }

  function togglePlay() {
    const D = duration.value
    if (!playing.value && currentTime.value >= D) {
      seek(0)
    }
    playing.value = !playing.value
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      stopTimer()
    })
  }

  return {
    currentTime,
    playing,
    duration,
    loadedDuration,
    seek,
    togglePlay,
  }
}
