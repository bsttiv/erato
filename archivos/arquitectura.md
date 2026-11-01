# Arquitectura del proyecto

Existen cinco actores principales en este proyecto:

- Frontend (VueJS con TailwindCSS)
- Backend (FastAPI)
- Base de datos (MongoDB)
- Almacenamiento (Cloudinary)
- Administrador de sesión

Para este último item, voy a utilizar mi proyecto Maestro (https://github.com/bsttiv/maestro). Todavía debo completar algunas cosas y testearlo correctamente, por lo que se debe crear una especie de "simulación" de sus endpoints y funcionamiento mientras aún no esté listo.

Además, actualmente poseo datos dentro de la base de datos de Erato en Atlas, por lo que probablemente se deba realizar algún tipo de migración. Especificamente, solía utilizar Cloudinary para el almacenamiento, pero ahora voy a cambiar a R2. Es posible también que haya cambiado alguna relación entre cada concepto de dato.

> **Revisión (2026-10-17, aprobada):** el mock de Maestro replica `POST /mint`, `POST /validate` y `POST /revoke` tal como existen hoy (errores 400 en texto plano) y además incluye `POST /refresh`, que el autor agregará luego a Maestro. El fingerprint (`context` en `/mint`, `fingerprint` en `/validate`) es un string que identifica de forma única el dispositivo en uso. Erato maneja registro, contraseñas (Argon2) y metadatos de sesión; obtiene el ID de usuario desde el claim `sub` del access token tras un `/validate` exitoso.

> **Revisión (2026-10-24, perfil-backend):** en el mock, `POST /revoke` recibe `{jti}` (el `jti` del access token) en lugar del token, para que Erato pueda revocar otras sesiones sin guardar sus tokens. El Maestro real adoptará ese contrato más adelante. Con el control habilitado, el mock registra las llamadas recibidas a `/mint`, `/validate`, `/revoke` y `/refresh` y las expone en `GET /__control/calls`; `POST /__control/reset` vacía ese registro.

> **Revisión (2026-11-01, aprobada):** Erato y el mock siguen el contrato real de Maestro (`bsttiv/maestro`, `9bb371f`), lo que deja sin efecto el `POST /revoke` con `{jti}` de la revisión del 2026-10-24. Las rutas viven bajo `/api/v1/maestro` y exigen `X-Api-Key` (variable `MAESTRO_API_KEY`). `POST /validate` devuelve `{userId, sessionId}`, los tokens inválidos responden 401, `POST /refresh` recibe `{refresh, fingerprint}` y `POST /revoke` recibe `{token}`. Como Maestro revoca solo por token y Erato no guarda tokens, cerrar sesión o la sesión actual revoca en Maestro con el access token, y cerrar otro dispositivo borra su fila en `sessions`: Erato lo rechaza de inmediato, aunque la sesión siga viva en Maestro hasta expirar (7 días como máximo).

> **Revisión (2026-10-17, aprobada): migración desde el modelo antiguo** (`bd_vieja.md`, base actual en Atlas).
>
> - Script único e idempotente: lee la base antigua y escribe en una base **nueva** del mismo cluster. La base antigua y los archivos de Cloudinary no se tocan hasta validar la migración.
> - Primero se corre en modo prueba (sin escribir), que reporta formatos heredados (acordes con `frets`, letra como string suelto, etc.) y se detiene si `bands` o `invitations` no están vacías (hoy no existen bandas).
> - Usuarios: el hash Argon2id se copia tal cual; el nombre de usuario se genera desde el nombre visible normalizado, con sufijo si choca.
> - Sesiones antiguas (`refresh_tokens`): se descartan; los usuarios vuelven a iniciar sesión vía Maestro.
> - Canciones: `public` → pública, `private` → privada; `share_slug` → Slug compartido; Modo tonalidad = manual; `style_tags`, `sections_enabled` y `section_revs` se descartan.
> - `composition_members` (editor/viewer) → Invitación tipo canción, aceptada, editor/lector.
> - Acordes: notas MIDI se conservan, nombres se recalculan con el algoritmo; para guitarra se deduce una digitación (el modelo antiguo no guardaba trastes).
> - Tablaturas: se conservan casi tal cual (barra `|` → columna de 6 `|`, afinación estándar por defecto).
> - Letra: ChordPro (`[Am7]texto`) → líneas con `col` + `chord_id`.
> - Demos: se descargan de Cloudinary, se comprimen y se suben a R2; comentarios se copian conservando `demo_id`.
> - Revisiones: no se migra el historial antiguo; el estado actual de cada sección queda como versión 1.

> **Revisión (2026-10-18, aprobada): subida y reproducción de demos.** Las Vercel Functions aceptan como máximo 4.5 MB por petición y por respuesta, así que el audio nunca pasa por el backend. El navegador sube el archivo crudo directo a R2 con una URL firmada (`uploads/<song_id>/<user_id>/<uuid>`); al confirmar, el backend lo lee desde R2, lo comprime de forma síncrona (Opus en Ogg, 96 kbps), guarda la versión final, escribe los metadatos y borra el crudo. El bucket es privado: la reproducción usa URLs firmadas de 15 minutos. Una regla de ciclo de vida de R2 borra los crudos abandonados a las 24 horas. Los límites (100 MB, 20 minutos) se confirman midiendo la compresión en Vercel antes de implementar.

> **Revisión (2026-10-18, aprobada): tests e infraestructura local.** Los tests ejecutables viven en `backend/tests/` (uno por cada archivo de `tests_md/`) y en `frontend/src/**/*.spec.ts`, junto al código que prueban. El `docker compose` local y el de tests levantan MongoDB como *replica set* de un solo nodo (las operaciones atómicas de varias colecciones usan transacciones), MinIO como sustituto de R2 y una imagen de backend con `ffmpeg`. Maestro siempre se reemplaza por su mock.

> **Revisión (2026-10-31, aprobada): vuelta a Cloudinary.** Cloudinary reemplaza a R2 y deja sin efecto lo que las revisiones anteriores dicen sobre R2, SeaweedFS, MinIO y la copia desde `uploads/`. El audio sigue sin pasar por el backend: el navegador hace un `POST` firmado directo a Cloudinary, con `resource_type: video` y `type: authenticated`. Al confirmar, el backend lee formato, tamaño y duración desde Cloudinary y aplica los límites y la cuota. La reproducción usa `private_download_url` con vencimiento de 15 minutos. Las URLs con token requieren el plan Advanced, y las URLs firmadas `authenticated` no vencen. Sin `CLOUDINARY_URL`, la aplicación levanta y las demos responden `503 storage_unavailable`. El plan de migración debe revisarse: los audios antiguos ya están en Cloudinary, pero falta comprobar si pueden pasar a entrega privada.

> **Revisión (2026-10-31, aprobada): reutilización de audios antiguos.** El autor eligió reutilizar los archivos existentes y sus `cloudinary_public_id`, sin copiarlos ni modificarlos durante la migración. Eliminar una demo desde la aplicación nueva después del cambio de aplicación también eliminará el archivo que usa la antigua; no se conserva una copia independiente. La adaptación de metadatos y tests de `decisiones/12-migracion.md` y `tests_md/migracion.md` también fue aprobada para su implementación local. No se inspeccionan ni migran datos remotos sin autorización específica. Si un archivo no admite el acceso privado esperado, su tratamiento vuelve al autor antes de cambiarlo.
