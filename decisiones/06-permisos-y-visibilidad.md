# 06 - Permisos y visibilidad

Regla de seguridad: **toda regla de acceso se valida en el servidor en cada petición**; ocultar botones en el frontend no es seguridad. El permiso se evalúa en cada petición, sin caché (PERM-061, PERM-062). Estado: aprobado por el autor (2026-10-17 y 2026-10-18).

## 1. Reglas de visibilidad

- La visibilidad solo puede ser `private` o `public`, combinada con el dueño de la canción (`owner_type` = `user` o `band`).
- **Personal privada:** la ven el dueño y los usuarios que son miembros de la canción.
- **De banda privada:** la ven (y editan) **todos los miembros de la banda** y los miembros de la canción. Nadie fuera de la banda la ve salvo los miembros de la canción. No hay estado adicional para «banda privada».
- **Pública (personal o de banda):** cualquiera con el enlace puede **verla**. Para editar hace falta ser miembro con rol `editor` (o, en canción de banda, miembro de la banda).
- **En todos los niveles, editar requiere** una membresía con rol editor (o ser dueño, o miembro de la banda dueña).
- Solo una **membresía** da acceso: tener un enlace de invitación sin usar, un enlace vencido o borrado, o una membresía quitada no da acceso (actor «IL» en las matrices).
- Ser miembro de una banda **no** da acceso a las canciones personales del dueño de la banda (PERM-017).

## 2. Canción pública: solo por enlace, sin IDs internos

Decisión del autor (2026-10-17), por reducción de la superficie de ataque (defensa en profundidad sobre los permisos del servidor):

- Quien no tiene acceso propio (anónimo o desconocido) lee una canción pública **solo** por `GET /c/{share_slug}`, en modo solo lectura. Por `/songs/{id}` responde `404` (`401` si es anónimo).
- La respuesta por slug **no incluye IDs internos**: ni `_id` de la canción, ni `owner_id`, `uploaded_by`, `author_id` ni `cloudinary_public_id` (la prueba busca recursivamente en todo el JSON). Los autores se muestran solo como `username` y `display_name`.
- **No existe ninguna ruta de escritura bajo `/c/`** (responde `405` o `404`). Tampoco hay historial de revisiones por el enlace público.
- Si la canción pasa a privada, el slug anterior responde `404`; volver a publicarla genera un slug **nuevo**.
- Quien tiene acceso propio (dueño, miembros, invitados con membresía) usa `/songs/{id}`.

### Enlace compartido (slug)

- Se genera al pasar a `public`; `share_slug = null` mientras sea privada. Formato: 22 caracteres URL-safe (`token_urlsafe(16)`), el mismo formato que los slugs del modelo antiguo.
- Único (índice único parcial); varias canciones privadas con `null` coexisten.
- Editar otros campos de una canción pública no cambia el slug. Un cliente no puede enviar su propio `share_slug` (`422`).

## 3. Reglas de acción

| Acción | Quién |
| --- | --- |
| **Invitar** (crear un enlace) a una canción o banda | Solo quien tenga derecho de editor sobre ella: miembro `editor` de la canción, miembro de la banda, dueño de la banda, dueño de la canción personal |
| **Cambiar la visibilidad** y **borrar** una canción | Solo el dueño (en una canción de banda, el dueño de la banda) |
| **Quitar a un integrante** de una canción | Solo el dueño (en una canción de banda, el dueño de la banda) |
| **Quitar a un miembro** de una banda | Solo el dueño de la banda |
| **Cambiar el rol** de un integrante de canción (editor ↔ lector) | Solo el dueño (en una canción de banda, el dueño de la banda) |
| **Abandonar** | Cualquier integrante, por su cuenta; el dueño de la banda no puede irse sin transferirla antes (`409 owner_must_transfer`) |
| **Borrar un enlace** | Quien lo creó, o el dueño (de la canción o de la banda) |
| **Transferir una banda** | Solo el dueño, de forma directa y sin aceptación, a un miembro actual |
| **Mover una canción personal a una banda** | Solo el dueño de la canción, solo a una banda de la que es miembro (ver 5) |
| **Crear una canción en una banda** | Cualquier miembro de la banda |
| **Comentar demos** | Solo editores (dueño, miembros `editor`) y miembros de la banda |

Detalle de enlaces, membresías y transferencias: archivo 11. Detalle de demos y comentarios: archivo 10.

## 4. Matriz de permisos

Actores:

| Código | Actor |
| --- | --- |
| ANON | Anónimo (sin token) |
| EXT | Autenticado sin relación con la canción ni con la banda |
| OWN | Dueño de la canción personal (`owner_type = user`, `owner_id = yo`) |
| SE | Miembro de la canción, `role = editor` |
| SV | Miembro de la canción, `role = viewer` |
| BO | Dueño de la banda dueña de la canción |
| BE | Miembro de la banda (editor): membresía de banda, `role = null` |
| IL | Sin membresía: tiene un enlace sin usar, o su membresía fue quitada, o el enlace expiró o fue borrado |

Acciones: **VER** (canción completa: secciones, demos, comentarios), **EDIT** (editar una sección: acordes, tablaturas, letra, tareas, metadatos), **INV** (crear enlaces de invitación a la canción), **VIS** (cambiar `visibility`), **DEL** (borrar la canción).

Leyenda: **Sí** permitido; **No** denegado (`401 not_authenticated` para ANON en endpoints con sesión; para autenticados, `404 not_found` si no puede ver la canción y `403 forbidden` si la ve pero no puede realizar la acción). `VER` de ANON y EXT en canciones públicas es **solo** vía `/c/{share_slug}`.

### `owner_type = user`, `visibility = private`

| Actor | VER | EDIT | INV | VIS | DEL |
| --- | --- | --- | --- | --- | --- |
| ANON | No | No | No | No | No |
| EXT | No | No | No | No | No |
| OWN | Sí | Sí | Sí | Sí | Sí |
| SE | Sí | Sí | Sí | No | No |
| SV | Sí | No | No | No | No |
| IL | No | No | No | No | No |
| BO / BE | equivalen a EXT | | | | |

### `owner_type = user`, `visibility = public`

| Actor | VER | EDIT | INV | VIS | DEL |
| --- | --- | --- | --- | --- | --- |
| ANON | Sí | No | No | No | No |
| EXT | Sí | No | No | No | No |
| OWN | Sí | Sí | Sí | Sí | Sí |
| SE | Sí | Sí | Sí | No | No |
| SV | Sí | No | No | No | No |
| IL | Sí | No | No | No | No |

### `owner_type = band`, `visibility = private`

| Actor | VER | EDIT | INV | VIS | DEL |
| --- | --- | --- | --- | --- | --- |
| ANON | No | No | No | No | No |
| EXT | No | No | No | No | No |
| BO | Sí | Sí | Sí | Sí | Sí |
| BE | Sí | Sí | Sí | No | No |
| SE | Sí | Sí | Sí | No | No |
| SV | Sí | No | No | No | No |
| IL (canción o banda) | No | No | No | No | No |

### `owner_type = band`, `visibility = public`

| Actor | VER | EDIT | INV | VIS | DEL |
| --- | --- | --- | --- | --- | --- |
| ANON | Sí | No | No | No | No |
| EXT | Sí | No | No | No | No |
| BO | Sí | Sí | Sí | Sí | Sí |
| BE | Sí | Sí | Sí | No | No |
| SE | Sí | Sí | Sí | No | No |
| SV | Sí | No | No | No | No |
| IL | Sí | No | No | No | No |

## 5. Casos de permisos con resultado fijado

Política de errores: ver archivo 07, sección 6. Resumen aplicado a canciones:

- Sin sesión → `401`; canción inexistente o ajena que no puede ver → `404` con cuerpo **idéntico** (indistinguible); puede ver pero no actuar → `403`; anónimo con un slug de una canción privada → `404`.
- Un `viewer` que intenta cualquier escritura (secciones, tareas, demos, comentarios, enlaces, visibilidad, borrar) → `403`; la prueba recorre todas las rutas de escritura.
- Un `editor` que intenta cambiar `visibility` (por su ruta o dentro de `meta`) o borrar la canción → `403`.
- Un miembro de banda que borra una canción de banda o cambia su visibilidad → `403` (aunque haya creado la canción): en canción de banda el dueño es el de la banda.
- Un miembro de la canción (no de la banda) que intenta crear un enlace a la **banda** → `404` (no la puede ver).
- Un cliente que envía `owner_id`, `owner_type` o `section_versions` arbitrarios → `422`; la canción no cambia.
- El permiso es **por canción**: ser editor de una no da acceso a otra canción del mismo dueño (`404`).
- **Combinación de roles:** un miembro de la banda que usa un enlace (con cualquier rol) a una canción de esa banda recibe `409 already_member`; no se crea membresía de canción y sigue editando.

### Listados (espacios de trabajo)

- `GET /songs?workspace=personal`: solo canciones cuyo dueño es el usuario (`owner_type = user`); **no** incluye canciones donde es miembro de la canción.
- `workspace=shared` («Compartidas conmigo»): solo canciones por membresía de canción; no incluye canciones propias, canciones con enlace sin usar ni canciones de bandas donde es miembro.
- `workspace=all` («Todas»): propias, compartidas y de todas las bandas del usuario, cada una con su origen (`own`, `shared`, `band`); no incluye canciones con enlace sin usar ni públicas ajenas (esas solo se abren por enlace).
- Listado del espacio de una banda: un no miembro recibe `404`. Orden: `updated_at` descendente.

### Mover una canción personal a una banda

- Solo se mueve de personal a banda, solo por el dueño de la canción y solo a una banda de la que es miembro (miembro que no es dueño de la canción → `403`; no es miembro de la banda → `404`; de banda a personal → `422`).
- Se **borran las membresías de canción de los miembros de esa banda** (ya son editores) y se **conservan** las demás con su rol. Visibilidad, slug, demos, comentarios y revisiones no cambian. Los enlaces y membresías de canción se conservan, salvo las membresías de miembros de esa banda.
- Si la canción trae demos que harían superar la cuota de 2 GB de la banda → `422 quota_exceeded` y no se mueve.

Origen: `archivos/conceptos_datos.md` (reglas de acción); `archivos/autonomo_automatico.md`; `tests_md/permisos.md`; `AGENTS.md` (regla 8); Engram 260, 267, 272, 273, 274, 277, 278, 282, 283.
