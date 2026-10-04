# Composition Versioning Specification

Repo: `erato`. Schema as approved in D1 (option C): `compositions.section_revs` counter plus
`section_revisions` collection.

## Purpose

Prevents silent overwrites between concurrent editors and keeps a bounded per-section history of
lyrics, chords and tablature, with restore. Todos are not versioned and stay last-write-wins.

## Requirements

### Requirement: Each versioned section MUST carry a revision counter

Lyrics, chords and tablature MUST each have a revision counter on the composition, exposed in the
composition response. A missing counter MUST be read as 0. The counter MUST increase by exactly one
on each successful save of that section. Todos MUST NOT require or enforce a revision.

#### Scenario: Legacy composition

- GIVEN a composition stored without any revision counters
- WHEN it is read
- THEN every versioned section revision MUST be reported as 0

#### Scenario: Successful save increments

- GIVEN lyrics revision 7
- WHEN an authorized editor saves lyrics with `expected_rev: 7`
- THEN the save MUST succeed and the lyrics revision MUST be 8
- AND the other sections' revisions MUST be unchanged

### Requirement: Saves MUST be conditional on the expected revision

A section write carrying `expected_rev` MUST be applied only if the stored revision equals it, as a
single atomic check-and-write. On mismatch the backend MUST respond 409 and MUST NOT modify the
section.

#### Scenario: Stale save is rejected

- GIVEN lyrics revision 8 and a client holding revision 7
- WHEN it saves lyrics with `expected_rev: 7`
- THEN the backend MUST respond 409
- AND the stored lyrics MUST be unchanged

#### Scenario: Concurrent saves

- GIVEN two clients both holding revision 3
- WHEN both save the same section concurrently with `expected_rev: 3`
- THEN exactly one MUST succeed and the other MUST receive 409

#### Scenario: Save without expected_rev keeps last-write-wins

- GIVEN a section write without `expected_rev`
- WHEN an authorized editor submits it
- THEN the write MUST be applied unconditionally and the revision MUST still increment

### Requirement: The 409 response MUST carry the current server state

The 409 body MUST include the current revision, the current section content, the author of that
revision and its timestamp, so the client can offer the choice to reload or overwrite.

#### Scenario: Conflict payload

- GIVEN a stale save of lyrics
- WHEN the backend responds 409
- THEN the body MUST contain `current_rev`, current `content`, `author` and `updated_at`

### Requirement: Successful saves MUST record a snapshot, deduplicated and bounded

After a successful save of a versioned section, the backend MUST store a full snapshot (composition,
section, rev, content, author, timestamp). Saving content identical to the current content MUST NOT
create a snapshot. At most the last 50 snapshots per section per composition MUST be retained; older
ones MUST be pruned after insert. Snapshots are recorded for every plan. Deleting a composition
MUST delete its snapshots. A snapshot insertion failure MUST NOT fail or alter the saved content.

#### Scenario: Snapshot recorded

- GIVEN lyrics revision 4
- WHEN an editor saves changed lyrics
- THEN a snapshot with rev 5, the new content, the author id and a timestamp MUST exist

#### Scenario: Identical content

- GIVEN current lyrics content "A"
- WHEN an editor saves "A" again
- THEN no new snapshot MUST be created

#### Scenario: Retention cap

- GIVEN a section with 50 snapshots, newest rev 50
- WHEN a 51st save succeeds
- THEN 50 snapshots MUST remain and rev 1 MUST be pruned

#### Scenario: Cascade delete

- GIVEN a composition with snapshots
- WHEN the composition is deleted
- THEN none of its snapshots MUST remain

#### Scenario: Snapshot failure does not fail the save

- GIVEN the snapshot insert fails after the section was updated
- WHEN the save completes
- THEN the response MUST be successful with the new content and revision

### Requirement: History listing and restore MUST be gated through PlanPolicy

Listing a section's history and restoring a snapshot MUST require edit permission on the composition
and MUST consult `PlanPolicy`'s history gate. When the gate denies, the backend MUST respond 403 with
a machine-readable code identifying the plan gate. Listing MUST be paginated, newest first. Restore
MUST be a normal save of the old content (a new revision) and MUST be subject to the same conflict
check.

#### Scenario: History allowed

- GIVEN a policy that allows history and a section with several snapshots
- WHEN an editor lists history
- THEN snapshots MUST be returned newest first with rev, author and timestamp

#### Scenario: History denied

- GIVEN a policy that denies history
- WHEN an editor requests history or restore
- THEN the backend MUST respond 403 with the plan-gate code
- AND no content MUST change

#### Scenario: Restore creates a new revision

- GIVEN lyrics at revision 9 and a snapshot rev 5
- WHEN an editor restores rev 5 with `expected_rev: 9`
- THEN lyrics content MUST equal snapshot rev 5 content and the revision MUST be 10

#### Scenario: Non-editor cannot read history

- GIVEN a viewer-role user
- WHEN they request history
- THEN the backend MUST respond 403 or 404 and return no content

#### Scenario: Unlimited default

- GIVEN `UnlimitedPlanPolicy`
- WHEN any editor requests history
- THEN it MUST be allowed

### Requirement: The UI MUST save only dirty sections and resolve conflicts per section

The frontend MUST send only sections that changed, settle all section saves independently, update
the stored revision for each success, and open a conflict dialog per conflicting section offering
"Cargar la versión guardada" and "Sobrescribir con la mía". Successful sections MUST stay saved.

#### Scenario: Only dirty sections are sent

- GIVEN lyrics edited and chords untouched
- WHEN the user saves
- THEN only the lyrics request MUST be sent

#### Scenario: Partial conflict

- GIVEN lyrics and chords both edited, lyrics stale
- WHEN the user saves
- THEN chords MUST be saved and its revision updated
- AND a conflict dialog MUST open for lyrics only

#### Scenario: Overwrite choice

- GIVEN the conflict dialog for lyrics
- WHEN the user chooses "Sobrescribir con la mía"
- THEN the client MUST resave using the `current_rev` from the 409 as `expected_rev`

#### Scenario: Load saved choice

- GIVEN the conflict dialog for lyrics
- WHEN the user chooses "Cargar la versión guardada"
- THEN the editor MUST show the server content and discard the local edit

### Requirement: A history panel MUST let editors browse and restore versions

The UI MUST provide a history panel per versioned section listing versions with author and time, a
preview, and a restore action. When the entitlements report history as not available, the panel
entry MUST be hidden or replaced by an unavailable notice, without hard-coding plan names.

#### Scenario: Restore from the panel

- GIVEN history is available
- WHEN the user restores a version
- THEN the section content MUST update and the list MUST show the new revision

#### Scenario: History unavailable

- GIVEN the entitlements endpoint reports history unavailable
- WHEN the composition renders
- THEN no history list or restore control MUST be actionable
