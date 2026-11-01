# 13 - Diseño visual y componentes del frontend

> **Aviso importante:** el autor cambió el diseño de la landing page y empieza un repositorio nuevo. Todo lo que dependa de la landing anterior (su estructura, sus secciones, sus textos, sus estilos, la copia del design system que trae) **puede quedar reemplazado** por el nuevo diseño. Este archivo conserva las reglas del producto y las decisiones del frontend de la aplicación (pantallas de la app, componentes base, página de perfil), que se tomaron sobre el design system anterior (`erato-design-system/`). Los valores concretos de color, tipografía, radios, espaciado y sombras vienen de `tokens.css`, que **no** se reproduce aquí; si el design system nuevo cambia tokens, prevalece el nuevo, salvo que el autor indique lo contrario. Todo lo marcado «(anterior)» debe revisarse contra el nuevo diseño.

## 1. Reglas de diseño de producto

- **Diseño visual desde el design system.** No se inventan colores, tipografías, radios ni componentes. Si algo no existe en el sistema, se propone antes de crearlo (regla 5 de `AGENTS.md`).
- **Ambiente: un bar de jazz.** Fondos oscuros, luces cálidas y destellos de esas mismas luces. «Imagínate que estás escuchando a Frank Sinatra.»
- **La landing no muestra precios ni medios de pago.** La única llamada a la acción es **«Empieza gratis»**. La maqueta anterior incluía planes; hay que quitarlos. (La landing anterior ya fue reemplazada por el autor.)
- **Accesibilidad:** contraste mínimo **4.5:1** en texto, **foco de teclado visible** y **controles semánticos** (`<button>`, `<input>`, `<label>`).
- **Visualización sencilla e intuitiva:** todo en la misma página; si hay muchos acordes, tablaturas, etc., se dejan en un carrusel; los acordes se filtran por instrumento (guitarra/piano); la letra tiene scroll automático por velocidad; al pasar el cursor sobre un acorde en la letra se ve la forma específica con la que se toca; los acordes con el mismo nombre pero distintas versiones se distinguen en la letra.
- Vista de acordes: **guitarra** (trastes vistos «desde arriba») o **piano**, a elección del usuario, para ver y agregar notas.
- Idioma de la interfaz: español, tuteo (ver textos aprobados en el archivo 07, sección 8.3). Los textos fijos del design system anterior («Navegación», «// composiciones», «Erato») se mantienen tal como están en el bundle; no hay i18n.

## 2. Design system (anterior)

Dos conjuntos de referencia (React/HTML, solo referencia de estilo y comportamiento):

- **Landing (anterior):** página de una sola página (SPA) con 7 secciones que se navegan como slides (menú superior, puntos laterales, flechas del pie, rueda del mouse); botones «Iniciar sesión», «Empieza gratis» y los de los planes apuntaban a `#`. **Reemplazada por el nuevo diseño del autor.**
- **Pantallas de la app (anterior):** maquetas de 6 pantallas: lista de composiciones (`Main`), crear composición (`Nueva`), vista de una composición (`Composicion`), compartir composición (`Compartir`), iniciar sesión (`Login`), registrarse (`Registro`). Datos de ejemplo (banda, canciones, comentarios).
- Contenido de cada paquete: pantallas/landing, `ds/erato/` (tokens y componentes React), `vendor/` (React 18.3.1 y el runtime del formato). Las fuentes (**Bodoni Moda, IBM Plex Mono, Libre Franklin**) se cargan desde Google Fonts y necesitan conexión.
- Temas: `noche` (base) y `matine`, seleccionables con `data-theme`.
- Tokens que se usan en las decisiones: fondos `--bg-000/100/200`; texto `--ink`, `--ink-muted`, `--ink-faint`; líneas `--line`, `--line-strong`; tonos `--amber`, `--ember`, `--wine`, `--moss` con variantes `-soft`; `--on-amber`; luces `--lamp`, `--lamp-wine`; `--focus-ring`; radios `--radius-sm|md|lg|control|pill`; fuentes `--font-sans|mono|display`; espaciado `--space-1, 2, 3, 4, 6, 8, 12, 16`; sombras `--shadow-glow`, `--shadow-lift`.
- La copia canónica de `tokens.css` era la de `erato-core/erato-pantallas/ds/erato/` (la de la landing era byte a byte idéntica). El frontend la importa sin copiarla.

## 3. Reglas de implementación en el frontend

- **Los componentes del design system se reimplementan en Vue, sin wrappers de React** ni imports de los `bundle.js` (decisión del autor, 2026-10-19; INFRA-055 lo verifica). Cada componente se implementa **en el cambio de su funcionalidad** (visor de acordes con acordes, editor de tablaturas con tablaturas, reproductor con demos, etc.); los componentes base (Button, Icon, Tag, Segmented, SideNav) tuvieron un cambio propio.
- **Estilos:** utilidades de Tailwind en cada componente (decisión del autor, 2026-10-20). Cada valor sale de `tokens.css` o, si no existe allí, **literalmente** de la hoja de estilos del design system (`bundle.css`); sin valores inventados. Reglas de procedencia: cuando la hoja usa un token (`var(--space-6)`), se usa la utilidad del tema; cuando usa un literal (`44px`, `.45`), un valor arbitrario con ese número exacto. No se usan las escalas por defecto de Tailwind (los colores, espaciados y sombras por defecto están desactivados: `bg-red-500`, `p-5`, `shadow-md` no generan CSS).
- Mapeo de tema: colores, radios, fuentes, espaciado (pasos 1, 2, 3, 4, 6, 8, 12, 16) y sombras (`shadow-glow`, `shadow-lift`) se mapean a variables del design system; ninguna propiedad personalizada puede definirse en función de sí misma.
- **Estilos globales** (en `frontend/src/style.css`, capa base): `@import` de Google Fonts al inicio del CSS compilado; fondo de `body` con dos luces radiales (`--lamp`, `--lamp-wine`) sobre `--bg-100` y `min-height: 100vh` (para que el fondo no se repita en franjas; aprobado el 2026-10-24, DS-102); `.er-label`; regla universal `:focus-visible` con `outline: 2px solid var(--focus-ring)` y `outline-offset: 2px`. Ningún componente usa utilidades `outline-*` que la anulen.
- **Pruebas de aspecto:** los tests verifican que las clases del elemento, compiladas con el build de estilos, declaran las variables esperadas; no usan `getComputedStyle` (jsdom no aplica el CSS de Tailwind).
- Rutas de la aplicación y router: sección 6.

## 4. Componentes base (decisiones de comportamiento)

| Componente | Capa | Decisiones |
| --- | --- | --- |
| **Icon** | átomo | `svg` de 16 px, `viewBox="0 0 16 16"`, siempre `aria-hidden="true"`, trazo `currentColor` de 1.5 con extremos y uniones redondeados; `pause` con trazo 2.25; `play` relleno. 15 nombres: `play pause plus x check max min left right bar guitar piano` (de la hoja de componentes) más `search`, `share`, `lock` (copiados de las pantallas). Un nombre desconocido no renderiza nada. El color lo pone quien usa el ícono |
| **Button** | átomo | `<button type="button">` que reenvía el resto de atributos; `variant`: `quiet` (por defecto: fondo `--bg-200`, borde `--line-strong`, texto `--ink`), `primary` (fondo y borde `--amber`, texto `--on-amber`, brillo en hover `--shadow-glow`), `ghost`, `danger` (texto `--wine`); `size`: `md` (44 px) o `sm` (34 px); `icon` antes de la etiqueta; deshabilitado con opacidad .45. Con `to` renderiza un `RouterLink` (sin `type`). `to` + `disabled` está prohibido en los tipos; en ejecución **gana `disabled`** (un botón deshabilitado sin `href`, no navega) y hay un aviso de desarrollo |
| **IconButton** | átomo | 36 × 36 px, fondo transparente, texto `--ink-muted`; `aria-label` **obligatorio** (prop requerida y tipo); acepta `to` con la misma prohibición `to` + `disabled` |
| **Tag** | átomo | `span` no interactivo; `tone`: `neutral` (por defecto), `amber`, `ember`, `wine`, `moss`; texto y borde del tono sobre su `-soft`; punto opcional (`aria-hidden`). Contraste ≥ 4.5:1 en `noche` y `matine` |
| **Segmented** | átomo | `role="group"` con `aria-label`; un `<button type="button">` por opción con `aria-pressed`; la elegida usa `--amber-soft` y `--amber`. Solo Tab (sin flechas), como el bundle. Controlado (`v-model`) |
| **SideNav** | organismo | `nav` con `aria-label` = encabezado o «Navegación»; marca con lámpara (`aria-hidden`), nombre («Erato») y subtítulo opcional; encabezado «// » + texto (por defecto «// composiciones»); ítems `{id, label, to, meta?}` como `RouterLink`, numerados con dos dígitos desde `00`. Ítem activo: `aria-current="page"` si la ruta es exactamente la del ítem y `"true"` si la ruta actual empieza por la del ítem seguida de `/` (prefijo por segmento; un ítem con `to="/"` nunca es `"true"`); el estilo de activo cubre ambos valores (fondo `--bg-200`, borde `--line`, borde interior izquierdo `--amber`, número en `--amber`). Ancho 248 px |
| **Card** | átomo | Contenedor `div` sin comportamiento: fondo `--bg-200`, borde `1px solid --line`, radio `--radius-lg`, relleno 24 px; sin hover ni rol |
| **Alert** | molécula | `tone` obligatorio: `error` (`role="alert"`, fondo `--wine-soft`) o `success` (`role="status"`, fondo `--moss-soft`); relleno `14px 16px`, radio `--radius-md`, texto `--ink` 14/22 px, flex con separación 12 px; **sin ícono**; contraste de `--ink` sobre el fondo ≥ 4.5:1 |
| **Field** | molécula | Etiqueta `<label for>` + `<input id>` (sin envolver); `id` único por instancia o el recibido; `label` obligatorio; atributos restantes llegan al `<input>`; `type="password"` incluye un botón «mostrar»/«ocultar» (sin `aria-pressed`, fuera de la etiqueta, `type="button"`, ghost `sm` de 44 px y fuente mono). Con `error`: `aria-invalid="true"`, mensaje con `role="alert"` enlazado con `aria-describedby`, borde y texto `--wine`. El campo no recorta ni transforma el valor. Input: alto 44 px, relleno horizontal `--space-4`, radio `--radius-control`, borde `1px solid --line-strong`, fondo `--bg-100`, texto `--ink`, fuente sans 14 px, marcador `--ink-faint` |

Decisiones de proceso de estos componentes: la unión de nombres de `Icon`, la exclusión `to` + `disabled` y el `aria-label` obligatorio se verifican con `vue-tsc --noEmit` (`make typecheck`) además de los avisos en ejecución; el `aria-label` de `IconButton` se declara con la clave literal `'aria-label'`.

### Componente pendiente

Un componente **snackbar** (aviso breve) aún no está en el design system y debe proponerse antes de implementar el aviso de cambio de tonalidad (archivo 08); las fuentes no dicen si `Alert` podría cubrir ese aviso.

## 5. Pantallas conocidas (anterior)

Las pantallas de la app anteriores son referencia, no especificación: lista de composiciones con filtro (`Segmented`), creación (visibilidad con `Segmented`), vista de composición, compartir (aviso con ícono `lock`), login y registro (campos `er-field`, botón «mostrar/ocultar»). **No existe una pantalla de Perfil en el design system**: el diseño de `/perfil` se derivó de `Main` (barra superior) y `Nueva` (columna central de 760 px) con aprobación del autor (archivo 07, sección 8). Las pantallas de login/registro/lista/composición/compartir no tienen decisiones propias más allá de estas referencias (archivo 15).

## 6. Rutas del frontend

Tabla aprobada el 2026-10-21 (router instalado con historial web; `App` solo renderiza `<RouterView />`):

| Ruta | Página |
| --- | --- |
| `/login` | `LoginPage` |
| `/registro` | `RegistroPage` |
| `/canciones` | `CancionesPage` |
| `/canciones/nueva` | `NuevaCancionPage` |
| `/canciones/:id` | `CancionPage` (también es el enlace compartido, según el diseño del cambio) |
| `/canciones/:id/compartir` | `CompartirPage` |
| `/canciones/:id/historial` | Historial de cambios de la canción, de todas sus secciones (aprobado el 2026-10-31) |
| `/perfil` | `PerfilPage` (la única con contenido real) |
| `/bandas/:id` | Detalle de banda (aprobado el 2026-10-30) |
| `/c/:slug/acordes` | Acordes de la canción compartida, solo lectura (aprobado el 2026-10-30) |
| `/c/:slug/tablatura` | Tablatura de la canción compartida, solo lectura (aprobado el 2026-10-30) |
| `/c/:slug/demos` | Demos de la canción compartida, solo lectura (aprobado el 2026-10-30) |
| `/c/:slug/escenario` | Vista de escenario de la canción compartida, solo lectura (aprobado el 2026-10-30) |

- `/` redirige a `/canciones`. `/bandas` **no se define**. `/canciones/nueva` nunca resuelve a `/canciones/:id` con `id = "nueva"`. Exactamente ocho registros (siete rutas y la redirección de `/`); sin ruta *catch-all* ni de «no encontrado» (aún no hay pantalla diseñada). Cada pantalla nueva que agregue una ruta actualiza el caso que compara la tabla.
- Las demás páginas son hoy marcadores vacíos (`<main></main>`) sin texto.
- Sin guardias de router para autenticación: la página maneja el `401` (archivo 07).
- Las rutas `/c/{slug}` e `/i/{token}` de los enlaces públicos y de invitación no están en esta tabla (contradicción/pendiente en el archivo 15).

Origen: `AGENTS.md` (Diseño visual); `descripcion_proyecto.md`; `archivos/restricciones.md`; `erato-design-system/*/README.md`; `tests_md/design_system.md`; `tests_md/rutas.md`; `tests_md/perfil.md`; `openspec/changes/archive/2026-10-22-design-system-vue/{exploration,proposal,design}.md`; `openspec/changes/archive/2026-10-24-perfil-frontend/{proposal,design}.md`; `openspec/specs/frontend-theme/spec.md`; Engram 309, 365, 408, 425.
