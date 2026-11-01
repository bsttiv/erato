# Arquitectura de la base de datos de Erato

Modelo de entidades y relaciones de la base MongoDB actual (rama `preview`, 2026-10-11).

## Entidades

| Entidad | Tipo | Descripción |
| --- | --- | --- |
| `users` | Colección | Cuentas de usuario |
| `refresh_tokens` | Colección | Sesiones de un usuario |
| `bands` | Colección | Grupos de usuarios |
| `band_members` | Embebida en `bands` | Pertenencia de un usuario a una banda, con rol |
| `invitations` | Colección | Invitaciones para unirse a una banda |
| `compositions` | Colección | Canciones de la banda o de un usuario |
| `composition_members` | Embebida en `compositions` | Acceso explícito de un usuario a una composición, con rol |
| `chords`, `tablature`, `lyrics` | Embebidas en `compositions` | Secciones de contenido opcionales |
| `todos` | Embebida en `compositions` | Tareas de la composición |
| `demos` | Embebida en `compositions` | Audios de la composición (el archivo vive fuera de MongoDB) |
| `composition_comments` | Colección | Comentarios anclados a un instante de un demo |
| `section_revisions` | Colección | Versiones guardadas de una sección de contenido |

## Diagrama

```mermaid
erDiagram
    users ||--o{ refresh_tokens : "tiene"
    users ||--o{ bands : "es propietario"
    bands ||--|{ band_members : "contiene"
    users ||--o{ band_members : "pertenece"
    bands ||--o{ invitations : "recibe"
    users ||--o{ invitations : "crea"
    users ||--o{ compositions : "es propietario"
    bands |o--o{ compositions : "agrupa"
    compositions ||--o{ composition_members : "contiene"
    users ||--o{ composition_members : "accede"
    compositions ||--o| chords : "contiene"
    compositions ||--o| tablature : "contiene"
    compositions ||--o| lyrics : "contiene"
    compositions ||--o{ todos : "contiene"
    compositions ||--o{ demos : "contiene"
    users ||--o{ demos : "sube"
    demos ||--o{ composition_comments : "recibe"
    users ||--o{ composition_comments : "escribe"
    compositions ||--o{ section_revisions : "versiona"
    users ||--o{ section_revisions : "edita"

    users {
        ObjectId _id
        string email
        string password_hash
        string display_name
        int token_version
        datetime created_at
    }
    refresh_tokens {
        ObjectId _id
        ObjectId user_id
        string token_hash
        string family_id
        bool revoked
        datetime expires_at
        datetime created_at
    }
    bands {
        ObjectId _id
        string name
        ObjectId owner_id
        object pending_transfer
        datetime created_at
        datetime updated_at
    }
    band_members {
        ObjectId user_id
        string role "owner | member"
    }
    invitations {
        ObjectId _id
        object target "type=band, id"
        string token_hash
        ObjectId created_by
        datetime expires_at
        datetime created_at
    }
    compositions {
        ObjectId _id
        ObjectId owner_id
        ObjectId band_id "opcional"
        bool band_editable
        string title
        string visibility "private | public"
        string share_slug "solo si es publica"
        string key
        int bpm
        string time_signature
        string_array style_tags
        string status "idea | in_progress | ready"
        object sections_enabled
        object section_revs
        datetime created_at
        datetime updated_at
    }
    composition_members {
        ObjectId user_id
        string role "editor | viewer"
    }
    chords {
        string instrument
        array entries
    }
    tablature {
        int strings
        string content
        array tabs
    }
    lyrics {
        string content
    }
    todos {
        string id
        string text
        bool done
    }
    demos {
        string demo_id
        string cloudinary_public_id
        string title
        float duration_s
        ObjectId uploaded_by
        datetime uploaded_at
    }
    composition_comments {
        ObjectId _id
        ObjectId composition_id
        string demo_id
        ObjectId author_id
        float timestamp_s
        string text
        datetime created_at
    }
    section_revisions {
        ObjectId _id
        ObjectId composition_id
        string section "lyrics | chords | tablature"
        int rev
        any content
        ObjectId author_id
        datetime created_at
    }
```

## Relaciones

| Origen | Destino | Cardinalidad | Cómo se representa |
| --- | --- | --- | --- |
| `users` | `refresh_tokens` | 1 a N | `refresh_tokens.user_id` |
| `users` | `bands` | 1 a N (propietario) | `bands.owner_id` |
| `users` | `bands` | N a N (miembros) | `bands.members[].user_id` |
| `bands` | `invitations` | 1 a N | `invitations.target.id` |
| `users` | `invitations` | 1 a N (creador) | `invitations.created_by` |
| `users` | `compositions` | 1 a N (propietario) | `compositions.owner_id` |
| `users` | `compositions` | N a N (acceso explícito) | `compositions.members[].user_id` |
| `bands` | `compositions` | 0..1 a N | `compositions.band_id` |
| `compositions` | secciones, `todos`, `demos` | 1 a N, embebidas | Subdocumentos dentro de `compositions` |
| `compositions` | `composition_comments` | 1 a N | `composition_comments.composition_id` |
| `demos` | `composition_comments` | 1 a N | `composition_comments.demo_id` (identificador de texto del demo embebido) |
| `compositions` | `section_revisions` | 1 a N | `section_revisions.composition_id` + `section` |
| `users` | `composition_comments`, `section_revisions`, `demos` | 1 a N (autor) | `author_id` / `uploaded_by` |

Las referencias son `ObjectId` guardados en el documento; MongoDB no impone integridad referencial entre colecciones.
