# Load and Scalability Testing

How TurnBase measures what it can carry: a k6 harness that drives real players through room creation,
game start and play against the Helm install on Docker Desktop Kubernetes, the chart and configuration
changes the harness needs, and the thresholds that decide pass or fail. Complements the local stack in
[`local-environment.md`](local-environment.md) and the signals in [`observability.md`](observability.md).

Items marked **(owner)** were decided by the project owner. **(orchestrator's call)** and
**(builder's call)** mark choices made, or deliberately left, during design; the builder may revisit the
former and must make the latter.

---

## 1. Intent, goals and boundaries

The owner wants to know how much the platform handles in the worst case, how it scales up and down, the
p95/p99 latencies and the failure rates — **focused on game behaviour**: room creation, game start and
player actions. The tests become part of this repository. Phase A measures what exists; Phase B adds
Game Host autoscaling.

First runs happen on the owner's machine: Docker Desktop Kubernetes under WSL2, one node, 16 cores and
15 GB on the host. **A single-node ceiling is the laptop's ceiling, not the platform's, and every report
says so.** Degradation found even at this scale is a finding in its own right and gets addressed.

**Goals**

- Find the breaking point: the first load step at which any threshold fails.
- p50/p95/p99 per game step; error rate by code; peak concurrent games and WebSockets.
- A server-side resource picture alongside the client-side one.
- Repeatable, committed scripts and committed run reports.

**Non-goals (Phase A)**

- Platform horizontal scaling. **(owner)** One Platform instance should handle 1000+ users; scaling it
  (option "4") is deferred.
- Cloud clusters.
- Load tests in CI. **(orchestrator's call)** Manual runs only.
- Browser or UI load; chat, social and notification load.

**Anti-goals**

- Any switch that can weaken rate limiting or another protection outside the `test`, `e2e` and `loadtest` profiles (§4 A1, A1a).
- Results that measure the rate limiter, Argon2 hashing or the k6 machine instead of the game path.
- Runs that leave abandoned `IN_PROGRESS` rooms behind.

## 2. Owner decisions

| Decision | Choice |
|---|---|
| Tool | k6 (installed at `/usr/bin/k6`). Scripts live in a new top-level `loadtest/` directory of this umbrella repository, because the work spans every component ([ADR-0012](../../decisions/0012-repo-strategy-polyrepo-submodules.md) boundary rule) |
| Order | Configurable limits for local testing, then a run without scaling = **Phase A**. Game Host scaling = **Phase B**. Platform scaling deferred |
| Pacing | Configurable random think time, but the focus is the pessimistic scenario: think time 0, maximum actions and requests per second |
| Target | Docker Desktop Kubernetes through the existing Helm chart `turnbase-platform/deploy/helm/turnbase` |
| Requirements | New NFRs for game start and p99 latencies are added "for the record" (§7) |

## 3. Current state (recon findings)

These are the facts the design rests on. Several are defects to fix in A0/A1, not constraints.

### 3.1 The Helm chart's Game Host side has never been exercised

The chart exists (the "Kubernetes manifests do not exist yet" note in `STATUS.md` is stale), but:

- `templates/gamehost-service.yaml` is a plain ClusterIP Service, while the host advertises
  `InetAddress.getLocalHost().getHostName() + ":9090"`
  (`turnbase-game-host/.../registration/RegistrationLifecycle.java:110`).
  [`orchestration-gamehost-protocol.md`](../internal-grpc/orchestration-gamehost-protocol.md)
  *Addressing the Game Host pods* requires a headless Service or the pod IP.
- `templates/gamehost-configmap.yaml` lacks the Redis host and password and the
  `TURNBASE_ARTIFACT_STORE_*` credentials that compose sets
  (`deploy/compose/docker-compose.yml`, roughly lines 196-210), and the deployment carries no secret
  reference.
- The chart's Prometheus scrapes only itself (`templates/observability/prometheus.yaml`); compose's
  scrapes the platform and the Game Host.
- The platform ConfigMap has no `extraEnv` hook.
- `origins.platform` is `:8080` but ingress-nginx serves on `:80`.
- No pod has resource requests or limits.

### 3.2 Rate limits

[`rate-limiting.md`](../api-design/rate-limiting.md) defines the tiers; every property is
`TURNBASE_RATE_LIMIT_*` in the platform `application.yml` (roughly lines 161-217) and no value is
mandated:

- guest mint 5/IP/h, registration 3/IP/h, authentication-failure lockout;
- API 100/10 s/user; public 200/min/IP;
- WebSocket per-user buckets (action: burst 10, 5/s; others), at most 4 WebSockets per user.

The master switch `enabled=false` is allowed only under the `test` and `e2e` profiles
(`RateLimitEnabledProfileCheck`); there are no per-mechanism switches yet (A1a adds them). The frontend nginx writes the ingress pod IP into `X-Forwarded-For`
(`turnbase-frontend/nginx/default.conf.template`), so **every per-IP tier is effectively global for a
load generator**. Argon2id (m=19456 KiB, t=2) makes login and registration expensive.

### 3.3 Metrics gaps

- `http_server_requests_seconds` has no histogram buckets, so the `HighLatencyP95` alert
  ([`observability.md`](observability.md) §6) cannot evaluate.
- The platform has `turnbase_websocket_connections_active`, `turnbase_rooms_active`,
  `turnbase_game_sessions_active`, plus Redis and Hikari metrics. It has **no move or dispatch latency
  metric and no gRPC latency metric**.
- The Game Host exposes JVM metrics only.

### 3.4 Game Host execution model

- One Espresso context per `{gameId}:{gameVersion}` per host, shared by all of that host's sessions.
- Each move arrives on its own gRPC thread; the only lock is per session (`SessionDispatcher.java`).
  [`game-host-internals.md`](../game-host/game-host-internals.md) §6.2 says sessions run concurrently in
  one context **(owner)**.
- **Whether Espresso actually parallelises those threads is unknown. Phase A must answer it.**
- There is no max-sessions knob: `platform-architecture.md` FR-SCALE-005 specifies one and it is
  unimplemented.
- Host selection is warm-first, then lowest `activeSessions`
  (`game-host-internals.md`, roughly lines 745-749; `platform-architecture.md` FR-ORCH-004). That is
  spec-mandated, so extra replicas stay idle. This is a Phase B spec change, not a Phase A bug.
- About one Game Host boot in five wedges ([ADR-0018](../../decisions/0018-game-start-resilience.md));
  `docker/supervise.sh` kills it.

### 3.5 Domain facts the harness relies on

- One room per user.
- Tic-Tac-Toe: two players, `gameId` `2cc66e36-52e6-4144-9a10-09d09c982ce4`, bundle in
  `turnbase-game-tictactoe/target/seed/`.
- After `GAME_OVER` the room returns to `LOBBY`, so a rematch is cheap.
- Leaving mid-game leaves the room `IN_PROGRESS`.

### 3.6 Client protocol reference

`.claude/skills/run-turnbase/driver.mjs` is the working client. HTTP: `POST /api/auth/register|login`,
`POST /api/rooms`, `POST /api/rooms/{id}/participants`. STOMP over `/ws` with `Origin` and the session
cookie; heartbeats `10000,10000` (the client must send `\n` about every 4 s).

| Step | Destination |
|---|---|
| `TOGGLE_READY` | `/app/room.{id}.member` |
| `START_GAME` | `/app/room.{id}.host` |
| `GAME_STARTED` | `/topic/room.{id}` |
| `GAME_START_STATUS` | `/topic/room.{id}.start` |
| subscribe to the game | `/topic/game.{sid}` |
| `REQUEST_GAME_SYNC` | `/app/game.{sid}.sync` → `GAME_SYNC` on `/user/queue/game` (`view.yourMark`) |
| `SUBMIT_ACTION {cell}` | `/app/game.{sid}.action` → `GAME_EVENT` move echo |
| end of game | `GAME_OVER` / `GAME_ENDED` |
| errors | `/user/queue/errors` |

## 4. Phase A design

### A0 — Make the chart's Game Host work (prerequisite)

Nothing else is measurable until this is done.

- Advertise a dialable address: pod IP through the downward API, or a headless Service **(builder's
  call)**. Follow the spec; if spec and code conflict, use the `spec-defect` skill.
- Supply Redis host and password and the artifact-store credentials from a Secret.
- The Game Host Deployment already has liveness and readiness probes on
  `/actuator/health/liveness` and `/actuator/health/readiness`; nothing to add.
- Add Prometheus scrape jobs for the platform and Game Host management ports.
- Enable `http.server.requests` percentile histograms **by default**. This fixes `HighLatencyP95` and is
  not load-test-only.
- Verify with the `run-turnbase` driver against the Helm install.

### A1 — Load-test configuration overlay

`loadtest/helm/values-loadtest.yaml`, applied on top of `values-local`:

- **Platform pinned to one instance** for Phase A: `platform.autoscaling.enabled=false` and
  `replicaCount=1` (orchestrator's call). The **Game Host is fixed at one replica** throughout Phase A,
  because warm-first selection (§3.4) would leave extra replicas idle (orchestrator's call).
- **Throttling mechanisms switched off, not merely raised** (owner decision; the mechanism is A1a). The
  overlay sets `SPRING_PROFILES_ACTIVE=local,loadtest` and turns off every mechanism that would distort
  a load scenario: the auth-failure lockout, the API and public tiers, guest-mint and registration
  minting (needed for provisioning), the WebSocket buckets and the WebSocket violation lockout. The
  maximum of 4 WebSockets per user stays enabled, because each user holds one socket and it distorts
  nothing (orchestrator's call). Raised capacities are dropped as an alternative (orchestrator's call).
- `origins` on port 80.
- Explicit resource requests and limits on the platform, Game Host, Postgres and Redis, so results are
  reproducible and the figures are recorded **(orchestrator's call)**. The builder picks values that fit
  the Docker Desktop VM and leave headroom for k6.
- This needs a generic `extraEnv` hook in the platform and Game Host ConfigMaps and Deployments (a chart
  change).
- Prometheus remote-write receiver enabled so k6 can push its metrics, or JSON output only **(builder's
  call)**.

### A1a — Per-mechanism rate-limit switches (spec and platform change)

A blocker-step item (owner decision), done spec-first.

- **Switches.** In addition to the master `turnbase.rate-limit.enabled`, each mechanism gets its own
  `enabled` property: auth-failure lockout, API tier, public tier, guest minting, registration minting,
  uploads, and the WebSocket limits. For the WebSocket limits the builder chooses per-bucket switches or
  a single switch (builder's call), but the set must cover at least the WebSocket buckets, the
  WebSocket violation lockout and max-connections-per-user. **Every switch defaults to enabled.**
- **Safety rule** (orchestrator's call). Disabling the master switch **or any per-mechanism switch** is
  allowed only when the active profiles include `test`, `e2e` or a new `loadtest` profile; otherwise the
  platform refuses to boot. This extends the existing `RateLimitEnabledProfileCheck`. `local` alone does
  **not** permit disabling.
- **Spec first.** [`rate-limiting.md`](../api-design/rate-limiting.md) *Configuration and environments*
  gains the switches and the profile rule before any code is written (§11).

### A2 — User provisioning outside the measured window

Deterministic users `lt-00001…` with one fixed password, created idempotently (log in; register if
absent) by a separate k6 script or setup step. Login cost is tagged and excluded from game thresholds. An
optional, separate "auth storm" scenario may measure login and registration on its own.

### A3 — The k6 harness

Lives in `loadtest/`.

- A small hand-written **STOMP-over-WebSocket module** on k6's WebSocket support (the builder checks the
  installed k6 version for the module to use), with per-VU cookie handling and explicit `Host` and
  `Origin` headers.
- **One VU drives one player pair** — two users, two sockets — which avoids cross-VU coordination
  **(orchestrator's call)**.
- Pair loop:
  1. create room;
  2. join;
  3. both ready;
  4. start;
  5. play to `GAME_OVER` with random legal moves, each sent as soon as the previous move is acknowledged
     (plus `THINK_MIN_MS`/`THINK_MAX_MS`, default 0);
  6. rematch.
- Every K games (env var) the pair leaves and creates a fresh room, so room creation stays loaded.
- **Defensive cleanup** (orchestrator's call): on its first iteration, and before each new room, a VU
  issues `DELETE /api/rooms/{id}/participants/me` for each of its users. Teardown also leaves on a
  best-effort basis, but **abort paths are covered by the post-run reset (§8), not by trusting
  teardown**. The builder checks whether `IMP-M7-05` (empty-lobby close) and `IMP-M7-06` (mid-game
  leave) are done and records which server-side sweeps exist.

**Load model** (orchestrator's call). Pair VUs are closed-loop at think time 0, which is the worst-case
move load. Latency is measured per request, and coordinated omission is a known limitation noted in the
report template. Game start is additionally stressed open-loop by the `start-rate` scenario (§5).

**Generator** (orchestrator's call). k6 (v2.2.0, native WebSockets) runs on the WSL host. Each step
records the CPU of the k6 process and of the Docker Desktop VM. **A step where k6 uses more than about
80% of its available CPU is flagged "generator-bound" in the report and does not count as the platform's
breaking point.** A short calibration run is optional. The README recommends capping the Docker Desktop
VM (`.wslconfig`) so k6 keeps dedicated cores, and the report records the setting.

**Custom metrics**

| Metric | Type | Measures |
|---|---|---|
| `login` | Trend | Login request |
| `room_create` | Trend | Room creation request |
| `room_join` | Trend | Join request |
| `lobby_event` | Trend | Ready or join broadcast as observed by the other player |
| `game_start` | Trend | `START_GAME` → `GAME_STARTED`; the cold first start is tagged separately |
| `move_rtt` | Trend | `SUBMIT_ACTION` → own `GAME_EVENT` echo |
| `game_duration` | Trend | First move to `GAME_OVER` |
| `games_completed` | Counter | Finished games |
| `errors{code}` | Counter | Errors by code |
| `ws_disconnects` | Counter | Unexpected socket closes |

Peak concurrent games is derived from the VU count and the completion rate.

## 5. Scenarios

| Scenario | Shape | Purpose |
|---|---|---|
| `ramp-to-break` | Stepped `ramping-vus`, +N pairs per step, step length from env; stops when thresholds cross (`abortOnFail` with a delay) | Finds the breaking point |
| `soak` | Hold about 70% of the last measured ceiling | Leaks and slow degradation |
| `up-down` | Ramp up, hold, ramp to zero, hold | Checks resource release; drives the autoscaler in Phase B |
| `parallelism` | Closed-loop pairs at think time 0 with a fixed number of concurrent games stepped 1, 2, 4, 8, 16, 32, 64… (orchestrator's call) | Answers the Espresso question directly (below) |
| `start-rate` | Open model: `constant-arrival-rate` of new games per second, stepped upward; each iteration creates a room, joins, readies, starts, plays to the end and leaves (orchestrator's call) | Stresses `game_start` as a rate independent of concurrency |
| `contexts` | The same game under several `gameId`/versions so sessions spread over several Espresso contexts | Separates context contention from host contention. Late, droppable item (below) |
| `default-limits` | Runs with **every limiter enabled** (no `loadtest` profile, stock switches) | Confirms the limiters work under load: asserts `RATE_LIMIT_EXCEEDED` appears and nothing else breaks |

Step size and duration are left to the builder (§10).

### `parallelism`: does the shared Espresso context parallelise?

Per step, record moves/s, `move_rtt` p50/p95/p99, Game Host CPU (cores used) and heap. The single-game
step is the baseline (orchestrator's call).

- If moves/s scales roughly linearly with concurrent games until Game Host CPU saturates, the shared
  context parallelises.
- If throughput plateaus while Game Host CPU stays well below its limit, something serialises. Record
  where, with a thread dump or JFR taken at the plateau step.

### `contexts`: late and droppable

A test-only copy of the Tic-Tac-Toe bundle with a rewritten manifest `gameId`/version is allowed
(orchestrator's call). If the bundle identity rules (signing, catalog) forbid it, drop the scenario and
record why in the report.

**Built (`IMP-M15-10`, 2026-10-18).** The seeder directory accepted four copies, each under a fresh `gameId` and
version `1.0.<k>`; `loadtest/lib/bundles.sh` makes them, `loadtest/scenarios/contexts.js` plays them, and the Game Host
logged four `Game context created` lines. `loadtest/README.md` has the procedure.

## 6. Thresholds

Pass or fail is evaluated per step. A threshold that fails ends the step, and the previous step is the
ceiling.

| Metric | Threshold | Source |
|---|---|---|
| `move_rtt` p95 | < 200 ms | `game-contracts.md` NFR-PERF-002 (stricter here, because it includes game time) |
| `login`, `room_create`, `room_join` p95 | < 200 ms | `platform-operations.md` NFR-PERF-001 |
| `lobby_event` p95 | < 300 ms | `game-rooms.md` NFR-PERF-002 |
| Error rate | < 1% | `HighErrorRate` alert |
| Concurrent sessions | ≥ 500 (capacity check) | `platform-architecture.md` NFR-SCALE-001 |
| Concurrent WebSockets | ≥ 5,000 (capacity check) | `platform-operations.md` NFR-PERF-003 |

The new NFRs in §7 join this table once they are defined.

## 7. New non-functional requirements

Added to the requirements "for the record" **(owner)**. The values are the orchestrator's proposal and
the owner may adjust them. Priority **Should**.

| Proposed target | Value |
|---|---|
| Warm game start (`START_GAME` → `GAME_STARTED`) | p95 < 1 s, p99 < 2 s. Cold start is recorded, not gated. [`platform-operations.md`](../../requirements/platform-operations.md) NFR-LOAD-001 |
| `move_rtt` | p99 < 500 ms. NFR-LOAD-002 |
| Non-game HTTP endpoints | p99 < 500 ms. NFR-LOAD-003 |
| Lobby event delivery | p99 < 600 ms. NFR-LOAD-004 |

The four IDs are defined in [`platform-operations.md`](../../requirements/platform-operations.md) (`NFR-LOAD`, registered in [`../../requirements/INDEX.md`](../../requirements/INDEX.md)), which links this document from its *Related Documents*.

## 8. Outputs and procedure

**Artifacts**

- Raw k6 JSON and summaries under `loadtest/results/` (git-ignored).
- One committed report per meaningful run, `loadtest/reports/YYYY-MM-DD-<scenario>.md`, from a template
  recording:
  - commit SHAs of every submodule and the chart values used;
  - Docker Desktop VM CPU and RAM, and the k6 host's load;
  - the threshold table;
  - the breaking point and **what broke first** — Game Host CPU, Espresso contention, DB pool, Redis,
    platform threads, or k6 itself;
  - server-side observations from Prometheus and Grafana.
- Every report states that the result is a single-node, laptop ceiling, records the `.wslconfig` VM cap, flags generator-bound steps, and notes the coordinated-omission limitation.

**Run procedure**, documented in `loadtest/README.md`: build images → `helm install` with the overlays →
provision users → run a scenario → collect → reset.

**Reset is a first-class build task** (orchestrator's call): `loadtest/reset.sh` does a schema wipe plus
a Redis flush, analogous to the `reset-db` target in the `turnbase-platform` Makefile, or alternatively a
`helm uninstall` plus PVC delete. Users are then re-provisioned (A2). Reset is what covers abort paths;
see the defensive cleanup in A3.

**Capacity targets** (≥500 concurrent sessions, ≥5,000 WebSockets) are recorded as reached or not
reached, with the limiting factor (orchestrator's call). If the laptop cannot generate the load, the
report says so rather than extrapolating.

## 9. Phase B (outline only; gets its own design round)

1. Change the host-selection spec so load spreads: implement the `platform-architecture.md` FR-SCALE-005
   per-host session cap and/or least-loaded among warm hosts.
2. Game Host HPA on `activeSessions` (a custom-metric adapter or KEDA) or on CPU.
3. Scale-in drain: sessions stay on a draining host; termination grace period versus migration.
4. Rerun `up-down`.

The boot wedge ([ADR-0018](../../decisions/0018-game-start-resilience.md)) will hit every scale-out;
measure it.

## 10. Left to the builder

- Exact resource limits, k6 step sizes and durations.
- STOMP module structure.
- Grafana dashboard (optional).
- How work items are registered, likely a new milestone in `docs/implementation` per the `work-item`
  skill.

## 11. Spec work and registration

Spec work is in scope of this effort (orchestrator's call):

- The new NFRs (§7).
- **`rate-limiting.md` *Configuration and environments*** gets the per-mechanism switches and the
  profile rule (A1a). This is a spec change in scope and is done before code, as a blocker-step item.
- A0 picks the pod IP or a headless Service, as the spec already permits either; no spec change is
  needed unless the code path disagrees, and then it goes through the `spec-defect` skill.
- The four recon defects below are filed and fixed through `spec-defect`.
- Work items are registered as **milestone M15** in
  [`registry.md`](../../implementation/registry.md) (`IMP-M15-01…13`, 2026-10-18).

### Spec defects found during recon

Filed and handled by `IMP-M15-02` (2026-10-18):

- **Fixed.** The flows and `local-environment.md` named the internal RPC with a name the proto does not
  have; they now use `ProcessInput`, as `gamehost.proto` and the code do.
- **Fixed.** No CI job applies the Helm chart to a cluster; `deployment/INDEX.md` and
  `local-environment.md` §4 said one did and now say it does not.
- **Fixed.** `STATUS.md` said the Kubernetes manifests do not exist; they do (the Helm chart).
- **Recorded for the owner.** `game-host-internals.md` §9.3 describes eager reassignment on lease expiry
  while the code reassigns lazily on the next input: `game-host-internals.md` §18 `OQ-5`.
- **Recorded for the owner.** `NFR-AVAIL-001` is 99% in `platform-operations.md` and 99.9% in
  `platform-architecture.md`: `OQ-004` in both documents' *Open Questions*.

## 12. Phase A outcome

**Measurement only** (owner). Phase A delivers the harness plus committed reports stating where and why
the system breaks. It does not fix what it finds. Each degradation found is recorded in the
run's report and listed in §13; the owner turns entries into work items (or spec defects) and
prioritises them afterwards, and Phase B starts after. An agent running a Phase A item does not add
registry items.

**Sequencing** (owner):

1. **Blockers first.** A0 (the chart's Game Host fix), A1 (the overlay, including the `extraEnv` hook), A1a (the rate-limit switches and their spec change),
   the Prometheus scrape jobs and histograms, and any spec work needed to unblock them.
2. **Then the test definition.** A2 provisioning, the A3 k6 harness and scenarios, `loadtest/reset.sh`,
   the report template and the README.
3. **Then test runs and reports.**

## 13. Follow-ups

Findings of the Phase A runs, one entry each, appended by the run items (`IMP-M15-11…13`) and read by the
owner. An entry names the report it comes from, the symptom with its numbers, the suspected cause and
what was not checked. An entry is not itself a work item. Milestone M16 (2026-10-19) schedules the fixes: each entry maps to an item in the
[registry](../../implementation/registry.md) M16 section, and the M16 items append an `**M16:**` line to the entries they resolve.

### From `IMP-M15-11` (reports `2026-10-18-parallelism.md`, `2026-10-18-ramp-to-break.md`)

1. **Throughput plateaus at 16 pairs and declines past 32; the Game Host is not the limit.**
   Report: `2026-10-18-parallelism.md`. Moves/s 759 (8 pairs), 805 (16), 909 (32), 678 (256), with the Game Host at 0.9 to 1.25 of
   4 cores and its gRPC executors parked in the thread dump, while the platform pod held about 3.0 of 4 cores and Postgres
   1.6 to 1.8 of 2. Suspected cause: platform CPU (STOMP broker, HTTP, event fan-out), with Postgres as co-limit. Not checked: CPU
   throttling counters of the platform pod, a platform thread dump, Postgres statistics.
   **M16:** `IMP-M16-13`, report [`2026-10-21-m16-cpu.md`](../../../loadtest/reports/2026-10-21-m16-cpu.md). A JFR profile at 64 pairs puts the platform at 3.28 of 4 cores and 2.60 ms of CPU per move, with no leaf above 4.1% and no cost centre that has a local fix: the OpenTelemetry agent 19 to 20%, Spring JDBC 19% (3.8 statements per move), the STOMP channels 13%, Lettuce 10% (about 10 commands per move), gRPC 7.5%. Two local defects were fixed (the completed-session increment now runs last in the recording transaction, so the `game` row lock is held only to the commit; the disconnect scan in `RoomSubscriptionAuthorizer` was linear in every room ever served, 2.3% of CPU, now indexed by session); CPU per move is 2.604 ms before and after, moves per second 1,258 and 1,212 (one run each). **Phase B notes:** the agent's share needs a decision against `FR-TRACE-001`; the per-move reads (a participant lookup three times, `session`/`routing`/`delivered`/`failcount`/`gamelog` keys) need a per-room cache and a single Redis round trip; the pool of 10 connections is saturated (pending max 62 to 68). Postgres is the co-limit.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-parallelism.md`](../../../loadtest/reports/2026-10-21-m16-parallelism.md). Persists: moves/s 955 (16 pairs), 1,055 (32), 1,017 (64), 998 (128), 637 (256), a peak 16% above Phase A's 909 and a 40% decline at 256 (Phase A 678). The Game Host stays at 0.7 to 1.2 of 4 cores; the limit is the database: from 16 pairs the 10-connection pool is fully busy and `hikari_pending` reaches 27, 61, 131, 199 and 207 at 16, 32, 64, 128 and 256 pairs (3 at most in Phase A) with Postgres at 1.9 to 2.1 of its 2 cores. Ceiling still 64 pairs, first to break the DB pool.
2. **The 200 ms move target fails at 128 pairs.** Report: `2026-10-18-parallelism.md`. `tb_move_rtt` p95 223 ms (241 ms at 256),
   `tb_room_join` p99 511 ms at 128; latency grows about linearly with the pair count from 16 pairs on. Suspected cause: queueing
   behind the saturated platform. Not checked: the same load with realistic think times.
   **M16:** `IMP-M16-13`, same report: the cause is confirmed as platform CPU and the connection pool (Hikari pending mean 26 and maximum 68 at 64 pairs, 10 connections active), and the fixes available locally do not move it (Hikari pending mean 13 after the two fixes, `tb_move_rtt` p95 59 and 63 ms before and after). The 128-pair result is for `IMP-M16-14` to rerun; closing the gap is the Phase B notes of finding 1.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-parallelism.md`](../../../loadtest/reports/2026-10-21-m16-parallelism.md). `tb_move_rtt` p95 is exactly 200 ms at 128 pairs (223 in Phase A) and 274 ms at 256 (241); persists at the same pair count. `tb_room_join` p95 climbs 32, 73, 158, 348 and 451 ms from 16 to 256 pairs because HTTP requests queue for a connection (finding 1).
3. **The ramp stops at 80 pairs on a `tb_room_join` tail.** Report: `2026-10-18-ramp-to-break.md`. p95 311.5 ms, p99 474 ms, max 535 ms
   over 838 joins (p50 18 ms) while move p95 was 81 ms; ceiling 70 pairs = 140 sockets, about 55 concurrent sessions, against
   the 500-session and 5,000-WebSocket targets (neither reached). Suspected cause: Postgres at 1.85 of 2 cores and the platform at
   2.9 of 4. Not checked: whether the tail is a periodic stall (step-50 p99 was also 199 ms), Postgres statistics, a rerun of 80 pairs alone.
   **M16:** `IMP-M16-12`, report [`2026-10-21-m16-stall.md`](../../../loadtest/reports/2026-10-21-m16-stall.md). The tail of `start-rate` (`room_join` p99 394 to 622 ms, max 1.0 to 1.5 s) is the backlog of the stall in item 10, not Postgres; with the stall gone a 15-minute run at 16 games/s has `room_join` p99 30.7 ms. Whether the `ramp-to-break` ceiling of 70 pairs moves is for `IMP-M16-14`: that scenario resolved the host name the same way and now resolves it once.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-ramp-to-break.md`](../../../loadtest/reports/2026-10-21-m16-ramp-to-break.md). Persists, with a higher ceiling: the ramp stops at 90 pairs (Phase A: 80), ceiling 80 pairs (70), on `tb_room_join` (running p95 crossed 200 ms; 199.9 ms at the end, against 311 ms in Phase A). `hikari_pending` is 29 to 91 from 30 pairs on (0 in Phase A) with Postgres at 2.06 to 2.11 of 2 cores; first to break the DB pool. 80 concurrent sessions and 160 sockets at the ceiling, still far from 500 and 5,000.
4. **`ready_timeout` errors under load.** Reports: both. 46 at 128 pairs (`parallelism`) and 10 in settle windows (`ramp-to-break`), 0.04%
   of operations at most. Suspected cause: the `SUBSCRIBE_SETTLE_MS` race described in `loadtest/README.md` or a late broadcast.
   Not checked: which rooms, and the server-side order of subscribe and ready.
   **M16:** `IMP-M16-11`. Spring's simple broker sends no `RECEIPT`; the platform now answers a `SUBSCRIBE` that carries a `receipt` header once the broker has registered it (`SubscribeReceiptInterceptor`, `room-websocket.md` § Snapshot Delivery). The k6 harness waits for the receipt instead of `SUBSCRIBE_SETTLE_MS` (removed), and the frontend requests the room snapshot only after the receipts. An integration test subscribes and broadcasts straight after the receipt 1,000 times with 0 misses.
   **M16:** `IMP-M16-14`, all four reports. Resolved: 0 errors of any code in `parallelism` (97,015 games), `ramp-to-break` (122,383), `contexts` (33,175) and `start-rate` (22,842 iterations); Phase A had 46 and 10 `ready_timeout` in the first two and 6 in `contexts`.
    **M16:** `IMP-M16-15`, reports [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md) and [`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md): 0 errors of any code in 213,175 and 111,330 games. Resolved.
5. **Platform threads grow from 80 to 226 under load** (`parallelism`: 226 at 256 pairs; `ramp-to-break`: 138 at 80 pairs); no pool
   exhaustion (`hikari_pending` max 9 once). Not checked: what the extra threads are.
   **M16:** `IMP-M16-10`, report [`2026-10-20-m16-threads.md`](../../../loadtest/reports/2026-10-20-m16-threads.md). Under 32 pairs the extras were Tomcat workers (22 -> 39), the two STOMP channel executors (8 threads each), gRPC's default event loop (4) and a few Netty/Lettuce loops. The STOMP channels, the gRPC client and the scheduler now have explicit bounds; the peak is 156 threads because the hand-off pools grow to 16 each, and they release.
6. **The run protocol's `jcmd 1` fails on the Game Host image** (PID 1 is `supervise.sh`; the JVM is PID 7). Report: `2026-10-18-parallelism.md`.
   `IMP-M15-12` and `13` use `jcmd 7`. **M16:** resolved by IMP-M16-01, record corrected: in the Game Host image `jcmd` exists at `/usr/bin/jcmd` and `kill` only as a shell builtin; PID 1 is `supervise.sh` and the JVM is a child (the process whose `/proc/<pid>/comm` is `java`, PID 7 observed), so `jcmd 1` fails and `jcmd <jvm pid>` works; the platform image has no `jcmd` (its JVM is PID 1), so `census.sh` reads platform threads from `/proc`.

### From `IMP-M15-12` (reports `2026-10-18-start-rate.md`, `2026-10-18-default-limits.md`, `2026-10-18-contexts.md`)
    **M16:** evidence for the corrected protocol: the censuses of `IMP-M16-15` use the JVM's own pid ([`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md), `census-*.txt`).

7. **The Game Host can wedge into health 503 and stay there; the supervisor does not restart it.** Report: `2026-10-18-contexts.md` (attempt 1).
   On the first cold start with four contexts no game started in 357 s: `DEADLINE_EXCEEDED` on `CreateSession` in the platform log, the `BootWatchdog` line in the Game Host log,
   `/actuator/health` answering 503 with the JVM alive, and no restart because `supervise.sh` counts any HTTP answer as alive (ADR-0018 §2). The in-JVM exit with code 70 did not follow.
   **M16:** resolved by IMP-M16-02, the supervisor probes the liveness URL with `curl -sf` and acts on the wedge marker file; `HostWedge` no longer calls the missing `kill` (ADR-0018 §2, restart measured at 17.2 s and 16.0 s).
   No `kill` binary in the pod (only the shell builtin) and `jcmd` cannot attach to a wedged JVM; `kill -3` produced no dump (corrected by IMP-M16-01: `jcmd` exists in the image). The rerun (attempt 2) was clean. Suspected cause: the `HostWedge` path marks health DOWN but the halt is not reached.
   **M16:** the cause is narrowed by IMP-M16-03: a wedge needs a first real guest boot, and the Game Host's throwaway warm-up context made it about ten times likelier (11 of 40 cold starts wedged, 2 of 40 with the warm-up off by default); the residual 5 % is covered by the supervisor. Details in `game-host-internals.md` §11 *Boot-wedge measurement*.
   Not checked: the exact log lines (lost with the stack reset), whether four contexts started at once make a wedge likelier, a thread dump of the wedged JVM.
    **M16:** `IMP-M16-15`, [`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md): the Game Host booted its first guest through the platform on a reset stack, 0 pod restarts and no `killing it` or `Guest boot wedged` line in its log; the soak ([`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md)) had 0 errors and a longest start of 7.2 s after a reset. Not reproduced in two cold starts.
8. **A cold start with four contexts takes 10.2 to 10.3 s, twice the single-context 5 s.** Report: `2026-10-18-contexts.md`. All 50 cold-tagged starts are within 0.1 s of each other; half of the 20 s `BootWatchdog` limit.
   Not checked: whether the contexts are created one after another, and whether more contexts would pass the 20 s limit.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-contexts.md`](../../../loadtest/reports/2026-10-21-m16-contexts.md). Persists and is worse: the first starts on a cold Game Host (warm-up off since `IMP-M16-03`) took 21.3 s on average and 27.8 s at most (50 starts), against 10.2 to 10.3 s in Phase A. The four contexts are created within the same millisecond, so the time is the guest boot that follows; with the warm-up off the boot lands in the first real starts, which is the likely reason and was not isolated. No `BootWatchdog` line and no error appeared although the mean is above 20 s. Not checked: one context with the warm-up off in the same session, what the 20 s limit counts from.
9. **Four contexts cost about three times the Game Host CPU for the same throughput.** Report: `2026-10-18-contexts.md`. 2.95 against 0.99 cores at 810 against 812 moves/s, heap 0.8 against 0.4 GB, same median latency (36 ms), tail slightly worse
   (move p99 85 against 54 ms). The CPU is flat over 5 minutes, so it does not look like warm-up. Compared against `ramp-to-break` at 50 pairs, not a controlled A/B. Not checked: a profile at the plateau, the same 50 pairs on one context in the same session.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-contexts.md`](../../../loadtest/reports/2026-10-21-m16-contexts.md). Persists: 2.83 to 2.98 Game Host cores for 4 contexts at 845 moves/s (2.95 to 3.03 at 810 in Phase A), against 0.93 cores at 1,012 moves/s for one context at 50 pairs in the `ramp-to-break` of the same session; move p50 / p95 / p99 26 / 79 / 140 ms. Flat over the 5 minutes (3.0 to 3.6 cores per minute), heap 0.53 to 0.68 GB (0.8). The shared Espresso engine of `IMP-M16-05` did not reduce it. Not checked: a profile of the plateau, one context at the same pair count in the same session, whether compiled code is shared between contexts of different bundles.
10. **A 10 s WebSocket connect stall recurs about every 300 s.** Reports: `2026-10-18-start-rate.md` (at 300 s and 605 s after the scenario start, the second with 146 dropped iterations and 54 `ready_timeout` at 32 games/s) and `2026-10-18-contexts.md`
    (`ws_connecting` max 10.0 s, the harness connect timeout). The machine is idle during them (platform 1.4 of 4 cores) and platform threads step up (123 to 232). Token expiry is ruled out (session TTL 24 h). Not checked: JVM safepoint or GC logs, ingress and frontend nginx access logs, the Tomcat accept queue, whether the interval is exact.
    **M16:** resolved by `IMP-M16-12`, report [`2026-10-21-m16-stall.md`](../../../loadtest/reports/2026-10-21-m16-stall.md): a harness artefact, not a platform stall. The WSL resolver never answers the IPv4 query for `turnbase.localhost`, so a lookup takes about 10 s, and k6 repeats it every 5 minutes (`dns.ttl`) on the first dial after expiry, which stalls every VU (period 306 s, the ingress receives nothing meanwhile). Ruled out with logs: Postgres checkpoints, Redis RDB/AOF (`LATENCY LATEST` empty), platform GC and safepoints (longest 52 ms), the ingress path (a 10 Hz probe stayed under 0.4 s through both stalls), k6's remote-write output. The harness now sets `dns.ttl` to `inf`; the 15-minute rerun has `ws_connecting` max 13 ms, `room_join` p99 30.7 ms, 0 errors, 0 dropped iterations. Earlier Phase A numbers that contain a stall are affected; `IMP-M16-14` reruns them.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-start-rate.md`](../../../loadtest/reports/2026-10-21-m16-start-rate.md): no stall in 16 minutes, `ws_connecting` at most 2.07 s (in the overloaded steps), 0 errors and 0 dropped iterations up to 32 games/s.
11. **`start-rate` did not find the rate at which `game_start` degrades.** Report: `2026-10-18-start-rate.md`. Warm `game_start` p95 was 11 to 16 ms (p99 13 to 18) at every rate from 1 to 32 games/s, resources far below their limits; the clean ceiling is 16 games/s only because of the stall in item 10. A rerun with higher rates (64, 128 games/s) would be needed.
   **M16:** `IMP-M16-14`, report [`2026-10-21-m16-start-rate.md`](../../../loadtest/reports/2026-10-21-m16-start-rate.md). Resolved: with `RATES=1,2,4,8,16,32,64,128` the clean ceiling is 32 games/s (nominal; 41 completed per second) and warm `game_start` p95 is 15 ms there, 928 ms at 64 and 2.1 s at 128 (the target 1 s is crossed at 128). The other operations cross first, at 64: `tb_move_rtt` p95 785 ms, `tb_room_join` 1.06 s. The limit is the database pool (`hikari_active` 10 of 10, `hikari_pending` up to 207, Postgres at 2.0 to 2.1 of 2 cores, Tomcat at 292 threads) while the Game Host uses 0.5 to 0.6 of 4 cores. Completed games per second run 4% to 29% above the nominal rate in this run (Phase A: within 4%); the cause was not found.
12. **The `default-limits` load trips the WebSocket action bucket in every iteration.** Report: `2026-10-18-default-limits.md`. 320 `RATE_LIMIT_EXCEEDED`, one per iteration in the third game, 961 starts against 641 completions; the HTTP tiers never fired (1,320 requests, 0 429). A client with no think time cannot play more than about two games per burst under the stock limits. Not checked: the server-side frame, a run with think times, the HTTP tiers.
   **M16:** resolved by IMP-M16-01, harness artefact, product limit unchanged. `default-limits` now defaults `THINK_MIN_MS` and `THINK_MAX_MS` to 250.

### From `IMP-M15-13` (reports `2026-10-18-soak.md`, `2026-10-19-up-down.md`)
    **M16:** evidence: [`SUMMARY.md`](../../../loadtest/reports/SUMMARY.md), section *M16*: the harness artefact is closed by `IMP-M16-01`; no later run changed it.

13. **Redis keeps two keys per room and never removes them.** Reports: `2026-10-19-up-down.md`, `2026-10-18-soak.md`. After `up-down`, 18,021 rooms created and 36,047 keys (5 base keys plus
    `room:<id>:pod` and `room:<id>:epoch`, 18,021 each), `used_memory` 1.77 -> 6.91 MB (about 0.29 KB per room), `connected_clients` 4 -> 5, none of it released five minutes after the last room closed.
    In the 30-minute `soak`, 86,271 keys and 1.77 -> 13.93 MB, linear at about 0.36 MB per minute with no plateau. Suspected cause: ownership keys written at room creation with no TTL and no delete on close.
    **M16:** `IMP-M16-08`. The cause was as suspected. Closing a room now deletes both keys in the one after-commit hook that also drops it from `owned` (a compare-and-delete script), and a reconciliation duty `SCAN`s `room:*:pod` and `room:*:epoch` and deletes the keys of closed or missing rooms, which also clears the existing leak. `room-lifecycle.md` §1.1, §1.3, §5.2. Not measured live: the key count after a run is `IMP-M16-14`/`15`.
    Not checked: the TTL of those keys, what the reconciliation job removes, how Redis behaves near its 512 MiB limit (at about 285 bytes per room, roughly 1.9 million rooms).
    **M16:** `IMP-M16-15`, reports [`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md) and [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md). Resolved: after `up-down` at 56 pairs `DBSIZE` was 5 before, 6 five minutes after the load (one extra key with a TTL, not a room key; 5 again a few minutes later) and `used_memory` 1.73 -> 1.68 MB; in the 30-minute soak Redis stayed between 1.1 and 1.9 MB (Phase A 1.77 -> 13.93 MB, 36,047 keys that were never released). The one extra key misses the letter of "within 1%"; whether to count it is the owner's reading.
14. **The platform lost the ownership of about 35 rooms at once, and the room and session gauges never recovered.** Report: `2026-10-18-soak.md`. At 21:22:38Z, 17.5 minutes into the hold, the platform log shows one `ERROR`
    (`IllegalStateException: room ... is not owned by this instance`, `RoomOwnershipService.nextVersion`, "Game end ... could not be detached") and 35 `WARN` "detach of room ... deferred: This instance does not own room" within 2 s.
    `rooms_active` went 48 -> 97 and `sessions_active` 40 -> 75 and stayed there for the rest of the hold; several minutes after the load ended 53 rooms and 38 sessions were still reported with no socket open.
    Suspected cause: a stall like item 10 let the ownership lease lapse and the deferred detaches were not completed. Not checked: the lease TTL and renew interval, whether the stall is the 300 s event of item 10, whether the gauges or the rooms themselves are stale.
    **M16:** `IMP-M16-07`. The likely cause is in the platform, not the stall: `owned` was never pruned and every 3 s one pass did a `GET` per entry on the shared single-thread scheduler, so with tens of thousands of rooms one pass approached the 10 s TTL. Now the lease renewal is one command on its own `lease-renewer` thread, the re-check is batched `MGET` on another, a closed room leaves `owned`, a claim answering *already mine* re-registers a dropped room, a lapse publishes `LivenessState.BROKEN`, and the `epochOf`/`nextVersion` race is a retry. `room-lifecycle.md` §1.3, §1.5, §1.6. Not measured live: the 30-minute rerun is `IMP-M16-15`.
    **M16:** `IMP-M16-15`, report [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md). Resolved: 0 `not owned by this instance` and no ERROR line other than the OpenTelemetry exporter's in 32 minutes at 56 pairs (and in the discarded first attempt); `rooms_active` 54 -> 52 and `sessions_active` 40 -> 37 across the hold, no doubling.
15. **Latency rises and throughput falls across a 30-minute hold at constant load.** Report: `2026-10-18-soak.md`. 49 pairs; HTTP p95 10 -> 48 ms and p99 18 -> 89 ms, requests per second 150 -> 113 (-25%), move p95 38 -> 52 ms, while platform CPU fell 2.96 -> 2.29 cores.
    All targets still held. Suspected cause: growth of a structure the platform walks on each operation (the room and session sets, the Redis keyspace of item 13). Not checked: a profile at the end of the hold, Postgres statistics, the same load after a platform restart.
    **M16:** `IMP-M16-09`. Two walks of that kind are gone. The 60 s reconciliation did nine `KEYS session:*`-style scans and then one `exists` query, one flag lookup and one flag delete *per session*; it is now one `SCAN` pass and a handful of statements per 500 sessions, and its "In Progress, no session" duty no longer writes a row per room per tick (`room-lifecycle.md` §5.2). The two 30 s gauges `count(*)` over `room` use an index-only scan with 100,000 closed rooms in the table (`BusinessMetricsQueryPlanIT`): `rooms_active` through `room_open_game_idx` (the planner prefers it to `room_open_state_idx`, both exclude `CLOSED`), `game_sessions_active` through `room_active_session_idx`. No migration was needed. Not measured live: the 30-minute rerun is `IMP-M16-15`.
    **M16:** `IMP-M16-15`, report [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md). Persists, smaller: p99 77 -> 172 ms (+122%; Phase A x4.9), requests per second 160.6 -> 118.0 (-26.5%), platform CPU 2.44 -> 1.94 cores, the Hikari pool 10 of 10 busy with about 50 pending throughout. The Redis and reconciliation walks of `IMP-M16-08` and `09` are gone; the cause that remains is in Postgres: `Seq Scan on room_participant` in the occupancy subquery (no `room_id` restriction) and in the lookup by `user_id` (no index), 6 to 10 ms a call and linear in a table that keeps every closed room's participants (three statements, 2,367 s of execution time in a 1,926 s run). Phase B note, not fixed here.
16. **Game Host heap after GC grows 251 -> 371 MB over the soak** (+48%, maximum 403 -> 529 MB) with 53 to 56 threads throughout. Report: `2026-10-18-soak.md`. Suspected cause: retained per-session state (more sessions are reported active after item 14) or Espresso context growth.
    Not checked: a heap histogram, whether it stabilises with a longer hold.
    **M16:** `IMP-M16-15`, report [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md). Resolved: Game Host heap after GC +1.1% (175.1 -> 177.0 MB) over the 30-minute hold, threads 103 -> 91 (the discarded first attempt: -5.9%).
17. **The platform keeps its threads after the load is gone.** Reports: `2026-10-19-up-down.md`, `2026-10-18-soak.md`. `up-down`: 57 before the ramp, 131 at the peak, 129 at the end of the ramp down, 110 from 70 s later and 109 five minutes after, with 0 sockets.
    `soak`: 58 -> 151 in steps at about 5, 10 and 20 minutes, flat after. Related to item 5. Suspected cause: a pool that shrinks once and not to its core size. Not checked: which pool, a longer idle wait.
    **M16:** `IMP-M16-10`, report [`2026-10-20-m16-threads.md`](../../../loadtest/reports/2026-10-20-m16-threads.md). The cause was Tomcat's worker pool: a worker above `min-spare` leaves after 60 s idle, and the Game Host's steady trickle of requests (about 0.5 per second) is served by each waiting worker in turn, so none idles that long. `TomcatWorkerIdleTimeout` sets the idle time to 10 s. Idle-after 81 threads against idle-before 77 (before the change 101 against 76), 32 pairs, one run. Also `spring.task.scheduling.pool.size` was inert (the WebSocket broker's scheduler made Boot's back off) and is now applied. The broker channel has no executor under the simple broker, so the settled "three STOMP executors" are two.
    **M16:** `IMP-M16-15`, report [`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md). Resolved: platform threads 76 before, 82 five minutes after the load (+7.9% by `/proc`; the JVM gauge reads 67 against 61), 152 -> 67 within 60 s; in the soak [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md) they stay at 154 to 159 from the first five minutes on.
18. **The Game Host wedges on its first cold start with the default single context too, and the restart took about 6 minutes.** Report: `2026-10-19-up-down.md` (attempt 1, run directory `20261018-234603-up-down-attempt1`). Context created 21:46:24Z, `BootWatchdog` "Guest boot wedged ... after 20000 ms" at 21:46:44Z,
    "supervisor: the JVM has not answered 4 probes in a row; killing it", next JVM log line 21:52:39Z. No game ran in the meantime (platform CPU 0.10 cores for the first 300 s, one `tb_game_start` of 59 s, 278 errors).
    Extends item 7 (seen with four contexts, and there the supervisor did not act). Attempt 2, on a reset stack, did not wedge. Not checked: the frequency, why the kill took about 6 minutes, whether it needs a freshly started pod.
    **M16:** frequency measured by IMP-M16-03: 11 of 40 cold starts wedged on the first real boot with the warm-up on, 2 of 40 with it off (the new default); see item 7. **M16:** resolved by IMP-M16-02, the six minutes are most likely the kubelet's CrashLoopBackOff after the supervisor's non-zero exit (not reproduced on the old image); the supervisor now respawns the JVM itself and a `kill -STOP` restart measured 17.2 s and 16.0 s with the pod's restart count 0 (ADR-0018 *Consequences*).
    **M16:** `IMP-M16-15`, reports [`2026-10-21-m16-up-down.md`](../../../loadtest/reports/2026-10-21-m16-up-down.md) and [`2026-10-21-m16-soak.md`](../../../loadtest/reports/2026-10-21-m16-soak.md): both runs began on a freshly reset stack and booted their first guest through the platform; no wedge in the up-down log, 0 pod restarts in either, 0 errors. Together with `IMP-M16-03` (2 of 40 cold starts wedged with the warm-up off) this is two clean cold starts, not a measurement of the frequency.

### Phase A results

- Date: 2026-10-18 and 2026-10-19; single node, Docker Desktop Kubernetes (16 CPUs, 15.2 GiB), the load generator on the same VM.
- Ceiling: 70 pairs (140 sockets, about 55 concurrent sessions) in `ramp-to-break`; 64 pairs in `parallelism`; 16 games/s clean in `start-rate`.
- What broke first: platform CPU and threads, with Postgres at 1.85 of 2 cores, while the Game Host used 0.9 to 1.5 of 4 cores (`tb_room_join` tail in `ramp-to-break`).
- Capacity targets: 500 concurrent sessions not reached (about 55 at the ceiling); 5,000 WebSockets not reached (140 at the ceiling; 160 open at the abort).
- Summary and all links: [`loadtest/reports/SUMMARY.md`](../../../loadtest/reports/SUMMARY.md).
