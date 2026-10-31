# FILL: scenario report, FILL: date

**Verdict:** FILL (one line: what the run showed)

**Phase:** FILL (`A`: one Platform and one Game Host, as in `load-testing.md`; `B`: autoscaling on, `load-testing-phase-b.md`. A `B` report also fills sections 10 to 12, which `check-report.sh` then requires; an `A` report deletes them)

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
`Game Host CPU`, `Espresso contention`, `DB pool`, `PostgreSQL`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. `PostgreSQL` when `hikari_pending` > 0 with PostgreSQL at or
above 1.9 of 2 cores at the failing step, `DB pool` when it is below (`load-testing.md` §8). A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

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

## 10. Scaling timeline (Phase B)

`timeline.csv` of the run directory (`timeline.sh`, every 5 s): Deployment, HPA and KEDA desired and ready replicas,
pod start and termination, and the `mark` rows of the `failover` kills. Replica counts as a table of events, one row per
change (a long run is summarised and the file is cited):

| Time (UTC) | Offset from scenario start | Event | Platform ready/desired | Game Host ready/desired |
|---|---|---|---|---|
| FILL | FILL | FILL (a scale-out, a scale-in, a pod Ready, a pod Terminating, a kill) | FILL | FILL |

Scale events: FILL (count; for `sustained-high`, how many after the first 10 minutes). Flapping (a scale-out followed by a
scale-in of the same workload within the stabilisation window): FILL.

## 11. Correctness (Phase B)

Output of `correctness.sh` (`correctness.txt` of the run directory), verbatim:

```
FILL
```

`tb_rest_retries` (a 503 `ROOM_UNAVAILABLE_RETRY` answered to a join on an instance that does not own the room, retried by the
harness after `REST_RETRY_MS`): FILL.

## 12. NFR-ASC (Phase B)

One row per requirement that this scenario judges (`load-testing-phase-b.md` §7); `n/a` for the others.

| ID | Target | Observed | Pass |
|---|---|---|---|
| NFR-ASC-001 scale-out reaction | <= 3 min, Platform and Game Host | FILL | FILL |
| NFR-ASC-002 correctness through scaling | no lost, duplicated or reordered input, error rate < 1% | FILL | FILL |
| NFR-ASC-003 scale-in | back to minimum, resources within 10% of the pre-run level, <= 10 min | FILL | FILL |
| NFR-ASC-004 spike recovery | thresholds recover <= 3 min | FILL | FILL |
| NFR-ASC-005 sustained high load | p99 drift < 25%, <= 1 scale event per 10 min after the first 10 | FILL | FILL |
| NFR-ASC-006 scaled ceiling | >= the single-instance ceiling | FILL | FILL |
| NFR-ASC-007 failover | games continue, players back in their room <= 30 s | FILL | FILL |
