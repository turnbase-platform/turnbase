# `sustained-high`, Phase B, `IMP-M18-17`, 2026-10-31

**Verdict:** 119 pairs (70% of the 170-pair scaled ceiling) held for 60 minutes: **NFR-ASC-005 met**. No scale event after the first minute (0 in the 50 minutes after the first 10), no flapping, the k6 p99 of every HTTP operation fell over the hold (room create 106 to 88 ms) while the server-side HTTP p99 stayed on its 0.223 s bucket edge, 770,040 games with 0 abandoned, 0 gaps, 0 duplicates, 15 errors in 9.26 million operations, `CORRECTNESS: PASS`, no pod restarts. One thing moved late: Platform threads went from 129 to 172 at +3,580 s, as the load began to fall, with no scale event. Single-node, laptop result.

**Phase:** B

## 1. Run

| Field | Value |
|---|---|
| Scenario | `sustained-high`, once, after `reset.sh`, provisioning (3,000 users), two `smoke.js` runs at `PAIRS=10` and a wait for 2 Platform replicas and no Terminating pod |
| Parameters (`params.txt`) | `K6_CORES=3`, `USERS=3000`, `CEILING=170`; defaults `FRACTION=0.7` (119 pairs), `RAMP_MINUTES=5`, `HOLD_MINUTES=60`, `DOWN_MINUTES=2` |
| Start (UTC) | 2026-10-31T19:39:58Z (VUs from 19:40:14Z) |
| End (UTC) | 2026-10-31T20:42:41Z |
| Duration | 62 min 27 s of wall clock; 67 min 16 s of VU time (`clock.start` / `clock.end`: 4,036.4 s of uptime for 3,760.2 s of wall, so the wall clock ran 6.8% slow) |
| k6 exit code | 0 |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 3 of 16 (`taskset`, `K6_CORES=3`) |
| Run directory | `loadtest/results/20261031-203958-sustained-high` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 (resources not halved) |
| Docker Desktop VM memory | 15.21 GiB (`docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | k6 at most 185% of the 240% allowed on the 3 pinned cores (§4) |
| Root commit | 30f5450 (the report is committed after it) |
| Component commits | as `2026-10-31-m18-spike.md` §2 (no rebuild since) |
| Image IDs | as `2026-10-31-m18-scaled-ramp-to-break.md` §2 (the same install, no rebuild between the runs) |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values and pod resources are those of `2026-10-31-m18-scaled-ramp-to-break.md` §2: Platform 2 to 3 replicas of 1.5 CPU (HPA CPU target 40%), Game Host 2 to 3 replicas of 1.5 CPU (KEDA, sessions utilisation 0.7), Postgres 4 CPU, Redis 1 CPU.

| Component | CPU | Memory |
|---|---|---|
| Platform | 1.5 per replica | 1.5 GiB |
| Game Host | 1.5 per replica | 2 GiB |
| Postgres | 4 | 2 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

The scenario has no aborting thresholds. The `hold` step has sub-metrics (`steps.csv`); the whole-run values are from `summary.json`.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` (hold) | p95 < 200 ms, p99 < 500 ms | 61 ms | 88 ms | yes |
| `tb_room_create`, `tb_room_join` (hold) | p95 < 200 ms, p99 < 500 ms | create 59.0 ms, join 62.0 ms | 87.7 ms, 92.3 ms | yes |
| `tb_lobby_event` (hold) | p95 < 300 ms, p99 < 600 ms | 55 ms | 80 ms | yes |
| `tb_game_start` (warm, hold) | p95 < 1 s, p99 < 2 s | 84 ms | 115 ms | yes |
| Error rate (`tb_op_failed`) | < 1% | 0.00016% (15 of 9.26 million) | n/a | yes |
| Concurrent sessions | >= 500 | not reached (81 peak; limiting factor: the load, 70% of 170 pairs) | n/a | no |
| Concurrent WebSockets | >= 5,000 | not reached (78 peak on the Platform gauges) | n/a | no |

## 4. Steps

| Step | Moves/s | `tb_move_rtt` p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| hold (119 pairs, 60 min) | about 1,640 | 61 / 88 | 84 / 115 | n/a | 15 `tb_errors` | 1.77 at most | 1.77 at most | no | pass |

`ramp` and `down` have no sub-metrics. CPU of the busiest pod per 600 s wall segment (means): Game Host 1.35, 1.03, 1.08, 1.19, 1.24, 1.23, 1.18 and Platform 1.30, 1.57, 1.59, 1.60, 1.61, 1.61, 1.57; the Platform pods sit near their 1.5-CPU request for the whole hold. Generator-bound: none (`check-generator.sh`: k6 at 150, 185, 182, 181, 182, 183, 134% of 240%). Throughput 205 games/s over the run (770,040 started), 5.49 million moves in the hold.

## 5. Result

Ceiling (pairs): 119
First to break: none
Evidence: nothing crossed a threshold. The ceiling line repeats the hold of 119 pairs (70% of the scaled `ramp-to-break` ceiling of 170), not a new measurement.

## 6. Server side

Output of `snapshot.sh` (`snapshot.txt` of the run directory; means by 600 s wall segment; segment 1 holds the ramp):

| Metric (mean) | seg 1 | seg 2 | seg 3 | seg 4 | seg 5 | seg 6 | seg 7 |
|---|---|---|---|---|---|---|---|
| Game Host CPU (busiest pod) | 1.35 | 1.03 | 1.08 | 1.19 | 1.24 | 1.23 | 1.18 |
| Platform CPU (busiest pod) | 1.30 | 1.57 | 1.59 | 1.60 | 1.61 | 1.61 | 1.57 |
| Game Host heap (bytes, MB) | 289 | 360 | 279 | 275 | 258 | 287 | 271 |
| Platform heap (MB) | 183 | 243 | 305 | 346 | 378 | 408 | 199 |
| Game Host threads | 113 | 126 | 133 | 132 | 132 | 134 | 127 |
| Platform threads | 110 | 128 | 129 | 129 | 129 | 131 | 172 |
| `hikari_pending` | 0 | 0.05 | 0 | 0 | 0 | 0 | 0 |
| `ws_connections` (sum) | 39 | 51 | 52 | 49 | 49 | 51 | 30 |
| `rooms_active` | 134 | 185 | 194 | 202 | 200 | 195 | 179 |
| `sessions_active` | 43 | 57 | 58 | 56 | 55 | 56 | 49 |
| `http_5xx_per_s` | 19.5 | 28.5 | 28.5 | 29.1 | 29.2 | 29.1 | 28.4 |
| `http_req_per_s` | 79 | 114 | 114 | 117 | 118 | 118 | 112 |

HTTP p95 / p99 read 0.22 s from the second segment on: the histogram bucket edge, flat, so the server-side series cannot show drift below 0.22 s. The drift is therefore read from k6's own p99 (§8). The `http_5xx_per_s` series is the `503 room-unavailable-retry` of joins on a Platform pod that does not own the room (307,278 retries by the harness, 82 per second). Platform heap grows 243 to 408 MB across the hold and the GC time per second is flat (0.011), then falls to 199 MB in segment 7; the heap is below the 1.5 GiB pod limit throughout.

| | At start | At end |
|---|---|---|
| Redis `DBSIZE` / `used_memory` (`redis.csv`) | 10 / 1.17 MB | 107 / 2.01 MB (last sample, the load had gone; the peak sample was 305 keys) |

Pod restarts and `OOMKilled`: none among the Platform, Game Host and frontend pods (the observability pods carry old restarts from before the run).

Missing metrics: none.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| other `tb_errors` | no | 15 (the code is not exported with the counter) |
| `tb_games_abandoned` | no | 0 |

## 8. Findings

- **NFR-ASC-005 holds on both parts.** (1) Scale events after the first 10 minutes: none. The only change in either workload was the Platform's HPA decision 2 to 3 (setup login burst, before the first VU), Ready at +42 s; the Platform stayed at 3 and the Game Host at 2 until the end (no Game Host scale-out: at most 81 sessions on 2 hosts, under the KEDA target of 0.7 per host). (2) p99 drift over the hold: k6's p99 per minute, averaged over 6 minutes (`k6_tb_*_p99{step="hold"}`), `tb_room_create` 106, 93, 92, 91, 90, 89, 89, 88, 88, 88 ms, `tb_room_join` 111 to 92, `tb_move_rtt` 127 to 88, `tb_game_start` 142 to 115, `tb_lobby_event` 106 to 80: the first window is the post-ramp warm-up and every operation is lower at the end. Last window against first: -17% (create), -17% (join), -31% (move). Last window against the second (from minute 6): -5% (create), -5% (join), -16% (move). The server-side HTTP p99 is a flat 0.223 s bucket edge (0%). The k6 percentiles come from a remote-write series (the p99 k6 reports for its current window, not the summary's whole-step value); drift is negative either way, so the < 25% bar holds with any reading.
- **Compared with the single-instance `soak`** (`2026-10-24-m18-soak.md`, 56 pairs, 30 min, p99 +21.8% first against last five minutes): the scaled deployment held twice the load for twice as long with no upward drift.
- **Platform threads 129 to 172 at +3,580 s wall**, about 50 seconds before the ramp down began (the `down` step starts at +3,630 s wall after the 6.8% slew). The jump is one sampled pod (the Prometheus series is per service), no scale event, no restart and no error follows; Platform heap and GC rise with it (GC 0.011 to 0.016 s/s; heap max 488 MB, then 256 MB). Not isolated: a thread dump was not taken, and the jump may be a pool growing under a burst in the last minutes of the hold. It does not affect the NFR-ASC-005 verdict (`up-down` showed threads back below the pre-run level after the load).
- **Platform CPU rises to its 1.5 CPU request** (1.57 to 1.61 cores busiest pod in every segment) at 119 pairs while the HPA target is 40% of the request: the HPA stays at its 3 maximum, so the Platform has no headroom to scale at this load; the Game Host is at 1.0 to 1.2 cores of 1.5 on 2 hosts.
- **Slew:** the wall clock ran 6.8% slow.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.

## 10. Scaling timeline (Phase B)

`timeline.csv` of the run directory (`timeline.sh`, every 5 s). Offsets are wall seconds from `scenario.epoch` (19:40:14Z).

| Time (UTC) | Offset from scenario start | Event | Platform ready/desired | Game Host ready/desired |
|---|---|---|---|---|
| 19:40:01 | -13 s | HPA Platform desired 3, seen at the first sample (setup login burst, before the first VU) | 2/3 | 2/2 |
| 19:40:40 | +26 s | third Platform pod Running (Deployment desired 3) | 3/3 | 2/2 |
| 19:40:56 | +42 s | third Platform pod Ready | 3/3 | 2/2 |

The decision predates the first sample, so the reaction is at most 55 s (first sample to Ready). Scale events: 1, none after the first minute. Flapping: none.

## 11. Correctness (Phase B)

Output of `correctness.sh` (`correctness.txt` of the run directory), verbatim:

```
games: started 770040 = completed 770040 + abandoned 0
sequence: gaps 0, duplicates 0, over 11745282 broadcast GAME_EVENTs checked
rooms: none IN_PROGRESS, none with an active session
CORRECTNESS: PASS
```

`tb_rest_retries` (a 503 `ROOM_UNAVAILABLE_RETRY` answered to a join on an instance that does not own the room, retried by the harness after `REST_RETRY_MS`): 307,278 over the run (82 per second).

## 12. NFR-ASC (Phase B)

| ID | Target | Observed | Pass |
|---|---|---|---|
| NFR-ASC-001 scale-out reaction | <= 3 min, Platform and Game Host | Platform Ready at most 55 s after the HPA's decision (setup burst); Game Host did not scale | yes (Platform) |
| NFR-ASC-002 correctness through scaling | no lost, duplicated or reordered input, error rate < 1% | `CORRECTNESS: PASS`; 0 gaps, 0 duplicates, 0 abandoned; error rate 0.00016% | yes |
| NFR-ASC-003 scale-in | back to minimum, resources within 10% of the pre-run level, <= 10 min | n/a (`up-down`) | n/a |
| NFR-ASC-004 spike recovery | thresholds recover <= 3 min | n/a (`spike`) | n/a |
| NFR-ASC-005 sustained high load | p99 drift < 25%, <= 1 scale event per 10 min after the first 10 | drift -17% to -31% (k6 p99, last against first window), 0 scale events after the first 10 minutes | **yes** |
| NFR-ASC-006 scaled ceiling | >= the single-instance ceiling | n/a (`ramp-to-break`) | n/a |
| NFR-ASC-007 failover | games continue, players back in their room <= 30 s | n/a (`failover`) | n/a |
