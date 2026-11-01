# Decisiones de producto de Erato

Fecha de consolidación: **2026-10-30**.

## Propósito

Esta carpeta reúne **todas las decisiones de producto de Erato** en archivos Markdown autocontenidos, para copiarla a un repositorio nuevo que empieza desde cero (el autor cambió el diseño de la landing). El repositorio nuevo no tendrá `archivos/`, `openspec/`, `tests_md/` ni Engram, por lo que cada archivo copia el contenido que necesita (pasos de algoritmos, listas de campos, gramáticas, tablas) en lugar de remitir a una fuente.

## Índice

| Archivo | Contenido |
| --- | --- |
| [01-producto.md](01-producto.md) | Qué es Erato, funcionalidades, procesos automáticos, requisitos de calidad y qué queda fuera de alcance |
| [02-roles-y-reglas-de-trabajo.md](02-roles-y-reglas-de-trabajo.md) | Autor frente a agentes, reglas que no se negocian, ciclo de tests, commits, requisitos del README («Mi rol en el proyecto»), licencia AGPL y CLA |
| [03-arquitectura-y-stack.md](03-arquitectura-y-stack.md) | Actores, stack, estructura, Docker, variables de entorno, despliegue en Vercel Services |
| [04-modelo-de-datos.md](04-modelo-de-datos.md) | Conceptos de datos y relaciones |
| [05-esquema-mongodb.md](05-esquema-mongodb.md) | Esquema físico: campos, tipos, índices, documentos de ejemplo, validaciones |
| [06-permisos-y-visibilidad.md](06-permisos-y-visibilidad.md) | Reglas de visibilidad, matriz de permisos, política de errores 401/403/404, canción pública por enlace |
| [07-cuentas-sesiones-y-maestro.md](07-cuentas-sesiones-y-maestro.md) | Registro, login, sesiones, contrato de Maestro (real y mock), perfil y página `/perfil`, datos públicos, formato de errores, límite de intentos |
| [08-acordes-y-tonalidad.md](08-acordes-y-tonalidad.md) | **Algoritmo completo de detección de acordes y tonalidad** (diseño del autor), con ejemplos resueltos |
| [09-secciones-de-cancion.md](09-secciones-de-cancion.md) | Canción, acordes como dato, gramática de tablaturas y teclado del editor, letra, tareas, revisiones y concurrencia |
| [10-demos-y-archivos.md](10-demos-y-archivos.md) | Demos, comentarios, Cloudinary, flujo de subida, cuota, compresión en pausa |
| [11-bandas-e-invitaciones.md](11-bandas-e-invitaciones.md) | Enlaces de invitación, membresías, vigencia, abandono, quitar integrantes, transferencia, borrado en cascada de enlaces |
| [12-migracion.md](12-migracion.md) | Migración desde Atlas (modelo antiguo y mapeo; plan en revisión) |
| [13-diseno-visual.md](13-diseno-visual.md) | Reglas de diseño, design system, componentes Vue, rutas del frontend; **la landing anterior puede estar reemplazada** |
| [14-testing.md](14-testing.md) | Formato de `tests_md/`, traducción a tests ejecutables, qué se aprobó y resumen por área |

## Regla de precedencia usada

1. Las **decisiones del autor registradas en Engram** y las **revisiones fechadas de `archivos/`** (escritas o aprobadas por el autor) ganan sobre `descripcion_proyecto.md`, `AGENTS.md` anterior a esas revisiones y `bd_vieja.md`.
2. Los **casos de `tests_md/` aprobados por el autor** se tratan como decisiones del autor (aprobación global del 2026-10-18 y ampliaciones del 2026-10-20, 2026-10-21, 2026-10-23 y 2026-10-24).
3. **Las fechas posteriores ganan sobre las anteriores.**
4. `bd_vieja.md` es el modelo antiguo: se usa solo para la migración (archivo 12), nunca como modelo vigente.
5. Los artefactos escritos por agentes (`openspec/`, `odd/`) solo cuentan como decisión donde registran explícitamente una decisión o aprobación del autor; el resto se marca **[diseño]** (propuesto por un agente, sin aprobación explícita línea por línea).
6. Lo implementado únicamente en el árbol de trabajo sin confirmar (login y límite de intentos, tarea T4 de `perfil-backend`) **no es una decisión**; solo valen los casos aprobados que lo describen.
7. Cuando dos fuentes discrepan, el archivo temático expone la posición más reciente o autorizada y el archivo 15 registra la discrepancia.

Cada sección o archivo termina con una línea `Origen:` que nombra los documentos fuente o los identificadores de Engram (números de observación).

## Alcance de la consolidación

Fuentes leídas completas: `AGENTS.md`, `descripcion_proyecto.md`, `bd_vieja.md`, `CONTRIBUTING.md`, `CLA.md`, los 6 archivos de `archivos/`, los 12 archivos de `tests_md/`, `odd/tasks/` (2), `vercel.json`, `compose.yaml`, `compose.override.yaml`, `Makefile`, `openspec/config.yaml`, los READMEs de `erato-design-system/`, y de `openspec/`: `proposal`, `design`, `exploration` y los specs delta de `perfil-backend`; `proposal`, `design` y `archive-report` de los tres cambios archivados, más `exploration` de `design-system-vue` y de `perfil-frontend`; y los specs principales `app-routing` (parcial), `backend-runtime`, `frontend-theme`, `local-services`, `maestro-mock`, `profile-api-contract`, `test-harness`.

Fuentes leídas solo en parte: los specs principales `openspec/specs/design-system-components/spec.md` y `openspec/specs/profile-page/spec.md` (derivan de los casos de `tests_md/design_system.md` y `tests_md/perfil.md`, leídos completos; solo se leyeron sus encabezados y notas finales) y `app-routing` (primeras líneas).

Fuentes no leídas: `exploration.md` de `project-scaffolding`, los `tasks.md`, `apply-progress.md`, `verify-report.md` y los specs delta de los cambios archivados `project-scaffolding`, `design-system-vue` y `perfil-frontend`, y `openspec/changes/perfil-backend/tasks.md`; todos son registros de ejecución de lo ya recogido en los demás documentos. Tampoco se leyeron los HTML ni `tokens.css` del design system (por indicación).

Engram (proyecto `erato-rewrite`): se obtuvieron completas las observaciones 195, 196, 254 (ajena), 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 269, 270, 271, 272, 273, 274, 275, 276 (ajena), 277, 278, 281, 282, 283, 284, 285, 286, 287, 288, 289, 291, 292, 294, 309, 399, 400, 401, 408, 427, 434. Las búsquedas por tema (perfil, maestro, design system, demos, migración, revisiones, tablatura, vercel, decisiones) devolvieron además observaciones de ciclo de vida de los cambios SDD, que se contrastaron con los archivos de `openspec/`.
