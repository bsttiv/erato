# 12 - Migración desde Atlas conservando los audios de Cloudinary

Estado: plan aprobado el 2026-10-17 y 2026-10-18 (`archivos/arquitectura.md`, `tests_md/migracion.md`). **Sirve solo si se migran los datos del modelo antiguo** (`bd_vieja.md`, rama `preview`, 2026-10-11, base actual en Atlas). Si el nuevo repositorio parte de cero sin datos, este archivo es referencia. El script es `backend/migrate.py` y sus tests, `backend/tests/test_migration.py`. **No se ha ejecutado contra datos reales.**

**Decisión aprobada el 2026-10-31:** el autor eligió reutilizar los audios existentes de Cloudinary, conservando sus `cloudinary_public_id`. No se copian, descargan, comprimen ni suben de nuevo. Esta decisión reemplaza los pasos anteriores hacia R2. El autor también aprobó la adaptación de los tests y el detalle de lectura de metadatos de la sección 5 para su implementación local; no hay autorización para ejecutar la migración ni inspeccionar los datos remotos.

## 1. Contexto

El autor tiene datos del modelo antiguo de Erato en Atlas y audios en **Cloudinary**. La aplicación nueva conserva Cloudinary y reutilizará esos mismos archivos. Es posible que haya cambiado alguna relación entre conceptos. La condición de que `bands` e `invitations` estén vacías debe verificarse antes de migrar, como exige el plan aprobado.

## 2. Modelo antiguo (referencia)

| Entidad | Tipo | Descripción |
| --- | --- | --- |
| `users` | Colección | `_id`, `email`, `password_hash`, `display_name`, `token_version`, `created_at` |
| `refresh_tokens` | Colección | `_id`, `user_id`, `token_hash`, `family_id`, `revoked`, `expires_at`, `created_at` |
| `bands` | Colección | `_id`, `name`, `owner_id`, `pending_transfer`, `created_at`, `updated_at` |
| `band_members` | Embebida en `bands` | `user_id`, `role` (`owner` \| `member`) |
| `invitations` | Colección | Invitaciones a unirse a una banda: `target {type=band, id}`, `token_hash`, `created_by`, `expires_at`, `created_at` |
| `compositions` | Colección | `_id`, `owner_id`, `band_id` (opcional), `band_editable`, `title`, `visibility` (`private` \| `public`), `share_slug` (solo si es pública), `key`, `bpm`, `time_signature`, `style_tags`, `status` (`idea` \| `in_progress` \| `ready`), `sections_enabled`, `section_revs`, `created_at`, `updated_at` |
| `composition_members` | Embebida en `compositions` | `user_id`, `role` (`editor` \| `viewer`) |
| `chords` / `tablature` / `lyrics` | Embebidas en `compositions` | `chords {instrument, entries[]}`; `tablature {strings, content, tabs[]}`; `lyrics {content}` |
| `todos` | Embebida | `id`, `text`, `done` |
| `demos` | Embebida | `demo_id`, `cloudinary_public_id`, `title`, `duration_s`, `uploaded_by`, `uploaded_at` |
| `composition_comments` | Colección | `_id`, `composition_id`, `demo_id`, `author_id`, `timestamp_s`, `text`, `created_at` |
| `section_revisions` | Colección | `_id`, `composition_id`, `section` (`lyrics` \| `chords` \| `tablature`), `rev`, `content`, `author_id`, `created_at` |

Formatos heredados observados (Engram 285): hashes Argon2id en formato PHC reutilizables; **no hay `username`**; los acordes guardaban `{instrument por composición, entries[{bar, notes MIDI, name}]}` y los trastes se perdían por un defecto del esquema; la letra es ChordPro en línea (`[Am7]texto`) con los acordes ubicados desde la paleta de la sección de acordes; las tablaturas eran casi idénticas a la grilla nueva (barra literal `|`, técnicas `hpbrs/\~xv`); acceso antiguo: dueño > miembros (`editor`|`viewer`) > miembro de banda (editor si `band_editable`, si no lector) > visor público; `share_slug` de `token_urlsafe(16)` y URL `/c/{slug}`; invitaciones antiguas: enlaces reutilizables de banda con TTL de 14 días; `pending_transfer` era la transferencia de propiedad; revisiones `section_revisions` de las últimas 50; demos en Cloudinary como video autenticado.

## 3. Plan de migración (aprobado el 2026-10-17)

- **Script único e idempotente**: lee la base antigua y escribe en una base **nueva** del mismo cluster. La base antigua y los archivos de Cloudinary **no se tocan** hasta validar la migración (huella de la base antigua idéntica antes y después; solo lecturas en Cloudinary).
- **Modo prueba primero** (sin escribir ni descargar): reporta los formatos heredados (acordes con `frets`, letra como string suelto, tablaturas heredadas, etc., con cantidad e IDs de composición), lista las demos (IDs de Cloudinary y cantidad), muestra qué `username` recibirán sufijo, y **se detiene si `bands` o `invitations` de la base antigua no están vacías** (hoy no existen bandas). La ejecución real repite la verificación.
- **Criterio de dato irrepresentable (2026-10-18):** si un dato antiguo no se puede representar fielmente en el modelo nuevo, el modo prueba lo reporta (con ID de composición y motivo) y la ejecución real **se detiene sin escribir nada**; el autor corrige el dato en origen y vuelve a correr.
- Se **conservan los `ObjectId` antiguos** (`songs._id` = `_id` de la composición).
- La ejecución real se **niega a correr** si la base nueva contiene documentos cuyo `_id` no existe en la antigua (datos creados por usuarios).
- **Una sola ejecución con la base en uso:** el script también se niega si un documento migrado cambió en la base nueva, para no pisar ediciones hechas en la aplicación.
- Reanudación por idempotencia (sin mecanismo de checkpoint): una corrida interrumpida se completa sin duplicar lo ya migrado; una segunda corrida no duplica documentos ni agrega sufijos nuevos a los `username`. Cloudinary no recibe escrituras: se reutilizan los mismos identificadores.

## 4. Mapeo por concepto

### Usuarios
- El hash Argon2id se copia **tal cual** (byte a byte); el login con la contraseña antigua debe funcionar en la app nueva.
- `email` a minúsculas; dos emails que coinciden al pasarlos a minúsculas → criterio de dato irrepresentable.
- `username` se **genera** desde el nombre visible: minúsculas, sin acentos, `ñ` → `n`, todo lo que no sea `[a-z0-9]` → `-`, guiones colapsados y sin extremos, de **3 a 30 caracteres** (se recorta a 30; si queda con menos de 3 o vacío, `usuario`). Si choca, sufijo `-2`, `-3`, ...: el original queda para el de `created_at` más antiguo (empate por `_id` menor). Ejemplos: `Juan Pérez` → `juan-perez`; `Ñandú & Cía.` → `nandu-cia`; tres nombres que normalizan igual dan tres `username` distintos. Esta misma normalización define el formato del `username` de la app.
- `token_version` no se migra; solo los campos del esquema aprobado (`email`, `username`, `display_name`, `password_hash`, fechas).
- `refresh_tokens` antiguos se **descartan** (`sessions` queda vacía); los usuarios vuelven a iniciar sesión vía Maestro.

### Canciones
- `public` → pública; `private` → privada. `share_slug` se conserva solo para las públicas; un slug residual en una privada se descarta.
- `key_mode = manual`; `key` se conserva.
- `bpm` → `tempo`; se conservan `time_signature`, `status`, `title`, `created_at`, `updated_at`; se descartan `band_editable`, `style_tags`, `sections_enabled`, `section_revs`.
- `owner_type = user` con el dueño antiguo. Una composición con `band_id` no nulo (sin bandas en la base) se migra como personal y aparece en el reporte.
- `section_versions = 1` en todas las secciones (incluidas las vacías); `revisions` tiene un documento versión 1 solo para las secciones **no vacías**. **No se migra el historial antiguo** de revisiones: el estado actual de cada sección queda como versión 1.

### Membresías
- `composition_members` (editor/viewer) → membresía de canción (`target_type = song`) con el mismo rol, `invitation_id = null`, `joined_at` = fecha de la migración. Si el miembro es el dueño, se omite. Un miembro duplicado produce una sola membresía.
- `band_members` e invitaciones antiguas no se mapean (la migración se detiene si no están vacías).

### Acordes
- Las notas MIDI se **conservan**; los nombres se **recalculan** con el algoritmo (archivo 08). Cada acorde nuevo recibe `id` propio y único y el `instrument` de su sección.
- Para guitarra sin trastes se **deduce una digitación** (el modelo antiguo no guardaba trastes): la más cómoda = una nota por cuerda, notas ascendentes de la cuerda 6 a la 1 (se pueden saltar cuerdas), **menor apertura** (máximo 4 trastes entre el menor y el mayor traste pisado, sin contar cuerdas al aire); empate → posición más baja en el mástil; luego más cuerdas al aire. Determinista. Ejemplos: C `[48,52,55,60,64]` → `frets [3,2,0,1,0]`, `strings [5,4,3,2,1]`; Am `[45,52,57,60,64]` → `frets [0,2,2,1,0]`, `strings [5,4,3,2,1]`; Em `[40,47,52,55,59,64]` → `frets [0,2,2,0,0,0]`, `strings [6,5,4,3,2,1]`.
- Piano: `frets = null`, `strings = null`.
- Acorde heredado con `frets` coherentes con sus `notes` (afinación estándar): se usan esos `frets`. Si contradicen las notas, o si un acorde de guitarra no tiene digitación tocable (7 notas, fuera del rango, apertura > 4): criterio de dato irrepresentable.

### Tablaturas
- Se conservan casi tal cual: cada barra `|` pasa a una **columna de seis `|`**; afinación estándar por defecto `["E4","B3","G3","D3","A2","E2"]`.
- `strings != 6`, tablatura solo con `content` (texto) o una celda que no cumple el patrón nuevo → criterio de dato irrepresentable (el reporte indica tablatura, columna y cuerda). Toda tablatura migrada cumple el patrón del archivo 09.

### Letra (ChordPro → líneas)
- `[Am7]Fly me to the [Dm7]moon` → una línea con `text = "Fly me to the moon"` y `chords = [{col 0, chord_id(Am7)}, {col 14, chord_id(Dm7)}]`. El texto queda sin los acordes, con los espacios tal cual, y `col` se mide en ese texto. Una línea solo con acordes `"[C] [G]"` → `text = " "`, `chords = [{col 0, C}, {col 1, G}]`. Una línea vacía → `{ "text": "", "chords": [] }`. Una letra como string suelto se interpreta igual que `content`. Sin letra → `lyrics = null`.
- El `chord_id` se empareja por el **nombre antiguo** del acorde en la sección de acordes. Un acorde inexistente → criterio de dato irrepresentable (el reporte indica composición, línea y nombre). Dos acordes con el mismo nombre → el primero en el orden de la sección, y se reporta.

### Demos y comentarios
- Cada demo **reutiliza el archivo existente y su `cloudinary_public_id`**, sin copia ni modificación en Cloudinary. Se conservan `title`, `uploaded_by` y `uploaded_at`. El detalle propuesto para completar los metadatos del esquema vigente está en la sección 5.
- El `id` de la demo nueva es el `demo_id` antiguo (para conservar comentarios). Los comentarios (`composition_comments`) pasan a `demo_comments` con `song_id`, el mismo `demo_id`, `author_id`, `timestamp_s`, `text`, `created_at`.
- **Fallos:** reintenta con espera creciente; a la tercera falla seguida **se detiene** con error; al volver a correr continúa sin duplicar.
- No depende de la compresión de demos, que sigue en pausa (archivo 10).
- **Consecuencia aceptada al reutilizar:** después de habilitar la aplicación nueva, borrar una demo elimina el mismo archivo al que apunta la aplicación antigua. No habrá una copia independiente para recuperar ese audio. Durante la migración, el origen y los archivos siguen siendo de solo lectura.

## 5. Adaptación aprobada el 2026-10-31

No se agregan campos, colecciones ni índices. Se propone completar los campos ya aprobados de cada demo con la respuesta de la Admin API, no con datos enviados por el navegador:

| Campo destino | Tipo vigente | Origen propuesto |
| --- | --- | --- |
| `id` | `ObjectId` | `demo_id` antiguo, sin cambiar |
| `cloudinary_public_id` | `string` | Identificador antiguo exacto, sin renombrar ni exigir el prefijo de las subidas nuevas |
| `format` | `string` | `format` leído de Cloudinary |
| `mime_type` | `string` | Mapeo de formatos vigente en `backend/app/demos.py` |
| `size_bytes` | `int` | `bytes` leído de Cloudinary |
| `duration_s` | `float` | `duration` leído de Cloudinary |
| `title`, `uploaded_by`, `uploaded_at` | Tipos del esquema vigente | Valores antiguos, sin cambiar |

Ejemplo de los metadatos afectados (los identificadores son ilustrativos):

```json
{
  "id": {"$oid": "507f1f77bcf86cd799439011"},
  "cloudinary_public_id": "legacy/demo-01",
  "format": "wav",
  "mime_type": "audio/wav",
  "size_bytes": 64044,
  "duration_s": 2.0
}
```

Se propone consultar cada archivo como `resource_type: video`, `type: authenticated`, con metadatos ampliados y `has_audio: true`, como en la integración verificada. Si un identificador no se puede leer así o sus metadatos no permiten representarlo en el modelo vigente, se reporta para revisión del autor: no se cambia su visibilidad, no se sustituye el archivo y no se omite la demo silenciosamente. Las reglas de prevalidación y detención sin escritura del plan aprobado siguen vigentes. Los reintentos pasan a cubrir la lectura de metadatos, no descargas ni compresión.

La ejecución remota requiere autorización separada del autor para el cluster, las bases origen/destino, la cuenta Cloudinary, las operaciones y las credenciales que se usarán. La autorización anterior para audios sintéticos no cubre datos existentes. Propuesta de tests: sección «Adaptación a Cloudinary» de `tests_md/migracion.md`.

## 6. Compatibilidad de IDs de demos — aprobada el 2026-10-31

La exploración encontró una contradicción que la propuesta anterior no contempló: `bd_vieja.md` define `demos.demo_id` y `composition_comments.demo_id` como `string`, pero el esquema vigente y las rutas de demos exigen `ObjectId`. Conservar el texto literalmente solo es representable como `ObjectId` si ese texto es compatible. No se inspeccionaron datos remotos para suponer que todos lo son.

**Decisión:** mantener el esquema vigente, sin campos ni índices nuevos. Si el ID antiguo es un texto ObjectId válido, convertirlo al `ObjectId` equivalente. En caso contrario, derivar un `ObjectId` nuevo y estable a partir de la composición y del identificador antiguo; la misma pareja siempre produce el mismo resultado en las reejecuciones. Usar esa correspondencia tanto en `songs.demos[].id` como en `demo_comments.demo_id`. Una colisión se reporta en la prevalidación y detiene la ejecución sin escrituras. La base de origen no se modifica y `cloudinary_public_id` permanece intacto.

| Campo | Tipo destino sin cambios | Ejemplo ilustrativo de correspondencia |
| --- | --- | --- |
| `songs.demos[].id` | `ObjectId` | `"take-01"` → `ObjectId("507f1f77bcf86cd799439011")` |
| `demo_comments.demo_id` | `ObjectId` | El mismo `ObjectId` asignado a esa demo |
| `songs.demos[].cloudinary_public_id` | `string` | `"legacy/demo-01"` → `"legacy/demo-01"` |

El ObjectId del ejemplo solo ilustra el tipo y la referencia compartida, no especifica el resultado de una función de derivación. MIG-091/MIG-092 se ajustan y MIG-091b se agrega en `tests_md/migracion.md`. Esta regla prevalece sobre la frase «sin cambiar» de la sección 5.

## 7. Corrección tras el modo prueba real — aprobada el 2026-10-31

El 2026-10-31 se ejecutó el modo prueba, de solo lectura, contra la base `erato`: 4 usuarios, 13 composiciones, 88 acordes, 15 demos y 52 comentarios. No hay comentarios huérfanos. Esta corrección prevalece sobre las secciones anteriores:

- **Guitarra:** `notes` antiguo contiene seis trastes de la cuerda 6 a la 1, con `-1` en las mudas. Se convierten a `notes` MIDI, `frets` y `strings` nuevos, conservando la digitación exacta. Con esta regla, los 88 acordes son válidos. Se elimina la deducción de digitación.
- **Tonalidad:** las 11 composiciones sin `key` pasan a `key_mode = auto` con la primera candidata (`null` sin acordes). Las que tienen `key` siguen en `manual`.
- **Formato `opus`:** se agrega al mapeo vigente con `mime_type = audio/ogg`. También lo aceptarán las subidas nuevas.

Tests: sección «Corrección tras el modo prueba real» de `tests_md/migracion.md`.

Origen: `archivos/arquitectura.md` (revisión 2026-10-17); `tests_md/migracion.md`; `bd_vieja.md`; Engram 264, 265, 285.
