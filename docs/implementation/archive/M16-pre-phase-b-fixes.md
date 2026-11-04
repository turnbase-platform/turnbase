# Archive — M16 Pre-Phase-B fixes

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M16-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M16-01 | Load-test harness and record corrections | docs (umbrella), platform (chart) | — | DONE |
| IMP-M16-02 | Game Host wedge supervision actually restarts the JVM | game-host, platform (chart), docs | — | DONE |
| IMP-M16-03 | First cold boot no longer wedges | game-host, docs (umbrella) | M16-01, M16-02 | DONE |
| IMP-M16-04 | Bounded concurrent guest boots | game-host, docs | M16-03 | DONE |
| IMP-M16-05 | Shared Espresso engine across game contexts | game-host, docs | M16-04 | DONE |
| IMP-M16-06 | Game Host session bookkeeping is released | game-host | M16-05 | DONE |
| IMP-M16-07 | Room ownership: lease renewal is O(1) and loss is recoverable | platform, docs | — | DONE |
| IMP-M16-08 | Closed rooms release their Redis keys | platform, docs | M16-07 | DONE |
| IMP-M16-09 | Reconciliation and metrics stop scanning everything | platform | M16-08 | DONE |
| IMP-M16-10 | Platform threads are bounded and released | platform, docs (umbrella) | M16-01, M16-07 | DONE |
| IMP-M16-11 | Room readiness is not lost to subscribe races | platform, frontend, docs | M16-01 | DONE |
| IMP-M16-12 | The 300-second stall is explained and removed | platform (chart), docs (umbrella) | M16-01, M16-07, M16-09, M16-10 | DONE |
| IMP-M16-13 | Platform CPU per move is profiled and the top hotspots fixed | platform, docs (umbrella) | M16-07, M16-09, M16-10 | DONE |
| IMP-M16-14 | Re-verification runs: capacity | docs (umbrella) | M16-01, M16-02, M16-03, M16-04, M16-05, M16-06, M16-07, M16-08, M16-09, M16-10, M16-11, M16-12, M16-13 | DONE |
| IMP-M16-15 | Re-verification runs: endurance, and the M16 summary | docs (umbrella) | M16-14 | DONE |

---

## M16 — Pre-Phase-B fixes

Opened 2026-10-19 from the 18 findings of Phase A ([`load-testing.md`](../../specs/deployment/load-testing.md)
§13). Phase A was measurement only; M16 is the fixing round the owner asked for before Phase B (autoscaling
and multiple replicas) gets its design. It repairs what Phase A broke, then reruns the heavy scenarios to
show whether it worked.

**The decisions in an item are the owner's.** The owner delegated every design decision of this milestone
to the orchestrator; what an item states as settled is settled, and nobody is to be asked. Where an item
says *amend spec X to say Y* the agent edits that spec as part of the item: that is not a `spec-defect`
stop. A *new* contradiction the item did not anticipate still goes through the `spec-defect` skill.

**Finding to item map.** A finding is cited as "`load-testing.md` §13 finding N". Every finding has an item.

| Finding | Symptom | Fixed or checked by |
|---|---|---|
| 1 | Throughput plateaus at 16 pairs; platform CPU is the limit | `13` (profile, fix), `09`, `10`; rerun `14` |
| 2 | 200 ms move target fails at 128 pairs | `13`; rerun `14` |
| 3 | `tb_room_join` tail stops the ramp | `12`; rerun `14` |
| 4 | `ready_timeout` under load | `11` |
| 5 | Platform threads grow 80 → 226 under load | `10` |
| 6 | The run protocol says `jcmd 1` fails; the record says the image has no `jcmd` | `01` (record corrected) |
| 7 | Game Host wedges and the supervisor does not restart it | `02`, `03` |
| 8 | A four-context cold start takes 10 s | `04` |
| 9 | Four contexts cost about three times the CPU | `05` |
| 10 | A 10 s connect stall about every 300 s | `12` |
| 11 | `start-rate` never found the rate where `game_start` degrades | `14` |
| 12 | `default-limits` trips the WebSocket action bucket every game | `01` (harness artefact) |
| 13 | Two Redis keys per room, never deleted | `08` |
| 14 | Room ownership lost, gauges never recover | `07` (and `09`: it removes the scan load that starves the lease) |
| 15 | Latency rises and throughput falls across a 30-minute soak | `09`, `13`; rerun `15` |
| 16 | Game Host heap after GC grows 251 → 371 MB | `06`; rerun `15` |
| 17 | Platform keeps its threads after the load is gone | `10`; rerun `15` |
| 18 | The Game Host restart took about 6 minutes | `02` |

**Out of scope (owner-held; nothing in M16 decides them).** `game-host-internals.md` §18 `OQ-5` (eager or
lazy reassignment after a Game Host dies); `platform-operations.md` `OQ-004` (`NFR-AVAIL-001` at 99% or
99.9%); `IMP-M13-08`; horizontal scaling and autoscaling (Phase B).

**Sequencing.** `01` → `02` → `03` → `04` → `05` → `06` → `07` → `08` → `09` → `10` → `11` → `12` → `13` →
`14` → `15`. Depends-on enforces it. `01`, `02`, `03` and `10…15` need the cluster; `04…09` do not, but they change
images and the chart, so every live item that follows must rebuild before it measures (below).

**Live items (an `**Environment:**` line).** They need Docker Desktop Kubernetes running with the
`turnbase` Helm release installed through `loadtest/install.sh`. Each starts with `bash loadtest/preflight.sh`
and must print `PREFLIGHT OK`; a cluster that stays down after the failed command is run once more live
is `BLOCKED`, naming the command. Runs longer than eight minutes go in the background and are polled at
most every five minutes (`work-item` *Live-environment and measurement items*).

**Rebuild rule for live items.** The cluster runs `turnbase/<component>:dev` images built locally, and
`master` may have moved since they were built. The platform and Game Host Dockerfiles `COPY target/*.jar`,
so a `docker build` over a stale `target/` packages the old code and reports no error. Before measuring,
for every repository that changed in M16:
1. In each changed Java submodule (`turnbase-platform`, `turnbase-game-host`) run
   `./mvnw clean package -DskipTests` (always `clean`, see `loadtest/README.md` *Run procedure* step 1).
2. `docker build` the image as `loadtest/README.md` *Run procedure* step 1 gives it
   (`turnbase/platform:dev`, `turnbase/game-host:dev`, `turnbase/frontend:dev`; the frontend has no jar step).
3. `bash loadtest/install.sh` when the chart or an overlay changed.
4. `bash loadtest/reset.sh` (it scales every service to zero and back, which starts the new image), then
   `k6 run loadtest/scenarios/provision.js`.

**Check it happened.** The run's `cluster.txt` lists `turnbase/<component>:dev sha256:…` under `## images`.
For every image that changed since the previous run, the ID must differ from the previous run's:
`diff <(sed -n '/^## images/,/^## root commit/p' <previous-run-dir>/cluster.txt) <(sed -n '/^## images/,/^## root commit/p' <this-run-dir>/cluster.txt)`
prints a changed line for each. An identical ID means the rebuild did not happen: stop and rebuild. A
report quotes the IDs.

**Overlay mirroring.** `loadtest/helm/values-default-limits.yaml` must equal `values-loadtest.yaml` except
for the `SPRING_PROFILES_ACTIVE` entry and everything from `^observability:` on; `bash
loadtest/test/check-overlays.sh` enforces it and fails otherwise. Every item that edits
`values-loadtest.yaml` (`01`, `12`, `13`) makes the same edit in `values-default-limits.yaml` and runs
that self-test before it commits.

**Measuring items record, they do not add items.** `10`, `12`, `13`, `14` and `15` measure; they write
their findings into their report under `loadtest/reports/` and into `load-testing.md` §13 (report names
use the run's date, `YYYY-MM-DD-m16-<name>.md`), and never
add a registry item; a problem that persists becomes a *Phase B note*. A §13 finding is annotated by
appending one line to its entry: `**M16:** resolved by IMP-M16-NN, <evidence link or number>` or
`**M16:** persists, <numbers>; Phase B note`.

**Submodules.** An item that changes a submodule bumps its ref in this repository only after the pipeline
on that repository's `master` is green (the CI wait applies to M16 as to any code item unless the loop's
prompt says otherwise).

### IMP-M16-01 — Load-test harness and record corrections

**Repo:** `turnbase` (docs, `loadtest/`), `turnbase-platform` (chart) · **Depends on:** nothing

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release (see the milestone
introduction).

**Covers:** findings 6 and 12, and the harness prerequisites of `10…15`.

**Read first:**
- `loadtest/README.md` and `loadtest/snapshot.sh`, `loadtest/run.sh`, `loadtest/lib/config.js`, `loadtest/lib/pair.js` (`think()`), `loadtest/scenarios/default-limits.js`
- `loadtest/helm/values-loadtest.yaml` (its header comment) and `loadtest/test/check-overlays.sh`
- `docs/specs/deployment/load-testing.md` §13 (findings 6 and 12)
- `turnbase-game-host/docker/supervise.sh` (PID 1 of the Game Host image; the JVM is its child)
- `turnbase-platform/src/main/resources/application.yml` (`turnbase.rate-limit.ws.action`: capacity 10, refill 5 per second)
- `turnbase-platform/deploy/helm/turnbase/templates/postgres-statefulset.yaml`, `.../redis-statefulset.yaml` and `.../values.yaml` (the `postgres` and `redis` keys), `loadtest/reset.sh`

**Satisfies:** none (the owner's instrument for the rest of M16)

**Settled:**
- **Chart hooks (the only chart edit of this item).** The chart gains the values `postgres.extraArgs` and
  `redis.extraArgs`: lists of strings, default `[]`. Postgres has no `args` today, so the StatefulSet
  renders `args:` only when the list is non-empty and the image's entrypoint is otherwise untouched; the
  Redis StatefulSet appends the list after its existing arguments (`--maxmemory-policy noeviction
  --appendonly yes --requirepass …`). With the defaults, `helm template` of both StatefulSets is
  identical to what it was before the change (diff it): production behaviour does not change.
- **Overlay.** `loadtest/helm/values-loadtest.yaml` sets `postgres.extraArgs: ["-c",
  "shared_preload_libraries=pg_stat_statements", "-c", "log_checkpoints=on"]`. `redis.extraArgs` stays
  empty here (`IMP-M16-12` uses it). The same lines go into `values-default-limits.yaml` (overlay
  mirroring, milestone introduction).
- **`reset.sh`** recreates `pg_stat_statements` next to `pgcrypto`, `pg_trgm` and `btree_gin`
  (`DROP SCHEMA public CASCADE` removes the extension's view every time). If `turnbase_owner` is not
  allowed to create it, run that one statement as the Postgres superuser.
- **`run.sh start`** zeroes the counters, because they are cumulative and every "per move" or "per join"
  delta in `13` would otherwise include the previous run: `select pg_stat_statements_reset()`, Redis
  `CONFIG RESETSTAT`, and `CONFIG SET latency-monitor-threshold 100` (the default of 0 leaves `LATENCY
  LATEST` empty, which `12` reads).
- **Process ids.** The platform JVM is PID 1 and its image has no `jcmd` (only `java`, `jfr`, `jrunscript`,
  `jwebserver`, `keytool`, `rmiregistry`), so platform threads come from `/proc` alone. In the Game Host
  image PID 1 and PID 8 are `supervise.sh` and the JVM is the process whose `/proc/<pid>/comm` is `java`
  (PID 7 observed); `/tmp/jvm.pid` is used instead once `IMP-M16-02` writes it. `jcmd` exists there.

**Done when:**
- **Census script.** `bash loadtest/census.sh <run-dir> <label>` writes `<run-dir>/census-<label>.txt`
  with: for the platform and for the Game Host JVM, a table of thread count by name prefix (from
  `/proc/<pid>/task/*/comm`, digits stripped, sorted descending, with the total); the Game Host's
  `jcmd <jvm pid> GC.class_histogram` top 30; and Redis `DBSIZE`, `INFO keyspace`, `INFO memory`
  (`used_memory`) and the `keys` and `scan` lines of `INFO commandstats`. A section that cannot be collected prints
  `<section> unavailable: <reason>` and the script carries on. `loadtest/snapshot.sh` calls it with the
  label `snapshot`; `IMP-M16-10` and `15` call it with `before`, `peak` and `after`. `loadtest/README.md`
  documents it in the *Scripts* table.
- **Statement statistics.** `snapshot.sh` appends the Postgres `pg_stat_statements` top 20 by `calls` and by
  `total_exec_time`; if the extension is missing it prints `pg_stat_statements unavailable` and carries on.
- **Chart and overlay.** `helm lint turnbase-platform/deploy/helm/turnbase` and `helm template` of it are
  green with the defaults (the Postgres and Redis StatefulSets identical to before) and with
  `-f loadtest/helm/values-loadtest.yaml` (the Postgres container shows the two `-c` arguments). The
  `turnbase-platform` branch is merged `--ff-only`, pushed and deleted, and its ref is bumped after the CI
  on its `master` is green.
- **Live check.** After `bash loadtest/install.sh` and `bash loadtest/reset.sh`: `SHOW
  shared_preload_libraries` in Postgres includes `pg_stat_statements`, `select count(*) from
  pg_stat_statements` succeeds, and after `bash loadtest/run.sh start smoke` the first snapshot shows
  `select sum(calls) from pg_stat_statements` is under 500 (the reset ran).
- **Redis sampler.** `run.sh start` also launches a Redis keyspace and memory sampler (`DBSIZE`,
  `used_memory`, a UTC timestamp) every 30 s into `<run-dir>/redis.csv` for the run's duration, stopped
  with the run. It replaces the ad-hoc `/tmp` side loop of `IMP-M15-13`. `loadtest/README.md` documents it.
- **F12 decision (settled).** The WebSocket action bucket (5 per second, burst 10) **stays the product
  limit**. The `default-limits` scenario defaults `THINK_MIN_MS` and `THINK_MAX_MS` to 250 when the
  environment does not set them (the variables exist today and default to 0 elsewhere), so a correct
  client never trips the bucket; `loadtest/README.md` says so. `load-testing.md` §13 finding 12 gains
  `**M16:** resolved by IMP-M16-01, harness artefact, product limit unchanged`.
- **Pair cap follows `USERS`.** `loadtest/lib/pair.js` hard-codes `PAIRS_PROVISIONED = 1000` (line 8) and
  `getPair` throws `VU id beyond provisioned users` at `idx >= 1000` (line 42), which would fail a
  1,500-pair run from VU 1001 on and record the failure as a capacity result. The cap becomes
  `Math.floor(Number(__ENV.USERS || 2000) / 2)` (`provision.js` already defaults `USERS` to 2000), and
  `loadtest/README.md` says so. `k6 inspect` on `parallelism.js`, `ramp-to-break.js` and `start-rate.js`
  succeeds.
- **Finding 6 correction.** `load-testing.md` §13 finding 6, and any other place in the repository that
  says the Game Host image has no `jcmd` (`grep -rn "jcmd" docs loadtest --include=*.md`), is corrected:
  in the Game Host image `jcmd` exists at `/usr/bin/jcmd` and `kill` only as a shell builtin; PID 1 is
  `supervise.sh` and the JVM is a child, so `jcmd 1` fails and the JVM's pid is found as above; the
  platform image has no `jcmd` at all (its JVM is PID 1).
- **Values file comment.** The header of `loadtest/helm/values-loadtest.yaml` no longer names the deleted
  `m15-test-definition-plan.md` nor says "a run item never edits it"; it points to `load-testing.md`
  (the M16 items edit it where they say so).
- `bash loadtest/test/check-overlays.sh` and the other self-tests (`loadtest/test/check-generator-selftest.sh`)
  pass; `bash -n` passes on every changed script; `bash loadtest/preflight.sh` prints `PREFLIGHT OK`;
  `bash loadtest/census.sh <a run directory of a finished smoke run> test` and `bash loadtest/snapshot.sh
  <that directory>` against the live cluster print every new section; `k6 inspect
  loadtest/scenarios/default-limits.js` succeeds.
- `python3 scripts/check-corpus.py` prints `clean`; the umbrella branch is merged to `master` and pushed.

**Evidence (session 216).** `helm lint` green; `helm template` of the defaults is byte-identical to before the change, and with the overlay differs by exactly the Postgres `args` (`-c shared_preload_libraries=pg_stat_statements -c log_checkpoints=on`). Live after `install.sh` and `reset.sh`: `shared_preload_libraries` is `pg_stat_statements`; after `run.sh start smoke` (exit 0) `sum(calls)` was 349, Redis `latency-monitor-threshold` 100, `redis.csv` written and its sampler gone with the run; `snapshot.sh` printed both `pg_stat_statements` tables and `census-snapshot.txt` has every section (platform and Game Host threads, class histogram top 30, `DBSIZE`, keyspace, `used_memory`, commandstats). `check-overlays.sh`, `check-generator-selftest.sh`, `k6 run test/selftest.js` pass; `k6 inspect` succeeds on `default-limits`, `parallelism`, `ramp-to-break` and `start-rate` (also with `USERS=3000`). Finding 6 corrected in `load-testing.md` §13 and the `contexts` report; finding 12 annotated.

### IMP-M16-02 — Game Host wedge supervision actually restarts the JVM

**Repo:** `turnbase-game-host`, `turnbase-platform` (chart), `turnbase` (docs) · **Depends on:** nothing

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release (milestone
introduction; apply the rebuild rule for the Game Host image). The primary test runs in the cluster,
because only the kubelet's restart back-off, which a plain Docker run does not have, can explain the
roughly 6 minutes of finding 18.

**Covers:** findings 7 and 18.

**Read first:**
- `docs/decisions/0018-game-start-resilience.md` (*Decision* 2, *Consequences*) and `docs/specs/game-host/game-host-internals.md` §11 (the paragraph beginning "A wedged guest boot")
- `turnbase-game-host/docker/supervise.sh`, `turnbase-game-host/Dockerfile`
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/espresso/BootWatchdog.java`, `.../registration/HostWedge.java`, `.../registration/RegistrationHealthIndicator.java`, `.../GameHostProperties.java`
- `turnbase-platform/deploy/helm/turnbase/templates/gamehost-deployment.yaml`
- `docs/specs/deployment/load-testing.md` §13 (findings 7 and 18)
- `docs/specs/deployment/local-environment.md` §7.8 (the Game Host property table, where `wedge-marker` is added)

**Satisfies:** none (ADR-0018 §2 as amended)

**Settled:**
- **Two wedge modes, two mechanisms.** (A) The *whole-JVM deadlock* (ADR-0018 *Context* 1, the real wedge
  of findings 7 and 18): no Java thread runs, SIGTERM is ignored, `/actuator/health` does not answer. Only
  the supervisor can act, by **probe silence**. (B) The *BootWatchdog layer*: the JVM is alive, a guest
  boot thread is stuck, the watchdog fires, `HostWedge` marks the host out of service and the supervisor
  reacts to the **503 and the marker file**. The tests below say which mode each exercises.
- **Why it fails today.** The image has no `kill` binary (it is a shell builtin), so `HostWedge`'s
  `ProcessBuilder("kill", "-9", …)` always fails; `supervise.sh` probes `/actuator/health` with `curl -s`
  and so counts the wedge's own 503 as an answer. `jcmd`, `curl` and `timeout` do exist in the image.
- **`HostWedge`.** It no longer starts any external process; the `ProcessBuilder("kill"…)` path and the
  `wedge-kill` thread are removed. On a wedge it (1) publishes an `AvailabilityChangeEvent` with
  `LivenessState.BROKEN`, (2) writes a marker file whose path is the new property
  `turnbase.gamehost.wedge-marker` (default `/tmp/turnbase-wedged`), (3) keeps the `Runtime.halt(70)`
  attempt after the existing 4 s grace.
- **`docker/supervise.sh` respawns the JVM itself.** It runs the JVM in a loop, so the kubelet's
  CrashLoopBackOff (it grows to 5 minutes and is the likely cause of finding 18) never applies to a wedge.
  After a 45 s grace per JVM, four consecutive silent probes SIGKILL the JVM and the loop starts a new one
  at once (the marker file is removed before the start). The script exits non-zero, so that kubelet
  restarts the container, only after **5 JVM deaths within 10 minutes**. A TERM or INT is passed to the
  JVM and the script exits with its status without respawning.
- **Probing (mode A and B).** It probes `/actuator/health/liveness` (not `/actuator/health`) with `curl -sf
  -m 3`, so a non-2xx answer counts as silent, and writes the current JVM's pid to `/tmp/jvm.pid`. Mode A
  is the silence: nothing answers, four probes, kill. Mode B is the **marker file**: it is checked on every
  probe and, when it exists, the supervisor sends `kill -KILL` (the builtin) to the child at once and
  removes it. Every line the script prints is prefixed with an ISO-8601 UTC timestamp, and it logs the
  child's exit status at every respawn. **A dependency outage (Redis or Postgres down) must not restart the
  host**: that is why the probe uses the liveness group, which excludes them.
- **Chart.** `gamehost-deployment.yaml` already probes `/actuator/health/liveness` (every 10 s, 6
  failures); check that this is still true and change the chart only if it is not or if the container test
  shows it fighting the supervisor. `terminationGracePeriodSeconds` is not set (the 30 s default stands).
  If nothing changes in the chart, `turnbase-platform` is untouched and has no ref to bump.
- **Spec.** ADR-0018 §2 and its *Consequences* timing sentence, and `game-host-internals.md` §11 where it
  describes the supervision, are amended to match: the respawn loop and the 5-in-10-minutes exit, the
  liveness probe, `-f`, the marker file, timestamps, BROKEN, the dead `kill` fallback removed, and the
  measured restart time of the cluster test.

**Done when:**
- **Primary test: the real wedge, in the cluster (mode A, findings 7 and 18).** With the rebuilt image
  running, `kubectl exec deploy/turnbase-gamehost -- sh -c 'kill -STOP <pid>'` where `<pid>` is the process
  whose `/proc/<pid>/comm` is `java`, **twice in a row**. Issue the second STOP no earlier than `GRACE` + 5 s (50 s) after the new JVM's first log
  line: the supervisor's 45 s grace restarts for every new JVM, and a STOP inside it would wait out the rest
  of the grace and fail the criterion through test timing, not through a defect.
  For each cycle, measure from the STOP to the first log line of the new JVM (the supervisor's timestamps
  and `kubectl logs --timestamps`). **Every cycle is at most 40 s.** The arithmetic: four silent probes,
  each a `curl -m 3` plus a 2 s sleep, are about 18 s; the kill and the start to the first log line add
  about 3 s; so 25 s is typical and 40 s the limit. Both timings and the pod's restart count (0 expected)
  go into ADR-0018. If a cycle is longer, find the cause and fix it. **After one fix cycle**, if a cycle is
  still over 40 s, record both timings and the cause in ADR-0018 and mark the item `DONE`.
- **Supervisor shell test (mode A and mode B, no cluster).** `bash
  turnbase-game-host/docker/test/supervise-test.sh` runs the real `supervise.sh` with a fake `java` first
  on `PATH` and a local stub HTTP server for the liveness URL, and proves: a stopped or silent child is
  killed after `FAILURES` probes and respawned, with the script still running (mode A); a 503 on the
  liveness URL counts as silent; the marker file kills the child within 3 s, is removed, and the child is
  respawned (mode B); a child that ignores TERM is still killed; an overall health `DOWN` with liveness
  `UP` does not kill it; 5 deaths within 10 minutes make the script exit non-zero. `supervise.sh` is
  `#!/bin/sh` (dash in the image) and the test runs it with `sh`, not `bash`. The script reads its
  settings from named environment variables, which the test overrides: `TURNBASE_SUPERVISOR_GRACE`,
  `TURNBASE_SUPERVISOR_FAILURES`, `MANAGEMENT_SERVER_PORT`, `TURNBASE_SUPERVISOR_PIDFILE` (default
  `/tmp/jvm.pid`), `TURNBASE_SUPERVISOR_MARKER` (default `/tmp/turnbase-wedged`),
  `TURNBASE_SUPERVISOR_MAX_DEATHS` (5) and `TURNBASE_SUPERVISOR_WINDOW` (600 seconds). The test script is
  run directly: no Maven lifecycle change. A step `Supervisor test` (`bash
  docker/test/supervise-test.sh`) is added to `turnbase-game-host/.github/workflows/build.yml` before the
  Maven build, and the CI on `master` passes with it.
- **Unit test (mode B).** `HostWedgeTest` proves a wedge publishes `LivenessState.BROKEN`, writes the
  marker, and starts no external process.
- `turnbase-game-host`: `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green;
  `helm lint turnbase-platform/deploy/helm/turnbase` and `helm template` of it are green; the branches
  merged `--ff-only`, pushed and deleted; the `turnbase-game-host` ref (and the `turnbase-platform` ref if
  the chart changed) bumped after CI is green.
- `python3 scripts/check-corpus.py` prints `clean`.

**Evidence (session 217).** Primary test in the cluster, image `turnbase/game-host:dev` `sha256:7094bc20…`: `kill -STOP` of the JVM (pid 8, then 255), the second STOP 58 s after the new JVM's first log line. STOP to the new JVM's first log line: **17.2 s and 16.0 s**, restart count 0, supervisor lines `has not answered 4 liveness probes in a row; killing it`, `exited with status 137 (death 1 of 5 within 600 s)`, `started JVM 255`. Mode B live: `touch /tmp/turnbase-wedged` killed JVM 476 within the second, started 618. `docker/test/supervise-test.sh` passes (mode A silent, stopped, 503, TERM-ignoring child, health DOWN with liveness UP, marker, SIGTERM, 5 deaths, window); `HostWedgeTest` covers BROKEN, marker and no process. `./mvnw verify -Pintegration` green; the chart needed no change (`helm lint` green; it already probes `/actuator/health/liveness`), so `turnbase-platform` is untouched. CI on `turnbase-game-host` `master` (`b6b1469`) green including the new `Supervisor test` step.

### IMP-M16-03 — First cold boot no longer wedges

**Repo:** `turnbase-game-host`, `turnbase` (docs, `loadtest/`) · **Depends on:** IMP-M16-01, IMP-M16-02

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release; apply the rebuild
rule (the Game Host image carries the `IMP-M16-02` supervisor). The wedge occurs on a container cold
start, which an in-JVM test does not reproduce, so the harness restarts the real Game Host pod and boots a
real game through the platform.

**Covers:** the cause behind findings 7 and 18 (ADR-0018 records 5 of 23 restarts wedging).

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §11 (the paragraph beginning "A wedged guest boot": it already names a suspected cause, the `nfi-gc` thread against the boot thread's `dlsym` in glibc 2.34)
- `docs/decisions/0018-game-start-resilience.md` (*Context*)
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/warmup/GameHostWarmup.java`, `.../warmup/WarmupLifecycle.java`, `.../espresso/EspressoContextFactory.java`, `.../espresso/BootWatchdog.java`
- `turnbase-game-host/docker/supervise.sh` (as changed by `IMP-M16-02`)
- `loadtest/run.sh`, `loadtest/README.md`, `loadtest/scenarios/smoke.js`, `loadtest/lib/pair.js` (`getPair`), `turnbase-platform/deploy/helm/turnbase/templates/gamehost-deployment.yaml`

**Satisfies:** none

**Settled:**
- **Harness first: `loadtest/boot-wedge-repro.sh <cycles> <pairs> [--dry-run]`** in the umbrella (not in
  game-host). Each cycle: (1) delete the Game Host pod, `kubectl delete pod -l
  app.kubernetes.io/name=gamehost,app.kubernetes.io/instance=turnbase` (the chart's `turnbase.selectorLabels`
  with the release name `turnbase`; verify with `kubectl get pods --show-labels`); (2) wait until a pod with a
  different name from the deleted one exists, then for it to be Ready (`kubectl wait
  --for=condition=Ready`, 300 s, the same as `reset.sh`'s rollout wait; a mode-A wedge during start costs
  about 63 s of kill plus the next boot); on a timeout write the row with `smoke_exit=ready_timeout` and go
  on with the next cycle, so one bad cycle does not abort the 40; (3) run `bash loadtest/run.sh start smoke
  PAIRS=<pairs>` and `bash loadtest/run.sh wait` it, so that the first real guest boot happens through the
  platform with the Tic-Tac-Toe bundle; (4) save the new pod's `kubectl logs --timestamps` and, when the container restarted (the
  supervisor exited after 5 deaths), also `kubectl logs --previous`, and count, in them, both wedge modes: mode B, the `BootWatchdog` line `Guest boot wedged`, and mode A, the timestamped
  supervisor lines `killing it` and the respawn from `IMP-M16-02`. It appends one CSV row per cycle to
  `<run-dir>/boot-wedge.csv` (`cycle,pairs,pod,mode_a,mode_b,smoke_exit,seconds_to_first_game`) in a
  run directory `loadtest/results/<stamp>-boot-wedge/` that also holds the logs. `<pairs>` is 1 for the
  baseline and 4 for contention (four pairs started at the same moment, so four contexts boot at once);
  `smoke.js` gains an env `PAIRS` (default 1), read with the `e()` helper style of `loadtest/lib/config.js`
  (an empty string counts as unset): the scenario becomes `per-vu-iterations` with `vus: PAIRS` and
  `iterations: 1` (`shared-iterations` could let a fast VU take two and leave a pair idle), `setup()` logs
  in `2 * PAIRS` users, and the threshold `tb_games_completed` becomes `count >= 3 * PAIRS`; check that
  `getPair` gives each VU its own two users. `--dry-run` prints the
  commands of one cycle and runs none of them. The harness is documented in the `loadtest/README.md`
  *Scripts* table. No `stress-ng`, no `grpcurl`, no fixture jar: the Tic-Tac-Toe bundle is the guest.
- **Hypothesis to test first.** The throwaway bridge-only warm-up context (`GameHostWarmup`,
  `WarmupLifecycle`, `createBridgeOnly`, closed by try-with-resources) races the first real boot's native
  library loading. Experiment: keep the warm-up context open until the first real context has booted (or
  close it on a background thread after that) and measure again.

**Done when:**
- **Harness checks.** `bash -n loadtest/boot-wedge-repro.sh` passes and `bash loadtest/boot-wedge-repro.sh 1
  1 --dry-run` prints one cycle's commands without running them; `k6 inspect loadtest/scenarios/smoke.js`
  succeeds and `bash loadtest/run.sh start smoke` (PAIRS unset) behaves as before.
- **Baseline recorded.** `bash loadtest/boot-wedge-repro.sh 40 1` is run (in the background, polled at most
  every five minutes). `game-host-internals.md` has a short new subsection on boot wedges (in §11 or §6.1,
  whichever fits) giving the cycles, the mode A and mode B counts and the rate of the baseline, with the
  CSV's run directory.
- **If the baseline reproduces (at least 1 of 40, either mode):** a fix lands in `turnbase-game-host`, the
  image is rebuilt and the rerun of 40 cycles shows 0 of 40, and the cause is written down in that
  subsection.
- **If the baseline shows 0 of 40:** run `bash loadtest/boot-wedge-repro.sh 40 4` (contention: four pairs
  started at once). If that is also 0, record "not reproducible outside the cluster; mitigated by
  IMP-M16-02" with both sets of numbers; the item is then `DONE`.
- **If no experiment helps.** After two experiments (the warm-up hypothesis above and one more chosen from
  the evidence) without a drop in the wedge rate, record the negative result in the same subsection (both
  rates and what each experiment changed), keep the `IMP-M16-02` supervisor as the mitigation, and mark
  the item `DONE`. Do not go on to a third.
- **If an experiment lowers the rate but not to 0** (added by `IMP-GATE-100`): the change that lowered it
  lands in `turnbase-game-host` as the default, its rerun of 40 cycles is recorded with its rate and
  the baseline's in the same subsection, and the supervisor stays as the mitigation for the residue. That
  is the end of the item (`DONE`); no third experiment is run to chase the residue.
- The harness is committed in the umbrella and documented in `loadtest/README.md`; the umbrella branch is
  merged to `master` and pushed.
- If a fix landed: `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green in
  `turnbase-game-host`; branch merged `--ff-only`, pushed and deleted; the `turnbase-game-host` ref is
  bumped after CI on its `master` is green. `python3 scripts/check-corpus.py` prints `clean`.

**Closed:** IMP-GATE-100 (opened and closed 2026-10-19, session 218) — the *Done when* clause covered a
baseline that reproduces and is fixed to 0 of 40, and experiments that do not help, but not the outcome that
happened: the warm-up experiment cut the rate from 11 of 40 to 2 of 40 and never reached 0. A fourth branch
was added above (rate lowered, residue left to the supervisor, item `DONE`), consistent with the existing
stop-after-two-experiments rule. Fixed in this section only.

### IMP-M16-04 — Bounded concurrent guest boots

**Repo:** `turnbase-game-host`, `turnbase` (docs) · **Depends on:** IMP-M16-03

**Covers:** finding 8.

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §6.1, §6.3, §12, §15
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/espresso/GameContextManager.java`, `.../espresso/ManagedContext.java` (`bridgeClient()` is `synchronized` and runs under `watchdog.guard`), `.../espresso/BootWatchdog.java`, `.../GameHostProperties.java`
- `docs/specs/deployment/load-testing.md` §13 (finding 8)

**Satisfies:** none

**Settled:**
- A fair `Semaphore` caps concurrent guest boots: `turnbase.gamehost.max-concurrent-boots`, default `2`.
  The `BootWatchdog` timer for a context starts when its boot **acquires a permit**, not when it is
  queued, so a queued boot waits without tripping it. The wait is bounded by the caller's gRPC deadline on
  `CreateSession`; no new timeout is added.
- `GameContextManager` uses `ConcurrentHashMap.computeIfAbsent`, which holds the bin lock while the
  mapping function runs. Check whether the boot runs inside it. If it does, change to a per-key holder
  (the map stores a `CompletableFuture` or equivalent, created inside `computeIfAbsent` and completed
  outside it), so that a slow boot for key A never blocks `get` for key B.
- `game-host-internals.md` §6.1 documents the cap, the property (add it to §15), and when the watchdog
  starts.

**Done when:**
- An integration test boots four distinct contexts concurrently with a `boot-timeout` small enough that
  four parallel boots would exceed it and two do not (or with a fake slow boot) and asserts no wedge and
  all four ready.
- A unit test proves a queued boot's watchdog has not started before its permit is acquired.
- A unit test proves a slow boot for key A does not block `get` for key B.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-game-host` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M16-05 — Shared Espresso engine across game contexts

**Repo:** `turnbase-game-host`, `turnbase` (docs) · **Depends on:** IMP-M16-04

**Covers:** finding 9 (four contexts cost about three times the CPU and twice the heap).

**Read first:**
- `docs/decisions/0005-game-sandbox-espresso-spike.md` and `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`
- `docs/specs/game-host/game-host-internals.md` §4 (isolation), §4.2 (context-builder configuration, spike-locked)
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/espresso/EspressoContextFactory.java`, `.../espresso/GameContextManager.java`
- `docs/decisions/INDEX.md` (to register the new ADR)
- `docs/specs/deployment/load-testing.md` §13 (finding 9)

**Satisfies:** none

**Settled:**
- `EspressoContextFactory` builds every context without a shared `Engine`. Spike one shared
  `org.graalvm.polyglot.Engine` for all contexts. Contexts stay separate; the sandbox and isolation
  options of each context are unchanged.
- **Acceptance rule (the owner's).** Adopt the shared engine if all game-host tests (unit and
  `-Pintegration`) pass **and** a new committed benchmark shows at least 25% lower CPU time **or** at
  least 25% lower heap after GC than per-context engines. The benchmark boots four contexts of distinct
  `gameId:version` and plays K moves in each (for example an `-Pintegration` test that measures
  `ThreadMXBean` CPU time and post-`System.gc()` heap, in both modes). Otherwise keep per-context engines
  and record the measured numbers and the reason (for example Espresso rejecting a shared engine for these
  options).
- **Record either way** in a new `docs/decisions/0019-<slug>.md` registered in `docs/decisions/INDEX.md`,
  and in a short pointer in `espresso-spike-results.md`. The ADR states the security reasoning: a shared
  engine shares compiled code and caches, not guest heap, and a context's resource limits and sandbox
  options are still honoured.

**Done when:**
- The benchmark is committed and its numbers are in the ADR; the decision is implemented per the rule.
- If adopted: a test proves a per-context resource limit or sandbox option is still enforced with a shared
  engine (for example a context with a tight statement or memory limit is stopped while a sibling is not).
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-game-host` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M16-06 — Game Host session bookkeeping is released

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M16-05

**Covers:** finding 16 (heap after GC 251 → 371 MB over the soak).

**Read first:**
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/dispatch/SessionDispatcher.java` (`localSessions`, `locks`, `terminated`) and every other per-session map, set or cache in `turnbase-game-host/src/main/java`
- `docs/specs/game-host/game-host-internals.md` §6.2, §9.3 (crash recovery), §15 (retry limit, handler timeout)
- `docs/specs/deployment/local-environment.md` (the `turnbase.orchestration.dispatch-deadline` row)
- `docs/specs/deployment/load-testing.md` §13 (finding 16)

**Satisfies:** none

**Settled:** entries of `localSessions`, `locks` and any other per-session structure are removed when the
session terminates. `terminated` exists to reject late inputs and to discard an in-flight result, so it is
kept in a bounded, expiring structure: **TTL 5 minutes, cap 10,000 entries (oldest evicted first)**, both
named constants. Where the 5 minutes comes from: the spec has no time-based "retry window", only a retry
count of 3 (`game-host-internals.md` §15), and each attempt can last up to the dispatch deadline of 35 s
(`turnbase.orchestration.dispatch-deadline`, `turnbase-platform/src/main/resources/application.yml`
line 107, `local-environment.md`), so the longest a late input or result can still arrive is 3 x 35 s =
105 s; 5 minutes is about three times that. A comment beside the constant gives this derivation.

**Done when:**
- A test creates and terminates 1,000 sessions and asserts every per-session map and set returns to its
  pre-test size (or to at most the stated bound for `terminated`).
- A test proves a late input for a terminated session inside the TTL is still rejected.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-game-host` ref is bumped. The heap-histogram check on the
  live Game Host is left to `IMP-M16-15`.

### IMP-M16-07 — Room ownership: lease renewal is O(1) and loss is recoverable

**Repo:** `turnbase-platform`, `turnbase` (docs) · **Depends on:** nothing

**Covers:** finding 14.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §1.1, §1.3, §1.4, §1.5 (layer 3), §1.6, §5.2
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomOwnershipService.java` (`renewAndRecheck`, `selfEvictInstance`, the claim script and its `ALREADY_MINE` branch, `nextVersion`), `.../room/RoomOwnershipSchedulingConfig.java`, `.../room/RoomEventExecutor.java` (`epochOf` then `nextVersion`), `.../room/ReconciliationJob.java` (`adoptUnownedRooms`)
- `turnbase-platform/src/main/resources/application.yml` (`turnbase.room` ownership keys: lease TTL 10 s, renew 3 s, self-evict-after 6 s)
- `turnbase-platform/src/test/java/io/turnbase/platform/room/RoomOwnershipServiceIT.java`
- `docs/specs/deployment/load-testing.md` §13 (findings 14 and 15)

**Satisfies:** none

**Settled:**
- **Why the lease lapsed (hypothesis the tests must pin).** `owned` is never pruned, and every 3 s
  `renewAndRecheck` does one Redis `GET` per entry on the shared single-thread scheduler; with tens of
  thousands of rooms one pass approaches the 10 s TTL.
- **`owned` loses a room** when the room reaches `CLOSED` and when it is released. **The close hook is
  shared with `IMP-M16-08`.** Every close goes through the one update in
  `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomRepository.java`, method
  `detachSession` (the `update room set state = :nextState …` statement whose `closed_at = case when
  :nextState = 'CLOSED'` is at line 2493; verify the line), called from `RoomSessionDetacherImpl`,
  `RoomService` and the listeners, inside `RoomEventExecutor`'s lock and transaction. The pruning of
  `owned` is registered there, as a `TransactionSynchronization.afterCommit` that runs only when
  `nextState` is `CLOSED`, as one small method that `IMP-M16-08` then extends rather than duplicates. If
  `TransactionSynchronizationManager.isSynchronizationActive()` is false (unit tests call `detachSession`
  without a transaction, and `registerSynchronization` throws then), the callback runs immediately.
- **Lease renewal is one Redis command** (`pod:<id>:alive`, TTL 10 s, every 3 s) on a dedicated
  single-thread scheduler named `lease-renewer`. The per-room ownership re-check is a separate task that
  uses batched `MGET` (batches of 500) and cannot delay renewal.
- **`ALREADY_MINE` re-registers.** When the claim script answers `ALREADY_MINE` and the room is missing
  from `owned`, the room is registered in `owned` with its current epoch. (`podId` is per incarnation,
  `room-lifecycle.md` §1.1, so this branch is reached by the same process after a self-eviction. A
  restarted container has a new `podId` and adopts its rooms through §1.4.)
- **Self-eviction stays "unconditionally fatal"** (§1.5 layer 3), realised as: it publishes
  `LivenessState.BROKEN` so Kubernetes restarts the platform container; the new incarnation adopts the
  rooms through the claim path. Amend `room-lifecycle.md` §1.3, §1.5 and §1.6 accordingly (release also
  on close; the renewal and re-check split; the BROKEN publication).
- **The race** in `RoomEventExecutor.execute` (`epochOf` passes, an eviction runs, `nextVersion` throws
  `IllegalStateException`) surfaces as `RoomUnavailableRetryException`, never as an
  `IllegalStateException` or an HTTP 500.

**Done when** (tests under `turnbase-platform/src/test/java/io/turnbase/platform/room/`, extending
`RoomOwnershipServiceIT`):
- A room that reaches `CLOSED` leaves `owned`.
- Lease renewal still happens on time while the re-check task is blocked (a latch or a slow Redis).
- 20,000 owned rooms: one re-check pass completes within 2 s against Testcontainers Redis.
- `ALREADY_MINE` repopulates `owned`, and a mutation then succeeds.
- A self-eviction publishes `LivenessState.BROKEN`.
- The `epochOf`/`nextVersion` race maps to `RoomUnavailableRetryException`.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green (this includes
  `ModularityTest`); branch merged `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped;
  `python3 scripts/check-corpus.py` prints `clean`.

### IMP-M16-08 — Closed rooms release their Redis keys

**Repo:** `turnbase-platform`, `turnbase` (docs) · **Depends on:** IMP-M16-07

**Covers:** finding 13.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §1.1 (key table), §1.2, §1.3, §4 (`detachSession`, the transition to `CLOSED`), §5.2
- `docs/specs/platform/data-model.md` (the `room.state` column and `closed_reason`)
- `turnbase-platform/src/main/java/io/turnbase/platform/room/RoomOwnershipService.java` (`CLAIM_SCRIPT`, `RELEASE_SCRIPT`), `.../room/ReconciliationJob.java`, `.../room/RoomSessionDetacherImpl.java`
- `turnbase-platform/src/test/java/io/turnbase/platform/room/ReconciliationJobIT.java`
- `docs/specs/deployment/load-testing.md` §13 (finding 13)

**Satisfies:** none

**Settled:**
- When a room's `CLOSED` transition commits, delete `room:<id>:pod` (only if it names this instance: a Lua
  compare-and-delete) and `room:<id>:epoch`. This is the **same after-commit hook** `IMP-M16-07` put in
  `RoomRepository.detachSession` (the `CLOSED` update at about line 2493, `closed_at = case when
  :nextState = 'CLOSED'`): extend that one method, do not register a second hook, so the two cleanups
  cannot diverge. **Verify first that `CLOSED` is terminal** in the room state
  machine (`room-lifecycle.md`, `data-model.md`, `room-websocket.md`: "The room cannot be rejoined"); if
  any document lets a closed room reopen, stop under `spec-defect`, because that would be a genuine new
  contradiction.
- The reconciliation job (`room-lifecycle.md` §5.2) gains a sweep that `SCAN`s `room:*:pod` and
  `room:*:epoch` in batches, checks the rooms' state in Postgres with one query per batch, and deletes the
  keys of `CLOSED` or nonexistent rooms. That cleans crash leftovers and the existing leak. It never uses
  `KEYS`.
- Amend `room-lifecycle.md` §1.1 (the *TTL* column: the keys now live until the room closes) and the §5.2
  duty table.

**Done when:**
- An integration test closes a room and asserts `EXISTS` is `0` for both keys.
- An integration test seeds 5,000 orphan keys for closed rooms: one sweep removes them and leaves the
  keys of open rooms untouched.
- Redis `INFO commandstats` shows 0 `keys` calls across those tests.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M16-09 — Reconciliation and metrics stop scanning everything

**Repo:** `turnbase-platform` · **Depends on:** IMP-M16-08

**Covers:** finding 15 and the platform-CPU share of findings 1 and 2.

**Read first:**
- `turnbase-platform/src/main/java/io/turnbase/platform/room/ReconciliationJob.java` (`reconcileOrphanedSessionArtifacts`: nine `redis.keys(prefix + "*")` calls, then `sessionBelongsToOpenRoom` once per session)
- `turnbase-platform/src/main/java/io/turnbase/platform/common/BusinessMetricsConfig.java` (the two `count(*)` gauges, refreshed every 30 s)
- `docs/specs/platform/data-model.md` (`room_open_state_idx`, `room_active_session_idx`), `docs/specs/deployment/schema-migrations.md` (migration naming)
- `docs/specs/platform/room-lifecycle.md` §5.2
- `docs/specs/deployment/load-testing.md` §13 (finding 15)

**Satisfies:** none

**Settled:**
- Replace the nine `redis.keys` calls with **one** `SCAN` pass over the keyspace (`COUNT 500`), classifying
  each key by its prefix in Java, so a reconcile tick walks the keyspace once, not nine times; and replace
  the per-session `sessionBelongsToOpenRoom` N+1 with one batched query per page of keys.
- The gauges `SELECT count(*) FROM room WHERE state <> 'CLOSED'` and `... WHERE active_session_id IS NOT
  NULL` already have partial indexes in the baseline (`room_open_state_idx`, `room_active_session_idx`).
  Run `EXPLAIN` on a Testcontainers Postgres seeded with 100,000 closed rooms and a few hundred open
  ones. If neither is a sequential scan, record the plans and add nothing. If either is, find why and add
  a Flyway migration (name per `schema-migrations.md`) with the partial index that makes it an index scan.

**Done when:**
- An integration test with 10,000 stale keys asserts 0 `keys` calls (`INFO commandstats`), exactly one
  full `SCAN` iteration per tick (the `scan` count in `commandstats` is the number of pages, not nine
  times that) and correct cleanup of exactly the stale ones.
- A test asserts the number of SQL statements per reconcile tick does not grow with the number of
  sessions (a datasource statement counter, or `pg_stat_statements`).
- An `EXPLAIN`-based test (or, if a test is impractical, a note in the commit message and in
  `load-testing.md` §13 finding 15) shows both gauge queries use an index.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped.

### IMP-M16-10 — Platform threads are bounded and released

**Repo:** `turnbase-platform`, `turnbase` (docs, `loadtest/reports/`) · **Depends on:** IMP-M16-01, IMP-M16-07

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release; apply the rebuild
rule of the milestone introduction.

**Covers:** findings 5 and 17.

**Read first:**
- `docs/specs/deployment/load-testing.md` §13 (findings 5 and 17), `loadtest/README.md` (run protocol, `snapshot.sh`)
- `turnbase-platform/src/main/java/io/turnbase/platform/websocket/WebSocketConfig.java` (`configureClientInboundChannel` and the heartbeat scheduler), `.../game/GameHostChannels.java`, `.../upload/UploadAsyncConfig.java` (a bounded pool to copy)
- `turnbase-platform/src/main/resources/application.yml` (`server.tomcat`, `spring.task`)

**Satisfies:** none

**Settled:**
- Set `spring.task.scheduling.pool.size: 4` (the ownership lease has its own scheduler since `IMP-M16-07`).
- Run the `parallelism` scenario at 32 pairs for 3 minutes (`LEVELS=32 STEP_SECONDS=180`) followed by 5
  minutes idle, taking `bash loadtest/census.sh <run-dir> before`, `… peak` (about 2 minutes into the
  step) and `… after` (after the idle wait). Identify which pools retain threads.
- Every pool that grows under load gets explicit bounds and releases idle threads: the STOMP
  `clientInboundChannel`, `clientOutboundChannel` and `brokerChannel` executors configured in
  `WebSocketConfig` (core = available processors, max = 4 × processors, keep-alive 60 s,
  `allowCoreThreadTimeOut` true, a bounded queue with caller-runs rejection); `server.tomcat.threads.max`
  and `min-spare` set explicitly; the gRPC client executors bounded; and any other retaining pool the
  census names gets the same treatment.

**Done when:**
- Configuration tests assert the pool settings (scheduler size, the three STOMP executors, the Tomcat
  keys, the gRPC executor).
- After rebuilding the platform image and reinstalling, the same 32-pair run's idle-after thread count is
  within 10% of idle-before, or within 10 threads, whichever is larger. **If it is still missed after one
  fix cycle** (the cause found and fixed, the run repeated once), record the numbers and the remaining
  cause with evidence as a *Phase B note* in `load-testing.md` §13 and mark the item `DONE`.
- A short report under `loadtest/reports/` (named `YYYY-MM-DD-m16-threads.md`) holds the three census
  tables (before, peak, after) before and after the change, and `load-testing.md` §13 findings 5 and 17
  each get an `**M16:**` line pointing at it.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M16-11 — Room readiness is not lost to subscribe races

**Repo:** `turnbase-platform`, `turnbase-frontend`, `turnbase` (docs, `loadtest/`) · **Depends on:** IMP-M16-01

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release (for the k6 smoke
only); apply the rebuild rule.

**Covers:** finding 4.

**Read first:**
- `docs/specs/api-design/room-websocket.md` (*Destinations*, *Readiness*, *Snapshot Delivery*, *Error Handling*) and `docs/specs/api-design/websocket.md`
- `turnbase-platform/src/main/java/io/turnbase/platform/websocket/WebSocketConfig.java`, `.../websocket/WebSocketChannelInterceptor.java`, `turnbase-platform/src/test/java/io/turnbase/platform/websocket/WebSocketIT.java`
- `loadtest/lib/stomp.js`, `loadtest/lib/pair.js` (`SUBSCRIBE_SETTLE_MS` near the subscriptions), `loadtest/lib/config.js`, `loadtest/README.md`
- `turnbase-frontend/src/features/rooms/roomSocket.ts`, `turnbase-frontend/src/features/rooms/RoomLobby.tsx`
- `docs/specs/deployment/load-testing.md` §13 (finding 4)

**Satisfies:** none

**Settled:**
- Clients must not act on a room until their room-topic `SUBSCRIBE` is confirmed. Mechanism: the STOMP
  `receipt` header on `SUBSCRIBE`, answered with a `RECEIPT` frame once the subscription is registered.
- First verify with an integration test whether the platform's simple-broker configuration already returns
  a `RECEIPT` for a `SUBSCRIBE` with a `receipt` header. If not, implement it (for example a channel
  interceptor) and prove the ordering. The hook must fire after the broker handler has registered the
  subscription: on the `clientInboundChannel` (an `ExecutorSubscribableChannel`), `afterSendCompletion`
  fires when the message has only been handed to the executor, which is too early. Use
  `ExecutorChannelInterceptor.afterMessageHandled` (it runs when the `SimpleBrokerMessageHandler` has
  handled the frame) to send the `RECEIPT`.
- The k6 harness (`stomp.js`, `pair.js`) waits for the `RECEIPT` instead of `SUBSCRIBE_SETTLE_MS`; that
  variable is removed from `config.js` and `README.md`.
- Check whether the frontend room client sends an action (for example `TOGGLE_READY`) before its
  subscription is confirmed. If yes, it waits for the receipt first.
- `room-websocket.md` is amended to require the receipt before a client acts.

**Done when:**
- **Platform integration test.** Subscribe with a receipt, then a broadcast sent immediately after the
  receipt is always received: 1,000 iterations, 0 misses.
- **Smoke.** `k6 run loadtest/scenarios/smoke.js` passes against the live cluster with the receipt-based
  harness (`tb_errors` 0).
- **Frontend.** If the client changed: a unit test proves it sends nothing before the receipt;
  `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm run build` and `npm test` are green in
  `turnbase-frontend`. If it did not, the commit message says what was checked.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green in
  `turnbase-platform`; branches merged `--ff-only`, pushed and deleted; the `turnbase-platform` ref (and
  the `turnbase-frontend` ref, if it changed) bumped; `python3 scripts/check-corpus.py` prints `clean`.

### IMP-M16-12 — The 300-second stall is explained and removed

**Repo:** `turnbase-platform` (chart, if a default changes), `turnbase` (docs, `loadtest/reports/`) · **Depends on:** IMP-M16-01, IMP-M16-07, IMP-M16-09, IMP-M16-10

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release; apply the rebuild
rule. The runs last 15 minutes or more: background them.

**Covers:** findings 3 and 10.

**Read first:**
- `docs/specs/deployment/load-testing.md` §5, §13 (findings 3 and 10), `loadtest/README.md`, `loadtest/reports/2026-10-18-start-rate.md`
- `loadtest/helm/values-loadtest.yaml`, `turnbase-platform/deploy/helm/turnbase/` (Postgres and Redis templates and values)
- `docs/specs/deployment/local-environment.md` (the Redis and Postgres settings)

**Satisfies:** none

**Settled:**
- Run `start-rate` at a constant 16 games/s for 15 minutes (`RATES=16 STEP_SECONDS=900`), or `parallelism`
  at 32 pairs for 15 minutes, with the `IMP-M16-01` sampling. Extract every `ws_connecting` above 2 s and
  every `room_join` above 300 ms with its timestamp; correlate with `kubectl logs --timestamps` of
  Postgres (`log_checkpoints=on` is set by `IMP-M16-01`), Redis (`LATENCY LATEST`, which works because
  `run.sh start` sets `latency-monitor-threshold 100`; `INFO persistence` `aof_delayed_fsync`; RDB saves),
  the platform (GC and safepoint logs: add `-Xlog:gc*,safepoint` to the platform's `JDK_JAVA_OPTIONS` in
  `values-loadtest.yaml` and mirror it in `values-default-limits.yaml`, per the overlay-mirroring rule)
  and the ingress. Reinstall with `bash loadtest/install.sh` after the overlay edit.
- **If the stall no longer appears** after `07`, `09` and `10`: record that with the numbers; the item is
  `DONE`.
- **Otherwise** run the experiment with Postgres `checkpoint_timeout=30min` and Redis `save ""` (the AOF
  stays on), set through the chart hooks `IMP-M16-01` added: `postgres.extraArgs: ["-c",
  "shared_preload_libraries=pg_stat_statements", "-c", "log_checkpoints=on", "-c",
  "checkpoint_timeout=30min"]` (keep the existing entries) and `redis.extraArgs: ["--save", ""]` in the
  overlay, mirrored in `values-default-limits.yaml`. No chart edit is needed for the experiment. Whichever change removes the stall is made permanent in the
  chart defaults if it is a sane production setting: for Redis, RDB snapshots off with the AOF on is
  acceptable; for Postgres, spread the checkpoints (`checkpoint_completion_target=0.9`, a larger
  `max_wal_size`) rather than disabling them. The cause is recorded. If neither removes it, continue down
  the candidates (the 10 s equals the lease TTL; Hikari `maxLifetime` 30 min; the JWKS refresh; the 60 s
  reconcile tick; the 15-minute `upload-slot-cleanup`; the Tomcat accept queue). If every candidate is
  ruled out and the cause remains unknown, record what was ruled out as a *Phase B note* in `load-testing.md`
  §13 and mark the item `DONE`.
- **If the number is still missed after one fix cycle** (a cause found and fixed, the 15-minute run
  repeated once, and `room_join` p99 or a `ws_connecting` above 2 s remains), record the numbers and the
  evidence as a *Phase B note* in `load-testing.md` §13 and mark the item `DONE`.

**Done when:**
- A report under `loadtest/reports/` (`YYYY-MM-DD-m16-stall.md`) holds the correlation table (stall
  timestamps against the logs of each component) and the conclusion.
- A 15-minute rerun shows no `ws_connecting` above 2 s and `room_join` p99 below 300 ms (or the escape
  above applies).
- A chart change, if any, passes `helm lint` and `helm template` and the `turnbase-platform` ref is bumped
  after green CI; the rebuilt install reproduces the rerun. `bash loadtest/test/check-overlays.sh` passes.
- `load-testing.md` §13 findings 3 and 10 carry `**M16:**` lines; `python3 scripts/check-corpus.py`
  prints `clean`; merged to `master` and pushed.

### IMP-M16-13 — Platform CPU per move is profiled and the top hotspots fixed

**Repo:** `turnbase-platform`, `turnbase` (docs, `loadtest/reports/`) · **Depends on:** IMP-M16-07, IMP-M16-09, IMP-M16-10

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release; apply the rebuild
rule.

**Covers:** findings 1 and 2.

**Read first:**
- `docs/specs/deployment/load-testing.md` §13 (findings 1, 2 and 15), `loadtest/README.md`, `loadtest/reports/2026-10-18-parallelism.md`
- `turnbase-platform/src/main/java/io/turnbase/platform/game/GameInputService.java` (the per-move path), `.../room/RoomEventExecutor.java` (the room mutation path: room lock, epoch read, version CAS)

**Satisfies:** none

**Settled:**
- Record a JFR profile of the platform during `parallelism` at 64 pairs. The platform image has no `jcmd`
  (only `java`, `jfr`, `jrunscript`, `jwebserver`, `keytool`, `rmiregistry`), so recording starts with the
  JVM: add `-XX:StartFlightRecording=disk=true,maxage=20m,settings=profile
  -XX:FlightRecorderOptions=repository=/tmp/jfr` to the platform's `JDK_JAVA_OPTIONS` in
  `values-loadtest.yaml` (after `-XX:MaxRAMPercentage=70`), mirrored in `values-default-limits.yaml`
  (overlay-mirroring rule), then `bash loadtest/install.sh` and `bash loadtest/reset.sh`. After the run's
  `exit-code` exists (a chunk still being written cannot be copied reliably), copy the chunk files out with `kubectl cp <platform pod>:/tmp/jfr <dir>` (the image has `tar`), combine
  them with `jfr assemble <dir> platform.jfr` (needs JDK 17 or later; the host's `jfr` is fine if it is 21), and analyse with `jfr summary` and `jfr print --events
  jdk.ExecutionSample --stack-depth 1` (the host JDK's `jfr`, or the pod's through `kubectl exec`). Capture
  `pg_stat_statements` and Redis `commandstats` deltas per move and per room join (the counters were zeroed
  by `run.sh start`, so a snapshot at the end of the run is the delta).
- Write the top-10 CPU hotspots and the per-move and per-join Redis and SQL command counts into a report
  under `loadtest/reports/` (`YYYY-MM-DD-m16-cpu.md`).
- Remove the JFR flags from both overlays in this item's last commit and reinstall, so that `14` and `15`
  measure without the recorder.
- Fix every hotspot that takes 10% or more of platform CPU and has a **local** fix (no architecture
  change, no spec change beyond a clarification). Anything needing more is recorded in the report and in
  `load-testing.md` §13 as a *Phase B note*; it does not become a registry item.

**Done when:**
- The report is committed; each fix has a test; a rerun at 64 pairs shows moves per second and platform CPU
  per move before and after, in the report.
  `bash loadtest/test/check-overlays.sh` passes and the JFR flags are gone from both overlays.
- `load-testing.md` §13 findings 1 and 2 carry `**M16:**` lines.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-platform` ref is bumped; `python3 scripts/check-corpus.py`
  prints `clean`.

### IMP-M16-14 — Re-verification runs: capacity

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M16-01, IMP-M16-02, IMP-M16-03, IMP-M16-04, IMP-M16-05, IMP-M16-06, IMP-M16-07, IMP-M16-08, IMP-M16-09, IMP-M16-10, IMP-M16-11, IMP-M16-12, IMP-M16-13

**Environment:** a live Docker Desktop Kubernetes cluster with the loadtest release, every M16 image
rebuilt and reinstalled (rebuild rule). Measurement only. Each run is long: background it and poll.

**Covers:** the capacity half of the re-verification; finding 11.

**Read first:**
- `loadtest/README.md` (run protocol), `loadtest/reports/TEMPLATE.md`, `loadtest/reports/SUMMARY.md`
- `docs/specs/deployment/load-testing.md` §5, §6, §8, §13
- the Phase A reports of the same scenarios in `loadtest/reports/` (`2026-10-18-parallelism.md`, `…-ramp-to-break.md`, `…-start-rate.md`, `…-contexts.md`)

**Satisfies:** none

**Settled:**
- Provision 3,000 users first (`USERS=3000`; finding 11), and start **every** run with `USERS=3000`
  (`bash loadtest/run.sh start <scenario> USERS=3000 …`), so that the cap in `pair.js` (`IMP-M16-01`) and
  `loginAll` use it. `ramp-to-break` and `start-rate` log in `2 * MAX_PAIRS` users in `setup()` (3,000
  logins for `MAX_PAIRS=1500`; `LOGIN_PARALLEL` applies). Run `parallelism`, `ramp-to-break`, `contexts` and
  `start-rate`, the last with `RATES=1,2,4,8,16,32,64,128 MAX_PAIRS=1500`, following `loadtest/README.md`
  and the run protocol of `load-testing.md`. Reset (`bash loadtest/reset.sh`) and re-provision between
  runs.
- One report per run from `TEMPLATE.md`, checked with `bash loadtest/check-report.sh` until
  `REPORT COMPLETE`, each with a *Phase A vs M16* comparison table against the Phase A report of the same
  scenario. A segment where `check-generator.sh` says `generator-bound` is flagged and not counted.
- No code, chart or overlay change; a bad number is a result.

**Done when:**
- `ls loadtest/reports/*-m16-parallelism.md loadtest/reports/*-m16-ramp-to-break.md loadtest/reports/*-m16-contexts.md loadtest/reports/*-m16-start-rate.md`
  lists four reports (the date prefix is the run's), each `REPORT COMPLETE`.
- `load-testing.md` §13 findings 1 to 4 and 8 to 11 each carry an `**M16:**` line, resolved or persists,
  with the new numbers.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M16-15 — Re-verification runs: endurance, and the M16 summary

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M16-14

**Environment:** as `IMP-M16-14`. The soak holds 30 minutes: background it, poll at most every five
minutes. Measurement only.

**Covers:** the endurance half of the re-verification; findings 5, 13 to 17.

**Read first:**
- `loadtest/README.md`, `loadtest/reports/TEMPLATE.md`, `loadtest/reports/SUMMARY.md`
- `docs/specs/deployment/load-testing.md` §5 (`soak`, `up-down`), §8, §13
- the `IMP-M16-14` `ramp-to-break` report (its ceiling sets the soak load) and the Phase A `soak` and `up-down` reports

**Satisfies:** none

**Settled:**
- Run `soak` (30 minutes at 70% of the new `ramp-to-break` ceiling, as in Phase A, started with
  `USERS=3000` as in `IMP-M16-14`) and `up-down`, with the
  Redis sampler and `bash loadtest/census.sh <run-dir> before|peak|after` (thread counts, Game Host
  class histogram, Redis `INFO`) taken before the load, at its peak and after the idle wait.
- State pass or fail for each, in the reports and in `SUMMARY.md`: no `not owned by this instance` ERROR in
  the platform log; the Redis keyspace returns to its pre-run size within 5 minutes after `up-down` (within
  1%); platform threads idle-after within 10% of idle-before; Game Host heap after GC drifts less than 10%
  over the soak; HTTP p99 drifts less than 25% over the soak; no Game Host restart other than a
  deliberately induced one.
- A problem that persists is a *Phase B note*, never a registry item.

**Done when:**
- `ls loadtest/reports/*-m16-soak.md loadtest/reports/*-m16-up-down.md` lists two reports, each
  `REPORT COMPLETE` by `bash loadtest/check-report.sh`.
- `loadtest/reports/SUMMARY.md` has an *M16* section with the pass or fail of every criterion above and
  links to the reports; `load-testing.md` §13 is annotated for **every** finding 1 to 18 with an `**M16:**`
  line and the evidence link.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

---
