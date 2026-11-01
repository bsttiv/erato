# 02 - Roles, reglas de trabajo, README y licencia

## 1. Roles

- **El autor diseña el sistema.** Define el producto, la arquitectura, el modelo de datos y las reglas de permisos, y aprueba los tests.
- **Los agentes implementan** lo que el autor definió, y **consultan antes de decidir** algo que no esté cubierto.
- Principio reiterado por el autor (2026-10-17): **no extender una respuesta del autor a roles o casos no declarados; preguntar.** (Ejemplo registrado: un agente había inventado un «lector de banda»; el autor lo corrigió.)
- El harness de implementación: **Gentle-AI, Codex y Claude** (no Gemini, como decía un `AGENTS.md` antiguo).

## 2. Reglas que no se negocian

1. **Modelo de datos: consultar siempre.** Antes de crear o modificar colecciones, esquemas, campos, índices, relaciones, validaciones o migraciones de MongoDB, detenerse y presentar una propuesta (campos con tipos, documento de ejemplo, índices y el porqué). Esperar aprobación explícita. Un modelo «provisional» también requiere aprobación. Los conceptos vigentes están en los archivos 04 y 05; el modelo antiguo es solo referencia y podría requerir una migración (que también se consulta).
2. **Arquitectura: la define el autor.** No introducir capas, patrones ni estructura de carpetas que contradigan el archivo 03. Si algo no está cubierto, preguntar.
3. **Tests: el agente propone, el autor aprueba.** El agente redacta la propuesta de tests; el autor la revisa, pide cambios si hace falta y la aprueba. Ningún test se da por aprobado ni se implementa sin esa aprobación explícita. Un test nuevo posterior sigue el mismo ciclo. (Archivo 14.)
4. **Backend simple.** Sin abstracciones especulativas, sin servicios extra ni infraestructura que no se haya pedido.
5. **Diseño visual desde el design system.** No inventar colores, tipografías, radios ni componentes. Si algo no existe en el sistema, proponerlo antes de crearlo. (Archivo 13.)
6. **Pregunta ante la ambigüedad.** Una pregunta a la vez, con alternativas y sus ventajas y desventajas cuando haya una bifurcación real.
7. **Sin secretos en el repositorio.** Credenciales y cadenas de conexión van en variables de entorno, documentadas en `.env.example`.
8. **Permisos en el backend.** Toda regla de acceso se valida en el servidor en cada petición; ocultar botones en el frontend no es seguridad.

## 3. Forma de trabajo

- **Pasos pequeños y verificables;** al cerrar cada paso, resumir qué cambió y qué falta.
- **Commits con Conventional Commits, sin atribución a IA** (sin `Co-Authored-By` ni equivalentes).
- `docker compose up` debe bastar para levantar el proyecto en local.
- **TDD estricto** (desde que existe el comando único de tests): RED observado con los IDs de casos aprobados, GREEN, refactor; un caso = una función de test; los tests solo usan entradas de casos aprobados.
- **Presupuesto de revisión de ~400 líneas** de cambios por PR/unidad de trabajo. Si una entrega lo supera, se divide en PR encadenados; una excepción de tamaño exige aprobación del autor. La estrategia de entrega por defecto es «preguntar ante riesgo» (`ask-on-risk`); las cadenas usadas fueron `feature-branch-chain` (andamiaje y sistema de diseño) y `stacked-to-main` (perfil). Los commits, `push`, PR y *merge* se hacen **solo cuando el autor lo pide o lo autoriza**.
- **Enrutamiento de modelos por fase** (decisión del autor, 2026-10-17): explorar, proponer, especificar, diseñar y planificar tareas con el modelo de mayor capacidad (opus); implementar con Codex (`gpt-6.1-sol`, esfuerzo medio); verificar y archivar con un modelo intermedio (sonnet).
- Desde el 2026-10-24 el cambio `perfil-backend` se pasó de SDD (desarrollo guiado por especificaciones) a ODD (flujo orgánico con documento de tareas por funcionalidad); para cambios nuevos, el autor decide entre SDD y ODD.
- **Idioma:** los documentos de producto del autor (`AGENTS.md`, `archivos/`, `tests_md/`) están en español; los artefactos de los agentes (especificaciones, diseños, documentos de tareas) y el código se escribieron en inglés, por convención de trabajo de los agentes, no como decisión explícita del autor. El README principal es en inglés, con enlace a una versión en español (sección 5).

## 4. Qué existía antes de empezar de cero (contexto)

Estado registrado el 2026-10-30 en el repositorio anterior (rama `feat/perfil-backend`):

- Andamiaje completo (entorno Docker, `make test`, mock de Maestro, tema de Tailwind sobre los tokens): archivado el 2026-10-20.
- Componentes base del design system en Vue y router de la aplicación: archivado el 2026-10-22.
- Página `/perfil` (frontend) con Card, Alert y Field: archivada el 2026-10-24.
- Backend de perfil (`perfil-backend`): mock de Maestro con `/revoke {jti}` y registro de llamadas (T1), cimientos (T2) y registro de usuarios (T3) confirmados; login y límite de intentos (T4) implementado pero sin confirmar; T5 a T8 pendientes.
- Nada de canciones, bandas, invitaciones, demos, acordes, tablaturas ni letras está implementado (solo especificado en las pruebas aprobadas).

## 5. README del proyecto (requisitos)

Se genera un `README.md` en la raíz que explique todo el proyecto, **escrito en inglés**, con un enlace a una versión en español (por ejemplo `README.es.md`). **Forma parte del portafolio profesional del autor y lo leerán reclutadores**, así que debe quedar claro su rol. Contenido:

1. Qué es Erato y qué problema resuelve.
2. Funcionalidades principales.
3. Stack técnico y arquitectura (diagrama simple).
4. Cómo correrlo en local con Docker y cómo se despliega en Vercel.
5. **Sección «Mi rol en el proyecto»**:
   - La implementación se hizo con un **harness de agentes de IA**: **Gentle-AI**, **Codex** y **Claude**.
   - **El autor diseñó el sistema**: producto, arquitectura, modelo de datos, permisos y dirección visual; revisó y aprobó los tests. También dirigió, revisó y validó el trabajo de los agentes.
   - **El algoritmo de detección de acordes y tonalidad es diseño del autor** (nombrar acordes según la tonalidad y proponer todas las tonalidades candidatas para que el usuario elija); los agentes propusieron refinamientos que el autor aprobó. **Debe destacarse en el README.** Detalle en el archivo 08.
   - **No presentar el código como escrito a mano por el autor ni minimizar su rol.**
6. Enlace a la carpeta del design system con una breve descripción de su estética.

## 6. Licencia y contribuciones

Fuentes: `CONTRIBUTING.md` y `CLA.md` (texto en inglés).

- Erato es de código abierto bajo la **GNU AGPL-3.0**, y su autor también opera una versión comercial hospedada.
- Se aceptan ramas de vida corta y PR descriptivos.
- **Contributor License Agreement (CLA)**, versión 1.0, vigente desde el 3 de octubre de 2026; titular del proyecto («Owner»): **Bastián Alexander Valencia Ull**. Antes de fusionar un PR, el contribuyente debe firmarlo; un bot de CLA comenta en el primer PR con las instrucciones; se firma con un comentario: «I have read the CLA Document and I hereby sign the CLA».
- Contenido principal del CLA: el contribuyente **conserva la titularidad** de sus contribuciones y otorga al Owner (y a los receptores del software distribuido) una licencia de derechos de autor perpetua, mundial, no exclusiva, gratuita e irrevocable para reproducir, preparar obras derivadas, mostrar, ejecutar, sublicenciar y distribuir; esa licencia incluye el **derecho de relicenciar** bajo los términos que el Owner elija (otras licencias de código abierto y licencias comerciales propietarias, incluido el servicio hospedado del Owner); **compromiso de código abierto:** toda contribución aceptada en el repositorio público seguirá disponible bajo la AGPL-3.0 u otra licencia aprobada por la OSI; licencia de patentes (termina para quien inicie litigio de patentes); no hacer valer derechos morales cuando la ley lo permita; declaraciones del contribuyente (derecho a otorgar las licencias, originalidad, notificar si dejan de ser ciertas); contribuciones «tal cual», sin obligación de soporte ni de uso; ley aplicable de la República de Chile con tribunales competentes de Santiago; el Owner puede publicar versiones nuevas del CLA, que se aplican solo a contribuciones posteriores a la firma.

Origen: `AGENTS.md`; `descripcion_proyecto.md`; `CONTRIBUTING.md`; `CLA.md`; `openspec/config.yaml`; `odd/tasks/perfil-backend.md`; memoria de enrutamiento de modelos (Engram 255); Engram 195, 256, 263, 274, 275, 399.
