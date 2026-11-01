# Restricciones y requisitos de calidad

- La visualización debe ser sencilla: si hay muchos acordes, dejarlos en un carrusel, lo mismo con tablaturas y etc. Poder filtrar acordes de guitarra y de piano. Poder hacer scroll automático basado en velocidad en la letra. 
- El flujo debe ser intuitivo: todo en la misma página, no crear secciones raras. Se debe poder ver y saber instantáneamente como interpretar la canción. Esto incluye poder poner el cursor sobre un acorde que está en la letra y ver la forma especifica con la que se toca. 
- Los acordes pueden tener el mismo nombre, pero varias versiones entre sí. En la letra esto debe poder distinguirse.
- Las invitaciones a canciones y bandas deben funcionar apropiadamente, se debe testear en profundidad
- El detector de acordes siempre debe detectar el acorde, no dejarlo como desconocido. Es posible que se deba crear un módulo especifico para esto.
- El mismo punto anterior se aplica para el detector de clave/tonalidad.
- No se debe hacer pública la información de un usuario más allá de su Nombre visible y Nombre de usuario. 

> **Revisión (2026-10-17, aprobada):** el detector de tonalidad entrega un arreglo de tonalidades candidatas y el usuario elige; si la canción no tiene acordes, el arreglo es vacío. El detector de acordes sigue sin dejar acordes como «desconocido».
