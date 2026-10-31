# `ramp-to-break`, Phase B scaled, `IMP-M18-15`, 2026-10-31

**Verdict:** With autoscaling on (2 to 3 Platform and 2 to 3 Game Host replicas, 1.5 CPU each) `ramp-to-break` reaches **170 pairs** (340 sockets, 76 sessions) and aborts at 180 on `tb_game_start{cold:false}` (p95 2,108 ms, 380 samples). That is below the single-instance ceiling of 220 (`2026-10-24-m18-ramp-to-break.md`), so **NFR-ASC-006 fails**. The abort is not a capacity limit: every other metric at 180 passed (move p95 132 ms, create 113 ms, join 114 ms, Hikari pending 0). It is the first sessions on a Game Host that the autoscaler had just added (the third), which pay a cold Espresso context boot. The same host had been scaled in and out twice during the ramp (flapping), and step 170 lost 28% of its games to it. Single-node, laptop result.

**Phase:** B

## 1. Run

| Field | Value |
|---|---|
| Scenario | `ramp-to-break`, once, after `reset.sh`, provisioning (3,000 users), three `smoke.js` runs at `PAIRS=40` (JVM warm-up) and a wait for the Platform to return to 2 replicas |
| Parameters (`params.txt`) | `K6_CORES=3`, `USERS=3000`, `START_PAIRS=20`, `STEP_PAIRS=10`, `MAX_PAIRS=1500` (120 s steps, 20 s settle) |
| Start (UTC) | 2026-10-31T16:28:10Z |
| End (UTC) | 2026-10-31T16:59:50Z |
| Duration | 31 min 40 s of wall clock; 33 min 28 s of VU time (`clock.start` / `clock.end`: 2,007.7 s of uptime for 1,899.5 s of wall, so the wall clock ran 5.4% slow) |
| k6 exit code | 99 (`tb_game_start{step:180,cold:false}` crossed, `abortOnFail`; a normal finish for this scenario) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 3 of 16 (`taskset`, `K6_CORES=3`) |
| Run directory | `loadtest/results/20261031-172808-ramp-to-break` (git-ignored; its first attempt, `…172801…`, failed the preflight on a terminating Platform pod and ran nothing) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`: 16,326,520,832 bytes) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 28.6, max 43.2; `vm_cpu_pct` mean 70%, max 85%; k6 mean at most 205% of the 240% allowed on 3 pinned cores |
| Root commit | 2a05cba324b040a315343503f46dd167b1e7a420 (the report is committed after it) |
| `turnbase-common` | 8b6d68b1e3fcee8d37ff6c1f7c8deb493fb861bb |
| `turnbase-sdk` | 068174dbc3884aa77e8f2ef66a861d6d80a2b1a7 |
| `turnbase-platform` | f6d9df640c290afeb00611292cf27ffcc1c8275b |
| `turnbase-game-host` | 88173cb915095442fe5e4f7bb13dd33c9583e975 |
| `turnbase-frontend` | 772d8acd44e974ee606ad1bf26a37cc356faf6a8 |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | platform `sha256:dc4779f97b16...`, game-host `sha256:bc385196e16e...`, frontend `sha256:231251173199...` (platform and game-host rebuilt with `clean package` for this item) |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values (`helm get values turnbase`, secrets omitted): `platform.autoscaling` enabled, min 2, max 3, `targetCPUUtilizationPercentage` 40, scale-up policy 1 pod per 30 s with no stabilisation, scale-down 1 pod per 60 s after 120 s; `gamehost.autoscaling` (KEDA) enabled, min 2, max 3, triggers `max(turnbase_gamehost_sessions_utilization)` at 0.7 and `max(turnbase_gamehost_memory_max_percent)` at 85, scale-up 1 pod per 60 s with no stabilisation, scale-down 1 pod per 120 s after 180 s; `platform.db.poolMaxSize` 10; profiles `local,loadtest`; `-XX:MaxRAMPercentage=70` on both JVMs; `observability.prometheus.remoteWriteReceiver` true.

Pod resources (requests equal limits; the VM has 16 CPUs, not halved):

| Component | CPU | Memory |
|---|---|---|
| Platform | 1.5 per replica (2 to 3) | 1.5 GiB |
| Game Host | 1.5 per replica (2 to 3; the §4.4 fallback of `IMP-M18-13`) | 2 GiB |
| Postgres | 4 | 2 GiB |
| Redis | 1 | 512 MiB |

At the replica maxima the requests are 4.5 + 4.5 + 4 + 1 = 14 CPU plus k6's 3 pinned cores: 17 of the node's 16, so the maxima cannot all be busy together with a saturated generator (recorded; `local-environment.md` §7.9 has the budget).

## 3. Thresholds

Observed values are those of step 170, the last step that passed (step 180 in the last line).

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 78 ms | 106 ms | yes |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | create 77.7 ms, join 80.9 ms | 105.7 ms, 108.5 ms | yes |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 73 ms | 98 ms | yes |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 104 ms (step 180: 2,108 ms) | 136 ms (step 180: 2,142 ms) | yes (step 180: no) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | yes |
| Concurrent sessions | >= 500 | not reached (76 at step 170, 81 peak; limiting factor: the autoscaler's cold host) | n/a | no |
| Concurrent WebSockets | >= 5,000 | not reached (340 sockets at step 170; limiting factor: the same) | n/a | no |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`. `steps.csv` has no p50, so only p95 / p99 are given. Generator-bound: none (`check-generator.sh`, 16 of 16 segments `ok`, k6 at most 205% of 240%). The CPU columns are the snapshot's busiest-pod figure (`process_cpu_usage` times the visible CPU count, which rounds 1.5 CPU up to 2, so a pod at its limit reads about 1.5 to 1.7), by 120 s wall-clock segment, which drifts from the steps by the clock slew (up to about 100 s at the end).

| Step | Moves/s | `tb_move_rtt` p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 513 | 47 / 71 | 71 / 100 | n/a (warm-up) | none | 1.47 | 1.13 | no | pass |
| 40 | 952 | 28 / 45 | 46 / 60.7 | n/a | none | 1.22 | 1.21 | no | pass |
| 60 | 1,288 | 28 / 47 | 47 / 74 | n/a | none | 1.15 | 1.53 | no | pass |
| 80 | 1,435 | 37 / 53 | 55 / 76.7 | n/a | none | 1.06 | 1.59 | no | pass |
| 100 | 1,498 | 48 / 68 | 69 / 95 | n/a | none | 1.11 | 1.60 | no | pass |
| 120 | 1,528 | 59 / 82 | 81 / 112 | n/a | none | 0.95 | 1.59 | no | pass |
| 140 | 1,534 | 72 / 103 | 97 / 136 | n/a | 2 `tb_errors` | 0.93 | 1.61 | no | pass |
| 160 | 1,643 | 78 / 111 | 101 / 136 | n/a | none | 0.93 | 1.65 | no | pass |
| 170 | 1,180 | 78 / 106 | 104 / 136 | n/a | 6 `tb_errors` | 0.61 | n/a | no | pass (28% fewer moves: a Game Host scaled in and out) |
| 180 | 27 | 132 / 166 | **2,108 / 2,142** | n/a | none | n/a | n/a | no | **fail** (aborted ~35 s in) |

The other steps (30, 50, 70, 90, 110, 130, 150) all passed, with the same monotone trend: moves per second rise to about 1,640 at 160 pairs and the move p95 rises from 21 ms (50 pairs) to 78 ms (160).

## 5. Result

Ceiling (pairs): 170
First to break: Espresso contention
Evidence: step 180 crossed `tb_game_start{cold:false}` only: p95 2,108 ms over 380 samples (the step lasted about 35 s), with move, create, join and lobby all inside their targets and Hikari pending 0. The new Game Host `turnbase-gamehost-…-2kf5t` was Ready at +1,699 s (wall offset from the scenario start) and logged its first `Game context created` 94 s after `Started GameHostApplication`; the sessions placed on it by the §5.1 spread rule paid the guest boot (about 2 s). The harness tags a start `cold` by time since the scenario start, not by host, so these starts count as warm and trip the abort. This is `Espresso contention` in the list's terms (a cold context boot on a new host), not a CPU, database or memory limit: Postgres was never near its 4 cores, `hikari_pending` was 0 except one sample, and the busiest Platform pod sat at its 1.5 CPU limit from step 60 on with the HPA already at its maximum of 3.

## 6. Server side

Output of `snapshot.sh` (`snapshot.txt` of the run directory; the means per 120 s wall segment, seg 1 = step 20 … seg 16 = step 170):

| Metric (mean) | seg 1 | seg 4 | seg 8 | seg 12 | seg 16 |
|---|---|---|---|---|---|
| Game Host CPU (busiest pod) | 1.47 | 1.05 | 1.14 | 0.92 | 0.61 |
| Platform CPU (busiest pod) | 1.13 | 1.45 | 1.61 | 1.63 | 0.50 |
| Platform threads | 83.5 | 93 | 113 | 131.5 | 144 |
| Game Host threads | 60 | 75 | 92 | 146 | 163 |
| `hikari_pending` | 0 | 0 | 0.125 | 0 | 0 |
| `ws_connections` (sum) | 6 | 16 | 40 | 64 | 87 |
| `rooms_active` | 28 | 102 | 166 | 218 | 245 |
| `sessions_active` | 3.9 | 16 | 36 | 65.5 | 53 |
| `http_5xx_per_s` | 4.9 | 21.6 | 26.8 | 28.0 | 29 |

HTTP p95 / p99 read 0.22 s / 0.22 s in every segment: that is the histogram bucket edge, not a latency (the k6 percentiles are authoritative). The `http_5xx_per_s` series (up to 30 per second) is the `503 room-unavailable-retry` answer to a join that lands on a Platform pod that does not own the room (`tb_rest_retries`, below), not a failure.

| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | see `redis.csv` (30 s samples, bytes) | 1.99M |
| Redis `connected_clients` | 13 (end) | 13 |

Pod restarts and `OOMKilled` (from `cluster.txt`): none for the Platform and Game Host pods (all 0 restarts); the observability pods' counts are those of the VM's earlier life.

Missing metrics: none.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| `http_5xx` | no | 3 (k6 counter) |
| `ws_closed` | no | 18 (k6 counter at the end of the run; not attributed to a step) |
| `tb_games_started` minus `tb_games_completed` | no | 138 games in flight when the abort interrupted the VUs |

## 8. Findings

- **Game Host flapping under a rising load.** The KEDA trigger is `max(turnbase_gamehost_sessions_utilization)` at 0.7. The series is spiky (samples of 23 to 86% next to samples of 0, from `query_range` at 30 s) and is a maximum over hosts, so it crosses 0.7 for a moment and falls under it once a third host spreads the load. Observed: scale-out to 3 at +1,398 s (pod Ready at +1,414), scale-in at +1,622 (224 s later, with the ramp still rising), scale-out again at +1,678 (Ready +1,699), the step-180 abort at about +1,735. Nothing in the 3 min scale-down window protects a host from a metric that is a point maximum. Candidate causes: the metric is a maximum of an instantaneous value; the scale-in stabilisation window is shorter than the ramp's step; the 0.7 threshold sits close to the spread rule's operating point. Not fixed here (measurement item).
- **Throughput dip at step 170.** Moves fell from 164,290 (step 160) to 117,973 and games from 21,545 to 15,398 (-28%) while all thresholds held, at the time the third host drained; `tb_errors` 6 in that step (2 in step 140, 23 over the run). No game was lost (`CORRECTNESS` below fails only on the abort's interrupted games).
- **The cold-tag of the harness does not follow the host.** A new Game Host's first sessions are counted as warm starts and gate the run. Phase B scenarios that scale hosts will show this again; the reports for `spike` and the later runs read the start tail beside the scale events.
- **Platform:** the third replica started 36 s after the scenario start (Ready +51 s), triggered by the setup's login burst, before the steps; the busiest pod is at its CPU limit from step 60 at three replicas, so the Platform tier is at its maximum and near its limit well below the single-instance ceiling in sessions: 76 sessions here against 165 at 220 pairs on a single 4-CPU pod. Three 1.5 CPU pods carry less of the move path than one 4 CPU pod did. This is the likely reason for NFR-ASC-006 failing independently of the flapping, and needs a run with the Game Host held at three.
- **NFR-ASC-001:** Game Host: the host crossed the target at about +1,398 s and its Ready 16 s after its pod started (a boot of 10.3 s); the reaction is below 3 min. The step that first crossed 0.7 is not isolated by the 30 s Prometheus samples; the bound used is the pod's Running-to-Ready time plus KEDA's 30 s polling. Platform: Ready 51 s after the scenario start.
- **Slew:** the wall clock ran 5.4% slow (above), so the wall offsets of the timeline are 5.4% short of the VU time; the steps themselves follow the VU clock.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.

## 10. Scaling timeline (Phase B)

`timeline.csv` of the run directory (`timeline.sh`, every 5 s). Offsets are wall seconds from `scenario.epoch`.

| Time (UTC) | Offset from scenario start | Event | Platform ready/desired | Game Host ready/desired |
|---|---|---|---|---|
| 16:29:43 | +36 s | Platform `…zgckm` Running (HPA 2 to 3, setup login burst) | 2/3 | 2/2 |
| 16:29:58 | +51 s | Platform `…zgckm` Ready | 3/3 | 2/2 |
| 16:52:28 | +1,398 s | Game Host `…tmpzm` Running (KEDA 2 to 3) | 3/3 | 2/3 |
| 16:52:44 | +1,414 s | Game Host `…tmpzm` Ready | 3/3 | 3/3 |
| 16:55:52 | +1,622 s | Game Host `…tmpzm` Terminating (scale-in, ramp still rising) | 3/3 | 3/2 |
| 16:57:11 | +1,678 s | Game Host `…2kf5t` Pending (KEDA 2 to 3 again) | 3/3 | 2/3 |
| 16:57:29 | +1,699 s | Game Host `…2kf5t` Ready | 3/3 | 3/3 |
| 16:59:50 | +1,858 s | k6 aborts at step 180 | 3/3 | 3/3 |

Scale events: 4 (one Platform scale-out, three Game Host: out, in, out). Flapping (a scale-out followed by a scale-in of the same workload within the stabilisation window): 1 Game Host cycle, scale-in 224 s after the scale-out's Running (208 s after its Ready), past the 180 s scale-down window but during a rising ramp.

## 11. Correctness (Phase B)

Output of `correctness.sh` (`correctness.txt` of the run directory), verbatim:

```
games: started 334060 != completed 333922 + abandoned 0 (a started game is neither)
sequence: gaps 0, duplicates 0, over 5093690 broadcast GAME_EVENTs checked
rooms: none IN_PROGRESS, none with an active session
CORRECTNESS: FAIL games
```

The `games` rule failed by 138 games: the threshold abort interrupted 180 VUs, and a VU interrupted between `GAME_STARTED` and the last move leaves one started, uncompleted, uncounted game. No sequence gap, no duplicate and no room left `IN_PROGRESS`. It is the harness's abort and not a lost game, but the harness does not count an interrupted game as abandoned; recorded here, not changed in a run item.

`tb_rest_retries` (a 503 `ROOM_UNAVAILABLE_RETRY` answered to a join on an instance that does not own the room, retried by the harness after `REST_RETRY_MS`): 131,895 over the run (70 per second).

## 12. NFR-ASC (Phase B)

| ID | Target | Observed | Pass |
|---|---|---|---|
| NFR-ASC-001 scale-out reaction | <= 3 min, Platform and Game Host | Platform 51 s from the scenario start to Ready; Game Host: new pod Ready 16 s after Running (the crossing is not isolated at 30 s sampling; well inside 3 min) | yes |
| NFR-ASC-002 correctness through scaling | no lost, duplicated or reordered input, error rate < 1% | sequence gaps 0, duplicates 0, no room `IN_PROGRESS`; error rate 0.00057% (`tb_op_failed`, 23 of 4,017,254); but `CORRECTNESS: FAIL games` from the abort (138 interrupted games) | no (as the harness counts it) |
| NFR-ASC-003 scale-in | back to minimum, resources within 10% of the pre-run level, <= 10 min | n/a (`up-down`) | n/a |
| NFR-ASC-004 spike recovery | thresholds recover <= 3 min | n/a (`spike`) | n/a |
| NFR-ASC-005 sustained high load | p99 drift < 25%, <= 1 scale event per 10 min after the first 10 | n/a (`sustained-high`); the Game Host scaled 3 times in the 20 min after the first 10 | n/a |
| NFR-ASC-006 scaled ceiling | >= the single-instance ceiling | 170 pairs against 220 (`2026-10-24-m18-ramp-to-break.md`) | **no** |
| NFR-ASC-007 failover | games continue, players back in their room <= 30 s | n/a (`failover`) | n/a |
