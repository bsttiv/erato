# 04 - Modelo de datos (conceptos y relaciones)

Describe los **conceptos** del dominio y sus relaciones, tal como los diseñó el autor (`archivos/conceptos_datos.md`, con sus revisiones aprobadas). La traducción física a MongoDB (colecciones, tipos, índices) está en el archivo 05. Las reglas de acceso y de acción están en el archivo 06.

Regla de trabajo: cualquier cambio de modelo (colecciones, campos, índices, relaciones, validaciones o migraciones) exige propuesta y aprobación explícita del autor (archivo 02, regla 1). El modelo antiguo (`bd_vieja.md`) **no es** el vigente; solo sirve para la migración (archivo 12).

## 1. Decisiones transversales

- **Campos polimórficos:** una sola colección de invitaciones con «tipo destino» (canción o banda) e «ID destino»; la canción tiene «tipo dueño» (usuario o banda) e «ID dueño». Motivo: el backend debe saber a qué colección apunta un ID y permite índices `(tipo, id)` para las consultas de permisos. Aprobado el 2026-10-17.
- **Visibilidad = `private | public`** combinada con el tipo de dueño. «Modo banda» es `owner_type = band`, no un valor de visibilidad (reemplaza una idea anterior de tres niveles privada/banda/pública). Aprobado el 2026-10-17.
- **Acceso por membresía:** quien tiene acceso a una canción o banda lo tiene porque existe un documento de membresía (el dueño tiene acceso implícito). Un enlace de invitación sin usar no da acceso.
- **Todos los miembros de una banda son editores** de todas sus canciones. No existe rol de lector en las bandas; la invitación a banda no lleva rol. (El agente había extrapolado un «lector de banda»; el autor lo corrigió el 2026-10-17.)

## 2. Conceptos

### Usuario
ID; email; **nombre de usuario** (único; editable por el usuario; en la migración se genera desde el nombre visible normalizado, p. ej. `Juan Pérez` → `juan-perez`, con sufijo numérico si choca); **nombre visible** (para todo el mundo); contraseña (hasheada con Argon2). Formato y límites de cada campo: archivo 07.

### Sesión
ID; refresh token; fecha de acceso; dispositivo de acceso. Un usuario posee una o varias sesiones. La sesión sigue en el modelo de datos pero la emisión de tokens es de Maestro (mock mientras no esté listo). El refresh token nunca se guarda en claro, solo su hash.

### Banda
ID; nombre; ID del dueño.

### Canción
ID; nombre (título); estado (`idea`, `in_progress`, `ready`: «idea», «en progreso» o «lista»); fecha de creación; fecha de actualización; tempo (opcional); tonalidad (opcional); **modo de tonalidad** (automático o manual; las canciones migradas quedan en manual); **privacidad** (privada o pública; ver archivo 06); **slug compartido** (opcional, único; existe solo mientras la canción es pública; se usa en el enlace `/c/{slug}`; se conserva desde el modelo antiguo); métrica (opcional); tipo de dueño (usuario o banda); ID de dueño (usuario o banda).

### Tarea
ID; título; estado (en el esquema físico se representa como `done: bool`).

### Acorde
ID; nombre; notas; trastes; cuerdas; instrumento (guitarra o piano). «Trastes» y «Cuerdas» se mantienen como **dos campos** (arreglos paralelos), no un arreglo fusionado (el autor rechazó el `frets[6]` fusionado). Un mismo acorde puede tener **varias versiones (formas)** con el mismo nombre; se distinguen por ID.

### Demo
ID; título; duración; subida por; fecha de subida; otros campos necesarios para conectar con Cloudinary.

### Comentario (de demo)
ID; subido por; fecha de subida; timestamp (instante del audio); comentario (texto).

### Letra (revisión 2026-10-17, aprobada)
Se guarda **línea por línea**; cada línea lleva sus acordes ubicados por columna de caracteres. Reemplaza al campo «contenido».

- ID de canción.
- `lines`: lista de líneas, cada una con `text` (puede ser vacío) y `chords`: lista de `{ col, chord_id }`.
- `section` (revisión 2026-10-31, aprobada): string opcional de una línea, de 1 a 40 caracteres, que nombra una parte de la canción. Una línea con `section` tiene `text` vacío y `chords` vacío, y no se agrega `section: null` a las demás. Sin índices nuevos y sin migración. Una sección instrumental es una línea con `text` vacío y sus acordes, normalmente después de una línea con `section`.
- **Pasajes instrumentales:** línea con `text: ""` y solo acordes. `col` puede superar el largo del texto.
- `chord_id` referencia un acorde **concreto** (con sus trastes y cuerdas): distingue versiones del mismo acorde y permite mostrar su forma al pasar el cursor. Los nombres se resuelven desde el acorde, por lo que **se actualizan si cambia la tonalidad**.
- **Al borrar un acorde se eliminan también sus ubicaciones en la letra.**

```json
{ "_id": "...", "song_id": "...",
  "lines": [
    { "text": "", "chords": [{ "col": 0, "chord_id": "a1" }, { "col": 6, "chord_id": "a2" }] },
    { "text": "Fly me to the moon", "chords": [{ "col": 0, "chord_id": "a3" }, { "col": 11, "chord_id": "a4" }] }
  ] }
```

### Tablatura (revisión 2026-10-17, aprobada)
Una grilla de columnas. Reemplaza a «cuerdas», «tabs» y «contenido».

- `title`: nombre de la tablatura.
- `tuning`: afinación de las 6 cuerdas, **de aguda a grave** (por defecto `["E4","B3","G3","D3","A2","E2"]`).
- `columns`: lista de columnas; cada columna tiene **6 celdas** (de cuerda aguda a grave).
- Gramática de celdas y teclado del editor: archivo 09.

```json
{ "_id": "...", "title": "Riff intro",
  "tuning": ["E4","B3","G3","D3","A2","E2"],
  "columns": [["","","","","3",""], ["","","","","3h5",""], ["|","|","|","|","|","|"]] }
```

### Revisión (agregado 2026-10-17, aprobado)
Historial de cambios **por sección**, como fotos completas.

- ID; ID de canción; sección (`lyrics`, `chords`, `tabs`, `tasks` o `meta`); versión (entero incremental por canción y sección); ID de autor; fecha de creación; contenido (foto completa de la sección en esa versión).
- Al «guardar cambios» se crea una revisión **solo por cada sección que cambió**; la canción mantiene el estado actual. Restaurar copia la foto al estado actual y genera una revisión nueva. **Las demos no se versionan.** Índice `(ID canción, sección, versión desc)`.
- Retención y acceso: archivo 09.

### Invitación (revisión 2026-10-18, aprobada)
Es un **enlace de uso múltiple**; el acceso se guarda aparte, en la membresía. Reemplaza la versión original (con invitado nominal y estados enviada/aceptada/rechazada/revocada, descartada).

- ID; tipo destino (`song` o `band`) e ID destino.
- Rol: `editor` o `viewer` (lector) si el destino es una canción; `null` si es una banda.
- Hash del token (sha256). El token se muestra **una sola vez**, al crear el enlace; el enlace es `/i/{token}`.
- ID de quien lo creó; fecha de expiración (por defecto 7 días, configurable por variable de entorno) y fecha de creación.
- **Sin estado:** revocar un enlace es borrar el documento. No existe «rechazada» (no usar un enlace no es rechazarlo).
- Cualquier número de personas puede usar el mismo enlace mientras sea válido. Un enlace vencido o inexistente responde `404`.
- Quién puede crear un enlace: solo quien tenga derecho de editor sobre el destino.

### Membresía (agregado 2026-10-18, aprobado)
Registra quién tiene acceso a una canción o banda.

- ID; tipo destino (`song` o `band`) e ID destino; ID de usuario.
- Rol: `editor` o `viewer` en canciones (copiado del enlace); `null` en bandas.
- ID de la invitación (enlace) usada: **solo histórico**, porque el enlace puede haberse borrado o vencido; es `null` si la membresía no nació de un enlace (p. ej. el dueño anterior tras transferir una banda).
- Fecha de ingreso.
- Se crea cuando un usuario **autenticado** usa un enlace válido. Quitar a un integrante es borrar su membresía. No puede haber dos membresías al mismo destino (usar el enlace con acceso previo → `409 already_member`). Ser miembro de una banda es tener una membresía con `target_type = band`; el dueño de la banda conserva acceso implícito de editor sin membresía.

### Intento de login fallido (revisión 2026-10-18, aprobada; concepto técnico)
Hash del email, IP y fecha. Con 5 intentos fallidos del mismo email e IP en 15 minutos, el login se bloquea para ese par hasta que venza la ventana; los intentos se borran solos a los 15 minutos o al iniciar sesión con éxito. Detalle: archivo 07.

## 3. Relaciones

- Un usuario posee una o varias sesiones.
- Una banda posee uno o varios usuarios (miembros).
- Una canción posee 0 o varias tareas, 0 o varias tablaturas, 0 o 1 letra, 0 o varias demos, 0 o varios acordes y 0 o varias revisiones por sección.
- Una demo tiene 0 o varios comentarios.
- Un usuario tiene acceso a 0 o varias canciones.
- **Revisión 2026-10-18:** donde el texto original dice «invitaciones» como forma de acceso, léase «membresías». Un usuario tiene membresías a 0 o varias canciones y bandas; un enlace de invitación (de uso múltiple) puede originar 0 o varias membresías; una canción o banda posee 0 o varios enlaces vigentes.

Los comentarios y las revisiones **crecen sin cota**; por eso viven en colecciones propias (archivo 05).

Origen: `archivos/conceptos_datos.md`; `archivos/esquema_mongodb.md`; `AGENTS.md`; Engram 261, 262, 266, 267, 274, 281.
