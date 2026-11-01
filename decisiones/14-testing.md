# 14 - Testing: formato de `tests_md/`, traducción a tests ejecutables y qué se aprobó

Los tests son responsabilidad compartida con un ciclo fijo: **el agente propone los tests en `tests_md/`; el autor los revisa, pide cambios si hace falta y los aprueba. Ningún test se da por aprobado ni se implementa sin esa aprobación explícita.** Un test nuevo posterior sigue el mismo ciclo. (Esto reemplazó la idea anterior de que el autor escribía los tests; ver archivo 15.) Los casos marcados **(PQ)** dependen de una pregunta abierta y no se implementan hasta que el autor la resuelva. Los tests usan solo entradas que figuran en casos aprobados de `tests_md`.

La carpeta `tests_md/` **no viaja** al repositorio nuevo; este archivo conserva el formato, el catálogo, las convenciones y el resumen por área. Las reglas de cada área están en los archivos 06 a 12.

## 1. Formato de un caso (aprobado el 2026-10-18)

Cada caso describe **un solo comportamiento**, como fila de tabla o bloque con cuatro campos:

| Campo | Contenido |
| --- | --- |
| **ID** | `PREFIJO-NNN`, correlativo dentro del archivo (ej. `PERM-012`). Un ID **no se reutiliza** aunque el caso se elimine |
| **Precondiciones** | Estado inicial: usuarios, canciones, enlaces, membresías, versión de secciones, estado del mock. Se referencian los *fixtures* comunes |
| **Acción** | Una petición HTTP (`MÉTODO /ruta` + cuerpo relevante) o una llamada a una función pura. Las rutas son ilustrativas |
| **Esperado** | Código HTTP **y** `code` de error legible por máquina, o el estado resultante (documento en MongoDB, objeto en Cloudinary, valor devuelto) |

Convenciones de aserción:

1. Los errores se verifican por **`code`**, nunca por texto libre; el cuerpo de error es `{"code": "<snake_case>", "detail": "<texto para humanos>"}`; `detail` puede cambiar sin romper tests. (Lección de tests anteriores del autor: códigos de error legibles por máquina, códigos HTTP correctos —201 crear, 409 conflicto, 422 validación—, sin enumeración de usuarios en el login, y reglas definidas con precisión.)
2. Códigos HTTP: `201` crear; `200`/`204` lectura/actualización/borrado; `401` sin sesión válida; `404` si el autenticado no puede ver el recurso y `403` si puede verlo pero no actuar; `429` por exceso de intentos de login; `409` en conflictos; `422` en validación.
3. **Un error no deja efectos:** todo caso de error verifica además que la base (y Cloudinary, si aplica) no cambió.
4. **Sin fugas de datos:** toda respuesta que exponga a otro usuario se verifica contra la proyección pública (`username`, `display_name`).

El catálogo de `code` está en el archivo 07, sección 6.

## 2. Fixtures comunes

| Fixture | Descripción |
| --- | --- |
| `alice` | Usuario dueño de canciones personales y de la banda `faroles` |
| `bob`, `carol`, `dave`, `erin` | Usuarios registrados que cada caso ubica en un rol |
| `faroles` | Banda con `owner_id = alice` |
| `otra` | Banda de la que `alice` no es miembro |
| `song_up`, `song_upub` | Canción de `alice`, `owner_type = user`, `private` / `public` |
| `song_x` | Otra canción personal y privada de `alice` |
| `song_bp`, `song_bpub` | Canción de `faroles`, `owner_type = band`, `private` / `public` |
| `maestro` | Mock de Maestro controlable desde el test (forzar expiración, revocación, error 400, sin respuesta) |
| `cloudinary` | Falso de Cloudinary: reemplaza solo las llamadas de red, registra cada llamada y se puede forzar a fallar. Firmas y URLs usan el SDK real |

## 3. Cómo se traducen a tests ejecutables (aprobado el 2026-10-18)

| Capa | Herramienta | Qué cubre |
| --- | --- | --- |
| Backend (API) | `pytest` + `httpx` / `fastapi.testclient.TestClient` | `AUTH`, `SES`, `USR`, `PERM`, `INV`, `SONG`, `CHD`, `TAB`, `LYR`, `TASK`, `SLUG`, `REV`, `KEY`, `DEMO`, `CMT` |
| Backend (unitario) | `pytest` sin red ni base | `DET` (módulo de detección), validador de celdas de tablatura, normalización de `username` |
| Migración | `pytest` con dos bases MongoDB de prueba (antigua y nueva), Cloudinary falso | `MIG` |
| Frontend (lógica pura) | `Vitest` | Validación de celdas y editor de tablaturas (`EDT`), ubicación de acordes en la letra; funciones puras |
| Frontend (componentes) | `Vitest` + `@vue/test-utils` + `jsdom` | `DS` (montaje, atributos, `aria-*`, eventos; aspecto sobre el CSS compilado). Aprobado el 2026-10-20 |
| Verificación de tipos | `vue-tsc --noEmit` mediante `make typecheck`, sobre fixtures de tipos | DS-068 a DS-071, DS-100, DS-101: un archivo `.vue` por caso con `<!-- @vue-expect-error -->`; excepción a «un caso = una función de test»; no corre en `make test`. Aprobado el 2026-10-21 |
| Frontend (rutas) | `Vitest`; RUTA-001 y RUTA-004 con `@vue/test-utils` + `jsdom`, el resto sin DOM | `RUTA`. Aprobado el 2026-10-21 |

Ubicación: `backend/tests/` (un archivo o carpeta por cada archivo de casos, ej. `test_permisos.py`) y `frontend/src/**/*.spec.ts` junto al código.

Reglas de traducción:

- **Un caso = una función de test**, nombrada con su ID: `test_perm_027_band_member_can_edit_chords`; en Vitest `it('TAB-014 rejects fret 25', ...)`.
- Los casos tabulares de la matriz de permisos se implementan con `pytest.mark.parametrize`, un parámetro por celda, con el ID de caso como `id`.
- **Base de datos de prueba:** MongoDB real del `docker compose` de tests, *replica set* de un nodo (las transacciones de INV-122 e INV-129 lo exigen), con una base aislada por sesión de test (nombre exclusivo, distinto de la de desarrollo) que se vacía entre casos (se borran documentos, no índices). Los índices del esquema aprobado se crean antes de correr (los tests de duplicados y TTL dependen de ellos).
- **Maestro:** siempre el mock, nunca el servicio real. **Cloudinary:** siempre falso.
- **Compresión:** la imagen de tests incluye `ffmpeg` real.
- **Sin E2E por ahora** (decisión del autor); se agregan si el autor los pide.
- `make test` es el comando único; exit distinto de 0 si falla cualquier suite; no quedan contenedores ni volúmenes de test.
- Fuera de alcance de la propuesta: comportamientos solo visuales (carrusel, maximizar letra, velocidad del desplazamiento, filtros de acordes, hover sobre acordes) no tienen reglas medibles en las fuentes.
- **TDD estricto** desde el final del andamiaje (primero se observa el RED con los IDs aprobados, luego GREEN, luego refactor).

## 4. Prefijos y qué se aprobó, por área

| Archivo | Prefijos | Aprobación | Resumen |
| --- | --- | --- | --- |
| `README.md` | - | 2026-10-18 | Formato, prefijos (incluye `EDT`), catálogo de 13 `code`, base de pruebas, E2E (ninguno), ubicación |
| `auth_sesiones.md` | `AUTH`, `SES`, `USR` | 2026-10-18; ampliación 2026-10-23 (AUTH-039 a AUTH-044) | Registro (AUTH-001 a 018, 039 a 044), login, mock de Maestro, límite de intentos (AUTH-031 a 038), validación por petición (SES-001 a 012), refresh y logout (SES-020 a 028), varias sesiones (SES-030 a 036), nombre de usuario (USR-001 a 008), email y contraseña (USR-010 a 019b), datos públicos (USR-020 a 024) |
| `permisos.md` | `PERM` | 2026-10-18 | Matriz por tipo de dueño × visibilidad × actor × acción, ver/editar/gestionar, aplicación en el servidor, listados, mover a banda |
| `invitaciones.md` | `INV` | 2026-10-18 | Creación de enlaces, uso, vencimiento y TTL, borrado, membresías, transferencia de banda, enlaces de quien pierde el derecho de editar (INV-110 a INV-123), integridad |
| `canciones_secciones.md` | `SONG`, `CHD`, `TAB`, `EDT`, `LYR`, `TASK`, `SLUG`, `REV`, `KEY` | 2026-10-18 | CRUD de canción, acordes, gramática de tablatura, teclado del editor, letra, tareas, slug, revisiones/concurrencia/retención, modo de tonalidad |
| `deteccion_acordes_tonalidad.md` | `DET` | 2026-10-18 (reescrito el 2026-10-17) | Algoritmo de acordes y tonalidad (archivo 08); sin preguntas abiertas |
| `demos.md` | `DEMO`, `CMT` | 2026-10-18 | Subida, compresión, reproducción, borrado, cuota, comentarios |
| `migracion.md` | `MIG` | 2026-10-18 | Modo prueba, base antigua intacta, mapeo por concepto, idempotencia |
| `infraestructura.md` | `INFRA` | 2026-10-18 (INFRA-055: 2026-10-19; INFRA-060 a 062: 2026-10-24) | Comando único de tests, MongoDB, almacenamiento, backend, `ffmpeg`, mock de Maestro, frontend de estilos |
| `design_system.md` | `DS` | 2026-10-20; ampliaciones 2026-10-21, 2026-10-23, 2026-10-24 | Icon, Button, IconButton, Tag, Segmented, SideNav, Field, Card, Alert; estilos globales y mapeo de tokens; verificación de tipos; DS-102 (alto mínimo del fondo) |
| `rutas.md` | `RUTA` | 2026-10-21 | Router de la aplicación, tabla de rutas y redirección de `/` |
| `perfil.md` | `PERF` | 2026-10-23 (PERF-108 a PERF-117 incluidas) | Página `/perfil` y su backend |

### Casos de infraestructura (INFRA)

- **INFRA-001 a 004** (`make test` y `make test-harness`): comando único con pytest y vitest en contenedores; exit ≠ 0 si falla alguna suite; no quedan contenedores ni volúmenes.
- **INFRA-010 a 014:** MongoDB responde como primario de un replica set; transacción de dos colecciones que confirma/aborta; base exclusiva por sesión, vaciada entre casos.
- **INFRA-020 a 024:** eliminados el 2026-10-31 junto con SeaweedFS; la cobertura pasa a los casos `CLD`.
- **INFRA-030 a 034:** `GET /health` → `200`; si falta una variable obligatoria la app no arranca nombrándola; `.env.example` coincide con las variables leídas; `ffmpeg` con `libopus`; WAV de 1.0 s se comprime a Ogg/Opus a 96 kbps (duración 1.0 ± 0.1 s).
- **INFRA-040 a 049, 060 a 062:** contrato del mock (archivo 07).
- **INFRA-050 a 055:** `vitest run`; las clases de color del tema compilan a `var(--bg-000)`, `var(--ink)`; `bg-red-500` no genera CSS; ambos temas vienen del `tokens.css` canónico sin copia en `frontend/`; radios y fuentes usan variables; sin `react`/`react-dom` ni imports de `bundle.js`.
- Verificación manual (sin E2E): `docker compose up` desde cero levanta MongoDB, el almacenamiento, el mock de Maestro, el backend y el frontend; `GET /health` → `200` y el frontend sirve su página inicial.

### Estado de la suite al consolidar

Último estado registrado por las fuentes: tras el cambio `perfil-frontend` (2026-10-24), `make test` pasaba con 47 tests de backend y 222 de frontend, y `make typecheck` pasaba. Durante `perfil-backend` (tareas T1 a T3 confirmadas), `make test` pasaba con 92 de backend y 223 de frontend. La tarea T4 (login) tiene sus chequeos funcionales pasando pero está sin confirmar (archivo 07, sección 10 y archivo 15).

Origen: `tests_md/README.md` y los demás archivos de `tests_md/`; `AGENTS.md` (regla 3); `openspec/config.yaml`; `openspec/specs/test-harness/spec.md`; `odd/tasks/{tests-proposal,perfil-backend}.md`; Engram 256, 293, 294.
