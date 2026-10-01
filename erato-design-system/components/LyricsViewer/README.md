# LyricsViewer

Visor de letra con acordes encima, desplazamiento automático a velocidad ajustable y pantalla completa.

- Props: `lyrics` (texto plano; acordes entre corchetes antes de la sílaba `[Am7]Bajo el farol`, `# Coro` para rótulos de sección, línea vacía entre estrofas), `title`, `defaultSpeed` (px/s, 24 = 1.0×), `height` (px en modo panel, 360), `showChords`.
- Play inicia el autoscroll; se detiene solo al final. El control de velocidad va de 0.3× a 5×.
- Maximizar ocupa toda la ventana con la letra en `display`; Esc vuelve.
