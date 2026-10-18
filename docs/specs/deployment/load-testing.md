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
| Warm game start (`START_GAME` → `GAME_STARTED`) | p95 < 1 s, p99 < 2 s. Cold start is recorded, not gated |
| `move_rtt` | p99 < 500 ms |
| Non-game HTTP endpoints | p99 < 500 ms |
| Lobby event delivery | p99 < 600 ms |

The builder chooses the defining requirements document and fresh IDs that collide with nothing (check
[`../../requirements/INDEX.md`](../../requirements/INDEX.md); `NFR-PERF` is already defined in nine
documents, and `platform-operations.md` currently stops at NFR-PERF-003), and links this document from
that requirement's Related section.

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
- Work items go in a **new milestone M15** in `docs/implementation`, per the work-item conventions.
  Registry entries are created later, during planning.

### Known spec defects found during recon

To be filed through the `spec-defect` skill when work starts:

- [`flows/03-game-turn.md`](../flows/03-game-turn.md) §C names the RPC `SubmitInput`; the proto and the
  code use `ProcessInput`.
- `game-host-internals.md` §9.3 describes eager reassignment on lease expiry; the code reassigns lazily
  on the next input.
- `NFR-AVAIL-001` conflicts: 99% in `platform-operations.md`, 99.9% in `platform-architecture.md`.
- `STATUS.md` says the Kubernetes manifests do not exist; they do.

## 12. Phase A outcome

**Measurement only** (owner). Phase A delivers the harness plus committed reports stating where and why
the system breaks. It does not fix what it finds. Each degradation found is filed as a separate
follow-up work item (or spec defect) and prioritised by the owner afterwards; Phase B starts after.

**Sequencing** (owner):

1. **Blockers first.** A0 (the chart's Game Host fix), A1 (the overlay, including the `extraEnv` hook), A1a (the rate-limit switches and their spec change),
   the Prometheus scrape jobs and histograms, and any spec work needed to unblock them.
2. **Then the test definition.** A2 provisioning, the A3 k6 harness and scenarios, `loadtest/reset.sh`,
   the report template and the README.
3. **Then test runs and reports.**
