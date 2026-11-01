# 03 - Arquitectura, stack, despliegue y entorno

La arquitectura la define el autor (`archivos/arquitectura.md`). Ningún agente introduce capas, patrones ni estructura de carpetas que la contradigan; si algo no está cubierto, se pregunta.

## 1. Actores del sistema

Existen **cinco actores principales**:

1. **Frontend** (Vue 3 con TailwindCSS).
2. **Backend** (FastAPI, Python).
3. **Base de datos** (MongoDB; Atlas en producción).
4. **Almacenamiento** (Cloudinary).
5. **Administrador de sesión**: el proyecto **Maestro** del autor (`github.com/bsttiv/maestro`). Aún debe completarse y probarse; mientras tanto se usa una simulación (mock) de sus endpoints y funcionamiento. Contrato: archivo 07.

## 2. Stack técnico

| Capa | Tecnología |
| --- | --- |
| Backend | Python + FastAPI |
| Frontend | Vue 3 + TailwindCSS |
| Base de datos | MongoDB (Atlas en producción) |
| Almacenamiento de archivos | Cloudinary |
| Sesiones | Maestro (access + refresh tokens), simulado con un mock mientras no esté listo |
| Contenedores | Docker (`docker compose` para el entorno local) |
| Deploy | Vercel |
| Repositorio | GitHub |

- **Backend simple:** sin abstracciones especulativas, sin servicios extra ni infraestructura que no se haya pedido.
- **TailwindCSS con criterio:** los tokens del design system (`tokens.css`) se mapean al tema de Tailwind; los estilos repetidos se extraen como componentes Vue o capas `@layer components`, no se copian clase por clase. (En la práctica, para los componentes base, el autor decidió el 2026-10-20 usar utilidades de Tailwind en cada componente; ver archivo 13.)
- Versiones fijadas durante el andamiaje (2026-10-18/19, aprobadas): Python 3.12 con `uv`; Node (LTS) con `npm`; MongoDB 8.0; PyMongo (sync) como driver; Vue 3.5, Tailwind v4, Vite, Vitest; `vue-router`; `typescript` fijado en 6.0.3 (TypeScript 7 rompe `vue-tsc` 3.3.13).

## 3. Estructura y decisiones de código

- **Frontend:** diseño atómico. `frontend/src/components/atoms/` (Icon, Button, IconButton, Tag, Segmented, Card), `molecules/` (Field, Alert), `organisms/` (SideNav) y `pages/` (una página por ruta). Contrato de API del frontend en `frontend/src/api/`. Los componentes se reimplementan en Vue (sin wrappers de React).
- **Backend (decisión del autor, 2026-10-18):** mínimo y plano; `backend/app/main.py` con una fábrica `create_app()` y un módulo de configuración. Estructura real definida cuando llega la primera funcionalidad. El diseño de `perfil-backend` (2026-10-24, propuesto por el agente) usa módulos planos bajo `backend/app` (errores, base de datos, reloj inyectable, cliente de Maestro, seguridad, límite de intentos, dependencia de autenticación, esquemas, dos routers) y **sin** repositorios, servicios ni clases de dominio; el autor aceptó seis valores por defecto de ese diseño (archivo 07, sección 9) pero no consta una aprobación explícita del resto del diseño. Los endpoints son funciones `def` (sync) con `pymongo` y `httpx` síncronos.
- **Tests:** viven en `backend/tests/` (uno por cada archivo de `tests_md/`) y en `frontend/src/**/*.spec.ts`, junto al código que prueban (revisión del 2026-10-18 de `arquitectura.md`). Detalle: archivo 14.
- **Reloj inyectable:** `create_app` acepta un reloj y un timeout de Maestro, para probar el paso del tiempo sin dormir **[diseño]**.

## 4. Entorno local (Docker)

`docker compose up` debe bastar para levantar el proyecto en local (también desde cero, sin crear un `.env`). Servicios:

| Servicio | Descripción |
| --- | --- |
| `mongo` | MongoDB 8.0 como **replica set de un solo nodo** (`rs0`), iniciado automáticamente por el healthcheck; necesario para las transacciones de varias colecciones |
| `maestro-mock` | Mock de Maestro (FastAPI) con los endpoints de control apagados |
| `maestro-mock-control` | Perfil `test`; el mismo mock con control encendido (`MAESTRO_MOCK_CONTROL=1`) |
| `backend` | FastAPI con `uvicorn --factory app.main:create_app --reload`; imagen con `ffmpeg` y el codificador `libopus` |
| `frontend` | Vite en el puerto 5173 con montaje del código fuente (recarga en caliente) |
| `backend-test`, `frontend-test` | Perfil `test`, para `make test` |

Puertos publicados en el host **solo en `127.0.0.1`** (para herramientas de desarrollo): MongoDB 27017, backend 8000, frontend 5173. Los servicios de test no publican puertos, para no chocar con un entorno de desarrollo en ejecución.

Comandos: `make test` (pytest y vitest en contenedores, proyecto fijo `erato-test`, siempre derriba el entorno y sus volúmenes), `make test-harness` (verificaciones en el host de los casos INFRA-001 a INFRA-004; obligatorio en el cambio de infraestructura, al cerrar y cuando cambie el Makefile o la configuración de pruebas), `make typecheck` (`vue-tsc --noEmit`, separado de `make test`).

## 5. Variables de entorno

Las credenciales y cadenas de conexión van en variables de entorno documentadas en `.env.example`; **sin secretos en el repositorio**. Regla de paridad (INFRA-032): el conjunto de variables que lee el backend es **igual** al conjunto de claves de `.env.example`; cada valor es vacío, una URL de servicio local o un valor de reemplazo local; los valores numéricos no caben en `.env.example`, por eso los límites numéricos (timeout de Maestro, umbral de intentos) son constantes de código.

| Variable | Uso |
| --- | --- |
| `MONGODB_URI` | Conexión a MongoDB (local: `mongodb://mongo:27017/?replicaSet=rs0`) |
| `MONGODB_DB` | Nombre de la base de desarrollo; la base de tests es otra |
| `CLOUDINARY_URL` | Credenciales de Cloudinary. Opcional: sin ella la aplicación levanta y las demos responden `503 storage_unavailable` |
| `MAESTRO_URL` | URL de Maestro (mock en local y tests) |
| Vigencia de enlaces de invitación | Variable de entorno (nombre no fijado en las fuentes); por defecto 7 días; inválida ⇒ el servidor no arranca |

- Si falta una variable obligatoria, la app **no arranca** y el error nombra la variable (en mayúsculas).
- `MAESTRO_MOCK_CONTROL` y `TEST_MAESTRO_PLAIN_URL` viven solo en el compose (no en `.env.example`).
- Las variables en producción se configuran en el proyecto de Vercel, incluida la conexión a MongoDB Atlas.

## 6. Despliegue en Vercel (Vercel Services)

Decisión del autor (2026-10-23): el despliegue usa **Vercel Services** definido en `vercel.json`:

- Servicio `frontend`: raíz `frontend/`.
- Servicio `backend`: raíz `backend/`, entrypoint `app.asgi:app` (módulo `backend/app/asgi.py`, instancia a nivel de módulo que Vercel necesita porque `main.py` solo expone la fábrica).
- El frontend se sirve en `/` y el backend FastAPI en `/api`. Una transformación de ruta (`request.path`) quita el prefijo `/api` antes de llegar a FastAPI: **las rutas de FastAPI se declaran sin el prefijo** y no se usa `root_path`.
- Reescrituras: `/api/(.*)` → backend; `/assets/(.*)` y las rutas con punto (`/(.*\..*)`) → frontend; cualquier otra ruta → frontend con `path: /index.html` (**SPA fallback**, necesario porque el router usa historial web y las rutas como `/canciones/:id` son enlaces directos).
- Contenido textual de `vercel.json`:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "services": {
    "frontend": { "root": "frontend/" },
    "backend": {
      "root": "backend/",
      "entrypoint": "app.asgi:app",
      "routes": [
        { "src": "/api/(.*)", "transforms": [ { "type": "request.path", "op": "set", "args": "/$1" } ] }
      ]
    }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": { "service": "backend" } },
    { "source": "/assets/(.*)", "destination": { "service": "frontend" } },
    { "source": "/(.*\\..*)", "destination": { "service": "frontend" } },
    { "source": "/(.*)", "destination": { "service": "frontend", "path": "/index.html" } }
  ]
}
```

- **Compresión de demos en el servidor: en pausa** (2026-10-23; archivo 10).
- Pendiente de verificar en un despliegue de vista previa: que Vercel sobrescriba `X-Forwarded-For` y que el runtime de Python ejecute el *startup* del ciclo de vida ASGI (la creación de índices depende de ello; si no, habría que crearlos de forma perezosa en la primera petición).
- Cabe señalar el límite de **4.5 MB por petición y por respuesta** de las Vercel Functions, que condiciona el diseño de las demos.

## 7. Repositorio y entrega

GitHub. Convenciones de ramas, commits y PR: archivo 02. Presupuesto de revisión de ~400 líneas por PR (planificación; no es criterio de aceptación).

Origen: `archivos/arquitectura.md`; `AGENTS.md`; `vercel.json`; `compose.yaml`, `compose.override.yaml`, `Makefile`; `openspec/changes/archive/2026-10-20-project-scaffolding/design.md`; `openspec/changes/perfil-backend/design.md`; Engram 400, 289.
