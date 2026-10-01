import { ref, watch, getCurrentScope, onScopeDispose, type Ref } from 'vue'

export interface UseAutoScrollOptions {
  defaultSpeed?: number
}

export function useAutoScroll(
  box: Ref<HTMLElement | null>,
  options?: UseAutoScrollOptions
) {
  const playing = ref(false)
  const speed = ref(options?.defaultSpeed || 24)
  const max = ref(false)

  let rafId = 0
  let acc = 0
  let lastTime = 0

  function tick(t: number) {
    if (!playing.value) return
    const el = box.value
    if (!el) return
    acc += ((t - lastTime) / 1000) * speed.value
    lastTime = t
    if (acc >= 1) {
      const step = Math.floor(acc)
      acc -= step
      el.scrollTop += step
    }
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 1) {
      playing.value = false
      return
    }
    rafId = requestAnimationFrame(tick)
  }

  watch(
    playing,
    (isPlaying) => {
      if (rafId) {
        cancelAnimationFrame(rafId)
        rafId = 0
      }
      if (isPlaying) {
        lastTime = performance.now()
        rafId = requestAnimationFrame(tick)
      }
    },
    { immediate: false }
  )

  function onEsc(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      max.value = false
    }
  }

  watch(
    max,
    (isMax) => {
      if (typeof window === 'undefined') return
      if (isMax) {
        window.addEventListener('keydown', onEsc)
      } else {
        window.removeEventListener('keydown', onEsc)
      }
    },
    { immediate: true, flush: 'sync' }
  )

  function togglePlay() {
    const el = box.value
    if (!playing.value && el && el.scrollTop + el.clientHeight >= el.scrollHeight - 1) {
      el.scrollTop = 0
    }
    playing.value = !playing.value
  }

  function toggleMax() {
    max.value = !max.value
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      if (rafId) {
        cancelAnimationFrame(rafId)
      }
      if (typeof window !== 'undefined') {
        window.removeEventListener('keydown', onEsc)
      }
    })
  }

  return {
    playing,
    speed,
    max,
    togglePlay,
    toggleMax,
  }
}
