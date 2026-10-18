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
| 3 | The ramp stops at 80 pairs on a `tb_room_join` tail | [ramp-to-break](2026-10-18-ramp-to-break.md) |
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
