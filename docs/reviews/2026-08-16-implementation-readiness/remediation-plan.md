# Blocker Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all 23 blocking findings (IR-01 … IR-23) from the 2026-08-16 implementation-readiness
review so that every milestone gate in `docs/implementation/registry.md` is clear and Phase 1 coding
can begin.

**Architecture:** This plan changes **documents, not code.** The deliverable of every task is an edit
to a requirement, specification or ADR under `docs/`, verified by a grep or link check rather than by
a test suite. Nineteen tasks are corrections to designs that are already sound; four are design
sessions producing new specification documents. The plan is ordered so that nothing blocks the build
for longer than it must: bootstrap first, then the room REST API that gates all of M2, then the M2
correctness pass as a single coherent sweep.

**Tech Stack:** Markdown under `docs/`, one `.proto` comment, one JSON Schema left untouched. No
compiler, no test runner. Verification is `grep`, the repo's link checker, and re-reading the
neighbouring paragraph.

**Spec:** [`INDEX.md`](INDEX.md) — the blocker register. Every task cites its `IR-NN` entry, which
carries the quotes, line numbers and failure scenario that justify the change. **Read the IR entry
before starting its task.**

## Global Constraints

Copied verbatim from `CLAUDE.md` and `docs/specs/INDEX.md`; every task's requirements implicitly
include these.

- **INDEX registration is mandatory.** When adding a file anywhere under `docs/`, register it in the
  nearest `INDEX.md` with a one-line description *before the task is done*. When changing an existing
  file, check whether its INDEX entry still describes it.
- **Requirement IDs are document-qualified when cited across documents** — `` `game-rooms.md`
  FR-LIFE-002``, not a bare `FR-LIFE-002`. A **wrong** qualifier is worse than a bare ID; that is what
  the three FR-ALERT-006 corrections in this review were.
- **Requirements documents link to specs** via "Related API Specifications". Adding a spec means
  adding its link there.
- **Migrations are authoritative over the schema documents** (ADR-0011 §4). No task here writes SQL
  into a migration; the schema documents are the *design* of the change.
- **Do not silently reconcile a disagreement.** If a task's edit reveals a second contradiction not
  named in this plan, record it in `INDEX.md` under a new `IR-NN` rather than fixing it in passing.
- **One commit per task.** Message form: `docs(specs): <what changed> (IR-NN)`.

## Decisions already made — do not re-litigate

Four scope questions were settled before this plan was written. They are recorded here because a task
executor who re-opens one will produce a different document than the one the rest of the plan assumes.

| Question | Decision | Consequence |
|---|---|---|
| **Onboarding wizard** (IR-23, half) | **Cut from v1.** | Task 24. No design session. 16 requirements move to Post-MVP. |
| **Design system home** (IR-23, half) | **Fold into `turnbase-frontend`** as an internal module with an enforced import boundary. `platform-ui-library.md` CON-002 is amended; no sixth repository. | Task 23. `CLAUDE.md`'s five-repo table stays at five. |
| **AI players** (IR-12) | **Keep the wire protocol; defer the schema.** Declare the v1 behaviour of the existing surface so it is implementable today. | Task 12. No `room_ai_player` table, no cut of `FR-HOST-003`. |
| **CI coverage gate** (IR-03) | **Narrow FR-CICD-003 to unit + integration**, measured at PR time. Keeps a PR gate, which is the point of having one. | Task 3. OQ-002 stands unchanged. |

---

## File structure

Files this plan creates:

| File | Responsibility |
|---|---|
| `docs/specs/api-design/room-rest-api.md` | **New.** The room REST surface: create, list, get, join, spectate, leave, invite-link resolution. Closes IR-13. |
| `docs/specs/deployment/observability.md` | **New.** OTLP export, Prometheus scrape, Loki shipping, Grafana provisioning, alert routing. Closes IR-04. |
| `docs/specs/platform-frontend/design-system.md` | **New.** Tokens, CSS strategy, component architecture, packaging boundary. Closes half of IR-23. |

Files this plan modifies, with the tasks that touch them:

| File | Tasks |
|---|---|
| `docs/specs/deployment/local-environment.md` | 1, 2, 21 |
| `docs/specs/deployment/secrets-and-configuration.md` | 1, 2 |
| `docs/requirements/platform-operations.md` | 3, 15, 21 |
| `docs/specs/platform/room-lifecycle.md` | 6, 7, 9, 10, 11 |
| `docs/specs/platform/data-model.md` | 9, 11, 12 |
| `docs/specs/platform/data-model-accounts.md` | 11, 26 |
| `docs/specs/api-design/room-chat-websocket.md` | 8 |
| `docs/specs/api-design/room-websocket.md` | 8, 12 |
| `docs/specs/api-design/websocket.md` | 19 |
| `docs/specs/api-design/rest-conventions.md` | 5 |
| `docs/requirements/game-rooms.md` | 5, 12 |
| `docs/requirements/platform-views.md` | 14, 24 |
| `docs/specs/manifest/manifest-schema.md` | 16 |
| `docs/specs/api-design/file-uploads.md` | 16 |
| `docs/specs/flows/08-upload-to-play.md` | 16 |
| `docs/specs/flows/02-room-to-game-start.md` | 17 |
| `docs/specs/game-host/game-host-internals.md` | 17, 18 |
| `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` | 18, 20 |
| `docs/specs/internal-grpc/gamehost.proto` | 20 |
| `docs/specs/api-design/input-validation.md` | 22 |
| `docs/specs/game-catalog.md` *(requirements)* | 22 |
| `docs/specs/platform-frontend/shell-architecture.md` | 23, 25 |
| `docs/specs/game-frontend/game-asset-serving.md` | 25 |
| `docs/requirements/platform-ui-library.md` | 23 |
| `docs/requirements/onboarding-wizard.md` | 24 |
| `docs/specs/INDEX.md` | 26 |
| `docs/implementation/registry.md` | 27 |
| `docs/reviews/2026-08-16-implementation-readiness/INDEX.md` | 27 |
| `STATUS.md` | 27 |

---

## Task 1: MinIO bucket — name it and create it (IR-01)

**Files:**
- Modify: `docs/specs/deployment/local-environment.md` §5 (`:258-276`) and §7.9 (`:437-456`)
- Modify: `docs/specs/deployment/secrets-and-configuration.md` §4 MinIO/S3 (`:204-213`)

**Interfaces:**
- Produces: config key `turnbase.artifact-store.bucket`, default `turnbase-bundles`, env
  `TURNBASE_ARTIFACT_STORE_BUCKET`. Tasks 2 and 21 add sibling rows to the same §7.9 table; keep the
  table's existing column order (`Property | Default | Env`).

- [ ] **Step 1: Add the bucket to the §7.9 configuration table**

Insert immediately after the existing `turnbase.artifact-store.endpoint` row:

```markdown
| `turnbase.artifact-store.bucket` | `turnbase-bundles` | `TURNBASE_ARTIFACT_STORE_BUCKET` |
```

- [ ] **Step 2: State the creation mechanism in §5**

The bucket must exist before the monolith serves its first upload slot, and `make seed` drives the
real upload pipeline on a clean machine. Append to §5, after the `helm upgrade` block:

```markdown
### The bundle bucket is created by an init step, not by the application

`turnbase.artifact-store.bucket` (§7.9) must exist before the monolith issues its first pre-signed
URL. It is created by a one-shot `minio/mc` init container that runs to completion before the
monolith starts:

```yaml
minio-init:
  image: minio/mc
  depends_on: { minio: { condition: service_healthy } }
  entrypoint: >
    /bin/sh -c "
    mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
    mc mb --ignore-existing local/$$TURNBASE_ARTIFACT_STORE_BUCKET &&
    mc anonymous set none local/$$TURNBASE_ARTIFACT_STORE_BUCKET"
```

Under Kubernetes the same three commands run as a `Job` with the chart's `minio` credentials.

`--ignore-existing` makes the step idempotent, which matters because it runs on every
`docker compose up` and a second run must not fail the stack. `mc anonymous set none` is explicit
rather than relying on the default: a bundle bucket that is publicly listable exposes every
unpublished game version, and the published-assets route (`../game-frontend/game-asset-serving.md`
§4) serves through the monolith precisely so the bucket never needs to be public.

**The application asserts, it does not create.** On startup the monolith checks the bucket exists and
fails with a message naming `TURNBASE_ARTIFACT_STORE_BUCKET` if it does not — the same posture
FR-CRED-005 takes on `CREATE EXTENSION` (§4 of
[`secrets-and-configuration.md`](secrets-and-configuration.md)), and for the same reason: a service
that provisions its own infrastructure needs privileges it should not hold at runtime.
```

- [ ] **Step 3: Add the bucket to the container table in §1**

The `minio-init` container is a tenth entry. Add a row to §1's table after the `MinIO` row:

```markdown
| MinIO init (`minio-init`) | `minio/mc` | — | MinIO. Runs to completion, then exits |
```

Then change §1's opening sentence from `Nine containers.` to
`Nine long-running containers plus a one-shot MinIO init job.`

- [ ] **Step 4: Cross-reference from the secrets document**

In `secrets-and-configuration.md` §4, MinIO / S3 subsection, append after the existing paragraph:

```markdown
The bucket itself is **not** a secret and is therefore in
[`local-environment.md`](local-environment.md) §7.9, not here. It is created by the init step in §5 of
that document, using the same root credentials; the application's own credential needs only object
read/write on it.
```

- [ ] **Step 5: Verify**

Run: `grep -rn "artifact-store.bucket\|turnbase-bundles\|minio-init" docs/specs/deployment/`
Expected: at least five hits across both files — the §7.9 row, the §1 container row, the init block,
and the two prose references.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/deployment/local-environment.md docs/specs/deployment/secrets-and-configuration.md
git commit -m "docs(specs): name and provision the bundle bucket (IR-01)"
```

---

## Task 2: Two-role Postgres provisioning (IR-02)

**Files:**
- Modify: `docs/specs/deployment/secrets-and-configuration.md` §1 (`:18-27`) and §4 PostgreSQL (`:171-191`)
- Modify: `docs/specs/deployment/local-environment.md` §5 and §7.9

**Interfaces:**
- Consumes: the §5 init-step pattern established in Task 1.
- Produces: two credential pairs. `POSTGRES_USER`/`POSTGRES_PASSWORD` name the **owner**;
  `TURNBASE_DB_APP_PASSWORD` is the application role's. `spring.datasource.username` becomes
  `turnbase_app`.

The failure this closes is silent: a naive compose file sets `POSTGRES_USER=turnbase_app`, which makes
the application role the database superuser and violates `platform-operations.md` FR-CRED-005 while
appearing to work perfectly. Nothing fails, so nothing is noticed.

- [ ] **Step 1: Split the credential in the §1 inventory**

Replace the single `PostgreSQL password` row with two:

```markdown
| PostgreSQL **owner** password (`turnbase_owner`) | Provisioning only — never held by a running service | Restart of the init step | `.env` |
| PostgreSQL **application** password (`turnbase_app`) | Platform Monolith | With a two-phase change | `.env` |
```

Then change the sentence below the table from `Seven secrets, one of which rotates on a schedule.` to
`Eight secrets, one of which rotates on a schedule.`

- [ ] **Step 2: Name the provisioning mechanism in §4**

Append to the PostgreSQL subsection of §4, after the "Rotating the password is two-phase" paragraph:

```markdown
**Where the split is actually made.** `postgres:16-alpine` runs every `*.sql` and `*.sh` in
`/docker-entrypoint-initdb.d` once, on an empty data directory, as the superuser named by
`POSTGRES_USER`. That is the only hook, and it is where the two roles are created:

```sql
-- deploy/compose/initdb/01-roles.sql
CREATE ROLE turnbase_app LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE turnbase TO turnbase_app;
GRANT USAGE, CREATE ON SCHEMA public TO turnbase_app;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

`POSTGRES_USER` is therefore `turnbase_owner`, **not** `turnbase_app` — the container's own user is
the superuser by construction, so naming the application role there would hand it superuser and
violate FR-CRED-005 with nothing appearing to be wrong. The application connects as `turnbase_app`
with `TURNBASE_DB_APP_PASSWORD`; `turnbase_owner`'s password reaches the init step and nothing else.

`GRANT ... CREATE ON SCHEMA public` is what lets Flyway run in-process under the application role
(ADR-0011 §1). `CREATE EXTENSION` stays with the owner because it needs superuser, and the baseline
migration only *asserts* the extension's presence ([`schema-migrations.md`](schema-migrations.md) §5).

**This runs on an empty data directory only.** A volume that already holds a database skips
`initdb` entirely, so a developer who adds a role after first start must apply it by hand or
`make reset-db`. Under Kubernetes the equivalent is a `Job` with the same SQL, guarded by
`IF NOT EXISTS`, because a `StatefulSet`'s PVC survives `helm upgrade`.
```

- [ ] **Step 3: Add the two datasource keys to §7.9 of `local-environment.md`**

The existing table has `spring.datasource.url` and no username. Insert after it:

```markdown
| `spring.datasource.username` | `turnbase_app` | `SPRING_DATASOURCE_USERNAME` |
```

Leave the password out of that table — §7.9 ends with "Credentials are **not** in this table", and
that rule holds.

- [ ] **Step 4: Reference the init directory from §5**

In `local-environment.md` §4's directory tree, add under `compose/`:

```
│   ├── initdb/
│   │   └── 01-roles.sql              # FR-CRED-005 two-role split
```

- [ ] **Step 5: Verify**

Run: `grep -rn "turnbase_owner\|turnbase_app\|initdb" docs/specs/deployment/`
Expected: hits in both files. Confirm no remaining text implies a single Postgres credential — in
particular that §1's table no longer has a bare `PostgreSQL password` row.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/deployment/
git commit -m "docs(specs): provision the two-role Postgres model (IR-02)"
```

---

## Task 3: Resolve the CI coverage-gate contradiction (IR-03)

**Files:**
- Modify: `docs/requirements/platform-operations.md:107` (FR-CICD-003)

FR-CICD-003 requires a PR-time gate measured "across all test types combined"; OQ-002 moves e2e
post-merge. The PR gate cannot compute a number whose input does not exist yet. **Decision: narrow the
requirement, keep the gate.**

- [ ] **Step 1: Replace the FR-CICD-003 description**

Replace the cell text of FR-CICD-003 with:

```markdown
All services must maintain ≥70% line coverage measured across **unit and integration tests** — the
two categories that run in the PR pipeline (OQ-002 moves e2e post-merge). Coverage is measured and
reported as part of the PR pipeline, and a drop below threshold is a failing check. E2E tests
deliberately do **not** contribute: their coverage is not available when the gate runs, and a
threshold that silently counts a number it cannot see is a threshold that will be met by accident.
Post-merge e2e runs report coverage for information only and gate nothing.
```

- [ ] **Step 2: Make OQ-002 point back**

Append one sentence to OQ-002's resolution (`:232`):

```markdown
FR-CICD-003's threshold is scoped to the two categories that run at PR time as a direct consequence.
```

- [ ] **Step 3: Verify**

Run: `grep -n "all test types combined" docs/requirements/platform-operations.md`
Expected: **no output.** The phrase that created the contradiction is gone.

- [ ] **Step 4: Commit**

```bash
git add docs/requirements/platform-operations.md
git commit -m "docs(requirements): scope the coverage gate to PR-time test types (IR-03)"
```

---

## Task 4: Design the room REST API (IR-13)

**Files:**
- Create: `docs/specs/api-design/room-rest-api.md`
- Modify: `docs/specs/api-design/INDEX.md` — register it
- Modify: `docs/requirements/game-rooms.md` — add it to "Related API Specifications"

This is the entry point to every join, create and rejoin scenario in the corpus and it gates all of
M2. `POST /api/rooms` currently exists only as a narrative step in `flows/02-room-to-game-start.md:15`
and a query-string example in `pagination-filtering-sorting.md:44`. The coverage script confirms
FR-CREATE-001/002/004, FR-HOST-001/002/008, FR-JOIN-001…005/009/010/011 and FR-LIST-002…007 are cited
by no spec.

**Interfaces:**
- Consumes: `rest-conventions.md` (status codes, the `/api/rooms/{id}` authorization predicate at
  `:94`, the Origin check), `pagination-filtering-sorting.md` (list envelope),
  `error-handling.md` (RFC 9457 shape), `room-lifecycle.md` §1.2 (the claim runs on the REST join,
  and `ROOM_UNAVAILABLE_RETRY` is its redirect result), `data-model.md` §1–§3 (column names).
- Produces: the endpoint set that `room-websocket.md` assumes a client has already called, and the
  affinity hint that `room-lifecycle.md` §1.7 calls advisory.

**Design decisions locked before writing** — these are the choices the document must not leave open:

1. **The REST surface is membership only. Every in-room mutation is STOMP.** Readiness, team
   management, parameters, kick and host transfer are all in `room-websocket.md` and stay there. REST
   covers: create, list, get, join, join-as-spectator, leave, resolve invite code. This is the line
   `rest-conventions.md:94` already assumes when it says "host commands additionally
   `room.host_user_id = principal`, re-checked under the room lock".
2. **`POST /api/rooms` returns `201` with a `Location` header and the full room resource**, including
   the affinity hint. A client must not need a second round-trip before opening its socket.
3. **The affinity hint is a response header, not a body field** — `X-TurnBase-Room-Instance`. It is
   transport routing, it is advisory (FR-DEPLOY-002), and putting it in the body invites a client to
   persist it.
4. **Join and create both run the claim** (`room-lifecycle.md` §1.2). Result `0` (redirect) becomes
   `503` with `Retry-After` and the problem type `room-unavailable-retry`, matching the STOMP
   `ROOM_UNAVAILABLE_RETRY` code so the client has one concept, not two.
5. **`POST /api/rooms/{id}/participants` is the join**, with a body distinguishing
   `{"role": "PLAYER"}` from `{"role": "SPECTATOR"}`. Not two endpoints — FR-JOIN-006 requires
   presenting both as distinct actions on the *same* room, and one endpoint with a role makes the
   "either, depending on availability" response shape natural.
6. **Leaving is `DELETE /api/rooms/{id}/participants/me`.** Never a user id in the path: the
   self-scoped rule in `rest-conventions.md:91` is explicit, and a room participant is self-scoped.
7. **The invite code resolves through the room resource, not a separate one.**
   `GET /api/rooms?inviteCode={code}` returns a single-element list or an empty one — never `404`,
   which would confirm that a code exists. FR-XFER-003 and NFR-SEC-002 both point here.
8. **FR-JOIN-007's single-room constraint is enforced server-side inside the join transaction**, and
   the abandonment prompts (FR-JOIN-008/009/010) are client-side only. The server never asks; it acts,
   and returns the released room in the response so the client can reconcile. A confirmation the
   server waits for is a lock held across a user's coffee break.

**Document outline** — sections in this order:

| § | Content |
|---|---|
| Scope | What is REST and what is STOMP, with decision 1 stated as the rule |
| Related | `rest-conventions.md`, `room-websocket.md`, `room-lifecycle.md`, `game-rooms.md`, `pagination-filtering-sorting.md` |
| 1. Endpoint table | Method, path, auth, success status, requirement IDs — one row per endpoint |
| 2. `POST /api/rooms` | Request body (`gameId`, `visibility`, `spectatingEnabled`), the FR-TEAM-012 instantiation and FR-CREATE-003 auto-join that happen inside it, `201` body, `Location`, affinity header |
| 3. `GET /api/rooms` | The FR-LIST-001 inclusion predicate written as a predicate; filters and sorts from FR-LIST-003; `inviteCode` per decision 7; FR-LIST-006/007 visibility; pre-computed `canJoin`/`canSpectate` per FR-LIST-003a |
| 4. `GET /api/rooms/{id}` | The full room resource; `404` for closed (FR-XFER-003) |
| 5. `POST /api/rooms/{id}/participants` | Join. Role selection, capacity and Blocked Slot evaluation, FR-JOIN-007 release of the prior room, FR-TEAM-005 auto-assignment, the claim, the `503` retry |
| 6. `DELETE /api/rooms/{id}/participants/me` | Leave. `204`. FR-LIFE-004 confirmed-voluntary semantics; the host case delegates to `room-lifecycle.md` §4 |
| 7. Error catalogue | One table: condition → status → problem `type` → requirement |
| 8. What is deliberately absent | No room update endpoint (game is locked, FR-CREATE-004); no participant list endpoint (`ROOM_STATE` carries it); no readiness or team routes (decision 1) |
| 9. Requirements traceability | Every FR-CREATE / FR-JOIN / FR-LIST / FR-LIFE id this document realizes |

- [ ] **Step 1: Re-read the requirement source**

Read `docs/requirements/game-rooms.md` sections *Room List*, *Room Joining*, *Room Creation* and
*Room Lifecycle*, and `docs/specs/api-design/rest-conventions.md` in full. The endpoint set is
determined by those two documents; this task adds no new behaviour.

- [ ] **Step 2: Write `docs/specs/api-design/room-rest-api.md`**

Follow the outline above. Match the house voice of `rest-conventions.md`: state the rule, then state
why the obvious alternative is wrong. Every decision in the locked list must appear in the document
*with its reason*, not merely its conclusion — the reason is what stops the next reader re-opening it.

- [ ] **Step 3: Register it in the API-design INDEX**

Add a row to `docs/specs/api-design/INDEX.md`:

```markdown
| [room-rest-api.md](room-rest-api.md) | Room membership REST surface: create, list, get, join, leave, invite-code resolution. In-room mutations are STOMP — see `room-websocket.md`. |
```

- [ ] **Step 4: Link it from the requirements**

Add to `docs/requirements/game-rooms.md`'s "Related API Specifications" list, after the
`rest-conventions.md` entry:

```markdown
- [room-rest-api.md](../specs/api-design/room-rest-api.md) — the room membership REST surface: create, list, get, join, leave, invite-code resolution (implements FR-CREATE-*, FR-JOIN-001–007, FR-LIST-*)
```

- [ ] **Step 5: Verify coverage of the previously uncited requirements**

Run:

```bash
for id in FR-CREATE-001 FR-CREATE-002 FR-CREATE-004 FR-JOIN-001 FR-JOIN-002 FR-JOIN-003 \
          FR-JOIN-004 FR-JOIN-005 FR-JOIN-009 FR-JOIN-010 FR-JOIN-011 \
          FR-LIST-002 FR-LIST-003 FR-LIST-004 FR-LIST-005 FR-LIST-006 FR-LIST-007; do
  grep -q "$id" docs/specs/api-design/room-rest-api.md || echo "UNCITED: $id"
done
```

Expected: no output. Every requirement the coverage script flagged is now cited by a spec.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/api-design/room-rest-api.md docs/specs/api-design/INDEX.md docs/requirements/game-rooms.md
git commit -m "docs(specs): the room REST API (IR-13)"
```

---

## Task 5: Profile owner bypasses their own privacy settings (IR-05)

**Files:**
- Modify: `docs/requirements/platform-views.md:294-306` (the `VW-PROF-*` table) and `:319-325`
  (the `VW-FREN-*` table)

Read literally — which is how a low-effort implementer reads a table — a user who sets their profile
to private sees *their own profile* rendered as "Profile is private". `user-accounts.md` FR-PROF-007
and `social-friends.md` FR-SOC-018 both assume an owner bypass; neither `platform-views.md` nor
`data-model-accounts.md`'s privacy-resolution schema states it.

- [ ] **Step 1: Add the rule above the `VW-PROF-*` table**

Insert immediately after the line `Profile content depends on the account type and privacy settings of
the viewed user (see user-accounts.md).`:

```markdown
**The owner is exempt from their own privacy settings.** Every visibility condition in the table below
is evaluated against the *viewer*, and when the viewer is the profile's owner it resolves to visible
regardless of the setting. A private profile is private to other people; it is not a way to hide your
own statistics from yourself, and VW-PROF-008's Edit Profile link would otherwise appear beside a
"Profile is private" message on the owner's own page. This restates `user-accounts.md` FR-PROF-007
and `social-friends.md` FR-SOC-018 at the point of use, because the tables read as complete without
it.
```

- [ ] **Step 2: Qualify the affected rows**

Change the `Condition` cell of VW-PROF-002, VW-PROF-002a, VW-PROF-002b and VW-PROF-002c from
`Public profile; <section> not hidden` to:

```
Viewer is the owner, or (public profile and <section> not hidden)
```

Change VW-PROF-003's condition from `Private registered profile` to
`Private registered profile, viewed by someone other than the owner`.

- [ ] **Step 3: Apply the same rule to the friends view**

Add below the `VW-FREN-*` table:

```markdown
The owner exemption above applies here too: `social-friends.md` FR-SOC-018 hides a friends list from
others, never from its owner. `/friends` is a self-scoped route — there is no viewer who is not the
owner — so the exemption is trivially satisfied, and it is stated so that a future "view a friend's
friends" feature does not inherit the wrong default.
```

- [ ] **Step 4: Verify**

Run: `grep -n "owner is exempt\|Viewer is the owner\|other than the owner" docs/requirements/platform-views.md`
Expected: at least six hits — the rule, four conditions, VW-PROF-003.

- [ ] **Step 5: Commit**

```bash
git add docs/requirements/platform-views.md
git commit -m "docs(requirements): profile owner bypasses their own privacy settings (IR-05)"
```

---

## Tasks 6–12: the M2 correctness pass

Tasks 6 through 12 are all edits to `room-lifecycle.md` and its immediate neighbours. **Execute them
as one continuous pass, in order, by one worker.** They interlock: Task 9's predicate change is what
makes Task 11's deferred closure work, and Task 11 depends on Task 10's fence being in place. Splitting
them across workers means each re-derives the ownership model from scratch and the second one
contradicts the first.

Before starting, read `room-lifecycle.md` end to end and `docs/decisions/0008`, `0009`, `0010`.

---

## Task 6: Lobby grace expiry must not write an outbox row (IR-06)

**Files:**
- Modify: `docs/specs/platform/room-lifecycle.md:392-395` (§3.3 in-transaction side effects)

`game_input_outbox.session_id` is `NOT NULL`. A Lobby room has `active_session_id = NULL`, which §3.4
states out loud. §3.3 step 2 inserts the row unconditionally. §3.3 step 4 carries a carefully reasoned
Lobby exemption; **step 2 does not.** The transaction aborts, the reservation is never resolved, and
the 5-second sweep retries it forever.

- [ ] **Step 1: Make step 2 conditional**

Replace step 2 of the in-transaction list:

```markdown
2. Insert the `player_left` row into `game_input_outbox` — **only if `room.active_session_id IS NOT
   NULL`.** A Lobby room has no session (§3.4), and `game_input_outbox.session_id` is `NOT NULL`
   (`data-model.md` §4.2), so an unconditional insert aborts the whole transaction on a room whose
   reservation §1.4 step 4 opened precisely because FR-DC-007 required it. The reservation would then
   never resolve and the 5-second sweep would retry it indefinitely — a stuck room and an error loop,
   from the one path that is guaranteed to run on every rolling deploy.
```

- [ ] **Step 2: Make the symmetry explicit**

Append to the "**A `LOBBY` room is deliberately exempt from step 4**" paragraph at `:409`:

```markdown
**Step 2 carries the same exemption, for a different reason.** Step 4's is a requirements argument —
FR-HDISC-003 is scoped to In Progress. Step 2's is a schema constraint: there is no `session_id` to
write. Both exemptions have the same trigger (`active_session_id IS NULL`) and must be kept together;
the two were separated once and the result was a transaction that could never commit.
```

- [ ] **Step 3: Verify**

Run: `grep -n "active_session_id IS NOT NULL" docs/specs/platform/room-lifecycle.md`
Expected: at least one hit inside §3.3's numbered list.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/platform/room-lifecycle.md
git commit -m "docs(specs): exempt Lobby rooms from the grace-expiry outbox insert (IR-06)"
```

---

## Task 7: Graceful drain must not re-trigger the FR-DC-007 cascade (IR-07)

**Files:**
- Modify: `docs/specs/platform/room-lifecycle.md:225-245` (§1.6) and `:166-178` (§1.5 layer 3)

§1.6 step 4 sends `RECONNECT_REQUIRED` as a STOMP `ERROR` frame, which closes the connection. Closing
a socket fires the ordinary disconnect handler. In a Lobby room, `reconnection-flow.md` FR-DC-002
makes a disconnect an immediate leave; chained with FR-XFER-002, **a rolling deploy deletes every
Lobby room on the platform** — the exact failure FR-DC-007's carve-out exists to stop, arriving by a
path the carve-out does not cover. Self-eviction (§1.5 layer 3) closes sockets the same way.

- [ ] **Step 1: Add the suppression rule to §1.6**

Insert a new paragraph immediately before step 1 of §1.6's numbered list:

```markdown
**Every socket this sequence closes is marked instance-initiated, and the disconnect handler must
skip such closures entirely.** Closing a socket fires `SessionDisconnectEvent` exactly as a network
drop does, and in a Lobby room `../../requirements/reconnection-flow.md` FR-DC-002 makes a disconnect
an immediate leave. Chained with `../../requirements/game-rooms.md` FR-XFER-002 — close a room whose
host has left with no humans remaining — an unsuppressed drain closes every Lobby room on the
instance, which is precisely the cascade FR-DC-007 exists to prevent, reached by a route its wording
does not cover. FR-DC-006/007 classify owner-instance loss as a mass event in *every* room state; a
drain is the graceful form of the same event and inherits the same classification.

Mechanically: the drain tags the STOMP session before closing it, and the disconnect handler returns
early on a tagged session without decrementing `connection_count`, without opening a reservation and
without evaluating FR-XFER-002. The participants' `connection_count` is instead zeroed by the *next*
owner during adoption (§1.4 step 5), which is the actor that can also open the reservations FR-DC-007
does permit.
```

- [ ] **Step 2: Apply the same rule to self-eviction**

Append to §1.5 layer 3, after `close those sockets with `RECONNECT_REQUIRED``:

```markdown
Those closes are instance-initiated in the sense of §1.6 and are suppressed identically. Self-eviction
is the ungraceful sibling of a drain: the instance has lost its lease and is severing sockets it may
no longer serve, not observing players leaving.
```

- [ ] **Step 3: Verify**

Run: `grep -n "instance-initiated" docs/specs/platform/room-lifecycle.md`
Expected: at least three hits — §1.6's rule, its mechanical restatement, §1.5 layer 3.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/platform/room-lifecycle.md
git commit -m "docs(specs): suppress the disconnect handler on drain and self-eviction (IR-07)"
```

---

## Task 8: Chat must not consume the room version (IR-08)

**Files:**
- Modify: `docs/specs/api-design/room-chat-websocket.md:27-33` (Message Envelope and Versioning)
- Modify: `docs/specs/api-design/room-websocket.md:119` (the event-catalogue preamble)

Chat messages advance the shared room `version`, but chat rides `/topic/room.{roomId}.chat` and
`/topic/room.{roomId}.team.{teamId}` — and `room-websocket.md:119` already states spectators receive
neither. Clients gap-detect on `version`. **Every spectator gaps on every chat message, and every
off-team player gaps on every team message.** One team chat message in a room with spectators produces
a resync storm, and a resync is `websocket.md` OQ-001's known hotspot.

- [ ] **Step 1: Replace the versioning section**

Replace the whole of `room-chat-websocket.md`'s *Message Envelope and Versioning* section body:

```markdown
Chat events use the `{ "type", "version", "payload" }` envelope shape of the room lobby stream
(defined in [room-websocket.md](room-websocket.md)), but **`version` is always `null` on a chat event
and chat never advances the room version counter.**

This is not an inconsistency to be tidied away. The room `version` is a gap-detection sequence: a
client that receives version *n+2* having last seen *n* knows it missed something and requests a
snapshot. That only works if every subscriber to the sequence receives every member of it. Chat does
not satisfy that: `/topic/room.{roomId}.chat` excludes spectators and
`/topic/room.{roomId}.team.{teamId}` reaches one team. If a chat message consumed a version, every
spectator would observe a permanent gap on every message sent in the room, and every off-team player
on every team message — each one triggering a `REQUEST_ROOM_STATE`, which is the most expensive
command in the protocol. An ordinary conversation in a spectated room would be a self-inflicted
resync storm.

**Chat needs no sequence of its own.** It has no ordering requirement against lobby events, no gap
semantics — FR-MSG-006 delivers once with no retry and no replay, so a missed message is *defined* as
lost rather than as a gap to repair — and `messageId` already handles duplicates. A second counter
would be state to maintain in service of a repair that must never happen.

Clients must therefore ignore `version` on `CHAT_MESSAGE` and must not update `localVersion` from it.
```

- [ ] **Step 2: Set the field to null in the example**

In the `CHAT_MESSAGE` example JSON, change `"version": 62,` to `"version": null,` and add a row to the
field table:

```markdown
| `version` | Always `null`. Chat does not participate in room version sequencing — see *Message Envelope and Versioning*. |
```

- [ ] **Step 3: State it from the room-websocket side**

Append to `room-websocket.md:119`:

```markdown
Chat events carry `version: null` and do **not** advance the counter, because their topics reach a
subset of this topic's subscribers and a partially-delivered sequence cannot be gap-detected — see
[room-chat-websocket.md](room-chat-websocket.md).
```

- [ ] **Step 4: Verify**

Run: `grep -n "version" docs/specs/api-design/room-chat-websocket.md`
Expected: no surviving claim that the counter is shared. Specifically,
`grep -c "shared with the room lobby event stream" docs/specs/api-design/room-chat-websocket.md`
returns `0`.

- [ ] **Step 5: Commit**

```bash
git add docs/specs/api-design/room-chat-websocket.md docs/specs/api-design/room-websocket.md
git commit -m "docs(specs): chat no longer consumes the room version (IR-08)"
```

---

## Task 9: Narrow deadline-sweep duty 2 (IR-09)

**Files:**
- Modify: `docs/specs/platform/room-lifecycle.md:557-560` (§5.1 duty 2) and §3.2 (`:356-380`)
- Modify: `docs/specs/platform/data-model.md:180-183` (the participant index) and `:218-224`
  (`lost_announced_at`)

Duty 2's predicate is `left_at IS NOT NULL AND lost_announced_at IS NULL`. Nothing sets
`lost_announced_at` on the paths that announce inline, so **every voluntary leave, host kick and room
closure matches it** — drawing a phantom `PLAYER_LOST` broadcast and a spurious closure evaluation one
sweep interval after the real event already handled it.

**Fix both halves.** Narrowing the predicate alone leaves `lost_announced_at` meaning something other
than its name, which is how the defect arose. Making every inline path stamp it alone relies on each
writer remembering. Do both: the column becomes honest, and the predicate stops depending on a
convention.

- [ ] **Step 1: Make §3.2's single statement stamp the column**

In §3.2, add `lost_announced_at` to the `SET` clause of the resolve statement:

```sql
UPDATE room_participant
   SET left_at = now(), leave_reason = :reason,
       grace_reservation_id = NULL, grace_expires_at = NULL,
       lost_announced_at = CASE WHEN :announceInline THEN now() ELSE NULL END
 WHERE room_id = :roomId AND user_id = :userId
   AND grace_reservation_id = :reservationId
   AND left_at IS NULL
   AND (:dueCheck = false OR grace_expires_at <= now())
RETURNING team_id;
```

and add a bullet to the "Every predicate earns its place" list:

```markdown
- **`lost_announced_at`** — set to `now()` when the resolving instance owns the room and will
  broadcast immediately, and left null when it does not, which is the *only* thing that marks a
  resolution as owing a deferred tail (§5.1 duty 2). `:announceInline` is `true` exactly when the
  claim of §3.3 returned `1` or `2`. Every other path that sets `left_at` — voluntary leave, kick,
  closure, account deletion on the owning instance — must stamp it too, for the same reason: an
  unstamped release is a promise that somebody will announce it.
```

- [ ] **Step 2: Narrow duty 2's predicate**

Replace duty 2 in §5.1:

```markdown
2. **Deferred tails** — resolutions committed by a foreign instance, identified by
   `left_at IS NOT NULL AND lost_announced_at IS NULL AND leave_reason IN ('GRACE_EXPIRED',
   'EARLY_RELEASE', 'LEFT')` on a room this instance owns: bump version → broadcast `PLAYER_LOST` →
   set `lost_announced_at` → **evaluate closure**. The closure evaluation is the load-bearing half;
   omitting it strands rooms whose last human left from another instance.

   **Both halves of the predicate are required and neither is redundant.** `lost_announced_at IS NULL`
   is the primary test and is now written by every inline path (§3.2), so a resolution that was
   already announced cannot match. The `leave_reason` list is the backstop: it is the set of reasons a
   *foreign* instance can produce, and it excludes `KICKED`, `ROOM_CLOSED` and `GAME_ENDED`, which are
   only ever produced by the owner under the room lock and can never legitimately owe a tail. Without
   the backstop, one path that forgets to stamp the column resurrects the defect as a phantom
   `PLAYER_LOST` for every ordinary leave, one sweep interval late — visible to players, and easy to
   read as a reconnection bug rather than a sweep bug.
```

- [ ] **Step 3: Add the supporting index**

The only participant index is partial on the *opposite* predicate
(`grace_expires_at IS NOT NULL AND left_at IS NULL`), so duty 2 has no index at all. Add to
`data-model.md` §2, after `room_participant_grace_due_idx`:

```sql
CREATE INDEX room_participant_unannounced_idx
  ON room_participant (room_id)
  WHERE left_at IS NOT NULL AND lost_announced_at IS NULL;
```

and to §5's index rationale:

```markdown
- `room_participant_unannounced_idx` spans only released participants whose departure has not been
  announced — the deferred tails of `room-lifecycle.md` §5.1 duty 2. Its steady-state size is zero,
  because the sweep's success is what removes a row from it. It is partial on the *opposite*
  predicate to `room_participant_grace_due_idx`, and both are needed: the 5-second sweep runs two
  queries per tick and neither would otherwise have an index.
```

- [ ] **Step 4: Update the `lost_announced_at` narrative**

Append to `data-model.md:218-224`:

```markdown
It is written by **every** path that sets `left_at`, not only by grace expiry: `now()` when the acting
instance owns the room and broadcasts immediately, null when it does not. A null value is therefore
the assertion "this departure is owed an announcement", and `room_participant_unannounced_idx` (§5)
is the index that makes finding those cheap. The sweep duty that consumes it is narrowed on
`leave_reason` as well, as a backstop against a writer that forgets — see `room-lifecycle.md` §5.1.
```

- [ ] **Step 5: Verify**

Run: `grep -n "lost_announced_at" docs/specs/platform/room-lifecycle.md docs/specs/platform/data-model.md`
Expected: hits in §3.2's `SET` clause, §3.2's predicate list, §5.1 duty 2, the new index, §5's
rationale, and the §2 narrative.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/platform/room-lifecycle.md docs/specs/platform/data-model.md
git commit -m "docs(specs): narrow deferred-tail detection to genuinely unannounced departures (IR-09)"
```

---

## Task 10: `detachSession` must bump the version and carry the epoch fence (IR-10)

**Files:**
- Modify: `docs/specs/platform/room-lifecycle.md:473-493` (§4's pseudocode) and the prose below it

§1.5 states that **every** mutation of the `room` row carries the epoch fence and bumps the version.
§4's transaction does neither, and it is the mutation that sets `state = 'CLOSED'` — the single most
important state change a client can observe. This is the ADR-0008 defect class the epoch was
introduced to close.

- [ ] **Step 1: Fence and version step 3**

Replace steps 1–3 of the `detachSession` pseudocode:

```
  TX — Postgres only. No gRPC, no Redis, no remote call of any kind.
    1. SELECT ... FROM room WHERE room_id = :roomId FOR UPDATE
    2. if room.active_session_id <> :sessionId: COMMIT; return    -- already detached, idempotent
    3. UPDATE room
          SET state = :nextState, active_session_id = NULL,
              version = :expected + 1,
              closed_at = CASE WHEN :nextState = 'CLOSED' THEN now() END,
              closed_reason = CASE WHEN :nextState = 'CLOSED' THEN :reason END
        WHERE room_id = :roomId AND version = :expected AND owner_epoch = :myEpoch;
       -- zero rows ⇒ a later tenure owns this room: abort the transaction,
       --   publish nothing, self-evict (§1.5 layer 4). Do NOT retry in place.
       release slots / clear reservations / reset readiness per the path
```

- [ ] **Step 2: State why, below the block**

Insert after the pseudocode, before "**The gRPC call is never inside the transaction.**":

```markdown
**Step 3 is a fenced, version-bumping mutation like every other write to the `room` row**, and it was
once neither. §1.5's rule is "every mutation of the `room` row", with exactly one carve-out —
resolving a reservation, which touches `room_participant` only. Closure is not that carve-out: it
writes `state`, `active_session_id`, `closed_at` and `closed_reason`.

Both halves matter and they fail differently. Without the **epoch fence**, a stale owner can close a
room under the legitimate owner — the precise scenario ADR-0008 introduced the epoch for, and worse
here than elsewhere because closure is irreversible. Without the **version bump**, clients receive a
`ROOM_CLOSED` at a version they have already applied and discard it silently (`room-websocket.md`
Client Reconciliation drops `delta.version <= localVersion`), so the room vanishes server-side while
every attached client still renders it as live.

Step 0's claim is what supplies `:myEpoch`, and the `FOR UPDATE` of step 1 is what supplies
`:expected` — closure is the one mutation that may read the version inside the transaction, because
its caller may be an instance that has just adopted the room and has no in-memory counter yet. That is
safe here and nowhere else: the epoch, not the version, is doing the fencing, and the row lock is
already held.
```

- [ ] **Step 3: Verify**

Run: `grep -n "owner_epoch = :myEpoch" docs/specs/platform/room-lifecycle.md`
Expected: at least three hits — §1.5 layer 4, §1.4's adoption guard variant, and now §4 step 3.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/platform/room-lifecycle.md
git commit -m "docs(specs): fence and version-bump the detachSession mutation (IR-10)"
```

---

## Task 11: Name the owed-closure mechanism, and make both documents agree (IR-11)

**Files:**
- Modify: `docs/specs/platform/room-lifecycle.md:465-476` (§4's step 0 and the prose above it)
- Modify: `docs/specs/platform/data-model-accounts.md:379-424` (§5's erasure table and narrative)

§4 says a caller that cannot claim the room "records the closure as owed" and names **no table, no
column and no sweep duty that consumes it**. `data-model-accounts.md` §5 describes the same closure as
happening synchronously inside the erasure transaction. Both cannot be built.

**Decision: no new table.** The mechanism already exists — §5.1 duty 2's deferred tail, which Task 9
just made honest. A foreign instance commits the participant departure with `lost_announced_at` null;
the owning instance's next 5-second tick announces it *and evaluates closure*. Adding a
`room_closure_owed` table would be a second durable to-do with the same semantics as one that already
works, and ADR-0010's lesson is about keying such tables correctly, not about minting more of them.

**Do Task 9 before this task.** This design depends on duty 2's predicate being correct.

- [ ] **Step 1: Replace §4 step 0 and its justifying paragraph**

Replace the paragraph beginning "**The detaching actor must hold the room claim**" through step 0 of
the pseudocode:

```markdown
**The detaching actor must hold the room claim before it commits or broadcasts.** Two of the five
callers arrive on threads that own nothing: account deletion is a REST call landing on an arbitrary
instance, and guest-account cleanup (FR-JOB-001) is a scheduled job. Under ADR-0002 there is no
cross-instance fan-out, so a non-owner's `ROOM_CLOSED` reaches **nobody** — and the audience is real,
because closure evicts spectators, who are connected at that moment and are not counted by the
"no human player remains" test.

**A caller that cannot claim the room defers through the existing deferred-tail mechanism, not
through a table of its own.** It commits the durable half — the participant departures, with
`lost_announced_at` left null per §3.2 — and returns. The owning instance's next deadline-sweep tick
picks the room up under §5.1 duty 2, which broadcasts and **evaluates closure** while holding the
claim. There is no `room_closure_owed` table and no third durable work table: duty 2 already does
exactly this job for grace expiries resolved by a foreign instance, and a closure owed by an account
deletion is the same shape of debt. This makes REST- and job-initiated closure asynchronous, bounded
by one sweep interval, which is the correct trade — a spectator silently stranded in a subscription to
a dead room has nothing to repair it.

**Duty 2's closure evaluation must therefore cover the Lobby host-departure case, not only
FR-HDISC-003.** When the departed participant was `room.host_user_id`, the tail additionally applies
FR-XFER-001's transfer if another human is connected, and closes with `NO_PLAYERS_REMAINING` if none
is — in **Lobby as well as In Progress**, because `game-rooms.md` FR-XFER-002 scopes immediate closure
to explicit departures in any state and account deletion is named there as one. The `GRACE_EXPIRED_NO_HUMAN`
path (§3.3 step 4) stays In-Progress-only and stays distinct; the two produce different
`closed_reason` values because they mean different things to a player.
```

Then replace step 0 of the pseudocode:

```
  0. Claim the room (§1.2). On redirect (result 0), commit the participant departures with
     lost_announced_at NULL and return — §5.1 duty 2 on the owning instance performs the
     announcement and the closure evaluation. Never commit the room-row mutation or broadcast
     without the claim.
```

- [ ] **Step 2: Extend duty 2 in §5.1 to cover host departure**

Append to §5.1 duty 2 (as rewritten in Task 9):

```markdown
   The tail also carries the **host disposition**. If the departed participant was
   `room.host_user_id`, apply FR-XFER-001's transfer to the next human by join order when one is
   connected, and close the room with `NO_PLAYERS_REMAINING` when none is — in Lobby as well as In
   Progress. This is the path that makes account deletion (`data-model-accounts.md` §5) and guest
   cleanup work from a non-owning instance, and without it a deleted host's room keeps a
   `host_user_id` naming a released participant, which is the dangling reference `data-model.md` §1
   makes the column nullable to avoid.
```

- [ ] **Step 3: Correct `data-model-accounts.md` §5**

Change the `room` row of the erasure table (`:395`) to:

```markdown
| `room` | rooms hosted with no other human remaining are **owed** a closure with `closed_reason = 'ACCOUNT_DELETED'`; otherwise a host transfer is owed. Neither happens in this transaction — see below | FR-XFER-002, FR-LIFE-004 |
```

and replace the `room_participant` / `room` bullet at `:415-420`:

```markdown
- **`room_participant` and `room`.** The erasure transaction writes the *durable* half only: each
  non-closed room the user occupies gets `left_at = now()`, `leave_reason = 'LEFT'` and
  `lost_announced_at = NULL`. It does **not** close rooms, transfer hosts or broadcast, because it
  runs on whichever instance received the REST call and that instance almost certainly does not own
  those rooms — under ADR-0002 a non-owner's `ROOM_CLOSED` reaches nobody. The owning instance's next
  deadline-sweep tick (`room-lifecycle.md` §5.1 duty 2) performs the announcement, the FR-XFER-001
  transfer and the FR-XFER-002 closure, under the claim. `data-model.md`'s
  `closed_reason = 'ACCOUNT_DELETED'` therefore still has account deletion as its only producer; what
  changed is *which actor* writes it, and when. The bound is one sweep interval.
```

- [ ] **Step 4: Reconcile the "one transaction" claim**

Replace the paragraph at `:422-424` ("The erasure is one transaction…"):

```markdown
The erasure is one transaction, and the room work inside it is now only the participant departures —
a conditional update per room, which cannot fail on lock contention the way a closure could. It is
still ordered **last** so that a retry re-runs only the idempotent operations above it: each is a
conditional update or a delete whose second execution matches zero rows. The closure and host-transfer
work that used to sit here is deliberately outside the transaction, deferred to the room's owner; a
retry of the erasure re-commits the same participant rows and produces no second tail, because
`left_at IS NULL` no longer holds.
```

- [ ] **Step 5: Verify the two documents agree**

Run:

```bash
grep -n "recorded as owed\|records the closure as owed\|room_closure_owed" docs/specs/platform/room-lifecycle.md
grep -n "deferred-tail\|duty 2\|lost_announced_at" docs/specs/platform/data-model-accounts.md
```

Expected: the first returns **no output** (the unnamed mechanism is gone); the second returns hits
(the accounts document now names the mechanism that performs its closures).

- [ ] **Step 6: Commit**

```bash
git add docs/specs/platform/room-lifecycle.md docs/specs/platform/data-model-accounts.md
git commit -m "docs(specs): owed closure rides the deferred-tail mechanism (IR-11)"
```

---

## Task 12: Declare the v1 behaviour of the AI surface (IR-12)

**Files:**
- Modify: `docs/specs/api-design/room-websocket.md` — `:151-158` (`aiPlayers`), `:186`, `:566`
  (`ADD_AI_PLAYER`), `:669` (`AI_NOT_SUPPORTED`)
- Modify: `docs/specs/platform/room-lifecycle.md:402-405` (§3.3 step 4)
- Modify: `docs/specs/platform/data-model.md` §6 (*What is deliberately absent*)
- Modify: `docs/requirements/game-rooms.md` — FR-HOST-003, FR-TEAM-008

`room_participant` is keyed `(room_id, user_id)` with `user_id NOT NULL REFERENCES app_user`, so an AI
cannot be a row. Meanwhile `platform-architecture.md:256` already defers the AI execution environment,
so no v1 game can drive an AI turn. **Decision: keep the wire protocol, defer the schema, and declare
what the surface does in v1** so it is implementable today.

- [ ] **Step 1: Declare the v1 state of `aiPlayers`**

Append to `room-websocket.md:186`'s paragraph:

```markdown
**`aiPlayers` is always empty in v1.** The AI player interface is deferred (`game-contracts.md`
OQ-002) and the AI execution environment with it (`platform-architecture.md` *Out of Scope*), so no v1
game declares `capabilities.ai` and no AI can be seated. The field is present rather than removed
because its shape is settled and removing it would be a breaking change to add back; a client must
render an empty array as "no AI players", never as an error.
```

- [ ] **Step 2: Make `ADD_AI_PLAYER`'s v1 behaviour unambiguous**

Change the `ADD_AI_PLAYER` precondition cell at `:566` to:

```
Lobby; game supports AI players (FR-HOST-003); target team has an available slot. **In v1 this always fails with `AI_NOT_SUPPORTED`** — see below
```

and add below the command table:

```markdown
**`ADD_AI_PLAYER` is specified but unreachable in v1.** The handler is implemented and returns
`AI_NOT_SUPPORTED` unconditionally, because no v1 game may declare `capabilities.ai` — bundle
validation rejects a manifest that sets it while `game-contracts.md` OQ-002 is open
(`../manifest/bundle-format.md`). Implementing the rejection rather than omitting the command keeps
the error catalogue honest and gives the frontend a defined response to a button it may still render
disabled.
```

- [ ] **Step 3: Simplify the closure predicate and say why**

In `room-lifecycle.md` §3.3 step 4, replace `If no participant remains with `left_at IS NULL AND role
= 'PLAYER'` that is not an AI` with:

```markdown
If no participant remains with `left_at IS NULL AND role = 'PLAYER'`
```

and add after step 4:

```markdown
**The predicate has no "and not an AI" clause, and in v1 it needs none.** `room_participant` holds
humans only — an AI has no `app_user` row and the table's primary key is `(room_id, user_id)` — and
`aiPlayers` is always empty (`../api-design/room-websocket.md`). When the AI interface lands
(`game-contracts.md` OQ-002) it must add both a representation *and* this clause; the OQ is recorded
as owing that pair rather than only the interface, because the closure question — does a room of AI
players survive the last human? — is decided here and not there.
```

- [ ] **Step 4: Record the absence in the schema document**

Add a bullet to `data-model.md` §6:

```markdown
- **No AI participant representation.** `room_participant` is keyed `(room_id, user_id)` against
  `app_user`, so it models humans only. The wire protocol carries an `aiPlayers` array
  (`../api-design/room-websocket.md`) that is always empty in v1, because the AI player interface and
  its execution environment are both deferred (`game-contracts.md` OQ-002,
  `platform-architecture.md` *Out of Scope*). Adding AI later is a new table rather than a column: a
  synthetic `app_user` row per AI would put bots into friend search, statistics and the guest purge.
  That is a design note, not a decision made here.
```

- [ ] **Step 5: Mark the requirements deferred in place**

Append to the description cells of `game-rooms.md` FR-HOST-003 and FR-TEAM-008:

```
**Deferred to post-MVP** with the AI player interface (`game-contracts.md` OQ-002); no v1 game declares AI support.
```

- [ ] **Step 6: Correct the OQ-002 mislabelling**

This is the one mislabelled deferral in the corpus. In `docs/requirements/game-contracts.md`, append
to OQ-002:

```markdown
**This OQ owes more than an interface.** Two shipped mechanisms already reference the representation
it postpones: `room-websocket.md`'s `aiPlayers` array and the room-closure predicate in
`room-lifecycle.md` §3.3. Both are given defined v1 behaviour (empty array; no AI clause) rather than
left ambiguous, but resolving this OQ must deliver a schema representation and a closure rule
alongside the interface, not the interface alone.
```

- [ ] **Step 7: Verify**

Run: `grep -n "that is not an AI" docs/specs/platform/room-lifecycle.md`
Expected: **no output.** Then
`grep -c "always empty in v1\|AI_NOT_SUPPORTED" docs/specs/api-design/room-websocket.md` returns at
least `3`.

- [ ] **Step 8: Commit**

```bash
git add docs/specs/api-design/room-websocket.md docs/specs/platform/room-lifecycle.md \
        docs/specs/platform/data-model.md docs/requirements/game-rooms.md \
        docs/requirements/game-contracts.md
git commit -m "docs(specs): declare the v1 behaviour of the AI surface (IR-12)"
```

---

## Task 13: Propagate the async validation error contract (IR-18)

**Files:**
- Modify: `docs/specs/manifest/manifest-schema.md:192-215` (*Error model*)
- Modify: `docs/specs/api-design/file-uploads.md:154-156`
- Modify: `docs/specs/flows/08-upload-to-play.md:47-49,55-56`

`bundle-format.md` §3.4 is the authority and resolves this correctly: manifest validation needs the
bundle bytes, so it runs after `confirm` has already returned `202`, and failures surface as the
version resource's `FAILED` state via `GET .../versions/{uploadId}` — never as a `422`. Three
documents still describe a synchronous `422`, including **the document that owns manifest
validation**. `file-uploads.md:156` contradicts its own error table three lines above. Found
independently by two agents.

**Sharpest detail worth preserving:** `manifest/INDEX.md`'s key-decisions list states the *correct*
model, so following the corpus's own "read the INDEX first" rule does not save an implementer — the
document the index points at is wrong in its body.

- [ ] **Step 1: Rewrite `manifest-schema.md`'s error model**

Replace the *Error model* section body (keeping the `check`-identifier paragraph and both JSON
examples, which are correct):

```markdown
Fatal validation failures use the `{ "check": <id>, "message": <human-readable> }` entry shape defined
in [`api-design/error-handling.md`](../api-design/error-handling.md). **How they are delivered depends
on when they are detected, and manifest validation is almost always the late case.**

- **Phase A — the slot request.** `POST /api/games/{gameId}/versions` validates what it can from the
  declared metadata alone. Those failures are a synchronous `422 business-rule-violation` whose
  `instance` names that path.
- **Phases B–G — everything that needs the bundle bytes, which is all manifest validation.** The
  manifest lives *inside* the uploaded archive, so it cannot be read until after `confirm`, which has
  already returned `202 Accepted`. These failures are **not an HTTP error at all**: they are the state
  of a resource that was successfully created. `GET /api/games/{gameId}/versions/{uploadId}` returns
  `200` with `status: "FAILED"` and the `errors` and `warnings` arrays below.

The full phase model and the reasoning are in
[`bundle-format.md`](bundle-format.md) §3.4, which is authoritative; this section states the
consequence for manifest checks specifically. All Layer 1 and Layer 2 failures are still reported
together in one array (FR-UPLOAD-008) — one report format, two carriers.

**Do not return a `422` from the `GET`.** The request was fine and the resource was found; a client
that treats 4xx as "retry the request differently" will loop.
```

Then change the JSON example's framing: the block currently shown as a `422` Problem Detail is correct
only for Phase A. Add above it: `A Phase A failure — synchronous, on the slot request:` and add after
it a second block labelled `A manifest failure — the version resource, fetched after the 202:` reusing
the `FAILED` resource shape from `bundle-format.md` §3.4.

- [ ] **Step 2: Fix `file-uploads.md`'s self-contradiction**

Line 154 already says the async case correctly (`Version → FAILED; structured errors in GET
response`). Line 156 then says all validation errors follow the bundle-validation error format.
Replace line 156:

```markdown
Phase A failures follow the bundle validation error format in
[error-handling.md](error-handling.md) as a synchronous `422`. Everything detected after `confirm` has
returned `202` — which is all manifest and bundle-content validation — is reported as the version
resource's `FAILED` state and its `errors` array, never as a `422`. See
[bundle-format.md](../manifest/bundle-format.md) §3.4.
```

- [ ] **Step 3: Remove flow 08's double claim**

Flow 08 §C currently asserts both `202` and a synchronous `422` for the same request. Replace the
paragraph at `:53-56`:

```markdown
`status='PROCESSING'`. Every check runs and **all failures are reported together** (`FR-UPLOAD-008`)
as a `{check, message}` array — a developer should not fix one error per round trip. The array is
**not** delivered as a `422`: `confirm` returned `202` minutes earlier and the HTTP exchange is over.
It is read from `GET /api/games/{gameId}/versions/{uploadId}`, which returns `200` with
`status: "FAILED"` (`../manifest/bundle-format.md` §3.4), or pushed as a
`BUNDLE_VALIDATION_COMPLETE` SSE notification.
```

- [ ] **Step 4: Verify**

Run:

```bash
grep -n "422" docs/specs/manifest/manifest-schema.md docs/specs/api-design/file-uploads.md \
                docs/specs/flows/08-upload-to-play.md
```

Expected: every surviving `422` is explicitly scoped to Phase A, the slot request, or the size check
at confirm. No `422` remains attached to manifest or bundle-content validation.

- [ ] **Step 5: Commit**

```bash
git add docs/specs/manifest/manifest-schema.md docs/specs/api-design/file-uploads.md \
        docs/specs/flows/08-upload-to-play.md
git commit -m "docs(specs): propagate the async validation error contract (IR-18)"
```

---

## Task 14: Add the expiry purge job (IR-20)

**Files:**
- Modify: `docs/requirements/platform-operations.md` — *Scheduled Jobs* table
- Modify: `docs/specs/deployment/local-environment.md` §7.2 — the interval key

Two schema documents assert that "the purge job" deletes expired `friend_request` and
`room_invitation` rows, and the notification design **depends** on it: `notification_purge_idx` is
partial and deliberately excludes actionable notifications from the generic sweep, on the
understanding that deleting the subject cascades the notification away. `FR-JOB-001…012` contains no
such job. Nothing scans `friend_request_expiry_idx` or `room_invitation_expiry_idx`.

This is a **regression of the bug session 9 believed it had fixed**: adding `expires_at` made expiry
expressible; nothing acts on it. It is the "a rule whose supporting state has no actor" pattern.

- [ ] **Step 1: Add FR-JOB-013**

Insert after FR-JOB-012 in the *Scheduled Jobs* table:

```markdown
| FR-JOB-013 | Expired request and invitation purge | A scheduled job permanently deletes `friend_request` and `room_invitation` rows whose `expires_at` has passed, scanning `friend_request_expiry_idx` and `room_invitation_expiry_idx` (`../specs/platform/data-model-social.md`, `../specs/platform/data-model-notifications.md`). Deleting the subject row cascades its actionable notification away, which is **the only mechanism that ever removes one**: `notification_purge_idx` is partial and deliberately excludes actionable notifications from FR-JOB-002's generic sweep, so without this job an invitation nobody acts on is retained forever and so is its notification. Default interval: once per hour; configurable. Executes on exactly one instance per interval per FR-JOB-005. | Must |
```

- [ ] **Step 2: Add the interval key**

Insert into `local-environment.md` §7.2, after the `notification-purge` row:

```markdown
| `turnbase.jobs.expiry-purge.interval` | `1h` | `TURNBASE_JOBS_EXPIRY_PURGE_INTERVAL` | FR-JOB-013 |
```

- [ ] **Step 3: Point the two schema documents at the job by name**

In `data-model-social.md:152` and `data-model-notifications.md:199`, replace the bare phrase
"the purge job" with `` the expiry purge job (`platform-operations.md` FR-JOB-013) ``. A named
requirement is what turns an assumption into an actor.

- [ ] **Step 4: Verify**

Run: `grep -rn "FR-JOB-013" docs/`
Expected: at least four hits — the requirement, the config row, and both schema documents.

- [ ] **Step 5: Commit**

```bash
git add docs/requirements/platform-operations.md docs/specs/deployment/local-environment.md \
        docs/specs/platform/data-model-social.md docs/specs/platform/data-model-notifications.md
git commit -m "docs(requirements): add the expired request and invitation purge job (IR-20)"
```

---

## Task 15: Single writer for `session:{id}` (IR-14)

**Files:**
- Modify: `docs/specs/flows/02-room-to-game-start.md:113` (step 6)
- Modify: `docs/specs/game-host/game-host-internals.md` §9.1 (`CreateSession`)

Flow 02 step 6 has Orchestration "write the session record and routing keys to Redis". §9.1 step 1
treats the existence of `session:{id}` as `CreateSession`'s idempotency guard, and §13 names the Game
Host as the key's owner. **The guard fires on the first call, so `onInit` never runs.** The game starts
with no initial state and no initial effects.

§13 is already right. Flow 02 is the document that is wrong.

- [ ] **Step 1: Correct flow 02 step 6**

```markdown
| 6 | Monolith | Allocate `sessionId`; write the **Orchestration-owned** Redis keys — `routing:`, `queue:`, `seq:`, `delivered:`, `failcount:`. **Not** `session:{sessionId}` — that record is the Game Host's (`../game-host/game-host-internals.md` §13) and pre-writing it would satisfy `CreateSession`'s idempotency guard on the very first call, so `onInit` would never run | **Redis routing keys** |
```

- [ ] **Step 2: State the guard's precondition from the Game Host side**

Append to §9.1's `CreateSession` block, after step 4:

```markdown
Step 1's guard is only correct because **`session:{sessionId}` has exactly one writer, the Game Host**
(§13). Its presence means "onInit has already run and its effects are recorded", and nothing else may
create it. An Orchestration pre-write of the same key — plausible, since Orchestration allocates the
`sessionId` and writes every other key of the family — turns the idempotency guard into an
unconditional short-circuit: the first `CreateSession` returns an empty `lastEffects` with `OK`, the
handler never runs, and the game begins with no state and no opening effects. Flow 02 step 6 names the
keys Orchestration does write.
```

- [ ] **Step 3: Verify**

Run: `grep -n "session:{sessionId}\|session record" docs/specs/flows/02-room-to-game-start.md`
Expected: the only mention is the explicit statement that Orchestration does *not* write it.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/flows/02-room-to-game-start.md docs/specs/game-host/game-host-internals.md
git commit -m "docs(specs): single writer for the session record (IR-14)"
```

---

## Task 16: `lastAppliedSequence` on a failed input (IR-15)

**Files:**
- Modify: `docs/specs/game-host/game-host-internals.md` §8.1 (the session record) and §9.1
  (`ProcessInput` steps 1 and 6)

`orchestration-gamehost-protocol.md:271` says the sequence is burned and `lastAppliedSequence`
advances, so a redelivery replays the same failure. The internals document's session record has
**nowhere to store a failure**: §9.1 step 6 returns `FAILED` with "state unchanged". Implement the
protocol doc against this record and the replay path returns `OK` carrying the **previous** input's
effects — a silent wrong answer rather than a visible error.

The protocol document's semantics are right. The record needs a slot.

- [ ] **Step 1: Add the outcome to the session record in §8.1**

```jsonc
// Redis key: session:{sessionId}   (see §13 for the full key map)
{
  "contextKey":          { "gameId": "…", "gameVersion": "1.4.0" },
  "stateJson":           "…",     // opaque; the last successfully-applied state
  "lastAppliedSequence": 42,      // highest sequence *consumed* (CreateSession = 0)
  "lastOutcome":         "OK",    // "OK" | "FAILED" — the outcome at lastAppliedSequence
  "lastEffects":         [ … ],   // effects produced at lastAppliedSequence; [] when FAILED
  "lastFailure":         null     // the GameFailure at lastAppliedSequence; null when OK
}
```

and add to the bullet list below it:

```markdown
- **`lastOutcome` / `lastFailure` exist because a burned sequence must be replayable.**
  `../internal-grpc/orchestration-gamehost-protocol.md` advances `lastAppliedSequence` on a *failed*
  input — the sequence is consumed, and a redelivery must return the same failure rather than invoke a
  handler that has already run and thrown. Without a place to record the outcome, the replay branch
  (§9.1 step 1) would return `lastEffects` with `OK`, and those effects belong to the *previous*
  input. That is a silent wrong answer: the client is told an action succeeded and handed somebody
  else's effects. `lastAppliedSequence` is therefore the highest sequence **consumed**, not the
  highest successfully applied, and `lastOutcome` says which.
```

- [ ] **Step 2: Correct `ProcessInput` steps 1 and 6**

```
1. If input.sequence ≤ record.lastAppliedSequence → REPLAY:
     lastOutcome == OK     → return ProcessResult(sequence, OK, record.lastEffects)
     lastOutcome == FAILED → return ProcessResult(sequence, FAILED, record.lastFailure)
   Do NOT invoke the handler.                          ← at-most-once application
```

```
6. On failure: atomically write { stateJson unchanged, lastAppliedSequence = input.sequence,
   lastOutcome = FAILED, lastEffects = [], lastFailure = failure }; then return
   ProcessResult(sequence, FAILED, failure). The sequence is burned — the game state is
   unchanged, but the input has been consumed and must not be re-invoked on redelivery.
```

- [ ] **Step 3: Extend the atomicity requirement**

In §8.1's *Atomicity requirement* bullet, change the tuple from
`{stateJson, lastAppliedSequence, lastEffects}` to
`{stateJson, lastAppliedSequence, lastOutcome, lastEffects, lastFailure}`, and append:

```markdown
The failure path writes the same unit — it is not a partial update. A torn write that advanced the
sequence without recording the outcome produces exactly the GAME-B2 class of bug on the failure path
that the atomic record forbids on the success path.
```

- [ ] **Step 4: Cross-reference from the protocol document**

Append to the `Does lastAppliedSequence advance?` answer cell in
`orchestration-gamehost-protocol.md:271`:

```
The Game Host records the outcome alongside the sequence (`../game-host/game-host-internals.md` §8.1 `lastOutcome`/`lastFailure`) so the replay returns the same failure rather than the previous input's effects.
```

- [ ] **Step 5: Verify**

Run: `grep -n "lastOutcome\|lastFailure" docs/specs/game-host/game-host-internals.md docs/specs/internal-grpc/orchestration-gamehost-protocol.md`
Expected: hits in §8.1's record, its bullet, both `ProcessInput` steps, the atomicity bullet, and the
protocol document.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/game-host/game-host-internals.md docs/specs/internal-grpc/orchestration-gamehost-protocol.md
git commit -m "docs(specs): record the outcome at lastAppliedSequence (IR-15)"
```

---

## Task 17: Proto and prose must agree on sequence gaps (IR-16)

**Files:**
- Modify: `docs/specs/internal-grpc/gamehost.proto:39-40` (the `service GameHostService` comment) and
  the `ProcessInputRequest.sequence` field comment
- Modify: `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — one cross-reference

The proto comment instructs the Game Host to "reject out-of-order/duplicate sequences defensively".
The prose makes forward gaps a normal consequence of failure handling. **Codegen follows the proto and
humans follow the prose**, so the two readings land in different files of the same service. A
defensive implementer following the proto freezes every session after its first failed action.

- [ ] **Step 1: Correct the service comment**

Replace lines 39–40:

```proto
// Per-session ordering is enforced by the Orchestration Service's Redis-backed
// queue (FR-ROUTE-002), NOT by the transport. The Game Host deduplicates a
// sequence at or below its watermark by replaying the recorded outcome, and
// ACCEPTS forward gaps: a burned sequence from a failed input makes the stream
// sparse by design (see ProcessInputRequest.sequence).
```

- [ ] **Step 2: Correct the field comment**

On `ProcessInputRequest.sequence`, state all three cases explicitly so codegen readers get the whole
rule at the field:

```proto
  // Monotonic per-session sequence allocated by Orchestration.
  //   sequence <= lastAppliedSequence : replay. Return the recorded outcome
  //     (OK + lastEffects, or FAILED + lastFailure). Do NOT invoke the handler.
  //   sequence == lastAppliedSequence + 1 : the ordinary case.
  //   sequence >  lastAppliedSequence + 1 : a FORWARD GAP. Accept and process
  //     it. Gaps are normal — a failed input burns its sequence without
  //     advancing state, and the stream is deliberately sparse. Rejecting a
  //     gap freezes the session after its first failed action.
  // See orchestration-gamehost-protocol.md "What happens to the input that
  // failed" and game-host-internals.md §9.1.
```

- [ ] **Step 3: Point the prose at the proto**

Append to the `Is the `sequence` consumed?` answer cell:

```
The proto's `ProcessInputRequest.sequence` comment states all three cases, because a codegen reader never sees this table.
```

- [ ] **Step 4: Verify**

Run: `grep -n "defensively" docs/specs/internal-grpc/gamehost.proto`
Expected: **no output.**

- [ ] **Step 5: Commit**

```bash
git add docs/specs/internal-grpc/
git commit -m "docs(specs): proto and prose agree that forward sequence gaps are normal (IR-16)"
```

---

## Task 18: Validate effect addresses against session membership (IR-17)

**Files:**
- Modify: `docs/specs/api-design/websocket.md:249-261` (the `GAME_EVENT` section)
- Modify: `docs/requirements/game-contracts.md:169` (NFR-SEC-002)

`websocket.md:261` argues NFR-SEC-002 is "mechanically true rather than aspirational" because
`send_to_player` rides a per-user queue a client cannot subscribe to on another's behalf. **That
secures the subscription. It does not secure the address.** Nothing validates that
`SendToPlayerEffect.player_id`, which is chosen by game code, identifies a participant of the session
that produced it. Game code returns a `player_id` for a user in another room and Spring delivers it.

Under ADR-0006 the MVP's games are first-party, so this is not currently exploitable — **which is
exactly the problem.** It is a fail-open gated on the trust model, of the class GRMP lesson F5 names,
and the document asserts the property is mechanical.

- [ ] **Step 1: Replace the claim with the check that would make it true**

Replace the paragraph at `:261`:

```markdown
**Every effect address is validated against session membership at fan-out, before delivery.** An
effect's destination is chosen by *game code*, and game code is untrusted (ADR-0006 makes the MVP's
games first-party; the contract is written for the general case). Before dispatching:

| Effect | Check | On failure |
|---|---|---|
| `send_to_player` | `player_id` is a current participant of the session that produced the effect | Drop the effect; WARN with `session_id` and the offending id; increment `turnbase.effect.address_rejected.total{kind="player"}` |
| `send_to_team` | `team_id` is a team of that session | Drop the effect; WARN; increment with `kind="team"` |
| `broadcast` | none needed — the audience *is* the session | — |

The roster is already in memory: the session's participant and team sets are held for
`InitContext` construction, so this is a set membership test, not a query.

**The per-user queue is not the control, and reading it as one is the trap.** It is genuinely true
that a client cannot subscribe to another user's `/user/queue/game` — that secures the *subscription*.
It says nothing about the *address*: Spring resolves `/user/queue/game` from whatever principal the
server hands it, so a `player_id` naming a user in an entirely different room is delivered to that
user faithfully. NFR-SEC-002 holds because of the membership check above, not because of the queue's
addressing.

A rejected address is a defect in the game, not an attack in the MVP — but it is logged at WARN and
metered precisely so that it is visible before third-party games arrive, rather than discovered by
one.
```

- [ ] **Step 2: Soften the requirement to name its mechanism**

Append to NFR-SEC-002's description in `game-contracts.md`:

```markdown
Enforced by validating every effect address against the producing session's membership at fan-out
(`../specs/api-design/websocket.md` § `GAME_EVENT`), not by the addressing of the underlying
destination — a per-user queue prevents a client from *subscribing* to another user's messages, but
not a game from *addressing* one.
```

- [ ] **Step 3: Verify**

Run: `grep -n "mechanically true" docs/specs/api-design/websocket.md`
Expected: the phrase survives only in the rewritten form that attributes the property to the
membership check — or not at all. Either is acceptable; an unqualified "mechanically true" is not.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/api-design/websocket.md docs/requirements/game-contracts.md
git commit -m "docs(specs): validate effect addresses against session membership (IR-17)"
```

---

## Task 19: Specify info-document Markdown sanitization (IR-19)

**Files:**
- Modify: `docs/specs/api-design/input-validation.md:182-195` (*The one exception*)
- Modify: `docs/requirements/game-catalog.md` — add a "Related API Specifications" pointer

FR-GDET-004 requires the game detail page to render a developer-supplied Markdown info document. **No
library, no server-versus-client split and no allow-list is named anywhere.**
`input-validation.md:182-195` compounds it by asserting the game-log renderer is "the only surface
where the platform renders anything other than plain text", which is not true.

Unlike a game frontend, this surface renders on the **trusted platform origin**, which carries the
session cookie — and it is the one XSS sink whose content comes from an uploaded artifact.
`input-validation.md`'s platform-wide ESLint ban on `dangerouslySetInnerHTML` rules out the naive
implementation, so an implementer has **no sanctioned path at all.**

The finding is recorded as unowned. **Assign it to `input-validation.md`**, which already owns output
encoding and already owns the ban that blocks the naive path.

**Decision: render Markdown to React elements, client-side, with no HTML string anywhere.** This needs
no exception to the `dangerouslySetInnerHTML` ban, no server-side sanitized-HTML column, and no
re-sanitization when the allow-list changes. Server-side sanitize-at-ingest was considered and
rejected: it stores a second representation of the same artifact, and a fix to the allow-list then has
to be back-applied to every stored document.

- [ ] **Step 1: Retitle and extend the section**

Change the heading `### The one exception: game log entries` to
`### Two rendered surfaces, and neither uses an HTML string`, and replace the sentence
`This is **the only surface where the platform renders anything other than plain text**` with:

```markdown
This is one of **two** surfaces where the platform renders anything other than plain text. The other
is the game detail page's info document (below). Both render *Markdown*, neither renders HTML, and
neither needs `dangerouslySetInnerHTML` — which is what keeps the platform-wide ban above absolute
rather than a rule with exceptions.
```

- [ ] **Step 2: Add the info-document subsection**

Append after the game-log rules:

```markdown
### The game info document

`game-catalog.md` FR-GDET-003/004: a game may ship a Markdown info document, rendered on the game
detail page. Its content comes from an **uploaded artifact** and it renders on the **platform origin**,
which holds the session cookie — so it is the highest-value XSS sink in the product, and the only one
whose input is a file rather than a form field.

**Rendered client-side, Markdown → React elements, never to an HTML string.** The renderer produces a
React tree directly (`react-markdown` with `skipHtml`, or equivalent); no HTML text is ever
constructed, so `dangerouslySetInnerHTML` is not needed and the ESLint ban stands unweakened. There is
no sanitized-HTML column and no server-side sanitization pass: storing a second, cleaned
representation of the artifact means a later tightening of the allow-list has to be back-applied to
every document ever uploaded, and the one that is missed is the one that matters.

The allow-list is wider than the game log's, because FR-GDET-004 names the content it must support:

| Allowed | Notes |
|---|---|
| Headings, paragraphs, lists, blockquotes | Plain structure |
| Emphasis, strong, inline code, fenced code blocks | No syntax highlighting — a highlighter is a second parser over untrusted input |
| Links | `http`/`https` only, rendered with `rel="noopener noreferrer nofollow"` and `target="_blank"`. **Any other scheme is dropped, not escaped** — `javascript:`, `data:` and `vbscript:` are the whole attack |
| Images | `https` only, from any host. Lazy-loaded, with a `referrerpolicy="no-referrer"` |
| Tables | The one construct developers most reliably want and hand-write badly |

Everything else is dropped: **raw HTML passthrough disabled** (`skipHtml`), no autolinking of bare
text, no footnotes, no directives, no math, no embedded SVG. `iframe`, `script`, `object`, `embed` and
`style` cannot appear because no HTML is parsed at all.

**Two rules that are not obvious:**

- **The image and link allow-lists are enforced on the parsed AST, not by a regex over the source.**
  A regex over Markdown text is defeated by reference-style links, entity encoding and whitespace; the
  AST node carries the resolved URL.
- **The info document is excluded from the published game-asset bundle**
  (`../manifest/bundle-format.md` §*Excluded*), so the raw Markdown is never fetchable from the games
  origin. That exclusion exists to force every reader through this renderer, and removing it would
  route around FR-GDET-004 entirely.

`bundle-format.md`'s exclusion table already states this; the rule it depends on is here.
```

- [ ] **Step 3: Point the requirement at its spec**

Add to `docs/requirements/game-catalog.md`'s "Related API Specifications" section:

```markdown
- [input-validation.md](../specs/api-design/input-validation.md) — the info document's Markdown renderer and allow-list (implements FR-GDET-004)
```

- [ ] **Step 4: Verify**

Run: `grep -n "only surface where the platform renders" docs/specs/api-design/input-validation.md`
Expected: **no output** — the false claim is gone. Then
`grep -c "FR-GDET-004" docs/specs/api-design/input-validation.md` returns at least `1`.

- [ ] **Step 5: Commit**

```bash
git add docs/specs/api-design/input-validation.md docs/requirements/game-catalog.md
git commit -m "docs(specs): specify info-document Markdown sanitization (IR-19)"
```

---

## Task 20: Resolve the iframe `sandbox` contradiction (IR-21)

**Files:**
- Modify: `docs/specs/platform-frontend/shell-architecture.md:136-150` (§5)
- Modify: `docs/specs/game-frontend/game-asset-serving.md:227-240` (§6.1)

`shell-architecture.md` specifies `sandbox="allow-scripts"` with a rationale for why
`allow-same-origin` would be dangerous. `game-asset-serving.md` specifies
`sandbox="allow-scripts allow-same-origin"` with a rationale for why it is safe given the separate
registrable domain. **Both claim to own the value; neither acknowledges the other.**

**ADR-0007 governs, and `game-asset-serving.md`'s reasoning is the one consistent with it.** If
`shell-architecture.md`'s version ships, the frame gets an opaque origin: game engines lose
`localStorage` and `IndexedDB`, and — the part that makes this a blocker rather than a preference —
`event.origin` becomes the string `"null"`, so the shell's own origin check drops every message the
game sends. The relay fails silently and completely.

- [ ] **Step 1: Correct the shell's iframe and cite the owner**

Replace the `<iframe>` block in `shell-architecture.md` §5 and the rule row beneath it:

```tsx
<iframe
  src={gameFrontendUrl}
  sandbox="allow-scripts allow-same-origin"
  allow=""
  referrerPolicy="no-referrer"
/>
```

```markdown
| Rule | Why |
|---|---|
| `sandbox="allow-scripts allow-same-origin"` — **normative value owned by [`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §6.1** | The well-known footgun is granting both to a *same-origin* frame, which lets it remove its own sandbox. This frame is cross-origin by construction (ADR-0007 puts game frontends on a separate **registrable domain**), so the pair grants the game a real origin of its own and nothing more. **`allow-scripts` alone would break the relay outright:** an opaque origin makes `event.origin` the string `"null"`, so the origin check below drops every message the game sends, and the game silently receives nothing. It also costs the game `localStorage` and `IndexedDB`. |
```

- [ ] **Step 2: Claim ownership explicitly on the other side**

Insert at the top of `game-asset-serving.md` §6.1, before the code block:

```markdown
**This document owns the `sandbox` value.** [`../platform-frontend/shell-architecture.md`](../platform-frontend/shell-architecture.md)
§5 renders the element and cites this section for the attribute; the two must not be changed
independently. The value follows from ADR-0007's separate registrable domain, which is a property of
the *serving* design specified here, not of the shell.
```

- [ ] **Step 3: Verify**

Run: `grep -n 'sandbox=' docs/specs/platform-frontend/shell-architecture.md docs/specs/game-frontend/game-asset-serving.md`
Expected: both files show `allow-scripts allow-same-origin`, and no occurrence of a bare
`sandbox="allow-scripts"` remains.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/platform-frontend/shell-architecture.md docs/specs/game-frontend/game-asset-serving.md
git commit -m "docs(specs): one owner for the game iframe sandbox attribute (IR-21)"
```

---

## Task 21: Specify the platform shell's CSP (IR-22)

**Files:**
- Modify: `docs/specs/platform-frontend/shell-architecture.md` — new section after §5

`game-asset-serving.md` §6.3 requires the shell to pin `frame-src` and **explicitly delegates the rest
of the shell's CSP to the frontend shell specification.** That specification has no CSP section. The
delegation target does not exist, so the platform origin — the one holding the session cookie — ships
with no specified policy.

Do this task after Task 20; both touch §5's neighbourhood.

- [ ] **Step 1: Add the section**

Insert a new `## 6. Content-Security-Policy` immediately after §5, renumbering subsequent sections:

```markdown
## 6. Content-Security-Policy

The shell document is served from the platform origin, which holds the session cookie. This is the
policy `../game-frontend/game-asset-serving.md` §6.3 delegates here; that document owns `frame-src`
and this one owns everything else.

```
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data: https:;
font-src 'self';
connect-src 'self';
frame-src {gameFrontendOrigin};
frame-ancestors 'none';
form-action 'self';
base-uri 'none';
object-src 'none';
```

Sent as a response header on the shell document, not as a `<meta>` tag: a header applies to the
response that carries it and cannot be displaced by injected markup earlier in the document.

| Directive | Why this value |
|---|---|
| `script-src 'self'` | No `'unsafe-inline'` and no `'unsafe-eval'`. Vite emits external modules in production, so neither is needed — and if a future dependency demands one, that is a dependency decision, not a CSP relaxation |
| `img-src ... https:` | Info-document images (FR-GDET-004, Task 19) come from arbitrary hosts. `data:` covers inline icons. This is the one deliberately wide directive, and it is wide for content that renders as an `<img>` and nothing else |
| `connect-src 'self'` | REST, STOMP and SSE are all same-origin. **The games origin is never added** — the shell talks to game frontends through `postMessage`, never over the network |
| `frame-src {gameFrontendOrigin}` | Owned by `game-asset-serving.md` §6.3. Pinned to the games origin, which blocks the frame from navigating itself off-origin and closes the exfiltration channel a second time |
| `frame-ancestors 'none'` | The platform is never embedded. This replaces `X-Frame-Options`, which is not sent |
| `base-uri 'none'` | An injected `<base>` retargets every relative URL in the document — including the script tags — which turns a single injection into full script control |
| `object-src 'none'` | Nothing on the platform uses a plugin element |

**No `nonce` and no hash allow-list**, because there is no inline script to permit. Adding a nonce
mechanism before there is anything to nonce creates the exact affordance — "put the nonce on it" —
that inline script bans exist to remove.

**The games origin has its own, stricter policy** (`../game-frontend/game-asset-serving.md` §6.4).
The two are separate documents for separate origins and must not be merged; the whole point of
ADR-0007 is that they are different security contexts.

**`report-uri` is deliberately absent for the MVP.** There is no collection endpoint and a
report-only header nobody reads is worse than none — it reads as monitored. When observability lands
(`../deployment/observability.md`), a `report-to` group is the natural addition.
```

- [ ] **Step 2: Close the delegation from the other side**

In `game-asset-serving.md` §6.3, replace `(The rest of the shell's CSP belongs to the frontend shell
spec.)` with:

```markdown
(The rest of the shell's CSP is [`../platform-frontend/shell-architecture.md`](../platform-frontend/shell-architecture.md) §6.)
```

- [ ] **Step 3: Verify**

Run: `grep -n "frame-ancestors\|base-uri\|connect-src" docs/specs/platform-frontend/shell-architecture.md`
Expected: hits for all three. Then confirm the delegation now resolves:
`grep -n "belongs to the frontend shell spec" docs/specs/game-frontend/game-asset-serving.md`
returns **no output**.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/platform-frontend/shell-architecture.md docs/specs/game-frontend/game-asset-serving.md
git commit -m "docs(specs): specify the platform shell's CSP (IR-22)"
```

---

## Task 22: Design the observability wiring (IR-04)

**Files:**
- Create: `docs/specs/deployment/observability.md`
- Modify: `docs/specs/deployment/INDEX.md` — register it
- Modify: `docs/requirements/platform-operations.md` — add it to *Related Documents*
- Modify: `docs/specs/deployment/local-environment.md` §7.9 — the OTLP endpoint key

Prometheus, Grafana, Loki and Tempo are listed containers with **nothing between them and the
requirement text.** The scripted coverage check confirms it: all ten `FR-MET-*` and `FR-TRACE-*`
requirements are cited by no spec anywhere in the corpus. `platform-operations.md` OQ-003 makes the
full Grafana stack a primary learning goal, so this is scoped as full wiring rather than a minimum.

**Interfaces:**
- Consumes: `platform-operations.md` FR-OBS-001…005, FR-MET-001…007, FR-TRACE-001…004,
  FR-ALERT-001…007, CON-003…006; `local-environment.md` §1 (the container set) and §7.9.
- Produces: `management.otlp.tracing.endpoint` and the Grafana provisioning paths, both referenced by
  the compose and Helm layouts in `local-environment.md` §4.

**Document outline:**

| § | Content |
|---|---|
| Scope | What this wires; that `platform-operations.md` owns the requirements and this owns the mechanism |
| 1. The four signals | One table: signal → producer → transport → store → the requirement IDs |
| 2. Metrics | Actuator exposure (`/actuator/prometheus` on `8081`), the scrape config, and **why Prometheus scrapes the management port rather than the public one** — `rest-conventions.md` already says it is never through the ingress. The FR-MET-003 business gauges and how they are updated periodically rather than per-request |
| 3. Logs | Logback JSON encoder, stdout, MDC fields from FR-OBS-003, and the compose shipping path: the Loki Docker driver, or Promtail on the container log directory. Name one and say why |
| 4. Traces | The OpenTelemetry Java agent, `management.otlp.tracing.endpoint` → Tempo `4317`, W3C propagation, the STOMP and Redis-queue hops FR-TRACE-002 calls out by name, and FR-TRACE-003's MDC injection |
| 5. Grafana provisioning | Datasource YAML for all three stores, dashboard provisioning from files in the repo, and the admin credential (already in `secrets-and-configuration.md` §1) |
| 6. Alert routing | FR-ALERT-001…007 as Prometheus rules; Alertmanager as the tenth container; FR-ALERT-005's configurable channel as a webhook URL that is **absent by default and disables routing when unset** — the same posture the OAuth secret takes |
| 7. What the local stack does *not* do | No long-term storage, no HA, no tail-based sampling (FR-TRACE-004's 10% is head-based via `management.tracing.sampling.probability`, already in §7.9) |
| 8. Requirements traceability | Every `FR-MET-*`, `FR-TRACE-*`, `FR-ALERT-*` and `FR-OBS-*` id |

Two decisions to make while writing, both of which the document must state rather than leave open:

1. **Log shipping under compose.** The Loki Docker logging driver is a plugin the developer must
   install; Promtail is another container but needs no host-level install. Choose **Promtail** and say
   that a plugin install is a step a clean-machine bootstrap cannot assume.
2. **Alert routing when no webhook is configured.** Rules still evaluate and fire into Alertmanager;
   only the notification receiver is absent. State this, because "alerts are configured" and "alerts
   reach a human" are different claims and FR-ALERT-005 is only the second.

- [ ] **Step 1: Write the document per the outline above**

- [ ] **Step 2: Add the OTLP endpoint to §7.9**

```markdown
| `management.otlp.tracing.endpoint` | `http://tempo:4317` | `MANAGEMENT_OTLP_TRACING_ENDPOINT` |
```

- [ ] **Step 3: Register it**

Add to `docs/specs/deployment/INDEX.md`:

```markdown
| [observability.md](observability.md) | Metrics, logs, traces and alert routing: Actuator/Prometheus scrape, Logback JSON → Promtail → Loki, OTLP → Tempo, Grafana provisioning, Alertmanager rules. |
```

and to `platform-operations.md`'s *Related Documents* list:

```markdown
- `../specs/deployment/observability.md` — the wiring for FR-OBS-*, FR-MET-*, FR-TRACE-* and FR-ALERT-*
```

- [ ] **Step 4: Verify coverage**

Run:

```bash
for id in FR-MET-001 FR-MET-002 FR-MET-003 FR-MET-004 FR-MET-005 FR-MET-006 FR-MET-007 \
          FR-TRACE-001 FR-TRACE-002 FR-TRACE-003 FR-TRACE-004 \
          FR-ALERT-001 FR-ALERT-002 FR-ALERT-003 FR-ALERT-004 FR-ALERT-005; do
  grep -q "$id" docs/specs/deployment/observability.md || echo "UNCITED: $id"
done
```

Expected: no output. All ten previously uncited `FR-MET-*`/`FR-TRACE-*` requirements now have a spec.

- [ ] **Step 5: Commit**

```bash
git add docs/specs/deployment/observability.md docs/specs/deployment/INDEX.md \
        docs/specs/deployment/local-environment.md docs/requirements/platform-operations.md
git commit -m "docs(specs): observability wiring — metrics, logs, traces, alerts (IR-04)"
```

---

## Task 23: Design the design system (IR-23, first half)

**Files:**
- Create: `docs/specs/platform-frontend/design-system.md`
- Modify: `docs/specs/platform-frontend/INDEX.md` — register it
- Modify: `docs/requirements/platform-ui-library.md` — amend CON-002, add the spec link

~30 requirements, 24 of them cited by no spec. No document in `docs/specs/` covers tokens, CSS
strategy or component architecture. **Decision (already taken): the library lives inside
`turnbase-frontend` as an internal module with an enforced import boundary.** CON-002's own-submodule
requirement is amended, and `CLAUDE.md`'s five-repo table stays at five.

**Document outline:**

| § | Content |
|---|---|
| Scope | The component library and its tokens; not page layout, which is `shell-architecture.md`'s |
| 1. Where it lives | `src/design-system/` inside `turnbase-frontend`. The import boundary: application code imports from the module's public entry point only, enforced by an ESLint `no-restricted-imports` rule on deep paths. **Why not a submodule** — the CON-002 amendment, stated here so the decision travels with the design |
| 2. Tokens | Colour, spacing, typography, radius, shadow, z-index, motion. Defined as CSS custom properties on `:root`, consumed by name and never by literal. The dark-mode strategy if `platform-ui-library.md` requires one |
| 3. CSS strategy | Pick one — CSS Modules, or vanilla-extract — and say why the alternatives lose. No runtime CSS-in-JS: it costs a render-blocking style injection on a shell whose first paint gates every view |
| 4. Component inventory | One row per `FR-COMP-*`: component, its variants, and the requirement it satisfies. This table is what makes the 24 uncited requirements cited |
| 5. Composition rules | Which components may contain which; the primitive/composite split |
| 6. Accessibility baseline | Focus management, keyboard interaction, colour contrast — whatever `platform-ui-library.md`'s NFRs require, restated as build rules |
| 7. Requirements traceability | Every `FR-COMP-*`, `FR-TOKEN-*`, `CON-*` and `NFR-*` in `platform-ui-library.md` |

- [ ] **Step 1: Read the requirements**

Read `docs/requirements/platform-ui-library.md` in full and inventory every requirement ID. §4's table
must have a row for each `FR-COMP-*`; §7 must cite every ID in the document.

- [ ] **Step 2: Write the document per the outline**

- [ ] **Step 3: Amend CON-002**

Replace CON-002's description in `platform-ui-library.md`:

```markdown
The component library is a self-contained module with a single public entry point and no dependency
on application code. **For v1 it lives inside the `turnbase-frontend` repository** at
`src/design-system/` rather than in its own submodule: it has exactly one consumer, and a separate
repository would add an npm publish step and a version bump to every UI change for a boundary that
lint already enforces. The module boundary — not the repository boundary — is the constraint, and it
is enforced by an ESLint rule forbidding deep imports. Extracting it to its own package later is a
`git filter-repo` and a `package.json`, because nothing in the design depends on co-location. See
[`../specs/platform-frontend/design-system.md`](../specs/platform-frontend/design-system.md) §1.
```

- [ ] **Step 4: Register and link**

Add to `docs/specs/platform-frontend/INDEX.md`:

```markdown
| [design-system.md](design-system.md) | Tokens, CSS strategy, component inventory and the import boundary for the platform component library. |
```

and add a "Related API Specifications" section to `platform-ui-library.md` if it has none, pointing at
`design-system.md`.

- [ ] **Step 5: Verify coverage**

Run:

```bash
grep -o '\bFR-[A-Z]*-[0-9]\{3\}' docs/requirements/platform-ui-library.md | sort -u > /tmp/ui-ids
while read id; do
  grep -q "$id" docs/specs/platform-frontend/design-system.md || echo "UNCITED: $id"
done < /tmp/ui-ids
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/platform-frontend/design-system.md docs/specs/platform-frontend/INDEX.md \
        docs/requirements/platform-ui-library.md
git commit -m "docs(specs): the platform design system (IR-23)"
```

---

## Task 24: Cut the onboarding wizard from v1 (IR-23, second half)

**Files:**
- Modify: `docs/requirements/onboarding-wizard.md` — scope banner, all 16 priorities
- Modify: `docs/requirements/INDEX.md` — annotate the entry
- Modify: `docs/requirements/platform-views.md` — resolve the FR-ONB-004 dangling CTA

All 16 requirements are uncited and **the entire document is referenced by nothing else in the
corpus** — no mount point, no trigger wiring, and no CTA row in `platform-views.md`'s landing-page
element table despite FR-ONB-004 requiring one. **Decision (already taken): cut from v1.**

A cut is not a deletion. The document stays, clearly marked, so the requirements survive for whoever
picks it up.

- [ ] **Step 1: Add the scope banner**

Insert immediately below the document's `# ` title:

```markdown
> **Post-MVP — not in v1 scope.** Cut during the 2026-08-16 implementation-readiness remediation
> (IR-23). The onboarding wizard is first-run polish on a platform whose v1 audience is its author,
> and it was the only one of the four structural gaps in that review that could be dropped without
> weakening the demonstration the project exists to make. The requirements below are retained
> unchanged and are the starting point whenever it is scheduled; nothing in v1 depends on them.
>
> **Nothing else in the corpus references this document**, which is what made the cut cheap — with
> one exception, now resolved: FR-ONB-004 required a landing-page CTA that `platform-views.md` never
> had, and that CTA is not being added.
```

- [ ] **Step 2: Retitle the priority column**

Change every `Must` / `Should` in the document's priority columns to `Post-MVP`. A requirement marked
`Must` inside a cut document is exactly the kind of thing that gets picked up by a coverage script two
sessions from now and re-raised as a blocker.

- [ ] **Step 3: Annotate the requirements INDEX**

In `docs/requirements/INDEX.md`, append to the `onboarding-wizard.md` entry:

```
**Post-MVP — cut from v1 (IR-23).**
```

- [ ] **Step 4: Close the FR-ONB-004 loose end**

Add a line to `platform-views.md`'s landing-page section, below its element table:

```markdown
No onboarding CTA is present. `onboarding-wizard.md` FR-ONB-004 requires one; that document is
**Post-MVP** (IR-23) and the row is deliberately absent rather than missing.
```

- [ ] **Step 5: Verify**

Run: `grep -c "| Must |" docs/requirements/onboarding-wizard.md`
Expected: `0`.

- [ ] **Step 6: Commit**

```bash
git add docs/requirements/onboarding-wizard.md docs/requirements/INDEX.md docs/requirements/platform-views.md
git commit -m "docs(requirements): cut the onboarding wizard from v1 (IR-23)"
```

---

## Task 25: Spec hygiene — the three items with no deadline

**Files:**
- Modify: `docs/specs/INDEX.md` — declare the sub-duty convention
- Modify: `docs/specs/platform/data-model-accounts.md:392` — the deliberately-deferred citation

Three items were recorded in the review as hygiene rather than blockers. Two are one line each; the
third was deliberately not guessed at and now has enough context to resolve.

- [ ] **Step 1: Declare the `FR-JOB-007a…e` convention**

It is used consistently in **eight places** and declared nowhere — a scripted check flagged
`FR-JOB-007d` as a dangling citation and was wrong. Add to `docs/specs/INDEX.md`, in the section that
states the ID-qualification rule:

```markdown
**Sub-duty suffixes.** A requirement that enumerates lettered duties in its body may be cited by
suffix: `FR-JOB-007d` is duty (d) of `platform-operations.md` FR-JOB-007. The suffix is not a separate
requirement ID and will not be found by a grep for a definition. This convention is used for
FR-JOB-007(a–e) and FR-JOB-008(a–c).
```

- [ ] **Step 2: Fix the `data-model-accounts.md:392` citation**

The row cites `FR-INV-002` (the friends-only restriction) for room-invitation deletion on erasure,
which is certainly wrong. The review left it rather than guess. Task 11 has since rewritten the
neighbouring rows, and the correct target is now clear from the row's own text — it deletes
invitations on **both** legs as part of account erasure, which is `FR-ACCT-005`'s duty, with
`FR-INV-001` establishing that the objects exist. Replace the requirement cell:

```
FR-ACCT-005 (amended); `notifications-invitations.md` FR-INV-001
```

- [ ] **Step 3: Verify**

Run: `grep -n "FR-INV-002" docs/specs/platform/data-model-accounts.md`
Expected: **no output.** Then `grep -c "Sub-duty suffixes" docs/specs/INDEX.md` returns `1`.

- [ ] **Step 4: Commit**

```bash
git add docs/specs/INDEX.md docs/specs/platform/data-model-accounts.md
git commit -m "docs(specs): declare the sub-duty convention; correct the erasure citation"
```

---

## Task 26: Close the gates and update the trackers

**Files:**
- Modify: `docs/implementation/registry.md` — the `<!-- GATES:BEGIN -->` … `<!-- GATES:END -->` block
- Modify: `docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — mark each IR closed
- Modify: `docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — register this plan
- Modify: `STATUS.md`

Run this task **last**, after every task above has committed. A gate closed before its fix lands is
worse than a gate left open.

- [ ] **Step 1: Verify every fix is actually in place**

Run the verification step of every task above, in one pass:

```bash
set -e
grep -q "artifact-store.bucket" docs/specs/deployment/local-environment.md
grep -q "turnbase_owner" docs/specs/deployment/secrets-and-configuration.md
! grep -q "all test types combined" docs/requirements/platform-operations.md
test -f docs/specs/deployment/observability.md
grep -q "owner is exempt" docs/requirements/platform-views.md
grep -q "active_session_id IS NOT NULL" docs/specs/platform/room-lifecycle.md
grep -q "instance-initiated" docs/specs/platform/room-lifecycle.md
! grep -q "shared with the room lobby event stream" docs/specs/api-design/room-chat-websocket.md
grep -q "room_participant_unannounced_idx" docs/specs/platform/data-model.md
grep -q "owner_epoch = :myEpoch" docs/specs/platform/room-lifecycle.md
! grep -q "records the closure as owed" docs/specs/platform/room-lifecycle.md
! grep -q "that is not an AI" docs/specs/platform/room-lifecycle.md
test -f docs/specs/api-design/room-rest-api.md
grep -q "lastOutcome" docs/specs/game-host/game-host-internals.md
! grep -q "defensively" docs/specs/internal-grpc/gamehost.proto
grep -q "address_rejected" docs/specs/api-design/websocket.md
! grep -q "only surface where the platform renders" docs/specs/api-design/input-validation.md
grep -q "FR-JOB-013" docs/requirements/platform-operations.md
grep -q "allow-scripts allow-same-origin" docs/specs/platform-frontend/shell-architecture.md
grep -q "frame-ancestors" docs/specs/platform-frontend/shell-architecture.md
test -f docs/specs/platform-frontend/design-system.md
grep -q "Post-MVP" docs/requirements/onboarding-wizard.md
grep -q "Sub-duty suffixes" docs/specs/INDEX.md
echo "ALL FIXES PRESENT"
```

Expected: `ALL FIXES PRESENT`. Any failure means that task is not done — go back to it.

- [ ] **Step 2: Check link integrity across the whole corpus**

Three new documents and roughly thirty new cross-references were added. Resolve every relative
markdown link under `docs/`:

```bash
python3 - <<'PY'
import os, re
bad = 0; total = 0
for root, dirs, files in os.walk('docs'):
    dirs[:] = [d for d in dirs if d != '.claude']
    for f in files:
        if not f.endswith('.md'): continue
        p = os.path.join(root, f)
        for n, line in enumerate(open(p, encoding='utf-8'), 1):
            for m in re.finditer(r'\]\((?!https?:|#|mailto:)([^)#]+)', line):
                total += 1
                t = os.path.normpath(os.path.join(root, m.group(1).strip()))
                if not os.path.exists(t):
                    bad += 1; print(f'BROKEN {p}:{n} -> {m.group(1)}')
print(f'{total} links, {bad} broken')
PY
```

Expected: `0 broken`. The pre-remediation baseline was 512 links, 0 broken; this must not regress.

- [ ] **Step 3: Rewrite the gates block in the registry**

Replace the body of `<!-- GATES:BEGIN -->` … `<!-- GATES:END -->` in
`docs/implementation/registry.md`. The table's `Gate` column becomes a status column:

```markdown
The 2026-08-16 readiness audit returned **23 blockers. All 23 are now closed** — see
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
for the register and the remediation plan that closed them.

**Every work item in the register above is ungated.** Status reverts to whatever the item's own
dependencies imply.

| Gate | Closed by | What changed |
|---|---|---|
| IR-01 | `local-environment.md` §1, §5, §7.9 | Bucket named `turnbase-bundles`, created by a `minio/mc` init step |
| … | | |
```

Fill one row per IR with the document that now carries the fix — a reader who wants to know *how* a
gate closed should not have to `git log`.

- [ ] **Step 4: Mark each blocker closed in the review INDEX**

For each `#### IR-NN` heading, append `— **CLOSED**` to the heading and add a final line to the entry:

```markdown
**Closed:** <one sentence naming the resolution and the document that now carries it.>
```

Update the *Verdict* section: the corpus is implementation-ready, 23 of 23 blockers closed, with the
four structural gaps resolved as three design sessions and one scope cut. Update the
*Recommended fix order* section to note it has been executed.

- [ ] **Step 5: Register this plan in the review INDEX**

Add to the *Files* table:

```markdown
| [remediation-plan.md](remediation-plan.md) | The task-by-task plan that closed all 23 blockers, with the four scope decisions taken before execution | — |
```

- [ ] **Step 6: Update `STATUS.md`**

**Replace** the "Last Session Summary" section — never append — per `CLAUDE.md`. It must record:

- 23 of 23 blockers closed; three new specification documents; one scope cut.
- The four scope decisions and who made them, since a future reader will otherwise re-open them.
- The two resolutions that departed from the review's own suggestion, and why: **IR-11** uses the
  existing deferred-tail mechanism rather than a new owed-closure table, and **IR-12** declares the v1
  behaviour of the AI wire surface rather than adding a schema representation or cutting the feature.
- **IR-09's fix has two halves** — the honest `lost_announced_at` and the `leave_reason` backstop —
  and Task 11 depends on the first. That dependency is not obvious from either document.
- Update *Next Priorities*: Phase 1 implementation begins at `IMP-M0-01`, and the sequencing note in
  the registry's gates block no longer holds because IR-01 and IR-02 are closed.
- Update the *Review action plan*: the 2026-08-16 round is **closed**.

- [ ] **Step 7: Final verification**

```bash
git status --short | grep -v '^??' | wc -l    # expect 0
grep -c "CLOSED" docs/reviews/2026-08-16-implementation-readiness/INDEX.md   # expect >= 23
```

- [ ] **Step 8: Commit**

```bash
git add docs/implementation/registry.md docs/reviews/2026-08-16-implementation-readiness/INDEX.md STATUS.md
git commit -m "docs: close all 23 implementation-readiness blockers"
```

---

## Self-review

Run against the blocker register before declaring the plan complete.

**Coverage.** All 23 IR findings have a task: IR-01→T1, IR-02→T2, IR-03→T3, IR-04→T22, IR-05→T5,
IR-06→T6, IR-07→T7, IR-08→T8, IR-09→T9, IR-10→T10, IR-11→T11, IR-12→T12, IR-13→T4, IR-14→T15,
IR-15→T16, IR-16→T17, IR-17→T18, IR-18→T13, IR-19→T19, IR-20→T14, IR-21→T20, IR-22→T21, IR-23→T23+T24.
The three hygiene items from the review's *Spec hygiene* list are Task 25. Task 26 closes the trackers.

**Ordering constraints that are not optional.**

- Tasks 6–12 run as one pass, in order, by one worker.
- **Task 9 before Task 11** — the deferred-closure design depends on duty 2's predicate being correct.
- **Task 10 before Task 11** — Task 11 rewrites the prose above the pseudocode Task 10 changes.
- **Task 20 before Task 21** — both edit `shell-architecture.md` §5's neighbourhood.
- **Task 26 last**, after every other task has committed.

Everything else is independent and may be parallelised. Tasks 1–3 are the shortest path to
`docker compose up` on a clean machine and should go first regardless.

**Known residuals — recorded, not fixed here.** These were below blocker severity in the review and
remain open after this plan: the `FR-SESS-*` collision across `user-accounts.md` and
`platform-architecture.md`; Argon2id having no cost parameters; profile privacy having no REST
endpoint; `FR-ACCT-010` having no route; the absent consolidated WebSocket error-code registry; offset
pagination on the notification centre; the `bigserial` versus `GENERATED ALWAYS AS IDENTITY` split;
`schema-migrations.md`'s mislabelled circular foreign key; the GDK example that violates the
determinism rule stated above it; and `test-harness.md`'s claim that the Game Host blocks filesystem
and network calls. They are in the per-slice files in this directory. **The last two are the most
likely to cost time**, because both are read by game developers as instructions.
