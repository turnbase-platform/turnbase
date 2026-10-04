# Implementation Registry — Work Items

Conventions, status vocabulary, the milestone map and the meaning of each field live in
[INDEX.md](INDEX.md). Read that first.

Every item below carries:

- **Repo** — which submodule the work lands in.
- **Depends on** — items that must be `DONE` first.
- **Read first** — the minimum document set that fully determines the item. *An implementation agent
  should not need to read anything outside this list.* If it does, that is a defect in this registry;
  record it.
- **Satisfies** — the requirement IDs the item implements, document-qualified per the rule in
  [`../specs/INDEX.md`](../specs/INDEX.md).
- **Done when** — checkable without judgement.
- **Gate** — present only when a finding is open against the item. No item is gated today.
- **Remaining** — present only while an item is `PARTIAL` (or being continued): what its *Done when*
  clause still lacks. See INDEX.md *Partly done items*.

Paths in *Read first* are relative to the repository root.

**[`conventions.md`](conventions.md) applies to every item and is not repeated in read-lists.**
Package layout, Spotless, test suffixes, JaCoCo, branch and commit format, and cross-repo version
pinning are settled there. Items name it only where they are the item that *establishes* it.

---

## Register

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| **M0 — Bootstrap** ||||
| IMP-M0-01 | gRPC stubs and internal models | common | — | DONE |
| IMP-M0-02 | Public SDK artifacts (Maven + npm) | sdk | — | DONE |
| IMP-M0-03 | Platform Monolith skeleton | platform | — | DONE |
| IMP-M0-04 | Game Host skeleton | game-host | M0-01 | DONE |
| IMP-M0-05 | Frontend skeleton | frontend | — | DONE |
| IMP-M0-06 | Flyway baseline `V202608091200__baseline.sql` | platform | M0-03 | DONE |
| IMP-M0-07 | Local stack — compose profile | platform | M0-03, M0-04, M0-05 | DONE |
| IMP-M0-08 | Local stack — Helm chart (canonical) | platform | M0-07 | DONE |
| IMP-M0-09 | Configuration and secrets wiring | platform, game-host | M0-03, M0-04 | DONE |
| IMP-M0-10 | Observability baseline | platform, game-host | M0-03, M0-04 | DONE |
| IMP-M0-11 | CI/CD workflows | all | M0-01…05 | DONE |
| IMP-M0-12 | Seed data | platform | M0-06, M4-03 | DONE |
| **M1 — Accounts and sessions** ||||
| IMP-M1-01 | Error model, REST conventions, validation harness | platform | M0-03 | DONE |
| IMP-M1-02 | Rate limiter (Tiers 1–5) | platform | M1-01 | DONE |
| IMP-M1-03 | JWT key set, issuance, rotation | platform | M0-09 | DONE |
| IMP-M1-04 | Credential registration and login | platform | M1-01, M1-03 | DONE |
| IMP-M1-05 | Guest minting and purge | platform | M1-04 | DONE |
| IMP-M1-06 | Session lifecycle and displacement | platform | M1-04 | DONE |
| IMP-M1-07 | Profiles and privacy settings | platform | M1-04 | DONE |
| IMP-M1-08 | Account deletion and erasure | platform | M1-07 | DONE |
| IMP-M1-09 | Social graph — friendships and requests | platform | M1-07 | DONE |
| IMP-M1-10 | Google OAuth registration and login | platform | M1-04 | DONE |
| IMP-M1-11 | Account read and auth-method management | platform | M1-10 | DONE |
| **M2 — Rooms and realtime** ||||
| IMP-M2-01 | Room CRUD and listing | platform | M1-06, M2-03 | DONE |
| IMP-M2-02 | STOMP endpoint, auth, subscriptions | platform | M2-01, M2-03 | DONE |
| IMP-M2-03 | Ownership claim, lease, epoch fence | platform | M1-06 | DONE |
| IMP-M2-04 | Room event versioning and fan-out | platform | M2-01, M2-03 | DONE |
| IMP-M2-05 | Join, teams, readiness | platform | M2-04 | DONE |
| IMP-M2-06 | Host management and transfer | platform | M2-05 | DONE |
| IMP-M2-07 | Disconnect, grace deadlines, sweeps | platform | M2-03 | DONE |
| IMP-M2-08 | Reconnect and resync | platform | M2-07 | DONE |
| IMP-M2-09 | Room closure and the five detach paths | platform | M2-07 | DONE |
| IMP-M2-10 | Adoption and reconciliation jobs | platform | M2-03 | DONE |
| IMP-M2-11 | In-room chat | platform | M2-05 | DONE |
| IMP-M2-12 | Room invitations | platform | M2-01, M1-09 | DONE |
| **M3 — Game execution** ||||
| IMP-M3-01 | GDK backend API surface | sdk | M0-02 | DONE |
| IMP-M3-02 | Espresso context lifecycle | game-host | M0-04 | DONE |
| IMP-M3-03 | GDK host bridge and serialization boundary | sdk, game-host | M3-01, M3-02 | DONE |
| IMP-M3-04 | gRPC service implementation | game-host | M3-03 | DONE (session 89) |
| IMP-M3-05 | Orchestration client and session registry | platform | M3-04, M2-04, M2-06 | DONE (session 93) |
| IMP-M3-06 | Game input outbox and delivery | platform | M3-05 | DONE |
| IMP-M3-07 | Effect fan-out and spectator filtering | platform | M3-06 | DONE |
| IMP-M3-08 | Session teardown as a durable to-do | platform | M3-05, M2-09 | DONE |
| IMP-M3-09 | Game failure handling | platform, game-host | M3-07, M2-09 | DONE |
| IMP-M3-10 | The first official game | sdk consumer | M3-03, M3-05 | DONE |
| IMP-M3-11 | GDK test harness | sdk | M3-01, M3-03, M3-13 | DONE |
| IMP-M3-12 | FE GDK client (`@turnbase/gdk`) | sdk | M0-02 | DONE |
| IMP-M3-13 | Shared bundle validator module | sdk, platform | M4-03, M3-03 | DONE |
| **M4 — Catalog and upload** ||||
| IMP-M4-01 | Catalog listing and game detail | platform | M1-01 | DONE (session 61) |
| IMP-M4-02 | Manifest schema validation | platform | M0-06 | DONE |
| IMP-M4-03 | Upload pipeline and version state machine | platform | M4-02 | DONE |
| IMP-M4-04 | Bundle publication and asset serving | platform | M4-03 | DONE |
| IMP-M4-05 | Admin API — review queue and badges | platform | M4-03 | DONE (session 60) |
| **M5 — History, statistics, notifications** ||||
| IMP-M5-01 | Game history recording and query API | platform | M3-09 | DONE |
| IMP-M5-02 | Per-game statistics | platform | M5-01 | DONE |
| IMP-M5-03 | Notifications and the SSE stream | platform | M1-06, M1-07 | DONE |
| IMP-M5-04 | Retention purge jobs | platform | M5-01, M5-03 | DONE |
| **M6 — Platform frontend** ||||
| IMP-M6-01 | Astryx integration and the `ui/` boundary | frontend | M0-05 | DONE |
| IMP-M6-02 | Shell, routing and auth tiers | frontend, platform | M6-01 | DONE (session 75) |
| IMP-M6-03 | Account and profile views | frontend | M6-02, M1-07, M1-11 | DONE |
| IMP-M6-04 | Room views and the STOMP client | frontend | M6-02, M2-08 | DONE |
| IMP-M6-05 | Game iframe host and postMessage relay | frontend | M6-04, M3-07 | DONE |
| IMP-M6-06 | Catalog and history views | frontend | M6-02, M4-01, M5-01 | DONE (session 108) |
| ~~IMP-M6-07~~ | ~~Onboarding wizard~~ | frontend | — | CANCELLED |
| **M7 — MVP review remediation** ||||
| IMP-M7-01 | Room list and join views | frontend | M6-04 | DONE (session 117) |
| IMP-M7-02 | Room lobby view | frontend | M7-01 | DONE |
| IMP-M7-03 | In-game and results views, game iframe mount | frontend | M7-02, M6-05 | DONE |
| IMP-M7-04 | Room chat panel | frontend | M7-02 | DONE |
| IMP-M7-05 | Close rooms abandoned in the Lobby | platform | M2-08 | DONE |
| IMP-M7-06 | Leaving mid-game reaches the engine | platform | M3-09 | DONE |
| IMP-M7-07 | Populate `reservedSlot` on the rooms list | platform | M2-07 | DONE |
| IMP-M7-08 | Tic-Tac-Toe rejects a malformed action | game | M3-10 | DONE |
| IMP-M7-09 | Game Host warm-up before readiness | game-host | M3-10 | DONE |
| IMP-M7-10 | Lifecycle logging for rooms, auth and sessions | platform, game-host | M3-10 | DONE |
| IMP-M7-11 | Anonymous session probe, cookie flag, scheduler bean | platform, frontend | M6-02 | DONE |
| IMP-M7-12 | Local stack first-run path | platform | M0-05 | DONE |
| IMP-M7-13 | MVP browser acceptance suite | frontend | M7-03, M7-05, M7-06 | DONE |
| **M8 — Regression review remediation and MVP view completeness** ||||
| IMP-M8-01 | Seeded users get their privacy settings | platform | M1-07, M3-10 | DONE |
| IMP-M8-02 | The friends list query runs on PostgreSQL | platform | M1-09 | DONE |
| IMP-M8-03 | A forfeit and a timeout are recorded | platform | M5-01, M7-06 | DONE |
| IMP-M8-04 | Rooms emptied around a game end are closed | platform | M7-05, M2-09 | DONE |
| IMP-M8-05 | Tic-Tac-Toe takes only an integer `cell` | game | M7-08 | DONE |
| IMP-M8-06 | Shell, navigation, landing and redirects | frontend | M7-11 | DONE |
| IMP-M8-07 | Login, registration and OAuth completion views | frontend | M8-06 | DONE |
| IMP-M8-08 | Catalog, game detail and create-room options | frontend | M6-06 | DONE |
| IMP-M8-09 | Rooms list and join views | frontend | M7-01, M7-07 | DONE |
| IMP-M8-10 | The game room: lobby, in-game and results | frontend | M7-03, M7-04, M8-04, M8-17 | DONE |
| IMP-M8-11 | Profile view | frontend | M8-01, M8-03, M6-03 | DONE |
| IMP-M8-12 | Friends view | frontend | M8-02, M8-14 | READY |
| IMP-M8-13 | Account settings view | frontend | M8-01, M6-03 | READY |
| IMP-M8-14 | Notifications bell and panel | frontend | M6-06, M5-03 | READY |
| IMP-M8-15 | The client retries a rate-limited subscribe | frontend | M6-04 | READY |
| IMP-M8-16 | The acceptance suite covers every view and the review's gaps | frontend | M8-01…15, M8-17 | READY |
| IMP-M8-17 | The room resource names the viewer's membership | platform | M2-09 | DONE |

**93 live items.** `IMP-M8-01…16` were added 2026-10-03 from the [MVP regression review](../reviews/2026-10-03-mvp-regression-review/INDEX.md): five close its backend and game findings, nine give every MVP view a minimal working UI (the game room is `IMP-M8-10`), and the last two close the client follow-up and re-run the review as a suite. `IMP-M7-01…13` were added 2026-10-01 from the [MVP implementation review](../reviews/2026-10-01-mvp-implementation-review/INDEX.md): the first four close its MR-01 (the room views `IMP-M6-04`/`05` did not build), the rest close MR-02…MR-11 and add the acceptance suite the review was run by hand. IMP-M6-07 is cancelled: IR-23 cut the onboarding wizard from v1, so
`onboarding-wizard.md`'s FR-ONB-* and NFR-ONB-* have no implementing item by design. The heading is
kept below so the number is never reused. `IMP-M3-12` was added 2026-08-22, closing IMP-GATE-05 — see
its section under M3. `IMP-M3-13` was added 2026-09-30, closing IMP-GATE-91 — see its section under M3. `IMP-M1-10` was added 2026-09-06, closing IMP-GATE-26, and `IMP-M1-11` on
2026-09-26, closing IMP-GATE-78 — see their sections under M1.

Statuses are seeded as `READY`. **No item is gated** — the 2026-08-16 audit's 23 blockers are all
closed (see *Readiness gates* at the end for what each fix changed). An item's real status is
whatever its own *Depends on* implies.

---

## M0 — Bootstrap

### IMP-M0-01 — gRPC stubs and internal models

**Repo:** `turnbase-common` · **Depends on:** — · **Publishes:** `io.turnbase:turnbase-grpc`

**Done 2026-08-20 (session 14).** `./mvnw verify` green with 15 tests, `buf lint` clean, both
services' stubs in the jar under `io.turnbase.grpc.gamehost.v1`, and a consumer project compiling and
running against the client stub and the server base class. **CI green on `master`** (`build` and
`contract`), which is the bar — the first run failed in both jobs and neither failure was reproducible
locally:

- `actions/setup-java` has **no `graalvm-community` distribution**. GraalVM CE needs
  `graalvm/setup-graalvm`. Applies to `IMP-M0-03` and `IMP-M0-04` too.
- `buf breaking` on a push compared against `HEAD~1`, which on the commit that *introduces* the proto
  is a tree with no protos: `Module "path: "."" had no .proto files` — a message that names the
  module rather than the missing baseline. It ran on pull requests only until 2026-09-05; with PRs
  suspended (ADR-0012) that gate would never fire, so it now runs on every push against
  `.git#ref=HEAD~1`, which has a baseline in every case except the one above.

**Dependabot opened five PRs within a minute of the first push**, one of them reverting the
deliberate `protobuf-maven-plugin` 4.1.3 pin to the 5.x that does not accept this configuration. The
ignore entry carrying that reason is in `.github/dependabot.yml`; expect the same the day each
remaining repo lands.

**Closed:** IMP-GATE-03 (opened and closed 2026-08-20) — the clause "resolves from both
`turnbase-platform` and `turnbase-game-host`" required this item's own dependents to exist first. The
half that is checkable here (install, then compile and run a consumer against both the client stub
and the server base class) stayed; the cross-repo half moved to `IMP-M0-03` and `IMP-M0-04`, which
are the items that have a consumer to check it with.

**Closed:** IMP-GATE-02 (opened and closed 2026-08-20) — "copies it into `src/main/proto/` at build
time" contradicted ADR-0012's own guarantee that each repo is independently usable without the root.
ADR-0012 is amended: the copy is a **committed file** at
`src/main/proto/turnbase/gamehost/v1/gamehost.proto`, nothing in `turnbase-common`'s build reads
outside the repository, and the drift guard is `scripts/sync-proto.sh --check` in the parent's
`pre-push` hook. `conventions.md` §5 carries the rule.

**Closed:** IMP-GATE-01 (opened and closed 2026-08-20) — `gamehost.proto` declared `java_package =
"com.turnbase.gamehost.grpc.v1"` against an `io.turnbase.grpc` root everywhere else. The proto now
declares `io.turnbase.grpc.gamehost.v1`, and `conventions.md` §5 states the rule so the next
generated artifact does not re-decide it. The same pass retired the stale "Proto home" open point in
`orchestration-gamehost-protocol.md` and the `buf.yaml` comment that still promised a shared buf
workspace ADR-0012 had rejected.

**Read first:**
- `docs/specs/internal-grpc/gamehost.proto` — the authoritative contract
- `docs/specs/internal-grpc/buf.yaml`
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — semantics, idempotency, error mapping

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-REG-001…004

**Done when:** `./mvnw verify` produces a jar containing generated client and server stubs for every
service in `gamehost.proto`; `buf lint` and `buf breaking` run in CI; `./mvnw install` puts the
artifact in the local Maven repository, where a **consumer project compiles and runs against both the
client stub and the server base class** and does not receive a gRPC transport transitively; the
generated code lands under `io.turnbase.grpc` and the build floor of `conventions.md` §6 is in place.

**The consuming repositories check their own half.** This clause used to require the artifact to
"resolve from both `turnbase-platform` and `turnbase-game-host`", which it cannot: neither has a build
until `IMP-M0-03`/`IMP-M0-04`, and `IMP-M0-04` depends on *this* item (IMP-GATE-03). The real
cross-repo resolution is now a *Done when* clause on each consumer, where there is something to
resolve it from.

**Note:** the `.proto` is the source of truth. Where the prose in
`orchestration-gamehost-protocol.md` disagrees with it, the proto wins for wire shape — but raise
the disagreement rather than silently following one.

**The proto here is a committed copy.** The authoritative file is
`docs/specs/internal-grpc/gamehost.proto` in this repository; `turnbase-common` tracks a copy at
`src/main/proto/turnbase/gamehost/v1/gamehost.proto`, refreshed by `scripts/sync-proto.sh`. Editing
the copy is a defect — the change belongs in the spec directory (`conventions.md` §5, ADR-0012).

**Consumers pin this artifact by exact version**, never `-SNAPSHOT` in a committed pom. The release
order that keeps the three repos coherent is in `conventions.md` §5.

---

### IMP-M0-02 — Public SDK artifacts

**Repo:** `turnbase-sdk` · **Depends on:** — · **Publishes:** `io.turnbase:turnbase-sdk` (Maven) + npm package

**Done 2026-08-22 (session 15).** `./mvnw verify` green (enforcer, Spotless, Checkstyle, Error
Prone + NullAway, tests, merged JaCoCo), `./mvnw install` publishes locally, and a throwaway
`provided`-scope consumer compiles a `GameState` implementor against the jar. `npm run
lint`/`typecheck`/`build`/`test`/`npm pack --dry-run` all green; the tarball carries
`dist/index.{js,cjs,d.ts,d.cts}`. **CI green on `master`**, both jobs, first push — the two traps
`IMP-M0-01` hit (`actions/setup-java` has no `graalvm-community` distribution; no `buf breaking`
baseline on a push) don't apply here (no proto, no gRPC), and `conventions.md` §6 already carried
the GraalVM fix into this workflow.

Two of the two Dependabot PRs opened on first push were legitimate and merged directly
(`actions/setup-node` 6→7, `@eslint/js` 9.39.1→10.0.1); neither touched a protected pin.

**The `typescript` pin needed for `typescript-eslint@8.67.0`'s peer range (`<6.1.0`) was found
by `npm install` itself**, not by reading a spec: the latest `typescript` (7.0.2) fails
`ERESOLVE`. Pinned to `6.0.3`, with the `ignore` entry landing in `dependabot.yml` in the same
commit as the pin (`conventions.md` §6).

**Closed:** IMP-GATE-04 (opened and closed 2026-08-22) — the read-list named `backend-gdk-api.md`
§1–3 and the item claimed FR-GDK-001, but §3's `TurnBaseGame` references ten types defined in §4 and
§7 and its default method calls `PlayerJoinedResult.of(state)`, so the §1–3 surface cannot compile
without all of §§3–8 — which is `IMP-M3-01`'s own *Done when*. Fixed by narrowing this item to the
build-and-publish floor: `FR-GDK-001` and the whole Java type surface stay with `IMP-M3-01`, which
already claimed them.

**Closed:** IMP-GATE-05 (opened and closed 2026-08-22) — `game-development-experience.md`
FR-FEGDK-001…009 (the `TurnBaseClient` class, ready handshake, origin validation, `sendAction`) was
claimed only by `IMP-M6-05`, which is in `turnbase-frontend` and implements the shell's half of the
boundary; no item in `turnbase-sdk` — the repo that publishes `@turnbase/gdk` — owned the client.
Fixed by adding `IMP-M3-12` below and correcting `IMP-M6-05`'s *Satisfies*.

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` §2 (artifact and packaging, package-layout table), §5
  (`GameState` only — the rest of §§3–8 is `IMP-M3-01`)
- `docs/specs/gdk-api/frontend-gdk-api.md` §2 (distribution and packaging), §5, §6, §9, §10 (the
  declared types only — `TurnBaseClient` itself is `IMP-M3-12`)
- `docs/specs/gdk-api/INDEX.md`
- `docs/requirements/game-development-experience.md` FR-GDK-014, FR-GDK-015, NFR-COMPAT-001
- `docs/decisions/0012-repo-strategy-polyrepo-submodules.md` — Release Strategy (Maven Central + npm)

**Satisfies:** `game-development-experience.md` FR-GDK-014, FR-GDK-015, NFR-COMPAT-001

**Done when:** both artifacts build and publish locally — `./mvnw install` puts
`io.turnbase:turnbase-sdk` in the local repository and `npm pack` produces a tarball carrying ESM,
CJS and `.d.ts`. The jar's class files are **major version 65** (Java 21) and the build enforces it
(`maven.compiler.release=21` plus the enforcer's `[21,22)`). The jar declares **no dependency on
`io.turnbase:turnbase-grpc` or `turnbase-game-host`**, and the enforcer's `bannedDependencies` fails
the build if one appears (`turnbase-sdk/CLAUDE.md`). A throwaway consumer compiles against the jar at
`provided` scope (FR-GDK-014). Checkstyle fails the build on a public type with no Javadoc,
demonstrated against a deliberate violation — `turnbase-sdk` is the one repository that runs
Checkstyle, configured for public-type Javadoc only (`conventions.md` §2), because that is the
documentation a third-party developer gets. The npm package declares **zero runtime dependencies**
(FR-FEGDK-008) and `strict: true`. The five packages of `backend-gdk-api.md` §2 exist, each carrying
`@NullMarked` (ADR-0015) — nullability here is part of the published contract, read by a third-party
developer's IDE.

**No `TurnBaseGame`, no context/result/effect types, and no `TurnBaseClient` ship here** — those are
`IMP-M3-01` and `IMP-M3-12`. NFR-COMPAT-001's compatibility regime begins at v1.0.0, so the committed
pom version is `0.1.0-SNAPSHOT` deliberately: 0.x may still break.

---

### IMP-M0-03 — Platform Monolith skeleton

**Repo:** `turnbase-platform` · **Depends on:** —

**Done 2026-09-04 (session 16).** Spring Boot 3.5.7 on Java 21 starts; `8080` serves HTTP, `8081` is
management with its bind address driven by `MANAGEMENT_SERVER_ADDRESS` — verified live loopback-only
when set and all-interfaces when unset; health/readiness/liveness all return `200` and report nothing
about the Game Host. The twelve empty feature packages exist under `io.turnbase.platform` and
`ApplicationModules.verify()` is green. `io.turnbase:turnbase-grpc` resolves and compiles (a
`GameHostServiceGrpc` blocking-stub test, plus the Modulith test). The Dockerfile packages a
pre-built jar rather than rebuilding inside the image — verified end to end: image builds, container
starts, actuator responds. **CI green on `master`**, all steps including the container build.

Closing three Dependabot PRs opened on the first push surfaced two more traps, now in
`conventions.md` §6: a **major**-version bump (Spring Boot 4.1.1, eclipse-temurin 25) is not a
routine update against a pinned stack, and **Dependabot's own `pull_request` runs get no repository
secrets**, so every Dependabot PR against this repo fails the bootstrap install step regardless of
content until the bootstrap window closes — apply anything legitimate directly and push instead of
waiting on that check.

**Closed:** IMP-GATE-07 (opened and closed 2026-09-02) — the *Done when* clause required the
`io.turnbase:turnbase-grpc` client stubs to "resolve at the exact pinned `<turnbase-common.version>`"
with `conventions.md` §5's absolute "no `-SNAPSHOT` in a committed pom" — but `turnbase-common` has
never been tagged (tagging is a human action, ADR-0012) and the publish workflow that would put a
release in GitHub Packages is `IMP-M0-11`, which **depends on** this item. The clause was
unsatisfiable as written: no release exists, and the pipeline that would produce one has not been
built. Fixed: `conventions.md` §5 gained a bootstrap exception — until `turnbase-common`'s first tag,
consumers pin its current development version and resolve it from the local install `IMP-M0-01`
already produces; the real-registry resolution check moves to `IMP-M0-11`. This item's clause below
is corrected to match.

**Closed:** IMP-GATE-06 (opened and closed 2026-09-02) — this item's read-list cites
`platform-operations.md` CON-010, which said "Integration and E2E tests use Docker Compose... within
the CI runner." That contradicts FR-CICD-004 in the same document — corrected 2026-08-20 to say the
integration tier **never** uses Docker Compose, only Testcontainers — and `conventions.md` §3, which
states the same rule. CON-010 was missed in the 2026-08-20 pass that fixed FR-CICD-004. Fixed: CON-010
now reads "E2E tests use Docker Compose... Integration tests use Testcontainers... never a stack
started separately (FR-CICD-004)."

**Read first:**
- `docs/specs/deployment/local-environment.md` §1, §3, §7.9
- `docs/requirements/platform-operations.md` — service topology, CON-010/011
- `docs/decisions/0001-local-first-mvp-platform.md`
- `docs/decisions/0014-modular-monolith-spring-modulith.md` — **in full**
- `docs/implementation/conventions.md` §§1–3, 6 — this item establishes them for the largest repo

**Satisfies:** `platform-operations.md` FR-DEPLOY-001…003, CON-010, CON-011

**Done when:** Spring Boot 3.5+ on Java 21 starts; `8080` serves HTTP and `8081` is the management
port bound per §1 (loopback under compose, unbound under Kubernetes — **the two profiles differ and
getting this wrong breaks the readiness probes**); a Dockerfile produces `turnbase/platform`;
actuator health and readiness respond, and **readiness does not depend on the Game Host**. The
`io.turnbase:turnbase-grpc` client stubs resolve and compile (`conventions.md` §5; the half of
`IMP-M0-01` that only a consumer can check, IMP-GATE-03) — against the local install, pinned to
`turnbase-common`'s current development version per §5's bootstrap exception (IMP-GATE-07), since no
tagged release exists yet.

Plus the build floor of `conventions.md` §6, which exists nowhere until this item creates it:

1. `./mvnw` committed, `.sdkmanrc` pinning `21.0.2-graalce`.
2. **Spotless** with `googleJavaFormat`, bound to `validate`, and `.mvn/jvm.config` carrying the
   `--add-exports` flags it needs on JDK 21 (§2 — the first run fails confusingly without them).
3. **Error Prone + NullAway** ([ADR-0015](../decisions/0015-static-analysis-error-prone-nullaway.md)):
   default `ERROR` patterns at `ERROR`, JSpecify `@NullMarked` on every package, generated code and
   Spring injection points excluded from NullAway's scope. The same `.mvn/jvm.config` gains
   `-XDcompilePolicy=simple` and `--should-stop=ifError=FLOW`.
4. **JaCoCo** with separate unit and integration exec files, `jacoco:merge`, and one `jacoco:check`
   at 70% line over the merged data (§3 — the one-execution wiring silently measures unit only).
5. **`spring-modulith-starter-core`**, the twelve feature packages of ADR-0014 §1 created empty, and
   a test asserting `ApplicationModules.of(TurnBaseApplication.class).verify()`. It passes trivially
   today; it exists so that the first violation fails a build rather than a review.
6. **`.githooks/pre-push`** running `spotless:check` and the compile, plus a README line telling a
   human to `git config core.hooksPath .githooks` once (§4 — a hook nobody enables is not a hook).

**Every item in that list is cheap now and prohibitive later.** Error Prone and NullAway in
particular: retrofitted at work item forty they arrive as one unreviewable change and get downgraded
to warnings, which is the same as not having them.

**Root package is `io.turnbase.platform`, packaged by feature.** Getting this wrong is a rename
across forty work items later.

---

### IMP-M0-04 — Game Host skeleton

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M0-01

**Done 2026-09-04 (session 17).** GraalVM CE 21.0.2 (`ghcr.io/graalvm/jdk-community:21.0.2`) boots
with Espresso available; `9090` serves `GameHostService` (UNIMPLEMENTED until `IMP-M3-04`), `8081` is
management only — `server.port=-1` disables the main servlet container so there is no port `8080`
here. A background `Register` attempt against `GameHostRegistryService` retries for the 60-second
budget without blocking startup, proven against an in-process stub (`IMP-GATE-08`). A trivial
Espresso guest context is created and disposed against the running GraalVM CE 21 JDK. `CI green on
master`, including the container build; the guest JDK 21 symlink and both ports verified live in the
built image, not just configured.

**Closed:** IMP-GATE-09 (opened and closed 2026-09-04) — the item requires the process to register
with the Platform Monolith, but no document names the address the Game Host dials to reach it.
`local-environment.md` §7 claims to be the whole tunable surface and §2's diagram shows the registry
service sharing the monolith's `8080` listener, but §7.8 (the Game Host's own properties) had no entry
for it — a missing configuration key, the same class of gap IR-24 closed for
`turnbase.room.spectator-capacity`. Fixed: `local-environment.md` §7.8 gained
`turnbase.gamehost.orchestration-address` (default `platform:8080`, following the `<service-name>:<port>`
convention every other compose dependency in §7.9 already uses).

**Closed:** IMP-GATE-08 (opened and closed 2026-09-04) — the *Done when* clause required "the process
registers with the Platform Monolith per §3's 60-second budget," but the Platform Monolith's server
side of `GameHostRegistryService` (`Register`/`Heartbeat`/`ReportContexts`/`Deregister`) is not
implemented until `IMP-M3-05`, which depends on `IMP-M3-04` and `IMP-M2-04` — nearly all of M2 and
M3's game-host chain, none of which `IMP-M0-04` (depends only on `IMP-M0-01`) can assume. Unsatisfiable
as written: there is no live registry service to register against at this point in the build order.
Same shape as `IMP-GATE-03`. Fixed: the clause below is narrowed to what a consumer skeleton can check
— the client-side `Register` call runs at startup and is exercised against an in-process stub
`GameHostRegistryService`, proving the retry/timeout logic and that the server base classes resolve
and link. The real end-to-end check — registration against a live Platform Monolith inside the
60-second budget — is now `IMP-M3-05`'s own *Done when* clause, added there, since M3-05 is the item
that gives the platform side of `GameHostRegistryService` a real implementation.

**Read first:**
- `docs/specs/deployment/local-environment.md` §1, §3 (especially *The 120-second suppression window
  and Game Host registration*), §7.8
- `docs/specs/game-host/game-host-internals.md` §1 (topology only), §11 (registration, health, drain)
- `docs/decisions/0005-game-sandbox-espresso-spike.md`
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`

**Satisfies:** `platform-architecture.md` FR-REG-001…004; `platform-operations.md` FR-DEPLOY-001…003

**Done when:** a GraalVM CE for JDK 21 image starts with Espresso available; `9090` serves gRPC and
`8081` is management; a trivial guest context can be created and disposed. At startup the process
attempts a `Register` call against `GameHostRegistryService` and retries per §3's budget until it
succeeds or the deadline elapses; **this is proven against an in-process stub registry service**, not
a live Platform Monolith (IMP-GATE-08) — the cross-repo, end-to-end check moves to `IMP-M3-05`. The
`io.turnbase:turnbase-grpc` **server** base classes resolve and compile (`conventions.md` §5; the half
of `IMP-M0-01` that only a consumer can check, IMP-GATE-03) — against the local install, pinned to
`turnbase-common`'s current development version per §5's bootstrap exception (IMP-GATE-07), since no
tagged release exists yet.

**Constraint:** host JVM is Java 21; guest is Espresso running Java 21. There is no CE build for JDK
23 — see `CLAUDE.md`.

Root package `io.turnbase.gamehost`; the build floor of `conventions.md` §6 applies here as it does
to the monolith — Spotless, Error Prone, NullAway (ADR-0015), JaCoCo, the `pre-push` hook. **Spring
Modulith does not** — ADR-0014 is about the monolith's twelve features, and the Game Host is one
bounded thing.

---

### IMP-M0-05 — Frontend skeleton

**Repo:** `turnbase-frontend` · **Depends on:** —

**Done 2026-09-04 (session 18).** Vite 8 + React 19.2 + TypeScript 6.0.3 builds; ESLint (flat
config, `typescript-eslint` strict + stylistic type-checked, `eslint-plugin-react-hooks`,
`eslint-config-prettier` last) and Prettier both run in CI and in `.githooks/pre-push`; a
multi-stage Dockerfile (Node build stage → nginx-alpine) produces the static bundle — built,
run, and checked in a real browser via Playwright: the page serves, the Astryx `Button` renders
themed, `data-astryx-theme="neutral"` lands on `<html>`, and `body`'s computed font resolves to
the self-hosted Figtree. The dev server proxies `/api` and `/ws` to
`http://turnbase.localhost:8080`. `.nvmrc` pins `22.20.0`; `package.json` carries `engines.node`
and the `astryx` script. **CI green on `master`**, first push, both jobs.

Astryx landed at **`0.5.2`**, not the `0.4.3` `design-system.md` §1 names — that value was
current when the ADR was written (2026-08-17); npm's `latest` had moved on by the time this item
ran (`0.5.2`, released 2026-08-30). Not treated as a spec defect: the normative instruction is
"pin exact versions, no `^`/`~`", which is satisfied regardless of which exact version, and no
*Done when* clause names a version number. Peer-checked against `0.5.2`: `@stylexjs/stylex`
pinned to `0.19.0` (core's own peer range).

**`<LinkProvider>` is deferred to `IMP-M6-02`.** `shell-architecture.md` §2 and `design-system.md`
§2 both describe mounting `<Theme>` and `<LinkProvider>` together as "the shell's two providers,"
but `LinkProvider` needs `react-router`'s `Link`, and routing is `IMP-M6-02`'s own dependency to
add — there is no router here for it to wrap. This item's own text names only the three CSS
imports and `<Theme>` as required at skeleton time, so only those landed; `App.tsx` says so
inline.

**Figtree self-hosted via `@fontsource/figtree`** (400/600/700 — the weights `theme-neutral`'s
heading/body scale actually references), not a raw font-file fetch: the npm package ships the
`.woff2`/`.woff` files and `@font-face` rules pre-written, bundled by Vite as ordinary static
assets from our own origin — satisfying `font-src 'self'` without hand-managing binary font
files in the repo.

**Three Vitest/TypeScript version traps, none named in any spec:**
- `typescript-eslint@8.69.0`'s peer range is still `>=4.8.4 <6.1.0` — the exact trap `IMP-M0-02`
  found. `typescript` pinned to `6.0.3` again.
- `jsdom@30.x` raises its own `engines` floor to `^22.22.2 || ^24.15.0 || >=26.0.0`, past what
  `.nvmrc` pins (`22.20.0`) — `npm install` only warns (`EBADENGINE`), it doesn't fail, so this
  is easy to install by accident. Pinned to `29.1.1`.
- Vitest 5 dropped `coverage.all`; specifying `coverage.include` now collects coverage for every
  matched file whether or not a test imports it, which is the same "no silent gap" behaviour
  `all: true` used to name. `vitest.config.ts` must import `defineConfig` from `vitest/config`,
  not `vite` — the latter's `UserConfigExport` doesn't know about the `test` key, and `tsc -b`
  only caught it because a stale incremental build cache had hidden it locally on the first
  `npm run build`.

**Five Dependabot PRs on first push, three closed:** `docker/build-push-action` 6→7 and `nginx`
1.29→1.31-alpine were routine and merged directly. Closed and ignored: `jsdom` 29.1.1→30.0.1 (the
engine-floor trap above) and the Docker build stage's `node:22.20.0-alpine`→`26.8.1-alpine` (CI
passed — the build stage happens to still compile under Node 26 — which is not the same claim as
"the project has adopted Node 26"; the base image moves when `.nvmrc` does). Both ignore entries
landed in `dependabot.yml` in their own follow-up commits, per `conventions.md` §6.

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §1, §2
- `docs/specs/platform-frontend/design-system.md` §1–§2 — the Astryx packages and the setup that
  must land in the skeleton, not later
- `docs/specs/deployment/local-environment.md` §1, §2 (*Both origins are one listener*), §7.7

**Satisfies:** `platform-operations.md` FR-DEPLOY-001…003

**Done when:** Vite + React 19 + TypeScript builds; Prettier and ESLint run in CI; a Dockerfile
produces the static bundle; the dev server proxies to `turnbase.localhost:8080`; `.nvmrc` pins the
Node version and `package.json` carries `engines.node` and the `astryx` script.

The lint stack is pinned in `conventions.md` §2 rather than left to `npm create vite`: **ESLint flat
config, `typescript-eslint` strict + stylistic (type-aware), `eslint-plugin-react-hooks`, and
`eslint-config-prettier` last.** `tsconfig.json` runs `strict: true` — the TypeScript half of
ADR-0015's argument, and equally impossible to adopt later. Also `.githooks/pre-push` running
`npm run lint && npm run typecheck`.

**Astryx is installed here, not in M6.** The three CSS imports and the `<Theme>` provider are what
make *any* view render correctly, so a skeleton without them produces screens that look almost right
and get corrected screen by screen later. Specifically:

- Exact-pinned deps: `@astryxdesign/core`, `@astryxdesign/theme-neutral`, `@stylexjs/stylex`; and
  `@astryxdesign/cli` as a dev dependency. **No `^` on any of them** — Astryx is Beta at 0.4.3.
- `src/index.css` imports `reset.css` → `astryx.css` → `theme.css`, **in that order**. The order is
  the cascade-layer order; getting it wrong renders built-in defaults with no error.
- `data-astryx-theme` on `<html>`, and Figtree self-hosted as `woff2` (the CSP sets `font-src 'self'`,
  and the theme names the font without loading it).

**No Vite plugin, no PostCSS, no Babel config.** Astryx ships pre-built CSS. If you find yourself
adding a StyleX build plugin, stop — that is `@astryxdesign/build`, and it is for compiling Astryx
from source, which this project never does.

---

### IMP-M0-06 — Flyway baseline

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-03

**Done 2026-09-05 (session 20).** `V202608091200__baseline.sql` transcribes all twenty tables from
the six schema documents, in the order and with the extensions/sequence/deferred FK fixed by
`schema-migrations.md` §5; `db/schema.sql` is committed alongside it. Verified against a real
Postgres 16 via Testcontainers (`FlywayBaselineIT`): the migration succeeds, creates exactly the
twenty expected tables, and a re-run applies zero migrations. `TurnBaseApplicationIT` boots the full
application against the same image, proving Flyway runs at startup per `schema-migrations.md` §3.
**CI green on `master`**, including the newly-wired `-Pintegration` step.

Exercising this path for the first time surfaced two dormant defects, fixed in the same session:
`ModularityTests.java` never matched surefire's `**/*Test.java` include (renamed to
`ModularityTest.java`), and `spring-modulith` 2.1.1 is binary-incompatible with Spring Boot 3.5.16
(`NoSuchMethodError` on `ConfigDataEnvironmentPostProcessor.applyTo` — 2.x targets a newer Boot
generation); pinned to 1.4.13, the latest release actually compatible with this Boot line. Neither
had ever run: the Modulith verification test — the thing ADR-0014 relies on to catch a feature
boundary violation — has been silently absent from every green build since IMP-M0-03.

**Read first:** all six schema documents, in this order —

1. `docs/specs/platform/data-model.md` (shared conventions **and** room/session tables)
2. `docs/specs/platform/data-model-accounts.md`
3. `docs/specs/platform/data-model-social.md`
4. `docs/specs/platform/data-model-catalog.md`
5. `docs/specs/platform/data-model-history.md`
6. `docs/specs/platform/data-model-notifications.md`

Plus `docs/specs/deployment/schema-migrations.md` and `docs/decisions/0011-schema-migrations.md`.

**Satisfies:** `platform-operations.md` FR-DB-001…004, CON-012

**Closed:** IMP-GATE-10 (opened and closed 2026-09-05) — the *Done when* clause named the baseline
file `V1__baseline.sql`, but ADR-0011 §5 and `schema-migrations.md` §§1–2 mandate timestamp-based
naming (`V<YYYYMMDDHHmm>__<snake_case_description>.sql`, precisely to avoid the collision a
sequential scheme produces across parallel branches) and both already name the actual baseline file
`V202608091200__baseline.sql`. Fixed: this registry entry — the one document that had it wrong — now
names `V202608091200__baseline.sql` throughout; ADR-0011 and `schema-migrations.md` needed no change.

**Closed:** IMP-GATE-11 (opened and closed 2026-09-05) — `schema-migrations.md` §5 names `shedlock`
as one of the baseline's tables, but no document in the read-list — nor any other document in the
corpus — gives its columns, so the *Done when* clause ("every table... named in the six documents")
could not be satisfied for this one table by transcription alone. Fixed: `schema-migrations.md` §5
now states `shedlock`'s DDL explicitly, noting it is ShedLock's own fixed `JdbcTemplateLockProvider`
schema rather than a TurnBase design choice.

**Done when:** `V202608091200__baseline.sql` creates every table, constraint and index named in the
six documents; Flyway migrates a clean Postgres 16 to completion; a re-run is a no-op; the FK graph
admits the creation order used.

**This item is the first real test of whether the schema documents are mutually consistent.** Any
disagreement found while transcribing is a **specification** defect: fix the document, then the SQL.
Do not reconcile silently in the migration.

**Two constructs are easy to miss.** `data-model.md` §5 adds the partial index
`room_participant_unannounced_idx ON room_participant (room_id) WHERE left_at IS NOT NULL AND
lost_announced_at IS NULL` — the deferred-tail scan of `room-lifecycle.md` §5.1 duty 2 is a sequential
scan without it. And `data-model.md` §4 is **two** durable-work tables, not one: `session_teardown`
keyed by `session_id` (never by room — ADR-0010) and `game_input_outbox` with `session_id NOT NULL`.

---

### IMP-M0-07 — Local stack, compose profile

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-03, M0-04, M0-05

**Done 2026-09-05 (session 22).** `deploy/compose/docker-compose.yml` (core: Postgres, Redis,
MinIO, `minio-init`, Platform Monolith, Game Host) and `docker-compose.observability.yml`
(Prometheus, Grafana, Loki, Tempo, Promtail, Alertmanager) — verified against the real stack, not
just written: a clean `docker compose up` migrates Postgres and reaches `healthy` on all five core
containers, the Game Host registers with the Platform Monolith over the real compose network, both
management ports (`8081`, `8082`) and the remapped Prometheus port (`9091`) answer from the host
while everything else stays loopback-only per §1's table, Promtail ships real container log lines
into Loki (confirmed via a live Loki query, not just "the container starts"), and both
`turnbase.localhost:8080` and `some-game.games.localhost:8080` reach the same listener. A new
`ArtifactBucketReadinessCheck` (`io.turnbase.platform.upload`, AWS SDK v2 S3 client against MinIO's
S3-compatible API) asserts the bucket exists at startup and fails loudly naming
`TURNBASE_ARTIFACT_STORE_BUCKET` if it does not — proven by a mocked unit test and a real-MinIO `*IT`
via Testcontainers. **CI green on `master`.**

**Closed:** IMP-GATE-12 (opened and closed 2026-09-05) — this item's own `Repo` field said "this
repo" (the root `turnbase` landing repo), but its read-list document, `local-environment.md` §4,
roots the whole deploy tree it describes at `turnbase-platform/deploy/…`, and ADR-0012 §*Repos*
describes `turnbase` itself as holding only "docs, specs, submodule refs" — no deploy artifacts of
any kind. The two could not both be right: a compose file and Helm chart cannot live in
`turnbase-platform` per the spec that defines their layout while the registry assigns the item that
builds them to a different repository entirely. Fixed here, the document that was wrong — `Repo` is
now `turnbase-platform`, matching `local-environment.md` §4 and ADR-0012. Also fixed on IMP-M0-08
below, which inherited the same error.

**Closed:** IMP-GATE-13 (opened and closed 2026-09-05) — ADR-0011 §6 requires `pg_trgm` and
`btree_gin` to be created by the Postgres init script as superuser, "the baseline migration issues
`CREATE EXTENSION IF NOT EXISTS` for both, which succeeds as a no-op when provisioning did its job."
But `secrets-and-configuration.md` §4's actual `01-roles.sql` content — the concrete init script
ADR-0011 §6 is describing — created only `pgcrypto`. Running the real compose stack (this item, the
first thing to run Flyway as the actual unprivileged `turnbase_app` role against a database it
doesn't own) failed baseline migration outright: `permission denied to create extension "pg_trgm"`.
No existing test had caught it — every Testcontainers-backed `*IT` connects as the container's own
default superuser, never through the two-role split at all. Fixed: `secrets-and-configuration.md`
§4's script now creates all three extensions, matching ADR-0011 §6; `deploy/compose/initdb/
01-roles.sql` here does the same. Verified: with the owner having created `pg_trgm`/`btree_gin`
first, the app role's own `CREATE EXTENSION IF NOT EXISTS` for either is confirmed to short-circuit
before the permission check and succeed as a harmless no-op — so the baseline migration file itself
(`IMP-M0-06`'s artifact) needed no change.

**Closed:** IMP-GATE-14 (opened and closed 2026-09-05) — `local-environment.md` §1 said compose
achieves the loopback-only management port by setting `management.server.address = 127.0.0.1`
*inside the container*, with the published port mapping ("loopback-only on the host") doing the
rest. Both cannot hold together: a Docker published port always forwards to the container's
bridge-network interface, never to its own loopback, so a listener bound to `127.0.0.1` inside the
container is unreachable through `-p 127.0.0.1:8081:8081` regardless of the host-side bind — proven
live (a container with the address set refused every host connection to its published port with
`Connection reset by peer`; the identical container with the address left unset answered `200`
through the same publish syntax). Never caught before now: `IMP-M0-03`/`IMP-M0-04`'s "verified live"
claims tested the app's own bind behavior, not a real Docker port-publish round trip, because
neither item had a working `docker-compose.yml` to test it through — this item is the first that
does. Fixed: `local-environment.md` §1 and §7.9 now state the real mechanism — the app listens on
all interfaces in **both** profiles; compose's restriction is the host-side bind of the published
port, Kubernetes's is topological (no Ingress/`LoadBalancer` names the port), and neither is the
app's own address. No application code changed — `MANAGEMENT_SERVER_ADDRESS` already defaults to
unset in both `turnbase-platform` and `turnbase-game-host`; only the stale comments describing the
old (wrong) mechanism were corrected, and `docker-compose.yml` here no longer sets the variable.

**Read first:**
- `docs/specs/deployment/local-environment.md` in full — especially §1 (**eleven long-running
  containers plus the one-shot `minio-init` job**), the host port map, §2 (network, and *Redis
  configuration is not optional*), §3 (startup order and readiness), §5 (the three invocations,
  and *The bundle bucket is created by an init step, not by the application*)
- `docs/specs/deployment/secrets-and-configuration.md` §4 — the two-role split and
  `deploy/compose/initdb/01-roles.sql`
- `docs/specs/deployment/observability.md` §1, §3, §5, §6 — what the six observability containers
  are actually wired to do

**Satisfies:** `platform-operations.md` CON-010, CON-011, FR-CRED-005; ADR-0001

**Done when:**

1. `docker compose up` with the core profile brings up Platform Monolith, Game Host, Postgres, Redis
   and MinIO, migrated and reachable.
2. `minio-init` (`minio/mc`) runs to completion and creates the `turnbase-bundles` bucket. **The
   application asserts the bucket exists and never creates it** — a service that creates its own
   bucket needs bucket-creation rights it must not hold in production.
3. `deploy/compose/initdb/01-roles.sql` creates both Postgres roles. `POSTGRES_USER` is
   **`turnbase_owner`**, not `turnbase_app` — naming the app role there makes it the container's
   superuser and violates FR-CRED-005 with nothing appearing to be wrong.
4. The full profile adds all six observability containers: Prometheus, Grafana, Loki, Tempo,
   **Promtail** and **Alertmanager**. Promtail is not optional decoration — it is the only thing that
   moves logs into Loki, because `observability.md` §3 rejects the Loki Docker driver.
5. The host port map matches §1 exactly, including Prometheus remapped to `9091` (the Game Host holds
   `9090` on the host network).
6. Both `turnbase.localhost:8080` and `{gameId}.games.localhost:8080` route to the monolith by `Host`
   header on the **same listener**.

---

### IMP-M0-08 — Local stack, Helm chart

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-07

**Done 2026-09-05 (session 23).** `deploy/helm/turnbase/` — Platform Monolith, Game Host, Postgres,
Redis, MinIO (all as separate Deployment/StatefulSet + Service, mirroring `docker-compose.yml`'s five
core components) plus the six observability containers (mirroring `docker-compose.observability.yml`),
an Ingress with the two host rules, and a `minio-init` Job for the bundle bucket. Verified against a
real Docker Desktop Kubernetes cluster, not just rendered: `helm upgrade --install` brings up all
eleven pods plus the completed init Job; the management port (`8081`) answers a real kubelet
readiness probe on every Deployment/StatefulSet, unset per §1; every Service is `ClusterIP` and the
Ingress routes only the `http` port, so nothing ever names `8081`; a live `kubectl rollout restart`
on the Platform Monolith showed the successor `Running` and `Ready` **before** the incumbent began
terminating (`maxSurge: 1, maxUnavailable: 0`), which is the ADR-0008 property this item exists to
prove, not merely configure; and — matching the bar `IMP-M0-07` set for its own Promtail — a live
Loki query through the deployed chart returned real platform-pod log lines, not just "the container
started."

**Closed:** IMP-GATE-12 (opened and closed 2026-09-05, on IMP-M0-07) — `Repo` corrected from "this
repo" to `turnbase-platform` for the same reason as IMP-M0-07's own note.

### `spring.lifecycle.timeout-per-shutdown-phase` and `server.shutdown: graceful` did not exist before this item

`local-environment.md` §3's shutdown table names both as the mechanism that makes the chart's
`preStop`/`terminationGracePeriodSeconds` mean anything — without them Spring exits immediately on
SIGTERM and the drain budget is pure decoration. Neither was in `application.yml`; `IMP-M0-03`'s own
*Done when* never named them, so this was not a broken promise, just an omission nothing had
exercised yet, surfaced by the first item that actually sends the app a real SIGTERM inside a pod.
Added both, `./mvnw verify`/`-Pintegration` still green.

### Two toolchain traps, neither in any spec, that would have shipped a chart that silently drops every log line

- **A wildcard Ingress host (`*.games.localhost`) is a YAML alias to `helm lint`'s parser** —
  unquoted, `- host: *.games.localhost` fails "did not find expected alphabetic or numeric character"
  because YAML reads a bare leading `*` as an anchor reference. Quoted both host fields.
- **`kubernetes_sd_configs` (`role: pod`) returned zero discovered targets against this cluster's
  Promtail/client-go, with no logged error** — confirmed live: RBAC granted exactly the needed
  `list`/`watch` on `pods`, and the same ServiceAccount's own token listed pods successfully via a
  direct `kubectl exec` curl, yet `promtail_targets_active_total` stayed `0` through a manual
  `-log.level=debug -dry-run` run. Replaced with a `static_configs` file glob
  (`/var/log/pods/*/*/*.log`) plus a `regex` pipeline stage pulling namespace/pod/container out of
  the directory name Kubernetes itself encodes — no Kubernetes API access needed at all for a
  DaemonSet, which only ever needs its own node's logs. Two more layers under that one, both found
  only by watching real log lines fail to arrive after the SD swap: the entries under
  `/var/log/pods/.../<container>/` are themselves symlinks into `/var/lib/docker/containers` on this
  cluster's dockerd-backed runtime (a second hostPath mount was missing), and the files there are
  Docker's own JSON-lines envelope, not the CRI plaintext format — the `cri: {}` pipeline stage
  silently no-ops on the wrong format, same as a missing stage; swapped for `docker: {}`, matching
  `docker-compose.observability.yml`'s own Promtail exactly. A containerd-CRI cluster hits none of the
  last two — the second hostPath mount is simply unused, and `cri: {}` would have been the right
  stage — but this chart's target is the Docker-Desktop-Kubernetes canonical path `local-environment.md`
  §4 names, which is dockerd-backed.

### The `minio-init` Job cannot be a Helm hook here — a genuine ordering deadlock, not a style choice

`local-environment.md` §5 says the bucket-creation step "runs as a Job" under Kubernetes, and a
Job that fails to reapply on every `helm upgrade` (a completed Job's spec is immutable) is exactly
what `helm.sh/hook: post-install,post-upgrade` plus `before-hook-creation` is for. It deadlocks
under `--wait`: Helm's `--wait` blocks on the **main** resources reaching ready *before* running
post-install hooks, and the Platform Monolith's own readiness never arrives without the bucket the
hook would create — reproduced live (`helm upgrade --install --wait` timed out with the Platform
Monolith crash-looping on `NoSuchBucketException`, the Job never having run at all). Fixed by making
`minio-init` an ordinary resource, applied in the same batch as MinIO and the Platform Monolith, so
`--wait` watches all three converge together — the Platform Monolith crash-loops briefly, which is
the same eventually-consistent shape `docker-compose.yml`'s own `depends_on: condition:
service_healthy` avoids and a bare Kubernetes Job cannot express. `{{ .Release.Revision }}` in the
Job's name sidesteps the immutable-Job-on-upgrade problem instead of a hook's delete policy, with
`ttlSecondsAfterFinished` reaping old runs.

### The Docker Desktop Kubernetes cluster's own `ingress-nginx` was reinstalled, not newly added

The cluster already carried an `IngressClass` named `nginx` and a `ValidatingWebhookConfiguration`
for `ingress-nginx-admission`, both orphaned — no controller Deployment, no Service, empty
`ingress-nginx` namespace — left over from before this session. A server-side dry-run of this
chart's Ingress failed on the stale webhook calling a Service that no longer exists. Removed the four
orphaned cluster-scoped objects (`ClusterRole`/`ClusterRoleBinding` × 2, the webhook, the
`IngressClass` — verified none had a controller or workload behind them first) and reinstalled the
upstream `ingress-nginx` chart with `controller.ingressClassResource.name=nginx`, the class name
`local-environment.md` already assumes exists. Left running: it is generic infrastructure this
cluster's own spec requires, not scoped to this item's verification.

**Read first:**
- `docs/specs/deployment/local-environment.md` §4 (*Kubernetes is canonical; compose is the quick
  start*), §3 *Deployment strategy*, §1 host port map
- `docs/decisions/0008-room-ownership-lifecycle.md` — why the rollout strategy is a correctness
  concern and not a preference

**Satisfies:** `platform-operations.md` CON-010, CON-011, FR-DEPLOY-001…003; ADR-0001

**Done when:** the chart deploys to Docker Desktop Kubernetes; the management port is reachable by
kubelet probes (address **unset**, per §1); no Ingress or LoadBalancer names `8081`; **the deploy is
a rolling update even at one replica** — under `Recreate`, ADR-0008's claim path never runs against a
live incumbent.

---

### IMP-M0-09 — Configuration and secrets wiring

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M0-03, M0-04

**Closed:** IMP-GATE-77 (opened and closed 2026-09-26, session 76, found running the compose stack under
`IMP-M6-02`) — `IMP-GATE-36`'s fix put the Redis address in `spring.data.redis.url` and the credential in
`spring.data.redis.password`, but Spring Boot's `url` property overrides `password`, so the monolith
connected with no credential and exited on `NOAUTH` under compose and Helm (CI's `e2e` job failed
identically). Fixed: `local-environment.md` §7.9 now names `spring.data.redis.host`/`.port`
(`SPRING_DATA_REDIS_HOST`/`_PORT`) and states that `url` must not be set; `secrets-and-configuration.md`
§ Redis says the same and extends it to the Game Host's future Redis client. `IMP-M1-02`'s note above
that the chart and compose "carry `SPRING_DATA_REDIS_URL`" is superseded.

**Read first:**
- `docs/specs/deployment/secrets-and-configuration.md` in full — the nine secrets, the two-role
  Postgres split (§4), and §6 *What must never be written down*
- `docs/specs/deployment/local-environment.md` §7 — the consolidated configuration surface

**Satisfies:** `platform-operations.md` FR-CRED-001…005

**Done when:** every key in §7 is bound to a typed configuration property with the stated default;
every secret in `secrets-and-configuration.md` has a local-dev provisioning path and a Kubernetes
Secret path; **no secret has a working default in committed configuration** — `.env` is git-ignored
and `.env.example` carries keys with no values; the application role is `turnbase_app` and holds no
superuser (FR-CRED-005); the JWT key set supports two concurrent keys for graceful rotation.

**§7 is the whole tunable surface — treat a missing key as a specification defect, not as licence to
invent one.** A property named at a call site and never registered in §7 is invisible to whoever next
audits the configuration, which is how the table stops being true. The last gap was
`turnbase.room.spectator-capacity` (IR-24, now closed and in §7.1).

**Closed:** IMP-GATE-15 (opened and closed 2026-09-05) — the *Done when* clause requires a Kubernetes
Secret path for every secret, including the JWT key set, but `secrets-and-configuration.md` §3.1 named
none: it said only "Supplied; startup fails if absent," and §7 deliberately excludes secrets by design
(§2's split), so there was nowhere else it could be named either. Fixed: §3.1 now names
`TURNBASE_JWT_KEY_SET` (`turnbase.auth.jwt-key-set`), one JSON-valued environment variable carrying the
whole key set in §3.2's own shape — chosen over separate active/retired variables so a rotation (§3.3)
updates atomically in one `Secret` change rather than as a pair that could disagree mid-rotation.

**Closed:** IMP-GATE-16 (opened and closed 2026-09-05) — `secrets-and-configuration.md` §3.1's
`local`/`test,e2e`/`Kubernetes` split for the JWT key set cannot be implemented by Spring profile
alone: `local-environment.md` §4 runs the canonical Kubernetes chart under the identical
`spring.profiles.active=local` compose uses, but the two rows need opposite behaviour — generate and
persist to a file under compose (one instance), fail if absent under Kubernetes (the chart's own HPA
can run more than one replica, and a self-generated key is only correct for exactly one). Fixed: a new
non-secret switch, `turnbase.auth.jwt-key-set-required` (`local-environment.md` §7.4, default `false`),
set to `true` only by the Helm chart's ConfigMap; `secrets-and-configuration.md` §3.1 now states this
is the actual mechanism and profile is not.

**Closed:** IMP-GATE-17 (opened and closed 2026-09-05) — `turnbase.gamehost.grpc.port`, shipped by
`IMP-M0-04` and already read live by `GrpcServerLifecycle`, was never added to `local-environment.md`
§7.8, contradicting §7's own "whole tunable surface" claim — the same class of gap IR-24 closed for
`turnbase.room.spectator-capacity`. Fixed: added to §7.8 with its existing default (`9090`).

---

### IMP-M0-10 — Observability baseline

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M0-03, M0-04

**Read first:**
- `docs/specs/deployment/observability.md` in full — the implementing spec for every metric, log and
  trace requirement
- `docs/requirements/platform-operations.md` — FR-MET-001…007, FR-TRACE-001…004, FR-OBS-001…005,
  FR-ALERT-001…007, NFR-OBS-001
- `docs/specs/deployment/local-environment.md` §1, §7.9
- `docs/specs/game-host/game-host-internals.md` §14 — the Game Host's own signal set

**Satisfies:** `platform-operations.md` FR-MET-001, FR-MET-003, FR-MET-004, FR-MET-006, FR-MET-007,
FR-TRACE-001…003, FR-OBS-001…005, FR-ALERT-001, FR-ALERT-002, FR-ALERT-004, FR-ALERT-005, NFR-OBS-001.
FR-MET-002, FR-MET-005, FR-ALERT-003, FR-ALERT-006, FR-ALERT-007 and `platform-architecture.md`
FR-OBS-001…009 are **not** satisfied here — see *Deferred to later items* below.

**Done when:** Micrometer exports to Prometheus at the management port on both services, including the
FR-MET-003 business gauges; Logback emits JSON to stdout with a correlation ID on every record; the
OpenTelemetry Java agent is attached to both services and a real HTTP request against the running
stack produces a trace visible in Tempo; the `ClientInterceptor`/`ServerInterceptor` pair that copies
`observability.md` §3's MDC correlation IDs onto gRPC metadata and restores them on the other side is
proven against a controlled, in-process gRPC call (IMP-GATE-18 — no live REST-triggers-gRPC call path
exists yet for the agent to instrument end to end); Grafana resolves Prometheus, Loki and Tempo as
data sources and its derived field links a log line's `traceId` to the Tempo trace (`observability.md`
§5); Prometheus alert rules FR-ALERT-001, FR-ALERT-002 and FR-ALERT-004 evaluate, and Alertmanager
routes to a webhook when `TURNBASE_ALERT_WEBHOOK_URL` is set and to no receiver when it is not
(FR-ALERT-005).

**Closed:** IMP-GATE-18 (opened and closed 2026-09-05) — the original clause required proving trace
propagation "across the REST → gRPC boundary," which is the agent's job automatically (§4 — "the
agent handles HTTP and gRPC automatically") and needs no code of this item's own, but there is no
REST-handler-calls-gRPC code path anywhere yet for the agent to instrument: `turnbase-platform` issues
no outbound gRPC call and runs no gRPC server, and the Game Host's one outbound gRPC call (`Register`,
`IMP-M0-04`) is not triggered by an inbound REST request. The real request chain client → WebSocket →
Orchestration → gRPC → Game Host (FR-TRACE-002) does not exist before `IMP-M3-05`. Same shape as
`IMP-GATE-08`. Fixed: the clause above keeps the agent-and-Tempo check (real, but HTTP-only for now)
and narrows the cross-process claim to what this item *can* build without a live caller — the
correlation-ID `ClientInterceptor`/`ServerInterceptor` pair of §3's gRPC-out row, proven against a
controlled gRPC call. The live, request-shaped, agent-instrumented cross-repo trace moves to
`IMP-M3-05`, which gained a Done-when clause for it below.

**Closed:** IMP-GATE-19 (opened and closed 2026-09-05) — `observability.md` §3's own worked example
showed `"sessionId": null` two sentences before the prose it illustrates says correlation IDs are
"**omitted when absent** rather than written as empty strings" — a `null` is neither omitted nor an
empty string, and the document contradicted its own stated rule in its only example of the rule.
Fixed: the example now omits the `sessionId` key entirely, matching the prose it sits next to.

**Closed:** IMP-GATE-20 (opened and closed 2026-09-05) — `observability.md` §2.1's literal SQL for
`turnbase_friend_requests_pending` was `SELECT count(*) FROM friend_request WHERE status = 'PENDING'`,
but the baseline migration's `friend_request` table (`IMP-M0-06`, already `DONE`) has no `status`
column — the query would fail against the real schema. Fixed: the query is now an unfiltered
`count(*)`, and §2.1 gained a sentence explaining why that is correct rather than a simplification —
a pending request's row exists; accepting one deletes it and inserts a `friendship` row, declining or
expiring one just deletes it, so existence already means pending.

**Closed:** IMP-GATE-21 (opened and closed 2026-09-05) — `observability.md`'s worked log example and
its Grafana derived-field regex both used camelCase `traceId`/`spanId`, but the OpenTelemetry Java
agent's `logback-mdc` instrumentation — the mechanism §3 itself assigns this job to ("injected by the
agent") — writes `trace_id`/`span_id` (OpenTelemetry semantic conventions for log correlation, not a
choice available to configure). Verified empirically against a running container: the field is real
and correctly populated, just spelled differently than the doc's own example. Fixed: the JSON
example, the promtail pipeline stage, and the Grafana derived-field `matcherRegex` all changed to
`trace_id`/`span_id`, in `observability.md` and in the committed `promtail-config.yaml` and
`datasources.yaml` this repeats. The five correlation IDs (`requestId` etc.) are unaffected — those
are this project's own MDC keys, not the agent's.

**Closed:** IMP-GATE-22 (opened and closed 2026-09-05) — `deploy/compose/tempo/tempo.yaml`
(`IMP-M0-08`) left the OTLP receivers' `endpoint` unset, and Tempo's own default for both is a
loopback bind — unreachable from another container even though the port is published on the compose
network, the same class of bind-address trap `local-environment.md` §1 already documents for the
management port (`IMP-GATE-14`). Found only by actually exporting a span against the running stack:
every export failed with `Connection refused` and zero traces ever reached Tempo. Fixed:
`tempo.yaml`'s `distributor.receivers.otlp.protocols` now sets `endpoint: 0.0.0.0:4317`/`:4318`
explicitly.

**Deferred to later items** — each of these needs a signal source this item's dependencies (`M0-03`,
`M0-04`) do not yet provide, so building it here would mean inventing the signal rather than reading
it from real code:

- **FR-MET-002** (`turnbase_websocket_connections_active`, bound to the STOMP session registry) —
  `IMP-M2-02`, which builds that registry. Added there.
- **FR-MET-005** (Redis metrics dimensioned by `concern`) — no single item owns this; `conventions.md`
  now states the rule that any item adding a new Redis usage site tags its metrics with the
  `observability.md` §2.2 concern dimension as part of its own Done-when.
- **FR-ALERT-003** (game session failure rate) — `IMP-M3-09` (game failure handling). Added there.
- **FR-ALERT-006** (reconciliation repairs persist) — `IMP-M2-10` (adoption and reconciliation jobs).
  Added there.
- **FR-ALERT-007** (owed teardown) — `IMP-M3-08` (session teardown as a durable to-do). Added there.
- **`platform-architecture.md` FR-OBS-001…009** (Game Host active-context/session counts, action
  latency, artifact-cache events) — these signals come from the Espresso context and session model,
  which is `IMP-M3-02`/`IMP-M3-04`. Not added as an explicit clause there because
  `game-host-internals.md` §14 already lists them as that layer's own signal set.
- **`redis-by-concern.json` and `room-lifecycle.json`** (`observability.md` §5) — cannot be
  meaningfully authored before FR-MET-005 and the per-duty reconciliation counter exist. Only
  `platform-overview.json` and `jvm-and-database.json` are built here.

**Three things in `observability.md` are counter-intuitive and are the ones to get right:**

- **FR-MET-003's business figures are polled gauges on a 30-second interval, not counters that
  application code increments** (§2). An incremented counter drifts the moment a pod dies mid-update
  and never self-corrects; a polled gauge is re-derived from the database every cycle. Because every
  pod polls the same global truth, Grafana must aggregate them with `max()` — a `sum()` multiplies
  every figure by the replica count.
- **Redis metrics are dimensioned by `concern`** ∈ {`game_state`, `action_queue`, `ownership`,
  `application`}. There is deliberately no `pubsub` value: ADR-0002 has no cross-instance fan-out, so
  a `pubsub` series would always read zero and look like a broken exporter.
- **FR-TRACE-004 is not met** and `observability.md` §7 says so. Sampling is head-based at 10% with no
  always-on-error tail, because tail sampling needs an OTel Collector the local stack does not run.
  This is a stated gap, not an oversight — do not implement a bespoke workaround.

---

### IMP-M0-11 — CI/CD workflows

**Repo:** all five submodules · **Depends on:** IMP-M0-01…05

**Done 2026-09-05 (session 26).** All five repos' `build.yml` gained a Trivy dependency scan
(report every severity, then gate on CRITICAL) — which immediately found a real finding,
CVE-2026-65182 in the Tomcat embedded by Spring Boot 3.5.16, fixed in both
`turnbase-platform` and `turnbase-game-host` by pinning `tomcat.version` to `10.1.59`, the
first 10.1.x release carrying the fix. `turnbase-platform`, `turnbase-game-host` and
`turnbase-frontend` also gained an image Trivy scan and now push their built image to
`ghcr.io/turnbase-platform/<name>:<sha>` on every push to `master` (FR-CICD-006) — verified
live: all three pushed successfully. `turnbase-common` and `turnbase-sdk` each gained a
`publish.yml` triggered only on a `v*.*.*` tag; neither has had a real run, since cutting the
tag is a human action the agent does not take, but both are reviewed and YAML-valid.
`turnbase-platform` gained `make e2e` and a post-merge `e2e` job — **verified for real against
the actual compose stack** (not just written): both services' actuator health checks return
`UP`. The job's cross-repo checkout of `turnbase-game-host` needs `TURNBASE_GAME_HOST_PAT`
(`conventions.md`), not yet provisioned (a human action), so it currently fails in CI exactly
as expected — `continue-on-error: true` keeps that from failing the workflow, matching
FR-CICD-005/OQ-002's "gates nothing." **CI green on `master` in all five repos.**

Three gates opened and closed in the same session, all found by actually trying to build the
pipeline rather than by reading: IMP-GATE-23 (PR-gated requirements after PRs were suspended),
IMP-GATE-24 (a production-deployment requirement with no production to deploy to), IMP-GATE-25
(a public-registry commitment with no license to publish under). None would have been caught
by `check-corpus.py`.

**Closed:** IMP-GATE-24 (opened and closed 2026-09-05) — FR-CICD-007 required the pipeline to "trigger
a production deployment" on a `v*.*.*` tag and FR-CICD-008 required rolling that deployment back, but
ADR-0001 §*Decision* item 4 ("Cloud deployment is deferred to post-MVP... not built for the MVP") and
item 2 (the canonical, CI-exercised deploy path is the **local** single-node Docker Desktop cluster)
together mean no production target exists anywhere in the corpus for a tag-triggered workflow to
reach — no cluster endpoint, no kubeconfig secret, no `values-production.yaml`. ADR-0001's own
*Affected documents* deferred `FR-SCALE-*` explicitly but never propagated the same deferral to
FR-CICD-006/007/008, the same class of gap `IMP-GATE-06` found for CON-010. Fixed: FR-CICD-007/008
marked deferred to post-MVP in `platform-operations.md`, and ADR-0001's *Affected documents* now names
the fix. This item's own *Satisfies*/*Done when* below are narrowed to match — FR-CICD-006 (image
push to a registry) stands, since a registry needs no production target, only a place to publish to.

**Closed:** IMP-GATE-25 (opened and closed 2026-09-05) — `game-development-experience.md` CON-003 and
ADR-0012's Release Strategy table both commit `turnbase-sdk` to publishing on Maven Central and npm,
but neither those two documents nor any other in the corpus names an open-source license for it —
and Maven Central's publish validation rejects an artifact with no `<licenses>` in its POM, so the
commitment is unsatisfiable as written. This is a decision the corpus left open, not a CI mechanic:
raised to the project owner, who chose to defer it rather than pick a license under this item. Fixed:
ADR-0012's Release Strategy row for `turnbase-sdk` and CON-003 both now say the Maven Central/npm
publish is deferred until a license is chosen. Only the **Maven** half has a working interim home —
GitHub Packages, same registry `turnbase-common` already uses, no new external account. The **npm**
half does not: GitHub Packages' npm registry requires a scoped package's scope to match the owning
GitHub org (`turnbase-platform`), and `@turnbase/gdk` (FR-FEGDK-007) cannot satisfy that — a hard
registry constraint, not a naming choice — so npm publication waits for the public registry alongside
the license, same as it already did before this gate. This item's own *Done when* below is narrowed
to match.

**Closed:** IMP-GATE-23 (opened and closed 2026-09-05) — `platform-operations.md` FR-CICD-002/003 and
OQ-002's resolution gated the pipeline on a **pull request** ("the PR cannot be merged if any check
fails", "PR feedback loops"), but ADR-0012 (amended 2026-09-05) suspends pull requests project-wide —
every merge to `master` is direct, so a workflow triggered on `pull_request` would never fire, the
same never-fires shape already found once in this same requirement (the `main`→`master` correction
noted in FR-CICD-002 itself) and again in `IMP-M0-01`'s `buf breaking` gate. Fixed: FR-CICD-002
retitled *Pre-merge checks* and reworded to gate on push to `master`; FR-CICD-003 and OQ-002's
resolution updated to match. The five repos' existing `build.yml` workflows (`IMP-M0-01…05`) already
run on `push` to `master` alongside the now-inert `pull_request` trigger, so no workflow code needed
to change — the defect was in the requirement's prose, not in the pipelines it describes.

**Read first:**
- `docs/requirements/platform-operations.md` FR-CICD-001…011
- `docs/specs/deployment/local-environment.md` §8 — **the authority on what each test category
  actually depends on.** Read it before the requirement, not after
- `docs/implementation/conventions.md` §§2–4, 6
- `CLAUDE.md` — *Submodule philosophy* and the End of Session Checklist

**Satisfies:** `platform-operations.md` FR-CICD-001…006, FR-CICD-009…011. FR-CICD-007/008 are
**deferred to post-MVP** (IMP-GATE-24) — no production target exists for the MVP.

**Done when:**

1. Every repo's existing pre-merge workflow (`IMP-M0-01…05`) keeps gating on push to `master`
   (FR-CICD-002, IMP-GATE-23) and gains a Trivy scan: a filesystem/dependency scan in all five, plus
   an image scan in the three that build one. A **critical** finding fails the job; lower severities
   report only (FR-CICD-010).
2. `turnbase-platform`, `turnbase-game-host` and `turnbase-frontend` build and push a Docker image
   tagged with the commit SHA to GHCR on every push to `master` (FR-CICD-006), authenticating with the
   workflow's own `GITHUB_TOKEN` — no new secret.
3. `turnbase-common` and `turnbase-sdk` each gain a `publish` workflow that triggers **only** on a
   `v*.*.*` tag, never on an ordinary push. `turnbase-common` publishes its Maven artifact to GitHub
   Packages. `turnbase-sdk` publishes only its Maven artifact there too — its npm package stays
   unpublished by any registry, public or interim (IMP-GATE-25: the public Maven Central/npm publish
   ADR-0012 names is deferred pending a license, and GitHub Packages' npm registry cannot host
   `@turnbase/gdk` under the `turnbase-platform` org scope it would require). `npm pack --dry-run`
   (already `IMP-M0-02`'s check) remains the ceiling for the npm side until both are resolved. Neither
   workflow's actual first run is exercised in this item: cutting a `v*.*.*` tag is a human action the
   agent does not take (`CLAUDE.md`, permissions). Verified as far as that allows: both workflows are
   syntactically valid and trigger only on a tag push, and the version-from-tag/credential-wiring steps
   mirror `turnbase-common`'s own working `-Prelease deploy` invocation.
4. `turnbase-platform` gains `make e2e` (compose up, an HTTP smoke test against both services' health
   endpoints, compose down) and a post-merge job that runs it on every push to `master`, reporting
   pass/fail for information only — it gates nothing (FR-CICD-005, OQ-002). A full end-to-end feature
   suite has nothing to exercise yet (M1 is not built); the smoke test is the honest ceiling today.
5. The workflow is still the gate `CLAUDE.md` requires before a submodule ref is bumped here.

**This item ends `IMP-GATE-07`'s bootstrap window.** Once `turnbase-common`'s publish workflow exists
and its first `v*.*.*` tag is cut (a human action), `turnbase-platform` and `turnbase-game-host` each
need the small follow-up `conventions.md` §5 describes: bump `<turnbase-common.version>` from the
bootstrap SNAPSHOT to the released version. That bump is not part of this item's own *Done when* — it
is the same "consumer bump is where the compile break surfaces" step every later release goes
through — but it does not happen by itself, so it belongs on whoever picks up the tag.

**Every trigger names `master`.** Not `main` — no repository has one. FR-CICD-002/006/007 said `main`
until 2026-08-20 and were corrected against ADR-0012's branch model; a workflow written from the old
text is one that never fires.

**Integration tests are Testcontainers, not compose.** The build job needs a Docker daemon and nothing
else — no `services:` block, no compose file, no stack started in a prior step. Compose belongs to the
post-merge e2e job alone — `local-environment.md` §8, and `platform-operations.md` FR-CICD-004 as
corrected.

**FR-CICD-010's scanning is configuration, not a mention.** Each repo gets a committed
`dependabot.yml` and a Trivy step covering dependencies *and* the built image, with **critical
failing the build and lower severities reporting only** — the split the requirement argues for,
because a pipeline that blocks on every advisory stops being run
([ADR-0015](../decisions/0015-static-analysis-error-prone-nullaway.md) §4).

---

### IMP-M0-12 — Seed data

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-06, IMP-M4-03

**Closed:** IMP-GATE-73 (opened and closed 2026-09-26, session 73, found when this item's CI run
`36252029924` sat in `Verify` for over two hours) — `local-environment.md` §1 pinned MinIO to
`quay.io/minio/minio` and `quay.io/minio/mc`, the registry `IMP-GATE-52` moved to. Both repositories
have since stopped serving anonymous pulls (`unauthorized`; `docker manifest inspect` reports no such
manifest for any tag), so upstream publishes no public image at all. Every `PostgresIntegrationTest`
subclass then spent about 7 minutes retrying the pull before failing in `initializationError`. The run
never failed because the workflow sets no `timeout-minutes`. Locally the suite passed only because the
old image was still cached. Fixed in `local-environment.md` §1 (table and a new paragraph) and §5
(the `minio-init` snippet): MinIO now comes from the `pgsty` community fork, which rebuilds the same
server and client from source on the same base image, with the same entrypoint and variables.
`turnbase-platform` (`34f020e`: compose, Helm `values.yaml`, both Testcontainers pins) and
`turnbase-game-host` (`7bbeee9`: `S3ArtifactStoreIT`) pin `pgsty/minio:RELEASE.2026-08-04T00-00-00Z`
and `pgsty/mc:RELEASE.2026-09-16T00-00-00Z`. `.asCompatibleSubstituteFor("minio/minio")` stays. No
`dependabot.yml` names a MinIO image.

**Closed:** IMP-GATE-72 (opened and closed 2026-09-26) — `local-environment.md` §6 still required one
`BUNDLE_VALIDATION_COMPLETE` notification, which goes to an uploader the v1 system cannot have (only the
admin listener uploads — ADR-0006 — and it has no user), and which no code produces; the same shape as
`IMP-GATE-65`/`66`. It also left open how the seeder reaches `SocialService`/`NotificationService`, which
are package-private and which earlier sessions stalled on. Fixed in §6: the type is excluded by name;
the remaining four are specified as one story; and the "real pipeline" rule is stated to govern games
only — users, the friendship, the request and the notifications are direct idempotent SQL against fixed
UUIDs (passwords hashed by the app's own `PasswordEncoder`), so no feature needs a seeding entry point.

**Closed:** IMP-GATE-71 (opened and closed 2026-09-26) — the *Done when* ("an official game that can
actually be started") cannot be met by this item: the only real game is `IMP-M3-10`'s, which this item
does not depend on and which itself waits on `IMP-M3-03`; and no document said where the seeder gets
bundle bytes at all — the platform image is a JRE (nothing can compile a game at seed time), the
monolith has no `turnbase-sdk` dependency, the manifest carries no identity field for §6's "fixed
UUIDs", and `POST /admin/games` mints a random id. Fixed in `local-environment.md` §6 (new paragraph)
and §7.10: the seeder *uploads* the ZIPs it finds in `turnbase.seed.bundles-dir`, the file name's stem
is the fixed `game_id`, an already-`ACTIVE` game is skipped, and an empty directory is a logged no-op.
The "can actually be started" clause moves to `IMP-M3-10`, the item that produces a real bundle and now
owns getting it into that directory. This item's clause is narrowed accordingly — the mechanism is
proven against a fixture bundle, not a real game.

**Closed:** IMP-GATE-66 (opened and closed 2026-09-22) — `local-environment.md` §6's `Notifications`
row (as left by IMP-GATE-65) still required seeding one `GAME_APPROVED` and one `GAME_REJECTED`
notification, both of which `AdminReviewService.approve`/`reject` can only produce by deciding a
pre-existing open `game_review` row — and nothing in this repository ever inserts one.
`admin-rest-api.md` §4 states it directly: "no `game_review` row is ever written by this pipeline for
any badge (nothing in it writes one today)"; §7 states it again: "`POST
/admin/games/{gameId}/approve`/`reject` consume a `game_review` row this document never produces."
The row would come from FR-PRV-004 (`admin-tooling.md`, "Must"), the game owner's submit-for-review
action — confirmed unclaimed by any registry item (verified by reading `AdminGameRepository`, whose
own Javadoc calls `insertGame()` "the one row-creation mechanism [`admin-rest-api.md`] supplies," and
it only inserts a `game` row) and disclaimed in `admin-rest-api.md` §7 itself ("No submission
endpoint... belongs with whichever item builds it"). Same shape as `IMP-GATE-65`: the seed table asked
for something the corpus has no real pipeline to produce, and §6's own rule ("the seeder drives the
real upload pipeline; it does not write rows and objects by hand") forbids inserting a `game_review`
row directly to manufacture the two notifications. Fixed in `local-environment.md` §6: the
`Notifications` row now excludes `ROOM_INVITATION`, `GAME_APPROVED` and `GAME_REJECTED` by name, with
the `game_review`/FR-PRV-004 reasoning inline; the remaining five types are enough for the center to
not be empty on first login. `GAME_APPROVED`/`GAME_REJECTED` seeding is left for whichever item builds
FR-PRV-004 and the review queue it feeds.

**Closed:** IMP-GATE-65 (opened and closed 2026-09-22) — `local-environment.md` §6's own seed table
contradicted itself: its `Notifications` row required "one of each type in §3" including
`ROOM_INVITATION`, whose subject (`notification.invitation_id`) references a `room_invitation` row,
and `room_invitation.room_id` is a `NOT NULL` FK to `room` — but the same table's `Rooms` row is
"None." A `CLOSED` room built to hold the invitation doesn't resolve it either: `room_invitation` rows
are deleted at closure (FR-INV-008), so that combination can't occur through the running system's own
code paths and would be fabricated state. Fixed in `local-environment.md` §6: the `Notifications` row
now excludes `ROOM_INVITATION` by name, with the reasoning inline; the other seven types in §3 already
populate the center on first login.

**Read first:**
- `docs/specs/deployment/local-environment.md` §6
- `docs/specs/manifest/bundle-format.md` §3 — the pipeline the seed must go through

**Satisfies:** — *(developer experience; `local-environment.md` §6 is the only source)*

**Done when:** (narrowed by IMP-GATE-71) under the `local`/`e2e` profiles a start seeds the §6 users,
the `alice`↔`bob` friendship, `carol`'s pending request and the four in-scope notification types (`IMP-GATE-72`); and
every `<gameId>.zip` in `turnbase.seed.bundles-dir` is driven through the real upload pipeline — an
integration test with a fixture bundle asserts the game is listed, its version is `ACTIVE`, and
`/g/{gameId}/{version}/<frontend entry point>` serves `200` (the unpack really happened); a second run
changes nothing and does not fail; an unset directory seeds no games and does not fail. *"Can actually
be started" is `IMP-M3-10`'s clause, not this one's.*

**Verified.** Code merged to `turnbase-platform master` at `f789407` (session 72). Its own CI run was
cancelled on `IMP-GATE-73`'s pull failure. The first green `build` containing it is run `36260709084`
on `34f020e` (the gate's fix). The full `-Pintegration` suite also passed locally on `f789407`
(231 tests). `SeedDataIT` boots the application under `local` per test on a fresh schema and asserts
the §6 users, friendship, pending request and four notification types, a fixture bundle driven to
`ACTIVE` and served from its game origin, a seeded login, a second run changing nothing, an unset
directory seeding no games, and no seeding outside `local`/`e2e`. `e2e` failed on the pre-existing `compose-platform-1` exit (see
`STATUS.md`), not on this item.

**The seed must go through the upload and validation pipeline, not around it.** A seed that inserts
catalog rows directly produces a game that lists and cannot start — the exact outcome §6 says it is
avoiding. This is why the item depends on M4-03 despite sitting in M0; it is the one M0 item that
cannot be finished first.

---

## M1 — Accounts and sessions

### IMP-M1-01 — Error model, REST conventions, validation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-03

**Read first:**
- `docs/specs/api-design/rest-conventions.md`
- `docs/specs/api-design/error-handling.md` — especially the **type taxonomy, which is a closed set**
- `docs/specs/api-design/input-validation.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `user-accounts.md` NFR-SEC-005; `game-rooms.md` NFR-USAB-001; `game-catalog.md`
NFR-USAB-001…002

**Done when:** one `@RestControllerAdvice` produces the single RFC 9457 error shape defined in
`error-handling.md` for every failure class; Bean Validation failures map to it; the pagination
contract is implemented once as a reusable type; an integration test asserts the exact response body
for each error class, including `room-unavailable-retry` and its `retryAfterMs` member.

**This item defines the shape every later endpoint conforms to. Build it before any endpoint.**

**The problem-type taxonomy is closed.** A new failure mode does not get a new `type` URI invented at
the call site — it gets registered in `error-handling.md` first. Every unregistered type is a client
branch nobody wrote.

---

### IMP-M1-02 — Rate limiter, Tiers 1–5

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01

**Closed:** IMP-GATE-36 (opened and closed 2026-09-08, session 35) — `secrets-and-configuration.md`'s
inventory (§1) and its own "### Redis" section (§4) required `requirepass`, one password shared by
the monolith and the Game Host, and `docker-compose.yml`'s `redis` service already enforced it
(`TURNBASE_REDIS_PASSWORD`) — but no document named the Spring property that carries it into a
running service (unlike the PostgreSQL section two headings above, which names
`TURNBASE_DB_APP_PASSWORD` → `SPRING_DATASOURCE_PASSWORD` explicitly), `local-environment.md` §7.9's
`spring.data.redis.url` row showed a bare `redis://redis:6379` default with no credentials, and the
`platform` service's own environment block in `docker-compose.yml` set no Redis-related variable at
all. Fixed: `secrets-and-configuration.md` § Redis now names `spring.data.redis.password`
(`SPRING_DATA_REDIS_PASSWORD`) as the carrier, kept separate from the URL the same way
`spring.datasource.password` is kept separate from `spring.datasource.url`; `local-environment.md`
§7.9 gained the corresponding row. Wiring `docker-compose.yml`'s `platform` service to actually pass
both is this item's own implementation work, not a further spec fix.

**Read first:**
- `docs/specs/api-design/rate-limiting.md` — Tiers 1–5, *Client identity: deriving the IP*, the 429
  response shape
- `docs/specs/deployment/local-environment.md` §7.6

**Satisfies:** `user-accounts.md` NFR-SEC-003, NFR-SEC-007

**Done when:** each tier's bucket, key, limit and window match the spec; breaches return the
`error-handling.md` shape with `429` and the stated headers; buckets are held in Redis. Tier 6
(WebSocket frames) is IMP-M2-02.

**Tier 5 counts successes, not attempts.** Account minting is limited by how many accounts an IP
actually created; counting attempts lets a failing client exhaust its own budget and lets a
successful one mint freely.

**Done 2026-09-08 (session 35).** One `common.RateLimitInterceptor` covers all five HTTP tiers.
Tiers 2-4 share a plain Bucket4j capacity/window bucket (`Bandwidth.simple`) resolved through a
`ProxyManager<byte[]>` built directly from a raw Lettuce `RedisClient`
(`common.RedisRateLimiterConfig`) — independent of `spring-boot-starter-data-redis`'s own
`LettuceConnectionFactory`, which Bucket4j's proxy manager cannot use directly. Tier 2 alone emits
`X-RateLimit-Limit/Remaining/Reset`. Tier 5 (account minting) pre-consumes a token in `preHandle` and
refunds it in `afterCompletion` when the response is non-2xx, which is what makes it success-only
without a check-then-consume race. Tier 1 (auth failures) is a hand-rolled `StringRedisTemplate`
counter plus a separate lockout key with the doubling duration, entirely independent of Tier 5's
counter even though both apply to `POST /api/auth/register` simultaneously. `common.ClientIpResolver`
implements the two-sided trusted-proxy policy (`X-Forwarded-For` honoured only from a peer inside
`turnbase.security.trusted-proxies`) and IPv6 /64 keying, with a dependency-free CIDR matcher.
Endpoint classification is exact-match against routes that exist today (the same convention
`session.SessionAuthenticationInterceptor` uses) — Tier 3's upload-version-create route
(`IMP-M4-03`), Tier 1's auth-method add/remove and Tier 5's OAuth callback (`IMP-M1-10`) are none of
them built yet, and each item extends the matching set when it lands.

**First Redis consumer in `turnbase-platform`, which is what opened and closed `IMP-GATE-36`** (see
above) before any code could be written. `local-environment.md` §7.9 and `secrets-and-configuration.md`
§ Redis are fixed; `docker-compose.yml`'s `platform` service and the Helm chart's
configmap/secret both now carry `SPRING_DATA_REDIS_URL`/`SPRING_DATA_REDIS_PASSWORD`.
`conventions.md` §7's `concern=application` tag is applied via `common.RateLimitMetrics`, wrapping
every Redis call this item makes (`turnbase_redis_operation_seconds`/`_errors_total`).

**Verified end to end.** `ClientIpResolverTest` (unit) proves the trusted-proxy/XFF policy and the
IPv6 /64 masking directly. `RateLimitInterceptorIT` (Testcontainers Postgres + Redis, real HTTP)
boots its own tiny-limit context per test: Tier 5 rejects over-cap minting with `Retry-After` and
refunds a validation failure rather than counting it; Tier 1 locks out after the configured failure
count and recovers once the lockout elapses; Tier 2 emits the three headers and 429s on the third
request; Tier 4 caps an unauthenticated profile read; disabling the switch under the `test` profile
is honoured. `PostgresIntegrationTest` gained a shared Redis Testcontainer
(`@ServiceConnection(name = "redis")`, no official Testcontainers Redis module exists) so every
full-boot `*IT` can reach one; the four existing classes that drive `/register`/`/guest` repeatedly
(`AuthControllerIT`, `ProfileControllerIT`, `SocialControllerIT`, `AccountDeletionControllerIT`)
needed generous Tier 1/5 overrides to keep passing once real budgets were enforced — the same
per-property escape hatch `local-environment.md` §8 describes for e2e, applied per test class instead
of wholesale. `./mvnw verify -Pintegration` green locally (85 integration tests). **CI green on
`turnbase-platform` `master`** (`build`, 11m10s).

**No specification defect found beyond IMP-GATE-36.** `rate-limiting.md` settled every tier's
bucket/key/limit/window precisely enough to implement without a further gap; which Redis client
library (Lettuce, matching `spring-data-redis`'s own choice) and which Bucket4j module
(`com.bucket4j:bucket4j_jdk17-lettuce`) are implementation detail no document claims to settle.

---

### IMP-M1-03 — JWT key set, issuance and rotation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-09

**Done 2026-09-06 (session 28).** `JwtService` issues HS256 tokens (jjwt) carrying `sub`/`jti`/`kid`
per §3.5, signed with the current active key from `JwtKeySetManager` — the mutable wrapper this item
adds around `IMP-M0-09`'s immutable `JwtKeySet` bean, needed because §3.3's rotation changes the set
while the process keeps running. Verification resolves the signing key by the token's `kid` header
against active-or-retired via a jjwt `Locator`, so a token signed under a just-retired key keeps
validating. `JwtKeyRotationService.promote()`/`retire(kid)` implement §3.3's three steps; `retire`
revokes every `user_session` row still bound to that `kid` (`revoked_reason = 'KEY_ROTATED'`) in the
same transaction the key disappears from the set, via a plain-JDBC `UserSessionRepository`
(`JdbcClient` — no ORM in this repo, `IMP-M0-06`'s own note). `JwtKeySetManagerTest`/`JwtServiceTest`
(unit) and `JwtKeyRotationServiceIT` (Testcontainers Postgres, full application boot) prove the
Done-when clause directly: a token issued under the original key still verifies after that key is
promoted to `retired`, and retiring it revokes exactly the session bound to it while a session on the
new active key is untouched. `./mvnw verify` and `-Pintegration` both green locally; **CI green on
`master`** (build, 5m36s).

**No registration/login endpoint exists yet** (`IMP-M1-04`) to produce a real session through the
ordinary flow, so `JwtKeyRotationServiceIT` inserts a minimal `app_user`/`user_session` fixture
directly — this item owns the key set and the session-revocation mechanics, not the endpoints that
create these rows once `IMP-M1-04` lands.

**No specification defect found.** §3 named the algorithm, claim shape and three-step rotation
precisely enough to implement without a gap; the one judgement call this item made — which JWT
library (`io.jsonwebtoken:jjwt` 0.12.6) and which persistence primitive (`JdbcClient`, matching the
jdbc-not-JPA choice `IMP-M0-06` already recorded) — is implementation detail no document claims to
settle, not an underspecified requirement.

**Read first:**
- `docs/specs/deployment/secrets-and-configuration.md` §3 (JWT signing keys, in full)
- `docs/specs/platform/data-model-accounts.md` §3 (`user_session`)
- `docs/specs/api-design/rest-conventions.md` § *Authentication*

**Satisfies:** `user-accounts.md` FR-SESS-001, FR-SESS-004; `platform-operations.md` FR-CRED-001…004

**Done when:** tokens carry a key id; verification accepts both the current and the previous key;
rotation is exercised by a test that verifies a token issued under the retired key still validates
until its expiry, and that `user_session.revoked_reason` records key-rotation revocation.

**Watch the ID collision:** `FR-SESS-001` and `FR-SESS-003` are each defined in **both**
`user-accounts.md` and `platform-architecture.md` with unrelated meanings. Here, `user-accounts.md`
is the one you want.

---

### IMP-M1-04 — Credential registration and login

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01, IMP-M1-03

**Done 2026-09-06 (session 29).** `POST /api/auth/register` and `POST /api/auth/login`
(`AuthController`, `account` package). `UsernamePolicy` runs `input-validation.md`'s canonicalization
pipeline plus ICU4J `SpoofChecker` at `MODERATELY_RESTRICTIVE` for FR-AUTH-015's single-script rule,
computes the `getSkeleton(caseFold(NFC(username)))` uniqueness key, and rejects the `guest-` prefix on
that same skeleton (FR-AUTH-013). `CredentialPolicy` validates email (FR-AUTH-002) and password
(FR-AUTH-005) shape. Registration is one transaction (`AccountRepository.insertRegisteredUser`,
`@Transactional`) inserting `app_user`/`user_auth_method`/`user_privacy_settings`; a unique-index
violation is mapped to `ConflictException` by matching the constraint name in Postgres's own error
text (`app_user_email_key` vs `app_user_skeleton_key`) rather than a compile-time dependency on the
driver's exception type, which stays at `runtime` scope. Passwords are Argon2id via
`Argon2PasswordEncoder(16, 32, 1, 19456, 2)` per `input-validation.md`'s explicit cost parameters — the
no-argument constructor input-validation.md itself rejects as too weak.

**New `session.SessionService`** — the public API a principal-resolving flow calls to get a session —
implements `data-model-accounts.md` §3's atomic displace-then-insert (FR-SESS-001/002/003): revoke
whatever session is active for the user, insert the new row, retry (bounded, 5 attempts) on the
partial-unique-index race between two concurrent logins. Both `RegistrationService` and `LoginService`
call it *after* their own transaction commits, never inside it, per this repo's "commit before publish"
rule. `rest-conventions.md`'s newly-named `turnbase_session` cookie (`common.SessionCookie.NAME`,
IMP-GATE-27) is set `HttpOnly; Secure; SameSite=Strict; Path=/` with `maxAge` from the session's actual
`expiresAt`.

**Verified end-to-end, not unit-tested in isolation.** `UsernamePolicyTest`/`CredentialPolicyTest`
(unit) prove the validation/skeleton rules directly, including that case variants of one username
share a skeleton and that a confusable lookalike of `guest-` is still caught. `AuthControllerIT` boots
the real application against Testcontainers Postgres and drives both endpoints over real HTTP: the
three rows land correctly, a duplicate username/email each produce their own 409 message, the reserved
prefix and a mismatched password confirmation both produce 400, login succeeds by username or by
email, a wrong password and an unknown identifier both produce the identical generic 401, and — the
FR-SESS-003 clause itself — a second login revokes the first session's row (`revoked_reason =
'DISPLACED'`) while leaving exactly one active session for the account. `./mvnw verify` and
`-Pintegration` both green locally; **CI green on `master`** (build, 7m59s).

**No specification defect found in the credential-auth path itself.** Two were found and closed
opening the item — see `IMP-GATE-26`/`IMP-GATE-27` below, both opened and closed this session.

**Two runtime dependencies neither `input-validation.md` nor `conventions.md` names, because they are
transitive gaps in libraries the documents *do* name, not choices made here:**
`Argon2PasswordEncoder` delegates to Bouncy Castle's Argon2 implementation
(`org.bouncycastle.crypto.params.Argon2Parameters$Builder`) at runtime — `spring-security-crypto`
keeps `bcprov-jdk18on` optional since not every consumer hashes with Argon2 — so registering a user
threw `NoClassDefFoundError` until it was added explicitly (`runtime` scope, pinned `1.85.2`, not
managed by the Spring Boot BOM). ICU4J itself needed no such fix; only the SpoofChecker API shape
(`failsChecks(String)`, `getSkeleton(CharSequence)`, `Builder.setChecks`/`setRestrictionLevel`) had to
be read from the actual `78.3` jar rather than assumed.

**No OAuth here.** `FR-AUTH-007…012`/`016` and the Google round trip are `IMP-M1-10`, split out by
`IMP-GATE-26` below — this item's own read-list and Done-when never covered them.

**Closed:** IMP-GATE-26 (opened and closed 2026-09-06, session 29) — this item's *Satisfies* claimed the full
`FR-AUTH-001…016` range, which includes six OAuth requirements (`FR-AUTH-007…012`, `FR-AUTH-016`) and
`VW-OAUTHCOMP-001…002`, but the *Done when* clause never mentioned OAuth — no `/auth/callback`, no
`/auth/complete-registration`, no Google client, no `state` handling — and the read-list didn't even
carry `secrets-and-configuration.md` §5, the document naming the OAuth client secret's config key
(`TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`) an implementation would need. `platform-operations.md`'s own
account of the OAuth client secret states "Google login is unavailable without it... credential login
(FR-AUTH-006) is complete on its own" — i.e. the two are already understood as separable features, so
Google OAuth (a full external round trip: consent screen, code exchange, `state` signing, the
FR-AUTH-016 collision-and-link path) not fitting the same *Done when* as credential auth is not a
surprise, it just was never given its own item. Fixed: this item is retitled *Credential registration
and login* and narrowed to what its *Done when* actually checks — `FR-AUTH-001…006, 011, 013…015`,
dropping the six OAuth-only IDs and `VW-OAUTHCOMP-001…002`. **IMP-M1-10** (new, below) owns Google
OAuth end to end, depending on this item for the `user_auth_method`/session-issuance machinery it
reuses. `VW-LOGIN-001…004`/`VW-REG-001…003` stay split across both — the credential form and page
shell here, the OAuth button and its endpoint in `IMP-M1-10`.

**Closed:** IMP-GATE-27 (opened and closed 2026-09-06, session 29) — building the endpoints that set
the session cookie (`user-accounts.md` CON-004) needs `rest-conventions.md`'s Authentication section,
which was missing from this item's read-list entirely — a registry defect independent of IMP-GATE-26.
Reading it surfaced a second gap: no document anywhere in the corpus names the cookie itself — its
`httpOnly`/`Secure`/`SameSite=Strict` properties are specified, but never its name. Every future item
that reads the cookie back (the STOMP handshake in `IMP-M2-02`, the SSE endpoint in `IMP-M5-03`, any
authenticated-route filter) needs the same string this item picks when setting it, and nothing forced
that agreement. Fixed: `rest-conventions.md`'s Authentication section now names it —
`turnbase_session`, `Path=/` — as a fixed protocol constant, not a `local-environment.md` §7 tunable:
a name two server-side code paths must agree on is not something an operator should be able to change
independently. Read-list corrected to include `rest-conventions.md`.

**Read first:**
- `docs/requirements/user-accounts.md` — FR-AUTH-001…006, FR-AUTH-011, FR-AUTH-013…015, FR-ACCT-001,
  NFR-SEC-001…003, 005…007
- `docs/specs/platform/data-model-accounts.md` §1 (`app_user`), §2 (`user_auth_method`)
- `docs/specs/api-design/input-validation.md` — the field catalogue and canonicalization
- `docs/specs/api-design/rest-conventions.md` — Authentication section (the session cookie's shape
  and name)
- `docs/specs/flows/01-arrival-and-account.md` §A, §D (§E is `IMP-M1-10`'s)

**Satisfies:** `user-accounts.md` FR-AUTH-001…006, FR-AUTH-011, FR-AUTH-013…015, FR-ACCT-001,
NFR-SEC-001…003, NFR-SEC-005…007; `platform-views.md` VW-LOGIN-001, VW-LOGIN-003…004, VW-REG-001,
VW-REG-003

**Done when:** registration and login endpoints exist with the validation rules of
`input-validation.md`; uniqueness is enforced by a database constraint **and** surfaced as a domain
error rather than a constraint-violation 500; passwords are Argon2 (NFR-SEC-001); a user always
retains at least one active auth method (FR-AUTH-011); login displaces the previous session per
`user-accounts.md` FR-SESS-003.

**FR-AUTH-015's homograph rule is a canonicalization problem, not a regex.** Compare usernames on
their canonical form, and store both the display form and the canonical form — a check applied only
at write time is bypassed by every later rename path.

---

### IMP-M1-05 — Guest minting and purge

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 31).** `POST /api/auth/guest` (`account.AuthController`) mints a
credential-free guest — `account.GuestService.mint` inserts `kind='GUEST'`, a
`guest-<serial>` username drawn from `guest_serial_seq` (`account.AccountRepository.insertGuestUser`),
no `user_auth_method` row and no `user_privacy_settings` row — then issues a session through the same
`SessionService.issueSession` registration and login already use, so the response is a `201` with the
session cookie set, identical in shape to registration's. Exempt from NFR-SEC-006 per `IMP-GATE-29`.

`account.GuestPurgeJob` runs the two-phase purge on `turnbase.jobs.guest-cleanup.interval`, under
`net.javacrumbs.shedlock`'s `@SchedulerLock` over the baseline's `shedlock` table (FR-JOB-005 — the
first scheduled job in this repo, so also the first to need it). Revoke phase:
`session.SessionService.revokeAllForUser` first (the actual inaccessibility mechanism —
`SessionAuthenticationFilter` never consults `app_user`), then `account.GuestPurgeRepository.markExpired`
sets `deleted_at`/`deletion_reason='GUEST_EXPIRED'`/`purgeable_after`. Purge phase
(`purgeUnreferencedGuests`) hard-deletes anything purgeable with no `room_participant` or
`room.host_user_id` reference, in the same run — `purgeable_after` is set to the revoke instant, not a
future deadline, per `data-model-accounts.md` §1's "not on a timer".

**Verified end to end.** `UsernamePolicyTest` covers the guest-skeleton method directly.
`AuthControllerIT` gained two tests: guest mint issues a working, credential-free, immediately
authenticated session with a unique serial. `GuestPurgeJobIT` proves all three `Done when` clauses
against a real Postgres: revoke phase (session revoked, event published, `app_user` marked — checked
against a room-seated guest so the purge phase in the same run doesn't remove the row first), the
unreferenced case (hard-deleted in the same run), and the load-bearing case — a guest seated in a live
room survives the purge phase indefinitely. `./mvnw verify -Pintegration` green locally (73 unit + 45
integration tests); CI green on `turnbase-platform` `master` (`build`, 8m3s — `e2e` stays blocked on
the same un-provisioned `TURNBASE_GAME_HOST_PAT` prior sessions' runs also show).

**Closed:** IMP-GATE-29 (opened and closed 2026-09-08, session 31) — `user-accounts.md` NFR-SEC-006
enumerated the endpoints exempt from session authentication ("the landing page, the login endpoint,
the registration endpoint, user profile pages, the game catalog, game detail pages") and omitted guest
creation, but `docs/specs/api-design/rest-conventions.md`'s Authentication section derives its own
"except" set from that exact list, and its idempotency section separately states `POST /api/auth/guest`
is "an unauthenticated `POST`" outright, matching `rate-limiting.md`'s Tier 5 text. A caller minting a
guest account has by definition no session yet, so the endpoint cannot require one — the omission was
not a defensible narrower reading, since satisfying NFR-SEC-006 literally would make FR-GUEST-001
unreachable. Fixed: NFR-SEC-006 now names the guest-creation endpoint alongside login and
registration, with the reason (no session exists yet to require) inline so the next reader doesn't
re-derive it.

**Closed:** IMP-GATE-30 (opened and closed 2026-09-08, session 31) — this item's *Satisfies* claimed
the full `FR-GUEST-001…010` range, but FR-GUEST-010 ("Guest profile display... only the username")
needs a `GET /api/users/{username}` profile-read endpoint that does not exist yet — that build is
`IMP-M1-07`'s (`FR-PROF-001…008`), which was never a dependency here. `user-accounts.md` FR-PROF-002
("Guest profile display") states the identical duty ("displays only the username... all other
profile fields... are not shown") under a different ID in the same document — a duplicate
`docs/requirements/INDEX.md` doesn't track, since it only lists prefix collisions *across*
documents — not a second requirement to satisfy separately. Same shape as
`IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed: this item's
*Satisfies* narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* below gained `FR-GUEST-010`
alongside its existing `FR-PROF-002`, recording that the one endpoint discharges both IDs.

**Read first:**
- `docs/requirements/user-accounts.md` FR-GUEST-001…009, NFR-SEC-006
- `docs/specs/platform/data-model-accounts.md` §1 (the `kind` discriminator)
- `docs/requirements/platform-operations.md` FR-RET-002 (the guest purge window)
- `docs/specs/deployment/local-environment.md` §7.3
- `docs/specs/api-design/rest-conventions.md` § Authentication (`POST /api/auth/guest`'s route,
  status code and response shape — the read-list omitted the one document naming the endpoint itself)

**Satisfies:** `user-accounts.md` FR-GUEST-001…009; `platform-operations.md` FR-RET-002

**Done when:** a guest principal can be minted without registration; guest serials are unique
(FR-GUEST-002); guests have no auth method, no friends, no statistics and no uploads (FR-GUEST-004,
007, 008, 009); the purge is **two-phase** and a guest seated in a live room is never removed — a
literal 24-hour delete fails permanently on `room_participant`'s FK, and the cascade that would
"fix" it removes a seated player from a live game. The real bound is ~8 days.

---

### IMP-M1-06 — Session lifecycle and displacement

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 30).** `session.SessionAuthenticationFilter` resolves the
`turnbase_session` cookie against `user_session` on every request — JWT verify, then the DB row's
`revoked_at`/`expires_at` — and wraps the request with a `common.AuthenticatedUser` principal on
success, or records why not (`invalid`, `expired`, or the row's own `revoked_reason`) on a request
attribute. It never rejects anything itself; ordered ahead of `CorrelationIdFilter` so the latter's
`userId` MDC value sees a resolved principal rather than running before one exists.
`session.SessionAuthenticationInterceptor` is the actual enforcement — a `HandlerInterceptor`
(the `RequestSizeInterceptor` pattern, so a rejection reaches `GlobalExceptionHandler` through the
same path as every other domain failure): a protected path with no principal throws
`UnauthenticatedException`, with FR-SESS-004's own wording when the reason is `DISPLACED`
("...because you logged in from another device"). NFR-SEC-006's exempt list, `PUBLIC_PATHS`, holds
exactly what has a server-side route today (`register`, `login`); `/test/` is separately exempt for
`IMP-M1-01`'s `GlobalExceptionHandlerIT` harness, which isn't a platform endpoint at all.

`GET /api/auth/session` and `POST /api/auth/logout` complete `rest-conventions.md`'s four-endpoint
session lifecycle table — the third and fourth existing only from this item on. `SessionService`
gained `revoke(sessionId, userId, reason)` for logout, symmetric with `issueSession`'s displacement:
both now publish `session.SessionRevokedEvent(sessionId, userId, reason)` **after** their own
transaction has committed (a plain post-commit call, not a `@TransactionalEventListener` — the
transaction is already committed by the time `issueSession`/`revoke` return, so there was no reason
to reach for the annotation). The event is the mechanism `IMP-M2-02` and `IMP-M5-03` subscribe to
once their connection registries exist (`IMP-GATE-28`).

**Verified end to end.** `SessionAuthenticationFilterTest`/`SessionAuthenticationInterceptorTest`
(unit, Mockito + `spring-test`'s `MockHttpServletRequest`) prove the filter's per-outcome attribute
and the interceptor's per-reason message directly. `AuthControllerIT` gained: a second login
publishing a `DISPLACED` `SessionRevokedEvent` for the first session; `GET /session` returning the
principal when authenticated and the generic 401 with no cookie; `POST /logout` revoking the row
(`revoked_reason = 'LOGOUT'`), clearing the cookie, and publishing the `LOGOUT` event; and a request
bearing the *first* session's cookie after a second login receiving exactly FR-SESS-004's wording.
`./mvnw verify -Pintegration` green locally (71 unit + 40 integration tests, JaCoCo merged gate
met); CI green on `master` (`build`, 9m0s — `e2e` remains blocked on the un-provisioned
`TURNBASE_GAME_HOST_PAT`, the same pre-existing gap `IMP-M1-04`'s run also shows, `conventions.md`
§3).

**Closed:** IMP-GATE-28 (opened and closed 2026-09-08, session 30) — this item's *Satisfies* claimed
`FR-SESS-010` in full, but the requirement's actual duty — closing a session's live WebSocket/SSE
connections on revocation, "after emitting a frame stating the reason" — needs a connection registry
to close, and none exists yet: `IMP-M2-02` (STOMP) and `IMP-M5-03` (SSE) are both still `READY`, and
this item has neither as a dependency. Worse, `IMP-M5-03`'s own *Satisfies* didn't claim `FR-SESS-010`
at all, despite SSE being one of the two connection types the requirement names — so no item's
*Done when* actually required the close-on-revocation behaviour anywhere in the registry. Same shape
as `IMP-GATE-08`/`IMP-GATE-18`: a *Done when* clause reaching past infrastructure that doesn't exist
yet. Fixed: this item's *Satisfies* narrows to `FR-SESS-001…004, FR-SESS-011` — what it actually
builds is the revocation write and a `SessionRevokedEvent` a connection registry can subscribe to, not
the close itself. `IMP-M2-02`'s *Done when* gains the STOMP-side close-on-revocation clause (it already
claimed `FR-SESS-010`). `IMP-M5-03`'s *Satisfies* now also claims `FR-SESS-010`, its *Done when* gains
the SSE-side close-on-revocation clause, and `IMP-M1-06` is added to its *Depends on* — it needs the
event type this item publishes.

**Read first:**
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/platform/data-model-accounts.md` §3 (`user_session`)
- `docs/specs/api-design/rest-conventions.md` § *Authentication*
- `docs/specs/api-design/websocket.md` § *Authentication*; `docs/specs/api-design/sse-notifications.md`
  § *Endpoint*

**Satisfies:** `user-accounts.md` FR-SESS-001…004, FR-SESS-011

**Done when:** at most one active session per account holds as a **database** invariant, not as a
service-layer check (FR-SESS-002); a new login revokes the previous session and writes
`user_session.revoked_reason` (FR-SESS-003); a request bearing an invalidated token receives the
`error-handling.md` 401 shape (FR-SESS-004); logout revokes (FR-SESS-011); every path that revokes a
session (displacement, logout) publishes a `SessionRevokedEvent(sessionId, userId, reason)` after its
own transaction commits — the mechanism `IMP-M2-02`'s STOMP registry and `IMP-M5-03`'s SSE registry
subscribe to once they exist. This item has no live connection to close, so FR-SESS-010's actual duty
is proved there, not here.

**FR-SESS-010 authenticates a WebSocket or SSE connection once, at handshake — and that is the
trap.** A long-lived connection is not re-checked per frame, so revoking a session does nothing to a
socket that is already open unless revocation *pushes* a close to it. Displacement must terminate the
displaced session's live connections; a check-on-next-frame design silently keeps the old device
connected for as long as it stays quiet.

**ID collision:** `FR-SESS-001`/`003` also exist in `platform-architecture.md` meaning something
else. `user-accounts.md` is the one that governs here.

---

### IMP-M1-07 — Profiles and privacy settings

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 32).** `account.ProfileController` (`/api/users`) adds four endpoints
alongside `AuthController`'s. `GET /{username}` (`ProfileService.view`, exempt from
`SessionAuthenticationInterceptor` via the new `isPublicProfileRead` path match, since the route
carries a variable segment `PUBLIC_PATHS`'s literal set can't match) resolves privacy **server-side**
against `ProfileRepository.findBySkeleton`'s single query: a soft-deleted row returns the FR-ACCT-009
placeholder (`{"username","deleted":true}`, checked before kind so a purged guest gets it too), a
`GUEST` row returns username-only (FR-GUEST-010), the owner (viewer id equals the row's) always gets
every section regardless of settings (FR-PROF-007), a private non-owner view gets none, and otherwise
`visibleSections` names only the sections not `HIDDEN` — `@JsonInclude(NON_NULL)` plus a *named*
(not boolean) section set is what makes "omits hidden sections" literal rather than a client-trust
convention. `PATCH /me` (FR-ACCT-002/003) updates username and/or email in one call, each against its
own `username_changed_at`/`email_changed_at` window (`AccountProperties.renameWindow`, already wired
by `IMP-M0-09`), rejecting an OAuth-sourced email outright. `POST /me/password` (FR-ACCT-010) and
`PATCH /me/privacy` (FR-PROF-004/006/008) round out the surface; all three `/me/**` mutations 403 for
a `GUEST` principal, which has no `user_auth_method` row to change a password against and no
`user_privacy_settings` row to patch (`data-model-accounts.md` §4: "a row exists only for registered
users").

**The friends section's third value, `FRIENDS_ONLY` (`social-friends.md` FR-SOC-017), resolves as
hidden for every non-owner viewer for now** — the confirmed-friendship check it needs is
`IMP-M1-09`'s, which depends on this item and does not exist yet. Recorded as a sentence on
`IMP-M1-09`'s own section below (same pattern as `IMP-M0-10`'s forward obligations) rather than a
gate, since it does not make this item's own Done-when unsatisfiable as written.

**Verified end to end.** `ProfileControllerIT` (13 tests, real Postgres): owner-sees-everything while
private, a private profile showing zero sections to another viewer, a public profile hiding only its
`HIDDEN` sections, an unauthenticated read of a public profile, the guest-only shape, the deleted
placeholder (not a 404), an unknown username *is* a 404, the username-window enforcement (success,
then a same-window rejection as `422`, then a duplicate as `409`), password change (wrong current
password `422`, correct one `204` and the new password logs in), and a guest `403` on the privacy
route. `./mvnw verify -Pintegration` green locally (91 unit + 58 integration tests, full suite); CI
green on `turnbase-platform` `master` (`build`, 6m34s — `e2e` stays blocked on the un-provisioned
`TURNBASE_GAME_HOST_PAT`, the same pre-existing gap every prior session's run also shows).

**Closed:** IMP-GATE-31 (opened and closed 2026-09-08, session 32) — no document in the corpus named a
route for FR-ACCT-002 (username update) or FR-ACCT-003 (email update); `rest-conventions.md`'s
"self-scoped account routes" named `POST /api/users/me/password` and `PATCH /api/users/me/privacy`
but nothing for the two other FR-ACCT mutations this item must satisfy. This item's own read-list
also never named `rest-conventions.md` at all, despite it being the document that supplies the
routes/status codes for every endpoint this item builds (`GET /api/users/{username}`, the password and
privacy routes above). Fixed: `rest-conventions.md` gained `PATCH /api/users/me` — one endpoint for
both username and email, each enforcing its own rolling 30-day window independently, email rejected
outright when OAuth-sourced (FR-AUTH-008/012); read-list corrected to include it.

**Read first:**
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010
- `docs/specs/platform/data-model-accounts.md` §1, §4 (`user_privacy_settings`)
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007 — the rendering contract the
  API must be able to satisfy
- `docs/specs/api-design/rest-conventions.md` § Authentication (the self-scoped account routes) and
  § Authorization and Ownership (the `/api/users/**` predicates) — omitted from the original read-list

**Satisfies:** `user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010, FR-GUEST-010
(`IMP-GATE-30`: FR-PROF-002 and FR-GUEST-010 are the same "guest profile shows only the username"
duty under two IDs — the `GET /api/users/{username}` endpoint built here discharges both)

**Done when:** privacy is evaluated **server-side on every read** and the response omits hidden
sections rather than returning them for the client to hide; **the owner is exempt from every one of
their own privacy settings** (FR-PROF-007, and IR-05's five conditions in `platform-views.md`
VW-PROF-002…003 and VW-FREN) — a private profile, a hidden section and a hidden friend list all
render in full to the person who set them; the 30-day username and email change limits are enforced
against a stored timestamp rather than a counter; a soft-deleted user's profile returns the
FR-ACCT-009 placeholder rather than a 404; a guest profile returns the username and nothing else
(FR-GUEST-010).

---

### IMP-M1-08 — Account deletion and erasure

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07

**Done 2026-09-08 (session 33).** `account.AccountDeletionService`/`AccountErasureRepository` add
`DELETE /api/users/me`. One `@Transactional` JDBC method disposes of every row in
`data-model-accounts.md` §5's table, in the order the spec states — `user_session` revoked
(`ACCOUNT_DELETED`), `user_auth_method` and `user_privacy_settings` deleted, `friendship` and
`friend_request` deleted both directions, `room_invitation` deleted both legs (cascading the
recipient's/inviter's `notification`), the caller's own `notification` rows deleted, any open
`game_review` on an owned game withdrawn (`decided_by = 'system'`), owned `game` rows archived,
`game_history_entry` pseudonymized with a fresh `UUID.randomUUID()` subject token (not derived —
ADR-0004 forbids a reversible construction), `app_user` soft-deleted (`deletion_reason =
'SELF_SERVICE'`, email released, username/skeleton retained per FR-ACCT-006), and
`room_participant` departures last. Room closure/host-transfer is deliberately not attempted here —
`room-lifecycle.md` §5.1 duty 2 on the owning instance discharges it within one sweep interval, since
this REST-triggered transaction holds no room claim. `user_session` is written directly rather than
through `session.SessionService` (which manages its own transaction boundary) precisely so the whole
disposition table is one physical transaction; `SessionRevokedEvent` is published for each revoked
session only after that transaction commits, closing live connections per FR-SESS-010. Guests get
`403`, matching every other `/me/**` mutation this repo builds.

**Verified end to end.** `AccountDeletionControllerIT`: every disposition-table object seeded and
checked after a real `DELETE` call against real Postgres — session revoked and the event published,
auth method and privacy settings gone, friendship/friend-request/room-invitation gone, the deleted
user's own notification gone, the open review withdrawn as `system`, the owned game archived, the
history entry pseudonymized with `user_id` nulled, the room-participant row showing a `LEFT`
departure with `lost_announced_at` still null, username retained and email released on the `app_user`
row. A second `DELETE` call gets `401` (no session left to authenticate with — the idempotent-retry
case `rest-conventions.md`'s general `DELETE` rule describes never arises here). A guest gets `403`.
`./mvnw verify -Pintegration` green locally, run five times to confirm no flakiness. CI green on
`turnbase-platform` `master` (`build`; `e2e` stays blocked on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's run also shows) — the first CI push caught a real bug
the local run hadn't: `UUID.compareTo` orders by signed-long comparison of the two halves, while
Postgres's `uuid` type orders by unsigned byte value, so a test fixture ordering a `friendship` pair
by `UUID.compareTo` violates `friendship_order_ck` for roughly half of random UUID pairs — passed
locally by chance, failed in CI on a different random draw. Fixed by comparing the canonical string
form instead, which matches Postgres's byte ordering exactly.

**Closed:** IMP-GATE-32 (opened and closed 2026-09-08, session 33) — this item's *Satisfies* claimed
the full `FR-ACCT-004…010` range, but `FR-ACCT-009` (deleted-profile placeholder) and `FR-ACCT-010`
(password change) are already implemented and claimed by `IMP-M1-07` — `ProfileService.view`'s
deleted-placeholder branch and `POST /me/password`, both verified in `ProfileControllerIT` — and
neither appears in this item's own *Done when* clause, which only ever tested the erasure-transaction
disposition table. Same shape as `IMP-GATE-08`/`18`/`28`/`30`. Fixed: narrowed to `FR-ACCT-004…008`
below, which is what this item actually builds — the deletion endpoint sets `deleted_at`, so
`FR-ACCT-009`'s already-built display renders correctly once this item runs, with no new code owed to
it here.

**Closed:** IMP-GATE-33 (opened and closed 2026-09-08, session 33) — no document in the corpus named a
route, method or status code for FR-ACCT-004 itself (the deletion trigger). `rest-conventions.md`'s
"self-scoped account routes" named `PATCH /api/users/me`, `POST /api/users/me/password` and
`PATCH /api/users/me/privacy` but nothing that triggers deletion, and this item's own read-list never
named `rest-conventions.md` at all despite it being the document that supplies the route for every
other `/api/users/me` mutation. Same shape as `IMP-GATE-31`. Fixed: `rest-conventions.md` gained
`DELETE /api/users/me` as a fourth self-scoped route — `DELETE` is the correct verb here, unlike
logout, because the account *is* the addressable resource named by `/me`. `204` on success, clears the
session cookie and closes live connections per `FR-SESS-010`, same as logout. No confirmation step at
the API layer — `VW-SET-007`'s confirmation is a frontend-only affordance. Read-list corrected to
include it.

**Read first:**
- `docs/specs/api-design/rest-conventions.md` § Authentication — the self-scoped account routes,
  including the deletion trigger added by `IMP-GATE-33`
- `docs/decisions/0004-account-erasure-pseudonymization.md`
- `docs/specs/platform/data-model-accounts.md` §5 in full — *Erasure: what account deletion actually
  writes*. §5 enumerates every object and its disposition; that enumeration is the specification.
- `docs/requirements/user-accounts.md` FR-ACCT-004…008
- `docs/specs/platform/data-model-catalog.md` §5, `data-model-history.md` §4,
  `data-model-notifications.md` §2, `data-model-social.md` §§1–2 — the documents that own the
  non-account objects §5 disposes of
- `docs/specs/platform/room-lifecycle.md` §4, §5.1 duty 2 — how an owed room closure is discharged

**Satisfies:** `user-accounts.md` FR-ACCT-004…008; `platform-operations.md` FR-RET-001, FR-RET-005

**Done when:** erasure is non-reversible — **a random token, not an HMAC**; `HMAC(user_id, pepper)`
is reversible by enumeration over a small id space given the key, which ADR-0004 forbids. Every
object listed in `data-model-accounts.md` §5 has a disposition, including the open `game_review`,
`room_invitation` on both legs, and `room`/`room_participant`. **Nothing happens by cascade on that
path** — a registered deletion is soft.

**The erasure transaction writes participant departures only.** It does not close rooms inline. A
room the deleted user hosted becomes an owed closure carried by the existing deferred tail —
`lost_announced_at IS NULL` — and is discharged by `room-lifecycle.md` §5.1 duty 2 on the owning
instance (IR-11). Closing a room from inside the erasure transaction means closing a room this pod
may not own, which is precisely the write ADR-0008's epoch fence exists to reject.

---

### IMP-M1-09 — Social graph, friendships and requests

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07

**Done 2026-09-08 (session 34).** `social.SocialController`/`SocialService`/`SocialRepository` add
the seven `social-rest-api.md` endpoints: `POST`/`GET /api/friend-requests`, `POST
/api/friend-requests/{id}/accept`, `DELETE /api/friend-requests/{id}` (cancel or decline,
discriminated by which side the caller is on), `GET /api/users/{username}/friends`, `DELETE
/api/users/me/friends/{userId}`, and `GET /api/users?search=`. Friendship rows insert in
`data-model-social.md` §1's canonical `(user_id_low, user_id_high)` order, using the same
canonical-string-form `UUID` comparison `IMP-M1-08` verified matches Postgres's unsigned-byte `uuid`
ordering (session 33) rather than `UUID#compareTo`. Send/accept/decline/cancel each write or
cascade-delete the matching `FRIEND_REQUEST`/`FRIEND_REQUEST_ACCEPTED`/`FRIEND_REQUEST_DECLINED`/
`FRIEND_ADDED` notification in the same transaction (FR-FREQ-001/003/004/006). The friend cap
(FR-SOC-009) and the block-friend-requests toggle (FR-SOC-021) are enforced without disclosing which
reason applies, both in the direct send response and in search's `canSendRequest` flag. Cross-feature
reads (`app_user`, `user_privacy_settings`, `notification`) go through raw `JdbcClient` SQL rather
than another module's Java API — the same pattern `account.AccountErasureRepository` established —
so `social` and `account` stay a one-way Modulith dependency: `account.ProfileService` calls the new
public `social.RelationshipQueries`; `social` never imports `account`. `account.ProfileResponse`
gained `relationshipState` (`social-rest-api.md` §9, FR-SOC-016), and the `FRIENDS_ONLY` friends-section
check `IMP-M1-07` left conservative now resolves against a real friendship. The confusable-skeleton
algorithm moved from `account.UsernamePolicy` into `common.UsernameSkeleton` so this item's
exact-username resolution can't drift from registration's.

**Verified end to end.** `SocialControllerIT` (17 tests, real Postgres): the notification coupling
on all four terminal actions (send/accept/decline/cancel), the FR-SOC-004 reverse-request auto-accept
with no leftover `friend_request` row, the sender cap and the blocked-recipient rejection (with the
Problem Detail `detail` text checked to never mention "block"), search's `canSendRequest` hiding the
same reason, idempotent delete on an already-resolved request and idempotent/mutual unfriend, a
third party forbidden from resolving someone else's request, `FRIENDS_ONLY` visibility and
`relationshipState` resolved against a real friendship (stranger vs. friend, `NONE`/`FRIENDS`/
`REQUEST_SENT`/`REQUEST_RECEIVED`), guests forbidden on every endpoint, and a ten-random-pair loop
guarding the canonical-ordering fix. `./mvnw verify -Pintegration` green locally, run twice. CI green
on `turnbase-platform` `master` (`build`, 10m17s — `e2e` stays blocked on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's run also shows). The first CI attempt on this commit
stalled for 55 minutes on the `Verify` step with no evidence of a code defect (two clean local runs,
no parallel test execution configured, no self-deadlock found in `SocialRepository`'s transactional
methods) and was cancelled and re-run; the re-run completed in the normal 6–10 minute range, pointing
to a one-off runner flake rather than a hang in this item's code.

**Closed:** IMP-GATE-34 (opened and closed 2026-09-08, session 34) — this item's *Satisfies* claimed
`notifications-invitations.md` FR-FREQ-001…006 in full, and `IMP-M5-03` independently claimed the
identical full range in its own *Satisfies*, but neither item's *Done when* clause tested the other's
overlap: this item's never mentioned notifications at all, and `IMP-M5-03`'s tested only the generic
retention/alert mechanics (the partial purge index, the SSE alert/notification class split), none of
it friend-request-specific. `data-model-notifications.md` §3's type table settles which item actually
writes the rows: `FRIEND_REQUEST`/`FRIEND_REQUEST_ACCEPTED`/`FRIEND_REQUEST_DECLINED`/`FRIEND_ADDED`
are all written at the moment a `friend_request` row is created, accepted, or declined — this item's
own transactions, not `IMP-M5-03`'s (which never mutates `friend_request`). Same shape as
`IMP-GATE-28`, in reverse: there the generic infrastructure item over-claimed a requirement the
specific producer had to build; here the generic item (`IMP-M5-03`) over-claimed a requirement the
specific producer (this item) actually builds. Fixed: `IMP-M5-03`'s *Satisfies* narrowed to drop
FR-FREQ-001…006 (its section below); this item keeps the claim, its *Done when* gained the notification
clauses below, and its read-list gained `data-model-notifications.md` §1/§3 — the column names and
type strings the original list never named.

**Closed:** IMP-GATE-35 (opened and closed 2026-09-08, session 34) — no document in the corpus ever
defined this item's REST surface. `rest-conventions.md`'s Authorization table has named the
`/api/friend-requests/{id}` ownership predicate ("`principal ∈ {sender, recipient}`, and the action
must match the side") since it was written, but nothing supplied the endpoints that predicate
governs — the same shape as `IMP-GATE-31`/`33`, except there the route was one missing row in an
existing table and here the entire feature's HTTP surface was unwritten, closer in size to
`room-rest-api.md`'s gap before `IMP-GATE-13`'s era. This item's own read-list never named
`rest-conventions.md` either, so nothing would have surfaced the gap short of writing the controller.
Fixed: new `docs/specs/api-design/social-rest-api.md` (registered in that directory's `INDEX.md`) —
seven endpoints (username search, send, list, accept, cancel/decline, friend list, unfriend) plus a
`relationshipState` extension to `GET /api/users/{username}` for FR-SOC-016, which is also how this
item's `IMP-M1-07` obligation (below) is discharged. Read-list corrected to include it.

**Read first:**
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform/data-model-social.md` §§1–3 — `friendship`, `friend_request`, and the
  interaction with `block_friend_requests`
- `docs/requirements/notifications-invitations.md` FR-FREQ-001…006
- `docs/requirements/user-accounts.md` FR-GUEST-007
- `docs/specs/platform/data-model-notifications.md` §1 (`notification` — the subject foreign keys and
  the actionable/informational split), §3 (the four `FRIEND_REQUEST*`/`FRIEND_ADDED` type rows this
  item writes)
- `docs/specs/api-design/social-rest-api.md` **in full** — the seven endpoints, the evaluation orders,
  the error table
- `docs/specs/api-design/rest-conventions.md` § Authorization and Ownership (the
  `/api/friend-requests/{id}` predicate) and § *Four further self-scoped account routes* (the pattern
  §7's `/api/users/me/friends/{userId}` follows)

**Satisfies:** `social-friends.md` FR-SOC-001…021; `notifications-invitations.md`
FR-FREQ-001…006; `user-accounts.md` FR-GUEST-007

**Done when:** guest exclusion is enforced by the foreign key — `friendship` references
`app_user (user_id, kind)` with a local `CHECK kind = 'REGISTERED'` — so `social-friends.md`
FR-SOC-020 cannot be violated from any code path; friendship rows are stored in the canonical
ordering `data-model-social.md` §1 defines, so the pair `(a,b)` and `(b,a)` cannot both exist; a
blocked user's request is rejected without disclosing that a block exists; sending a request inserts a
`FRIEND_REQUEST` notification for the recipient with `friend_request_id` set (FR-FREQ-001), in the same
transaction as the `friend_request` insert; accepting deletes the request, inserts the friendship, and
writes two subject-less notifications in the same transaction — `FRIEND_REQUEST_ACCEPTED` to the
sender and `FRIEND_ADDED` to the accepter (FR-FREQ-003); declining deletes the request and writes one
subject-less `FRIEND_REQUEST_DECLINED` notification to the sender only, none to the decliner
(FR-FREQ-004); cancelling deletes the request and, because the notification carries
`friend_request_id` with `ON DELETE CASCADE`, needs no separate delete statement for the recipient's
notification to disappear (FR-FREQ-006); `friend_request.expires_at` is written absolutely at insert as
`now() + :window`, from the same configuration key `NFR-SOC-SCALE-001` requires, never derived at read
time (the mechanical half of FR-FREQ-005 — the expiry purge job itself is `IMP-M5-04`'s); every
endpoint in `social-rest-api.md` §1 exists with the exact method, path and status codes that document
specifies, including the idempotent `204` on `DELETE /api/friend-requests/{id}` and `DELETE
/api/users/me/friends/{userId}` for an already-resolved id (§5, §7) and the `canSendRequest`/
`relationshipState` fields that carry FR-SOC-021's non-disclosure and FR-SOC-016's button state
respectively (§2, §9).

**Obligation left by `IMP-M1-07`:** `account.ProfileService.visibleSectionsFor` resolves the friends
section's `FRIENDS_ONLY` value (FR-SOC-017) as hidden for every non-owner viewer, since the
confirmed-friendship check it needs is this item's, not `IMP-M1-07`'s. This item's Done-when gains a
fifth clause: replace that conservative resolution with an actual friendship check (a direct query
against `friendship`, canonically ordered, is enough — no new public API is needed since
`ProfileService` and this item's code both live in `turnbase-platform`).

---

### IMP-M1-10 — Google OAuth registration and login

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 36).** Five endpoints (`OAuthController`, `OAuthRegistrationController`,
`account` package): `GET /auth/google` builds the consent-screen URL with a signed, short-lived
`state` (`session.OAuthStateService`, over the same JWT key set session tokens use) carrying a
validated internal redirect destination; `GET /auth/callback` exchanges the code server-side
(`GoogleOAuthClient`, resolving identity from Google's userinfo endpoint with the freshly-issued
access token rather than verifying the ID token itself) and resolves by
`(method='GOOGLE', provider_subject=sub)`, never by email; a first-time login mints a Redis-backed
pending record (`PendingOAuthRegistration`, `concern=application`) and sets `turnbase_oauth_pending`
rather than a session cookie. `POST /api/auth/oauth/complete-registration` creates the account or
reports `CHALLENGE_REQUIRED` (`200`, not an error — same shape as `social-rest-api.md`'s outcome
pattern) on an FR-AUTH-016 email collision, without creating a duplicate or silently linking;
`POST /api/auth/oauth/link-challenge` verifies the existing account's password and links the Google
identity as an additional `user_auth_method` on success, the same generic 401 on failure whether the
password is wrong or the collision account no longer resolves.

**One platform-wide gap found and fixed while building this item, not gated because the spec was
already correct.** `rest-conventions.md`'s Origin check for state-changing requests had never been
implemented anywhere in the app — six already-`DONE` items (`IMP-M1-04` through `IMP-M1-09`) build
`POST`/`PATCH`/`DELETE` endpoints with no such enforcement. Fixed with a new
`common.OriginCheckInterceptor`, registered ahead of every other interceptor
(`Ordered.HIGHEST_PRECEDENCE`) in `PlatformWebMvcConfig`, covering the whole app at once rather than
just this item's two new `POST` endpoints.

**`rate-limiting.md` changes**: Tier 1 gained `POST /api/auth/oauth/link-challenge` (an
auth-method-addition credential guess); Tier 4 gained the two redirect routes; Tier 5's OAuth
accounting moves to `complete-registration`'s actual success path — the callback never creates the
row, so counting there would charge an aborted registration against the cap.

**Verified end to end.** `GoogleOAuthClientTest`/`OAuthStateServiceTest`/`PendingOAuthRegistrationTest`
(unit) prove the pure mechanics directly, Google stubbed with a plain JDK `HttpServer` — no mock-HTTP
library is a project dependency. `OAuthServiceTest` (unit, Mockito) covers every branch of the
orchestration. `OAuthControllerIT` (Testcontainers Postgres + Redis, real HTTP) drives the full round
trip against a real boot: initiate → callback → complete-registration for a first-time login, a
returning login skipping the pending cookie entirely, and the email-collision challenge-and-link path
including a wrong-password rejection. `./mvnw verify -Pintegration` green locally (211 tests). CI
green on `turnbase-platform` `master` (`build`, 12m27s) — the `e2e` job's "Check out
turnbase-game-host" step fails for an unrelated, pre-existing reason also present in `IMP-M1-02`'s
accepted run.

**Closed:** IMP-GATE-37 (opened and closed 2026-09-08, session 36) — no document in the corpus named
the JSON/redirect REST surface this item builds: `secrets-and-configuration.md` §5 and
`flows/01-arrival-and-account.md` §E name two browser-navigated paths (`/auth/callback`,
`/auth/complete-registration`) but not the endpoint the "Continue with Google" button hits, not the
JSON endpoint the complete-registration page calls to learn the pending email or submit the username,
and not any endpoint for FR-AUTH-016's credential-challenge-and-link step; `rest-conventions.md`'s
Authentication section — the document naming every other auth endpoint — was missing from this item's
own read-list. Same shape as IMP-GATE-31/33/35. Fixed: new `docs/specs/api-design/oauth-rest-api.md` —
five endpoints (initiate, callback, read-pending, complete-registration, link-challenge), the
`turnbase_oauth_pending` cookie, and two new `local-environment.md` §7.4 TTL properties; `rate-limiting.md`
Tier 1's endpoint list gained the link-challenge route and Tier 5's OAuth row now names the exact
success path it counts; read-list corrected.

**Added 2026-09-06 (session 29), closing IMP-GATE-26** — see `IMP-M1-04`'s *Closed* note. Split out
because credential auth (`FR-AUTH-006`) is complete without it (`secrets-and-configuration.md` §1
says so directly — the OAuth client secret is absent by default and the platform starts anyway) and
because the OAuth round trip is a comparable amount of work to `IMP-M1-04` in its own right: consent
redirect, server-side code exchange, signed `state`, a Redis-backed pending-registration token, and
the FR-AUTH-016 email-collision challenge-and-link path — none of which the credential flow touches.

**Closed:** IMP-GATE-38 (opened and closed 2026-09-08, session 36) — `user-accounts.md` NFR-SEC-006
enumerates every endpoint exempt from session authentication and did not name this item's five: the
Google OAuth entry point and callback (never had a session to require) and the three
pending-registration JSON endpoints (gated by `oauth-rest-api.md` §2's pending token instead, a
different mechanism entirely). Same shape as IMP-GATE-29. Fixed: NFR-SEC-006 now names all five;
read-list gained the citation.

**Read first:**
- `docs/requirements/user-accounts.md` FR-AUTH-007…012, FR-AUTH-016, NFR-SEC-006
- `docs/specs/platform/data-model-accounts.md` §1 (`email_source`), §2 (`user_auth_method`)
- `docs/specs/deployment/secrets-and-configuration.md` §1 (the OAuth client secret's absent-by-default
  behaviour), §5 (`TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`, the redirect URI, the signed `state`)
- `docs/specs/flows/01-arrival-and-account.md` §E
- `docs/requirements/platform-views.md` VW-LOGIN-002, VW-REG-002, VW-OAUTHCOMP-001…002, VW-REDIR-004…006
- `docs/specs/api-design/rest-conventions.md` § Authentication, § Origin Policy and CSRF
- `docs/specs/api-design/oauth-rest-api.md` **in full** — the REST surface this item builds
- `docs/specs/api-design/rate-limiting.md` § Tier 1, § Tier 5
- `docs/specs/api-design/error-handling.md`
- `docs/specs/deployment/local-environment.md` §7.4 (the two new OAuth TTL properties)

**Satisfies:** `user-accounts.md` FR-AUTH-007…009, FR-AUTH-012, FR-AUTH-016; `platform-views.md`
VW-LOGIN-002, VW-REG-002, VW-OAUTHCOMP-001…002 (`FR-AUTH-010`/`011` are `IMP-M1-11`'s — `IMP-GATE-78`)

**Done when:** `GET /auth/google` redirects to Google with a signed, short-lived `state` carrying a
validated internal destination; `GET /auth/callback` verifies `state`, exchanges the code server-side
(client secret never reaches the browser), and resolves the identity by `(method='GOOGLE',
provider_subject=sub)` — never by email; a first-time login mints the `oauth-rest-api.md` §2 pending
record and cookie and redirects to `/auth/complete-registration`; `POST
/api/auth/oauth/complete-registration` creates `app_user` (`email_source='OAUTH'`), `user_auth_method`
and default privacy settings and issues a session, or responds `CHALLENGE_REQUIRED` when the email
collides with an active account (FR-AUTH-016) rather than creating a duplicate or silently linking;
`POST /api/auth/oauth/link-challenge` verifies the existing account's password, links the Google
identity as an additional `user_auth_method` on success, and returns the same generic failure message
on failure that reveals nothing about which account exists; the login/registration pages hide the
Google button when `TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET` is absent rather than offering a button that
fails.

**The redirect URI is `http://turnbase.localhost:8080/auth/callback`, not `localhost`** —
`secrets-and-configuration.md` §5 flags this explicitly: they are different URIs to Google, and the
platform origin is deliberately the non-obvious one.

### IMP-M1-11 — Account read and auth-method management

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-10

**Closed:** IMP-GATE-78 (opened and closed 2026-09-26, session 77) — `IMP-M6-03`'s Account Settings view
(`platform-views.md` VW-SET-001…006a) had nothing to render from and nothing to call. No route
returned the caller's own email, `email_source`, linked auth methods or per-section privacy values
(`GET /api/users/{username}` is the public representation and rightly omits them), and no route added
or removed an auth method: `oauth-rest-api.md` §11 and §12 deferred `FR-AUTH-010`/`011` to "a future
add/remove item" that no registry entry was. Fixed: `rest-conventions.md` gained `GET /api/users/me`
and `/api/users/me/auth-methods` (password add, Google complete, remove); `oauth-rest-api.md` gained
§7a (the three-request Google link flow, shaped by `turnbase_session` being `SameSite=Strict`);
`rate-limiting.md` Tier 1 names the routes; `IMP-M1-10`'s *Satisfies* no longer claims
`FR-AUTH-010`/`011`; this item is new, and `IMP-M6-03` depends on it.

**Read first:**
- `docs/requirements/user-accounts.md` FR-AUTH-008…012, FR-ACCT-002…003, NFR-SEC-003
- `docs/specs/api-design/rest-conventions.md` § Authentication — *The account representation* and
  the `/api/users/me` routes table
- `docs/specs/api-design/oauth-rest-api.md` §2, §3, §4, §7a, §10
- `docs/specs/platform/data-model-accounts.md` §1 (`email_source`, the two `*_changed_at` columns),
  §2 (`user_auth_method`, and FR-AUTH-011's guarded delete), §4 (`user_privacy_settings`)
- `docs/specs/api-design/rate-limiting.md` § Tier 1
- `docs/specs/api-design/error-handling.md`

**Satisfies:** `user-accounts.md` FR-AUTH-010, FR-AUTH-011 (the removal guard; the creation-time half
is `IMP-M1-04`'s)

**Done when:** `GET /api/users/me` answers the representation in `rest-conventions.md` and `403` for a
guest, with no `password_hash` or `provider_subject` anywhere in it; `usernameChangeableAt` and
`emailChangeableAt` are `null` when the field is changeable now and the instant the window elapses
otherwise; `POST .../auth-methods/password` adds a `PASSWORD` row under registration's password policy
and `409`s when one exists; `DELETE .../auth-methods/{method}` is a guarded delete in the same
transaction as its count (two concurrent removals against an account with two methods leave exactly
one — asserted with a real concurrent test, not a mock), refuses the only method with `422`, and
removing `GOOGLE` from an `email_source = 'OAUTH'` account sets `email_source = 'SELF'`; `GET
/auth/google?intent=link` needs a Registered session, and `/auth/callback` on that branch **issues no
session and reads none** — asserted by a callback with no cookie at all — storing only the
`oauth:link:{token}` record; `POST .../auth-methods/google` links only when the record's `userId`
equals the caller's (a record minted for user A, confirmed by user B, is `403` and is not consumed),
`409`s on an already-held `sub`, and never touches `email` or `email_source`; the four Tier 1 routes
count failures only.

---

## M2 — Rooms and realtime

The single most subtle milestone. `docs/specs/platform/room-lifecycle.md` and
`docs/specs/api-design/room-websocket.md` are the two core documents; read both in full before
starting **any** M2 item, along with ADR-0008, ADR-0009 and ADR-0010.

Walk `docs/specs/flows/02`, `04`, `05` and `07` before writing code.

Three invariants hold across every item in this milestone and are restated at the items where they
bite:

1. **The owner epoch is the fence token. The room version is not.**
2. **Commit before publish.** The version reaches Postgres before the delta reaches a client.
3. **Lock outer, transaction inner, publish after commit.** In that nesting, never another.

### IMP-M2-01 — Room CRUD and listing

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06, IMP-M2-03

**Closed:** IMP-GATE-41 (opened and closed 2026-09-08, session 38) — this item's read-list never named
[`data-model-catalog.md`](../specs/platform/data-model-catalog.md), although the endpoints it
determines cannot be built without it. Three separate needs land in that document and were nowhere in
the read-list: (1) `room-rest-api.md` §3's `canJoin`/`canSpectate` predicate and §3's row shape
(FR-LIST-002, FR-LIST-003a) need `game_version.min_players`, `.max_players`, `.supports_ai`,
`.supports_spectators`, `.supports_mid_game_join` — the actual queryable columns, joined via
`room.game_id`/`room.game_version` → `game_version(game_id, version)`; (2) `room-rest-api.md` §2's
create transaction said only "a game with an ACTIVE version the caller may see", but
`data-model-catalog.md` §1 *Where the write-side rules are enforced* names this as three concrete,
separately-checked preconditions on `INSERT INTO room` — `game.deleted_at IS NULL AND
game.archived_at IS NULL` (FR-GAME-013), `game.listed OR :creator = game.owner_user_id` (FR-GAME-007),
`game.badge <> 'UNVERIFIED' OR :creator = game.owner_user_id` (FR-PRV-002) — none of which
`room-rest-api.md` stated; (3) `gameName`/`hostUsername` in the list row and detail resource resolve
through `game.title` and `app_user.username` via `room.host_user_id`, both defined outside the
original read-list.

Also fixed a naming defect in the document that **was** read: `room-rest-api.md` §3 wrote
`game.capabilities.midGameJoin` and `game.capabilities.spectating` as if `game` carried a
`capabilities` object directly. It does not — `manifest-schema.md` §`capabilities` names the JSON
field `spectators`, not `spectating`, and `data-model-catalog.md` §2 projects it onto
`game_version.supports_spectators`/`.supports_mid_game_join`, not a nested object on `game` at all.
Fixed: `room-rest-api.md` §3's predicate (and §5 step 3's `IN_PROGRESS` mid-game-join check) now name
`gameVersion.supports_mid_game_join`/`.supports_spectators` and cite `data-model-catalog.md` §2; §2's
`gameId` field description now states the three room-creation preconditions explicitly; the *Related*
table gained `data-model-catalog.md`. This item's read-list gained `data-model-catalog.md` §1–§2.

**Closed:** IMP-GATE-40 (opened and closed 2026-09-08, session 37) — this item's own Done-when clause
5 requires the room-ownership claim/redirect/`503` mechanism, which `room-lifecycle.md` §1 documents
in full and which `IMP-M2-03` ("Ownership claim, lease, epoch fence") is the item that builds — but
`IMP-M2-03` depended on `IMP-M2-02`, which depended on `IMP-M2-01`. That is a cycle in substance: this
item cannot satisfy its own clause 5 without the mechanism `IMP-M2-03` owns, `IMP-M2-03` cannot start
under its old dependency until `IMP-M2-02` is done, and `IMP-M2-02` cannot start until this item is
done. Same shape as `IMP-GATE-03`/`08`/`18`/`28` — a *Done when* clause reaching past infrastructure
that does not exist yet — but here the infrastructure's own item was mis-sequenced *behind* the item
that needs it, rather than simply not yet written. `IMP-M2-04`, `IMP-M2-07` and `IMP-M2-10` already
depend on `IMP-M2-03` directly and needed no change — only the two REST/STOMP consumers were
mis-ordered relative to the mechanism they call. Fixed: `IMP-M2-03`'s *Depends on* changes to
`IMP-M1-06` (nothing in its own read-list — ADR-0008, `room-lifecycle.md` §1–§2, `data-model.md` §1,
`local-environment.md` §7.1 — needs REST or STOMP to exist first); this item's *Depends on* gains
`IMP-M2-03`; `IMP-M2-02`'s *Depends on* gains `IMP-M2-03` alongside its existing `IMP-M2-01` (its own
subscribe-time ownership re-verification, `room-lifecycle.md` §1.7, needs the same mechanism). Done-when
clause 5 below is unchanged in substance — the claim/redirect/`503` behaviour it describes is real and
still this item's to expose over REST — but it now presumes `IMP-M2-03`'s claim component exists to be
called, rather than requiring this item to build it.

**Closed:** IMP-GATE-39 (opened and closed 2026-09-08, session 37) — this item's read-list never named
`docs/specs/platform/room-lifecycle.md`, although `room-rest-api.md` (this item's own read-list
document, in full) cites it repeatedly as the mechanism behind Done-when clause 5 (the room-ownership
claim behind the `503`/`Retry-After` and `X-TurnBase-Room-Instance` behaviour, §1.2/§1.7) and behind
the delegation boundary in §6 (host-leave consequences run under `room-lifecycle.md` §4, not this
item). Separately, `room-rest-api.md` §5, §3, §3.1 and §4 build FR-JOIN-007 (the single-room
constraint, entirely inside the REST join transaction), FR-XFER-003 (closed-room invisibility/404) and
FR-HOST-002 (invite-code minting, host-only exposure, resolution) in full — all three inside this
item's own endpoints — yet this item's *Satisfies* claimed none of them, while `IMP-M2-05`'s
*Satisfies*/*Done when* explicitly claimed FR-JOIN-007 ("FR-JOIN-007's one-room-at-a-time rule is
enforced server-side") and `IMP-M2-06`'s *Satisfies* claimed FR-XFER-003 and FR-HOST-002 via its
`FR-XFER-001…005`/`FR-HOST-001…003` ranges, even though neither of those items' STOMP-layer read-lists
or done-when clauses touch the REST handlers that actually build them. Fixed: this item's read-list
gains `room-lifecycle.md` §1.2 (claim), §1.3 (release), §1.4 (adoption), and §1.7 (affinity hint) —
the mechanism Done-when clause 5 requires — plus enough of §4 to know where the delegation boundary to
`IMP-M2-06` sits. This item's *Satisfies* gains FR-JOIN-007, FR-XFER-003 and FR-HOST-002, which
`room-rest-api.md` builds here in full. `IMP-M2-05`'s *Satisfies* narrows its FR-JOIN range to
`FR-JOIN-001…006, FR-JOIN-008…011` (007 moves here) and its *Done when* drops the FR-JOIN-007 clause —
the STOMP command layer never touches the single-room constraint, which the REST join transaction
enforces before any STOMP command is reachable. `IMP-M2-06`'s *Satisfies* narrows to
`FR-HOST-001, FR-HOST-003, FR-HOST-006…009, FR-XFER-001…002, FR-XFER-004…005` — FR-HOST-002 and
FR-XFER-003 are this item's, not the host-transfer STOMP layer's.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §1.2 (*Claim*), §1.3 (*Release*), §1.4 (*Adoption*), §1.7
  (*Routing*) — the contract of `IMP-M2-03`'s claim component this item's handlers call for Done-when
  clause 5 (not this item's to implement, `IMP-GATE-40`), and enough of §4 to know the host-leave
  delegation boundary in `room-rest-api.md` §6
- `docs/specs/api-design/room-rest-api.md` **in full** — the five endpoints, §3's inclusion
  predicate, §5's join contract, §7's error table
- `docs/specs/platform/data-model.md` §1 (`room`), §2 (`room_participant`), §3 (`room_team`)
- `docs/specs/platform/data-model-catalog.md` §1 (`game`), §2 (`game_version`) — the room-creation
  preconditions (FR-GAME-013, FR-GAME-007, FR-PRV-002) and the `min_players`/`max_players`/
  `supports_ai`/`supports_spectators`/`supports_mid_game_join` columns behind §3's `canJoin`/
  `canSpectate` predicate and row shape (`IMP-GATE-41`)
- `docs/requirements/game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…006
- `docs/specs/api-design/pagination-filtering-sorting.md`, `rest-conventions.md`
- `docs/specs/manifest/manifest-schema.md` § `capabilities`, § `teamTemplates` — the manifest JSON
  shape `data-model-catalog.md` §2 projects onto `game_version`'s capability columns, and FR-TEAM-012's
  team instantiation; no other read-list document defines it (repaired, no gate — a plain missing
  citation)

**Satisfies:** `game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…007, FR-XFER-003,
FR-HOST-002, FR-LIFE-004, NFR-PERF-001, NFR-SEC-001…002, NFR-USAB-001, NFR-SPEC-001;
`notifications-invitations.md` FR-LINK-001…002 (`IMP-GATE-58` — this item's own §3.1 invite-code
mint/resolve mechanism is the entire behaviour either requirement describes; neither `IMP-M2-12` nor
`IMP-M5-03`, which both claimed it, builds anything toward it); `platform-views.md` VW-ROOMS-001…005,
VW-JOIN-001…003

**Done when:**

1. `POST /api/rooms` returns `201` with a `Location` header and the full room resource.
2. Listing applies §3's predicate exactly:
   `included(room, viewer) := room.state <> 'CLOSED' AND visible(room, viewer) AND (canJoin(room, viewer) OR canSpectate(room, viewer))`.
   An Invite Only room appears to nobody (FR-LIST-007); a Friends Only room appears only to the
   host's friends (FR-LIST-006).
3. `GET /api/rooms?inviteCode=…` returns a **0-or-1 element list and never a `404`**. A `404`
   confirms or denies the existence of a code to an unauthenticated prober, which is what
   NFR-SEC-002's unguessable identifiers were bought to prevent.
4. Join is **one** endpoint discriminated by the body's `{"role":"PLAYER"|"SPECTATOR"}`; leave is
   `DELETE /api/rooms/{roomId}/participants/me`.
5. A request that lands on a pod which is neither the owner nor able to claim returns `503` with
   `Retry-After` and the `room-unavailable-retry` problem type — **not** a redirect. The affinity
   hint travels as the `X-TurnBase-Room-Instance` response header.

**REST is membership only.** Team edits, readiness, parameters, kick and start are all STOMP
(IMP-M2-05, M2-06). Adding a REST route for any of them puts a second writer outside the per-room
serialization `room-websocket.md` depends on, and the ordering guarantee is gone.

**`PLAYER_JOINED`/`PLAYER_LEFT` broadcast on the join/leave transactions above is `IMP-M2-04`'s duty,
not this item's** (`IMP-GATE-43`) — both events require the lock-scoped, version-assigning,
commit-then-publish executor that item builds, which did not exist when this item shipped.

**`canSpectate`'s capacity is `turnbase.room.spectator-capacity`** (default `8`,
`local-environment.md` §7.1) — a platform property, not a room column and not a create-request field.
Hosts choose whether a room allows spectating; they do not choose how many (NFR-SPEC-001). The wire
field `spectatorCapacity` is the resolved value, so lowering the property never evicts a seated
spectator.

---

### IMP-M2-02 — STOMP endpoint, auth, subscriptions

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M2-03 (`IMP-GATE-40`: subscribe-time
ownership re-verification, `room-lifecycle.md` §1.7, needs `IMP-M2-03`'s claim component)

**Done 2026-09-09 (session 39).** New `websocket` feature package (`IMP-GATE-42`):
`WebSocketConfig` (`@EnableWebSocketMessageBroker`, STOMP at `/ws`, no SockJS, `.`-delimited
`AntPathMatcher`, 10000/10000ms heartbeats on an explicit `TaskScheduler` bean, simple broker on
`/topic`/`/queue`, `setPreservePublishOrder(true)`) → `WebSocketChannelInterceptor`, the single
`clientInboundChannel` interceptor: `CONNECT` reads the session token `SessionCookieHandshakeInterceptor`
stashed into the handshake attributes during the HTTP upgrade (the httpOnly cookie itself never
reaches a STOMP frame) and resolves it via `session.SessionService.resolve()` — a new public method
extracted from `SessionAuthenticationFilter` so the HTTP and WS paths share one token-verify-then-
session-lookup instead of duplicating it — then checks the `WebSocketRateLimiter` reconnect lockout
and `WebSocketConnectionRegistry.tryRegister()`'s connection cap (4/user); any failure throws, and
Spring's own STOMP handling turns that into a `CONNECT`-frame `ERROR` + close (`websocket.md` §
Authentication), so no bespoke frame-building was needed there. Every later frame is classified by
`WebSocketRateLimiter` into `rate-limiting.md` Tier 6's six buckets (pod-local Bucket4j `LocalBucket`s,
no Redis round trip) with the full penalty ladder — drop-and-throttled-notice, then sustained-violation
force-close via `WebSocketConnectionRegistry.closeSession()` (a manually-built STOMP `ERROR` command
message sent on `clientOutboundChannel`, which Spring's `StompSubProtocolHandler` closes the session
after relaying — verified end to end by `RoomSubscriptionAuthorizerIT`, not assumed), writing the
doubling `rate:ws-lockout:*` Redis key. `WebSocketConnectionRegistry` also exposes
`turnbase_websocket_connections_active` (`observability.md` §2, `platform-operations.md` FR-MET-002)
and subscribes to `session.SessionRevokedEvent`, closing every connection under the revoked login
session with its `revoked_reason` (`FR-SESS-010`, `IMP-GATE-28`).

`SUBSCRIBE` authorization is a pluggable seam (`websocket.SubscriptionAuthorizer`/`SubscriptionDecision`)
the channel interceptor dispatches by destination, kept out of `websocket` itself per the gate's
resolution. `room.RoomSubscriptionAuthorizer` is the one implementation today: membership
(`RoomRepository.isCurrentParticipant`, widened from `private`) gates a silent drop, then subscribe-time
ownership re-verification calls a new `RoomOwnershipService.claimWithRetry()` (the §1.7 bounded-retry
loop extracted from `RoomService.claimAndGetInstanceHeader`, now shared by REST and STOMP rather than
duplicated) — a `Redirect`/`Superseded` outcome after retries rejects with `ROOM_UNAVAILABLE_RETRY` and
`retryAfterMs` on `/user/queue/errors` (`room-websocket.md` § the "arises at two points" section),
never silently served. It also tracks which STOMP sessions are subscribed to which room (the only place
that knows the mapping, since `RoomOwnershipLostEvent` carries no session ids) and severs exactly that
room's sockets with a `ROOM_OWNERSHIP_LOST` code on `RoomOwnershipLostEvent` (`room-lifecycle.md` §1.5
layer 3/§1.6) — the subscriber `IMP-M2-03`'s own text named as still missing. Chat/team sub-topics
(`.chat`, `.team.*`) are deliberately out of `supports()`'s match — `IMP-M2-11`'s.

**Deferred, each to the item that owns it:** the room member/host `@MessageMapping` command handlers
and `ROOM_STATE` snapshot delivery (`IMP-M2-04`/`M2-05`/`M2-06`/`M2-11`) — this item's Done-when never
required them, and the Tier 6 `command`/`chat`/`snapshot` buckets already classify their destinations
so those items need no interceptor change; the game destinations and `action`/`snapshot`-for-game
classification (`IMP-M3-*`). **IMP-GATE-47** (closed the same session it opened, on `IMP-M2-11`):
`input-validation.md`'s per-destination STOMP frame-size ceiling was never built here either — this
item's own read-list never named `input-validation.md`, so `WebSocketChannelInterceptor` shipped Tier
6 classification with no companion size guard. `IMP-M2-11` adds it to the same interceptor, covering
this item's own `/app/room.*.member`/`.host` rows retroactively (no code change needed here — the
guard runs ahead of every feature's handlers) alongside chat's own row and the two game rows M3
inherits.

**Verified.** Unit: `WebSocketRateLimiterTest` (bucket classification, the drop→notify-throttle→
force-close ladder, lockout doubling), `WebSocketConnectionRegistryTest` (connection cap,
`SessionRevokedEvent` closes only matching sessions), `RoomSubscriptionAuthorizerTest` (membership,
both ownership outcomes, `RoomOwnershipLostEvent` severing, disconnect bookkeeping), `SessionServiceTest`
(the extracted `resolve()`, all five resolutions). Integration, real STOMP clients over a real port:
`WebSocketIT` (`CONNECT` with no cookie never completes a session; a valid cookie does; a non-member's
`SUBSCRIBE` produces no error and no data) and `RoomSubscriptionAuthorizerIT` (a member's `SUBSCRIBE`
on the owning pod, then a directly-published `RoomOwnershipLostEvent` actually closes that live
WebSocket with a `ROOM_OWNERSHIP_LOST` `ERROR` frame — the assumption most worth not merely asserting).
A Modulith circular-dependency trap surfaced and was fixed with two `@Lazy` injection points
(`WebSocketConfig`'s `WebSocketChannelInterceptor`, `WebSocketConnectionRegistry`'s
`clientOutboundChannel`) — both are themselves dependents of the broker infrastructure that Spring
cannot finish assembling until every `WebSocketMessageBrokerConfigurer` (including `WebSocketConfig`)
is constructed. `./mvnw verify -Pintegration` green locally (113 tests, merged JaCoCo gate met); CI
green on `turnbase-platform` `master` (`build`, 15m5s) after an unrelated fix landed in the same
session — a freshly-disclosed CRITICAL CVE (CVE-2026-75595) in `netty-handler`, pulled in transitively
by `IMP-M0-07`'s AWS SDK client, was blocking every push; pinned the whole `netty-bom` to `4.1.137.Final`.
`e2e`'s "Check out turnbase-game-host" step fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT`
every prior session's accepted run also shows.

**Closed:** IMP-GATE-42 (opened and closed 2026-09-09, session 39) — `conventions.md` §1's package
table lists the monolith's features exhaustively ("the feature list is the milestone decomposition")
but named no package for the STOMP/WebSocket infrastructure this item must build — base connection
config, CONNECT authentication, the Tier 6 pod-local rate limiter, and the connection registry — even
though `websocket.md` and `room-websocket.md` make clear this infrastructure is cross-feature (it
already spans `room` here and `game` from M3 onward), the same shape `rate-limiting.md` Tiers 1–5
already resolved by living in `common`. Fixed: `conventions.md` §1 gained a `websocket/` feature
package — connection config, CONNECT auth, Tier 6 limiter, connection registry and its
`turnbase_websocket_connections_active` gauge — with per-destination `SUBSCRIBE` authorization and
`@MessageMapping` command handlers staying inside the feature they authorize (`room` here, `game`
from M3), consuming `websocket/`'s public API rather than the reverse.

**Read first:**
- `docs/specs/api-design/websocket.md` — connection, authentication, envelope, authorization
- `docs/specs/api-design/room-websocket.md` — *Room Affinity and WebSocket Routing*, *Destinations*,
  *Message Envelope*, *Authorization Model*
- `docs/decisions/0002-websocket-room-affinity.md`
- `docs/specs/api-design/rate-limiting.md` Tier 6

**Satisfies:** `platform-architecture.md` FR-ROUTE-001…005; `user-accounts.md` FR-SESS-010;
`game-rooms.md` NFR-PERF-002

**Done when:** the handshake authenticates once from the session token and no frame re-authenticates
(FR-SESS-010); a SUBSCRIBE is authorised against room membership **at subscribe time**, so an
unauthorised destination is refused rather than silently delivering nothing; Tier 6's frame limit is
enforced pod-locally, in-process — it is the one tier that does not go to Redis, because a Redis round
trip per inbound frame is the cost the limiter exists to avoid; a client connected to a pod that does
not own the room is redirected using the affinity hint rather than served across instances (ADR-0002:
**there is no cross-instance fan-out**). The STOMP session registry this item creates exposes
`turnbase_websocket_connections_active` as a `Gauge` (`observability.md` §2 names the metric;
`platform-operations.md` FR-MET-002 defines it, deferred here by `IMP-M0-10`). The registry also
subscribes to `IMP-M1-06`'s `SessionRevokedEvent`: on receipt, every connection registered under that
`sessionId` is sent a STOMP `ERROR` frame naming `revoked_reason` and then closed — this is
`FR-SESS-010`'s actual duty (`IMP-GATE-28`), narrowed out of `IMP-M1-06` because no registry existed
there to close. **It also subscribes to `IMP-M2-03`'s `RoomOwnershipLostEvent`** the same way, to sever
a room's sockets on self-eviction or a per-room ownership mismatch and mark those closures
instance-initiated — `room-lifecycle.md` §1.5 layer 3/§1.6's socket-closing half, which `IMP-M2-03`
could not build itself since no STOMP registry existed there either.

---

### IMP-M2-03 — Ownership claim, lease, epoch fence

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06 (`IMP-GATE-40`: moved off `IMP-M2-02` —
nothing in this item's own read-list needs REST or STOMP to exist first, and both `IMP-M2-01` and
`IMP-M2-02` need this item's claim component, not the other way round)

**Done 2026-09-08 (session 37).** `room.RoomOwnershipService` — `claim()` runs §1.2's script verbatim
(`REDIRECT`=0, `ALREADY_MINE`=1, `ADOPTED`=2, matching the spec and `room-rest-api.md`'s own table
exactly, not a locally-renumbered equivalent) over `room:{roomId}:pod`/`:epoch`; `adopt()` is §1.4
steps 1–3 and 7 in one fenced `UPDATE ... WHERE owner_epoch < :epoch RETURNING version` — a guard
failure returns `Superseded` and self-evicts that room without retrying in place, matching §1.4 step
3's "abandon the adoption" instruction literally. `release()` is §1.3's compare-and-delete plus the
Postgres mirror, never resetting `owner_epoch`. `renewAndRecheck()` (`room.RoomOwnershipSchedulingConfig`,
`turnbase.room.lease.renew-interval`, no `@SchedulerLock` — every instance renews its own key, this is
not a cluster-wide job) renews via `SET ... XX` and treats a `false` reply as a proven lease lapse
(§1.5 layer 2/3), never a renewal-failure guess; it also independently re-verifies `room:{roomId}:pod`
for every locally-owned room on the same tick, so a Redis flush that steals one room's key evicts only
that room, not the whole instance. `epochOf()`/`nextVersion()` expose the two primitives every future
room-mutating item (`IMP-M2-04` onward) fences its own writes on.

**Steps 4–6 and 8 of §1.4 adoption (grace-period reservations, `connection_count` reset, session
re-dispatch, suppressed disconnect events), and §1.6's graceful-shutdown socket-closing sequence, are
not this item's** — they need `room_participant`/session infrastructure and a STOMP session registry
that do not exist yet. `RoomOwnershipLostEvent` is published on self-eviction and on a per-room
ownership mismatch with no subscriber yet, the same inversion `IMP-M1-06`'s `SessionRevokedEvent`
already established (`IMP-GATE-28`) — `IMP-M2-02`'s STOMP registry is the intended subscriber, and its
own Done-when already expects to build the disconnect-handler-skips-tagged-closes behaviour once it
exists. `IMP-M2-07`/`IMP-M2-08` own §1.4 steps 4–5 and grace-period semantics generally; Game Host
session dispatch (step 6) is M3's. Recorded as a sentence per item, not a gate — this item's own
Done-when never required them; `IMP-GATE-40`'s own text already scoped the dependency reorder to the
claim/fence mechanism, not full adoption.

**Verified.** `RoomOwnershipServiceIT` (9 tests, two full `TurnBaseApplication` contexts sharing one
Postgres/Redis, standing in for two pods — `PodIdentity` is a random-per-boot singleton so the two
naturally get distinct `podId`s): first claim adopts and stamps the room row; re-claiming is
idempotent and does not bump the epoch; a second instance is redirected while the incumbent's lease is
live and the room row is untouched; a second instance adopts once the incumbent's lease is deleted
(simulating lapse), epoch advances monotonically (2, never reset); self-eviction on lease lapse drops
every owned room and never recreates the liveness key; a per-room ownership mismatch (simulated Redis
flush) evicts only that room; a forged higher `owner_epoch` makes adoption's own guard fail and return
`Superseded`; release is graceful and never resets the epoch; `nextVersion()` assigns from the adopted
value and never goes backwards. `./mvnw verify -Pintegration` green locally (99 tests, JaCoCo merged
gate met); CI green on `turnbase-platform` `master` (`build`, 11m4s — `e2e`'s "Check out
turnbase-game-host" step fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT` every prior
session's accepted run also shows).

**Read first:**
- `docs/decisions/0008-room-ownership-lifecycle.md` **in full**
- `docs/specs/platform/room-lifecycle.md` §1 (all six subsections) and §2
- `docs/specs/platform/data-model.md` §1 — `owner_epoch`, `version`
- `docs/specs/deployment/local-environment.md` §7.1
- `docs/specs/flows/05-owner-loss-and-adoption.md`

**Satisfies:** `platform-architecture.md` FR-SCALE-001…007, NFR-AVAIL-001; `platform-operations.md`
NFR-AVAIL-001; ADR-0008

**Done when:** the claim script is atomic and is **also the failure detector** — no dead-pod watcher
exists anywhere in this design. The four layers of §1 are all present: atomicity, the
`pod:{podId}:alive` liveness gate (10 s TTL, renewed every 3 s), self-eviction on lease lapse via
`SET … XX`, and the owner-epoch fence. Every ownership-fenced write carries `WHERE owner_epoch <
:myEpoch` on adoption and the epoch **equality** fence on mutation. Invariant I1 holds.

**Self-eviction triggers on lease *lapse*, not on renewal failure.** A stop-the-world pause longer
than the TTL produces no failed renewal to observe — the pod simply wakes up holding a key that
expired and was taken. A renewal-failure check misses exactly the case that matters.

**The room version is not a fence token.** It is room-scoped and both producers advance it densely
from one sequence, so a stale owner is eventually *reached* by the legitimate owner and its CAS then
matches. Use the owner epoch.

**Instance-initiated closes are tagged and the disconnect handler skips them** (§1.5 layer 3, §1.6).
A drain or a self-eviction closes sockets deliberately; treating those closes as player disconnects
starts grace deadlines for players who never went anywhere.

---

### IMP-M2-04 — Room event versioning and fan-out

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M2-03

**Done 2026-09-09 (session 40).** `room.RoomEventExecutor` — a per-room `ReentrantLock`, keyed in a
`ConcurrentHashMap`, wrapping a `TransactionTemplate`-scoped mutation plus the fenced conditional
`UPDATE room SET version = …` and a post-commit `SimpMessagingTemplate.convertAndSend` to
`/topic/room.{roomId}`, all before the lock releases. Version assignment is
`RoomOwnershipService.nextVersion`'s existing in-JVM `AtomicLong` (`IMP-M2-03`), never a fresh read.
A fenced-commit failure (zero rows updated) calls the new `RoomOwnershipService.evictAfterFailedCas`
rather than retrying in place, matching `room-lifecycle.md` §2.1's "a failed CAS leaves the in-memory
room state dirty" — the next claim re-initializes from the database. A lock-acquisition timeout or a
statement timeout fails the command without evicting, per the same section.

Retrofitted REST join/leave (`IMP-GATE-43`/`44`): join's ownership claim moves before its transaction
(`RoomService.join`) so the mutation runs fenced and versioned inside the lock; a no-op join
(already a member) and a no-op leave (not a member) skip the executor's version bump and broadcast
entirely. Leave claims opportunistically and, when this instance doesn't own the room, falls back to
an unfenced update with no broadcast — the departure still commits (`204`), deferring the
announcement to the owning instance's next sweep, matching `releaseCallersCurrentRoom`'s existing
precedent for a caller's *other* room.

**Verified.** `RoomEventExecutorIT` (mechanism level): a mutation with an event assigns and commits
the next version from the counter (not a fresh `max()`), a no-event mutation never touches
`room.version`, a fenced-commit failure evicts the room and fails with `RoomUnavailableRetryException`
rather than retrying, and executing against an unclaimed room fails without mutating.
`RoomEventFanoutIT` (end to end, a real STOMP subscriber on `/topic/room.{roomId}`): a second player's
REST join broadcasts a version-1 `PLAYER_JOINED` with the correct payload, a re-join broadcasts
nothing, a REST leave broadcasts a version-2 `PLAYER_LEFT`, and a second leave broadcasts nothing.
`./mvnw verify -Pintegration` green locally (134 tests, merged JaCoCo gate met, run solitary after an
accidental concurrent double-run produced one Testcontainers-Postgres `Connection refused` flake in an
unrelated class, `JwtKeyRotationServiceIT` — confirmed non-reproducing in isolation). CI green on
`turnbase-platform` `master` (`build`, 12m).

**Closed:** IMP-GATE-43 (opened and closed 2026-09-09, session 40) — this item's own read-list
(`room-websocket.md` *Per-Room Serialization and Versioning*) states that every room mutation,
"whether REST-originated (join, leave, create) or STOMP-originated," acquires the room lock, commits
the version, and publishes the delta — and `room-rest-api.md` §5 (`IMP-M2-01`'s own read-list) says
outright that `PLAYER_JOINED` "is broadcast by the owning instance after the commit... not by this
handler synchronously," while `room-websocket.md`'s own `PLAYER_JOINED` entry says it is "Emitted
after the REST join call completes." But `IMP-M2-01` (`DONE`) built REST create/join/leave with no
lock, no version increment beyond the creation-time `0`, and no delta publish — because the
mechanism those sentences presuppose (a lock-scoped, version-assigning, commit-then-publish
executor) is exactly what this item builds, and did not exist until now. No item's *Done when*
clause named the REST retrofit explicitly, so the gap was invisible until this item's read-list was
checked against `IMP-M2-01`'s already-shipped code. Same shape as `IMP-GATE-08`/`28`: a duty that
presupposes infrastructure a later item builds. Fixed: this item's *Depends on* gains `IMP-M2-01`
(the handlers it retrofits); its read-list gains `room-rest-api.md` §5 (join) and §6 (leave); its
*Done when* gains the two explicit broadcast clauses below. Room **creation** needs no retrofit: at
insert time no pod has yet claimed the room (the Redis claim and the in-JVM epoch/version state this
item's executor relies on are both established *after* `createRoom` returns), so there is no lock to
acquire and no subscriber to publish to — `version = 0` at insert is already correct, not a mutation
awaiting a delta.

**Closed:** IMP-GATE-44 (opened and closed 2026-09-09, session 40) — `room-rest-api.md` §5 (join)
documented the Redis claim as running *after* the join transaction commits, but `room-lifecycle.md`
§2.1 and `room-websocket.md`'s own versioning section — both in this item's read-list — normatively
require "lock outer → transaction inner → publish after commit," and §2.1 says a stalled database
"blocks every operation on that room, including REST joins" — which only holds if a REST join
acquires the *same* lock a STOMP command does, before its mutation, not after. Claim-after-commit and
lock-before-transaction cannot both be true for the same endpoint. Fixed, in `room-rest-api.md`: §5's
claim moves to step 0, before the transaction — this does not reintroduce the remote-call-in-a-
transaction problem `room-lifecycle.md` §4 forbids (the claim is still outside the transaction, only
earlier), and the one cost (a validation failure after a successful claim leaves this instance owning
a room it added nobody to) is harmless. §6 (leave) gained the matching claim/lock/version/broadcast
paragraph — leave never claimed at all before this — with one deliberate asymmetry: leave's own
existing text already accepts "this handler may be executing on an instance that does not hold
\[the claim\]," so a failed claim there skips the lock/version/broadcast rather than failing the
request (`204` still holds; the departure is announced on the owning instance's next sweep instead),
where join's failed claim still fails the request as before.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §2 (*Versioning*)
- `docs/specs/api-design/room-websocket.md` — *Per-Room Serialization and Versioning*, *Server→Client
  Event Catalogue* (`PLAYER_JOINED`, `PLAYER_LEFT`), *Client Reconciliation*
- `docs/specs/api-design/room-rest-api.md` §5 (join — the `PLAYER_JOINED` broadcast this item wires
  up), §6 (leave — `PLAYER_LEFT`)
- `docs/specs/platform/data-model.md` §1 (`version`)
- `docs/decisions/0002-websocket-room-affinity.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-rooms.md` NFR-PERF-002

**Done when:** the version is committed to Postgres **before** the delta is published, and is
**assigned**, never `max()`-ed. Clients discard `delta.version <= localVersion`, so a pod that
re-issues a seen version is silently and permanently wrong for every client — strictly worse than a
gap. Chat is excluded from the counter entirely (`version: null`, IMP-M2-11). The REST join
transaction of `room-rest-api.md` §5 broadcasts `PLAYER_JOINED` and the REST leave transaction of §6
broadcasts `PLAYER_LEFT`, both through this mechanism and both after their own commit — closing the
gap `IMP-M2-01` (`DONE`) left open pending this item's mechanism (`IMP-GATE-43`).

---

### IMP-M2-05 — Join, teams, readiness

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-04

**Done 2026-09-09 (session 40).** Two new STOMP `@Controller`s dispatch on the command envelope's
`type` field, since STOMP routes by destination rather than by a field inside the frame body:
`RoomMemberCommandController` (`/app/room.{roomId}.member` — the whole Member Commands table:
`TOGGLE_READY`, `SWITCH_TO_SPECTATOR`, `SWITCH_TO_PLAYER`, `REQUEST_ROOM_STATE`) and
`RoomHostCommandController` (`/app/room.{roomId}.host` — this item's own slice: `ADD_TEAM`,
`REMOVE_TEAM`, `RESIZE_TEAM`, `REASSIGN_PLAYER`, `ADD_AI_PLAYER`; `KICK_PLAYER`/
`CHANGE_PARAMETERS`/`START_GAME`/`TRANSFER_HOST` are `IMP-M2-06`'s, whose FR-HOST/FR-XFER
requirements this item's read-list never names). Every mutation runs through `RoomEventExecutor`'s
lock — the "lock outer → transaction inner → publish after commit" nesting `IMP-M2-04` built —
with a fresh `RoomCommandException` carrying one of `room-websocket.md`'s closed error codes on
every precondition failure, caught at the dispatch site (not `@MessageExceptionHandler`) so the
originating command's `correlationId` can be echoed on `/user/queue/errors`. Authorization is
handler-level and authoritative: no channel-level fast-fail exists for these destinations
(`IMP-M2-02` deferred it), so every command re-verifies membership/role/host identity itself, under
the lock — required regardless for host commands, since host identity is mutable runtime state.

`RoomRepository` gained the readiness/role-switch/team-management mutations and the `ROOM_STATE`
snapshot assembly (`Snapshot Delivery`); team template parsing now also carries the manifest's
`name` field (`manifest-schema.md` § `teamTemplates`, defaulting to `"Team"`), needed for
`TEAM_ADDED`/`ROOM_STATE` payloads and unused until this item. `ROOM_STATE.players[].connected` is
unconditionally `true`: connection/disconnect tracking is `IMP-M2-07`'s, so no present participant
can be anything but connected before that item lands — not a shortcut, an honest reflection of what
the system can track today. `PLAYER_REASSIGNED.readinessReset` is likewise unconditionally `true`:
no AI seat can ever exist (IR-12), so the human-only branch is the only one reachable.

**FR-READY-004 (readiness resets on the return to Lobby) has no code here** for the same shape of
reason as `ADD_AI_PLAYER` below: nothing in the build so far can start a game session, so nothing
can end one and return a room to Lobby. The clause is real but unreachable until `IMP-M3-*`/
`IMP-M2-06` give a room a session to return from.

**Verified end to end on real STOMP clients** (`RoomCommandControllerIT`): readiness and role-switch
preconditions and broadcasts (including the host's `ROLE_NOT_ELIGIBLE` on `TOGGLE_READY`/
`SWITCH_TO_SPECTATOR`, `IMP-GATE-45`); team management preconditions (`TEMPLATE_MAX_TEAMS`,
`SIZE_OUT_OF_RANGE`, `TEAM_NOT_EMPTY`, `OVER_CAPACITY` via `RESIZE_TEAM`, `TEAM_FULL` via
`REASSIGN_PLAYER`); `NOT_HOST` for a non-host sender; `AI_NOT_SUPPORTED`; `UNKNOWN_COMMAND`; and a
unicast, version-stamped `ROOM_STATE` snapshot. `./mvnw verify -Pintegration` green locally (141
unit + 121 integration tests, coverage checks met). **CI green on `turnbase-platform` `master`**
(`build`, 13m15s); `e2e`'s "Check out turnbase-game-host" step fails on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's accepted run also shows.

**Closed:** IMP-GATE-45 (opened and closed 2026-09-09, session 40) — the Member Commands table's
*Authorized sender* column states a role precondition for `TOGGLE_READY`/`SWITCH_TO_SPECTATOR`
(non-host human player) and `SWITCH_TO_PLAYER` (spectator), but the error-code registry — which
states its own completeness ("the registry for every WebSocket error code in the corpus") — had no
code for violating it: `NOT_HOST` is host-only-command-sent-by-non-host, the opposite direction. Fixed:
`room-websocket.md` gained `ROLE_NOT_ELIGIBLE`, a note stating the *Authorized sender* column is
server-enforced (unlike FR-JOIN-008–010's client-side-only abandonment prompts), and the error table
row.

**Read first:**
- `docs/requirements/game-rooms.md` FR-JOIN-001…011, FR-TEAM-001…012, FR-READY-001…004,
  FR-LIFE-004…006
- `docs/specs/api-design/room-websocket.md` — *Client→Server Command Catalogue* and the matching
  server events
- `docs/specs/api-design/room-rest-api.md` §5 (the REST join, which precedes every STOMP command)
- `docs/specs/platform/data-model.md` §2, §3
- `docs/specs/flows/02-room-to-game-start.md`

**Satisfies:** `game-rooms.md` FR-JOIN-001…006, FR-JOIN-008…011, FR-TEAM-001…012, FR-READY-001…004,
FR-LIFE-005…006, FR-HOST-003, NFR-SPEC-001; `platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017

**`FR-HOST-003` added retroactively** (`IMP-GATE-46`, session 41, this item not reopened) — the
`ADD_AI_PLAYER` → `AI_NOT_SUPPORTED` behaviour below already satisfies it in full; `IMP-M2-06`'s
Done-when clause had duplicated the same check under its own claim.

**Done when:** auto-assignment follows FR-TEAM-005, and FR-TEAM-012's team instantiation happens
**before** the host is seated on room creation — a host assigned first has nowhere to go;
FR-TEAM-010's capacity floor is checked on **every** operation that could reduce total capacity, not
only on explicit slot removal (moving a player and removing a team both can); readiness resets on
the return to Lobby (FR-READY-004). **FR-JOIN-007 (the single-room constraint) belongs to
`IMP-M2-01`'s REST join transaction, not here** (`IMP-GATE-39`) — by the time a STOMP command is
reachable the caller already holds exactly one room's slot.

**AI is wire-present and behaviour-absent in v1** (IR-12). `ADD_AI_PLAYER` always returns
`AI_NOT_SUPPORTED`, the room snapshot's `aiPlayers` is always empty, and FR-READY-002 ("AI players are
always ready") is therefore implemented and unreachable. Implement it anyway; do not delete the
branch, and do not build an AI seat to make it reachable.

---

### IMP-M2-06 — Host management and transfer

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

**Done 2026-09-10 (session 41).** `RoomHostCommandController`'s switch gains `KICK_PLAYER`,
`CHANGE_PARAMETERS`, `START_GAME`, `TRANSFER_HOST`, each re-verifying host identity under
`RoomEventExecutor`'s lock like `IMP-M2-05`'s share. `CHANGE_PARAMETERS` validates every key against
the pinned game version's manifest parameter schema (`input-validation.md`'s whitelist — unknown key,
type mismatch, or out-of-range value) and persists the full merged set, not just the changed keys.
`START_GAME` evaluates FR-TEAM-009's three conditions atomically under the lock, collecting every
unmet condition into `START_CONDITIONS_NOT_MET`'s `details` rather than stopping at the first; on
success it calls a new `GameSessionStarter` port, whose only implementation
(`PendingGameSessionStarter`) is a deliberate no-op — no broadcast, no state change — since
`GAME_STARTED` requires a real `sessionId` that does not exist until `IMP-M3-05`. `KICK_PLAYER`
unicasts `KICKED` to the removed player (no `correlationId`, per `room-websocket.md`'s exact shape)
and conditionally enqueues a `player_left` game-backend input when a session is attached — currently
unreachable, since nothing before `IMP-M3-05` can attach one, the same "real but unreachable" shape
`IMP-M2-05` left for `FR-READY-004`. `TRANSFER_HOST` moves only `room.host_user_id`; the former host
keeps their player slot (FR-XFER-004).

**Verified end to end on real STOMP clients** (`RoomCommandControllerIT`, a fourth test method):
`NOT_HOST` for every command sent by a non-host; `PLAYER_NOT_FOUND` for an unknown kick target;
`PLAYER_KICKED` broadcast plus the kicked player's own unicast; `UNKNOWN_PARAMETER`/
`PARAMETER_TYPE_MISMATCH`/`PARAMETER_OUT_OF_RANGE` for each `CHANGE_PARAMETERS` whitelist rule, then
`PARAMETERS_CHANGED` carrying the full merged set; `START_CONDITIONS_NOT_MET` with a non-empty
`failedConditions` list while a non-host player is un-ready, then silence (no error, no broadcast, no
state change) once ready; `TARGET_NOT_PLAYER` for a `TRANSFER_HOST` naming a non-participant, then
`HOST_TRANSFERRED`, after which the former host's own further host commands get `NOT_HOST`.
`./mvnw verify -Pintegration` green locally (full suite: 122 tests, coverage checks met). **CI green
on `turnbase-platform` `master`** (`build`, 15m22s).

**Closed:** IMP-GATE-46 (opened and closed 2026-09-10, session 41) — this item's *Satisfies* and
*Done when* claimed five things it does not actually build, and were silent on the command surface
its own title names:

1. **FR-HOST-003 was already shipped by `IMP-M2-05`** (`RoomHostCommandController`'s `ADD_AI_PLAYER`
   returning `AI_NOT_SUPPORTED` unconditionally, verified by `RoomCommandControllerIT`) — this item's
   Done-when clause repeated a check that already passes and always will, since no dependency of this
   item changes that behaviour.
2. **FR-HDISC-001…004 is double-claimed with `IMP-M2-07`**, which already claims the identical range
   in full and is titled *Disconnect, grace deadlines, sweeps*. Worse, this item's own Done-when
   assigned itself "the sweep that closes `migration_window_expires_at`" — but `room-lifecycle.md`
   §5.1 defines that as **duty 3 of one ordered tick** alongside due expiries (duty 1), deferred tails
   (duty 2) and the outbox drain (duty 4), all squarely `IMP-M2-07`'s, which is not this item's
   dependency and has no sweep scaffolding in the codebase at all yet. Splitting duty 3 into a
   separate item is not merely awkward, it is unbuildable: there is no sweep tick for it to be a duty
   *of*.
3. **FR-XFER-002 and FR-XFER-005 are double-claimed with `IMP-M2-09`**, which builds the one
   `detachSession` method (`room-lifecycle.md` §4) that both requirements actually run through; no
   command in this item's own command set (`KICK_PLAYER`, `CHANGE_PARAMETERS`, `START_GAME`,
   `TRANSFER_HOST`) closes a room.
4. **FR-HOST-001 is double-claimed with `IMP-M2-12`** (*Room invitations*), which already owns it —
   invite-via-notification has nothing to do with a realtime host command.
5. **FR-HOST-009's happy path is unsatisfiable as written**: `room-websocket.md`'s `GAME_STARTED`
   event requires a real `sessionId` and `gameFrontendUrl`, which only exist once a game session has
   actually been created — machinery `IMP-M3-05` (*Orchestration client and session registry*) builds,
   and which is not this item's dependency. Same shape as `IMP-GATE-08`/`18`/`28`.
6. Incidentally found while resolving (3): `IMP-M2-09`'s own *Satisfies* also names **FR-XFER-003**,
   which `IMP-GATE-39` already assigned to `IMP-M2-01` in full (the REST-layer `state <> 'CLOSED'`
   listing predicate) — a second, unrelated double-claim on the same requirement. Fixed on `IMP-M2-09`
   below.

Fixed: this item's *Satisfies* narrows to `FR-HOST-006…009, FR-XFER-004` — the four commands
(`KICK_PLAYER`, `CHANGE_PARAMETERS`, `START_GAME`'s precondition/rejection half, `TRANSFER_HOST`) this
item actually builds. Its read-list drops `reconnection-flow.md`, `room-lifecycle.md` §3/§5 and
`data-model.md` §1's `migration_window_expires_at` — none of it is this item's mechanism any more.
`IMP-M2-07`'s own Done-when gains an explicit duty-3 clause (it already claimed FR-HDISC-004 in full
but never tested it — same shape as `IMP-GATE-34`). `IMP-M2-09`'s *Satisfies* drops `FR-XFER-003`.
`IMP-M2-05`'s *Satisfies* (`DONE`, not reopened) gains `FR-HOST-003` to match what it already shipped.
FR-HOST-009's success path — actually creating a session and broadcasting `GAME_STARTED` with a live
`sessionId`/`gameFrontendUrl` — is deferred to `IMP-M3-05`, which gains the clause below; this item
instead defines a narrow `GameSessionStarter` port and proves `START_GAME`'s precondition-check and
rejection path against an in-process stub, the same pattern `IMP-GATE-08` established for
`GameHostRegistryService`.

**Read first:**
- `docs/requirements/game-rooms.md` FR-HOST-006…009, FR-TEAM-009, FR-XFER-004
- `docs/specs/api-design/input-validation.md` — `CHANGE_PARAMETERS`' whitelist validation against the
  game manifest's declared parameter schema
- `docs/specs/api-design/room-websocket.md` — the Host Commands table and its four events
  (`PLAYER_KICKED`/`KICKED`, `PARAMETERS_CHANGED`, `GAME_STARTED`, `HOST_TRANSFERRED`)
- `docs/requirements/game-contracts.md` FR-IN-005 — the `player_left` input's `kicked` payload shape
  for the conditional `game_input_outbox` insert (no other read-list document defines it; repaired,
  no gate — a plain missing citation, same shape as `IMP-M2-01`'s manifest-schema.md fix)

**Satisfies:** `game-rooms.md` FR-HOST-006…009, FR-XFER-004.

**Done when:**

- `KICK_PLAYER` removes a human, AI, or spectator member in any room state; in In Progress it voids
  any active grace period on the target and enqueues a `player_left` game-backend input with
  `reason: kicked` (deferred to `IMP-M3-06`'s outbox — this item writes the row, it does not drain
  it); the kicked party receives a unicast `KICKED` error on `/user/queue/errors`.
- `CHANGE_PARAMETERS` is Lobby-only and whitelist-validated against the pinned game version's manifest
  parameter schema (`input-validation.md`): an undeclared key is `UNKNOWN_PARAMETER`, a type mismatch
  is `PARAMETER_TYPE_MISMATCH`, an out-of-range value is `PARAMETER_OUT_OF_RANGE`. Accepted changes
  broadcast and are retained verbatim across the room's return to Lobby (FR-HOST-008) — nothing here
  yet resets them, since nothing yet ends a game.
- `START_GAME` evaluates FR-TEAM-009's three conditions atomically under the room lock; any unmet
  condition rejects with `START_CONDITIONS_NOT_MET` and lists every failed condition, not just the
  first. On success it calls a new `GameSessionStarter` port; this item proves the call against an
  in-process stub implementation only — the real implementation, a live `sessionId`/`gameFrontendUrl`
  and the `GAME_STARTED` broadcast are `IMP-M3-05`'s clause, added there.
- `TRANSFER_HOST` requires the target to be a current human player (not spectator, not AI):
  `TARGET_NOT_PLAYER` otherwise. The former host retains their player slot and becomes a regular
  player (FR-XFER-004); valid in both Lobby and In Progress.
- Every handler re-verifies `principal.id == room.hostId` inside the lock, not just at the channel
  guard, since a `TRANSFER_HOST` command — including one racing this one — can change
  `room.hostId` between the two.

---

### IMP-M2-07 — Disconnect, grace deadlines, sweeps

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Done 2026-09-10 (session 43).** `room.RoomSubscriptionAuthorizer` increments
`room_participant.connection_count` on a session's first `SUBSCRIBE` to the bare room topic (the
mirror of the decrement below, and the missing piece that made the refcount design real for the
first time) and feeds a genuine `SessionDisconnectEvent` into a new `room.RoomService#onDisconnect`
— the membership map doubles as the instance-initiated-close tag (§1.5 layer 3/§1.6): `onRoomOwnershipLost`
removes a session from it *before* severing the socket, so the disconnect handler that fires
afterward correctly sees nothing to process, while a revoked or rate-limited session (which never
touches this map) is still processed as a genuine involuntary disconnect. `onDisconnect` runs
`RoomRepository#registerDisconnect` under `RoomEventExecutor`'s lock: still-connected (another tab)
is a no-op; Lobby or spectator (any state) is an immediate leave reusing `leaveRoom`; In-Progress
player opens a grace reservation (§3.1) and, if the disconnecting user was host, a second fenced
call applies FR-HDISC-001's immediate transfer to the next connected human by join order, unless
the migration window is open (FR-HDISC-004) or nobody else is connected (FR-HDISC-003, deferred).

`room.GraceDeadlineSweepJob` (`turnbase.jobs.deadline-sweep.interval`, no `@SchedulerLock` —
ownership-partitioned like `RoomOwnershipService`'s own lease renewal, ***not*** a cluster-wide job)
runs all four §5.1 duties in order: due expiries (§3.2's resolve statement, `announceInline=true`,
with §3.3 step 2's outbox insert conditional on `active_session_id IS NOT NULL`, IR-06); deferred
tails (announces a foreign instance's `EARLY_RELEASE`/`GRACE_EXPIRED`/`LEFT` resolution, then
applies FR-XFER-001 host disposition — transfer to the next connected human, or leave it for
closure to decide); elapsed migration windows (FR-HDISC-004, clearing the column and performing the
deferred transfer); and the outbox drain (not ownership-partitioned — a gRPC call needs no room
claim — allocating each row's `sequence` once and stamping `dispatched_at` only on ACK). Both
duty 1's and duty 2's closure evaluation call a new `room.RoomSessionDetacher` seam
(`IMP-GATE-49`).

**`IMP-GATE-48`'s adoption fix carried a correction found while testing it**: the mass grace-open
must not run on a room's very first-ever claim, only a genuine takeover — the claim script's own
`ADOPTED` result conflates "free" and "lease lapsed" (§1.2), but the Redis epoch counter still
distinguishes them (epoch 1 is always the first claim). Without this, a fresh room's own creator
was handed a grace reservation before their first `SUBSCRIBE` ever completed, since nothing
distinguishes "never connected" from "connection_count = 0" otherwise.

**Two latent bugs in already-shipped code, exposed by finally building the mechanism they
presuppose:** `RoomRepository#leaveRoom` (`IMP-M2-01`) stamped `lost_announced_at = null`
unconditionally rather than per `:announceInline` (§3.2), which would have made every ordinary
voluntary leave (already announced correctly at leave time) match duty 2's predicate again and
double-broadcast a spurious `PLAYER_LOST` one sweep tick later — fixed by adding the parameter
`RoomService#leave`'s two branches already needed. `releaseCallersCurrentRoom` (`IMP-M2-01`,
FR-EXPIRY-004's early release) never inserted the `player_left` outbox row game-contracts.md FR-IN-005
requires from "the acting instance" — fixed, reusing `insertPlayerLeftOutbox`.

**A discovered JDBC hazard, not a spec defect:** `UPDATE ... RETURNING team_id` mapped through
`.query(UUID.class).optional()` cannot distinguish a genuinely-unmatched row from a matched row
whose `team_id` is itself `null` — both collapse to `Optional.empty()`. `resolveExpiredReservation`
now checks `.list()` emptiness instead, the rowcount being what §3.2 actually promises as "the
entire idempotency story," never the value.

**Verified**, `GraceDeadlineSweepJobIT` (10 methods) plus `RoomOwnershipServiceIT`'s new adoption
test: Lobby/spectator disconnect is an immediate leave with no reservation; a second open tab stops
a disconnect from doing anything; an In-Progress player disconnect opens a reservation and bumps
the version once; a disconnecting host transfers immediately with another human connected and
defers with none; the sweep resolves a due expiry, inserts the outbox row only when a session is
attached, and never fires the outbox insert in a Lobby room whose reservation was forced past due;
a deferred tail announces `PLAYER_LOST` and transfers host to the next connected human; an elapsed
migration window transfers host and clears the column; adoption opens a mass reservation for every
connected player (not spectators), never resets one already running, and skips entirely on a first
claim. `./mvnw verify -Pintegration` green locally (137 tests, merged JaCoCo gate met). **CI green
on `turnbase-platform` `master`** (`build`, 13m9s — `e2e`'s "Check out turnbase-game-host" step
fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT` every prior session's accepted run also
shows).

**Closed:** IMP-GATE-46's second half (`IMP-M2-06`, opened and closed 2026-09-10, session 41) — this
item's *Satisfies* already claimed `FR-HDISC-001…004` in full, but its *Done when* never tested
FR-HDISC-004 (the migration-window sweep) — the same claim-without-a-clause shape as `IMP-GATE-34`.
Fixed: the clause below gains duty 3 explicitly, and `data-model.md` §1's `migration_window_expires_at`
joins the read-list (moved here from `IMP-M2-06`, which never had a mechanism to attach it to).

**Closed:** IMP-GATE-48 (opened and closed 2026-09-10, session 43) — `room.RoomOwnershipService`
(`IMP-M2-03`, `DONE`) explicitly defers `room-lifecycle.md` §1.4 adoption steps 4–5 (opening a grace
reservation for every participant with `connection_count > 0` and no reservation already outstanding,
`COALESCE`-guarded; zeroing their `connection_count`) to "`IMP-M2-07`/`IMP-M2-08`", but neither item's
read-list named §1.4 and neither item's *Done when* tested it — the same claim-without-an-owner shape
as `IMP-GATE-47`. Without it, a mass owner-pod-loss disconnect (FR-DC-006) that this item's own
`reconnection-flow.md` FR-DC-006/007 Satisfies-range covers had no mechanism opening the reservations
it is enforcing: adoption's own comment already says "steps 4–6 and 8 ... need `room_participant`
... infrastructure" — infrastructure this item is the one to build, since it owns §3.1's
individual-disconnect grace-opening statement that step 4/5 is the mass-adoption analogue of.
`IMP-M2-08` ("Reconnect and resync") is about a client's return, not about opening reservations for
participants who were connected when the room's previous owner died — the wrong item for this duty.
Fixed: `IMP-M2-07`'s read-list gains `room-lifecycle.md` §1.4 (adoption, steps 4–5 and 7 only — step 6
stays Game Host dispatch's, M3's; step 8 needs no code, since neither this item nor `IMP-M2-03` emits
a per-player event on adoption); its *Done when* gains the explicit clause below.

**Closed:** IMP-GATE-49 (opened and closed 2026-09-10, session 43) — "the sweep tick runs all four
§5.1 duties" requires duty 1's closure evaluation (§3.3 step 4) and duty 2's closure half, both of
which call `detachSession` (§4) — but §4 is `IMP-M2-09`'s own item ("Room closure and the five detach
paths"), which **depends on `IMP-M2-07`**. Requiring it here is circular as written: `IMP-M2-09`
cannot exist yet to supply it, and this item's own read-list never named §4 either. Same shape as
`IMP-GATE-40`, one milestone over — a foundational shared primitive assigned to the item that needs it
*second*. Unlike `IMP-GATE-40`'s fix (reorder the dependency), `detachSession`'s remaining four callers
(host-leave, game-end, retry-limit-failure, reconciliation) are all `IMP-M2-09`'s or later items' own,
so moving the whole mechanism here would leave `IMP-M2-09` an empty shell. Fixed with the seam already
established for the identical shape of problem in `room.GameSessionStarter`/`PendingGameSessionStarter`
(`START_GAME`'s own downstream dependency on `IMP-M3-05`, which does not exist at `IMP-M2-05`'s build
time either): a new package-private `room.RoomSessionDetacher` interface
(`detach(roomId, sessionId, reason, nextState)`, matching §4's own signature), called by duty 1 after a
won expiry leaves no human and by duty 2 after announcing a deferred tail whose participant was the
room's last human; `room.PendingRoomSessionDetacher` is a no-op default bean, honest because no room
can reach a real `IN_PROGRESS` state with a live session before `IMP-M3-05` lands regardless — the
same reasoning `PendingGameSessionStarter`'s own doc comment already gives. `IMP-M2-09`'s read-list
gains `room-lifecycle.md` §3.3 step 4 and §5.1 duty 2 (to know it is replacing a live seam, not writing
new call sites); its *Done when* gains a clause: replace `PendingRoomSessionDetacher` with a real
`detachSession` implementation wired into the two call sites `IMP-M2-07` already built, rather than
adding its own.

**Read first:**
- `docs/decisions/0009-grace-deadline-durability.md`
- `docs/specs/platform/room-lifecycle.md` §3 **in full** (especially §3.2's resolve statement and
  §3.3's conditional outbox insert), §5.1 **in full** — all four sweep duties, including duty 3
  (elapsed migration windows), are this item's — and §1.4 steps 4–5 and 7 (`IMP-GATE-48`: adoption's
  own mass grace-opening, the `COALESCE`-guarded analogue of §3.1 for every participant left connected
  when the previous owner was lost) — and §4's `detachSession`/`terminateAndCleanup` signature only
  (`IMP-GATE-49`: the seam this item calls into, not the mechanism it builds)
- `docs/requirements/reconnection-flow.md` FR-DC-001…007, FR-GRACE-001…006, FR-EXPIRY-001…006,
  FR-KICK-001…004, FR-HDISC-001…004
- `docs/specs/platform/data-model.md` §1 — `migration_window_expires_at`; §2 — `left_at`,
  `leave_reason`, `lost_announced_at`
- `docs/specs/deployment/local-environment.md` §7.1
- `docs/specs/flows/04-disconnect-and-return.md`

**Satisfies:** `reconnection-flow.md` FR-DC-001…007, FR-GRACE-001…006, FR-EXPIRY-001…006,
FR-KICK-001…004, FR-HDISC-001…004, NFR-CONF-001…003, NFR-PERF-001…003

**Done when:** deadlines are **persisted absolute timestamps, swept** — with no in-process timer. Two
mechanisms enforcing one deadline is a dual write and a three-way race on every reconnect. The
Postgres clock is the single time authority, which removes clock skew by construction.

Grace expiry must not fire in a **Lobby** room; `reconnection-flow.md` FR-DC-007 exists to stop a
rolling deploy deleting every Lobby room, and a Lobby grace expiry re-creates that bug.

**Two details from the IR-06/IR-09 fixes are load-bearing.** §3.3's `game_input_outbox` insert is
conditional on `room.active_session_id IS NOT NULL` — a departure from a Lobby room has no session to
notify, and the unconditional insert wrote outbox rows nothing would ever drain. And §3.2's resolve
statement stamps `lost_announced_at = CASE WHEN :announceInline THEN now() ELSE NULL END`: a NULL
marks a departure that a *foreign* instance resolved and the owner still owes an announcement for.

**The single sweep tick runs all four §5.1 duties, in order, on one schedule.** Duty 3 — elapsed
migration windows (FR-HDISC-004) — clears `migration_window_expires_at` and, if the host is
disconnected or released while another human is connected, performs the FR-HDISC-001 transfer that
§3.1's own opening deliberately skipped while the window was open. `IMP-M2-03`'s adoption `UPDATE`
already persists the deadline (§1.4 step 7); this item is what closes it. Proving duty 3 requires no
mechanism from any other item — the deadline is a plain column already written.

**`IMP-GATE-48`: adoption itself (§1.4 steps 4–5) opens the mass grace reservation.** When a room is
adopted after owner-pod loss, every participant with `connection_count > 0` and no reservation already
outstanding gets a grace period at `now() + graceSeconds`, `COALESCE`-guarded so a reservation already
running from an earlier individual disconnect is never reset; their `connection_count` is zeroed in the
same step, since their connections died with the previous owner (FR-DC-006). This is `§3.1`'s statement
applied to every eligible participant in one pass rather than one row, called from
`RoomOwnershipService#adopt` inside the same fenced transaction that already sets `owner_epoch`, not
from the sweep — the mass disconnect is observed at the moment of adoption, not on the next tick.

**`IMP-GATE-49`: duty 1 and duty 2's closure evaluation go through a `RoomSessionDetacher` seam.**
Duty 1, after a won expiry (§3.3) leaves no `PLAYER` with `left_at IS NULL`, and duty 2, after
announcing a deferred tail whose departed participant was the room's last human, both call
`detacher.detach(roomId, sessionId, reason, "CLOSED")`. `room.PendingRoomSessionDetacher` — the only
bean until `IMP-M2-09` — is a no-op, matching `GameSessionStarter`/`PendingGameSessionStarter`'s
precedent: no room can carry a real `active_session_id` before `IMP-M3-05` either, so a stub here
costs nothing today and the call site is proven to exist and fire under the right condition, which is
what this item's own tests assert.

---

### IMP-M2-08 — Reconnect and resync

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Closed:** IMP-GATE-52 (opened and closed 2026-09-13, session 44, found verifying this item's CI
run, fixed in `local-environment.md` §1 — an `IMP-M0-07`/`M0-08` document — and in
`turnbase-platform`'s compose file, Helm chart and Testcontainers pins, none of which this item
otherwise touches) — `local-environment.md` §1 pins `minio/minio` and `minio/mc` with no registry
host, which every consumer (this repo's `docker-compose.yml`, its Helm chart's `values.yaml`, and
`PostgresIntegrationTest`/`ArtifactBucketReadinessCheckIT`'s Testcontainers pins) resolved as
`docker.io/minio/…` — correct when written, but MinIO stopped publishing to Docker Hub some time
after IR-01/IR-13 were verified, so every one of those pulls now fails
`pull access denied ... repository does not exist`, hard-failing `./mvnw verify -Pintegration` (and,
by the same mechanism, `make e2e` and a fresh `docker compose up`) regardless of which item is being
worked. Confirmed byte-identical on MinIO's current registry before touching anything:
`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z` and `quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z`
both resolve to the exact digests already cached locally under the old, now-dead Docker Hub
reference. Fixed: `local-environment.md` §1's table and its `minio-init` YAML snippet, both
`docker-compose.yml` image lines, both `values.yaml` image lines, and both Testcontainers
`DockerImageName.parse(...)` calls now pin `quay.io/minio/minio`/`quay.io/minio/mc` — same tags, same
digests, new host. Testcontainers' `MinIOContainer` validates the image name against the bare
`minio/minio` repository regardless of host, so both Java pins also add
`.asCompatibleSubstituteFor("minio/minio")` — found only by actually running the fix, not by reading.
No `dependabot.yml` entry named the old host (Docker ecosystem entries key on the bare image name,
`conventions.md` §6), so none needed updating.

**Closed:** IMP-GATE-50 (opened and closed 2026-09-13, session 44) — `data-model.md` §2 states
`room_participant` keeps one row per `(room_id, user_id)` for a user's entire history in a room (never
deleted, `left_at` marks release), but `room-rest-api.md` §5 step 6 said "Insert" unconditionally —
the two cannot both hold the moment a caller re-joins a room they previously departed (voluntary
leave, kick, or grace expiry: exactly this item's own "ordinary join after expiry" clause), since the
row already exists and a plain `INSERT` violates the primary key. Fixed: `data-model.md` §2 and
`room-rest-api.md` §5 step 6 both now specify `INSERT ... ON CONFLICT (room_id, user_id) DO UPDATE`,
reinitializing the row, for exactly the departed-row case.

**Closed:** IMP-GATE-51 (opened and closed 2026-09-13, session 44) — this item's *Satisfies* claimed
`reconnection-flow.md` FR-REJOIN-001…008 in full, but no *Done when* clause tested FR-REJOIN-007 (a
reconnection attempt that loses the race to its own grace expiry must be told plainly, not silently
dropped or failed generically), and no document said which call path emits `room-websocket.md`'s
already-registered `SLOT_RELEASED` error code or under what predicate. Fixed, building on
`IMP-GATE-50`'s row-reuse guarantee: `room-websocket.md`'s Authorization Model now specifies the
predicate (`left_at IS NOT NULL AND leave_reason = 'GRACE_EXPIRED'` on the caller's own
`room_participant` row) and the call site (`SUBSCRIBE` to `/topic/room.{roomId}`, rejecting with
`SLOT_RELEASED` instead of the default silent drop); this item's *Done when* gained the clause below.

**Read first:**
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003
- `docs/specs/api-design/room-websocket.md` — *Snapshot Delivery*, *Client Reconciliation*, *
  Authorization Model* (`IMP-GATE-51`)
- `docs/specs/platform/room-lifecycle.md` §2, §3.2
- `docs/specs/platform/data-model.md` §2 (`IMP-GATE-50`)
- `docs/specs/api-design/room-rest-api.md` §5 step 6 (`IMP-GATE-50`)
- `docs/specs/flows/04-disconnect-and-return.md`

**Satisfies:** `reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003; `game-rooms.md`
FR-JOIN-011

**Done when:** a reconnecting client receives a **snapshot carrying its version**, then deltas from
that version onward — there is no merge path and no partial replay; the server never re-announces a
departure whose `lost_announced_at` is already set; a rejoin inside the grace window restores the
participant's seat and team rather than re-seating them (FR-REJOIN-*, FR-JOIN-011); a rejoin after
expiry is an ordinary join and is subject to every capacity rule; a rejoin that loses the race to its
own grace expiry receives `SLOT_RELEASED` on `SUBSCRIBE` rather than a silent drop (FR-REJOIN-007,
`IMP-GATE-51`).

**Verified.** Code merged to `turnbase-platform master` at `7948aea`, `IMP-GATE-52`'s MinIO re-pin
merged on top at `417ecf9`. `./mvnw verify -Pintegration` green locally, including 4 new
`RoomReconnectIT` methods and 4 new `RoomControllerIT` methods covering every Done-when clause
(snapshot-then-delta, no re-announce of an already-`lost_announced_at` departure, grace-window seat
restoration, post-expiry ordinary join, `IMP-GATE-51`'s `SLOT_RELEASED` race). CI green on
`turnbase-platform master`'s `build` job (run `34749048422`, 18m23s — the two prior runs on `7948aea`
failed only on `IMP-GATE-52`'s pre-fix pull error, not on this item's code). `e2e` failed in the same
run, but past a point it has never reached before: MinIO itself now pulls and starts correctly in the
real compose stack (confirming `IMP-GATE-52` fixes the live stack, not just Testcontainers), and the
job instead died on `lstat /target: no such file or directory` inside the e2e smoke test's own Docker
build context — unrelated to `IMP-M2-08` or `IMP-GATE-52`, and **a different failure than the
`TURNBASE_GAME_HOST_PAT`/checkout error every prior session's accepted run showed**. Not investigated
or gated here (out of this item's scope); next session should expect this new failure mode, not the
old one, when `e2e` is looked at.

---

### IMP-M2-09 — Room closure and the five detach paths

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Closed: IMP-GATE-53** (opened and closed 2026-09-13, session 45) — this item's own *Done when*
required wiring all three of its remaining `detachSession` callers (host-leave with no humans, normal
game end, retry-limit permanent failure) alongside the two `IMP-M2-07` already wired — but two of the
three have no trigger anywhere in this item's dependency closure. Normal game end (FR-LIFE-002) and
retry-limit permanent failure (FR-FAIL-003/005) both originate in the Orchestration Service —
`platform-architecture.md` FR-FAIL-005 states the Orchestration Service itself "notifies the Room
Service" on permanent failure, and flow 06's game-end trigger is the same actor — which is
`IMP-M3-05` (*Orchestration client and session registry*) and its dependents, none of which this item
depends on or which exist yet: `grep` across `src/main/java` for any game-end or retry-limit call site
turned up nothing, matching `PendingGameSessionStarter`'s own note that no room can carry a real
`active_session_id` before `IMP-M3-05` lands. Unsatisfiable as written — same shape as
`IMP-GATE-08`/`18`/`28`/`46`. Fixed: this item's *Done when* narrows to the mechanism plus the one
caller actually reachable now — host-leave with no humans, wired into `RoomService#leave`'s
already-claimed branch (the REST/voluntary path; the two non-owning arrivals, account deletion and
guest cleanup, already flow through `IMP-M2-07`'s existing deferred-tail duty 2 once the real detacher
lands, per `room-lifecycle.md` §4's own text, and need no new call site here). The other two callers
move to their natural owners: `IMP-M3-08` (*Session teardown as a durable to-do*, already reading
`room-lifecycle.md` §4 and `flows/06-game-end-and-rematch.md`) gains the normal-game-end wiring clause
and `IMP-M2-09` in *Depends on*; `IMP-M3-09` (*Game failure handling*) gains the retry-limit-failure
wiring clause, `room-lifecycle.md` §4 and `flows/07-room-closure.md` in its read-list, and `IMP-M2-09`
in *Depends on*. Both already claim the relevant requirement IDs (`FR-XFER-005` and `FR-FAIL-003/005`
respectively) in their existing *Satisfies*, so neither gains a new claim, only a Done-when clause
naming the call site.

**Closed:** IMP-GATE-46's third half (`IMP-M2-06`, opened and closed 2026-09-10, session 41) — this
item's *Satisfies* named `FR-XFER-003`, which `IMP-GATE-39` already assigned to `IMP-M2-01` in full
(the REST-layer `state <> 'CLOSED'` listing/lookup predicate) — a second, independent double-claim on
the same requirement, found while resolving `IMP-M2-06`'s own overlapping claims. Fixed: narrowed
below to the two requirements this item actually builds.

**Closed:** IMP-GATE-49's other half (`IMP-M2-07`, opened and closed 2026-09-10, session 43) —
`IMP-M2-07`'s own Done-when needed `detachSession` for its sweep's closure evaluation before this item
(`detachSession`'s owner) could exist, since this item depends on `IMP-M2-07`. Fixed there with a
`RoomSessionDetacher` seam (`GameSessionStarter`/`PendingGameSessionStarter`'s precedent); this item's
own read-list gains `room-lifecycle.md` §3.3 step 4 and §5.1 duty 2, and its *Done when* gains the
clause below the SQL block: replace the seam, wired into the two call sites already built, rather than
adding new ones.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §4 **in full** — the five paths and the fenced step 3 — and
  §3.3 step 4, §5.1 duty 2 (`IMP-GATE-49`: the two call sites this item's real implementation replaces
  a stub at, not writes fresh)
- `docs/specs/flows/07-room-closure.md`
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §1 (`closed_at`, `closed_reason`), §4
- `docs/requirements/notifications-invitations.md` FR-INV-008

**Satisfies:** `game-rooms.md` FR-LIFE-007, FR-XFER-002, FR-XFER-005;
`notifications-invitations.md` FR-INV-008

**Done when:** `detachSession` step 3 is a single fenced, version-bumping `UPDATE`:

```sql
UPDATE room
   SET state = :nextState, active_session_id = NULL,
       version = :expected + 1,
       closed_at    = CASE WHEN :nextState = 'CLOSED' THEN now() END,
       closed_reason = CASE WHEN :nextState = 'CLOSED' THEN :reason END
 WHERE room_id = :roomId AND version = :expected AND owner_epoch = :myEpoch;
```

Without the `owner_epoch` fence a stale owner closes a live room. Without the version bump every
client discards the resulting `ROOM_CLOSED` as stale, and the room is closed on the server and open
on every screen.

`notifications-invitations.md` FR-INV-008's deletion of invitations happens **at closure**, not by
the FK cascade that fires seven days later at purge.

**Step 0 defers rather than closing eagerly.** A closure this instance does not own is left as
`lost_announced_at IS NULL` for §5.1 duty 2 to discharge — the same deferred tail an account erasure
uses (IMP-M1-08).

**`IMP-GATE-49`: this item's real `detachSession` replaces `room.PendingRoomSessionDetacher`.**
`IMP-M2-07`'s sweep duty 1 (§3.3 step 4) and duty 2 (closure half) already call
`RoomSessionDetacher#detach` at the moment each condition is met; this item swaps the no-op bean for
one implementing the transaction above and adds nothing at `IMP-M2-07`'s two call sites.

**`IMP-GATE-53` narrowed this item's own third caller to host-leave with no humans** (FR-XFER-002),
wired into `RoomService#leave`'s already-claimed branch: when the departing user is the room's host
and no other human participant remains (`left_at IS NULL AND role = 'PLAYER'`, the same predicate
§3.3 step 4 uses), close immediately with `NO_PLAYERS_REMAINING` instead of an ordinary
`PLAYER_LEFT`. The unclaimed branch is unchanged — it already commits the departure with
`lost_announced_at` left null and returns, exactly `room-lifecycle.md` §4's "a caller that cannot
claim defers through the existing deferred-tail mechanism" — no new closure logic belongs there; the
owning instance's duty 2 evaluates closure (including the host disposition) on its next tick, using
this item's real detacher. Normal game end and retry-limit permanent failure are `IMP-M3-08` and
`IMP-M3-09`'s own callers respectively (`IMP-GATE-53`).

---

### IMP-M2-10 — Adoption and reconciliation jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Done 2026-09-13 (session 49).** `ReconciliationJob` (`@SchedulerLock`, 60s) runs all five FR-JOB-007
duties in the specified order, `FOR UPDATE SKIP LOCKED`, each idempotent and exposing FR-JOB-011's
per-duty candidate/repair/skip counts: (a) owed teardowns re-driven via `SessionTerminatorImpl` →
`RoomRepository.recordSessionTeardownFailure` (10s-doubling-to-5min backoff), which also resolves the
session 48 open question about `SessionTerminator` being `void` — there is still no Game Host gRPC
client, so every call honestly takes the failure branch and records it, rather than silently
succeeding; (b) orphaned Redis session-key families (age > 10 min) deleted, two-strike via the new
`orphaned_session_flag` table (`IMP-GATE-56`); (c) In-Progress-no-session fails back to Lobby via
`GAME_ENDED (readinessReset: true)`, never closes (`IMP-GATE-55`); (d) idle Lobby rooms close
`IDLE_TIMEOUT`; (e) unowned-room adoption via `RoomOwnershipService.claim()`, exempt from both
FR-JOB-008 guards. Duties (c)/(d) share `room.reconcile_flagged_at`; startup suppression (120s
default) gates (b)/(c)/(d) only, matching `flows/05-owner-loss-and-adoption.md` §D. `RoomPurgeJob`
(FR-JOB-009, daily) purges Closed rooms past retention, cascading participant/team/invite rows.
`ReconciliationMetrics` exposes `turnbase.reconcile.candidates{duty}`,
`turnbase.reconcile.repairs.total{duty,result}`, `turnbase.rooms.in_progress_without_session`,
`turnbase.teardown.owed` and `turnbase.job.aborted.total{job,reason}`. `PodIdentity` gained
`bootAt()` for the suppression guard. Migration `V202609131400__add_orphaned_session_flag.sql`,
`FlywayBaselineIT` updated. `./mvnw verify` and `./mvnw verify -Pintegration` both green locally;
**CI green on `master`** at `852d415`. Landed directly on `master` (branch
`feat/imp-m2-10-reconciliation`, ff-merged and deleted same session as ADR-0012 requires) —
found already merged into the submodule when this session picked the item back up, with only the
parent repo's submodule ref and this registry/STATUS.md bookkeeping left outstanding; both are
caught up now.

**Closed:** IMP-GATE-56 (opened and closed 2026-09-13, session 48) — `room-lifecycle.md` §5.4's
two-strike guard (FR-JOB-008b) names exactly one persistence mechanism, `room.reconcile_flagged_at`,
and states that duties (b)/(c)/(d) all take the guard. But `room.reconcile_flagged_at` lives on the
`room` row, while duty (b)'s candidates are session IDs recovered from a Redis key family, qualified
as orphaned precisely when "the room no longer exists **or** is closed" (`room-lifecycle.md` §5.2) —
the "no longer exists" branch has no room row to stamp a flag on, and even the "closed" branch has no
stable one-to-one room since a room's `active_session_id` is cleared at the same detach that makes the
session's artifacts orphan candidates. No document supplied a persistence mechanism duty (b) could
actually use. Fixed: new `data-model.md` §4.3, `orphaned_session_flag` — a session-scoped table with
the same insert/consult/clear lifecycle as `room.reconcile_flagged_at`, holding no foreign key to
`room` or `session_teardown` since the absence of both is exactly the case it exists to cover;
`room-lifecycle.md` §5.4 guard 2 now names it explicitly for duty (b) and scopes
`room.reconcile_flagged_at` to duties (c)/(d) alone, which is what the surrounding prose already
assumed.

**Closed:** IMP-GATE-55 (opened and closed 2026-09-13, session 47) — `game-rooms.md` FR-LIFE-007 and
`room-websocket.md`'s `ROOM_CLOSED` reason table said an In-Progress room whose session state is gone
is **closed** with `SESSION_UNRECOVERABLE`; `platform-operations.md` FR-JOB-007(c) and
`room-lifecycle.md` §5.2 (this item's own read-list) say it **fails back to Lobby, not closed**
instead — a flat disagreement on first reading. That reading turned out to be incomplete:
`flows/07-room-closure.md` § Caller 5 — a document this item's read-list never named, though it is the
one place all five `detachSession` callers are enumerated together — already reconciles the two sides
with "fail back to Lobby; `SESSION_UNRECOVERABLE` only if that also fails." That reconciliation is
itself hollow: `detachSession`'s shared skeleton (same document)
has exactly two non-success outcomes for any caller — a claim redirect, deferred to the next tick, and
step 2's idempotent no-op when another caller already detached — and neither is a "failure" this duty
could close on. No document, including flow 07, names a third outcome. `SESSION_UNRECOVERABLE` has no
producer under the mechanism as specified anywhere in the corpus. Fixed: `room-lifecycle.md` §5.2's
duty (c) row and prose state explicitly that this duty has no closure branch, citing the skeleton's two
non-success outcomes; `flows/07-room-closure.md`'s Caller 5 table and prose drop the
"`SESSION_UNRECOVERABLE` only if that also fails" hedge; `game-rooms.md` FR-LIFE-007 narrows to the
idle-Lobby-closure case alone, stating the unrecoverable-session case fails back to Lobby instead;
`room-websocket.md`'s `ROOM_CLOSED` reason table and `data-model.md`'s closure-reasons table both drop
`SESSION_UNRECOVERABLE` (five closure paths become four). Separately, duty (c)'s "notify participants"
cited `platform-architecture.md` FR-FAIL-005, which names no wire event, but the behaviour it
describes — room back in Lobby, readiness reset — is verbatim `room-websocket.md`'s existing
`GAME_ENDED` contract; that section and flow 07 both gain FR-JOB-007c as `GAME_ENDED`'s second trigger,
same payload shape, rather than a new event type. This item's read-list gains
`flows/07-room-closure.md` § Caller 5 (below) so the next reader of duty (c) has the full mechanism in
one place rather than reconstructing it from `room-lifecycle.md` alone. This item's *Done when* clause
already said "fails back to Lobby, not closed, with no history entry," so it is unchanged by the fix
except to name the event to publish, which was genuinely undetermined before this gate closed.

**Closed:** IMP-GATE-54 (opened and closed 2026-09-13, session 46) — this item's *Done when* required
"the three reconciliation duties," but `platform-operations.md` FR-JOB-007 has always defined **five**
lettered duties (a–e: owed-teardown re-drive, orphaned-artifact deletion, In-Progress-no-session
fail-back, idle-Lobby closure, unowned-room adoption), matching `room-lifecycle.md` §5.2's five-row
table exactly — no reading of either document yields three. Separately, this item's *Satisfies*
claimed the full `FR-JOB-001…013` range verbatim, identical to `IMP-M5-04`'s claim of the same full
range, even though `FR-JOB-001` (guest cleanup) is already built and unclaimed by `IMP-M1-05`,
`FR-JOB-006` (deadline sweep) is already built and unclaimed by `IMP-M2-07`, and `FR-JOB-012` (upload
slot sweep) belongs to `IMP-M4-03`'s manifest/upload domain, which this item's read-list never touches
— same shape as `IMP-GATE-08`/`18`/`28`/`30`/`46`. Fixed: the *Done when* clause below enumerates all
five duties; *Satisfies* narrows to `FR-JOB-007…011` (reconciliation, its safety guards, the room
purge `room-lifecycle.md` §5.3 also assigns here, repair idempotency, and reconciliation
observability — a contiguous, verifiable range) plus `NFR-JOB-002` (the adoption recoverability
bound; `NFR-JOB-001` is FR-JOB-006's bound, `IMP-M2-07`'s already-shipped concern); read-list corrected
to name the real duty count and add §6 for FR-JOB-011's metric names. `IMP-M5-04`'s matching over-claim
is narrowed in its own section below. `FR-JOB-001`/`006` staying unclaimed by their actual builders
(`IMP-M1-05`/`IMP-M2-07`, both `DONE`) is a pre-existing gap, not reopened here — noted in `STATUS.md`
instead of touching finished items' sections.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §5 **in full** — §5.1 (already built by `IMP-M2-07`; read
  for context, not to rebuild) plus this item's own §5.2 (the five reconciliation duties), §5.3
  (closed-room purge) and §5.4 (safety preconditions) — and §6 (metric names for FR-JOB-011)
- `docs/requirements/platform-operations.md` FR-JOB-007…011, NFR-JOB-002
- `docs/decisions/0008-room-ownership-lifecycle.md`
- `docs/specs/deployment/local-environment.md` §7.2
- `docs/specs/flows/05-owner-loss-and-adoption.md`
- `docs/specs/flows/07-room-closure.md` § Caller 5 — duty (c)/(d)'s shared `detachSession` mechanism,
  and why duty (c) has no closure branch (`IMP-GATE-55`)
- `docs/specs/game-host/game-host-internals.md` §13 — duty (b)'s six session-key-family names
  (`session:`/`routing:`/`queue:`/`seq:`/`delivered:`/`failcount:{sessionId}`) and their shared
  24h-refreshed-on-write TTL, the only place either is stated; not previously in this item's read-list
  despite `room-lifecycle.md`'s own Scope section naming this document as out of scope for *game
  execution*, which the key inventory is not.

**Satisfies:** `platform-operations.md` FR-JOB-007…011, NFR-JOB-002

**Done when:** all **five** FR-JOB-007 reconciliation duties run, `FOR UPDATE SKIP LOCKED`, each
idempotent (FR-JOB-010 — a repair whose guard no longer holds is a no-op) and each exposing
FR-JOB-011's per-duty candidate/repair/skip counts: (a) owed teardowns are re-driven via
`terminateAndCleanup`; (b) orphaned Redis session-key families older than 10 minutes are deleted; (c)
an In-Progress room with no session **fails back to Lobby, not closed**, with no history entry,
broadcasting `GAME_ENDED` (`readinessReset: true`) as its FR-JOB-007c trigger (`IMP-GATE-55`); (d)
an idle Lobby room (zero connected participants, past the idle window) closes `IDLE_TIMEOUT`; (e) an
unowned room is claimed and adopted. The adopt duty (e) alone is exempt from both FR-JOB-008 guards
(120 s startup suppression, two-consecutive-runs), which would otherwise block adoption for 120 s
after every restart. The closed-room purge (FR-JOB-009, §5.3) deletes rooms Closed past the retention
window, cascading to participant, team and invite rows — **orphaned participant rows are handled by
this cascade, not by a duty of their own**, distinct from duty (b)'s orphaned Redis *artifacts*, which
is a real duty.

**Duty 2 is the deferred tail.** It announces departures whose `lost_announced_at` is NULL and then
evaluates closure, and it is the mechanism three other items rely on (M1-08, M2-07, M2-09). Its
`leave_reason` filter is a backstop, not the primary control — the primary control is that every
inline path stamps `lost_announced_at` itself (IR-09).

The per-duty reconciliation counters these jobs increment fire the `ReconciliationRepairsPersist`
alert (`observability.md` §6 sketches the rule; `platform-operations.md` FR-ALERT-006 defines it,
deferred here by `IMP-M0-10`) — repairs applied on more than 3 consecutive runs, or a room
detected-but-unrepaired for more than 10 minutes.

---

### IMP-M2-11 — In-room chat

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

**Done 2026-09-10 (session 42).** New `chat` feature package (ADR-0014's own listing, kept separate
from `room` despite sharing its `room.*` wire prefix). `ChatController`'s `SEND_CHAT_MESSAGE` on
`/app/room.{roomId}.chat` resolves the sender's role/team through a new public `room.RoomChatPort` —
a deliberate cross-feature API (ADR-0014 §3) rather than reaching into `room`'s package-private
`RoomRepository`/`RoomEventExecutor`. `resolveSenderForSend` runs under a new `RoomEventExecutor
.withLock` (lock + fresh ownership check, no transaction, no version bump, no publish — `execute`'s
CAS/publish machinery is specific to the bare room topic), giving the "team assignment re-validated
under the room lock" requirement real mutual exclusion against a racing `REASSIGN_PLAYER` and a
monotonic `serverTimestamp`. `ChatSubscriptionAuthorizer` governs the `.chat`/`.team.{teamId}`
sub-topics `room.RoomSubscriptionAuthorizer` always excluded, using the lighter unlocked
`currentMembership` read (mirroring `room`'s own bare-topic check) since the doc's Authorization table
names only silent-drop, never `ROOM_UNAVAILABLE_RETRY`, for chat subscriptions. Text is canonicalized
via the existing `common.Canonicalizer` (NFC, forbidden-code-point rejection doubling as chat's "no
control characters at all") before the 1–500-code-point check.

**Closed:** IMP-GATE-47 (opened and closed 2026-09-10, session 42) — `input-validation.md`'s Size
limits table assigns the whole per-destination STOMP frame-size ceiling (8 KB
`/app/room.*.member`/`.host`, 4 KB `/app/room.*.chat`, 256 KB `/app/game.*.action`, 1 KB
`/app/game.*.sync`) to "the same `ChannelInterceptor` as the Tier 6 rate limits," but no work item's
read-list or Done-when ever required building it — `IMP-M2-02` built that exact interceptor
(`WebSocketChannelInterceptor`, `DONE`) without `input-validation.md` in its read-list, so it shipped
Tier 6 bucket classification alone; `IMP-M2-05`/`M2-06` (also `DONE`) never named the document either.
A registry omission, not a wording conflict between two specs. Fixed: this item builds the guard —
see the size-limit Done-when clause below and the deferral note added to `IMP-M2-02`'s section above.
The guard is generic (destination → byte ceiling, mirroring Tier 6's own `classify()`), so it covers
`IMP-M2-05`/`M2-06`'s already-shipped member/host destinations with no code change to either, and
pre-registers the two game rows for `IMP-M3-01`/`M3-06` to inherit rather than re-decide.

**Read first:**
- `docs/requirements/in-room-chat.md` in full
- `docs/specs/api-design/room-chat-websocket.md` in full
- `docs/specs/api-design/input-validation.md` § *Output encoding*, § *Size limits*
- `docs/specs/api-design/rate-limiting.md` Tier 6

**Satisfies:** `in-room-chat.md` FR-MSG-001…006, FR-CHAN-001…004, FR-TEAM-001…004,
FR-SWITCH-001…002, NFR-SEC-001…003, NFR-PERF-001; `game-rooms.md` FR-TEAM-011

**Done when:** chat frames carry `version: null` and **never advance the room version counter**
(IR-08); the channel a message lands on is derived from the sender's current team **server-side**,
never read from the frame; a message missed while disconnected is **lost, not gapped** (FR-MSG-006) —
there is no chat history, no catch-up and no second sequence number; bodies are escaped at render and
no HTML string is ever constructed; a spectator's send is rejected `SPECTATOR_CANNOT_CHAT`, an empty
or oversized `text` is rejected `MESSAGE_EMPTY`/`MESSAGE_TOO_LONG` at the 500-code-point limit
measured after NFC, a `TEAM` send with no team assignment is `NO_TEAM_ASSIGNMENT`, and one against a
game with no team support is `TEAM_CHAT_NOT_AVAILABLE` (FR-MSG-002, NFR-SEC-001…003); `authorId`/
`authorUsername` are resolved server-side from the authenticated principal, never from the frame
(NFR-SEC-002); `WebSocketChannelInterceptor` gains a generic per-destination frame-size guard —
`/app/room.*.chat` at 4 KB, `/app/room.*.member`/`.host` at 8 KB, `/app/game.*.action` at 256 KB,
`/app/game.*.sync` at 1 KB — checked from the raw frame's byte length before Tier 6 consumption
(`input-validation.md`'s pipeline: Size precedes Authorize), rejecting with `MESSAGE_TOO_LARGE`
(`ACTION_TOO_LARGE` for the action row, per the table) on `/user/queue/errors`, interceptor-dropped so
it carries no `correlationId`.

**Verified end to end on real STOMP clients** (`ChatControllerIT`): room-channel broadcast reaches
every player, excludes a subscribed spectator entirely (silent drop, no error), and leaves
`room.version` unchanged across the send; every documented validation/business error code fires from
the right sender; a team message reaches only players sharing that team and nothing arrives on the
off-team topic; a game with no team templates rejects `TEAM_CHAT_NOT_AVAILABLE`; a 6 KB frame is
rejected `MESSAGE_TOO_LARGE` with no `correlationId` key, at the interceptor, before the 500-code-point
business check ever runs. `./mvnw verify -Pintegration` green locally (116 tests plus this item's 4,
coverage checks met). **CI green on `turnbase-platform` `master`.**

**Giving chat a version number is the tempting mistake.** Two writers on one counter means a client
that filters chat sees a permanent gap in the room stream and resyncs forever.

---

### IMP-M2-12 — Room invitations

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M1-09

**Closed:** IMP-GATE-57 (opened and closed 2026-09-13, session 50) — superseded by `IMP-GATE-58`
below, whose own fix removes the clause this one corrected: the invite-*link* Done-when clause turned
out not to belong to this item at all. Kept for the record — the correction it made
(`room-rest-api.md` §3.1's no-way-in case returns a room resource, not "not found") is still true, it
now just lives entirely in `IMP-M2-01`'s own section instead.

**Closed:** IMP-GATE-58 (opened and closed 2026-09-13, session 50) — three findings from reading this
item's own read-list before writing code, all the same root cause: the item was scoped before
`IMP-M2-01`/`IMP-M2-05` existed and was never revisited once they shipped.

1. **Double-claim, `game-rooms.md`.** `FR-HOST-002`, `FR-JOIN-003…004`, `NFR-SEC-002` are `IMP-M2-01`'s
   (its own *Satisfies*, `IMP-GATE-39`) — the invite **link** (mint, host-only exposure, `GET
   /api/rooms?inviteCode=…` resolution) is fully built and shipped there, verified by reading
   `RoomController`/`RoomService`/`RoomRepository` directly rather than assuming. `FR-JOIN-006` and
   `FR-JOIN-008` are `IMP-M2-05`'s (its own *Satisfies*), also shipped. Same shape as
   `IMP-GATE-08`/`18`/`28`/`30`/`32`/`34`. This item built none of the five and should never have
   claimed them.
2. **Double-claim, `FR-LINK-001…002`.** Claimed by *both* this item and `IMP-M5-03`, and neither
   builds anything for it — it describes exactly the invite-link mechanism `IMP-M2-01` already ships
   (`data-model-notifications.md` §2: "**this is not the invite link** ... the shareable join link is
   `room.invite_code`... unrelated objects"). Reassigned to `IMP-M2-01`, whose section gains it.
3. **No document defined this item's actual REST surface** — same shape as `IMP-GATE-31`/`33`/`35`/`37`.
   `room-rest-api.md` §8 explicitly defers FR-HOST-001's notification invites elsewhere ("belong to
   `notifications-invitations.md`, not here"), but that document is requirements prose with no
   endpoints, and nothing else supplied them. Also undefined: whether "accept" is its own endpoint or
   resolves through the existing join call, and what happens to a pending invitation when that join
   *fails* (FR-INV-005) — `data-model-notifications.md` §2 says accepting deletes the row but not at
   what moment. Fixed: new
   [`docs/specs/api-design/room-invitation-rest-api.md`](../specs/api-design/room-invitation-rest-api.md)
   — `POST /api/rooms/{roomId}/invitations` (send) and `DELETE …/invitations/me` (decline); acceptance
   is `room-rest-api.md` §5's existing join endpoint, which gains one clause (step 7): a *successful*
   join deletes the caller's pending invitation to that room and alerts its inviter; a *failed* join
   leaves it untouched, so a rejected join doesn't cost the player their invitation. `rest-conventions.md`'s
   Authorization table gains both predicates; `room-rest-api.md` §8's cross-reference and Related table
   updated to point at the new document instead of the requirements doc.

This item's *Satisfies* narrows to what it actually builds: `notifications-invitations.md`
FR-INV-001…009 and `game-rooms.md` FR-HOST-001. `IMP-M2-01`'s *Satisfies* gains `FR-LINK-001…002`;
`IMP-M5-03`'s drops them.

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-INV-001…009 (FR-LINK-001…002 is `IMP-M2-01`'s
  now — read there if the invite-link mechanism itself is in question, not here)
- `docs/specs/platform/data-model-notifications.md` §1 (`notification`), §2 (`room_invitation`)
- `docs/specs/api-design/room-invitation-rest-api.md` **in full** — the two endpoints this item builds
  and the join-endpoint clause it adds to `IMP-M2-01`'s shipped code
- `docs/specs/api-design/sse-notifications.md` § *Notification types*, § *Alert types* — the
  `ROOM_INVITATION` notification and `INVITATION_ACCEPTED`/`INVITATION_DECLINED` alert payload shapes
  this item writes/publishes
- `docs/requirements/game-rooms.md` FR-HOST-001

**Satisfies:** `notifications-invitations.md` FR-INV-001…009; `game-rooms.md` FR-HOST-001

**Done when:** `POST /api/rooms/{roomId}/invitations` is host-only, friends-only (FR-INV-002, a direct
`friendship` check matching `RoomRepository#isVisible`'s existing precedent), and writes a
`ROOM_INVITATION` notification
(`room-invitation-rest-api.md` §2); `DELETE …/invitations/me` deletes the caller's own pending row
idempotently and alerts the inviter only when a row actually existed (§3); a successful join at
`IMP-M2-01`'s join endpoint deletes the caller's pending invitation to that room and alerts its
inviter, while a failed join leaves it pending (§4); invitations are removed **at closure** by
`IMP-M2-09`'s `detachSession`, not by this item and not by the purge cascade (FR-INV-008); no alert
delivery mechanism exists yet (`IMP-M5-03` is not a dependency and is not `DONE`) — this item defines
an `AlertPublisher`-shaped seam with a no-op implementation for now, matching the
`SessionTerminator`/`PendingSessionTerminator` precedent (`IMP-M2-09`), swapped for a real one when
`IMP-M5-03` lands.

---

## M3 — Game execution

**Read first for the whole milestone:** `docs/specs/game-host/game-host-internals.md`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md`, `gamehost.proto`,
`docs/specs/gdk-api/backend-gdk-api.md`, `docs/requirements/game-contracts.md`,
`docs/decisions/0005`, `docs/decisions/0006`, and flows `03` and `06`.

### IMP-M3-01 — GDK backend API surface

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M0-02

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` **in full** — §3 lifecycle, §4 contexts, §5 data model,
  §6 effects, §7 results, §8 outcome, §9 determinism, §11 the worked example
- `docs/requirements/game-development-experience.md` FR-GDK-001…016, NFR-COMPAT-001, NFR-DX-001…002
- `docs/requirements/game-contracts.md` — the behavioural contract the types encode
- `docs/decisions/0006-game-trust-model-java-official-only.md`

**Satisfies:** `game-development-experience.md` FR-GDK-001…016, NFR-COMPAT-001, NFR-DX-001…002;
`game-contracts.md` FR-STATE-001…005, FR-IN-001…006, FR-EFF-001…007, FR-RESP-001…005,
FR-OUTCOME-001…004, FR-PROC-001…003, FR-LOG-001…005

**Done when:** every type in §§3–8 exists with the stated signature and carries Javadoc; the artifact
compiles to Java 21 bytecode and references no Java 22+ API — **it runs inside Espresso, where a
Java 22 API is a runtime failure in a sandbox, not a compile error**; §9's determinism contract is
stated in Javadoc on the interface itself, not only in the spec, because that is the only place a
game developer reads it.

---

### IMP-M3-02 — Espresso context lifecycle

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M0-04

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §§1–2, §4 (isolation: requirement → mechanism),
  §6 (context, session and instance model), §7 (game code loading and guest classpath), §11
- `docs/decisions/0005-game-sandbox-espresso-spike.md`
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`
- `docs/requirements/platform-architecture.md` FR-CTX-001…012, FR-LOAD-001…005
- `docs/specs/deployment/local-environment.md` §7.8 (Game Host config), §7.9 (artifact-store
  endpoint/bucket keys, shared with the monolith) — added: the artifact-fetch half of §7 needs the
  same `turnbase.artifact-store.*` keys the monolith already binds, and §7.8 alone does not carry them.

**Satisfies:** `platform-architecture.md` FR-CTX-001…012, FR-LOAD-001…005

**Done when:** every isolation requirement in §4's table maps to a concrete Truffle/Espresso mechanism
that a test exercises — the table is a checklist, and an unexercised row is an assumption; a context
is created and disposed per §6's model with no leak across sessions; the guest classpath built per §7
contains the game JAR and the SDK and nothing else.

**Scope note (session 68/69):** FR-CTX-004/005/007 (no filesystem, no network, per-context memory cap)
are container-owned per §4.1's own framing — no deployment-manifest work item yet exists to provision
a container, so they are not exercised here; that is a gap in a later item, not in this one.
FR-CTX-009/010 (idle and memory-pressure eviction) are host-owned and implemented in
`GameContextManager`. FR-CTX-012 (polyglot extensibility) is "design" status per §4's table and needed
no code. "The SDK" on the guest classpath is the configured `sdkJarPath` placeholder — the real guest
bridge jar carrying the GDK API classes is IMP-M3-03's deliverable (§3.2).

---

### IMP-M3-03 — GDK host bridge and serialization boundary

**Repo:** `turnbase-sdk` (the serialization component), then `turnbase-game-host` (the guest bridge
and host shim) — two branches, in that order, per `conventions.md` §5 · **Depends on:** IMP-M3-01,
IMP-M3-02

**Closed:** IMP-GATE-69 (opened and closed 2026-09-26) — `game-host-internals.md` §3.2/§5 call the
serialization engine "one module reused by" the guest bridge, the harness and the upload validator,
and no document said which repository builds it or where the guest bridge jar itself is built; the
item's *Repo* named only `turnbase-game-host`, which the harness (`turnbase-sdk`) cannot depend on.
`IMP-M4-03` had already hardcoded the capability table for want of an artifact to read it from. Fixed:
new `game-host-internals.md` §3.6 — `io.turnbase:turnbase-serialization` is built by `turnbase-sdk`;
the guest bridge JAR is a second, shaded and unrelocated artifact of `turnbase-game-host`;
`conventions.md` §5 names the new artifact.

**Closed:** IMP-GATE-70 (opened and closed 2026-09-26) — the item's *Done when* needs `turnbase-game-host`
to depend on `turnbase-sdk` and `turnbase-serialization` and its pipeline to go green, but `conventions.md`
§5's bootstrap window covered `turnbase-common` alone: `turnbase-sdk` is private and untagged, so its
artifacts are nowhere for the Game Host's CI to fetch, and `TURNBASE_COMMON_PAT` cannot read it. Fixed:
`conventions.md` §5 extends the window to `turnbase-sdk` — one root `./mvnw install` installs both
artifacts, a second bootstrap step, a new human-provisioned `TURNBASE_SDK_PAT` secret on
`turnbase-game-host`. **The secret is a human action and does not yet exist**: do the `turnbase-sdk` half
first and merge it, verify the game-host half locally, and merge that half only once the secret is
present (`gh secret list -R turnbase-platform/turnbase-game-host` shows it).

**Closed:** IMP-GATE-79 (opened and closed 2026-09-27) — §3.3's guest-boundary call interface listed
`createSession(sessionId, teamsJson, parametersJson)` with no way to tell the guest bridge which
`TurnBaseGame` implementation to classload, and §6.1/§7.2 assigned entry-class loading to the bridge
without saying how the FQCN crosses the boundary; `CreateSessionRequest` carried no such field either.
Unsatisfiable as written — a `createSession` call with no entry point cannot instantiate a game. Fixed:
`gamehost.proto`'s `CreateSessionRequest` gains `entry_point_fqcn` (field 5), resolved by Orchestration
from the manifest's `backend.entryPoint` the same way it already resolves `parameters`
(`orchestration-gamehost-protocol.md` new "Entry-point resolution" §); `game-host-internals.md` §3.3's
table, §6.1 and §7.2 updated to match. `turnbase-common`'s committed proto copy synced and pushed
(`c04f932`), CI green.

**Session 86 progress:** the `turnbase-sdk` half is done and merged (`6d05ac4`) — `turnbase-sdk` is
now a two-module reactor (`gdk-api/`, unchanged; new `serialization/`), publishing
`io.turnbase:turnbase-serialization` (`GdkSerialization`'s write/read round trip with
NFR-SIZE-001/002 limits, `GdkObjectMapper`, and the `BindingCapabilities` Jackson-free descriptor
`bundle-format.md` §4.4 will eventually read, per `IMP-M4-03`'s recorded follow-up). CI green on
`master`.

**Session 87 progress:** the `turnbase-game-host` half is built, tested and committed on local branch
`feat/imp-m3-03-guest-bridge-and-host-shim` (`6b0adca`) — `io.turnbase.gamehost.bridge` (six §3.3
entrypoint methods, `GameEntrypoint`, `PlatformJson`, `GameParametersImpl`, the `*ContextImpl`
classes, `CodeLoadException`) plus `io.turnbase.gamehost.shim.GameBridgeClient`, driven end to end
through a real Espresso context by `GameBridgeClientEspressoTest` (5/5 green) — the authoritative
proof that the host shim sees only strings, primitives and byte arrays. `pom.xml`'s `maven-shade-plugin`
execution is bound to the `package` phase and declared before `spring-boot-maven-plugin` so
`default-jar` and then shading both complete before Spring Boot's `repackage` runs, producing the
`guest-bridge`-classifier artifact (`io.turnbase.gdk.*` + `turnbase-serialization` + Jackson,
unrelocated) alongside the app jar. The Dockerfile now stages both jars and sorts the `guest-bridge`
one to `/opt/turnbase/guest-bridge.jar` — `turnbase.gamehost.sdk-jar-path`'s default — which the
original glob fix would have silently discarded; verified by `docker build` + `docker run` showing
both artifacts at their correct paths with correct ownership. Because Espresso's guest-side class
loading is invisible to JaCoCo's host-JVM agent, `GameEntrypointTest`, `PlatformJsonTest` and
`GameParametersImplTest` exercise the same bridge classes directly on the host JVM so the merged
coverage floor is measurable; `./mvnw verify` (52 tests) and `./mvnw verify -Pintegration` (54 tests)
are both green locally. `build.yml` gained the `turnbase-sdk` bootstrap step `IMP-GATE-70` specifies.
`TURNBASE_SDK_PAT` was provisioned on `turnbase-platform/turnbase-game-host` this same session
(confirmed via `gh secret list`), clearing `IMP-GATE-70`'s human-action blocker. Merged
`feat/imp-m3-03-guest-bridge-and-host-shim` `--ff-only` into `master` and pushed (`6b0adca`); branch
deleted both locally and on the remote. The triggered CI run failed once on `Trivy scan — image
(report)` with "no space left on device" during the image export — a runner disk-space exhaustion
from the two bootstrap Maven installs plus this module's own image, not a code or vulnerability
defect. Fixed in two follow-up commits, both merged `--ff-only` directly to `master` to keep it green:
`7a3f1fb` deletes each bootstrap clone (`turnbase-common`, `turnbase-sdk`) right after installing it
to `~/.m2`; `24e3398` additionally frees disk by removing `ubuntu-latest`'s unused preinstalled
toolchains (`.NET`, Android SDK, GHC, CodeQL) before the image build. CI green on `master` at
`24e3398` (run `36342814547`, confirmed via `gh run watch --exit-status`), including the GHCR image
push. Submodule ref bumped in this repo to match. **`IMP-M3-03` is `DONE`.**

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §3 (the guest bridge and host shim — **including §3.6,
  where each half is built**), §5 (the serialization engine), §8 (state representation)
- `docs/specs/gdk-api/backend-gdk-api.md` §10 (relationship to the gRPC contract)
- `docs/requirements/game-contracts.md` NFR-SEC-001…004, NFR-SIZE-001…002
- `docs/specs/manifest/bundle-format.md` §4.4 (the capability-descriptor consumer, for the exact
  shape `BindingCapabilities` needs to expose — missing from the original read-list; added this
  session because §3.6's "capability descriptor" line is undecidable without it)

**Satisfies:** `platform-architecture.md` FR-CTX-001…012; `game-contracts.md` NFR-SEC-001…004,
NFR-SIZE-001…002

**Done when:** every object crossing the Espresso boundary is copied, not shared. A shared mutable
object across that boundary is a sandbox escape regardless of ADR-0006's trust model. Also (§3.6):
`io.turnbase:turnbase-serialization` is built and pinned by exact version in `turnbase-game-host`; the
guest bridge JAR is a shaded, unrelocated second artifact of `turnbase-game-host` containing
`io.turnbase.gdk.*`, the serialization component and Jackson, and it — not the Spring Boot fat jar — is
what `turnbase.gamehost.sdk-jar-path` points at in the image; a test drives §3.3's entrypoint through a
real Espresso context and the host shim sees only strings, primitives and byte arrays.

---

### IMP-M3-04 — gRPC service implementation

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-03

**Read first:**
- `docs/specs/internal-grpc/gamehost.proto` — including the field comments, which state all three
  sequence cases
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` **in full** — processing semantics,
  the error model, message size
- `docs/specs/game-host/game-host-internals.md` §9 (invocation, sequencing, idempotency, recovery),
  §12 (timeouts and `GameFailureKind` mapping)

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-FAIL-001…007

**Done when:** `TerminateSession` is idempotent **as specified in the contract**, not merely in the
implementation; `NOT_FOUND` is scoped so a retried teardown does not read as a hard failure.

**A forward gap in the sequence is normal and must be accepted** (IR-16). The three cases — replay of
a seen sequence, the ordinary next sequence, and a forward gap — are stated at the field in the
`.proto` precisely because a reader working from generated code never sees the prose table.

**Closed IMP-GATE-86:** 2026-09-27 — `game-host-internals.md` §9.3 required a Game Host recovering a
session after a crash to reconstruct the guest-side `TurnBaseGame` instance from Redis alone, but the
§8.1 session record had no `entryPointFqcn` field, no RPC after `CreateSession` carried that value
again, and the guest bridge (`GameEntrypoint`) had no way to populate its session map other than
`createSession`, which unconditionally re-runs `onInit` — an idempotency violation for a session
already mid-game. Blocked FR-FAIL-002, which this item's own *Satisfies* claims. Fixed the same
session: `game-host-internals.md` §8.1 now has a persisted `entryPointFqcn` field (written once at
`CreateSession`, outside the per-invocation atomic unit); §3.3 adds a
`restoreSession(sessionId, entryPointFqcn)` guest-bridge method that populates the session map without
invoking `onInit`; §9.3 now calls it out explicitly in the recovery flow.

**Scope note (session 89):** this item's *Done when* clause is narrowly `TerminateSession`
idempotency plus `NOT_FOUND` scoping, and that is what the implementation (`SessionDispatcher`,
`GameHostServiceImpl`, the `session:{sessionId}` Redis record) and its tests cover. Two things named
in the *Read first* §12 material are deliberately not built here, so a later item doesn't discover
their absence by surprise: (1) no watchdog/timeout-interrupt infrastructure exists — a handler that
hangs rather than throwing is not detected or escalated to `GameFailureKind.TIMEOUT`; only an
in-band exception during a handler call is reported as a failure. (2) `ArtifactCache.pin`/`unpin`
(`IMP-M3-02`) is still not wired to context lifecycle (`IMP-M3-03`'s `GameContextManager`) — neither
references the other — so FR-LOAD-004 ("never evict a JAR backing a live context") is not yet
enforced. Neither gap blocks this item's own clause or FR-FAIL-001's in-band-exception path; both
are pre-existing or orthogonal, not introduced by this session, but are undone.

---

### IMP-M3-05 — Orchestration client and session registry

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-04, IMP-M2-04, IMP-M2-06, IMP-M4-04

**`IMP-M2-06` added to *Depends on*** (`IMP-GATE-46`, session 41) — this item's own clause below
replaces `IMP-M2-06`'s in-process-stub `GameSessionStarter` with a real implementation, so the port
and the `START_GAME` handler calling it must exist first.

**`IMP-M4-04` added to *Depends on*** (`IMP-GATE-62`, session 56) — `GET /play/{sessionId}`
(`game-asset-serving.md` §4.1 row 1, §5) reuses `IMP-M4-04`'s `Host`-routing filter and asset-serving
code, and needs the deny-listed unpacked tree that item's dependency (`IMP-M4-03`) publishes; this
item is the one that creates the session data the route resolves against, so it is where the route
lands. See `IMP-M4-04`'s *Closed* note for the full gate.

**Read first:**
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — *Addressing the Game Host pods*,
  *Processing semantics*, *Error model*
- `docs/specs/game-host/game-host-internals.md` §6, §9, §13 (the Redis data model)
- `docs/specs/flows/02-room-to-game-start.md` — **step 6 names exactly which keys Orchestration writes**
- `docs/specs/platform/data-model.md` §1 (`active_session_id`), §4
- `docs/specs/api-design/room-websocket.md` — `GAME_STARTED`'s exact payload shape
- `docs/specs/game-frontend/game-asset-serving.md` §4.1 (the `/play/{sessionId}` route and version
  pinning), §5 (the bootstrap document), §7 (session integration)

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-REG-001…004, FR-SESS-001…006;
`game-rooms.md` FR-HOST-009 (success path only — the precondition/rejection half is `IMP-M2-06`'s);
`game-development-experience.md` FR-ASSET-003, FR-ASSET-007, FR-ASSET-008

**Done when:** `session:{id}` has **exactly one writer, the Game Host** (IR-14). Orchestration writes
only the keys flow 02 step 6 names and reads the rest. The platform's own record of a live session is
`room.active_session_id` — a durable Postgres fact — not a Redis key, so a Redis flush loses cached
state and not the knowledge that a session exists.

**The real `GameSessionStarter` implementation replaces `IMP-M2-06`'s stub**: on a successful
`START_GAME`, it creates the session via the orchestration client, persists `room.active_session_id`
(the session's `(gameId, version)` is `room.game_version`, pinned at room creation per flow 02 §A
step 3 and never rewritten — FR-ASSET-007 holds because that column is immutable, not because the
version is re-resolved at start; `IMP-GATE-87`), and
broadcasts `GAME_STARTED` with the live `sessionId` and the server-composed `gameFrontendUrl`
(`room-websocket.md`) — not before, since a failed session creation must never advance the room to
In Progress.

**`GET /play/{sessionId}` serves `game-asset-serving.md` §5's bootstrap document** for the pinned
`(gameId, version)`, 404ing when the session is unknown or ended and when the `Host` header's
`gameId` does not match the session's own (§4.1's *Validation*) — never serving game A's code from
game B's origin. A reconnecting player and every other participant receive the identical bundle
regardless of any republish in between (FR-ASSET-007).

**Closed IMP-GATE-87:** 2026-09-29 — three things this item needs that no document supplied, found
while reading its read-list, none of which the code could settle without a silent choice. (1) The
Redis shape of the Game Host registry: `game-host-internals.md` §13 named `hostlease:` and `contexts:`
but no key for the advertised address, runtime types, load signals or the enumeration of instances,
though the protocol doc says the address "is stored in the Redis registry" and host selection needs to
enumerate them; §13 and §11 now define `hosts`, `host:{instanceId}` and the selection rule, and
correct `hostlease:`'s writer (the Game Host never touches Redis directly). (2) The heartbeat
interval, lease TTL and dispatch deadline had no values or config keys — `local-environment.md` §7.8
now carries `turnbase.orchestration.*`. (3) `game-asset-serving.md` §4.1 and this item's own *Done
when* said the session's version is resolved at session start and stored on "the session record",
contradicting flow 02 §A step 3 and `game-catalog.md` FR-GAME-010/011 (the version is pinned at room
creation) and naming a record the platform does not own; §4.1 and this clause now say
`room.game_version`, reached through `room.active_session_id`.

**Closed IMP-GATE-88:** 2026-09-29 — `START_GAME` had no defined outcome when the preconditions hold
but session creation fails (no eligible Game Host, or `CreateSession` errors); the WebSocket error
registry had no code for it and this item's clause says only that the room must not advance.
`room-websocket.md` now defines `GAME_START_FAILED` (`details.reason` `NO_HOST_AVAILABLE` |
`SESSION_CREATION_FAILED`), unicast to the host, room left in Lobby.

**Scope note (session 92) — partly landed, not `DONE`.** Session 91's list (registry server,
`GameSessionService.create`, real `START_GAME`, `/play`) plus, in `turnbase-platform`:
`GameInputService` (per-session `seq:` `INCR`, `ProcessInput` against the host `routing:` names,
the `delivered:` watermark so effects reach `EffectDelivery` once per sequence, `failcount:` counting
consecutive failures with the `turnbase.gamehost.retry-limit` limit, transport statuses mapped per the
protocol's *Error model*); the real `GameInputDispatcher` (outbox `player_left` → `ProcessInput`,
`NOT_FOUND` conditional on `room.active_session_id`, sequence from `seq:` rather than the row id);
`CreateSession`'s initial effects handed to `EffectDelivery`. `EffectDelivery` is the seam to
`IMP-M3-07`; until then a logging stub delivers to no client. **Still owed:** (1) the two cross-repo
end-to-end checks below; (2) `ACTION_REJECTED` unicast to the acting player and the player-facing failure notice
at the retry limit — the acting-player action path (`GAME_ACTION` → `ProcessInput`) has no caller
yet, so `GameInputService.process` is exercised only by the outbox; (3) reassigning a session to
another host on `UNAVAILABLE` (FR-ORCH-005) — the call is left for retry with the failure counted, but
`routing:` is not rewritten, because the game key needed to re-select a host is not in Redis;
(4) `TerminateSession` at the retry limit belongs to `IMP-M3-08`. Transport facts from session 91
stand (trailers-only status lost under grpc-servlet; `maxSavePostSize` raised to 1 MiB for h2c).

**Closed IMP-GATE-89:** 2026-09-30 — what session 92 left owed was not all this item's. (1) The
trace check needs a session that a Game Host can actually run, and the only loadable game is
`IMP-M3-10`'s (it already owns "can actually be started"); `TestBundles`' Chess is an empty-interface
stub. It moves there. (2) `ACTION_REJECTED` and the retry-limit notice are `IMP-M3-09`'s own clause
("the acting player is told why"), and the `/app/game.*.action` admission handler that would feed
`GameInputService.process` is `IMP-M3-06`'s (FR-IN-003). (3) Host reassignment on `UNAVAILABLE` is
FR-ORCH-005, which `IMP-M3-08` satisfies; it also needs the game key that `routing:` lacks, which is a
design question for that item. The `Register` half of IMP-GATE-08 was checkable now and is:
`deploy/compose/e2e-smoke.sh` fails unless a Game Host is in the `hosts` set within 60 s of
`compose up` (measured 27 s).

**Closes IMP-GATE-08's cross-repo half:** this item gives `GameHostRegistryService` its real server
implementation, so it also carries the end-to-end check `IMP-M0-04` could not — a `turnbase-game-host`
instance pointed at a running Platform Monolith completes `Register` within `local-environment.md`
§3's 60-second budget.

**IMP-GATE-18's cross-repo half moved to `IMP-M3-10`** (`IMP-GATE-89`): this item builds the chain
client → WebSocket → Orchestration → gRPC → Game Host, but nothing that a Game Host can run exists
until the first official game does, so the one-trace-in-Tempo check is that item's clause.

---

### IMP-M3-06 — Game input outbox and delivery

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05

**Read first:**
- `docs/specs/platform/data-model.md` §4 — `game_input_outbox`, and why `session_id` is `NOT NULL`
- `docs/specs/platform/room-lifecycle.md` §3.3 — the conditional insert
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/flows/03-game-turn.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-contracts.md` FR-IN-001…006

**Also owns the acting-player path** (`IMP-GATE-89`): the `/app/game.*.action` handler that admits a
`GAME_ACTION` frame and calls `game.GameInputService#process`. `IMP-M3-05` built the service and only
the outbox calls it; this item is its second caller.

**Done when:** the outbox drain is **not** ownership-partitioned — it is a gRPC call needing no
ownership, and partitioning it leaves an unowned room's `player_left` undelivered, with the game
sitting on a turn that never comes.

**Built (session 94):** the drain (`GraceDeadlineSweepJob` duty 4, `GameInputDispatcherImpl`) already
existed from `IMP-M2-09`/`IMP-M3-05` and is not ownership-partitioned; this item added
`GameActionController` (`/app/game.{sessionId}.action`: handler-level admission read from durable room
state, the `PlayerRef` built server-side, `NOT_MEMBER` / `ROLE_NOT_ELIGIBLE` per `room-websocket.md`)
and `GameInputService.submitAction`, which serialises allocate-plus-dispatch per session — without it
two concurrent actions could reach the Game Host as 44, 43 and the first would be dropped as a replay.
A non-`DELIVERED` outcome is only logged; telling the player is `IMP-M3-09`. The channel-level
fast-fail (`game.*` `SubscriptionAuthorizer`) is `IMP-M3-07`'s, with the subscriptions it guards.

---

### IMP-M3-07 — Effect fan-out and spectator filtering

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-06

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §10 (effect delivery and fan-out)
- `docs/specs/api-design/websocket.md` § `GAME_EVENT`, § *Authorization model (game)*
- `docs/specs/api-design/room-websocket.md` § *Spectator Event Visibility*
- `docs/requirements/game-contracts.md` FR-EFF-001…007, NFR-SEC-001…004

**Satisfies:** `game-contracts.md` FR-EFF-001…007, NFR-SEC-001…004; `platform-architecture.md`
FR-DELIVER-001…006

**Done when:** **every effect address is validated against the producing session's membership at
fan-out** (IR-17). The per-user queue secures the *subscription*, not the *address* — a subscriber can
only read their own queue, but nothing stops game code addressing an effect to a user who is not in
this session, and without the check the platform delivers it. Spectator visibility is applied
server-side; a client-side filter hands spectators the hidden state and asks them not to look.

**Built (session 95):** `game.EffectFanOut` replaces the logging stub. It validates each
`send_to_player`/`send_to_team` address against the session's *durable* roster (`SessionRosterSource`,
implemented by `room` from `room_participant`; a spectator is not a valid player target) and drops a
failing effect with a WARN and `turnbase.effect.address_rejected.total{kind}`; only the first
`game_over` per result is delivered and its structured outcome is never sent. Spectator filtering is
structural (topic subscriptions plus the player-only address check). `room.GameSubscriptionAuthorizer`
is the channel-level fast-fail for `game.*` topics. `CreateSession`'s initial effects are checked
against the roster from the create command, because `active_session_id` is not yet committed.
Not built here: `GAME_SYNC`/`GAME_PLAYER_*`/`SESSION_FAILED` messages, the game-log retention, and
what follows `game_over` (history, teardown) — `IMP-M3-08`/`09`.

---

### IMP-M3-08 — Session teardown as a durable to-do

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05, IMP-M2-09

**`IMP-M2-09` added to *Depends on*** (`IMP-GATE-53`, session 45) — this item wires the normal
game-end caller into `room.RoomSessionDetacher#detach`, whose real implementation (`detachSession`,
`room-lifecycle.md` §4) is `IMP-M2-09`'s.

**Read first:**
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §4 — `session_teardown`, keyed by `session_id`
- `docs/specs/platform/room-lifecycle.md` §4
- `docs/specs/flows/06-game-end-and-rematch.md`

**Satisfies:** `game-rooms.md` FR-XFER-005; `platform-architecture.md` FR-ORCH-005…007

**Also owns host reassignment on `UNAVAILABLE`** (FR-ORCH-005, `IMP-GATE-89`): `IMP-M3-05` counts the
failure and leaves the call for retry, but does not rewrite `routing:`, because the game key needed to
re-select a host is not in Redis. Deciding where that key lives is this item's, in
`game-host-internals.md` §13, before code.

**Done when:** the to-do is keyed by `sessionId`, **not** by a flag on the room — a rematch would
overwrite the previous session's owed teardown. Any rule testing whether a teardown was recorded must
test `room.active_session_id = :sessionId`, a durable fact, rather than the presence of the
`session_teardown` row, which `terminateAndCleanup` deletes on success. The age of the oldest owed row
is exposed so the `TeardownOwed` alert can fire past 15 minutes (`observability.md` §6 sketches the
rule; `platform-operations.md` FR-ALERT-007 defines it, deferred here by `IMP-M0-10`).

**`IMP-GATE-53`: this item wires `detachSession`'s normal-game-end caller** (flow 06, `nextState =
'LOBBY'`, no `closed_reason`) — the game backend's `game_over` notification, once this item's own
session-completion handling recognizes it, calls `RoomSessionDetacher#detach` exactly as
`GraceDeadlineSweepJob` already does for the closure paths.

**Built (session 96):** `game.SessionTerminationClient` (`TerminateSession`, 2 s deadline, reason mapped
onto the proto enum, whole key family deleted on confirmation) behind `room.SessionTerminatorImpl`, which
deletes the `session_teardown` row on success and backs off on failure; `game.GameEndListener`
implemented by `room.RoomGameEndListener` (first delivered `game_over` → `detachSession(..., 'GAME_OVER',
'LOBBY')`); `turnbase.teardown.owed.age` gauge. **Game key decision:** `gamekey:{sessionId}` =
`{gameId}:{gameVersion}`, written with `routing:` (`game-host-internals.md` §13); `GameInputService`
uses it to reassign `routing:` on `UNAVAILABLE` or a vanished host. History recording on `game_over`
is `IMP-M5-01`'s; the retry-limit caller is `IMP-M3-09`'s.

---

### IMP-M3-09 — Game failure handling

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M3-07, IMP-M2-09

**`IMP-M2-09` added to *Depends on*** (`IMP-GATE-53`, session 45) — this item wires the
retry-limit-failure caller into `room.RoomSessionDetacher#detach`, whose real implementation
(`detachSession`, `room-lifecycle.md` §4) is `IMP-M2-09`'s.

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §8.1 (the session record's failure slot), §9.1, §12
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` § *Error model*
- `docs/requirements/platform-architecture.md` FR-FAIL-001…007
- `docs/requirements/game-contracts.md` FR-FA-001…003, NFR-REL-001…002
- `docs/specs/platform/room-lifecycle.md` §4 — the detach mechanism this item's caller invokes
- `docs/specs/flows/07-room-closure.md` § Caller 4 — retry-limit failure fails back to Lobby, not
  closed

**Satisfies:** `platform-architecture.md` FR-FAIL-001…007; `game-contracts.md` FR-FA-001…003,
NFR-REL-001…002

**Also owns the two notices `IMP-M3-05` left** (`IMP-GATE-89`): the unicast `ACTION_REJECTED` on
`/user/queue/errors` (kind, never message) and the player-facing notice at the retry limit.
`GameInputService` already counts `failcount:` and exposes the failure; this item delivers it.

**Done when:** the acting player is told why. `platform-architecture.md` FR-FAIL-001 and FR-FAIL-003
must be coherent about first-failure versus three-failure termination, and the failed input has a
stated disposition on every path.

**`IMP-GATE-53`: this item wires `detachSession`'s retry-limit-failure caller** (flow 07 caller 4,
`nextState = 'LOBBY'`, no `closed_reason`, `SESSION_FAILED` broadcast to clients instead of
`ROOM_CLOSED`, no history entry per `game-history.md` CON-001) — FR-FAIL-005's "notifies the Room
Service" is this call to `RoomSessionDetacher#detach`.

**The session record carries `lastOutcome` and `lastFailure` for a reason** (IR-15). A replayed
sequence that previously failed must return *its own* failure. Without those two slots the replay
returns `lastEffects` from the last *successful* input, so a retry of a rejected move looks to the
client like the move succeeded.

Retry-limit terminations feed the `GameSessionFailureRate` alert (`observability.md` §6 sketches the
rule; `platform-operations.md` FR-ALERT-003 defines it, deferred here by `IMP-M0-10`) — sessions
terminated by retry limit over active sessions, > 1% in 10 minutes.

---

### IMP-M3-10 — The first official game

**Repo:** a sixth repository, `turnbase-game-<name>`, **created when this item starts** ·
**Depends on:** IMP-M3-03

**The repository does not exist yet, and that is deliberate** (decided 2026-08-20). Nothing before
M3 needs a real game, and creating an empty sixth repo at M0 would put a submodule in this tree that
stays empty through four milestones. When this item starts: create it under the
`turnbase-platform` organisation, register it as a submodule, and add it to ADR-0012's repository
table and `CLAUDE.md`'s. It is a **consumer** of the platform, not part of it — which is the whole
point of the item, so it does not become a sixth first-class component.

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` §11 (the worked example) and §§3–8
- `docs/specs/gdk-api/frontend-gdk-api.md` §§3–7, §11
- `docs/specs/manifest/bundle-format.md` §2 (the archive), `manifest-schema.md`
- `docs/decisions/0006-game-trust-model-java-official-only.md`
- `docs/specs/api-design/websocket.md`, `room-websocket.md`, `room-rest-api.md` (the round-trip driver
  speaks them: login → `POST /api/rooms` → `POST …/participants {role}` → `TOGGLE_READY` /
  `START_GAME` → `REQUEST_GAME_SYNC` / `SUBMIT_ACTION`)

**Satisfies:** — *(no requirement. This item exists to prove the GDK contract is implementable by
someone outside the platform team, which ADR-0006 makes the MVP's only game-supply mechanism.)*

**Done when:** the game compiles against the **published SDK artifact only** — a dependency on
`turnbase-game-host` or `turnbase-common` means the contract is not self-sufficient and the item has
failed even if the game runs; it ships a frontend bundle built against the published npm package; it
is packaged per `bundle-format.md` §2 and published through IMP-M4-03's real pipeline; a full
create → join → start → several turns → outcome → history round trip passes against the local stack,
**and one game action shows as a single trace in Tempo spanning client → WebSocket → Orchestration →
gRPC → Game Host** (`observability.md` FR-TRACE-002; the cross-repo half of `IMP-GATE-18`, moved here
from `IMP-M3-05` by `IMP-GATE-89` because it needs a game a Game Host can run). `IMP-M3-05` is a
dependency for that reason.
Also (`IMP-GATE-71`): the bundle is placed in the directory `turnbase.seed.bundles-dir` names, as
`<gameId>.zip` with a fixed UUID (`local-environment.md` §6) — the compose bind mount and the chart
volume are this item's to add — and a clean `make reset-db` lists the game and it can be started.

**Closed:** IMP-GATE-93 (opened and closed 2026-09-30, session 111) — no work item owned the
platform's `REQUEST_GAME_SYNC` handler (`/app/game.{sessionId}.sync` → `GAME_SYNC` on
`/user/queue/game`, `websocket.md` § Game Session Protocol): `IMP-M3-07` listed `GAME_SYNC` as "not
built here — `IMP-M3-08`/`09`", and neither of those (teardown, failure handling) claims it, so the
round trip cannot pass. Fixed by giving the handler to this item, the first whose clause needs it
(remaining item 2 below).

**Done 2026-09-30 (session 113):** `make reset-db` / `make seed` in `turnbase-platform/Makefile` (stop clients, recreate schema + grants + extensions, flush Redis, restart → Flyway + seeder); after a clean reset the game is `ACTIVE` and `e2e-roundtrip.mjs` passes. `TURNBASE_SDK_PAT` now exists and game CI is green. Not built, not required by the clause: the real frontend sends no `traceparent` on STOMP frames, so a browser action's trace starts at the platform's `STOMP SEND` span.

**History:** **session 112:** `GAME_SYNC` handler (`game.{sessionId}.sync`, `GameSyncService`, retained `gamelog:` entries), full round trip login → create → join → ready → start → sync → 5 turns → `GAME_OVER` → history passes on compose, Tempo export fixed (OTLP HTTP 4318 in platform, Game Host, Helm), `STOMP SEND` span parented on `traceparent` and joined by the Game Host `ProcessInput` spans in one trace, Game Host artifact cache survives a restart; repo + submodule, backend (11 tests), frontend (vitest ≥95%), bundle
packaging, compose and Helm seed mounts; **session 111:** Game Host `HostLivenessLoop`
(Register/Heartbeat/ReportContexts/Deregister, re-registers on `NOT_FOUND`), `guest-bridge` jar now
actually contains `io.turnbase.gamehost.bridge.*` (it shipped only the SDK; `GuestBridgeJarIT`
guards it), the image's artifact-cache dir is writable, the platform logs why a session creation
failed. `START_GAME` works on the compose stack.

---

### IMP-M3-11 — GDK test harness

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M3-01, IMP-M3-03 (added by IMP-GATE-69: Done-when
clause 8's "same `ObjectMapper` configuration as the GDK Host" is `io.turnbase:turnbase-serialization`,
which `IMP-M3-03`'s `turnbase-sdk` half builds — `game-host-internals.md` §3.6), IMP-M3-13 (added by
IMP-GATE-91: clause 2's "shared bundle validator" is `io.turnbase:turnbase-bundle-validator`)

**Closed:** IMP-GATE-91 (opened and closed 2026-09-30, session 102) — clause 2 required a validator
artifact shared with the upload pipeline, but the pipeline's validator existed only inside
`turnbase-platform` (Spring-coupled, unpublishable) and no item extracted it. Fixed by `IMP-M3-13`.

**Read first:**
- `docs/specs/gdk-api/test-harness.md` **in full** — §1 is a scope boundary, not a preamble
- `docs/specs/manifest/bundle-format.md` §2.4, §3 and `docs/requirements/game-contracts.md` — the
  validator's entry point and the WebSocket protocol clause 4 speaks (added by IMP-GATE-91; the
  list previously named neither)
- `docs/requirements/game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010,
  NFR-UPLOAD-002
- `docs/specs/api-design/websocket.md` § Game Session Protocol, `docs/specs/gdk-api/frontend-gdk-api.md`
  §8–§10 and `docs/specs/game-frontend/game-asset-serving.md` §5 — the wire clause 4 must speak and the
  bootstrap clause 3 must populate (added by session 104: `game-contracts.md` says only that the
  client-facing wire is defined elsewhere, and names neither)

**Satisfies:** `game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010

**Closed:** IMP-GATE-67 (opened and closed 2026-09-22) — this item's own *Done when* clause checked
only the executing round trip (FR-HARNESS-010), while its own *Satisfies* claimed the full harness
(FR-HARNESS-001…008) — the CLI launcher, the two-origin browser bootstrap, the mock
Orchestration/WebSocket bridge, bundle-validator reuse before launch, multi-player simulation, log
rendering and team/parameter configuration `test-harness.md` describes at length — none of which
exists anywhere in `turnbase-sdk` yet and which no other registry item claims. Fixed by rewriting
*Done when* below to cover every Must-priority FR-HARNESS clause *Satisfies* already claimed, not just
FR-HARNESS-010. FR-HARNESS-008 (hot reload, "Could") is left out of *Done when* deliberately — it
stays in *Satisfies* as aspirational per its own priority, matching how other items treat "Could"
rows.

**Done when:**
1. `mvn io.turnbase:turnbase-harness:run`, invoked from a game project directory containing a manifest
   and bundle, launches a local environment with no Docker, Redis or database (FR-HARNESS-001,
   FR-HARNESS-006).
2. Before launch, the shared bundle validator (the same artifact `bundle-format.md` gives the upload
   pipeline) runs against the project's manifest and bundle; a fatal finding stops the launch, a
   warning prints and the launch continues (FR-HARNESS-002).
3. The harness serves the game FE (`frontend.entryPoint`) at `http://game.localhost:{port}` and its own
   shell at `http://localhost:{port}`, populating `window.__TURNBASE__` before the game's JS runs
   (`test-harness.md` §3).
4. Two or more browser tabs connect as distinct simulated players through an in-process mock
   Orchestration that speaks `game-contracts.md`'s real WebSocket protocol — session, roster, teams,
   sequence allocation, effect fan-out with the spectator-broadcast-only rule (FR-HARNESS-001,
   FR-HARNESS-003).
5. Team assignment and game parameters are configurable before a session starts — the roster synthesized
   from the manifest's `teamTemplates` at the `count.min` × `size.max` shape, parameters overridable via
   `harness.json` (FR-HARNESS-007).
6. A CLI flag or debug-panel action delivers a mock `action`, `player_joined`, or `player_left` (with a
   selectable `reason`) to a chosen player without opening a browser tab for them, and can force a
   `resync` (FR-HARNESS-005).
7. The game log renders with the platform's Markdown configuration (FR-HARNESS-004).
8. After `onInit` and after every action, the harness runs the executing serialization round trip
   (serialize, deserialize, compare) using the same `ObjectMapper` configuration as the GDK Host;
   `strictSerialization: true` (the default) fails the run on a mismatch, `false` warns and continues
   (FR-HARNESS-010).

**Built (session 104):** module `harness` (`io.turnbase:turnbase-harness`, `io.turnbase.harness`),
plain jar for now. Clause 2 (`PreLaunchCheck`, over the shared `BundleValidator`; a project directory is
an unpacked bundle, zipped in memory — `test-harness.md` §8 now says so), clause 5's roster half
(`RosterSynthesizer`, `HarnessConfig` for `harness.json`) and clause 8 (`LocalGame`: in-process game,
`equals` round trip after `onInit` and every handler, strict/non-strict) hold, with tests. The E5
`gdkApiVersion` check accepts any version and a warning says so (`test-harness.md` §7).

**Built (session 105):** the module is now `maven-plugin` packaging: `RunMojo` (`io.turnbase:turnbase-harness:run`,
`-Dturnbase.harness.dir`/`.port`, no project model needed — verified from a bare directory through Maven,
offline of Docker/Redis/DB) → `HarnessLauncher` (pre-launch check → `GameLoader` → `onInit` → server), also
`HarnessMain`. `HarnessServer` (clause 3): JDK `HttpServer`, both origins on one port told apart by `Host`
(`localhost` shell, `game.localhost` game, anything else 421); the game origin serves the §5 bootstrap with
`window.__TURNBASE__` ahead of the entry-point script, `parentOrigin` fixed from the shell origin, and
serves project files except `manifest.json`, `harness.json`, the backend JAR and anything outside the root.
Clauses 1, 2, 3 (server side) and 8 hold, with tests (`LaunchTest`).

**Built (session 106):** clauses 3–7 complete. `MockOrchestration` speaks the real STOMP-over-WebSocket game session protocol (`websocket.md`): sync flow with `asOfSequence`, `GAME_EVENT`/`GAME_LOG`/`GAME_OVER`/`GAME_PLAYER_JOINED|LEFT` with `sequence`/`index` (lifecycle at `index: -1`), effect-address validation, spectator = broadcast only, identity from the connection. Transport is a hand-rolled RFC 6455 endpoint (`WebSocketServer`, own loopback port, `Origin` must be the shell). The shell (`shell.js`) relays STOMP↔`postMessage` with both halves of the origin check, renders the log through a locked-down Markdown subset, and has the roster/parameters/debug panel; `DebugCommand` is one shape for panel POST, `harness.json` scenario and CLI flags (`--player --action|--join|--leave|--resync`, or `-Dturnbase.harness.*`). `@turnbase/gdk` is injected by import map from the built `dist/index.js` bundled into the harness jar (`publish.yml` now runs the npm build first). Verified in a real browser. **Not built, outside *Done when*:** log colour annotations (syntax is `game-contracts.md` OQ-001), the CSP would-have-blocked report and audit-hook warnings of `test-harness.md` §2–§3, `game-development-experience.md` FR-HARNESS-008.

---

### IMP-M3-12 — FE GDK client (`@turnbase/gdk`)

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M0-02

Opened by IMP-GATE-05 (`IMP-M0-02`, closed 2026-08-22): `FR-FEGDK-001…009` had no owning item in
`turnbase-sdk`, the repository that publishes the package. `IMP-M6-05` implements the platform
shell's half of the postMessage boundary, not the client library itself.

**Read first:**
- `docs/specs/gdk-api/frontend-gdk-api.md` **in full** — §4 handshake, §7 actions, §8 origin
  validation, §9 bootstrap contract, §10 the inbound/outbound envelope
- `docs/requirements/game-development-experience.md` FR-FEGDK-001…009
- `docs/requirements/game-contracts.md` FR-FE-001…006, FR-FA-001…003, NFR-SEC-004

**Satisfies:** `game-development-experience.md` FR-FEGDK-001…009; `game-contracts.md`
FR-FE-001…006, FR-FA-001…003, NFR-SEC-004

**Done when:** `TurnBaseClient<TAction, TEvent>` exists with the five replaceable callbacks
(`onInit`, `onGameEvent`, `onPlayerJoined`, `onPlayerLeft`, `onGameOver`), `start()`, `sendAction()`
and `dispose()`; the inbound message listener accepts a message only when **both**
`event.origin === parentOrigin` **and** `event.source === window.parent` hold (§8); no outbound post
ever uses `targetOrigin: '*'`; `start()` throws synchronously when `window.__TURNBASE__` is missing
and no `parentOrigin` override was supplied; calling `sendAction` before `init` throws.

**The trusted origin is never derived from a received message** — only from the shell bootstrap
(§9) or the explicit test-harness override — because inferring it from message traffic is circular
and is exactly the mistake the origin check exists to prevent.

---

### IMP-M3-13 — Shared bundle validator module

**Repo:** `turnbase-sdk`, then `turnbase-platform` · **Depends on:** IMP-M4-03, IMP-M3-03

Opened by IMP-GATE-91 (`IMP-M3-11`, 2026-09-30): `bundle-format.md` §2.4 and `game-development-experience.md` FR-HARNESS-002 say the
archive reader and validator are one component consumed by the upload pipeline, the unpacker and the
test harness. It was built inside `turnbase-platform` (`upload.ArchiveReader`, `ManifestValidator`,
`BackendJarAnalyzer`, `StateSerializabilityAnalyzer`, `ClassFileUtil`, and the pipeline body of
`BundleValidationService`), where the Spring stereotypes and `platform.common.CheckError` make it
unusable by the harness. Same lesson as the serialization engine (`game-host-internals.md` §3.6):
extract it, or the harness reimplements it and drifts.

**Read first:**
- `docs/specs/manifest/bundle-format.md` §2.4, §3, §4 and `manifest-schema.md`
- `docs/implementation/conventions.md` §5 (cross-repo artifacts) and the *manifest schema is copied*
  paragraph — the schema copy moves to this module
- `turnbase-platform/src/main/java/io/turnbase/platform/upload/` — the code being extracted

**Satisfies:** `game-development-experience.md` FR-HARNESS-002 (the artifact half)

**Done when:**
1. `turnbase-sdk` builds a third module, `io.turnbase:turnbase-bundle-validator`, from the same root
   `./mvnw install`, at the shared version. It has no Spring, no `turnbase-common`, no
   `turnbase-game-host` dependency (the enforcer's banned list applies) and carries its own committed
   copy of `manifest.schema.json` (`scripts/sync-manifest-schema.sh` learns the new path).
2. It exposes the reader, manifest validation, backend JAR analysis and static serializability
   analysis behind one entry point returning framework-free findings (severity, code, message), reusing
   `turnbase-serialization` where the analysis needs it.
3. `turnbase-platform` depends on it (pinned per `conventions.md` §5), its `upload` package keeps only
   the Spring wiring, persistence and async orchestration, and its existing upload unit and integration
   tests pass unchanged.
4. The moved classes' tests move with them and the module meets the JaCoCo gate.

**Built (session 103):** `io.turnbase:turnbase-bundle-validator` in `turnbase-sdk` (package
`io.turnbase.bundle`), entry point `BundleValidator.validate(zip, Options)` → `Result` of
`Finding(severity, code, message)` plus the `Bundle` Phase G needs. The platform's `upload` package
keeps `BundleValidationService` (fetch, trust rule, persistence, Phase G) and maps `Finding` to its own
`CheckError`. Decisions worth knowing: `VersionOrdering` moved with the module (the gdk range check
uses it; the platform imports it); the platform's own copy of `manifest.schema.json` is gone and
`sync-manifest-schema.sh` now targets the module's copy; the static analysis consults
`BindingCapabilities` for JDK map keys and module-dependent types (additive — the hardcoded lists
still apply); `TestBundles`/`TestJavaCompiler` are duplicated in the module's tests because the
platform's ITs still use theirs.

---

## M4 — Catalog and upload

**Read first:** `docs/specs/manifest/bundle-format.md`, `manifest-schema.md`, `manifest.schema.json`,
`docs/specs/platform/data-model-catalog.md`, `docs/specs/api-design/file-uploads.md`,
`docs/specs/game-frontend/game-asset-serving.md`, flow `08`.

### IMP-M4-01 — Catalog listing and game detail

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01

**Read first:**
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009
- `docs/specs/platform/data-model-catalog.md` §1 (`game`), §3 (`game_tag`), §4 (`game_review`)
- `docs/requirements/admin-tooling.md` FR-BADGE-001…004, FR-PRV-001 — visibility is an
  admin-tooling rule that this endpoint enforces
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/specs/api-design/input-validation.md` § *Output encoding*
- `docs/specs/api-design/rest-conventions.md`
- `docs/specs/api-design/error-handling.md`
- `docs/specs/platform/data-model.md` §1 (`room`), §2 (`room_participant`) — FR-GDET-005's active
  player count reads these tables directly, `room_open_game_idx`'s documented purpose
- `docs/specs/api-design/catalog-rest-api.md`

**Satisfies:** `game-catalog.md` FR-CAT-001…010, FR-GDET-001…009, NFR-PERF-001…002,
NFR-SCAL-001, NFR-SEC-001…002, NFR-USAB-001…002; `admin-tooling.md` FR-PRV-001; `platform-views.md`
VW-CAT-001…003, VW-GDET-001…003

**Done when:** an Unverified game is absent from the catalog and from search for every caller except
its owner (`admin-tooling.md` FR-PRV-001); each game carries exactly one badge, read from one column
(FR-BADGE-001); descriptions are delivered as **Markdown source** and rendered to React elements
client-side (IMP-M6-06) — the API never returns an HTML string, which is what makes
`input-validation.md`'s `dangerouslySetInnerHTML` ban enforceable rather than aspirational (IR-19).

**Closed:** `IMP-GATE-64` (opened and closed 2026-09-20, session 61) — three defects found claiming
this item. (1) No document defined the `GET /api/games` / `GET /api/games/{gameId}` routes this item's
own *Done when* requires; fixed by adding `docs/specs/api-design/catalog-rest-api.md`, registered in
that directory's `INDEX.md` and in `game-catalog.md`'s *Related API Specifications*. (2)
`pagination-filtering-sorting.md` § *Filtering* § *Implementation* and `api-design/INDEX.md`'s *Key
Decisions* both described a Spring Data JPA Specifications mechanism that exists nowhere in
`turnbase-platform` — every repository (`RoomRepository`, `AdminGameRepository`, etc.) hand-writes SQL
via `JdbcClient`; fixed both documents to describe that mechanism instead. (3) This item's own
*Satisfies* claimed the entirety of `FR-GAME-001…014` and `admin-tooling.md FR-PRV-001…004`, neither
of which its *Done when* clause tests or its two read-only endpoints build — narrowed to what is
actually built (dropped `FR-GAME-001…014` outright; narrowed `FR-PRV-001…004` to `FR-PRV-001`).
`FR-PRV-004` (the game owner's submit-for-review action) remains unclaimed by any item in the
registry — `admin-rest-api.md` §7 already disclaims building it; noted in `STATUS.md` for a future
item rather than solved here. (4) `data-model-catalog.md` §1 asserted a null-owner game "renders the
platform name" as its catalog author without ever naming the literal string — a decision visible in a
response body that no document made; fixed by naming it (`"TurnBase"`) in that section.

---

### IMP-M4-02 — Manifest schema validation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-06

**Closed:** IMP-GATE-60 (opened and closed 2026-09-14, session 53) — this item's own read-list calls
`manifest.schema.json` "the executable artifact and the authority," meaning code in this repository
reads it directly, but `turnbase-platform` must build from a standalone clone (no path outside the
repository, same constraint `conventions.md` §5 states for `turnbase-common`) and no document said
how the file gets from the spec tree into this repository's build, where it lives, or whether a
drift guard exists — `manifest-schema.md`'s own "the contract ... so the two cannot drift" language
already names the exact risk `conventions.md` §5 built a full mechanism for on the proto, and never
extended it here. Same shape as `IMP-GATE-31`/`33`/`35`/`37`/`57`/`58`/`59`, at the scale of a build
mechanism rather than a REST surface. Fixed: `conventions.md` §5 gained a paragraph mirroring "The
proto is copied, not shared" — a committed copy at
`turnbase-platform/src/main/resources/manifest/manifest.schema.json`, refreshed and checked by new
`scripts/sync-manifest-schema.sh` (`--check` is a no-op until a copy exists, since none does yet —
wiring the parent's pre-push hook is this item's own job once it creates the first copy, not a
prerequisite to starting it).

**Read first:**
- `docs/specs/manifest/manifest.schema.json` — **the executable artifact and the authority**
- `docs/specs/manifest/manifest-schema.md` — the prose, including the `capabilities` rules
- `docs/specs/manifest/bundle-format.md` §3 (where in the pipeline this runs)
- `docs/requirements/game-development-experience.md` FR-MANIFEST-001…009

**Satisfies:** `game-development-experience.md` FR-MANIFEST-001…009

**Done when:** validation runs against `manifest.schema.json` — the executable artifact — and the
prose documents agree with it. Where they disagree, fix the document. `capabilities.ai: true` is
**rejected** at validation (IR-12): the field survives in the schema for a future release, and a
bundle declaring it today would list a game whose AI seats can never be filled. The schema file is
committed to this repository via `scripts/sync-manifest-schema.sh` (`IMP-GATE-60`,
`conventions.md` §5), and that script's `--check` mode is wired into the parent repo's
`.githooks/pre-push` in the same change that creates the copy.

**Done 2026-09-14 (session 54).** `upload.ManifestValidator` runs `manifest.schema.json` — the
committed copy this item creates at `turnbase-platform/src/main/resources/manifest/`, generated by
`scripts/sync-manifest-schema.sh` — as Layer 1, through `com.networknt:json-schema-validator`
(Draft 2020-12) rather than hand-written per-field checks. Layer 2 covers the cross-field rules the
schema cannot express (`manifest-schema.md` § Validation): team-template and parameter range
ordering, the conditional team-template name, parameter-default membership/bounds per type, and
duplicate parameter keys — plus the IR-12 rejection of `capabilities.ai: true`, reported the same way
(`check: "manifest.capabilities.ai"`). Unknown top-level and nested keys are collected into a
separate `warnings` list rather than failing validation, matching the schema's deliberately lenient
`additionalProperties` stance. `ManifestValidationResult` carries both lists; `errors`/`warnings`
entries are `common.CheckError` (`{check, message}`), the shape `error-handling.md`'s bundle-
validation format already uses. Bundle-, archive- and JAR-level checks (`bundle-format.md` Phases A,
B, C, E, F, G) are `IMP-M4-03`'s concern, not this item's — `ManifestValidator` only ever sees an
already-parsed manifest document.

**Also fixed, found while committing the schema copy:** neither this repository's nor
`turnbase-platform`'s `.gitattributes` pinned `manifest.schema.json` to LF, unlike `gamehost.proto`
— `sync-manifest-schema.sh`'s own header comment claimed the same "pinned to LF on each side"
guarantee `sync-proto.sh`'s does, copied verbatim from it, but the pin itself was never added when
the script was written (`IMP-GATE-60`, session 53). Under this environment's `core.autocrlf=true`,
a fresh clone would have checked the authoritative file out as CRLF while the committed copy in
`turnbase-platform` stayed whatever line ending existed at commit time, and `sync-manifest-schema.sh
--check`'s `--strip-trailing-cr` masks exactly this case locally without fixing it for a real content
diff. Fixed: both `.gitattributes` files gained a `text eol=lf` pin for their respective path,
mirroring `*.proto`'s. Not gated — a missing safeguard the script's own comment already claimed
existed, not a contradiction between two documents — but worth a line here so it is not
rediscovered as a mystery CI flake.

**Verified.** `ManifestValidatorTest` (unit): the spec's own worked example validates clean; each
Layer 2 rule and the `capabilities.ai` rejection independently produce the documented `check` id;
an unrecognized top-level key produces a warning without affecting `valid()`; an empty document
produces the full set of missing-required-field errors. `./mvnw verify` and
`./mvnw verify -Pintegration` green locally. Pushed directly to `turnbase-platform master`
(no PR, ADR-0012) after the `pre-push` hook passed; CI run `34893340481`'s `build` job green
(19m42s — Verify, coverage, both Trivy gates, image push). `e2e` failed on the same
`compose-platform-1`/smoke-test issue flagged as unrelated and non-gating since session 50/51
(`platform-operations.md` OQ-002); this run's failure is on "Run the e2e smoke test," not a new
shape. Submodule ref bumped in this repo.

---

### IMP-M4-03 — Upload pipeline and version state machine

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-02

**Follow-up (IMP-GATE-69, not a gate):** `StateSerializabilityAnalyzer` hardcodes the Jackson
capability table `bundle-format.md` §4.4 says to read from the shared serialization component, because
that artifact did not exist. Once `io.turnbase:turnbase-serialization` is published
(`game-host-internals.md` §3.6), replace the hardcoded table with its capability descriptor. Nothing
else waits on it.

**Closed:** IMP-GATE-61 (opened and closed 2026-09-19, session 55) — `error-handling.md`'s Bundle
Validation Errors § Synchronous claimed `POST /api/games/{gameId}/versions` is the only endpoint
producing a synchronous `422` in the `{check, message}` shape, and `bundle-format.md` §3.1's phase
table and §3.4's prose grouped Phase B with the asynchronous C-G background job, reporting only via
`validation_errors`/`GET`. Both directly contradict `file-uploads.md`, whose flow narrative (step 3)
and dedicated § Size Validation independently and repeatedly state that stage B1 (the stored-object
size check) fails the `confirm` request itself, synchronously, before `202` is ever returned. Fixed
in `file-uploads.md`'s favor — it is the more specific, operational document for the confirm
endpoint and states the same thing twice: `bundle-format.md` §3.1's table now carries B1 as its own
synchronous row distinct from the C-F background job, §3.2's Phase B heading and §3.4's prose say so
explicitly, and `error-handling.md`'s Synchronous section now names both request paths that can
produce this shape.

**Read first:**
- `docs/specs/manifest/bundle-format.md` **in full** — §3 the pipeline (Phases A–G), §4 the
  serialization round trip, §7 failure/retry/cleanup, §9 the assumptions it makes visible.
  **§3.4 is the authoritative statement of where a failure surfaces.**
- `docs/specs/api-design/file-uploads.md` — the three-step flow and its error cases
- `docs/specs/platform/data-model-catalog.md` §2 (`game_version`) and §7
- `docs/specs/api-design/rate-limiting.md` Tier 3; `error-handling.md` § *Bundle Validation Errors*
- `docs/specs/flows/08-upload-to-play.md`

**Satisfies:** `game-development-experience.md` FR-UPLOAD-001…009, FR-BUNDLE-001…007,
NFR-UPLOAD-001…002, NFR-SIZE-001

**Done when:** every non-terminal status has a documented exit, including `PROCESSING` when the
validating pod dies; a died-mid-validation version number is not permanently burned by the
`(game_id, version)` unique constraint; two open slots cannot walk the active version **backwards**;
activation clears Verified status **only on `VERIFIED → UNVERIFIED`** — an unconditional clear makes
every official upload abort against `game_official_ownerless_ck`, which is the only path the MVP
exercises.

**Failures surface in two different places and the split is not negotiable** (IR-18). Phase A
failures are a **synchronous `422`** on the request itself. Everything from `confirm` onward — Phases
B through G — surfaces as the version resource's `FAILED` state, read via
`GET /api/games/{gameId}/versions/{uploadId}`. A client that waits for a `422` from `confirm` waits
forever.

---

### IMP-M4-04 — Bundle publication and asset serving

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03

**Closed:** IMP-GATE-62 (opened and closed 2026-09-19, session 56) — this item's own *Satisfies*
triple-claimed `game-contracts.md` FR-FE-001…006 with `IMP-M3-12` and `IMP-M6-05`, even though
`game-asset-serving.md`'s own Scope section names "the postMessage message catalogue itself" as
explicitly **out of scope** for that document — FR-FE-001…006 is the game-session event catalogue
(`init`, `game_event`, `player_joined`, `player_left`, `game_over`, spectator filtering), which
neither bundle publication nor asset serving ever touches. Separately, this item's own *Done when*
clause tested none of its real `FR-ASSET-001…009` scope: its one clause ("publication filters") was
already fully satisfied by `IMP-M4-03`'s `PublicationService`, which implements §5.2's deny list
verbatim, before this item's own code existed. Underneath that, half of this item's read-list —
`GET /play/{sessionId}` (§5's server-rendered bootstrap document; §4.1's version-pinning row and its
`Host`-vs-session `gameId` cross-check; FR-ASSET-003/007) — has no data to resolve against: no
`sessionId → (gameId, version)` mapping exists anywhere in the schema, because game sessions are
`IMP-M3-05`'s data to create, and `IMP-M3-05` was not this item's dependency
(`room.GameSessionStarter` is still `IMP-M2-06`'s no-op stub, confirmed by reading
`room/PendingGameSessionStarter.java`). Same shape as `IMP-GATE-08`/`18`/`28`/`46`/`53` — an item
whose read-list quietly assumes a caller or a data source that a sibling, unlisted item actually
builds. Fixed: `FR-FE-001…006` dropped from this item's *Satisfies* — unique to `IMP-M3-12`
(the client library) and `IMP-M6-05` (the shell's relay) already, per their own sections. This item
narrowed to exactly what `IMP-M4-03` alone makes buildable: the `Host`-header virtual-routing filter
and `GET /g/{gameId}/{version}/**` static asset serving. `GET /play/{sessionId}` (§4.1 row 1, §5, §7)
moves to `IMP-M3-05` below — the item that already composes and broadcasts `gameFrontendUrl` on
`GAME_STARTED` and is the only item with session data to resolve the route against; `IMP-M3-05` gains
`IMP-M4-04` in *Depends on* (it reuses this item's asset-serving code and deny-listed tree),
`FR-ASSET-003/007/008` in *Satisfies* (008 was already being built there, unclaimed), and a *Done
when* clause. Read-list and Done-when corrected below.

**Read first:**
- `docs/specs/manifest/bundle-format.md` §5 (unpacking and publication)
- `docs/specs/game-frontend/game-asset-serving.md` §3 (origin architecture), §4 (serving — routes,
  the `Host` filter, the unauthenticated-assets deny list), §6.4 (CSP on game responses), §9
  invariants 1, 2, 4 (the ones that do not depend on session data — §9 has only 5 invariants total;
  the prior citation of a 6th was an editing slip, corrected here, session 57)
- `docs/decisions/0007-game-frontend-separate-domain.md`
- `docs/specs/deployment/local-environment.md` §7.7

**Satisfies:** `game-development-experience.md` FR-ASSET-001, FR-ASSET-002, FR-ASSET-005,
FR-ASSET-006, FR-ASSET-009

**Done when:** a request's `Host` header alone decides whether it may reach the platform API, the
platform frontend, or `/g/{gameId}/{version}/**` — never routes from one set to the other regardless
of path (§4, §9 invariant 1). `GET /g/{gameId}/{version}/**` serves only what `IMP-M4-03`'s
publication deny list wrote — unpacking the whole archive would publish the backend JAR to anonymous
callers, since `gameId` is in the hostname and the version is a public catalog column, so the URL is
derivable from a catalog page — with the fixed extension-to-content-type map, `X-Content-Type-Options:
nosniff`, `Cache-Control: public, max-age=31536000, immutable`, and §6.4's CSP on every response; a
missing object 404s. No platform cookie is ever scoped to the games domain, and the games origin never
appears in any CORS/STOMP/server-side trust allowlist (§9 invariant 2).

**A pre-signed URL is a bearer credential.** Every log line that carries one is truncated at the
query string (FR-OBS-005).

---

### IMP-M4-05 — Admin API, review queue and badges

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03

**Closed:** `IMP-GATE-63` (opened and closed 2026-09-19, session 58) — this item's own claimed
`admin-tooling.md` FR-OFF-001 ("admin can upload a game directly as an Official title") turned out to
be unbuildable: no document anywhere defines how a `game` row is created at all — `file-uploads.md`
step 1 assumes `gameId` already names one, and `game-catalog.md` FR-GAME-001 defers the mechanism to
a document that itself defers it onward again. This item's read-list also never named
`file-uploads.md`/`bundle-format.md`, whose Phase A–G pipeline the fix has to reuse, and its own
*Satisfies* duplicated `FR-PRV-001…004` with `IMP-M4-01`, which already claims and actually implements
them (catalog visibility, room-creation preconditions) — neither is admin-API work. Fixed: new
`docs/specs/api-design/admin-rest-api.md` — `POST /admin/games` (the missing game-row creation, scoped
to the one path the MVP needs: admin's own official upload) plus an admin-scoped mirror of
`file-uploads.md`'s three routes, the review-queue endpoints (list/detail/approve/reject), and the
`bundle-format.md` stage E4 resolution (the "arrived on the admin path" half `IMP-M4-03`'s session
note left open is decided by which listener served the request — there is no other signal available).
`rest-conventions.md` § *Base Path* now carves out the admin listener's `/admin/` namespace;
`admin-tooling.md` gained a *Related API Specifications* section. `FR-PRV-001…004` dropped from this
item's *Satisfies* (see below). `python3 scripts/check-corpus.py` clean.

**Read first:**
- `docs/requirements/admin-tooling.md` **in full**
- `docs/specs/api-design/admin-rest-api.md` **in full** — the endpoint shapes, request/response
  bodies and status codes this item builds to
- `docs/specs/api-design/file-uploads.md`, `docs/specs/manifest/bundle-format.md` §3.2 (Phases A-G,
  stage E4) — the pipeline `admin-rest-api.md` §4 reuses verbatim; read `upload.VersionUploadController`/
  `Service`/`PublicationService` directly, don't re-derive them
- `docs/specs/platform/data-model-catalog.md` §1, §2, §4
- `docs/specs/api-design/rest-conventions.md` § *Actuator and the Management Port*, § *Base Path*
- `docs/specs/deployment/local-environment.md` §1 host port map

**Satisfies:** `admin-tooling.md` FR-ADM-001…003, FR-REV-001…006, FR-BADGE-001…004, FR-OFF-001…002,
NFR-AUD-001, NFR-CRED-001, NFR-SEC-001

**`FR-PRV-001…004` removed from *Satisfies*** — `IMP-M4-01` already claims them and its own Done-when
is where they are actually checked (catalog-query invisibility, room-creation preconditions); nothing
in this item's own Done-when below ever exercised them, so the duplicate was a bookkeeping error, not
a second implementation.

**Done when:** the admin API is served on the **management port, the same listener as actuator**, and
is loopback-bound under compose and unrouted under Kubernetes (FR-ADM-001, `admin-tooling.md`
CON-001, `local-environment.md` §1); HTTP Basic with credentials from configuration (FR-ADM-002);
**no browser panel exists** (FR-ADM-003); `POST /admin/games` creates the game row and `POST
/admin/games/{gameId}/versions`/`.../confirm` complete an official upload to `ACTIVE` with no review
row ever created (FR-OFF-001…002, `admin-rest-api.md` §3-§4); approval sets Verified and publishes,
rejection stores a plain-text reason and does **not** delete the game or transfer ownership
(FR-REV-004…006, `admin-rest-api.md` §5); every mutating admin action writes an audit record
(NFR-AUD-001).

---

## M5 — History, statistics, notifications

### IMP-M5-01 — Game history recording and query API

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-09

**Closed:** IMP-GATE-81 (opened and closed 2026-09-27, session 81) — this item's own *Satisfies*
claimed FR-HIST-020…030 (the Profile History Tab's display, search and pagination behaviour) in full,
but no document gave it a REST surface to build against — `data-model-history.md` §2's own three
indexes (`ghe_user_recent_idx`, `ghe_user_name_trgm_idx`) exist specifically to answer this tab, yet
nothing exposed them over HTTP — and this item's own *Done when* clause never tested any of
FR-HIST-020…030, only the recording transaction. `IMP-M6-06` claims the identical range on the
frontend side but had no dependency on this item and no endpoint to render. Same shape as
`IMP-GATE-80`. Fixed: new `docs/specs/api-design/history-rest-api.md` —
`GET /api/users/{username}/history`, privacy-resolved the same way `social-rest-api.md` §7 resolves
the friends tab, searchable and paginated per FR-HIST-025…026; registered in that directory's
`INDEX.md` and in `game-history.md`'s new *Related API Specifications* section. This item retitled
from *Game history recording* to name the read side it was already claiming; its read-list and
*Done when* gained the new document.

**Read first:**
- `docs/requirements/game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030
- `docs/specs/platform/data-model-history.md` §1 (`game_session_completion`), §2
  (`game_history_entry`)
- `docs/requirements/game-contracts.md` FR-OUTCOME-001…004
- `docs/specs/flows/06-game-end-and-rematch.md`
- `docs/specs/api-design/history-rest-api.md` (`IMP-GATE-81`) — the read endpoint this item also
  builds

**Satisfies:** `game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030,
NFR-HIST-001…003; `game-contracts.md` FR-OUTCOME-001, FR-OUTCOME-004

**Done when:** a malformed outcome from game code cannot abort the whole recording transaction with
no retry path (`ghe_placement_ck`); `GET /api/users/{username}/history` implements
`history-rest-api.md` in full — the `visibleSections` privacy re-check, `search`, pagination, and the
server-computed `outcomeLabel`/`gameLinkable` fields — since that document, not this clause, is what
makes FR-HIST-020…030 checkable.

**Game code produces the outcome, so the outcome is untrusted input.** Validate it before it reaches
a `CHECK` constraint; a constraint violation here rolls back a completed game's entire record and
there is nothing left to retry from.

---

### IMP-M5-02 — Per-game statistics

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01

**Read first:**
- `docs/requirements/per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027
- `docs/specs/api-design/statistics-rest-api.md` (`IMP-GATE-90`) — the two read surfaces
- `docs/specs/platform/data-model-history.md` §3 — *The per-game counter and its writer*
- `docs/requirements/user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Closed:** IMP-GATE-90 (opened and closed 2026-09-30, session 99) — the item claims FR-STATS-010…012
and FR-STATS-020…027, but no document defined a route or response field for either:
`catalog-rest-api.md` §6 excluded per-game statistics from game detail, and `profile-rest-api.md` has
no statistics content. `IMP-M5-01` already shipped the single counter writer, so what is left is
the two reads. Fixed: new `statistics-rest-api.md` — `completedSessionCount` on `GET
/api/games/{gameId}` (also added to `catalog-rest-api.md` §4/§6) and `GET
/api/users/{username}/statistics` (`totalPlayed`, `mostPlayedGame`), privacy-resolved like `/history`
with a zero-state `200`. Registered in `api-design/INDEX.md` and `per-game-statistics.md`.

**Satisfies:** `per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027,
NFR-STATS-001…003; `user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Done when:** the counter has exactly **one** writer — the one `data-model-history.md` §3 names. Two
writers race and the count drifts silently, with no error and no way to detect it after the fact.
Guests accumulate no statistics (FR-GUEST-009). Removing a deleted user's statistics leaves every
other player's aggregates unchanged (FR-ACCT-008).

---

### IMP-M5-03 — Notifications and the SSE stream

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06, IMP-M1-07

**`IMP-GATE-34` narrowed this item's *Satisfies*** (closed 2026-09-08, session 34, on `IMP-M1-09`):
FR-FREQ-001…006 dropped — this item delivers whatever rows land in `notification` over SSE and
enforces the generic retention/alert rules, but never writes a `friend_request`-linked row itself;
`IMP-M1-09` does, and now carries the claim. FR-FREQ-001…006 stays in this item's read-list: the type
table (`data-model-notifications.md` §3) is still the wire contract the SSE stream serves.

**`IMP-GATE-58` narrowed this item's *Satisfies*** (closed 2026-09-13, session 50, on `IMP-M2-12`):
`FR-LINK-001…002` dropped — double-claimed with `IMP-M2-12`, and neither item builds anything for it;
`IMP-M2-01`'s already-shipped invite-code mechanism is the entire behaviour, and now carries the claim.

**Closed:** IMP-GATE-59 (opened and closed 2026-09-14, session 51) — this item's *Satisfies* claims
FR-NOTIF-001…009 in full (notification center access, unread badge, read/unread state, mark-all-read,
delete, retention, real-time and offline delivery, pagination), but no document in the corpus ever
defined the notification center's REST surface — `sse-notifications.md` specifies only the stream
(`GET /api/notifications/stream`), and `rest-conventions.md`'s Authorization table already assumed
`GET /api/notifications` and `/api/notifications/{id}` exist (the ownership predicate, the
principal-scoped collection rule) without any document ever naming their methods, request/response
shapes, or status codes. `room-invitation-rest-api.md` §6 independently assumed the same endpoint as
where a received `ROOM_INVITATION` is read, confirming the gap is real rather than a document this
item merely hadn't read yet. Same shape as `IMP-GATE-31`/`33`/`35`/`37`/`57`/`58`. This item's own
read-list never named `rest-conventions.md` or `pagination-filtering-sorting.md` either, despite both
supplying conventions the missing surface would have to follow. Fixed: new
[`docs/specs/api-design/notification-rest-api.md`](../specs/api-design/notification-rest-api.md) —
five endpoints (`GET /api/notifications` list, `GET .../unread-count`, `PATCH .../{id}` mark read,
`POST .../read-all`, `DELETE .../{id}`); registered in that directory's `INDEX.md`;
`room-invitation-rest-api.md` §6 and its Related table now cite it instead of a bare requirement ID.
Read-list corrected below.

**Done 2026-09-14 (session 52).** `notification.NotificationController` builds the five
`notification-rest-api.md` endpoints exactly (`GET /api/notifications`, `GET .../unread-count`, `PATCH
.../{id}`, `POST .../read-all`, `DELETE .../{id}`), each scoped by the `rest-conventions.md` ownership
predicate (`WHERE user_id = :principal`, `404` on mismatch) via `NotificationRepository`'s direct SQL
against `notification` — this package's own table, so no cross-schema read is needed the way
`room.RoomInvitationRepository` needed one. `notification.NotificationStreamController` builds `GET
/api/notifications/stream`; `notification.NotificationEmitterRegistry` is the SSE counterpart of
`websocket.WebSocketConnectionRegistry` — same two-index shape (connections by emitter id, a secondary
index by user id), the `sse-notifications.md` § Keepalive comment on a 30s `@Scheduled` tick, and an
`@EventListener` on `session.SessionRevokedEvent` that sends the matching session's stream one final
`event: alert` naming `revoked_reason` and closes it (`FR-SESS-010`, `IMP-GATE-28` — the SSE half
`IMP-M2-02` already closed for STOMP). Offline catch-up (`delivered_at IS NULL`, oldest `event_seq`
first, stamped as sent) is `NotificationRepository#markUndeliveredAsDelivered`. `AlertPublisher`'s real
implementation, `SseAlertPublisher`, replaces `PendingAlertPublisher` (deleted) and routes through the
same registry — `room.RoomInvitationService`'s existing `alertPublisher.publish(...)` call for
`INVITATION_ACCEPTED`/`INVITATION_DECLINED` now actually reaches a connected host with no change on
that side.

**Live push of a newly created notification to an already-open stream is deliberately not built here.**
`room.RoomInvitationRepository` and `social.SocialRepository` write `notification` rows by direct SQL,
with no dispatch call of any kind — unlike alerts, no placeholder port for this existed for them to
call, and this item's own *Done when* clause names only the offline-catch-up path and the
revocation-close behaviour, not a live-push guarantee for an already-connected client. A user who is
already on the stream when another feature writes a row sees it only at their next panel open or badge
refresh (`unread-count`), not pushed instantly — `sse-notifications.md`'s "at-least-once at best... the
notification center is the backstop" reasoning covers exactly this gap, but closing it for existing
producers would mean editing two other already-`DONE` items' repositories, which this item's *Done
when* does not ask for. Left as a scope note rather than a gate: nothing here contradicts another
document or leaves an unmade decision, and the *Done when* clause is satisfiable exactly as written.

**Verified.** `NotificationEmitterRegistryTest` (unit, mocked `SseEmitter` — the
`WebSocketConnectionRegistryTest` pattern): alert routing by user id, silent drop for an offline user,
session-scoped close-with-final-alert on `SessionRevokedEvent`, keepalive. `NotificationControllerIT`
(integration, real Postgres): all five endpoints including ownership `404`s, the guarded one-way
`read_at` transition and its `422` on `{"read":false}`, mark-all-read and delete scoped to the
principal, delete idempotency; the stream test connects with the JDK `HttpClient`, asserts the exact
`event: notification` / `id:` / flattened-payload frame shape `sse-notifications.md`'s wire example
specifies for a row inserted before connecting, and confirms `delivered_at` is stamped.
`./mvnw verify -Pintegration` green locally (162 unit + all integration tests, JaCoCo merged gate met).

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
  FR-FREQ-001…006
- `docs/specs/platform/data-model-notifications.md` §1 (`notification`), §3 (types), **§4 — alerts
  have no table, and three current "notifications" are alerts**
- `docs/specs/api-design/sse-notifications.md` **in full**
- `docs/specs/api-design/notification-rest-api.md` **in full** — the five REST endpoints this item
  builds
- `docs/specs/api-design/rest-conventions.md` § *Authorization and Ownership* — the
  `/api/notifications/{id}` ownership predicate and the principal-scoped collection rule
- `docs/specs/api-design/pagination-filtering-sorting.md` — the envelope and total-ordering rule
  `notification-rest-api.md` §2's list endpoint follows
- `docs/requirements/platform-operations.md` FR-JOB-013, FR-RET-001…006

**Satisfies:** `notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
NFR-PERF-001, NFR-SCALE-001, NFR-SEC-001; `user-accounts.md`
FR-SESS-010; `platform-views.md` VW-NOTIF-001…004

**Done when:** the five `notification-rest-api.md` endpoints exist, each enforcing the
`rest-conventions.md` ownership predicate and returning the exact status codes and bodies that
document specifies; the retention purge is indexed **partially on having no subject**, so it can never
remove an actionable message out from under a live object; and no notification is permanently
unpurgeable because its subject never expires. The SSE connection registry subscribes to
`IMP-M1-06`'s `SessionRevokedEvent`: on receipt, the matching session's stream sends a final `event:
alert` naming `revoked_reason` and then closes — the SSE half of `FR-SESS-010`'s duty (`IMP-GATE-28`),
narrowed out of `IMP-M1-06` because no stream registry existed there to close.

**Persisted notifications and transient alerts are two classes, not one with a flag** (§4). Three
things the requirements call notifications are alerts and must never get a table row — writing them
to `notification` makes them re-deliverable on reconnect, which is the opposite of what a transient
alert is for.

---

### IMP-M5-04 — Retention purge jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01, IMP-M5-03

**Narrowed by IMP-GATE-54** (`IMP-M2-10`, opened and closed 2026-09-13, session 46) — this item's
*Satisfies* claimed the full `FR-JOB-001…013` range verbatim, identical to `IMP-M2-10`'s claim of the
same full range, but this item's read-list touches only the notification/history retention domain:
`FR-JOB-001` (guest cleanup) is `IMP-M1-05`'s, `FR-JOB-006…011` (deadline sweep and room
reconciliation/purge) are `IMP-M2-07`'s/`IMP-M2-10`'s, and `FR-JOB-012` (upload slot sweep) is
`IMP-M4-03`'s — none of those documents appear here. Fixed: narrowed to `FR-JOB-002` (notification
purge, `data-model-notifications.md`) and `FR-JOB-013` (already named explicitly below); `NFR-JOB-001…002`
dropped (both are `IMP-M2-07`'s/`IMP-M2-10`'s recoverability bounds, not a retention-window property).

**Read first:**
- `docs/requirements/platform-operations.md` FR-RET-001…006, FR-JOB-002, FR-JOB-013
- `docs/specs/platform/data-model-history.md` §4 (erasure), `data-model-notifications.md` §1
- `docs/specs/deployment/local-environment.md` §7.2 (job scheduling), §7.3 (retention windows)

**Satisfies:** `platform-operations.md` FR-RET-001…006, FR-JOB-002, FR-JOB-013;
`game-history.md` NFR-HIST-003

**Done when:** every retention window comes from the §7.3 configuration keys and none is hard-coded;
the FR-JOB-013 expiry purge exists, is named, and is the **only** mechanism that ever removes an
actionable notification (IR-20); every job honours the FR-JOB-008 startup suppression **except** the
adopt duty, which IMP-M2-10 exempts; a purge that would remove a row a live object still references
cannot run — the partial index of IMP-M5-03 is the guard, not a code check.

---

## M6 — Platform frontend

**Read first:**
- `docs/decisions/0013-astryx-design-system.md` — **read this before anything else in M6.** The
  component library is Astryx, not ours
- `docs/specs/platform-frontend/design-system.md` — the Astryx integration and the composition ladder
- `docs/specs/platform-frontend/shell-architecture.md` — the application shell
- `docs/requirements/platform-views.md` — every view's contract
- `docs/requirements/platform-ui-library.md` — what the platform needs from the library
- `docs/specs/game-frontend/game-asset-serving.md`, `docs/decisions/0007-game-frontend-separate-domain.md`

**Component lookup is a tool call, not a document.** `npm run astryx -- component <Name>` or the
`astryx` MCP server. Nothing in this corpus lists Astryx's components, deliberately — a copy would be
stale within a release.

`docs/requirements/onboarding-wizard.md` is **not** in this list. IR-23 cut the wizard from v1; the
document is retained as a record of a deferred feature and implements nothing.

### IMP-M6-01 — Astryx integration and the `ui/` boundary

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M0-05

**Closed:** IMP-GATE-68 (opened and closed 2026-09-22) — this item's own Done-when clause 4 requires
`no-raw-color` and `no-raw-spacing` ESLint rules "with no path allow-list," but `design-system.md`
(the item's own read-list, in full) never defined what either rule checks — the pre-Astryx version of
that document did (a table: hex/`rgb()`/`hsl()`/`oklch()` literals in `.css`/`.tsx` for the first,
`px`/`rem` on `padding`/`margin`/`gap`/`inset` for the second, plus a now-obsolete `tokens.css`
allow-list for the first only), but the ADR-0013 rewrite dropped the table entirely without replacing
it, and §9's traceability table mapped the whole `FR-TOK-001…008` range to "Astryx" — wrong for
`FR-TOK-008` specifically, which is about raw values in *our* code, not Astryx's token supply, and is
exactly what the pre-rewrite table enforced. Fixed in `design-system.md`: §5 gained an *Enforcement
(FR-TOK-008)* subsection carrying the two rules forward with no allow-list (dropping the pre-Astryx
`no-raw-font-size`, since typography is now fully Astryx-owned and this item's own Done-when never
names it); §9's traceability table splits `FR-TOK-001…007` (Astryx) from `FR-TOK-008` (ours, §5).
`python3 scripts/check-corpus.py` clean.

**Read first:**
- `docs/decisions/0013-astryx-design-system.md` — why the library is Astryx
- `docs/specs/platform-frontend/design-system.md` **in full** — §2 setup, §3 the composition ladder,
  §4 where our code lives, §5 styling our own code, §6 what remains ours, §7 the CLI
- `docs/requirements/platform-ui-library.md` **in full** — what the platform needs from the library

**Satisfies:** `platform-ui-library.md` FR-TOK-001…006, FR-TOK-008, FR-COMP-001…014,
FR-LYT-001…003, FR-THM-001…002, NFR-DX-001…004, NFR-PERF-001…002, NFR-VER-001

**This item is an integration, not a construction.** IMP-M0-05 already installed and wired Astryx;
what remains is the boundary around our own code and the rules that keep it from drifting.

**Done when:**

1. `src/ui/` exists with `index.ts` as its only legal import path, and **both**
   `no-restricted-imports` rules are in force: deep imports out, and imports from `features/` *into*
   `ui/` out. The second direction matters more — a shared component that reaches into application
   code is a screen with a generic name and it breaks on its second use.
2. `src/ui/` is **empty or near-empty**, and that is the correct end state. Application code imports
   `Button` from `@astryxdesign/core/Button` directly. A pass-through wrapper for every Astryx
   component re-creates the maintenance burden ADR-0013 exists to remove, and puts a stale prop
   signature between the developer and the real documentation.
3. **No parallel token scale exists.** No `--tb-*` custom property is defined anywhere. Every value
   comes from Astryx's `--spacing-*`, `--color-*`, `--radius-*`, `--shadow-*`.
4. `no-raw-color` and `no-raw-spacing` lint rules are enabled with **no path allow-list** — there is
   no token definition file to exempt any more (FR-TOK-008).
5. Any component in `src/ui/` uses CSS Modules and consumes Astryx tokens; `className` overrides on
   Astryx components **append, never substitute**.
6. Every swizzled component (`astryx swizzle`) carries a comment naming what could not be done
   through props. A swizzle is a fork: it stops receiving upstream fixes, including accessibility
   ones, and `astryx upgrade` cannot codemod it.
7. Contrast meets WCAG AA on body text with no exceptions (§6). `theme-neutral` clears this, so the
   check is on anything we compose or swizzle.

**Climb the ladder in order: compose → swizzle → write** (§3). The failure mode this item exists to
prevent is an agent writing a `Button` because it did not think to run
`npm run astryx -- component --list` first.

**`npm run astryx -- init` writes an Astryx component index into `CLAUDE.md`.** Useful — it is how a
low-effort agent discovers components instead of guessing. Run it deliberately and review the diff;
do not let it land unread in a hand-written file.

---

### IMP-M6-02 — Shell, routing and auth tiers

**Repo:** `turnbase-frontend` (the shell, and the nginx template that serves it) and
`turnbase-platform` (the compose service and Helm templates that put the Frontend container on the
platform origin — `IMP-GATE-74`; and the one-field principal change of `IMP-GATE-75`). Branch per
repo; `turnbase-frontend` first, since the platform change pins its image. · **Depends on:** IMP-M6-01

**Closed:** IMP-GATE-75 (opened and closed 2026-09-26, session 75, found writing the tier gate) —
§3's three tiers need to tell a Guest from a Registered user, and `GET /api/auth/session` ("returns
the current principal") was the only source, but no document said what the principal contains and the
shipped `PrincipalResponse` was `{userId, username}` — no tier. The alternatives were parsing the
`guest-` username prefix or an extra `GET /api/users/{username}` per page load. Fixed:
`rest-conventions.md` § Authentication defines the principal body as `{userId, username, kind}`
(`REGISTERED` | `GUEST`, the `app_user.kind` literals) for `register`, `login`, `guest`, `session` and
`complete-registration`; `oauth-rest-api.md` §6 cites it. The platform's `PrincipalResponse` gains
`kind` as part of this item. The same section now also names the `login`/`register` request bodies,
which no document gave and which the shell's forms must match.

**Closed:** IMP-GATE-76 (opened and closed 2026-09-26, session 75, found designing the nginx template
and the login page) — two defects. (1) `local-environment.md` §1 (as `IMP-GATE-74` fixed it) proxied
the whole `/auth/` prefix to the monolith, but `/auth/complete-registration` is a *shell* route that
`oauth-rest-api.md` §4 redirects the browser to; the prefix would send it to the monolith and 404.
Fixed: only `/auth/google` and `/auth/callback` are proxied. (2) `VW-LOGIN-002`/`VW-REG-002` hide the
Google button when the secret is absent, but no document gave the frontend any way to know — a
browser cannot probe a `302`-or-`404` across a navigation. Fixed: `GET /api/auth/providers` →
`{ "google": bool }` (`oauth-rest-api.md` §1/§3), exempted in `user-accounts.md` NFR-SEC-006, Tier 4
in `rate-limiting.md`. The platform half (endpoint, interceptor exemption, rate-limit path) is this
item's.

**Closed:** IMP-GATE-74 (opened and closed 2026-09-26, session 74, found reading this item's
*Done when*) — the item says "the CSP is emitted by the platform origin", but no document said what
serves the shell document at that origin. `local-environment.md` §1 had the monolith answering
`turnbase.localhost:8080` and no Frontend container at all — neither compose nor the Helm chart
deployed `turnbase-frontend`'s image, whose `nginx.conf` already anticipated SPA fallback for this
item. And `frame-src`, which `game-asset-serving.md` §6.3 "owns", was given there only as a literal
local value, though the value is deployment configuration (`turnbase.game-frontend.origin-template`)
that a static bundle cannot know. Fixed: `local-environment.md` §1/§4/§7.7 make the Frontend
container the listener on the platform origin (shell + CSP + reverse proxy to the monolith; every
other `Host` falls through to the monolith); `game-asset-serving.md` §6.3 defines `frame-src` as
derived at container start from the origin template (`{gameId}` → `*`); `shell-architecture.md` §6
names nginx as the emitter and stops restating the directive. The wiring is this item's, below.

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §§1–3 (structure, auth tiers, routing),
  §6 (Content-Security-Policy), §7 (notifications and alerts), §10
- `docs/specs/deployment/local-environment.md` §1 (*Both origins are one listener*), §4, §7.7 — who
  serves the shell, and the two env vars it reads
- `docs/specs/game-frontend/game-asset-serving.md` §6.3 — the one place `frame-src` is specified
- `docs/specs/api-design/rest-conventions.md` § Authentication — `login`, `guest`, `logout`,
  `session` and the `turnbase_session` cookie the tier check rests on
- `docs/specs/api-design/oauth-rest-api.md` — `/auth/google`, `/auth/callback`, and the three
  `/api/auth/oauth/*` endpoints `/auth/complete-registration` calls (VW-OAUTHCOMP)
- `docs/requirements/platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
  VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/api-design/sse-notifications.md`
- `docs/specs/platform-frontend/design-system.md` §2 — the two providers the shell owns
- `docs/specs/api-design/notification-rest-api.md` — `GET /api/notifications/unread-count`, the
  badge the shell refreshes on each pushed notification
- `docs/specs/api-design/error-handling.md` — the `application/problem+json` shape `apiFetch` parses
- `docs/specs/platform/data-model-accounts.md` §1 — `app_user.kind`, the value `IMP-GATE-75` exposes

**Satisfies:** `platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002, NFR-USAB-001…002

**Done when:** (`IMP-GATE-75`) every response carrying the principal — `register`, `login`, `guest`,
`session`, `complete-registration` — includes `kind`, and `GET /api/auth/providers` answers
`{ "google": bool }` unauthenticated, each asserted in `turnbase-platform`; the shell takes its tier
from `kind` and renders the Google buttons only when `google` is `true`; §3's three auth tiers gate every route, and a route's tier is declared with the route
rather than checked inside the view; §6's CSP is emitted by the platform origin **without restating
`frame-src`**, which `game-asset-serving.md` §6.3 owns — two documents specifying one directive is how
they drift; a mid-session 401 follows the VW-REDIR rules rather than blanking the view; the SSE
stream reconnects with backoff and does not duplicate alerts on reconnect. **And (`IMP-GATE-74`)** a
`docker compose up` serves the shell at `http://turnbase.localhost:8080` from the Frontend
container — `/api`, `/ws` (including the upgrade), `/auth/google` and `/auth/callback` reach the monolith through it
(`/auth/complete-registration` is served by the shell — `IMP-GATE-76`), and a
`Host: x.games.localhost` request reaches the monolith's games origin unchanged; the served CSP's
`frame-src` equals `game-asset-serving.md` §6.3's derivation for the configured template, and a
test proves it for both a per-game and a constant (shared-origin) template; the Helm chart gains the
`frontend-*` templates and its Ingress sends `turnbase.localhost` to the Frontend Service.

**Done 2026-09-26 (session 75).** `turnbase-frontend` `9bc005d`, `turnbase-platform` `cdbc78e`, both CI
green. Frontend: `react-router` 8.4.0, `appRoutes` table declaring each route's access kind, `RouteGuard`
(gated elements are removed, never disabled), `safeRedirect`, `AuthProvider` with a 401 listener,
login/register/OAuth-completion pages, the SSE stream (reopens only when the browser gives up —
`readyState` CLOSED — with backoff and jitter, dedupes on `notificationId`), and nginx rendered at
container start with `frame-src` derived from the origin template (`src/deploy/nginx.test.ts` proves
per-game, constant, multi-occurrence and default templates). Platform: `kind` on all five principal
responses, `GET /api/auth/providers` (public, Tier 4), a compose `frontend` service that owns host port
`8080`, Helm `frontend-*` templates with one `origins` values source for both configmaps, e2e smoke
retargeted. Verified against the real stack (compose with the Redis workaround below): shell + SPA
fallback + CSP served for `turnbase.localhost`, `/api` and `/ws` (101 upgrade) proxied,
`/auth/complete-registration` served by the shell, `x.games.localhost` reaching the monolith.
**Not done in this item, on purpose:** the notification centre, the OAuth link-challenge form and every
placeholder page belong to later M6 items.

**The shell mounts `<LinkProvider component={Link}>` inside `<Theme>`, once** (`design-system.md`
§2). Skipping it is the expensive mistake in M6: every Astryx `Link`, and every component that
renders one internally, falls back to a plain `<a href>` and triggers a **full page reload** —
dropping the STOMP connection, the room subscription and all in-memory session state. It fails as a
navigation bug three milestones from where it was introduced.

---

### IMP-M6-03 — Account and profile views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M1-07, IMP-M1-11

**Closed:** IMP-GATE-78 (opened and closed 2026-09-26, session 77) — see `IMP-M1-11`. Settings had no
read route and no auth-method routes; the platform half is now its own item and this one waits on it.
The read-list also lacked `social-rest-api.md` (the Friends views' whole API) and the two `rest-conventions.md`
/ `oauth-rest-api.md` sections above. **Still open, not gated:** the profile page's statistics and game
history tabs need `IMP-M5-01`/`M5-02`'s REST surface, which is not `DONE`; build those tabs against
whatever those items publish, or leave them for the item that does.

**Closed:** IMP-GATE-80 (opened and closed 2026-09-27, session 80) — this item's own *Done when*
requires VW-PROF-002…003 to render for the owner, and VW-PROF-002c ("Profile section — uploaded
games") is in that range, but no document gave the uploaded-games section anything to call:
`catalog-rest-api.md`'s `GET /api/games` had no owner/author filter, its own "what is deliberately
absent" section never named the gap, and `game-catalog.md` FR-UPROF-001…004 (the requirement that
actually specifies this section's behaviour — not `user-accounts.md` FR-PROF-001, which only names
"uploaded games" as one of five profile contents) had no realizing API at all. Fixed: `catalog-rest-api.md`
`GET /api/games` gained an `owner` query parameter that composes with the existing §2 visibility
predicate — the owner-viewing-own-profile case already falls out of that predicate's owner carve-out,
a non-owner viewer sees only that user's listed games, an unknown username yields an empty page rather
than `404` (§3, §6, §7 updated); `game-catalog.md`'s `catalog-rest-api.md` cross-reference updated to
match. FR-UPROF-002's per-game management actions (edit, delist/publish, delete) remain unrealized —
no mutation route exists yet, same pre-existing gap `catalog-rest-api.md` §6 already disclaimed for
FR-GAME-001…013 — so this item's owner view renders the list but not those actions. The read-list below
gained `game-catalog.md` FR-UPROF-001…004, which it should have named from the start.

**Closed:** IMP-GATE-82 (opened and closed 2026-09-27, session 82) — this item's own *Done when* clause
requires rendering every case of `GET /api/users/{username}` (owner, guest, soft-deleted, private
non-owner, `relationshipState`), and `social-rest-api.md` §9, `catalog-rest-api.md` §3 and
`history-rest-api.md` all treat that endpoint as an established contract they extend or reference, but
no `docs/specs/api-design/*.md` document ever specified it — only `IMP-M1-07`'s own (already-`DONE`)
registry prose and unshaped prose requirements in `user-accounts.md` described the response, so this
item had no wire contract to build its views against. Same shape as `IMP-GATE-31/33/35/37/78/80/81`.
Fixed: new `docs/specs/api-design/profile-rest-api.md`, transcribed from the shipped
`account.ProfileResponse`/`ProfileService.view` (`IMP-M1-07`, session 32) rather than inventing a
divergent shape — registered in `api-design/INDEX.md` and cross-referenced from `user-accounts.md`.
This item's read-list below now cites it in place of the prose it was reading around.

**Closed:** IMP-GATE-83 (opened and closed 2026-09-27, session 83) — the Account Settings password
form this item builds (VW-SET-003) posts to `POST /api/users/me/password`, and `rest-conventions.md`'s
own entry for that route names only "the current password and the new one" — FR-ACCT-010's "supplying
their current password and the new password twice" gives a field *count*, not the three field names a
client actually has to send. Every sibling route on that same table is exact (`login`'s
`usernameOrEmail`/`password`, the auth-methods `password`/`confirmPassword` body), so this was the one
gap left in that section. Fixed: `rest-conventions.md`'s password-change row now names the body,
transcribed from the shipped `account.ChangePasswordRequest` (`IMP-M1-08`) rather than inventing field
names that might diverge from it — `{ "currentPassword", "newPassword", "confirmNewPassword" }`.

**Read first:**
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005
- `docs/specs/api-design/profile-rest-api.md` — the `GET /api/users/{username}` envelope every case
  below renders from (`IMP-GATE-82`)
- `docs/specs/api-design/rest-conventions.md` § Authentication — the `/api/users/me` routes and *The
  account representation*: everything Account Settings reads and writes (`IMP-GATE-78`)
- `docs/specs/api-design/oauth-rest-api.md` §7a — the three-request Google link the Add
  authentication method action drives
- `docs/specs/api-design/social-rest-api.md` — the friend list, requests and `relationshipState` the
  Friends and profile views call
- `docs/specs/api-design/catalog-rest-api.md` §3's `owner` filter — the uploaded-games profile section
  (`IMP-GATE-80`)
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010
- `docs/requirements/game-catalog.md` FR-UPROF-001…004 — the uploaded-games section's actual behaviour
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform-frontend/design-system.md` §4 (the component inventory these views compose)

**Satisfies:** `platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005;
`user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010; `game-catalog.md`
FR-UPROF-001, FR-UPROF-003…004; `social-friends.md` FR-SOC-001…021

**Done when:** **the owner sees their own profile in full regardless of every privacy setting they
have set** — private profile, hidden sections and hidden friend list all render for them (IR-05,
FR-PROF-007, VW-PROF-002…003, VW-FREN); a guest profile shows the username and nothing else
(FR-GUEST-010); a soft-deleted user's profile shows the FR-ACCT-009 placeholder; deletion is a
confirmed, explicit action (FR-ACCT-004).

**Done (session 84):** Profile, Friends and Settings pages built and wired at `/users/:username`,
`/friends`, `/settings`; all four *Done when* cases covered by `ProfilePage.test.tsx` and
`SettingsPage.test.tsx`. Also built, beyond the *Done when* clause but within *Satisfies*: friend
request send/accept/decline/remove (`FriendsPage.tsx`), password change and add-password
(`FR-ACCT-010`/`IMP-GATE-83`), auth-method add (Google link, `oauth-rest-api.md` §7a) and remove, and
the four privacy-visibility toggles. **Deliberately deferred:** the profile page's statistics and
game-history tabs render nothing yet — `IMP-M5-01`/`M5-02` are not `DONE` and have no REST surface to
build against, per the still-open note left on `IMP-GATE-78` above; build those tabs when either item
ships. The `GET /api/users?search=` endpoint (`social-rest-api.md`) was not built into any view — no
`VW-*` requirement in this item's *Done when*/*Satisfies* calls for a username-search UI.

**The view is not the access control.** Every rule above is already enforced by IMP-M1-07 server-side;
implementing it here as well is a rendering concern, and implementing it *only* here is a
vulnerability.

---

### IMP-M6-04 — Room views and the STOMP client

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M2-08

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §4 (the WebSocket client) and §8 (the room
  view's one-component-three-states shape and the global reconnection card)
- `docs/specs/api-design/websocket.md` — the base connection this protocol extends: `/ws`, the
  cookie-only `CONNECT` auth with no separate token, and the shared envelope
- `docs/specs/api-design/room-websocket.md` **in full**, and `room-chat-websocket.md`
- `docs/specs/api-design/room-rest-api.md` — the affinity hint and the `503` contract
- `docs/requirements/platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003, VW-RLOBBY-001…007, VW-RLOBBY-009…017,
  VW-RGAME-001…008, VW-RRESULT-001…005
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008

**Satisfies:** `platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003, VW-RLOBBY-001…007, VW-RLOBBY-009…017,
VW-RGAME-001…008, VW-RRESULT-001…005; `game-rooms.md` NFR-PERF-001…002; `in-room-chat.md`
FR-CHAN-001…004, FR-SWITCH-001…002

**Done when:** the client holds a `localVersion` and **discards any delta with
`version <= localVersion`**; resync is snapshot-then-deltas with no merge path; chat frames carry
`version: null` and are excluded from that comparison entirely (IR-08) — comparing them against
`localVersion` discards every chat message after the first room event; the
`X-TurnBase-Room-Instance` hint is honoured when opening the socket; a `503` with `Retry-After` from
a join is retried after the stated delay rather than surfaced as a failure, because it means "not
here yet", not "no".

**Done 2026-09-27 (session 85).** `turnbase-frontend`: `roomSocket.ts` (STOMP client —
`localVersion` assigned, never merged, from `ROOM_STATE`; `reconcileVersion`'s apply/discard/resync
table; a resync discards every delta until the next snapshot rather than reconciling against a
stale version; chat's `/topic/room.{roomId}.chat` and `.team.{teamId}` subscriptions never touch
`reconcileVersion`; `brokerUrl` honours `?instance={hint}`), `roomsApi.ts` (`joinRoom` retries a
`503`+`retryAfterMs` transparently), `roomReducer.ts` and `useRoomConnection.ts` (the event-to-state
reducer and the React hook wiring the two together). 36 unit tests, all *Done when* clauses asserted
directly. `npm run format && lint && typecheck && test && build` green locally and in CI
(`36323893623`). The room list/join/lobby/game/results views (VW-ROOMS/VW-JOIN/VW-RLOBBY/VW-RGAME/
VW-RRESULT, `in-room-chat.md` FR-CHAN/FR-SWITCH) are not built by this item — `registry.md`
INDEX.md's own instruction is to build exactly the *Done when* clause, which names none of them, and
IMP-GATE-84's closing note already established the precedent of deferring a *Satisfies* entry the
backend or a later item has to finish first. Tracked in `STATUS.md` *Next Priorities* as the
remaining work before those requirement IDs are actually satisfied.

**Closed:** IMP-GATE-85 — this item's own *Done when* requires the `X-TurnBase-Room-Instance` hint
to be "honoured when opening the socket", but no document named a mechanism a browser's native
`WebSocket` (which cannot set arbitrary handshake headers) can actually use to carry it, and
`room-websocket.md` §*Routing on join*'s own illustrative "cookie or header" aside never resolved to
one either. Opened and closed 2026-09-27: `room-websocket.md` now names the concrete mechanism — the
client appends the hint as `/ws?instance={podId}`, consumed by an ingress configured for it and
ignored otherwise (`local-environment.md` §3's round-robin ingress, correctly per FR-DEPLOY-002).

**Closed:** IMP-GATE-84 — `shell-architecture.md` §8 requires the `/rooms` reconnection pinned card
(VW-ROOMS-005, FR-REJOIN-002) to be "driven by a field on the rooms list response", but
`room-rest-api.md` §3's `GET /api/rooms` response had no field naming the caller's own held
grace-period reservation, and `reconnection-flow.md` never named the wire mechanism either. Opened
and closed 2026-09-27: added a top-level `reservedSlot` field to the `GET /api/rooms` envelope in
`room-rest-api.md` §3 (sibling to `content`/`pagination`, unaffected by filters, `null` when the
caller holds no live reservation). The backend (`IMP-M2-01`, `IMP-M2-07`, both `DONE`) does not yet
populate it — VW-ROOMS-005 is deferred within this item pending that backend follow-up (tracked
below, not in this item's *Done when*).

---

### IMP-M6-05 — Game iframe host and postMessage relay

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04, IMP-M3-07

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §5 (the trust boundary), §6
- `docs/specs/game-frontend/game-asset-serving.md` §6 (the iframe), §7 (session integration),
  §8, §9
- `docs/specs/gdk-api/frontend-gdk-api.md` §8 (origin validation), §9 (the bootstrap contract),
  §10 (the inbound envelope)
- `docs/decisions/0007-game-frontend-separate-domain.md`
- `docs/specs/api-design/websocket.md` § *Catch-up: the sync flow*, § *Platform-shell relay contract*,
  § *Client→server command catalogue* — the STOMP half of the relay (added session 109; the list
  named no document for the game stream the relay translates)

**Satisfies:** `game-contracts.md` FR-FE-001…006, NFR-SEC-001…004; `platform-views.md`
VW-RGAME-001…008

**Note:** `FR-FEGDK-001…009` (the `TurnBaseClient` library itself) moved to `IMP-M3-12` in
`turnbase-sdk` when IMP-GATE-05 closed 2026-08-22 — this item implements the platform shell's half
of the postMessage boundary, not the client.

**Done when:** the shell validates `event.origin` against the game origin on every inbound message;
the iframe carries the sandbox attributes and CSP of `game-asset-serving.md`; no state is shared with
the game frontend other than by `postMessage` (`CLAUDE.md` AVOID).

**The sandbox is `allow-scripts allow-same-origin`, and dropping the second token breaks everything
silently** (IR-21). With `allow-scripts` alone the iframe gets an opaque origin, every
`event.origin` reads the string `"null"`, and the origin check either fails permanently or gets
"fixed" by comparing against `"null"` — which accepts messages from any sandboxed frame. The
separation ADR-0007 buys comes from the **registrable domain**, not from withholding
`allow-same-origin`.

---

### IMP-M6-06 — Catalog and history views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M4-01, IMP-M5-01

**Closed:** IMP-GATE-81 (opened and closed 2026-09-27, session 81) — this item's own *Satisfies*
claimed `game-history.md` FR-HIST-020…030 (the History tab: cards, search, pagination, empty state,
visibility), but no REST endpoint existed to render it against, this item's *Depends on* never named
`IMP-M5-01` (the platform item that owns `game_history_entry`), and its own *Done when* never tested
any of the range — same shape as `IMP-GATE-80`. Fixed: see `IMP-M5-01`'s closed gate for the new
`history-rest-api.md`. This item's *Depends on* gained `IMP-M5-01`; its read-list gained the new
document; its *Done when* gained the clauses below.

**Read first:**
- `docs/requirements/platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009
- `docs/requirements/game-history.md` FR-HIST-020…030
- `docs/specs/api-design/history-rest-api.md` (`IMP-GATE-81`) — the History tab's data source
- `docs/specs/api-design/input-validation.md` § *Output encoding* — the owner of the Markdown rule
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/specs/api-design/notification-rest-api.md` — the notifications panel (VW-NOTIF); added
  session 107, the list named no document for a range the item claims

**Satisfies:** `platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004;
`game-catalog.md` FR-CAT-001…010, FR-GDET-001…009; `game-history.md` FR-HIST-020…030

**Closed:** IMP-GATE-92 (opened and closed 2026-09-30, session 108) — no document stated the payload of `FRIEND_REQUEST` or how its Accept/Decline reaches a request id; `notification-rest-api.md` §2 now has a *Payload shapes* table and the resolution rule.

**Done when:** game descriptions are parsed from Markdown into **React elements**, client-side, with
no intermediate HTML string anywhere in the path (IR-19); `dangerouslySetInnerHTML` appears nowhere
in the repository and a lint rule enforces its absence — the ban is only worth having if nothing can
quietly re-introduce it; catalog paging uses the shared contract from IMP-M1-01 rather than a
bespoke one; the History tab renders `history-rest-api.md`'s `content` array as cards
(`gameName`/`gameLinkable`/`outcomeLabel`/`completedAt`), each expandable to its `playerStats`/
`teamStats` sections when present and collapsed otherwise (FR-HIST-021…022); an empty `content` array
renders FR-HIST-027's placeholder, not a blank tab; the search input and pagination controls drive
`history-rest-api.md`'s `search`/`page`/`size` query parameters rather than filtering a client-held
page; the notifications panel opens from the bell, lists `notification-rest-api.md`'s `content` without
marking anything read on open, offers Accept / Decline on `ROOM_INVITATION` (join / decline the room invitation)
and `FRIEND_REQUEST` (accept / delete the request, its id resolved from `GET /api/friend-requests`) rows, and
drives mark-read, mark-all-read and dismiss through the PATCH / POST / DELETE endpoints (VW-NOTIF-001…004).

---

### ~~IMP-M6-07 — Onboarding wizard~~ · CANCELLED

**Cancelled by IR-23.** The onboarding wizard is cut from v1.
`docs/requirements/onboarding-wizard.md` is retained as the record of a deferred feature; its
FR-ONB-001…013 and NFR-ONB-001…003 have no implementing item and are not expected to.

The identifier is retired and will not be reused. If the wizard returns, it gets a new number.

---

## M7 — MVP review remediation

Opened 2026-10-01 from the [MVP implementation review](../reviews/2026-10-01-mvp-implementation-review/INDEX.md).
Each item names the finding it closes (`MR-nn`). The review's evidence is a black-box run: the
backend and Game Host passed, the frontend's room views did not exist.

---

### IMP-M7-01 — Room list and join views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003
- `docs/specs/platform-frontend/shell-architecture.md` §8
- `docs/specs/api-design/room-rest-api.md` — `GET /api/rooms`, join, `reservedSlot`
- `docs/specs/platform-frontend/design-system.md`

**Satisfies:** `platform-views.md` VW-ROOMS-001…004, VW-JOIN-001…003 (VW-ROOMS-005 needs `IMP-M7-07`)

**Done when:** `/rooms` and `/rooms/join/:code` replace their `later(...)` placeholders in
`routes.tsx`; the list renders `GET /api/rooms` with filter, sort and refresh, and Join calls
`joinRoom` (which already retries a `503`); the join page shows the Player/Spectator prompt only when
both roles are open and an error message for an invalid code, a vanished room or no available role;
a successful join navigates to `/rooms/:id`; registration lands on a working `/rooms`.

---

### IMP-M7-02 — Room lobby view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-01 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017
- `docs/specs/platform-frontend/shell-architecture.md` §4, §8 (one component, three states)
- `docs/specs/api-design/room-websocket.md` in full
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008

**Satisfies:** `platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017; `reconnection-flow.md`
FR-REJOIN-001…008 (the global reconnection card)

**Done when:** `/rooms/:id` mounts the room component on `useRoomConnection`; the lobby shows the
player list with readiness, the read-only parameters panel, Toggle Readiness for non-host players,
Start for the host only (enabled by the platform's own readiness rule, not recomputed), invite code,
and the host's Kick and Transfer Host; a refresh of the page rejoins the room from a `ROOM_STATE`
snapshot; a dropped socket shows the reconnection card and resyncs without a stale-delta replay.

---

### IMP-M7-03 — In-game and results views, game iframe mount

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-02, IMP-M6-05 · **Closes:** MR-01 (part), MR-09

**Read first:**
- `docs/requirements/platform-views.md` VW-RGAME-001…005, VW-RRESULT-001…005
- `docs/specs/game-frontend/game-asset-serving.md` §6, §7
- `docs/specs/platform-frontend/shell-architecture.md` §5
- `docs/specs/api-design/websocket.md` § *Platform-shell relay contract*

**Satisfies:** `platform-views.md` VW-RGAME-001…005, VW-RRESULT-001…005

**Done when:** on `GAME_STARTED` the room view mounts the existing `GameFrame` at the payload's
`gameFrontendUrl`, and the shell relays the game stream both ways with origin validation; the game
frontend actually loads from `http://{gameId}.games.<host>` (the review saw `404 problem+json` at `/`,
MR-09 — either the path the platform hands out resolves or the asset route is fixed); the participant
status panel, Leave, and the host's Kick and Transfer Host are present; on `GAME_OVER` the results
view keeps the iframe and offers Return to Lobby and Leave; two browser contexts can play Tic-Tac-Toe
to a win through the UI alone.

---

### IMP-M7-04 — Room chat panel

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-02 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/in-room-chat.md` FR-CHAN-001…004, FR-SWITCH-001…002
- `docs/requirements/platform-views.md` VW-RGAME-006…008
- `docs/specs/api-design/room-chat-websocket.md`

**Satisfies:** `in-room-chat.md` FR-CHAN-001…004, FR-SWITCH-001…002; `platform-views.md` VW-RGAME-006…008

**Done when:** players see a unified room log and a team tab only when the game declares teams; the
write-channel switcher is shown only to players with both channels; chat frames carry `version: null`
and never touch the room's `localVersion` (IR-08); spectators have no chat panel and a spectator's
send is refused by the server, not merely hidden; the chat log is client-held only (FR-CHAN-003).

---

### IMP-M7-05 — Close rooms abandoned in the Lobby

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-08 · **Closes:** MR-02

**Read first:**
- `docs/requirements/game-rooms.md` FR-XFER-001…003, FR-LIFE-004, FR-LIFE-007
- `docs/specs/platform/room-lifecycle.md`
- `docs/specs/flows/05-owner-loss-and-adoption.md`, `docs/specs/flows/07-room-closure.md`
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-02

**Satisfies:** `game-rooms.md` FR-XFER-002, FR-XFER-003

**Done when:** a Lobby room whose last human loses their socket, or leaves implicitly by creating or
joining another room, is closed at once and disappears from `GET /api/rooms` and from
`GET /api/rooms/{id}` (404), exactly as an explicit `DELETE …/participants/me` already does; when other
humans remain, host transfer happens instead (FR-XFER-001); an integration test reproduces the
review's three paths (socket loss, implicit release, explicit leave) and asserts no listed room has
`playerCount` 0. The 30-minute idle sweep is unchanged and remains the backstop.


**Follow-up (2026-10-03):** the review found rooms emptied by concurrent leaves, or around a game end, still listed — `IMP-M8-04`.
---

### IMP-M7-06 — Leaving mid-game reaches the engine

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-09 · **Closes:** MR-03

**Read first:**
- `docs/requirements/game-rooms.md` FR-LIFE-004
- `docs/requirements/reconnection-flow.md` FR-EXPIRY-002 and § *Game engine response set*
- `docs/requirements/per-game-statistics.md` FR-STATS-001
- `docs/specs/flows/04-disconnect-and-return.md`, `docs/specs/flows/06-game-end-and-rematch.md`
- `docs/specs/gdk-api/backend-gdk-api.md` — the "player lost" event and the response set
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-03

**Satisfies:** `reconnection-flow.md` FR-EXPIRY-002; `per-game-statistics.md` FR-STATS-001 (forfeit)

**Done when:** an explicit `DELETE /api/rooms/{id}/participants/me` by a player during `IN_PROGRESS`
delivers the same "player lost" event to the engine that grace-period expiry does; for Tic-Tac-Toe the
opponent receives `GAME_OVER` (forfeit) and the room returns to LOBBY with a `GAME_ENDED`; a forfeit
session is counted in statistics and written to history; a spectator leaving changes nothing in the
session. If the requirements do not say what an explicit leave must do, stop and open a gate with
`spec-defect` — do not choose. An integration test reproduces the review's run (leave with a socket
open, game not stuck).


**Follow-up (2026-10-03):** the clause "a forfeit session is … written to history" was not met: the history service rejects the outcome (`playerResults names a non-participant`) — `IMP-M8-03`.
---

### IMP-M7-07 — Populate `reservedSlot` on the rooms list

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07 · **Closes:** the deferral recorded in `IMP-M6-04`

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §3 (the `reservedSlot` field)
- `docs/requirements/reconnection-flow.md` FR-REJOIN-002
- `docs/requirements/platform-views.md` VW-ROOMS-005

**Satisfies:** `platform-views.md` VW-ROOMS-005 (backend half), `reconnection-flow.md` FR-REJOIN-002

**Done when:** `GET /api/rooms` returns `reservedSlot` populated for a caller who holds a live
grace-period reservation and `null` otherwise, unaffected by filters; `IMP-M7-01`'s list shows the
pinned reconnection card from it.

---

### IMP-M7-08 — Tic-Tac-Toe rejects a malformed action

**Repo:** `turnbase-game-tictactoe` · **Depends on:** IMP-M3-10 · **Closes:** MR-04

**Read first:**
- `turnbase-game-tictactoe/src/main/java/io/turnbase/games/tictactoe/Move.java`, `TicTacToeGame.java`
- `docs/specs/gdk-api/backend-gdk-api.md` — the action-rejection contract

**Done when:** `Move.cell` is nullable (`Integer`) and an action with no `cell`, a non-integer `cell`
or an unparsable payload yields a rejection (`That cell is not available.` or a dedicated message)
to the sender only, with no state change and no turn consumed; a unit test covers `{}`, `null`,
`"x"` and a valid move; the game remains a model for third-party authors.

---

### IMP-M7-09 — Game Host warm-up before readiness

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-10 · **Closes:** MR-05

**Read first:**
- `docs/specs/game-host/game-host-internals.md`
- `docs/decisions/0005-game-sandbox-espresso-spike.md` (startup NFRs deferred post-MVP) — what is and is not owed
- `docs/specs/deployment/observability.md`

**Done when:** before the Game Host reports readiness it runs a synthetic session against an
embedded trivial game so the first real `START_GAME` no longer pays the Truffle warm-up; the measured
cold `START_GAME → GAME_STARTED` on a freshly booted stack is recorded in the item's section and is
within the same order as warm (target < 1 s; if not reachable, record the figure and the reason);
the synthetic session never appears in history, statistics or the active-session gauge.

**Measured (session 123, compose stack, GraalVM CE 21.0.2):** cold `START_GAME → GAME_STARTED` fell from
6 465 ms (review, MR-05) to **4 163 ms**; warm is 39 ms. The < 1 s target is **not reached**: the remaining
cost is the per-context Espresso boot (a guest JVM per context, ~13 s on the unit-test classpath), which a
throwaway context cannot pre-pay and a shared `Engine` did not reduce. Closing it needs a pre-booted pool of
game contexts, which is a post-MVP design (ADR-0005 defers the startup NFRs). The warm-up context is outside
`GameContextManager`/Redis, so it is invisible to history, statistics and the `active_sessions` signal.

---

### IMP-M7-10 — Lifecycle logging for rooms, auth and sessions

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M3-10 · **Closes:** MR-06

**Read first:**
- `docs/specs/deployment/observability.md` (logging section)
- `docs/specs/api-design/websocket.md` (connect, disconnect)

**Done when:** structured INFO lines with `roomId`, `userId` (and `sessionId` where one exists) are
emitted for: registration, login and guest creation, room create / join / leave / close (with the
close reason), game start and end (with outcome), socket connect / disconnect and the grace-period
open / expiry / reconnect; the Game Host logs context create / release and `Deregister`; no credential,
session token or chat text is logged; a reviewer can reconstruct the review's game from Loki alone.

---

### IMP-M7-11 — Anonymous session probe, cookie flag, scheduler bean

**Repo:** `turnbase-platform`, `turnbase-frontend` · **Depends on:** IMP-M6-02 · **Closes:** MR-07, MR-08, MR-10

**Read first:**
- `docs/specs/api-design/rest-conventions.md`, `docs/specs/platform/` auth and session specs
- `docs/specs/deployment/secrets-and-configuration.md`
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-07, MR-08, MR-10

**Done when:** an anonymous load of any page produces no console error (the session probe answers
without a 401, or the 401 is the documented contract and the client handles it silently — record
which in the spec); `turnbase_session` is `Secure` only when the configuration says the deployment is
HTTPS, so the local HTTP stack works in browsers that do not treat `localhost` as secure;
the "more than one TaskScheduler bean" WARN no longer appears at start-up (the intended scheduler is
named or `@Primary`); password inputs carry `autocomplete` attributes.

---

### IMP-M7-12 — Local stack first-run path

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-05 · **Closes:** MR-11

**Read first:**
- `docs/specs/deployment/local-environment.md`, `docs/specs/deployment/secrets-and-configuration.md`
- `turnbase-platform/deploy/compose/`

**Done when:** `deploy/compose/.env.example` lists every required variable with a dummy value; a `make`
target (or a documented command) copies it when no `.env` exists and fails fast naming any missing
variable; `local-environment.md` states that a changed database password needs `down -v`; a cold clone
reaches a healthy stack and a listed Tic-Tac-Toe following only that document.

**Closed:** IMP-GATE-94 (opened and closed 2026-10-03, session 126) — `secrets-and-configuration.md` §2 said `.env.example` holds no values while this clause requires dummy ones; §2 now says every required variable carries a labelled local-only dummy, and that `make env`/`check-env` exist.

---

### IMP-M7-13 — MVP browser acceptance suite

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-03, IMP-M7-05, IMP-M7-06

**Read first:**
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` — the scenarios run by hand
- `turnbase-game-tictactoe/scripts/e2e-roundtrip.mjs`
- `docs/implementation/conventions.md` (test layout)

**Done when:** a Playwright suite runs against the compose stack with **separate browser contexts**
for each player and covers, through the UI where a view exists: register and guest login; create,
join, ready, start; a full Tic-Tac-Toe game to a win; history and statistics for the registered
player; spectator can watch and cannot act; an outsider receives nothing from the room and game
topics; a mid-game socket drop and resume; a leave mid-game ending in a forfeit; a Lobby abandoned
by its host disappearing from the list; a foreign `Origin` refused on REST and on the WebSocket upgrade.
The review's *Not covered* list (grace-period expiry, rate-limit flood, friends / notifications /
profile pages, 400 px layout, concurrent games) is either covered here or recorded as an explicit
follow-up. The suite is wired into CI or a documented `make` target.

**Follow-ups (recorded, not owed by this item):** the suite is `npm run e2e`, run by hand against the compose stack (`make reset-db` between runs; documented in `turnbase-frontend/CLAUDE.md`) — no CI job, it needs the full stack. Not covered, by choice: grace-period expiry, rate-limit flood, friends / notifications / profile pages, 400 px layout, concurrent games; the create-room view exposes neither visibility nor spectating (FR-CREATE-001/002), so the suite makes spectating rooms over REST. The forfeit scenario asserts the opponent is told and can return to the lobby but not the history row — whether a leave-forfeit emits `game_over` (FR-HIST) is unsettled. Found while running it: `GET /api/users/{username}/friends` throws `BadSqlGrammarException` (500) in the platform log. The client does not retry a `SUBSCRIBE`/`REQUEST_GAME_SYNC` dropped by Tier 6, so a game started on an empty bucket renders no board.


**Follow-up (2026-10-03):** the uncovered areas and the known defects above are owned by `IMP-M8-01…16`; the suite is extended by `IMP-M8-16`.
---

## M8 — Regression review remediation and MVP view completeness

Opened 2026-10-03 from the [MVP regression review](../reviews/2026-10-03-mvp-regression-review/INDEX.md)
(`RR-01…RR-10`). Two kinds of item: `IMP-M8-01…05` close the backend and game findings; `IMP-M8-06…14`
give **every view the MVP ships a minimal, working UI** — one item per view, the game room being
`IMP-M8-10` — and `IMP-M8-15…16` close the client-side follow-up and re-run the review as a suite.

**Why a view item exists for views that are already "done".** The first review found views missing;
the second found views that exist and return `500` (Profile, Settings, Friends) or lack a control the
requirements list (create-room options). `IMP-M6-03/04/06` and `IMP-M7-01…04` were closed against their
narrow *Done when* clauses, and none walked the `VW-*` tables row by row. The review did not audit rows
individually either, so no document says which rows fail today. Each view item therefore starts with
that walk and records its failures as a checklist in its own *Remaining* line before fixing them.

**View standard — applies to every `IMP-M8-06…14`.** "Minimal working" means:

1. For each `VW-*` row of the view and each tier the row names, the element is present or absent exactly
   as the table says; an element a tier may not use is **hidden, not disabled** (NFR-USAB-001).
2. Every action the view offers succeeds against the compose stack: no `4xx`/`5xx` except the ones the
   view means to show, and no console error or warning on load or during the flow.
3. Loading, empty and error states each render something a user can act on; none is a spinner or the
   word "Loading…" that never resolves.
4. At 400 px wide the page does not scroll horizontally, and no control overlaps another.
5. Every control is reachable by keyboard and has an accessible name.
6. Astryx components only, layout styling only — nothing the `VW-*` rows do not list. Minimal means no
   polish work, not a partial feature.
7. One Playwright spec per view in `turnbase-frontend/e2e/` that exercises the rows, as a seeded user
   and — where the view has one — a Guest and an Unauth visitor. Specs use the seeded users; at most
   one registration per run (the address limit is 5 an hour, RR-10).

---

### IMP-M8-01 — Seeded users get their privacy settings

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07, IMP-M3-10 · **Closes:** RR-01

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-01
- `docs/specs/platform/data-model-accounts.md` §4 (`user_privacy_settings`: "one always exists")
- `docs/specs/deployment/local-environment.md` §6, §7 (the `local` seeder)
- `docs/specs/api-design/profile-rest-api.md`

**Satisfies:** `user-accounts.md` privacy-settings requirements as listed in `profile-rest-api.md`

**Done when:** after a clean `make up`, `GET /api/users/me` and `GET /api/users/{name}` return `200` for
each of `alice`, `bob`, `carol`, `dave`, as themselves and as one another; the seeder (not a lazy read)
writes the row; a repository-level test asserts every seeded registered user has exactly one
`user_privacy_settings` row; a missing row for a live registered user is an invariant violation that
the `500` message already names — an integration test over real PostgreSQL covers both the seeded path
and a user registered through the API. If §4's "always exists" and the seeder's design disagree about
who creates the row, stop and open a gate with `spec-defect`.

---

### IMP-M8-02 — The friends list query runs on PostgreSQL

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-09 · **Closes:** RR-02

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-02
- `docs/specs/api-design/social-rest-api.md` — `GET /api/users/{username}/friends`
- `docs/specs/platform/data-model-social.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `social-friends.md` friend-list requirements as listed in `social-rest-api.md`

**Done when:** `GET /api/users/{username}/friends` returns `200` with its page and sort order for a user
with no friends, one friend and more than one page of friends; the `ORDER BY` no longer refers to an
output alias inside an expression (`BadSqlGrammarException`, PostgreSQL error `column "friend_username"
does not exist`); the integration test runs against real PostgreSQL, not a mock, and fails on the
current query. Every other hand-written `ORDER BY`/`GROUP BY` in `JdbcClient` repositories is checked
for the same pattern and the result is recorded in the item's *Closed* line.

**Closed:** session 131 — `SocialRepository.listFriends` now sorts an outer select by `lower(friend_username), friend_id`; `SocialControllerIT` covers none/one/two-page lists on real PostgreSQL and failed on the old query with `column "friend_username" does not exist`. Every other hand-written `ORDER BY`/`GROUP BY` in `JdbcClient` repositories (admin, history, catalog, account, notification, room) was checked: they sort by table-qualified columns or bare aliases, never an alias inside an expression — no further defect.

---

### IMP-M8-03 — A forfeit and a timeout are recorded

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01, IMP-M7-06 · **Closes:** RR-03

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-03
- `docs/requirements/game-history.md` FR-HIST-001…003
- `docs/requirements/per-game-statistics.md` FR-STATS-001
- `docs/requirements/reconnection-flow.md` FR-EXPIRY-002
- `docs/specs/flows/06-game-end-and-rematch.md`, `docs/specs/api-design/history-rest-api.md`
- `docs/implementation/registry.md` IMP-M7-06 *Done when* — its last-but-one clause

**Satisfies:** `game-history.md` FR-HIST-001…003; `per-game-statistics.md` FR-STATS-001 (forfeit)

**Done when:** after an explicit leave during `IN_PROGRESS` **and** after grace-period expiry, the
platform writes one history entry for each registered player of the session (the leaver's *Defeat*, the
opponent's *Victory*) and counts the session in both players' statistics; the log line `Invalid game
outcome … playerResults names a non-participant` and `turnbase_history_invalid_outcome_total` stay at
zero for a legitimate forfeit — the outcome's players are validated against the **session's** player
list, not the room's current members; an integration test covers both paths and reads the history API
afterwards. `IMP-M7-06` carried this clause and was closed without it. **FR-HIST-001 says history is
written only when the engine emits `game_over`**: if a forfeit's `game_over` and FR-HIST-001's wording
disagree, stop and open a gate with `spec-defect` rather than choose.

---

### IMP-M8-04 — Rooms emptied around a game end are closed

**Repo:** `turnbase-platform` · **Depends on:** IMP-M7-05, IMP-M2-09 · **Closes:** RR-04

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-04
- `docs/requirements/game-rooms.md` FR-XFER-001…003, FR-LIFE-004, FR-LIFE-007
- `docs/requirements/reconnection-flow.md` FR-DC-002, FR-DC-005, FR-EXPIRY-001…002
- `docs/specs/platform/room-lifecycle.md`, `docs/specs/flows/05-owner-loss-and-adoption.md`, `docs/specs/flows/07-room-closure.md`
- `docs/implementation/registry.md` IMP-M7-05

**Satisfies:** `game-rooms.md` FR-XFER-002, FR-XFER-003

**Done when:** (a) when every member of a room leaves within one scheduling instant — three sockets
closing 30 ms apart after `GAME_ENDED`, or two contexts closed together — the room is closed and absent
from `GET /api/rooms`, with host transfer taking place only while a human remains; the leaves are
serialised per room, not raced; (b) a room that returns to `LOBBY` after a grace expiry whose last member
is already gone is closed in the same step; (c) the grace period for two simultaneously disconnected
players is the configured 60 s — the review measured 11 s against 61 s for one player; either the
requirements define a shorter rule for that case and the item records it, or it is fixed; (d) an
integration test reproduces `09203c03` and `fe4d83bc` and asserts no listed room has `playerCount` 0
afterwards. The 30-minute idle sweep stays as the backstop and is **not** what closes these.

**Outcome (session 133):** (a) closure now keys on "the departing player left no human behind", not "the departing user was the host" — with serialised leaves the host goes first and the last one out is an ordinary player; (b) `detachSession` to `LOBBY` resolves outstanding reservations (`FR-EXPIRY-006`) and closes the room if no human remains, `ROOM_CLOSED` instead of `GAME_ENDED`; (c) **not reproduced** — each disconnect opens its own full 60 s reservation (asserted for two simultaneous drops); the review's 11 s is consistent with the second player dropping ~49 s after the first (`HOST_TRANSFERRED` shows the second was still connected at the first drop). Known simplification: if the host was among the resolved reservations and humans remain, `host_user_id` is left on the departed host as the existing "no host" state.

---

### IMP-M8-05 — Tic-Tac-Toe takes only an integer `cell`

**Repo:** `turnbase-game-tictactoe` (and `turnbase-sdk` if the mapper lives there) · **Depends on:** IMP-M7-08 · **Closes:** RR-09

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-09
- `docs/requirements/game-contracts.md` (action payloads)
- `docs/specs/gdk-api/backend-gdk-api.md` (how an action payload reaches the game)
- `turnbase-game-tictactoe/src/main/java/.../Move.java`, `TicTacToeGame.java`

**Satisfies:** `game-contracts.md` input-validation requirements

**Done when:** `SUBMIT_ACTION` with `{cell:"4"}` is `rejected` like `{cell:null}`, `-1`, `1.5` and `99`
already are; a unit test per malformed shape; if the mapper is the SDK's, the fix is made there, the
SDK's version is bumped under `conventions.md` §5 and the game consumes it.

---

### IMP-M8-06 — Shell, navigation, landing and redirects

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-11 · **Closes:** RR-07 (header)

**Read first:**
- `docs/requirements/platform-views.md` — *Navigation Bar* (VW-NAV-001…012), *Landing Page* (VW-LAND-*), *Redirect & Fallback Behavior* (VW-REDIR-*), NFR-SEC-001, NFR-USAB-001…002
- `docs/specs/platform-frontend/shell-architecture.md`, `docs/specs/platform-frontend/design-system.md`
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-07

**Satisfies:** `platform-views.md` VW-NAV-001…012, VW-LAND-001…, VW-REDIR-001…, NFR-SEC-001, NFR-USAB-001…002

**Done when:** the *View standard* holds for the nav bar, the user menu, the landing page, the 403 view,
the 404 view and every redirect row, for Unauth, Guest and Registered; the header at 400 px collapses
(menu or wrap) so that **Rooms**, **Notifications** and its count badge do not overlap, which is the
defect the review saw; the `redirect` parameter rejects an external URL; a Guest following a
Registered-only link sees the explanatory message of NFR-USAB-002.

**Closed:** session 135 — the walk found the rows already present for all three tiers (`App.test.tsx` covers them); the one defect was RR-07's header. `NavBar` now moves the links (and, signed out, the three calls to action) to a wrapping second row at ≤ 640 px. `e2e/shell.spec.ts` covers Unauth, Guest and `alice` (nav rows, user menu, 403 text, `//evil` redirect, 404, no overlap/page scroll at 400 px). The `/rooms` table's horizontal scroll is `IMP-M8-09`'s, `/games` is `IMP-M8-08`'s.

---

### IMP-M8-07 — Login, registration and OAuth completion views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-06 · **Closes:** RR-10

**Read first:**
- `docs/requirements/platform-views.md` — *Login* (VW-LOGIN-*), *Register* (VW-REG-*), *OAuth Completion* (VW-OAUTHCOMP-*)
- `docs/specs/api-design/rate-limiting.md` (the `429` and `Retry-After`)
- `docs/specs/api-design/error-handling.md`, `docs/specs/api-design/input-validation.md`
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-10

**Satisfies:** `platform-views.md` VW-LOGIN-001…, VW-REG-001…, VW-OAUTHCOMP-001…

**Done when:** the *View standard* holds for `/login`, `/register`, `/auth/complete-registration` and
the *Play as Guest* action; every server field error appears next to its field; a `429` shows the wait
from `Retry-After` ("try again in 14 minutes"), not "a moment"; the OAuth button is hidden — not
disabled — when the provider is not configured, and the completion view is exercised with the stubbed
provider if the stack has one, otherwise the item records that it cannot be and why.

---

### IMP-M8-08 — Catalog, game detail and create-room options

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-06 · **Closes:** RR-06

**Read first:**
- `docs/requirements/platform-views.md` — *Game Catalog* (VW-CAT-*), *Game Detail* (VW-GDET-*)
- `docs/requirements/game-rooms.md` FR-CREATE-001…004, FR-LIST-006
- `docs/specs/api-design/catalog-rest-api.md`, `docs/specs/api-design/room-rest-api.md` (`POST /api/rooms`)
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-06

**Satisfies:** `platform-views.md` VW-CAT-001…, VW-GDET-001…; `game-rooms.md` FR-CREATE-001, FR-CREATE-002

**Done when:** the *View standard* holds for `/games` and `/games/:id`; **Create room** opens a choice of
visibility (Public, Friends Only, Invite Only) and — only when the game `supportsSpectators` — whether
spectating is allowed, then posts exactly that to `POST /api/rooms`; Friends Only is not offered to a
Guest (FR-LIST-006 / FR-GUEST-007); the e2e support no longer creates spectating rooms over REST and a
spec makes one through the dialog and enters it as a spectator.

**Closed:** session 137 — `CreateRoomButton` opens a dialog: visibility (Public default, Friends Only omitted for a Guest, Invite Only) and an *Allow spectators* switch shown only when `supportsSpectators`; `spectatingEnabled` is posted only then. The `/games` filter row now wraps, so 400 px no longer scrolls the page (RR-07). `e2e/catalog.spec.ts` covers Unauth, Guest and `alice`; `support.createRoom({spectating})` goes through the dialog, no REST.

---

### IMP-M8-09 — Rooms list and join views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-01, IMP-M7-07 · **Closes:** RR-07 (rooms table)

**Read first:**
- `docs/requirements/platform-views.md` — *Active Rooms* (VW-ROOMS-001…005), *Join* (VW-JOIN-001…003)
- `docs/requirements/game-rooms.md` FR-LIST-001…007, FR-JOIN-001…007
- `docs/requirements/reconnection-flow.md` FR-REJOIN-002
- `docs/specs/api-design/room-rest-api.md`

**Satisfies:** `platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003

**Done when:** the *View standard* holds for `/rooms` and `/rooms/join/:code`; the table at 400 px
becomes a stacked list or scrolls inside its own container (the page scrolled 154 px sideways in the
review); the pinned reconnection card appears for a caller holding a grace-period slot and goes away when
it is released, shown by a spec that drops a player mid-game; Friends Only rooms are absent for a Guest;
Join and Spectate are each present only when that role is open; a full-room code and a code that
resolves to nothing each show their own reason (VW-JOIN-003). *Corrected session 138:* the clause
said invalid, expired and full each differ, but `room-rest-api.md` §3.1 returns one empty list for a
wrong, expired and closed code on purpose (no oracle, NFR-SEC-002), so the client can name only
"not valid, expired or closed" as one reason.

---

### IMP-M8-10 — The game room: lobby, in-game and results

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-03, IMP-M7-04, IMP-M8-04, IMP-M8-17 · **Closes:** RR-05, RR-08, RR-07 (room at 400 px)

**Read first:**
- `docs/requirements/platform-views.md` — *Room Lobby* (VW-RLOBBY-001…017), *Room In-Game* (VW-RGAME-001…008), *Room Results* (VW-RRESULT-001…005), *Join* (VW-JOIN-001…003)
- `docs/specs/platform-frontend/shell-architecture.md` §4, §5, §8
- `docs/specs/api-design/room-websocket.md`, `docs/specs/api-design/room-chat-websocket.md`
- `docs/requirements/game-rooms.md` FR-XFER-*, FR-JOIN-*, `docs/requirements/reconnection-flow.md` FR-REJOIN-*
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-05, RR-08
- `docs/specs/api-design/room-rest-api.md` §4 (`viewerRole`)

**Satisfies:** `platform-views.md` VW-RLOBBY-001…017, VW-RGAME-001…008, VW-RRESULT-001…005

**Done when:** the *View standard* holds for `/rooms/:id` in each of its states — **lobby, in-game and
results** — and for each role: host, non-host player, spectator, and a non-member. **Known (session 138):** a full page reload
of `/rooms/:id` mid-game showed the Lobby view for the reconnecting player and left their grace-period
slot held — cover it in the *refresh rejoins from a snapshot* spec. **First step:** the
review found that opening `/rooms/:id` as a non-member enrols the visitor (as a player in a public room,
as a spectator when a room has no seat) with no prompt, while VW-JOIN-002 asks for a Player / Spectator
choice before joining; `platform-views.md` writes that for the join-by-code route only. Decide in the
spec which route may enrol (`spec-defect`), then build it: a visit that is not a deliberate join does not
take a seat. Then: *Start game* is disabled — not merely refused by the server — until the platform's
readiness rule holds, and the reason is shown; host actions (Kick, Transfer host, Start) are absent for
everyone else; a spectator sees the board, the participant panel and *Switch to player* where allowed,
and no chat box; the *Team* chat tab appears only when the game declares teams (it showed in a two-player
Tic-Tac-Toe room); the results view keeps the board and offers *Return to lobby* and *Leave*; the lobby,
the in-game view and the results view at 400 px keep the board inside the viewport and the controls
reachable; a refresh in each state rejoins from a snapshot. Specs: four contexts (host, player,
spectator, outsider) through lobby → game → results, plus a drop-and-resume and a forfeit.

**Built (session 141):** entry prompt for non-members (`viewerRole`), Start disabled with reasons, Switch gated on a free slot, team chat only when a team holds more than one player (`in-room-chat.md` FR-CHAN-002 now says so), 400 px wrapping, `e2e/room.spec.ts`. The mid-game refresh defect was the platform: `ROOM_STATE` always sent `gameFrontendUrl: null` — fixed in `turnbase-platform`. A refresh by a spectator, or in the Lobby, is a disconnect-leave (FR-DC-002/003) and returns through the prompt by design.

**Closed:** IMP-GATE-95 (opened and closed 2026-10-03, session 139) — the *First step* above. Only `/rooms/join/:code` enrols on arrival; `/rooms/:id` re-enters a member and otherwise shows the Player / Spectator prompt, enrolling on a button press (`platform-views.md` *Room — Lobby*, Entry; `shell-architecture.md` §8). The client cannot tell a member from a visitor today, so the room resource gains `viewerRole` (`room-rest-api.md` §4) — built by `IMP-M8-17`, which this item now depends on. What remains for this item is the rest of its *Done when*, starting at *Start game* disabled with a reason.

---

### IMP-M8-11 — Profile view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01, IMP-M8-03, IMP-M6-03 · **Closes:** RR-01 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Profile* (VW-PROF-001…), including *The owner is exempt from their own privacy settings*
- `docs/specs/api-design/profile-rest-api.md`, `docs/specs/api-design/history-rest-api.md`, `docs/specs/api-design/statistics-rest-api.md`
- `docs/requirements/game-history.md`, `docs/requirements/per-game-statistics.md`

**Satisfies:** `platform-views.md` VW-PROF-001…

**Done when:** the *View standard* holds for `/users/:username` for the owner, another registered user, a
Guest and an Unauth visitor, over a public and a private profile; the history tab shows a forfeit as
*Victory*/*Defeat* (needs `IMP-M8-03`); statistics show the totals the API returns; an error response
renders a message with a retry, never an unresolved state; the owner sees Edit Profile (VW-PROF-008).

---

### IMP-M8-12 — Friends view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-02, IMP-M8-14 · **Closes:** RR-02 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Friends* (VW-FREN-001…)
- `docs/requirements/social-friends.md`
- `docs/specs/api-design/social-rest-api.md`, `docs/specs/api-design/notification-rest-api.md`

**Satisfies:** `platform-views.md` VW-FREN-001…

**Done when:** the *View standard* holds for `/friends` as a Registered user, and a Guest and an Unauth
visitor are sent where VW-REDIR says; the friend list, send request, incoming and outgoing requests,
accept, decline, remove and block (whichever VW-FREN rows exist) each work end to end between two
contexts, and the receiver's bell shows the request live; a failed action reports **which** action
failed, not "Could not complete that action" twice on load (the review saw two such toasts on every
visit).

---

### IMP-M8-13 — Account settings view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01, IMP-M6-03 · **Closes:** RR-01 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Account Settings* (VW-SET-001…)
- `docs/requirements/user-accounts.md` (username change, password change, privacy, deletion as listed)
- `docs/specs/api-design/profile-rest-api.md`, `docs/specs/api-design/input-validation.md`

**Satisfies:** `platform-views.md` VW-SET-001…

**Done when:** the *View standard* holds for `/settings`; each form (username, password, email,
privacy, delete account — whichever VW-SET rows exist) loads its current value, validates with the
server's field errors, saves, and shows a confirmation; a Guest sees the registered-only message
(NFR-USAB-002), not a blank page; Settings never sits on "Loading…" when the request fails.

---

### IMP-M8-14 — Notifications bell and panel

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-06, IMP-M5-03 · **Closes:** the review's *Not covered* (live friend-request notification)

**Read first:**
- `docs/requirements/platform-views.md` — *Notifications* (VW-NOTIF-001…), VW-NAV-005
- `docs/requirements/notifications-invitations.md`
- `docs/specs/api-design/notification-rest-api.md`, `docs/specs/api-design/sse-notifications.md`
- `docs/requirements/game-rooms.md` (room invitations)

**Satisfies:** `platform-views.md` VW-NOTIF-001…, VW-NAV-005

**Done when:** the *View standard* holds for the bell and its panel as Guest and Registered; every
notification type the platform emits has a rendered text, including **room invitations** with a
working *Join* action and a friend request with *Accept*/*Decline*; a notification created while the
page is open (SSE) updates the badge without a reload and survives a reconnect of the stream; *Mark
read*, *Mark all read* and *Dismiss* persist across a reload; an unknown type renders a generic line
rather than nothing.

---

### IMP-M8-17 — The room resource names the viewer's membership

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-09 · **Closes:** RR-05 (backend half; `IMP-GATE-95`)

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §4 (`viewerRole`), §5 step 2
- `docs/requirements/platform-views.md` *Room — Lobby*, Entry
- `docs/requirements/reconnection-flow.md` FR-REJOIN-003, FR-EXPIRY-001

**Satisfies:** `platform-views.md` VW-JOIN-002 (on `/rooms/:id`)

**Done when:** `GET /api/rooms/{roomId}` carries `viewerRole`: `PLAYER` for a caller with an open player
row or a grace-period reservation, `SPECTATOR` for an open spectator row, `null` otherwise — including
a visitor to a public room and a caller who has left; the field is absent from list rows; the
OpenAPI document and the frontend's generated contract fixtures name it; an integration test asserts all
four values and that a `GET` never changes membership or bumps the room's version.

---

### IMP-M8-15 — The client retries a rate-limited subscribe

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04 · **Closes:** the follow-up recorded under `IMP-M7-13`

**Read first:**
- `docs/specs/api-design/rate-limiting.md` (Tier 6, `RATE_LIMIT_EXCEEDED` on `/user/queue/errors`)
- `docs/specs/api-design/websocket.md`, `docs/specs/api-design/room-websocket.md`
- `docs/implementation/registry.md` IMP-M7-13 *Follow-ups*

**Satisfies:** `reconnection-flow.md` FR-REJOIN-* (a join that does not silently half-complete)

**Done when:** a `SUBSCRIBE` or `REQUEST_GAME_SYNC` answered with `RATE_LIMIT_EXCEEDED` is retried after a
bounded back-off and the room or game view recovers without a reload; after the retry limit the view
shows an error with a retry button; a unit test and a Playwright spec that exhausts the bucket (three
game attaches in under 30 s for one user) end with a rendered board.

---

### IMP-M8-16 — The acceptance suite covers every view and the review's gaps

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01…15

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` — *What was verified working* and *Not covered*
- `docs/implementation/registry.md` IMP-M7-13 and its *Follow-ups*
- `docs/implementation/conventions.md` (test layout)

**Done when:** `npm run e2e` includes the per-view specs of `IMP-M8-06…14`, a forfeit scenario that
asserts the history row and the statistics, grace-period expiry with the 60 s figure asserted, the
`RATE_LIMIT_EXCEEDED` flood and its recovery, two simultaneous departures leaving no listed room, a
400 px pass over every route asserting no horizontal scroll, and a console-error and `5xx` tripwire
that fails any spec which saw one; the suite is wired into a documented `make` target and either a CI
job or an explicit note of why it cannot run there; a clean `make up` followed by the suite is green
**twice in a row** (the run must not exhaust the registration or guest allowance).

---

## Readiness gates

Populated from
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md).

<!-- GATES:BEGIN -->
The 2026-08-16 readiness audit returned **23 blockers. All 23 are now closed** — see
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
for the register, where each entry carries the evidence and a `**Closed:**` line naming the
resolution.

**Every work item in the register above is ungated.** Status reverts to whatever the item's own
dependencies imply. The table below is a record of what changed, not an overlay to consult before
starting work — each fix is already carried by the item it affects.

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
| IR-23 | **new** `platform-frontend/design-system.md`; `onboarding-wizard.md` | Design system specified and folded into `turnbase-frontend` (CON-002 amended); onboarding wizard **cut from v1** — IMP-M6-07 is cancelled |

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

### Raised during remediation — both closed

| ID | What | Resolution |
|---|---|---|
| ~~IR-24~~ | ~~`game-rooms.md` NFR-SPEC-001 requires spectator capacity to be configurable, and no property name is assigned~~ | **Closed.** `turnbase.room.spectator-capacity`, default `8`, in `local-environment.md` §7.1 and named at all four call sites |
| ~~IR-25~~ | ~~`docs/requirements/` has no `INDEX.md`~~ | **Closed.** [`../requirements/INDEX.md`](../requirements/INDEX.md) lists all seventeen documents and the requirement prefixes each one *defines* — use it to resolve a qualifier before citing one |

**No review finding is open anywhere in the corpus**, and since ADR-0013 no `OQ-*` in
`platform-ui-library.md` is open either — three were dropped rather than answered, because Astryx had
already made the visual decisions they were asking the platform to make.

**On the *Satisfies* qualifiers above.** Each names the document that **defines** the requirement, not
one that merely cites it. The two are easy to confuse: `game-history.md` discusses `FR-RET-003` at
length, but `platform-operations.md` defines it. Nineteen citations in this corpus had it the wrong
way round and were corrected; `../requirements/INDEX.md` is the lookup that prevents the next one.
