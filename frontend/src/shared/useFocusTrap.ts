import { ref, watch, onUnmounted, type Ref } from 'vue'

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(
  containerRef: Ref<HTMLElement | null>,
  isActive: Ref<boolean>
) {
  const previouslyFocusedElement = ref<HTMLElement | null>(null)

  function getFocusableElements(): HTMLElement[] {
    if (!containerRef.value) return []
    return Array.from(
      containerRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    ).filter((el) => el.offsetParent !== null || el.getClientRects().length > 0)
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (!isActive.value || e.key !== 'Tab') return

    const focusables = getFocusableElements()
    if (focusables.length === 0) {
      e.preventDefault()
      return
    }

    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    const current = document.activeElement as HTMLElement

    if (e.shiftKey) {
      if (current === first || !containerRef.value?.contains(current)) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (current === last || !containerRef.value?.contains(current)) {
        e.preventDefault()
        first.focus()
      }
    }
  }

  function activate() {
    if (typeof document !== 'undefined') {
      previouslyFocusedElement.value = document.activeElement as HTMLElement | null
      const focusables = getFocusableElements()
      if (focusables.length > 0) {
        // Schedule focus on next microtask or tick
        queueMicrotask(() => {
          focusables[0].focus()
        })
      }
      window.addEventListener('keydown', handleKeyDown)
    }
  }

  function deactivate() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleKeyDown)
    }
    if (previouslyFocusedElement.value && typeof previouslyFocusedElement.value.focus === 'function') {
      previouslyFocusedElement.value.focus()
      previouslyFocusedElement.value = null
    }
  }

  watch(
    isActive,
    (active) => {
      if (active) {
        activate()
      } else {
        deactivate()
      }
    },
    { immediate: true }
  )

  onUnmounted(() => {
    deactivate()
  })

  return {
    getFocusableElements,
  }
}
