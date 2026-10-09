# Erato

[Leer en español](README.es.md)

> Songbook and collaborative workspace for bands and musical ensembles.

Erato (named after the Greek muse of lyric poetry and choral song) is a web application designed for band members to organize, compose, and share their songs in a single place. Instead of dispersing voice memos across messaging apps, lyrics in loose documents, and chord sheets in smartphone photos, each composition in Erato brings all musical elements together in an elegant, unified interface: interactive chord diagrams, precise tablature editing, auto-scrolling synced lyrics, audio demo takes with timestamped feedback, and rehearsal to-do lists.

<p align="center">
  <img src="img/dashboard.png" alt="Erato dashboard in the dark Noche theme: composition list with status filters" width="900">
</p>

---

## 1. What Erato is and the problem it solves

During creative songwriting and band rehearsals, critical song information frequently gets fragmented across disparate channels:
- Ambiguous or handwritten chord notations with missing variations.
- Incomplete tablatures or incompatible text file formats.
- Unsynced lyrics that are cumbersome to read during live sessions.
- Audio recordings and scratch takes shared in group chats with disconnected feedback (*"the bass comes in late at 1:35"*).
- Forgotten rehearsal action items (*"re-string acoustic guitar"*, *"finalize outro groove"*).

Erato centralizes the band's songbook. It provides purpose-built tools for musicians with an understated interface inspired by the midnight ambiance of a jazz club, ensuring that composers, session players, and bandmates always have accurate, accessible, and securely permissioned material on any device.

---

## 2. Core Features

Every composition in Erato is organized into flexible, modular sections:

- **Chord Editor with Real-Time Harmonic Recognition:**
  - Visual editing over interactive diagrams for **guitar** (fretboard with standard tuning, custom base frets, and barre indicators) or **piano** (chromatic keyboard layout).
  - **Automatic chord detection** in real time from active notes, supporting triads, seventh chords, extended voicings (`Cmaj7`, `F#m7b5`, `D9`), slash chords / inversions (`D/F#`), and rootless voicings.
  - Smart instrument switching with automatic octave folding (`octave-folding` into MIDI [48, 71]).

- **Interactive ASCII Tablature Editor:**
  - 6-string tablature grid built for natural keyboard and click-based entry.
  - Bi-directional arrow navigation, measure bar insertion (`|`), multi-digit fret values (e.g., `12`), and standard articulation techniques (`h` hammer-on, `p` pull-off, `b` bend, `/` slide, `~` vibrato, `x` mute).
  - Faithful mono-spaced plaintext export.

- **Lyrics Viewer with Chord-over-Syllable Synchronization:**
  - Intuitive inline markup that places chords precisely above lyrics syllables (e.g., `[Am7]Under the streetlamp…`).
  - Section dividers and headers (`# Chorus`, `# Verse`, `# Bridge`).
  - Distraction-free full-screen mode for rehearsal and live stage use, featuring **speed-adjustable auto-scrolling** and quick exit via `Escape`.

- **Demo Player with Timestamped Commentary:**
  - Dedicated multi-take audio player scoped to each individual composition.
  - Deterministic synthetic audio waveforms for visual scrubbing without heavy backend audio processing.
  - **Timestamp-anchored comments:** contextual band feedback allowing musicians to jump straight to the exact second in the track with one click.
  - Secure direct-to-cloud media upload (*direct-to-Cloudinary*), ensuring audio file bytes never traverse the backend server.

- **Rehearsal Task List (To-Dos):**
  - Integrated to-do panel for songwriting, tracking, and rehearsal tasks: add items, toggle completion status, delete individual tasks, or clear completed items in batch.

- **Granular Sharing and Permission Model:**
  - Access visibility modes:
    - **Public:** Anyone with the link can view the composition without needing an account; only invited collaborators can edit.
    - **Private:** Strictly restricted to invited band members.
  - Role hierarchy: **Owner** (`owner`), **Editor** (`editor`), and **Viewer** (`viewer`), strictly enforced on every backend request.
  - Anti-probing security: uninvited requests to private resources return `404 Not Found` rather than `403 Forbidden`, preventing resource enumeration.
  - Invitation links with cryptographically secure tokens and TTL expiration.

### Product tour

**Create a song and open it**

| Create a song | Composition view |
|---|---|
| ![Create-song form: title, key, tempo, time signature, status, visibility and initial sections](img/crear.png) | ![Composition view with status, visibility, section navigation, lyrics and rehearsal tasks](img/vista%20composicion.png) |

**Chord editor with automatic chord detection**

| Guitar fretboard | Guitar and piano |
|---|---|
| ![Chord editor on a horizontal guitar fretboard that detects the chord name from the notes](img/editor-acorde.gif) | ![Guitar and piano chord cards, with slash chords such as AbMaj7/G detected automatically](img/editor-acorde-2.gif) |

**Lyrics**

| Lyrics viewer | Chords over syllables |
|---|---|
| ![Lyrics viewer with adjustable auto-scroll speed and full-screen mode](img/letra.gif) | ![Assigning chords to lyric syllables from the chord palette](img/letra-acordes.gif) |

**Demo player with timestamped comments**

![Demo player with a waveform and a comment anchored to the current timestamp](img/demo.gif)


---

## 3. Technical Stack & Architecture

Erato is engineered with strict separation of concerns, optimized for lightweight containerized development and cost-free serverless cloud deployment:

| Layer | Technology | Role & Key Characteristics |
| --- | --- | --- |
| **Frontend** | Vue 3 + Vite + TypeScript | Reactive single-page application using Composition API and strict typing. |
| **Design System** | `erato-design-system/` | Custom design system (CSS custom properties, Bodoni Moda, Libre Franklin, and IBM Plex Mono typography). |
| **Backend** | Python + FastAPI | Asynchronous RESTful API, Pydantic v2 schemas, stateless JWT bearer auth, and secure HttpOnly refresh cookies. |
| **Database** | MongoDB | NoSQL persistence via `AsyncMongoClient` (PyMongo) with compound indexes and TTL collections. |
| **Media Storage** | Cloudinary | Client-side signed audio uploads and authenticated short-lived playback URLs. |
| **Containers** | Docker & Docker Compose | Reproducible local orchestration for backend, frontend, and database services. |
| **Deployment** | Vercel Serverless | Single ASGI function re-export (`api/index.py`) and static SPA hosting. |

### Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Client Browser / Mobile Device"]
        SPA["Frontend SPA (Vue 3 + Vite + TS)"]
        State["Memory: Access Token JWT"]
        Cookie["HttpOnly Cookie: Refresh Token"]
    end

    subgraph CDN_Cloud ["Cloudinary Media"]
        Cloudinary["Cloudinary Storage (Audio Takes)"]
    end

    subgraph Backend_App ["Backend (FastAPI ASGI / Vercel Serverless)"]
        API["API Router (/api)"]
        AuthSvc["Auth Service (Argon2id + JWT HS256)"]
        CompSvc["Composition & Permissions Service"]
        DemoSvc["Demo Service (Cloudinary Signer)"]
        SweepCron["Maintenance / Cron Orphan Sweep"]
    end

    subgraph Database ["Database"]
        Mongo[("MongoDB (Local / Atlas M0 Cluster)")]
    end

    SPA -- "1. Request signed upload params" --> API
    API -- "2. Return signature + timestamp" --> SPA
    SPA -- "3. Direct audio upload (FormData)" --> Cloudinary
    SPA -- "4. POST confirmed audio metadata" --> API
    API --> Mongo
    SPA -- "API requests with Bearer JWT" --> API
    API --> AuthSvc
    API --> CompSvc
    API --> DemoSvc
    AuthSvc --> Mongo
    CompSvc --> Mongo
    DemoSvc --> Mongo
    SweepCron -- "Sweep orphaned pending uploads (>24h)" --> Cloudinary
```

---

## 4. Local Development & Deployment

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+.
- Node.js 20+ and Python 3.12+ (optional, for running natively outside containers).

### Environment Configuration

Copy the example environment configuration and supply your local or production credentials:

```bash
cp .env.example .env
```

All 14 configuration variables documented in `.env.example` must be configured:

| Variable | Example Value | Description |
| --- | --- | --- |
| `MONGODB_URI` | `mongodb://root:erato_dev_password@mongo:27017` | Full MongoDB connection string (local Docker URI or MongoDB Atlas SRV URI for production). |
| `MONGODB_DB` | `erato` | Target database name in the MongoDB cluster. |
| `MONGO_INITDB_ROOT_USERNAME` | `root` | Root administrative username for local MongoDB Docker container. |
| `MONGO_INITDB_ROOT_PASSWORD` | `erato_dev_password` | Root administrative password for local MongoDB Docker container. |
| `JWT_SECRET` | 32+ byte random string | Cryptographic secret key used to sign HS256 access tokens. |
| `ACCESS_TOKEN_TTL_MINUTES` | `15` | Expiration window for volatile in-memory access tokens (in minutes). |
| `REFRESH_TOKEN_TTL_DAYS` | `30` | Lifespan of rotating refresh tokens stored in HttpOnly cookies (in days). |
| `INVITE_TOKEN_TTL_DAYS` | `14` | Validity window of collaboration invitation tokens (in days). |
| `CLOUDINARY_CLOUD_NAME` | `your-cloud-name` | Cloudinary account cloud identifier for direct media uploads. |
| `CLOUDINARY_API_KEY` | `123456789012345` | Public Cloudinary API key for upload signature requests. |
| `CLOUDINARY_API_SECRET` | `cloudinary-secret-key` | Private secret key used for server-side HMAC-SHA1 upload verification. |
| `CLOUDINARY_FOLDER_PREFIX` | `erato` | Cloudinary asset folder prefix isolating band media files. |
| `APP_BASE_URL` | `http://localhost:5173` | Public base URL used to format shareable invitation links. |
| `CRON_SECRET` | `secure-cron-secret` | Shared secret token guarding scheduled background maintenance routes (e.g. `/api/cron/orphan-sweep`). |

### Running Locally with Docker Compose

Launch the complete multi-container stack (Vite frontend, FastAPI backend, and MongoDB database):

```bash
docker compose up --build
```

Once initialized:
- **Frontend SPA:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB Database:** `localhost:27017`

### Running the Test Suite

- **Backend (Python / pytest):**
  ```bash
  .venv/bin/pytest tests/
  ```
- **Frontend (Vitest & TypeScript Typecheck):**
  ```bash
  cd frontend
  npm run test:unit
  npm run build
  ```

### Deployment to Vercel

Erato is structured for seamless single-origin deployment on Vercel:
1. `vercel.json` routes `/api/(.*)` to `api/index.py` (Vercel Serverless Python function re-exporting the FastAPI ASGI app).
2. All other routes serve the static SPA compiled into `frontend/dist`.
3. Production environment variables (`MONGODB_URI` pointing to MongoDB Atlas M0, Cloudinary credentials, `JWT_SECRET`, etc.) are configured via the Vercel Project Settings dashboard.
4. Daily maintenance cron sweeps call `/api/cron/orphan-sweep` authenticated only via the `CRON_SECRET` bearer token, which Vercel sends automatically when the variable is set. The `x-vercel-cron` header is not trusted, because any client can send it.
5. After setting the environment variables, create the MongoDB indexes once (unique and TTL indexes): export `MONGODB_URI` / `MONGODB_DB` in your shell (never commit them), together with any placeholder values for `JWT_SECRET`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET` (the app settings require them to load, the script does not use them), and run `python -m scripts.ensure_indexes` against Atlas. For local Docker use `docker compose exec backend python -m scripts.ensure_indexes`. The script is idempotent, so it is safe to re-run. It is intentionally not executed at app startup, because every serverless cold start would repeat it.

---

## 5. My Role in the Project

This project forms part of my professional engineering portfolio and demonstrates my methodology for designing robust, scalable, and resilient software systems using modern agentic AI development workflows:

- **AI Agentic Harness Development:**
  The implementation code was written and verified across an orchestrated multi-agent harness (**Gentle-AI**, **Gemini**, and **Claude**), operating under strict formal architectural specifications, capability constraints, and rigorous Test-Driven Development (strict TDD).

- **System Architecture & Product Ownership:**
  As the system designer and author, I held full responsibility for:
  - Defining the product vision, domain workflows for musicians, and end-to-end feature scope.
  - Designing the complete software architecture (strict layer boundaries, memory-only volatile tokens with HttpOnly rotating refresh cookies, and direct-to-cloud audio pipelines).
  - Modeling the MongoDB data architecture, designing collections, schemas, embedded structures, compound indexes, and the role-based access matrix (`owner`, `editor`, `viewer`).
  - Directing visual design, typography, color palettes, and component architecture in [`erato-design-system/`](./erato-design-system/).
  - Supervising, directing, reviewing, and validating each implementation phase, guaranteeing code consistency, 100% test scenario coverage, and strict enforcement of security and accessibility standards.

The codebase was not hand-typed character-by-character; rather, it was engineered, architected, and validated under my technical leadership. The architecture, system design, data models, and specifications represent my original intellectual work.

---

## 6. Design System

Erato's visual aesthetic is codified in the [`erato-design-system/`](./erato-design-system/) package:

- **Aesthetic:** Inspired by the intimate, sophisticated atmosphere of a midnight jazz club. Dark nocturnal foundations contrast with warm amber and deep wine accents, reminiscent of soft stage lighting.
- **Typography:**
  - *Bodoni Moda:* Titles and chord banners, providing classic mid-century elegance.
  - *Libre Franklin:* High-legibility sans-serif for UI labels, navigation, and controls.
  - *IBM Plex Mono:* Tablatures, chord symbols, and measure numbering, ensuring strict monospace alignment.
- **Dual Themes:** Native CSS variable token support (`data-theme`):
  - **Noche:** Default dark midnight theme.
  - **Matiné:** High-contrast daylight theme.
- **Accessibility:** 4.5:1 minimum text contrast, prominent focus indicators (`focus-ring`), and semantic HTML elements throughout.

---

## 7. License & Contact

- **License:** [GNU AGPL-3.0](./LICENSE). Erato is free and open source; if you run a modified version of it as a network service, the AGPL requires you to make your modified source available to its users as well.
- **Contact:** For inquiries, collaboration, or professional contact, please reach out via GitHub or professional contact channels.
