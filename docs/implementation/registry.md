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

Paths in *Read first* are relative to the repository root. Closed milestones (M0–M19) are in [`archive/`](archive/); see [INDEX.md](INDEX.md) *Archive*.

**[`conventions.md`](conventions.md) applies to every item and is not repeated in read-lists.**
Package layout, Spotless, test suffixes, JaCoCo, branch and commit format, and cross-repo version
pinning are settled there. Items name it only where they are the item that *establishes* it.

---

## Closed milestones

Every item of these is `DONE` (or `CANCELLED`). Their sections and register rows live in [`archive/`](archive/), verbatim; a session does not read them unless an item's read-list names one.

| Milestone | Items | Archive |
|---|---|---|
| M0 — Bootstrap | 12 | [`archive/M0-bootstrap.md`](archive/M0-bootstrap.md) |
| M1 — Accounts and sessions | 11 | [`archive/M1-accounts-and-sessions.md`](archive/M1-accounts-and-sessions.md) |
| M2 — Rooms and realtime | 12 | [`archive/M2-rooms-and-realtime.md`](archive/M2-rooms-and-realtime.md) |
| M3 — Game execution | 13 | [`archive/M3-game-execution.md`](archive/M3-game-execution.md) |
| M4 — Catalog and upload | 5 | [`archive/M4-catalog-and-upload.md`](archive/M4-catalog-and-upload.md) |
| M5 — History, statistics, notifications | 4 | [`archive/M5-history-statistics-notifications.md`](archive/M5-history-statistics-notifications.md) |
| M6 — Platform frontend | 7 | [`archive/M6-platform-frontend.md`](archive/M6-platform-frontend.md) |
| M7 — MVP review remediation | 13 | [`archive/M7-mvp-review-remediation.md`](archive/M7-mvp-review-remediation.md) |
| M8 — Regression review remediation and MVP view completeness | 18 | [`archive/M8-regression-review-remediation-and-mvp-vi.md`](archive/M8-regression-review-remediation-and-mvp-vi.md) |
| M9 — MVP completeness audit remediation | 11 | [`archive/M9-mvp-completeness-audit-remediation.md`](archive/M9-mvp-completeness-audit-remediation.md) |
| M10 — E2E & security audit remediation | 24 | [`archive/M10-e2e-security-audit-remediation.md`](archive/M10-e2e-security-audit-remediation.md) |
| M11 — Spring Boot 4 migration | 8 | [`archive/M11-spring-boot-4-migration.md`](archive/M11-spring-boot-4-migration.md) |
| M12 — TurnBase visual identity | 11 | [`archive/M12-turnbase-visual-identity.md`](archive/M12-turnbase-visual-identity.md) |
| M13 — Prototype fidelity | 8 | [`archive/M13-prototype-fidelity.md`](archive/M13-prototype-fidelity.md) |
| M14 — Game start resilience | 3 | [`archive/M14-game-start-resilience.md`](archive/M14-game-start-resilience.md) |
| M15 — Load and scalability testing, Phase A | 13 | [`archive/M15-load-and-scalability-testing-phase-a.md`](archive/M15-load-and-scalability-testing-phase-a.md) |
| M16 — Pre-Phase-B fixes | 15 | [`archive/M16-pre-phase-b-fixes.md`](archive/M16-pre-phase-b-fixes.md) |
| M17 — Database capacity | 5 | [`archive/M17-database-capacity.md`](archive/M17-database-capacity.md) |
| M18 — Load testing Phase B: capacity and autoscaling | 17 | [`archive/M18-load-testing-phase-b-capacity-and-autosc.md`](archive/M18-load-testing-phase-b-capacity-and-autosc.md) |
| M19 — The immersive game room | 1 | [`archive/M19-the-immersive-game-room.md`](archive/M19-the-immersive-game-room.md) |

---

## Register

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| **M20 — Refinement** ||||
| IMP-M20-01 | Registry archive: closed milestones out of the session's way | docs | — | DONE |
| IMP-M20-02 | `STATUS.md` reset to the present | docs | M20-01 | DONE |
| IMP-M20-03 | `CLAUDE.md` trim, counts checked, memory aligned | docs | M20-02 | DONE |
| IMP-M20-04 | Code maps: one checked `ARCHITECTURE.md` per service | platform, game-host, frontend, sdk, docs | — | DONE |
| IMP-M20-05 | Code→spec references checked by the corpus checker | docs, platform, frontend | — | DONE |
| IMP-M20-06 | Claude tooling review: permissions, skills, language server | docs | M20-01 | DONE |
| IMP-M20-07 | An honest build: green locally, verified submodule refs | frontend, 7WD, docs | — | DONE |
| IMP-M20-08 | `scripts/test-cost.sh` and the test-cost baseline | docs | — | DONE |
| IMP-M20-09 | Platform ITs share one set of containers | platform | M20-08 | DONE |
| IMP-M20-10 | Platform ITs share a cached Spring context | platform | M20-09 | PARTIAL |
| IMP-M20-11 | Measurements leave the default build (`perf` tag) | platform, game-host | M20-08 | READY |
| IMP-M20-12 | Platform IT overlap pass | platform | M20-10 | READY |
| IMP-M20-13 | One Trivy scan per target | platform, game-host, frontend, sdk, common | — | READY |
| IMP-M20-14 | `RoomRepository` split by concern | platform | M20-10 | READY |
| IMP-M20-15 | ADR-0021: deployment profiles | docs | — | READY |
| IMP-M20-16 | Recovery from a full stop | platform, docs | M20-15 | READY |
| IMP-M20-17 | Startup time measured, class-data sharing tried | platform, game-host | — | READY |
| IMP-M20-18 | `OQ-6`: twelve Espresso contexts per JVM | game-host, docs | — | READY |
| IMP-M20-19 | Platform thread growth under sustained load explained | platform, docs | — | READY |
| IMP-M20-20 | Open-question triage and the backlog | docs | — | READY |
| IMP-M20-21 | Credits for games based on existing games | docs, sdk, platform, frontend, 7WD | — | READY |
| IMP-M20-22 | Load-test record tidy | docs | M20-20 | READY |

**232 live items.** `IMP-M20-01…22` were added 2026-11-04 from the refinement spike ([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../reviews/2026-11-04-refinement-spike/INDEX.md)): the files a session reads first, checked code maps and references, an honest and cheaper build, code and architecture debt, manifest credits; see the M20 section. `IMP-M19-01` (the immersive game room) was added 2026-10-27. `IMP-M18-01…17` were added 2026-10-24 by the Phase B design round ([`load-testing-phase-b.md`](../specs/deployment/load-testing-phase-b.md)): spec groundwork (`01`), capacity on one node with the cores reallocated to PostgreSQL (`02…07`), the Platform scaling out with room affinity and a two-replica minimum (`08…10`), the Game Host spreading, `OQ-5` by measurement and KEDA autoscaling (`11…13`), and the harness and runs (`14…17`); see the M18 section. `IMP-M17-01…05` were added 2026-10-22 from the M16 re-verification, in which the database was the first thing to break (`platform-operations.md` FR-DBQ-*, NFR-DBQ-*): the sweep re-read (`01`), history-independent game-path queries (`02`), an explicit pool size (`03`), the pool size measured (`04`) and the re-verification runs (`05`); see the M17 section. `IMP-M16-01…15` were added 2026-10-19 from the 18 findings of Phase A ([`load-testing.md`](../specs/deployment/load-testing.md) §13): the harness and record corrections (`01`), the Game Host wedge and boot fixes (`02…06`), the platform's room ownership, Redis keys, scans and threads (`07…10`), the subscribe race and the 300 s stall (`11`, `12`), the CPU profile (`13`) and the two re-verification runs (`14`, `15`); see the M16 section. `IMP-M15-01…13` were added 2026-10-18 by the load-testing design ([`load-testing.md`](../specs/deployment/load-testing.md)): the spec groundwork and the four fixes the chart and the platform need before anything can be measured (`01…06`), the k6 harness and its scenarios (`07…10`), and the baseline runs, split into three run items so that none outlasts a session (`11…13`); see the M15 section. `IMP-M14-01…03` were added 2026-10-17 by ADR-0018: a game start that survives a cold, restarting or wedged Game Host and shows its progress; see the M14 section. `IMP-M13-01…08` were added 2026-10-12 after the owner reviewed the running M12 build and found it did not match the approved prototype: see the M13 section. `IMP-M12-01…11` were added 2026-10-11 by [ADR-0017](../decisions/0017-turnbase-visual-identity.md): the approved prototype look replaces the stock Astryx theme across every view while the services, reducers and sockets stay as they are (see the M12 section). Before them, 137 live items. `IMP-M11-01…08` were added 2026-10-10 by [ADR-0016](../decisions/0016-spring-boot-4-migration.md), closing `IMP-GATE-97`: both Spring Boot services move to Boot 4.1.1 because two CRITICAL `spring-webmvc` CVEs have no fix on the 3.5 line. **M11 runs before M10** — every `IMP-M10-*` item depends on `IMP-M11-08` — and its items are judged locally with CI not awaited (see the M11 section). `IMP-M10-01…24` were added 2026-10-10 from the
[E2E & security audit](../reviews/2026-10-10-e2e-security-audit/INDEX.md) (`AUD-01…24`), the first
black-box run of the full stack after the build plan reached 105: two Critical cross-user breaches
(`IMP-M10-01` the ownerless-upload hole closed by `IMP-GATE-96`, `IMP-M10-02` the wildcard-subscribe
queue leak), six High (auth-control bypasses, the public-edge gRPC reachability, the chunked-body
limit, and the cold-start Game Host wedge), seven Medium and nine Low/Info hardening and polish items.
One finding (join-by-code vs. visibility) was reproduced and confirmed **as specified** — no item. `IMP-M9-01…11` were added 2026-10-04 from the [MVP completeness audit](../reviews/2026-10-04-mvp-completeness-audit/INDEX.md) (`CA-01…CA-10`): the invite-friends control and the `owner` filter the MVP still lacks, the reference game's missing outcome, the clipped catalog action, the late forfeit dispatch, the settings gaps, one spec decision, polish, and the suite that pins them. `IMP-M8-01…16` were added 2026-10-03 from the [MVP regression review](../reviews/2026-10-03-mvp-regression-review/INDEX.md): five close its backend and game findings, nine give every MVP view a minimal working UI (the game room is `IMP-M8-10`), and the last two close the client follow-up and re-run the review as a suite. `IMP-M7-01…13` were added 2026-10-01 from the [MVP implementation review](../reviews/2026-10-01-mvp-implementation-review/INDEX.md): the first four close its MR-01 (the room views `IMP-M6-04`/`05` did not build), the rest close MR-02…MR-11 and add the acceptance suite the review was run by hand. IMP-M6-07 is cancelled: IR-23 cut the onboarding wizard from v1, so
`onboarding-wizard.md`'s FR-ONB-* and NFR-ONB-* have no implementing item by design. The heading is
kept below so the number is never reused. `IMP-M3-12` was added 2026-08-22, closing IMP-GATE-05 — see
its section under M3. `IMP-M3-13` was added 2026-09-30, closing IMP-GATE-91 — see its section under M3. `IMP-M1-10` was added 2026-09-06, closing IMP-GATE-26, and `IMP-M1-11` on
2026-09-26, closing IMP-GATE-78 — see their sections under M1.

Statuses are seeded as `READY`. **No item is gated** — the 2026-08-16 audit's 23 blockers are all
closed (see *Readiness gates* at the end for what each fix changed). An item's real status is
whatever its own *Depends on* implies.

---

## M20 — Refinement

Opened 2026-11-04 from the refinement spike
([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../reviews/2026-11-04-refinement-spike/INDEX.md),
findings `RS-*`), approved by the owner the same day. It changes how the system is tested, documented and
navigated, not what it does, except where an item says so by name (`21`). Public release is M21; cloud
deployment is M22; Phase C load work is not here.

**Milestone rules** (the owner's, from the approved design):

- **Judged locally.** GitHub Actions is refused for billing (`RS-07`). *Done when* is judged on the owner's
  machine, as M11 did (ADR-0016 §4): the repository's own build, a measured number, a checker exit code, a
  grep that returns nothing. When CI runs again, the first green `master` run is recorded on the item, not
  awaited by it; a submodule ref is bumped once that repository's full build passes locally.
- **Speed claims carry numbers:** before and after, from `scripts/test-cost.sh` (`08`), on the same machine.
- **Test counts fall only in `12`**, and only with the covering test named for each removed one.
- **A refactor that changes behaviour is a defect** unless the item names the change.
- **Every new document that names code is checked by a script**, or it rots: `04`, `05`, `03`.
- `IMP-*` references in code and session numbers in commits **stay**, as provenance (owner, `RS-05`).

Order: `01` → `02` → `03`, `06` after `01`; `04`, `05` any time. `07`, `08` any time, then `09` → `10` →
`12` and `14`; `11`, `13` free. Stream C and D items are best taken after `01`–`03`, so that their sessions
start on the trimmed files.

### IMP-M20-01 — Registry archive: closed milestones out of the session's way

**Repo:** `turnbase` (umbrella; `.claude/skills/work-item`) · **Depends on:** —

**Read first:** this file's header and register; `INDEX.md` (this directory) *Where status lives* and
*Milestone map*; `scripts/check-corpus.py` (`check_registry`); `.claude/skills/work-item/SKILL.md`.

**Settled:** the item sections of every closed milestone (M0–M19) move to `docs/implementation/archive/`,
one file per milestone, verbatim. `registry.md` keeps the field definitions, the register rows of open
milestones, one line per closed milestone linking its archive, and the readiness gates. Nothing is deleted:
the archive is the record, and 221 `IMP-*` identifiers are cited from specs, requirements and ADRs.

**Done when:**
- `registry.md` is under 600 lines; each archive file is registered in `INDEX.md` *Files*.
- `check-corpus.py`'s `registry` check enforces its invariants over the register and the archives, and a new
  check resolves every `IMP-*` identifier cited anywhere in `docs/` to a section in the register or an
  archive; a planted bad identifier fails it.
- The `work-item` skill says where a closed item's text lives and that a session does not read the archive
  unless an item's read-list names it.
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-02 — `STATUS.md` reset to the present

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M20-01

**Read first:** `STATUS.md`; `conventions.md`; the submodules' `CLAUDE.md` files.

**Settled:** `STATUS.md` holds the last session summary, the current state (milestone, open items, what
is red) and the next priorities, nothing older. Each durable lesson in the removed text goes to
`conventions.md` or the submodule `CLAUDE.md` it concerns, or is judged spent; git history keeps the rest.

**Done when:**
- `STATUS.md` is under 80 lines.
- The commit body lists every harvested lesson and where it went, and names the ones judged spent.
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-03 — `CLAUDE.md` trim, counts checked, memory aligned

**Repo:** `turnbase` (umbrella); the project auto-memory · **Depends on:** IMP-M20-02

**Read first:** `CLAUDE.md`; `conventions.md` (to remove what `CLAUDE.md` restates); `scripts/check-corpus.py`.

**Settled:** *Current Phase* states the present in at most three lines and links the register; M19, M20 and
the `turnbase-game-7wonders-duel` submodule are reflected; nothing restates `conventions.md`. Every count
`CLAUDE.md` states (requirement documents, work items, repositories) is checked by a new `counts` check or
removed. The auto-memory (outside the repository) keeps only what `CLAUDE.md` cannot carry, or is emptied.

**Done when:**
- The `counts` check passes and fails on a planted wrong count.
- The memory contains no claim that contradicts `CLAUDE.md`; its state is reported in `STATUS.md`, since it
  cannot be checked from the repository.
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-04 — Code maps: one checked `ARCHITECTURE.md` per service

**Repo:** `turnbase-platform`, `turnbase-game-host`, `turnbase-frontend`, `turnbase-sdk`, `turnbase`
(umbrella) · **Depends on:** —

**Read first:** `docs/specs/flows/INDEX.md` and the flows it lists for sign-in, room create/join, a move,
game upload and Game Host failure; ADR-0014; each repository's `CLAUDE.md` and source tree.

**Settled:** each of the four repositories gains an `ARCHITECTURE.md`: its modules or packages with one
line of responsibility each, and the five flows traced through its packages and classes. The umbrella
gains a short system overview linking them and `docs/specs/flows/`. A map names code; it does not restate
the specifications.

**Done when:**
- A `code-maps` check (in `check-corpus.py` or beside it) resolves every class, package and path named in
  the maps, and fails on a planted rename.
- Each repository's build passes; `check-corpus.py` clean; merged and pushed, submodule refs bumped.

### IMP-M20-05 — Code→spec references checked by the corpus checker

**Repo:** `turnbase` (umbrella), `turnbase-platform`, `turnbase-frontend` · **Depends on:** —

**Read first:** `scripts/check-corpus.py` (`links`, `sections`); the spike INDEX `RS-14`.

**Settled:** a `code-refs` check scans the submodules' tracked sources for `*.md` file references and
`<file>.md §N` references and resolves them against the corpus and the repository's own documents. The
seven dangling references of `RS-14` are fixed in code (or the documents they meant are named).

**Done when:**
- `code-refs` is clean and fails on a planted bad file reference and a planted bad `§` reference.
- The touched repositories' builds pass; `check-corpus.py` clean; merged and pushed, refs bumped.

### IMP-M20-06 — Claude tooling review: permissions, skills, language server

**Repo:** `turnbase` (umbrella: `.claude/`) · **Depends on:** IMP-M20-01

**Read first:** `.claude/settings.json`; `.claude/skills/*/SKILL.md`; `.mcp.json`.

**Settled:** permissions pruned to what is still used; each skill re-read against the post-archive layout
and corrected; a language server (jdtls for Java, tsserver for TypeScript) tried on one real navigation
task in `turnbase-platform` and adopted or rejected on the measured difference (tool calls and time).

**Done when:**
- `settings.json` validates against its schema; each removed permission is listed in the commit body.
- The language-server decision and its measurement are one paragraph in `CLAUDE.md` (if adopted) or in
  `STATUS.md` (if rejected).
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-07 — An honest build: green locally, verified submodule refs

**Repo:** `turnbase-frontend`, `turnbase-game-7wonders-duel`, `turnbase` (umbrella) · **Depends on:** —

**Read first:** `conventions.md` §5 and §6; the spike INDEX `RS-07`, `RS-08`; each repository's workflow.

**Settled:** the frontend base image moves past CVE-2026-111497 (`brotli-libs`) and the `curl` HIGH. The 7WD
bootstrap secret is the owner's to provision; re-check it live (`gh secret list`) before reporting it
missing. The umbrella's refs move to commits whose full build passes locally (`turnbase-platform` 60e7489 is
ahead of the pinned f6d9df6).

**Done when:**
- Every repository's full build passes locally at the pinned ref; `trivy image` passes the gate on the
  frontend image.
- `git submodule status` names only commits verified in this item; `STATUS.md` lists, per repository, the
  last CI result and whether CI ran at all.
- Merged and pushed.

### IMP-M20-08 — `scripts/test-cost.sh` and the test-cost baseline

**Repo:** `turnbase` (umbrella: `scripts/`) · **Depends on:** —

**Read first:** `conventions.md` §3.

**Settled:** one script reads the surefire, failsafe and vitest reports of a repository (or all) and prints
the total per phase and the slowest classes and methods, as a table. It does not run the builds.

**Done when:**
- It runs against every repository with reports and prints the table; it fails clearly when a repository
  has none.
- The baseline (per repository: unit and integration totals, top ten classes) is recorded in `STATUS.md`
  for `09`–`12` to compare against.
- Merged and pushed.

### IMP-M20-09 — Platform ITs share one set of containers

**Repo:** `turnbase-platform` · **Depends on:** IMP-M20-08

**Read first:** `local-environment.md` §8; `conventions.md` §3; `PostgresIntegrationTest` and the other IT
base classes.

**Settled:** one Postgres, MinIO and Redis per test JVM (the singleton container pattern), started once
and reused by every IT class; isolation between classes stays whatever the tests already rely on (schema
reset, distinct keys), made explicit where it was implicit.

**Done when:**
- `./mvnw verify` passes with the failsafe test count unchanged.
- Failsafe time before and after, from `test-cost.sh`, in the commit body.
- Merged and pushed; ref bumped.

### IMP-M20-10 — Platform ITs share a cached Spring context

**Repo:** `turnbase-platform` · **Depends on:** IMP-M20-09

**Read first:** as `09`; ADR-0016 (Boot 4 test support).

**Settled:** the 44 hand-booted ITs move to a cached Spring test context, family by family (controller
ITs; jobs and sweeps; the rest), with as few distinct configurations as the tests allow. The ITs that need
their own boot (two instances, thread bounds, single-listener routing, boot behaviour) keep it and say why in
their Javadoc. The slow SSE tests of `NotificationControllerIT` (~30 s each) are explained and shortened if
the wait is the test's, not the system's. May be split into `10a`/`10b` when picked up.

**Done when:**
- `./mvnw verify` passes with the failsafe test count unchanged.
- Failsafe time at most half of the `08` baseline (Claude's target, not the owner's: if it is missed, the
  item says by how much and why).
- Merged and pushed; ref bumped.

**Remaining:** (session 269 built `SharedApplication` + `@UsesSharedApplication` in the test tree and moved
17 `@BeforeEach`-boot classes onto it: failsafe 590.8 s → ~503 s, 381 tests unchanged.) Still owed: the
hand-booted classes with no `@BeforeEach` boot (`GraceDeadlineSweepJobIT`, `MoveParticipantCacheIT`,
`RoomPurgeJobIT`, `RoomReconnectIT`, `RoomEventExecutorIT`, `RoomOwnershipServiceIT`,
`SweepSelectsOnlyRoomsItCanChangeIT`, `RoomSessionDetacherImplIT`, `GamePathQueryCostIT`,
`ReconciliationJobIT`, `SessionTeardownIT`, `GameHostRegistryServerIT`, `GameInputServiceIT`,
`InlineLeaveDispatchIT`); a Javadoc line saying why on every class that keeps its own boot
(`TwoInstanceIT`, `ThreadBoundsIT`, `SingleListenerOriginRoutingIT`, `TurnBaseApplicationIT`, `SeedDataIT`,
`RateLimitInterceptorIT`, `AuthMethodControllerIT`/`OAuthControllerIT` (stub port in the args),
`GameAssetControllerIT`; `GuestPurgeJobIT`/`NotificationPurgeJobsIT` already say so); the ~100 s of
`NotificationControllerIT` (SSE waits) explained and shortened; then the half-of-baseline target (≤ ~307 s) or
the shortfall and why. Caveat learned: a long-lived context's own scheduled jobs race fixtures (retention 0 s),
and `SharedApplication` must keep `pod:*:alive` and `platform:sentinel` in Redis.

### IMP-M20-11 — Measurements leave the default build (`perf` tag)

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M20-08

**Read first:** `conventions.md` §3; each listed test.

**Settled:** each of `EngineSharingBenchmarkIT`, `ConcurrentBootsIT`, `GameBridgeClientEspressoTest`,
`HostWedgeTest`, `GameHostWarmupTest`, `LoginServiceTimingTest`, `GamePathQueryCostIT`, `ThreadBoundsIT` and
`HttpLatencyHistogramIT` is judged: a regression guard for a requirement stays in the default build (made
cheaper if it can be); a measurement gets the JUnit tag `perf`, excluded by default and run by `-Pperf`.

**Done when:**
- Default `verify` excludes the moved tests; `./mvnw verify -Pperf` runs them and they pass.
- The judgement per test, with the requirement a kept test guards, is in the commit body.
- `conventions.md` §3 names the `perf` tag; merged and pushed; refs bumped.

### IMP-M20-12 — Platform IT overlap pass

**Repo:** `turnbase-platform` · **Depends on:** IMP-M20-10

**Read first:** the IT classes; `docs/requirements/INDEX.md` (to qualify IDs).

**Settled:** each IT class names in its Javadoc the requirements it protects, document-qualified. Where two
tests protect the same path through the same boot, one goes and the survivor is named.

**Done when:**
- Every IT class carries requirement IDs.
- Each removed test is listed in the commit body with the test that still covers it.
- Merged JaCoCo line coverage of `room`, `game`, `session` and `websocket` is not lower than before.
- Merged and pushed; ref bumped.

### IMP-M20-13 — One Trivy scan per target

**Repo:** every repository with a Trivy step · **Depends on:** —

**Read first:** `conventions.md` §6; each repository's workflow.

**Settled:** one scan per target produces both the report and the gate (one JSON or SARIF result, gated on
its severities), where today each target is scanned twice.

**Done when:**
- Each workflow scans each target once, with the gate's severities unchanged.
- The gate still fails on a known-bad image, shown locally (the frontend image before `07`'s fix, or a
  pinned old image).
- Merged and pushed in each repository; refs bumped.

### IMP-M20-14 — `RoomRepository` split by concern

**Repo:** `turnbase-platform` · **Depends on:** IMP-M20-10

**Read first:** `RoomRepository.java` and its callers; `room-lifecycle.md` §1; ADR-0008; ADR-0014.

**Settled:** the 3,242-line class splits along its own seams (for instance ownership and epochs,
participants, sweeps, read queries). SQL text and transaction boundaries are moved, not rewritten.

**Done when:**
- No class in the result exceeds 800 lines.
- Modulith, unit and integration suites pass with unchanged counts.
- Merged and pushed; ref bumped.

### IMP-M20-15 — ADR-0021: deployment profiles

**Repo:** `turnbase` (umbrella) · **Depends on:** —

**Read first:** ADR-0020; `load-testing-phase-b.md` §3–4; `platform-architecture.md` (FR-ASC, NFR-ASC);
`local-environment.md`; `PodIdentity.java`; `turnbase-frontend/nginx/default.conf.template`.

**Settled:** two profiles. *Scaled Kubernetes*: what M18 measured, two-replica minimum, HPA and KEDA.
*Single instance*: one Platform and one Game Host, which may scale to zero; the compose stack is its local
form. The instance-addressing contract (WebSocket `?instance=` routing; the Platform reaching a chosen Game
Host) is stated as a contract, the headless Service being one implementation. One provider per deployment,
not one per component (owner).

**Done when:**
- ADR-0021 is registered; every FR-ASC/NFR-ASC row says which profile it binds.
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-16 — Recovery from a full stop

**Repo:** `turnbase-platform` (or `turnbase` `scripts/`, the builder's call) · **Depends on:** IMP-M20-15

**Read first:** ADR-0021; ADR-0008, 0009, 0010; `room-lifecycle.md`; `game-host-internals.md` §9.

**Settled:** a repeatable local test of the single-instance profile: rooms in the lobby and games in
progress; the whole stack stopped; time passes beyond grace and dispatch deadlines and lease TTLs; the stack
started. The test asserts the states the specifications require for rooms, deadlines, leases and sessions.

**Done when:**
- The test exists, is documented in `local-environment.md`, and passes, or each defect it finds is a
  `spec-defect` or a new item.
- Merged and pushed.

### IMP-M20-17 — Startup time measured, class-data sharing tried

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** —

**Read first:** both Dockerfiles; ADR-0016; `game-host-internals.md` (boot watchdog, warm-up).

**Settled:** time-to-ready of each service measured in the compose stack; AppCDS (or Spring's CDS support)
and similar startup options tried in the image; adopted where it saves time without a behaviour change.

**Done when:**
- Before and after numbers (median of five starts) are in the commit body; each option adopted or rejected
  with its reason.
- Builds and the e2e smoke pass; merged and pushed; refs bumped.

### IMP-M20-18 — `OQ-6`: twelve Espresso contexts per JVM

**Repo:** `turnbase-game-host`, `turnbase` (umbrella) · **Depends on:** —

**Read first:** `game-host-internals.md` §18 `OQ-6` and the sections it cites; ADR-0019; `IMP-M16-05`.

**Settled:** reproduce the limit locally, find the cause or bound it, and decide the mitigation (for
instance recycling the JVM before the limit). The decision is the owner's if it changes behaviour.

**Done when:**
- §18 `OQ-6` is closed with the cause (or the bound) and the decision.
- A test pins the behaviour decided.
- Merged and pushed; ref bumped.

### IMP-M20-19 — Platform thread growth under sustained load explained

**Repo:** `turnbase-platform`, `turnbase` (umbrella) · **Depends on:** —

**Read first:** `loadtest/reports/2026-10-31-m18-sustained-high.md`; `load-testing.md` §13;
`ThreadBoundsIT`.

**Settled:** reproduce the growth (129 → 172 platform threads at the end of the hold) with a short targeted
run, and classify it: a pool growing to its bound, or a leak.

**Done when:**
- The cause is a `**M20:**` line on the finding in `load-testing.md` §13.
- If it is a leak: a test that fails before the fix and passes after.
- Merged and pushed; ref bumped if code changed.

### IMP-M20-20 — Open-question triage and the backlog

**Repo:** `turnbase` (umbrella) · **Depends on:** —

**Read first:** every `OQ-*` in `docs/specs` (33, besides `OQ-6`); `loadtest/reports/SUMMARY.md` *What Phase
C starts from*.

**Settled:** each open question gets a disposition: *closed* (already answered by the corpus or the code),
*decided* (the owner chooses from a short list the item prepares), or *backlog*: one document, registered
in `docs/specs/INDEX.md`, saying why it can wait.

**Done when:**
- No `OQ-*` in `docs/specs` without a disposition.
- The backlog document exists and is registered.
- `check-corpus.py` clean; merged and pushed.

### IMP-M20-21 — Credits for games based on existing games

**Repo:** `turnbase` (manifest spec), `turnbase-sdk` (schema, bundle validator), `turnbase-platform`,
`turnbase-frontend`, `turnbase-game-7wonders-duel` · **Depends on:** —

**Read first:** `manifest-schema.md`; `manifest.schema.json`; `bundle-format.md` (where the validator checks
the manifest); `game-catalog.md` FR-GAME-002; `platform-views.md` *Game Catalog* and *Game Detail*.

**Settled (owner):** a game that implements an existing game credits its original authors, in the manifest,
and the platform shows the credits. For 7 Wonders Duel: designed by Antoine Bauza and Bruno Cathala, art by
Miguel Coimbra, published by Repos Production, 2015. The field is optional: an original game has none. The
field's name and shape are the builder's, settled in `manifest-schema.md` first.

**Done when:**
- The spec, `manifest.schema.json`, the SDK's copy and the bundle validator agree; the validator accepts the
  field and rejects a malformed one.
- The Game Detail view shows the credits (and the Catalog card, if the view spec says so); 7WD's manifest,
  `README.md` and `INFO.md` carry them, and `INFO.md` no longer calls the game a skeleton.
- The credits show for 7WD in the running stack; every touched repository's build passes; merged and pushed;
  refs bumped.

### IMP-M20-22 — Load-test record tidy

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M20-20

**Read first:** `loadtest/reports/SUMMARY.md`; `loadtest/reports/2026-10-24-m18-otel.md`; the `20` backlog.

**Settled:** `SUMMARY.md`'s "The owner's choice is pending" becomes the recorded choice (configuration 1,
2026-10-24); every *What Phase C starts from* point has a backlog entry.

**Done when:**
- `SUMMARY.md` contradicts no report.
- `check-corpus.py` clean; merged and pushed.

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
