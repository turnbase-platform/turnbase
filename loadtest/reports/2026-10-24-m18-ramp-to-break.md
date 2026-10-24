# `ramp-to-break`, M18 single-instance re-verification, `IMP-M18-07`, 2026-10-24

**Verdict:** On the M18 build `ramp-to-break` reaches **220 pairs** (440 sockets, 165 sessions), the same ceiling as the M18 baseline, and aborts at 230 on `tb_room_create` (p95 200.0 ms) and `tb_room_join` (221 ms). Moves per second are 1 to 11% higher than the baseline's at 180 to 220 pairs (2,015 against 1,917 at 220) and move p95 is 99 ms against 131 ms at 220 pairs, but the join tail is the binding limit and it did not move. The first to break is **DB pool** (`hikari_pending` up to 168, Postgres at 2.0 of 4 cores); the platform is at 3.6 to 3.8 of 4. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `ramp-to-break` (start 10 pairs, +10 per step, 120 s steps, 20 s settle, abort on a failed threshold), once, after `reset.sh`, provisioning (3,000 users) and a warm-up of three `smoke.js` runs at `PAIRS=40` (see below) |
| Parameters (`params.txt`) | `scenario=ramp-to-break`, `K6_CORES=4`, `USERS=3000`, `MAX_PAIRS=1500` |
| Start (UTC) | 2026-10-24T20:38:22Z |
| End (UTC) | 2026-10-24T21:23:24Z (45 min 2 s) |
| k6 exit code | 99 (`tb_room_create{step:230}` and `tb_room_join{step:230}` crossed, `abortOnFail` stopped the test; a normal finish for this scenario) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261024-223819-ramp-to-break` (git-ignored) |

A first attempt (`20261024-223326-ramp-to-break`) aborted 21 s into step 10 on `tb_move_rtt{step:10}` (p95 671 ms over 11 samples): the platform and Game Host had just been restarted by `reset.sh`, so the first moves ran on cold JVMs. It is a harness artefact and not a result; it is not used. The run above was preceded by `reset.sh`, provisioning and three `smoke.js` runs (`PAIRS=40`, 0 errors) to warm the JVMs, which `reset.sh` clears again for no later run. The `parallelism` run did not need this: its first step has no abort.

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`, as in the M18 baseline) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 mean at most 248% of the 320% allowed on the pinned cores; no segment generator-bound (`check-generator.sh`: 23 of 23 `ok`) |
| Root commit | 06ffbe487fdd2f7345d232151dd33cc0a05f53d9 (the claim commit of `IMP-M18-07`; the report is committed after it) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | 9eb97384a10dd427e2086cf0d81ce263ebc699ec (`IMP-M18-05`; image `sha256:c93612fe48d9...`, built with `clean package`) |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 (image `sha256:15f70fd3ccc5...`, unchanged since M16) |
| `turnbase-frontend` | image `sha256:3663712f5b6e...`, unchanged since M17 |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values and cores as `2026-10-24-m18-parallelism.md` §2 (the Phase B overlay of the baseline: Platform 4 CPU, Game Host 2, PostgreSQL 4 / 2 GiB, Redis 1, pool of 10, the OpenTelemetry agent as specified).

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when every row passes for that step. Observed values are those of 220 pairs, the last passing step.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 99 ms | 141 ms | pass at every step (230: 76 / 97 ms, partial) |
| `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | create 170 ms, join 194 ms | 233 / 271 ms | pass up to 220; **fail at 230** (create 200.0 ms, join 221 ms in a partial step of 170 creates) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | pass | n/a | pass at every step (230: 108 / 143 ms) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s | pass | n/a | pass at every step (230: 262 / 347 ms) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass: `tb_errors` 0 in 647,446 games, 4,939,701 moves |
| Concurrent sessions | >= 500 | 165 at 220 pairs | n/a | **not reached** |
| Concurrent WebSockets | >= 5,000 | 435 at 220 pairs (444 at the abort) | n/a | **not reached; ceiling in sockets: 440** |

## 4. Steps

Moves per second is `count(tb_move_rtt) / 100`, from `steps.csv`. Steps 10 to 90 passed with p95 at most 77 ms for every metric (`steps.csv`).

### `ramp-to-break`: M18 baseline vs M18

| Step (pairs) | Moves/s, baseline / M18 | `tb_move_rtt` p95 ms, baseline / M18 | `tb_room_join` p95 ms, baseline / M18 | `tb_room_create` p95 ms, baseline / M18 | Verdict, baseline / M18 |
|---|---|---|---|---|---|
| 100 | n/a / 2,058 | 68 / 46 | 74 / 63 | 69 / 59 | pass / pass |
| 150 | 1,673 / 1,859 | 104 / 79 | 116 / 108 | 110 / 101 | pass / pass |
| 160 | 1,684 / 1,948 | 112 / 79 | 125 / 119 | 115 / 110 | pass / pass |
| 170 | 1,724 / 1,973 | 116 / 78 | 134 / 132 | 124 / 125 | pass / pass |
| 180 | 1,916 / 2,039 | 108 / 79 | 136 / 154 | 125 / 139 | pass / pass |
| 190 | 1,917 / 2,025 | 112 / 83 | 149 / 161 | 133 / 147 | pass / pass |
| 200 | 1,747 / 1,934 | 132 / 95 | 159 / 163 | 145 / 146 | pass / pass |
| 210 | 1,836 / 1,862 | 132 / 110 | 174 / 173 | 156 / 157 | pass / pass |
| 220 | 1,917 / 2,015 | 131 / 99 | 171 / 194 | 154 / 170 | pass / pass |
| 230 | n/a (partial) / n/a (partial) | 176 / 76 | 218 / 221 | 176 / 200 | fail / fail |

Segment means at the last steps (`snapshot.sh` segments 20 to 23, that is 200, 210, 220 and 230 pairs; Postgres from `pods.csv`):

| Metric | 200 pairs | 210 pairs | 220 pairs | 230 pairs (failing) |
|---|---|---|---|---|
| Platform cores (of 4) | 3.74 | 3.58 | 3.59 | 3.81 |
| Game Host cores (of 2) | 1.36 | 1.30 | 1.29 | 1.36 |
| Postgres cores (of 4, `kubectl top` mean) | 1.99 | 1.93 | 1.99 | n/a (partial step) |
| `hikari_active` / `hikari_pending` max | 10 / 168 | 10 / 79 | 10 / 106 | 9 / 9 |
| `http_p99_seconds` mean | 0.130 | 0.126 | 0.137 | 0.160 |
| Sockets / sessions (max) | 395 / 135 | 413 / 158 | 435 / 165 | 444 / 113 |

Generator check: 23 of 23 segments `ok` (k6 mean 248% of 320% at most).

## 5. Result

Ceiling (pairs): 220
First to break: DB pool
Evidence: the only metrics that crossed are `tb_room_create` (p95 200.0 ms) and `tb_room_join` (221 ms) at 230 pairs, while moves, lobby events and game starts stay inside their targets. In the steps before it connections wait (`hikari_pending` max 79 to 168 at 200 to 220 pairs, `hikari_active` at the pool's 10) with Postgres at 1.9 to 2.0 of 4 cores (about 50%), below the 95% (3.8) of the `load-testing.md` §8 rule, so the rule names `DB pool`, not `PostgreSQL`. The platform is at 3.6 to 3.8 of 4 cores, the next limit. The 230-pair step is a partial step (170 creates) in which the first samples after the settle window already exceed the target; it is the same abort point as the baseline's. No generator-bound segment, no 5xx.

Capacity statements:

- 500 concurrent sessions: **not reached.** Ceiling 220 pairs; `sessions_active` max 165.
- 5,000 WebSockets: **not reached; ceiling in sockets: 440** (2 x 220; 444 open at the abort). The ceiling is below 1,000 pairs, so the idle-socket run was not made.

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Pod restarts and `OOMKilled` (from `cluster.txt`): platform, Game Host, Postgres and frontend 0 restarts; Redis and the observability pods show 7 restarts from before the session; no `OOMKilled`; no 5xx. Redis `used_memory` 2.07 MiB. Platform threads flat at 293 to 294 from 200 pairs on (not a limit: nothing queues on them), Game Host threads 197 to 254. The run played 647,446 games in 45 minutes (240 games/s), against 593,143 (220 games/s) for the baseline.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

1. **The ceiling did not move: 220 pairs, as the baseline.** Moves per second at 200 to 220 pairs are 1 to 11% higher (1,862 to 2,015 against 1,747 to 1,917) and move p95 is 17 to 28% lower, so the platform does more work per pair. Create and join, which fail the ramp, are not faster: join p95 at 220 pairs is 194 ms (baseline 171), create 170 ms (154). The pairs play 9% more games per second, so each issues more creates and joins per second at the same pair count; the pool of 10 and the platform CPU (3.6 to 3.8 of 4) are the same two limits as in the baseline.
2. **Postgres is no longer in question for this scenario.** It runs at 1.9 to 2.0 of 4 cores at the ceiling (baseline 2.3 to 2.4) with the pool queueing: the cores `IMP-M18-02` gave it are not what limits the ramp, as the baseline found. `NFR-DBQ-001` for this scenario: `DB pool`, fail.
3. **A cold platform fails the first step.** A `reset.sh` followed at once by the ramp aborted at step 10 on 11 samples of `tb_move_rtt` (p95 671 ms). The M17 and baseline ramps ran after a `parallelism` run, which warms the JVMs. A later run item that resets before a ramp should warm up first (a `smoke.js` at `PAIRS=40`, three times, as here).
4. **Capacity targets** (500 sessions, 5,000 WebSockets) remain unreached on one node: 165 sessions and 444 sockets at the abort.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
