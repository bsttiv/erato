# Erato

*Leer en español: [README.es.md](README.es.md)*

Erato (named after the Greek muse of choral and love poetry) is a web application where a band keeps its **compositions**. Each composition gathers the chords, tablatures, lyrics, recorded demos and pending tasks of one song in an interface that is easy to read at a glance.

## What problem it solves

A song usually lives in scattered places: chords in one note, lyrics in another, a rough recording in a chat, a to-do list somewhere else. Erato puts all of it on one page per song, so a musician can see how to play it, read the lyrics, hear the demo and know what is still missing, and so a band can share and edit the same material.

## Main features

- **Accounts and workspaces.** Registration and login, a personal workspace and band workspaces. Sessions use access and refresh tokens, and one user can have several sessions (devices). Only the display name and username are public.
- **Compositions.** Create, view, edit and delete. Each has a status (idea, in progress, ready) and optional tempo and key. The chords, tablatures, lyrics, demos and tasks sections are all optional.
- **Sharing and visibility.** A composition is shared by link and is private or public, combined with its owner (personal or band). Song invitations carry an editor or reader role; every band member is an editor of the band's songs. All access rules are enforced on the server on every request.
- **Chords.** Guitar view (frets seen from above) or piano. The chord name is detected automatically from the notes and is never "unknown". Several shapes of the same chord can coexist, chords can be placed over the lyrics, and hovering one shows its exact shape.
- **Key detection.** The system proposes the candidate keys for the song and the user picks one (automatic mode), or sets the key by hand (manual mode).
- **Tablatures.** Six strings, manual editing with keyboard-friendly input and techniques (`h`, `p`, `b`, `/`, `~`, `x`). There is no automatic tab generation.
- **Lyrics.** Can be maximized and auto-scroll at an adjustable speed.
- **Demos.** A list of audio demos per composition, with comments anchored to a timestamp.
- **Revisions.** Changes are saved explicitly and versioned per section.
- **Tasks.** A shared checklist: add, mark as done, delete.

The full backend route list is in [backend/API.md](backend/API.md).

### Current limitations

- **Demo compression is paused.** The product design calls for the server to compress demos on upload; for now they are stored uncompressed.
- **There is no migration tool yet.** `backend/migrate.py` migrates the previous MongoDB Atlas data and reuses the existing Cloudinary audio, but it has not been run against real data yet.
- **Sessions use a mock.** Session handling is designed around [Maestro](https://github.com/bsttiv/maestro), the author's session manager, which is not finished. Until it is, the repository ships a mock of its endpoints (`maestro-mock/`).
- No deployment is published from this repository, and this README does not claim one.

## Stack and architecture

| Layer | Technology |
| --- | --- |
| Backend | Python + FastAPI |
| Frontend | Vue 3 + TypeScript + TailwindCSS |
| Database | MongoDB (Atlas in production) |
| File storage | Cloudinary |
| Sessions | Maestro (access + refresh tokens), mocked for now |
| Containers | Docker / `docker compose` |
| Deploy | Vercel |

```
 Browser (Vue 3 SPA)
        |  HTTPS, /api/*
        v
 FastAPI backend ----> Maestro (mock for now): mint / validate / revoke / refresh
        |         \
        v          v
    MongoDB     Cloudinary (demo audio)
```

The backend is deliberately small and flat: plain modules under `backend/app/` with no repository or service layers. The frontend follows atomic design (`atoms`, `molecules`, `organisms`, `pages`) with the API contract in `frontend/src/api/`. The chord and key detector lives in [backend/app/detection.py](backend/app/detection.py).

## Running locally with Docker

Requirements: Docker with the Compose plugin. No `.env` file is needed; every variable has a local default.

```bash
docker compose up
```

This starts MongoDB 8.0 (single-node replica set), the Maestro mock, the backend and the frontend. Ports are bound to `127.0.0.1` only:

| Service | URL |
| --- | --- |
| Frontend (Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 (OpenAPI docs at `/docs`) |

Connection settings are environment variables (for example `MONGODB_URI` and `CLOUDINARY_URL`, without which demos report that they are unavailable); see [`.env.example`](.env.example) and [`compose.yaml`](compose.yaml). No secrets are committed.

Tests run in containers:

```bash
make test           # backend (pytest) and frontend (vitest)
make test-harness   # host-side infrastructure checks
```

## Deployment on Vercel

[`vercel.json`](vercel.json) defines two Vercel Services: the `frontend` (root `frontend/`) served at `/`, and the FastAPI `backend` (root `backend/`, entrypoint `app.asgi:app`) mounted at `/api`. A path transform strips the `/api` prefix before FastAPI sees the request, and any other route falls back to the SPA's `index.html`. Environment variables, including the MongoDB Atlas connection, are set in the Vercel project.

Two things are still to be verified on a preview deployment: that the Python runtime runs the ASGI startup (index creation depends on it) and that demos play and seek correctly with a real Cloudinary account.

## My role in the project

This section is written in the author's voice about how the project was made.

- **The implementation was done with an AI agent harness:** Gentle-AI, Codex and Claude. The code in this repository was written by those agents; it is not hand-written by me, and I do not present it that way.
- **I designed the system.** I defined the product, the architecture, the data model, the permission rules and the visual direction. I reviewed and approved the tests, and I directed, reviewed and validated the agents' work. The agents implemented what I specified and were required to ask before deciding anything not covered.
- **The chord and key detection algorithm is my design.** The central idea: name every chord according to the key it is played in, and have the detector return *all* candidate keys so the user picks the one that represents the song, instead of imposing a single answer. The agents proposed refinements that I approved: scoring over the 24 keys, use of the harmonic minor scale, the ordering of the suggested candidates, and a fallback name for chords with no standard name. It replaced an earlier version that chose one key through chains of tie-breakers, which left cases unresolved. The implementation is in [backend/app/detection.py](backend/app/detection.py).

## Design

The visual design lives in [`erato-design/`](erato-design/) (see its [README](erato-design/README.md)). The aesthetic is a jazz bar at night: a dark brown-black background, cream ink, a single amber accent and hanging lamps that cast warm light.

## License

Erato is open source under the GNU AGPL-3.0, and its author also operates a commercial hosted version. See [LICENSE](LICENSE). To contribute, read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Contributor License Agreement](CLA.md).
