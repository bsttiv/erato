# Erato

*Read in English: [README.md](README.md)*

Erato (por la musa griega de la lírica coral y amorosa) es una aplicación web donde una banda guarda sus **composiciones**. Cada composición reúne los acordes, tablaturas, letras, demos grabadas y tareas pendientes de una canción, en una interfaz que se entiende de un vistazo.

## Qué problema resuelve

Una canción suele estar repartida: los acordes en una nota, la letra en otra, una grabación en un chat y la lista de pendientes en otro lugar. Erato lo junta todo en una página por canción, de modo que un músico puede ver cómo se toca, leer la letra, escuchar la demo y saber qué falta, y una banda puede compartir y editar el mismo material.

## Funcionalidades principales

- **Cuentas y espacios de trabajo.** Registro e inicio de sesión, un espacio personal y espacios de banda. Las sesiones usan access y refresh tokens, y un usuario puede tener varias sesiones (dispositivos). Solo el nombre visible y el nombre de usuario son públicos.
- **Composiciones.** Crear, ver, editar y borrar. Cada una tiene un estado (idea, en progreso, lista) y tempo y tonalidad opcionales. Las secciones de acordes, tablaturas, letra, demos y tareas son opcionales.
- **Compartir y visibilidad.** Una composición se comparte por enlace y es privada o pública, combinado con su dueño (personal o banda). Las invitaciones a canción tienen rol editor o lector; todos los miembros de una banda son editores de sus canciones. Todas las reglas de acceso se validan en el servidor en cada petición.
- **Acordes.** Vista de guitarra (trastes vistos desde arriba) o piano. El nombre del acorde se detecta automáticamente a partir de las notas y nunca queda como «desconocido». Un mismo acorde puede tener varias formas, los acordes se pueden ubicar sobre la letra y, al pasar el cursor, se ve la forma exacta.
- **Detección de tonalidad.** El sistema propone las tonalidades candidatas de la canción y el usuario elige una (modo automático), o fija la tonalidad a mano (modo manual).
- **Tablaturas.** Seis cuerdas, edición manual con ingreso cómodo por teclado y técnicas (`h`, `p`, `b`, `/`, `~`, `x`). No hay generación automática de tablaturas.
- **Letras.** Se pueden maximizar y tienen desplazamiento automático con velocidad ajustable.
- **Demos.** Una lista de demos de audio por composición, con comentarios anclados a un timestamp.
- **Revisiones.** Los cambios se guardan explícitamente y se versionan por sección.
- **Tareas.** Una lista de pendientes común: agregar, marcar como hecha y borrar.

La lista completa de rutas del backend está en [backend/API.md](backend/API.md) (en inglés).

### Limitaciones actuales

- **La compresión de demos está en pausa.** El diseño del producto indica que el servidor comprime las demos al subirlas; por ahora se guardan sin comprimir.
- **Aún no existe una herramienta de migración.** `backend/migrate.py` migra los datos anteriores de MongoDB Atlas y reutiliza los audios existentes en Cloudinary, pero todavía no se ha ejecutado con datos reales.
- **Las sesiones usan un mock.** El manejo de sesiones está pensado en torno a [Maestro](https://github.com/bsttiv/maestro), el administrador de sesiones del autor, que aún no está terminado. Mientras tanto, el repositorio incluye una simulación de sus endpoints (`maestro-mock/`).
- Este repositorio no publica ningún despliegue, y este README no afirma que exista uno.

## Stack técnico y arquitectura

| Capa | Tecnología |
| --- | --- |
| Backend | Python + FastAPI |
| Frontend | Vue 3 + TypeScript + TailwindCSS |
| Base de datos | MongoDB (Atlas en producción) |
| Almacenamiento de archivos | Cloudinary |
| Sesiones | Maestro (access + refresh tokens), simulado por ahora |
| Contenedores | Docker / `docker compose` |
| Deploy | Vercel |

```
 Navegador (SPA Vue 3)
        |  HTTPS, /api/*
        v
 Backend FastAPI ----> Maestro (mock por ahora): mint / validate / revoke / refresh
        |         \
        v          v
    MongoDB     Cloudinary (audio de las demos)
```

El backend es deliberadamente pequeño y plano: módulos simples en `backend/app/`, sin capas de repositorios ni de servicios. El frontend sigue diseño atómico (`atoms`, `molecules`, `organisms`, `pages`) con el contrato de la API en `frontend/src/api/`. El detector de acordes y tonalidad está en [backend/app/detection.py](backend/app/detection.py).

## Cómo correrlo en local con Docker

Requisitos: Docker con el plugin Compose. No hace falta un archivo `.env`; cada variable tiene un valor local por defecto.

```bash
docker compose up
```

Esto levanta MongoDB 8.0 (replica set de un solo nodo), el mock de Maestro, el backend y el frontend. Los puertos se publican solo en `127.0.0.1`:

| Servicio | URL |
| --- | --- |
| Frontend (Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 (documentación OpenAPI en `/docs`) |

La configuración de conexión son variables de entorno (por ejemplo `MONGODB_URI` y `CLOUDINARY_URL`, sin la cual las demos informan que no están disponibles); ver [`.env.example`](.env.example) y [`compose.yaml`](compose.yaml). No hay secretos en el repositorio.

Los tests corren en contenedores:

```bash
make test           # backend (pytest) y frontend (vitest)
make test-harness   # verificaciones de infraestructura en el host
```

## Despliegue en Vercel

[`vercel.json`](vercel.json) define dos Vercel Services: el `frontend` (raíz `frontend/`), servido en `/`, y el `backend` FastAPI (raíz `backend/`, entrypoint `app.asgi:app`), montado en `/api`. Una transformación de ruta quita el prefijo `/api` antes de que FastAPI reciba la petición, y cualquier otra ruta cae al `index.html` de la SPA. Las variables de entorno, incluida la conexión a MongoDB Atlas, se configuran en el proyecto de Vercel.

Quedan dos puntos por verificar en un despliegue de vista previa: que el runtime de Python ejecute el *startup* de ASGI (la creación de índices depende de ello) y que las demos se reproduzcan y permitan adelantar con una cuenta real de Cloudinary.

## Mi rol en el proyecto

Esta sección está escrita en primera persona por el autor, sobre cómo se hizo el proyecto.

- **La implementación se hizo con un harness de agentes de IA:** Gentle-AI, Codex y Claude. El código de este repositorio lo escribieron esos agentes; no está escrito a mano por mí y no lo presento así.
- **Yo diseñé el sistema.** Definí el producto, la arquitectura, el modelo de datos, las reglas de permisos y la dirección visual. Revisé y aprobé los tests, y dirigí, revisé y validé el trabajo de los agentes. Los agentes implementaron lo que especifiqué y debían consultar antes de decidir algo que no estuviera cubierto.
- **El algoritmo de detección de acordes y tonalidad es diseño mío.** La idea central: nombrar cada acorde según la tonalidad en que se toca, y hacer que el detector entregue *todas* las tonalidades candidatas para que el usuario elija la que representa su canción, en lugar de imponer una sola. Los agentes propusieron refinamientos que yo aprobé: puntaje sobre las 24 tonalidades, uso de la escala menor armónica, el orden de sugerencia de las candidatas y un nombre de respaldo para acordes sin nombre estándar. Reemplazó una versión anterior que elegía una sola tonalidad mediante cadenas de desempates y dejaba casos sin resolver. La implementación está en [backend/app/detection.py](backend/app/detection.py).

## Diseño

El diseño visual vive en [`erato-design/`](erato-design/) (ver su [README](erato-design/README.md)). La estética es un bar de jazz de noche: fondo marrón-negro, tinta crema, un único acento ámbar y lámparas colgantes que dan una luz cálida.

## Licencia

Erato es de código abierto bajo la GNU AGPL-3.0, y su autor también opera una versión comercial hospedada. Consulta [LICENSE](LICENSE). Para contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md) y el [Contributor License Agreement](CLA.md).
