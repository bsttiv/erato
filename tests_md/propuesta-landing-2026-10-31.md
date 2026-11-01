# Additional test proposals — landing and lyrics modal, 2026-10-31

Approved by the author on 2026-10-31 and implemented in the specs next to each piece: `LandingNav.spec.ts`, `LandingView.spec.ts`, `chordDetection.spec.ts`, `useLampSwing.spec.ts` and `CompositionView.spec.ts`.

## Landing session

| ID | Setup | Expected |
| --- | --- | --- |
| LAND-001 | Visitor without a session | Navigation shows `Iniciar sesión` and `Empieza gratis` |
| LAND-002 | Visitor with a valid refresh cookie | Navigation shows the display name and links to `/canciones`; sign-in links are absent |
| LAND-003 | API unreachable during the check | Navigation shows the sign-in links; the page does not fail |

## Landing chord detector

| ID | Frets | Expected |
| --- | --- | --- |
| LAND-010 | `[0,0,0,2,3,-1]` | `Cmaj7`, notes `C · E · G · B` |
| LAND-011 | `[0,3,1,0,2,0]` | `E7`, notes `E · G# · B · D` |
| LAND-012 | One string only, or all muted | Prompt `Marca al menos dos notas`, no chord name |
| LAND-013 | Notes E G G# D | `E7(#9)`, the same as DET-028 |
| LAND-014 | Change a fret in the landing | Name and notes update |

## Landing content

| ID | Check | Expected |
| --- | --- | --- |
| LAND-020 | `Lectura` section | No `Siguiente acorde` text |

## Lamp

| ID | Input | Expected |
| --- | --- | --- |
| LAND-030 | Pointer within reach moves 50 px right, then left | Push target is positive, then negative |
| LAND-031 | Pointer moves far beyond the limit | Push target stays at ±16° |
| LAND-032 | Pointer leaves the reach | Push target returns to 0 |
| LAND-033 | Lamp released at 16° | Passes rest, then settles in under 3 s, also at 30 frames per second |
| LAND-034 | `prefers-reduced-motion`, or a device without hover | No pointer listener is added and the lamp stays still |

## Lyrics modal

| ID | Action | Expected |
| --- | --- | --- |
| MOD-001 | Press `Editar letra` | The modal opens; the editor is not below the sheet |
| MOD-002 | Press `Cerrar` or Escape | The modal closes and the draft stays |
| MOD-003 | Save successfully | The modal closes |
| MOD-004 | Save with a conflict or an error | The modal closes and the message is visible on the page with the draft intact |
