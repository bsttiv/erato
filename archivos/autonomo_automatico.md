# Procesos autónomos y entradas automáticas

Estas son cosas realizadas por el servidor a partir de los datos

- Manejo de sesión de usuario con access y refresh tokens
- Manejo de invitaciones a banda: un usuario invitado como editor puede editar una canción, uno que es lector no puede
  - > Revisión (2026-10-17, aprobada): los roles editor/lector aplican a invitaciones a **canción**. En una banda todos los miembros son editores; la invitación a banda no lleva rol.
- Manejo de privacidad de las canciones: una canción privada puede ser accedida por las personas que están invitadas o por los miembros de una banda que decide hacer la canción pública para los demás integrantes (solo de esa banda). Por el contrario, si es pública, cualquier persona con el link la puede ver.
- Identificar acordes automáticamente
- Identificar clave automáticamente
- Manejar revisiones de cambios (separado por cada sección)
- Manejar tamaño de las demos (minificarlas)

## Revisión (2026-10-17, aprobada): detección de acordes y tonalidad

> Reemplaza la versión anterior de esta sección (una sola tonalidad elegida por desempates). La tonalidad depende de cómo resuelve la canción, algo que no se deduce solo del conjunto de acordes; por eso el sistema propone candidatas y el usuario elige.

**Autoría:** el diseño es del autor: nombrar cada acorde según la tonalidad en que se toca, y que la detección entregue **todas las tonalidades candidatas** para que el usuario elija la que representa su canción, en lugar de imponer una. El harness de IA propuso detalles (puntaje sobre las 24 tonalidades, uso de la menor armónica, orden de sugerencia y nombre de respaldo) que el autor revisó y aprobó.

- **Determinista:** a las mismas notas y acordes siempre les corresponde el mismo resultado.
- **Candidatas:** en cada cambio (agregar, editar o borrar un acorde) se puntúan las 24 tonalidades según cuántos acordes son diatónicos en cada una (en menor puntúan solo los acordes de la menor natural). Un acorde suma en una tonalidad solo si **todas** sus notas pertenecen a ella (`Cmaj7` suma en C, `C7` no); si el acorde tiene tensiones alteradas (`b9`, `#9`, `#11` o `b13`), solo se evalúa su tríada principal; con tensiones naturales (`9`, `11`, `13`) se evalúan todas sus notas. Los acordes con nombre de respaldo siguen la misma regla (revisión 2026-10-17, aprobada). La función devuelve un **arreglo** con todas las tonalidades empatadas en el puntaje máximo.
- **Orden del arreglo** (orden de sugerencia, no descarta opciones):
  1. Menores con más acordes de la menor armónica presentes (V mayor, vii°, III aumentado, incluidas sus séptimas: V7, vii°7).
  2. Tonalidades cuyo acorde I aparece en la canción.
  3. Mayores antes que menores.
  4. Orden del círculo de quintas desde C.
  - Ejemplos: `[C, F, G, E]` → `[Am, C]`; `[C, G, D]` → `[G, Em]`.
- **Puntaje máximo 0** (ningún acorde calza en ninguna tonalidad): se devuelve un arreglo vacío, igual que sin acordes (revisión 2026-10-17, aprobada).
- **Sin acordes:** se devuelve un arreglo vacío (las tablaturas no se usan para detectar tonalidad). En `auto`, la tonalidad queda vacía (`null`) y la interfaz invita a agregar acordes; al agregar el primero se selecciona la primera candidata sin aviso, porque no había elección previa (revisión 2026-10-17, aprobada).
- **Nombres de los acordes:** se calculan con la tonalidad seleccionada, eligiendo la interpretación y la grafía enarmónica (F# vs Gb) coherentes con ella. Mientras el usuario no elija, se usa **siempre la primera tonalidad del arreglo**, aunque otras empaten en puntaje.
- **Identificación del acorde** (revisión 2026-10-17, aprobada; reemplaza «la nota más grave es la fundamental»):
  1. Se busca qué acorde conocido forman las notas, probando cada una como fundamental.
  2. Si hay varias lecturas válidas (`C6` = `Am7` en notas), gana la que tiene el bajo (nota más grave) como fundamental.
  3. Si aún empatan, gana la lectura diatónica a la tonalidad seleccionada.
  4. Si el bajo no es la fundamental, se escribe con barra (ej. `C/E`).
- **Notación** (revisión 2026-10-17, aprobada): solo ASCII. Calidades: `m`, `dim`, `+`, `7`, `maj7`, `m7`, `6`, `m7b5`, `dim7`, `sus2`, `sus4`, `add9`, `9`, `maj9`, `m9`, `11`, `m11`, `13`. Tensiones alteradas entre paréntesis (`G7(b9)`, `C7(#11)`). Tonalidades: `"C"`, `"Am"`, `"F#m"`, `"Bb"`.
- **Grafía de acordes no diatónicos** (revisión 2026-10-17, aprobada): se elige la grafía enarmónica que da menos alteraciones al escribir las notas del acorde (`Ab` y no `G#` en C; `F#dim` y no `Gbdim`). Empate: bemoles en tonalidades con bemoles y en C/Am; sostenidos en tonalidades con sostenidos.
- **Acordes de pocas notas** (revisión 2026-10-17, aprobada): un acorde necesita al menos 2 clases de altura distintas (si no, error de validación). Díadas: quinta justa → `C5`; tercera mayor → `C(no5)`; tercera menor → `Cm(no5)`; otro intervalo → nombre de respaldo (`C(#11)`). Puntúan como cualquier acorde (todas sus notas deben caber).
- **Quinta omitida** (revisión 2026-10-31, aprobada): un acorde que conserva la tercera y al menos otra nota además de la fundamental puede omitir la quinta justa y se nombra sin marcarlo (`E G G# D` = `E7(#9)`, `C E Bb` = `C7`). Un acorde completo siempre tiene prioridad.
- **Nunca «desconocido» (acordes):** si ningún nombre estándar calza, se nombra como fundamental + intervalos (ej. `C(b9,#11)`), tomando el bajo como fundamental.
- **`key_mode = auto`:** la tonalidad se elige del arreglo de candidatas (por defecto, la primera). Si tras un cambio la tonalidad elegida sigue en el arreglo, se conserva aunque el orden cambie. Si un cambio en los acordes la deja fuera del arreglo, se vuelve a la primera candidata y se avisa al usuario con una notificación breve (tipo snackbar) de que su tonalidad cambió (revisión 2026-10-17, aprobada).
- **`key_mode = manual`:** el usuario fija cualquier tonalidad; los nombres de los acordes se adaptan a ella. Las candidatas se siguen calculando y se muestran solo como sugerencia, sin afectar la tonalidad fijada ni los nombres (revisión 2026-10-17, aprobada).
- **Paso de manual a auto:** misma regla: si la tonalidad fijada está entre las candidatas se conserva; si no, se toma la primera y se avisa al usuario (revisión 2026-10-17, aprobada).
