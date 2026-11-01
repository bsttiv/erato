# 09 - Canciones y sus secciones

Estado: aprobado por el autor el 2026-10-18 (`tests_md/canciones_secciones.md`). Se asume un actor autorizado (dueño, miembro `editor` de la canción o miembro de la banda); los permisos están en el archivo 06. Las demos (sección opcional) están en el archivo 10; acordes y tonalidad, en el archivo 08.

## 1. La canción

### Creación y valores por defecto

- `POST /songs` con `title` (obligatorio). Valores por defecto: `owner_type = user`, `owner_id` = usuario autenticado, `status = idea`, `visibility = private`, `key_mode = auto`, `key = null`, `share_slug = null`, `lyrics = null`, listas de secciones vacías. Para crear en una banda: `owner_type = band` con `owner_id` de la banda (cualquier miembro puede).
- `created_at` y `updated_at` en UTC. **`section_versions = 1` en todas las secciones** (`lyrics`, `chords`, `tabs`, `tasks`, `meta`), incluidas las vacías. Existe una sola revisión (`meta`, versión 1); no hay revisión para las secciones vacías.
- Se pueden cambiar título y estado; `tempo`, `key`, `time_signature` son opcionales. Validaciones de campo: archivo 05, sección 9.
- Una sola lectura (`GET /songs/{id}`) devuelve todas las secciones embebidas.
- **Borrado:** físico. Se borran la canción, sus comentarios, revisiones, enlaces, membresías y los objetos de sus demos en Cloudinary. Un enlace de una canción borrada responde `404`.
- Un cliente no puede enviar `owner_id`, `owner_type`, `section_versions` ni `share_slug` arbitrarios (`422`).

### Las secciones son opcionales

Cada canción puede tener acordes, tablaturas, letra, demos y tareas, todos opcionales. Todo se ve y se edita en la misma página («no crear secciones raras»).

## 2. Acordes como dato

Reglas de validación del servidor (el nombre del acorde lo calcula siempre el servidor; ver archivo 08):

| Regla | Resultado |
| --- | --- |
| Agregar acorde de guitarra con `notes`, `frets`, `strings` | `200`; el acorde recibe `id` propio y `instrument = guitar`; `name` calculado por el servidor |
| Acorde de piano | `frets = null`, `strings = null`; con `frets` o `strings` no nulos → `422` |
| `frets` y `strings` de distinto largo que `notes` | `422` |
| `strings` fuera de 1..6 | `422` |
| Traste `-1` o `25` | `422`; `0` y `24` válidos (las cuerdas que no suenan no figuran en `strings`) |
| `notes` con valor fuera de 0..127, o `notes = []` | `422` |
| Una sola clase de altura (`[48, 60]`) | `422` (mínimo 2 clases de altura distintas) |
| `notes = [48, 55]` | `200`; `name = "C5"` |
| `instrument = "bass"` (u otro) | `422` |
| Guitarra cuyos `frets`/`strings` no producen las `notes` con la afinación estándar | `422` |
| Guitarra con dos notas en la misma cuerda (`strings` repetidas) | `422` |
| El cliente envía `name` | `422` |
| Dos acordes con el mismo `name` y distinta digitación | Permitido: son versiones del mismo acorde (distinto `id`) |
| Editar `notes` | `name` recalculado; los demás acordes se renombran si cambia la tonalidad |
| **Borrar un acorde** | Desaparece de `chords`; todas sus ubicaciones `{col, chord_id}` desaparecen de la letra; las de otros acordes y el texto quedan intactos; una línea instrumental queda como `{ "text": "", "chords": [] }`; `chords` y `lyrics` suben de versión y cada una crea una revisión |

## 3. Tablaturas

- Seis cuerdas, edición **manual**, sin generación automática. Ingresar notas debe ser cómodo (teclado, flechas, técnicas).
- `tuning`: 6 notas, de aguda a grave, por defecto `["E4","B3","G3","D3","A2","E2"]`. Cada nota cumple `^[A-G](#|b)?[0-9]$` (`"D#3"`, `"Eb3"`, `"C0"` válidas; `"H9"`, `"E"`, `"e4"`, `"E10"` inválidas). 5 o 7 elementos → `422`.
- Cada columna tiene exactamente 6 celdas (5 o 7 → `422`). `columns = []` es válido. Si no se envía `title`, el servidor usa «Tablatura N» (N = posición).

### Gramática de una celda

Una celda es **vacía**, **`x`**, **`|`** (barra de compás), o **un traste 0-24 seguido de hasta 3 transiciones y opcionalmente un vibrato final**.

| Elemento | Regla |
| --- | --- |
| Vacía | `""` válida |
| `x` | Nota apagada. `X` mayúscula → `422` en el backend (el editor normaliza a `x` antes de enviar) |
| Traste | `0` a `24`. `25` o `-1` → `422`. Sin ceros a la izquierda (`03` → `422` en el backend; el editor normaliza a `3`) |
| Técnicas con segundo traste | `h` hammer-on, `p` pull-off, `b` bend, `r` release, `/` slide ascendente, `\` slide descendente, `s` slide. **Exigen un traste destino** (`3h5`, `5p3`, `7b9`, `9r7`, `3/5`, `5\3`, `3s5`). Sin segundo traste (`3h`, `5p`, `7b`, `9r`, `3/`, `5\`, `3s`) → `422`. Técnica sin traste inicial (`h5`) → `422`. Técnica inexistente (`3q5`) → `422`. Segundo traste fuera de rango (`3h25`) → `422` |
| Vibrato | `~` o `v`. **No lleva segundo traste** (`5~`, `5v` válidos; `5~7`, `5v7` → `422`). Solo puede ir al final |
| Encadenadas | Hasta **3 transiciones** por celda: `5h7p5`, `5h7p5~`, `3/5/7`, `7b9r7` válidas. `1h2h3h4h5` (4 transiciones), `5~h7` (vibrato no final), `5h7~~`, `5hp7`, `5h7p25` → `422` |
| Barra `\|` | Ocupa las **6 cuerdas** de su columna: `["\|","\|","\|","\|","\|","\|"]` válida; mezclar `\|` con trastes en una columna → `422` |
| Otros | `abc`, `1.5`, número no string, `x5`, `\|\|`, `"3 "`, `" 3"` → `422` |

Estos casos se implementan dos veces: validador del backend (estricto) y validador del editor (normaliza y nunca permite escribir una celda inválida).

### Teclado del editor de tablaturas (mapa aprobado el 2026-10-18)

El editor **nunca** permite escribir una celda inválida: la tecla que la volvería inválida se ignora.

| Tecla / situación | Efecto |
| --- | --- |
| `←` / `→` | Mueve el cursor a la columna anterior/siguiente; la cuerda no cambia |
| `↑` / `↓` | Mueve a la cuerda anterior/siguiente, sin pasar de los bordes (cuerda 1 arriba, cuerda 6 abajo) |
| Dígitos | Forman el traste: dos dígitos se combinan si el resultado es ≤ 24 (`1` `2` → `12`); si pasaría de 24 (`3` `5` → `35`), el segundo dígito **reemplaza** al primero y empieza un traste nuevo (la celda queda en `5`). Sobre un `0`, `5` → `5` (sin ceros a la izquierda) |
| Letras de técnica (`h p b r / \ s`) | Se agregan a la celda; ignoradas si no hay traste antes, si ya hay 3 transiciones, o si ya hay vibrato (el vibrato va al final). `3` `h` `5` → `3h5` |
| `~` / `v` | Vibrato al final (`5h7` `p` `5` `~` → `5h7p5~`) |
| `x` (o `X`) | La celda queda `x` |
| `\|` | Las 6 celdas de la columna quedan `\|` |
| `Espacio` | Inserta una columna vacía a la derecha del cursor y el cursor salta a ella |
| `Backspace` | Borra el último carácter: `3h5` → `3h` → `3` → vacía |
| `Supr` | Vacía la celda; la columna sigue existiendo |
| `Shift` + `Supr` | Elimina la columna; el cursor queda en la nueva columna en esa posición |
| `Esc` | El editor pierde el foco; no modifica ninguna celda |
| Celda incompleta (`3h`) | Puede moverse el cursor, pero la celda se marca incompleta y no se envía hasta completarla o borrarla |

## 4. Letra

- Se guarda como líneas con acordes ubicados (modelo en archivo 04). Se pueden **maximizar** y tienen **desplazamiento automático** con velocidad ajustable (comportamiento visual sin reglas medibles definidas).
- `lyrics = null` si no hay letra; borrar la letra la deja en `null`.
- Validaciones: una línea puede ser instrumental (`text = ""` con acordes); `col` mayor que el largo del texto es válido; `col` negativo → `422`; `chord_id` que no existe en los acordes de **esa** canción → `422`; dos ubicaciones en la misma `col` de una línea → `422`; una línea con texto y sin acordes es válida.
- Cada ubicación conserva su `chord_id`, de modo que se distinguen versiones del mismo nombre. La letra **no guarda nombres**: el nombre mostrado sale del acorde actualizado.
- Los acordes se ubican sobre la letra incluyendo espacios vacíos, se filtran por instrumento, y se muestran en carrusel si son muchos. Al pasar el cursor sobre un acorde de la letra se ve la forma exacta con la que se toca.

## 5. Tareas

- Lista de pendientes común y corriente: agregar, marcar como hecha (`done`), editar el título y borrar.
- `title` de 1 a 200 caracteres tras recortar espacios; vacío o solo espacios → `422`; `done` que no sea booleano → `422`. Cada tarea recibe `id` propio.

## 6. Revisiones y concurrencia

Secciones versionadas: `lyrics`, `chords`, `tabs`, `tasks`, `meta`. **Las demos no se versionan** (subir o borrar una demo no crea revisión ni cambia `section_versions`).

- **Los cambios se guardan explícitamente** («guardar cambios»). Cada sección que cambia sube su versión y crea una revisión (foto completa del contenido, con `author_id`). Una sección enviada **sin cambios reales** no crea revisión ni sube la versión: el servidor compara el contenido normalizado y no confía en el cliente.
- Se puede guardar varias secciones a la vez: una revisión por cada una.
- **Versión base obligatoria** por sección guardada; sin ella → `422`. El control es **por sección**: guardar `chords` con su base vigente funciona aunque otra persona haya cambiado `lyrics`.
- **Conflicto de versión:** guardar con una base desactualizada → `409 version_conflict` y el contenido de la otra persona permanece. Dos guardados concurrentes con la misma base: exactamente uno `200` y otro `409` (atomicidad).
- **Guardado de varias secciones (decisión del autor, que reemplazó la propuesta de todo-o-nada del agente):** se guardan las secciones sin conflicto y se informan las desactualizadas. Respuesta `200` con `saved = [{section, version}]` y `conflicts = [{section, current_version}]`, para que la interfaz avise que esa sección estaba desactualizada. Una sección que dependería de otra no guardada (p. ej. una letra que usa un acorde nuevo cuya sección de acordes tuvo conflicto) tampoco se guarda y se reporta. Si **todas** las secciones enviadas están en conflicto → `409 version_conflict` y nada cambia.
- **`meta`** = `title`, `status`, `tempo`, `time_signature`, `key`, `key_mode`. Cambiar la visibilidad **no** crea revisión de `meta` (es una acción del dueño aparte de «guardar cambios»).
- **Restaurar** una versión: copia la foto al estado actual y genera una **revisión nueva** (ej.: con versiones 1..4, restaurar la 2 crea la 5 con ese contenido; las 1..4 siguen existiendo). Versión inexistente → `404`.
- **Retención (2026-10-18): las últimas 50 revisiones por sección.** Al guardar la 51.ª se borra la más antigua; las otras secciones no se tocan; restaurar una versión fuera de la retención → `404`.
- **Quién ve y quién restaura:** las ven (listan y leen) todas las personas con **acceso propio** a la canción, incluidos los lectores (con autores solo como `username` y `display_name`); **restauran los editores** (un lector recibe `403`); un autenticado sin acceso propio (aunque la canción sea pública) recibe `404`; un anónimo por `/songs/{id}` recibe `401`. **El enlace público no expone el historial** (no existe ruta de historial bajo `/c/`).

## 7. Operaciones de tonalidad

- `key_mode = auto`: agregar, editar o borrar un acorde recalcula `key`. Elegir una tonalidad entre las candidatas → `200`; elegir otra → `422` (para otra tonalidad, pasar a `manual`).
- `key_mode = manual`: la tonalidad no cambia al agregar acordes; cambiarla a mano recalcula los nombres de todos los acordes.
- `manual` → `auto`: regla de conservar o reiniciar con aviso (archivo 08, sección 6).
- Sin acordes en `auto`: `key = null`.

## 8. Entradas manuales del usuario (lista del autor)

Crear un usuario; crear una canción; agregar acordes, letra, tareas, tablaturas y demos; cambiar el estado de una canción; agregar acordes sobre la letra (incluyendo espacios vacíos); editar/borrar letra, acordes, tareas, tablaturas y comentarios de demos; agregar comentarios a una demo; cambiar el título y la tonalidad; crear una banda; crear/borrar invitación a canción/banda; guardar cambios a una canción; cambiar nombre de usuario. Entradas agregadas el 2026-10-18: cambiar email y contraseña (siempre con la contraseña actual; cambiar la contraseña cierra las demás sesiones), ver y cerrar sesiones propias, usar un enlace de invitación, quitar integrantes / cambiar su rol / abandonar, transferir una banda y mover una canción personal a una banda.

Origen: `tests_md/canciones_secciones.md`; `archivos/conceptos_datos.md`; `archivos/entradas_manuales.md`; `archivos/restricciones.md`; `AGENTS.md`; Engram 262, 291, 292.
