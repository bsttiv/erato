# Migración desde el modelo antiguo — APROBADO (adaptación Cloudinary: 2026-10-31)

> **Estado: APROBADO por el autor (2026-10-18)** (AGENTS.md, regla 3). Formato en [`README.md`](README.md). Los tests usan dos bases MongoDB de prueba (antigua con la forma de `bd_vieja.md`, nueva vacía), Cloudinary falso y R2 falso.
>
> **Revisión del 2026-10-31, aprobada por el autor:** se reutilizan los audios existentes y sus identificadores, sin copias ni escrituras en Cloudinary. Las referencias a R2 y compresión de los casos históricos de abajo no son requisitos vigentes. Sus reemplazos y casos adicionales aprobados están al final. El resto de los casos conserva su aprobación anterior. Esta aprobación permite implementar los tests localmente, no ejecutar operaciones sobre datos remotos.

Reglas de origen (`arquitectura.md`, revisión aprobada; `conceptos_datos.md`; `bd_vieja.md`):

- Script único e idempotente; lee la base antigua y escribe en una base nueva del mismo cluster. La base antigua y Cloudinary no se tocan.
- Modo prueba (sin escribir): reporta formatos heredados y se detiene si `bands` o `invitations` no están vacías.
- Usuarios: hash Argon2id copiado tal cual; `username` desde el nombre visible normalizado (`Juan Pérez` → `juan-perez`), con sufijo numérico si choca.
- `refresh_tokens` se descartan.
- Canciones: `public`/`private` se mantienen; `share_slug` se conserva; `key_mode = manual`; se descartan `style_tags`, `sections_enabled`, `section_revs`.
- `composition_members` → membresía de canción (`memberships`, `target_type = song`) con el mismo rol; `band_members` e invitaciones antiguas no se mapean porque la migración se detiene si `bands` o `invitations` no están vacías.
- Acordes: notas MIDI conservadas, nombres recalculados con el algoritmo; para guitarra se deduce una digitación.
- Tablaturas: casi tal cual; barra `|` → columna de seis `|`; afinación estándar por defecto.
- Letra: ChordPro (`[Am7]texto`) → líneas con `col` + `chord_id`.
- Demos: Cloudinary → compresión → R2; comentarios conservan `demo_id`.
- Revisiones: no se migra el historial; el estado actual de cada sección queda como versión 1.
- Criterio de dato irrepresentable (2026-10-18, aprobado): si un dato antiguo no se puede representar fielmente en el modelo nuevo, el modo prueba lo reporta y la ejecución real se detiene sin escribir nada; el autor corrige el dato en origen y vuelve a correr.
- Se conservan los `ObjectId` antiguos (2026-10-18, aprobado).

## Modo prueba (`MIG`)

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-001 | Base antigua con datos; base nueva vacía | Ejecutar en modo prueba | La base nueva sigue vacía; R2 sin objetos; ninguna descarga de Cloudinary; el reporte lista las demos (IDs de Cloudinary y cantidad) |
| MIG-002 | Base antigua con acordes en formato `frets`, letra como string suelto y tablaturas heredadas | Modo prueba | El reporte lista cada formato heredado con su cantidad y los IDs de composición afectados |
| MIG-003 | Base **antigua** con `bands` no vacía | Modo prueba | Se detiene con error explícito; nada escrito |
| MIG-004 | Base antigua con `invitations` no vacía | Modo prueba | Se detiene; nada escrito |
| MIG-005 | Base antigua con `bands` e `invitations` vacías | Modo prueba | Termina con reporte y código de salida exitoso |
| MIG-006 | Datos que generarían colisiones de `username` | Modo prueba | El reporte muestra los `username` que recibirán sufijo |
| MIG-007 | MIG-003 o MIG-004 | Ejecución real | También se detiene (la ejecución real repite la verificación); nada escrito |
| MIG-008 | Base antigua con un dato irrepresentable (ver criterio) | Modo prueba y luego ejecución real | El modo prueba lo reporta con el ID de la composición y el motivo; la ejecución real se detiene sin escribir nada |
| MIG-009 | Base nueva con un documento cuyo `_id` no existe en la antigua (dato creado por usuarios) | Ejecución real | Se niega a correr; nada escrito |

## Base antigua intacta

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-010 | Huella (hash de todos los documentos) de la base antigua | Ejecución real | Huella idéntica después |
| MIG-011 | Cloudinary falso | Ejecución real | Solo lecturas; ningún borrado ni modificación |

## Usuarios

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-020 | Usuario antiguo con `password_hash` Argon2id | Migrar | `users.password_hash` idéntico byte a byte |
| MIG-021 | MIG-020 | Login con la contraseña antigua en la app nueva | `200` (ver `auth_sesiones.md`, AUTH-028) |
| MIG-022 | `display_name = "Juan Pérez"` | Migrar | `username = "juan-perez"`; `display_name` sin cambios |
| MIG-023 | Dos usuarios `"Juan Pérez"` | Migrar | `juan-perez` para el de `created_at` más antiguo (empate: menor `_id`) y `juan-perez-2` para el otro; un tercero recibe `juan-perez-3` |
| MIG-024 | Tres usuarios cuyos nombres normalizan igual (`"Juan Pérez"`, `"juan perez"`, `"JUAN PÉREZ"`) | Migrar | Tres `username` distintos, todos únicos |
| MIG-025 | `display_name` con caracteres especiales (`"Ñandú & Cía."`) | Migrar | `username = "nandu-cia"` (minúsculas, sin acentos, `ñ` → `n`, lo que no es `[a-z0-9]` → `-`, guiones colapsados y sin extremos) |
| MIG-026 | `display_name` vacío o solo símbolos | Migrar | `username = "usuario"` (con sufijo si choca) |
| MIG-026b | `display_name` que normaliza a más de 30 caracteres o a menos de 3 | Migrar | `username` recortado a 30; si queda con menos de 3, `usuario` (con sufijo si choca) |
| MIG-027 | Usuario con `email` en mayúsculas | Migrar | `email` en minúsculas |
| MIG-027b | Dos usuarios cuyos emails coinciden al pasarlos a minúsculas | Modo prueba y ejecución real | Criterio de dato irrepresentable (reporta y se detiene) |
| MIG-028 | Usuario con `token_version` | Migrar | El campo no existe en `users` nuevo |
| MIG-029 | Usuarios migrados | — | Ningún campo fuera del esquema aprobado (`email`, `username`, `display_name`, `password_hash`, fechas) |

## Sesiones

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-030 | `refresh_tokens` con documentos | Migrar | `sessions` vacía en la base nueva |

## Canciones

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-040 | `compositions` con `visibility = public` y `share_slug` | Migrar | `songs.visibility = public`; mismo `share_slug`; `GET /c/{share_slug}` funciona |
| MIG-041 | Composición `private` | Migrar | `visibility = private`; `share_slug = null` |
| MIG-042 | Composición `private` con `share_slug` residual | Migrar | `share_slug = null` (el slug existe solo si es pública) |
| MIG-043 | Cualquier composición | Migrar | `key_mode = manual`; `key` conservada |
| MIG-044 | Composición con `style_tags`, `sections_enabled`, `section_revs` | Migrar | Esos campos no existen en `songs` |
| MIG-045 | Composición personal | Migrar | `owner_type = user`, `owner_id` = dueño antiguo |
| MIG-046 | Composición con `band_id` no nulo (sin bandas en la base) | Migrar | Se migra como personal (`owner_type = user`, `owner_id` = dueño antiguo) y aparece en el reporte |
| MIG-047 | Composición con `bpm`, `band_editable`, `time_signature`, `status`, `title`, `created_at`, `updated_at` | Migrar | `tempo = bpm`; `band_editable` no existe en `songs`; los demás campos conservados con el mismo valor |
| MIG-048 | Composición con letra y acordes, sin tablaturas ni tareas | Migrar | `section_versions = 1` en todas las secciones (incluidas las vacías); `revisions` tiene un documento versión 1 para `lyrics` y para `chords`, y ninguno para las secciones vacías |
| MIG-048b | Cualquier composición | Migrar | `songs._id` = `_id` de la composición antigua (se conservan los `ObjectId`) |
| MIG-049 | `section_revisions` antiguas | Migrar | `revisions` no contiene historial antiguo |

## Membresías desde `composition_members`

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-050 | Composición con miembro `editor` | Migrar | Membresía `target_type = song`, `target_id` = canción, `user_id` = miembro, `role = editor` |
| MIG-051 | Miembro `viewer` | Migrar | Membresía con `role = viewer` |
| MIG-052 | MIG-050 | — | `invitation_id = null`; `joined_at` = fecha de la migración |
| MIG-053 | Miembro que también es el dueño | Migrar | Se omite (el dueño tiene acceso implícito); no se crea membresía para él |
| MIG-054 | Miembro duplicado en la misma composición | Migrar | Una sola membresía (índice único `(target_type, target_id, user_id)`) |
| MIG-055 | MIG-050 | El miembro lee y edita la canción en la app nueva | Acceso según su rol |

## Acordes

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-060 | Acorde antiguo con notas MIDI | Migrar | `notes` idénticas; `name` = salida del algoritmo de detección |
| MIG-061 | Acorde de guitarra sin trastes | Migrar | `frets` y `strings` no nulos, del mismo largo que `notes`, `strings` en 1..6 |
| MIG-062 | MIG-061 | — | La digitación deducida reproduce exactamente las `notes` con afinación estándar y es la más cómoda: una nota por cuerda, notas ascendentes de la cuerda 6 a la 1 (se pueden saltar cuerdas), menor apertura (máximo 4 trastes entre el menor y el mayor traste pisado, sin contar cuerdas al aire); empate → posición más baja en el mástil; luego más cuerdas al aire |
| MIG-062b | Acordes conocidos (parametrizado) | Deducir digitación | `[48,52,55,60,64]` (C) → `frets = [3,2,0,1,0]`, `strings = [5,4,3,2,1]`; `[45,52,57,60,64]` (Am) → `frets = [0,2,2,1,0]`, `strings = [5,4,3,2,1]`; `[40,47,52,55,59,64]` (Em) → `frets = [0,2,2,0,0,0]`, `strings = [6,5,4,3,2,1]` |
| MIG-062c | Dos digitaciones con la misma apertura | Deducir digitación | Se elige la de posición más baja; si persiste el empate, la de más cuerdas al aire; el resultado es el mismo en cada corrida (determinista) |
| MIG-063 | Acorde de piano | Migrar | `frets = null`, `strings = null` |
| MIG-064 | Acorde heredado con `frets` coherentes con sus `notes` (afinación estándar) | Migrar | Se usan esos `frets`; no se deduce digitación |
| MIG-064b | Acorde heredado con `frets` que contradicen sus `notes` | Modo prueba y ejecución real | Criterio de dato irrepresentable |
| MIG-065 | `chords.entries` con `instrument` a nivel de sección | Migrar | Cada acorde nuevo lleva su propio `instrument` (el de la sección) |
| MIG-066 | Acorde de guitarra sin digitación tocable (parametrizado: 7 notas; notas fuera del rango del mástil; ninguna forma con apertura ≤ 4 trastes) | Modo prueba y ejecución real | Criterio de dato irrepresentable (el reporte indica la composición, el acorde y el motivo) |
| MIG-067 | Cada acorde migrado | — | Tiene `id` propio y único en la canción |

## Tablaturas

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-070 | Tablatura antigua con `tabs` y barras `\|` | Migrar | `columns` equivalentes; cada barra es una columna de seis `\|` |
| MIG-071 | Sin afinación antigua | Migrar | `tuning = ["E4","B3","G3","D3","A2","E2"]` |
| MIG-072 | Tablatura con `strings != 6` | Modo prueba y ejecución real | Criterio de dato irrepresentable |
| MIG-073 | Tablatura solo con `content` (texto) | Modo prueba y ejecución real | Criterio de dato irrepresentable |
| MIG-074 | Celda antigua que no cumple el patrón nuevo | Modo prueba y ejecución real | Criterio de dato irrepresentable (el reporte indica tablatura, columna y cuerda) |
| MIG-075 | Tablatura migrada | — | Toda celda cumple el patrón de `canciones_secciones.md` |

## Letra

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-080 | `lyrics.content = "[Am7]Fly me to the [Dm7]moon"`; acordes Am7 y Dm7 existen | Migrar | Una línea `text = "Fly me to the moon"`, `chords = [{col 0, chord_id(Am7)}, {col 14, chord_id(Dm7)}]` |
| MIG-081 | Contenido con varias líneas (`\n`) | Migrar | Una entrada en `lines` por línea, en orden |
| MIG-082 | Línea solo con acordes `"[C] [G]"` | Migrar | `text = " "` (sin los acordes, con los espacios tal cual); `chords = [{col 0, C}, {col 1, G}]` |
| MIG-083 | Línea vacía | Migrar | `{ "text": "", "chords": [] }` |
| MIG-084 | Letra como string suelto (sin estructura `content`) | Migrar | Se interpreta igual que `content` |
| MIG-085 | ChordPro con un acorde que no existe en la sección de acordes | Modo prueba y ejecución real | Criterio de dato irrepresentable (el reporte indica composición, línea y nombre) |
| MIG-086 | Dos acordes con el mismo nombre antiguo en la sección | Migrar letra con ese nombre | `chord_id` del primero en el orden de la sección; el caso aparece en el reporte |
| MIG-086b | Acorde antiguo `name = "Am7"` cuyo nombre recalculado es distinto (p. ej. por la tonalidad) | Migrar letra con `[Am7]` | El emparejamiento usa el nombre antiguo: `chord_id` de ese acorde; su `name` nuevo es el recalculado |
| MIG-087 | Composición sin letra | Migrar | `lyrics = null` |
| MIG-088 | Toda letra migrada | — | Cada `chord_id` referencia un acorde existente de la canción |

## Demos y comentarios

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-090 | Demo con `cloudinary_public_id` | Migrar | Se descargó de Cloudinary, se comprimió y existe en R2 bajo `r2_key`; metadatos `title`, `uploaded_by`, `uploaded_at` conservados |
| MIG-091 | MIG-090 | — | `id` de la demo nueva = `demo_id` antiguo (para conservar comentarios) |
| MIG-092 | `composition_comments` de esa demo | Migrar | En `demo_comments` con `song_id` = canción, mismo `demo_id`, `author_id`, `timestamp_s`, `text`, `created_at` |
| MIG-093 | Descarga o compresión falla para una demo (Cloudinary falso falla 2 veces y luego responde) | Migrar | Se reintenta con espera creciente; la demo se migra en el tercer intento |
| MIG-093b | Descarga falla 3 veces seguidas | Migrar | La ejecución se detiene con error; al volver a correr, continúa sin duplicar lo ya migrado |
| MIG-094 | Demo migrada | — | `duration_s` recalculada del audio comprimido; `mime_type` y `size_bytes` corresponden al archivo comprimido |

## Idempotencia

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-100 | Ejecución real completada | Ejecutar de nuevo | Mismo número de documentos en cada colección; sin duplicados |
| MIG-101 | MIG-100 | — | R2 sin objetos duplicados (la misma clave se reutiliza) |
| MIG-102 | MIG-100 | — | Los `username` no reciben sufijos nuevos en la segunda corrida |
| MIG-103 | Primera corrida interrumpida a mitad | Ejecutar de nuevo | Termina el trabajo sin duplicar lo ya migrado (por idempotencia; sin mecanismo de checkpoint) |
| MIG-104 | Base nueva ya usada por la app después de migrar | Ejecutar de nuevo | Se niega a correr (ver MIG-009); nada escrito |

## Preguntas abiertas

Resueltas (2026-10-18, aprobadas): ~~1. modo prueba y red~~ (no descarga; lista las demos); ~~2. verificación de `bands`/`invitations`~~ (sobre la base antigua; se repite en la ejecución real); ~~3. sufijo~~ (`-2`, `-3`…; el original para el `created_at` más antiguo, empate por `_id`); ~~4. normalización de `username`~~ (minúsculas, sin acentos, `ñ` → `n`, lo demás → `-`, guiones colapsados y sin extremos, 3 a 30 caracteres, vacío → `usuario`; misma regla que la PQ 3 de `auth_sesiones.md`); ~~5. emails~~ (minúsculas; choque → criterio de dato irrepresentable); ~~6. slug residual~~ (se descarta); ~~7. `band_id` sin banda~~ (personal y reportada); ~~8. campos no mencionados~~ (`bpm` → `tempo`, `band_editable` se descarta, fechas conservadas); ~~9. versión 1~~ (todas las secciones; documento en `revisions` solo para las no vacías); ~~10. `invitation_id`/`joined_at`~~ (`null` / fecha de migración); ~~11. dueño en miembros~~ (se omite); ~~13. formato heredado de acordes~~ (`frets` coherentes se usan; contradictorios → criterio); ~~15, 16. tablaturas y celdas heredadas~~ (criterio); ~~17. ChordPro~~ (texto sin acordes con espacios tal cual; `col` en ese texto); ~~19. fallo de demo~~ (3 reintentos con espera creciente, luego se detiene; reanuda por idempotencia); ~~20. `duration_s`~~ (se recalcula); ~~21. reanudación~~ (por idempotencia); ~~22. base nueva con datos de usuarios~~ (se niega a correr); ~~23. `ObjectId`~~ (se conservan); ~~24. bandas e invitaciones antiguas~~ (cubierto por la verificación de `bands`/`invitations` vacías; `composition_members` → `memberships`).

Resueltas después (2026-10-18, aprobadas):

12. ~~Algoritmo para deducir la digitación~~ — resuelta (2026-10-18): la más cómoda (menor apertura ≤ 4 trastes; empate → posición más baja; luego más cuerdas al aire) (MIG-062 a MIG-062c).
14. ~~Acordes de guitarra sin digitación tocable~~ — resuelta (2026-10-18): criterio de dato irrepresentable (MIG-066).
18. ~~Acordes de la letra inexistentes o repetidos~~ — resuelta (2026-10-18): se empareja por el nombre antiguo; inexistente → criterio de dato irrepresentable; repetido → el primero en el orden de la sección, reportado (MIG-085, MIG-086, MIG-086b).

## Adaptación a Cloudinary — APROBADO (2026-10-31)

Decisión de producto y adaptación de tests aprobadas: reutilizar los archivos existentes conservando `cloudinary_public_id`. Esta tabla reemplaza los casos afectados. Implementados en `backend/tests/test_migration.py`. La infraestructura usa dos bases MongoDB de prueba y Cloudinary falso, sin R2. La base de origen y Cloudinary permanecen intactos. No se usa Atlas real ni se requieren credenciales reales en los tests.

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-001 (reemplazo) | Base antigua con demos; destino vacío | Modo prueba | Destino vacío; reporte con identificadores y cantidad; ninguna descarga, subida, copia, transformación ni borrado de archivos |
| MIG-011 (ajuste) | Cloudinary falso con archivos existentes | Migrar | Solo consultas de metadatos; contenido, identificadores y tipo de entrega sin cambios |
| MIG-090 (reemplazo) | Demo antigua con `cloudinary_public_id` legible como `video/authenticated`; metadatos válidos con `has_audio: true` | Migrar | Mismo identificador exacto, aunque no tenga el prefijo de las subidas nuevas; `title`, `uploaded_by`, `uploaded_at` conservados; no se crea ni modifica ningún archivo |
| MIG-093 (reemplazo) | Lectura de metadatos falla dos veces y luego responde | Migrar | Reintentos con espera creciente; demo migrada en el tercer intento, sin descargas ni escrituras en Cloudinary |
| MIG-093b (reemplazo) | Lectura de metadatos falla tres veces seguidas | Migrar | Se detiene con error; al repetir, continúa sin duplicar; el origen permanece intacto |
| MIG-094 (reemplazo) | Metadatos de la Admin API difieren de los valores antiguos | Migrar | `format`, `size_bytes` y `duration_s` proceden de Cloudinary; `mime_type` del mapeo vigente; no hay compresión ni `r2_key` |
| MIG-095 (nuevo) | Un identificador antiguo no puede leerse como `video/authenticated` | Prevalidar y migrar | Reporte con composición/demo y motivo; ejecución real detenida sin escrituras; no se cambia visibilidad, renombra, reemplaza ni omite el archivo |
| MIG-096 (nuevo) | Metadatos sin audio o insuficientes para el modelo vigente | Prevalidar y migrar | Criterio de dato irrepresentable: se reporta y la ejecución real se detiene sin escrituras; no se destruye el archivo antiguo |
| MIG-101 (reemplazo) | Migración completada | Repetir | Mismos documentos y referencias; inventario y contenido del Cloudinary falso idénticos antes y después; sin archivos duplicados ni modificados |

Los casos de reintentos preservan la política aprobada y cambian únicamente la operación que puede fallar. No hay cambios de esquema ni índices; el mapeo y ejemplo del documento están en la sección 5 de `decisiones/12-migracion.md`.

## Compatibilidad de IDs de demos — APROBADO (2026-10-31)

La conservación literal de MIG-091/MIG-092 contradice el tipo `string` del modelo antiguo frente al `ObjectId` vigente cuando el texto no es un ObjectId válido. Esta tabla reemplaza esos casos, según la sección 6 de `decisiones/12-migracion.md`:

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-091 (ajuste) | `demo_id` antiguo es un texto ObjectId válido | Migrar | `id` es el ObjectId equivalente; texto serializado equivalente; archivo Cloudinary e identificador del archivo sin cambios |
| MIG-091b (nuevo) | `demo_id` antiguo no es un ObjectId válido, por ejemplo `take-01` | Migrar y repetir | La misma composición/demo recibe un ObjectId estable en ambas corridas, sin duplicados; el origen no se modifica |
| MIG-092 (ajuste) | Comentarios de una demo de MIG-091 o MIG-091b | Migrar | `demo_comments.demo_id` es el ObjectId asignado a la demo correspondiente; `author_id`, `timestamp_s`, `text` y `created_at` conservados; ninguna referencia rota |

El esquema, los índices y `cloudinary_public_id` no cambian. Las colisiones de identidad se tratan mediante el criterio aprobado de prevalidación sin escrituras, no generando sufijos o IDs aleatorios en cada ejecución.

## Casos adicionales — APROBADO (2026-10-31)

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-047b | Composición sin `status` | Migrar | `status = idea`, como hacía la aplicación antigua |
| MIG-050b | Miembro sin `role` | Migrar | Membresía con `role = editor`, como hacía la aplicación antigua |
| MIG-092b | Comentario sin `author_id`, o miembro sin `user_id` | Modo prueba y ejecución real | Criterio de dato irrepresentable; nunca se genera un identificador nuevo |

## Corrección tras el modo prueba real — APROBADO (2026-10-31)

El modo prueba del 2026-10-31 mostró que, en guitarra, `chords.entries[].notes` guarda **seis trastes de la cuerda 6 a la 1**, con `-1` en las cuerdas mudas (`fretsToMidi` en `frontend/src/design-system/core/guitar.ts` del repositorio antiguo), no notas MIDI. Tampoco hay `frets` heredados, y dos demos están en formato `opus`.

| ID | Precondiciones | Acción | Esperado |
| --- | --- | --- | --- |
| MIG-060 (ajuste) | Acorde de guitarra `[-1,3,2,0,1,0]` | Migrar | `notes = [48,52,55,60,64]`, `frets = [3,2,0,1,0]`, `strings = [5,4,3,2,1]`; `name` = salida del algoritmo |
| MIG-060b (nuevo) | Acorde de guitarra que no tiene seis trastes entre `-1` y `24` | Modo prueba y ejecución real | Criterio de dato irrepresentable |
| MIG-043b (nuevo) | Composición sin `key` | Migrar | `key_mode = auto`; `key` = primera candidata, o `null` sin acordes; los nombres se calculan con esa tonalidad |
| MIG-096b (nuevo) | Demo con formato `opus` | Migrar | `format = opus`, `mime_type = audio/ogg` |

Se eliminan MIG-061, MIG-062, MIG-062b, MIG-062c, MIG-064, MIG-064b y MIG-066: sin notas MIDI en guitarra ni `frets` heredados no hay digitación que deducir ni comparar. MIG-043 queda solo para composiciones con `key`.
