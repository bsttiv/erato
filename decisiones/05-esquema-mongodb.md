# 05 - Esquema físico de MongoDB

Esquema aprobado por el autor el 2026-10-17, con las decisiones adicionales del 2026-10-18 (enlaces de invitación, membresías, intentos de login). Se basa en los conceptos del archivo 04.

## 1. Convenciones

- Nombres de colecciones y campos en inglés `snake_case`.
- IDs: `ObjectId`. Fechas: `datetime` UTC (el cliente de MongoDB se usa con fechas conscientes de zona horaria).
- Los subdocumentos embebidos también llevan `id` para poder referenciarlos. La convención del esquema dice `id` de tipo `ObjectId`, pero los documentos de ejemplo los muestran como cadenas (`"a1"`, `"t1"`, `"k1"`, `"d1"`); el tipo exacto queda como contradicción en el archivo 15.
- Sin validadores `$jsonSchema` en MongoDB: la validación ocurre solo en la aplicación (decisión del autor, 2026-10-24).
- Los índices se crean **al iniciar la aplicación**, de forma idempotente (decisión del autor, 2026-10-24). Los tests exigen que los índices del esquema aprobado existan antes de correr.
- Las referencias son `ObjectId` guardados en el documento; MongoDB no impone integridad referencial.

## 2. Resumen de colecciones

| Colección | Contenido | Por qué separada |
| --- | --- | --- |
| `users` | Cuentas | Entidad raíz |
| `sessions` | Metadatos de sesión (Maestro emite los tokens) | Crece por dispositivo; expira |
| `login_attempts` | Intentos de login fallidos | Expiran solos a los 15 minutos (TTL) |
| `bands` | Bandas | Entidad raíz |
| `invitations` | Enlaces de invitación de uso múltiple a canción o banda | Expiran solos (TTL) y se borran al revocar |
| `memberships` | Quién tiene acceso a una canción o banda | Se consulta desde el usuario y desde el destino |
| `songs` | Canción **con sus secciones embebidas**: acordes, tablaturas, letra, tareas y metadatos de demos | Una sola lectura arma la página completa |
| `demo_comments` | Comentarios con timestamp | Crecen sin límite |
| `revisions` | Fotos por sección | Crecen con cada guardado |

**Decisión central (embebido vs. referencias):** las secciones de una canción se leen siempre juntas («todo en la misma página») y son chicas (texto y listas cortas), así que van embebidas en `songs`. Comentarios y revisiones crecen sin cota, por eso van en colecciones propias. El límite de 16 MB por documento queda muy lejos (los audios viven en Cloudinary, no en Mongo).

## 3. `users`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `email` | string | minúsculas, único |
| `username` | string | minúsculas, único, editable |
| `display_name` | string | |
| `password_hash` | string | Argon2id (`$argon2id$v=19$m=19456,t=2,p=1$...` en el ejemplo) |
| `created_at` | datetime | |
| `updated_at` | datetime | |

```json
{
  "_id": "ObjectId",
  "email": "juan@example.com",
  "username": "juan-perez",
  "display_name": "Juan Pérez",
  "password_hash": "$argon2id$v=19$m=19456,t=2,p=1$...",
  "created_at": "2026-10-17T20:00:00Z",
  "updated_at": "2026-10-17T20:00:00Z"
}
```

- Índices: `email` único; `username` único.
- Proyección pública: solo `username` y `display_name`.
- La migración **no** copia `token_version` (campo del modelo antiguo).

## 4. `sessions`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | Es el `id` que ve el cliente en `GET /me/sessions` |
| `user_id` | ObjectId | |
| `jti` | string | Enlaza con Maestro (para revocar) |
| `refresh_token_hash` | string | SHA-256; el refresh token nunca se guarda en claro |
| `device` | string | Etiqueta derivada del `User-Agent` (p. ej. «Firefox en Linux») |
| `last_access_at` | datetime | A lo sumo una escritura por minuto |
| `created_at` | datetime | |
| `expires_at` | datetime | Vencimiento del refresh token (7 días); se renueva en cada refresh |

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "jti": "uuid-del-par-de-tokens",
  "refresh_token_hash": "sha256...",
  "device": "Firefox en Linux",
  "last_access_at": "2026-10-17T20:00:00Z",
  "created_at": "2026-10-17T20:00:00Z",
  "expires_at": "2026-10-24T20:00:00Z"
}
```

- Índices: `user_id` (listar dispositivos); `jti` único; TTL sobre `expires_at` (`expireAfterSeconds = 0`).

## 5. `login_attempts`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `email_hash` | string | SHA-256 del email normalizado |
| `ip` | string | Sale de `X-Forwarded-For` |
| `created_at` | datetime | |

```json
{ "_id": "ObjectId", "email_hash": "sha256 del email normalizado", "ip": "203.0.113.7", "created_at": "2026-10-18T20:00:00Z" }
```

- Un documento por intento de login fallido (también con emails inexistentes). Reglas de bloqueo: archivo 07.
- Índices: `(email_hash, ip, created_at)`; TTL sobre `created_at` de 15 minutos (`expireAfterSeconds = 900`).

## 6. `bands`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `name` | string | |
| `owner_id` | ObjectId | |
| `created_at`, `updated_at` | datetime | |

```json
{ "_id": "ObjectId", "name": "Los Faroles", "owner_id": "ObjectId",
  "created_at": "...", "updated_at": "..." }
```

- La membresía **no** se embebe: un miembro es quien tiene un documento en `memberships` con `target_type = band`. El dueño tiene acceso implícito de editor.
- Índice: `owner_id`.

## 7. `invitations`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `target_type` | string | `song` \| `band` |
| `target_id` | ObjectId | |
| `role` | string \| null | `editor` \| `viewer` si `target_type = song`; `null` si `band` |
| `token_hash` | string | SHA-256 del token |
| `created_by` | ObjectId | |
| `expires_at` | datetime | |
| `created_at` | datetime | |

```json
{
  "_id": "ObjectId",
  "target_type": "song",
  "target_id": "ObjectId",
  "role": "editor",
  "token_hash": "sha256 del token",
  "created_by": "ObjectId",
  "expires_at": "2026-10-25T00:00:00Z",
  "created_at": "..."
}
```

- Es el **enlace** `/i/{token}`, de uso múltiple. El token se muestra una sola vez al crearlo; solo se guarda su hash.
- Sin campo de estado: revocar es borrar físicamente el documento. No existe el estado «rechazada».
- Vigencia por defecto de 7 días, configurable por una variable de entorno (se documenta en `.env.example` al implementar; el nombre no está fijado en las fuentes). Si la variable es inválida (no numérica o ≤ 0), el servidor **no arranca** y reporta un error de configuración claro (INV-060).
- Índices: `token_hash` único; `(target_type, target_id)`; TTL sobre `expires_at` (`expireAfterSeconds = 0`). Además de la purga por TTL, la validez se comprueba en la aplicación: el enlace vale solo mientras `ahora < expires_at`.

## 8. `memberships`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `target_type` | string | `song` \| `band` |
| `target_id` | ObjectId | |
| `user_id` | ObjectId | |
| `role` | string \| null | copiado del enlace; `null` si `band` |
| `invitation_id` | ObjectId \| null | solo histórico; `null` si no nació de un enlace |
| `joined_at` | datetime | |

```json
{
  "_id": "ObjectId",
  "target_type": "song",
  "target_id": "ObjectId",
  "user_id": "ObjectId",
  "role": "viewer",
  "invitation_id": "ObjectId",
  "joined_at": "..."
}
```

- Se crea cuando un usuario autenticado usa un enlace válido. Quitar a un integrante es borrar su documento.
- Índices: único `(target_type, target_id, user_id)` (usar un enlace con acceso previo → `409 already_member`); `(user_id, target_type)` («mis bandas» y «compartidas conmigo»).

## 9. `songs`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `owner_type` | string | `user` \| `band` |
| `owner_id` | ObjectId | |
| `title` | string | Obligatorio, no vacío tras recortar |
| `status` | string | `idea` \| `in_progress` \| `ready` |
| `tempo` | int \| null | Opcional |
| `key` | string \| null | Opcional |
| `key_mode` | string | `auto` \| `manual` |
| `time_signature` | string \| null | Opcional |
| `visibility` | string | `private` \| `public` |
| `share_slug` | string \| null | `null` mientras sea privada |
| `chords` | array | Ver abajo |
| `tablatures` | array | Ver abajo |
| `lyrics` | object \| null | `{ lines: [...] }`; `null` si no hay letra |
| `tasks` | array | `{ id, title, done }` |
| `demos` | array | Solo metadatos; el archivo vive en Cloudinary |
| `section_versions` | object | `{ lyrics, chords, tabs, tasks, meta }` |
| `created_at`, `updated_at` | datetime | |

```json
{
  "_id": "ObjectId",
  "owner_type": "user",
  "owner_id": "ObjectId",
  "title": "Bajo el farol",
  "status": "in_progress",
  "tempo": 92,
  "key": "Am",
  "key_mode": "auto",
  "time_signature": "4/4",
  "visibility": "private",
  "share_slug": null,
  "chords": [
    { "id": "a1", "name": "C", "instrument": "guitar",
      "notes": [48, 52, 55, 60, 64],
      "frets": [3, 2, 0, 1, 0], "strings": [5, 4, 3, 2, 1] }
  ],
  "tablatures": [
    { "id": "t1", "title": "Riff intro",
      "tuning": ["E4","B3","G3","D3","A2","E2"],
      "columns": [["","","","","3",""], ["|","|","|","|","|","|"]] }
  ],
  "lyrics": {
    "lines": [
      { "text": "", "chords": [{ "col": 0, "chord_id": "a1" }] },
      { "text": "Bajo el farol", "chords": [{ "col": 0, "chord_id": "a1" }] }
    ]
  },
  "tasks": [ { "id": "k1", "title": "Grabar bajo", "done": false } ],
  "demos": [
    { "id": "d1", "title": "Toma 1", "duration_s": 183.4,
      "cloudinary_public_id": "erato/songs/<song_id>/<user_id>/<uuid>",
      "format": "mp3",
      "mime_type": "audio/ogg", "size_bytes": 2400000,
      "uploaded_by": "ObjectId", "uploaded_at": "..." }
  ],
  "section_versions": { "lyrics": 3, "chords": 5, "tabs": 1, "tasks": 2, "meta": 1 },
  "created_at": "...",
  "updated_at": "..."
}
```

Subcampos y reglas:

- **Acordes (`chords[]`):** `id`, `name`, `instrument` (`guitar` \| `piano`), `notes`, `frets`, `strings`. `notes` son números MIDI (la más grave es el bajo). `frets` (traste de cada nota) y `strings` (cuerda de cada nota, 1 = aguda ... 6 = grave) son **arreglos paralelos del mismo largo**; ambos `null` para piano. `name` se guarda **ya calculado por el algoritmo** (archivo 08) y se recalcula en cada cambio; el cliente no puede enviarlo.
- **Tablaturas (`tablatures[]`):** `id`, `title`, `tuning` (6 notas), `columns` (cada columna con 6 celdas). Gramática: archivo 09.
- **Letra (`lyrics`):** ver archivo 04.
- **Tareas:** «Estado» se representa como `done: bool`.
- **Demos (`demos[]`):** `id`, `title`, `duration_s`, `cloudinary_public_id`, `format`, `mime_type`, `size_bytes`, `uploaded_by`, `uploaded_at`. El archivo comprimido vive en Cloudinary bajo `cloudinary_public_id`.
- **`section_versions`:** versión vigente de cada sección. Enlaza con `revisions` y además sirve de **control de concurrencia optimista**: si dos editores guardan la misma sección a la vez, el segundo recibe un conflicto en vez de pisar el trabajo del primero.
- `tempo`, `key`, `time_signature`: opcionales.
- Índices: `(owner_type, owner_id, updated_at desc)` (listar el espacio personal o de banda); `share_slug` **único parcial** (solo cuando existe).

### Validaciones de campo aprobadas (2026-10-18)

| Campo | Regla |
| --- | --- |
| `title` | Obligatorio; vacío o solo espacios → `422` |
| `status` | `idea` \| `in_progress` \| `ready` |
| `visibility` | Solo `private` \| `public` (`band` → `422`) |
| `key_mode` | `auto` \| `manual` |
| `owner_type` | `user` \| `band` |
| `tempo` | De 20 a 400 (19, 401, -5, 0 y 92.5 son inválidos) |
| `time_signature` | `N/D`, N de 1 a 32, D ∈ {1, 2, 4, 8, 16, 32} (`"4/4"`, `"7/8"`, `"12/16"`, `"32/32"` válidos; `"0/4"`, `"33/4"`, `"4/3"`, `"4/64"`, `"x/y"` inválidos) |
| `key` | Las 15 grafías mayores `C G D A E B F# C# F Bb Eb Ab Db Gb Cb` y las 15 menores `Am Em Bm F#m C#m G#m D#m A#m Dm Gm Cm Fm Bbm Ebm Abm` (`"H#"`, `"c"`, `"E#"`, `"Fb"`, `"Cbm"`, `"A#"` inválidas) |
| Tareas `title` | De 1 a 200 caracteres tras recortar (los espacios de los extremos se recortan) |

## 10. `demo_comments`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `song_id` | ObjectId | |
| `demo_id` | ObjectId | `id` de la demo embebida |
| `author_id` | ObjectId | Siempre el usuario autenticado |
| `timestamp_s` | float | Entre 0 y `duration_s` inclusive |
| `text` | string | De 1 a 2000 caracteres tras recortar |
| `created_at`, `updated_at` | datetime | |

```json
{ "_id": "ObjectId", "song_id": "ObjectId", "demo_id": "ObjectId",
  "author_id": "ObjectId", "timestamp_s": 42.5, "text": "Acá entra la batería",
  "created_at": "...", "updated_at": "..." }
```

- Índice: `(song_id, demo_id, timestamp_s)`. Al borrar una demo se borran sus comentarios.

## 11. `revisions`

| Campo | Tipo | Notas |
| --- | --- | --- |
| `_id` | ObjectId | |
| `song_id` | ObjectId | |
| `section` | string | `lyrics` \| `chords` \| `tabs` \| `tasks` \| `meta` |
| `version` | int | Incremental por canción y sección |
| `author_id` | ObjectId | |
| `created_at` | datetime | |
| `content` | any | Foto completa de la sección en esa versión |

```json
{ "_id": "ObjectId", "song_id": "ObjectId", "section": "lyrics", "version": 3,
  "author_id": "ObjectId", "created_at": "...", "content": { "lines": [] } }
```

- Índice **único** `(song_id, section, version desc)`.
- Nota de nombres: la sección de tablaturas se llama `tabs` en `section`/`section_versions`, y el campo de la canción se llama `tablatures`.
- `meta` agrupa `title`, `status`, `tempo`, `time_signature`, `key`, `key_mode`; `visibility` no entra en `meta`.

## 12. Resolución de permisos (consultas)

1. **Dueño:** `songs.owner_type = user` y `owner_id = yo`; o canción de una banda de la que soy dueño o miembro (`memberships` con `target_type = band`).
2. **Miembro de la canción:** `memberships` con `target_type = song`, `user_id = yo` → su `role`.
3. **Miembro de la banda dueña** (`memberships` con `target_type = band`): editor de todas las canciones de la banda. Si la canción es de banda y `private`, la ven y editan todos los miembros; nadie fuera de la banda la ve salvo miembros de la canción.
4. **`visibility = public`:** cualquiera puede ver vía `share_slug`.

## 13. Decisiones aprobadas

**2026-10-17:** (1) secciones embebidas en `songs`; (2) «Trastes» y «Cuerdas» como dos campos (`frets`, `strings`), no un arreglo fusionado; (3) tareas con `done: bool`; (4) `section_versions` como control de concurrencia optimista; (5) `visibility` solo admite `private` \| `public`; «modo banda» es `owner_type = band`.

**2026-10-18:** (1) `invitations` pasa a ser un enlace de uso múltiple (`/i/{token}`), con token guardado como hash sha256, sin estado y con TTL sobre `expires_at` (7 días por defecto, configurable por variable de entorno); (2) nueva colección `memberships` para el acceso a canciones y bandas, que reemplaza los estados `sent`/`accepted`/`rejected`/`revoked`; (3) revocar un enlace o quitar a un integrante es borrar el documento correspondiente; (4) usar un enlace con acceso previo (incluidos los dueños) responde `409 already_member`, un token vencido o inexistente `404 not_found` y sin sesión `401 not_authenticated`; (5) nueva colección `login_attempts` (5 por `email_hash` + `ip` en 15 minutos → `429 rate_limited`, con TTL de 15 minutos).

**2026-10-24 (perfil-backend):** índices creados al iniciar la app; sin validadores de MongoDB; sin cambios de esquema respecto de lo aprobado.

Origen: `archivos/esquema_mongodb.md`; `tests_md/canciones_secciones.md`; `tests_md/invitaciones.md`; `tests_md/demos.md`; `openspec/changes/perfil-backend/{exploration,design}.md`; Engram 266, 281, 287, 291.
