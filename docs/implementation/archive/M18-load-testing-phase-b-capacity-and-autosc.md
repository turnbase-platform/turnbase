# Archive — M18 Load testing Phase B: capacity and autoscaling

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M18-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M18-01 | Phase B spec groundwork: ADR-0020, FR-ASC/NFR-ASC, the amended rows | docs | — | DONE |
| IMP-M18-02 | Cores reallocated to PostgreSQL, and the Phase B baseline | docs (umbrella), platform (chart) | M18-01 | DONE |
| IMP-M18-03 | Fewer statements per room create and join | platform | M18-02 | DONE |
| IMP-M18-04 | A per-room participant cache on the move path | platform | M18-02 | DONE |
| IMP-M18-05 | One Redis round trip per move | platform | M18-02 | DONE |
| IMP-M18-06 | The OpenTelemetry agent's cost is measured and decided | docs (umbrella), platform (chart) | M18-02 | DONE |
| IMP-M18-07 | Single-instance re-verification | docs (umbrella) | M18-03, M18-04, M18-05, M18-06 | DONE |
| IMP-M18-08 | Platform state is correct across instances | platform, docs | M18-01 | DONE |
| IMP-M18-09 | WebSocket upgrades reach the room's instance | frontend, platform (chart), docs | M18-01 | DONE |
| IMP-M18-10 | Platform autoscaling, two-replica minimum and release on scale-in | platform, docs (umbrella) | M18-08, M18-09 | DONE |
| IMP-M18-11 | Host selection spreads sessions under a per-host cap | platform, docs | M18-01 | DONE |
| IMP-M18-12 | `OQ-5`: eager and lazy reassignment measured, the winner kept | platform, docs | M18-01 | DONE |
| IMP-M18-13 | Game Host autoscaling with KEDA, two-replica minimum and drain | platform (chart), game-host, docs (umbrella) | M18-11, M18-12 | DONE |
| IMP-M18-14 | Harness: scaling timeline, correctness check, new scenarios | docs (umbrella) | M18-07, M18-10, M18-13 | DONE |
| IMP-M18-15 | Phase B runs: ceiling and spike | docs (umbrella) | M18-14 | DONE |
| IMP-M18-16 | Phase B runs: failover, up-down and diurnal | docs (umbrella) | M18-15 | DONE |
| IMP-M18-17 | Phase B runs: sustained high load, and the Phase B summary | docs (umbrella) | M18-16 | DONE |

---

## M18 — Load testing Phase B: capacity and autoscaling

Opened 2026-10-24 from the M17 re-verification (`loadtest/reports/SUMMARY.md`, *M17*) and the Phase B design
round with the owner the same day: [`load-testing-phase-b.md`](../../specs/deployment/load-testing-phase-b.md).
That document is the design; an item's section names the part it builds.

**Goal (owner).** Autoscaling that adapts to rising and falling load, with peak traffic, extended high load and
ordinary daily shapes handled correctly and efficiently. **Redundancy and correctness come before a higher
ceiling**: at least two Platform and two Game Host replicas at all times, and the loss of any one costs no game.
The Game Host is not the bottleneck: it drops to 2 cores and PostgreSQL gets the 2 freed (4 in all). PostgreSQL
and Redis stay single, non-HA instances.

**The decisions in the design are the owner's or marked as the orchestrator's**, as in M16 and M17: what an
item states as settled is settled. Where an item says *amend spec X to say Y* the agent edits that spec as part
of the item. A *new* contradiction the item did not anticipate still goes through the `spec-defect` skill.

**Four tracks** (`load-testing-phase-b.md` §9). Track 1, capacity on one node (`02…07`), runs first because it
changes the replica that Track 2 multiplies. Track 2, the Platform scales out (`08…10`), and Track 3, the Game
Host (`11…13`), are independent of each other and may interleave with Track 1 once `01` is done. Track 4, the
harness and the runs (`14…17`), comes last. `01` (spec) blocks everything.

**Live items (`02`, `06`, `07`, `10`, `12`, `13`, `15…17`, and `14`'s smoke runs).** The M16 milestone introduction applies unchanged:
*Live items*, the *Rebuild rule for live items* with its *Check it happened* diff of `cluster.txt`, *Overlay
mirroring*, and *Measuring items record, they do not add items* (report names `YYYY-MM-DD-m18-<name>.md`; a
§13 finding is annotated with an `**M18:**` line). Reset the stack (`bash loadtest/reset.sh`) and re-provision
before every run. From `02` on, every run uses the Phase B overlays, so no M18 figure is compared with an M17
figure without saying the cores differ.

**Submodules.** An item that changes a submodule bumps its ref here only after the pipeline on that
repository's `master` is green.

### IMP-M18-01 — Phase B spec groundwork: ADR-0020, FR-ASC/NFR-ASC, the amended rows

**Repo:** `turnbase` · **Depends on:** —

**Read first:**
- `docs/specs/deployment/load-testing-phase-b.md` (all), `docs/specs/deployment/load-testing.md` §8, §9
- `docs/decisions/0002-websocket-room-affinity.md`, `0008-room-ownership-lifecycle.md`
- `docs/requirements/platform-operations.md` NFR-SCALE-001, CON-013, FR-DEPLOY-002, FR-TRACE-001;
  `platform-architecture.md` FR-SCALE-001…006, *Open Questions* `OQ-003`
- `docs/specs/game-host/game-host-internals.md` §11, `docs/specs/deployment/local-environment.md` §3, §7.9

**Settled:** `load-testing-phase-b.md` §8 is the list, with the requirement rows exactly as §7 tables them.
`IMP-M18-01` changes no code.

**Done when:**
- `docs/decisions/0020-platform-horizontal-scaling.md` exists with the content of §8's first bullet and is
  registered in `docs/decisions/INDEX.md`; ADR-0002 and ADR-0008 each carry a one-line *Amended by ADR-0020*
  note.
- `platform-operations.md` defines FR-ASC-001…005 and NFR-ASC-001…007 as §7 states them, NFR-SCALE-001 and
  CON-013 are amended, and `docs/requirements/INDEX.md` lists `FR-ASC` and `NFR-ASC` for it.
- `platform-architecture.md` FR-SCALE-006 is amended and `OQ-003` resolved (drain, then migrate);
  `game-host-internals.md` §11 states the §5.1 rule; `local-environment.md` §3 and §7.9 and `load-testing.md`
  §8 are amended.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M18-02 — Cores reallocated to PostgreSQL, and the Phase B baseline

**Repo:** `turnbase` (umbrella: overlays, reports), `turnbase-platform` (chart defaults of `postgres.settings`) · **Depends on:** IMP-M18-01

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release (M16 rebuild rule). Each run
is long: background it and poll.

**Read first:** `load-testing-phase-b.md` §3.1; `local-environment.md` §7.9; `loadtest/README.md`;
`loadtest/reports/2026-10-24-m17-parallelism.md`, `…-m17-ramp-to-break.md`

**Settled:**
- Both overlays (mirrored, `test/check-overlays.sh`): PostgreSQL 4 CPU and 2 GiB, Game Host 2 CPU (one
  replica), Platform and Redis unchanged. `postgres.settings` rescaled for 4 CPU and 2 GiB as §3.1 states, with
  the values and their reasons in `local-environment.md` §7.9.
- Run `parallelism` and `ramp-to-break` as `IMP-M17-05` ran them, on the unchanged `e52c1f4`-equivalent
  platform build. One report, `YYYY-MM-DD-m18-baseline.md`, with an *M17 vs M18 baseline* table per scenario
  and the first to break under the amended §8 rule.

**Done when:**
- The report exists and `bash loadtest/check-report.sh` prints `REPORT COMPLETE`; `SUMMARY.md` gains an *M18*
  section with its row.
- `turnbase-platform` pipeline green and its ref bumped if the chart changed; `python3 scripts/check-corpus.py`
  prints `clean`; merged to `master` and pushed.

### IMP-M18-03 — Fewer statements per room create and join

**Repo:** `turnbase-platform` · **Depends on:** IMP-M18-02

**Read first:** `load-testing-phase-b.md` §3.2; `loadtest/reports/2026-10-21-m16-cpu.md` §3;
`docs/specs/flows/02-room-to-game-start.md` (create and join steps); `docs/specs/platform/room-lifecycle.md` §2;
`platform-operations.md` FR-DBQ-001…004

**Settled:** §3.2. Transaction boundaries, the room lock and version-before-publish are not changed.

**Done when:**
- A table of statements and Postgres time per create and per join, before and after, from `pg_stat_statements`
  on a `start-rate` smoke run, is recorded as an `**M18:**` line under `load-testing.md` §13 finding 3; the count
  per join and per create is strictly lower, or the item records why a statement cannot go.
- `GamePathQueryCostIT` covers every new or changed statement and passes; `./mvnw verify` and `./mvnw verify
  -Pintegration` green.
- Pipeline green, ref bumped, merged and pushed.

### IMP-M18-04 — A per-room participant cache on the move path

**Repo:** `turnbase-platform` · **Depends on:** IMP-M18-02

**Read first:** `load-testing-phase-b.md` §3.3; `2026-10-21-m16-cpu.md` §3 and §5; `docs/decisions/0008-room-ownership-lifecycle.md`;
`room-lifecycle.md` §1; `GameActionController`, `GameInputService`, `RoomOwnershipService`

**Settled:** §3.3: owner-local, invalidated on every participant or host mutation, dropped on ownership loss
and closure; a miss reads Postgres as today.

**Done when:**
- A move by a cached, authorised participant issues no Postgres statement (a statement-counting test at the
  datasource, as `SweepSelectsOnlyRoomsItCanChangeIT` counts).
- A property-style test interleaves joins, leaves, kicks, disconnects, reconnects, host transfers, ownership
  loss and moves, and the cached decision equals the uncached one every time.
- `./mvnw verify` and `-Pintegration` green; pipeline green, ref bumped, merged and pushed.

### IMP-M18-05 — One Redis round trip per move

**Repo:** `turnbase-platform` · **Depends on:** IMP-M18-02

**Read first:** `load-testing-phase-b.md` §3.4; `game-host-internals.md` §9.2; `2026-10-21-m16-cpu.md` §3

**Settled:** §3.4: the post-result writes become one pipeline or one Lua script (builder's call); the delivery
watermark rules are unchanged.

**Done when:**
- A Redis command-counting test shows one round trip for the post-result writes of a move (`MONITOR` or a
  Lettuce command listener).
- A test shows `delivered:` is never advanced before fan-out, and the existing exactly-once tests pass.
- `./mvnw verify` and `-Pintegration` green; pipeline green, ref bumped, merged and pushed.

### IMP-M18-06 — The OpenTelemetry agent's cost is measured and decided

**Repo:** `turnbase` (umbrella: report, docs), `turnbase-platform` (chart default) only if the owner chooses a change · **Depends on:** IMP-M18-02

**Environment:** as `IMP-M18-02`.

**Read first:** `load-testing-phase-b.md` §3.5; `platform-operations.md` FR-TRACE-001, FR-TRACE-004;
`docs/specs/deployment/observability.md` §4; `2026-10-21-m16-cpu.md` §5

**Settled:** three `parallelism` runs, configurations 1 to 3 of §3.5, set through `platform.extraEnv` in the
load-test overlays. **The agent stops and asks the owner** with the report's table; it does not choose.


**Done when:**
- `YYYY-MM-DD-m18-otel.md` exists, `REPORT COMPLETE`, with CPU per move (`cpu-per-move.sh`), peak moves/s and
  the ceiling per configuration.
- The owner's choice is recorded in the report. If it is not configuration 1, FR-TRACE-001, `observability.md`
  §4 and the chart default are amended to match (pipeline green, ref bumped).
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M18-07 — Single-instance re-verification

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M18-03, IMP-M18-04, IMP-M18-05, IMP-M18-06

**Environment:** as `IMP-M18-02`, every M18 image rebuilt.

**Read first:** `load-testing-phase-b.md` §3.6; `platform-operations.md` NFR-DBQ-001…003; the `m18-baseline`
report; `IMP-M17-05` (this item repeats its protocol)

**Settled:** `parallelism`, `ramp-to-break` and `soak` (`PAIRS=56`) on one Platform instance, as `IMP-M17-05`
ran them. If PostgreSQL is still first to break, record it and proceed: Track 2 does not wait on it.

**Done when:**
- `…-m18-parallelism.md`, `…-m18-ramp-to-break.md`, `…-m18-soak.md` exist, each `REPORT COMPLETE` with an *M18
  baseline vs M18* table.
- `SUMMARY.md` *M18* records NFR-DBQ-001…003 pass or fail and the single-instance ceiling NFR-ASC-006 is judged
  against; `load-testing.md` §13 findings 1 to 3 and 15 carry `**M18:**` lines.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M18-08 — Platform state is correct across instances

**Repo:** `turnbase-platform`, `turnbase` (specs) · **Depends on:** IMP-M18-01

**Read first:** `load-testing-phase-b.md` §4.1, §4.2; ADR-0020; `docs/specs/api-design/sse-notifications.md`;
`docs/specs/api-design/rate-limiting.md` (connections per user); `docs/specs/platform/room-lifecycle.md` §1

**Settled:** §4.1's table is the minimum; §4.2's Redis pub/sub for user-scoped pushes, best-effort as today.
Room fan-out stays owner-local (ADR-0002).

**Done when:**
- An audit table of every in-memory map in the Platform (at least the classes §4.1 names) with *correct per
  instance, because …* or *fixed by …* is added to the platform spec it belongs in (builder's call which), and
  the channel names and payloads are specified there.
- Integration tests with **two Platform application contexts** sharing one Postgres and one Redis show: an
  alert published on one reaches an SSE stream on the other; a revocation on one closes the user's WebSocket
  and SSE stream on the other; a fifth WebSocket for one user is refused when the four are split across both;
  the API tiers and ShedLock'd jobs behave as one instance.
- `./mvnw verify` and `-Pintegration` green; `check-corpus.py` clean; pipeline green, ref bumped, merged and
  pushed.

### IMP-M18-09 — WebSocket upgrades reach the room's instance

**Repo:** `turnbase-frontend` (nginx), `turnbase-platform` (chart: headless Service), `turnbase` (specs) · **Depends on:** IMP-M18-01

**Read first:** `load-testing-phase-b.md` §4.3; `room-websocket.md` *Routing on join*; `room-lifecycle.md` §1.7;
`local-environment.md` §3; `turnbase-frontend/nginx/default.conf.template`; `turnbase-frontend/src/features/rooms/roomSocket.ts`

**Settled:** §4.3: the hint names the target pod; fallback to the Service when it does not resolve or refuses;
no consistent hashing; REST stays round-robin. The compose stack (one instance) keeps working unchanged.

**Done when:**
- With two Platform replicas on the cluster, 100 `/ws?instance={pod}` upgrades for each pod all land on that
  pod (its connection gauge or log), an upgrade naming a deleted pod lands on a live one, and one without the
  parameter lands on either.
- The frontend's `make e2e` passes against compose; `local-environment.md` §3 describes the routing.
- Both pipelines green, refs bumped, merged and pushed.

### IMP-M18-10 — Platform autoscaling, two-replica minimum and release on scale-in

**Repo:** `turnbase-platform` (chart, shutdown path), `turnbase` (overlays, docs) · **Depends on:** IMP-M18-08, IMP-M18-09

**Environment:** live cluster (M16 rebuild rule).

**Read first:** `load-testing-phase-b.md` §4.4…§4.6; `local-environment.md` §3 (rolling deploy) and §7.9;
`room-lifecycle.md` §1.6; ADR-0020

**Settled:** HPA on CPU through metrics-server, `minReplicas` 2, `maxReplicas` 3, 1.5 CPU per replica, the
§4.4 budget; `max_connections` from §4.5; on `SIGTERM` stop new rooms, release, close sockets (order and
timings builder's call).

**Done when:**
- The Phase B overlays render the HPA; `kubectl get hpa` shows 2 replicas at rest and a third under a
  `parallelism` smoke at a load that crosses the target.
- A scripted test on the cluster scales 3 → 2 by lowering the load, and separately deletes one of two pods
  gracefully, each mid-game with 8 pairs playing: every game finishes, no `ROOM_UNAVAILABLE_RETRY` outlasts the client's retry
  budget, and the released rooms are claimed by the survivor (log lines).
- `local-environment.md` §7.9 records the budget arithmetic; both overlays mirrored; pipeline green, ref
  bumped, `check-corpus.py` clean, merged and pushed.

### IMP-M18-11 — Host selection spreads sessions under a per-host cap

**Repo:** `turnbase-platform`, `turnbase` (specs) · **Depends on:** IMP-M18-01

**Read first:** `load-testing-phase-b.md` §5.1; `game-host-internals.md` §11 (as `01` amended it);
`platform-architecture.md` FR-SCALE-005, FR-ORCH-004; `HostRegistry.selectHost`

**Settled:** §5.1's rule; the cap is a configuration key with a default the builder sizes from the
`m18-baseline` report (recorded in `local-environment.md` §7.9).

**Done when:**
- Unit tests cover: warm host below cap preferred; warm host at cap skipped for a cold one; all at cap gives
  `NO_HOST_AVAILABLE`; draining and quarantined hosts skipped; lowest `activeSessions` among equals.
- `./mvnw verify` and `-Pintegration` green; pipeline green, ref bumped, merged and pushed.

### IMP-M18-12 — `OQ-5`: eager and lazy reassignment measured, the winner kept

**Repo:** `turnbase-platform`, `turnbase` (specs, report) · **Depends on:** IMP-M18-01

**Environment:** the suite runs as integration tests (two Game Host containers, Testcontainers or the compose
stack, builder's call); live cluster only for the drain scenario if the builder needs it.

**Read first:** `load-testing-phase-b.md` §5.2; `game-host-internals.md` §9.2, §9.3, §11, §18 `OQ-5`;
`platform-architecture.md` FR-FAIL-002, NFR-REL-002; `GameInputService.reassign`

**Settled:** §5.2 in full: eager implemented behind a switch, one suite for both modes with at least the
scenarios listed, the correctness checks, the decision rule, removal of the losing mode.

**Done when:**
- `loadtest/reports/YYYY-MM-DD-m18-reassignment.md` (or `docs/reviews/…` if the builder judges it is not a load
  report; registered either way) has the scenario × mode table of correctness results, recovery times and
  calls, and names the winner by the rule.
- The losing mode and its switch are removed; the suite stays and passes against the winner.
- `game-host-internals.md` §9.3 describes the winner and §18 `OQ-5` is marked resolved with the report linked.
- `./mvnw verify` and `-Pintegration` green; `check-corpus.py` clean; pipeline green, ref bumped, merged and pushed.

### IMP-M18-13 — Game Host autoscaling with KEDA, two-replica minimum and drain

**Repo:** `turnbase-platform` (chart, registry drain), `turnbase-game-host` (drain behaviour if needed), `turnbase` (install script, overlays, docs) · **Depends on:** IMP-M18-11, IMP-M18-12

**Environment:** live cluster (M16 rebuild rule).

**Read first:** `load-testing-phase-b.md` §4.4, §5.3; `platform-architecture.md` FR-SCALE-001…006 (as `01`
amended them); ADR-0018; `load-testing.md` §13 findings 8 and 9; `HostRegistry` (`draining`)

**Settled:** KEDA from a pinned chart installed by `loadtest/install.sh`; a `ScaledObject` on `activeSessions`
against the cap and on memory; min 2, max 3, 1 CPU per replica (the §4.4 fallback to 1.5 if the boot watchdog
trips); scale-in drains, then the `OQ-5` winner reassigns what remains.

**Done when:**
- At rest two Game Hosts run and both receive sessions (the §5.1 rule, with `warm-hosts` 2 from session 251); a `parallelism` smoke past the cap
  brings a third, Ready within NFR-ASC-001's 3 min.
- Removing a replica with 8 pairs playing: it is marked draining, takes no new session, and every game
  finishes, including those reassigned after the drain period.
- Cold start at 1 CPU (single and four contexts) recorded as `**M18:**` lines under findings 8 and 9.
- Overlays mirrored; pipelines green, refs bumped, `check-corpus.py` clean, merged and pushed.

### IMP-M18-14 — Harness: scaling timeline, correctness check, new scenarios

**Repo:** `turnbase` (umbrella: `loadtest/`) · **Depends on:** IMP-M18-07, IMP-M18-10, IMP-M18-13

**Read first:** `load-testing-phase-b.md` §6; `loadtest/README.md`; `loadtest/scenarios/`; `loadtest/reports/TEMPLATE.md`

**Settled:** the timeline sampler (5 s) and the post-run correctness check of §6; scenarios `spike`,
`sustained-high`, `diurnal`, `failover` (kills through `kubectl`, on the timeline); `ramp-to-break` and
`up-down` with autoscaling on; the k6 `/ws` URL carries the instance hint; the early-ending 256-pair step
explained (and fixed if it is the harness). k6 pinned to 3 cores (§4.4).

**Done when:**
- Each new scenario has run once as a short smoke with a timeline file and a correctness verdict; the README
  documents them; `TEMPLATE.md` gains the scaling timeline and NFR-ASC sections, and `check-report.sh` enforces
  them.
- The 256-pair finding is explained in an `**M18:**` line.
- `check-corpus.py` clean; merged to `master` and pushed.

### IMP-M18-15 — Phase B runs: ceiling and spike

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M18-14

**Environment:** live cluster, every M18 image rebuilt. Each run is long: background it and poll.

**Read first:** `load-testing-phase-b.md` §6, §7; `loadtest/README.md`; the `IMP-M18-07` reports

**Settled:** `ramp-to-break` first (its ceiling sets the loads of every later scenario), then `spike`.

**Done when:**
- `…-m18-scaled-ramp-to-break.md` and `…-m18-spike.md` exist, `REPORT COMPLETE`, with the timeline and the
  verdicts on NFR-ASC-001, 002, 004 and 006.
- `check-corpus.py` clean; merged and pushed.

### IMP-M18-16 — Phase B runs: failover, up-down and diurnal

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M18-15

**Environment:** as `IMP-M18-15`.

**Read first:** as `IMP-M18-15`, and its reports.

**Done when:**
- `…-m18-failover.md`, `…-m18-up-down.md`, `…-m18-diurnal.md` exist, `REPORT COMPLETE`, with the verdicts on
  NFR-ASC-002, 003 and 007 (and 001 where a scale-out happens).
- `check-corpus.py` clean; merged and pushed.

### IMP-M18-17 — Phase B runs: sustained high load, and the Phase B summary

**Repo:** `turnbase` (umbrella) · **Depends on:** IMP-M18-16

**Environment:** as `IMP-M18-15`. The run lasts over an hour.

**Read first:** as `IMP-M18-15`, and the `IMP-M18-15` and `16` reports.

**Done when:**
- `…-m18-sustained-high.md` exists, `REPORT COMPLETE`, with the verdict on NFR-ASC-005.
- `SUMMARY.md` *M18* has a table of every FR-ASC and NFR-ASC with pass or fail and evidence, the owner's three
  questions answered for the scaled deployment, and what Phase C (if any) starts from; `load-testing.md` §13
  findings touched by M18 carry `**M18:**` lines.
- `check-corpus.py` clean; merged and pushed.

---
