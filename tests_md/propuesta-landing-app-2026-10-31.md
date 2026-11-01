# Additional test proposals — landing/app alignment, 2026-10-31

Approved by the author on 2026-10-31. Implemented in `backend/tests/test_songs.py` and the frontend specs of the landing, footer, navigation, dashboard, legal page, router and history.

## Composition preview and chord hints

| ID | Setup | Expected |
| --- | --- | --- |
| LAPP-001 | Render the landing hero | The real SongStatus and LyricSheet render the composition title, status, metadata and a short lyric preview, with tabs Letra, Acordes, Tablatura and Demos |
| LAPP-001B | Choose each hero tab | Shows that content in a panel of fixed height, so the hero keeps its size; Acordes shows chord figures, Tablatura the riff and Demos the takes |
| LAPP-002 | Hover or focus a chord name in the hero lyrics, in Escritura, in Lectura or in the collaboration history | The real ChordHint shows the exact guitar shape; leaving or blurring hides it. Chord figures in the hero Acordes tab have no hint |
| LAPP-003 | Change the writing mock's frets | The detected name, notes and hint shape update together; fewer than two pitch classes show the existing prompt without a hint trigger |
| LAPP-004 | Focus a chord inside the scrolling lyric preview | Its hint is attached to the viewport outside the transformed/overflow container, remains visible and keyboard focus is indicated |
| LAPP-005 | Interact with the landing after the preview change | Both existing lamp refs, radial glows and flexible physics remain active; no prices or payment methods appear; the signup CTA remains `Empieza gratis` |
| LAPP-006 | Select the first audio demo | Chord alternatives use focusable/hoverable real hints while the demo's existing timestamp interactions remain available |

## Links and legal page

| ID | Setup | Expected |
| --- | --- | --- |
| LAPP-010 | Inspect landing/footer repository links and author credit | Repository links target `https://github.com/bsttiv/erato`; existing Bastián Valencia credit targets `https://bsttiv.github.io` |
| LAPP-011 | Open `/legal` without a session, then follow both footer legal links | One public Spanish page loads; anchors reach the terms and privacy sections without requiring authentication |
| LAPP-012 | Inspect the legal page | Accounts, sessions, content, Cloudinary, MongoDB, Vercel and AGPL-3.0 are described; the responsible person and contact email set by the author appear; no placeholder, jurisdiction or address remains |
| LAPP-013 | Visit an existing protected route without a session | The previous sign-in redirect remains unchanged after adding `/legal` to the public allowlist |

## Profile initial

| ID | Setup | Expected |
| --- | --- | --- |
| LAPP-020 | Signed-in landing and dashboard with a display name | Both use the shared UserInitial atom, showing one uppercase initial in a circle |
| LAPP-021 | Empty or whitespace-only display name with a username | Both initials fall back to the username's first character |
| LAPP-022 | Navigate to account links by keyboard | The existing accessible account name, visible focus and `/canciones` or `/perfil` destination remain intact |

## History

The author chose to add `summary` to `revisions` on 2026-10-31.

| ID | Action | Expected |
| --- | --- | --- |
| HIS-001 | Save a change in lyrics under `#Coro` | The revision stores `editó la letra de Coro` |
| HIS-002 | Move only a chord in the lyrics | The revision stores `cambió los acordes de la letra` plus the section |
| HIS-003 | Add, remove and change a chord in one save | The revision names each change |
| HIS-004 | Add, remove and rename a tablature | Each revision names the tablature; an untitled one uses the name the server gives it, such as `Tablatura 1` |
| HIS-005 | Complete and reopen a task | The revisions store `completó la tarea` and `reabrió la tarea` with its title |
| HIS-006 | Change title, status and tempo in one save, then time signature and key in another | Each meta revision names each change, and the status uses its Spanish label |
| HIS-007 | Clear the tempo and the time signature | The revision stores `quitó el tempo, quitó el compás` |
| HIS-008 | Create a song | The first revision stores `creó la composición` |
| HIS-009 | Restore version 2 | The new revision stores `restauró la versión 2` |
| HIS-010 | Change enough to exceed 120 characters | The summary has 120 characters and ends in `…` |
| HIS-011 | Save without changes | No revision is written |
| HIS-012 | Read a revision saved before `summary` existed | Returns `summary: null` and its snapshot unchanged |
| HIS-013 | Read revisions as a reader | The summary is returned, and no internal ID is added |
| HIS-014 | Show a revision with a summary in HistoryList | Shows author, summary, date and the Ver and Restaurar buttons |
| HIS-015 | Show a revision without a summary in HistoryList | Shows the author and `Versión N` |
