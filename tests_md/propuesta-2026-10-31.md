# Additional test proposals — 2026-10-31

Approved by the author on 2026-10-31 and implemented in `backend/tests/test_deteccion.py`. These cases cover the omitted fifth rule in `decisiones/08-acordes-y-tonalidad.md` section 4.6.

| ID | Input | Expected | Why |
| --- | --- | --- | --- |
| DET-028 | `name_chord([40,55,56,62], "C")` (E G G# D) | `"E7(#9)"` | Reported failure; was `E(b3,3,b7)` |
| DET-029 | `name_chord([48,64,70], "C")` (C E Bb) | `"C7"` | Dominant seventh without a fifth |
| DET-030 | `name_chord([48,64,71], "C")` (C E B) | `"Cmaj7"` | Major seventh without a fifth |
| DET-031 | `name_chord([48,63,70], "C")` (C Eb Bb) | `"Cm7"` | Minor seventh without a fifth |
| DET-032 | `name_chord([48,64,70,74], "C")` (C E Bb D) | `"C9"` | Extension without a fifth |
| DET-033 | `name_chord([52,60,70], "C")` (E C Bb) | `"C7/E"` | Slash rule still applies |
| DET-034 | `name_chord([48,64,69], "C")` (C E A) | `"Am/C"` | A complete chord beats a reading without a fifth |
| DET-035 | `name_chord([48,67,71], "C")` (C G B) | `"C(5,7)"` | No third, so no omitted fifth reading |
| DET-036 | `candidate_keys` of C, F and G B F | `["C", "Am"]` | A chord without a fifth scores with all its notes; was `["C", "F", "Am", "Dm"]` |
