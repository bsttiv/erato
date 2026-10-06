import { ref, computed, onMounted, onUnmounted, getCurrentInstance, type Ref } from 'vue'

export interface UseSlideNavOptions {
  totalSlides?: number
  initialIndex?: number
  scrollExclusionSelector?: string
}

export interface UseSlideNavReturn {
  activeIndex: Ref<number>
  totalSlides: number
  counter: Ref<string>
  counterText: Ref<string>
  prefersReducedMotion: Ref<boolean>
  reducedMotion: Ref<boolean>
  next: () => void
  prev: () => void
  goTo: (index: number) => void
  cleanup: () => void
}

const DEFAULT_TOTAL_SLIDES = 7
const WHEEL_DEBOUNCE_MS = 900
const DEFAULT_SCROLL_EXCLUSION_SELECTOR = '[data-scroll-exclusion]'

function isEditableElement(element: unknown): boolean {
  if (typeof Element === 'undefined' || !(element instanceof Element)) {
    return false
  }

  const tagName = element.tagName ? element.tagName.toLowerCase() : ''
  if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
    return true
  }

  const htmlElement = element as HTMLElement
  if (htmlElement.isContentEditable) {
    return true
  }

  const attr = element.getAttribute('contenteditable')
  if (attr === 'true' || attr === '') {
    return true
  }

  if (typeof element.closest === 'function') {
    const editableAncestor = element.closest('input, textarea, select, [contenteditable="true"], [contenteditable=""]')
    if (editableAncestor !== null) {
      return true
    }
  }

  return false
}

export function useSlideNav(options: UseSlideNavOptions = {}): UseSlideNavReturn {
  const totalSlides = options.totalSlides ?? DEFAULT_TOTAL_SLIDES
  const activeIndex = ref(options.initialIndex ?? 0)
  const scrollExclusionSelector = options.scrollExclusionSelector ?? DEFAULT_SCROLL_EXCLUSION_SELECTOR

  const counter = computed(() => `${activeIndex.value + 1} de ${totalSlides}`)
  const prefersReducedMotion = ref(false)

  let lastWheelTimestamp = 0
  let isCleanedUp = false

  const goTo = (targetIndex: number) => {
    const clampedIndex = Math.max(0, Math.min(totalSlides - 1, targetIndex))
    activeIndex.value = clampedIndex
  }

  const next = () => {
    if (activeIndex.value < totalSlides - 1) {
      activeIndex.value += 1
    }
  }

  const prev = () => {
    if (activeIndex.value > 0) {
      activeIndex.value -= 1
    }
  }

  const handleWheel = (event: WheelEvent) => {
    const target = event.target as Element | null
    if (target !== null && typeof target.closest === 'function') {
      if (target.closest(scrollExclusionSelector) !== null) {
        return
      }
    }

    if (Math.abs(event.deltaY) < 1) {
      return
    }

    const now = Date.now()
    if (now - lastWheelTimestamp < WHEEL_DEBOUNCE_MS) {
      return
    }

    lastWheelTimestamp = now
    if (event.deltaY > 0) {
      next()
    } else if (event.deltaY < 0) {
      prev()
    }
  }

  const handleKeyDown = (event: KeyboardEvent) => {
    const target = event.target as Element | null
    const activeDocElement = typeof document !== 'undefined' ? document.activeElement : null

    if (isEditableElement(target) || isEditableElement(activeDocElement)) {
      return
    }

    const key = event.key
    if (key === 'ArrowDown' || key === 'ArrowRight' || key === 'PageDown' || key === ' ') {
      event.preventDefault?.()
      next()
    } else if (key === 'ArrowUp' || key === 'ArrowLeft' || key === 'PageUp') {
      event.preventDefault?.()
      prev()
    } else if (key === 'Home') {
      event.preventDefault?.()
      goTo(0)
    } else if (key === 'End') {
      event.preventDefault?.()
      goTo(totalSlides - 1)
    }
  }

  let mediaQueryList: MediaQueryList | null = null
  let mediaQueryHandler: ((e: MediaQueryListEvent) => void) | null = null

  const setupReducedMotion = () => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return
    }

    mediaQueryList = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = mediaQueryList.matches

    mediaQueryHandler = (e: MediaQueryListEvent) => {
      prefersReducedMotion.value = e.matches
    }

    if (typeof mediaQueryList.addEventListener === 'function') {
      mediaQueryList.addEventListener('change', mediaQueryHandler)
    } else if ('addListener' in mediaQueryList) {
      (mediaQueryList as any).addListener(mediaQueryHandler)
    }
  }

  const attachListeners = () => {
    if (typeof window === 'undefined') {
      return
    }

    window.addEventListener('wheel', handleWheel, { passive: true })
    window.addEventListener('keydown', handleKeyDown)
    setupReducedMotion()
  }

  const cleanup = () => {
    if (isCleanedUp) {
      return
    }
    isCleanedUp = true

    if (typeof window !== 'undefined') {
      window.removeEventListener('wheel', handleWheel)
      window.removeEventListener('keydown', handleKeyDown)
    }

    if (mediaQueryList !== null && mediaQueryHandler !== null) {
      if (typeof mediaQueryList.removeEventListener === 'function') {
        mediaQueryList.removeEventListener('change', mediaQueryHandler)
      } else if ('removeListener' in mediaQueryList) {
        (mediaQueryList as any).removeListener(mediaQueryHandler)
      }
    }
  }

  const instance = getCurrentInstance()
  if (instance !== null) {
    onMounted(() => {
      attachListeners()
    })
    onUnmounted(() => {
      cleanup()
    })
  } else {
    attachListeners()
  }

  return {
    activeIndex,
    totalSlides,
    counter,
    counterText: counter,
    prefersReducedMotion,
    reducedMotion: prefersReducedMotion,
    next,
    prev,
    goTo,
    cleanup,
  }
}
