# 10 - Demos, comentarios y archivos (Cloudinary)

Estado: aprobado por el autor el 2026-10-18 (`tests_md/demos.md`, `archivos/arquitectura.md`), con una **pausa** posterior: el 2026-10-23 el autor pidió mantener **en pausa** la compresión de demos en el servidor (ver sección 6).

**Revisión del 2026-10-31 (aprobada):** Cloudinary reemplaza a Cloudinary. Esta revisión prevalece sobre cualquier mención anterior a la compresión, a los crudos o a Cloudinary.

## 1. Producto

- Cada composición tiene **su propia lista de demos**; un audio pertenece a **una sola** composición (subir la misma grabación a dos canciones crea dos demos con `id` y `cloudinary_public_id` distintos).
- El usuario **elige cuál reproducir** y puede agregar **comentarios anclados a un timestamp** del audio.
- El servidor **comprime** las demos («minificarlas»); los archivos viven en **Cloudinary** (reemplaza a Cloudinary). En MongoDB solo hay metadatos.
- Las demos **no se versionan**.

## 2. Flujo de subida y reproducción (revisado el 2026-10-31)

Motivo: las Vercel Functions aceptan como máximo **4.5 MB por petición y por respuesta**, así que **el audio nunca pasa por el backend**.

1. El backend firma una subida para `erato/songs/<song_id>/<user_id>/<uuid>`. El secreto nunca sale del servidor.
2. El navegador envía un `POST` multipart directo a Cloudinary, con `resource_type: video` (Cloudinary trata el audio como video) y `type: authenticated`.
3. El cliente confirma con el `public_id`. El backend lee formato, tamaño y duración desde Cloudinary, aplica límites y cuota, y escribe los metadatos.
4. **Entrega privada.** La reproducción usa `private_download_url` con vencimiento de **15 minutos**. No pasa por CDN y consume el doble de ancho de banda; las URLs con token requieren el plan Advanced y las URLs firmadas `authenticated` no vencen.
5. Cloudinary no tiene regla de ciclo de vida: una subida que nunca se confirma queda almacenada. Los recursos rechazados al confirmar se destruyen.

Metadatos de cada demo (`songs.demos[]`): `id`, `title`, `duration_s`, `cloudinary_public_id`, `format`, `mime_type`, `size_bytes`, `uploaded_by`, `uploaded_at`. `cloudinary_public_id` y `format` no aparecen en ninguna respuesta.

## 3. Reglas de la subida

| Regla | Detalle |
| --- | --- |
| Entradas aceptadas | Formatos mp3, wav, ogg, opus, flac, aac, m4a, mp4 y webm, según informe Cloudinary. Se guardan sin recomprimir |
| Límites | Hasta **100 MB** y **20 minutos** de audio. Exceso → `422 validation_error`; el recurso se destruye |
| No es audio (p. ej. un PDF) | `422 validation_error`; el recurso se destruye; nada nuevo en `songs.demos` |
| `duration_s` | La informa Cloudinary; un valor del cliente se ignora |
| Título | Opcional; por defecto «Demo N» (N = posición: con 2 demos, «Demo 3») |
| Renombrar | Permitido a quienes pueden editar (`200`; no cambia `cloudinary_public_id` ni crea revisión); título vacío → `422`; un `viewer` → `403` |
| Quién sube | Quien puede editar. Un `viewer` pide URL de subida o confirma → `403`; no se emite URL |
| Confirmar con el `public_id` de otra persona o de otra canción | `404 not_found`; el recurso no se toca (debe contener la canción y el usuario de quien confirma). Inexistente o ya en uso → `404` |
| Consistencia Cloudinary/MongoDB | Si falla guardar los metadatos: error y se **destruye el recurso**. Cualquier fallo de Cloudinary responde `503 storage_unavailable` |
| Respuestas | `GET /songs/{id}` lista las demos con metadatos; ninguna respuesta incluye credenciales de Cloudinary |

### Cuota de almacenamiento (2026-10-18)

- **2 GB por dueño** (por usuario o por banda), calculada **sumando `size_bytes`** de las demos de sus canciones. El exceso responde `422 quota_exceeded` (se destruye el recurso; sin cambios en `songs.demos`).
- Cuenta la cuota **del dueño de la canción** (si `bob` miembro sube a una canción de banda, cuenta la cuota de la banda, no la de `bob`). Las cuotas de usuario y de banda son independientes. Sin cambio de modelo.
- Mover una canción personal a una banda que superaría su cuota → `422 quota_exceeded` y no se mueve.

## 4. Reproducción y acceso

- Mismas reglas que ver la canción: dueño, miembros (incluido `viewer`) y miembros de banda pueden reproducir; un autenticado ajeno recibe `404`.
- Anónimo en canción pública: pide la demo vía `/c/{share_slug}`; recibe una URL firmada y la respuesta **no expone `cloudinary_public_id`**. Si la canción vuelve a ser privada, deja de emitirse y recibe `404` (las URLs ya emitidas vencen solas a los 15 minutos).
- Una demo pedida por la ruta de otra canción → `404`; demo inexistente → `404`.
- Acceso al bucket sin firma: rechazado (privado). URL firmada usada después de 15 minutos: rechazada por Cloudinary.

## 5. Borrado y comentarios

- **Borrar una demo:** `204`; sale de `songs.demos`; se borran sus comentarios (los de otras demos quedan); el objeto `cloudinary_public_id` se borra en la misma operación. Un `viewer` → `403`; inexistente → `404`. **Borrar la canción** borra los objetos de todas sus demos en Cloudinary.

| Regla de comentarios | Detalle |
| --- | --- |
| Quién comenta | Solo editores (dueño, miembros `editor` de la canción) y miembros de la banda; un `viewer` → `403` (no se crea comentario); quien entra por enlace público solo lee; anónimo → `401` |
| `timestamp_s` | Entre `0` y la duración de la demo, **ambos inclusive**; `-0.1` o mayor que la duración → `422` |
| Texto | De 1 a 2000 caracteres tras recortar espacios de los extremos; vacío o solo espacios → `422` |
| Demo inexistente | `404` |
| Orden al listar | Por `timestamp_s` ascendente; los comentarios de otra demo no aparecen |
| Editar | Solo el **autor** (un editor o el dueño no autores reciben `403`); `updated_at` cambia |
| Borrar | El **autor** o el **dueño** de la canción (en canción de banda, el dueño de la banda) = moderación (`204`); otro editor/miembro no autor → `403` |
| `author_id` | Siempre el usuario autenticado; el que envíe el cliente se ignora |
| Lectura pública | Autores solo con `username` y `display_name` |

## 6. Compresión en pausa (2026-10-23)

El autor pidió mantener la compresión de demos en el servidor **en pausa** (AGENTS.md y Engram 400: «compression on STANDBY»). Lo que sigue vigente y aprobado: el diseño anterior, los casos DEMO-004 a DEMO-006 con `ffmpeg` real, y la imagen del backend con `ffmpeg` y el codificador `libopus` (INFRA-033/034: un WAV de 1.0 s se comprime a Ogg con flujo Opus y duración 1.0 ± 0.1 s). No se define en las fuentes qué se implementa durante la pausa ni cuándo se reanuda (archivo 15). Hay además una tarea previa a implementar demos: **medir** el tiempo y la memoria de `ffmpeg` dentro de una Vercel Function (confirma los límites de 100 MB y 20 minutos).

Decisión del autor (2026-10-30): mientras la compresión siga en pausa, las demos se guardan **sin comprimir**; el paso de confirmar no transcodifica (conserva el formato real, `mime_type` y extensión reales, `size_bytes` real y `duration_s` leída con `ffprobe`).

Origen: `archivos/arquitectura.md` (revisión 2026-10-18); `archivos/autonomo_automatico.md`; `tests_md/demos.md`; `AGENTS.md` (decisiones pendientes); `openspec/config.yaml` (regla de tareas); Engram 289, 400.
