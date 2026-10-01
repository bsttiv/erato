# AGENTS.md — Erato

Instrucciones para cualquier agente de código (Claude, Gemini, Gentle-AI u otro) que trabaje en este repositorio. Léelas completas antes de escribir código.

## Qué es Erato

Erato (por la musa griega de la lírica coral y amorosa) es una aplicación web donde una banda guarda sus **composiciones**. Cada composición reúne los acordes, tablaturas, letras, demos grabadas y tareas pendientes de una canción, en una interfaz fácil de entender para cualquier integrante.

## Reglas que no se negocian

1. **El modelo de datos lo decide el autor del proyecto.** Antes de crear o modificar colecciones, esquemas, campos, índices, relaciones o reglas de validación de MongoDB, **detente y consulta**. Presenta tu propuesta (colecciones, campos con tipos, ejemplos de documentos, índices y el porqué) y espera aprobación explícita. Esto incluye:
   - cómo se guardan acordes, tablaturas, letras, demos, comentarios y tareas;
   - cómo se modelan usuarios, invitaciones, permisos y visibilidad;
   - dónde y cómo se almacenan los archivos de audio;
   - cualquier migración o cambio en datos existentes.
   No avances con supuestos «temporales»: un modelo provisional también requiere aprobación.
2. **El diseño visual sale de `erato-design-system/`.** No inventes colores, tipografías, radios ni componentes nuevos. Si algo no existe en el sistema, propónlo antes de crearlo.
3. **Pregunta ante la ambigüedad.** Si una decisión de arquitectura no está cubierta aquí (framework del backend, autenticación, almacenamiento de archivos, estructura de carpetas), propón opciones con sus ventajas y desventajas y espera respuesta.
4. **No subas secretos.** Credenciales, cadenas de conexión y claves van en variables de entorno, documentadas en `.env.example` y nunca commiteadas.

## Stack técnico

| Capa | Tecnología | Notas |
| --- | --- | --- |
| Backend | Python (FastAPI) | Framework confirmado por el autor (FastAPI para ASGI en Vercel y local). |
| Frontend | Vue.js (Vue 3) | Composition API. |
| Base de datos | MongoDB | El esquema requiere aprobación (ver regla 1). |
| Contenedores | Docker | `docker compose` para levantar el entorno local completo (backend, frontend, MongoDB). |
| Deploy | Vercel | Frontend y backend Python (funciones serverless de Vercel). Confirma la estrategia de deploy del backend antes de implementarla. |
| Repositorio | GitHub | Ramas cortas por funcionalidad y pull requests descriptivos. |

Puntos para confirmar con el autor antes de implementarlos:
- El backend en Vercel corre como funciones serverless, y Docker sirve para el entorno local y para que el proyecto sea portable. Si una funcionalidad no encaja en serverless (procesar audio, conexiones largas), avisa y propón alternativas.
- MongoDB en producción necesita un servicio administrado (por ejemplo, MongoDB Atlas).
- Los audios de los demos necesitan almacenamiento de archivos: propón opciones (Vercel Blob, S3, GridFS…) y espera la decisión.

## Funcionalidades

### Composiciones

- Crear, ver, editar y borrar composiciones.
- Cada composición puede incluir, de forma **opcional**, cualquiera de estas secciones: acordes, tablaturas, letra, demos y tareas.

### Acordes

- Se muestran y editan sobre un diagrama de **guitarra** o de **piano**, a elección del usuario.
- El usuario marca o agrega las notas sobre el diagrama.
- El **nombre del acorde se detecta automáticamente** a partir de las notas (al estilo de oolimo), incluidos acordes con barra (`D/F#`) y extendidos (`Cmaj7`, `F#m7b5`, `D9`).
- Referencia: `Erato.ChordEditor` y `Erato.detectChord()` en el design system.

### Tablaturas

- Se escriben a mano sobre 6 cuerdas, sin generación automática.
- Ingresar notas debe ser cómodo: escribir con el teclado, moverse con las flechas, insertar compases y técnicas (h, p, b, /, ~, x).
- Referencia: `Erato.TabEditor` y `Erato.tabToText()`.

### Letras

- Se pueden **maximizar** a pantalla completa.
- Tienen **desplazamiento automático** con velocidad ajustable por el usuario.
- Admiten acordes sobre la sílaba (`[Am7]Bajo el farol…`) y rótulos de sección (`# Coro`).
- Referencia: `Erato.LyricsViewer`.

### Demos (audio)

- Cada composición tiene su **propia lista de demos**; un audio pertenece a una sola composición.
- El usuario elige qué demo reproducir.
- Se pueden agregar **comentarios anclados a un momento** (timestamp) de cada audio y saltar a ese punto.
- Referencia: `Erato.DemoPlayer`.

### Tareas

- Una lista de pendientes común y corriente: agregar, marcar como hecha, borrar y limpiar las hechas.
- Referencia: `Erato.TodoList`.

### Usuarios

- Registro e inicio de sesión.
- El método de autenticación (correo y contraseña, OAuth con Google, sesiones o JWT) debe proponerse y confirmarse antes de implementarlo.

### Compartir

- Una composición se comparte mediante un **enlace**.
- **Pública:** cualquier persona con el enlace puede **verla**, incluso sin cuenta. Solo los **usuarios invitados** pueden **editar**.
- **Privada:** solo los usuarios invitados pueden verla y editarla. El enlace no da acceso a nadie más.
- Los permisos se validan **en el backend** en cada petición, no solo ocultando botones en el frontend.

## Diseño visual

- El sistema de diseño está en `erato-design-system/`. Empieza siempre por su `README.md`: explica voz, color, tipografía, espaciado, iconografía y cómo usar cada componente.
- Ambiente: un **bar de jazz** a medianoche. Fondos oscuros, luces cálidas y destellos de esas mismas luces. Piensa en Frank Sinatra sonando de fondo.
- Usa los tokens (`tokens.css` / `tokens.json`); no escribas colores, tamaños ni radios a mano.
- Hay dos temas: **Noche** (principal, oscuro) y **Matiné** (claro). Todo debe verse bien en ambos.
- Carga los estilos en este orden: `tokens.css`, `components/bundle.css` y luego `components/bundle.js`, después de React 18. Los componentes del bundle son de React; para usarlos en Vue, envuélvelos (por ejemplo, montándolos en un componente Vue) o reimpleméntalos en Vue respetando exactamente su aspecto y comportamiento. **Consulta cuál de los dos caminos tomar antes de empezar.**
- Los textos de la interfaz van en español, tuteando, sin signos de exclamación ni emoji (ver «Voz y contenido» en el README del design system).
- Accesibilidad: contraste mínimo de 4.5:1 en texto, foco de teclado visible (`focus-ring`) y controles reales (`<button>`, `<input>`, `<label>`).

## Forma de trabajo

- Trabaja en pasos pequeños y verificables. Al terminar cada paso, resume qué cambiaste y qué falta.
- Escribe pruebas para la lógica del backend (permisos, visibilidad, CRUD) y para la lógica no trivial del frontend (detección de acordes, edición de tablaturas).
- Mantén el entorno reproducible: `docker compose up` debe bastar para levantar el proyecto en local.
- Documenta las variables de entorno en `.env.example`.
- Commits en español, en presente y descriptivos («Agrega comentarios con timestamp a los demos»).

## README.md del proyecto

Genera un `README.md` en la raíz que explique todo el proyecto. Este proyecto forma parte del portafolio profesional del autor y lo leerán reclutadores, así que debe quedar muy claro **qué rol cumplió el autor**. Debe incluir:

1. **Qué es Erato** y qué problema resuelve.
2. **Funcionalidades** principales, con capturas o GIFs cuando existan.
3. **Stack técnico** y arquitectura (diagrama simple de frontend, backend, base de datos y almacenamiento).
4. **Cómo correrlo** en local con Docker y cómo se despliega en Vercel.
5. **Sección «Mi rol en el proyecto»**, redactada de forma explícita:
   - El desarrollo se hizo con un **harness de agentes de IA**: **Gentle-AI**, **Gemini** y **Claude**.
   - **El autor diseñó el sistema**: definió el producto y sus funcionalidades, la arquitectura, el modelo de datos y las reglas de permisos, y la dirección visual y el design system. También dirigió, revisó y validó el trabajo de los agentes.
   - No presentes el código como escrito a mano por el autor ni minimices su rol: el diseño del sistema y las decisiones son suyas, y la implementación fue asistida por IA.
6. **Design system:** un enlace a `erato-design-system/` con una breve descripción de su estética.
7. **Licencia y contacto** (pregunta al autor qué incluir).

## Antes de empezar, pregunta

- El modelo de datos completo (regla 1).
- El framework del backend.
- El método de autenticación.
- El almacenamiento de los audios.
- Si los componentes del design system se envuelven desde React o se reimplementan en Vue.
