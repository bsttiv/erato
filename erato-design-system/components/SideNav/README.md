# SideNav

Riel lateral con la marca y la lista numerada de composiciones.

- Props: `brand`, `subtitle`, `heading` (sin `//`, se agrega solo), `items` `[{id, label, meta?}]`, `activeId` (controlado) o `defaultActiveId`, `onSelect(id)`.
- `meta` corto en mono: la tonalidad («Am») o un contador. Numera desde `00`.
- El consumidor da el contenedor con alto completo; el riel mide 248px.
