# Erato

[Read in English](README.md)

> Cancionero y espacio de trabajo colaborativo para bandas musicales.

Erato (nombrado en honor a la musa griega de la lírica coral y la poesía) es una aplicación web diseñada para que los integrantes de una banda organicen y compartan sus composiciones en un solo lugar. En lugar de dispersar notas de voz en aplicaciones de mensajería, letras en documentos sueltos y acordes en papeles fotografiados, cada composición en Erato reúne en una interfaz armónica todos los elementos de un tema musical: acordes interactivos, tablaturas precisas, letras sincronizables, demos con comentarios temporales y una lista de pendientes.

---

## 1. Qué es Erato y qué problema resuelve

En el proceso creativo y de ensayo de un grupo musical, la información sobre una canción suele perderse en múltiples canales:
- Versiones de acordes anotadas de forma ambigua.
- Tablaturas incompletas o en formatos incompatibles.
- Letras con anotaciones manuscritas difíciles de leer en vivo.
- Grabaciones y maquetas enviadas por chat con comentarios descontextualizados («en el minuto 1:35 el bajo entra a destiempo»).
- Tareas de ensayo olvidadas («cambiar cuerdas», «definir final»).

Erato centraliza el cancionero de la banda. Proporciona herramientas diseñadas específicamente para músicos, con una interfaz sobria inspirada en la atmósfera nocturna de un club de jazz, garantizando que tanto quien compone como quien ensaya o acompaña disponga de la información exacta, accesible desde cualquier dispositivo y con permisos bien definidos.

---

## 2. Funcionalidades principales

Cada composición en Erato se organiza en módulos opcionales y flexibles:

- **Editor de acordes con detección armónica:**
  - Edición visual sobre diagramas interactivos de **guitarra** (mástil con afinación estándar y cálculo de cejillas) o de **piano** (teclado con distribución cromática).
  - **Detección automática del nombre del acorde** en tiempo real a partir de las notas seleccionadas, con soporte para tríadas, cuatríadas, acordes extendidos (`Cmaj7`, `F#m7b5`, `D9`) y acordes con bajo alterado / inversión (`D/F#`).
  - Conversión inteligente entre instrumentos con plegado de octavas (`octave-folding`).

- **Editor de tablaturas ASCII interactivo:**
  - Cuadrícula de 6 cuerdas para escritura manual con teclado o pulsadores.
  - Navegación bidireccional mediante teclas de flecha, inserción de compases (`|`), cifras de dos dígitos (ej. `12`) y técnicas de ejecución estándar (`h` hammer-on, `p` pull-off, `b` bend, `/` slide, `~` vibrato, `x` mute).
  - Exportación fidedigna a texto plano monospaciado.

- **Visor de letras con acordes sobre sílabas:**
  - Formato de marcado sencillo que ubica los acordes exactamente encima de la sílaba correspondiente (por ejemplo: `[Am7]Bajo el farol…`).
  - Rótulos de sección (`# Coro`, `# Estrofa`, `# Puente`).
  - Modo a pantalla completa para ensayos o presentaciones en vivo, con **desplazamiento automático (*autoscroll*)** de velocidad graduable por el usuario y salida con tecla `Escape`.

- **Reproductor de maquetas (*demos*) con comentarios anclados:**
  - Lista de tomas de audio exclusivas de cada composición.
  - Visualización sintética de onda sonora generada de forma determinista para navegación visual intuitiva.
  - **Comentarios con marca de tiempo (*timestamps*):** retroalimentación contextualizada que permite saltar directamente al segundo exacto del comentario al hacer clic.
  - Carga directa segura a almacenamiento multimedia en la nube (*direct-to-Cloudinary*), sin sobrecargar el servidor backend.

- **Lista de pendientes (*To-do list*):**
  - Tareas operativas de ensayo o grabación asociadas a cada composición: agregar pendientes, marcar como completadas, eliminar o limpiar las tareas realizadas.

- **Compartir y control de acceso granular:**
  - Modos de visibilidad: **Pública** (cualquiera con el enlace puede consultar la composición sin necesidad de iniciar sesión; solo los usuarios invitados pueden editarla) o **Privada** (restringida exclusivamente a integrantes invitados).
  - Roles de usuario: **Dueño** (`owner`), **Editor** (`editor`) y **Lector** (`viewer`), validados estrictamente en cada petición del backend.
  - Generación y revocación de enlaces de invitación con tokens criptográficos de un solo uso.

*(Nota: En futuras iteraciones se incorporarán capturas de pantalla y demostraciones animadas del flujo completo).*

---

## 3. Stack técnico y arquitectura

Erato está construido desacoplando responsabilidades de manera estricta y optimizado para ejecutarse tanto en contenedores locales como en plataformas serverless en la nube:

| Capa | Tecnología | Rol y características |
| --- | --- | --- |
| **Frontend** | Vue 3 + Vite + TypeScript | Interfaz reactiva con Composition API y tipado estricto. |
| **Diseño** | `erato-design-system/` | Sistema de diseño propio (CSS Tokens, tipografías Bodoni Moda, Libre Franklin e IBM Plex Mono). |
| **Backend** | Python + FastAPI | API RESTful asíncrona, validación con Pydantic v2, autenticación stateless con JWT y cookies HttpOnly seguras. |
| **Base de datos** | MongoDB | Persistencia NoSQL mediante `AsyncMongoClient` (PyMongo). Índices compuestos y optimizados. |
| **Almacenamiento multimedia** | Cloudinary | Firma de uploads directa desde el cliente y URLs de entrega autenticadas para audio. |
| **Contenedores** | Docker & Docker Compose | Orquestación local reproducible de backend, frontend y base de datos. |
| **Despliegue** | Vercel Serverless | Backend expuesto como función ASGI única (`api/index.py`) y frontend como SPA estática. |

### Diagrama de arquitectura

```mermaid
flowchart TD
    subgraph Cliente ["Navegador Web / Dispositivo"]
        SPA["Frontend (Vue 3 + Vite + TS)"]
        State["Memoria: Access Token JWT"]
        Cookie["Cookie HttpOnly: Refresh Token"]
    end

    subgraph CDN_Cloud ["Cloudinary Media"]
        Cloudinary["Cloudinary Storage (Audio Demos)"]
    end

    subgraph Backend_App ["Backend (FastAPI ASGI / Vercel Serverless)"]
        API["Router API (/api)"]
        AuthSvc["Auth Service (Argon2id + JWT HS256)"]
        CompSvc["Composition & Permissions Service"]
        DemoSvc["Demo Service (Cloudinary Signer)"]
        SweepCron["Maintenance / Cron Orphan Sweep"]
    end

    subgraph Database ["Base de Datos"]
        Mongo[("MongoDB (Local / Atlas Cluster)")]
    end

    SPA -- "1. Solicita firma de subida" --> API
    API -- "2. Retorna timestamp + sign" --> SPA
    SPA -- "3. POST audio directo (FormData)" --> Cloudinary
    SPA -- "4. POST metadatos confirmados" --> API
    API --> Mongo
    SPA -- "Peticiones API con Bearer JWT" --> API
    API --> AuthSvc
    API --> CompSvc
    API --> DemoSvc
    AuthSvc --> Mongo
    CompSvc --> Mongo
    DemoSvc --> Mongo
    SweepCron -- "Limpia subidas huérfanas (>24h)" --> Cloudinary
```

---

## 4. Cómo correrlo en local y despliegue

### Requisitos previos
- [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2+.
- Node.js 20+ y Python 3.12+ (opcional, si se desea ejecutar sin contenedores).

### Configuración de variables de entorno

Copia la plantilla de variables de entorno y define los valores necesarios:

```bash
cp .env.example .env
```

Todas las variables documentadas en `.env.example` deben estar presentes:

| Variable | Tipo / Valor ejemplo | Descripción |
| --- | --- | --- |
| `MONGODB_URI` | `mongodb://root:erato_dev_password@mongo:27017` | Cadena de conexión completa a la base de datos MongoDB (local o MongoDB Atlas SRV en producción). |
| `MONGODB_DB` | `erato` | Nombre de la base de datos utilizada en la instancia de MongoDB. |
| `MONGO_INITDB_ROOT_USERNAME` | `root` | Usuario administrativo inicial para el contenedor de desarrollo de MongoDB. |
| `MONGO_INITDB_ROOT_PASSWORD` | `erato_dev_password` | Contraseña administrativa inicial para el contenedor de desarrollo de MongoDB. |
| `JWT_SECRET` | Cadena aleatoria (mín. 32 bytes) | Clave criptográfica para la firma de tokens de acceso JWT (algoritmo HS256). |
| `ACCESS_TOKEN_TTL_MINUTES` | `15` | Tiempo de vida del token de acceso en memoria (en minutos). |
| `REFRESH_TOKEN_TTL_DAYS` | `30` | Tiempo de vida del token de refresco rotativo almacenado en cookie HttpOnly (en días). |
| `INVITE_TOKEN_TTL_DAYS` | `14` | Validez de los tokens de invitación para nuevos colaboradores (en días). |
| `CLOUDINARY_CLOUD_NAME` | `tu-cloud-name` | Identificador de cuenta de Cloudinary para la carga directa de maquetas. |
| `CLOUDINARY_API_KEY` | `123456789012345` | API Key pública para firmar solicitudes a Cloudinary. |
| `CLOUDINARY_API_SECRET` | `secreto-cloudinary` | Clave secreta para la generación de firmas HMAC-SHA1 y validación de respuestas. |
| `CLOUDINARY_FOLDER_PREFIX` | `erato` | Prefijo de carpeta en Cloudinary donde se almacenan y aíslan los archivos de audio. |
| `APP_BASE_URL` | `http://localhost:5173` | URL base de la aplicación frontend, utilizada para construir enlaces de invitación compartibles. |
| `CRON_SECRET` | `cron-secret-seguro` | Token secreto que protege las rutas de mantenimiento programadas (ej. `/api/cron/orphan-sweep`). |

### Ejecución en local con Docker Compose

Para levantar todo el entorno (Frontend en Vite, Backend en FastAPI y Base de datos MongoDB):

```bash
docker compose up --build
```

Una vez levantados los servicios:
- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **API Backend:** [http://localhost:8000](http://localhost:8000)
- **Documentación interactiva de la API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB:** `localhost:27017`

### Ejecución de pruebas

- **Backend (Python / pytest):**
  ```bash
  .venv/bin/pytest tests/
  ```
- **Frontend (Vitest & TypeScript build check):**
  ```bash
  cd frontend
  npm run test:unit
  npm run build
  ```

### Despliegue en Vercel

Erato está preparado para ser desplegado en Vercel con configuración zero-config para funciones ASGI:
1. El archivo `vercel.json` enruta las peticiones `/api/*` hacia `api/index.py` (función serverless Python con FastAPI).
2. Las rutas restantes sirven la aplicación de página única (SPA) generada por Vite en `frontend/dist`.
3. Configurar en el panel de Vercel las variables de entorno de producción (`MONGODB_URI` apuntando a MongoDB Atlas, credenciales de Cloudinary, `JWT_SECRET`, etc.).
4. Las tareas de mantenimiento (como la purga de audios huérfanos) se conectan mediante Vercel Cron llamando a `/api/cron/orphan-sweep` con el encabezado `Authorization: Bearer <CRON_SECRET>`.
5. Tras configurar las variables de entorno, crear una sola vez los índices de MongoDB (únicos y TTL): exportar `MONGODB_URI` / `MONGODB_DB` en tu terminal (nunca se commitean) y ejecutar `python -m scripts.ensure_indexes` contra Atlas. En Docker local usa `docker compose exec backend python -m scripts.ensure_indexes`. El script es idempotente, por lo que se puede volver a ejecutar sin riesgo. No se ejecuta al arrancar la app a propósito, porque cada arranque en frío de la función serverless lo repetiría.

---

## 5. Mi rol en el proyecto

Este proyecto forma parte de mi portafolio profesional y refleja mi enfoque para diseñar sistemas escalables, usables y robustos, aprovechando metodologías modernas de desarrollo acelerado con inteligencia artificial:

- **Desarrollo con harness de agentes de IA:**
  El código de la aplicación fue implementado utilizando un entorno estructurado de agentes de inteligencia artificial (**Gentle-AI**, **Gemini** y **Claude**), trabajando bajo especificaciones técnicas estrictas y desarrollo guiado por pruebas (TDD estricto).

- **Autoría del diseño y arquitectura:**
  Como autor del proyecto, fui el responsable de:
  - Definir la visión del producto, los casos de uso para músicos y el alcance funcional integral.
  - Diseñar la arquitectura de software (separación de capas, API client seguro con tokens volátiles en memoria y cookies de refresco HttpOnly, direct-to-storage para audio sin pase por servidor).
  - Modelar la base de datos en MongoDB, diseñando las colecciones, campos, índices compuestos y la matriz de permisos por roles (`owner`, `editor`, `viewer`).
  - Crear la dirección visual, la paleta y la biblioteca de componentes del sistema de diseño propio (`erato-design-system/`).
  - Dirigir, supervisar, revisar y validar cada ciclo de implementación, asegurando la consistencia del código, la cobertura de pruebas unitarias y el cumplimiento de los principios de seguridad y accesibilidad.

El código no fue escrito carácter por carácter a mano, sino orquestado y validado técnicamente; la arquitectura, las decisiones de ingeniería, el diseño de producto y las especificaciones son autoría intelectual propia.

---

## 6. Design System

El diseño visual de Erato está contenido en el paquete [`erato-design-system/`](./erato-design-system/):

- **Estética:** Inspirada en la intimidad y sofisticación de un club de jazz a medianoche. Combina tonos oscuros de fondo con acentos cálidos y destellos lumínicos que emulan iluminación tenue de escenario.
- **Tipografías:**
  - *Bodoni Moda:* Títulos y marcas de acordes, aportando elegancia clásica.
  - *Libre Franklin:* Textos de interfaz y controles, garantizando legibilidad y claridad.
  - *IBM Plex Mono:* Tablaturas y números de compás, permitiendo alineación estricta de caracteres.
- **Temas:** Soporte nativo para dos temas controlados mediante tokens CSS (`data-theme`):
  - **Noche:** Tema oscuro principal.
  - **Matiné:** Tema claro complementario.
- **Accesibilidad:** Diseñado con contraste de texto superior a 4.5:1, indicadores de foco de teclado visibles (`focus-ring`) y controles interactivos semánticos.

---

## 7. Licencia y contacto

- **Licencia:** [GNU AGPL-3.0](./LICENSE). Erato es software libre y de código abierto; si alguien aloja una versión modificada como servicio en red, la AGPL exige que también publique el código fuente de esa versión a sus usuarios.
- **Contacto:** Para consultas, contacto profesional o información sobre el proyecto, por favor dirigirse al repositorio del autor en GitHub o mediante sus canales profesionales de contacto.
