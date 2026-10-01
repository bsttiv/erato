import { ref } from 'vue'

export function useDrawer() {
  const open = ref(false)

  const toggle = () => {
    open.value = !open.value
  }

  const close = () => {
    open.value = false
  }

  return {
    open,
    toggle,
    close,
  }
}
