# ChordEditor

Diagrama de acorde editable en guitarra o piano; el nombre se detecta solo a partir de las notas, con acordes con barra (`D/F#`) y séptimas sin quinta.

- Props: `defaultFrets` (6 valores, de la 6ª cuerda a la 1ª: `-1` apagada, `0` al aire, `n` traste), `defaultBaseFret`, `defaultInstrument` `"guitar" | "piano"`, `defaultNotes` (MIDI, para piano; C3 = 48), `editable` (por defecto true), `hideSwitch`, `onChange({instrument, frets, notes, name})`.
- Guitarra: toca un casillero para poner la nota, otra vez para quitarla; toca arriba de la cuerda para alternar al aire / apagada; ‹ › mueve la ventana de trastes.
- Piano: dos octavas desde C3; toca teclas para marcarlas. Al pasar de guitarra a piano, las notas se trasladan.
- La raíz se pinta en `wine`, el resto en `amber`. La detección está en `Erato.detectChord(notas)` si la necesitas fuera.
