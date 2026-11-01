# Additional test proposals — compact chord figure, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `frontend/src/components/atoms/ChordDiagram.spec.ts`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| DIA-001 | Show an open chord and one at fret 12 | Both figures keep the same size and show five frets |
| DIA-002 | Show a chord on frets 7 to 9 | The neck starts at fret 7 and every pressed note is drawn |
| DIA-003 | Show a chord with muted, open and pressed strings | Each string shows its own mark |
| DIA-004 | Show a piano chord above C5 | The keyboard starts at the octave of its lowest note and marks every note |
| DIA-005 | Show a piano chord wider than two octaves | The written shape replaces the keyboard |
