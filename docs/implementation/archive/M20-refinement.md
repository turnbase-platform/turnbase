# Archive — M20 Refinement

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim when M20 closed (2026-11-07). Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M20-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M20-01 | Registry archive: closed milestones out of the session's way | docs | — | DONE |
| IMP-M20-02 | `STATUS.md` reset to the present | docs | M20-01 | DONE |
| IMP-M20-03 | `CLAUDE.md` trim, counts checked, memory aligned | docs | M20-02 | DONE |
| IMP-M20-04 | Code maps: one checked `ARCHITECTURE.md` per service | platform, game-host, frontend, sdk, docs | — | DONE |
| IMP-M20-05 | Code→spec references checked by the corpus checker | docs, platform, frontend | — | DONE |
| IMP-M20-06 | Claude tooling review: permissions, skills, language server | docs | M20-01 | DONE |
| IMP-M20-07 | An honest build: green locally, verified submodule refs | frontend, 7WD, docs | — | DONE |
| IMP-M20-08 | `scripts/test-cost.sh` and the test-cost baseline | docs | — | DONE |
| IMP-M20-09 | Platform ITs share one set of containers | platform | M20-08 | DONE |
| IMP-M20-10 | Platform ITs share a cached Spring context | platform | M20-09 | DONE |
| IMP-M20-11 | Measurements leave the default build (`perf` tag) | platform, game-host | M20-08 | DONE |
| IMP-M20-12 | Platform IT overlap pass | platform | M20-10 | DONE |
| IMP-M20-13 | One Trivy scan per target | platform, game-host, frontend, sdk, common | — | DONE |
| IMP-M20-14 | `RoomRepository` split by concern | platform | M20-10 | DONE |
| IMP-M20-15 | ADR-0021: deployment profiles | docs | — | DONE |
| IMP-M20-16 | Recovery from a full stop | platform, docs | M20-15 | DONE |
| IMP-M20-17 | Startup time measured, class-data sharing tried | platform, game-host | — | DONE |
| IMP-M20-18 | `OQ-6`: twelve Espresso contexts per JVM | game-host, docs | — | DONE |
| IMP-M20-19 | Platform thread growth under sustained load explained | platform, docs | — | DONE |
| IMP-M20-20 | Open-question triage and the backlog | docs | — | DONE |
| IMP-M20-21 | Credits for games based on existing games | docs, sdk, platform, frontend, 7WD | — | DONE |
| IMP-M20-22 | Load-test record tidy | docs | M20-20 | DONE |

---

## M20 — Refinement

Opened 2026-11-04 from the refinement spike
([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../../reviews/2026-11-04-refinement-spike/INDEX.md),
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
