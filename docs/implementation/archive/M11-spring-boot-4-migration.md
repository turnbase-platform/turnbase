# Archive — M11 Spring Boot 4 migration

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M11-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M11-01 | The corpus describes the Spring Boot 4.1 stack | docs | — | DONE |
| IMP-M11-02 | `turnbase-platform` compiles on Spring Boot 4.1.1 | platform | M11-01 | DONE |
| IMP-M11-03 | Platform host-side JSON is Jackson 3 | platform | M11-02 | DONE |
| IMP-M11-04 | Platform unit and integration tests are green on Boot 4 | platform | M11-03 | DONE |
| IMP-M11-05 | `turnbase-game-host` compiles on Spring Boot 4.1.1 with Jackson 3 host-side | game-host | M11-01 | DONE |
| IMP-M11-06 | Game Host unit and integration tests are green on Boot 4 | game-host | M11-05 | DONE |
| IMP-M11-07 | The local stack and the acceptance suite run on both Boot 4 branches | platform, game-host, frontend | M11-04, M11-06 | DONE |
| IMP-M11-08 | Both migration branches merge and the pipelines are green | platform, game-host | M11-07 | DONE |

---

## M11 — Spring Boot 4 migration

Opened 2026-10-10 by [ADR-0016](../../decisions/0016-spring-boot-4-migration.md), which closed
`IMP-GATE-97`: CVE-2026-47884/47890 (CRITICAL, `spring-webmvc` 6.2.19) have no fix on the Boot 3.5
line, so `turnbase-platform` and `turnbase-game-host` move to **Spring Boot 4.1.1** (Spring Framework
7.0.9, Jackson 3 host-side, Modulith 2.1.x, JUnit 6, Testcontainers 2). ADR-0016 §5 is the risk
register; each item below retires the risks it names.

**M11 runs before M10.** Every `IMP-M10-*` item depends on `IMP-M11-08` (ADR-0016 §6).

**How M11 differs from every other milestone — read before claiming any item:**

- **Ordinary workflow.** Short-lived branch per item, merged `--ff-only` into `master` and deleted in
  the same session, ref bumped. There is no long-lived migration branch (ADR-0016 §4).
- **CI is awaited unless the session prompt carries a `CI policy for this run` paragraph** (the loop's
  `--skip-ci-wait`); with no such paragraph, `gh run watch --exit-status` as for any item. Under it, `DONE` for `IMP-M11-02…07` means the *Done when* clause
  holds from a clean local checkout — `./mvnw spotless:apply` leaves no diff, and `verify` /
  `verify -Pintegration` pass as far as the clause demands — with `master` pushed and the ref bumped.
  Only `IMP-M11-08` carries `**CI wait:** required`.
- **A red build on exit is allowed only where an item says so** with a `**Build on exit:** may be red`
  line naming what may fail (`02`, `03`, `05`). Still merge, push and bump the ref, and record in
  STATUS.md exactly what is red. Any other item leaves `master` green.
- **Hold the wire format.** No item may change a REST body, STOMP frame, Redis value or `jsonb`
  column as a side effect of the upgrade (ADR-0016 §2). A difference is a `spec-defect`, not a fix.
- **Guest-side Jackson 2 is not in scope.** Anything that would change the Jackson inside the Espresso
  guest stops the item (ADR-0016 §2, R4).

### IMP-M11-01 — The corpus describes the Spring Boot 4.1 stack

**Repo:** `turnbase` (docs) · **Depends on:** —

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md`
- `docs/decisions/0012-repo-strategy-polyrepo-submodules.md` (*Pull requests are suspended*)

**Satisfies:** `platform-operations.md` CON-001; `platform-architecture.md` CON-010

**Done when:**
- **Stack lines.** `CLAUDE.md`'s tech-stack and repository tables, ADR-0012's repository table and
  every requirements document's backend constraint name Spring Boot 4.1+; no `docs/` file outside
  `docs/reviews/` and the historical record in this registry names Boot 3.5 as the current stack.
- **Specs.** Any spec that names a Boot-3- or Jackson-2-specific API for host code is restated for
  the Boot 4 / Jackson 3 stack (`input-validation.md`'s `StreamReadConstraints`, `error-handling.md`'s
  `ProblemDetail`).
- **Process.** ADR-0016 is registered in `docs/decisions/INDEX.md`; M11 is in the register and in `INDEX.md`'s milestone map; `IMP-GATE-97` is closed;
  `check-corpus.py` is clean.

### IMP-M11-02 — `turnbase-platform` compiles on Spring Boot 4.1.1

**Repo:** `turnbase-platform` · **Depends on:** IMP-M11-01

**Build on exit:** may be red — tests may fail to compile or fail at run time (Jackson 2 beans, moved
test APIs); `main` sources and `spotless:check` must pass.

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§1, §4, §5 R5–R8, R10)
- `docs/decisions/0014-modular-monolith-spring-modulith.md`
- `docs/decisions/0015-static-analysis-error-prone-nullaway.md`

**Satisfies:** `platform-operations.md` CON-001; `platform-operations.md` FR-CICD-010

**Done when:**
- **Versions.** `spring-boot-starter-parent` is `4.1.1`; `spring-modulith.version` is the latest
  2.1.x; the `tomcat.version` override and its CVE comment are removed (Boot's Tomcat 11 is used);
  starters use their Boot 4 names (`spring-boot-starter-webmvc`); Testcontainers dependencies use
  their 2.x artifact names. Every remaining explicit version outside the Boot BOM (ShedLock, Bucket4j,
  jjwt, AWS SDK, logstash encoder, gRPC, icu4j, Bouncy Castle) is checked against Spring 7 / Lettuce 7
  and either kept with a one-line pom comment saying so or bumped.
- **Compiles.** `./mvnw -DskipTests verify` passes on the branch: Spotless clean, Error Prone and
  NullAway at their ADR-0015 severity (no check downgraded, no new exclusion), main and test sources
  compiled. Jackson 2 may still be referenced in code at this point (`IMP-M11-03` removes it); if a
  temporary explicit `jackson-databind` 2.x dependency is needed to compile, it carries a
  `TODO(IMP-M11-03)` comment.
- **Housekeeping.** `.github/dependabot.yml`'s `spring-boot-starter-parent` ignore entry now reads
  `>= 5.0.0` with its comment rewritten to cite ADR-0016; `README.md` and the repo's `CLAUDE.md` name
  Boot 4.1.
- **Landed.** Merged to `master`, pushed, ref bumped; STATUS.md says the build is red and why.

### IMP-M11-03 — Platform host-side JSON is Jackson 3

**Repo:** `turnbase-platform` · **Depends on:** IMP-M11-02

**Build on exit:** may be red — integration tests may still fail for causes `IMP-M11-04` owns (Modulith,
Tomcat 11, Testcontainers); unit tests and `main` compilation must pass.

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§2, §5 R1–R3)
- `docs/specs/api-design/input-validation.md` (the `StreamReadConstraints` paragraph)
- `docs/specs/api-design/error-handling.md`

**Satisfies:** `platform-operations.md` CON-001

**Done when:**
- **Golden payloads first.** Before any Jackson change, round-trip tests capture the serialized form
  of representative REST bodies (a profile, a room, a catalog page, a `ProblemDetail`), a STOMP room
  event, a Redis-stored value (`GameLogStore`) and a `jsonb` column (`GameVersionRepository`), and they
  pass on the branch as it stood after `IMP-M11-02`.
- **Migrated.** No main or test source in `io.turnbase.platform` imports `com.fasterxml.jackson.databind`
  or `com.fasterxml.jackson.core` (annotations excepted); the Spring-managed mapper is Boot 4's
  Jackson 3 `JsonMapper`, customised in one place, with every Jackson-3 default that differs from the
  golden payloads set explicitly. A test asserts the import rule. The temporary Jackson 2 dependency,
  if `02` added one, is gone; `jjwt-jackson`'s own Jackson 2 is untouched.
- **Unchanged wire.** The golden-payload tests pass unmodified.
- **Nesting limit.** A request body nested deeper than the configured limit is rejected with the
  status `input-validation.md` specifies.
- **Landed.** As `IMP-M11-02`.

### IMP-M11-04 — Platform unit and integration tests are green on Boot 4

**Repo:** `turnbase-platform` · **Depends on:** IMP-M11-03

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§4, §5 R5, R6, R8, R9)
- `docs/specs/deployment/local-environment.md` (the test tiers)

**Satisfies:** `platform-operations.md` FR-CICD-003

**Done when:**
- **Green locally** — `./mvnw verify` and `./mvnw verify -Pintegration` pass; the unit
  and integration test counts are at least `master`'s, and the item records both pairs of numbers.
- **Modulith still bites.** `ModularityTest` runs under Modulith 2.1.x, and a deliberately introduced
  cross-feature reference makes it fail (then is removed).
- **Coverage.** The JaCoCo gate over merged unit + IT data holds at its configured threshold.
- **Edges.** The gRPC registry IT (servlet transport on Tomcat 11), the rate-limit ITs (Bucket4j on
  Lettuce 7), the ShedLock-guarded jobs and the S3/MinIO upload ITs pass without being disabled or
  weakened.
- **Clean properties.** No configuration property in `src/main/resources` is reported as renamed or
  removed by `spring-boot-properties-migrator`, which is then removed from the pom.
- **Landed.** As `IMP-M11-02`.
- **Carried in from `IMP-M11-03` (session 168):** the ITs do not start. (1) Flyway does not run — Boot 4 split it into `spring-boot-starter-flyway` (`relation "app_user" does not exist`). (2) `netty.version` was moved to 4.2.17.Final (Lettuce 7 needs 4.2); confirm the AWS SDK `netty-nio-client` and the Trivy gate against it. (3) The JaCoCo merged check fails only because the ITs cannot boot. Unit tests: 216 run, 0 failed. Pre-migration IT baseline numbers: take them from `master` before `IMP-M11-02` (`ff4ee3b^`).
- **Result (session 169):** unit 216 run / 0 failed (master: 204 `@Test` methods); integration 314 run (317 annotated, same as master). Added `spring-boot-starter-flyway`; test and `ProblemType` `HttpStatus` constants renamed (`UNPROCESSABLE_CONTENT`, `CONTENT_TOO_LARGE`). `ModularityTest` fails on a deliberate `room`↔`chat` cycle and passes without it; no `properties-migrator` in the pom. **Environment caveat:** the 7 ITs that call `*.localhost` over real HTTP (`GameAssetControllerIT` ×6, `SeedDataIT` ×1) fail on this WSL host because the JDK cannot resolve `.localhost` names; they fail identically on pre-migration `master` (`ff4ee3b^`), so they are not a migration regression — `IMP-M11-08`'s pipelines are where they run for real. Two Testcontainers start-up timeouts seen in the full run passed on rerun.

### IMP-M11-05 — `turnbase-game-host` compiles on Spring Boot 4.1.1 with Jackson 3 host-side

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M11-01

**Build on exit:** may be red — tests may fail until `IMP-M11-06`; `main` sources must compile and the
guest-bridge comparison must hold.

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§1, §2, §5 R1, R4, R7, R10)
- `docs/specs/game-host/game-host-internals.md` (§4–§5: the guest bridge and serialization)
- `docs/specs/manifest/bundle-format.md` (F4)

**Satisfies:** `platform-architecture.md` CON-010; `platform-operations.md` FR-CICD-010

**Done when:**
- **Versions.** `spring-boot-starter-parent` is `4.1.1`; starters use their Boot 4 names; the
  `dependabot.yml` ignore entry is rewritten as in `IMP-M11-02`; README and the repo's `CLAUDE.md`
  name Boot 4.1.
- **Host JSON.** Host-side code (outside the guest bridge) imports no `com.fasterxml.jackson.databind`
  or `.core`; it uses Boot 4's Jackson 3 mapper.
- **Guest untouched.** The guest bridge jar's dependency list — in particular every
  `com.fasterxml.jackson.*` coordinate and version — is identical before and after, compared by a
  recorded `dependency:tree` or jar listing from `master` and from the branch. The shade/repackage
  configuration that keeps it out of `BOOT-INF/lib` (`pom.xml`) still produces the same layout.
- **Compiles.** `./mvnw -DskipTests verify` passes with Error Prone/NullAway at full severity.
- **Landed.** As `IMP-M11-02`.
- **Result (session 170):** `turnbase-game-host` `master` (`d19e739`): parent 4.1.1, `starter-webmvc`, Testcontainers 2 artifact names, `tomcat.version` override removed, dependabot/README/CLAUDE.md updated. Host JSON (`dispatch/TeamsJson`, `SessionRecordCodec`, `EnvelopeCodec`) on Jackson 3; `HostJacksonImportsTest` guards it. **The `bridge` package keeps Jackson 2 by design** — it is shaded into the guest — so "outside the guest bridge" excludes it. **Guest comparison:** `jackson-2-bom.version` pinned to 2.21.4 (Boot 4.1.1 would manage 2.21.5); guest-bridge jar file layout and Jackson coordinates (databind/core 2.21.4, annotations 2.21, parameter-names 2.21.4) identical to the 3.5.16 build. `./mvnw verify`: compiles, Spotless/Error Prone/NullAway clean; unit 57 run, 5 errors — all protobuf gencode `NoClassDefFound` on `io.turnbase.grpc.gamehost.v1.*` (platform's fix: pin `protobuf-java` to turnbase-common's gencode, as in `c2869d4`) — **`IMP-M11-06` owns it.**

### IMP-M11-06 — Game Host unit and integration tests are green on Boot 4

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M11-05

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§4, §5 R4, R9)
- `docs/specs/game-host/game-host-internals.md` (§4–§5)

**Satisfies:** `platform-operations.md` FR-CICD-003

**Done when:**
- **Green locally**, with unit and integration counts recorded and at least `master`'s.
- **Guest round-trip.** The Espresso tests that load a real game JAR, run a move and round-trip its
  state through the guest-side serializer pass unchanged.
- **Landed.** As `IMP-M11-02`.
- **Result (session 171):** `turnbase-game-host` `master` (`03f4c39`): pinned `protobuf-java` 4.36.0 (turnbase-grpc gencode) and `netty.version` 4.2.17.Final (Lettuce 7 needs `MultiThreadIoEventLoopGroup`; the 4.1.137 CVE pin broke every Redis IT). `./mvnw verify -Pintegration` green: unit 57 + IT 17 = 74 run, equal to the 74 `@Test` methods now (pre-migration `master`: 73, +1 `HostJacksonImportsTest`) — no drop. Guest round-trip: `GameBridgeClientEspressoTest`, `EspressoIsolationTest`, `SessionDispatcherIT` pass unchanged; JaCoCo merged check met.

### IMP-M11-07 — The local stack and the acceptance suite run on both Boot 4 branches

**Repo:** `turnbase-frontend` (suite only; no frontend change expected), `turnbase-platform`,
`turnbase-game-host` · **Depends on:** IMP-M11-04, IMP-M11-06

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§5 R11, R12, R14)
- `docs/specs/deployment/local-environment.md`
- `docs/specs/deployment/observability.md` (the metric names dashboards and alerts depend on)

**Satisfies:** `platform-operations.md` FR-CICD-010; `platform-operations.md` CON-001

**Done when:**
- **Stack.** The compose stack starts with images built from `master` of both repositories, twice: on a
  fresh database, and on a database migrated by the current `master` images (Flyway 12 continues it).
- **Suite.** The frontend acceptance suite (`make e2e`) passes against that stack with no new
  failures relative to a pre-migration run, and a full Tic-Tac-Toe game plays to an outcome.
- **Observability.** Every metric name `observability.md` names is present in the platform's and the
  Game Host's `/actuator/prometheus`; a trace for one REST request reaches Tempo.
- **Scan.** A local `trivy fs` and `trivy image` at severity `CRITICAL` report zero findings for both
  repositories. A finding with no fix opens a gate under FR-CICD-010 instead.
- **Result (session 172):** images built from `master` of both repos. Stack up on a fresh DB (Flyway applied both migrations) and on a DB first migrated by the pre-migration images (`ff4ee3b^`, `21a5544`; Flyway 12 validated, "up to date"). `make e2e`: 52 passed pre-migration, 52 passed on Boot 4; `driver.mjs game` and `drop` play Tic-Tac-Toe to an outcome. Observability: every `observability.md` metric name is present on `/actuator/prometheus` of platform and Game Host **except** `http_server_requests_seconds_bucket` and `spring_data_repository_invocations_seconds`, which the pre-migration build does not emit either (no histogram config; no repository metrics) — pre-existing drift, not a migration regression (`HighLatencyP95` has no data). Lettuce metrics were renamed (`lettuce_command_*` → `lettuce_seconds`, `lettuce_active_seconds`); no spec names them. A REST trace (`GET /api/games`, fixed `traceparent`) is retrievable from Tempo. **Trivy:** the image scan found Tomcat 11.0.24 CRITICAL (CVE-2026-65182, -65905, -68525; fixed in 11.0.25) in both images; fixed by pinning `tomcat.version` 11.0.25 (platform `9a71a57`, game-host `990e8b7`); unit tests green (216 / 57); `trivy image` and `trivy fs` (with `~/.m2` mounted — Maven Central rate-limited the scanner) report 0 CRITICAL for both.

### IMP-M11-08 — Both pipelines are green on Spring Boot 4

**Repo:** `turnbase-platform`, `turnbase-game-host`, `turnbase` · **Depends on:** IMP-M11-07

**CI wait:** required — the only M11 item that waits for the pipeline.

**Read first:**
- `docs/decisions/0016-spring-boot-4-migration.md` (§4, §6)

**Satisfies:** `platform-operations.md` FR-CICD-010

**Done when:**
- **Green.** The `build` workflow on `master` of `turnbase-platform` and of `turnbase-game-host` is
  green, including both Trivy gates (dependency and image). A failure is fixed on a short-lived branch
  and re-run; a finding with no fix opens a gate under FR-CICD-010 instead.
- **Bumped.** Both submodule refs in this repository point at the green commits.
- **Unpaused.** `IMP-M10-01`'s `**Remaining:**` (green pipeline, ref bump) is satisfied and it is marked
  `DONE`; STATUS names M10 as the open milestone again.
- **Result (session 173):** `build` green on `master` — platform `9a71a57` (build + e2e jobs), game-host `990e8b7`; all four Trivy steps (dependency and image, report and gate) succeeded in both. Refs already pointed at those commits. `IMP-M10-01` is `DONE`; M10 is unpaused.

---
