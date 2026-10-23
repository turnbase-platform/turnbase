# `parallelism`, M17 re-verification, 2026-10-24

**Verdict:** Ceiling 64 pairs and the first to break is **PostgreSQL**, on both builds: the untuned chart (peak 1,779 moves/s at 64 pairs, 1,762 at 128) and the chart with the `IMP-M17-05` PostgreSQL settings (1,733 at 128). `tb_room_create` and `tb_room_join` cross their targets at 128 pairs while the 10-connection pool queues (`hikari_pending` up to 206) and Postgres sits at 2.2 of its 2 cores. `NFR-DBQ-003` holds (ceiling 64, peak 1,779 against 1,002); `NFR-DBQ-001` does not. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `parallelism`, defaults (levels 1, 2, 4, 8, 16, 32, 64, 128, 256 pairs; 120 s steps, 20 s settle), `USERS=3000`, after `reset.sh` and provisioning, twice: run A on the chart as it was (`IMP-M17-04`), run B after `FR-DBQ-007` (see §8) |
| Parameters (`params.txt`) | `scenario=parallelism`, `K6_CORES=4`, `USERS=3000` |
| Start (UTC) | A 2026-10-23T19:45:50Z; B 2026-10-23T21:16:51Z |
| End (UTC) | A 20:02:27Z; B 21:33:30Z |
| Duration | about 16 min 40 s each (the 256-pair step ended early, finding 4) |
| k6 exit code | 99 in both (thresholds crossed at 128 and 256 pairs; the scenario does not abort on them) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261023-214547-parallelism` (A), `20261023-231648-parallelism` (B); git-ignored |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`, as in the M16 reports) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 mean 15% to 193% of the 320% allowed on the pinned cores; no step generator-bound (`check-generator.sh`, 9 of 9 segments ok in both runs) |
| Root commit | a8fc67e76ea77dc56ff674f94a3477d30776c97f (the claim commit of `IMP-M17-05`; the report is committed after it) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | e52c1f4913060b47b34c1aae6823cec3fd76b505 plus the `postgres.settings` chart change of this item (`0b6f015`, committed after the runs; the image is the same) |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 (image unchanged since M16) |
| `turnbase-frontend` | 9b480fe73496f946902916f6ec3084b8d9b0d2bc |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | platform `sha256:56c732e00523...`, game-host `sha256:15f70fd3ccc5...`, frontend `sha256:3663712f5b6e...` (full IDs and the full `helm get values` in each run's `cluster.txt`) |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values are `values-local.yaml` plus `loadtest/helm/values-loadtest.yaml` as in `2026-10-21-m16-parallelism.md` §2, with the `IMP-M17-04` default `platform.db.poolMaxSize: 10`. Run B adds the `postgres.settings` block of `FR-DBQ-007` (§8); run A has Postgres at its image defaults apart from the overlay's `shared_preload_libraries` and `log_checkpoints`.

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when every row passes for that step. Observed values are those of the last step that passed (64 pairs), run B.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 78 ms | 104 ms | pass at every step in both runs (153 / 201 ms at 128 in B) |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 108 ms; `tb_room_create` 97 ms | see `steps.csv` | pass up to 64; `tb_room_join` p95 231 ms (A) and 232 ms (B) and `tb_room_create` 201 and 210 ms fail at 128; `tb_login` happens in setup |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 59 ms | n/a | pass at every step |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 122 ms | n/a | pass at every step (254 ms at 128) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass: `tb_errors` 0 in 141,305 (A) and 140,205 (B) games |
| Concurrent sessions | >= 500 | not attempted (`parallelism` peaks at 256 pairs); 187 (A) and 195 (B) reached at 128 pairs | n/a | not attempted here; `ramp-to-break` measures it |
| Concurrent WebSockets | >= 5,000 | not attempted; 505 and 508 reached | n/a | not attempted here |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`. Run A / run B (`steps.csv`). The M16 column is `2026-10-21-m16-parallelism.md`.

| Step (pairs) | Moves/s, M16 | Moves/s, A / B | `tb_move_rtt` p95 ms, A / B | `tb_room_join` p95 ms, A / B | `tb_room_create` p95 ms, A / B | Postgres cores, A / B | Verdict, A / B |
|---|---|---|---|---|---|---|---|
| 1 | n/a | 124 / 130 | 6 / 6 | 9 / 8 | 7 / 7 | 0.13 / 0.13 | pass / pass |
| 2 | n/a | 306 / 304 | 5 / 5 | 7 / 7 | 7 / 6 | 0.35 / 0.32 | pass / pass |
| 4 | n/a | 609 / 613 | 6 / 6 | 9 / 8 | 8 / 8 | 0.73 / 0.75 | pass / pass |
| 8 | n/a | 1,090 / 1,074 | 9 / 10 | 10 / 11 | 10 / 10 | 1.38 / 1.32 | pass / pass |
| 16 | 955 | 1,438 / 1,489 | 19 / 17 | 21 / 20 | 19 / 18 | 1.84 / 1.90 | pass / pass |
| 32 | 1,055 | 1,638 / 1,618 | 39 / 40 | 46 / 46 | 41 / 43 | 2.11 / 2.05 | pass / pass |
| 64 | 1,017 | 1,779 / 1,711 | 75 / 78 | 106 / 108 | 93 / 97 | 2.16 / 2.14 | pass / pass |
| 128 | 998 | 1,762 / 1,733 | 150 / 153 | 231 / 232 | 201 / 210 | 2.15 / 2.20 | fail / fail |
| 256 | 637 | (step cut short) | 136 / 133 | 255 / 254 | 201 / 219 | 2.20 / 2.19 | fail / fail, not valid (finding 4) |

Per-run resource view (`snapshot.sh` segment means, run A / run B; segment N is step N):

| Segment | 4 (8 pairs) | 5 (16) | 6 (32) | 7 (64) | 8 (128) |
|---|---|---|---|---|---|
| Platform cores | 2.79 / 2.83 | 3.27 / 3.29 | 3.47 / 3.46 | 3.57 / 3.53 | 3.57 / 3.56 |
| Game Host cores | 1.07 / 0.95 | 1.22 / 1.23 | 1.27 / 1.27 | 1.25 / 1.24 | 1.24 / 1.26 |
| `hikari_active` max | 6 / 5 | 10 / 10 | 10 / 10 | 10 / 10 | 10 / 10 |
| `hikari_pending` max | 0 / 0 | 5 / 3 | 13 / 59 | 53 / 134 | 198 / 206 |

Generator check (`check-generator.sh`): every segment of both runs `-> ok`.

## 5. Result

Ceiling (pairs): 64
First to break: PostgreSQL
Evidence: the 128-pair step is the first to fail in both runs, on `tb_room_join` (231 and 232 ms p95 against 200) and `tb_room_create` (201 and 210 ms). At that step connections wait (`hikari_pending` mean 89 to 145, max 198 and 206) and Postgres runs at 2.15 and 2.20 cores, above the 1.9 of `load-testing.md` §8, so the rule names `PostgreSQL` and not `DB pool`. The platform is at 3.57 of 4 cores and the Game Host at 1.2 of 4; no restart, no 5xx, no generator-bound step. The moves target passes at 128 (150 and 153 ms p95), which M16 did not.


`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Per-run `snapshot.sh` tables are in `snapshot.out` of each run directory; the figures used here are in §4. After each run: platform, Game Host and frontend 0 restarts; no `OOMKilled`; the Postgres, Redis and observability pods show 5 to 6 restarts from before the session; no 5xx request (`http_5xx_per_s` has no samples). Redis `used_memory` 1.6 MiB after run A. Postgres statements by total time in run A: `update room set version` 0.17 ms mean (537k calls, 89 s), the two team-occupancy joins 0.04 to 0.06 ms (1.36 M calls each, 57 s and 85 s), `update game set completed_session_count` 0.54 ms (141k calls, 76 s), `insert into game_history_entry` 0.24 ms (283k calls, 68 s); no statement is slow, the volume is the load.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

1. **The ceiling stays 64 pairs; PostgreSQL is the limit.** The first threshold to fail is room creation and join at 128 pairs while Postgres is at its 2-core limit and requests queue behind the 10 connections. Peak 1,779 moves/s (A) against M16's 1,055, and 1,762 at 128 pairs against 998.
2. **`FR-DBQ-007` applied and was tried (run B).** The chart gained `postgres.settings`, rendered as `-c name=value` before `extraArgs` (so the load-test overlay's `extraArgs` do not replace them): `shared_buffers=256MB` (25% of the 1 GiB), `effective_cache_size=512MB`, `max_connections=50` (the pool is 10; the default of 100 reserves memory for connections nobody opens), `max_wal_size=2GB`, `checkpoint_completion_target=0.9`, `random_page_cost=1.1`. Confirmed in the pod with `pg_settings`. Result: no gain in this scenario: peak 1,711 against 1,779 (within noise), the 128-pair step 1,733 against 1,762, `tb_room_join` p95 232 against 231 ms, Postgres still 2.2 cores. The limit is CPU, which memory and connection settings do not add. The settings are kept (they match the pinned size and the ramp run gained, see the `ramp-to-break` report), but they are not what moves the ceiling.
3. **`NFR-DBQ-003` holds, `NFR-DBQ-001` fails** for this scenario (see `SUMMARY.md`, *M17*).
4. **The 256-pair step ended early in both runs, as in `2026-10-23-m17-pool-sizing.md` finding 3** (7,700 to 8,400 moves instead of about 100,000). The 256-pair row is not a measurement and is not used; the ceiling and the peak come from steps 1 to 128. The cause was not investigated.
5. **The pool-sizing report labels its first to break `DB pool`** although its own figures (`hikari_pending` above 0 and Postgres at 2.07 to 2.23 cores) satisfy the `PostgreSQL` rule of `load-testing.md` §8. The choice of 10 is unaffected (it follows `FR-DBQ-006`'s ceiling and peak rules); the label is corrected there.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
