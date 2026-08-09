# Platform Architecture Requirements — Game Execution Infrastructure

This document defines the requirements for the game execution infrastructure: how user-submitted game code is isolated, executed, scaled, and managed. It covers the Game Host, Orchestration Service, container lifecycle, and operational concerns.

> **Note:** This document uses "Orchestration Service" as a logical component name. As clarified in `platform-operations.md`, the Orchestration Service is a domain within the Platform Monolith, not a separately deployed process. References here describe logical responsibilities and module boundaries, not deployment boundaries.

> **MVP scope (2026-07-10 owner decisions — see [`../decisions/`](../decisions/INDEX.md)):** This
> document specifies the full production execution infrastructure. For the **local-first MVP**
> several requirements are re-scoped:
> - **gVisor** (FR-SEC-001, FR-SEC-005, CON-003, NFR-SEC-003) is **production-only** — `runsc` is
>   unavailable on Docker Desktop/WSL2 (ADR-0001). MVP isolation relies on Truffle context
>   sandboxing plus pod/process isolation (a single layer for the MVP).
> - **Scaling & startup budgets** (`FR-SCALE-*`, NFR-PERF-001 context-creation, FR-SCALE-007
>   cold-start) are **deferred to post-MVP** (ADR-0001, ADR-0003); the MVP runs a single local
>   Game Host instance.
> - **Game trust model (ADR-0006):** the Espresso spike (ADR-0005,
>   [results](../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md)) found that in-JVM
>   Espresso on **GraalVM CE for JDK 21 cannot isolate *untrusted* Java** — filesystem and network
>   access leak to the host OS, and the per-context heap cap is Oracle-GraalVM-only. The MVP therefore
>   hosts **official, first-party Java games only** (trusted code); untrusted game backends of any
>   language are deferred to post-MVP. For the MVP the untrusted-code isolation Musts —
>   **FR-CTX-004 (no filesystem), FR-CTX-005 (no network), FR-CTX-007 (per-context heap cap)** and
>   **NFR-SEC-001/002** — are **not enforced in-JVM**. Robustness against *buggy* (not hostile)
>   official games comes from **FR-CTX-008 wall-clock timeouts** (`Context.interrupt`, verified on CE)
>   plus a **container/cgroup memory limit**, with filesystem/network denial applied as container-level
>   defense-in-depth. Post-MVP, untrusted Java returns via the hardened-container + gVisor path
>   (OQ-002) and untrusted JS/Python via GraalJS/GraalPy runtimes (FR-CTX-012). Trust is assigned
>   **per runtime** (FR-CTX-011/012) — Espresso/Java is trusted-only for the MVP.
> - "GraalVM CE 23" elsewhere in this document is the deprecated GraalVM product-version label and
>   means **GraalVM CE for JDK 21** (the installed version; there is no CE build for JDK 23).

## Related Documents

- `game-contracts.md` — communication protocol between platform and game BE/FE
- `game-development-experience.md` — GDK libraries, packaging, upload pipeline
- `game-rooms.md` — room lifecycle, team management, game start/end triggers
- `reconnection-flow.md` — disconnect detection, grace period, re-entry
- `../decisions/INDEX.md` — ADR-0001 (local-first platform / gVisor production-only), ADR-0005 (Espresso spike gates the Game Host sandbox design), ADR-0006 (game trust model — official-only Java backends for the MVP)

## Related API Specifications

- [websocket.md](../specs/api-design/websocket.md) — STOMP-over-WebSocket: topics, authentication, message envelope for game and lobby events. Its **Game Session Protocol** section is the client-facing realization of FR-DELIVER-001…006: which destination each effect type is delivered on, the game event catalogue, `resync`-based client catch-up, and action-send authorization.
- [internal-grpc/](../specs/internal-grpc/INDEX.md) — Orchestration Service ↔ Game Host gRPC contract: `gamehost.proto`, topology decision, dispatch/registry services, error model
- [game-host/](../specs/game-host/INDEX.md) — Game Host & execution internals: the server-side realization of the FR-CTX/FR-SESS/FR-LOAD/FR-ORCH/FR-ROUTE/FR-DELIVER/FR-FAIL requirements — Espresso topology, GDK Host + serialization, isolation-mechanism mapping, session/state model, crash recovery, effect delivery

---

## Stakeholders

| Role | Description |
|------|-------------|
| Orchestration Service | Platform microservice that manages game sessions: queues actions, routes inputs to Game Hosts, delivers effects to player clients, manages session lifecycle |
| Game Host | Platform-internal application running inside a GraalVM container; manages Truffle contexts, loads game code, multiplexes sessions, holds game state in local memory with persistence to Redis |
| Room Service | Platform microservice managing room lifecycle; signals game start/end to the Orchestration Service |
| WebSocket Gateway | Platform component maintaining persistent connections to player clients; receives effect deliveries from the Orchestration Service |
| Artifact Store | Storage service holding game bundles (JARs, frontend assets); Game Hosts fetch game code from here on demand |
| Redis | In-memory data store used for game state persistence, action queue durability, and session routing metadata. Enables crash recovery and stateless scaling of the Orchestration Service |
| Operations / SRE | Monitors container health, resource usage, scaling events, game failures |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Truffle Context** | An isolated execution environment within a GraalVM process. Each context has its own heap, resource limits, and sandbox policy. One context is created per (game title, version) pair. |
| **Game Host Container** | A gVisor-sandboxed container running one GraalVM process with the Game Host application. Hosts multiple Truffle contexts for different games. |
| **Session** | One active game instance, identified by a unique session ID (UUID). A session is bound to a specific Truffle context within a Game Host container. |
| **Context Key** | The combination of game ID and game version that uniquely identifies a Truffle context. Multiple sessions of the same game version share one context. |
| **Artifact Store** | A storage backend holding game bundles. Abstracted behind an interface to support local filesystem (development), MinIO (local Kubernetes), and S3 (production). |
| **Action Queue** | A per-session ordered queue of pending player actions, maintained by the Orchestration Service and backed by Redis. Actions are dequeued only after the Game Host confirms processing. |

---

## Functional Requirements

### Game Host — Truffle Context Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CTX-001 | Context per game version | The Game Host must create one Truffle context per unique (game ID, version) pair. Multiple concurrent sessions of the same game version share a single context. A new version of the same game results in a separate context. | Must |
| FR-CTX-002 | Context creation on demand | When the Game Host receives an input for a game version it does not have a context for, it must create a new Truffle context, fetch the game code from the Artifact Store, and load it into the context before processing the input. | Must |
| FR-CTX-003 | Context isolation — memory | Each Truffle context must have an isolated heap. Code in one context must not be able to read or write memory belonging to another context. | Must |
| FR-CTX-004 | Context isolation — no filesystem | Truffle contexts must have no filesystem access. Game code cannot read, write, or list files on the container's filesystem. | Must |
| FR-CTX-005 | Context isolation — no network | Truffle contexts must have no network access. Game code cannot open sockets, make HTTP requests, or communicate with any external system. | Must |
| FR-CTX-006 | Context isolation — no system exit | Game code must not be able to terminate the Game Host process (e.g., via `System.exit()` or equivalent). Such calls must be intercepted and blocked by the Truffle sandbox policy. | Must |
| FR-CTX-007 | Context resource limits — memory | Each Truffle context must have a configurable maximum heap size. When a context exceeds its memory limit, the Game Host must terminate the context and fail all sessions associated with it. | Must |
| FR-CTX-008 | Context resource limits — CPU | Each action invocation within a Truffle context must have a configurable CPU time limit (default: 30 seconds, consistent with `game-contracts.md` NFR-REL-002). When the limit is exceeded, the invocation is terminated and the session fails. | Must |
| FR-CTX-009 | Context idle eviction | When the last active session in a Truffle context ends, an idle timer begins (configurable, default: 5 minutes). If no new session is created for that game version before the timer expires, the context is destroyed and its resources freed. | Should |
| FR-CTX-010 | Context idle eviction — memory pressure | When the Game Host's total memory usage exceeds a configurable threshold, it must evict idle contexts using a least-recently-used (LRU) strategy, regardless of whether their idle timer has expired. Contexts with active sessions are never evicted. | Must |
| FR-CTX-011 | Espresso for JVM | For games declaring the `jvm` runtime type, the Game Host must use GraalVM Espresso (Java on Truffle) to load and execute standard JARs within Truffle contexts. Espresso provides a Java 21 guest JVM. Game backend code must not use Java 22+ APIs. The Game Host process itself runs on GraalVM CE for JDK 21 (Java 21 host). | Must |
| FR-CTX-012 | Polyglot extensibility | The Game Host architecture must support adding new Truffle-based language runtimes (GraalJS, GraalPy, etc.) for future non-JVM game backends. Adding a new runtime requires no changes to the Orchestration Service or the game contracts. | Should |

### Game Host — Session Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SESS-001 | Multi-session multiplexing | The Game Host must manage multiple concurrent sessions across multiple Truffle contexts. Each session is identified by a unique session ID. | Must |
| FR-SESS-002 | Session-to-context binding | Each session is bound to a specific Truffle context (identified by the context key). The Game Host maintains a mapping of session ID to context key. | Must |
| FR-SESS-003 | Session state — local memory | The Game Host holds the game state for each active session in local memory. State is provided to the game code on each handler invocation and updated with the returned value. Local memory is the primary read/write path for performance. | Must |
| FR-SESS-003a | Session state — Redis persistence | After each successful handler invocation, the Game Host must persist the updated game state to Redis, keyed by session ID. This ensures state survives container crashes. | Must |
| FR-SESS-003b | Session state — recovery | When a Game Host receives an input for a session it does not have in local memory (e.g., after a crash and re-dispatch), it must load the state from Redis before invoking the game handler. | Must |
| FR-SESS-004 | Session creation | When the Orchestration Service sends an `init` input for a new session, the Game Host creates the session, invokes the game's `onInit` handler (with empty state), stores the returned initial state in local memory and persists it to Redis, and returns the effects. | Must |
| FR-SESS-005 | Session termination | When the Game Host processes a `game_over` effect or receives a termination signal from the Orchestration Service, it removes the session's state from local memory and from Redis. The Truffle context is not destroyed (other sessions may still use it). | Must |
| FR-SESS-006 | Sequential action processing | The Game Host must process inputs for a given session sequentially. It must not invoke a handler for a session while a previous invocation for the same session is in progress. Inputs for different sessions may be processed concurrently. | Must |

### Game Host — Game Code Loading

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LOAD-001 | Fetch from artifact store | When a Truffle context is created for a game version, the Game Host must fetch the game's backend artifact (JAR for JVM) from the Artifact Store. | Must |
| FR-LOAD-002 | Artifact store abstraction | The Artifact Store interface must be abstracted to support multiple backends: local filesystem (development), S3-compatible storage (MinIO for local Kubernetes, S3 for production). | Must |
| FR-LOAD-003 | Local artifact cache | The Game Host must cache fetched artifacts on the container's local filesystem. Subsequent context creations for the same game version use the cached artifact without re-fetching. | Must |
| FR-LOAD-004 | Cache size limit | The artifact cache has a configurable maximum size. When the limit is reached, the least recently used artifacts (those without an active Truffle context) are evicted. An artifact must not be evicted while it has an active context. | Must |
| FR-LOAD-005 | Entry class discovery | The Game Host must load the game's entry class as declared in the game manifest (`entryClass` field) and verify it implements the `TurnBaseGame` interface. If the class is not found or does not implement the interface, the context creation fails and the session is terminated with an error. | Must |

### Game Host — Registration and Health

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-REG-001 | Service registration | On startup, the Game Host must register itself with the Orchestration Service, advertising its availability and the runtime types it supports. | Must |
| FR-REG-002 | Context reporting | The Game Host must report to the Orchestration Service which game contexts it currently has loaded (context keys). This enables the Orchestration Service to route sessions to the correct Game Host instance. | Must |
| FR-REG-003 | Health checks | The Game Host must expose a health check endpoint. The Orchestration Service uses this to detect unresponsive or crashed Game Host instances. | Must |
| FR-REG-004 | Deregistration on shutdown | On graceful shutdown, the Game Host must deregister from the Orchestration Service so sessions are not routed to a stopping instance. | Should |

### Orchestration Service — Session Lifecycle

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ORCH-001 | Session creation | When the Room Service signals a game start, the Orchestration Service must create a session record, select a Game Host instance (one that has or can load the required game version context), and send the `init` input. | Must |
| FR-ORCH-002 | Session routing | The Orchestration Service must maintain a mapping of session ID to Game Host instance, stored in Redis. All inputs for a session are routed to the same Game Host for the lifetime of the session. Any Orchestration Service replica can read this mapping and route accordingly. | Must |
| FR-ORCH-003 | Session termination | When the Game Host returns a `game_over` effect or a session fails, the Orchestration Service must mark the session as terminated, notify the Room Service (to transition the room to Lobby state), and deliver final effects to player clients. | Must |
| FR-ORCH-004 | Game Host selection | When creating a session, the Orchestration Service must prefer a Game Host instance that already has a Truffle context loaded for the required game version. If no such instance exists, any available instance is selected (it will create the context on demand). | Must |
| FR-ORCH-005 | Game Host failure detection | If a Game Host instance becomes unreachable (health check failure, timeout, crash), the Orchestration Service must reassign affected sessions to another available Game Host instance. The new Game Host loads state from Redis and resumes processing. | Must |
| FR-ORCH-006 | Orchestration Service statelessness | The Orchestration Service must be stateless — all session metadata, routing tables, and action queues are stored in Redis. Any Orchestration Service replica can handle any request. | Must |
| FR-ORCH-007 | Orchestration Service horizontal scaling | Multiple Orchestration Service replicas may run concurrently behind a load balancer. No session affinity is required at the Orchestration Service level. | Must |

### Orchestration Service — Action Routing

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ROUTE-001 | Action queuing | The Orchestration Service must maintain a per-session ordered queue of pending actions, backed by Redis. Actions are enqueued in arrival order. The queue survives Orchestration Service restarts. | Must |
| FR-ROUTE-002 | Sequential dispatch | The Orchestration Service must dispatch actions to the Game Host one at a time per session. The next action is dispatched only after the Game Host confirms processing of the previous action (by returning a response). | Must |
| FR-ROUTE-003 | Action durability | An action must remain in the queue until the Game Host returns a successful response. If the Game Host fails during processing, the action is re-dispatched to another Game Host instance (or the same instance after recovery). | Must |
| FR-ROUTE-004 | Platform input routing | Platform-generated inputs (`player_joined`, `player_left`) are enqueued in the same per-session queue as player actions, maintaining total ordering. | Must |
| FR-ROUTE-005 | gRPC transport | Communication between the Orchestration Service and Game Host uses gRPC. | Must |

### Orchestration Service — Effect Delivery

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DELIVER-001 | Direct WebSocket push | When the Game Host returns effects, the Orchestration Service must deliver them to player clients by pushing directly to the WebSocket Gateway. | Must |
| FR-DELIVER-002 | Effect routing rules | The Orchestration Service must enforce effect routing as defined in `game-contracts.md`: `broadcast` to all players and spectators, `send_to_player` to a single player, `send_to_team` to all players on a team. Spectators receive only `broadcast`, `player_joined`, `player_left`, and `game_over` events. | Must |
| FR-DELIVER-003 | Game log storage | The Orchestration Service must store `log` effect entries for the duration of the game session, enabling players who join mid-game or reconnect to view the full log. | Should |
| FR-DELIVER-004 | Effect ordering preservation | Effects must be delivered to player clients in the order they were returned by the Game Host, as guaranteed by `game-contracts.md` FR-RESP-004. | Must |
| FR-DELIVER-005 | Client catch-up on attach | When a client attaches to a session (game start, reconnection, or mid-game join), the Orchestration Service must serve it a `resync` (`game-contracts.md` FR-IN-006) and deliver the resulting per-viewer view, the session's init context, and the retained game log to that client alone. The platform retains **no effect journal**: past effects are never replayed. Effects returned from `init` are not delivery-guaranteed, since no client is subscribed at session creation. | Must |
| FR-DELIVER-006 | Session affinity | A session's dispatcher and effect fan-out run on the Platform Monolith pod that owns the session's room (ADR-0002), so every participant's WebSocket is local to the producing pod. Dispatcher ownership **follows room ownership**: when a room is claimed by another pod ([ADR-0008](../decisions/0008-room-ownership-lifecycle.md)), that pod re-establishes the dispatcher and resumes from the session's persisted queue. While a room is unowned, nothing dispatches its queue — acceptable, because no client is attached to observe the pause. | Must |

### Container Security

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SEC-001 | gVisor runtime | Game Host containers must run under a gVisor sandbox runtime. gVisor intercepts system calls and provides a user-space kernel, limiting the attack surface available to code running inside the container. **MVP: deferred** — `runsc` is unavailable on Docker Desktop/WSL2; the MVP relies on Truffle context sandboxing plus pod isolation (ADR-0001). | Post-MVP |
| FR-SEC-002 | No outbound network | Game Host containers must have no outbound network access except to: the Orchestration Service (gRPC), the Artifact Store (artifact fetching), Redis (state persistence), and the Kubernetes health check endpoint. All other network traffic must be blocked. | Must |
| FR-SEC-003 | Read-only filesystem | The Game Host container's filesystem must be read-only, except for a designated temporary directory used for the artifact cache. | Must |
| FR-SEC-004 | Non-root execution | The Game Host process must run as a non-root user inside the container. | Must |
| FR-SEC-005 | Two-layer isolation | Game code is isolated by two independent layers: (a) gVisor at the container level (OS-level syscall interception), and (b) Truffle context sandboxing at the application level (memory isolation, capability restrictions). A breach of one layer is contained by the other. | Must |

### Container Lifecycle and Scaling

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SCALE-001 | Minimum instance count | The platform must maintain at least one Game Host container instance at all times for the primary runtime type (JVM/GraalVM). | Must |
| FR-SCALE-002 | Scale-to-zero — future | The platform should support scaling to zero Game Host instances when no sessions are active. This is deferred to a future release; the minimum instance count of one applies initially. | Could |
| FR-SCALE-003 | Horizontal scale-out | When a Game Host container's resource usage (memory or active session/context count) exceeds a configurable threshold, the platform must spin up an additional Game Host container for the same runtime type. | Must |
| FR-SCALE-004 | Scale-out threshold — memory | The memory-based scale-out threshold is a configurable percentage of the container's memory limit (e.g., 80%). | Must |
| FR-SCALE-005 | Scale-out threshold — sessions | The session-count-based scale-out threshold is a configurable maximum number of active sessions per container. | Must |
| FR-SCALE-006 | Scale-in | When a Game Host container's resource usage drops below a configurable threshold and another instance can absorb its remaining sessions, the platform may drain and terminate the container. New sessions are not routed to a draining container; existing sessions complete naturally. | Should |
| FR-SCALE-007 | Cold start budget | A new Game Host container must be ready to process its first input within 5 seconds of the spin-up trigger. This includes container start, GraalVM initialization, and Game Host application readiness. **MVP: deferred** — startup budget gated by the Espresso feasibility spike (ADR-0005); not enforced for the single-instance local MVP (ADR-0001). | Post-MVP |

### Failure Handling

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-FAIL-001 | Action processing failure | If the game code fails to process an action (exception, timeout, malformed output), the Game Host reports the failure to the Orchestration Service. The Orchestration Service terminates the session and notifies all participants. | Must |
| FR-FAIL-002 | Container crash recovery | If a Game Host container crashes, the Orchestration Service detects the failure via health checks and reassigns affected sessions to another Game Host instance (or the same instance after restart) with exponential backoff. The new Game Host loads game state from Redis and resumes processing. Pending actions are re-dispatched from the Redis-backed queue. | Must |
| FR-FAIL-003 | Retry limit | After 3 consecutive failures for the same session (across container restarts or re-dispatches), the Orchestration Service permanently fails the session and notifies all participants. | Must |
| FR-FAIL-004 | State durability | Game state is persisted to Redis after each successful handler invocation. When a Game Host container crashes, state in local memory is lost but the last persisted state in Redis is available for recovery. The only state loss is an in-flight action that was being processed at the time of the crash; this action is re-dispatched from the queue. | Must |
| FR-FAIL-005 | Graceful session termination | When a session is permanently failed (after retry limit), the Orchestration Service must clean up the session's state and queue from Redis, notify the Room Service (to transition the room to Lobby state), and deliver a failure notification to all player clients via the WebSocket Gateway. | Must |
| FR-FAIL-006 | Redis failure handling | If Redis becomes unavailable, the Game Host must continue processing actions using local memory state but must not acknowledge action completion to the Orchestration Service until Redis persistence succeeds. If Redis is unavailable for a configurable duration (default: 60 seconds), affected sessions are failed gracefully. **This requirement covers unavailability only.** Redis *data loss* — reachable, but state gone — is a different condition with a different response, handled by reconciliation (`platform-operations.md` FR-JOB-007/008). The distinction is load-bearing: an errored or timed-out command is evidence of unavailability and must never be read as evidence of absence, or a transient outage would be repaired as though every session had been lost. | Must |
| FR-FAIL-007 | Context crash isolation | If a Truffle context crashes (e.g., out-of-memory within the context), only sessions in that context are affected. Other contexts in the same Game Host must continue operating normally. State for affected sessions remains in Redis; the Orchestration Service can reassign them to a new context. | Must |

### Observability

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-OBS-001 | Metrics — context count | The Game Host must expose the number of active Truffle contexts as a metric. | Must |
| FR-OBS-002 | Metrics — session count | The Game Host must expose the total active session count and the per-context session count as metrics. | Must |
| FR-OBS-003 | Metrics — memory per context | The Game Host must expose memory usage per Truffle context as a metric, where supported by the GraalVM Truffle API. | Should |
| FR-OBS-004 | Metrics — action latency | The Game Host must expose action processing latency (time from input received to response returned) as a histogram metric. | Must |
| FR-OBS-005 | Events — context lifecycle | The Game Host must emit structured log events for context creation, context destruction (with reason: idle eviction, memory pressure, game version unloaded), and context crash. | Must |
| FR-OBS-006 | Events — session lifecycle | The Game Host must emit structured log events for session creation, session completion, and session failure (with failure reason). | Must |
| FR-OBS-007 | Events — artifact loading | The Game Host must emit structured log events for artifact cache hits, cache misses (with fetch latency), and cache evictions. | Should |
| FR-OBS-008 | Correlation IDs | All log events and metrics related to a session must include the session ID as a correlation ID. All events related to a game must include the game ID and version. | Must |
| FR-OBS-009 | Orchestration Service metrics | The Orchestration Service must expose: active session count, action queue depth (total and per-session), effect delivery latency, Game Host instance count, session failure count, and Redis operation latency. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Truffle context creation (excluding artifact fetch) — post-MVP target, gated by the Espresso feasibility spike on GraalVM CE for JDK 21 (ADR-0005) | < 3s p95 | Post-MVP |
| NFR-PERF-002 | Performance | Artifact fetch from store on cache miss | < 5s p95 for 256 MB bundle | Should |
| NFR-PERF-003 | Performance | Action routing overhead (Orchestration Service queue to Game Host invocation, excluding game processing) | < 50ms p95 | Should |
| NFR-PERF-004 | Performance | Effect delivery overhead (Game Host response to WebSocket Gateway push) | < 50ms p95 | Should |
| NFR-SEC-001 | Security | Game code must not be able to access memory, state, or data belonging to other games or sessions | Complete isolation | Must |
| NFR-SEC-002 | Security | Game code must not be able to access the host filesystem, network, or any platform-internal services beyond the in-process invocation boundary managed by the Game Host (see MVP-scope note above: for trusted official Java this is enforced at the container layer, not in-JVM on GraalVM CE) | Zero capability by default | Must |
| NFR-SEC-003 | Security | A vulnerability in game code must not compromise the Game Host process or the container host, given the two-layer isolation (gVisor + Truffle) | Defense in depth | Must |
| NFR-SCALE-001 | Scalability | The platform must support at least 500 concurrent game sessions across all Game Host containers | 500 sessions | Must |
| NFR-SCALE-002 | Scalability | The platform must support at least 200 distinct game titles with active sessions concurrently | 200 game titles | Should |
| NFR-REL-001 | Reliability | A single Truffle context crash must not affect other contexts or sessions in the same Game Host container | Blast radius: one game version | Must |
| NFR-REL-002 | Reliability | Game Host container crashes must be detected and affected sessions failed within a bounded time | < 30s detection | Must |
| NFR-AVAIL-001 | Availability | At least one Game Host container must be available at all times for the primary runtime type | 99.9% uptime | Should |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Game Host containers run on GraalVM Community Edition (CE) with Truffle framework for polyglot sandboxed execution. Oracle GraalVM is not required — Espresso and Truffle are fully available in CE, and Native Image (an Oracle GraalVM differentiator) is not used. **Spike correction (ADR-0005):** CE provides Espresso/Truffle *execution*, but **not adversarial isolation of untrusted Java** — there is no in-JVM filesystem/network denial and no per-context heap cap (the `sandbox.MaxHeapMemory` control is Oracle-GraalVM-only). Untrusted-code isolation must come from the container layer; the MVP avoids the problem by hosting official-only Java (ADR-0006). Truffle's strong sandbox does apply to native-free guest languages (JS/Python) on CE — relevant to the post-MVP GraalJS/GraalPy runtimes. |
| CON-002 | JVM game code is executed via GraalVM Espresso (Java on Truffle), included in GraalVM CE. Espresso provides a Java 21 guest environment. Game backends must target Java 21. The Game Host process runs on GraalVM CE for JDK 21. |
| CON-003 | Container sandboxing uses gVisor as the OCI runtime. |
| CON-004 | Orchestration Service ↔ Game Host communication uses gRPC. |
| CON-005 | Effect delivery from Orchestration Service to WebSocket Gateway uses direct push (no intermediate message bus). |
| CON-006 | Game state is held in the Game Host's local memory (primary) and persisted to Redis (durability). The Orchestration Service does not store or transmit game state. |
| CON-007 | Artifact storage is abstracted behind an interface supporting local filesystem, MinIO (S3-compatible), and AWS S3. |
| CON-008 | Infrastructure runs on Kubernetes. Development uses Docker Desktop Kubernetes or equivalent local cluster. Production targets cloud Kubernetes. |
| CON-009 | All services are designed with cloud-native architecture in mind, but initial development and testing is fully local. |
| CON-010 | The Game Host service runs on Java 21 (GraalVM CE for JDK 21). Game code executes inside an Espresso Java 21 guest context. Platform Monolith uses Java 21 with Spring Boot 3.5+. |
| CON-011 | Redis is used for game state persistence, action queue durability, and session routing metadata. All Orchestration Service state is stored in Redis, making the service stateless and horizontally scalable. |

---

## Out of Scope

- Game contracts protocol (defined in `game-contracts.md`)
- GDK libraries, packaging, and developer tooling (defined in `game-development-experience.md`)
- Room lifecycle management and lobby mechanics (defined in `game-rooms.md`)
- WebSocket Gateway implementation (existing platform infrastructure)
- Kubernetes cluster provisioning, CI/CD pipelines, and infrastructure-as-code
- Network topology, service mesh, and ingress configuration
- Scale-to-zero for Game Host containers (future release)
- Automated game delisting based on failure metrics (future release)
- AI/bot player execution environment (future specification)

---

## Open Questions

- **OQ-001** — Truffle context memory overhead: the actual per-context memory overhead of Espresso contexts needs to be benchmarked. This affects the scale-out thresholds and the number of contexts a single container can support. Prototype validation is needed.
- **OQ-002** — ~~GraalVM Espresso maturity~~ **Partially resolved:** Espresso passes the Java Compatibility Kit (JCK) for Java SE 21 and is mature enough to run large applications (Eclipse IDE, Scala). Performance is 2–3x slower than HotSpot, which is acceptable for turn-based game logic given the 30-second CPU time budget. Remaining validation needed: compatibility of common Java game libraries under Espresso's Java 21 guest. Fallback (process-level isolation with standard JVMs) remains available if compatibility issues arise in practice. **This fallback is first-class for the MVP:** per ADR-0005, an Espresso feasibility spike on GraalVM CE for JDK 21 (also validating OQ-001 per-context overhead and the FR-CTX isolation controls) gates whether the MVP uses in-context Truffle isolation or the process-isolation fallback. The spike runs before the FR-CTX enforcement design is frozen. **Spike done (2026-07-10) — [results](../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md):** in-JVM Espresso on CE does **not** satisfy FR-CTX-004 (filesystem), FR-CTX-005 (network), or FR-CTX-007 (heap cap) on its own — those leak to the host OS / are Oracle-GraalVM-only — so **this process/container-isolation fallback is required for the MVP** to enforce them, while Espresso (if retained) still provides FR-CTX-001/003 isolation, FR-CTX-006 exit-containment, and FR-CTX-008 forced termination. The Game Host internals spec chooses Espresso-in-hardened-container vs plain-JVM-per-process. OQ-001 per-context overhead remains open (out of scope for this go/no-go spike).
- **OQ-003** — Scale-in session draining: the exact mechanism for draining sessions from a container being scaled in needs further design. With Redis-backed state, sessions can be migrated by reassigning the routing entry — the new Game Host loads state from Redis. The question is whether to wait for natural session completion or actively migrate.
