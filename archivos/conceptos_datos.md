# Conceptos de datos

Este archivo contiene la estructura de la base de datos en general, de la forma en que lo pensé. Posteriores revisiones (cualquier tipo de cambio) deben ser anotadas posteriormente en su sección respectiva.

## Usuarios

Un usuario de Erato se compone de los siguientes campos
- ID
- Email
- Nombre de usuario (único; editable por el usuario; en la migración se genera desde el nombre visible normalizado, ej. `Juan Pérez` → `juan-perez`, con sufijo numérico si choca)
- Nombre visible (para todo el mundo)
- Contraseña (hasheada con Argon)

## Sesión

Una sesión de un usuario se modela así

- ID
- Refresh Token
- Fecha acceso
- Dispositivo acceso

## Banda

Una banda se modela de la siguiente forma

- ID
- Nombre
- ID del dueño

## Canción

Una canción se estructura así

- ID
- Nombre
- Estado (idea, en progreso o lista)
- Fecha creación
- Fecha actualización
- Tempo (opcional)
- Tonalidad (opcional)
- Modo tonalidad (automático o manual; las canciones migradas del modelo antiguo quedan en manual)
- Privacidad (privada o pública). Canción personal privada: la ven el dueño y sus invitados. Canción de banda privada: la ven todos los miembros de la banda y los invitados. Pública: cualquiera con el enlace
- Slug compartido (opcional, único; existe solo mientras la canción es pública; se usa en el enlace `/c/{slug}` y se conserva desde el modelo antiguo)
- Métrica (opcional)
- Tipo dueño (usuario o banda)
- ID dueño (banda o usuario)

## Tarea

Una tarea se modela así

- ID
- Título
- Estado

## Acordes

- ID
- Nombre
- Notas
- Trastes
- Cuerdas
- Instrumento (guitarra o piano)

## Demos

- ID
- Titulo
- Duración
- Subida por
- Fecha subida
- otros campos necesarios para conectar con Cloudinary

## Comentario

- ID
- subido_por
- fecha subida
- Timestamp
- Comentario

## Letras

- ID
- contenido

> **Revisión (2026-10-17, aprobada):** la letra se guarda línea por línea; cada línea lleva sus acordes ubicados por columna de caracteres.
>
> - ID canción
> - `lines`: lista de líneas, cada una con `text` (puede ser vacío) y `chords`: lista de `{ col, chord_id }`. Reemplaza a «contenido».
> - `section` (revisión 2026-10-31, aprobada): campo opcional de una línea, de 1 a 40 caracteres, que nombra una parte de la canción (`Estrofa`, `Coro`, `Puente`). Una línea con `section` no lleva texto ni acordes. Las canciones existentes no requieren migración.
> - Pasajes instrumentales: línea con `text: ""` y solo acordes. `col` puede superar el largo del texto.
> - `chord_id` referencia un acorde concreto (con sus trastes y cuerdas), lo que distingue versiones del mismo acorde y permite mostrar su forma al pasar el cursor. Los nombres se resuelven desde el acorde, por lo que se actualizan si cambia la tonalidad.
> - Al borrar un acorde se eliminan también sus ubicaciones en la letra.
>
> ```json
> { "_id": "...", "song_id": "...",
>   "lines": [
>     { "text": "", "chords": [{ "col": 0, "chord_id": "a1" }, { "col": 6, "chord_id": "a2" }] },
>     { "text": "Fly me to the moon", "chords": [{ "col": 0, "chord_id": "a3" }, { "col": 11, "chord_id": "a4" }] }
>   ] }
> ```

## Tablatura

- ID
- tabs
- cuerdas
- contenido

> **Revisión (2026-10-17, aprobada):** la tablatura se modela como una grilla de columnas.
>
> - `title`: nombre de la tablatura.
> - `tuning`: afinación de las 6 cuerdas, de aguda a grave (por defecto `["E4","B3","G3","D3","A2","E2"]`). Reemplaza a «cuerdas».
> - `columns`: lista de columnas; cada columna tiene 6 celdas (de cuerda aguda a grave). Reemplaza a «tabs». «contenido» se elimina.
> - Cada celda es vacía, `x`, un traste (0–24) seguido opcionalmente de una técnica (`h` hammer-on, `p` pull-off, `b` bend, `r` release, `/` slide ascendente, `\` slide descendente, `s` slide, `~` o `v` vibrato) y otro traste (ej. `3h5`), o `|` como barra de compás.
>   - Revisión (2026-10-18, aprobada): `h`, `p`, `b`, `r`, `/`, `\` y `s` exigen segundo traste (`3h5`); el vibrato (`~`, `v`) no lo lleva (`5~`). Una barra `|` ocupa las 6 cuerdas de su columna. Una celda puede encadenar hasta 3 transiciones (`5h7p5`, `3/5/7`), con el vibrato solo al final (`5h7p5~`).
>
> ```json
> { "_id": "...", "title": "Riff intro",
>   "tuning": ["E4","B3","G3","D3","A2","E2"],
>   "columns": [["","","","","3",""], ["","","","","3h5",""], ["|","|","|","|","|","|"]] }
> ```

## Revisión

> **Agregado (2026-10-17, aprobado):** historial de cambios por sección, como fotos completas.
>
> - ID
> - ID canción
> - Sección (`lyrics`, `chords`, `tabs`, `tasks` o `meta`)
> - Versión (entero incremental por canción y sección)
> - ID autor
> - Fecha creación
> - Contenido (foto completa de la sección en esa versión)
>
> Al «guardar cambios» se crea una revisión solo por cada sección que cambió; la canción mantiene el estado actual. Restaurar copia la foto al estado actual y genera una revisión nueva. Las demos no se versionan. Índice: `(ID canción, sección, versión desc)`. Opcionalmente se conservan solo las últimas N revisiones por sección.
>
> Revisión (2026-10-18, aprobada): se conservan las **últimas 50 revisiones por sección**; al guardar la 51.ª se borra la más antigua. Las ve cualquiera con acceso propio a la canción (incluidos lectores); restauran los editores; el enlace público no expone el historial. Un guardado con varias secciones guarda las que no tienen conflicto e informa al usuario las que estaban desactualizadas.

## Invitación

- ID
- Rol: solo en invitaciones a canción (editor: puede editar cualquier sección; lector: solo puede ver). Las invitaciones a banda no llevan rol: todos los miembros de una banda son editores de todas sus canciones (revisión 2026-10-17, aprobada)
- ID invitado
- Tipo destino (canción o banda)
- ID destino (canción o banda)
- ID quien invita
- Estado (enviada, aceptada, rechazada o revocada); solo una invitación aceptada da acceso. «Rechazada» la marca el invitado; «revocada», quien invita
- Fecha

> **Revisión (2026-10-18, aprobada):** la invitación pasa a ser un **enlace de uso múltiple** y el acceso se guarda aparte, en el concepto «Membresía». Esta revisión reemplaza los campos «ID invitado», «ID quien invita» y «Estado» de arriba.
>
> - ID
> - Tipo destino (`song` o `band`) e ID destino.
> - Rol: `editor` o `viewer` (lector) si el destino es una canción; `null` si es una banda (sin cambios respecto de la revisión 2026-10-17).
> - Hash del token (sha256). El token se muestra una sola vez, al crear el enlace; el enlace es `/i/{token}`.
> - ID de quien lo creó.
> - Fecha de expiración (por defecto 7 días, configurable por variable de entorno) y fecha de creación.
> - Sin estado: revocar un enlace es borrar el documento («Crear/borrar invitación»). No existe «rechazada»: no usar un enlace no es rechazarlo.
> - Cualquier número de personas puede usar el mismo enlace mientras sea válido. Un enlace vencido o inexistente responde `404`.
> - Quién puede crear un enlace no cambia: solo quien tenga derecho de editor sobre el destino.

## Membresía

> **Agregado (2026-10-18, aprobado):** registra quién tiene acceso a una canción o banda.
>
> - ID
> - Tipo destino (`song` o `band`) e ID destino.
> - ID usuario.
> - Rol: `editor` o `viewer` en canciones (copiado del enlace); `null` en bandas.
> - ID de la invitación (enlace) usada; es solo histórico, porque el enlace puede haberse borrado o vencido.
> - Fecha de ingreso.
>
> Se crea cuando un usuario autenticado usa un enlace válido. Quitar a un integrante es borrar su membresía. Un usuario no puede tener dos membresías al mismo destino (usar el enlace con acceso previo responde `409 already_member`). Ser miembro de una banda es tener una membresía con `target_type = band`; el dueño de la banda conserva acceso implícito de editor sin membresía. Todos los miembros de una banda siguen siendo editores de todas sus canciones.

## Reglas de acción (revisión 2026-10-17, aprobada)

- **Invitar** a una canción o banda: solo quien tenga derecho de editor sobre ella.
- **Cambiar la visibilidad** y **borrar** una canción: solo el dueño (en una canción de banda, el dueño de la banda).
- **Canción pública sin acceso propio:** se lee solo por el enlace `/c/{slug}`, en modo solo lectura y sin exponer IDs internos (`_id`, IDs de usuarios, claves de Cloudinary); por su ID responde `404`. Objetivo: reducir la superficie de ataque (revisión 2026-10-17, aprobada).

> Revisión (2026-10-18, aprobada) — integrantes y enlaces:
> - **Quitar a un integrante** de una canción: solo el dueño (en una canción de banda, el dueño de la banda). **Quitar a un miembro** de una banda: solo el dueño de la banda.
> - **Cambiar el rol** de un integrante de canción (editor ↔ lector): solo el dueño (en una canción de banda, el dueño de la banda).
> - **Abandonar:** cualquier integrante puede irse por su cuenta; el dueño de la banda no puede irse sin transferirla antes.
> - **Borrar un enlace:** quien lo creó o el dueño (de la canción o de la banda).
> - **Quien pierde el derecho de editor** sobre un destino (lo quitan, se va, pasa a lector o deja la banda) pierde en ese momento los enlaces que creó para ese destino; las membresías ya creadas con ellos se conservan.
> - **Transferir una banda:** solo el dueño, de forma directa y sin aceptación, a un miembro actual; el dueño anterior queda como miembro.
> - **Enlaces:** sin límite de usos; vigencia global de 7 días, configurable.

> Revisión (2026-10-18, aprobada) — **Intento de login fallido** (nuevo concepto técnico): hash del email, IP y fecha. Con 5 intentos fallidos del mismo email e IP en 15 minutos, el login se bloquea para ese par hasta que venza la ventana; los intentos se borran solos a los 15 minutos o al iniciar sesión con éxito.

# Relaciones

- Un usuario posee una o varias sesiones
- Una banda posee uno o varios usuarios
- Una canción posee 0 o varias tareas
- Una canción posee 0 o varias tablaturas
- UNa canción posee 0 o 1 letra
- Una canción posee 0 o varias demos
- Una canción posee 0 o varios acordes
- Una demo tiene 0 o varios comentarios
- Una canción posee 0 o varias revisiones por sección
- Un usuario tiene acceso a 0 o varias canciones
- Un usuario puede tener cero o varias invitaciones a una o varias canciones

> **Revisión (2026-10-18, aprobada):** donde dice «invitaciones» como forma de acceso, léase «membresías». Un usuario tiene membresías a 0 o varias canciones y bandas; un enlace de invitación (de uso múltiple) puede originar 0 o varias membresías, y una canción o banda posee 0 o varios enlaces vigentes.
