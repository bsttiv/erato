# Esquema físico de MongoDB — PROPUESTA

> **Estado: aprobado por el autor (2026-10-17).** Se basa en `archivos/conceptos_datos.md`.

Convenciones: nombres de colecciones y campos en inglés `snake_case`; IDs `ObjectId`; fechas `datetime` UTC; los subdocumentos embebidos también llevan `id` (`ObjectId`) para poder referenciarlos.

## Resumen

| Colección | Contenido | Por qué separada |
| --- | --- | --- |
| `users` | Cuentas | Entidad raíz |
| `sessions` | Metadatos de sesión (Maestro emite los tokens) | Crece por dispositivo; expira |
| `login_attempts` | Intentos de login fallidos (límite de intentos) | Expiran solos a los 15 minutos (TTL) |
| `bands` | Bandas | Entidad raíz |
| `invitations` | Enlaces de invitación de uso múltiple a canción o banda | Expiran solos (TTL) y se borran al revocar |
| `memberships` | Quién tiene acceso a una canción o banda | Se consulta desde el usuario y desde el destino |
| `songs` | Canción **con sus secciones embebidas**: acordes, tablaturas, letra, tareas y metadatos de demos | Una sola lectura arma la página completa |
| `demo_comments` | Comentarios con timestamp | Crecen sin límite |
| `revisions` | Fotos por sección | Crecen con cada guardado |

**Decisión central — embebido vs. referencias:** las secciones de una canción se leen siempre juntas («todo en la misma página») y son chicas (texto y listas cortas), así que van embebidas en `songs`. Comentarios y revisiones crecen sin cota, por eso van en colecciones propias. El límite de 16 MB por documento queda muy lejos (los audios viven en Cloudinary, no en Mongo).

## `users`

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

- `email`: string, minúsculas. `username`: string, minúsculas, editable.
- Índices: `email` único; `username` único.
- Proyección pública: solo `username` y `display_name`.

## `sessions`

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "sid": "uuid-de-la-sesion-en-maestro",
  "refresh_token_hash": "sha256...",
  "device": "Firefox en Linux",
  "last_access_at": "2026-10-17T20:00:00Z",
  "created_at": "2026-10-17T20:00:00Z",
  "expires_at": "2026-10-24T20:00:00Z"
}
```

- `sid` enlaza con Maestro: es estable durante toda la sesión y viene en ambos tokens (reemplaza a `jti`, aprobado 2026-11-01). Al crear los índices se eliminan `jti_1` y las filas sin `sid`, y esos usuarios vuelven a iniciar sesión. El refresh token nunca se guarda en claro: solo su hash.
- Índices: `user_id` (listar dispositivos); `sid` único; TTL sobre `expires_at`.

## `login_attempts`

```json
{ "_id": "ObjectId", "email_hash": "sha256 del email normalizado", "ip": "203.0.113.7", "created_at": "2026-10-18T20:00:00Z" }
```

- Un documento por intento de login fallido (también con emails inexistentes). `email_hash` evita guardar el email en claro; `ip` sale de `X-Forwarded-For`.
- Con 5 o más intentos del mismo `email_hash` + `ip` en los últimos 15 minutos, el login responde `429 rate_limited` con `Retry-After`, aunque la contraseña sea correcta. Un login exitoso borra los intentos de ese par. Límite y ventana son constantes en el código.
- Índices: `(email_hash, ip, created_at)`; TTL sobre `created_at` de 15 minutos.

## `bands`

```json
{ "_id": "ObjectId", "name": "Los Faroles", "owner_id": "ObjectId",
  "created_at": "...", "updated_at": "..." }
```

- La membresía **no** se embebe: un miembro es quien tiene un documento en `memberships` con `target_type = band`. El dueño tiene acceso implícito de editor.
- Índice: `owner_id`.

## `invitations`

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

- Es el **enlace** `/i/{token}`, de uso múltiple: cualquier número de personas puede usarlo mientras sea válido. El token se muestra una sola vez, al crearlo; solo se guarda su hash (sha256).
- `target_type`: `song` | `band`. `role`: `editor` | `viewer` cuando `target_type = song`; `null` cuando `target_type = band` (todos los miembros son editores).
- Sin campo de estado: revocar un enlace es borrar físicamente el documento. No existe el estado «rechazada».
- Vigencia por defecto de 7 días, configurable por una variable de entorno (se documenta en `.env.example` al implementar).
- Índices:
  - `token_hash` único.
  - `(target_type, target_id)` — enlaces de un destino.
  - TTL sobre `expires_at` — Mongo borra automáticamente los enlaces vencidos.

## `memberships`

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

- Se crea cuando un usuario autenticado usa un enlace válido; `role` se copia del enlace (`null` si `target_type = band`). `invitation_id` es solo histórico: el enlace puede haberse borrado o vencido. Es `null` cuando la membresía no nació de un enlace (p. ej. el dueño anterior tras transferir una banda) (aclaración 2026-10-18, aprobada).
- Quitar a un integrante es borrar su documento.
- Índices:
  - Único `(target_type, target_id, user_id)` — usar un enlace con acceso previo responde `409 already_member`.
  - `(user_id, target_type)` — «mis bandas» y «compartidas conmigo».

## `songs`

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

- `owner_type`: `user` | `band`. `status`: `idea` | `in_progress` | `ready`. `key_mode`: `auto` | `manual`. `visibility`: `private` | `public` (el alcance de «privada» depende de `owner_type`).
- `tempo`, `key`, `time_signature`: opcionales. `lyrics`: `null` si no hay letra.
- **Acordes:** `notes` son números MIDI (la más grave es el bajo). «Trastes» y «Cuerdas» de los conceptos se mantienen como dos campos: `frets` (traste de cada nota) y `strings` (cuerda de cada nota, 1 = aguda … 6 = grave), arreglos paralelos del mismo largo; ambos `null` para piano. `name` se guarda ya calculado por el algoritmo y se recalcula en cada cambio.
- **Tareas:** «Estado» se representa como `done: bool`.
- **Demos:** solo metadatos; el archivo comprimido vive en Cloudinary bajo `cloudinary_public_id`.
- `section_versions`: versión vigente de cada sección. Enlaza con `revisions` y además sirve de control de concurrencia optimista: si dos editores guardan la misma sección a la vez, el segundo recibe un conflicto en vez de pisar el trabajo del primero.
- Índices:
  - `(owner_type, owner_id, updated_at desc)` — listar el espacio personal o de banda.
  - `share_slug` único parcial (solo cuando existe).

## `demo_comments`

```json
{ "_id": "ObjectId", "song_id": "ObjectId", "demo_id": "d1",
  "author_id": "ObjectId", "timestamp_s": 42.5, "text": "Acá entra la batería",
  "created_at": "...", "updated_at": "..." }
```

- Índice: `(song_id, demo_id, timestamp_s)`.
- Al borrar una demo se borran sus comentarios.

## `revisions`

```json
{ "_id": "ObjectId", "song_id": "ObjectId", "section": "lyrics", "version": 3,
  "author_id": "ObjectId", "created_at": "...", "content": { "lines": [] },
  "summary": "editó la letra de Coro" }
```

- `section`: `lyrics` | `chords` | `tabs` | `tasks` | `meta`.
- `summary`: texto opcional de hasta 120 caracteres que describe el cambio. Lo genera el servidor al comparar la sección antes y después. Las revisiones anteriores a este campo no lo tienen (aprobado por el autor, 2026-10-31).
- Índice único: `(song_id, section, version desc)`.

## Resolución de permisos (consultas)

1. Dueño: `songs.owner_type = user` y `owner_id = yo`, o canción de una banda de la que soy dueño o miembro (`memberships` con `target_type = band`).
2. Miembro de la canción: `memberships` con `target_type = song`, `user_id = yo` → su `role`.
3. Miembro de la banda dueña (`memberships` con `target_type = band`): editor de todas las canciones de la banda. Si la canción es de banda y `private`, la ven y editan todos los miembros; nadie fuera de la banda la ve salvo miembros de la canción.
4. `visibility = public`: cualquiera puede ver vía `share_slug`.

## Decisiones aprobadas (2026-10-17)

1. Secciones embebidas en `songs`.
2. «Trastes» y «Cuerdas» como dos campos (`frets`, `strings`), no un arreglo fusionado.
3. Tareas con `done: bool`.
4. `section_versions` como control de concurrencia optimista.
5. `visibility` solo admite `private` | `public`; «modo banda» es `owner_type = band`, no un valor de visibilidad.

## Decisiones aprobadas (2026-10-18)

1. `invitations` pasa a ser un enlace de uso múltiple (`/i/{token}`), con token guardado como hash sha256, sin estado y con TTL sobre `expires_at` (7 días por defecto, configurable por variable de entorno).
2. Nueva colección `memberships` para el acceso a canciones y bandas; reemplaza los estados `sent`/`accepted`/`rejected`/`revoked`. La membresía de banda es un documento con `target_type = band`.
3. Revocar un enlace o quitar a un integrante es borrar el documento correspondiente.
4. Usar un enlace con acceso previo (incluidos los dueños de la canción o banda) responde `409 already_member`; un token vencido o inexistente, `404 not_found`; sin sesión, `401 not_authenticated`.
5. Nueva colección `login_attempts` para limitar intentos de login fallidos (5 por `email_hash` + `ip` en 15 minutos → `429 rate_limited`), con TTL de 15 minutos.
