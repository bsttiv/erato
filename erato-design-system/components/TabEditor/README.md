# TabEditor

Tablatura de 6 cuerdas que se escribe a mano con el teclado.

- Props: `defaultValue` (columnas: arreglos de 6 textos, de `e` aguda a `E` grave, o `"|"` para una línea de compás), `columns` (vacías al iniciar, 16), `strings` (nombres de cuerda), `title`, `hideHint`, `onChange(columns)`.
- Teclado: dígitos escriben el traste (hasta 24, dos dígitos seguidos se juntan), `h p b / \ ~ x r s v` agregan técnica, flechas mueven, espacio avanza (y crea columna al final), Enter inserta un tiempo, `|` inserta compás, Backspace borra.
- `Erato.tabToText(columns)` exporta a texto plano ASCII para copiar.
