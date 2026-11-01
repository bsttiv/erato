# 07 - Cuentas, sesiones, Maestro y perfil

Cubre registro, inicio de sesión, sesiones con varios dispositivos, el contrato de Maestro (real y mock), el perfil de usuario, la regla de datos públicos, el formato de errores y el límite de intentos.

Estado de las fuentes: las reglas de comportamiento están en `tests_md/auth_sesiones.md` y `tests_md/perfil.md` (aprobadas por el autor el 2026-10-18 y el 2026-10-23). Las **rutas HTTP** de las tablas siguientes se fijaron en la especificación del cambio `perfil-backend` (2026-10-24); en `tests_md/` las rutas se declaran «ilustrativas». La forma exacta de los cuerpos de respuesta la propuso el agente en el diseño de `perfil-backend`; el autor aceptó seis valores por defecto (sección 9) y no consta una aprobación línea por línea del resto. Se marca como **[diseño]** lo que no tiene aprobación explícita del autor.

## 1. Reparto de responsabilidades

- **Maestro** (proyecto propio del autor, `github.com/bsttiv/maestro`) emite y valida los tokens. No tiene usuarios ni contraseñas.
- **Erato** maneja registro, contraseñas (Argon2id) y metadatos de sesión. Obtiene el ID de usuario del claim `sub` del access token, **solo después** de un `/validate` exitoso.
- Mientras Maestro no esté listo, se usa un **mock** que replica su contrato (sección 3).
- Duraciones: **access token 15 minutos; refresh token 7 días.** Un usuario puede tener varias sesiones (dispositivos), **sin límite**.
- Transporte de tokens (decisión del autor, 2026-10-24): cabecera `Authorization: Bearer <access_token>` más la cabecera `X-Device-Id`; los tokens se devuelven en los cuerpos de respuesta.
- **Fingerprint:** string que identifica de forma única el dispositivo en uso. Es un **UUID generado una vez por el frontend, guardado en el navegador y enviado en la cabecera `X-Device-Id`.** Para Erato es un valor opaco: se envía sin transformar como `context` en `/mint` y como `fingerprint` en `/validate` y `/refresh`. `sessions.device` es otra cosa: una etiqueta legible derivada del `User-Agent` (por ejemplo «Firefox en Linux»), independiente del fingerprint.

Origen: `archivos/arquitectura.md`; `archivos/autonomo_automatico.md`; `tests_md/auth_sesiones.md` (PQ 6, 7, 12); `openspec/changes/perfil-backend/exploration.md` (respuestas del autor); Engram 259, 286, 427.

## 2. Usuarios: campos y validaciones

| Campo | Regla |
| --- | --- |
| `email` | Se guarda en minúsculas; único. Se valida con forma de email (`texto@texto.texto`). El login es **solo por email** (por `username` responde `422`). |
| `username` | `[a-z0-9-]`, de 3 a 30 caracteres, sin guiones al inicio, al final ni repetidos. A mano **solo se pasa a minúsculas**; nada más se transforma (lo demás es `422`). Único. Editable. **Lo elige el usuario al registrarse y es obligatorio**: no se genera automáticamente (solo la migración lo genera). El nombre anterior queda libre de inmediato tras un cambio, sin historial de nombres. |
| `display_name` | De 1 a 60 caracteres **después de recortar** los espacios de los extremos (los internos no cambian). Obligatorio. Vale en registro y en `PATCH /me` (aprobado el 2026-10-23). Longitud contada en puntos de código. |
| `password` | De 8 a 128 caracteres, **sin reglas de composición** (`aaaaaaaa` es válida). Hash **Argon2id** (prefijo `$argon2id$`); la contraseña en claro no aparece en ningún documento. |

Los hashes Argon2id de la base antigua se copian tal cual y deben seguir funcionando para iniciar sesión (AUTH-028).

Origen: `tests_md/auth_sesiones.md` (AUTH-003 a AUTH-015, AUTH-039 a AUTH-044; PQ 1 a 3); `tests_md/perfil.md` (PQ 1, 2, 4); `archivos/conceptos_datos.md`; Engram 286, 287, 401.

## 3. Contrato de Maestro

### 3.1 Maestro real (observado el 2026-10-17)

Base `/api/v1/maestro` (Scala 3 / Pekko / Tapir, Redis):

- `POST /mint {userId, context}` → `{accessToken, refreshToken}`.
- `POST /revoke {token}` → `204`.
- `POST /validate {token, fingerprint}` → `200 {}` (sin claims).
- Todos los fallos son `400` con texto plano. Sin autenticación entre servicios.
- JWT EdDSA; access 15 min (`sub = "sub_<userId>"`, `ctx`, `jti`); refresh 7 días con el mismo `jti`.
- **No tiene `/refresh` ni JWKS.**
- Defectos verificados: el refresh token falla en `validate`/`revoke` porque siempre se parsea como access (`JWTManager.scala:30`); las claves se regeneran en memoria al reiniciar; Redis fijo en localhost; tokens revocados sin TTL; `/validate` imprime claims por stdout.

### 3.2 Mock (contrato vigente)

El mock se ejecuta como servicio de `docker compose`. Maestro **siempre** se reemplaza por el mock en tests.

| Endpoint | Cuerpo | Éxito | Fallo |
| --- | --- | --- | --- |
| `POST /mint` | `{userId, context}` | `200 {accessToken, refreshToken}` | `400` texto plano |
| `POST /validate` | `{token, fingerprint}` | `200 {}` | `400` texto plano: firma mala, tipo equivocado, vencido o vencido a la fuerza, `jti` revocado, fingerprint distinto del de emisión |
| `POST /revoke` | `{jti}` (revisión 2026-10-24) | `204`; un `jti` desconocido también `204`; luego el token deja de validar | `400` texto plano; un cuerpo `{token}` se rechaza como cuerpo inválido |
| `POST /refresh` | `{refreshToken, fingerprint}` | `200 {accessToken, refreshToken}` con `jti` nuevo; el refresh anterior queda inválido | `400` texto plano: usado, revocado, vencido, fingerprint distinto |

- `/refresh` **no existe en el Maestro real**: el autor lo agregará luego. El mock lo incluye por adelantado.
- Hasta la revisión de 2026-10-24, `/revoke` recibía `{token}`. Pasó a `{jti}` para que Erato pueda revocar **otras** sesiones sin guardar sus tokens; el Maestro real adoptará ese contrato más adelante.
- Tokens del mock: JWT HS256 con `sub = "sub_<userId>"`, `jti` (compartido por el par access/refresh), `typ`, `ctx` (fingerprint), `iat`, `exp` (access 900 s, refresh 604800 s). Tolerancia de INFRA-040: ±5 s en `exp`.
- Cualquier cuerpo inválido (JSON mal formado, campo faltante o tipo incorrecto) en un endpoint del contrato responde `400` texto plano (los endpoints de control quedan excluidos).
- **Endpoints de control** (solo existen si la variable `MAESTRO_MOCK_CONTROL=1`; si no, `404`): `POST /__control/expire {token}` (`204`), `POST /__control/fault {endpoint, mode}` con `mode` `error_400` o `no_response` (duerme 30 s; el cliente de prueba usa 2 s de timeout) (`204`), `POST /__control/reset` (`204`; además vacía el registro de llamadas) y, desde 2026-10-24, `GET /__control/calls`.
- **Registro de llamadas** (con control habilitado): cada llamada a `/mint`, `/validate`, `/revoke`, `/refresh` con cuerpo válido se anota en orden de llegada como `{path, body}`; las llamadas a endpoints de control no se registran; `GET /__control/calls` responde `200` con la lista; sin la variable, `404`.
- Existe un servicio `maestro-mock` (control apagado) y otro `maestro-mock-control` (perfil `test`, control encendido).

Origen: `archivos/arquitectura.md` (revisiones 2026-10-17 y 2026-10-24); `tests_md/infraestructura.md` (INFRA-040 a INFRA-049, INFRA-060 a INFRA-062); `openspec/specs/maestro-mock/spec.md`; `openspec/changes/perfil-backend/specs/maestro-mock/spec.md`; Engram 259, 427.

## 4. Flujos de cuenta y sesión

### 4.1 Rutas

| Ruta | Éxito | Notas |
| --- | --- | --- |
| `POST /auth/register` | `201` | Cuerpo `{email, username, display_name, password}`, cabecera `X-Device-Id` |
| `POST /auth/login` | `200` | Cuerpo `{email, password}`, cabecera `X-Device-Id` |
| `POST /auth/refresh` | `200` | Rota el par de tokens |
| `POST /auth/logout` | `204` | Protegida |
| `GET /me` | `200` | Devuelve `username`, `display_name`, `email` del propio usuario |
| `PATCH /me` | `200` | `username` y/o `display_name` |
| `PATCH /me/email` | `200` | Con `current_password` |
| `PATCH /me/password` | `204` | Con `current_password` y `new_password` |
| `GET /me/sessions` | `200` | Lista de sesiones propias |
| `DELETE /me/sessions/{id}` | `204` | Cierra una sesión propia |
| `GET /health` | `200` | |

Rutas protegidas (exigen Bearer + `X-Device-Id`): `GET /me`, `PATCH /me`, `PATCH /me/email`, `PATCH /me/password`, `GET /me/sessions`, `DELETE /me/sessions/{id}`, `POST /auth/logout`. En producción el backend se sirve bajo el prefijo `/api` (archivo 03).

### 4.2 Registro

1. Valida todo **antes** de llamar a Maestro (campos, formato, política de contraseña, cabecera `X-Device-Id`).
2. Crea el usuario (email y username en minúsculas). Duplicados: `409 email_taken` o `409 username_taken` (la unicidad se evalúa tras normalizar a minúsculas; la respuesta no revela datos del usuario existente).
3. **El registro inicia sesión:** llama a `/mint` una vez con el `_id` del usuario y el fingerprint, devuelve access y refresh token y crea el documento de sesión con las mismas reglas que el login.
4. Si Maestro falla o no responde: **`201` igualmente**, con el usuario creado, **sin tokens y sin sesión**; un login posterior funciona.
5. Sin `X-Device-Id`: `422 validation_error` y no se crea el usuario. (Elección propuesta por el agente y aprobada con el conjunto de `tests_md`.)

### 4.3 Login

- Autentica por email (normalizado a minúsculas) y contraseña. Éxito: `200` con access y refresh token; llama a `/mint` una vez con `{userId, context}` y crea un documento de sesión con `user_id`, el `jti` del par emitido, `refresh_token_hash` (SHA-256 del refresh token; el refresh en claro **no** se guarda), `device`, `last_access_at`, `created_at` y `expires_at` igual al vencimiento del refresh token.
- Contraseña incorrecta y email inexistente responden **igual**: `401 invalid_credentials`, cuerpos idénticos salvo `detail`; no llama a `/mint` ni crea sesión. Para un email inexistente se verifica la contraseña contra un hash ficticio, de modo que ambos caminos tarden parecido **[diseño]**.
- Sin `password`, con identificador que no es email (p. ej. `username`), o sin `X-Device-Id`: `422 validation_error`, sin llamar a `/mint`.
- Una etiqueta `device` desconocida del `User-Agent` se rotula «Dispositivo desconocido» (valor por defecto aceptado por el autor). El formato es «{navegador} en {sistema}»; solo está aprobado el ejemplo «Firefox en Linux».

### 4.4 Autenticación por petición

1. Sin cabecera `Authorization: Bearer ...` o sin `X-Device-Id` → `401 not_authenticated` **sin llamar a `/validate`**.
2. Llama a `/validate {token, fingerprint}` con el `X-Device-Id` de la petición actual.
3. Solo si es exitoso se leen `sub` y `jti` (sin verificar firma: Erato no tiene la clave de Maestro y confía en `validate`). `sub` debe tener la forma `sub_<userId>`.
4. Debe existir el usuario y un documento de sesión con ese `jti` (esto da sentido al logout y a la rotación; un access token anterior al refresh falla).
5. `last_access_at` se actualiza **a lo sumo una vez por minuto** y nunca se toca el de otras sesiones.

Errores: `400` de `/validate` (vencido, revocado, fingerprint distinto), token mal formado, `sub` sin prefijo, usuario inexistente o sesión inexistente → `401 not_authenticated` (sin resolver ningún usuario). Si `/validate` no responde → `502 session_upstream_error`.

### 4.5 Refresh y logout

- **Refresh:** llama a `/refresh {refreshToken, fingerprint}` y devuelve un par nuevo con `jti` nuevo. **Actualiza el mismo documento de sesión** (nuevo `jti`, nuevo `refresh_token_hash`, `last_access_at`, `expires_at` renovado a 7 días); no crea otra sesión. El refresh anterior y el access anterior quedan inválidos (`401`). Refresh desconocido, sesión vencida, sesión revocada o `400` de Maestro → `401 not_authenticated`. Sin respuesta de Maestro → `502`, sesión sin cambios.
- **Logout:** llama a `/revoke` con el `jti` de la sesión y, si responde `204`, **borra el documento de sesión** y responde `204`. Si revoke falla o no responde → `502 session_upstream_error` y el documento se conserva (el cliente puede reintentar). Tras el logout, access y refresh de esa sesión → `401`.

### 4.6 Lista y cierre de sesiones

> **Revisión (2026-11-01):** `sessions.jti` pasó a `sessions.sid` y `/revoke` recibe el token. Cerrar la sesión actual revoca en Maestro; cerrar otra borra su fila. Ver `archivos/arquitectura.md`.

- `GET /me/sessions`: solo sesiones **del usuario autenticado** con `expires_at` futuro (aunque el TTL de MongoDB aún no las haya borrado), ordenadas por `last_access_at` descendente. Cada elemento contiene exactamente `id` (el `_id` del documento), `device`, `last_access_at`, `created_at` y `current` (verdadero solo para la sesión cuyo `jti` es el del access token validado). **No** contiene `jti`, `user_id`, `refresh_token_hash`, tokens ni `expires_at`, y el cuerpo no contiene fingerprints. Cuerpo: arreglo simple. Listar no modifica `last_access_at` de las otras sesiones.
- `DELETE /me/sessions/{id}`: llama a `/revoke` con el `jti` de esa sesión y, si responde `204`, borra el documento y responde `204`; la sesión cerrada queda rechazada (`401`) y las demás siguen válidas. **Cerrar la sesión actual equivale a logout.** Un `id` inexistente, **mal formado** o de otro usuario responde `404 not_found` (indistinguible), sin llamar a `/revoke`. Cerrar dos veces → `404`. Si revoke falla → `502` y el documento se conserva.

### 4.7 Cambios de perfil, email y contraseña

- **`PATCH /me`:** cuerpo parcial con `username` y/o `display_name`; es **atómico** (si una parte falla, no cambia nada) y rechaza con `422 validation_error` los campos desconocidos (`email`, `password_hash`, `_id`, ...), el cuerpo vacío `{}` y los valores no string. Un `username` ya usado → `409 username_taken` (bajo concurrencia entre dos usuarios exactamente uno gana: lo garantiza el índice único). Cambiar al propio `username` actual → `200`. `display_name` se recorta antes de medir. Actualiza `updated_at`, no cambia `email`, **no cierra ni modifica sesiones**. Responde `200` con el usuario actualizado con la forma de `GET /me`.
- **`PATCH /me/email`:** requiere `email` y `current_password`. Éxito: guarda el nuevo email en minúsculas, **sin verificación por correo**; el login con el email anterior falla (`401`) y con el nuevo funciona. Contraseña incorrecta → `401 invalid_credentials`; falta `current_password` o email inválido → `422`; email de otra cuenta → `409 email_taken` (sin revelar datos). Responde con el usuario actualizado (valor por defecto aceptado por el autor).
- **`PATCH /me/password`:** requiere `current_password` y `new_password` (8 a 128). La nueva contraseña **puede ser igual a la actual**. Éxito: revoca en Maestro, por `jti`, **todas las demás sesiones** del usuario, borra esos documentos, guarda el nuevo hash Argon2id, **conserva la sesión actual** y responde `204` sin tokens. Si falla la revocación de las demás sesiones → `502 session_upstream_error` y **la contraseña no cambia** (las sesiones ya revocadas quedan revocadas, por decisión del autor). Las sesiones de otros usuarios no se tocan. Contraseña actual incorrecta → `401 invalid_credentials` (sin crear sesiones ni llamar a `/mint` ni `/revoke`); campos faltantes o fuera de política → `422`.

Origen: `tests_md/auth_sesiones.md`; `tests_md/perfil.md` (backend); `openspec/changes/perfil-backend/{proposal,design}.md` y `specs/`; Engram 286, 287, 288, 401.

## 5. Límite de intentos de login

- Colección `login_attempts` (esquema en archivo 05): un documento por **cada login fallido**, también con emails inexistentes. `email_hash` = SHA-256 del email normalizado (el email en claro no se guarda); `ip` sale de `X-Forwarded-For`; `created_at`.
- Con **5 o más** intentos del mismo `email_hash` + `ip` en los últimos **15 minutos**, el login responde `429 rate_limited` con cabecera `Retry-After`, **aunque la contraseña sea correcta**, y no llama a `/mint`. El quinto intento fallido aún responde `401`; el sexto, `429`.
- El bloqueo es por par email + IP: otra IP o otro email no se ven afectados.
- Un login exitoso **borra** los intentos de ese par. Los intentos se borran solos a los 15 minutos (TTL).
- Un `current_password` incorrecto en `PATCH /me/email` o `PATCH /me/password` **cuenta** como intento fallido con el `email_hash` de la cuenta y la IP, con el mismo umbral; bloqueado, el cambio responde `429` aunque la contraseña sea correcta y un login de esa cuenta desde esa IP también responde `429` hasta que venza la ventana. Una contraseña actual correcta **no** borra los intentos (valor aceptado por el autor).
- Límite y ventana son constantes en el código. `Retry-After` se calcula a partir del intento más antiguo de la ventana, mínimo 1 segundo **[diseño]**.
- Sin límite de frecuencia para `PATCH /me` ni para cerrar sesiones.
- Pendiente de verificar en un despliegue de vista previa: que Vercel sobrescriba un `X-Forwarded-For` enviado por el cliente (si no, el límite se podría eludir falsificando la cabecera).

Origen: `archivos/esquema_mongodb.md`; `tests_md/auth_sesiones.md` (AUTH-031 a AUTH-038, USR-019b); `openspec/changes/perfil-backend/design.md`; Engram 287, 288.

## 6. Formato de errores

Cuerpo: `{"code": "<snake_case>", "detail": "<texto para humanos>"}`. **Los tests y el frontend identifican errores por `code` y estado HTTP, nunca por `detail`.** Un error no deja efectos (ni en la base ni en Cloudinary). Las respuestas de error nunca incluyen datos de otro usuario.

### Catálogo de `code` (aprobado el 2026-10-18)

| `code` | HTTP | Uso |
| --- | --- | --- |
| `validation_error` | 422 | Cuerpo inválido (campo faltante, tipo o enum incorrecto, campo desconocido donde la ruta lo prohíbe, cabecera requerida ausente) |
| `email_taken` | 409 | Email ya registrado |
| `username_taken` | 409 | Nombre de usuario ya usado |
| `invalid_credentials` | 401 | Login fallido (email desconocido o contraseña incorrecta, sin distinguir); también `current_password` incorrecta |
| `not_authenticated` | 401 | Sin token, token inválido, expirado o revocado |
| `forbidden` | 403 | Autenticado que puede ver el recurso pero no tiene permiso para la acción |
| `not_found` | 404 | Recurso inexistente, o que el autenticado no puede ver (respuesta indistinguible) |
| `version_conflict` | 409 | `section_versions` desactualizada |
| `already_member` | 409 | Usar un enlace de invitación teniendo ya acceso: miembro de la canción o banda, o dueño de la canción o de la banda |
| `owner_must_transfer` | 409 | El dueño de una banda intenta abandonarla sin transferirla antes |
| `quota_exceeded` | 422 | La demo (o el movimiento de una canción) haría superar la cuota de 2 GB del dueño |
| `rate_limited` | 429 | Demasiados intentos de login fallidos para el mismo email e IP; incluye `Retry-After` |
| `session_upstream_error` | 502 | Maestro no respondió o respondió algo inesperado |

Un código nuevo exige el ciclo de aprobación de tests.

### Política de estados HTTP

- Sin sesión válida en una ruta con sesión → `401`.
- Autenticado que **no puede ver** el recurso → `404` (se oculta su existencia; cuerpo idéntico al de un recurso inexistente).
- Autenticado que **puede ver** pero no actuar → `403`.
- `201` al crear; `200`/`204` en lectura, actualización o borrado exitosos; `409` en conflictos; `422` en validación; `429` por exceso de intentos.
- Errores de validación de FastAPI se mapean a `422 validation_error`; el `detail` resume los campos fallidos sin repetir valores (para no devolver contraseñas) **[diseño]**.

### Fallos de Maestro

| Situación | Resultado |
| --- | --- |
| `/mint`, `/refresh` o `/revoke` sin respuesta o con respuesta inesperada; `/validate` sin respuesta | `502 session_upstream_error`, sin cambios de estado (excepción: el registro, 4.2) |
| `400` de `/validate` o `/refresh` | `401 not_authenticated` (token inválido) |

El cliente HTTP de Maestro usa un timeout menor que el retardo de «sin respuesta» del mock (30 s). Valor de producción: 3 s como constante de código **[diseño]**; no se usa variable de entorno porque INFRA-032 exige que toda variable leída esté en `.env.example` y no admite valores numéricos.

Origen: `tests_md/README.md` (convenciones y catálogo); `tests_md/auth_sesiones.md` (PQ 5); `openspec/changes/perfil-backend/{design.md,specs/api-errors/spec.md}`; Engram 272.

## 7. Datos públicos de usuario

- **Nada del usuario es público salvo `display_name` y `username`.** Hacia otros usuarios (miembros, comentarios, autores de revisiones, vista pública) solo se exponen esos dos campos.
- El email solo aparece en las respuestas de `/me` del propio usuario (`GET /me`, `PATCH /me`, `PATCH /me/email`). Ampliación aprobada el 2026-10-24 sobre la regla original de USR-024 («`email` solo en `GET /me`»).
- Ninguna respuesta JSON contiene `password_hash` ni `refresh_token_hash`; la prueba USR-024 barre todas las respuestas de la API para verificarlo. La respuesta de registro no incluye `email`.
- Si un usuario cambia su `username`, el contenido donde aparece muestra el nuevo (las referencias son por `_id`).
- Quedan **diferidos** hasta los cambios de canciones, bandas y enlaces: USR-008 y USR-020 a USR-022 (aparición del usuario en miembros, comentarios, vista pública y lista de miembros).

Origen: `archivos/restricciones.md`; `AGENTS.md`; `tests_md/auth_sesiones.md` (USR-020 a USR-024); `openspec/changes/perfil-backend/specs/user-profile-api/spec.md`.

## 8. Página `/perfil` (frontend)

### 8.1 Alcance definido por el autor

Muestra y permite editar el **nombre de usuario** y el **nombre visible**; lista las **sesiones activas** (dispositivos) y permite cerrarlas; permite **cambiar la contraseña**. Fuera de alcance: cambio de email en la página (existe en el backend), borrado de cuenta, foto de perfil, bandas, y un botón «cerrar todas las demás» (se cierran de a una). El email no se muestra en la página.

### 8.2 Decisiones de comportamiento (todas aprobadas el 2026-10-23)

- Sin confirmación al cerrar otra sesión; se puede cerrar la sesión actual desde la lista (equivale a logout y navega a `/login`).
- Una respuesta `401 not_authenticated` de cualquier llamada de la página lleva a `/login`. No hay guardia de router (la página maneja el `401`) ni refresh automático en el frontend. `401 invalid_credentials` no redirige: es un error de campo.
- Formulario de contraseña: tres campos («Contraseña actual», «Contraseña nueva», «Repetir contraseña nueva»; la repetición solo existe en el cliente y no se envía). Tras un `401 invalid_credentials` o un `429` se vacían los tres campos. Tras un `429` con `Retry-After` válido el botón queda deshabilitado exactamente esos segundos. Ningún valor de contraseña aparece en atributos, texto o marcado serializado fuera del `value` de los `<input type="password">`.
- La validación del cliente es una ayuda (el servidor es la autoridad) y corre al enviar.
- Fechas de `last_access_at`: absolutas, en español con `Intl` (ejemplo «23 oct 2026, 21:45»).
- Sin proveedor de API, la página muestra «No se pudo cargar tu perfil.» (el adaptador HTTP real llega con el cambio de autenticación del frontend; no está definido el transporte de tokens en el cliente).
- Diseño: barra superior con la marca «Erato» y un avatar (inicial del `display_name`, enlace a `/perfil`, nombre accesible «Tu cuenta: {display_name}», `aria-current="page"`); columna central de 760 px; tres tarjetas (`Card`) «Datos», «Sesiones», «Contraseña»; sin `SideNav`. Etiqueta ámbar «Este dispositivo» en la sesión actual; botón de cierre con ícono `x` y nombre accesible «Cerrar sesión de {dispositivo}». Detalle visual en el archivo 13.

### 8.3 Textos aprobados (tuteo, español)

| Uso | Texto |
| --- | --- |
| Título (`h1`) | «Tu perfil» |
| Encabezados de bloque | «Datos», «Sesiones», «Contraseña» |
| Carga | «Cargando…» |
| Error de carga / sin proveedor | «No se pudo cargar tu perfil.» |
| Reintentar | «Reintentar» |
| Error de red | «No hay conexión con el servidor. Inténtalo de nuevo.» |
| Error genérico (`422`, `502`, desconocido) | «No se pudo completar la acción. Inténtalo de nuevo.» |
| Datos guardados | «Cambios guardados.» |
| Sin sesiones | «No hay sesiones abiertas.» |
| Etiquetas | «Nombre de usuario», «Nombre visible», «Guardar», «Contraseña actual», «Contraseña nueva», «Repetir contraseña nueva», «Cambiar contraseña», «Este dispositivo», «Cerrar sesión de {dispositivo}» |
| Campo obligatorio | «Este campo es obligatorio.» |
| Formato de usuario | «Usa de 3 a 30 letras minúsculas, números o guiones, sin guiones al inicio, al final ni seguidos.» |
| Usuario en uso (`409`) | «Ese nombre de usuario ya está en uso.» |
| Nombre visible largo | «Debe tener entre 1 y 60 caracteres.» |
| Política de contraseña | «Debe tener entre 8 y 128 caracteres.» |
| No coinciden | «Las contraseñas no coinciden.» |
| `401 invalid_credentials` | «La contraseña actual no es correcta.» |
| Contraseña cambiada | «Contraseña actualizada. Cerramos tus otras sesiones.» |
| `429` con `Retry-After` | «Demasiados intentos. Espera {n} minutos e inténtalo de nuevo.» con `n` = segundos / 60 redondeado hacia arriba; singular «1 minuto» cuando `n` es 1 |
| `429` sin `Retry-After` o con valor inválido (`0`, negativo, no numérico) | «No se pudo cambiar la contraseña. Inténtalo de nuevo.» (sin bloqueo del botón) |
| `502` / desconocido al cambiar contraseña | «No se pudo cambiar la contraseña. Inténtalo de nuevo.» |

### 8.4 Contrato de API del frontend (interfaz, sin adaptador)

Entregado a la página por `provide`/`inject` con una clave tipada; los tests inyectan un doble (`api_perfil`).

- Tipos: `Me {username, display_name}`, `Session {id, device, last_access_at, current}`, `PasswordChange {current_password, new_password}`, `ApiError {status, code, retryAfter?}` (segundos), y un error de red distinguible de los errores HTTP.
- Operaciones: `getMe`, `updateMe(patch)`, `listSessions`, `closeSession(id)`, `changePassword(body)`; una por ruta.
- Un adaptador HTTP real debe convertir un `Retry-After` inválido en un valor no finito (`NaN`).

Origen: `tests_md/perfil.md`; `openspec/changes/archive/2026-10-24-perfil-frontend/{proposal,design}.md`; `openspec/specs/profile-page/spec.md`, `profile-api-contract/spec.md`; Engram 408, 401.

## 9. Valores por defecto aceptados por el autor (2026-10-24)

Sin caso de test que los cubra; definen comportamiento y no agregan tests:

1. `PATCH /me/email` devuelve el usuario actualizado con la forma de `GET /me`.
2. `POST /auth/logout` es protegida (Bearer + `X-Device-Id`).
3. Si falla la revocación durante un cambio de contraseña, la contraseña no cambia; las sesiones ya revocadas quedan revocadas.
4. `POST /auth/refresh` lleva el refresh token en el cuerpo y un `X-Device-Id` ausente responde `422`.
5. Una `current_password` correcta no borra los `login_attempts`; expiran por TTL a los 15 minutos.
6. Un `User-Agent` desconocido se rotula «Dispositivo desconocido».

Origen: `openspec/changes/perfil-backend/design.md` («Author Decisions (2026-10-24)»).

## 10. No es decisión (solo en el árbol de trabajo)

El login y el límite de intentos están implementados en el árbol de trabajo sin confirmar (rama `feat/perfil-backend`, tarea T4). Su comportamiento esperado está fijado por los casos aprobados AUTH-020 a AUTH-038; lo que falta resolver (qué hacer con los intentos previos cuando `/mint` falla) está en el archivo 15.
