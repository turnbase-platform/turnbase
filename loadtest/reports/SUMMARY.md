# Phase A summary, 2026-10-19

Phase A of load and scalability testing ([`load-testing.md`](../../docs/specs/deployment/load-testing.md)) ran six scenarios
against the Helm install on one Docker Desktop Kubernetes node (16 CPUs, 15.2 GiB), with the load generator on the same VM.
Every figure below is a single-node, laptop ceiling: the ceiling of this machine, not of the platform. Closed-loop clients with no or little think time
saturate the platform far sooner than human players would, and coordinated omission makes the latencies optimistic. Nothing was fixed; the findings are in
[`load-testing.md` §13](../../docs/specs/deployment/load-testing.md#13-follow-ups).

## Reports

| Scenario | Report | Result in one line |
|---|---|---|
| `parallelism` | [2026-10-18-parallelism.md](2026-10-18-parallelism.md) | Moves/s 759 at 8 pairs, 909 at 32, 678 at 256; ceiling 64 pairs; the Game Host never above 1.5 of 4 cores |
| `ramp-to-break` | [2026-10-18-ramp-to-break.md](2026-10-18-ramp-to-break.md) | Ceiling 70 pairs (140 sockets, about 55 sessions); aborted on a `tb_room_join` tail at 80 pairs |
| `start-rate` | [2026-10-18-start-rate.md](2026-10-18-start-rate.md) | 1 to 32 games/s, warm `game_start` p95 11 to 16 ms; clean ceiling 16 games/s, degradation rate not reached |
| `default-limits` | [2026-10-18-default-limits.md](2026-10-18-default-limits.md) | 320 `RATE_LIMIT_EXCEEDED` from the WebSocket action bucket, 0 unexpected errors, 0 5xx |
| `contexts` | [2026-10-18-contexts.md](2026-10-18-contexts.md) | Four contexts: 810 moves/s as with one, about three times the Game Host CPU; attempt 1 wedged |
| `soak` | [2026-10-18-soak.md](2026-10-18-soak.md) | 49 pairs for 30 minutes: all targets met, but Redis, threads, heap and latency drifted and rooms went stale |
| `up-down` | [2026-10-19-up-down.md](2026-10-19-up-down.md) | Sockets, rooms, sessions released in 30 s; platform threads and Redis keys were not; attempt 1 wedged |

## The owner's three questions

**(a) What is the worst-case load?** The ramp stopped at 80 pairs, so the ceiling is 70 pairs: 140 WebSockets and about 55 concurrent sessions, the last step with every target met.
`parallelism` gives 64 pairs. Throughput peaked at 909 moves/s at 32 pairs. The first thing to break was the `tb_room_join` tail (p95 311 ms against 200 ms) with
the platform pod at about 3 of its 4 cores and Postgres at 1.85 of its 2; move, lobby and game-start latencies were still far inside their targets (move p95 81 ms).
`start-rate` found no breaking rate up to 32 games/s.

**(b) How does it behave as load rises and falls?** Moves per second scale about linearly to 8 pairs (759/s), flatten at 16 (805/s), peak at 32 (909/s) and fall to 678/s at 256, with latency growing roughly linearly from 16 pairs on and the 200 ms move target failing at 128 pairs.
Held for 30 minutes at 70% of the ceiling (49 pairs), all latency targets passed, but the system drifted: HTTP p95 10 -> 48 ms with requests per second down 25%, Redis 3.2 -> 13.8 MB, platform threads 125 -> 151,
Game Host heap after GC 251 -> 371 MB, and at 17.5 minutes the platform lost the ownership of about 35 rooms, after which the room and session gauges stayed doubled. After the load fell to zero (`up-down`) sockets, rooms, sessions and Hikari connections were at 0 within 30 s, the Game Host was back at 45 threads,
but the platform kept 109 threads (57 before) and Redis kept 36,047 keys and 6.91 MB (5 keys and 1.77 MB before): two keys per room are never removed.

**(c) Where does it break, and why?** At the platform pod and Postgres, not the Game Host: from 8 pairs on the platform sat at 2.5 to 3.0 of 4 cores and Postgres at 1.6 to 1.85 of 2, while the Game Host used 0.9 to 1.5 of 4 and its gRPC executors were parked in the thread dump.
The cause inside the platform (STOMP broker, HTTP, event fan-out, Postgres writes) was not isolated. Two failures were not about load at all: a Game Host wedge on its first cold start (seen in `contexts` and in `up-down` attempt 1, once with the supervisor taking about 6 minutes to restart it),
and a 10 s WebSocket connect stall about every 300 s.

## Capacity targets

| Target | Result | Limiting factor |
|---|---|---|
| 500 concurrent sessions | **not reached**: about 55 at the `ramp-to-break` ceiling (63 at its highest step); 210 were active at 256 pairs in `parallelism`, with the 200 ms move target failed from 128 pairs | `tb_room_join` latency; platform pod CPU (about 3 of 4 cores) and Postgres CPU (1.85 of 2) |
| 5,000 WebSockets | **not reached**: 140 at the ceiling (160 open when the run aborted; 512 at 256 pairs in `parallelism`, with latency targets failed); 4,860 not attempted | as above; 5,000 sockets need 2,500 pairs and 1,000 are provisioned |

## Single node

All of it ran on one node with the load generator inside the same VM (4 of 16 CPUs reserved for k6, generator-bound steps flagged). It says nothing about horizontal scaling:
the platform and Game Host ran with one replica each and no autoscaler. Phase B has its own design round.

## Follow-ups

Every degradation is an entry in [`load-testing.md` §13](../../docs/specs/deployment/load-testing.md#13-follow-ups):

| # | Entry | Report |
|---|---|---|
| 1 | Throughput plateaus at 16 pairs and declines past 32; the Game Host is not the limit | [parallelism](2026-10-18-parallelism.md) |
| 2 | The 200 ms move target fails at 128 pairs | [parallelism](2026-10-18-parallelism.md) |
| 3 | The ramp stops at 80 pairs on a `tb_room_join` tail (Phase A) | [ramp-to-break](2026-10-18-ramp-to-break.md) |
| 4 | `ready_timeout` errors under load | [parallelism](2026-10-18-parallelism.md), [ramp-to-break](2026-10-18-ramp-to-break.md) |
| 5 | Platform threads grow from 80 to 226 under load | [parallelism](2026-10-18-parallelism.md), [ramp-to-break](2026-10-18-ramp-to-break.md) |
| 6 | The run protocol's `jcmd 1` fails on the Game Host image | [parallelism](2026-10-18-parallelism.md) |
| 7 | The Game Host can wedge into health 503 and stay there; the supervisor does not restart it | [contexts](2026-10-18-contexts.md) |
| 8 | A cold start with four contexts takes 10.2 to 10.3 s | [contexts](2026-10-18-contexts.md) |
| 9 | Four contexts cost about three times the Game Host CPU for the same throughput | [contexts](2026-10-18-contexts.md) |
| 10 | A 10 s WebSocket connect stall recurs about every 300 s | [start-rate](2026-10-18-start-rate.md), [contexts](2026-10-18-contexts.md) |
| 11 | `start-rate` did not find the rate at which `game_start` degrades | [start-rate](2026-10-18-start-rate.md) |
| 12 | The `default-limits` load trips the WebSocket action bucket in every iteration | [default-limits](2026-10-18-default-limits.md) |
| 13 | Redis keeps two keys per room and never removes them | [up-down](2026-10-19-up-down.md), [soak](2026-10-18-soak.md) |
| 14 | The platform lost the ownership of about 35 rooms at once; the gauges never recovered | [soak](2026-10-18-soak.md) |
| 15 | Latency rises and throughput falls across a 30-minute hold | [soak](2026-10-18-soak.md) |
| 16 | Game Host heap after GC grows 251 -> 371 MB over the soak | [soak](2026-10-18-soak.md) |
| 17 | The platform keeps its threads after the load is gone | [up-down](2026-10-19-up-down.md), [soak](2026-10-18-soak.md) |
| 18 | The Game Host wedges on its first cold start with a single context too | [up-down](2026-10-19-up-down.md) |

## M16 re-verification, 2026-10-21

After the fixes of `IMP-M16-01` to `13` the same scenarios ran again on the same single node (16 CPUs, 15.2 GiB, load generator in the VM), at the commits of `turnbase-platform` `65d9d74` and `turnbase-game-host` `b121989`, with the harness now resolving the host name once. It is a single-node, laptop result like Phase A's. Nothing was fixed by the runs themselves; what persists is a Phase B note in [`load-testing.md` §13](../../docs/specs/deployment/load-testing.md#13-follow-ups), where every finding 1 to 18 carries an `**M16:**` line.

### Reports

| Scenario | Report | Result in one line |
|---|---|---|
| `parallelism` | [2026-10-21-m16-parallelism.md](2026-10-21-m16-parallelism.md) | Peak 1,055 moves/s at 32 pairs (909 in Phase A); ceiling still 64 pairs; 0 errors in 97,015 games; first to break the DB pool |
| `parallelism` (M17 pool sizing) | [2026-10-23-m17-pool-sizing.md](2026-10-23-m17-pool-sizing.md) | Pools 5, 10, 20: ceiling 64 pairs each; peak 1,452, 1,755, 1,714 moves/s; pool 10 confirmed (`FR-DBQ-006`)
| `ramp-to-break` | [2026-10-21-m16-ramp-to-break.md](2026-10-21-m16-ramp-to-break.md) | Ceiling 80 pairs (Phase A 70), aborted at 90 on a `tb_room_join` p95 of 200 ms; first to break the DB pool |
| `start-rate` | [2026-10-21-m16-start-rate.md](2026-10-21-m16-start-rate.md) | Clean to 32 games/s (Phase A 16); degrades between 32 and 64; no stall |
| `contexts` | [2026-10-21-m16-contexts.md](2026-10-21-m16-contexts.md) | Four contexts still cost about 3 Game Host cores; cold start 21.3 s mean (10.2 s in Phase A) |
| `soak` | [2026-10-21-m16-soak.md](2026-10-21-m16-soak.md) | 56 pairs for 30 minutes: all latency targets met, 0 errors, leaks gone; HTTP p99 drift +122% |
| `up-down` | [2026-10-21-m16-up-down.md](2026-10-21-m16-up-down.md) | Everything released within 60 s; platform threads 82 against 76 before; Redis 6 keys against 5 |
| stall | [2026-10-21-m16-stall.md](2026-10-21-m16-stall.md) | The 300 s stall was k6's DNS re-resolve, not the product |
| CPU per move | [2026-10-21-m16-cpu.md](2026-10-21-m16-cpu.md) | 2.60 ms of platform CPU per move, no local hotspot of 10% |
| threads | [2026-10-20-m16-threads.md](2026-10-20-m16-threads.md) | Platform threads 81 after the load against 77 before (25 kept before the fix) |

### Endurance criteria (`IMP-M16-15`)

| Criterion | Run | Result |
|---|---|---|
| No `not owned by this instance` ERROR in the platform log | `soak` | **pass**: 0 in 32 minutes (and 0 in the discarded first attempt) |
| Redis keyspace back to its pre-run size within 5 minutes after `up-down` (within 1%) | `up-down` | **fail by one key, no leak**: `DBSIZE` 5 before, 6 five minutes after (one extra key with a TTL, not a room key; 5 again a few minutes later), `used_memory` -2.8%; Phase A left 36,047 keys. Whether the one key counts is the owner's reading of "within 1%" |
| Platform threads idle-after within 10% of idle-before | `up-down` | **pass**: 82 against 76 (+7.9%, `/proc`); the JVM gauge 67 against 61 (+9.8%) |
| Game Host heap after GC drifts < 10% over the soak | `soak` | **pass**: +1.1% (175.1 -> 177.0 MB) |
| HTTP p99 drifts < 25% over the soak | `soak` | **fail**: +122% (77 -> 172 ms), p95 +103%, requests per second -26.5%. Cause visible in Postgres: `Seq Scan on room_participant` in the room occupancy subquery and in the lookup by `user_id`, linear in a table that keeps every closed room's participants. Phase B note |
| No Game Host restart | `soak`, `up-down` | **pass**: 0 pod restarts in both, 0 errors |

The first soak attempt ran on a database that still held 22,842 rooms of an earlier run (the stack had not been reset) and is kept as `20261021-225609-soak-attempt1`; it agrees with the result on every criterion (p99 drift +90%, `tb_room_join` p95 214 ms over its target).

### The owner's three questions, after M16

**(a) Worst-case load.** The `ramp-to-break` ceiling rose from 70 to 80 pairs (160 sockets, at most 62 concurrent sessions); `parallelism` still gives 64; the clean `start-rate` ceiling doubled to 32 games/s. 500 sessions and 5,000 WebSockets are still not reached.
**(b) Rising and falling load.** Held for 30 minutes at 56 pairs everything stays inside its target and the Phase A drifts in Redis, threads, Game Host heap and the room and session gauges are gone, but HTTP latency still rises at constant load (p99 77 -> 172 ms). After the load every resource is released within 60 s.
**(c) Where it breaks.** At the database: the 10-connection Hikari pool is 10 of 10 busy from about 16 to 30 pairs on, with up to 207 requests waiting, and Postgres sits at about its 2-core limit, while the Game Host uses 0.4 to 1.2 of 4 cores. The statements that dominate are scans of `room_participant`.

### Findings after M16

| # | Entry | Status | Evidence |
|---|---|---|---|
| 1 | Throughput plateaus at 16 pairs and declines past 32; the Game Host is not the limit | persists, smaller (peak 1,055 moves/s); DB pool | [parallelism](2026-10-21-m16-parallelism.md), [cpu](2026-10-21-m16-cpu.md) |
| 2 | The 200 ms move target fails at 128 pairs | persists (128 pairs); DB pool | [parallelism](2026-10-21-m16-parallelism.md) |
| 3 | The ramp stops at 80 pairs on a `tb_room_join` tail (Phase A) | persists, with a higher ceiling: aborts at 90 pairs (Phase A 80) | [ramp-to-break](2026-10-21-m16-ramp-to-break.md) |
| 4 | `ready_timeout` errors under load | resolved: 0 errors in every M16 run | [soak](2026-10-21-m16-soak.md), [up-down](2026-10-21-m16-up-down.md) |
| 5 | Platform threads grow from 80 to 226 under load | resolved: flat at 154 to 159 in the soak | [threads](2026-10-20-m16-threads.md), [soak](2026-10-21-m16-soak.md) |
| 6 | The run protocol's `jcmd 1` fails on the Game Host image | resolved by the record correction | [up-down](2026-10-21-m16-up-down.md) |
| 7 | The Game Host can wedge into health 503 and the supervisor does not restart it | resolved by `IMP-M16-02`; no wedge in two cold starts | [up-down](2026-10-21-m16-up-down.md) |
| 8 | A cold start with four contexts takes 10.2 to 10.3 s, twice the single-context 5 s | persists, worse (21.3 s mean) | [contexts](2026-10-21-m16-contexts.md) |
| 9 | Four contexts cost about three times the Game Host CPU for the same throughput | persists (about 3.0 cores) | [contexts](2026-10-21-m16-contexts.md) |
| 10 | A 10 s WebSocket connect stall recurs about every 300 s | resolved: k6's DNS re-resolve | [stall](2026-10-21-m16-stall.md) |
| 11 | `start-rate` did not find the rate at which `game_start` degrades | resolved: between 32 and 64 games/s | [start-rate](2026-10-21-m16-start-rate.md) |
| 12 | The `default-limits` load trips the WebSocket action bucket in every iteration | resolved: harness artefact | this file |
| 13 | Redis keeps two keys per room and never removes them | resolved (one TTL key after 5 minutes, see above) | [up-down](2026-10-21-m16-up-down.md), [soak](2026-10-21-m16-soak.md) |
| 14 | The platform lost the ownership of about 35 rooms at once; the gauges never recovered | resolved: 0 occurrences | [soak](2026-10-21-m16-soak.md) |
| 15 | Latency rises and throughput falls across a 30-minute hold at constant load | persists, smaller; Postgres scans | [soak](2026-10-21-m16-soak.md) |
| 16 | Game Host heap after GC grows 251 -> 371 MB over the soak | resolved: +1.1% | [soak](2026-10-21-m16-soak.md) |
| 17 | The platform keeps its threads after the load is gone | resolved: +7.9% | [up-down](2026-10-21-m16-up-down.md) |
| 18 | The Game Host wedges on its first cold start with a single context too | resolved by `IMP-M16-02`/`03`; two clean cold starts | [up-down](2026-10-21-m16-up-down.md), [soak](2026-10-21-m16-soak.md) |

Phase B starts from the persisting entries: 1 to 3 and 15 (the database pool and the `room_participant` scans), 8 and 9 (the cost of several Espresso contexts).

## M17 re-verification, 2026-10-24

After `IMP-M17-01` to `04` (the game-path statements that scanned `room`, `room_team` and `room_participant`, the explicit pool of 10) the three failing scenarios ran again on the same single node, at `turnbase-platform` `e52c1f4`. Two of the three named `PostgreSQL` as the first to break, so `FR-DBQ-007` applied: the chart gained `postgres.settings` ([`local-environment.md`](../../docs/specs/deployment/local-environment.md) §7.9) and `parallelism` and `ramp-to-break` were rerun on it (two runs each in their reports, `A` before and `B` after). It is a single-node, laptop result.

### Reports

| Scenario | Report | Result in one line |
|---|---|---|
| `parallelism` | [2026-10-24-m17-parallelism.md](2026-10-24-m17-parallelism.md) | Ceiling 64 pairs; peak 1,779 moves/s (M16 1,055); the move target now passes at 128 pairs; first to break `PostgreSQL`; the settings did not move it |
| `ramp-to-break` | [2026-10-24-m17-ramp-to-break.md](2026-10-24-m17-ramp-to-break.md) | Ceiling 170 pairs (M16 80), 190 with the settings (380 sockets, 150 sessions); first to break `PostgreSQL` |
| `soak` | [2026-10-24-m17-soak.md](2026-10-24-m17-soak.md) | 56 pairs for 30 minutes: 0 errors, HTTP p99 drift -7.2% (M16 +122%); first to break `none` |

### Database criteria (`platform-operations.md` NFR-DBQ-001 to 003)

| Criterion | Result |
|---|---|
| NFR-DBQ-001: the database is not the first thing to break in `parallelism`, `ramp-to-break` and `soak` | **fail**: `parallelism` and `ramp-to-break` name `PostgreSQL` (2.0 to 2.2 of 2 cores with 150 to 206 requests waiting for a connection); `soak` names `none` |
| NFR-DBQ-002: HTTP p99 drift < 25% over the soak hold | **pass**: -7.2% (36.3 -> 33.6 ms), throughput +11.6% |
| NFR-DBQ-003: `ramp-to-break` ceiling >= 80 pairs; `parallelism` ceiling >= 64 pairs and peak >= 1,002 moves/s | **pass**: 170 (190 tuned) pairs; 64 pairs and 1,779 moves/s |

`FR-DBQ-007` was applied and did not change the verdict: Postgres is CPU-bound on its 2-core pin and memory or connection settings do not add CPU. The ceilings moved from the statement work removed by `IMP-M17-01` and `02` (platform CPU is now the next limit, 3.5 to 3.7 of 4 cores).

### The owner's three questions, after M17

**(a) Worst-case load.** `ramp-to-break` ceiling 170 pairs (190 tuned), 340 to 380 sockets and at most 150 sessions; 500 sessions and 5,000 WebSockets are still not reached.
**(b) Rising and falling load.** The Phase A and M16 drift is gone: 30 minutes at 56 pairs, p99 -7.2%, throughput +11.6%.
**(c) Where it breaks.** At Postgres CPU (2 cores) behind the 10-connection pool, on `tb_room_join` and `tb_room_create`; the Game Host is at 1.2 of 4 cores.

### Findings after M17

| # | Entry | Status | Evidence |
|---|---|---|---|
| 1 | Throughput plateaus at 16 pairs and declines past 32 | resolved as a decline (1,779 peak, no drop to 128); the plateau and the 64-pair ceiling persist; `PostgreSQL` | [parallelism](2026-10-24-m17-parallelism.md) |
| 2 | The 200 ms move target fails at 128 pairs | resolved: 150 ms | [parallelism](2026-10-24-m17-parallelism.md) |
| 3 | The ramp stops on a `tb_room_join` tail | persists at a higher ceiling: 170 (190 tuned) pairs; `PostgreSQL` | [ramp-to-break](2026-10-24-m17-ramp-to-break.md) |
| 15 | Latency rises across a 30-minute hold | resolved: -7.2% | [soak](2026-10-24-m17-soak.md) |

Phase B starts from findings 1 and 3: Postgres CPU (more cores, read offload or fewer statements per room join and create), then 8 and 9 (the cost of several Espresso contexts).
