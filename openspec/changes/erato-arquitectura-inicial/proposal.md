# Proposal: Initial Architecture for Erato

> **Status: awaiting author confirmation.** Per `AGENTS.md` rules 1 and 3, this document proposes
> decisions; it does not enact them. No application code, no MongoDB schema, and no dependency
> installation follows until the author explicitly confirms the recommendations below.

## Intent

Erato currently has one commit and no backend or frontend source. Five foundational decisions listed
in `AGENTS.md` ("Antes de empezar, pregunta") and `openspec/config.yaml` `pending_decisions` block
every line of implementation: the Python backend framework, the MongoDB service, the authentication
method, demo audio storage, and design-system integration. Until they are settled, every downstream
phase (spec, design, tasks, apply) would be writing against assumptions the author has explicitly
forbidden.

A hard, non-negotiable constraint governs all of them: **Erato must be hostable at zero recurring
cost, indefinitely.** That constraint is why Vercel was chosen for deploy, and it is the first filter
every option below passes through — ahead of developer experience, performance, or popularity.
One-time or time-limited credits (GitHub Student Pack: ~USD 50 MongoDB Atlas credit, ~USD 100–200
DigitalOcean credit, free domain for year one) are treated as bonuses only. They expire, so no
recommendation rests on them. Azure is excluded by author decision.

Success looks like: the author reads this document, confirms or corrects four recommendations, and
the project can then move to specs and design with a known, costed, permanently free platform.

## Decision Status at a Glance

| # | Decision | State | Recommendation |
|---|----------|-------|----------------|
| 1 | Backend Python framework | **Newly proposed** — needs confirmation | FastAPI on Vercel Python serverless functions |
| 2 | MongoDB service tier | **Newly proposed** — needs confirmation | MongoDB Atlas M0 (free forever). Schema NOT designed here |
| 3 | Authentication method | **Newly proposed** — needs confirmation | Self-rolled email/password + JWT, backend-validated |
| 4 | Demo audio storage | **Newly proposed** — needs confirmation | Cloudinary free tier |
| 5 | Design-system integration | **Already locked by the author** — not reopened | Components reimplemented in Vue 3 (no React wrapping) |

## Scope

### In Scope

- A written recommendation with rationale for decisions 1–4, each justified first against the
  zero-recurring-cost constraint and then against fit with the `AGENTS.md` feature set.
- Restating decision 5 as settled, with the porting risks it carries into design and tasks.
- Naming the residual free-tier limits that survive confirmation and must be designed around
  (Vercel 10s execution cap, Atlas M0 512MB storage cap, serverless-to-Mongo connection reuse).
- Declaring which capabilities the spec phase must write, and which are deliberately deferred.

### Out of Scope

- **The MongoDB schema.** Collections, fields, types, indexes, relationships, and validation rules
  require a separate, explicit author approval step under `AGENTS.md` rule 1. This proposal
  recommends only the *service tier*. A dedicated schema proposal follows after confirmation.
- Any application code, dependency installation, `docker-compose.yml`, or Vercel configuration.
- Feature-level behavior: chord detection, tab editing, lyrics auto-scroll, timestamp comments,
  task lists. These depend on the approved schema and are separate changes.
- The composition-level permission/sharing rules themselves (public view-only vs private, invited
  editors). The auth *mechanism* is decided here; the authorization *rules* depend on the approved
  schema and are deferred.
- Domain registration, production environment provisioning, and CI setup.
- Azure-based options of any kind (excluded by the author).

## Capabilities

> Contract with the spec phase. These names assume the author confirms decisions 1–4; if a
> recommendation is corrected, the affected capability's spec changes accordingly.

### New Capabilities

- `backend-platform`: Python serverless backend on Vercel — request handling contract, environment
  configuration, health/readiness behavior, and the execution-time budget every handler must respect.
- `data-persistence`: MongoDB Atlas connection contract for a serverless runtime — client reuse
  across warm invocations, connection limits, failure behavior. **Explicitly excludes the schema.**
- `authentication`: user registration, login, credential storage, and token issuance/validation as a
  backend-enforced contract.
- `media-storage`: demo audio upload, storage, and delivery through an external media provider, plus
  the rule that audio binaries never enter MongoDB.
- `design-system-port`: the contract that Vue 3 components must match the `erato-design-system/`
  reference in appearance and behavior, including the non-trivial ported logic.

### Modified Capabilities

None. `openspec/specs/` is empty; this is the project's first change.

## Approach

### Decision 1 — Backend framework: **FastAPI**

Vercel's Hobby (free) plan caps function execution at 10 seconds, allows ~1,000,000 invocations and
4 CPU-hours per month, and limits a function bundle to 50MB compressed. Both FastAPI and Flask fit
comfortably inside those limits for a band-sized app, so cost does not separate them — fit does.

FastAPI is recommended because:

- Vercel auto-detects ASGI applications natively; FastAPI deploys without a WSGI shim.
- Pydantic validation is built in, which directly serves the `AGENTS.md` requirement that permission
  and visibility rules are validated **in the backend on every request** rather than hidden in the UI.
- Async I/O suits a workload dominated by waiting on MongoDB Atlas and the media provider, which
  matters under a 10s wall clock.
- Generated OpenAPI documentation is free and useful for a portfolio project.

The tradeoff against Flask is a slightly heavier import graph (marginally worse cold starts) and the
async learning curve. Both are judged acceptable against the validation and ASGI benefits.

**Design consequence to carry forward:** handlers must stay thin. Anything synchronous and heavy —
audio transcoding, waveform generation, bulk processing — cannot live in a Vercel Hobby function.
Audio must be uploaded to the media provider and processed there or not at all.

### Decision 2 — Database service: **MongoDB Atlas M0 (free forever)**

Atlas serverless instances were retired in January 2026; the remaining options are Free (M0), Flex,
and Dedicated. M0 is the only perpetual $0 tier and therefore the only option that satisfies the
governing constraint. It provides 512MB storage, up to 500 connections, roughly 100 ops/sec, and
auto-pauses after 30 days with zero connections (it does not expire).

The GitHub Student Pack's ~USD 50 Atlas credit is a bonus that can temporarily fund a larger tier. It
is deliberately **not** the basis of this recommendation, because the credit expires and the cost
constraint does not.

**This proposal does not design the schema.** For context only — and subject to the separate approval
step — exploration mapped the conceptual shape as: compositions as the core entity (with chords,
tabs, lyrics, and tasks as closely-held sections), demos as a one-to-many child of a composition,
timestamp-anchored comments attached to demos, plus users and invitations/sharing state. Those are
candidates for discussion in the schema proposal, not approved structures.

**Design consequence:** audio binaries must never be stored in MongoDB. GridFS would consume the
512MB cap almost immediately, which is why decision 4 exists at all.

### Decision 3 — Authentication: **self-rolled email/password + JWT**

All three realistic candidates (self-rolled JWT, Google OAuth only, hosted providers like Clerk or
Auth0) cost nothing today at a band's user count, so the deciding factors are vendor-policy risk and
fit with Erato's sharing model.

Recommended: self-rolled email and password with JWT bearer tokens, validated by the backend on
every request.

- **Zero vendor-policy risk.** JWT is a standard, not a service. Clerk and Auth0 free tiers are
  generous today but are commercial products whose terms can change; Clerk's limits were already
  revised in February 2026. A perpetual-cost constraint argues against depending on another
  company's pricing decisions.
- **Statelessness fits serverless.** Token validation needs no database round trip, which helps under
  the 10s cap and avoids pressure on Atlas M0's connection and ops limits.
- **The sharing model has to be built either way.** `AGENTS.md` requires public compositions viewable
  by anyone with the link (no account), private compositions visible only to invited users, and edit
  rights restricted to invited users in both cases. No auth provider supplies that
  composition-level authorization; it is custom logic on top of identity regardless of choice. A
  hosted provider would remove perhaps the password-hashing work while adding a dependency.

The cost is real and should be acknowledged: the author owns the security surface — password hashing
(bcrypt or argon2), token expiry and refresh, invite-link token generation, and revocation. These
must be specified explicitly and covered by tests, which `AGENTS.md` already requires for permissions
and visibility.

**If the author prefers lower implementation effort**, adding Google OAuth as a login option later is
compatible with this design: the permission layer is independent of how identity is proven. That is a
non-blocking extension, not an alternative architecture.

### Decision 4 — Demo audio storage: **Cloudinary free tier**

The author is already signing up for Cloudinary, and exploration confirmed it as the strongest fit:

- **Cloudinary** offers a perpetual free plan of 25 monthly credits (1 credit ≈ 1GB storage, 1GB
  bandwidth, or 1,000 transformations) — the most generous pooled allowance among the options
  compared, with no time limit, and built for media delivery.
- **AWS S3 was rejected**: its 5GB/100GB-transfer free tier lasts only 12 months from account
  creation, then reverts to paid. A portfolio project meant to stay live indefinitely would breach
  the cost constraint in year two.
- **MongoDB GridFS was rejected**: it collides directly with Atlas M0's 512MB cap.
- **Vercel Blob** was considered (first-party, trivial integration) but its free-tier figures were
  inconsistent across sources during exploration (500MB vs 1GB storage), suggesting an actively
  changing tier — weak ground for a permanent commitment.

**Design consequence:** audio files live in Cloudinary; MongoDB stores only references and metadata
(public ID, URL, duration, uploader, timestamps). Credits are pooled, so heavy transformation usage
would eat the storage budget — the app should store and serve audio without on-the-fly
transformations unless a specific need justifies it.

### Decision 5 — Design-system integration: **already decided — reimplement in Vue 3**

The author has already settled this: `erato-design-system/` components are **reimplemented in Vue 3**,
not wrapped from React. This avoids shipping React 18 and Vue in the same bundle and yields an
idiomatic, lighter frontend. It is recorded here as settled context, not reopened as an option.

Risks this carries into design and tasks:

- Non-trivial logic must be ported faithfully: `detectChord()` (including slash chords like `D/F#`
  and extended chords like `Cmaj7`, `F#m7b5`, `D9`), `tabToText()`, and the tab editor's keyboard
  navigation (arrow movement, measure insertion, techniques `h p b / ~ x`).
- `erato-design-system/components/index.d.ts` suggests these utilities may be plain JS/TS separable
  from the React component shells. **The design phase must verify whether they can be imported
  independently of `bundle.js`.** If they can, the hardest reimplementation risk (the chord-detection
  algorithm) collapses into reuse rather than a rewrite.
- Visual drift from the reference is an ongoing risk; tokens from `tokens.css` / `tokens.json` must
  be used directly, and both themes (Noche, Matiné) verified.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/config.yaml` | Modified | `pending_decisions` resolved on confirmation; `rules.apply.test_command`, `rules.verify.test_command`, and `build_command` become fillable once the framework is fixed |
| `openspec/changes/erato-arquitectura-inicial/` | New | This proposal and its downstream spec/design/tasks artifacts |
| `AGENTS.md` | Modified (deferred) | "Antes de empezar, pregunta" and the stack table can record the confirmed choices once the author approves |
| Backend source tree (not yet created) | New (deferred) | FastAPI application, Vercel function entry point, Atlas client module, auth module |
| Frontend source tree (not yet created) | New (deferred) | Vue 3 app and ported design-system components |
| `erato-design-system/components/index.d.ts`, `bundle.js` | Read-only reference | Source of truth for the Vue port; the design system itself is not modified |
| `.env.example` (not yet created) | New (deferred) | Atlas connection string, JWT secret, Cloudinary credentials — documented, never committed (`AGENTS.md` rule 4) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Vercel Hobby's 10s execution cap breaks a heavy endpoint | Medium | Keep handlers thin; upload audio directly to Cloudinary rather than proxying through a function; never do synchronous audio processing in a Vercel function |
| Atlas M0's 512MB cap is exhausted by metadata and comment growth | Medium | Audio stays in Cloudinary; schema proposal must consider comment volume and document growth; monitor usage and treat the Student Pack Atlas credit as emergency headroom, not a plan |
| Serverless cold starts open a new Mongo connection per invocation, exhausting the 500-connection limit | Medium | Reuse a module-level Mongo client across warm invocations; specify this explicitly in the `data-persistence` capability rather than leaving it to implementation |
| Self-rolled auth is implemented insecurely | Medium | Specify hashing algorithm, token expiry, refresh, and invite-token generation in the spec phase; require tests for permissions and visibility as `AGENTS.md` already mandates |
| Cloudinary's credit model conflates storage, bandwidth, and transformations | Low-Medium | Serve audio without on-the-fly transformations; track credit consumption; the 25-credit perpetual allowance is ample for a band library if transformations stay unused |
| Vue port drifts visually or behaviorally from the design system | Medium | Verify whether `detectChord`/`tabToText` are importable independently before rewriting; use tokens directly; test both Noche and Matiné themes; write tests for chord detection and tab editing |
| A free tier's terms change after the project is built | Low-Medium | Every recommended service has a perpetual (not trial) free plan; the self-rolled auth choice removes the largest vendor-policy exposure; re-verify Vercel Blob/Cloudinary figures at implementation time rather than trusting this snapshot |
| The author disagrees with a recommendation | Medium | Nothing is implemented until confirmation; each decision is independent, so a correction to one does not invalidate the others |

## Rollback Plan

No code or infrastructure exists yet, so rollback at this stage is documentary and cheap:

1. **Before confirmation:** this proposal is a file plus an Engram observation. Reverting means
   deleting `openspec/changes/erato-arquitectura-inicial/` and leaving `pending_decisions` untouched.
   Nothing downstream depends on it.
2. **After confirmation, before implementation:** restore the affected entries in
   `openspec/config.yaml` `pending_decisions` and reopen the specific decision; the other three
   recommendations remain valid independently.
3. **After implementation begins**, per decision:
   - *Framework (FastAPI → Flask)*: the costliest reversal. Confined to the backend entry point,
     routing, and validation layer; business logic and the Mongo client module should be written
     framework-agnostically to keep this contained.
   - *Database tier (M0 → Flex/Dedicated)*: Atlas supports in-place tier upgrade with no application
     change beyond the connection string. Low-risk, but breaks the cost constraint and requires
     author approval.
   - *Auth (self-rolled → hosted provider)*: the composition-level permission layer is independent of
     the identity mechanism, so swapping identity providers leaves authorization intact. Existing
     users would need a migration or re-registration path.
   - *Audio storage (Cloudinary → other)*: MongoDB stores only references, so migration means
     re-uploading files and rewriting reference fields. Keep the storage integration behind a single
     module so the provider is swappable.
   - *Design system (Vue port → React wrapping)*: reversible by loading `bundle.js` and mounting
     React components inside Vue wrappers, at the cost of a second UI runtime. The ported Vue
     components would be discarded.

## Dependencies

- **Author confirmation of decisions 1–4** — blocking. Nothing proceeds without it (`AGENTS.md` rule 3).
- **A separate MongoDB schema proposal and explicit approval** — blocking for any data-touching work
  (`AGENTS.md` rule 1). This proposal deliberately does not satisfy that gate.
- **Accounts to provision** (all free tier): MongoDB Atlas, Cloudinary (author already signing up),
  Vercel.
- **Available bonuses, not load-bearing**: GitHub Student Pack (~USD 50 Atlas credit, free domain for
  year one, ~USD 100–200 DigitalOcean credit). Azure is excluded.
- **Verification pending in design:** whether `detectChord` and `tabToText` are importable
  independently of the React shells in `erato-design-system/components/`.

## Success Criteria

- [ ] The author has explicitly confirmed or corrected each of decisions 1–4.
- [ ] Decision 5 is recorded as settled (Vue 3 reimplementation) with its porting risks carried into
      the design phase.
- [ ] Every confirmed service has a **perpetual** free tier; no recommendation depends on an expiring
      credit, and any that does is flagged as a risk rather than assumed.
- [ ] `openspec/config.yaml` `pending_decisions` is updated to reflect the resolved decisions.
- [ ] The MongoDB schema remains unspecified and is routed to its own approval step.
- [ ] The three residual free-tier constraints (Vercel 10s cap, Atlas M0 512MB cap, serverless
      connection reuse) are carried into the spec and design phases as explicit requirements, not
      implementation folklore.
- [ ] No application code, dependency, or infrastructure config was created by this phase.
