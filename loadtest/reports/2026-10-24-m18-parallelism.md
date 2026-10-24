# `parallelism`, M18 single-instance re-verification, `IMP-M18-07`, 2026-10-24

**Verdict:** On the M18 build (`IMP-M18-03` to `05`, the OpenTelemetry agent as specified) `parallelism` passes every step up to 128 pairs and, for the first time, runs the 256-pair step in full: it fails there on `tb_room_join` (p95 238 ms) and `tb_room_create` (211 ms) while moves stay at 102 ms. Peak **2,068 moves/s** at 128 pairs (M18 baseline 1,690, +22%), platform CPU per move 1.84 ms against 2.09 ms (-12%). The first to break is **DB pool** (`hikari_pending` up to 150 with Postgres at 2.1 of 4 cores); the platform is at 3.84 of 4 cores. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `parallelism` (levels 1, 2, 4, 8, 16, 32, 64, 128, 256 pairs; 120 s steps, 20 s settle), once, after `reset.sh` and provisioning (3,000 users), as `IMP-M17-05` and `IMP-M18-02` ran it |
| Parameters (`params.txt`) | `scenario=parallelism`, `K6_CORES=4`, `USERS=3000` |
| Start (UTC) | 2026-10-24T20:12:31Z |
| End (UTC) | 2026-10-24T20:30:43Z (18 min 12 s, the whole plan) |
| k6 exit code | 99 (`tb_room_create{step:256}` and `tb_room_join{step:256}` crossed; this scenario does not abort) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261024-221228-parallelism` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`, as in the M18 baseline) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 mean at most 238% of the 320% allowed on the pinned cores; no segment generator-bound (`check-generator.sh`: 9 of 9 `ok`) |
| Root commit | 06ffbe487fdd2f7345d232151dd33cc0a05f53d9 (the claim commit of `IMP-M18-07`; the report is committed after it) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | 9eb97384a10dd427e2086cf0d81ce263ebc699ec (`IMP-M18-05`; includes `03`, `04`, `05` and the agent as specified, `IMP-M18-06`). Image `turnbase/platform:dev` built from it with `clean package` (`sha256:c93612fe48d9...`) |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 (image `sha256:15f70fd3ccc5...`, unchanged since M16) |
| `turnbase-frontend` | image `sha256:3663712f5b6e...`, unchanged since M17 |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values are `values-local.yaml` plus the Phase B `loadtest/helm/values-loadtest.yaml`, identical to the M18 baseline (`2026-10-24-m18-baseline.md` §2): Platform 4 CPU / 3 GiB, Game Host 2 CPU / 4 GiB, PostgreSQL 4 CPU / 2 GiB with the rescaled `postgres.settings`, Redis 1 CPU / 512 MiB, pool of 10. Only the platform image differs from the baseline. Full `helm get values` and image IDs are in `cluster.txt`.

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when every row passes for that step. Observed values are those of the last passing step, 128 pairs.

| Metric | Target | Observed p95 (128 pairs) | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 58 ms | 80 ms | pass at every step (256 pairs: 102 / 142 ms) |
| `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | create 86 ms, join 97 ms | 122 / 142 ms | pass at 1 to 128 pairs; **fail at 256** (create 211 ms, join 238 ms, p99 288 / 325 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 63 ms | 88 ms | pass at every step (256: 125 / 171 ms) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s | 125 ms | 166 ms | pass at every step (256: 263 / 347 ms) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass: `tb_errors` 0 in 177,960 games, 1,356,360 moves |
| Concurrent sessions | >= 500 | 90 at 128 pairs, 172 at 256 | n/a | **not reached** |
| Concurrent WebSockets | >= 5,000 | 253 at 128 pairs, 506 at 256 | n/a | **not reached** |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`, from `steps.csv`. Postgres cores are the mean of `pods.csv` (`kubectl top`) after each step's settle window.

### `parallelism`: M18 baseline vs M18

| Step (pairs) | Moves/s, baseline / M18 | `tb_move_rtt` p95 ms, baseline / M18 | `tb_room_join` p95 ms, baseline / M18 | `tb_room_create` p95 ms, baseline / M18 | Postgres cores (of 4), baseline / M18 | Verdict, baseline / M18 |
|---|---|---|---|---|---|---|
| 1 | 126 / 140 | 6 / 4 | 8 / 8 | 7 / 7 | 0.14 / 0.13 | pass / pass |
| 2 | 284 / 308 | 5 / 3 | 7 / 6 | 6 / 6 | 0.33 / 0.32 | pass / pass |
| 4 | 582 / 584 | 6 / 4 | 8 / 7 | 7 / 6 | 0.68 / 0.64 | pass / pass |
| 8 | 1,024 / 1,005 | 8 / 5 | 9 / 8 | 9 / 8 | 1.31 / 1.16 | pass / pass |
| 16 | 1,403 / 1,480 | 16 / 9 | 16 / 11 | 14 / 10 | 1.81 / 1.61 | pass / pass |
| 32 | 1,521 / 1,798 | 38 / 17 | 34 / 18 | 33 / 18 | 1.87 / 1.84 | pass / pass |
| 64 | 1,683 / 1,955 | 76 / 33 | 82 / 38 | 72 / 36 | 2.12 / 1.96 | pass / pass |
| 128 | 1,690 / 2,068 | 151 / 58 | 169 / 97 | 150 / 86 | 2.13 / 2.10 | pass / pass |
| 256 | cut short (not valid) / 2,067 | 166 / 102 | 191 / 238 | 177 / 211 | 2.15 / 2.12 | not valid / **fail** |

The 256-pair step ran in full this time (206,721 moves, 26,970 warm game starts), so it is a measurement; the baseline's was cut short at 17 min 14 s and the cause of that truncation is not known (finding 3 of the baseline). Segment means (`snapshot.sh`; segment k holds 2^(k-1) pairs):

| Segment | 4 (8 pairs) | 5 (16) | 6 (32) | 7 (64) | 8 (128) | 9 (256) |
|---|---|---|---|---|---|---|
| Platform cores (of 4), baseline | 2.87 | 3.37 | 3.31 | 3.56 | 3.54 | n/a |
| Platform cores (of 4), M18 | 2.74 | 3.33 | 3.61 | 3.73 | 3.80 | 3.84 |
| Game Host cores (of 2), M18 | 0.98 | 1.30 | 1.43 | 1.45 | 1.40 | 1.38 |
| `hikari_active` max, M18 | 4 | 5 | 6 | 10 | 10 | 10 |
| `hikari_pending` max, baseline / M18 | 0 / 0 | 0 / 0 | 21 / 0 | 37 / 43 | 148 / 111 | n/a / 150 |

Platform CPU per move (segment mean cores over moves per second): 64 pairs 1.91 ms (baseline 2.12), 128 pairs 1.84 ms (2.09): -10% and -12%. Generator check: 9 of 9 segments `ok`.

## 5. Result

Ceiling (pairs): 128
First to break: DB pool
Evidence: every step up to 128 pairs passes and the 256-pair step fails on two thresholds only, `tb_room_join` (p95 238 ms) and `tb_room_create` (211 ms); moves, lobby events and game starts stay inside their targets. At 256 pairs the pool of 10 is saturated (`hikari_active` max 10) and requests wait for a connection (`hikari_pending` mean 50, max 150) with Postgres at 2.12 of 4 cores (53%), well under the 95% (3.8) of the `load-testing.md` §8 rule, so the rule names `DB pool`, not `PostgreSQL`. The platform is at 3.84 of 4 cores (96%), the next limit. No restart, no 5xx, no generator-bound segment. The ceiling equals the baseline's (128), but the baseline's 256-pair step was not valid, so the true gap is unknown; the throughput gap is not: peak 2,068 moves/s against 1,690.

Capacity statements:

- 500 concurrent sessions: **not reached** (172 at 256 pairs).
- 5,000 WebSockets: **not reached** (506 at 256 pairs).

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Pod restarts and `OOMKilled` (from `cluster.txt`): platform, Game Host, Postgres and frontend 0 restarts; Redis and the observability pods show 7 restarts from before the session; no `OOMKilled`; no 5xx (`http_5xx_per_s` has no samples). Redis `used_memory` 1.61 MiB. Platform threads 78 to 292 (mean 291 in the 256-pair segment), Game Host threads 42 to 229. Postgres statements by total time: `update game set completed_session_count` 0.71 ms mean (177,960 calls, 127 s; baseline 0.49 ms), `update room set version` 0.15 ms (676k calls, 101 s), `insert into game_history_entry` 0.20 ms (356k calls, 71 s); the per-join statements `IMP-M18-03` removed are not in the list, and no statement is slow, the volume is the load. Full tables are in `snapshot.out`.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

1. **The M18 platform changes moved throughput, not the ceiling.** Peak 2,068 moves/s (baseline 1,690, M17 1,779) at 128 pairs and platform CPU per move -10 to -12% (`IMP-M18-03` to `05`: fewer statements per create and join, the participant cache, one Redis round trip per move). Move p95 at 128 pairs is 58 ms (151). The pass/fail step is the same, 128 pairs, because `tb_room_create` and `tb_room_join` are what fail and a faster client issues more of them per second at the same pair count.
2. **The first to break is still the connection pool, with the platform at 96% of its CPU.** `hikari_pending` max 150 at 256 pairs with Postgres at 53%; this is the baseline's finding 2 unchanged. `NFR-DBQ-001` for this scenario: `DB pool`, fail.
3. **The 256-pair step is not cut short this time** (the baseline's and M17's were). The cause of the earlier truncations is therefore not the platform build; it is not investigated here.
4. **Capacity targets** (500 sessions, 5,000 WebSockets) remain unreached on one node.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
