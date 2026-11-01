# 11 - Bandas, invitaciones y membresías

Estado: aprobado por el autor (2026-10-17 y 2026-10-18). `restricciones.md` exige que las invitaciones a canciones y bandas funcionen apropiadamente y se prueben en profundidad.

## 1. Modelo vigente (enlaces de uso múltiple + membresías)

- Las invitaciones son **solo enlaces de uso múltiple** (`/i/{token}`); no hay invitaciones nominales ni estados. Revocar = borrar el documento.
- El token se muestra **una sola vez** al crearlo (respuesta del `POST`, junto con la URL `/i/{token}`); en la base solo existe su hash SHA-256. Consultas posteriores muestran metadatos (destino, rol, vencimiento, creador), nunca el token.
- Cualquier número de personas puede usar el mismo enlace mientras sea válido. **Sin límite de usos.** No usar un enlace no es rechazarlo.
- **Vigencia global de 7 días**, configurable por una variable de entorno; no se elige por enlace. El enlace vale solo mientras `ahora < expires_at` (un enlace con `expires_at` igual al instante de la petición ya no vale). La validez se comprueba en la aplicación, no solo con el TTL de MongoDB.
- Si la variable de vigencia es inválida (no numérica o ≤ 0), el servidor no arranca y reporta un error de configuración claro; no usa el valor por defecto en silencio.
- Rol: `editor` o `viewer` (lector) para canciones (obligatorio al crear; ausente o `null` → `422`; `admin` → `422`); `null` para bandas (un rol en un enlace a banda → `422`). Un tipo de destino inválido → `422`; destino inexistente → `404`.
- Los campos `created_by`, `token_hash`, `expires_at`, `created_at` no los envía el cliente (`422`); `created_by` es siempre el usuario autenticado.
- **El acceso lo da solo la membresía.** Tener enlaces creados o sin usar no cuenta como acceso.

## 2. Quién puede crear y borrar enlaces

- **Crear:** solo quien tenga derecho de editor sobre el destino.
  - Destino canción: dueño de la canción personal, miembro `editor` de la canción y, si es de banda, el dueño de la banda y cualquier miembro.
  - Destino banda: dueño de la banda y cualquier miembro (un enlace creado por un miembro tiene el mismo efecto que el del dueño).
  - Miembros `viewer` → `403`; usuarios sin relación o que solo ven la canción por slug → `404`; anónimo → `401`.
- **Borrar un enlace:** quien lo creó, o el dueño (de la canción o de la banda) → `204`. Otro editor que no lo creó → `403`. `404` si ya no existe o si quien pide no puede ver el destino. Borrar un enlace **no** quita las membresías ya creadas con él.
- Borrar una banda: fuera de alcance (no figura en `entradas_manuales.md`).

## 3. Usar un enlace

| Situación | Resultado |
| --- | --- |
| Usuario autenticado sin acceso, enlace válido | `201`; se crea la membresía (`target_type`, `target_id`, `user_id`, `role` copiado del enlace o `null`, `invitation_id`, `joined_at`) |
| Sin sesión | `401 not_authenticated`; no se crea membresía |
| Token vencido, inexistente o de un destino borrado | `404 not_found` |
| Ya tiene acceso (miembro, o dueño de la canción o de la banda), con cualquier rol | `409 already_member`; la membresía existente no cambia (no se modifica el rol) |
| Dos peticiones concurrentes del mismo usuario | Una `201` y otra `409 already_member` (índice único); una sola membresía |
| Dos usuarios a la vez | `201` ambos |

- Usar un enlace a una canción de banda siendo de fuera de la banda crea una membresía **de canción** (no de banda): esa persona no ve otras canciones de la banda ni la banda.
- Usar un enlace a la banda da acceso de editor a todas sus canciones, incluidas las creadas después.
- Un enlace sigue funcionando para usarse de nuevo si el integrante fue quitado y el enlace sigue válido (acceso restituido con el rol del enlace).
- La membresía **sobrevive** al enlace (vence, se purga o se borra).

## 4. Integrantes: quitar, cambiar rol, abandonar

- **Quitar a un integrante de una canción:** solo el dueño de la canción (en canción de banda, el dueño de la banda) → `204`. Un editor no dueño → `403`; un `viewer` → `403`; un ajeno → `404`; anónimo → `401`. Quitar a quien ya no es integrante → `404`. El dueño no puede quitarse a sí mismo (no tiene membresía: acceso implícito) → `404`.
- **Quitar a un miembro de una banda:** solo el dueño de la banda. Otro miembro → `403`. El miembro quitado pierde acceso a todas las canciones privadas de la banda; si además es miembro de una canción concreta, conserva ese acceso.
- Los efectos son **inmediatos, sin caché**: en la petición siguiente la canción responde `404`.
- **Cambiar el rol** (editor ↔ lector) de un integrante de canción: solo el dueño de la canción (en canción de banda, el dueño de la banda). Un editor que lo intenta → `403`; un rol inválido (`admin`) → `422`; el cambio rige desde la petición siguiente.
- **Abandonar:** cualquier integrante borra su propia membresía (`204`); pierde acceso a lo privado. El **dueño de una banda no puede abandonarla** sin transferirla antes: `409 owner_must_transfer`; sigue siendo dueño.
- **Listar miembros de una canción:** muestra solo `username`, `display_name` y rol de cada miembro (sin email ni IDs internos de usuario); solo lo piden quienes pueden ver la canción. Lo mismo para los miembros de una banda.
- «Mis bandas»: aparecen las bandas con membresía; una banda con enlace sin usar o con membresía quitada no aparece.

## 5. Enlaces de quien pierde el derecho de editor

Regla aprobada el 2026-10-18 (el autor eligió el borrado en cascada en lugar de comprobar al usar el enlace, con pruebas exhaustivas): **cuando alguien pierde el derecho de editor sobre un destino, se borran en ese momento los enlaces que creó para ese destino.** Se prueba cada camino por el que se pierde el derecho:

- Lo quitan del destino; se va por su cuenta; su rol pasa de editor a lector (los enlaces `editor` y `viewer` que había creado desaparecen y sigue siendo miembro `viewer`); lo quitan de la banda o se va de la banda (se borran sus enlaces a la banda **y** a las canciones de la banda).
- Si vuelve a ser editor y crea un enlace, y luego vuelve a ser lector, ese enlace también se borra.
- Los enlaces de otros creadores, los enlaces del mismo creador a **otros** destinos (otra canción, otra banda) y las membresías ya creadas con los enlaces borrados **no cambian** (quien entró con un enlace de `carol` sigue siendo miembro aunque `carol` sea quitada).
- Quitar a alguien que no tiene enlaces no falla.
- **Atomicidad:** quitar al integrante y borrar sus enlaces es una sola operación (si falla a mitad, no cambia nada). Por eso MongoDB local y de pruebas corre como *replica set* de un nodo (transacciones).
- **Carrera** (quitar a `carol` mientras otro usa su enlace): el estado final nunca deja un enlace vigente de `carol`; si el uso llegó antes de la quita, esa membresía es válida; si llegó después, `404`.
- Al **mover** una canción personal a una banda: los enlaces se conservan (los miembros de la banda siguen siendo editores) y las membresías de canción de los miembros de esa banda se borran; se conservan las de ajenos a la banda.
- Al **transferir** la banda, los enlaces del dueño anterior se conservan (sigue siendo editor como miembro).

## 6. Transferencia de una banda

- **Directa, sin aceptación**, solo por el dueño actual y solo **a un miembro actual**.
- Efecto: `bands.owner_id` pasa al nuevo dueño; se borra la membresía de banda del nuevo dueño (su acceso pasa a ser implícito); se crea una membresía de banda para el dueño anterior (`role = null`, `invitation_id = null`). Es inmediato.
- Después, el dueño anterior no cambia visibilidad, no borra canciones ni quita miembros (`403`); el nuevo dueño sí. El dueño anterior puede abandonar la banda (`204`).
- Un miembro que intenta transferirla (a sí mismo o a otro) → `403`; a quien no es miembro → `422`; a sí mismo (el dueño) → `422`; sin cambios parciales si la operación falla a mitad.
- No requiere cambios en el modelo de datos.

## 7. Integridad

- Índices únicos: `invitations.token_hash`; `memberships (target_type, target_id, user_id)`. Insertar directo duplicados es rechazado por el índice.
- Al borrar una canción: se borran sus enlaces y sus membresías; el token de un enlace antiguo responde `404`.
- Resolver permisos de un usuario cuenta solo las membresías (los enlaces no dan acceso).

Origen: `archivos/conceptos_datos.md` (revisiones 2026-10-17 y 2026-10-18); `archivos/esquema_mongodb.md`; `tests_md/invitaciones.md`; `tests_md/permisos.md` (PERM-032, PERM-048 a PERM-059, PERM-077 a PERM-081); Engram 277, 278, 281, 282, 283, 284.
