# FILL: scenario report, FILL: date

**Verdict:** FILL (one line: what the run showed)

## 1. Run

| Field | Value |
|---|---|
| Scenario | FILL |
| Parameters (`params.txt`) | FILL |
| Start (UTC) | FILL |
| End (UTC) | FILL |
| Duration | FILL |
| k6 exit code | FILL (`99` = a threshold crossed, a normal finished run) |
| k6 version | FILL |
| k6 pinned to CPUs | FILL |
| Run directory | FILL |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | FILL |
| Docker Desktop VM memory | FILL (from `docker info`) |
| `.wslconfig` | FILL (content, or "absent (VM defaults)") |
| Host load during the run | FILL (`samples.csv`: mean and max of `load1` and `vm_cpu_pct`) |
| Root commit | FILL |
| `turnbase-common` | FILL |
| `turnbase-sdk` | FILL |
| `turnbase-platform` | FILL |
| `turnbase-game-host` | FILL |
| `turnbase-frontend` | FILL |
| `turnbase-game-tictactoe` | FILL |
| Image IDs | FILL |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values (`helm get values turnbase`):

```yaml
FILL
```

Pod resources (requests equal limits; halved if the VM has fewer than 12 CPUs, say so here: FILL):

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when
every row passes for that step. Observed values are those of the last step that passed, or of the whole run
for a scenario without steps.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | FILL | FILL | FILL |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | FILL | FILL | FILL |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | FILL | FILL | FILL |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | FILL | FILL | FILL |
| Error rate (`tb_op_failed`) | < 1% | FILL | n/a | FILL |
| Concurrent sessions | >= 500 | FILL (`reached` / `not reached` / `not attempted`; limiting factor: FILL) | n/a | FILL |
| Concurrent WebSockets | >= 5,000 | FILL (`reached` / `not reached` / `not attempted`; limiting factor: FILL) | n/a | FILL |

## 4. Steps

`steps.csv` (`segment,metric,count,p95,p99,rate,pass`), one row per step. Moves per second is
`count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)`. Generator-bound comes from `check-generator.sh`.

| Step | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| FILL | FILL | FILL | FILL | FILL | FILL | FILL | FILL | FILL (`yes` / `no`) | FILL (`pass` / `fail`) |

## 5. Result

Ceiling (pairs): FILL
First to break: FILL
Evidence: FILL

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Output of `snapshot.sh` (mean / max per segment): Game Host and platform CPU, heap, threads, GC, Hikari,
HTTP p95 and p99, 5xx rate, active WebSockets, rooms and sessions.

FILL

| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | FILL | FILL |
| Redis `connected_clients` | FILL | FILL |

Pod restarts and `OOMKilled` (from `cluster.txt`): FILL

Missing metrics: FILL

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| FILL | FILL | FILL |

## 8. Findings

- FILL (each bullet carries numbers and the suspected cause; "none" is a valid fill)

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
