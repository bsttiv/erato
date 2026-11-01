# 01 - Producto: qué es Erato, funcionalidades y alcance

## 1. Qué es

**Erato** (por la musa griega de la lírica coral y amorosa) es una aplicación web donde una banda guarda sus **composiciones**. Cada composición reúne acordes, tablaturas, letras, demos grabadas y tareas pendientes de una canción, en una interfaz **fácil de entender**: el usuario debe poder interpretar los acordes, leer las tablaturas y letras y escuchar las demos sin fricción.

El autor también opera una versión comercial hospedada de Erato; el código es de código abierto bajo GNU AGPL-3.0 (archivo 02, sección 6). El proyecto es además parte del portafolio profesional del autor (archivo 02, sección 5).

## 2. Funcionalidades

### Cuentas y espacios de trabajo

- Registro e inicio de sesión (el registro inicia sesión; el login es solo por email).
- Dos espacios de trabajo: **personal** y **banda**.
  - Personal: solo el dueño ve sus composiciones, salvo que invite a alguien.
  - Banda: un usuario crea una banda e invita personas; todos los miembros pueden revisar y editar las composiciones de la banda.
- Invitaciones a **canción** con rol **editor** (puede editar cualquier sección) o **lector** (solo ve). Invitaciones a **banda** sin rol: **todos los miembros de una banda son editores** de sus canciones.
- Sesiones con access y refresh tokens; un usuario puede tener varias sesiones (dispositivos).
- **Solo el nombre visible y el nombre de usuario son públicos**; ningún otro dato del usuario se expone.
- Página de perfil: editar nombre de usuario y nombre visible, ver y cerrar sesiones, cambiar contraseña. Se puede cambiar el email y la contraseña (siempre con la contraseña actual); cambiar la contraseña cierra las demás sesiones.

### Composiciones

- Crear, ver, editar y borrar ("guardar, editar y borrar nuevas composiciones").
- Cada composición tiene: nombre, estado (**idea**, **en progreso** o **lista**), fechas de creación y actualización, tempo (opcional), tonalidad (opcional), modo de tonalidad, privacidad, slug compartido, métrica (opcional), tipo e ID de dueño.
- Secciones **opcionales**: acordes, tablaturas, letra, demos y tareas.
- Se puede **mover** una canción personal a una banda (solo el dueño y solo a una banda de la que es miembro).

### Compartir y visibilidad

- Una composición se comparte mediante un **enlace**. Visibilidad **privada** o **pública**, combinada con el dueño de la canción:
  - **Personal privada:** la ven el dueño y los usuarios invitados.
  - **De banda privada:** la ven (y editan) todos los miembros de la banda y los usuarios invitados.
  - **Pública** (personal o de banda): cualquiera con el enlace puede verla.
- En todos los niveles, **editar requiere** una invitación con rol editor (o ser dueño / miembro de la banda). Reglas completas: archivo 06.

### Acordes

- Vista de **guitarra** (trastes vistos desde arriba) o **piano**, a elección del usuario, para ver y agregar notas.
- El **nombre del acorde se detecta automáticamente** a partir de las notas, nunca queda como «desconocido», y se nombra según la tonalidad de la canción.
- La **tonalidad**: el sistema propone un arreglo de tonalidades candidatas a partir de los acordes y el usuario elige (**modo automático**), o la fija a mano (**modo manual**). Sin acordes, no hay candidatas.
- Un mismo acorde puede tener **varias versiones (formas)**; en la letra se distinguen y, al pasar el cursor, se ve la forma exacta.
- Los acordes se pueden ubicar sobre la letra; se filtran por instrumento y se muestran en carrusel si son muchos.
- El algoritmo es diseño del autor: archivo 08.

### Tablaturas

- Seis cuerdas, edición manual, **sin generación automática**.
- Ingresar notas debe ser cómodo (teclado, flechas, técnicas como `h`, `p`, `b`, `/`, `~`, `x`). Gramática y teclado: archivo 09.

### Letras

- Se pueden **maximizar**.
- **Desplazamiento automático** con velocidad ajustable.

### Demos (audio)

- Cada composición tiene su propia lista de demos; un audio pertenece a una sola composición.
- El usuario elige qué demo reproducir.
- Comentarios anclados a un **timestamp** del audio.
- El servidor **comprime** las demos al subirlas (hoy en pausa); los archivos viven en Cloudinary. Archivo 10.

### Revisiones

- Los cambios se **guardan explícitamente** y se **versionan por sección** (letra, acordes, tablaturas, tareas, metadatos). Las demos no se versionan. Archivo 09.

### Tareas

- Lista de pendientes común: agregar, marcar como hecha y borrar.

## 3. Procesos automáticos del servidor (lista del autor)

- Manejo de sesión de usuario con access y refresh tokens.
- Manejo de invitaciones: un usuario invitado como editor puede editar una canción; uno que es lector no puede. (Revisión del 2026-10-17: los roles editor/lector aplican a invitaciones a **canción**; en una banda todos son editores.)
- Manejo de privacidad de las canciones.
- Identificar acordes automáticamente.
- Identificar la tonalidad automáticamente.
- Manejar revisiones de cambios (separado por cada sección).
- Manejar el tamaño de las demos (comprimirlas).

## 4. Requisitos de calidad (restricciones del autor)

- **Visualización sencilla:** si hay muchos acordes, dejarlos en un **carrusel**; lo mismo con tablaturas y similares. Poder filtrar acordes de guitarra y de piano. Poder hacer scroll automático en la letra por velocidad.
- **Flujo intuitivo:** todo en la misma página, sin «secciones raras». Se debe poder ver y saber instantáneamente cómo interpretar la canción, incluido poder poner el cursor sobre un acorde que está en la letra y ver la forma específica con la que se toca.
- Los acordes pueden tener el mismo nombre pero varias versiones; en la letra esto debe distinguirse.
- Las **invitaciones** a canciones y bandas deben funcionar apropiadamente y **probarse en profundidad**.
- El **detector de acordes** siempre debe detectar el acorde, sin dejarlo como «desconocido»; es posible que requiera un módulo específico. Lo mismo para el detector de tonalidad (revisión del 2026-10-17: entrega un arreglo de candidatas y el usuario elige; sin acordes, el arreglo es vacío; el detector de acordes sigue sin dejar acordes como «desconocido»).
- No se hace pública la información de un usuario más allá de su **nombre visible** y su **nombre de usuario**.
- Accesibilidad y diseño: archivo 13.

## 5. Qué queda fuera de alcance (según las fuentes)

- **Precios y medios de pago:** la landing no los muestra ni hace referencia a ellos; la única llamada a la acción es «Empieza gratis».
- **Pruebas E2E:** no por ahora (decisión del autor).
- **Verificación de email** al cambiarlo: no existe (el email se cambia sin verificación).
- **Borrado de banda:** fuera de alcance de las pruebas (no figura en las entradas manuales). **Borrado de cuenta**, foto de perfil, bandas dentro de `/perfil`, cambio de email desde la página `/perfil` y un botón «cerrar todas las demás sesiones»: fuera del alcance de la página de perfil definida por el autor.
- **Generación automática de tablaturas:** no existe; la edición es manual.
- **Ruta `/bandas`:** no se define (tabla de rutas del frontend).
- **Integración con el Maestro real:** por ahora solo el mock.
- **Compresión de demos en el servidor:** en pausa (2026-10-23).
- **Adaptador HTTP del frontend para el perfil, y login/registro/lista/composición/compartir como pantallas funcionales:** aún no definidos (archivo 15).

Origen: `descripcion_proyecto.md`; `AGENTS.md`; `archivos/entradas_manuales.md`; `archivos/autonomo_automatico.md`; `archivos/restricciones.md`; `archivos/conceptos_datos.md`; `tests_md/perfil.md` (alcance); `tests_md/invitaciones.md` (INV-075); `CONTRIBUTING.md`.
