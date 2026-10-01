# DemoPlayer

Lista de demos de una composición con reproductor, forma de onda y comentarios anclados a un momento.

- Props: `takes` `[{id, title, date?, note?, duration (s), src?, comments: [{t, author, text}]}]`, `defaultTakeId`, `author` (quién comenta), `onComment(takeId, comment)`.
- Con `src` usa `<audio>`; sin él simula el tiempo (útil para maquetas).
- Clic en la onda para saltar; los marcadores `wine` sobre la onda y la lista de comentarios también saltan. El comentario nuevo queda en el tiempo actual: «Comentar en 01:12…».
- El consumidor guarda los comentarios desde `onComment`.
