Erato guarda las composiciones de una banda: acordes, tablaturas, letras, demos y lo que falta por hacer. La interfaz debe sentirse como un bar de jazz a medianoche: sala oscura, lámparas cálidas, destellos sobre el bronce. Colores tierra y una sola luz que guía la vista: `amber`.

## Voz y contenido

- Habla de tú, cercano y sin vueltas, como alguien de la banda. «Agrega una tarea para el puente», no «El usuario puede añadir tareas».
- Frases cortas, sin signos de exclamación, sin emoji.
- Mayúscula solo al inicio de la frase: «Nueva composición», «Toma 3 — ensayo».
- Rótulos de sección en mono, minúscula precedida de `//` y mostrados en mayúsculas con el estilo `label`: `// contenido`, `// demos`, `// por hacer`.
- Tags y metadatos en minúscula, mono: «en progreso», «Am · 72 bpm», «3 comentarios».
- Los estados vacíos tienen voz propia y no culpan: «Nada pendiente. Toca otra vez desde el coro.», «Aún no hay demos.».
- Notación musical en ASCII cifrado americano: `C`, `Am7`, `F#m7b5`, `D/F#`. Bemoles como `b` (`Bb`, `Eb`, `Ab`), sostenidos como `#` (`C#`, `F#`). Tiempos siempre `mm:ss` (`01:24`).

## Color

- Dos temas: **Noche** (primero, el de siempre) y **Matiné** (claro, papel viejo). Diseña primero en Noche.
- Superficies en capas: `bg-000` la sala (riel lateral, pantalla completa), `bg-100` la página, `bg-200` paneles y tarjetas, `bg-300` celdas activas y hover.
- `amber` es la lámpara: acción primaria, estado activo, progreso, notas marcadas, foco. Una acción primaria por vista. Texto sobre relleno amber: `on-amber`, nunca blanco.
- `ember` (terracota) para acordes sobre la letra y líneas de compás. `wine` para la nota raíz, los comentarios del timeline y lo destructivo. `moss` para lo terminado, siempre con palabra o ícono además del color.
- Cada tono tiene su `*-soft` para fondos de tags y chips; el texto sobre él es el tono pleno.
- La luz ambiente: el `body` lleva dos gradientes radiales, `lamp` arriba a la izquierda y `lamp-wine` abajo a la derecha, sobre `bg-100`. Nunca uses `lamp` como único fondo de texto.
- `line` es decorativo; bordes de inputs, trastes, cuerdas y controles usan `line-strong` (≥3:1).
- Todo par de texto listado en las notas de los tokens cumple 4.5:1 en ambos temas.

## Tipografía

- Tres familias de Google Fonts: **Bodoni Moda** (`display`) para títulos con voz de cartel de club; **Libre Franklin** (`sans`) para leer; **IBM Plex Mono** (`mono`) para rótulos, acordes, tablaturas y tiempos.
- Un `display-xl` por pantalla, el título de la composición. Puedes poner una palabra en itálica y en `amber` (el destello): «Noche de *otoño*».
- `title-italic` para nombres de demos y subtítulos con carácter.
- Letras de canción en `lyric` (20/34) para dejar sitio al acorde encima; al maximizar pasan a `display`.
- Todo lo musical en mono: acordes (`chord`), celdas de tablatura y tiempos (`tab`).

## Espacio, forma y luz

- Escala de 4px: `space-1` … `space-16`. Paneles con `space-6` de padding, `space-8` entre paneles, `space-12` de margen en la vista principal.
- Radios: `radius-control` (4px) para botones, inputs y control segmentado: casi rectos; `radius-sm` celdas, checkbox y teclas; `radius-md` ítems de menú y tarjetas de opción; `radius-lg` paneles; `radius-pill` solo tags y marcadores.
- Controles a 44px de alto: botones con `space-6` de padding horizontal (34px y `space-4` en `sm`), inputs con `space-4`. El botón de reproducir sigue siendo un círculo.
- Selects: `class="er-input er-select"`. Mismo alto, borde y radio que un input, `space-4` a la izquierda y espacio a la derecha para la flecha, dibujada con `ink-muted`.
- Sin sombras de profundidad sobre el fondo; los paneles se separan con `line`. `shadow-glow` es el destello de la lámpara: botón primario en hover, botón de reproducir, una vez por vista. `shadow-lift` solo para lo que flota (letras maximizadas).
- Foco de teclado: `outline` sólido de 2px en `focus-ring` con 2px de separación, en todo control.
- Movimiento sobrio: transiciones de 200ms en color y brillo; nada rebota. El autoscroll de letras es lineal.

## Iconografía

- Íconos de trazo 1.5px, 16px, puntas redondeadas, dibujados con `currentColor` (`Erato.Icon`, nombres: play, pause, plus, x, check, max, min, left, right, bar, guitar, piano). Para más, usa Lucide con `stroke-width` 1.5 al mismo tamaño.
- Sin logo por ahora: el nombre «Erato» se escribe en Bodoni Moda itálica, con el punto de luz `amber` al lado (ver `SideNav`).

## Componentes

`components/bundle.js` expone `window.Erato` y espera React 18. Carga `tokens.css` y luego `components/bundle.css` (importa las fuentes). Para la app:

- Navegación: `SideNav` con las composiciones numeradas `00`, `01`…
- Controles: `Button`, `Tag`, `Segmented`.
- Música: `ChordEditor` (guitarra o piano, nombre detectado solo), `TabEditor` (6 cuerdas a teclado), `LyricsViewer` (autoscroll y pantalla completa), `DemoPlayer` (demos y comentarios con marca de tiempo).
- Proyecto: `TodoList`.
- Utilidades: `Erato.detectChord(midiNotes)` y `Erato.tabToText(columns)`.
