# Connection-pool sizing report, `parallelism` at 5, 10 and 20 connections, 2026-10-23

**Verdict:** The ceiling is 64 pairs at every pool size, so the choice falls to peak moves/s: 1,452 at 5, 1,755 at 10 and 1,714 at 20; 20 is within 5% of 10, they tie, and the smallest tied pool, **10**, is confirmed as the default (`FR-DBQ-006`). Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `parallelism`, defaults (levels 1, 2, 4, 8, 16, 32, 64, 128, 256 pairs; 120 s steps, 20 s settle), once per candidate pool size, `reset.sh`, `install.sh` and `USERS=3000` provisioning between runs |
| Parameters (`params.txt`) | `scenario=parallelism`, `K6_CORES=4`, `USERS=3000`; the pool size is `platform.db.poolMaxSize` in both overlays (5, then 10, then 20), confirmed in the pod with `printenv SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE` before each run |
| Start (UTC) | pool 5 2026-10-23T18:43:10Z; pool 10 19:03:57Z; pool 20 19:24:01Z |
| End (UTC) | pool 5 18:59:50Z; pool 10 19:20:35Z; pool 20 19:40:40Z |
| Duration | about 16 min 40 s each, including a setup of about 14 s: the 256-pair step ended early (finding 3) |
| k6 exit code | 99 in all three (thresholds crossed at 128 and 256 pairs; the scenario does not abort on them) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261023-204305-parallelism` (pool 5), `20261023-210355-parallelism` (pool 10), `20261023-212401-parallelism` (pool 20); git-ignored |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`, as in the M16 reports) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 mean 110% to 163% of 400% on the pinned cores in the three runs; no step generator-bound (`check-generator.sh`, 9 of 9 segments ok in each) |
| Root commit | 6d78e012da63b3adda61aace0a7136c25e144e48 (overlay edits uncommitted while the runs ran; the report is committed after them) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | e52c1f4913060b47b34c1aae6823cec3fd76b505 (image `turnbase/platform:dev` rebuilt from it with `clean package`; includes the M17-01 to 03 changes) |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 (image unchanged since M16) |
| `turnbase-frontend` | 9b480fe73496f946902916f6ec3084b8d9b0d2bc |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | in each run's `cluster.txt` |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values are `values-local.yaml` plus `loadtest/helm/values-loadtest.yaml` as in `2026-10-21-m16-parallelism.md` §2, with one addition: `platform.db.poolMaxSize` (5, 10, 20). The full `helm get values` of each run is in its `cluster.txt`.

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when every row passes for that step. Observed values are those of the last step that passed (64 pairs) at pool 10, the chosen size.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 76 ms | 102 ms | pass up to 128 at pools 10 and 20 (167 / 220 ms and 151 / 196 ms); at pool 5 p95 202 ms at 128 fails |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 107 ms; `tb_room_create` 95 ms | see `steps.csv` | pass at 64 at every pool; `tb_room_join` fails at 128 at every pool (333, 260 and 214 ms p95 at pools 5, 10 and 20); `tb_login` happens in setup, not stepped |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 29 ms (32 pairs; step 64 in `steps.csv`) | n/a | pass at every step at every pool |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | below 350 ms at every step at pool 5 | n/a | pass at every step at every pool |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass: 0 errors (`tb_errors` 0) in 99,294, 112,356 and 113,959 games |
| Concurrent sessions | >= 500 | not attempted (`parallelism` peaks at 256 pairs) | n/a | not attempted here; `ramp-to-break` measures it |
| Concurrent WebSockets | >= 5,000 | not attempted | n/a | not attempted here; `ramp-to-break` measures it |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`. Candidates side by side (from `steps.csv`; `hikari` columns are the `snapshot.sh` maxima of the 120 s segment, offset by the setup time; Postgres cores are the mean of `kubectl top` samples per segment):

| Step (pairs) | Moves/s, pool 5 | Moves/s, pool 10 | Moves/s, pool 20 | `tb_move_rtt` p95 ms, 5 / 10 / 20 | `tb_room_join` p95 ms, 5 / 10 / 20 | Verdict, 5 / 10 / 20 |
|---|---|---|---|---|---|---|
| 1 | 133 | 121 | 119 | 6 / 6 / 6 | 8 / 9 / 9 | pass / pass / pass |
| 2 | 306 | 300 | 299 | 5 / 5 / 5 | 8 / 8 / 8 | pass / pass / pass |
| 4 | 593 | 597 | 589 | 6 / 6 / 6 | 9 / 9 / 9 | pass / pass / pass |
| 8 | 1,020 | 986 | 1,050 | 10 / 10 / 10 | 13 / 12 / 12 | pass / pass / pass |
| 16 | 1,253 | 1,401 | 1,486 | 21 / 19 / 18 | 29 / 21 / 20 | pass / pass / pass |
| 32 | 1,452 | 1,654 | 1,659 | 43 / 38 / 39 | 70 / 46 / 45 | pass / pass / pass |
| 64 | 1,428 | 1,755 | 1,714 | 95 / 76 / 80 | 169 / 107 / 98 | pass / pass / pass |
| 128 | 1,312 | 1,673 | 1,694 | 202 / 167 / 151 | 333 / 260 / 214 | fail / fail / fail |
| 256 | (step cut short) | (step cut short) | (step cut short) | 174 / 141 / 149 | 335 / 299 / 210 | fail / fail / fail, not valid (finding 3) |

Per-run resource view (segment means, `snapshot.sh`; the platform and Game Host columns are the means over the whole 120 s segment):

| Pool | Segment | 4 (8 pairs) | 5 (16) | 6 (32) | 7 (64) | 8 (128) |
|---|---|---|---|---|---|---|
| 5 | Platform cores | 2.85 | 3.29 | 3.42 | 3.46 | 3.39 |
| 10 | Platform cores | 2.79 | 3.26 | 3.51 | 3.56 | 3.56 |
| 20 | Platform cores | 2.85 | 3.21 | 3.37 | 3.36 | 3.35 |
| 5 | Game Host cores | 0.95 | 1.08 | 1.13 | 1.12 | 1.10 |
| 10 | Game Host cores | 0.91 | 1.16 | 1.24 | 1.24 | 1.24 |
| 20 | Game Host cores | 1.06 | 1.20 | 1.26 | 1.21 | 1.19 |
| 5 | Postgres cores | 1.32 | 1.73 | 1.82 | 1.91 | 1.80 |
| 10 | Postgres cores | 1.37 | 1.87 | 2.07 | 2.17 | 2.18 |
| 20 | Postgres cores | 1.37 | 1.91 | 2.10 | 2.19 | 2.23 |
| 5 | `hikari_active` max / `hikari_pending` max | 5 / 1 | 5 / 22 | 5 / 51 | 5 / 123 | 5 / 206 |
| 10 | `hikari_active` max / `hikari_pending` max | 6 / 0 | 9 / 0 | 10 / 23 | 10 / 86 | 10 / 179 |
| 20 | `hikari_active` max / `hikari_pending` max | 5 / 0 | 6 / 0 | 11 / 0 | 20 / 30 | 20 / 153 |

Generator check (`check-generator.sh`): every segment of every run `-> ok` (k6 mean at most 163% of 320%).

## 5. Result

Ceiling (pairs): 64
First to break: DB pool
Evidence: the ceiling is 64 pairs for each candidate (the last step meeting every threshold), so `FR-DBQ-006` goes to the second rule. Peak moves/s: 1,452 at 5 (32 pairs), 1,755 at 10 (64 pairs) and 1,714 at 20 (64 pairs). Pool 5 is 17% below the best and out. Pool 20 is 2.3% below pool 10, inside the 5% tie, and the smallest tied pool is **10**. Pool 5 queues from 8 pairs (`hikari_pending` 22 at 16, 206 at 128); pool 10 from 32 pairs (23, then 179 at 128); pool 20 from 64 pairs (30, then 153 at 128). Postgres sits at 1.8 of 2 cores at pool 5 and at 2.07 to 2.23 at pools 10 and 20, so a larger pool moves the saturation from the connections to the Postgres CPU without raising the peak. The first threshold to fail is `tb_room_join` at 128 pairs (and `tb_room_create`, `tb_move_rtt` at smaller pools); `tb_room_join` p95 at 128 is 333, 260 and 214 ms. The Game Host stays at about 1.1 to 1.3 of 4 cores, no restart, no 5xx, no generator-bound step.

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Per-run `snapshot.sh` tables are in `snapshot.out` of each run directory. The figures used here are in §4. After each run: platform, Game Host and frontend 0 restarts; no `OOMKilled`; the Postgres, Redis and observability pods show 5 to 6 restarts from before the session (the same counts in all three snapshots); no 5xx request (`http_5xx_per_s` has no samples in any run).

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

1. **The pool of 10 is confirmed.** Pool 5 loses 17% of the peak and queues three steps earlier. Pool 20 gains nothing (peak 2.3% below, `tb_room_join` p95 at 128 pairs 214 ms against 260 ms): the 2-core Postgres is the limit, and 20 connections only change where requests wait. `FR-DBQ-006` decides for 10; the default in `application.yml`, the chart and both overlays is 10. No fourth candidate: the best of the three is not the largest.
2. **Compared with the M16 parallelism run (pool 10, before M17-01 to 03):** peak 1,755 moves/s against 1,055 and 1,673 at 128 pairs against 998, `tb_move_rtt` p95 at 128 pairs 167 ms against 200 ms, `hikari_pending` maximum 179 against 207, Postgres 2.17 cores at 64 pairs against 2.08. The ceiling stays 64 pairs, now decided by `tb_room_join` and `tb_room_create` alone at pool 10 (the move target passes at 128). The platform now uses 3.5 of its 4 cores at 32 to 128 pairs (2.9 in M16), so the platform CPU is the next limit to be reached. Not checked: which of the three M17 changes carries the gain.
3. **The 256-pair step ended early in all three runs.** Each run ended about 985 s after the setup finished, 95 s before the 1,080 s of the nine steps; 256 pairs delivered 7,700 to 8,300 moves instead of about 100,000 (M16 report: complete, 17 min 41 s). The 256-pair row is therefore not a measurement and is not used for the choice; the ceiling and the peak come from steps 1 to 128. The cause was not investigated (k6.log shows no error besides the threshold line).
4. The k6 exit code 99 is the thresholds at 128 pairs (`tb_move_rtt` at pool 5 only), not an abort.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
