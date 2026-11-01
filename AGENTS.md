# AGENTS.md — Erato

Instrucciones para cualquier agente de código (Claude, Codex, Gentle-AI u otro) que trabaje en este repositorio. Léelas completas antes de escribir código. La fuente de verdad del producto es `descripcion_proyecto.md`, complementada por los documentos del autor en `archivos/`:

| Archivo | Contenido |
| --- | --- |
| `archivos/arquitectura.md` | Actores del sistema, Maestro, migración |
| `archivos/conceptos_datos.md` | Conceptos de datos y relaciones (base del modelo; cambios se anotan en su sección) |
| `archivos/entradas_manuales.md` | Acciones que hace el usuario |
| `archivos/autonomo_automatico.md` | Procesos que hace el servidor |
| `archivos/restricciones.md` | Restricciones y requisitos de calidad |

## Qué es Erato

Erato (por la musa griega de la lírica coral y amorosa) es una aplicación web donde una banda guarda sus **composiciones**. Cada composición reúne acordes, tablaturas, letras, demos grabadas y tareas pendientes de una canción, en una interfaz fácil de entender.

## Roles

- **El autor diseña el sistema.** Define el producto, la arquitectura, el modelo de datos y las reglas de permisos, y aprueba los tests.
- **Los agentes implementan** lo que el autor definió, y consultan antes de decidir algo que no esté cubierto.

## Reglas que no se negocian

1. **Modelo de datos: consultar siempre.** Antes de crear o modificar colecciones, esquemas, campos, índices, relaciones, validaciones o migraciones de MongoDB, detente y presenta tu propuesta (campos con tipos, documento de ejemplo, índices y el porqué). Espera aprobación explícita. Un modelo «provisional» también requiere aprobación. Los conceptos vigentes están en `archivos/conceptos_datos.md`. El modelo antiguo está en `bd_vieja.md`: sirve de referencia, no es el modelo vigente, y podría requerir una migración (que también se consulta).
2. **Arquitectura: la define el autor.** Sus decisiones están en `archivos/arquitectura.md`. No introduzcas capas, patrones ni estructura de carpetas que contradigan ese documento. Si algo no está cubierto, pregunta.
3. **Tests: el agente propone, el autor aprueba.** El agente redacta la propuesta de tests en `tests_md/`; el autor la revisa, pide cambios si hace falta y la aprueba. Ningún test se da por aprobado ni se implementa sin esa aprobación explícita. Un test nuevo posterior sigue el mismo ciclo.
4. **Backend simple.** Sin abstracciones especulativas, sin servicios extra ni infraestructura que no se haya pedido.
5. **Diseño visual desde `erato-design-system/`.** No inventes colores, tipografías, radios ni componentes. Si algo no existe en el sistema, propónlo antes de crearlo.
6. **Pregunta ante la ambigüedad.** Una pregunta a la vez, con alternativas y sus ventajas y desventajas cuando haya una bifurcación real.
7. **Sin secretos en el repositorio.** Credenciales y cadenas de conexión van en variables de entorno, documentadas en `.env.example`.
8. **Permisos en el backend.** Toda regla de acceso se valida en el servidor en cada petición; ocultar botones en el frontend no es seguridad.

## Stack técnico

| Capa | Tecnología |
| --- | --- |
| Backend | Python + FastAPI |
| Frontend | Vue 3 + TailwindCSS |
| Base de datos | MongoDB (Atlas en producción) |
| Almacenamiento de archivos | Cloudinary |
| Sesiones | Maestro (`github.com/bsttiv/maestro`), simulado con un mock mientras no esté listo |
| Contenedores | Docker (`docker compose` para el entorno local) |
| Deploy | Vercel |
| Repositorio | GitHub |

TailwindCSS se usa con criterio: los tokens del design system (`tokens.css`) se mapean al tema de Tailwind, y los estilos repetidos se extraen como componentes Vue o capas `@layer components`, no se copian clase por clase.

## Funcionalidades

### Cuentas y espacios de trabajo

- Registro e inicio de sesión.
- Dos espacios de trabajo: **personal** y **banda**.
- Personal: solo el dueño ve sus composiciones, salvo que invite a alguien.
- Banda: un usuario crea una banda e invita personas.
- Invitaciones a canción con rol **editor** (puede editar) o **lector** (solo ve). Invitaciones a banda sin rol: **todos los miembros de una banda son editores** de sus canciones.
- Sesiones con access y refresh tokens; un usuario puede tener varias sesiones (dispositivos).
- Solo el nombre visible y el nombre de usuario son públicos; ningún otro dato del usuario se expone.

### Composiciones

- Crear, ver, editar y borrar.
- Secciones opcionales: acordes, tablaturas, letra, demos y tareas.

### Compartir y visibilidad

- Una composición se comparte mediante un **enlace**.
- Visibilidad: **privada** o **pública**, combinada con el dueño de la canción:
  - **Personal privada:** la ven el dueño y los usuarios invitados.
  - **De banda privada:** la ven (y editan) todos los miembros de la banda, y los usuarios invitados.
  - **Pública** (personal o de banda): cualquiera con el enlace puede verla.
- En todos los niveles, editar requiere una invitación con rol editor.

### Acordes

- Vista de **guitarra** (trastes vistos desde arriba) o **piano**, a elección del usuario, para ver y agregar notas.
- El **nombre del acorde se detecta automáticamente** a partir de las notas, nunca queda como «desconocido», y se nombra según la tonalidad de la canción.
- La **tonalidad**: el sistema propone un arreglo de tonalidades candidatas a partir de los acordes y el usuario elige (modo automático), o la fija a mano (modo manual). Sin acordes, no hay candidatas.
- Un mismo acorde puede tener varias versiones (formas); en la letra se distinguen y, al pasar el cursor, se ve la forma exacta.
- Los acordes se pueden ubicar sobre la letra; se filtran por instrumento y se muestran en carrusel si son muchos.

### Tablaturas

- Seis cuerdas, edición manual, sin generación automática.
- Ingresar notas debe ser cómodo (teclado, flechas, técnicas como h, p, b, /, ~, x).

### Letras

- Se pueden **maximizar**.
- **Desplazamiento automático** con velocidad ajustable.

### Demos (audio)

- Cada composición tiene su propia lista de demos; un audio pertenece a una sola composición.
- El usuario elige qué demo reproducir.
- Comentarios anclados a un **timestamp** del audio.
- El servidor **comprime** las demos al subirlas; los archivos viven en Cloudinary.

### Revisiones

- Los cambios se guardan explícitamente y se versionan por sección.

### Tareas

- Lista de pendientes común: agregar, marcar como hecha y borrar.

## Diseño visual

- Base: `erato-design-system/` (`erato-landing/` y `erato-core/erato-pantallas/`). Lee sus `README.md` y toma los HTML y CSS como referencia.
- Ambiente: un **bar de jazz**. Fondos oscuros, luces cálidas y destellos de esas mismas luces. Frank Sinatra sonando de fondo.
- La **landing no muestra precios ni medios de pago**; la única llamada a la acción es «Empieza gratis». La maqueta actual incluye planes: hay que quitarlos.
- Accesibilidad: contraste mínimo 4.5:1 en texto, foco de teclado visible y controles semánticos (`<button>`, `<input>`, `<label>`).

## Forma de trabajo

- Pasos pequeños y verificables; al cerrar cada paso, resume qué cambió y qué falta.
- Commits con Conventional Commits, sin atribución a IA.
- `docker compose up` debe bastar para levantar el proyecto en local.

## README.md del proyecto

Genera un `README.md` en la raíz que explique todo el proyecto, **escrito en inglés**, con un enlace a una versión en español (por ejemplo `README.es.md`). Forma parte del portafolio profesional del autor y lo leerán reclutadores, así que debe quedar claro su rol:

1. Qué es Erato y qué problema resuelve.
2. Funcionalidades principales.
3. Stack técnico y arquitectura (diagrama simple).
4. Cómo correrlo en local con Docker y cómo se despliega en Vercel.
5. **Sección «Mi rol en el proyecto»**:
   - La implementación se hizo con un **harness de agentes de IA**: **Gentle-AI**, **Codex** y **Claude**.
   - **El autor diseñó el sistema**: producto, arquitectura, modelo de datos, permisos y dirección visual; revisó y aprobó los tests. También dirigió, revisó y validó el trabajo de los agentes.
   - **El algoritmo de detección de acordes y tonalidad es diseño del autor** (nombrar acordes según la tonalidad y proponer todas las tonalidades candidatas para que el usuario elija); los agentes propusieron refinamientos que el autor aprobó. Debe destacarse en el README. Detalle en `archivos/autonomo_automatico.md`.
   - No presentes el código como escrito a mano por el autor ni minimices su rol.
6. Enlace a `erato-design-system/` con una breve descripción de su estética.

## Decisiones pendientes

Se completan a medida que el autor responde. Ningún agente las resuelve por su cuenta.

- [x] Conceptos de datos (ver `archivos/conceptos_datos.md`).
- [x] Esquema físico de MongoDB (ver `archivos/esquema_mongodb.md`).
- [x] Contenido de `archivos/arquitectura.md`.
- [x] Archivos de entrada del autor, en `archivos/`.
- [x] Modelo de revisiones por sección (ver `archivos/conceptos_datos.md`).
- [x] Modelo de tablatura (ver `archivos/conceptos_datos.md`).
- [x] Contrato del mock de Maestro: `/mint`, `/validate`, `/revoke` y `/refresh` (ver `archivos/arquitectura.md`).
- [x] Modelo de la letra con acordes ubicados (ver `archivos/conceptos_datos.md`).
- [x] Plan de migración desde Atlas, reutilizando los audios de Cloudinary (2026-10-31; ver `decisiones/12-migracion.md`).
- [x] Formato de `tests_md/` y cómo se traducen a tests ejecutables (ver `tests_md/README.md`).
- [x] Método de autenticación: Maestro (access + refresh tokens).
- [x] Almacenamiento de los audios: Cloudinary, con entrega privada y URLs que vencen a los 15 minutos (2026-10-31).
- [x] Estrategia de deploy del backend en Vercel y MongoDB en producción: Vercel Services (`vercel.json`), con el frontend en `/` y el backend FastAPI en `/api` (entrypoint `backend/app/asgi.py`). Las variables de entorno, incluida la conexión a MongoDB Atlas, se configuran en el proyecto de Vercel. La compresión de demos en el servidor queda en pausa (2026-10-23).
- [x] Componentes del design system: se reimplementan en Vue, sin wrappers de React. Cada componente se implementa en el cambio de su funcionalidad; los componentes base (Button, Icon, Tag, Segmented, SideNav) van en un cambio propio (`design-system-vue`).
