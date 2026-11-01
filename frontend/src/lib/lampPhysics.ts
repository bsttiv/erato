/** A weighted, inextensible cord: Verlet particles with a fixed ceiling anchor. */
export interface CordPoint {
  x: number
  y: number
  previousX: number
  previousY: number
}
export interface LampPhysics {
  length: number
  points: CordPoint[]
}
const SEGMENTS = 10
const GRAVITY = 1800
const DRAG = 5
const MAX_SLOPE = Math.tan(16 * Math.PI / 180)
export const PHYSICS_STEP = 1 / 120

export function createLamp(length: number): LampPhysics {
  return {
    length,
    points: Array.from({ length: SEGMENTS + 1 }, (_, i) => ({
      x: 0, y: length * i / SEGMENTS, previousX: 0, previousY: length * i / SEGMENTS,
    })),
  }
}

/** Transfer pointer displacement as momentum, never as a persistent target. */
export function pushLamp(lamp: LampPhysics, index: number, movedX: number) {
  const point = lamp.points[index]
  if (!point || index === 0) return
  point.previousX -= Math.max(-120, Math.min(120, movedX)) * 0.15
}

export function stepLamp(lamp: LampPhysics, dt = PHYSICS_STEP): boolean {
  const segment = lamp.length / SEGMENTS
  for (const point of lamp.points.slice(1)) {
    const x = point.x
    const y = point.y
    const decay = Math.exp(-DRAG * dt)
    point.x += (x - point.previousX) * decay
    point.y += (y - point.previousY) * decay + GRAVITY * dt * dt
    point.previousX = x
    point.previousY = y
  }
  // The bob has twenty times a cord particle's mass. Iterating constraints
  // transfers a local cord push to the shade without making the cord rigid.
  for (let iteration = 0; iteration < 80; iteration++) {
    for (let i = 1; i <= SEGMENTS; i++) {
      const a = lamp.points[i - 1]!
      const b = lamp.points[i]!
      const dx = b.x - a.x
      const dy = b.y - a.y
      const distance = Math.hypot(dx, dy) || segment
      const error = (distance - segment) / distance
      const inverseA = i === 1 ? 0 : 1
      const inverseB = i === SEGMENTS ? 0.05 : 1
      const total = inverseA + inverseB
      a.x += dx * error * inverseA / total
      a.y += dy * error * inverseA / total
      b.x -= dx * error * inverseB / total
      b.y -= dy * error * inverseB / total
      // A damped stop preserves the existing landing's ±16 degree envelope.
      const limit = Math.max(0, b.y) * MAX_SLOPE
      if (Math.abs(b.x) > limit) {
        b.x = Math.sign(b.x) * limit
        b.previousX = b.x
      }
    }
  }
  const settled = lamp.points.every((point, i) =>
    Math.abs(point.x) < 0.08 &&
    Math.abs(point.y - i * segment) < 0.5 &&
    Math.hypot(point.x - point.previousX, point.y - point.previousY) / dt < 0.4,
  )
  if (settled) lamp.points = createLamp(lamp.length).points
  return settled
}
