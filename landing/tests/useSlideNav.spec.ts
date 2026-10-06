import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSlideNav } from '../src/composables/useSlideNav'

describe('useSlideNav', () => {
  let cleanupNav: (() => void) | undefined

  beforeEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  })

  afterEach(() => {
    if (cleanupNav) {
      cleanupNav()
      cleanupNav = undefined
    }
    vi.clearAllTimers()
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('starts at index 0, shows "1 de 7", and clamps between 0 and 6', () => {
    const nav = useSlideNav()
    cleanupNav = nav.cleanup

    expect(nav.activeIndex.value).toBe(0)
    expect(nav.totalSlides).toBe(7)
    expect(nav.counter.value).toBe('1 de 7')

    // Clamping lower bound
    nav.prev()
    expect(nav.activeIndex.value).toBe(0)

    // Advance to end
    for (let i = 0; i < 10; i++) {
      nav.next()
    }
    expect(nav.activeIndex.value).toBe(6)
    expect(nav.counter.value).toBe('7 de 7')

    // Clamping upper bound
    nav.next()
    expect(nav.activeIndex.value).toBe(6)
  })

  it('debounces wheel events by 900 ms', () => {
    vi.useFakeTimers()
    const nav = useSlideNav({ initialIndex: 2 })
    cleanupNav = nav.cleanup

    expect(nav.activeIndex.value).toBe(2)

    // First wheel down advances once
    window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120 }))
    expect(nav.activeIndex.value).toBe(3)

    // Second wheel down within < 900 ms is ignored
    vi.advanceTimersByTime(400)
    window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120 }))
    expect(nav.activeIndex.value).toBe(3)

    // After reaching >= 900 ms from the first event, wheel down advances again
    vi.advanceTimersByTime(500)
    window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120 }))
    expect(nav.activeIndex.value).toBe(4)

    // Wheel up after >= 900 ms goes to previous slide
    vi.advanceTimersByTime(900)
    window.dispatchEvent(new WheelEvent('wheel', { deltaY: -120 }))
    expect(nav.activeIndex.value).toBe(3)
  })

  it('ignores wheel events inside scroll exclusion elements', () => {
    vi.useFakeTimers()
    const nav = useSlideNav({ initialIndex: 1 })
    cleanupNav = nav.cleanup

    const exclusionContainer = document.createElement('div')
    exclusionContainer.setAttribute('data-scroll-exclusion', '')
    const scrollChild = document.createElement('div')
    scrollChild.textContent = 'Scrollable area'
    exclusionContainer.appendChild(scrollChild)
    document.body.appendChild(exclusionContainer)

    const event = new WheelEvent('wheel', {
      deltaY: 120,
      bubbles: true,
      cancelable: true,
    })
    scrollChild.dispatchEvent(event)

    expect(nav.activeIndex.value).toBe(1)
  })

  it('navigates with keyboard keys (Arrow, PageUp/Down, Space, Home, End)', () => {
    const nav = useSlideNav({ initialIndex: 1 })
    cleanupNav = nav.cleanup

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    expect(nav.activeIndex.value).toBe(2)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
    expect(nav.activeIndex.value).toBe(3)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'PageDown' }))
    expect(nav.activeIndex.value).toBe(4)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }))
    expect(nav.activeIndex.value).toBe(5)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }))
    expect(nav.activeIndex.value).toBe(4)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' }))
    expect(nav.activeIndex.value).toBe(3)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'PageUp' }))
    expect(nav.activeIndex.value).toBe(2)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'End' }))
    expect(nav.activeIndex.value).toBe(6)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Home' }))
    expect(nav.activeIndex.value).toBe(0)
  })

  it('does not change slide or call preventDefault on browser modifier shortcuts or defaultPrevented', () => {
    const nav = useSlideNav({ initialIndex: 2 })
    cleanupNav = nav.cleanup

    // Alt+ArrowLeft (browser back)
    const altEvent = new KeyboardEvent('keydown', {
      key: 'ArrowLeft',
      altKey: true,
      cancelable: true,
    })
    const altSpy = vi.spyOn(altEvent, 'preventDefault')
    window.dispatchEvent(altEvent)
    expect(nav.activeIndex.value).toBe(2)
    expect(altSpy).not.toHaveBeenCalled()

    // Ctrl+End
    const ctrlEvent = new KeyboardEvent('keydown', {
      key: 'End',
      ctrlKey: true,
      cancelable: true,
    })
    const ctrlSpy = vi.spyOn(ctrlEvent, 'preventDefault')
    window.dispatchEvent(ctrlEvent)
    expect(nav.activeIndex.value).toBe(2)
    expect(ctrlSpy).not.toHaveBeenCalled()

    // MetaKey
    const metaEvent = new KeyboardEvent('keydown', {
      key: 'ArrowDown',
      metaKey: true,
      cancelable: true,
    })
    const metaSpy = vi.spyOn(metaEvent, 'preventDefault')
    window.dispatchEvent(metaEvent)
    expect(nav.activeIndex.value).toBe(2)
    expect(metaSpy).not.toHaveBeenCalled()

    // defaultPrevented
    const preventedEvent = new KeyboardEvent('keydown', {
      key: 'ArrowDown',
      cancelable: true,
    })
    preventedEvent.preventDefault()
    window.dispatchEvent(preventedEvent)
    expect(nav.activeIndex.value).toBe(2)
  })

  it('ignores Space on interactive elements but allows ArrowDown on buttons', () => {
    const nav = useSlideNav({ initialIndex: 1 })
    cleanupNav = nav.cleanup

    const button = document.createElement('button')
    const link = document.createElement('a')
    link.setAttribute('href', '#target')
    document.body.append(button, link)

    // Space on focused button does not change slide
    button.focus()
    const spaceBtnEvent = new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true })
    const spaceBtnSpy = vi.spyOn(spaceBtnEvent, 'preventDefault')
    button.dispatchEvent(spaceBtnEvent)
    expect(nav.activeIndex.value).toBe(1)
    expect(spaceBtnSpy).not.toHaveBeenCalled()

    // Space on focused link does not change slide
    link.focus()
    const spaceLinkEvent = new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true })
    const spaceLinkSpy = vi.spyOn(spaceLinkEvent, 'preventDefault')
    link.dispatchEvent(spaceLinkEvent)
    expect(nav.activeIndex.value).toBe(1)
    expect(spaceLinkSpy).not.toHaveBeenCalled()

    // ArrowDown on focused button DOES advance slide
    button.focus()
    const arrowBtnEvent = new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true })
    button.dispatchEvent(arrowBtnEvent)
    expect(nav.activeIndex.value).toBe(2)
  })

  it('does not change slide when focus is in an input, textarea, select or contenteditable', () => {
    const nav = useSlideNav({ initialIndex: 2 })
    cleanupNav = nav.cleanup

    const input = document.createElement('input')
    const textarea = document.createElement('textarea')
    const select = document.createElement('select')
    const editable = document.createElement('div')
    editable.setAttribute('contenteditable', 'true')

    document.body.append(input, textarea, select, editable)

    input.focus()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }))
    expect(nav.activeIndex.value).toBe(2)

    textarea.focus()
    textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }))
    expect(nav.activeIndex.value).toBe(2)

    select.focus()
    select.dispatchEvent(new KeyboardEvent('keydown', { key: 'PageDown', bubbles: true }))
    expect(nav.activeIndex.value).toBe(2)

    editable.focus()
    editable.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }))
    expect(nav.activeIndex.value).toBe(2)
  })

  it('exposes prefers-reduced-motion flag to disable transitions', () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('prefers-reduced-motion: reduce'),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))

    const nav = useSlideNav()
    cleanupNav = nav.cleanup

    expect(nav.prefersReducedMotion.value).toBe(true)
  })

  it('cleans up event listeners when cleanup is invoked', () => {
    vi.useFakeTimers()
    const nav = useSlideNav({ initialIndex: 1 })
    nav.cleanup()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    expect(nav.activeIndex.value).toBe(1)

    window.dispatchEvent(new WheelEvent('wheel', { deltaY: 100 }))
    expect(nav.activeIndex.value).toBe(1)
  })
})
