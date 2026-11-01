# Erato · Frontend (diseño)

Diseño de la landing y de las pantallas de Erato en **Vue 3 + Vite + TailwindCSS 3**.
Estética: un bar de jazz de noche (fondo marrón-negro, tinta crema, un único acento ámbar y lámparas colgantes).

## Cómo correrlo

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # genera dist/ (listo para Vercel; vercel.json redirige todo a index.html)
```

## Logo y favicon

La marca es una lira (el atributo de la musa Erato) dentro de un círculo ámbar.
- `src/components/ui/LogoMark.vue`: la marca en SVG, se escala con el tamaño del texto.
- `src/components/ui/Wordmark.vue`: marca + "Erato", usada en la navegación, el pie y la app.
- `public/favicon.svg`, `public/favicon-32.png`, `public/apple-touch-icon.png` (180 px) y
  `public/icon-512.png`, enlazados desde `index.html`.

## Rutas

| Ruta | Pantalla |
| --- | --- |
| `/` | Landing |
| `/login` · `/registro` | Inicio de sesión · Registro |
| `/composiciones` | Lista de composiciones (espacio personal / banda) |
| `/composiciones/nueva` | Nueva composición |
| `/bandas/nueva` | Crear banda e invitar integrantes |
| `/c/noche-de-otono` | Vista de composición (letra, acordes, tareas, última demo, historial) |
| `/c/noche-de-otono/acordes` | Editor de acordes (guitarra o piano, nombre detectado automáticamente) |
| `/c/noche-de-otono/tablatura` | Editor de tablatura |
| `/c/noche-de-otono/demos` | Demos con comentarios por segundo |
| `/c/noche-de-otono/escenario` | Letra maximizada con desplazamiento automático |
| `/c/noche-de-otono/compartir` | Compartir (pública / privada, invitar) |
| `/perfil` | Editar perfil |

## Estructura

```
tailwind.theme.js        tokens: colores, tipografías, luz de lámpara, animación
src/assets/main.css      estilos base y componentes extraídos con @apply
                         (.btn-*, .field-*, .chip, .tab, .card, .segmented, .option-card,
                          .lyric-*, .fret-cell, .nut-cell…)
src/lib/chords.js        detección del nombre del acorde a partir de las notas
src/data/sample.js       contenido de ejemplo (reemplazar por la API)
src/components/
  ui/                    Wordmark, StageLamp, BackBar
  landing/               LandingNav (menú móvil), FeatureSection, CompositionPreview, SiteFooter
  app/                   AppShell (barra lateral plegable), CompositionHeader, AuthLayout,
                         BandCard, HistoryList, ShareLinkBar
  music/                 Fretboard, PianoKeys, LyricSheet, Waveform, DemoPlayer, TodoList
src/views/               una vista por ruta
```

Las secciones de la landing reutilizan los mismos componentes de la app
(Fretboard, LyricSheet, DemoPlayer, BandCard, HistoryList, ShareLinkBar).

## Móvil

Todas las vistas se revisaron a 390 px y 1440 px de ancho: sin desplazamiento horizontal,
barra lateral y navegación plegadas en un botón "Menú", objetivos táctiles de 44 px o más.
Las líneas de acordes y la tablatura se desplazan horizontalmente dentro de su caja en vez
de desalinearse.

## Pendiente antes de producción

- Conectar los datos de `src/data/sample.js` con el backend (FastAPI).
- Reemplazar el enlace de GitHub del pie de página por el del repositorio.
- Los formularios no envían nada todavía (`@submit.prevent`).
