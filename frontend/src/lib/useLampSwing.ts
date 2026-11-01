import { onBeforeUnmount, onMounted, type Ref } from 'vue'
import { createLamp, PHYSICS_STEP, pushLamp, stepLamp, type CordPoint } from './lampPhysics'

interface LampElement {
  $el: SVGElement
  setPose?: (points: CordPoint[]) => void
}

/** A pointer-driven flexible pendulum, with no held target after a push. */
export function useLampSwing(lamp: Ref<LampElement | null>, light: Ref<HTMLElement | null>, cord = 110) {
  let physics = createLamp(cord)
  let lastPointer: { x: number; y: number } | null = null
  let lastTime = 0
  let accumulator = 0
  let frame = 0
  let hover: MediaQueryList
  let reduced: MediaQueryList

  function paint() {
    lamp.value?.setPose?.(physics.points)
    const bob = physics.points[physics.points.length - 1]!
    if (light.value) light.value.style.transform = `translate3d(${bob.x}px, ${bob.y - cord}px, 0)`
  }
  function tick(time: number) {
    accumulator += Math.min(Math.max(0, (time - lastTime) / 1000), 1 / 30)
    lastTime = time
    let settled = false
    while (accumulator >= PHYSICS_STEP) {
      settled = stepLamp(physics)
      accumulator -= PHYSICS_STEP
    }
    paint()
    frame = settled ? 0 : requestAnimationFrame(tick)
  }
  function wake() {
    if (frame) return
    lastTime = performance.now()
    accumulator = 0
    frame = requestAnimationFrame(tick)
  }
  function onPointerMove(event: PointerEvent) {
    if (event.pointerType === 'touch' || !hover.matches || reduced.matches) {
      lastPointer = null
      return
    }
    const previous = lastPointer
    lastPointer = { x: event.clientX, y: event.clientY }
    if (!previous || !lamp.value) return
    const movedX = event.clientX - previous.x
    if (!movedX) return
    // Root bounds stay fixed: transforms are confined to the cord and shade.
    const box = lamp.value.$el.getBoundingClientRect()
    const x = event.clientX - box.left - box.width / 2
    const y = event.clientY - box.top
    const oldX = previous.x - box.left - box.width / 2
    const oldY = previous.y - box.top
    const dx = x - oldX
    const dy = y - oldY
    const distanceSquared = dx * dx + dy * dy
    let nearest = 0
    let closest = Infinity
    physics.points.slice(1).forEach((point, offset) => {
      // Swept contact catches a fast pointer crossing the thin cord.
      const t = Math.max(0, Math.min(1, ((point.x - oldX) * dx + (point.y - oldY) * dy) / distanceSquared))
      const distance = Math.hypot(point.x - oldX - t * dx, point.y - oldY - t * dy)
      if (distance < closest) { closest = distance; nearest = offset + 1 }
    })
    const bob = physics.points[physics.points.length - 1]!
    const shadeT = Math.max(0, Math.min(1, ((bob.x - oldX) * dx + (bob.y + 24 - oldY) * dy) / distanceSquared))
    const shadeDistance = Math.hypot(bob.x - oldX - shadeT * dx, bob.y + 24 - oldY - shadeT * dy)
    if (shadeDistance < 42) nearest = physics.points.length - 1
    else if (closest > 18) return
    pushLamp(physics, nearest, movedX)
    wake()
  }
  function onPointerLeave() { lastPointer = null }
  function onMediaChange() {
    lastPointer = null
    window.removeEventListener('pointermove', onPointerMove)
    if (hover.matches && !reduced.matches) {
      window.addEventListener('pointermove', onPointerMove, { passive: true })
      return
    }
    cancelAnimationFrame(frame)
    frame = 0
    physics = createLamp(cord)
    paint()
  }

  onMounted(() => {
    hover = window.matchMedia('(hover: hover) and (pointer: fine)')
    reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    hover.addEventListener?.('change', onMediaChange)
    reduced.addEventListener?.('change', onMediaChange)
    onMediaChange()
    document.documentElement.addEventListener('pointerleave', onPointerLeave)
  })
  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    hover?.removeEventListener?.('change', onMediaChange)
    reduced?.removeEventListener?.('change', onMediaChange)
    window.removeEventListener('pointermove', onPointerMove)
    document.documentElement.removeEventListener('pointerleave', onPointerLeave)
  })
}
