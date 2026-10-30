# Load and Scalability Testing, Phase B: capacity and autoscaling

Phase B of [`load-testing.md`](load-testing.md), replacing its §9 outline. Phase A and milestones M16 and
M17 measured one Platform instance and one Game Host on one node and removed the defects that measurement
found. Phase B makes the system **grow when load rises and shrink when it falls**, and proves that it stays
correct and efficient while it does: at peak traffic, under extended high load, and through ordinary rises
and falls.

Items marked **(owner)** were decided by the project owner (2026-10-24). **(orchestrator's call)** marks a
choice made during design that the builder may revisit with a reason; **(builder's call)** marks a choice
deliberately left to the builder. Work items are registered as milestone **M18** in
[`registry.md`](../../implementation/registry.md).

---

## 1. Intent

After M17 the platform carries 170 pairs (190 tuned) on the reference node, the 30-minute soak no longer
drifts, and the first thing to break is PostgreSQL's CPU (2 cores, pinned) behind the 10-connection pool,
on `tb_room_join` and `tb_room_create` ([`SUMMARY.md`](../../../loadtest/reports/SUMMARY.md) *M17*). The
platform is the next limit at 3.5 to 3.7 of its 4 cores. The Game Host is at 1.2 of 4.

The owner's goal for Phase B: **proper autoscaling that adapts to increasing and decreasing load**, with
peak traffic, extended high load and the other common load shapes handled correctly and efficiently. **At
this point redundancy and correctness matter more than a higher ceiling (owner).** The reference node is a
16-core, 32 GB desktop. The Docker Desktop WSL2 VM sees 16 CPUs and about 15 GiB (`docker info`, M17
reports), and that is accepted as it is.

### Goals

- **No single point of failure in the stateless tiers**: at least two Platform and two Game Host replicas
  at all times, and the loss of any one of them under load loses no game (§6 `failover`).
- The Platform Monolith scales horizontally under a HorizontalPodAutoscaler, with WebSocket room affinity
  as ADR-0002 and ADR-0008 specify (§4).
- The Game Host scales out and in on its own signal, spreads sessions across replicas, and drains
  correctly on scale-in (§5).
- The single-node capacity work the M17 findings point to is done first, so autoscaling multiplies an
  efficient replica rather than an inefficient one (§3).
- The behaviour of the scaled system is measured under five load shapes (§6) against requirements written
  for the purpose (§7).
- `game-host-internals.md` §18 `OQ-5` is decided by measurement (§5.2).

### Non-goals

- PostgreSQL or Redis replication, read replicas, or a connection pooler (PgBouncer). Both stay single,
  non-HA instances ([ADR-0001](../../decisions/0001-local-first-mvp-platform.md),
  [ADR-0003](../../decisions/0003-mvp-availability-target.md)). **(orchestrator's call)**
- Scale to zero (`platform-architecture.md` FR-SCALE-002 stays *Could*, deferred).
- Cloud clusters and multi-node scheduling. Phase B runs on the same single Docker Desktop node as Phase A.
- Load tests in CI.

### Anti-goals

- A scale event that loses, duplicates or reorders a game input, aborts a game, or strands a player in a
  room nobody serves. **Correctness under scaling outranks every latency figure.**
- Autoscaling that flaps: replicas added and removed repeatedly under a steady load.
- Trading correctness or redundancy for a higher ceiling. A ceiling raised by measuring the generator, not the platform, is also a failure: every report keeps Phase A's single-node
  caveat, generator-bound flag and coordinated-omission note (`load-testing.md` §8).
- Weakening a protection outside the `test`, `e2e` and `loadtest` profiles (`load-testing.md` §1, unchanged).

## 2. Owner decisions

| Decision | Choice |
|---|---|
| Focus | Shift away from the Game Host as the bottleneck: it is far from its ceiling (1.2 of 4 cores at the M17 ceiling) |
| Resources | **The Game Host drops to 2 cores; the 2 cores freed go to PostgreSQL**, which moves from 2 to 4 |
| Capacity work | Done before scale-out: fewer statements per room join and create, a per-room participant cache on the move path, one Redis round trip per move, and a decision on the OpenTelemetry agent's 19 to 20% of platform CPU |
| Priority | **Redundancy and correctness over a higher ceiling**; the scaled ceiling only has to stay at or above the single-instance one |
| What scales | **The Platform autoscales**; **PostgreSQL stays one fixed instance**; **the Game Host keeps a correct scale-out and scale-in** even though it rarely needs to scale out |
| `OQ-5` | Eager or lazy reassignment after a Game Host dies is decided from **empirical test results of both, focusing on correctness** |
| `OQ-004` | `NFR-AVAIL-001` stays at 99% (resolved 2026-10-24) |

The owner's 2026-10-24 decision to autoscale the Platform lifts the deferral that
`platform-operations.md` NFR-SCALE-001 and CON-013 carry. `IMP-M18-01` records it as ADR-0020 and amends
both rows (§8).

## 3. Track 1: capacity on one node

The goal of this track is `platform-operations.md` NFR-DBQ-001, which M17 left failing: the database is not
the first thing to break in `parallelism`, `ramp-to-break` and `soak`.

### 3.1 Reallocate the cores (owner)

The load-test overlays (`loadtest/helm/values-loadtest.yaml`, `values-default-limits.yaml`, mirrored as
`test/check-overlays.sh` requires) move to:

| Component | Phase A / M17 | Phase B |
|---|---|---|
| PostgreSQL | 2 CPU, 1 GiB | **4 CPU**, 2 GiB (orchestrator's call: memory doubles with the CPU) |
| Game Host | 4 CPU, 4 GiB | **2 CPU** in total, 4 GiB, one replica for Track 1 (memory unchanged: four contexts used 0.8 GB of heap, `load-testing.md` §13 finding 9). Track 3 splits it into two replicas of 1 CPU (§4.4) |
| Platform | 4 CPU, 3 GiB | unchanged for Track 1; per-replica sizing for Track 2 is §4.4 |
| Redis | 1 CPU, 512 MiB | unchanged |

`postgres.settings` ([`local-environment.md`](local-environment.md) §7.9, FR-DBQ-007) is rescaled for 4 CPU
and 2 GiB (`shared_buffers` 25% of memory; `max_worker_processes` and the parallel-worker settings to the
core count). `max_connections` is set from the cross-replica budget of §4.5.

The §8 *first to break* rule's PostgreSQL threshold, "at or above 1.9 of its 2 cores", becomes **95% of its
CPU limit** (3.8 of 4). `load-testing.md` §8 and `platform-operations.md` CON-013 are amended by
`IMP-M18-01`.

A baseline (`parallelism` and `ramp-to-break`) is run on the reallocated cores before any code changes, so
that every later improvement is measured against the same hardware.

### 3.2 Fewer statements per room create and join

Per room join today: a `select … for update` on the participant, an `insert into room_participant` with a
`select max(join_order)`, the team-slot query (`room_team` left join `room_participant`, the slowest per-join
statement), the `room` version CAS, and the invitation delete
([`2026-10-21-m16-cpu.md`](../../../loadtest/reports/2026-10-21-m16-cpu.md) §3). Room create has a similar
sequence.

- Count the statements and their Postgres time per create and per join with `pg_stat_statements` on a
  `start-rate` or `ramp-to-break` run, before and after.
- Remove, merge or index statements on both paths. **The transaction boundaries, the room lock and the
  version-before-publish ordering** (`02-room-to-game-start.md` step 5) **are not changed.** Merging two
  statements into one that keeps the same isolation is in scope; moving a statement outside the
  transaction is not.
- Which statements and how are the **builder's call**. `GamePathQueryCostIT` (IMP-M17-02) is extended so
  the new statements stay history-independent (FR-DBQ-001).

### 3.3 A per-room participant cache on the move path

Each move issues 3.8 Postgres statements that answer one question: *is this user the acting participant of
a live room?* (the host lookup and the two `room_participant` lookups, `2026-10-21-m16-cpu.md` §3).

- The cache lives in memory **on the room's owning instance** and is keyed by room. Only the owner mutates
  a room (ADR-0008), so the owner is the one place that sees every change.
- It is **invalidated** on every mutation of the room's participants or host: join, leave, kick, disconnect,
  reconnect, host transfer, reassignment and closure. It is **dropped as a whole** when the instance loses
  ownership of the room (`onRoomOwnershipLost`) or the room closes.
- A miss reads Postgres exactly as today. A cache that cannot prove itself current is a miss.
- Where the invalidation hooks into the room code is the **builder's call**. The test that matters is a
  property-style one: an interleaving of mutations and moves never authorises a move that today's code
  would reject.
- **As built (`IMP-M18-04`).** `room.ParticipantCache` holds one `room`-plus-participants view per active
  session. `RoomEventExecutor.execute` brackets every mutation, and nothing is served or stored for the room
  while one runs, so the cache never answers differently from Postgres. A hit also needs the room's ownership
  epoch unchanged and the entry under 30 s old; the age bound covers account erasure, the one writer of
  `room_participant` outside the executor, whose sessions are revoked in the same step. The view also serves
  the fan-out roster, which was the second per-move statement (the three statements named above had been
  the deadline sweep's, fixed by `IMP-M17-01`, not the move path's).

### 3.4 One Redis round trip per move

Per move today: about ten Redis commands (`GET session:`, `GET routing:`, `SET session:`, `SET delivered:`,
`SET failcount:`, `RPUSH gamelog:`, `PEXPIRE gamelog:`, `INCR seq:`, `GET delivered:`). The writes after a
`ProcessResult` become one pipeline or one Lua script (**builder's call**). The reads that gate dispatch stay
where they are if merging them would change the order relative to the gRPC call. The exactly-once rules of
`game-host-internals.md` §9.2 (the delivery watermark) are not changed. A test shows the watermark is never
advanced before the effects are fanned out.

- **As built (`IMP-M18-05`).** One Lua script, `game.MoveCommit`, after the fan-out: the `failcount:` reset,
  the `gamelog:` append and the `delivered:` watermark. A move is now `GET routing:`, `GET delivered:`, the
  `INCR seq:` and that one script: four commands where there were about nine, and one round trip for the
  writes. The watermark is in the script, so the script runs after the fan-out and the watermark cannot move
  first; for that reason `EffectDelivery.deliver` returns the `log` entries it published and `MoveCommit`
  stores them, instead of `EffectFanOut` appending each as it publishes. A replay (`sequence <= delivered`)
  skips the fan-out and passes no entry and no watermark, so the script only resets the counter. If the
  fan-out throws, the counter is still reset, the watermark and the log are left, and the replay does both.
  The cost: a `GAME_SYNC` read in the instant between a `GAME_LOG` frame going out and the script landing can
  lack that one entry in its `log` (the client already has it live if it was subscribed). `CreateSession`'s
  initial effects still append as they publish.

### 3.5 The OpenTelemetry agent's cost

`platform-operations.md` FR-TRACE-001 (Must) requires the OpenTelemetry Java agent on all outbound calls.
The agent was 19 to 20% of platform CPU at 64 pairs, although traces are head-sampled at 10%
(`observability.md` §4). `IMP-M18-06` measures `parallelism` at the post-reallocation baseline under three
configurations and reports CPU per move and peak moves/s for each:

1. the agent as specified;
2. the agent with the JDBC and Lettuce instrumentation modules disabled (`OTEL_INSTRUMENTATION_JDBC_ENABLED`,
   `OTEL_INSTRUMENTATION_LETTUCE_ENABLED`);
3. the agent disabled (`OTEL_JAVAAGENT_ENABLED=false`), as the upper bound.

**The owner chooses from the report.** If the choice is not configuration 1, `IMP-M18-06` amends FR-TRACE-001
and `observability.md` §4 to match and sets the chart default. Otherwise nothing changes.

### 3.6 Re-verification

`parallelism`, `ramp-to-break` and `soak` run again on one Platform instance once §3.1 to §3.5 are in. The
verdict on NFR-DBQ-001 is recorded. If PostgreSQL is still the first to break, that is recorded as a finding
and Track 2 proceeds anyway: the database is not on Track 2's scaling path, and §7's requirements are
written so that they can be judged regardless.

## 4. Track 2: the Platform scales out

### 4.1 What multi-instance needs that the code does not yet have

ADR-0008's ownership claim, adoption and release already run on every restart and rolling deploy (M16
`IMP-M16-07` made them correct). Recon found these gaps for more than one live replica:

| Gap | Today | Required |
|---|---|---|
| WebSocket affinity | The browser sends `/ws?instance={podId}` (`room-websocket.md` *Routing on join*), but the frontend nginx `location /ws` proxies to the Service, round-robin | The upgrade reaches the named pod when it is ready, and falls back to the Service when it is not (FR-DEPLOY-002) |
| SSE alerts | `NotificationEmitterRegistry` holds every `/api/notifications/stream` connection in memory, so `AlertPublisher.publish` on instance B never reaches a user whose stream is on instance A | A user-scoped alert reaches every connection of that user on every instance |
| Session revocation | `SessionRevokedEvent` closes WebSockets and SSE streams on the instance that raised it | It closes them on every instance |
| WebSocket connections per user | At most 4, counted per instance in `WebSocketConnectionRegistry` | At most 4 cluster-wide (`rate-limiting.md`) |
| Anything else | `KeyedLocks`, `GameHostChannels`, `ReconciliationMetrics`, `RoomOwnershipService`, `RoomSubscriptionAuthorizer` and `WebSocketRateLimiter` also hold in-memory maps | Audited: each is either correct per instance (and the audit says why) or fixed |

The API and public rate-limit tiers are already Redis-backed, and the scheduled jobs that must run once are
already ShedLock'd or ownership-aware. The audit (`IMP-M18-08`) confirms both and does not assume them.

### 4.2 Cross-instance user-scoped delivery

ADR-0002 rejected Redis pub/sub for **room** fan-out, and that stays true: room traffic is served by the
room's owner. User-scoped pushes (SSE alerts, revocation) have no owner and are low-volume. They go
through **one Redis pub/sub channel per concern**, published by any instance and delivered by the instance
that holds the user's connections. (orchestrator's call; ADR-0020 records that this does not reopen
ADR-0002.) Delivery stays best-effort, exactly as the in-memory push is today (`sse-notifications.md`: an
alert to a user with no stream is dropped; the notification row is the durable record).

### 4.3 Affinity routing

The frontend nginx routes `/ws` by the `instance` query parameter:

- a **headless Service** for the platform pods gives each *ready* pod a resolvable DNS name. A Deployment's
  pod name is not one (a pod's name resolves only when the pod sets `hostname`, which a pod template cannot do
  per pod), but the address is: the endpoint `10.1.6.38` resolves as
  `10-1-6-38.{release}-platform-pods.{namespace}.svc.cluster.local`. So the **instance name carries the pod's
  address**: `{pod name}@{a-b-c-d}` plus the per-incarnation UUID (`room-lifecycle.md` §1.1; the chart supplies
  `POD_IP` through the downward API);
- with `?instance=` present, nginx takes the dashed address out of the hint and proxies to that name; when
  the hint is not shaped like one, the name does not resolve (a pod that is not ready, or gone) or the
  connection is refused, it falls back to the regular Service (the hint is advisory, FR-DEPLOY-002,
  `room-lifecycle.md` §1.7). Only the dashed address is taken from the parameter, so the proxy can reach
  nothing but an endpoint of that Service;
- without the parameter, it proxies to the regular Service as today.

The nginx mechanism, as built (`IMP-M18-09`): a `resolver` plus a variable `proxy_pass` and an `error_page`
fallback to a named location. ADR-0008 rejected consistent hashing at the ingress, so **the pod
named by the hint is the target, not a hash of the room.** The REST path stays round-robin: any instance
can serve a REST call and returns the owner's hint. The k6 harness already builds the `/ws` URL from the hint
the same way (`IMP-M18-14` checks this and fixes it if not).

### 4.4 Replicas, per-replica size and the node budget

- `platform.autoscaling.enabled=true` in the Phase B overlays, on CPU utilisation through metrics-server
  (present on the reference node).
- **Minimum two replicas of the Platform and of the Game Host (owner: redundancy).** One replica of either
  is a single point of failure, and the `failover` scenario (§6) kills one.
- **Per-replica size** (orchestrator's call): **Platform 1.5 CPU**, **Game Host 1 CPU**. Two Game Host
  replicas of 1 CPU keep the owner's 2-core Game Host total at the minimum (§3.1), and the M17 ceiling used
  1.2 cores of it. Two Platform replicas of 1.5 CPU are 3 CPU against today's single 4, a gap Track 1's
  savings are meant to cover. If a 1-CPU Game Host's cold start trips the 20 s `BootWatchdog`
  ([ADR-0018](../../decisions/0018-game-start-resilience.md)), `IMP-M18-13` records it and moves to two
  replicas of 1.5 CPU, taking the half core from the Platform maximum. Memory is the builder's call within
  the VM's 15 GiB.
- **Maxima: three of each** (orchestrator's call). The budget at the maxima, all at `requests == limits`:

  > PostgreSQL 4 + Redis 1 + Game Host 3 × 1 + Platform 3 × 1.5 = 12.5 CPU, plus k6 pinned to 3 cores = 15.5
  > of the node's 16.

  k6 moves from 4 pinned cores to 3. If `check-generator.sh` flags a step generator-bound at 3, that step
  does not count (`load-testing.md` §4 A3, unchanged) and the report says so. The builder may rebalance
  within the 16 CPUs and records the arithmetic in `local-environment.md` §7.9.
- The CPU target and the `behavior` stabilisation windows (scale-out fast, scale-in slow, so that §1's
  anti-flapping goal holds) are the **builder's call**.

### 4.5 Connection budget

Each replica has its own pool (FR-DBQ-005, 10 connections). PostgreSQL's `max_connections` covers
`platform.maxReplicas × poolMaxSize` plus migrations and operators. Whether the per-replica pool stays 10
when several replicas share 4 PostgreSQL cores is measured by the Track 2 runs, not assumed. A finding there
is recorded; it does not reopen `IMP-M17-04` within M18.

### 4.6 Scale-in

The rolling-deploy path of `local-environment.md` §3 is the scale-in path: on `SIGTERM` the instance stops
accepting new rooms, **releases** its rooms (`RoomOwnershipService.release`; the next claimant takes the free
branch with no lease wait, `room-lifecycle.md` §1.6) and closes its WebSockets, so that clients reconnect,
rejoin and receive the new owner's hint. The `preStop` hook, `terminationGracePeriodSeconds`, and the order
of readiness-off, release and socket close are the **builder's call**, verified by a test that scales from 2
to 1 replica mid-game with every game finishing.

## 5. Track 3: the Game Host

### 5.1 Spread the load and cap it (`platform-architecture.md` FR-SCALE-005)

Host selection today is warm-first, then lowest `activeSessions` (`game-host-internals.md` §11). It leaves
new replicas idle while the warm one has capacity. The rule becomes: **among live, non-draining,
non-quarantined hosts below their session cap, prefer warm, then lowest `activeSessions`; if every warm host
is at its cap, choose a cold one; and while fewer than `warm-hosts` (default 2) hosts are warm, choose a cold one so the standby holds the context before a drain or failover needs it** (`IMP-M18-13` found a cold standby lost a game: the cold boot at 1 CPU, 21 to 28 s, outlasted the 30 s retry budget). The per-host cap is the FR-SCALE-005 configurable maximum (default sized by the
builder from the §3.1 baseline at 2 CPU). A start with every host at its cap fails with `NO_HOST_AVAILABLE`, as
today. `IMP-M18-01` amends §11.

### 5.2 `OQ-5`: decided by measurement (owner)

`game-host-internals.md` §9.3 describes **eager** reassignment: at lease expiry, Orchestration clears
`routing:{sessionId}` for the dead host's sessions and reassigns them. The code reassigns **lazily**: on the
first `ProcessInput` whose routed host is unreachable (`GameInputService.reassign`).

`IMP-M18-12` implements eager reassignment behind a configuration switch beside the lazy one, runs **one
correctness suite against both**, and decides:

- **The suite** covers at least: a host killed mid-move, with the input applied and then not applied before
  the kill; a host killed with idle sessions that receive their next input after 1 s, after the lease TTL,
  and after the reassignment; a host killed while a deadline or turn timer is pending; a host that returns
  after its lease expired (a zombie still answering gRPC); two hosts killed in succession; a planned drain
  (§5.3) instead of a kill; and concurrent inputs for the same session during reassignment.
- **Correctness**, per scenario and mode: no input lost, none applied twice, none applied out of order, no
  session left routed to a dead host after it next needs one, no game aborted that the spec says survives.
  The checks reuse the `delivered:` watermark and `sequence` (§9.2).
- **Also recorded**: time from the kill to the session's next accepted input, and the Redis and gRPC calls
  each mode makes.
- **Decision rule** (orchestrator's call, applying the owner's *focus on correctness*): the mode with fewer
  correctness failures wins. If both have none, the mode that meets `platform-architecture.md` NFR-REL-002
  (< 30 s) in more scenarios wins. If they still tie, lazy wins, because it is the code that exists and
  ADR-0008 rejected eager reassignment for rooms on the same ground. The losing mode's code and switch are
  removed. §9.3 and §18 `OQ-5` are amended to describe the winner, with the report as evidence.
- A correctness failure **common to both modes** is a defect. It is fixed in this item if it is local, or
  recorded and escalated through `spec-defect` if it is not.

### 5.3 Autoscaling and scale-in drain (FR-SCALE-003, -004, -005, -006)

- **Signal.** FR-SCALE-003 asks for memory **or** active-session/context count, and neither is CPU. Session
  count needs a custom metric, so the Game Host scales with **KEDA**, on a Prometheus query over the
  hosts' `activeSessions` against the FR-SCALE-005 cap and on memory percentage (FR-SCALE-004)
  (orchestrator's call: KEDA over prometheus-adapter because it scales on a query without an adapter
  configuration language). KEDA is installed by `loadtest/install.sh` from a pinned Helm chart version, and
  the chart's `ScaledObject` is rendered only when enabled.
- **`minReplicaCount` 2** (owner: redundancy; FR-SCALE-001's "at least one" is met), maximum 3 (§4.4).
- **Scale-in** resolves `platform-architecture.md` `OQ-003` (wait or actively migrate) as **drain, then
  migrate** (orchestrator's call). The host to be removed is marked draining (the `draining` flag already
  exists in the registry and the heartbeat), so it receives no new sessions. It keeps serving its sessions
  for a drain period (builder's call, bounded by `terminationGracePeriodSeconds`). Sessions still on it at
  the end are reassigned by the `OQ-5` winner. FR-SCALE-006's "existing sessions complete naturally" is
  amended accordingly, because a session can outlive any grace period (an idle game is never "complete").
- **Cold starts and context limits.** A scale-out is a cold start: ADR-0018's boot wedge and
  `load-testing.md` §13 findings 8 and 9 (a four-context cold start at 10.2 s; three times the CPU) are
  re-measured at 2 CPU. `game-host-internals.md` §18 `OQ-6` (twelve contexts per JVM lifetime) is not
  reached by the Phase B scenarios, which run one game title, and each report says so.

## 6. Track 4: the scenarios that prove it

The harness (`loadtest/`) gains a **scaling timeline**: replica counts of every Deployment, HPA and KEDA
desired and current replicas, pod start and termination times, sampled every 5 s and written beside the
k6 summary. It also gains a **correctness check** after every run, in addition to the k6 thresholds: every
game started is finished or explicitly abandoned by the harness, no `GAME_EVENT` sequence gaps or
duplicates are seen by a client after dedup, and no room is left `IN_PROGRESS` (`load-testing.md`
anti-goals).

| Scenario | Shape | Answers |
|---|---|---|
| `ramp-to-break` (existing) | As Phase A, with autoscaling on | The scaled ceiling, and what breaks first when the replicas are at their maximum |
| `spike` (new) | 10% of the scaled ceiling for 5 min, a step to 100% within 30 s, a hold of 10 min, a drop back to 10% | How fast scale-out reacts and how much of the spike the thresholds absorb |
| `sustained-high` (new) | Ramp to 70% of the scaled ceiling and hold it for **60 min** | Drift and flapping under extended high load |
| `up-down` (existing) | Ramp up, hold, ramp to zero, hold, as Phase A | Scale-in: release of replicas and resources |
| `diurnal` (new) | Two compressed "days" of a smooth rise to 60%, a plateau and a fall to 5%, 20 min each | The ordinary daily shape: no flapping, no scale-in mid-game failures |
| `failover` (new) | A hold at 50% of the scaled ceiling. Under it: one Platform pod killed (`SIGKILL`, no grace), recovery, one Game Host pod killed, recovery, then one of each deleted gracefully | Redundancy: the loss of any one replica costs no game and no player their room |

The `failover` kills are driven by the harness through `kubectl`, at times recorded on the scaling timeline.
Ceiling-relative loads use the `ramp-to-break` ceiling measured in the same Phase B run series. Step sizes,
ramps and VU ceilings are the **builder's call**. The 256-pair step that ends early (`load-testing.md` §13,
M17 notes) is investigated in the harness item before the runs, so that ceilings are not misread.

## 7. Requirements

New requirements, `FR-ASC` and `NFR-ASC`, are added to
[`platform-operations.md`](../../requirements/platform-operations.md) by `IMP-M18-01` and registered in the
requirements `INDEX.md`. The values below are the orchestrator's proposal "for the record", as Phase A's
`NFR-LOAD` were (`load-testing.md` §7); the owner may adjust them. All are judged on the reference node and
recorded per scenario.

| ID | Requirement | Target |
|---|---|---|
| FR-ASC-001 | The Platform Monolith scales horizontally under an autoscaler between configured minimum and maximum replicas, on CPU | min 2 |
| FR-ASC-005 | At least two Platform and two Game Host replicas run at all times in the scaled deployment | 2 |
| FR-ASC-002 | WebSocket upgrades carrying an instance hint reach the named ready instance; otherwise any ready instance | FR-DEPLOY-002 |
| FR-ASC-003 | User-scoped pushes (alerts, session revocation) and the per-user connection cap hold across instances | §4.1 |
| FR-ASC-004 | A Platform instance being removed releases its rooms and closes its connections before it exits | §4.6 |
| NFR-ASC-001 | Scale-out reaction: from the step that crosses the target to the new replica serving (Ready and receiving traffic) | ≤ 3 min, Platform and Game Host |
| NFR-ASC-002 | Correctness through scaling: no lost, duplicated or reordered game input, no game aborted by a scale event, error rate < 1% | Every Phase B scenario |
| NFR-ASC-003 | Scale-in: after load ends, replicas return to minimum, and threads, rooms, sessions and Redis keys return to within 10% of the pre-run level | ≤ 10 min (`up-down`) |
| NFR-ASC-004 | Spike: `load-testing.md` §6 thresholds recover after the step | ≤ 3 min (`spike`) |
| NFR-ASC-005 | Sustained high load: HTTP p99 drift over the hold, and scale events after the first 10 min | < 25%; ≤ 1 per 10 min (`sustained-high`) |
| NFR-ASC-006 | The scaled `ramp-to-break` ceiling is at least the single-instance ceiling of §3.6 | ≥ §3.6 |
| NFR-ASC-007 | Failover: after an unannounced kill of one Platform or one Game Host replica, every game in progress continues (NFR-ASC-002 holds) and every affected player is back in their room | ≤ 30 s (`platform-architecture.md` NFR-REL-002) (`failover`) |

The Platform-side FR-SCALE rows in `platform-architecture.md` (FR-SCALE-003 to 006) stay as the Game Host
requirements. FR-SCALE-006 is amended for §5.3.

## 8. Spec and decision changes (done by `IMP-M18-01` before any code)

- **ADR-0020: Platform horizontal scaling.** Lifts NFR-SCALE-001's post-MVP deferral of multi-instance
  Platform for the reference node. Adopts affinity by instance hint at the frontend proxy (§4.3), Redis
  pub/sub for user-scoped pushes only (§4.2), a minimum of two replicas of each stateless tier, CPU-based HPA, release-on-`SIGTERM` scale-in, and KEDA for
  the Game Host. Amends ADR-0002 and ADR-0008 by reference only: neither is reversed.
- `platform-operations.md`: NFR-SCALE-001 and CON-013 amended; FR-ASC and NFR-ASC added (§7); the requirements
  INDEX updated.
- `platform-architecture.md`: FR-SCALE-006 amended (§5.3); `OQ-003` resolved (drain, then migrate).
- `game-host-internals.md` §11: the selection rule (§5.1). §9.3 and `OQ-5` are left for `IMP-M18-12`.
- `local-environment.md` §3: the ingress and proxy now route by hint; §7.9: the Phase B resource and
  connection budget.
- `load-testing.md`: §8 *first to break* threshold made relative to the CPU limit; §9 points here.

## 9. Order

Track 1 runs first because it changes the efficiency of the replica that Track 2 multiplies. Tracks 2 and 3
are independent of each other and may interleave. Track 4's runs come last.

```
01 spec ─┬─ 02 reallocate + baseline ─┬─ 03 statements ─┐
         │                            ├─ 04 cache ──────┼─ 07 single-node re-verification ─┐
         │                            ├─ 05 Redis ──────┘                                  │
         │                            └─ 06 OTel measurement                               │
         ├─ 08 multi-instance state ─┬─ 10 Platform HPA + scale-in ───────────────────────┤
         ├─ 09 affinity routing ─────┘                                                     ├─ 14 harness ─ 15, 16, 17 runs
         ├─ 11 host selection + cap ─┐                                                     │
         └─ 12 OQ-5 ─────────────────┴─ 13 Game Host KEDA + drain ─────────────────────────┘
```

## 10. Left to the builder

Everything marked **(builder's call)** above, and:

- the replica maxima, CPU targets and stabilisation windows within §4.4's budget;
- the drain period and the termination grace periods;
- the KEDA chart version (pinned, at least two weeks old);
- the Redis pub/sub channel names and payloads (recorded in the platform spec they touch).
