# Erato

## Descripción general

Erato (basado en el nombre de la musa griega de la lírica coral y amorosa) es una aplicación
web que tiene como objetivo albergar las creaciones musicales de una banda, dígase, composiciones.

En un plano general, Erato debe ser capaz de entregarle a los usuarios una interfaz lo
suficientemente fácil de usar como para poder entender los acordes utilizados, tablaturas,
letras escritas y escuchar demos grabadas.

## Características

Las características que Erato debe poseer son las siguientes:

- Capacidad para guardar, editar y borrar nuevas "composiciones"
- Cada composición posee dentro de sí los siguientes elementos (opcionales todos):
    - Acordes
    - Tablaturas
    - Letras de canciones
    - Audios con demos
    - Lista de tareas por hacer
    (to-do)
- Los acordes deben poder ser visualmente
legibles y editables, es decir, se debe presentar
una vista de "guitarra" o "piano" (elegible) para observar o agregar las notas que se
tocan. 
- El nombre del acorde se detecta automáticamente basado en la notas (como en oolimo)
- Las tablaturas se editan a mano (solo se debe entregar las 6 cuerdas y que el usuario introduzca las tablaturas a mano) pero debe entregarse una manera cómoda para ingresar nuevas notas
- Las letras de las canciones se pueden maximizar y también deben poder ser scrolleadas automáticamente con velocidad personalizada
- Los audios son únicos para cada proyecto y debe ser posible tener una lista de ellos dentro de cada proyecto, pudiendo seleccionar cual reproducir y agregar comentarios en cada uno de ellos en cierto timestamp
- La lista de tareas por hacer debe funcionar como un todo común y corriente
- Un usuario debe poder registrarse e iniciar sesión
- Las composiciones deben poder compartirse mediante un link
- Si la composición es pública, cualquier persona con el link puede ver, pero solo editar si es que son un usuario invitado
- Si la composición es privada, solo los usuarios invitados pueden ver y editar

## Estética visual

- El diseño base se encuentra dentro de erato-design-system
- La estética de la página debe sentirse como estar dentro de un bar de jazz: luces cálidas, fondos oscuros pero con destellos de las mismas luces. Imaginate que estas escuchando a Frank Sinatra.

## Instrucciones

- El modelo de datos me lo tienes que consultar primero
- Cada decisión que quieras tomar en cuanto a modelos de datos tienes que consultarmelo primero.
- Genera un README.md en donde se explique todo el proyecto. Deja en claro que se utilizó un Harness con Gentle-AI, Gemini y Claude, pero que yo me encargué del diseño del sistema. La idea es que este proyecto quede en mi curriculum, así que los reclutadores deben saber el rol que cumplí en este proyecto.

## Stack técnico

- Python para el backend
- VueJS para el frontend
- Vercel para deploy
- MongoDB para la base de datos
- Utilizar Docker para containerizar
- Github para el repositorio