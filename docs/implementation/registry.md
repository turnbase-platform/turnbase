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
| IMP-M3-12 | FE GDK client (`@turnbase/gdk`) | sdk | M0-02 | DONE |
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
| IMP-M6-01 | Astryx integration and the `ui/` boundary | frontend | M0-05 | READY |
| IMP-M6-02 | Shell, routing and auth tiers | frontend | M6-01 | READY |
| IMP-M6-03 | Account and profile views | frontend | M6-02, M1-07 | READY |
| IMP-M6-04 | Room views and the STOMP client | frontend | M6-02, M2-08 | READY |
| IMP-M6-05 | Game iframe host and postMessage relay | frontend | M6-04, M3-07 | READY |
| IMP-M6-06 | Catalog and history views | frontend | M6-02, M4-01 | READY |
| ~~IMP-M6-07~~ | ~~Onboarding wizard~~ | frontend | — | CANCELLED |

**60 live items.** IMP-M6-07 is cancelled: IR-23 cut the onboarding wizard from v1, so
`onboarding-wizard.md`'s FR-ONB-* and NFR-ONB-* have no implementing item by design. The heading is
kept below so the number is never reused. `IMP-M3-12` was added 2026-08-22, closing IMP-GATE-05 — see
its section under M3.

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

**Satisfies:** `platform-operations.md` FR-MET-001…007, FR-TRACE-001…004, FR-OBS-001…005,
FR-ALERT-001…007, NFR-OBS-001; `platform-architecture.md` FR-OBS-001…009

**Done when:** Micrometer exports to Prometheus at the management port; Logback emits JSON to stdout
with a correlation ID on every record; OpenTelemetry propagates W3C trace context across the REST →
gRPC boundary and traces land in Tempo; Grafana resolves Prometheus, Loki and Tempo as data sources
and its derived field links a log line's `traceId` to the Tempo trace (`observability.md` §5).

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

**Read first:**
- `docs/requirements/platform-operations.md` FR-CICD-001…011
- `docs/specs/deployment/local-environment.md` §8 — **the authority on what each test category
  actually depends on.** Read it before the requirement, not after
- `docs/implementation/conventions.md` §§2–4, 6
- `CLAUDE.md` — *Submodule philosophy* and the End of Session Checklist

**Satisfies:** `platform-operations.md` FR-CICD-001…011

**Done when:** each repo has a GitHub Actions workflow that builds, tests, and publishes its
artifact; coverage is reported and gated on **unit and integration tests only** — the two categories
that run in the pre-merge pipeline (FR-CICD-003, as narrowed by IR-03; `CLAUDE.md`: >70% on critical paths); the
workflow is the gate `CLAUDE.md` requires before a submodule ref is bumped here.

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

**Read first:**
- `docs/specs/deployment/local-environment.md` §6
- `docs/specs/manifest/bundle-format.md` §3 — the pipeline the seed must go through

**Satisfies:** — *(developer experience; `local-environment.md` §6 is the only source)*

**Done when:** a seeded local stack lists at least one official game **that can actually be started**.

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

---

### IMP-M1-03 — JWT key set, issuance and rotation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-09

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

### IMP-M1-04 — Registration and login

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01, IMP-M1-03

**Read first:**
- `docs/requirements/user-accounts.md` — FR-AUTH-001…016, FR-ACCT-001, NFR-SEC-001…003, 005…007
- `docs/specs/platform/data-model-accounts.md` §1 (`app_user`), §2 (`user_auth_method`)
- `docs/specs/api-design/input-validation.md` — the field catalogue and canonicalization
- `docs/specs/flows/01-arrival-and-account.md`

**Satisfies:** `user-accounts.md` FR-AUTH-001…016, FR-ACCT-001, NFR-SEC-001…003, NFR-SEC-005…007;
`platform-views.md` VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002

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

**Read first:**
- `docs/requirements/user-accounts.md` FR-GUEST-001…010
- `docs/specs/platform/data-model-accounts.md` §1 (the `kind` discriminator)
- `docs/requirements/platform-operations.md` FR-RET-002 (the guest purge window)
- `docs/specs/deployment/local-environment.md` §7.3

**Satisfies:** `user-accounts.md` FR-GUEST-001…010; `platform-operations.md` FR-RET-002

**Done when:** a guest principal can be minted without registration; guest serials are unique
(FR-GUEST-002); guests have no auth method, no friends, no statistics and no uploads (FR-GUEST-004,
007, 008, 009); the purge is **two-phase** and a guest seated in a live room is never removed — a
literal 24-hour delete fails permanently on `room_participant`'s FK, and the cascade that would
"fix" it removes a seated player from a live game. The real bound is ~8 days.

---

### IMP-M1-06 — Session lifecycle and displacement

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Read first:**
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/platform/data-model-accounts.md` §3 (`user_session`)
- `docs/specs/api-design/rest-conventions.md` § *Authentication*
- `docs/specs/api-design/websocket.md` § *Authentication*; `docs/specs/api-design/sse-notifications.md`
  § *Endpoint*

**Satisfies:** `user-accounts.md` FR-SESS-001…004, FR-SESS-010…011

**Done when:** at most one active session per account holds as a **database** invariant, not as a
service-layer check (FR-SESS-002); a new login revokes the previous session and writes
`user_session.revoked_reason` (FR-SESS-003); a request bearing an invalidated token receives the
`error-handling.md` 401 shape (FR-SESS-004); logout revokes (FR-SESS-011).

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

**Read first:**
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010
- `docs/specs/platform/data-model-accounts.md` §1, §4 (`user_privacy_settings`)
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007 — the rendering contract the
  API must be able to satisfy

**Satisfies:** `user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010

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

**Read first:**
- `docs/decisions/0004-account-erasure-pseudonymization.md`
- `docs/specs/platform/data-model-accounts.md` §5 in full — *Erasure: what account deletion actually
  writes*. §5 enumerates every object and its disposition; that enumeration is the specification.
- `docs/requirements/user-accounts.md` FR-ACCT-004…010
- `docs/specs/platform/data-model-catalog.md` §5, `data-model-history.md` §4,
  `data-model-notifications.md` §2 — the three documents that own the non-account objects §5 disposes of
- `docs/specs/platform/room-lifecycle.md` §4, §5.1 duty 2 — how an owed room closure is discharged

**Satisfies:** `user-accounts.md` FR-ACCT-004…010; `platform-operations.md` FR-RET-001, FR-RET-005

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

**Read first:**
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform/data-model-social.md` §§1–3 — `friendship`, `friend_request`, and the
  interaction with `block_friend_requests`
- `docs/requirements/notifications-invitations.md` FR-FREQ-001…006
- `docs/requirements/user-accounts.md` FR-GUEST-007

**Satisfies:** `social-friends.md` FR-SOC-001…021; `notifications-invitations.md`
FR-FREQ-001…006; `user-accounts.md` FR-GUEST-007

**Done when:** guest exclusion is enforced by the foreign key — `friendship` references
`app_user (user_id, kind)` with a local `CHECK kind = 'REGISTERED'` — so `social-friends.md`
FR-SOC-020 cannot be violated from any code path; friendship rows are stored in the canonical
ordering `data-model-social.md` §1 defines, so the pair `(a,b)` and `(b,a)` cannot both exist; a
blocked user's request is rejected without disclosing that a block exists.

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

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06

**Read first:**
- `docs/specs/api-design/room-rest-api.md` **in full** — the five endpoints, §3's inclusion
  predicate, §5's join contract, §7's error table
- `docs/specs/platform/data-model.md` §1 (`room`), §2 (`room_participant`), §3 (`room_team`)
- `docs/requirements/game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…006
- `docs/specs/api-design/pagination-filtering-sorting.md`, `rest-conventions.md`

**Satisfies:** `game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…006, FR-LIFE-004,
NFR-PERF-001, NFR-SEC-001…002, NFR-USAB-001, NFR-SPEC-001; `platform-views.md` VW-ROOMS-001…005,
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

**`canSpectate`'s capacity is `turnbase.room.spectator-capacity`** (default `8`,
`local-environment.md` §7.1) — a platform property, not a room column and not a create-request field.
Hosts choose whether a room allows spectating; they do not choose how many (NFR-SPEC-001). The wire
field `spectatorCapacity` is the resolved value, so lowering the property never evicts a seated
spectator.

---

### IMP-M2-02 — STOMP endpoint, auth, subscriptions

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01

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
**there is no cross-instance fan-out**).

---

### IMP-M2-03 — Ownership claim, lease, epoch fence

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-02

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

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §2 (*Versioning*)
- `docs/specs/api-design/room-websocket.md` — *Per-Room Serialization and Versioning*, *Server→Client
  Event Catalogue*, *Client Reconciliation*
- `docs/specs/platform/data-model.md` §1 (`version`)
- `docs/decisions/0002-websocket-room-affinity.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-rooms.md` NFR-PERF-002

**Done when:** the version is committed to Postgres **before** the delta is published, and is
**assigned**, never `max()`-ed. Clients discard `delta.version <= localVersion`, so a pod that
re-issues a seen version is silently and permanently wrong for every client — strictly worse than a
gap. Chat is excluded from the counter entirely (`version: null`, IMP-M2-11).

---

### IMP-M2-05 — Join, teams, readiness

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-04

**Read first:**
- `docs/requirements/game-rooms.md` FR-JOIN-001…011, FR-TEAM-001…012, FR-READY-001…004,
  FR-LIFE-004…006
- `docs/specs/api-design/room-websocket.md` — *Client→Server Command Catalogue* and the matching
  server events
- `docs/specs/api-design/room-rest-api.md` §5 (the REST join, which precedes every STOMP command)
- `docs/specs/platform/data-model.md` §2, §3
- `docs/specs/flows/02-room-to-game-start.md`

**Satisfies:** `game-rooms.md` FR-JOIN-001…011, FR-TEAM-001…012, FR-READY-001…004, FR-LIFE-005…006,
NFR-SPEC-001; `platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017

**Done when:** auto-assignment follows FR-TEAM-005, and FR-TEAM-012's team instantiation happens
**before** the host is seated on room creation — a host assigned first has nowhere to go;
FR-TEAM-010's capacity floor is checked on **every** operation that could reduce total capacity, not
only on explicit slot removal (moving a player and removing a team both can); readiness resets on
the return to Lobby (FR-READY-004); FR-JOIN-007's one-room-at-a-time rule is enforced server-side.

**AI is wire-present and behaviour-absent in v1** (IR-12). `ADD_AI_PLAYER` always returns
`AI_NOT_SUPPORTED`, the room snapshot's `aiPlayers` is always empty, and FR-READY-002 ("AI players are
always ready") is therefore implemented and unreachable. Implement it anyway; do not delete the
branch, and do not build an AI seat to make it reachable.

---

### IMP-M2-06 — Host management and transfer

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

**Read first:**
- `docs/requirements/game-rooms.md` FR-HOST-001…003, FR-HOST-006…009, FR-XFER-001…005
- `docs/requirements/reconnection-flow.md` FR-HDISC-001…004
- `docs/specs/platform/room-lifecycle.md` §3 (grace deadlines), §5 (the sweeps)
- `docs/specs/platform/data-model.md` §1 — `migration_window_expires_at`
- `docs/specs/api-design/room-websocket.md` — the host command set

**Satisfies:** `game-rooms.md` FR-HOST-001…003, FR-HOST-006…009, FR-XFER-001…005; `reconnection-flow.md`
FR-HDISC-001…004

**Done when:** `migration_window_expires_at` is persisted and a sweep duty closes it. Without it a
host who does not return leaves the room permanently headless — adoption never routes through the
individual-disconnect path that would otherwise end the window. FR-HOST-003 (add AI player) returns
`AI_NOT_SUPPORTED` per IR-12. FR-HOST-008 retains game parameters across the return to Lobby.

---

### IMP-M2-07 — Disconnect, grace deadlines, sweeps

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Read first:**
- `docs/decisions/0009-grace-deadline-durability.md`
- `docs/specs/platform/room-lifecycle.md` §3 **in full** (especially §3.2's resolve statement and
  §3.3's conditional outbox insert) and §5.1
- `docs/requirements/reconnection-flow.md` FR-DC-001…007, FR-GRACE-001…006, FR-EXPIRY-001…006,
  FR-KICK-001…004
- `docs/specs/platform/data-model.md` §2 — `left_at`, `leave_reason`, `lost_announced_at`
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

---

### IMP-M2-08 — Reconnect and resync

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Read first:**
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003
- `docs/specs/api-design/room-websocket.md` — *Snapshot Delivery*, *Client Reconciliation*
- `docs/specs/platform/room-lifecycle.md` §2, §3.2
- `docs/specs/flows/04-disconnect-and-return.md`

**Satisfies:** `reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003; `game-rooms.md`
FR-JOIN-011

**Done when:** a reconnecting client receives a **snapshot carrying its version**, then deltas from
that version onward — there is no merge path and no partial replay; the server never re-announces a
departure whose `lost_announced_at` is already set; a rejoin inside the grace window restores the
participant's seat and team rather than re-seating them (FR-REJOIN-*, FR-JOIN-011); a rejoin after
expiry is an ordinary join and is subject to every capacity rule.

---

### IMP-M2-09 — Room closure and the five detach paths

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §4 **in full** — the five paths and the fenced step 3
- `docs/specs/flows/07-room-closure.md`
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §1 (`closed_at`, `closed_reason`), §4
- `docs/requirements/notifications-invitations.md` FR-INV-008

**Satisfies:** `game-rooms.md` FR-LIFE-007, FR-XFER-002…003, FR-XFER-005;
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

---

### IMP-M2-10 — Adoption and reconciliation jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §5 **in full** — the three duties, and duty 2's
  `leave_reason IN ('GRACE_EXPIRED','EARLY_RELEASE','LEFT')` narrowing plus its host disposition
- `docs/requirements/platform-operations.md` FR-JOB-001…013, NFR-JOB-001…002
- `docs/decisions/0008-room-ownership-lifecycle.md`
- `docs/specs/deployment/local-environment.md` §7.2
- `docs/specs/flows/05-owner-loss-and-adoption.md`

**Satisfies:** `platform-operations.md` FR-JOB-001…013, NFR-JOB-001…002

**Done when:** the three reconciliation duties run per `platform-operations.md` FR-JOB-*; an
In-Progress room with no session **fails back to Lobby, not closed**; the adopt duty is exempt from
both FR-JOB-008 guards, which would otherwise block adoption for 120 s after every restart; orphaned
participant rows are handled by `ON DELETE CASCADE` rather than by a job.

**Duty 2 is the deferred tail.** It announces departures whose `lost_announced_at` is NULL and then
evaluates closure, and it is the mechanism three other items rely on (M1-08, M2-07, M2-09). Its
`leave_reason` filter is a backstop, not the primary control — the primary control is that every
inline path stamps `lost_announced_at` itself (IR-09).

---

### IMP-M2-11 — In-room chat

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

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
no HTML string is ever constructed.

**Giving chat a version number is the tempting mistake.** Two writers on one counter means a client
that filters chat sees a permanent gap in the room stream and resyncs forever.

---

### IMP-M2-12 — Room invitations

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M1-09

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-INV-001…009, FR-LINK-001…002
- `docs/specs/platform/data-model-notifications.md` §2 (`room_invitation`)
- `docs/specs/api-design/room-rest-api.md` §3 — invite-code resolution
- `docs/requirements/game-rooms.md` FR-HOST-001…002, FR-JOIN-003…004, NFR-SEC-002

**Satisfies:** `notifications-invitations.md` FR-INV-001…009, FR-LINK-001…002; `game-rooms.md`
FR-HOST-001…002, FR-JOIN-003…004, FR-JOIN-006…008, NFR-SEC-002

**Done when:** the invite identifier is cryptographically random and non-sequential (NFR-SEC-002);
resolution goes through `GET /api/rooms?inviteCode=…` and returns an empty list rather than a `404`
for an unknown or dead code (FR-JOIN-004's four invalidity conditions are all "not found", and they
must be indistinguishable from each other); the link is single and reusable per room (FR-HOST-002);
invitations are removed **at closure** by IMP-M2-09, not by the purge cascade (FR-INV-008).

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

**Satisfies:** `platform-architecture.md` FR-CTX-001…012, FR-LOAD-001…005

**Done when:** every isolation requirement in §4's table maps to a concrete Truffle/Espresso mechanism
that a test exercises — the table is a checklist, and an unexercised row is an assumption; a context
is created and disposed per §6's model with no leak across sessions; the guest classpath built per §7
contains the game JAR and the SDK and nothing else.

---

### IMP-M3-03 — GDK host bridge and serialization boundary

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-01, IMP-M3-02

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §3 (the guest bridge and host shim), §5 (the
  serialization engine), §8 (state representation)
- `docs/specs/gdk-api/backend-gdk-api.md` §10 (relationship to the gRPC contract)
- `docs/requirements/game-contracts.md` NFR-SEC-001…004, NFR-SIZE-001…002

**Satisfies:** `platform-architecture.md` FR-CTX-001…012; `game-contracts.md` NFR-SEC-001…004,
NFR-SIZE-001…002

**Done when:** every object crossing the Espresso boundary is copied, not shared. A shared mutable
object across that boundary is a sandbox escape regardless of ADR-0006's trust model.

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

---

### IMP-M3-05 — Orchestration client and session registry

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-04, IMP-M2-04

**Read first:**
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — *Addressing the Game Host pods*,
  *Processing semantics*, *Error model*
- `docs/specs/game-host/game-host-internals.md` §6, §9, §13 (the Redis data model)
- `docs/specs/flows/02-room-to-game-start.md` — **step 6 names exactly which keys Orchestration writes**
- `docs/specs/platform/data-model.md` §1 (`active_session_id`), §4

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-REG-001…004, FR-SESS-001…006

**Done when:** `session:{id}` has **exactly one writer, the Game Host** (IR-14). Orchestration writes
only the keys flow 02 step 6 names and reads the rest. The platform's own record of a live session is
`room.active_session_id` — a durable Postgres fact — not a Redis key, so a Redis flush loses cached
state and not the knowledge that a session exists.

**Closes IMP-GATE-08's cross-repo half:** this item gives `GameHostRegistryService` its real server
implementation, so it also carries the end-to-end check `IMP-M0-04` could not — a `turnbase-game-host`
instance pointed at a running Platform Monolith completes `Register` within `local-environment.md`
§3's 60-second budget.

---

### IMP-M3-06 — Game input outbox and delivery

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05

**Read first:**
- `docs/specs/platform/data-model.md` §4 — `game_input_outbox`, and why `session_id` is `NOT NULL`
- `docs/specs/platform/room-lifecycle.md` §3.3 — the conditional insert
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/flows/03-game-turn.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-contracts.md` FR-IN-001…006

**Done when:** the outbox drain is **not** ownership-partitioned — it is a gRPC call needing no
ownership, and partitioning it leaves an unowned room's `player_left` undelivered, with the game
sitting on a turn that never comes.

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

---

### IMP-M3-08 — Session teardown as a durable to-do

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05

**Read first:**
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §4 — `session_teardown`, keyed by `session_id`
- `docs/specs/platform/room-lifecycle.md` §4
- `docs/specs/flows/06-game-end-and-rematch.md`

**Satisfies:** `game-rooms.md` FR-XFER-005; `platform-architecture.md` FR-ORCH-005…007

**Done when:** the to-do is keyed by `sessionId`, **not** by a flag on the room — a rematch would
overwrite the previous session's owed teardown. Any rule testing whether a teardown was recorded must
test `room.active_session_id = :sessionId`, a durable fact, rather than the presence of the
`session_teardown` row, which `terminateAndCleanup` deletes on success.

---

### IMP-M3-09 — Game failure handling

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M3-07

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §8.1 (the session record's failure slot), §9.1, §12
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` § *Error model*
- `docs/requirements/platform-architecture.md` FR-FAIL-001…007
- `docs/requirements/game-contracts.md` FR-FA-001…003, NFR-REL-001…002

**Satisfies:** `platform-architecture.md` FR-FAIL-001…007; `game-contracts.md` FR-FA-001…003,
NFR-REL-001…002

**Done when:** the acting player is told why. `platform-architecture.md` FR-FAIL-001 and FR-FAIL-003
must be coherent about first-failure versus three-failure termination, and the failed input has a
stated disposition on every path.

**The session record carries `lastOutcome` and `lastFailure` for a reason** (IR-15). A replayed
sequence that previously failed must return *its own* failure. Without those two slots the replay
returns `lastEffects` from the last *successful* input, so a retry of a rejected move looks to the
client like the move succeeded.

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

**Satisfies:** — *(no requirement. This item exists to prove the GDK contract is implementable by
someone outside the platform team, which ADR-0006 makes the MVP's only game-supply mechanism.)*

**Done when:** the game compiles against the **published SDK artifact only** — a dependency on
`turnbase-game-host` or `turnbase-common` means the contract is not self-sufficient and the item has
failed even if the game runs; it ships a frontend bundle built against the published npm package; it
is packaged per `bundle-format.md` §2 and published through IMP-M4-03's real pipeline; a full
create → join → start → several turns → outcome → history round trip passes against the local stack.

---

### IMP-M3-11 — GDK test harness

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M3-01

**Read first:**
- `docs/specs/gdk-api/test-harness.md` **in full** — §1 is a scope boundary, not a preamble
- `docs/requirements/game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010,
  NFR-UPLOAD-002

**Satisfies:** `game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010

**Done when:** the harness performs the **executing** round trip. `game-development-experience.md`
NFR-UPLOAD-002 forbids running game code at upload, so static serializability is checked at upload
and the executing round trip belongs here (FR-HARNESS-010).

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

## M4 — Catalog and upload

**Read first:** `docs/specs/manifest/bundle-format.md`, `manifest-schema.md`, `manifest.schema.json`,
`docs/specs/platform/data-model-catalog.md`, `docs/specs/api-design/file-uploads.md`,
`docs/specs/game-frontend/game-asset-serving.md`, flow `08`.

### IMP-M4-01 — Catalog listing and game detail

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01

**Read first:**
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009, FR-GAME-001…014
- `docs/specs/platform/data-model-catalog.md` §1 (`game`), §3 (`game_tag`), §4 (`game_review`)
- `docs/requirements/admin-tooling.md` FR-BADGE-001…004, FR-PRV-001…004 — visibility is an
  admin-tooling rule that this endpoint enforces
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/specs/api-design/input-validation.md` § *Output encoding*

**Satisfies:** `game-catalog.md` FR-CAT-001…010, FR-GDET-001…009, FR-GAME-001…014, NFR-PERF-001…002,
NFR-SCAL-001, NFR-SEC-001…002, NFR-USAB-001…002; `admin-tooling.md` FR-PRV-001…004; `platform-views.md`
VW-CAT-001…003, VW-GDET-001…003

**Done when:** an Unverified game is absent from the catalog and from search for every caller except
its owner (`admin-tooling.md` FR-PRV-001); each game carries exactly one badge, read from one column
(FR-BADGE-001); descriptions are delivered as **Markdown source** and rendered to React elements
client-side (IMP-M6-06) — the API never returns an HTML string, which is what makes
`input-validation.md`'s `dangerouslySetInnerHTML` ban enforceable rather than aspirational (IR-19).

---

### IMP-M4-02 — Manifest schema validation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-06

**Read first:**
- `docs/specs/manifest/manifest.schema.json` — **the executable artifact and the authority**
- `docs/specs/manifest/manifest-schema.md` — the prose, including the `capabilities` rules
- `docs/specs/manifest/bundle-format.md` §3 (where in the pipeline this runs)
- `docs/requirements/game-development-experience.md` FR-MANIFEST-001…009

**Satisfies:** `game-development-experience.md` FR-MANIFEST-001…009

**Done when:** validation runs against `manifest.schema.json` — the executable artifact — and the
prose documents agree with it. Where they disagree, fix the document. `capabilities.ai: true` is
**rejected** at validation (IR-12): the field survives in the schema for a future release, and a
bundle declaring it today would list a game whose AI seats can never be filled.

---

### IMP-M4-03 — Upload pipeline and version state machine

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-02

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

**Read first:**
- `docs/specs/manifest/bundle-format.md` §5 (unpacking and publication)
- `docs/specs/game-frontend/game-asset-serving.md` **in full** — §3 origin architecture, §4 serving,
  §5 the bootstrap document, §9 invariants
- `docs/decisions/0007-game-frontend-separate-domain.md`
- `docs/specs/deployment/local-environment.md` §7.7

**Satisfies:** `game-development-experience.md` FR-ASSET-001…009; `game-contracts.md` FR-FE-001…006

**Done when:** publication **filters**. Unpacking the whole archive under `/g/{gameId}/{version}/`
publishes the backend JAR to anonymous callers — `gameId` is in the hostname and the version is a
public catalog column, so the URL is derivable from a catalog page.

**A pre-signed URL is a bearer credential.** Every log line that carries one is truncated at the
query string (FR-OBS-005).

---

### IMP-M4-05 — Admin API, review queue and badges

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03

**Read first:**
- `docs/requirements/admin-tooling.md` **in full**
- `docs/specs/platform/data-model-catalog.md` §1, §2
- `docs/specs/api-design/rest-conventions.md` § *Actuator and the Management Port*
- `docs/specs/deployment/local-environment.md` §1 host port map

**Satisfies:** `admin-tooling.md` FR-ADM-001…003, FR-REV-001…006, FR-BADGE-001…004, FR-OFF-001…002,
FR-PRV-001…004, NFR-AUD-001, NFR-CRED-001, NFR-SEC-001

**Done when:** the admin API is served on the **management port, the same listener as actuator**, and
is loopback-bound under compose and unrouted under Kubernetes (FR-ADM-001, `admin-tooling.md`
CON-001, `local-environment.md` §1); HTTP Basic with credentials from configuration (FR-ADM-002);
**no browser panel exists** (FR-ADM-003); approval sets Verified and publishes, rejection stores a
plain-text reason and does **not** delete the game or transfer ownership (FR-REV-004…006); official
uploads bypass the queue entirely (FR-OFF-002); every admin action writes an audit record
(NFR-AUD-001).

---

## M5 — History, statistics, notifications

### IMP-M5-01 — Game history recording

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-09

**Read first:**
- `docs/requirements/game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030
- `docs/specs/platform/data-model-history.md` §1 (`game_session_completion`), §2
  (`game_history_entry`)
- `docs/requirements/game-contracts.md` FR-OUTCOME-001…004
- `docs/specs/flows/06-game-end-and-rematch.md`

**Satisfies:** `game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030,
NFR-HIST-001…003; `game-contracts.md` FR-OUTCOME-001, FR-OUTCOME-004

**Done when:** a malformed outcome from game code cannot abort the whole recording transaction with
no retry path (`ghe_placement_ck`).

**Game code produces the outcome, so the outcome is untrusted input.** Validate it before it reaches
a `CHECK` constraint; a constraint violation here rolls back a completed game's entire record and
there is nothing left to retry from.

---

### IMP-M5-02 — Per-game statistics

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01

**Read first:**
- `docs/requirements/per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027
- `docs/specs/platform/data-model-history.md` §3 — *The per-game counter and its writer*
- `docs/requirements/user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Satisfies:** `per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027,
NFR-STATS-001…003; `user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Done when:** the counter has exactly **one** writer — the one `data-model-history.md` §3 names. Two
writers race and the count drifts silently, with no error and no way to detect it after the fact.
Guests accumulate no statistics (FR-GUEST-009). Removing a deleted user's statistics leaves every
other player's aggregates unchanged (FR-ACCT-008).

---

### IMP-M5-03 — Notifications and the SSE stream

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
  FR-FREQ-001…006
- `docs/specs/platform/data-model-notifications.md` §1 (`notification`), §3 (types), **§4 — alerts
  have no table, and three current "notifications" are alerts**
- `docs/specs/api-design/sse-notifications.md` **in full**
- `docs/requirements/platform-operations.md` FR-JOB-013, FR-RET-001…006

**Satisfies:** `notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
FR-FREQ-001…006, FR-LINK-001…002, NFR-PERF-001, NFR-SCALE-001, NFR-SEC-001; `platform-views.md`
VW-NOTIF-001…004

**Done when:** the retention purge is indexed **partially on having no subject**, so it can never
remove an actionable message out from under a live object; and no notification is permanently
unpurgeable because its subject never expires.

**Persisted notifications and transient alerts are two classes, not one with a flag** (§4). Three
things the requirements call notifications are alerts and must never get a table row — writing them
to `notification` makes them re-deliverable on reconnect, which is the opposite of what a transient
alert is for.

---

### IMP-M5-04 — Retention purge jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01, IMP-M5-03

**Read first:**
- `docs/requirements/platform-operations.md` FR-RET-001…006, FR-JOB-001…013, NFR-JOB-001…002
- `docs/specs/platform/data-model-history.md` §4 (erasure), `data-model-notifications.md` §1
- `docs/specs/deployment/local-environment.md` §7.2 (job scheduling), §7.3 (retention windows)

**Satisfies:** `platform-operations.md` FR-RET-001…006, FR-JOB-001…013, NFR-JOB-001…002;
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

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-01

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §§1–3 (structure, auth tiers, routing),
  §6 (Content-Security-Policy), §7 (notifications and alerts), §10
- `docs/requirements/platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
  VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/api-design/sse-notifications.md`
- `docs/specs/platform-frontend/design-system.md` §2 — the two providers the shell owns

**Satisfies:** `platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002, NFR-USAB-001…002

**Done when:** §3's three auth tiers gate every route, and a route's tier is declared with the route
rather than checked inside the view; §6's CSP is emitted by the platform origin **without restating
`frame-src`**, which `game-asset-serving.md` §6.3 owns — two documents specifying one directive is how
they drift; a mid-session 401 follows the VW-REDIR rules rather than blanking the view; the SSE
stream reconnects with backoff and does not duplicate alerts on reconnect.

**The shell mounts `<LinkProvider component={Link}>` inside `<Theme>`, once** (`design-system.md`
§2). Skipping it is the expensive mistake in M6: every Astryx `Link`, and every component that
renders one internally, falls back to a plain `<a href>` and triggers a **full page reload** —
dropping the STOMP connection, the room subscription and all in-memory session state. It fails as a
navigation bug three milestones from where it was introduced.

---

### IMP-M6-03 — Account and profile views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M1-07

**Read first:**
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform-frontend/design-system.md` §4 (the component inventory these views compose)

**Satisfies:** `platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005;
`user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010; `social-friends.md`
FR-SOC-001…021

**Done when:** **the owner sees their own profile in full regardless of every privacy setting they
have set** — private profile, hidden sections and hidden friend list all render for them (IR-05,
FR-PROF-007, VW-PROF-002…003, VW-FREN); a guest profile shows the username and nothing else
(FR-GUEST-010); a soft-deleted user's profile shows the FR-ACCT-009 placeholder; deletion is a
confirmed, explicit action (FR-ACCT-004).

**The view is not the access control.** Every rule above is already enforced by IMP-M1-07 server-side;
implementing it here as well is a rendering concern, and implementing it *only* here is a
vulnerability.

---

### IMP-M6-04 — Room views and the STOMP client

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M2-08

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §4 (the WebSocket client)
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

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M4-01

**Read first:**
- `docs/requirements/platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009
- `docs/requirements/game-history.md` FR-HIST-020…030
- `docs/specs/api-design/input-validation.md` § *Output encoding* — the owner of the Markdown rule
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004;
`game-catalog.md` FR-CAT-001…010, FR-GDET-001…009; `game-history.md` FR-HIST-020…030

**Done when:** game descriptions are parsed from Markdown into **React elements**, client-side, with
no intermediate HTML string anywhere in the path (IR-19); `dangerouslySetInnerHTML` appears nowhere
in the repository and a lint rule enforces its absence — the ban is only worth having if nothing can
quietly re-introduce it; catalog paging uses the shared contract from IMP-M1-01 rather than a
bespoke one.

---

### ~~IMP-M6-07 — Onboarding wizard~~ · CANCELLED

**Cancelled by IR-23.** The onboarding wizard is cut from v1.
`docs/requirements/onboarding-wizard.md` is retained as the record of a deferred feature; its
FR-ONB-001…013 and NFR-ONB-001…003 have no implementing item and are not expected to.

The identifier is retired and will not be reused. If the wizard returns, it gets a new number.

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
