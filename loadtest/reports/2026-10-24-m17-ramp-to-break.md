# `ramp-to-break`, M17 re-verification, 2026-10-24

**Verdict:** Ceiling **170 pairs** (340 sockets, 141 concurrent sessions at most) on the chart as it was, and **190 pairs** (380 sockets, 150 sessions) with the `IMP-M17-05` PostgreSQL settings; each run aborted at the next step on a `tb_room_join` p95 just over 200 ms (201 and 206 ms) while 0 operations failed. M16 stopped at 80 pairs. The first to break is **PostgreSQL** (2.0 to 2.2 of 2 cores, `hikari_pending` 155 to 206). Neither the 500-session nor the 5,000-WebSocket target was reached. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `ramp-to-break`, defaults (start 10 pairs, +10 per step, 120 s steps, 20 s settle, abort on a failed threshold), `MAX_PAIRS=1500`, `USERS=3000`, twice: run A on the chart as it was, run B after `FR-DBQ-007` |
| Parameters (`params.txt`) | `scenario=ramp-to-break`, `K6_CORES=4`, `USERS=3000`, `MAX_PAIRS=1500` |
| Start (UTC) | A 2026-10-23T20:05:09Z; B 21:35:57Z |
| End (UTC) | A 20:40:28Z (35 min 19 s); B 22:15:13Z (39 min 16 s) |
| Duration | A 35 min 19 s; B 39 min 16 s (setup about 35 s each, then the load) |
| k6 exit code | 99 in both (`tb_room_join` crossed at 180 pairs in A and 200 in B, `abortOnFail` stopped the test; a normal finish for this scenario) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261023-220506-ramp-to-break` (A), `20261023-233555-ramp-to-break` (B); git-ignored |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`, as in the M16 reports) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 mean at most 196% of the 320% allowed in any segment of either run; no step generator-bound (`check-generator.sh`, 0 flagged) |
| Root commit | a8fc67e76ea77dc56ff674f94a3477d30776c97f (the claim commit of `IMP-M17-05`; the report is committed after it) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | e52c1f4913060b47b34c1aae6823cec3fd76b505 plus the `postgres.settings` chart change of this item (`0b6f015`, committed after the runs; the image is the same) |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 (image unchanged since M16) |
| `turnbase-frontend` | 9b480fe73496f946902916f6ec3084b8d9b0d2bc |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | platform `sha256:56c732e00523...`, game-host `sha256:15f70fd3ccc5...`, frontend `sha256:3663712f5b6e...` (full IDs and the full `helm get values` in each run's `cluster.txt`) |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values are `values-local.yaml` plus `loadtest/helm/values-loadtest.yaml` as in `2026-10-21-m16-parallelism.md` §2, with the `IMP-M17-04` default `platform.db.poolMaxSize: 10`. Run B has the `postgres.settings` block (see `2026-10-24-m17-parallelism.md` §8 finding 2).

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when every row passes for that step. Observed values are those of the last step that passed: 170 pairs in run A, 190 in run B.

| Metric | Target | Observed p95 (A / B) | Observed p99 (A / B) | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 118 / 124 ms | 156 / 166 ms | pass at every step |
| `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | join 188 / 200 ms; create 164 / 176 ms | join 235 ms (A) | pass up to 170 (A) and 190 (B); `tb_room_join` fails at 180 (A: 201.1 ms over 1,092 joins) and 200 (B: 205.5 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 87 / 90 ms | n/a | pass |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s | 203 / 221 ms | n/a | pass |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass: `tb_errors` 0 in 453,456 (A) and 473,636 (B) games |
| Concurrent sessions | >= 500 | 141 (A), 150 (B) | n/a | **not reached** |
| Concurrent WebSockets | >= 5,000 | 390 (A), 397 (B) | n/a | **not reached; ceiling in sockets 340 (A), 380 (B)** |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`; `steps.csv` of each run. M16 ran to 80 pairs.

| Step (pairs) | Moves/s, A / B | `tb_move_rtt` p95 ms, A / B | `tb_room_join` p95 ms, A / B | `tb_room_create` p95 ms, A / B | Verdict, A / B |
|---|---|---|---|---|---|
| 150 | 1,701 / 1,580 | 105 / 98 | 160 / 152 | 142 / 134 | pass / pass |
| 160 | 1,766 / 1,577 | 110 / 104 | 170 / 170 | 146 / 147 | pass / pass |
| 170 | 1,758 / 1,591 | 118 / 110 | 188 / 178 | 164 / 155 | pass / pass |
| 180 | 408 (partial) / 1,576 | 118 / 119 | 201 / 194 | 168 / 165 | fail / pass |
| 190 | not run / 1,592 | n/a / 124 | n/a / 200 (199.8) | n/a / 176 | n/a / pass |
| 200 | not run / 274 (partial) | n/a / 131 | n/a / 206 | n/a / 189 | n/a / fail |

Steps 10 to 140 passed in both runs (`steps.csv`). Segment means at the last full steps (`snapshot.sh`, run B; run A within 3%):

| Metric | Run A, 160 to 170 pairs | Run B, 170 to 190 pairs |
|---|---|---|
| Platform cores | 3.53 | 3.64 to 3.66 |
| Game Host cores | 1.14 to 1.15 | 1.18 to 1.20 |
| Postgres cores (`kubectl top` mean) | 2.15 to 2.22 | 1.98 to 2.02 |
| `hikari_active` / `hikari_pending` max | 10 / up to 189 | 10 / up to 206 |
| `http_p99_seconds` mean | 0.145 to 0.156 | 0.143 to 0.173 |

Generator check: 0 of 18 (A) and 20 (B) segments flagged.

## 5. Result

Ceiling (pairs): 190
First to break: PostgreSQL
Evidence: the only metric that crossed is `tb_room_join`, and it grows steadily with the pair count (p95 95 ms at 100 pairs, 143 at 140, 188 at 170 in run A) while moves, lobby events and game starts stay far inside their targets. From about 120 pairs the 10-connection pool is fully busy and requests queue (`hikari_pending` 155 to 206 at the last steps) while Postgres sits at its 2-core limit (2.1 to 2.2 cores in A, 2.0 in B), above the 1.9 of `load-testing.md` §8, so the rule names `PostgreSQL`. The platform is at 3.5 to 3.7 of 4 cores, the Game Host at 1.2 of 4, Redis flat; no restart, no 5xx. The ceiling reported is run B's (the chart as it now ships); run A's is 170.

Capacity statements:

- 500 concurrent sessions: **not reached.** Ceiling 190 pairs = 190 sessions at most (`sessions_active` max 150 in B, 141 in A); limiting factor `tb_room_join` latency behind Postgres.
- 5,000 WebSockets: **not reached; ceiling in sockets: 380** (2 x 190; 397 open at the abort). The ceiling is below 1,000 pairs, so the idle-socket run was not made (protocol, `IMP-M15-11` step 3).

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Pod restarts and `OOMKilled` (from each run's `cluster.txt`): platform, Game Host and frontend 0 restarts; Postgres, Redis and the observability pods show 5 to 6 restarts from before the session; no `OOMKilled`; no 5xx (`http_5xx_per_s` has no samples). Redis `used_memory` 1.6 to 1.9 MiB. Full per-segment tables are in `snapshot.out` of each run directory.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

1. **M16 vs M17.** Ceiling 80 pairs (M16) to 170 (A) and 190 (B); the sockets at the ceiling 160 to 340 and 380; `tb_room_join` p95 at 80 pairs 181 ms in M16 against 73 ms here (A, step 80, `steps.csv`). Postgres is still the limit, now with a much higher load behind it: the `IMP-M17-01` to `03` changes removed the full-table scans, so the same 2 cores serve more than twice the pairs. `NFR-DBQ-003` holds (ceiling at least 80); `NFR-DBQ-001` does not (first to break is `PostgreSQL`).
2. **`FR-DBQ-007` applied, and the settings gave a modest gain here:** ceiling 190 against 170 and Postgres at 2.0 cores against 2.15 to 2.2 for the same hikari queue, so the same CPU does somewhat more work per step. Moves per second at the common steps are lower in B (1,577 to 1,592 against 1,701 to 1,766), so the step ordering is not a clean win: the pair count at the abort moved by one step (10 pairs, 6%), which is the resolution of the scenario, and one run each does not separate that from noise.
3. **Capacity targets** (500 sessions, 5,000 WebSockets) remain unreached; the limit is Postgres CPU on a 2-core pin, a Phase B subject (a larger Postgres, read offload, fewer statements per join).

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
