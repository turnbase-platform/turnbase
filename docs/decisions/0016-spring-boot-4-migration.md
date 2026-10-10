# ADR-0016: Both Spring Boot services move to Spring Boot 4.1

- **Status:** Accepted
- **Date:** 2026-10-10
- **Deciders:** Project owner
- **Supersedes:** the "Spring Boot 3.5+" version line in `CLAUDE.md`, [ADR-0012](0012-repo-strategy-polyrepo-submodules.md)'s
  repository table, and each requirements document's backend constraint (`platform-operations.md`
  CON-001 and its copies)
- **Amends:** [ADR-0012](0012-repo-strategy-polyrepo-submodules.md) *Pull requests are suspended* — one
  named migration branch per repository may outlive a session (§4 below)
- **Relates to:** [ADR-0014](0014-modular-monolith-spring-modulith.md) (Spring Modulith moves 1.4 → 2.x),
  [ADR-0015](0015-static-analysis-error-prone-nullaway.md) (NullAway meets Spring 7's JSpecify annotations)
- **Executed by:** milestone **M11** in [`registry.md`](../implementation/registry.md) (`IMP-M11-01…08`)

## Context

On 2026-10-10 `IMP-M10-01` merged to `turnbase-platform` `master` and the pipeline went red on the
Trivy dependency gate alone: **CVE-2026-47884 and CVE-2026-47890**, both CRITICAL (remote code
execution) in `org.springframework:spring-webmvc` 6.2.19. The only fixed version listed is Spring
Framework **7.0.9**. Spring Boot 3.5.16 is the last 3.5.x release and manages 6.2.19; no 6.2.20 exists.
`platform-operations.md` FR-CICD-010 fails the build on any CRITICAL finding, so neither the platform
nor any item after it can reach `DONE`. This was opened as `IMP-GATE-97`.

`turnbase-game-host` is exposed identically — it also inherits Boot 3.5.16 and declares
`spring-boot-starter-web`. Its last green run (2026-10-01) predates the advisories; its next push goes
red on the same gate.

Two ways out were weighed. A **dated waiver** in FR-CICD-010 keeps the stack and accepts a known
RCE in a public-facing servlet stack with no upstream fix on the line we are pinned to — it never
expires on its own, because 6.2.x is not going to receive one. **Moving to Spring Boot 4** is the
only path on which the gate goes green without an exception, and the Boot 3.5 line is at its end
regardless: every future Spring CVE will land in the same place.

Boot 4 is not a patch upgrade. It is a new generation: Spring Framework 7, Jakarta EE 11 (Servlet 6.1,
Tomcat 11), Jackson 3 as the default JSON stack, a modularised auto-configuration (one module and one
starter per technology, with package moves), JUnit 6, Testcontainers 2, Spring Data 2026.x with
Lettuce 7, and Micrometer 1.17. This ADR records the decision and the migration procedure; the work is
the M11 milestone.

## Decision

### 1. Target: Spring Boot **4.1.1**, a GA release

Both Spring Boot services — `turnbase-platform` and `turnbase-game-host` — move to
`spring-boot-starter-parent` **4.1.1**, which manages Spring Framework 7.0.9 (the CVE fix), Tomcat
11.0.24, Jackson 3.1.5 (plus Jackson 2.21.5 via `jackson-2-bom`), Spring Security 7.1.1, Spring Data
2026.0.1, Lettuce 7.5.2, Flyway 12.4.0, Micrometer 1.17.1, OpenTelemetry 1.62.0, Hibernate Validator
9.1.3, JUnit Jupiter 6.0.3 and Testcontainers 2.0.5. Spring Modulith moves to the **2.1.x** line, the
first that targets this Boot generation (1.4.13 was pinned in `IMP-M0-05` precisely because 2.1.1 is
binary-incompatible with Boot 3.5).

**Only GA releases.** Milestones (`-M1`, `-M2`: feature-incomplete previews) and release candidates
(`-RC1`) are never a target — `4.2.0-M2` was considered and rejected on that ground. A 4.0.x target
was also rejected: it carries the same Framework fix, but leaves a 4.0 → 4.1 hop owed immediately.

Java stays at **21** for both services, and the Game Host stays on GraalVM CE for JDK 21. Boot 4
requires Java 17+, so this ADR changes neither.

### 2. Host-side JSON is Jackson 3; guest-side JSON stays Jackson 2

All **host** code — the platform, and the Game Host's own Spring side — moves to Jackson 3
(`tools.jackson.*`): `JsonMapper` instead of `ObjectMapper`, the unchecked `JacksonException` instead
of `JsonProcessingException`, and Boot 4's auto-configured mapper rather than a Jackson 2 bean. The
`spring-boot-jackson2` compatibility module is **not** used: it is a deprecated bridge, and adopting it
would defer the same migration with interest.

Three things stay on Jackson 2 deliberately, and the migration must not move them:

- **The guest side of the Game Host.** Game code is serialized by Jackson 2 running *inside* the
  Espresso guest, and `com.fasterxml.jackson.annotation.*` is part of the published GDK contract
  (`game-host-internals.md` §4–§5, `bundle-format.md` F4, `backend-gdk-api.md`). The guest bridge jar's
  Jackson version is pinned by `turnbase-sdk`'s serialization component, not by Boot, and must come
  out of the migration byte-identical unless a separate decision changes it.
- **`jjwt-jackson`**, which is compiled against Jackson 2 and brings its own `jackson-databind`.
  It is an implementation detail of JWT parsing and never sees a Spring-managed mapper.
- **`jackson-annotations`.** Jackson 3 keeps the `com.fasterxml.jackson.annotation` package, so
  `@JsonInclude`, `@JsonProperty` and `@JsonIgnoreProperties` imports do not change.

**The wire format must not change.** Jackson 3 changed several defaults relative to Jackson 2. Every
REST body, STOMP frame, Redis value and `jsonb` column the platform writes today must round-trip
identically after the move; where a Jackson 3 default differs, the platform's mapper sets the Jackson 2
behaviour explicitly rather than letting a default leak onto the wire.

### 3. Scope

| Repository | In scope | Why |
|---|---|---|
| `turnbase-platform` | yes | the failing Trivy gate |
| `turnbase-game-host` | yes | same `spring-webmvc` 6.2.19; red on its next push |
| `turnbase-common` | no | gRPC stubs only, no Spring. Its `grpc.version` pin is unchanged |
| `turnbase-sdk` | no | no Spring; the guest-side Jackson 2 pin lives here and is held still |
| `turnbase-frontend`, `turnbase-game-tictactoe` | no | no Maven dependency on Boot |

### 4. Procedure: one migration branch per repository, CI paused until local green

**The branch.** Each in-scope repository carries one branch, **`chore/boot4`**, cut from `master`.
It is the single exception to ADR-0012's *"merged and deleted within the session that created it"*:
it may live across sessions for the duration of M11, and it **is pushed to the remote** so that no
session's work exists only on one machine. Every other ADR-0012 rule still holds — no pull request is
opened, `master` stays linear, and the branch is merged `--ff-only` and deleted locally and on the
remote by `IMP-M11-08`. Nothing else may be named `chore/boot4`, and no other branch may outlive a
session on the strength of this exception.

**`master` is frozen for these two repositories while M11 is open.** M10 is paused (§6), so no other
work lands on either `master`; a freeze is what makes the final fast-forward possible without a
rebase of a migration-sized diff.

**CI is paused, not skipped.** The `build` workflow runs only on pushes to `master` (and on pull
requests, which are suspended), so pushing `chore/boot4` runs nothing — this is the intended state.
`IMP-M11-02…07` are judged on **local** evidence: `./mvnw spotless:apply`, `./mvnw verify` and
`./mvnw verify -Pintegration` green on the branch, run from a clean checkout. The pipeline — including
both Trivy gates — is first exercised by `IMP-M11-08`, which merges the branch and must see it green.
Until then, `turnbase-platform` `master` stays red on the gate and neither submodule ref moves in this
repository.

**Order.** The corpus is updated first (`IMP-M11-01`), so every later item builds against documents
that already say Boot 4. Then each repository in three steps — *compiles*, *host JSON migrated*,
*tests green locally* (platform `02`–`04`, Game Host `05`–`06`) — then the running stack end to end
(`07`), then the merge and the pipeline (`08`).

### 5. Known risks

Each risk names the item that owns retiring it. A risk that turns out to need a decision the
documents do not make is a `spec-defect`, not a judgement call on the branch.

| # | Risk | What could break | Mitigation / evidence | Owner |
|---|---|---|---|---|
| R1 | **Jackson 3 API migration** | ~24 platform main classes and ~40 test classes inject or build `com.fasterxml.jackson.databind.ObjectMapper`; 6 Game Host files use Jackson host-side. Boot 4 auto-configures no Jackson 2 mapper, so these fail at context start, not at compile time | Migrate to `JsonMapper`/`JacksonException`; a guard test (or ArchUnit rule) that host code imports no `com.fasterxml.jackson.databind` | `03`, `05` |
| R2 | **Jackson 3 default drift on the wire** | Changed defaults (date/time format, unknown-property and null handling, ordering) silently change REST/STOMP/Redis/`jsonb` payloads; the frontend and the stored data disagree with the server | Golden-payload round-trip tests for representative REST bodies, STOMP frames, Redis values and `jsonb` columns, written against the 3.5 build first; defaults pinned explicitly in the mapper customizer | `03`, `04` |
| R3 | **`StreamReadConstraints` moves** | `input-validation.md` relies on Jackson's nesting/size constraints to stop a deep-nesting body; in Jackson 3 the type moves to `tools.jackson.core` and its configuration path changes. A silently dropped limit is a DoS regression | A deep-nesting body is rejected on the branch (a test is added by `04` if none exists); `input-validation.md` names the constraint generically | `01`, `04` |
| R4 | **Guest-side Jackson 2 drifts with the BOM** | Boot 4 manages `jackson-2-bom` 2.21.5; if the guest bridge or `turnbase-serialization` resolves Jackson from the Boot BOM, the Jackson inside Espresso changes and with it what games can round-trip (`bundle-format.md` F4) | The guest bridge jar's Jackson coordinates are compared before and after; any change fails `05` | `05` |
| R5 | **Spring Modulith 1.4 → 2.1** | API and verification changes; `ModularityTest` stops detecting a boundary violation (it has been silently absent before — `IMP-M0-05`) | `ModularityTest` runs and fails on a deliberately introduced violation, then passes | `02`, `04` |
| R6 | **Tomcat 10.1 → 11 (Servlet 6.1)** | `grpc-servlet-jakarta`, which serves the platform's Game Host registry (`GrpcServletConfig`); trailers/HTTP-2 behaviour; the `tomcat.version` CVE override (10.1.59) becomes wrong and must be removed; body-size limits | The `tomcat.version` override is deleted; the gRPC registry IT and the body-size ITs pass | `02`, `04` |
| R7 | **Boot modularisation** | Auto-configuration classes move packages (`RedisConnectionDetails`, `RedisAutoConfiguration`, `ServletRegistrationBean`, `TomcatServletWebServerFactory`, `WebServerFactoryCustomizer` are all imported today); `spring-boot-starter-web` becomes `-webmvc`; configuration properties are renamed | Compiler errors find the moves; `spring-boot-properties-migrator` on the branch (removed before `08`) finds renamed properties | `02`, `05` |
| R8 | **Third-party libraries outside the Boot BOM** | `bucket4j_jdk17-lettuce` 8.19.0 is compiled against Lettuce 6, now 7.5; ShedLock 7.7.0, `logstash-logback-encoder` 8.1, AWS SDK 2.54, `jjwt` 0.12.6, icu4j, Bouncy Castle against Spring 7 | Each checked against its release notes; rate-limit, lock and S3 ITs exercise them for real. A library with no Spring-7-compatible release is a `spec-defect` | `02`, `04` |
| R9 | **Test stack: JUnit 6, Testcontainers 2** | Testcontainers 2 renames its modules (`org.testcontainers:postgresql`, `junit-jupiter`, `minio` → `testcontainers-*`); surefire/failsafe and JaCoCo must still see merged unit + IT data | Test counts on the branch are compared with `master`'s; a drop is a failure, not a pass | `04`, `06` |
| R10 | **NullAway against Spring 7** | Spring 7 annotates its API with JSpecify; overriding or calling it surfaces new NullAway errors (ADR-0015 keeps them as errors) | Fixed in code, never by downgrading the check or widening `ExcludedFieldAnnotations` | `02`, `05` |
| R11 | **Observability drift** | Micrometer 1.17 / OTel 1.62 / Boot 4's OpenTelemetry auto-configuration change property names or metric/tag names; Grafana dashboards and alert rules in `observability.md` go blank | Actuator `prometheus` output compared before/after for the metric names `observability.md` names; traces reach Tempo in the local stack | `07` |
| R12 | **Flyway 11 → 12** | Startup migration on an existing database (ADR-0011's forward-only, backward-compatible rule) | The local stack starts on a database migrated by the 3.5 build, and on an empty one | `07` |
| R13 | **Branch drift and a long-lived diff** | `chore/boot4` diverges from `master` and the final merge is not a fast-forward | `master` frozen for both repos while M11 is open (§4); `08` merges `--ff-only` | `08` |
| R14 | **Trivy finds a new CRITICAL in the Boot 4 tree** | The point of the migration is a green gate; Tomcat 11.0.24, Netty 4.2.17 and the rest are new to the scan | A local `trivy fs` run on each branch before `08`; a finding with no fix is a new gate under FR-CICD-010 | `07`, `08` |

### 6. M10 is paused until M11 is done

Every `IMP-M10-*` item gains `IMP-M11-08` as a dependency. The fixes M10 carries are worth less than
a pipeline that can certify them, and building them on Boot 3.5 code that M11 is rewriting would
force each to be ported twice. `IMP-M10-01`, already merged on `master`, finishes with `IMP-M11-08`:
its `**Remaining:**` line (a green pipeline and the ref bump) is exactly what `08` delivers.

## Consequences

- The stack line in `CLAUDE.md`, ADR-0012 and the requirements' backend constraints reads
  **Spring Boot 4.1+** from `IMP-M11-01` onward — ahead of the code, as for any other specification.
  For the duration of M11 the documents describe the target and `master` of the two repositories
  describes 3.5.16; the M11 section of the registry is where that gap is visible.
- `IMP-GATE-97` is closed by this ADR. FR-CICD-010 is unchanged: the gate is satisfied by upgrading,
  not waived.
- Each repository's `dependabot.yml` `ignore` entry for `spring-boot-starter-parent >= 4.0.0` is
  rewritten by the migration, not deleted — its comment records *why* a major is a deliberate decision.
- Jackson 2 remains on the Game Host's runtime classpath for the guest bridge and `jjwt`. That is the
  intended state, not leftover debt.
