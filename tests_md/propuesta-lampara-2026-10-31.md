# Additional test proposals — flexible landing lamp, 2026-10-31

Approved by the author on 2026-10-31. Executable coverage: `lampPhysics.spec.ts`, `useLampSwing.spec.ts`, `StageLamp.spec.ts`, and `LandingView.spec.ts`; LAMP-012's real-browser layout and hit-testing portion is explicitly skipped in jsdom.

## Flexible cord and pendulum

| ID | Input | Expected |
| --- | --- | --- |
| LAMP-001 | Move a mouse from left to right across the shade | The bob receives rightward momentum; a reverse push opposes its current velocity without resetting its position |
| LAMP-002 | Move the mouse across the middle of the cord | That part of the cord bends first; tension transfers motion to the bob and the fixed ceiling anchor does not move |
| LAMP-003 | Stop the mouse while it remains beside the lamp | No persistent pointer target holds the bob away from equilibrium; gravity and damping continue the free swing |
| LAMP-004 | Push the cord at different heights with the same displacement | Both pushes reach the bob through the constrained cord; the resulting responses depend on the contact point rather than rotating a rigid SVG |
| LAMP-005 | Run an identical release at 30, 60 and 120 frames per second | Fixed 1/120 s physics steps give equivalent trajectories within numerical tolerance; a delayed frame does not destabilize the chain |
| LAMP-006 | Let both landing lamps reach equilibrium | Cord and shade return to their initial pose and no animation frame remains scheduled; another push restarts the loop |

## Light and decoration

| ID | Check | Expected |
| --- | --- | --- |
| LAMP-010 | Inspect either lamp before interaction | Existing `bg-spot` provides a centered radial background glow, with no gradient starting at a visible horizontal edge |
| LAMP-011 | Push the shade and then the cord | Glow translation follows the same bob displacement used to position the shade |
| LAMP-012 | Click page controls through the lamp or glow at narrow and wide viewport widths | Decorative elements never intercept input and never increase the page's horizontal scroll width |
| LAMP-013 | Open a sign-in page that also uses `StageLamp` | Its static lamp retains its existing appearance; flexible rendering is enabled only by the landing |

## Motion preferences and pointer safety

| ID | Input | Expected |
| --- | --- | --- |
| LAMP-020 | Send touch pointer events on a hybrid device whose primary pointer supports hover | No impulse or animation is created; touch does not become a false mouse hover |
| LAMP-021 | Enable reduced motion or remove hover capability during a swing | The frame is canceled, the pose resets, and subsequent pointer movement cannot restart it |
| LAMP-022 | Disable reduced motion and restore fine-pointer hover | A fresh mouse movement can push the lamp; duplicate listeners are not installed |
| LAMP-023 | Unmount while swinging | Pending animation and media/pointer listeners are removed |

## Minimal adaptations of already approved lamp tests

The existing six executable cases retain their LAND IDs; no new executable test case was added.

| Existing ID | Minimal adaptation | Reason |
| --- | --- | --- |
| LAND-030 | Apply the same right/left displacement inputs to the bob and inspect its physical position after integration | The implementation now transfers momentum instead of maintaining an angular pointer target |
| LAND-031 | Inspect the constrained bob's displacement under repeated extreme pushes | The existing ±16° safety envelope now belongs to the physical chain, not a spring-target clamp |
| LAND-032 | Release a displaced chain without further impulses and inspect its movement toward equilibrium | Leaving reach no longer needs a target reset: the lamp is always free after each instantaneous impulse, even while the pointer stays nearby |
| LAND-033 | Release the chain from 16° using fixed physics substeps at both existing frame rates; retain overshoot and under-3-second assertions | The rigid angular spring has been replaced by a flexible weighted cord; the approved observable release behavior is unchanged |
| LAND-034 | No change | Reduced motion and hover listener gating still apply |

## Implementation and verification notes

The deterministic test-first exception follows the author's requirement: new cases need approval before executable tests can be added. The already approved cases above were adapted only where the removed spring-target API no longer represented the requested behavior.

The model is a ten-segment, weighted Verlet chain with a fixed anchor, gravity, exponential velocity drag, and iterated distance constraints. The bob has twenty times a cord particle's mass. Pointer movement supplies a bounded horizontal momentum impulse at the nearest swept contact; there is no held target. A damped angular stop preserves the existing ±16° envelope. The solver uses 1/120 s substeps and caps catch-up work after delayed frames. Rest snaps subpixel constraint residuals to the exact hanging pose and pauses the animation loop.

The cord path must repaint to deform, but only that small SVG path changes. Shade and existing radial glow move directly without per-frame Vue reactive state changes or page layout changes. This is a lightweight visual approximation, not an exact continuous-rope or Lagrangian solver. Browser/device feel, paint cost, and the newly proposed visual/interaction cases remain pending manual verification and author approval.
