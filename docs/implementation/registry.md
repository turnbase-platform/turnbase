# Implementation Registry — Work Items

Conventions, status vocabulary and the milestone map live in [INDEX.md](INDEX.md). Read that first.

Every item below carries:

- **Repo** — which submodule the work lands in.
- **Depends on** — items that must be `DONE` first.
- **Read first** — the minimum document set that fully determines the item. *An implementation agent
  should not need to read anything outside this list.* If it does, that is a defect in this registry;
  record it.
- **Satisfies** — the requirement IDs the item implements, document-qualified per the rule in
  [`../specs/INDEX.md`](../specs/INDEX.md).
- **Done when** — checkable without judgement.
- **Gate** — open findings blocking the item, or `—`.

---

## Register

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| **M0 — Bootstrap** ||||
| IMP-M0-01 | gRPC stubs and internal models | common | — | READY |
| IMP-M0-02 | Public SDK artifacts (Maven + npm) | sdk | — | READY |
| IMP-M0-03 | Platform Monolith skeleton | platform | — | READY |
| IMP-M0-04 | Game Host skeleton | game-host | M0-01 | READY |
| IMP-M0-05 | Frontend skeleton | frontend | — | READY |
| IMP-M0-06 | Flyway baseline `V1__baseline.sql` | platform | M0-03 | READY |
| IMP-M0-07 | Local stack — compose profile | this repo | M0-03, M0-04, M0-05 | READY |
| IMP-M0-08 | Local stack — Helm chart (canonical) | this repo | M0-07 | READY |
| IMP-M0-09 | Configuration and secrets wiring | platform, game-host | M0-03, M0-04 | READY |
| IMP-M0-10 | Observability baseline | platform, game-host | M0-03, M0-04 | READY |
| IMP-M0-11 | CI/CD workflows | all | M0-01…05 | READY |
| IMP-M0-12 | Seed data | platform | M0-06, M4-03 | READY |
| **M1 — Accounts and sessions** ||||
| IMP-M1-01 | Error model, REST conventions, validation harness | platform | M0-03 | READY |
| IMP-M1-02 | Rate limiter (Tiers 1–5) | platform | M1-01 | READY |
| IMP-M1-03 | JWT key set, issuance, rotation | platform | M0-09 | READY |
| IMP-M1-04 | Registration and login | platform | M1-01, M1-03 | READY |
| IMP-M1-05 | Guest minting and purge | platform | M1-04 | READY |
| IMP-M1-06 | Session lifecycle and displacement | platform | M1-04 | READY |
| IMP-M1-07 | Profiles and privacy settings | platform | M1-04 | READY |
| IMP-M1-08 | Account deletion and erasure | platform | M1-07 | READY |
| IMP-M1-09 | Social graph — friendships and requests | platform | M1-07 | READY |
| **M2 — Rooms and realtime** ||||
| IMP-M2-01 | Room CRUD and listing | platform | M1-06 | READY |
| IMP-M2-02 | STOMP endpoint, auth, subscriptions | platform | M2-01 | READY |
| IMP-M2-03 | Ownership claim, lease, epoch fence | platform | M2-02 | READY |
| IMP-M2-04 | Room event versioning and fan-out | platform | M2-03 | READY |
| IMP-M2-05 | Join, teams, readiness | platform | M2-04 | READY |
| IMP-M2-06 | Host management and transfer | platform | M2-05 | READY |
| IMP-M2-07 | Disconnect, grace deadlines, sweeps | platform | M2-03 | READY |
| IMP-M2-08 | Reconnect and resync | platform | M2-07 | READY |
| IMP-M2-09 | Room closure and the five detach paths | platform | M2-07 | READY |
| IMP-M2-10 | Adoption and reconciliation jobs | platform | M2-03 | READY |
| IMP-M2-11 | In-room chat | platform | M2-05 | READY |
| IMP-M2-12 | Room invitations | platform | M2-01, M1-09 | READY |
| **M3 — Game execution** ||||
| IMP-M3-01 | GDK backend API surface | sdk | M0-02 | READY |
| IMP-M3-02 | Espresso context lifecycle | game-host | M0-04 | READY |
| IMP-M3-03 | GDK host bridge and serialization boundary | game-host | M3-01, M3-02 | READY |
| IMP-M3-04 | gRPC service implementation | game-host | M3-03 | READY |
| IMP-M3-05 | Orchestration client and session registry | platform | M3-04, M2-04 | READY |
| IMP-M3-06 | Game input outbox and delivery | platform | M3-05 | READY |
| IMP-M3-07 | Effect fan-out and spectator filtering | platform | M3-06 | READY |
| IMP-M3-08 | Session teardown as a durable to-do | platform | M3-05 | READY |
| IMP-M3-09 | Game failure handling | platform, game-host | M3-07 | READY |
| IMP-M3-10 | The first official game | sdk consumer | M3-03 | READY |
| IMP-M3-11 | GDK test harness | sdk | M3-01 | READY |
| **M4 — Catalog and upload** ||||
| IMP-M4-01 | Catalog listing and game detail | platform | M1-01 | READY |
| IMP-M4-02 | Manifest schema validation | platform | M0-06 | READY |
| IMP-M4-03 | Upload pipeline and version state machine | platform | M4-02 | READY |
| IMP-M4-04 | Bundle publication and asset serving | platform | M4-03 | READY |
| IMP-M4-05 | Admin API — review queue and badges | platform | M4-03 | READY |
| **M5 — History, statistics, notifications** ||||
| IMP-M5-01 | Game history recording | platform | M3-09 | READY |
| IMP-M5-02 | Per-game statistics | platform | M5-01 | READY |
| IMP-M5-03 | Notifications and the SSE stream | platform | M1-07 | READY |
| IMP-M5-04 | Retention purge jobs | platform | M5-01, M5-03 | READY |
| **M6 — Platform frontend** ||||
| IMP-M6-01 | Design tokens and component library | frontend | M0-05 | READY |
| IMP-M6-02 | Shell, routing and auth tiers | frontend | M6-01 | READY |
| IMP-M6-03 | Account and profile views | frontend | M6-02, M1-07 | READY |
| IMP-M6-04 | Room views and the STOMP client | frontend | M6-02, M2-08 | READY |
| IMP-M6-05 | Game iframe host and postMessage relay | frontend | M6-04, M3-07 | READY |
| IMP-M6-06 | Catalog and history views | frontend | M6-02, M4-01 | READY |
| IMP-M6-07 | Onboarding wizard | frontend | M6-02 | READY |

Statuses above are seeded as `READY`; the audit's open findings are applied as gates in the
*Readiness gates* section at the end of this document. **Consult that section before starting any
item** — it is the authoritative status overlay.

---

## M0 — Bootstrap

### IMP-M0-01 — gRPC stubs and internal models

**Repo:** `turnbase-common` · **Depends on:** — · **Publishes:** `io.turnbase:turnbase-grpc`

**Read first:**
- `docs/specs/internal-grpc/gamehost.proto` — the authoritative contract
- `docs/specs/internal-grpc/buf.yaml`
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — semantics, idempotency, error mapping

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-REG-001…004

**Done when:** `mvn verify` produces a jar containing generated client and server stubs for every
service in `gamehost.proto`; `buf lint` and `buf breaking` run in CI; the artifact installs to the
local Maven repository and resolves from both `turnbase-platform` and `turnbase-game-host`.

**Note:** the `.proto` is the source of truth. Where the prose in
`orchestration-gamehost-protocol.md` disagrees with it, the proto wins for wire shape — but raise
the disagreement rather than silently following one.

**Gate:** see *Readiness gates*.

---

### IMP-M0-02 — Public SDK artifacts

**Repo:** `turnbase-sdk` · **Publishes:** `io.turnbase:turnbase-sdk` (Maven) + npm package

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` §1–3 (interface and type surface only; behaviour is IMP-M3-01)
- `docs/specs/gdk-api/frontend-gdk-api.md` (TypeScript types)
- `docs/specs/gdk-api/INDEX.md`

**Satisfies:** `game-development-experience.md` FR-GDK-001 (interface shape), NFR-COMPAT-001

**Done when:** both artifacts build and publish locally; the Java artifact targets Java 21 bytecode
and uses no Java 22+ API; the npm package ships `.d.ts` types; Javadoc is present on every public
type (`CLAUDE.md` SHOULD).

---

### IMP-M0-03 — Platform Monolith skeleton

**Repo:** `turnbase-platform`

**Read first:**
- `docs/specs/deployment/local-environment.md` §1, §3, §7.9
- `docs/requirements/platform-operations.md` — service topology, CON-010/011
- `docs/decisions/0001-local-first-mvp-platform.md`

**Satisfies:** `platform-operations.md` FR-DEPLOY-001…003

**Done when:** Spring Boot 3.5+ on Java 21 starts; `8080` serves HTTP and `8081` is the management
port bound per §1 (loopback under compose, unbound under Kubernetes — **the two profiles differ and
getting this wrong breaks the readiness probes**); a Dockerfile produces `turnbase/platform`;
actuator health and readiness respond, and **readiness does not depend on the Game Host**.

---

### IMP-M0-04 — Game Host skeleton

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M0-01

**Read first:**
- `docs/specs/deployment/local-environment.md` §1, §3, §7.8
- `docs/specs/game-host/game-host-internals.md` §1 (topology only)
- `docs/decisions/0005-game-sandbox-espresso-spike.md`
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`

**Done when:** a GraalVM CE for JDK 21 image starts with Espresso available; `9090` serves gRPC and
`8081` is management; the process registers with the Platform Monolith per §3's 60-second budget; a
trivial guest context can be created and disposed.

**Constraint:** host JVM is Java 21; guest is Espresso running Java 21. There is no CE build for JDK
23 — see `CLAUDE.md`.

---

### IMP-M0-05 — Frontend skeleton

**Repo:** `turnbase-frontend`

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §1
- `docs/specs/deployment/local-environment.md` §1

**Done when:** Vite + React 19 + TypeScript builds; Prettier and ESLint run in CI; a Dockerfile
produces the static bundle; the dev server proxies to `turnbase.localhost:8080`.

---

### IMP-M0-06 — Flyway baseline

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-03

**Read first — all six schema documents, in this order:**
1. `docs/specs/platform/data-model.md` (shared conventions **and** room/session tables)
2. `docs/specs/platform/data-model-accounts.md`
3. `docs/specs/platform/data-model-social.md`
4. `docs/specs/platform/data-model-catalog.md`
5. `docs/specs/platform/data-model-history.md`
6. `docs/specs/platform/data-model-notifications.md`

Plus `docs/specs/deployment/schema-migrations.md` and `docs/decisions/0011-schema-migrations.md`.

**Satisfies:** `platform-operations.md` FR-DB-001…004, CON-012

**Done when:** `V1__baseline.sql` creates every table, constraint and index named in the six
documents; Flyway migrates a clean Postgres 16 to completion; a re-run is a no-op; the FK graph
admits the creation order used.

**This item is the first real test of whether the schema documents are mutually consistent.** Any
disagreement found while transcribing is a **specification** defect: fix the document, then the SQL.
Do not reconcile silently in the migration.

---

### IMP-M0-07 — Local stack, compose profile

**Repo:** this repo · **Depends on:** IMP-M0-03, M0-04, M0-05

**Read first:** `docs/specs/deployment/local-environment.md` in full — especially §1 (nine
containers), the host port map, §2 (network, and *Redis configuration is not optional*), §3 (startup
order and readiness), §5 (the three invocations).

**Satisfies:** `platform-operations.md` CON-010, CON-011; ADR-0001

**Done when:** `docker compose up` with the core profile brings up Platform Monolith, Game Host,
Postgres, Redis and MinIO, migrated and reachable; the full profile adds Prometheus, Grafana, Loki
and Tempo; the host port map matches §1 exactly, including Prometheus remapped to `9091`; both
`turnbase.localhost:8080` and `{gameId}.games.localhost:8080` route to the monolith by `Host` header
on the **same listener**.

---

### IMP-M0-08 — Local stack, Helm chart

**Repo:** this repo · **Depends on:** IMP-M0-07

**Read first:** `docs/specs/deployment/local-environment.md` §4 (*Kubernetes is canonical; compose is
the quick start*), §3 *Deployment strategy*.

**Done when:** the chart deploys to Docker Desktop Kubernetes; the management port is reachable by
kubelet probes (address **unset**, per §1); no Ingress or LoadBalancer names `8081`; **the deploy is
a rolling update even at one replica** — under `Recreate`, ADR-0008's claim path never runs against a
live incumbent.

---

### IMP-M0-09 — Configuration and secrets wiring

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M0-03, M0-04

**Read first:**
- `docs/specs/deployment/secrets-and-configuration.md` in full
- `docs/specs/deployment/local-environment.md` §7 — **the consolidated configuration surface; every
  tunable in the corpus is in that one table**

**Satisfies:** `platform-operations.md` FR-CRED-001…005

**Done when:** every key in §7 is bound to a typed configuration property with the stated default;
every secret in `secrets-and-configuration.md` has a local-dev provisioning path and a Kubernetes
Secret path; no secret has a default value in committed configuration; the JWT key set supports two
concurrent keys for graceful rotation.

---

### IMP-M0-10 — Observability baseline

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M0-03, M0-04

**Read first:** `docs/requirements/platform-operations.md` — FR-MET-001…006, FR-TRACE-001…004,
FR-OBS-*, NFR-OBS-001; `docs/specs/deployment/local-environment.md` §1, §7.9.

**Done when:** Micrometer exports to Prometheus at the management port; Logback emits JSON to stdout
with a correlation ID on every record; OpenTelemetry propagates W3C trace context across the REST →
gRPC boundary and traces land in Tempo; Grafana resolves Prometheus, Loki and Tempo as data sources.

**Gate:** see *Readiness gates* — the metric and trace requirements have no implementing spec.

---

### IMP-M0-11 — CI/CD workflows

**Repo:** all five submodules · **Depends on:** IMP-M0-01…05

**Read first:** `docs/requirements/platform-operations.md` FR-CICD-001…011.

**Done when:** each repo has a GitHub Actions workflow that builds, tests, and publishes its
artifact; coverage is reported (`CLAUDE.md`: >70% on critical paths); the workflow is the gate
`CLAUDE.md` requires before a submodule ref is bumped here.

---

### IMP-M0-12 — Seed data

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-06, IMP-M4-03

**Read first:** `docs/specs/deployment/local-environment.md` §6.

**Done when:** a seeded local stack lists at least one official game **that can actually be started**.

**The seed must go through the upload and validation pipeline, not around it.** A seed that inserts
catalog rows directly produces a game that lists and cannot start — the exact outcome §6 says it is
avoiding. This is why the item depends on M4-03 despite sitting in M0; it is the one M0 item that
cannot be finished first.

---

## M1 — Accounts and sessions

### IMP-M1-01 — Error model, REST conventions, validation

**Read first:** `docs/specs/api-design/rest-conventions.md`, `error-handling.md`,
`input-validation.md`, `pagination-filtering-sorting.md`.

**Done when:** one `@RestControllerAdvice` produces the single error shape defined in
`error-handling.md` for every failure class; Bean Validation failures map to it; the pagination
contract is implemented once as a reusable type; an integration test asserts the exact response body
for each error class.

**This item defines the shape every later endpoint conforms to. Build it before any endpoint.**

---

### IMP-M1-02 — Rate limiter, Tiers 1–5

**Read first:** `docs/specs/api-design/rate-limiting.md`; `docs/specs/deployment/local-environment.md` §7.6.

**Done when:** each tier's bucket, key, limit and window match the spec; breaches return the
`error-handling.md` shape with `429` and the stated headers; buckets are held in Redis. Tier 6
(WebSocket frames) is IMP-M2-02.

---

### IMP-M1-03 — JWT key set, issuance and rotation

**Read first:** `docs/specs/deployment/secrets-and-configuration.md` (JWT section, in full);
`docs/specs/platform/data-model-accounts.md` (`user_session`).

**Satisfies:** `user-accounts.md` FR-AUTH-*, FR-SESS-*

**Done when:** tokens carry a key id; verification accepts both the current and the previous key;
rotation is exercised by a test that verifies a token issued under the retired key still validates
until its expiry, and that `user_session.revoked_reason` records key-rotation revocation.

**Watch the ID collision:** `FR-SESS-001` and `FR-SESS-003` are each defined in **both**
`user-accounts.md` and `platform-architecture.md` with unrelated meanings. Here, `user-accounts.md`
is the one you want.

---

### IMP-M1-04 — Registration and login

**Read first:** `docs/requirements/user-accounts.md`; `docs/specs/platform/data-model-accounts.md`;
`docs/specs/api-design/input-validation.md`; `docs/specs/flows/01-arrival-and-account.md`.

**Done when:** registration and login endpoints exist with the validation rules of
`input-validation.md`; uniqueness is enforced by a database constraint **and** surfaced as a domain
error rather than a constraint-violation 500; login displaces the previous session per
`user-accounts.md` FR-SESS-003.

---

### IMP-M1-05 — Guest minting and purge

**Read first:** `docs/requirements/user-accounts.md` (guest section);
`docs/specs/platform/data-model-accounts.md`; `docs/requirements/platform-operations.md` FR-RET-002.

**Done when:** a guest principal can be minted without registration; the purge is **two-phase** and a
guest seated in a live room is never removed — a literal 24-hour delete fails permanently on
`room_participant`'s FK, and the cascade that would "fix" it removes a seated player from a live
game. The real bound is ~8 days.

---

### IMP-M1-06 — Session lifecycle and displacement
### IMP-M1-07 — Profiles and privacy settings
### IMP-M1-08 — Account deletion and erasure
### IMP-M1-09 — Social graph

**Read first (M1-06…09):** `docs/requirements/user-accounts.md`,
`docs/requirements/social-friends.md`, `docs/specs/platform/data-model-accounts.md`,
`docs/specs/platform/data-model-social.md`, `docs/decisions/0004-account-erasure-pseudonymization.md`.

**Done when (M1-08):** erasure is non-reversible — **a random token, not an HMAC**; `HMAC(user_id,
pepper)` is reversible by enumeration over a small id space given the key, which ADR-0004 forbids.
Every object listed in `data-model-accounts.md` §5 has a disposition, including the open
`game_review`, `room_invitation` on both legs, and `room`/`room_participant`. **Nothing happens by
cascade on that path** — a registered deletion is soft.

**Done when (M1-09):** guest exclusion is enforced by the foreign key —`friendship` references
`app_user (user_id, kind)` with a local `CHECK kind = 'REGISTERED'` — so `social-friends.md`
FR-SOC-020 cannot be violated from any code path.

---

## M2 — Rooms and realtime

The single most subtle milestone. `docs/specs/platform/room-lifecycle.md` and
`docs/specs/api-design/room-websocket.md` are the two core documents; read both in full before
starting **any** M2 item, along with ADR-0008, ADR-0009 and ADR-0010.

Walk `docs/specs/flows/02`, `04`, `05` and `07` before writing code.

### IMP-M2-01 — Room CRUD and listing
### IMP-M2-02 — STOMP endpoint, auth, subscriptions

**Read first:** `docs/specs/api-design/websocket.md`, `room-websocket.md`,
`docs/decisions/0002-websocket-room-affinity.md`; `rate-limiting.md` Tier 6.

### IMP-M2-03 — Ownership claim, lease, epoch fence

**Read first:** `docs/decisions/0008-room-ownership-lifecycle.md` in full;
`docs/specs/platform/room-lifecycle.md`.

**Done when:** the claim script is atomic and is **also the failure detector** — no dead-pod watcher
exists anywhere in this design. Every ownership-fenced write carries `WHERE owner_epoch < :myEpoch`
on adoption and the epoch equality fence on mutation. Self-eviction triggers on lease **lapse**, not
on renewal failure — a stop-the-world pause longer than the TTL slips past a renewal-failure check
entirely.

**The room version is not a fence token.** It is room-scoped and both producers advance it densely
from one sequence, so a stale owner is eventually *reached* by the legitimate owner and its CAS then
matches. Use the owner epoch.

### IMP-M2-04 — Room event versioning and fan-out

**Done when:** the version is committed to Postgres **before** the delta is published, and is
**assigned**, never `max()`-ed. Clients discard `delta.version <= localVersion`, so a pod that
re-issues a seen version is silently and permanently wrong for every client — strictly worse than a
gap.

### IMP-M2-05 — Join, teams, readiness
### IMP-M2-06 — Host management and transfer

**Done when (M2-06):** `migration_window_expires_at` is persisted and a sweep duty closes it. Without
it a host who does not return leaves the room permanently headless — adoption never routes through
the individual-disconnect path that would otherwise end the window.

### IMP-M2-07 — Disconnect, grace deadlines, sweeps

**Read first:** `docs/decisions/0009-grace-deadline-durability.md`.

**Done when:** deadlines are **persisted absolute timestamps, swept** — with no in-process timer. Two
mechanisms enforcing one deadline is a dual write and a three-way race on every reconnect. The
Postgres clock is the single time authority, which removes clock skew by construction.

Grace expiry must not fire in a **Lobby** room; `reconnection-flow.md` FR-DC-007 exists to stop a
rolling deploy deleting every Lobby room, and a Lobby grace expiry re-creates that bug.

### IMP-M2-08 — Reconnect and resync
### IMP-M2-09 — Room closure and the five detach paths

**Read first:** `docs/specs/flows/07-room-closure.md`.

**Done when:** `notifications-invitations.md` FR-INV-008's deletion of invitations happens **at
closure**, not by the FK cascade that fires seven days later at purge.

### IMP-M2-10 — Adoption and reconciliation jobs

**Done when:** the three reconciliation duties run per `platform-operations.md` FR-JOB-*; an
In-Progress room with no session **fails back to Lobby, not closed**; the adopt duty is exempt from
both FR-JOB-008 guards, which would otherwise block adoption for 120 s after every restart; orphaned
participant rows are handled by `ON DELETE CASCADE` rather than by a job.

### IMP-M2-11 — In-room chat
### IMP-M2-12 — Room invitations

---

## M3 — Game execution

**Read first for the whole milestone:** `docs/specs/game-host/game-host-internals.md`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md`, `gamehost.proto`,
`docs/specs/gdk-api/backend-gdk-api.md`, `docs/requirements/game-contracts.md`,
`docs/decisions/0005`, `docs/decisions/0006`, and flows `03` and `06`.

### IMP-M3-01 — GDK backend API surface
### IMP-M3-02 — Espresso context lifecycle
### IMP-M3-03 — GDK host bridge and serialization boundary

**Done when:** every object crossing the Espresso boundary is copied, not shared. A shared mutable
object across that boundary is a sandbox escape regardless of ADR-0006's trust model.

### IMP-M3-04 — gRPC service implementation

**Done when:** `TerminateSession` is idempotent **as specified in the contract**, not merely in the
implementation; `NOT_FOUND` is scoped so a retried teardown does not read as a hard failure.

### IMP-M3-05 — Orchestration client and session registry
### IMP-M3-06 — Game input outbox and delivery

**Done when:** the outbox drain is **not** ownership-partitioned — it is a gRPC call needing no
ownership, and partitioning it leaves an unowned room's `player_left` undelivered, with the game
sitting on a turn that never comes.

### IMP-M3-07 — Effect fan-out and spectator filtering
### IMP-M3-08 — Session teardown as a durable to-do

**Read first:** `docs/decisions/0010-session-teardown-ordering.md`.

**Done when:** the to-do is keyed by `sessionId`, **not** by a flag on the room — a rematch would
overwrite the previous session's owed teardown. Any rule testing whether a teardown was recorded must
test `room.active_session_id = :sessionId`, a durable fact, rather than the presence of the
`session_teardown` row, which `terminateAndCleanup` deletes on success.

### IMP-M3-09 — Game failure handling

**Done when:** the acting player is told why. `platform-architecture.md` FR-FAIL-001 and FR-FAIL-003
must be coherent about first-failure versus three-failure termination, and the failed input has a
stated disposition on every path.

### IMP-M3-10 — The first official game
### IMP-M3-11 — GDK test harness

**Done when:** the harness performs the **executing** round trip. `game-development-experience.md`
NFR-UPLOAD-002 forbids running game code at upload, so static serializability is checked at upload
and the executing round trip belongs here (FR-HARNESS-010).

---

## M4 — Catalog and upload

**Read first:** `docs/specs/manifest/bundle-format.md`, `manifest-schema.md`, `manifest.schema.json`,
`docs/specs/platform/data-model-catalog.md`, `docs/specs/api-design/file-uploads.md`,
`docs/specs/game-frontend/game-asset-serving.md`, flow `08`.

### IMP-M4-01 — Catalog listing and game detail
### IMP-M4-02 — Manifest schema validation

**Done when:** validation runs against `manifest.schema.json` — the executable artifact — and the
prose documents agree with it. Where they disagree, fix the document.

### IMP-M4-03 — Upload pipeline and version state machine

**Done when:** every non-terminal status has a documented exit, including `PROCESSING` when the
validating pod dies; a died-mid-validation version number is not permanently burned by the
`(game_id, version)` unique constraint; two open slots cannot walk the active version **backwards**;
activation clears Verified status **only on `VERIFIED → UNVERIFIED`** — an unconditional clear makes
every official upload abort against `game_official_ownerless_ck`, which is the only path the MVP
exercises.

### IMP-M4-04 — Bundle publication and asset serving

**Done when:** publication **filters**. Unpacking the whole archive under `/g/{gameId}/{version}/`
publishes the backend JAR to anonymous callers — `gameId` is in the hostname and the version is a
public catalog column, so the URL is derivable from a catalog page.

### IMP-M4-05 — Admin API, review queue and badges

---

## M5 — History, statistics, notifications

### IMP-M5-01 — Game history recording

**Done when:** a malformed outcome from game code cannot abort the whole recording transaction with
no retry path (`ghe_placement_ck`).

### IMP-M5-02 — Per-game statistics
### IMP-M5-03 — Notifications and the SSE stream

**Done when:** the retention purge is indexed **partially on having no subject**, so it can never
remove an actionable message out from under a live object; and no notification is permanently
unpurgeable because its subject never expires.

### IMP-M5-04 — Retention purge jobs

---

## M6 — Platform frontend

**Read first:** `docs/specs/platform-frontend/shell-architecture.md`,
`docs/requirements/platform-views.md`, `docs/requirements/platform-ui-library.md`,
`docs/requirements/onboarding-wizard.md`, `docs/specs/game-frontend/game-asset-serving.md`,
`docs/decisions/0007-game-frontend-separate-domain.md`.

### IMP-M6-01 — Design tokens and component library
### IMP-M6-02 — Shell, routing and auth tiers
### IMP-M6-03 — Account and profile views
### IMP-M6-04 — Room views and the STOMP client
### IMP-M6-05 — Game iframe host and postMessage relay

**Done when:** the shell validates `event.origin` against the game origin on every inbound message;
the iframe carries the sandbox attributes and CSP of `game-asset-serving.md`; no state is shared with
the game frontend other than by `postMessage` (`CLAUDE.md` AVOID).

### IMP-M6-06 — Catalog and history views
### IMP-M6-07 — Onboarding wizard

---

## Readiness gates

Populated from
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md).

<!-- GATES:BEGIN -->
The 2026-08-16 readiness audit returned **23 blockers. All 23 are now closed** — see
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
for the register and
[`../reviews/2026-08-16-implementation-readiness/remediation-plan.md`](../reviews/2026-08-16-implementation-readiness/remediation-plan.md)
for the plan that closed them.

**Every work item in the register above is ungated.** Status reverts to whatever the item's own
dependencies imply.

| Gate | Closed by | What changed |
|---|---|---|
| IR-01 | `local-environment.md` §1, §5, §7.9 | Bucket named `turnbase-bundles`, created by a one-shot `minio/mc` init step. The application asserts its existence and never creates it |
| IR-02 | `secrets-and-configuration.md` §1, §4; `local-environment.md` §4, §7.9 | Two roles created by `deploy/compose/initdb/01-roles.sql`. `POSTGRES_USER` is `turnbase_owner`, not `turnbase_app` — naming the app role there would silently hand it superuser |
| IR-03 | `platform-operations.md` FR-CICD-003, OQ-002 | Coverage gate narrowed to unit + integration, the two categories that run at PR time |
| IR-04 | **new** `deployment/observability.md` | Full wiring: Actuator scrape, Logback JSON → Promtail → Loki, OTLP → Tempo, Grafana provisioning, Alertmanager rules. Promtail chosen over the Loki Docker driver because a plugin install is a step a clean-machine bootstrap cannot assume |
| IR-05 | `platform-views.md` VW-PROF-002…003, VW-FREN | The owner is exempt from their own privacy settings, stated as a rule and applied to five conditions |
| IR-06 | `room-lifecycle.md` §3.3 | The outbox insert is conditional on `active_session_id IS NOT NULL`, the same trigger step 4's Lobby exemption already used |
| IR-07 | `room-lifecycle.md` §1.5 layer 3, §1.6 | Drain- and self-eviction-initiated socket closes are tagged; the disconnect handler skips them |
| IR-08 | `room-chat-websocket.md`, `room-websocket.md` | Chat carries `version: null` and never advances the counter. No second sequence: FR-MSG-006 defines a missed message as lost, not as a gap |
| IR-09 | `room-lifecycle.md` §3.2, §5.1 duty 2; `data-model.md` §2, §5 | Two halves — `lost_announced_at` is stamped by every inline path, and duty 2 is additionally narrowed on `leave_reason` as a backstop. New partial index `room_participant_unannounced_idx` |
| IR-10 | `room-lifecycle.md` §4 | `detachSession` step 3 is a fenced, version-bumping `UPDATE`. Without the fence a stale owner closes a live room; without the bump every client discards the `ROOM_CLOSED` |
| IR-11 | `room-lifecycle.md` §4, §5.1 duty 2; `data-model-accounts.md` §5 | **No new table.** Owed closure rides the existing deferred tail; duty 2 gains the host disposition. The erasure transaction writes participant departures only |
| IR-12 | `room-websocket.md`, `room-lifecycle.md` §3.3, `data-model.md` §6, `manifest-schema.md`, `game-rooms.md`, `game-contracts.md` OQ-002 | Wire kept, schema deferred, **v1 behaviour declared**: `aiPlayers` always empty, `ADD_AI_PLAYER` always `AI_NOT_SUPPORTED`, `capabilities.ai: true` rejected at validation, the "not an AI" clause removed |
| IR-13 | **new** `api-design/room-rest-api.md` | Five endpoints: create, list, get, join, leave. REST is membership only; every in-room mutation stays STOMP |
| IR-14 | `flows/02-room-to-game-start.md` step 6; `game-host-internals.md` §9.1 | `session:{id}` has exactly one writer, the Game Host. Flow 02 names the keys Orchestration does write |
| IR-15 | `game-host-internals.md` §8.1, §9.1; `orchestration-gamehost-protocol.md` | The session record gains `lastOutcome` and `lastFailure`, so a replayed burned sequence returns its own failure rather than the previous input's effects |
| IR-16 | `gamehost.proto` service and field comments; protocol doc | Forward gaps are normal and must be accepted. All three sequence cases are stated at the field, because a codegen reader never sees the prose table |
| IR-17 | `api-design/websocket.md` § `GAME_EVENT`; `game-contracts.md` NFR-SEC-002 | Every effect address is validated against the producing session's membership at fan-out. The per-user queue secures the subscription, not the address |
| IR-18 | `manifest-schema.md`, `file-uploads.md`, `flows/08-upload-to-play.md` | Phase A is a synchronous `422`; everything after `confirm` is the version resource's `FAILED` state |
| IR-19 | `api-design/input-validation.md`; `game-catalog.md` | Assigned an owner. Markdown → React elements client-side, no HTML string anywhere, so the `dangerouslySetInnerHTML` ban stands unweakened |
| IR-20 | `platform-operations.md` FR-JOB-013; `local-environment.md` §7.2; both schema docs | The expiry purge job exists and is named. It is the only mechanism that ever removes an actionable notification |
| IR-21 | `shell-architecture.md` §5; `game-asset-serving.md` §6.1 | `allow-scripts allow-same-origin`, owned by `game-asset-serving.md`. `allow-scripts` alone makes `event.origin` `"null"` and silently breaks the whole relay |
| IR-22 | `shell-architecture.md` §6 *(new section)* | The platform origin's CSP, with `frame-src` still owned by `game-asset-serving.md` §6.3. The delegation now resolves |
| IR-23 | **new** `platform-frontend/design-system.md`; `onboarding-wizard.md` | Design system specified and folded into `turnbase-frontend` (CON-002 amended); onboarding wizard **cut from v1** |

### Two resolutions that departed from the review's own suggestion

Recorded here because a future reader will otherwise reopen them.

- **IR-11 uses the existing deferred-tail mechanism rather than a new owed-closure table.** §5.1 duty
  2 already performs exactly this job for grace expiries resolved by a foreign instance, and a
  closure owed by an account deletion is the same shape of debt. ADR-0010's lesson is about keying
  such tables correctly, not about minting more of them.
- **IR-12 declares the v1 behaviour of the AI wire surface** rather than adding a schema
  representation or cutting `FR-HOST-003`. The protocol shape survives for when the AI interface
  lands; the implementer gets an unambiguous instruction today.

**IR-09's fix has two halves and Task 11 depended on the first** — that dependency is not visible
from either document, which is why it is written down here.
<!-- GATES:END -->
