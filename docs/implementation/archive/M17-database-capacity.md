# Archive — M17 Database capacity

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M17-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M17-01 | The migration-window sweep stops re-reading rooms it cannot change | platform | — | DONE |
| IMP-M17-02 | Game-path queries cost the same whatever the retained history | platform | — | DONE |
| IMP-M17-03 | The connection-pool size is explicit and configurable | platform, docs | — | DONE |
| IMP-M17-04 | The pool size is chosen by measurement | docs (umbrella), platform | M17-01, M17-02, M17-03 | DONE |
| IMP-M17-05 | Re-verification runs, and the M17 summary | docs (umbrella) | M17-04 | DONE |

---

## M17 — Database capacity

Opened 2026-10-22 from the M16 re-verification (`loadtest/reports/SUMMARY.md`, *M16*): in `parallelism` and
`ramp-to-break` the first thing to break was the 10-connection Hikari pool, with PostgreSQL at its 2-core
limit (in `soak` nothing broke, but the pool stayed saturated), and the statements that dominate are scans of `room_participant` (`load-testing.md` §13
findings 1 to 3 and 15). The requirements are `platform-operations.md` FR-DBQ-001…007 and
NFR-DBQ-001…004, written with the owner in a requirements session the same day.

**Goal (owner).** After M17 the database is not the first thing to break in `parallelism`, `ramp-to-break` and
`soak`. *First to break* now distinguishes `PostgreSQL` from `DB pool` (`load-testing.md` §8); neither may be
named. Other
bottlenecks are expected to appear in its place; they become Phase B notes, not M17 items.

**Scope (owner): minimal.** Query improvements, the sweep bug, and an explicit, measured Hikari pool size.
PostgreSQL server tuning only as a last resort (FR-DBQ-007). Out of scope, by the owner's decision and
recorded in `platform-operations.md` *Out of Scope*: write batching, fail-fast or `503` shedding on pool
exhaustion (CON-014: requests keep waiting as today), a separate pool for background jobs, a cross-replica
connection budget and PgBouncer, caching, retention changes (CON-016), more than one platform instance.

**The decisions in an item are the owner's**, as in M16: what an item states as settled is settled. Where an
item says *amend spec X to say Y* the agent edits that spec as part of the item. A *new* contradiction the
item did not anticipate still goes through the `spec-defect` skill.

**Sequencing.** `01`, `02` and `03` are independent code items and may run in any order; `04` needs all
three; `05` needs `04`. If `01` and `02` both add a Flyway migration, the later one to merge takes the later
version timestamp.

**Live items (`04`, `05`).** The M16 milestone introduction applies unchanged: *Live items*, the *Rebuild
rule for live items* with its *Check it happened* diff of `cluster.txt`, *Overlay mirroring*, and *Measuring
items record, they do not add items* (report names `YYYY-MM-DD-m17-<name>.md`; a §13 finding is annotated
with an `**M17:**` line). Reset the stack (`bash loadtest/reset.sh`) and re-provision before every run.

**Submodules.** An item that changes `turnbase-platform` bumps its ref here only after the pipeline on that
repository's `master` is green.

### IMP-M17-01 — The migration-window sweep stops re-reading rooms it cannot change

**Repo:** `turnbase-platform` · **Depends on:** nothing

**Covers:** `platform-operations.md` OQ-005; the "participant lookup three times" in `load-testing.md` §13 finding 1's M16 Phase B note.

**Read first:**
- `docs/requirements/platform-operations.md` FR-JOB-006, FR-JOB-007, FR-RET-006, FR-DBQ-004, OQ-005
- `docs/specs/platform/room-lifecycle.md` §5.1 (the deadline sweep's duties)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/GraceDeadlineSweepJob.java` (all four duties; `closeMigrationWindow`)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomEventExecutor.java` (`execute`, the `RoomUnavailableRetryException` paths)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomOwnershipService.java` (`onRoomClosed`, `release`)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomRepository.java` (`elapsedMigrationWindowRoomIds`, `clearMigrationWindow`, `detachSession`, `dueGraceReservations`, `deferredTails`)
- `loadtest/reports/2026-10-21-m16-cpu.md` §3 (the three statements at about 1.26 calls per move)

**Satisfies:** `platform-operations.md` FR-DBQ-004

**Settled:**
- **Reproduce first.** An integration test (Testcontainers PostgreSQL and Redis) creates rooms whose
  `migration_window_expires_at` has elapsed and whose `owner_instance_id` is this instance, but which this
  instance cannot mutate (no in-memory epoch, the case `RoomEventExecutor.execute` refuses with
  `RoomUnavailableRetryException`). The fixture includes the likeliest case, a room that **closed inside its
  window** through the real close path (`onRoomClosed` leaves the owner and the window set), and a room
  released by `RoomOwnershipService.release`. The test counts the statements of several consecutive sweep ticks. Record in
  OQ-005 whether the endless re-read is confirmed, and by how many statements per tick.
- **Fix, if confirmed.** A room the duty cannot act on stops being selected until its state changes (for
  example, its ownership is re-acquired). The exclusion is in SQL, never a filter in Java after the select
  (FR-DBQ-004): closed rooms are excluded by the statement (`state <> 'CLOSED'`) or have their window cleared
  when they close; a live room without a local epoch either is excluded or has its `owner_instance_id`
  released so FR-JOB-007's adoption path picks it up. Which is the builder's call, if FR-JOB-006 and
  `room-lifecycle.md` §5.1 stay true. If the selection needs an index, it goes in a migration per
  `platform-operations.md` CON-015. Amend §5.1 to state the rule.
- **The other duties.** Check `dueGraceReservations` and `deferredTails` for the same pattern (selection by
  `owner_instance_id`, mutation through `execute`, the exception swallowed). Fix any that has it the same way,
  covered by the same kind of test.
- If the re-read does **not** reproduce, find what does issue those three statements at that rate (the
  `pg_stat_statements` `queryid` and a stack sample during a `smoke` run), record it in OQ-005, and fix it if it
  is a defect of the same kind; otherwise record why the rate is correct.

**Done when:**
- An integration test asserts that, over at least three sweep ticks, the statements issued for rooms the
  instance cannot mutate do not recur on every tick (a datasource statement counter or `pg_stat_statements`),
  and that a room the instance *can* mutate still has its window closed and its host transferred as before.
- `platform-operations.md` OQ-005 is marked **Resolved** with the outcome; `room-lifecycle.md` §5.1 states
  the rule if a duty changed; the M16 Phase B note under `load-testing.md` §13 finding 1 ("a participant lookup
  three times" per move) gets an `**M17:**` line saying what those calls were.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M17-02 — Game-path queries cost the same whatever the retained history

**Repo:** `turnbase-platform` · **Depends on:** nothing

**Covers:** `load-testing.md` §13 finding 15, and the statement share of findings 1 to 3.

**Read first:**
- `docs/requirements/platform-operations.md` FR-DBQ-001…003, NFR-DBQ-004, CON-015, CON-016, FR-RET-006
- `docs/specs/platform/data-model.md` (`room`, `room_participant`, `room_team`, their indexes)
- `docs/specs/deployment/schema-migrations.md` (migration naming, backward compatibility, § `CREATE INDEX CONCURRENTLY`)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomRepository.java`: the team-occupancy queries that `left join (select team_id, count(*) as occupied from room_participant …)`; `teamOccupancy` (filters on `team_id`, unindexed); `RESOURCE_SELECT` / `findRoomResource` (the refetch after create and join, with unrestricted `room_participant` / `room_team` aggregates); the open-room listing (its `player_count` / `player_capacity` / `spectator_count` aggregates); the `where user_id = :userId and left_at is null` lookups and the release on join that sets `left_at`; the `RoomForJoin` read (a primary-key lookup `for update`)
- `loadtest/reports/2026-10-21-m16-soak.md` (the `pg_stat_statements` table and the `EXPLAIN (ANALYZE)` note)

**Satisfies:** `platform-operations.md` FR-DBQ-001, FR-DBQ-002, FR-DBQ-003, NFR-DBQ-004

**Settled:**
- **The fixture.** A Testcontainers PostgreSQL seeded with at least 100,000 participant rows of closed rooms
  and a few hundred live rooms with live participants, `ANALYZE`d. Closing a room does **not** set `left_at`
  (a seated participant keeps `left_at IS NULL` until that user's next join releases the row), so the
  closed-room rows are a realistic mix, preferably produced through the real paths: `left_at` null and set,
  `lost_announced_at` null and set, and closed rooms still carrying this instance's `owner_instance_id` and an
  elapsed migration window.
- **The statement set** is every statement the platform issues on room create, room join, the open-room
  listing, lobby and ready commands, game start, a game action, and one tick of each deadline-sweep duty, collected with `pg_stat_statements`
  while an integration flow drives those operations against the fixture. Each is `EXPLAIN`ed.
- **Known fixes.** The team-occupancy queries, `teamOccupancy` and `RESOURCE_SELECT` restrict their
  participant and team aggregates to the room in question (FR-DBQ-002). The live lookup by `user_id` gets a
  partial index on `room_participant (user_id) WHERE left_at IS NULL` (FR-DBQ-003; at most one stale
  closed-room row per user stays in it, which is bounded) in a new Flyway migration named per
  `schema-migrations.md`. The open-room listing computes its aggregates for the listed rooms only.
  `elapsedMigrationWindowRoomIds` is covered if `IMP-M17-01` has not already indexed it. The `RoomForJoin`
  read (10.6 ms mean in the M16 soak) is a primary-key lookup `for update`: if its plan does not scan, its
  time is lock wait and is recorded as such, not fixed here. Any other statement of the set that fails the
  checks below is fixed the same way.
- `data-model.md` lists every index added, with the requirement it serves.

**Done when:**
- An `EXPLAIN (ANALYZE)`-based integration test over the fixture asserts, for every statement of the set,
  that no plan node is a sequential scan of `room`, `room_team` or `room_participant`, and that the rows it
  examines in those tables (actual rows plus rows removed by filter, times loops) exceed the same statement's
  on an empty-history database by no more than 10 (FR-DBQ-001).
- NFR-DBQ-004 is measured: each statement's mean execution time on the fixture and on an empty-history
  database, each within 25% or 0.5 ms; the table is recorded as an `**M17:**` line under `load-testing.md`
  §13 finding 15.
- Existing room integration tests stay green (no behaviour change).
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M17-03 — The connection-pool size is explicit and configurable

**Repo:** `turnbase-platform` (application config, chart), `turnbase` (`loadtest/helm/`, docs) · **Depends on:** nothing

**Covers:** the spec-versus-code drift on the pool size: `local-environment.md` §7.9 documents
`spring.datasource.hikari.maximum-pool-size` = 20, and the build runs Hikari's unset default of 10.

**Read first:**
- `docs/requirements/platform-operations.md` FR-DBQ-005, CON-014
- `docs/specs/deployment/local-environment.md` §7 (the binding rule) and §7.9 (the pool-size row and the FR-ALERT-004 paragraph under it)
- `turnbase-platform/src/main/resources/application.yml` (it has no `spring.datasource` block today; the URL comes from `SPRING_DATASOURCE_URL` in the platform ConfigMap)
- `turnbase-platform/deploy/helm/turnbase/values.yaml` (`platform:`) and `templates/platform-configmap.yaml`
- `loadtest/helm/values-loadtest.yaml`, `loadtest/helm/values-default-limits.yaml`, `loadtest/test/check-overlays.sh`

**Satisfies:** `platform-operations.md` FR-DBQ-005

**Settled:**
- Add a `spring.datasource.hikari` block to `application.yml` setting `maximum-pool-size` to **10**: the value
  in effect today, so this item changes no behaviour; `IMP-M17-04` chooses the real default. The
  environment variable is `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE`, by §7's binding rule (no alias). The
  pool stays fixed-size (Hikari's `minimum-idle` left at its default, which equals the maximum). Nothing
  else about the pool changes (CON-014).
- The chart exposes it as `platform.db.poolMaxSize` and passes it through the platform ConfigMap as that
  variable; both
  load-test overlays may set it, mirrored per *Overlay mirroring*.
- `local-environment.md` §7.9: the row's default becomes 10 and says FR-DBQ-006 governs it; the FR-ALERT-004
  paragraph's arithmetic (80% of the pool) follows the new value.

**Done when:**
- A Spring context test asserts the `HikariDataSource` maximum pool size follows the property (the default,
  and an override).
- `helm template` with `platform.db.poolMaxSize=7` renders `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE: "7"` in
  the platform ConfigMap; `bash loadtest/test/check-overlays.sh` passes.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M17-04 — The pool size is chosen by measurement

**Repo:** `turnbase` (umbrella: reports, docs, overlays), `turnbase-platform` (the chosen default) · **Depends on:** IMP-M17-01, IMP-M17-02, IMP-M17-03

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release, every M17 image rebuilt
and reinstalled (M16 rebuild rule). Each run is long: background it and poll.

**Covers:** `load-testing.md` §13 finding 1's Phase B note "the pool of 10 connections is saturated".

**Read first:**
- `docs/requirements/platform-operations.md` FR-DBQ-006, NFR-LOAD-001…004
- `loadtest/README.md` (run protocol), `loadtest/reports/TEMPLATE.md`, `loadtest/reports/2026-10-21-m16-parallelism.md`
- `docs/specs/deployment/load-testing.md` §5, §6, §8
- `docs/specs/deployment/local-environment.md` §7.9 (the pool-size row `IMP-M17-03` corrected)

**Satisfies:** `platform-operations.md` FR-DBQ-006

**Settled:**
- Run `parallelism` once per candidate pool size, set through `platform.db.poolMaxSize` in the load-test
  overlays: **5** (PostgreSQL's 2 cores × 2 + 1), **10** and **20**; add a further candidate only if the best
  of the three is the largest. Reset and re-provision between runs.
- The choice follows FR-DBQ-006 exactly: highest ceiling first (the report's `Ceiling (pairs)`, the last step
  meeting every threshold); among candidates at that ceiling, peak moves/s within 5% of the best is a tie,
  and the smallest tied pool wins. One run per candidate; if the top two differ by less than 5% in peak and
  share the ceiling, they are tied by this rule and no rerun is needed. Set it as the default in `application.yml` and the chart, and
  in both overlays.
- One report, `YYYY-MM-DD-m17-pool-sizing.md`, from `TEMPLATE.md`, with a table of the candidates (moves/s per
  step, `hikari_active` and `hikari_pending`, PostgreSQL cores, first to break). Record the candidates, the
  result and the reason in `local-environment.md` §7.9 under the key's row.

**Done when:**
- `ls loadtest/reports/*-m17-pool-sizing.md` lists the report, `REPORT COMPLETE` by
  `bash loadtest/check-report.sh`.
- The default is changed (or confirmed at 10) in `application.yml`, the chart and both overlays;
  `local-environment.md` §7.9 records the choice and its evidence.
- `turnbase-platform` pipeline green and its ref bumped if the default changed; `python3
  scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M17-05 — Re-verification runs, and the M17 summary

**Repo:** `turnbase` (umbrella), and `turnbase-platform` (chart) only if FR-DBQ-007 applies · **Depends on:** IMP-M17-04

**Environment:** as `IMP-M17-04`. Each run is long: background it and poll.

**Covers:** `load-testing.md` §13 findings 1 to 3 and 15 (re-measured).

**Read first:**
- `docs/requirements/platform-operations.md` NFR-DBQ-001…003, FR-DBQ-007, CON-013
- `loadtest/README.md`, `loadtest/reports/TEMPLATE.md`, `loadtest/reports/SUMMARY.md` (*M16*)
- `docs/specs/deployment/load-testing.md` §5, §6, §8, §13
- the M16 reports of the same scenarios (`2026-10-21-m16-parallelism.md`, `…-ramp-to-break.md`, `…-soak.md`)

**Satisfies:** `platform-operations.md` NFR-DBQ-001, NFR-DBQ-002, NFR-DBQ-003; FR-DBQ-007 if it applies

**Settled:**
- Run `parallelism`, `ramp-to-break` and `soak` as `IMP-M16-14` and `IMP-M16-15` ran them (same parameters,
  `USERS=3000`; `soak` at `PAIRS=56`, M16's load, so the drift is comparable, even if the M17 ramp ceiling
  moves), on the build with the `IMP-M17-04` default. One report each with an *M16 vs M17* comparison
  table against the M16 report of the same scenario.
- **FR-DBQ-007, only if needed.** If any of the three reports names `PostgreSQL` first to break (the `load-testing.md` §8 rule), tune the
  chart's PostgreSQL settings (memory and connection limits) within the pinned 2 CPU and 1 GiB, record the
  values and their rationale in `local-environment.md`, and rerun the
  failing scenario. If `DB pool` is first to break, that is a finding about `IMP-M17-04`'s choice:
  record it, do not resize here.
- What persists becomes a Phase B note (`**M17:**` line in `load-testing.md` §13).

**Done when:**
- `ls loadtest/reports/*-m17-parallelism.md loadtest/reports/*-m17-ramp-to-break.md loadtest/reports/*-m17-soak.md`
  lists three reports, each `REPORT COMPLETE`.
- `loadtest/reports/SUMMARY.md` has an *M17* section with the pass or fail of NFR-DBQ-001, 002 and 003 and links
  to the reports; `load-testing.md` §13 findings 1 to 3 and 15 each carry an `**M17:**` line.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed (and the `turnbase-platform`
  ref bumped if FR-DBQ-007 changed the chart).

---
