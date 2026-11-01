# Especificación de tests — Erato

> **Estado: APROBADO por el autor (2026-10-18).** El formato y todos los casos de los archivos siguientes están aprobados. Todo test nuevo o cambio posterior sigue el mismo ciclo: el agente propone y el autor aprueba (AGENTS.md, regla 3).

> **Ampliación (2026-10-20):** `design_system.md` (prefijo `DS`) y la capa «Frontend (componentes)» fueron aprobados por el autor el 2026-10-20.

> **Ampliación (2026-10-21):** `rutas.md` (prefijo `RUTA`), la sección «Ampliación (2026-10-21)» de `design_system.md` (DS-065 a DS-071), las capas «Verificación de tipos» y «Frontend (rutas)» y la excepción de la capa de tipos a «un caso = una función de test» fueron aprobadas por el autor el 2026-10-21.

> **Ampliación (2026-10-23):** `perfil.md` (prefijo `PERF`, con la fixture `api_perfil`, incluidas sus ampliaciones PERF-108 a PERF-117), las secciones «Ampliación (2026-10-23)» de `design_system.md` (DS-072 a DS-101: Field, Card y Alert, con las fixtures de tipos DS-100 y DS-101) y la de `auth_sesiones.md` (AUTH-039 a AUTH-044) fueron aprobadas por el autor el 2026-10-23.

Fuentes de verdad: `descripcion_proyecto.md`, `AGENTS.md`, `archivos/arquitectura.md`, `archivos/conceptos_datos.md`, `archivos/esquema_mongodb.md`, `archivos/entradas_manuales.md`, `archivos/autonomo_automatico.md`, `archivos/restricciones.md` y, para la migración, `bd_vieja.md`. Ningún caso agrega reglas que no estén en esas fuentes; donde las fuentes callan, el punto queda en la sección **Preguntas abiertas** de cada archivo.

> **Ampliación (2026-11-01):** `propuesta-maestro-real-2026-11-01.md` (prefijo `MAE`) adapta el mock y las sesiones al contrato real de Maestro; aprobada por el autor el 2026-11-01.

## Índice

| Archivo | Alcance | Prefijos de ID |
| --- | --- | --- |
| [`auth_sesiones.md`](auth_sesiones.md) | Registro, login, mock de Maestro, sesiones, nombre de usuario, datos públicos | `AUTH`, `SES`, `USR` |
| [`permisos.md`](permisos.md) | Matriz de permisos y su aplicación en el servidor | `PERM` |
| [`invitaciones.md`](invitaciones.md) | Enlaces de invitación de uso múltiple y membresías de canción y banda | `INV` |
| [`canciones_secciones.md`](canciones_secciones.md) | CRUD de canciones, secciones, enlace compartido, revisiones, concurrencia | `SONG`, `CHD`, `TAB`, `EDT`, `LYR`, `TASK`, `SLUG`, `REV`, `KEY` |
| [`deteccion_acordes_tonalidad.md`](deteccion_acordes_tonalidad.md) | Algoritmo de detección de acordes y tonalidad (unitario) | `DET` |
| [`demos.md`](demos.md) | Subida, Cloudinary, comentarios con timestamp | `DEMO`, `CMT` |
| [`migracion.md`](migracion.md) | Script de migración desde el modelo antiguo | `MIG` |
| [`infraestructura.md`](infraestructura.md) | Comando único de tests, MongoDB, backend, `ffmpeg`, mock de Maestro, tokens en el frontend | `INFRA` |
| [`design_system.md`](design_system.md) | Componentes base del design system en Vue (Icon, Button, IconButton, Tag, Segmented, SideNav, Field, Card, Alert), estilos globales y mapeo de tokens. | `DS` |
| [`rutas.md`](rutas.md) | Router de la aplicación, tabla de rutas y redirección de `/` | `RUTA` |
| [`perfil.md`](perfil.md) | Página `/perfil`: nombre de usuario, nombre visible, sesiones y cambio de contraseña | `PERF` |

## Formato de un caso (aprobado 2026-10-18)

Cada caso describe **un solo comportamiento**. Se escribe como fila de tabla o, si necesita más detalle, como bloque:

| Campo | Contenido |
| --- | --- |
| **ID** | `PREFIJO-NNN`, correlativo dentro del archivo (ej. `PERM-012`). Un ID no se reutiliza aunque el caso se elimine. |
| **Precondiciones** | Estado inicial: usuarios, canciones, enlaces de invitación, membresías, versión de secciones, estado del mock. Se referencian los *fixtures* comunes (abajo). |
| **Acción** | Una petición HTTP (`MÉTODO /ruta` + cuerpo relevante) o una llamada a una función pura. Las rutas son ilustrativas: la API todavía no está definida. |
| **Esperado** | Código HTTP **y** `code` de error legible por máquina, o el estado resultante (documento en MongoDB, objeto en Cloudinary, valor devuelto). |

Convenciones de aserción:

1. **Los errores se verifican por `code`, nunca por texto libre.** El cuerpo de error es `{"code": "<snake_case>", "detail": "<texto para humanos>"}`; los tests solo comparan `code` (y el estado HTTP). `detail` puede cambiar sin romper tests.
2. **Códigos HTTP:** `201` al crear, `200`/`204` en lectura/actualización/borrado exitoso, `401` sin sesión válida, `404` si el autenticado no puede ver el recurso y `403` si puede verlo pero no actuar (política aprobada, ver `permisos.md`), `429` por exceso de intentos de login, `409` en conflictos (duplicados, usuario que ya es miembro, versión desactualizada), `422` en validación.
3. **Un error no deja efectos:** todo caso de error verifica además que la base (y Cloudinary, si aplica) no cambió.
4. **Sin fugas de datos:** toda respuesta que exponga a otro usuario se verifica contra la proyección pública (`username`, `display_name`).

### Catálogo de `code` (aprobado 2026-10-18)

Se usan en todos los archivos. Un código nuevo sigue el ciclo de aprobación de los tests.

| `code` | HTTP | Uso |
| --- | --- | --- |
| `validation_error` | 422 | Cuerpo inválido (campo faltante, tipo o enum incorrecto) |
| `email_taken` | 409 | Email ya registrado |
| `username_taken` | 409 | Nombre de usuario ya usado |
| `invalid_credentials` | 401 | Login fallido (email desconocido o contraseña incorrecta, sin distinguir) |
| `not_authenticated` | 401 | Sin token, token inválido, expirado o revocado |
| `forbidden` | 403 | Autenticado que puede ver el recurso pero no tiene permiso para la acción |
| `not_found` | 404 | Recurso inexistente, o que el autenticado no puede ver (respuesta indistinguible) |
| `version_conflict` | 409 | `section_versions` desactualizada |
| `already_member` | 409 | Usar un enlace de invitación (con cualquier rol) teniendo ya acceso: miembro de la canción o banda, o dueño de la canción o de la banda |
| `owner_must_transfer` | 409 | El dueño de una banda intenta abandonarla sin haberla transferido antes |
| `quota_exceeded` | 422 | La demo haría superar la cuota de almacenamiento del dueño de la canción (2 GB por usuario o por banda) |
| `rate_limited` | 429 | Demasiados intentos de login fallidos para el mismo email e IP; incluye `Retry-After` |
| `session_upstream_error` | 502 | Maestro no respondió o respondió algo inesperado (ver PQ 5 de `auth_sesiones.md`) |

### Fixtures comunes

| Fixture | Descripción |
| --- | --- |
| `alice` | Usuario dueño de canciones personales y de la banda `faroles`. |
| `bob`, `carol`, `dave`, `erin` | Usuarios registrados que cada caso ubica en un rol (miembro de canción, miembro de banda, ajeno). |
| `faroles` | Banda con `owner_id = alice`. |
| `otra` | Banda de la que `alice` no es miembro. |
| `song_up`, `song_upub` | Canción de `alice`, `owner_type = user`, `private` / `public`. |
| `song_x` | Otra canción personal y privada de `alice`. |
| `song_bp`, `song_bpub` | Canción de `faroles`, `owner_type = band`, `private` / `public`. |
| `maestro` | Mock de Maestro (`/mint`, `/validate`, `/revoke`, `/refresh`) controlable desde el test (forzar expiración, revocación, error 400). |
| `cloudinary` | Falso de Cloudinary: reemplaza solo las llamadas de red, registra cada llamada y se puede forzar a fallar. Firmas y URLs usan el SDK real. |

## Cómo se traducen a tests ejecutables (aprobado 2026-10-18)

| Capa | Herramienta | Qué cubre |
| --- | --- | --- |
| Backend (API) | `pytest` + `httpx` / `fastapi.testclient.TestClient` | Casos `AUTH`, `SES`, `USR`, `PERM`, `INV`, `SONG`, `CHD`, `TAB`, `LYR`, `TASK`, `SLUG`, `REV`, `KEY`, `DEMO`, `CMT` |
| Backend (unitario) | `pytest` sin red ni base | `DET` (módulo de detección), validador de celdas de tablatura, normalización de `username` |
| Migración | `pytest` con dos bases MongoDB de prueba (antigua y nueva) y Cloudinary falso | `MIG` |
| Frontend (lógica pura) | `Vitest` | Validación de celdas y editor de tablaturas (`EDT`), ubicación de acordes en la letra; solo funciones puras, sin DOM cuando sea posible |
| Frontend (componentes) | `Vitest` + `@vue/test-utils` + `jsdom` | `DS` (montaje, atributos, `aria-*`, eventos; aspecto verificado sobre el CSS compilado). Aprobado 2026-10-20. |
| Verificación de tipos | `vue-tsc --noEmit` mediante `make typecheck`, sobre fixtures de tipos en `frontend/src/type-fixtures/` | DS-068 a DS-071: un fixture por caso, nombrado con su ID. Aprobado 2026-10-21. |
| Frontend (rutas) | `Vitest`; RUTA-001 y RUTA-004 con `@vue/test-utils` + `jsdom` (montan `App`), RUTA-002, RUTA-003 y RUTA-005 sin DOM (solo `router.resolve` y `router.getRoutes`) | `RUTA`. Aprobado 2026-10-21. |

Ubicación: `backend/tests/`, con un archivo o carpeta por cada archivo de `tests_md/` (ej. `backend/tests/test_permisos.py`), y `frontend/src/**/*.spec.ts`, junto al código que prueban.

Reglas de traducción:

- **Un caso = una función de test**, nombrada con su ID: `test_perm_027_band_member_can_edit_chords`. En Vitest: `it('TAB-014 rejects fret 25', ...)`.
- **Excepción, capa de verificación de tipos** (aprobada 2026-10-21): cada caso DS-068 a DS-071 es un archivo de fixture `.vue` en `frontend/src/type-fixtures/` que comprueba `make typecheck`, no una función de test, y no corre en `make test`.
- Los casos tabulares de la matriz (`permisos.md`) se implementan con `pytest.mark.parametrize`, un parámetro por celda, con el ID de caso como `id`.
- **Base de datos de prueba:** MongoDB real del `docker compose` de tests, configurado como *replica set* de un solo nodo (las transacciones de INV-122 e INV-129 lo exigen), con una base aislada por sesión de test que se vacía entre casos. Los índices del esquema aprobado se crean antes de correr (los tests de duplicados y TTL dependen de ellos).
- **Maestro:** siempre el mock; nunca el servicio real. **Cloudinary:** siempre falso.
- **Compresión:** la imagen de tests incluye `ffmpeg` real (DEMO-004 a DEMO-006).
- **Sin E2E por ahora**; se agregan si el autor los pide.
- Los casos marcados **(PQ)** dependen de una pregunta abierta: no se implementan hasta que el autor la resuelva.

## Fuera de alcance de esta propuesta

Comportamientos solo visuales (carrusel, maximizar letra, velocidad del desplazamiento automático, filtros de acordes, *hover* sobre acordes) no tienen reglas medibles en las fuentes. Se pueden cubrir luego con tests de componentes o E2E si el autor lo pide. Los tests de componentes de los átomos y organismos base del design system están en `design_system.md` (aprobado 2026-10-20).

## Preguntas abiertas

Resueltas (2026-10-18, aprobadas): ~~1. formato y prefijos~~ (aprobados, con `EDT`); ~~2. cuerpo de error y catálogo~~ (aprobados); ~~3. base de pruebas~~ (MongoDB real como *replica set* de un nodo; MinIO como Cloudinary; `ffmpeg` real); ~~4. E2E~~ (no por ahora); ~~5. ubicación~~ (`backend/tests/` y `frontend/src/**/*.spec.ts`; anotado en `archivos/arquitectura.md`).
