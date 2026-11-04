# Archive — M0 Bootstrap

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M0-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
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
3. **Error Prone + NullAway** ([ADR-0015](../../decisions/0015-static-analysis-error-prone-nullaway.md)):
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
- `docs/specs/deployment/secrets-and-configuration.md` in full — the ten secrets, the two-role
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
([ADR-0015](../../decisions/0015-static-analysis-error-prone-nullaway.md) §4).

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
